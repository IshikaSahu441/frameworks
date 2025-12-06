# Pydantic Data Validation for MIMIC-IV Encounter Processing

## Overview

This implementation adds comprehensive **Pydantic data validation** to the DAFT-based MIMIC-IV FHIR Encounter data processing pipeline. Pydantic provides runtime type checking, data validation, and automatic data parsing, ensuring data quality and integrity throughout the processing workflow.

## 🎯 Key Benefits

### 1. **Data Quality Assurance**
- **Runtime validation**: All incoming data is validated against strict schemas
- **Type safety**: Automatic type checking prevents type-related errors
- **Business logic validation**: Custom validators ensure data meets domain requirements
- **Error reporting**: Detailed validation errors help identify data quality issues

### 2. **Developer Experience**
- **IDE support**: Full autocomplete and type hints in modern IDEs
- **Self-documenting code**: Models serve as living documentation
- **Reduced bugs**: Catch errors at validation time, not runtime
- **Easy refactoring**: Type hints make code changes safer

### 3. **FHIR Compliance**
- **Standard adherence**: Models follow FHIR resource structure
- **Healthcare domain validation**: Ensures medical data integrity
- **Interoperability**: Validated data ready for downstream healthcare systems

## 📋 Architecture

### Model Hierarchy

```
MimicEncounter (Root FHIR Resource)
├── Meta (metadata about the resource)
├── EncounterClass (encounter classification)
├── Period (time boundaries)
├── Reference (patient and organization references)
├── CodeableConcept (coded values)
│   └── Coding (individual codes)
├── Location[] (list of encounter locations)
│   ├── Reference (location reference)
│   └── Period (time at location)
├── Identifier[] (encounter identifiers)
└── Hospitalization (admission/discharge details)
    ├── CodeableConcept (admit source)
    └── CodeableConcept (discharge disposition)

ProcessedEncounter (Flattened for analytics)
├── encounter_id
├── patient_id
├── encounter_class
├── period_start/end
├── priority_code/display
├── location_count
└── encounter_duration_hours
```

## 🔍 Validation Features

### Field-Level Validation

#### 1. **Enum Validation**
```python
class EncounterStatus(str, Enum):
    FINISHED = "finished"
    IN_PROGRESS = "in-progress"
    # ... etc
```
Ensures only valid status values are accepted.

#### 2. **Format Validation**
```python
@field_validator('reference')
def validate_reference_format(cls, v):
    if '/' not in v:
        raise ValueError("Reference must be in format 'ResourceType/id'")
    return v
```
Validates FHIR reference format (e.g., `Patient/12345`).

#### 3. **DateTime Validation**
```python
@field_validator('start', 'end')
def validate_datetime_format(cls, v):
    datetime.fromisoformat(v.replace('Z', '+00:00'))
    return v
```
Ensures ISO 8601 datetime format compliance.

#### 4. **Numeric Constraints**
```python
location_count: int = Field(..., ge=0)
encounter_duration_hours: float = Field(..., ge=0)
```
Prevents negative values for counts and durations.

### Model-Level Validation

#### 1. **Business Logic Validation**
```python
@model_validator(mode='after')
def validate_encounter_data(self):
    if self.status == EncounterStatus.FINISHED and not self.period.end:
        raise ValueError("Finished encounters must have a period end time")
    return self
```

#### 2. **Cross-Field Validation**
```python
@model_validator(mode='after')
def validate_period_order(self):
    if self.start and self.end:
        if start_dt > end_dt:
            raise ValueError("Period start must be before end")
    return self
```

#### 3. **Collection Validation**
```python
@field_validator('coding')
def validate_coding_not_empty(cls, v):
    if not v:
        raise ValueError("CodeableConcept must have at least one coding")
    return v
```

## 📊 Data Models

### MimicEncounter

Primary model representing a FHIR Encounter resource from MIMIC-IV dataset.

**Key Fields:**
- `id`: Unique encounter identifier (UUID)
- `resourceType`: Must be "Encounter"
- `status`: Encounter status (finished, in-progress, etc.)
- `encounter_class`: Classification (emergency, ambulatory, etc.)
- `subject`: Patient reference
- `period`: Start and end times
- `location`: List of locations visited
- `priority`: Urgency level (emergency, urgent, routine)
- `hospitalization`: Admission and discharge details

**Helper Methods:**
- `get_patient_id()`: Extract patient UUID from reference
- `get_encounter_duration_hours()`: Calculate duration in hours
- `is_high_priority()`: Check if emergency or urgent
- `get_location_count()`: Count locations visited

### ProcessedEncounter

Flattened model optimized for analytics and downstream processing.

**Key Fields:**
- `encounter_id`: Extracted encounter ID
- `patient_id`: Extracted patient ID
- `encounter_class`: Flattened class code
- `period_start/end`: Flattened timestamps
- `priority_code/display`: Flattened priority
- `service_type`: Medical service type
- `admit_source`: Where patient came from
- `discharge_disposition`: Where patient went
- `location_count`: Number of locations
- `encounter_duration_hours`: Calculated duration

**Constraints:**
- No extra fields allowed (`extra = "forbid"`)
- All numeric values >= 0
- Patient ID must be valid identifier

## 🔄 Integration with DAFT

### Validation Workflow

```python
# 1. Load raw NDJSON data
with open("Dataset/MimicEncounter.ndjson") as f:
    for line in f:
        data = json.loads(line)
        
        # 2. Validate with Pydantic
        encounter = MimicEncounter(**data)
        validated_encounters.append(encounter)

# 3. Process with DAFT
df = daft.read_json("Dataset/MimicEncounter.ndjson")
# ... DAFT transformations ...

# 4. Validate processed results
processed_data = df.to_pydict()
for record in records:
    validated = ProcessedEncounter(**record)
```

### Error Handling

Validation errors are captured and logged:

```python
try:
    encounter = MimicEncounter(**data)
except ValidationError as e:
    validation_errors.append({
        "line": line_num,
        "error_type": "ValidationError",
        "message": str(e),
        "data_id": data.get("id")
    })
```

Errors are saved to `output/validation_errors.json` for review.

## 🧪 Testing

### Test Coverage

Comprehensive pytest suite covering:

1. **Model Validation**
   - Valid data acceptance
   - Invalid data rejection
   - Required field enforcement
   - Optional field handling

2. **Field Validators**
   - Enum validation
   - Format validation (references, dates)
   - Numeric constraints
   - String patterns

3. **Model Validators**
   - Business logic rules
   - Cross-field validation
   - Collection constraints

4. **Helper Methods**
   - Patient ID extraction
   - Duration calculation
   - Priority detection
   - Location counting

5. **Real Data Validation**
   - Sample records from actual dataset
   - Edge cases (multiple locations, missing fields)

### Running Tests

```bash
# Run all tests
pytest tests/test_pydantic_validation.py -v

# Run specific test class
pytest tests/test_pydantic_validation.py::TestMimicEncounter -v

# Run with coverage
pytest tests/test_pydantic_validation.py --cov=Pydantic --cov-report=html
```

### Test Statistics

- **30+ test cases** covering all models
- **100% critical path coverage** for validation logic
- **Real dataset validation** with actual MIMIC data samples

## 📈 Validation Results

When processing the MIMIC dataset, validation provides:

### Metrics Tracked

1. **Raw Data Validation**
   - Total records loaded
   - Successfully validated encounters
   - Validation errors found
   - Error types and frequencies

2. **Processed Data Validation**
   - Successfully validated processed records
   - Processing validation errors
   - Data transformation issues

3. **Output**
   - `output/validation_errors.json`: Raw data validation errors
   - `output/processing_validation_errors.json`: Processing errors
   - `output/validated_encounters.json`: Sample validated data

### Example Output

```
================================================================================
MIMIC-IV FHIR Encounter Data Processing with Pydantic Validation
================================================================================

[1/6] Loading and validating NDJSON data...
✓ Loaded 276 raw records
✓ Validated 276 encounters successfully

[2/6] Loading data into Daft DataFrame...
✓ Daft DataFrame created

[3/6] Extracting and flattening data...
✓ Data extraction complete

[4/6] Validating processed records...
✓ Validated 276 processed records

[5/6] Computing statistics and filtering...

[6/6] Writing output files...
✓ Parquet files created successfully
✓ Sample validated encounters saved

================================================================================
PROCESSING SUMMARY
================================================================================
Total encounters processed: 276
Successfully validated (raw): 276
Successfully validated (processed): 276
Validation errors (raw): 0
Validation errors (processed): 0
High priority encounters: 156
================================================================================
```

## 🛠️ Usage Examples

### Basic Validation

```python
from Pydantic.mimic_encounter_models import MimicEncounter

# Load and validate a single encounter
data = {...}  # FHIR Encounter JSON
encounter = MimicEncounter(**data)

# Access validated data
print(f"Patient: {encounter.get_patient_id()}")
print(f"Duration: {encounter.get_encounter_duration_hours()} hours")
print(f"High Priority: {encounter.is_high_priority()}")
```

### Batch Validation

```python
import json
from pydantic import ValidationError

validated = []
errors = []

with open("encounters.ndjson") as f:
    for line_num, line in enumerate(f, 1):
        try:
            data = json.loads(line)
            encounter = MimicEncounter(**data)
            validated.append(encounter)
        except ValidationError as e:
            errors.append({"line": line_num, "error": str(e)})

print(f"Validated: {len(validated)}, Errors: {len(errors)}")
```

### Exporting Validated Data

```python
# Convert to dictionary
encounter_dict = encounter.model_dump()

# Convert to JSON
encounter_json = encounter.model_dump_json(indent=2)

# Convert with alias (use FHIR field names)
encounter_fhir = encounter.model_dump(by_alias=True)
```

## 🔧 Configuration

### Model Configuration

Models use Pydantic's `Config` class for behavior:

```python
class Config:
    extra = "allow"              # Allow extra fields (for FHIR extensions)
    populate_by_name = True      # Accept both field name and alias
```

For analytics models:
```python
class Config:
    extra = "forbid"             # Strict - no extra fields
```

### Custom Validators

Add custom validation logic:

```python
@field_validator('field_name')
@classmethod
def validate_field_name(cls, v):
    # Custom validation logic
    if not is_valid(v):
        raise ValueError("Invalid value")
    return v
```

## 📦 Dependencies

Required packages (in `requirements.txt`):
```
pydantic>=2.0.0
```

For testing:
```
pytest>=7.0.0
pytest-cov>=4.0.0
```

## 🚀 Best Practices

### 1. **Validate Early**
- Validate data at ingestion point
- Catch errors before processing
- Fail fast with clear error messages

### 2. **Use Type Hints**
- Enable IDE autocomplete
- Catch type errors early
- Improve code readability

### 3. **Document Models**
- Add field descriptions
- Document validation rules
- Provide usage examples

### 4. **Test Thoroughly**
- Test valid and invalid cases
- Test edge cases
- Test real data samples

### 5. **Handle Errors Gracefully**
- Log validation errors
- Continue processing valid records
- Provide actionable error messages

## 🔮 Future Enhancements

1. **Additional Models**
   - Patient resource validation
   - Location resource validation
   - Organization resource validation

2. **Enhanced Validation**
   - Cross-resource validation
   - Temporal consistency checks
   - Medical code validation (SNOMED, ICD-10)

3. **Performance Optimization**
   - Parallel validation
   - Caching frequently validated structures
   - Lazy validation for large datasets

4. **Integration**
   - Export to FHIR servers
   - Validation REST API
   - Real-time validation streaming

## 📚 References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FHIR Encounter Resource](https://www.hl7.org/fhir/encounter.html)
- [MIMIC-IV Documentation](https://mimic.mit.edu/)
- [ISO 8601 DateTime Format](https://en.wikipedia.org/wiki/ISO_8601)

## 🤝 Contributing

When adding new validation:

1. Add validator to appropriate model
2. Add test cases for new validation
3. Update this README with new features
4. Document validation rationale

## 📄 License

This implementation follows the same license as the parent project.

---

**Last Updated**: December 2025
**Version**: 1.0.0
