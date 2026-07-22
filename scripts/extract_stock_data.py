import yfinance as yf
import pandas as pd
from datetime import datetime
import logging

TICKERS = ["SNDK", "ASTS", "JNJ", "GOOGL", "VRT", "NVDA", "RKLB"]

def extract_stock_data(tickers: list[str] = TICKERS, period: str = "5d") -> pd.DataFrame:
    """
    ดึงราคาหุ้นย้อนหลัง (period) จาก Yahoo Finance
    คืนค่าเป็น DataFrame เดียวที่รวมทุก ticker
    """
    all_data = []

    for ticker in tickers:
        logging.info(f"Fetching data for {ticker}...")
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)

        if hist.empty:
            logging.warning(f"No data returned for {ticker}, skipping.")
            continue

        hist = hist.reset_index()
        hist["ticker"] = ticker
        hist["extracted_at"] = datetime.now()
        all_data.append(hist)

    if not all_data:
        raise ValueError("No data extracted for any ticker.")

    df = pd.concat(all_data, ignore_index=True)

    # เลือกและเรียงคอลัมน์ให้อ่านง่าย
    df = df[["ticker", "Date", "Open", "High", "Low", "Close", "Volume", "extracted_at"]]
    df.columns = ["ticker", "date", "open", "high", "low", "close", "volume", "extracted_at"]

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = extract_stock_data()
    print(df)
    print(f"\nTotal rows extracted: {len(df)}")