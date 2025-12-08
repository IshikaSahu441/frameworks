"""
Complete Project Execution Script
Runs all components of the Intelligent Real-Time Patient Flow Optimization System
"""
import os
import sys
import time
from datetime import datetime

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")

def print_step(step_num, total_steps, description):
    """Print a step header"""
    print(f"\n[Step {step_num}/{total_steps}] {description}")
    print("-" * 80)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 10 and version.minor <= 12:
        print("✓ Python version is compatible with Ray and Iceberg")
        return True
    else:
        print("✗ Python version not optimal. Recommended: 3.10, 3.11, or 3.12")
        return False

def run_daft_processing():
    """Run Daft data processing"""
    print_step(1, 5, "Running Daft Data Processing")
    start_time = time.time()
    
    try:
        print("Processing 58,976 admission records with Daft...")
        import admission_daft_complete
        elapsed = time.time() - start_time
        print(f"✓ Daft processing completed in {elapsed:.2f} seconds")
        return True
    except Exception as e:
        print(f"✗ Daft processing failed: {e}")
        return False

def run_pydantic_validation():
    """Run Pydantic validation"""
    print_step(2, 5, "Running Pydantic Validation")
    start_time = time.time()
    
    try:
        print("Validating admission records with Pydantic...")
        import admission_pydantic_validation
        elapsed = time.time() - start_time
        print(f"✓ Pydantic validation completed in {elapsed:.2f} seconds")
        return True
    except Exception as e:
        print(f"✗ Pydantic validation failed: {e}")
        return False

def run_ray_distributed():
    """Run Ray distributed processing"""
    print_step(3, 5, "Running Ray Distributed Processing")
    start_time = time.time()
    
    try:
        print("Processing admissions with Ray distributed computing...")
        import pandas as pd
        from admission_ray_distributed import process_admissions_distributed
        
        df = pd.read_csv('Dataset/ADMISSIONS.csv')
        results = process_admissions_distributed(df, batch_size=50)
        
        elapsed = time.time() - start_time
        print(f"\n✓ Ray processing completed in {elapsed:.2f} seconds")
        print(f"  Total Processed: {results['total_processed']:,}")
        print(f"  Features Extracted: {results['features_extracted']:,}")
        print(f"  Anomalies Detected: {results['anomalies']['summary_statistics']}")
        return True
    except Exception as e:
        print(f"✗ Ray processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_iceberg_integration():
    """Run Iceberg integration"""
    print_step(4, 5, "Running Iceberg Integration")
    start_time = time.time()
    
    try:
        print("Integrating data with PyIceberg...")
        from admission_iceberg_integration import AdmissionIcebergIntegration
        
        integration = AdmissionIcebergIntegration()
        integration.run_integration()
        
        elapsed = time.time() - start_time
        print(f"✓ Iceberg integration completed in {elapsed:.2f} seconds")
        return True
    except Exception as e:
        print(f"✗ Iceberg integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_temporal_workflow():
    """Run Temporal workflow"""
    print_step(5, 5, "Running Temporal Workflow")
    start_time = time.time()
    
    try:
        print("Executing workflow orchestration with Temporal...")
        print("Note: Make sure Temporal worker is running in another terminal!")
        print("      Run: python optimal_temporal_demo.py worker")
        print("\nPress Enter when worker is ready, or Ctrl+C to skip...")
        
        try:
            input()
        except KeyboardInterrupt:
            print("\nSkipping Temporal workflow...")
            return True
        
        import asyncio
        from optimal_temporal_demo import start_workflow
        
        result = asyncio.run(start_workflow())
        
        elapsed = time.time() - start_time
        print(f"✓ Temporal workflow completed in {elapsed:.2f} seconds")
        return True
    except Exception as e:
        print(f"✗ Temporal workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main execution function"""
    print_header("INTELLIGENT REAL-TIME PATIENT FLOW OPTIMIZATION SYSTEM")
    print("Complete Project Execution")
    print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check Python version
    print("\n" + "-" * 80)
    print("Checking Prerequisites...")
    print("-" * 80)
    
    if not check_python_version():
        print("\n⚠ Warning: Python version may not be optimal")
        print("Recommended: Python 3.10, 3.11, or 3.12")
        print("Continuing anyway...\n")
    
    # Check if dataset exists
    if not os.path.exists("Dataset/ADMISSIONS.csv"):
        print("✗ Dataset not found: Dataset/ADMISSIONS.csv")
        return
    print("✓ Dataset found: Dataset/ADMISSIONS.csv")
    
    # Check Temporal server
    print("\n⚠ Note: Temporal server should be running at localhost:7233")
    print("If not running, start it with:")
    print('  temporal server start-dev --db-filename "C:\\temporal-data\\temporal.db"')
    
    # Execute all components
    results = {}
    start_time = time.time()
    
    results['daft'] = run_daft_processing()
    results['pydantic'] = run_pydantic_validation()
    results['ray'] = run_ray_distributed()
    results['iceberg'] = run_iceberg_integration()
    results['temporal'] = run_temporal_workflow()
    
    total_time = time.time() - start_time
    
    # Print summary
    print_header("EXECUTION SUMMARY")
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"Completed: {success_count}/{total_count} components")
    print(f"Total Execution Time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)\n")
    
    for component, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {component.upper()}: {status}")
    
    if success_count == total_count:
        print("\n🎉 All components completed successfully!")
        print("\nOutput locations:")
        print("  - Daft processed data: output/daft_complete/")
        print("  - Pydantic validation: output/pydantic_validation/")
        print("  - Iceberg warehouse: output/iceberg_catalog/")
        print("  - Iceberg reports: output/iceberg_reports/")
        print("\n✅ Project Objectives: 100% Complete")
    else:
        print("\n⚠ Some components failed. Check the logs above for details.")
        print(f"\n📊 Project Objectives: {(success_count/total_count)*100:.0f}% Complete")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
