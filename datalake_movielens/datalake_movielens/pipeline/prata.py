import pandas as pd
from pipeline.config import read_table, save_table

def executar_prata() -> dict:
    """
    Camada Prata (Silver / Staging):
    - Limpeza, tipagem forte, remoção de duplicatas e padronização de strings.
    - Extração de atributos derivados (ano de lançamento, década, data legível).
    - Normalização de gêneros (tabela movie_genres).
    """
    resumo = {}

    # 1. MOVIES
    df_movies = read_table("bronze", "movies", "movies").drop(
        columns=["_data_ingestao", "_arquivo_origem"], errors="ignore"
    )
    df_movies = df_movies.drop_duplicates(subset=["movieId"]).copy()
    df_movies["movie_id"] = df_movies["movieId"].astype("int64")
    df_movies["titulo_original"] = df_movies["title"].astype(str).str.strip()

    df_movies["ano_lancamento"] = (
        df_movies["titulo_original"].str.extract(r"\((\d{4})\)\s*$")[0].astype("Int64")
    )
    df_movies["titulo_limpo"] = (
        df_movies["titulo_original"].str.replace(r"\s*\(\d{4}\)\s*$", "", regex=True).str.strip()
    )
    df_movies["decada"] = (
        (df_movies["ano_lancamento"] // 10 * 10).astype("Int64").astype(str) + "s"
    )
    df_movies.loc[df_movies["ano_lancamento"].isna(), "decada"] = "Desconhecida"

    df_movies["generos"] = df_movies["genres"].replace("(no genres listed)", "Não Informado").fillna("Não Informado")
    df_movies["genero_principal"] = df_movies["generos"].str.split("|").str[0]
    df_movies["qtd_generos"] = df_movies["generos"].apply(
        lambda g: 0 if g == "Não Informado" else len(g.split("|"))
    ).astype("int64")

    df_movies_silver = df_movies[[
        "movie_id", "titulo_limpo", "titulo_original",
        "ano_lancamento", "decada", "generos", "genero_principal", "qtd_generos"
    ]]
    save_table(df_movies_silver, "prata", "movies", "movies")
    resumo["movies"] = len(df_movies_silver)
    print(f"[PRATA] movies: {len(df_movies_silver)} registros limpos.")

    # 1b. MOVIE_GENRES
    df_mg = df_movies_silver[["movie_id", "generos"]].copy()
    df_mg["genero"] = df_mg["generos"].str.split("|")
    df_mg = df_mg.explode("genero")[["movie_id", "genero"]].drop_duplicates()
    df_mg["genero"] = df_mg["genero"].str.strip()
    save_table(df_mg, "prata", "movie_genres", "movie_genres")
    resumo["movie_genres"] = len(df_mg)
    print(f"[PRATA] movie_genres: {len(df_mg)} associações filme-gênero.")

    # 2. LINKS
    df_links = read_table("bronze", "links", "links").drop(
        columns=["_data_ingestao", "_arquivo_origem"], errors="ignore"
    )
    df_links = df_links.drop_duplicates(subset=["movieId"]).copy()
    df_links["movie_id"] = df_links["movieId"].astype("int64")
    df_links["imdb_id"] = "tt" + df_links["imdbId"].astype(int).astype(str).str.zfill(7)
    df_links["tmdb_id"] = df_links["tmdbId"].astype("Int64")
    df_links_silver = df_links[["movie_id", "imdb_id", "tmdb_id"]]
    save_table(df_links_silver, "prata", "links", "links")
    resumo["links"] = len(df_links_silver)
    print(f"[PRATA] links: {len(df_links_silver)} registros padronizados.")

    # 3. RATINGS
    df_ratings = read_table("bronze", "ratings", "ratings").drop(
        columns=["_data_ingestao", "_arquivo_origem"], errors="ignore"
    )
    df_ratings = df_ratings.drop_duplicates(subset=["userId", "movieId", "timestamp"]).copy()
    df_ratings = df_ratings[(df_ratings["rating"] >= 0.5) & (df_ratings["rating"] <= 5.0)]
    df_ratings["user_id"] = df_ratings["userId"].astype("int64")
    df_ratings["movie_id"] = df_ratings["movieId"].astype("int64")
    df_ratings["nota"] = df_ratings["rating"].astype("float64")
    df_ratings["data_hora_avaliacao"] = pd.to_datetime(df_ratings["timestamp"], unit="s", utc=True).dt.tz_localize(None)
    df_ratings["data_avaliacao"] = df_ratings["data_hora_avaliacao"].dt.date

    df_ratings_silver = df_ratings[[
        "user_id", "movie_id", "nota", "data_hora_avaliacao", "data_avaliacao"
    ]]
    save_table(df_ratings_silver, "prata", "ratings", "ratings")
    resumo["ratings"] = len(df_ratings_silver)
    print(f"[PRATA] ratings: {len(df_ratings_silver)} avaliações válidas.")

    # 4. TAGS
    df_tags = read_table("bronze", "tags", "tags").drop(
        columns=["_data_ingestao", "_arquivo_origem"], errors="ignore"
    )
    df_tags["user_id"] = df_tags["userId"].astype("int64")
    df_tags["movie_id"] = df_tags["movieId"].astype("int64")
    df_tags["tag_normalizada"] = df_tags["tag"].astype(str).str.strip().str.lower()
    df_tags = df_tags[df_tags["tag_normalizada"] != ""]
    df_tags["data_hora_tag"] = pd.to_datetime(df_tags["timestamp"], unit="s", utc=True).dt.tz_localize(None)
    df_tags["data_tag"] = df_tags["data_hora_tag"].dt.date
    df_tags = df_tags.drop_duplicates(subset=["user_id", "movie_id", "tag_normalizada", "data_tag"])

    df_tags_silver = df_tags[["user_id", "movie_id", "tag_normalizada", "data_hora_tag", "data_tag"]]
    save_table(df_tags_silver, "prata", "tags", "tags")
    resumo["tags"] = len(df_tags_silver)
    print(f"[PRATA] tags: {len(df_tags_silver)} tags normalizadas.")

    return resumo

if __name__ == "__main__":
    executar_prata()
