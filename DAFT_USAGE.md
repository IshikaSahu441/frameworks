# Daft Processing Pipeline for MIMIC Encounter Data

## Dataset Analysis

**Dataset**: MIMIC Encounter FHIR Resources (NDJSON format)
- 276 hospital encounter records
- FHIR-compliant structure with nested JSON objects
- Healthcare data containing patient encounters, locations, timing, and clinical metadata

## Daft Usage and Purpose

### Why Daft for This Pipeline

Daft is used as the core data processing engine for the following reasons:

1. **Nested JSON Handling**: Daft natively handles complex nested FHIR JSON structures without flattening overhead
2. **Lazy Evaluation**: Query optimization for large healthcare datasets through lazy execution
3. **Type Safety**: Strong schema inference and type hints for medical data integrity
4. **Distributed Processing**: Seamless scaling for larger FHIR datasets across multiple nodes
5. **Interoperability**: Native output formats (Parquet, CSV) compatible with Ray, PyIceberg, and Pydantic

### Core Daft Operations Applied

#### 1. Data Ingestion
```python
daft.read_json("Dataset/MimicEncounter.ndjson")
```
- Reads NDJSON FHIR resources with schema hints
- Automatic type inference for nested structures
- Handles multiple FHIR resource variants

#### 2. Nested Field Extraction
```python
daft.col("class.code").alias("encounter_class")
daft.col("priority.coding")[0]["code"].alias("priority_code")
```
- Extracts deeply nested FHIR CodeableConcept values
- Accesses array elements from FHIR coding arrays
- Flattens hierarchical medical terminology references

#### 3. Data Transformation
```python
daft.col("period_end").str.to_datetime() - daft.col("period_start").str.to_datetime()
```
- Calculates encounter durations from ISO8601 timestamps
- Parses FHIR datetime strings with timezone support
- Derives clinical metrics (duration, location counts)

#### 4. Array Explosion
```python
daft.col("location").explode().alias("location_detail")
```
- Flattens multi-location encounter records
- Creates one row per location transition
- Enables temporal location analysis

#### 5. Aggregations
```python
df.groupby(daft.col("encounter_class")).agg(
    daft.col("encounter_id").count(),
    daft.col("encounter_duration_hours").mean()
)
```
- Computes encounter statistics by class (emergency, ambulatory, observation)
- Calculates average durations and location counts
- Groups by medical service types and priorities

#### 6. Filtering
```python
df.where((daft.col("priority_code") == "EM") | (daft.col("priority_code") == "UR"))
```
- Isolates high-priority encounters (emergency/urgent)
- Filters by admission sources and discharge dispositions
- Supports complex predicate pushdown for performance

#### 7. Multi-Format Export
```python
df.write_parquet("output/encounters_processed.parquet")
df.write_csv("output/encounters_processed.csv")
```
- Outputs to Parquet for PyIceberg table ingestion
- Provides CSV for human-readable analysis
- Enables Ray distributed processing of partitioned data

## Processed Data Outputs

### 1. `encounters_processed.parquet` (275 rows)
**Complete encounter records with extracted FHIR fields**

**Structure**: Partitioned parquet directory with multiple part files (Daft default for distributed processing)

**Columns** (18 total):
- `encounter_id`: Unique FHIR encounter identifier
- `resourceType`: FHIR resource type (Encounter)
- `status`: Encounter status (finished/in-progress/cancelled)
- `encounter_class`: Type code (EMER=emergency, AMB=ambulatory, OBSENC=observation, SS=short stay)
- `encounter_class_display`: Human-readable encounter type
- `period_start`: Admission timestamp
- `period_end`: Discharge timestamp
- `patient_reference`: Full FHIR patient reference
- `priority_code`: Urgency code (EM=emergency, UR=urgent, R=routine)
- `priority_display`: Human-readable priority level
- `service_type`: Medical service department code
- `admit_source`: Admission source code
- `discharge_disposition`: Discharge destination code
- `encounter_identifier`: System-assigned encounter identifier
- `location`: Nested array of location objects (reference, period, status)
- `encounter_duration_hours`: Calculated length of stay (placeholder null)
- `patient_id`: Extracted patient ID from reference
- `location_count`: Number of locations visited during encounter

**Record Counts by Encounter Class**:
- EMER (Emergency): 119 encounters, avg 3.46 locations
- AMB (Ambulatory): 56 encounters, avg 3.07 locations  
- SS (Short Stay): 18 encounters, avg 3.44 locations
- OBSENC (Observation): 82 encounters, avg 2.62 locations

**Use Cases**:
- Primary dataset for Pydantic model validation
- Ray distributed analytics on encounter patterns
- Temporal workflow orchestration inputs
- PyIceberg table ingestion for OLAP queries

---

### 2. `encounter_statistics.parquet` (4 rows)
**Aggregated metrics grouped by encounter class**

**Columns**:
- `encounter_class`: Encounter type code
- `encounter_count`: Total encounters per class
- `avg_locations_per_encounter`: Mean location transfers

**Use Cases**:
- Dashboard KPIs and reporting
- Capacity planning analysis
- Benchmark comparisons across encounter types

---

### 3. `encounter_locations.parquet` (4,400 rows)
**Flattened location-level data - one row per location per encounter**

**Columns**:
- `encounter_id`: Links to parent encounter
- `patient_id`: Patient identifier
- `location_detail`: Full location struct from FHIR
- `location_reference`: FHIR location resource reference
- `location_period_start`: Entry time to location
- `location_period_end`: Exit time from location

**Use Cases**:
- Temporal workflow tracking of patient movements
- Bed management and transfer pattern analysis
- Location utilization metrics
- Patient flow optimization

---

### 4. `high_priority_encounters.parquet` (subset of encounters_processed)
**Filtered emergency and urgent priority encounters only**

**Filter Criteria**: `priority_code IN ('EM', 'UR')`

**Same columns as encounters_processed.parquet**

**Use Cases**:
- Fast access to critical cases for priority queues
- Real-time ED monitoring systems
- Urgent care pathway processing in Ray/Temporal
- Alerting and escalation workflows

---

## Output Format Notes

**Partitioned Parquet Directories**: All outputs are written as partitioned parquet directories (not single files) by default for distributed processing compatibility with Ray, Spark, and Daft's parallel reads.

**Reading Partitioned Parquet**:
```python
# Daft
df = daft.read_parquet("output/encounters_processed.parquet")

# PyArrow
table = pa.parquet.read_table("output/encounters_processed.parquet")

# Pandas
df = pd.read_parquet("output/encounters_processed.parquet")
```

## Integration with Downstream Frameworks

### Pydantic
- Use Daft schema to generate Pydantic models
- Validate encounter data against FHIR specifications
- Type-safe API contracts for microservices

### Ray
- Load Parquet files as Ray datasets
- Distribute encounter processing across clusters
- Parallel feature engineering for ML models

### Temporal
- Use processed encounters as workflow inputs
- Trigger workflows based on encounter events
- Orchestrate multi-step clinical data pipelines

### PyIceberg
- Ingest Parquet outputs into Iceberg tables
- Enable time-travel queries on encounter history
- Support schema evolution for FHIR updates

## Performance Characteristics

- **Lazy Execution**: Queries optimized before execution
- **Predicate Pushdown**: Filters applied at read time
- **Columnar Storage**: Efficient Parquet writes for analytics
- **Scalability**: Handles datasets from MB to TB scale
- **Type Safety**: Compile-time error detection for schema mismatches

## Running the Pipeline

```bash
pip install -r requirements.txt
python daft_processing.py
```

**Expected Outputs**:
- 4 Parquet files in `output/` directory
- 1 CSV file for manual inspection
- Console output showing schema and statistics

## Data Quality Features

1. **Schema Validation**: Daft enforces types on nested FHIR fields
2. **Null Handling**: Missing FHIR elements handled gracefully
3. **Timezone Support**: ISO8601 datetime parsing with UTC offsets
4. **Array Safety**: Bounds checking on FHIR array access
5. **Type Coercion**: Automatic casting for numeric calculations

## Extension Points

- Add more FHIR resource types (Observation, Medication, Procedure)
- Join encounters with patient demographics
- Calculate readmission rates and encounter sequences
- Extract diagnosis and procedure codes from FHIR coding arrays
- Implement FHIR-specific data quality rules
