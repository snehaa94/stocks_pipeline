from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import os, logging

from scripts.fetch_and_upsert import run_for_tickers

DEFAULT_ARGS = {
    "owner": "data-eng",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="stock_prices_pipeline",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    max_active_runs=1,
) as dag:

    def _run(**kwargs):
        tickers = os.getenv("TICKERS", "AAPL,MSFT").split(",")
        api_key = os.getenv("ALPHAVANTAGE_API_KEY")
        db_url = os.getenv("DB_URL")
        if not api_key:
            raise RuntimeError("ALPHAVANTAGE_API_KEY is not set")
        if not db_url:
            raise RuntimeError("DB_URL is not set")
        logging.info("Running for tickers: %s", tickers)
        run_for_tickers(tickers, api_key, db_url)

    run_pipeline = PythonOperator(
        task_id="fetch_and_upsert",
        python_callable=_run,
        provide_context=True,
    )
