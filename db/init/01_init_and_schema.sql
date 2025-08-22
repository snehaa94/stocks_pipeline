-- Create metadata DB for Airflow and application DB for stocks
CREATE DATABASE airflow;
CREATE DATABASE stocks;

-- Create table in the stocks DB
\connect stocks

CREATE TABLE IF NOT EXISTS stock_prices (
    ticker           TEXT      NOT NULL,
    trade_date       DATE      NOT NULL,
    open             NUMERIC,
    high             NUMERIC,
    low              NUMERIC,
    close            NUMERIC,
    adjusted_close   NUMERIC,
    volume           BIGINT,
    fetched_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT stock_prices_pk PRIMARY KEY (ticker, trade_date)
);

CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_date ON stock_prices (ticker, trade_date DESC);
