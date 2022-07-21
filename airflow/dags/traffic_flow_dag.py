import os
from datetime import datetime

import pandas as pd
from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.postgres.operators.postgres import PostgresOperator

deployment = os.environ.get("DEPLOYMENT", "prod")


def read_data():
    df = pd.read_csv(
        "/opt/airflow/data/20181024_d1_0830_0900.csv",
        skiprows=1,
        header=None,
        delimiter="\n",
    )

    return df.shape


def insert_data():
    pg_hook = PostgresHook(postgres_conn_id=f"traffic_flow_{deployment}")
    conn = pg_hook.get_sqlalchemy_engine()
    df = pd.read_csv(
        "/opt/airflow/data/20181024_d1_0830_0900.csv",
        sep="[,;:]",
        index_col=False,
    )

    df.to_sql(
        "traffic_flow",
        con=conn,
        if_exists="replace",
        index=False,
    )


default_args = {
    "owner": "airflow",
    "start_date": datetime(2022, 7, 19, 8, 25, 00),
    "concurrency": 1,
    "retries": 0,
}


dag = DAG(
    "traffic_flow_dag",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
)
envs = ["dev", "stg", "prod"]

with dag:
    start = DummyOperator(task_id="start")

    dbt_test_op = BashOperator(
        task_id="dbt_test",
        bash_command="dbt run --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt",
    )

    read_data_op = PythonOperator(
        task_id="read_data", python_callable=read_data
    )

    create_table_op = PostgresOperator(
        task_id=f"create_pg_table_{deployment}",
        postgres_conn_id=f"traffic_flow_{deployment}",
        sql="""
            create table if not exists traffic_flow (
                track_id integer,
                type integer,
                traveled_d integer,
                avg_speed integer,
                lat integer,
                lon integer,
                speed integer,
                lon_acc integer,
                lat_acc integer,
                time integer,
                primary key (track_id)
            )
        """,
    )

    load_data_op = PythonOperator(
        task_id=f"load_data_{deployment}", python_callable=insert_data
    )

    start >> dbt_test_op >> read_data_op >> create_table_op >> load_data_op
