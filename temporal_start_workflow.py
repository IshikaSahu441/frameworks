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
        temporal_workflows.CompleteAdmissionWorkflow.run,
        args=[csv_path, batch_size],
        id=f"complete_admission_workflow_{asyncio.get_event_loop().time()}",
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
    
    if result.get('status') == 'FAILED':
        print(f"❌ Pipeline failed at: {result.get('failed_at', 'unknown')}")
        print(f"Error: {result.get('error', 'unknown error')}")
        print("\nPartial results:")
        for component, comp_result in result.get('results', {}).items():
            status = "✅" if comp_result.get('status') == 'success' else "❌"
            print(f"  {component}: {status}")
        return result
    
    # Success case
    print(f"✅ Pipeline Status: {result['status']}")
    print(f"✅ All Components Completed: {result['pipeline_completed']}")
    
    summary = result.get('summary', {})
    print(f"\n📊 Processing Summary:")
    print(f"   Total Records Processed: {summary.get('total_processed', 0):,}")
    print(f"   Features Extracted: {summary.get('features_extracted', 0):,}")
    print(f"   Data Lake Ready: {'✅' if summary.get('data_lake_ready') else '❌'}")
    
    anomalies = summary.get('anomalies_detected', {})
    if anomalies:
        print(f"\n🔍 Anomalies Detected:")
        print(f"   Unusual Length of Stay: {anomalies.get('total_unusual_los', 0)}")
        print(f"   High-Risk Patients: {anomalies.get('total_high_risk', 0)}")
        print(f"   Off-Hours Admissions: {anomalies.get('total_off_hours', 0)}")
    
    components = result.get('components', {})
    print(f"\n🔧 Component Status:")
    for component_name, comp_result in components.items():
        # Check for status field, if not present but has data, consider it success
        if comp_result.get('status') == 'success':
            status = "✅ SUCCESS"
        elif comp_result.get('status') == 'error':
            status = "❌ FAILED"
        elif isinstance(comp_result, dict) and len(comp_result) > 0 and 'total_processed' in comp_result:
            # Ray result without explicit status but with data
            status = "✅ SUCCESS"
        else:
            status = "❌ FAILED"
        print(f"   {component_name.replace('_', ' ').title()}: {status}")
    
    print("\n" + "=" * 80)
    print("🎉 Complete pipeline orchestrated by Temporal!")
    print("=" * 80)
    return result

if __name__ == "__main__":
    import sys
    
    # Get CSV path from command line or use default
    csv = sys.argv[1] if len(sys.argv) > 1 else "Dataset/ADMISSIONS.csv"
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    asyncio.run(start(csv, batch_size))
