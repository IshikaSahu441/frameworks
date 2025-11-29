import asyncio
import pandas as pd
import uuid
import ray
from temporalio.client import Client
from temporal.workflows.ml_pipeline_workflow import MLTrainingWorkflow
from ray_store.dataset_store import DatasetStore

async def main():
    # Connect to Ray
    if not ray.is_initialized():
        ray.init(address="auto", namespace="ml_pipeline", ignore_reinit_error=True)

    # Ensure DatasetStore exists
    try:
        store = ray.get_actor("dataset_store")
    except ValueError:
        store = DatasetStore.options(name="dataset_store", lifetime="detached").remote()

    # Connect to Temporal
    client = await Client.connect("localhost:7233")

    # Load dataset
    DATA_PATH = "D:\\frameworks\\house_price_prediction\\data\\House Price Prediction Dataset.csv"
    df = pd.read_csv(DATA_PATH)
    dataset_key = f"dataset-{uuid.uuid4()}"
    await store.put.remote(dataset_key, df)

    # Raw features for prediction
    predict_features = {
        "area": 2200,
        "bedrooms": 4,
        "bathrooms": 3,
        "floors": 2,
        "yearbuilt": 2020,
        "location": "Downtown",
        "condition": 4,
        "garage": 1,
    }

    workflow_id = f"house-ml-{uuid.uuid4()}"
    handle = await client.start_workflow(
        MLTrainingWorkflow.run,
        args=[{"dataset_key": dataset_key, "predict_features": predict_features}],
        id=workflow_id,
        task_queue="pipeline",
    )

    print(f"Workflow started: {workflow_id}")
    result = await handle.result()
    print("🎉 RESULT:", result)


if __name__ == "__main__":
    asyncio.run(main())
