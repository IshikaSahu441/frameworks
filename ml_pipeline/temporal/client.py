import asyncio
from temporalio.client import Client
from temporalio.api.enums.v1 import WorkflowIdReusePolicy
from temporal.workflows.training_pipeline import TrainingPipelineWorkflow


async def main():
    client = await Client.connect("localhost:7233")

    workflow_id = "ml-demo"

    # terminate old workflow if exists
    try:
        await client.terminate_workflow(workflow_id, reason="Restarting workflow")
        print("Old workflow terminated")
    except Exception:
        print("No existing workflow to terminate")

    data = [
        {"user_id": 1, "name": "Alice", "age": 17, "income": 25000.0},
        {"user_id": 2, "name": "Bob", "age": 40, "income": 80000.0},
    ]

    pred_age = 30
    pred_income = 1000000.0

    handle = await client.start_workflow(
        workflow=TrainingPipelineWorkflow.run,
        args=[data, pred_age, pred_income],  # <-- FIXED
        id=workflow_id,
        task_queue="pipeline",
        id_reuse_policy=WorkflowIdReusePolicy.WORKFLOW_ID_REUSE_POLICY_ALLOW_DUPLICATE,
    )

    print("RUNNING workflow id=ml-demo, waiting for result...")
    result = await handle.result()
    print("FINAL RESULT:", result)


if __name__ == "__main__":
    asyncio.run(main())
