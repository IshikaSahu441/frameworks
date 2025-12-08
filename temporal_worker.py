"""
Temporal Worker for Admission Processing Pipeline
Connects to local Temporal server at localhost:7233
"""
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

async def run_worker():
    """Start the Temporal worker that connects to local server"""
    print("=" * 80)
    print("TEMPORAL WORKER: Connecting to Local Server")
    print("=" * 80)
    print("Server Address: localhost:7233")
    print("Task Queue: admission-task-queue")
    print("-" * 80)
    
    # Connect to local Temporal server
    client = await Client.connect("localhost:7233")
    print("✓ Connected to Temporal server")

    # Import workflows and activities here to register
    import temporal_workflows
    import temporal_activities

    worker = Worker(
        client,
        task_queue="admission-task-queue",
        workflows=[temporal_workflows.AdmissionWorkflow],
        activities=[
            temporal_activities.run_distributed_pipeline, 
            temporal_activities.simple_ping
        ],
    )

    print("✓ Worker registered with workflows and activities")
    print("\n" + "=" * 80)
    print("Worker started, polling task queue: admission-task-queue")
    print("Waiting for workflow executions...")
    print("=" * 80 + "\n")
    
    await worker.run()

if __name__ == "__main__":
    asyncio.run(run_worker())
