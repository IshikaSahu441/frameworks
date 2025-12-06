import daft
from daft import col
import os

print("=" * 80)
print("DAFT: Distributed Data Loading and Transformation")
print("Patient Admission Dataset Processing")
print("=" * 80)

print("\n[1/10] Loading admission records with lazy evaluation...")
df = daft.read_csv("Dataset/ADMISSIONS.csv")

print("Data loaded (lazy - not yet materialized)")
print("Schema inferred automatically")

print("\n[2/10] Dataset Schema and Sample Records")
print("-" * 80)
df.show(5)

print("\n[3/10] Computing total records...")
total_count = df.count_rows()
print(f"Total admission records: {total_count}")

print("\n[4/10] Analyzing unique patients...")
unique_patients = df.select(col("SUBJECT_ID")).distinct()
unique_count = unique_patients.count_rows()
print(f"Unique patients: {unique_count}")

print("\n[5/10] Admission Type Distribution")
print("-" * 80)
admission_stats = (
    df.groupby(col("ADMISSION_TYPE"))
    .agg(
        col("HADM_ID").count().alias("admission_count")
    )
    .sort(col("admission_count"), desc=True)
)
admission_stats.show()

print("\n[6/10] Insurance Type Analysis")
print("-" * 80)
insurance_stats = (
    df.groupby(col("INSURANCE"))
    .agg(
        col("HADM_ID").count().alias("total_admissions")
    )
    .sort(col("total_admissions"), desc=True)
)
insurance_stats.show()

print("\n[7/10] Top Admission Locations")
print("-" * 80)
location_stats = (
    df.groupby(col("ADMISSION_LOCATION"))
    .agg(
        col("HADM_ID").count().alias("count")
    )
    .sort(col("count"), desc=True)
)
location_stats.show(10)

print("\n[8/10] Top Discharge Locations")
print("-" * 80)
discharge_stats = (
    df.groupby(col("DISCHARGE_LOCATION"))
    .agg(
        col("HADM_ID").count().alias("count")
    )
    .sort(col("count"), desc=True)
)
discharge_stats.show(10)

print("\n[9/10] Hospital Mortality Analysis")
print("-" * 80)
mortality_stats = (
    df.groupby(col("HOSPITAL_EXPIRE_FLAG"))
    .agg(
        col("HADM_ID").count().alias("count")
    )
)
mortality_stats.show()

print("\n[10/10] Emergency Admissions by Insurance Type")
print("-" * 80)
emergency_analysis = (
    df.where(col("ADMISSION_TYPE") == "EMERGENCY")
    .groupby(col("INSURANCE"))
    .agg(
        col("HADM_ID").count().alias("emergency_admissions"),
        col("HOSPITAL_EXPIRE_FLAG").sum().alias("deaths")
    )
    .sort(col("emergency_admissions"), desc=True)
)
emergency_analysis.show()

os.makedirs("output/daft_processed", exist_ok=True)

print("\n" + "=" * 80)
print("Exporting Processed Data (Distributed Parquet Format)")
print("=" * 80)

print("\n[1/5] Exporting main admission dataset...")
df.write_parquet("output/daft_processed/admissions_full.parquet")
print("Saved: output/daft_processed/admissions_full.parquet")

print("\n[2/5] Exporting admission type statistics...")
admission_stats.write_parquet("output/daft_processed/admission_type_stats.parquet")
print("Saved: output/daft_processed/admission_type_stats.parquet")

print("\n[3/5] Exporting insurance statistics...")
insurance_stats.write_parquet("output/daft_processed/insurance_stats.parquet")
print("Saved: output/daft_processed/insurance_stats.parquet")

print("\n[4/5] Exporting emergency admission analysis...")
emergency_analysis.write_parquet("output/daft_processed/emergency_analysis.parquet")
print("Saved: output/daft_processed/emergency_analysis.parquet")

print("\n[5/5] Creating enriched dataset with derived features...")
enriched_df = df.with_columns({
    "is_emergency": col("ADMISSION_TYPE") == "EMERGENCY",
    "is_elective": col("ADMISSION_TYPE") == "ELECTIVE",
    "has_chart_data": col("HAS_CHARTEVENTS_DATA") == 1,
    "expired": col("HOSPITAL_EXPIRE_FLAG") == 1
})

enriched_df.write_parquet("output/daft_processed/admissions_enriched.parquet")
print("Saved: output/daft_processed/admissions_enriched.parquet")

print("\n" + "=" * 80)
print("DAFT PROCESSING COMPLETE")
print("=" * 80)
print("\nAll datasets processed with lazy evaluation")
print("Distributed parquet files created for downstream frameworks")
print("Memory-efficient processing completed")
print("\nOutput files ready for:")
print("  - Pydantic: Schema validation")
print("  - Ray: Distributed ML training")
print("  - Temporal: Workflow orchestration")
print("  - Iceberg: Data lake storage")
