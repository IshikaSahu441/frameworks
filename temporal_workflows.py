"""
Temporal Workflows for Admission Processing Pipeline
Connects to local Temporal server at localhost:7233
"""
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class AdmissionWorkflow:
    """Orchestrates the end-to-end admission processing pipeline.

    Steps:
    1. Ping activity (quick health check)
    2. Run distributed Ray pipeline (feature extraction, anomalies, predictions)
    3. Return the aggregated result
    """

    @workflow.run
    async def run(self, csv_path: str, batch_size: int = 50) -> dict:
        # Health check
        pong = await workflow.execute_activity(
            "simple_ping",
            args=["worker-start"],
            schedule_to_close_timeout=timedelta(seconds=10)
        )
        workflow.logger.info(f"Health check activity result: {pong}")

        # Run distributed pipeline (may be long-running)
        result = await workflow.execute_activity(
            "run_distributed_pipeline",
            args=[csv_path, batch_size],
            schedule_to_close_timeout=timedelta(minutes=60),
        )

        # Optionally, you could add other activities here (optimize beds, write to Iceberg, etc.)
        return result
