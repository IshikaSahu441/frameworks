from temporalio.worker import Worker
from temporalio.client import Client
from workflow.pipeline_workflow import DataPipelineWorkflow
from activities import validate, convert, ray_tasks, daft_tasks
import asyncio

async def main():
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="pipeline",
        workflows=[DataPipelineWorkflow],
        activities=[validate.validate_records,
                    convert.to_arrow,
                    ray_tasks.ray_process,
                    daft_tasks.daft_filter]
    )
    await worker.run()

asyncio.run(main())
