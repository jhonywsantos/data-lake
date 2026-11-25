import os
import pandas as pd

# Modo de armazenamento: "minio" (Docker) ou "local" (execução direta sem Docker)
STORAGE_MODE = os.getenv("STORAGE_MODE", "local").lower()
FILE_FORMAT = os.getenv("FILE_FORMAT", "parquet").lower()  # "parquet" (padrão) ou "csv"

DATA_RAW_DIR = os.getenv("DATA_RAW_DIR", os.path.join(os.path.dirname(__file__), "..", "data_raw"))
LOCAL_LAKE_DIR = os.getenv("LOCAL_LAKE_DIR", os.path.join(os.path.dirname(__file__), "..", "datalake_local"))

# Configurações MinIO (S3-compatível)
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")

# Configurações Trino
TRINO_HOST = os.getenv("TRINO_HOST", "localhost")
TRINO_PORT = int(os.getenv("TRINO_PORT", "8080"))
TRINO_USER = os.getenv("TRINO_USER", "admin")

STORAGE_OPTIONS = {
    "key": MINIO_ACCESS_KEY,
    "secret": MINIO_SECRET_KEY,
    "client_kwargs": {"endpoint_url": MINIO_ENDPOINT},
}

def _ext() -> str:
    return "parquet" if (STORAGE_MODE == "minio" or FILE_FORMAT == "parquet") else "csv"

def get_path(layer: str, table: str, stem: str) -> str:
    filename = f"{stem}.{_ext()}"
    if STORAGE_MODE == "minio":
        return f"s3://{layer}/{table}/{filename}"
    path = os.path.join(LOCAL_LAKE_DIR, layer, table)
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, filename)

def save_table(df: pd.DataFrame, layer: str, table: str, stem: str) -> str:
    path = get_path(layer, table, stem)
    if STORAGE_MODE == "minio":
        df.to_parquet(path, index=False, compression="snappy", storage_options=STORAGE_OPTIONS)
    elif FILE_FORMAT == "parquet":
        df.to_parquet(path, index=False, compression="snappy")
    else:
        df.to_csv(path, index=False)
    return path

def read_table(layer: str, table: str, stem: str) -> pd.DataFrame:
    path = get_path(layer, table, stem)
    if STORAGE_MODE == "minio":
        return pd.read_parquet(path, storage_options=STORAGE_OPTIONS)
    elif FILE_FORMAT == "parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)
