import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple

import requests
import psycopg2
from psycopg2.extras import execute_values

ALPHA_URL = "https://www.alphavantage.co/query"

def fetch_daily_adjusted(symbol: str, api_key: str, max_retries: int = 5, backoff: int = 15) -> Dict:
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "apikey": api_key,
        "outputsize": "compact",
        "datatype": "json",
    }
    attempt = 0
    while True:
        attempt += 1
        try:
            resp = requests.get(ALPHA_URL, params=params, timeout=30)
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code} while fetching {symbol}")
            data = resp.json()
            # AlphaVantage returns 'Time Series (Daily)' on success
            if "Time Series (Daily)" in data:
                return data
            # If API limit reached, AlphaVantage includes 'Note'
            if "Note" in data:
                logging.warning("API rate limit hit for %s: %s", symbol, data.get("Note"))
                if attempt >= max_retries:
                    raise RuntimeError("Rate limit reached and max retries exceeded")
                time.sleep(backoff * attempt)
                continue
            if "Error Message" in data:
                raise RuntimeError(f"Error from API for {symbol}: {data.get('Error Message')}")
            # Unexpected payload
            raise RuntimeError(f"Unexpected payload for {symbol}: {data}")
        except requests.RequestException as e:
            logging.exception("Request failed for %s: %s", symbol, e)
            if attempt >= max_retries:
                raise
            time.sleep(backoff * attempt)


def parse_series(symbol: str, payload: Dict) -> List[Tuple]:
    series = payload.get("Time Series (Daily)", {})
    rows = []
    for date_str, vals in series.items():
        try:
            trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            open_ = vals.get("1. open")
            high = vals.get("2. high")
            low = vals.get("3. low")
            close = vals.get("4. close")
            adjusted = vals.get("5. adjusted close") or vals.get("5. adjusted_close") or vals.get("5. adjustedclose")
            volume = vals.get("6. volume") or vals.get("5. volume") or vals.get("6. volume")
            # Convert to proper python types (None if missing)
            def to_num(x):
                try:
                    return None if x is None else float(x)
                except Exception:
                    return None
            rows.append((symbol, trade_date, to_num(open_), to_num(high), to_num(low), to_num(close), to_num(adjusted), int(volume) if volume else None))
        except Exception as e:
            logging.exception("Skipping date %s for %s due to parse error: %s", date_str, symbol, e)
    # return list of tuples matching table columns (without fetched_at; that'll default)
    return rows


def upsert_rows(db_url: str, rows: List[Tuple]):
    if not rows:
        return 0
    insert_sql = """INSERT INTO stock_prices
        (ticker, trade_date, open, high, low, close, adjusted_close, volume)
        VALUES %s
        ON CONFLICT (ticker, trade_date) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            adjusted_close = EXCLUDED.adjusted_close,
            volume = EXCLUDED.volume
    ;"""
    # add fetched_at timestamp column automatically in DB
    conn = psycopg2.connect(db_url)
    try:
        with conn.cursor() as cur:
            rows_with_ts = rows  # execute_values will expand tuples
            execute_values(cur, insert_sql, rows_with_ts, page_size=500)
        conn.commit()
    finally:
        conn.close()
    return len(rows)


def run_for_tickers(tickers: List[str], api_key: str, db_url: str):
    for sym in tickers:
        sym = sym.strip()
        if not sym:
            continue
        try:
            payload = fetch_daily_adjusted(sym, api_key)
            rows = parse_series(sym, payload)
            count = upsert_rows(db_url, rows)
            logging.info("Upserted %d rows for %s", count, sym)
            # respect free API rate limits
            time.sleep(12)
        except Exception as e:
            logging.exception("Failed to process %s: %s", sym, e)
