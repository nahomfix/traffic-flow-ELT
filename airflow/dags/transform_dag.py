import os
from datetime import datetime

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy import DummyOperator

deployment = os.environ.get("DEPLOYMENT", "dev")


default_args = {
    "owner": "airflow",
    "start_date": datetime(2022, 7, 19, 8, 25, 00),
    "concurrency": 1,
    "retries": 0,
}


dag = DAG(
    "transform_dag",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
)

with dag:
    start = DummyOperator(task_id="start")

    dbt_op = BashOperator(
        task_id="dbt",
        bash_command="dbt run --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt",
    )

    start >> dbt_op