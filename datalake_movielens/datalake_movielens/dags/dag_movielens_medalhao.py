from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

from pipeline.bronze import executar_bronze
from pipeline.prata import executar_prata
from pipeline.ouro import executar_ouro
from pipeline.registrar_tabelas import executar_registro

def task_bronze(**context):
    resumo = executar_bronze()
    context["ti"].xcom_push(key="resumo_bronze", value=resumo)

def task_prata(**context):
    resumo_bronze = context["ti"].xcom_pull(task_ids="camada_bronze", key="resumo_bronze")
    print(f"Recebido da Bronze via XCom: {resumo_bronze}")
    resumo = executar_prata()
    context["ti"].xcom_push(key="resumo_prata", value=resumo)

def task_ouro(**context):
    resumo = executar_ouro()
    context["ti"].xcom_push(key="resumo_ouro", value=resumo)

def task_registrar(**context):
    executar_registro()

with DAG(
    dag_id="movielens_arquitetura_medalhao",
    description="Pipeline ELT MovieLens: Bronze -> Prata -> Ouro -> Registro Hive/Trino",
    start_date=datetime(2026, 11, 1),
    schedule="@daily",
    catchup=False,
    tags=["datalake", "medalhao", "ufal"],
) as dag:
    t_bronze = PythonOperator(task_id="camada_bronze", python_callable=task_bronze)
    t_prata = PythonOperator(task_id="camada_prata", python_callable=task_prata)
    t_ouro = PythonOperator(task_id="camada_ouro", python_callable=task_ouro)
    t_registrar = PythonOperator(task_id="registrar_tabelas_trino", python_callable=task_registrar)

    t_bronze >> t_prata >> t_ouro >> t_registrar
