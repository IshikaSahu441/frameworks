import asyncio
from temporalio.worker import Worker
from temporalio.client import Client
import ray

# Import workflow & activities
from temporal.workflows.ml_pipeline_workflow import MLTrainingWorkflow
from activities.validate import validate_records
from activities.preprocess import preprocess
from activities.train_model import train_model
from activities.serve_model import serve_model
from activities.predict import call_prediction

# Import DatasetStore actor
from ray_store.dataset_store import DatasetStore

async def main():
    # Connect to Ray cluster with fixed namespace
    if not ray.is_initialized():
        try:
            ray.init(address="auto", namespace="ml_pipeline", ignore_reinit_error=True)
            print("Ray: Connected to existing cluster.")
        except Exception:
            print("Ray: Starting new local cluster.")
            ray.init(namespace="ml_pipeline", ignore_reinit_error=True)

    # Ensure detached DatasetStore actor exists
    try:
        store = ray.get_actor("dataset_store")
        print("Ray actor 'dataset_store' already exists.")
    except ValueError:
        store = DatasetStore.options(name="dataset_store", lifetime="detached").remote()
        print("Created Ray actor 'dataset_store' (detached).")

    # Connect to Temporal
    client = await Client.connect("localhost:7233")

    # Start worker
    worker = Worker(
        client,
        task_queue="pipeline",
        workflows=[MLTrainingWorkflow],
        activities=[
            validate_records,
            preprocess,
            train_model,
            serve_model,
            call_prediction,
        ],
        max_concurrent_activities=50,
        max_concurrent_workflow_tasks=50,
    )

    print("🚀 Worker started on task queue: pipeline")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
