import asyncio
from temporalio.client import Client
import workflows

async def start(csv_path: str):
    client = await Client.connect("localhost:7233")

    handle = await client.start_workflow(
        workflows.AdmissionWorkflow.run,
        csv_path,
        id="admission_workflow_1",
        task_queue="admission-task-queue",
    )

    print(f"Started workflow execution with id: {handle.id}")
    result = await handle.result()
    print("Workflow result:")
    print(result)

if __name__ == "__main__":
    import sys
    csv = sys.argv[1] if len(sys.argv) > 1 else "Dataset/ADMISSIONS.csv"
    asyncio.run(start(csv))
