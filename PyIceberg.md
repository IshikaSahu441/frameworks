# PyIceberg Integration Documentation

## Overview

This document provides a complete explanation of how PyIceberg is integrated into the MIMIC Encounter data processing pipeline. It covers the architecture, catalog configuration, table ingestion workflow, schema handling. This file serves as proof of PyIceberg implementation as part of the hospital-wide data quality and audit tracking system.

---

## Why PyIceberg?

PyIceberg enables a true **data lakehouse** architecture by providing:

* **Time-travel queries** across versions of encounter data
* **Schema evolution** for healthcare datasets that change frequently
* **ACID-compliant table updates**
* **Decoupled metadata storage**
* **Interoperability** with Spark, DuckDB, Trino, Snowflake, and Ray

It ensures that clinical encounter data is versioned, auditable, and queryable in a scalable format.

---

## Architecture

```
FHIR NDJSON → Daft Processing → Pydantic Validation → PyIceberg Tables → Ray/Temporal
```

### Components

* **Daft**: Extracts, flattens, transforms, and exports Parquet files
* **Pydantic**: Applies strict validation rules for healthcare data
* **PyIceberg**: Ingests validated Parquet data into Iceberg tables
* **SQLite Catalog**: Stores Iceberg metadata
* **Iceberg Warehouse**: Stores table files, snapshots, and manifests

---

## Catalog Setup

A `.pyiceberg.yaml` file is placed at the project root:

```yaml
catalog:
  local:
    type: sql
    uri: sqlite:///iceberg_catalog/catalog.db
    warehouse: file:///iceberg_warehouse
```

Environment variable:

```
set PYICEBERG_HOME=%cd%
```

### Catalog Structure

```
iceberg_catalog/
 └── catalog.db
iceberg_warehouse/
 └── mimic/
      ├── encounters_processed/
      ├── encounter_statistics/
      ├── encounter_locations/
      └── high_priority_encounters/
```

---

## Table Ingestion Workflow

The ingestion script processes Daft outputs:

```
output/encounters_processed.parquet
output/encounter_statistics.parquet
output/encounter_locations.parquet
output/high_priority_encounters.parquet
```

### Steps

1. Load Parquet using PyArrow
2. Convert PyArrow schema → Iceberg schema
3. Create namespace `mimic` if not exists
4. Create Iceberg table with correct schema
5. Append Parquet data into the table

### Table Creation Code (simplified)

```python
from Iceberg.iceberg_writer import append_parquet_to_table
append_parquet_to_table(ENCOUNTERS_TABLE)
```

---

## Custom Arrow → Iceberg Schema Conversion

Because older PyIceberg versions lack `schema_to_pyiceberg`, a custom converter was implemented.

### Supported Types

* string
* int32 / int64
* float / double
* timestamp
* date
* boolean
* list
* map
* struct

This ensures the Iceberg tables correctly mirror Daft’s Parquet schemas.

---

## Testing Strategy

A complete test suite demonstrates end‑to‑end PyIceberg functionality:

### ✔ Catalog Tests

* Catalog loads successfully
* Namespace `mimic` exists

### ✔ Table Tests

* Iceberg table is created
* Table can be reloaded
* Row count > 0
* Iceberg schema matches Parquet schema

### Command

```
python -m pytest -v
```

Example output:

```
test_pyiceberg_integration.py::test_catalog_loads PASSED
test_pyiceberg_integration.py::test_namespace_created PASSED
test_table_creation_and_load PASSED
test_table_has_rows PASSED
test_schema_matches_parquet PASSED
```

This serves as strong proof that PyIceberg is installed, configured, and working.

---

## Key Benefits for the Project

### ✔ Auditability

Every data load creates a snapshot with full metadata.

### ✔ Time Travel

Query previous versions of encounter data.

### ✔ Schema Evolution

Healthcare datasets often change; Iceberg handles this gracefully.

### ✔ Interoperability

Ray, DuckDB, Spark, and other engines can read the same tables.

### ✔ Reliability

Tables are ACID-compliant, which is vital for clinical systems.

---

## Future Enhancements

* Enable **partitioning** (e.g., by encounter_class or date)
* Add **Temporal workflow** steps for incremental ingestion
* Add **snapshot rollback tests**
* Add **DuckDB queries** for analytics

---

## Conclusion

PyIceberg is now fully integrated into the data processing pipeline for MIMIC Encounter data. The system supports validated, versioned, auditable clinical datasets with robust test coverage and maintainability.
