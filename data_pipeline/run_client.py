from temporalio.client import Client
import asyncio
from workflow.pipeline_workflow import DataPipelineWorkflow

async def main():
    # Connect to Temporal
    client = await Client.connect("localhost:7233")

    # Input data
    data = [
        {"user_id": 1, "name": "Alice", "age": 25},
        {"user_id": 2, "name": "Bob", "age": 40},
    ]

    # Start workflow (returns a WorkflowHandle)
    handle = await client.start_workflow(
        DataPipelineWorkflow.run,
        data,
        id="pipeline-demo",
        task_queue="pipeline"
    )

    # Wait for workflow result
    result = await handle.result()

    print("RESULT:", result)

# Run main
asyncio.run(main())
