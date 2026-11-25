# Data Lake — Arquitetura Medalhão (MovieLens + Power BI)
Disciplina: Tópicos em Banco de Dados — UFAL Campus Arapiraca

## Como Executar

### Opção A: Ambiente Completo com Docker (MinIO + Hive Metastore + Trino + Airflow)
1. Subir os containers:
   `docker compose up -d`
2. Acessar os serviços:
   - **MinIO**: http://localhost:9001 (`minioadmin` / `minioadmin123`)
   - **Airflow**: http://localhost:8082 (`admin` / `admin`) -> Ativar e disparar a DAG `movielens_arquitetura_medalhao`
   - **Trino**: http://localhost:8080 (`admin`)
3. Para consumir no Power BI:
   - Baixe os arquivos `.parquet` do bucket `ouro/` no MinIO (ou use a pasta `ouro_powerbi_csv/` já pronta) e importe via **Obter Dados > Parquet** (ou **Texto/CSV**).

### Opção B: Execução Local Direta (Python -> Parquet)
```bash
pip install -r requirements.txt
set STORAGE_MODE=local
set FILE_FORMAT=parquet
python -m pipeline.run_pipeline
```
Os arquivos Parquet serão gerados em `datalake_local/bronze`, `datalake_local/prata` e `datalake_local/ouro`.
