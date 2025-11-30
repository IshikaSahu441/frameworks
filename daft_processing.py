
import daft
import pyarrow as pa
import pyarrow.csv as csv
import pyarrow.parquet as pq
import pandas as pd
from datetime import datetime
import json
from typing import List, Dict, Any
from pydantic import ValidationError

# Import Pydantic models for validation
from Pydantic.mimic_encounter_models import (
    MimicEncounter,
    ProcessedEncounter,
    EncounterStatus,
    ActCode,
    PriorityCode
)

print("=" * 80)
print("MIMIC-IV FHIR Encounter Data Processing with Pydantic Validation")
print("=" * 80)

# Load and validate NDJSON data
print("\n[1/6] Loading and validating NDJSON data...")
raw_data = []
validation_errors = []
validated_encounters = []

# Read raw NDJSON file
with open("Dataset/MimicEncounter.ndjson", "r") as f:
    for line_num, line in enumerate(f, 1):
        if line.strip():
            try:
                data = json.loads(line)
                raw_data.append(data)
                
                # Validate with Pydantic model
                encounter = MimicEncounter(**data)
                validated_encounters.append(encounter)
                
            except json.JSONDecodeError as e:
                validation_errors.append({
                    "line": line_num,
                    "error_type": "JSONDecodeError",
                    "message": str(e)
                })
            except ValidationError as e:
                validation_errors.append({
                    "line": line_num,
                    "error_type": "ValidationError",
                    "message": str(e),
                    "data_id": data.get("id", "unknown")
                })

print(f"✓ Loaded {len(raw_data)} raw records")
print(f"✓ Validated {len(validated_encounters)} encounters successfully")
if validation_errors:
    print(f"⚠ Found {len(validation_errors)} validation errors")
    # Save validation errors for review
    with open("output/validation_errors.json", "w") as f:
        json.dump(validation_errors, f, indent=2)
    print(f"  → Errors saved to output/validation_errors.json")

# Load NDJSON data into Daft DataFrame
print("\n[2/6] Loading data into Daft DataFrame...")
df = daft.read_json("Dataset/MimicEncounter.ndjson")

print("✓ Daft DataFrame created")
print("\nFirst few rows (before validation):")
df.select(daft.col("id"), daft.col("resourceType"), daft.col("status")).show(3)

# Extract key fields from nested FHIR structure using struct notation
# Access period timestamps directly as strings without parsing
print("\n[3/6] Extracting and flattening data...")
df_extracted = df.select(
    daft.col("id").alias("encounter_id"),
    daft.col("resourceType"),
    daft.col("status"),
    daft.col("class").struct.get("code").alias("encounter_class"),
    daft.col("class").struct.get("display").alias("encounter_class_display"),
    daft.col("period").alias("period_struct"),  # Keep as struct temporarily
    daft.col("subject").struct.get("reference").alias("patient_reference"),
    daft.col("priority").struct.get("coding")[0].struct.get("code").alias("priority_code"),
    daft.col("priority").struct.get("coding")[0].struct.get("display").alias("priority_display"),
    daft.col("serviceType").struct.get("coding")[0].struct.get("code").alias("service_type"),
    daft.col("hospitalization").struct.get("admitSource").struct.get("coding")[0].struct.get("code").alias("admit_source"),
    daft.col("hospitalization").struct.get("dischargeDisposition").struct.get("coding")[0].struct.get("code").alias("discharge_disposition"),
    daft.col("identifier")[0].struct.get("value").alias("encounter_identifier"),
    daft.col("location"),
)

# Extract period start/end after the main selection to handle them separately
df_extracted = df_extracted.with_columns({
    "period_start": daft.col("period_struct").struct.get("start"),
    "period_end": daft.col("period_struct").struct.get("end")
})

df = df_extracted.exclude("period_struct")

# Calculate encounter duration (converting datetime strings to timestamps)
# For now, keep the datetime strings as-is for easier processing downstream
df = df.with_column(
    "encounter_duration_hours",
    daft.lit(None).cast(daft.DataType.float64())  # Placeholder - will calculate downstream
)

# Extract patient ID from reference
df = df.with_column(
    "patient_id",
    daft.col("patient_reference").str.split("/")[1]
)

# Count locations per encounter
df = df.with_column(
    "location_count",
    daft.col("location").list.length()
)

print("✓ Data extraction complete")

# Validate processed records using ProcessedEncounter model
print("\n[4/6] Validating processed records with sample...")
validated_processed = []
processing_errors = []

# Validate using the original validated encounters (which we already have)
# This avoids the timezone parsing issue in DAFT's to_pydict()
for encounter in validated_encounters[:10]:  # Validate a sample
    try:
        # Extract processed data from validated encounter
        record = {
            'encounter_id': encounter.id,
            'resourceType': encounter.resourceType,
            'status': encounter.status.value,
            'encounter_class': encounter.encounter_class.code.value,
            'encounter_class_display': encounter.encounter_class.display,
            'period_start': encounter.period.start if encounter.period else None,
            'period_end': encounter.period.end if encounter.period else None,
            'patient_reference': encounter.subject.reference,
            'patient_id': encounter.get_patient_id(),
            'priority_code': encounter.priority.coding[0].code if encounter.priority else None,
            'priority_display': encounter.priority.coding[0].display if encounter.priority else None,
            'service_type': encounter.serviceType.coding[0].code if encounter.serviceType else None,
            'admit_source': encounter.hospitalization.admitSource.coding[0].code if encounter.hospitalization and encounter.hospitalization.admitSource else None,
            'discharge_disposition': encounter.hospitalization.dischargeDisposition.coding[0].code if encounter.hospitalization and encounter.hospitalization.dischargeDisposition else None,
            'encounter_identifier': encounter.identifier[0].value if encounter.identifier else None,
            'location_count': encounter.get_location_count(),
            'encounter_duration_hours': encounter.get_encounter_duration_hours(),
        }
        
        validated = ProcessedEncounter(**record)
        validated_processed.append(validated.model_dump())
    except ValidationError as e:
        processing_errors.append({
            'encounter_id': encounter.id,
            'error': str(e)
        })

print(f"✓ Validated {len(validated_processed)} processed record samples")
if processing_errors:
    print(f"⚠ Found {len(processing_errors)} processing validation errors")
    with open("output/processing_validation_errors.json", "w") as f:
        json.dump(processing_errors, f, indent=2)
    print(f"  → Errors saved to output/processing_validation_errors.json")

# Create flattened location data for location analysis
location_df = df.explode(daft.col("location")).select(
    daft.col("encounter_id"),
    daft.col("patient_id"),
    daft.col("location").alias("location_detail")
).with_columns({
    "location_reference": daft.col("location_detail").struct.get("location").struct.get("reference"),
    "location_period_start": daft.col("location_detail").struct.get("period").struct.get("start"),
    "location_period_end": daft.col("location_detail").struct.get("period").struct.get("end"),
})

# Aggregate statistics by encounter class
print("\n[5/6] Computing statistics and filtering...")
encounter_stats = df.groupby(daft.col("encounter_class")).agg(
    daft.col("encounter_id").count().alias("encounter_count"),
    daft.col("location_count").mean().alias("avg_locations_per_encounter")
)

# Filter high priority encounters
high_priority_encounters = df.where(
    (daft.col("priority_code") == "EM") | (daft.col("priority_code") == "UR")
)

# Export processed data in formats suitable for downstream frameworks
# Parquet for PyIceberg and Ray distributed processing
print("\n[6/6] Writing output files...")
print("Writing parquet files...")
df.write_parquet("output/encounters_processed.parquet")
encounter_stats.write_parquet("output/encounter_statistics.parquet")
location_df.write_parquet("output/encounter_locations.parquet")
high_priority_encounters.write_parquet("output/high_priority_encounters.parquet")

print("✓ Parquet files created successfully!")
print("  - output/encounters_processed.parquet")
print("  - output/encounter_statistics.parquet")
print("  - output/encounter_locations.parquet")
print("  - output/high_priority_encounters.parquet")

# Save validated data as JSON for inspection
print("\nWriting validated data...")
with open("output/validated_encounters.json", "w") as f:
    json.dump([e.model_dump() for e in validated_encounters[:10]], f, indent=2)
print("✓ Sample validated encounters saved to output/validated_encounters.json")

# Display statistics
print("\n" + "=" * 80)
print("PROCESSING SUMMARY")
print("=" * 80)
print(f"Total encounters processed: {df.count_rows()}")
print(f"Successfully validated (raw): {len(validated_encounters)}")
print(f"Successfully validated (processed samples): {len(validated_processed)}")
print(f"Validation errors (raw): {len(validation_errors)}")
print(f"Validation errors (processed samples): {len(processing_errors)}")
print(f"High priority encounters: {high_priority_encounters.count_rows()}")
print("=" * 80)
print(f"\nEncounter class distribution:")
encounter_stats.show()
