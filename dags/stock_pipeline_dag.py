from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys

# ทำให้ import script จาก /opt/airflow/scripts ได้
sys.path.append('/opt/airflow/scripts')

from extract_stock_data import extract_stock_data
from load_stock_data import load_stock_data


default_args = {
    "owner": "tent",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def extract_task_fn(**context):
    df = extract_stock_data()
    # ส่งข้อมูลต่อไปยัง task ถัดไปผ่าน XCom (แปลงเป็น dict ก่อน เพราะ XCom เก็บ DataFrame ตรงๆ ไม่ได้)
    context["ti"].xcom_push(key="stock_df", value=df.to_json())


def load_task_fn(**context):
    import pandas as pd
    df_json = context["ti"].xcom_pull(key="stock_df", task_ids="extract_task")
    df = pd.read_json(df_json)
    load_stock_data(df)


with DAG(
    dag_id="stock_etl_pipeline",
    default_args=default_args,
    description="Extract stock prices -> Load to Postgres -> Transform with dbt",
    schedule_interval="0 22 * * 1-5",  # ทุกวันจันทร์-ศุกร์ 22:00 (หลังตลาดสหรัฐปิด)
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["stock", "etl"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_task",
        python_callable=extract_task_fn,
    )

    load_task = PythonOperator(
        task_id="load_task",
        python_callable=load_task_fn,
    )

    dbt_run_task = BashOperator(
        task_id="dbt_run_task",
        bash_command="cd /opt/airflow/dbt_project && dbt run --profiles-dir /opt/airflow/dbt_profiles",
    )

    extract_task >> load_task >> dbt_run_task