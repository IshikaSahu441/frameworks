"""
Start Temporal Workflow for Admission Processing
Connects to local Temporal server at localhost:7233
"""
import asyncio
from temporalio.client import Client
import temporal_workflows

async def start(csv_path: str, batch_size: int = 50):
    """Start the admission workflow"""
    print("=" * 80)
    print("TEMPORAL WORKFLOW: Starting Admission Processing")
    print("=" * 80)
    print(f"Server Address: localhost:7233")
    print(f"CSV Path: {csv_path}")
    print(f"Batch Size: {batch_size}")
    print("-" * 80)
    
    # Connect to local Temporal server
    client = await Client.connect("localhost:7233")
    print("✓ Connected to Temporal server")

    # Start workflow
    handle = await client.start_workflow(
        temporal_workflows.AdmissionWorkflow.run,
        args=[csv_path, batch_size],
        id=f"admission_workflow_{asyncio.get_event_loop().time()}",
        task_queue="admission-task-queue",
    )

    print(f"✓ Started workflow execution with id: {handle.id}")
    print("\nWaiting for workflow to complete...")
    print("-" * 80)
    
    # Wait for result
    result = await handle.result()
    
    print("\n" + "=" * 80)
    print("WORKFLOW COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print("\nWorkflow Result:")
    print(f"  Total Processed: {result.get('total_processed', 0):,}")
    print(f"  Batches Processed: {result.get('batches_processed', 0)}")
    print(f"  Features Extracted: {result.get('features_extracted', 0):,}")
    
    if 'anomalies' in result:
        anomalies = result['anomalies']['summary_statistics']
        print(f"\n  Anomalies Detected:")
        print(f"    - Unusual Length of Stay: {anomalies.get('total_unusual_los', 0)}")
        print(f"    - High-Risk Patients: {anomalies.get('total_high_risk', 0)}")
        print(f"    - Off-Hours Admissions: {anomalies.get('total_off_hours', 0)}")
    
    if 'predictions' in result:
        predictions = result['predictions']
        print(f"\n  Predictions:")
        print(f"    - Total Predictions: {predictions.get('total_predictions', 0):,}")
        print(f"    - High-Risk Patients: {predictions.get('total_high_risk', 0)}")
        print(f"    - Long-Stay Predictions: {predictions.get('total_long_stay', 0)}")
    
    print("\n" + "=" * 80)
    return result

if __name__ == "__main__":
    import sys
    
    # Get CSV path from command line or use default
    csv = sys.argv[1] if len(sys.argv) > 1 else "Dataset/ADMISSIONS.csv"
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    asyncio.run(start(csv, batch_size))
