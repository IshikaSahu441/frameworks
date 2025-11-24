import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from temporal.workflows.training_pipeline import TrainingPipelineWorkflow
import activities


async def main():
    client = await Client.connect("localhost:7233")
    worker = Worker(
    client,
    task_queue="pipeline",
    workflows=[TrainingPipelineWorkflow],
    activities=[
        activities.validate.validate_records,
        activities.to_arrow.to_arrow,
        activities.preprocess.preprocess,
        activities.train_model.train_model,
        activities.serve_model.serve_model,
        activities.predict.call_prediction,
    ],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())