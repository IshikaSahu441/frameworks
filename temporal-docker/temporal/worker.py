import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

async def run_worker():
    # Connect to local Temporal server
    client = await Client.connect("localhost:7233")

    # Import workflows and activities here to register
    import workflows
    import activities

    worker = Worker(
        client,
        task_queue="admission-task-queue",
        workflows=[workflows.AdmissionWorkflow],
        activities=[activities.run_distributed_pipeline, activities.simple_ping],
    )

    print("Worker started, polling task queue: admission-task-queue")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(run_worker())
