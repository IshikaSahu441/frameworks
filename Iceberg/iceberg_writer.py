from __future__ import annotations

import os
from typing import Optional

import pyarrow.parquet as pq
from pyiceberg.table import Table

from .iceberg_config import (
    get_catalog,
    IcebergTableConfig,
)


def ensure_file_exists(path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Parquet path not found: {path}")


def get_or_create_table_from_parquet(cfg: IcebergTableConfig) -> Table:
    """
    Load an Iceberg table if it exists; otherwise create it using the
    schema inferred from the Parquet file written by Daft.

    This keeps the schema perfectly aligned with your Daft pipeline.
    """
    catalog = get_catalog()
    ensure_file_exists(cfg.parquet_path)
    pa_table = pq.read_table(cfg.parquet_path)

    #Check whether namespace exists, if not create it
    from pyiceberg.exceptions import NamespaceAlreadyExistsError
    namespace, _, _ = cfg.identifier.partition(".")
    try:
        catalog.create_namespace(namespace)
        print(f"[Iceberg] Created namespace: {namespace}")
    except NamespaceAlreadyExistsError:
        pass

    #Load table if exists
    try:
        table = catalog.load_table(cfg.identifier)
        print(f"[Iceberg] Loaded existing table: {cfg.identifier}")
    except Exception:
        print(f"[Iceberg] Creating new table: {cfg.identifier}")
        # Let the catalog decide the table location based on warehouse
        table = catalog.create_table(
            identifier=cfg.identifier,
            schema=pa_table.schema,  
        )

    return table


def append_parquet_to_table(cfg: IcebergTableConfig) -> int:
    """
    Append the entire Parquet dataset into the Iceberg table.

    Returns:
        int: Number of rows appended.
    """
    table = get_or_create_table_from_parquet(cfg)

    pa_table = pq.read_table(cfg.parquet_path)
    row_count = pa_table.num_rows

    if row_count == 0:
        print(f"[Iceberg] No rows found in {cfg.parquet_path}, skipping append.")
        return 0

    print(
        f"[Iceberg] Appending {row_count} rows from {cfg.parquet_path} "
        f"to table {cfg.identifier}"
    )
    table.append(pa_table)
    print("[Iceberg] Append complete.")

    return row_count