# run_admission_system.py
import pandas as pd
from admission_ray_distributed import process_admissions_distributed
import json

# Load CSV data
df = pd.read_csv('d:\\xc\\frameworks\\Dataset\\ADMISSIONS.csv')

# Run distributed pipeline
results = process_admissions_distributed(df, batch_size=50)

# Print results with better formatting
print("\n" + "="*80)
print("INTELLIGENT PATIENT FLOW OPTIMIZATION - FINAL RESULTS")
print("="*80)

print(f"\n[PROCESSING SUMMARY]")
print(f"   Total Admissions Processed: {results['total_processed']:,}")
print(f"   Batches Processed: {results['batches_processed']}")
print(f"   Features Extracted: {results['features_extracted']:,}")

print(f"\n[WARNING] ANOMALIES DETECTED")
anomalies = results['anomalies']['summary_statistics']
print(f"   Unusual Length of Stay: {anomalies['total_unusual_los']}")
print(f"   High-Risk Patients: {anomalies['total_high_risk']}")
print(f"   Off-Hours Admissions: {anomalies['total_off_hours']}")

print(f"\n[PATIENT OUTCOME PREDICTIONS]")
predictions = results['predictions']
print(f"   Total Predictions Made: {predictions['total_predictions']:,}")
print(f"   High-Risk Patients Identified: {predictions['total_high_risk']}")
print(f"   Long-Stay Predictions: {predictions['total_long_stay']}")
print(f"   Average Mortality Risk: {predictions['average_mortality_risk']:.2%}")

print(f"\n[TOP 10 PRIORITY ADMISSIONS]")
print(f"   {'Rank':<6} {'HADM_ID':<12} {'Priority Level':<18} {'Risk Score':<12}")
print(f"   {'-'*50}")
for idx, score in enumerate(results['priority_scores'], 1):
    priority_icon = {
        'CRITICAL': '[!]',
        'HIGH': '[H]',
        'MEDIUM': '[M]',
        'LOW': '[L]'
    }.get(score['priority_level'], '[ ]')
    
    print(f"   {idx:<6} {score['hadm_id']:<12} {priority_icon} {score['priority_level']:<15} {score['priority_score']:.1f}")

print(f"\n[KEY INSIGHTS]")
print(f"   - Total High-Risk Cases: {predictions['total_high_risk']} patients need immediate intervention")
print(f"   - Long-Stay Predictions: {predictions['total_long_stay']} patients likely to stay >10 days")
print(f"   - Mortality Risk: Average {predictions['average_mortality_risk']:.2%} across admissions")
print(f"   - Resource Alert: {anomalies['total_high_risk']} patients flagged for special monitoring")

print("\n" + "="*80)
print("Analysis Complete")
print("="*80 + "\n")