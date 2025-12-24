import daft
from daft import col
import os

print("=" * 80)
print("DAFT COMPREHENSIVE ANALYSIS: Patient Admission Processing")
print("Combining Basic Processing + Advanced Analytics")
print("=" * 80)

# ============================================================================
# SECTION 1: DATA LOADING AND BASIC EXPLORATION
# ============================================================================

print("\n[1/16] Loading admission records with lazy evaluation...")
df = daft.read_csv("Dataset/ADMISSIONS.csv")
print("Data loaded (lazy - not yet materialized)")
print("Schema inferred automatically")

print("\n[2/16] Dataset Schema and Sample Records")
print("-" * 80)
df.show(5)

print("\n[3/16] Computing total records...")
total_count = df.count_rows()
print(f"Total admission records: {total_count}")

print("\n[4/16] Analyzing unique patients...")
unique_patients = df.select(col("SUBJECT_ID")).distinct()
unique_count = unique_patients.count_rows()
print(f"Unique patients: {unique_count}")

# ============================================================================
# SECTION 2: BASIC STATISTICS AND DISTRIBUTIONS
# ============================================================================

print("\n[5/16] Admission Type Distribution")
print("-" * 80)
admission_stats = (
    df.groupby(col("ADMISSION_TYPE"))
    .agg(
        col("HADM_ID").count().alias("admission_count")
    )
    .sort(col("admission_count"), desc=True)
)
admission_stats.show()

print("\n[6/16] Insurance Type Analysis")
print("-" * 80)
insurance_stats = (
    df.groupby(col("INSURANCE"))
    .agg(
        col("HADM_ID").count().alias("total_admissions")
    )
    .sort(col("total_admissions"), desc=True)
)
insurance_stats.show()

print("\n[7/16] Top Admission Locations")
print("-" * 80)
location_stats = (
    df.groupby(col("ADMISSION_LOCATION"))
    .agg(
        col("HADM_ID").count().alias("count")
    )
    .sort(col("count"), desc=True)
)
location_stats.show(10)

print("\n[8/16] Top Discharge Locations")
print("-" * 80)
discharge_stats = (
    df.groupby(col("DISCHARGE_LOCATION"))
    .agg(
        col("HADM_ID").count().alias("count")
    )
    .sort(col("count"), desc=True)
)
discharge_stats.show(10)

print("\n[9/16] Hospital Mortality Analysis")
print("-" * 80)
mortality_stats = (
    df.groupby(col("HOSPITAL_EXPIRE_FLAG"))
    .agg(
        col("HADM_ID").count().alias("count")
    )
)
mortality_stats.show()

# ============================================================================
# SECTION 3: ADVANCED ANALYTICS - READMISSION AND RISK ANALYSIS
# ============================================================================

print("\n[10/16] Creating Readmission Risk Features")
print("-" * 80)

patient_admissions = (
    df.groupby(col("SUBJECT_ID"))
    .agg(
        col("HADM_ID").count().alias("total_admissions"),
        col("HOSPITAL_EXPIRE_FLAG").sum().alias("total_deaths")
    )
)

readmission_patients = (
    patient_admissions
    .where(col("total_admissions") > 1)
    .sort(col("total_admissions"), desc=True)
)

print(f"Patients with multiple admissions (readmission risk):")
readmission_patients.show(10)

print("\n[11/16] Emergency Room Admission Patterns")
print("-" * 80)

er_admissions = (
    df.where(col("ADMISSION_LOCATION") == "EMERGENCY ROOM ADMIT")
    .groupby(col("INSURANCE"), col("ETHNICITY"))
    .agg(
        col("HADM_ID").count().alias("er_count"),
        col("HOSPITAL_EXPIRE_FLAG").sum().alias("er_deaths")
    )
    .where(col("er_count") > 10)
    .sort(col("er_count"), desc=True)
)

er_admissions.show(15)

print("\n[12/16] High-Risk Diagnosis Profiles")
print("-" * 80)

high_risk = (
    df.where((col("ADMISSION_TYPE") == "EMERGENCY") & (col("HOSPITAL_EXPIRE_FLAG") == 1))
    .groupby(col("DIAGNOSIS"))
    .agg(
        col("HADM_ID").count().alias("fatal_cases")
    )
    .sort(col("fatal_cases"), desc=True)
)

high_risk.show(15)

# ============================================================================
# SECTION 4: DEMOGRAPHIC AND ACCESSIBILITY ANALYSIS
# ============================================================================

print("\n[13/16] Language and Insurance Accessibility Analysis")
print("-" * 80)

language_insurance = (
    df.groupby(col("LANGUAGE"), col("INSURANCE"))
    .agg(
        col("HADM_ID").count().alias("admission_count")
    )
    .where(col("admission_count") > 5)
    .sort(col("admission_count"), desc=True)
)

language_insurance.show(20)

print("\n[14/16] Discharge Disposition by Admission Type")
print("-" * 80)

discharge_patterns = (
    df.groupby(col("ADMISSION_TYPE"), col("DISCHARGE_LOCATION"))
    .agg(
        col("HADM_ID").count().alias("count")
    )
    .where(col("count") > 10)
    .sort(col("count"), desc=True)
)

discharge_patterns.show(20)

print("\n[15/16] Emergency Admissions by Insurance Type")
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

print("\n[16/16] Religious and Cultural Demographics")
print("-" * 80)

religion_stats = (
    df.groupby(col("RELIGION"))
    .agg(
        col("HADM_ID").count().alias("admission_count"),
        col("HOSPITAL_EXPIRE_FLAG").sum().alias("deaths")
    )
    .sort(col("admission_count"), desc=True)
)

religion_stats.show(15)

# ============================================================================
# SECTION 5: DATA ENRICHMENT AND EXPORT
# ============================================================================

print("\n" + "=" * 80)
print("Exporting Comprehensive Processed Data")
print("=" * 80)

os.makedirs("output/daft_complete", exist_ok=True)

print("\n[1/10] Exporting main admission dataset...")
df.write_parquet("output/daft_complete/admissions_full.parquet")
print("Saved: output/daft_complete/admissions_full.parquet")

print("\n[2/10] Exporting admission type statistics...")
admission_stats.write_parquet("output/daft_complete/admission_type_stats.parquet")
print("Saved: output/daft_complete/admission_type_stats.parquet")

print("\n[3/10] Exporting insurance statistics...")
insurance_stats.write_parquet("output/daft_complete/insurance_stats.parquet")
print("Saved: output/daft_complete/insurance_stats.parquet")

print("\n[4/10] Exporting emergency admission analysis...")
emergency_analysis.write_parquet("output/daft_complete/emergency_analysis.parquet")
print("Saved: output/daft_complete/emergency_analysis.parquet")

print("\n[5/10] Exporting readmission risk dataset...")
readmission_patients.write_parquet("output/daft_complete/readmission_risk.parquet")
print("Saved: output/daft_complete/readmission_risk.parquet")

print("\n[6/10] Exporting emergency room patterns...")
er_admissions.write_parquet("output/daft_complete/er_patterns.parquet")
print("Saved: output/daft_complete/er_patterns.parquet")

print("\n[7/10] Exporting high-risk diagnoses...")
high_risk.write_parquet("output/daft_complete/high_risk_diagnoses.parquet")
print("Saved: output/daft_complete/high_risk_diagnoses.parquet")

print("\n[8/10] Exporting discharge patterns...")
discharge_patterns.write_parquet("output/daft_complete/discharge_patterns.parquet")
print("Saved: output/daft_complete/discharge_patterns.parquet")

print("\n[9/10] Exporting language-insurance accessibility...")
language_insurance.write_parquet("output/daft_complete/language_insurance_access.parquet")
print("Saved: output/daft_complete/language_insurance_access.parquet")

print("\n[10/10] Creating enriched dataset with derived features...")
enriched_df = df.with_columns({
    "is_emergency": col("ADMISSION_TYPE") == "EMERGENCY",
    "is_elective": col("ADMISSION_TYPE") == "ELECTIVE",
    "has_chart_data": col("HAS_CHARTEVENTS_DATA") == 1,
    "expired": col("HOSPITAL_EXPIRE_FLAG") == 1
})

enriched_df.write_parquet("output/daft_complete/admissions_enriched.parquet")
print("Saved: output/daft_complete/admissions_enriched.parquet")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("COMPREHENSIVE DAFT PROCESSING COMPLETE")
print("=" * 80)
print("\nAll datasets processed with lazy evaluation")
print("Distributed parquet files created for downstream frameworks")
print("Memory-efficient processing completed")
print("\n📊 BASIC ANALYTICS:")
print("  ✓ Admission type distribution")
print("  ✓ Insurance coverage analysis")
print("  ✓ Location statistics (admission/discharge)")
print("  ✓ Mortality rates")
print("\n🔬 ADVANCED ANALYTICS:")
print("  ✓ Readmission risk profiling")
print("  ✓ Emergency room patterns")
print("  ✓ High-risk diagnosis identification")
print("  ✓ Language/insurance accessibility")
print("  ✓ Discharge disposition patterns")
print("  ✓ Cultural demographics")
print("\n🚀 OUTPUT FILES READY FOR:")
print("  - Pydantic: Schema validation")
print("  - Ray: Distributed ML training")
print("  - Temporal: Workflow orchestration")
print("  - Iceberg: Data lake storage")
print("\n📁 Output location: output/daft_complete/")
