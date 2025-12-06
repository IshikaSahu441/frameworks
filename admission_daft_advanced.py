import daft
from daft import col
import os

print("=" * 80)
print("ADVANCED DAFT ANALYSIS: Patient Flow Optimization Features")
print("=" * 80)

print("\n[Loading] Admission records...")
df = daft.read_csv("Dataset/ADMISSIONS.csv")

print("\n[1/6] Creating Readmission Risk Features")
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

print("\n[2/6] Emergency Room Admission Patterns")
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

print("\n[3/6] High-Risk Admission Profiles")
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

print("\n[4/6] Language and Insurance Accessibility Analysis")
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

print("\n[5/6] Discharge Disposition by Admission Type")
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

print("\n[6/6] Religious and Cultural Demographics")
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

print("\n" + "=" * 80)
print("Exporting Advanced Analytics")
print("=" * 80)

os.makedirs("output/daft_advanced", exist_ok=True)

print("\n[1/4] Exporting readmission risk dataset...")
readmission_patients.write_parquet("output/daft_advanced/readmission_risk.parquet")
print("Saved: output/daft_advanced/readmission_risk.parquet")

print("\n[2/4] Exporting emergency room patterns...")
er_admissions.write_parquet("output/daft_advanced/er_patterns.parquet")
print("Saved: output/daft_advanced/er_patterns.parquet")

print("\n[3/4] Exporting high-risk profiles...")
high_risk.write_parquet("output/daft_advanced/high_risk_diagnoses.parquet")
print("Saved: output/daft_advanced/high_risk_diagnoses.parquet")

print("\n[4/4] Exporting discharge patterns...")
discharge_patterns.write_parquet("output/daft_advanced/discharge_patterns.parquet")
print("Saved: output/daft_advanced/discharge_patterns.parquet")

print("\n" + "=" * 80)
print("ADVANCED ANALYTICS COMPLETE")
print("=" * 80)
print("\nFeature sets created for:")
print("  - Readmission prediction models")
print("  - ER capacity planning")
print("  - High-risk patient identification")
print("  - Discharge planning optimization")
