from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final

from pyiceberg.catalog import load_catalog


CATALOG_NAME: Final[str] = "local"
NAMESPACE: Final[str] = "mimic"

ENCOUNTERS_PROCESSED_PATH: Final[str] = "output/encounters_processed.parquet"
ENCOUNTER_STATS_PATH: Final[str] = "output/encounter_statistics.parquet"
ENCOUNTER_LOCATIONS_PATH: Final[str] = "output/encounter_locations.parquet"
HIGH_PRIORITY_ENCOUNTERS_PATH: Final[str] = "output/high_priority_encounters.parquet"


@dataclass(frozen=True)
class IcebergTableConfig:
    identifier: str
    parquet_path: str


ENCOUNTERS_TABLE = IcebergTableConfig(
    identifier=f"{NAMESPACE}.encounters_processed",
    parquet_path=ENCOUNTERS_PROCESSED_PATH,
)

ENCOUNTER_STATS_TABLE = IcebergTableConfig(
    identifier=f"{NAMESPACE}.encounter_statistics",
    parquet_path=ENCOUNTER_STATS_PATH,
)

ENCOUNTER_LOCATIONS_TABLE = IcebergTableConfig(
    identifier=f"{NAMESPACE}.encounter_locations",
    parquet_path=ENCOUNTER_LOCATIONS_PATH,
)

HIGH_PRIORITY_ENCOUNTERS_TABLE = IcebergTableConfig(
    identifier=f"{NAMESPACE}.high_priority_encounters",
    parquet_path=HIGH_PRIORITY_ENCOUNTERS_PATH,
)


def get_catalog():
    """
    Load the 'local' catalog configured in .pyiceberg.yaml.

    Make sure PYICEBERG_HOME is set to your project root:
        export PYICEBERG_HOME=$(pwd)
    """
    if "PYICEBERG_HOME" not in os.environ:
        print(
            "[Iceberg] Warning: PYICEBERG_HOME is not set. "
            "PyIceberg will search for .pyiceberg.yaml in default locations."
        )
    return load_catalog(name=CATALOG_NAME)