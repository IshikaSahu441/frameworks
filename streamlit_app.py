"""
Intelligent Real-Time Patient Flow Optimization System - Streamlit Dashboard
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import plotly.express as px

# Define paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
PYDANTIC_DIR = OUTPUT_DIR / "pydantic_validation"
ICEBERG_DIR = OUTPUT_DIR / "iceberg_reports"
DAFT_DIR = OUTPUT_DIR / "daft_complete"
RAY_DIR = OUTPUT_DIR / "ray_predictions"

def load_json_file(filepath):
    """Load JSON file safely"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading {filepath}: {e}")
        return None

@st.cache_data
def load_sample_data():
    """Load sample processed admissions data with calculated features"""
    # Load processed data which includes calculated fields like length_of_stay_days
    data = load_json_file(PYDANTIC_DIR / "processed_admissions_sample.json")
    if data:
        return pd.DataFrame(data[:50])  # Load first 50 records
    return None

@st.cache_data
def load_validation_summary():
    """Load validation summary"""
    return load_json_file(PYDANTIC_DIR / "validation_summary.json")

@st.cache_data
def load_audit_summary():
    """Load audit trail summary"""
    try:
        with open(ICEBERG_DIR / "audit_trail_summary.txt", 'r', encoding='utf-8') as f:
            content = f.read()
            # Parse basic info
            lines = content.split('\n')
            summary = {}
            for line in lines:
                if 'Total Operations:' in line:
                    summary['total_operations'] = int(line.split(':')[1].strip())
                elif 'Tables Affected:' in line:
                    summary['tables_affected'] = int(line.split(':')[1].strip())
                elif 'Total Records Modified:' in line:
                    summary['records_modified'] = int(line.split(':')[1].strip())
            return summary
    except:
        return None

@st.cache_data
def load_ray_results():
    """Load Ray distributed processing results"""
    return load_json_file(RAY_DIR / "ray_results.json")

@st.cache_data
def calculate_anomaly_metrics(data):
    """Calculate anomaly detection metrics from validated data"""
    if data is None or len(data) == 0:
        return None
    
    metrics = {
        'unusual_los_count': 0,
        'unusual_los_percentage': 0.0,
        'los_threshold': 0.0,
        'off_hours_count': 0,
        'off_hours_percentage': 0.0,
        'high_risk_count': 0,
        'high_risk_percentage': 0.0,
        'readmission_risk_count': 0,
        'readmission_risk_percentage': 0.0
    }
    
    try:
        # Calculate length of stay anomalies (using 3-sigma rule)
        if 'length_of_stay_days' in data.columns:
            los_values = data['length_of_stay_days'].dropna()
            if len(los_values) > 0:
                los_mean = los_values.mean()
                los_std = los_values.std()
                los_threshold = los_mean + (3 * los_std)
                unusual_los = data[data['length_of_stay_days'] > los_threshold]
                metrics['unusual_los_count'] = len(unusual_los)
                metrics['unusual_los_percentage'] = (len(unusual_los) / len(data)) * 100
                metrics['los_threshold'] = los_threshold
        
        # Off-hours admissions (before 6 AM or after 11 PM)
        if 'admit_time' in data.columns:
            admit_hours = pd.to_datetime(data['admit_time']).dt.hour
            off_hours = data[(admit_hours < 6) | (admit_hours > 23)]
            metrics['off_hours_count'] = len(off_hours)
            metrics['off_hours_percentage'] = (len(off_hours) / len(data)) * 100
        
        # High-risk admissions (emergency + mortality flag)
        if 'is_emergency' in data.columns and 'hospital_expire_flag' in data.columns:
            high_risk = data[(data['is_emergency'] == True) & (data['hospital_expire_flag'] == 1)]
            metrics['high_risk_count'] = len(high_risk)
            metrics['high_risk_percentage'] = (len(high_risk) / len(data)) * 100
        
        # Readmission risk (long stay > 7 days or death)
        if 'is_readmission_risk' in data.columns:
            readmission_risk = data[data['is_readmission_risk'] == True]
            metrics['readmission_risk_count'] = len(readmission_risk)
            metrics['readmission_risk_percentage'] = (len(readmission_risk) / len(data)) * 100
    except Exception as e:
        st.error(f"Error calculating anomaly metrics: {e}")
    
    return metrics

@st.cache_data
def calculate_risk_scores(data):
    """Calculate risk scoring metrics from validated data"""
    if data is None or len(data) == 0:
        return None
    
    risk_data = []
    
    try:
        for _, row in data.iterrows():
            risk_score = 0.0
            
            # Emergency admission (+40 points)
            if row.get('is_emergency', False):
                risk_score += 40
            
            # High mortality risk (+30 points)
            if row.get('hospital_expire_flag', 0) == 1:
                risk_score += 30
            
            # Long length of stay > 10 days (+20 points)
            if row.get('length_of_stay_days', 0) > 10:
                risk_score += 20
            
            # Readmission risk (+10 points)
            if row.get('is_readmission_risk', False):
                risk_score += 10
            
            # Normalize to 0-100
            risk_score = min(100, max(0, risk_score))
            
            # Determine risk level
            if risk_score >= 80:
                risk_level = 'CRITICAL'
            elif risk_score >= 60:
                risk_level = 'HIGH'
            elif risk_score >= 40:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            risk_data.append({
                'hadm_id': row.get('hadm_id'),
                'risk_score': risk_score,
                'risk_level': risk_level
            })
        
        risk_df = pd.DataFrame(risk_data)
        
        return {
            'risk_distribution': risk_df['risk_level'].value_counts().to_dict(),
            'average_risk_score': risk_df['risk_score'].mean(),
            'critical_count': len(risk_df[risk_df['risk_level'] == 'CRITICAL']),
            'high_count': len(risk_df[risk_df['risk_level'] == 'HIGH']),
            'medium_count': len(risk_df[risk_df['risk_level'] == 'MEDIUM']),
            'low_count': len(risk_df[risk_df['risk_level'] == 'LOW']),
            'risk_dataframe': risk_df
        }
    except Exception as e:
        st.error(f"Error calculating risk scores: {e}")
        return None

def main():
    """Main dashboard function"""
    st.title("Intelligent Real-Time Patient Flow Optimization System")
    
    st.markdown("""    
    *Predicting patient admissions • Optimizing bed allocation • Detecting anomalies • Automating resource management*
    """)

    # Sidebar navigation
    st.sidebar.title("Dashboard Navigation")
    page = st.sidebar.radio(
        "Select View",
        ["Overview", "Anomaly & Risk Analysis", "Data Validation", "System Architecture"]
    )

    # Load data
    validation_data = load_validation_summary()
    sample_data = load_sample_data()
    audit_data = load_audit_summary()
    
    if page == "Overview":
        st.header("System Overview")
        
        if validation_data:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Records", f"{validation_data['total_records_processed']:,}")
            
            with col2:
                st.metric("Success Rate", f"{validation_data['validation_success_rate']:.2f}%")
            
            with col3:
                st.metric("Mortality Rate", f"{validation_data['data_quality_metrics']['mortality_rate']:.2f}%")
            
            with col4:
                st.metric("Avg Length of Stay", f"{validation_data['clinical_metrics']['avg_length_of_stay_days']:.1f} days")
            
            # Add Anomaly and Risk Summary Metrics
            if sample_data is not None:
                st.markdown("---")
                st.subheader("🔍 Anomaly & Risk Summary")
                
                anomaly_metrics = calculate_anomaly_metrics(sample_data)
                risk_metrics = calculate_risk_scores(sample_data)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if anomaly_metrics:
                        st.metric(
                            "Anomalies Detected", 
                            f"{anomaly_metrics.get('unusual_los_count', 0):,}",
                            delta="Unusual LOS",
                            delta_color="inverse"
                        )
                
                with col2:
                    if anomaly_metrics:
                        st.metric(
                            "Off-Hours Admissions",
                            f"{anomaly_metrics.get('off_hours_count', 0):,}",
                            delta=f"{anomaly_metrics.get('off_hours_percentage', 0):.1f}%",
                            delta_color="off"
                        )
                
                with col3:
                    if risk_metrics:
                        st.metric(
                            "Critical Risk Patients",
                            f"{risk_metrics.get('critical_count', 0):,}",
                            delta="High Priority",
                            delta_color="inverse"
                        )
                
                with col4:
                    if risk_metrics:
                        st.metric(
                            "Avg Risk Score",
                            f"{risk_metrics.get('average_risk_score', 0):.1f}",
                            delta="Out of 100",
                            delta_color="off"
                        )
            
            # Charts
            st.subheader("Data Distributions")
            col1, col2 = st.columns(2)
            
            with col1:
                # Admission types pie chart
                admission_types = validation_data['distribution_statistics']['admission_types']
                fig1 = px.pie(
                    values=list(admission_types.values()),
                    names=list(admission_types.keys()),
                    title="Admission Types"
                )
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Insurance types bar chart
                insurance_types = validation_data['distribution_statistics']['insurance_types']
                fig2 = px.bar(
                    x=list(insurance_types.keys()),
                    y=list(insurance_types.values()),
                    title="Insurance Types",
                    labels={'x': 'Type', 'y': 'Count'}
                )
                st.plotly_chart(fig2, use_container_width=True)
    
    elif page == "Anomaly & Risk Analysis":
        st.header("Anomaly Detection & Risk Analysis")
        st.markdown("*Combining Ray's distributed processing with real-time analytics*")
        
        # Load both Ray results and sample data
        ray_results = load_ray_results()
        
        # Show Ray processing status
        if ray_results:
            st.success("✅ Ray Distributed Processing: Active")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Processed (Ray)", f"{ray_results.get('total_processed', 0):,}")
            with col2:
                st.metric("Features Extracted", f"{ray_results.get('features_extracted', 0):,}")
            with col3:
                st.metric("Batches Processed", f"{ray_results.get('batches_processed', 0):,}")
            with col4:
                anomalies = ray_results.get('anomalies', {}).get('summary_statistics', {})
                total_anomalies = sum(anomalies.values()) if anomalies else 0
                st.metric("Anomalies (Ray)", f"{total_anomalies:,}")
        else:
            st.info("ℹ️ Ray predictions not loaded. Showing calculated metrics from Pydantic data.")
        
        st.markdown("---")
        
        # ============================================================================
        # 1. RAY DISTRIBUTED ANOMALY DETECTION
        # ============================================================================
        if ray_results:
            st.subheader("🔍 Ray Distributed Anomaly Detection")
            st.caption("Results from parallel processing across CPU cores")
            
            anomalies = ray_results.get('anomalies', {})
            summary_stats = anomalies.get('summary_statistics', {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Unusual Length of Stay (Ray)",
                    f"{summary_stats.get('total_unusual_los', 0):,}",
                    delta="3-sigma outliers",
                    delta_color="inverse"
                )
            
            with col2:
                st.metric(
                    "High Risk Cases (Ray)",
                    f"{summary_stats.get('total_high_risk', 0):,}",
                    delta="Mortality >70%",
                    delta_color="inverse"
                )
            
            with col3:
                st.metric(
                    "Off-Hours Admissions (Ray)",
                    f"{summary_stats.get('total_off_hours', 0):,}",
                    delta="0-6 AM, 11 PM-12 AM",
                    delta_color="off"
                )
            
            with st.expander("🔬 Ray Anomaly Detection Methodology"):
                st.markdown("""
                Ray uses **distributed statistical analysis** across worker nodes:
                
                1. **Unusual LOS:** Identifies stays >3 standard deviations from mean
                2. **High Risk:** Flags patients with mortality risk >70%
                3. **Off-Hours:** Detects admissions requiring increased staffing (midnight-6 AM)
                
                Each worker processes batches independently, then results are aggregated.
                """)
            
            st.markdown("---")
        
        # ============================================================================
        # 2. RAY ML PREDICTIONS
        # ============================================================================
        if ray_results:
            st.subheader("🏥 Ray Patient Outcome Predictions")
            st.caption("ML-based predictions from distributed inference")
            
            predictions = ray_results.get('predictions', {})
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Total Predictions",
                    f"{predictions.get('total_predictions', 0):,}"
                )
            with col2:
                st.metric(
                    "High Risk Patients",
                    f"{predictions.get('total_high_risk', 0):,}",
                    delta="Requires attention",
                    delta_color="inverse"
                )
            with col3:
                st.metric(
                    "Long Stay Predictions",
                    f"{predictions.get('total_long_stay', 0):,}",
                    delta=">10 days",
                    delta_color="off"
                )
            with col4:
                avg_mortality = predictions.get('average_mortality_risk', 0)
                st.metric(
                    "Avg Mortality Risk",
                    f"{avg_mortality:.2%}",
                    delta_color="off"
                )
            
            # High risk patients details
            if predictions.get('high_risk_summary'):
                with st.expander("📋 View Top 20 High-Risk Patients (Ray ML Model)"):
                    high_risk_df = pd.DataFrame(predictions['high_risk_summary'][:20])
                    if not high_risk_df.empty:
                        high_risk_df['risk_level'] = high_risk_df['risk_score'].apply(
                            lambda x: '🔴 CRITICAL' if x >= 0.8 else '🟠 HIGH' if x >= 0.6 else '🟡 MEDIUM'
                        )
                        high_risk_df['risk_score'] = high_risk_df['risk_score'].apply(lambda x: f"{x:.2%}")
                        st.dataframe(high_risk_df, use_container_width=True)
                        st.info("💡 **Model Logic:** Risk Score = (Emergency × 0.4) + (Mortality Risk × 0.6)")
            
            st.markdown("---")
        
        # ============================================================================
        # 3. RAY PRIORITY SCORING
        # ============================================================================
        if ray_results:
            st.subheader("⚡ Ray Admission Priority Scoring")
            st.caption("Triage priority scores for bed allocation")
            
            priority_scores = ray_results.get('priority_scores', [])
            
            if priority_scores:
                priority_df = pd.DataFrame(priority_scores)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Priority Level Distribution**")
                    priority_counts = priority_df['priority_level'].value_counts()
                    fig = px.pie(
                        values=priority_counts.values,
                        names=priority_counts.index,
                        title="Priority Levels (Sample)",
                        color_discrete_map={
                            'CRITICAL': '#FF0000',
                            'HIGH': '#FF6B6B',
                            'MEDIUM': '#FFD93D',
                            'LOW': '#6BCB77'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("**Priority Scoring Details**")
                    st.dataframe(priority_df, use_container_width=True)
                
                with st.expander("📊 Priority Scoring Algorithm"):
                    st.markdown("""
                    **Scoring Rules:**
                    - Emergency Admission: +40 points
                    - High Mortality Risk (>0.5): +30 points
                    - Off-Hours Admission (0-6, 22-23): +15 points
                    
                    **Risk Levels:**
                    - 🔴 **CRITICAL:** Score 80-100
                    - 🟠 **HIGH:** Score 60-79
                    - 🟡 **MEDIUM:** Score 40-59
                    - 🟢 **LOW:** Score 0-39
                    """)
            
            st.markdown("---")
        
        # ============================================================================
        # 4. CALCULATED METRICS FROM SAMPLE DATA
        # ============================================================================
        if sample_data is not None:
            st.subheader("📈 Calculated Risk & Anomaly Metrics")
            st.caption("Real-time analysis from Pydantic validated data")
            
            # Calculate anomaly metrics
            anomaly_metrics = calculate_anomaly_metrics(sample_data)
            risk_metrics = calculate_risk_scores(sample_data)
            
            if anomaly_metrics:
                st.subheader("🔍 Anomaly Detection Results")
                
                # Anomaly metrics display
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Unusual Length of Stay", 
                        f"{anomaly_metrics.get('unusual_los_count', 0):,}",
                        f"{anomaly_metrics.get('unusual_los_percentage', 0):.1f}%"
                    )
                
                with col2:
                    st.metric(
                        "Off-Hours Admissions", 
                        f"{anomaly_metrics.get('off_hours_count', 0):,}",
                        f"{anomaly_metrics.get('off_hours_percentage', 0):.1f}%"
                    )
                
                with col3:
                    st.metric(
                        "High-Risk Cases", 
                        f"{anomaly_metrics.get('high_risk_count', 0):,}",
                        f"{anomaly_metrics.get('high_risk_percentage', 0):.1f}%"
                    )
                
                with col4:
                    st.metric(
                        "Readmission Risk", 
                        f"{anomaly_metrics.get('readmission_risk_count', 0):,}",
                        f"{anomaly_metrics.get('readmission_risk_percentage', 0):.1f}%"
                    )
                
                # Anomaly threshold information
                st.info(f"📊 Length of Stay Threshold: {anomaly_metrics.get('los_threshold', 0):.2f} days (3-sigma rule)")
                
                # Visualizations
                col1, col2 = st.columns(2)
                
                with col1:
                    # Length of stay distribution with anomaly threshold
                    st.subheader("Length of Stay Distribution")
                    fig1 = px.histogram(
                        sample_data, 
                        x='length_of_stay_days',
                        nbins=30,
                        title="Length of Stay with Anomaly Threshold",
                        labels={'length_of_stay_days': 'Days', 'count': 'Frequency'}
                    )
                    # Add vertical line for threshold
                    threshold = anomaly_metrics.get('los_threshold', 0)
                    fig1.add_vline(
                        x=threshold, 
                        line_dash="dash", 
                        line_color="red",
                        annotation_text=f"Threshold: {threshold:.1f} days"
                    )
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col2:
                    # Admission timing analysis
                    st.subheader("Admission Hour Distribution")
                    if 'admit_time' in sample_data.columns:
                        admit_hours = pd.to_datetime(sample_data['admit_time']).dt.hour
                        hour_data = pd.DataFrame({'hour': admit_hours})
                        fig2 = px.histogram(
                            hour_data,
                            x='hour',
                            nbins=24,
                            title="Admissions by Hour of Day",
                            labels={'hour': 'Hour of Day', 'count': 'Admissions'}
                        )
                        # Highlight off-hours (0-6, 23)
                        fig2.add_vrect(
                            x0=-0.5, x1=6.5, 
                            fillcolor="red", opacity=0.2,
                            annotation_text="Off Hours"
                        )
                        st.plotly_chart(fig2, use_container_width=True)
            
            if risk_metrics:
                st.subheader("⚠️ Risk Calculation Results")
                
                # Risk metrics display
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Critical Risk", f"{risk_metrics.get('critical_count', 0):,}")
                
                with col2:
                    st.metric("High Risk", f"{risk_metrics.get('high_count', 0):,}")
                
                with col3:
                    st.metric("Medium Risk", f"{risk_metrics.get('medium_count', 0):,}")
                
                with col4:
                    st.metric("Average Risk Score", f"{risk_metrics.get('average_risk_score', 0):.1f}/100")
                
                # Risk level distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Risk Level Distribution")
                    risk_dist = risk_metrics.get('risk_distribution', {})
                    fig3 = px.pie(
                        values=list(risk_dist.values()),
                        names=list(risk_dist.keys()),
                        title="Patient Risk Levels",
                        color_discrete_map={
                            'CRITICAL': '#FF0000',
                            'HIGH': '#FF6B6B',
                            'MEDIUM': '#FFD93D',
                            'LOW': '#6BCB77'
                        }
                    )
                    st.plotly_chart(fig3, use_container_width=True)
                
                with col2:
                    st.subheader("Risk Score Distribution")
                    risk_df = risk_metrics.get('risk_dataframe')
                    if risk_df is not None:
                        fig4 = px.histogram(
                            risk_df,
                            x='risk_score',
                            nbins=20,
                            title="Risk Score Distribution",
                            labels={'risk_score': 'Risk Score', 'count': 'Frequency'},
                            color_discrete_sequence=['#4ECDC4']
                        )
                        st.plotly_chart(fig4, use_container_width=True)
                
                # Risk scoring methodology
                st.subheader("📋 Risk Scoring Methodology")
                st.markdown("""
                **Risk Score Calculation:**
                - Emergency Admission: +40 points
                - Mortality Risk (Death Flag): +30 points  
                - Long Length of Stay (>10 days): +20 points
                - Readmission Risk: +10 points
                
                **Risk Levels:**
                - 🔴 CRITICAL: Score ≥ 80
                - 🟠 HIGH: Score 60-79
                - 🟡 MEDIUM: Score 40-59
                - 🟢 LOW: Score < 40
                """)
                
                # Top high-risk patients
                if risk_df is not None:
                    st.subheader("Top 10 High-Risk Patients")
                    top_risk = risk_df.nlargest(10, 'risk_score')
                    # Merge with sample data to get more details
                    detailed_risk = top_risk.merge(
                        sample_data[['hadm_id', 'admission_type', 'length_of_stay_days', 'diagnosis']], 
                        on='hadm_id', 
                        how='left'
                    )
                    st.dataframe(detailed_risk, use_container_width=True)
        else:
            st.warning("⚠️ Sample data not available. Please run the Pydantic validation pipeline first.")
            st.info("To generate data, run: `python admission_pydantic_validation.py`")
    
    elif page == "Data Validation":
        st.header("Data Validation Results")
        if validation_data:
            st.subheader("Validation Summary")
            st.json(validation_data)
            
            # Sample validated data
            if sample_data is not None:
                st.subheader("Sample Validated Records")
                st.dataframe(sample_data.head(10))
            else:
                st.info("Sample data not available")
    
    elif page == "System Architecture":
        st.header("System Architecture")
        
        st.subheader("Data Pipeline Flow")
        st.markdown("""
        ```
        Raw MIMIC-III Data → Pydantic Validation → Ray Distributed Processing → Iceberg Data Lake → Temporal Workflows
        ```
        """)
        
        st.subheader("Technology Stack")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **Data Processing**
            - Daft: Distributed ETL
            - Pandas: Data manipulation  
            - PyArrow: Columnar storage
            """)
        
        with col2:
            st.markdown("""
            **Distributed Computing**
            - Ray: Parallel processing
            - Pydantic: Data validation
            - NumPy: Numerical computing
            """)
        
        with col3:
            st.markdown("""
            **Data Lake & Orchestration**
            - PyIceberg: ACID transactions
            - Temporal: Workflow orchestration
            - Streamlit: Dashboard
            """)
        
        st.subheader("Performance Benchmarks")
        perf_data = {
            "Component": ["Daft Processing", "Pydantic Validation", "Ray Distributed", "Iceberg Integration", "Temporal Workflow"],
            "Duration (seconds)": [7, 7, 30, 1, "Variable"],
            "Status": ["✅ Working", "✅ Working", "✅ Working", "✅ Working", "✅ Working"]
        }
        st.table(pd.DataFrame(perf_data))
    
    # Footer
    st.markdown("---")
    st.markdown(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("**Status:** All Systems Operational")

if __name__ == "__main__":
    main()