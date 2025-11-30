
import daft
import pyarrow as pa
import pyarrow.csv as csv
import pyarrow.parquet as pq
import pandas as pd
from datetime import datetime

# Load NDJSON data into Daft DataFrame
df = daft.read_json("Dataset/MimicEncounter.ndjson")

print("Loading MIMIC Encounter data...")
print("First few rows:")
df.select(daft.col("id"), daft.col("resourceType"), daft.col("status")).show(3)

# Extract key fields from nested FHIR structure using struct notation
# Access period timestamps directly as strings without parsing
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
print("\nWriting parquet files...")
df.write_parquet("output/encounters_processed.parquet")
encounter_stats.write_parquet("output/encounter_statistics.parquet")
location_df.write_parquet("output/encounter_locations.parquet")
high_priority_encounters.write_parquet("output/high_priority_encounters.parquet")

print("\nParquet files created successfully!")
print("- output/encounters_processed.parquet")
print("- output/encounter_statistics.parquet")
print("- output/encounter_locations.parquet")
print("- output/high_priority_encounters.parquet")

# Display statistics
print("\nProcessed Encounter Schema:")
print(f"Total encounters: {df.count_rows()}")
print(f"\nEncounter class distribution:")
encounter_stats.show()
