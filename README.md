# Stocks Pipeline

A Dockerized data pipeline to automatically fetch, process, and store stock market data using **Airflow**, **PostgreSQL**, and **Docker**.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Folder Structure](#folder-structure)
4. [Requirements](#requirements)
5. [Setup & Installation](#setup--installation)
6. [Environment Variables](#environment-variables)
7. [Running the Pipeline](#running-the-pipeline)
8. [Database Schema](#database-schema)
9. [Logs](#logs)

---

## Project Overview

This project fetches stock data from a free API (Alpha Vantage), processes it, and stores it in a PostgreSQL database. It runs automatically using **Airflow DAGs** and is fully **Dockerized** for easy deployment.

---

## Features

* Fetch JSON stock data for multiple tickers (e.g., AAPL, MSFT, GOOG)
* Parse and upsert data into PostgreSQL
* Dockerized Airflow setup
* Scheduled and manual pipeline runs
* Logs stored for monitoring pipeline runs

---

## Folder Structure

```
stock-pipeline-fixed/
│
├─ dags/                       # Airflow DAGs and scripts
│   ├─ stock_pipeline_dag.py
│   └─ scripts/fetch_and_upsert.py
│
├─ db/
│   └─ init/                   # Database initialization scripts
│       └─ 01_init_and_schema.sql
│
├─ logs/                        # Airflow logs (runtime)
│
├─ docker-compose.yml           # Docker Compose file
├─ .env                        # Environment variables
├─ README.md                    # Project documentation
└─ requirements.txt             # Python dependencies
```

---

## Requirements

* Docker & Docker Compose
* Python 3.x (for local testing)
* PostgreSQL (Dockerized)
* Alpha Vantage API key

---

## Setup & Installation

1. **Clone the repository**

```bash
git clone https://github.com/snehaa94/stocks_pipeline.git
cd stocks_pipeline
```

2. **Create a `.env` file** in the project root:

```env
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
POSTGRES_DB=postgres
ALPHAVANTAGE_API_KEY=YOUR_API_KEY_HERE
TICKERS=AAPL,MSFT,GOOG
DB_URL=postgresql://airflow:airflow@postgres:5432/stocks
```

> Replace `YOUR_API_KEY_HERE` with your Alpha Vantage API key.

3. **Build and start Docker containers**

```bash
docker-compose up --build
```

This will start:

* PostgreSQL database
* Airflow scheduler
* Airflow webserver at `http://localhost:8080`

4. **Access Airflow UI**

* Open your browser: `http://localhost:8080`
* Default login:

  * Username: `admin`
  * Password: `admin`

5. **Initialize the database** (if not auto-initialized)

```bash
docker exec -it <postgres_container_name> psql -U airflow -d postgres -f /db/init/01_init_and_schema.sql
```

> Replace `<postgres_container_name>` with your running PostgreSQL container name (`docker ps` to check).

---

## Running the Pipeline

* The DAG is named: `stock_prices_pipeline`
* You can **trigger DAG manually** via the Airflow UI or wait for scheduled runs
* Logs for each run are stored in `logs/` and viewable in the Airflow UI

---

## Database Schema

**Table: stock\_prices**

| Column          | Type        | Comment        |
| --------------- | ----------- | -------------- |
| ticker          | text        | Stock ticker   |
| trade\_date     | date        | Trade date     |
| open            | numeric     | Opening price  |
| high            | numeric     | Highest price  |
| low             | numeric     | Lowest price   |
| close           | numeric     | Closing price  |
| adjusted\_close | numeric     | Adjusted close |
| volume          | bigint      | Trading volume |
| fetched\_at     | timestamptz | Default now()  |

**Primary Key:** combination of `ticker` and `trade_date`

---

## Logs

* Airflow stores pipeline run logs in `logs/`
* Each DAG run has its own folder
* Runtime logs (like `logs/scheduler/latest`) may cause issues on Windows if pushed to Git — usually ignored in `.gitignore`

---

**Enjoy your automated stock data pipeline!**
