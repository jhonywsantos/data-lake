import os
from datetime import datetime, timezone
import pandas as pd
from pipeline.config import DATA_RAW_DIR, save_table

TABELAS_FONTE = {
    "movies": "movies.csv",
    "ratings": "ratings.csv",
    "tags": "tags.csv",
    "links": "links.csv",
}

def executar_bronze() -> dict:
    """
    Camada Bronze (Raw / Landing Zone):
    - Cópia fiel dos dados brutos da fonte (MovieLens CSV), sem transformações de negócio.
    - Adiciona metadados técnicos de rastreabilidade (_data_ingestao, _arquivo_origem).
    - Salva particionado por data de ingestão (data_ingestao=YYYY-MM-DD).
    """
    agora = datetime.now(timezone.utc)
    data_particao = agora.strftime("%Y-%m-%d")
    resumo = {}

    for nome_tabela, nome_arquivo in TABELAS_FONTE.items():
        caminho_csv = os.path.join(DATA_RAW_DIR, nome_arquivo)
        df = pd.read_csv(caminho_csv)

        df["_data_ingestao"] = agora.isoformat()
        df["_arquivo_origem"] = nome_arquivo

        destino = save_table(df, "bronze", f"{nome_tabela}/data_ingestao={data_particao}", nome_tabela)
        save_table(df, "bronze", nome_tabela, nome_tabela)

        resumo[nome_tabela] = len(df)
        print(f"[BRONZE] {nome_tabela}: {len(df)} registros ingeridos -> {destino}")

    return resumo

if __name__ == "__main__":
    executar_bronze()
