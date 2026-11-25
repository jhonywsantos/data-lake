import trino
from pipeline.config import TRINO_HOST, TRINO_PORT, TRINO_USER

DDL_STATEMENTS = [
    "CREATE SCHEMA IF NOT EXISTS hive.bronze WITH (location = 's3a://bronze/')",
    "CREATE SCHEMA IF NOT EXISTS hive.prata WITH (location = 's3a://prata/')",
    "CREATE SCHEMA IF NOT EXISTS hive.ouro WITH (location = 's3a://ouro/')",

    """
    CREATE TABLE IF NOT EXISTS hive.ouro.dim_filme (
        sk_filme BIGINT,
        movie_id BIGINT,
        titulo_limpo VARCHAR,
        titulo_original VARCHAR,
        ano_lancamento BIGINT,
        decada VARCHAR,
        generos VARCHAR,
        genero_principal VARCHAR,
        qtd_generos BIGINT,
        imdb_id VARCHAR,
        tmdb_id BIGINT,
        url_imdb VARCHAR
    ) WITH (external_location = 's3a://ouro/dim_filme/', format = 'PARQUET')
    """,
    """
    CREATE TABLE IF NOT EXISTS hive.ouro.dim_genero (
        sk_genero BIGINT,
        nome_genero VARCHAR
    ) WITH (external_location = 's3a://ouro/dim_genero/', format = 'PARQUET')
    """,
    """
    CREATE TABLE IF NOT EXISTS hive.ouro.bridge_filme_genero (
        sk_filme BIGINT,
        sk_genero BIGINT
    ) WITH (external_location = 's3a://ouro/bridge_filme_genero/', format = 'PARQUET')
    """,
    """
    CREATE TABLE IF NOT EXISTS hive.ouro.dim_usuario (
        sk_usuario BIGINT,
        user_id BIGINT,
        total_avaliacoes BIGINT,
        media_nota_dada DOUBLE,
        perfil_atividade VARCHAR
    ) WITH (external_location = 's3a://ouro/dim_usuario/', format = 'PARQUET')
    """,
    """
    CREATE TABLE IF NOT EXISTS hive.ouro.dim_tempo (
        sk_tempo BIGINT,
        data DATE,
        ano BIGINT,
        trimestre VARCHAR,
        mes BIGINT,
        nome_mes VARCHAR,
        dia BIGINT,
        dia_semana VARCHAR,
        fim_de_semana BOOLEAN
    ) WITH (external_location = 's3a://ouro/dim_tempo/', format = 'PARQUET')
    """,
    """
    CREATE TABLE IF NOT EXISTS hive.ouro.fato_avaliacoes (
        sk_avaliacao BIGINT,
        sk_filme BIGINT,
        sk_usuario BIGINT,
        sk_tempo BIGINT,
        nota DOUBLE,
        avaliacao_positiva BIGINT,
        qtd_tags_aplicadas BIGINT
    ) WITH (external_location = 's3a://ouro/fato_avaliacoes/', format = 'PARQUET')
    """,
    """
    CREATE TABLE IF NOT EXISTS hive.ouro.fato_tags (
        sk_tag BIGINT,
        sk_filme BIGINT,
        sk_usuario BIGINT,
        sk_tempo BIGINT,
        tag_normalizada VARCHAR
    ) WITH (external_location = 's3a://ouro/fato_tags/', format = 'PARQUET')
    """
]

def executar_registro():
    conn = trino.dbapi.connect(
        host=TRINO_HOST,
        port=TRINO_PORT,
        user=TRINO_USER,
        catalog="hive",
    )
    cur = conn.cursor()
    for stmt in DDL_STATEMENTS:
        cur.execute(stmt)
        cur.fetchall()
    print("[TRINO/HIVE] Tabelas externas registradas com sucesso na camada Ouro!")

if __name__ == "__main__":
    executar_registro()
