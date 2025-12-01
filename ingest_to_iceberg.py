from __future__ import annotations

from Iceberg.iceberg_config import (
    ENCOUNTERS_TABLE,
    ENCOUNTER_STATS_TABLE,
    ENCOUNTER_LOCATIONS_TABLE,
    HIGH_PRIORITY_ENCOUNTERS_TABLE,
)
from Iceberg.iceberg_writer import append_parquet_to_table


def main() -> None:
    print("=== MIMIC-IV Iceberg Ingestion ===")

    total_rows = 0
    for cfg in [
        ENCOUNTERS_TABLE,
        ENCOUNTER_STATS_TABLE,
        ENCOUNTER_LOCATIONS_TABLE,
        HIGH_PRIORITY_ENCOUNTERS_TABLE,
    ]:
        try:
            rows = append_parquet_to_table(cfg)
            total_rows += rows
        except FileNotFoundError as e:
            # In case some outputs aren't generated yet, don't crash whole run
            print(f"[Iceberg] Skipping {cfg.identifier}: {e}")

    print(f"=== Done. Total rows appended across tables: {total_rows} ===")


if __name__ == "__main__":
    main()