import ray
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import pickle
from pydantic import BaseModel, Field
from dataclasses import dataclass
import daft

# Initialize Ray cluster
ray.init(ignore_reinit_error=True)

# ============================================================================
# Data Models
# ============================================================================

@dataclass
class AdmissionRecord:
    """Structured admission record for processing"""
    hadm_id: int
    subject_id: int
    admit_time: str
    discharge_time: str
    admission_type: str
    diagnosis: str
    hospital_expire_flag: int
    ethnicity: str
    marital_status: str

@dataclass
class FeatureVector:
    """Computed feature vector for a patient admission"""
    hadm_id: int
    subject_id: int
    length_of_stay: float
    admission_hour: int
    is_emergency: int
    mortality_risk: float
    readmission_flag: int
    features: Dict[str, float]

@dataclass
class BedAllocationPlan:
    """Bed allocation recommendation"""
    facility_id: str
    total_beds: int
    occupied_beds: int
    available_beds: int
    predicted_admits_24h: int
    utilization_rate: float
    recommendations: List[str]

# ============================================================================
# Ray Remote Tasks - Feature Engineering
# ============================================================================

@ray.remote
def extract_admission_features(admission_batch: List[Dict]) -> List[FeatureVector]:
    """
    Extract features from a batch of admission records.
    Distributed task for feature engineering across clusters.
    """
    features_list = []
    
    for admission in admission_batch:
        try:
            # Validate required fields exist
            if not admission or 'admittime' not in admission or 'dischtime' not in admission:
                continue
            
            # Handle None/NaN values
            if pd.isna(admission.get('admittime')) or pd.isna(admission.get('dischtime')):
                continue
            
            admit_dt = datetime.fromisoformat(str(admission['admittime']).replace(' ', 'T'))
            discharge_dt = datetime.fromisoformat(str(admission['dischtime']).replace(' ', 'T'))
            
            length_of_stay = (discharge_dt - admit_dt).days
            admission_hour = admit_dt.hour
            is_emergency = 1 if str(admission.get('admission_type', '')).upper() == 'EMERGENCY' else 0
            
            feature_vec = FeatureVector(
                hadm_id=int(admission.get('hadm_id', 0)),
                subject_id=int(admission.get('subject_id', 0)),
                length_of_stay=max(0, length_of_stay),
                admission_hour=admission_hour,
                is_emergency=is_emergency,
                mortality_risk=float(admission.get('hospital_expire_flag', 0)),
                readmission_flag=0,
                features={
                    'length_of_stay': float(max(0, length_of_stay)),
                    'admission_hour': float(admission_hour),
                    'is_emergency': float(is_emergency),
                    'mortality_risk': float(admission.get('hospital_expire_flag', 0)),
                    'admission_weekday': float(admit_dt.weekday()),
                }
            )
            features_list.append(feature_vec)
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            # Silently skip malformed records
            continue
    
    return features_list


@ray.remote
def compute_patient_statistics(patient_admissions: List[Dict]) -> Dict:
    """
    Compute aggregate statistics for a single patient.
    Used for readmission risk and pattern analysis.
    """
    if not patient_admissions:
        return {}
    
    # Sort by admit time
    sorted_admits = sorted(patient_admissions, 
                          key=lambda x: x['admittime'])
    
    stats = {
        'subject_id': patient_admissions[0]['subject_id'],
        'total_admissions': len(patient_admissions),
        'emergency_admissions': sum(1 for a in patient_admissions 
                                   if a['admission_type'] == 'EMERGENCY'),
        'mortality_count': sum(1 for a in patient_admissions 
                              if a['hospital_expire_flag'] == 1),
        'average_los': np.mean([
            (datetime.fromisoformat(a['dischtime'].replace(' ', 'T')) - 
             datetime.fromisoformat(a['admittime'].replace(' ', 'T'))).days
            for a in patient_admissions
        ]),
        'readmission_rate': 0.0,
    }
    
    # Compute readmission intervals
    if len(sorted_admits) > 1:
        readmission_intervals = []
        for i in range(len(sorted_admits) - 1):
            curr_discharge = datetime.fromisoformat(
                sorted_admits[i]['dischtime'].replace(' ', 'T'))
            next_admit = datetime.fromisoformat(
                sorted_admits[i+1]['admittime'].replace(' ', 'T'))
            interval_days = (next_admit - curr_discharge).days
            if interval_days <= 30:  # 30-day readmission
                readmission_intervals.append(interval_days)
        
        stats['readmission_rate'] = len(readmission_intervals) / len(sorted_admits)
        stats['readmission_intervals'] = readmission_intervals
    
    return stats


# ============================================================================
# Ray Remote Tasks - Anomaly Detection
# ============================================================================

@ray.remote
def detect_admission_anomalies(feature_batch: List[FeatureVector]) -> Dict:
    """
    Detect anomalous admission patterns using statistical methods.
    Distributed anomaly detection across clusters.
    """
    anomalies = {
        'unusual_los': [],
        'unusual_timing': [],
        'high_risk': [],
        'batch_size': len(feature_batch),
    }
    
    # Extract metrics for statistical analysis
    los_values = [f.length_of_stay for f in feature_batch if f.length_of_stay > 2]
    mortality_rates = [f.mortality_risk for f in feature_batch]
    
    if los_values:
        los_mean = np.mean(los_values)
        los_std = np.std(los_values)
        los_threshold = los_mean + (3 * los_std)
        
        # Flag unusually long stays
        anomalies['unusual_los'] = [
            f.hadm_id for f in feature_batch 
            if f.length_of_stay > los_threshold
        ]
    
    # Detect high-risk admissions
    high_mortality_threshold = 0.7
    anomalies['high_risk'] = [
        f.hadm_id for f in feature_batch 
        if f.mortality_risk > high_mortality_threshold
    ]
    
    # Detect unusual admission timing (off-hours)
    off_hours = [f.hadm_id for f in feature_batch 
                 if f.admission_hour < 6 or f.admission_hour > 23]
    anomalies['unusual_timing'] = off_hours
    
    return anomalies


@ray.remote
def detect_resource_anomalies(bed_allocation: Dict) -> List[str]:
    """
    Detect anomalies in bed utilization and resource allocation.
    """
    alerts = []
    
    utilization = bed_allocation.get('utilization_rate', 0)
    available = bed_allocation.get('available_beds', 0)
    
    if utilization > 0.95:
        alerts.append(f"CRITICAL: Bed utilization at {utilization*100:.1f}%")
    elif utilization > 0.85:
        alerts.append(f"WARNING: High bed utilization at {utilization*100:.1f}%")
    
    if available < 5:
        alerts.append(f"ALERT: Only {available} beds available")
    
    return alerts


# ============================================================================
# Ray Remote Tasks - Bed Allocation
# ============================================================================

@ray.remote
def predict_daily_admissions(historical_data: List[Dict], 
                           facility_id: str) -> Dict:
    """
    Predict admission volume for next 24 hours using historical patterns.
    """
    current_day = datetime.now().strftime('%A')
    current_hour = datetime.now().hour
    
    # Filter historical data for same day of week and time
    similar_periods = [
        d for d in historical_data
        if datetime.fromisoformat(d['admittime'].replace(' ', 'T')).strftime('%A') == current_day
    ]
    
    predictions = {
        'facility_id': facility_id,
        'predicted_24h_admissions': len(similar_periods) if similar_periods else 5,
        'predicted_emergency': sum(1 for d in similar_periods 
                                   if d['admission_type'] == 'EMERGENCY'),
        'predicted_elective': sum(1 for d in similar_periods 
                                 if d['admission_type'] == 'ELECTIVE'),
        'confidence': 0.75 if similar_periods else 0.3,
    }
    
    return predictions


@ray.remote
def optimize_bed_allocation(facility_data: Dict, 
                          admission_forecast: Dict) -> BedAllocationPlan:
    """
    Optimize bed allocation based on predicted admissions and current state.
    """
    total_beds = facility_data.get('total_beds', 100)
    currently_occupied = facility_data.get('occupied_beds', 75)
    available = total_beds - currently_occupied
    
    predicted_admits = admission_forecast.get('predicted_24h_admissions', 0)
    utilization_rate = currently_occupied / total_beds
    
    recommendations = []
    
    # Generate recommendations
    if available < predicted_admits * 1.5:
        recommendations.append("URGENT: Prepare for bed shortage - consider early discharge")
        recommendations.append("Activate surge capacity protocols")
    
    if utilization_rate > 0.9:
        recommendations.append("HIGH OCCUPANCY: Expedite non-urgent discharges")
        recommendations.append("Review ICU bed availability")
    
    if available > total_beds * 0.3:
        recommendations.append("Adequate bed availability - routine operations")
    
    plan = BedAllocationPlan(
        facility_id=facility_data.get('facility_id', 'UNKNOWN'),
        total_beds=total_beds,
        occupied_beds=currently_occupied,
        available_beds=available,
        predicted_admits_24h=predicted_admits,
        utilization_rate=utilization_rate,
        recommendations=recommendations,
    )
    
    return plan


# ============================================================================
# Ray Remote Tasks - Model Inference
# ============================================================================

@ray.remote
def predict_patient_outcomes(feature_batch: List[FeatureVector]) -> Dict:
    """
    Predict patient outcomes (LOS, mortality) using distributed inference.
    """
    predictions = {
        'total_predictions': len(feature_batch),
        'high_risk_patients': [],
        'long_stay_predictions': [],
        'predicted_mortality': 0.0,
    }
    
    mortality_scores = []
    los_predictions = []
    
    for feature in feature_batch:
        # Simple model: higher emergency + high mortality risk = high overall risk
        risk_score = (feature.is_emergency * 0.4 + 
                     feature.mortality_risk * 0.6)
        
        if risk_score > 0.5:
            predictions['high_risk_patients'].append({
                'hadm_id': feature.hadm_id,
                'risk_score': float(risk_score),
            })
        
        mortality_scores.append(feature.mortality_risk)
        
        # Predict LOS (simple linear model)
        predicted_los = (5 + 
                        feature.is_emergency * 2 + 
                        feature.mortality_risk * 10)
        
        if predicted_los > 10:
            los_predictions.append({
                'hadm_id': feature.hadm_id,
                'predicted_los': float(predicted_los),
            })
    
    predictions['long_stay_predictions'] = los_predictions
    predictions['predicted_mortality'] = float(np.mean(mortality_scores)) if mortality_scores else 0.0
    
    return predictions


@ray.remote
def score_admission_priority(feature: FeatureVector) -> Dict:
    """
    Score admission priority for triage and bed allocation.
    """
    priority_score = 0.0
    
    # Emergency admissions get priority
    if feature.is_emergency:
        priority_score += 40
    
    # High mortality risk
    if feature.mortality_risk > 0.5:
        priority_score += 30
    
    # Off-hours admission (higher intervention needed)
    if feature.admission_hour < 6 or feature.admission_hour > 22:
        priority_score += 15
    
    # Normalize to 0-100
    priority_score = min(100, max(0, priority_score))
    
    priority_level = 'CRITICAL' if priority_score >= 80 else (
                    'HIGH' if priority_score >= 60 else (
                    'MEDIUM' if priority_score >= 40 else 'LOW'))
    
    return {
        'hadm_id': feature.hadm_id,
        'priority_score': float(priority_score),
        'priority_level': priority_level,
    }


# ============================================================================
# Ray Aggregation Tasks
# ============================================================================

@ray.remote
def aggregate_features(feature_lists: List[List[FeatureVector]]) -> pd.DataFrame:
    """Aggregate feature vectors from multiple workers into a DataFrame"""
    all_features = []
    for feature_list in feature_lists:
        all_features.extend(feature_list)
    
    records = []
    for f in all_features:
        record = {
            'hadm_id': f.hadm_id,
            'subject_id': f.subject_id,
            'length_of_stay': f.length_of_stay,
            'admission_hour': f.admission_hour,
            'is_emergency': f.is_emergency,
            'mortality_risk': f.mortality_risk,
        }
        record.update(f.features)
        records.append(record)
    
    return pd.DataFrame(records)


@ray.remote
def aggregate_anomalies(anomaly_results: List[Dict]) -> Dict:
    """Aggregate anomalies detected across all workers"""
    aggregated = {
        'total_batches': len(anomaly_results),
        'all_unusual_los': [],
        'all_unusual_timing': [],
        'all_high_risk': [],
        'summary_statistics': {},
    }
    
    for result in anomaly_results:
        aggregated['all_unusual_los'].extend(result.get('unusual_los', []))
        aggregated['all_unusual_timing'].extend(result.get('unusual_timing', []))
        aggregated['all_high_risk'].extend(result.get('high_risk', []))
    
    aggregated['summary_statistics'] = {
        'total_unusual_los': len(set(aggregated['all_unusual_los'])),
        'total_high_risk': len(set(aggregated['all_high_risk'])),
        'total_off_hours': len(set(aggregated['all_unusual_timing'])),
    }
    
    return aggregated


@ray.remote
def aggregate_predictions(prediction_results: List[Dict]) -> Dict:
    """Aggregate predictions from all workers"""
    aggregated = {
        'total_predictions': 0,
        'total_high_risk': 0,
        'total_long_stay': 0,
        'average_mortality_risk': 0.0,
        'high_risk_summary': [],
    }
    
    mortality_scores = []
    
    for result in prediction_results:
        aggregated['total_predictions'] += result.get('total_predictions', 0)
        aggregated['total_high_risk'] += len(result.get('high_risk_patients', []))
        aggregated['total_long_stay'] += len(result.get('long_stay_predictions', []))
        
        if result.get('predicted_mortality'):
            mortality_scores.append(result['predicted_mortality'])
        
        aggregated['high_risk_summary'].extend(result.get('high_risk_patients', []))
    
    aggregated['average_mortality_risk'] = (
        np.mean(mortality_scores) if mortality_scores else 0.0
    )
    
    return aggregated


# ============================================================================
# Main Distributed Pipeline
# ============================================================================

def process_admissions_distributed(df: pd.DataFrame, batch_size: int = 100):
    """
    Main distributed processing pipeline using Ray.
    """
    print(f"Starting distributed processing of {len(df)} admissions")
    
    # Standardize column names to lowercase for consistency
    df.columns = df.columns.str.lower()
    
    # Remove rows with missing critical fields
    critical_fields = ['admittime', 'dischtime', 'hadm_id', 'subject_id']
    df = df.dropna(subset=critical_fields)
    print(f"After removing missing critical fields: {len(df)} admissions")
    
    # Convert dataframe to dict records
    records = df.to_dict('records')
    
    # Create batches
    batches = [records[i:i+batch_size] for i in range(0, len(records), batch_size)]
    print(f"Created {len(batches)} batches of size {batch_size}")
    
    # ============================================================================
    # Stage 1: Distributed Feature Extraction
    # ============================================================================
    print("\n[Stage 1/4] Extracting Features...")
    feature_futures = [extract_admission_features.remote(batch) for batch in batches]
    feature_results = ray.get(feature_futures)
    all_features = [f for batch in feature_results for f in batch]
    print(f"✓ Extracted {len(all_features)} features")
    
    # ============================================================================
    # Stage 2: Distributed Anomaly Detection
    # ============================================================================
    print("\n[Stage 2/4] Detecting Anomalies...")
    feature_batches = [all_features[i:i+batch_size] 
                      for i in range(0, len(all_features), batch_size)]
    
    anomaly_futures = [detect_admission_anomalies.remote(batch) 
                      for batch in feature_batches]
    anomaly_results = ray.get(anomaly_futures)
    anomaly_summary = ray.get(aggregate_anomalies.remote(anomaly_results))
    print(f"✓ Anomalies Detected: {anomaly_summary['summary_statistics']}")
    
    # ============================================================================
    # Stage 3: Distributed Model Inference
    # ============================================================================
    print("\n[Stage 3/4] Running Predictions...")
    inference_futures = [predict_patient_outcomes.remote(batch) 
                        for batch in feature_batches]
    inference_results = ray.get(inference_futures)
    prediction_summary = ray.get(aggregate_predictions.remote(inference_results))
    print(f"✓ Predictions Complete")
    
    # ============================================================================
    # Stage 4: Priority Scoring (Individual)
    # ============================================================================
    print("\n[Stage 4/4] Scoring Priorities...")
    priority_futures = [score_admission_priority.remote(feature) 
                       for feature in all_features[:10]]
    priority_scores = ray.get(priority_futures)
    print(f"✓ Priority Scores Calculated")
    
    # ============================================================================
    # Results Summary
    # ============================================================================
    return {
        'total_processed': len(records),
        'batches_processed': len(batches),
        'features_extracted': len(all_features),
        'anomalies': anomaly_summary,
        'predictions': prediction_summary,
        'priority_scores': priority_scores,
    }


if __name__ == "__main__":
    # Example usage
    print("Ray Distributed Processing System Initialized")
    print(f"Ray nodes: {ray.nodes()}")
    
    # Shutdown Ray when done
    # ray.shutdown()
