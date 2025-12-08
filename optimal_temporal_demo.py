"""
Optimal Temporal Demo - Uses Pre-Processed Data
This is the RIGHT way to use Temporal - orchestration, not processing!
"""
import asyncio
import json
import os
from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.worker import Worker
from datetime import timedelta

# ============================================================================
# Activities - Fast because they just read pre-computed results!
# ============================================================================

@activity.defn
async def check_data_ready() -> dict:
    """Check if data processing is complete"""
    activity.logger.info("Checking if data is ready...")
    
    daft_ready = os.path.exists('output/daft_complete/admissions_full.parquet')
    pydantic_ready = os.path.exists('output/pydantic_validation/validation_summary.json')
    
    return {
        'daft_ready': daft_ready,
        'pydantic_ready': pydantic_ready,
        'all_ready': daft_ready and pydantic_ready
    }

@activity.defn
async def get_daft_summary() -> dict:
    """Get Daft processing summary - FAST!"""
    activity.logger.info("Reading Daft results...")
    
    # Just count files - no heavy processing!
    output_dir = 'output/daft_complete'
    files = os.listdir(output_dir) if os.path.exists(output_dir) else []
    
    return {
        'status': 'complete',
        'output_files': len(files),
        'location': output_dir,
        'files': files
    }

@activity.defn
async def get_pydantic_summary() -> dict:
    """Get Pydantic validation summary - FAST!"""
    activity.logger.info("Reading Pydantic results...")
    
    summary_file = 'output/pydantic_validation/validation_summary.json'
    
    if os.path.exists(summary_file):
        with open(summary_file, 'r') as f:
            summary = json.load(f)
        return summary
    else:
        return {'status': 'not_found'}

@activity.defn
async def generate_final_report(daft_summary: dict, pydantic_summary: dict) -> dict:
    """Generate final report - FAST!"""
    activity.logger.info("Generating final report...")
    
    report = {
        'pipeline_status': 'SUCCESS',
        'daft_processing': {
            'status': daft_summary['status'],
            'output_files': daft_summary['output_files'],
            'location': daft_summary['location']
        },
        'pydantic_validation': {
            'total_validated': pydantic_summary.get('successfully_validated', 0),
            'validation_rate': pydantic_summary.get('validation_success_rate', 0),
            'emergency_admissions': pydantic_summary.get('data_quality_metrics', {}).get('emergency_admissions', 0),
            'mortality_rate': pydantic_summary.get('data_quality_metrics', {}).get('mortality_rate', 0)
        },
        'recommendation': 'Data is ready for downstream processing (Ray, Iceberg)'
    }
    
    return report

# ============================================================================
# Workflow - Orchestrates, doesn't process!
# ============================================================================

@workflow.defn
class OptimalAdmissionWorkflow:
    """Optimal workflow - orchestrates pre-processed data"""
    
    @workflow.run
    async def run(self) -> dict:
        workflow.logger.info("Starting optimal admission workflow...")
        
        # Step 1: Check if data is ready (fast!)
        data_status = await workflow.execute_activity(
            check_data_ready,
            start_to_close_timeout=timedelta(seconds=10)
        )
        workflow.logger.info(f"Data status: {data_status}")
        
        if not data_status['all_ready']:
            return {
                'status': 'ERROR',
                'message': 'Data not ready. Run Daft and Pydantic processing first!',
                'data_status': data_status
            }
        
        # Step 2: Get Daft summary (fast!)
        daft_summary = await workflow.execute_activity(
            get_daft_summary,
            start_to_close_timeout=timedelta(seconds=10)
        )
        workflow.logger.info(f"Daft summary retrieved")
        
        # Step 3: Get Pydantic summary (fast!)
        pydantic_summary = await workflow.execute_activity(
            get_pydantic_summary,
            start_to_close_timeout=timedelta(seconds=10)
        )
        workflow.logger.info(f"Pydantic summary retrieved")
        
        # Step 4: Generate final report (fast!)
        final_report = await workflow.execute_activity(
            generate_final_report,
            args=[daft_summary, pydantic_summary],
            start_to_close_timeout=timedelta(seconds=10)
        )
        workflow.logger.info(f"Final report generated")
        
        return final_report

# ============================================================================
# Worker
# ============================================================================

async def run_worker():
    """Start the Temporal worker"""
    print("=" * 80)
    print("OPTIMAL TEMPORAL DEMO - WORKER")
    print("=" * 80)
    print("Server: localhost:7233")
    print("Task Queue: optimal-admission-queue")
    print("Strategy: Orchestrate pre-processed data (FAST!)")
    print("-" * 80)
    
    client = await Client.connect("localhost:7233")
    print("✓ Connected to Temporal server")
    
    worker = Worker(
        client,
        task_queue="optimal-admission-queue",
        workflows=[OptimalAdmissionWorkflow],
        activities=[
            check_data_ready,
            get_daft_summary,
            get_pydantic_summary,
            generate_final_report
        ],
    )
    
    print("✓ Worker registered")
    print("\n" + "=" * 80)
    print("Worker running - ready for FAST workflows!")
    print("=" * 80 + "\n")
    
    await worker.run()

# ============================================================================
# Client
# ============================================================================

async def start_workflow():
    """Start the workflow"""
    print("=" * 80)
    print("OPTIMAL TEMPORAL DEMO - CLIENT")
    print("=" * 80)
    print("Server: localhost:7233")
    print("Strategy: Read pre-processed results (FAST!)")
    print("-" * 80)
    
    client = await Client.connect("localhost:7233")
    print("✓ Connected to Temporal server")
    
    # Start workflow
    workflow_id = f"optimal_admission_{int(asyncio.get_event_loop().time())}"
    handle = await client.start_workflow(
        OptimalAdmissionWorkflow.run,
        id=workflow_id,
        task_queue="optimal-admission-queue",
    )
    
    print(f"✓ Started workflow: {handle.id}")
    print("\nWaiting for workflow to complete...")
    print("-" * 80)
    
    # Wait for result
    result = await handle.result()
    
    print("\n" + "=" * 80)
    print("WORKFLOW COMPLETED")
    print("=" * 80)
    
    if result.get('status') == 'ERROR':
        print(f"\n❌ {result['message']}")
        print("\nPlease run:")
        print("  1. python admission_daft_complete.py")
        print("  2. python admission_pydantic_validation.py")
        print("  3. Then run this workflow again")
    else:
        print(f"\n✅ Pipeline Status: {result['pipeline_status']}")
        print(f"\n📊 Daft Processing:")
        print(f"   Status: {result['daft_processing']['status']}")
        print(f"   Output Files: {result['daft_processing']['output_files']}")
        print(f"   Location: {result['daft_processing']['location']}")
        
        print(f"\n✅ Pydantic Validation:")
        print(f"   Total Validated: {result['pydantic_validation']['total_validated']:,}")
        print(f"   Validation Rate: {result['pydantic_validation']['validation_rate']:.2f}%")
        print(f"   Emergency Admissions: {result['pydantic_validation']['emergency_admissions']:,}")
        print(f"   Mortality Rate: {result['pydantic_validation']['mortality_rate']:.2f}%")
        
        print(f"\n💡 {result['recommendation']}")
    
    print("\n" + "=" * 80)
    print("⚡ Workflow completed in SECONDS (not minutes)!")
    print("=" * 80)
    
    return result

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Worker: python optimal_temporal_demo.py worker")
        print("  Client: python optimal_temporal_demo.py client")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "worker":
        asyncio.run(run_worker())
    elif mode == "client":
        asyncio.run(start_workflow())
    else:
        print(f"Unknown mode: {mode}")
        print("Use 'worker' or 'client'")
        sys.exit(1)
