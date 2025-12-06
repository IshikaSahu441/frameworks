# Patient Admission Data Processing with Daft

## Overview

This document describes the distributed data processing pipeline built using Daft for the MIMIC-III patient admission dataset. The pipeline implements lazy evaluation and memory-efficient transformations to support the Intelligent Real-Time Patient Flow Optimization System.

## Dataset Information

**Source**: MIMIC-III ADMISSIONS.csv  
**Total Records**: 58,976 admission records  
**Unique Patients**: 46,520 patients  
**Time Period**: Historical hospital admission data

## Daft Processing Architecture

### Why Daft?

Daft was selected as the core data processing engine for the following capabilities:

1. **Lazy Evaluation**: Query optimization through deferred execution until results are needed
2. **Distributed Processing**: Automatic parallelization across available CPU cores with potential for cluster scaling
3. **Memory Efficiency**: Processes data in chunks without loading entire dataset into memory
4. **Type Safety**: Automatic schema inference and type validation
5. **Interoperability**: Native Parquet output format compatible with Ray, PyIceberg, Temporal, and Pydantic

### Processing Workflow

```
Raw CSV Data (58,976 rows)
    ↓
Lazy Loading with Schema Inference
    ↓
Distributed Transformations & Aggregations
    ↓
Feature Engineering (Derived Columns)
    ↓
Partitioned Parquet Outputs (9 files)
```

## Data Processing Pipeline

### Stage 1: Basic Data Loading and Statistics

**Script**: `admission_daft_processing.py`

**Operations Performed**:

1. **Lazy CSV Loading**
   - Automatic schema inference
   - Deferred execution for memory efficiency

2. **Record Counting**
   - Total admissions: 58,976
   - Unique patients: 46,520
   - Readmission rate: 16.2% (7,537 patients with multiple admissions)

3. **Admission Type Distribution**
   - EMERGENCY: 42,071 admissions (71.3%)
   - NEWBORN: 7,863 admissions (13.3%)
   - ELECTIVE: 7,706 admissions (13.1%)
   - URGENT: 1,336 admissions (2.3%)

4. **Insurance Analysis**
   - Medicare: 28,215 admissions (47.8%)
   - Private: 22,582 admissions (38.3%)
   - Medicaid: 5,785 admissions (9.8%)
   - Government: 1,783 admissions (3.0%)
   - Self Pay: 611 admissions (1.0%)

5. **Admission Location Patterns**
   - Emergency Room Admit: 22,754 (38.6%)
   - Physician Referral/Normal Delivery: 15,079 (25.6%)
   - Clinic Referral/Premature: 12,032 (20.4%)
   - Transfer from Hospital/External: 8,456 (14.3%)

6. **Discharge Location Analysis**
   - Home: 18,962 (32.2%)
   - Home Health Care: 13,963 (23.7%)
   - Skilled Nursing Facility (SNF): 7,705 (13.1%)
   - Rehab/Distinct Part Hospital: 6,429 (10.9%)
   - Dead/Expired: 5,854 (9.9%)

7. **Mortality Statistics**
   - Hospital deaths: 5,854 (9.9% overall mortality rate)
   - Emergency admissions with deaths: 5,434 (12.9% of emergency admissions)

8. **Emergency Admissions by Insurance**
   - Medicare: 23,634 emergency admissions, 3,681 deaths (15.6% mortality)
   - Private: 12,636 emergency admissions, 1,220 deaths (9.7% mortality)
   - Medicaid: 4,024 emergency admissions, 353 deaths (8.8% mortality)

### Stage 2: Advanced Analytics and Feature Engineering

**Script**: `admission_daft_advanced.py`

**Operations Performed**:

1. **Readmission Risk Identification**
   - Identified 7,537 patients with multiple admissions
   - Highest risk patient: 42 total admissions
   - Top readmission patients tracked for predictive modeling

2. **Emergency Room Pattern Analysis**
   - Cross-tabulation by insurance type and ethnicity
   - Medicare/White patients: 9,776 ER admissions, 1,696 deaths (17.4% mortality)
   - Private/White patients: 5,035 ER admissions, 472 deaths (9.4% mortality)
   - Identified demographic disparities in ER outcomes

3. **High-Risk Diagnosis Profiles**
   - Sepsis: 266 fatal cases
   - Pneumonia: 263 fatal cases
   - Intracranial Hemorrhage: 230 fatal cases
   - Congestive Heart Failure: 122 fatal cases
   - Altered Mental Status: 88 fatal cases

4. **Language and Insurance Accessibility**
   - English speakers with Medicare: 15,845 admissions
   - Non-English speakers identified for language services
   - Insurance barriers analyzed across linguistic groups

5. **Discharge Disposition Patterns**
   - Emergency to Home: 11,115 (26.4% of emergency admissions)
   - Emergency to Home Health Care: 8,934 (21.2%)
   - Emergency to SNF: 6,497 (15.4%)
   - Emergency to Rehab: 5,530 (13.1%)

6. **Cultural and Religious Demographics**
   - Catholic: 20,606 admissions, 1,921 deaths (9.3% mortality)
   - Not Specified: 11,753 admissions, 937 deaths (8.0% mortality)
   - Jewish: 5,314 admissions, 670 deaths (12.6% mortality)

## Output Files

### Basic Processing Outputs (`output/daft_processed/`)

1. **admissions_full.parquet**
   - All 58,976 admission records with complete fields
   - 19 columns including demographics, admission details, timing, insurance
   - Partitioned format for distributed reading

2. **admission_type_stats.parquet**
   - 4 rows (one per admission type)
   - Columns: ADMISSION_TYPE, admission_count

3. **insurance_stats.parquet**
   - 5 rows (one per insurance type)
   - Columns: INSURANCE, total_admissions

4. **emergency_analysis.parquet**
   - 5 rows (emergency admissions by insurance)
   - Columns: INSURANCE, emergency_admissions, deaths

5. **admissions_enriched.parquet**
   - Enhanced dataset with derived boolean features
   - New columns: is_emergency, is_elective, has_chart_data, expired
   - Ready for machine learning feature engineering

### Advanced Analytics Outputs (`output/daft_advanced/`)

1. **readmission_risk.parquet**
   - 7,537 rows (patients with multiple admissions)
   - Columns: SUBJECT_ID, total_admissions, total_deaths
   - Sorted by readmission count for risk prioritization

2. **er_patterns.parquet**
   - Cross-tabulation of ER admissions by insurance and ethnicity
   - Columns: INSURANCE, ETHNICITY, er_count, er_deaths
   - Identifies demographic patterns in emergency care

3. **high_risk_diagnoses.parquet**
   - Fatal case analysis by diagnosis
   - Columns: DIAGNOSIS, fatal_cases
   - Supports clinical risk stratification

4. **discharge_patterns.parquet**
   - Discharge destinations by admission type
   - Columns: ADMISSION_TYPE, DISCHARGE_LOCATION, count
   - Enables discharge planning optimization

## Key Processing Features

### Lazy Evaluation Benefits

- Queries are optimized before execution
- Multiple operations combined into single pass
- Memory usage minimized through streaming

### Distributed Processing

- Automatic parallelization across CPU cores
- Scalable to distributed clusters with Ray or Dask backends
- Efficient handling of large datasets without memory constraints

### Type Safety

- Automatic schema inference from CSV
- Type validation during transformations
- Column existence checks at query build time

### Performance Characteristics

- CSV scan: 58,976 rows processed in under 1 second
- Aggregations: Grouped statistics computed in milliseconds
- Parquet writes: Partitioned outputs for parallel downstream reads

## Integration with Downstream Frameworks

### Pydantic (Next Stage)
- Use Daft-processed Parquet files for schema validation
- Define data models matching the enriched dataset structure
- Validate admission records against HIPAA compliance rules

### Ray (Next Stage)
- Load Parquet partitions as Ray datasets
- Distribute machine learning training across cluster
- Parallel inference for readmission risk scoring

### Temporal (Next Stage)
- Trigger workflows based on admission events
- Orchestrate multi-step patient care coordination
- Implement SLAs for high-risk patient follow-up

### PyIceberg (Next Stage)
- Ingest Parquet outputs into Iceberg data lake
- Enable time-travel queries for regulatory audits
- Support schema evolution for changing healthcare standards

## Technical Implementation Details

### Daft Operations Used

**Data Ingestion**:
```python
df = daft.read_csv("Dataset/ADMISSIONS.csv")
```

**Lazy Transformations**:
```python
df.with_columns({
    "is_emergency": col("ADMISSION_TYPE") == "EMERGENCY",
    "expired": col("HOSPITAL_EXPIRE_FLAG") == 1
})
```

**Distributed Aggregations**:
```python
df.groupby(col("ADMISSION_TYPE"))
  .agg(col("HADM_ID").count().alias("admission_count"))
  .sort(col("admission_count"), desc=True)
```

**Filtering with Predicate Pushdown**:
```python
df.where((col("ADMISSION_TYPE") == "EMERGENCY") & 
         (col("HOSPITAL_EXPIRE_FLAG") == 1))
```

**Efficient Exports**:
```python
df.write_parquet("output/daft_processed/admissions_full.parquet")
```

### Memory Efficiency Strategy

- CSV reading with lazy evaluation
- Streaming aggregations without full materialization
- Partitioned Parquet writes for distributed storage
- Column pruning in aggregation queries

## Summary Statistics

### Dataset Overview
- Total Admissions: 58,976
- Unique Patients: 46,520
- Average Admissions per Patient: 1.27
- Patients with Readmissions: 7,537 (16.2%)
- Overall Mortality Rate: 9.9%

### Admission Patterns
- Emergency Dominance: 71.3% of all admissions
- Newborn Admissions: 13.3%
- Elective Procedures: 13.1%
- Urgent Cases: 2.3%

### Insurance Distribution
- Medicare Coverage: 47.8% (predominantly elderly)
- Private Insurance: 38.3%
- Medicaid: 9.8%
- Government/Self-Pay: 4.0%

### High-Risk Categories
- Sepsis Mortality: 266 deaths
- Pneumonia Mortality: 263 deaths
- Intracranial Hemorrhage: 230 deaths
- Emergency Medicare Deaths: 3,681 (15.6% of Medicare ER admissions)

## Next Steps

1. **Pydantic Schema Validation**: Define data models for admission records
2. **Ray Distributed Processing**: Build readmission prediction models
3. **Temporal Workflow Orchestration**: Implement patient care coordination workflows
4. **PyIceberg Data Lake**: Set up versioned data storage with ACID transactions

## Execution Instructions

```bash
# Run basic processing
python admission_daft_processing.py

# Run advanced analytics
python admission_daft_advanced.py

# Outputs will be in:
# - output/daft_processed/
# - output/daft_advanced/
```

## File Structure

```
frameworks/
├── Dataset/
│   └── ADMISSIONS.csv
├── admission_daft_processing.py
├── admission_daft_advanced.py
├── output/
│   ├── daft_processed/
│   │   ├── admissions_full.parquet/
│   │   ├── admission_type_stats.parquet/
│   │   ├── insurance_stats.parquet/
│   │   ├── emergency_analysis.parquet/
│   │   └── admissions_enriched.parquet/
│   └── daft_advanced/
│       ├── readmission_risk.parquet/
│       ├── er_patterns.parquet/
│       ├── high_risk_diagnoses.parquet/
│       └── discharge_patterns.parquet/
└── ADMISSION_DAFT_PROCESSING.md
```
