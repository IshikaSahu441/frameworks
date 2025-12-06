# Frameworks

This repository is a collection of projects and examples built with different frameworks and technologies, such as:
- Ray
- Daft
- Pydantic
- Temporal
- PyIceberg
- PyArrow
  
This repository serves as a learning lab and reference hub for exploring how various frameworks work and interact together

---

## Intelligent Real-Time Patient Flow Optimization System

A comprehensive healthcare data pipeline built on MIMIC-III patient admission dataset demonstrating enterprise-grade data engineering practices.

### Components

| Layer | Technology | Status | Purpose |
|-------|-----------|--------|---------|
| **Data Processing** | Daft | ✅ Complete | Distributed ETL with lazy evaluation on 58,976 admission records |
| **Data Validation** | Pydantic | ✅ Complete | Schema validation with 30+ business rules, 99.58% success rate |
| **Distributed Computing** | Ray | ✅ Complete | Feature extraction, anomaly detection, priority scoring |
| **Table Management** | PyIceberg | ✅ Complete | ACID transactions, schema evolution, audit trails, time-travel |
| **Workflow Orchestration** | Temporal | ⏳ Pending | Long-running admission lifecycle workflows |

---

## Repository Structure

Different branches contain experiments and examples done on the frameworks mentioned above.

### Current Branch: Project2.0

**Completed Features:**
- ✅ Daft-based distributed data processing with 16-stage analytics pipeline
- ✅ Pydantic validation layer with comprehensive test suite (34 tests, 100% pass)
- ✅ Ray distributed computing for feature engineering and risk scoring
- ✅ PyIceberg integration with schema evolution and audit trails
- ✅ Complete documentation and usage examples

### Project Structure

```
e:\XCaliber\frameworks\
├── admission_daft_complete.py           # Main Daft processing pipeline
├── admission_pydantic_validation.py     # Pydantic validation script
├── admission_ray_distributed.py         # Ray distributed processing
├── admission_iceberg_integration.py     # Iceberg integration (NEW)
├── iceberg_examples.py                  # Iceberg usage examples (NEW)
├── run_admission_system.py              # Main orchestration entry point
│
├── Pydantic/
│   └── admission_models.py              # Pydantic validation models
│
├── Iceberg/                             # NEW: PyIceberg package
│   ├── __init__.py
│   ├── iceberg_config.py                # Configuration management
│   ├── iceberg_schemas.py               # Table schema definitions
│   ├── iceberg_ingestor.py              # Data ingestion
│   ├── schema_evolution.py              # Schema versioning
│   └── audit_trail.py                   # Audit logging & lineage
│
├── Dataset/
│   └── ADMISSIONS.csv                   # MIMIC-III data (58,976 records)
│
├── tests/
│   ├── test_admission_pydantic.py       # Pydantic validation tests
│   └── test_iceberg_integration.py      # Iceberg integration tests (NEW)
│
├── output/
│   ├── daft_processed/                  # Daft output Parquet files
│   ├── iceberg_catalog/                 # Iceberg warehouse (NEW)
│   └── iceberg_reports/                 # Schema & audit reports (NEW)
│
├── DAFT_SCRIPTS_OVERVIEW.md             # Daft documentation
├── ADMISSION_DAFT_PROCESSING.md         # Daft processing details
├── ADMISSION_PYDANTIC_IMPLEMENTATION.md # Pydantic documentation
├── ICEBERG.md                           # Iceberg guide (NEW)
├── RAY.md                               # Ray documentation
└── README.md                            # This file
```

