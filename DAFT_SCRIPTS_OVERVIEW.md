# Daft Processing Scripts Overview

## Script Architecture

This project contains two complementary Daft processing scripts designed for distributed data analysis of patient admission records. Both scripts leverage Daft's lazy evaluation and distributed processing capabilities for memory-efficient analytics on large-scale healthcare datasets.

---

## 1. admission_daft_processing.py - Basic ETL Pipeline

### Purpose
Performs fundamental data loading and statistical analysis on patient admission records, creating foundational datasets for downstream processing.

### Key Operations

#### Data Loading
- **Loads** 58,976 admission records with lazy evaluation
- Automatic schema inference from CSV format
- Memory-efficient streaming without full materialization

#### Statistical Analysis
- **Computes** basic statistics (total records, unique patients)
- **Analyzes** admission type distribution
  - Emergency: 42,071 (71.3%)
  - Newborn: 7,863 (13.3%)
  - Elective: 7,706 (13.1%)
  - Urgent: 1,336 (2.3%)

#### Insurance Analysis
- **Analyzes** insurance type distribution
  - Medicare: 28,215 (47.8%)
  - Private: 22,582 (38.3%)
  - Medicaid: 5,785 (9.8%)
  - Government: 1,783 (3.0%)
  - Self Pay: 611 (1.0%)

#### Location Patterns
- **Analyzes** admission locations
  - Emergency Room Admit: 22,754
  - Physician Referral/Normal Delivery: 15,079
  - Clinic Referral/Premature: 12,032
  - Transfer from Hospital/External: 8,456

#### Discharge Analysis
- **Analyzes** discharge locations
  - Home: 18,962
  - Home Health Care: 13,963
  - Skilled Nursing Facility (SNF): 7,705
  - Rehab/Distinct Part Hospital: 6,429
  - Dead/Expired: 5,854

#### Mortality Statistics
- **Computes** hospital mortality rates (5,854 deaths, 9.9% overall)
- **Analyzes** emergency admissions by insurance type with mortality breakdown

### Output Files (5 Parquet Files)

1. **admissions_full.parquet** - Complete dataset with all 58,976 records
2. **admission_type_stats.parquet** - Aggregated statistics by admission type
3. **insurance_stats.parquet** - Insurance distribution statistics
4. **emergency_analysis.parquet** - Emergency admissions with mortality by insurance
5. **admissions_enriched.parquet** - Enhanced dataset with derived boolean features
   - `is_emergency` - Boolean flag for emergency admissions
   - `is_elective` - Boolean flag for elective admissions
   - `has_chart_data` - Chart events data availability flag
   - `expired` - Hospital mortality flag

### Execution
```bash
python admission_daft_processing.py
```

### Output Location
```
output/daft_processed/
├── admissions_full.parquet/
├── admission_type_stats.parquet/
├── insurance_stats.parquet/
├── emergency_analysis.parquet/
└── admissions_enriched.parquet/
```

---

## 2. admission_daft_advanced.py - Advanced Analytics

### Purpose
Performs feature engineering for patient flow optimization and clinical risk stratification. Generates specialized datasets for predictive modeling and operational decision support.

### Key Operations

#### Readmission Risk Analysis
- **Identifies** 7,537 patients with multiple admissions (16.2% readmission rate)
- **Tracks** highest-risk patients
  - Maximum: 42 admissions for single patient
  - Provides patient-level aggregation with total admissions and deaths
- **Purpose**: Readmission prediction models

#### Emergency Room Patterns
- **Cross-analyzes** ER admissions by insurance type and ethnicity
- **Key findings**:
  - Medicare/White patients: 9,776 ER admissions, 1,696 deaths (17.4% mortality)
  - Private/White patients: 5,035 ER admissions, 472 deaths (9.4% mortality)
- **Purpose**: ER capacity planning and demographic disparity analysis

#### High-Risk Diagnosis Profiles
- **Identifies** fatal diagnosis patterns from emergency admissions
- **Top fatal conditions**:
  - Sepsis: 266 deaths
  - Pneumonia: 263 deaths
  - Intracranial Hemorrhage: 230 deaths
  - Congestive Heart Failure: 122 deaths
  - Altered Mental Status: 88 deaths
- **Purpose**: Clinical risk stratification and resource allocation

#### Language and Insurance Accessibility
- **Analyzes** barriers to care across linguistic and insurance groups
- **Cross-tabulation** of language and insurance for accessibility planning
- **Key findings**:
  - English speakers with Medicare: 15,845 admissions
  - Identifies non-English speaking populations requiring language services
- **Purpose**: Healthcare accessibility and equity analysis

#### Discharge Disposition Patterns
- **Maps** admission types to discharge destinations
- **Emergency discharge patterns**:
  - Home: 11,115 (26.4%)
  - Home Health Care: 8,934 (21.2%)
  - SNF: 6,497 (15.4%)
  - Rehab: 5,530 (13.1%)
  - Dead/Expired: 5,434 (12.9%)
- **Purpose**: Discharge planning optimization

#### Religious and Cultural Demographics
- **Analyzes** patient demographics by religious affiliation
- **Mortality analysis** across religious groups
  - Catholic: 20,606 admissions, 1,921 deaths (9.3%)
  - Jewish: 5,314 admissions, 670 deaths (12.6%)
- **Purpose**: Culturally competent care planning

### Output Files (4 Parquet Files)

1. **readmission_risk.parquet** - Patients with multiple admissions sorted by risk
2. **er_patterns.parquet** - ER admission patterns by demographics
3. **high_risk_diagnoses.parquet** - Fatal diagnosis patterns
4. **discharge_patterns.parquet** - Admission-to-discharge flow mapping

### Execution
```bash
python admission_daft_advanced.py
```

### Output Location
```
output/daft_advanced/
├── readmission_risk.parquet/
├── er_patterns.parquet/
├── high_risk_diagnoses.parquet/
└── discharge_patterns.parquet/
```

---

## Common Features

### Daft Capabilities Utilized

#### Lazy Evaluation
- Queries optimized before execution
- Multiple operations combined into single pass
- Deferred execution until results needed

#### Distributed Processing
- Automatic parallelization across CPU cores
- Scalable to distributed clusters
- Memory-efficient chunk processing

#### Type Safety
- Automatic schema inference
- Runtime type validation
- Column existence checks at build time

#### Performance Characteristics
- CSV scan: Sub-second processing of 58,976 rows
- Aggregations: Millisecond-level grouped statistics
- Parquet writes: Partitioned for parallel downstream reads

---

## Downstream Integration

### Pydantic (Schema Validation)
- Use Parquet outputs to define validation models
- Type-safe admission record contracts
- HIPAA compliance validation rules

### Ray (Distributed ML)
- Load partitioned Parquet as Ray datasets
- Parallel model training across cluster
- Distributed inference for risk scoring

### Temporal (Workflow Orchestration)
- Trigger workflows from admission events
- Multi-step patient care coordination
- SLA monitoring for high-risk patients

### PyIceberg (Data Lake)
- Ingest Parquet into versioned tables
- Time-travel queries for auditing
- Schema evolution support

---

## Execution Workflow

### Complete Pipeline Execution
```bash
# Run basic processing first
python admission_daft_processing.py

# Run advanced analytics
python admission_daft_advanced.py
```

### Output Summary
- **Total Output Files**: 9 parquet directories
- **Total Records Processed**: 58,976 admissions
- **Processing Time**: Under 5 seconds for complete pipeline
- **Memory Usage**: Streaming mode with lazy evaluation

---

## Data Quality Metrics

### Coverage
- 58,976 total admissions
- 46,520 unique patients
- 7,537 patients with readmissions
- 5,854 in-hospital deaths

### Completeness
- All 19 CSV columns processed
- Missing value handling for optional fields
- Null-safe aggregations

### Accuracy
- Schema validation at load time
- Type enforcement on derived columns
- Consistent aggregation across datasets

---

## Technical Stack

- **Daft**: Distributed dataframe processing
- **PyArrow**: Columnar data format for Parquet I/O
- **Python 3.12**: Runtime environment
- **Lazy Evaluation**: Memory-efficient query optimization
- **Partitioned Storage**: Distributed file format for scalability
