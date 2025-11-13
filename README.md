# Apache Iceberg Pipeline

This project demonstrates building an Apache Iceberg table from Parquet using Daft, PyIceberg, SQLite catalog, and DuckDB.

## Steps
1. Create virtual environment
2. Install dependencies (`pip install -r requirements.txt`)
3. Run the pipeline (`python main.py`)
4. Query history and data (`python read_history.py`, `python query_iceberg_duckdb.py`)

## Project Structure
main.py — builds Iceberg table
read_history.py — displays snapshot history
query_iceberg_duckdb.py — queries Iceberg table with DuckDB