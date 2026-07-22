import pandas as pd
from sqlalchemy import create_engine, text
import logging

import os

DB_CONNECTION = os.getenv(
    "DB_CONNECTION",
    "postgresql+psycopg2://airflow:airflow@localhost:5432/airflow"
)

TABLE_NAME = "raw_stock_prices"


def get_engine():
    return create_engine(DB_CONNECTION)


def create_table_if_not_exists(engine):
    """สร้างตารางถ้ายังไม่มี พร้อม unique constraint กัน duplicate"""
    create_query = text(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(10) NOT NULL,
            date DATE NOT NULL,
            open NUMERIC,
            high NUMERIC,
            low NUMERIC,
            close NUMERIC,
            volume BIGINT,
            extracted_at TIMESTAMP,
            UNIQUE (ticker, date)
        );
    """)
    with engine.begin() as conn:
        conn.execute(create_query)
    logging.info(f"Table '{TABLE_NAME}' is ready.")


def load_stock_data(df: pd.DataFrame):
    """
    โหลด DataFrame เข้า Postgres แบบ UPSERT
    (ถ้ามี ticker+date ซ้ำ จะ update แทนการสร้างแถวใหม่ -> idempotent)
    """
    engine = get_engine()
    create_table_if_not_exists(engine)

    df["date"] = pd.to_datetime(df["date"]).dt.date

    insert_query = text(f"""
        INSERT INTO {TABLE_NAME} (ticker, date, open, high, low, close, volume, extracted_at)
        VALUES (:ticker, :date, :open, :high, :low, :close, :volume, :extracted_at)
        ON CONFLICT (ticker, date)
        DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            extracted_at = EXCLUDED.extracted_at;
    """)

    records = df.to_dict(orient="records")

    with engine.begin() as conn:
        conn.execute(insert_query, records)
    logging.info(f"Loaded {len(records)} rows into '{TABLE_NAME}'.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from extract_stock_data import extract_stock_data

    df = extract_stock_data()
    load_stock_data(df)
    print(f"Successfully loaded {len(df)} rows.")