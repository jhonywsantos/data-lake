import pandas as pd
from pipeline.config import read_table, save_table

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}
DIAS_SEMANA_PT = {
    0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira",
    3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"
}

def executar_ouro() -> dict:
    """
    Camada Ouro (Gold / Star Schema):
    Constrói o modelo dimensional (Fato-Dimensão) pronto para Power BI e Trino:
      - dim_filme
      - dim_genero
      - bridge_filme_genero (resolve relação N:N entre filmes e gêneros)
      - dim_usuario
      - dim_tempo
      - fato_avaliacoes
      - fato_tags
    """
    resumo = {}

    df_movies = read_table("prata", "movies", "movies")
    df_links = read_table("prata", "links", "links")
    df_mg = read_table("prata", "movie_genres", "movie_genres")
    df_ratings = read_table("prata", "ratings", "ratings")
    df_tags = read_table("prata", "tags", "tags")

    # 1. DIM_FILME
    dim_filme = df_movies.merge(df_links, on="movie_id", how="left").sort_values("movie_id").reset_index(drop=True)
    dim_filme.insert(0, "sk_filme", range(1, len(dim_filme) + 1))
    dim_filme["url_imdb"] = "https://www.imdb.com/title/" + dim_filme["imdb_id"].fillna("") + "/"
    save_table(dim_filme, "ouro", "dim_filme", "dim_filme")
    resumo["dim_filme"] = len(dim_filme)

    # 2. DIM_GENERO e BRIDGE_FILME_GENERO
    generos_unicos = sorted(df_mg["genero"].unique())
    dim_genero = pd.DataFrame({
        "sk_genero": range(1, len(generos_unicos) + 1),
        "nome_genero": generos_unicos
    })
    save_table(dim_genero, "ouro", "dim_genero", "dim_genero")
    resumo["dim_genero"] = len(dim_genero)

    bridge_filme_genero = (
        df_mg.merge(dim_filme[["sk_filme", "movie_id"]], on="movie_id", how="inner")
             .merge(dim_genero, left_on="genero", right_on="nome_genero", how="inner")
             [["sk_filme", "sk_genero"]]
             .drop_duplicates()
             .reset_index(drop=True)
    )
    save_table(bridge_filme_genero, "ouro", "bridge_filme_genero", "bridge_filme_genero")
    resumo["bridge_filme_genero"] = len(bridge_filme_genero)

    # 3. DIM_USUARIO
    stats_user = df_ratings.groupby("user_id").agg(
        total_avaliacoes=("nota", "count"),
        media_nota_dada=("nota", "mean")
    ).reset_index()
    todos_usuarios = pd.DataFrame({
        "user_id": sorted(set(df_ratings["user_id"]).union(set(df_tags["user_id"])))
    })
    dim_usuario = todos_usuarios.merge(stats_user, on="user_id", how="left")
    dim_usuario["total_avaliacoes"] = dim_usuario["total_avaliacoes"].fillna(0).astype("int64")
    dim_usuario["media_nota_dada"] = dim_usuario["media_nota_dada"].round(2)

    def classificar_perfil(qtd):
        if qtd >= 300:
            return "Cinéfilo (300+)"
        elif qtd >= 100:
            return "Frequente (100-299)"
        elif qtd >= 50:
            return "Moderado (50-99)"
        return "Casual (<50)"

    dim_usuario["perfil_atividade"] = dim_usuario["total_avaliacoes"].apply(classificar_perfil)
    dim_usuario.insert(0, "sk_usuario", range(1, len(dim_usuario) + 1))
    save_table(dim_usuario, "ouro", "dim_usuario", "dim_usuario")
    resumo["dim_usuario"] = len(dim_usuario)

    # 4. DIM_TEMPO
    datas_unicas = pd.to_datetime(
        sorted(set(df_ratings["data_avaliacao"].astype(str)).union(set(df_tags["data_tag"].astype(str))))
    )
    dim_tempo = pd.DataFrame({"data": datas_unicas})
    dim_tempo["sk_tempo"] = dim_tempo["data"].dt.strftime("%Y%m%d").astype("int64")
    dim_tempo["ano"] = dim_tempo["data"].dt.year.astype("int64")
    dim_tempo["trimestre"] = "T" + dim_tempo["data"].dt.quarter.astype(str)
    dim_tempo["mes"] = dim_tempo["data"].dt.month.astype("int64")
    dim_tempo["nome_mes"] = dim_tempo["mes"].map(MESES_PT)
    dim_tempo["dia"] = dim_tempo["data"].dt.day.astype("int64")
    dim_tempo["dia_semana"] = dim_tempo["data"].dt.dayofweek.map(DIAS_SEMANA_PT)
    dim_tempo["fim_de_semana"] = dim_tempo["data"].dt.dayofweek.isin([5, 6])
    dim_tempo["data"] = dim_tempo["data"].dt.date
    dim_tempo = dim_tempo[[
        "sk_tempo", "data", "ano", "trimestre", "mes", "nome_mes", "dia", "dia_semana", "fim_de_semana"
    ]]
    save_table(dim_tempo, "ouro", "dim_tempo", "dim_tempo")
    resumo["dim_tempo"] = len(dim_tempo)

    # 5. FATO_AVALIACOES
    tags_por_par = df_tags.groupby(["user_id", "movie_id"]).size().reset_index(name="qtd_tags_aplicadas")

    fato_avaliacoes = (
        df_ratings.merge(dim_filme[["sk_filme", "movie_id"]], on="movie_id", how="inner")
                  .merge(dim_usuario[["sk_usuario", "user_id"]], on="user_id", how="inner")
                  .merge(tags_por_par, on=["user_id", "movie_id"], how="left")
    )
    fato_avaliacoes["sk_tempo"] = pd.to_datetime(fato_avaliacoes["data_avaliacao"]).dt.strftime("%Y%m%d").astype("int64")
    fato_avaliacoes["qtd_tags_aplicadas"] = fato_avaliacoes["qtd_tags_aplicadas"].fillna(0).astype("int64")
    fato_avaliacoes["avaliacao_positiva"] = (fato_avaliacoes["nota"] >= 4.0).astype("int64")
    fato_avaliacoes.insert(0, "sk_avaliacao", range(1, len(fato_avaliacoes) + 1))

    fato_avaliacoes = fato_avaliacoes[[
        "sk_avaliacao", "sk_filme", "sk_usuario", "sk_tempo",
        "nota", "avaliacao_positiva", "qtd_tags_aplicadas"
    ]]
    save_table(fato_avaliacoes, "ouro", "fato_avaliacoes", "fato_avaliacoes")
    resumo["fato_avaliacoes"] = len(fato_avaliacoes)

    # 6. FATO_TAGS
    fato_tags = (
        df_tags.merge(dim_filme[["sk_filme", "movie_id"]], on="movie_id", how="inner")
               .merge(dim_usuario[["sk_usuario", "user_id"]], on="user_id", how="inner")
    )
    fato_tags["sk_tempo"] = pd.to_datetime(fato_tags["data_tag"]).dt.strftime("%Y%m%d").astype("int64")
    fato_tags.insert(0, "sk_tag", range(1, len(fato_tags) + 1))
    fato_tags = fato_tags[["sk_tag", "sk_filme", "sk_usuario", "sk_tempo", "tag_normalizada"]]
    save_table(fato_tags, "ouro", "fato_tags", "fato_tags")
    resumo["fato_tags"] = len(fato_tags)

    for k, v in resumo.items():
        print(f"[OURO] {k}: {v} registros.")

    return resumo

if __name__ == "__main__":
    executar_ouro()
