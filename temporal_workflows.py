"""
Temporal Workflows for Complete Admission Processing Pipeline
Connects to local Temporal server at localhost:7233
"""
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class CompleteAdmissionWorkflow:
    """Orchestrates the complete end-to-end admission processing pipeline.

    Steps:
    1. Health check
    2. Run Daft processing (ETL and analytics)
    3. Run Pydantic validation (schema validation)
    4. Run distributed Ray pipeline (feature extraction, anomalies, predictions)
    5. Run Iceberg integration (data lake setup and audit trails)
    6. Generate final report
    """

    @workflow.run
    async def run(self, csv_path: str = "Dataset/ADMISSIONS.csv", batch_size: int = 50) -> dict:
        workflow.logger.info("Starting complete admission processing workflow...")

        results = {}

        # Step 1: Health check
        workflow.logger.info("Step 1: Health check")
        pong = await workflow.execute_activity(
            "simple_ping",
            args=["workflow-start"],
            schedule_to_close_timeout=timedelta(seconds=10)
        )
        workflow.logger.info(f"Health check result: {pong}")
        results['health_check'] = pong

        # Step 2: Run Daft processing
        workflow.logger.info("Step 2: Running Daft processing")
        daft_result = await workflow.execute_activity(
            "run_daft_processing",
            schedule_to_close_timeout=timedelta(minutes=5)
        )
        workflow.logger.info(f"Daft processing result: {daft_result}")
        results['daft'] = daft_result

        # Check if Daft failed
        if daft_result.get('status') == 'error':
            return {
                'status': 'FAILED',
                'failed_at': 'daft_processing',
                'error': daft_result.get('message'),
                'results': results
            }

        # Step 3: Run Pydantic validation
        workflow.logger.info("Step 3: Running Pydantic validation")
        pydantic_result = await workflow.execute_activity(
            "run_pydantic_validation",
            schedule_to_close_timeout=timedelta(minutes=5)
        )
        workflow.logger.info(f"Pydantic validation result: {pydantic_result}")
        results['pydantic'] = pydantic_result

        # Check if Pydantic failed
        if pydantic_result.get('status') == 'error':
            return {
                'status': 'FAILED',
                'failed_at': 'pydantic_validation',
                'error': pydantic_result.get('message'),
                'results': results
            }

        # Step 4: Run distributed Ray pipeline
        workflow.logger.info("Step 4: Running Ray distributed processing")
        ray_result = await workflow.execute_activity(
            "run_distributed_pipeline",
            args=[csv_path, batch_size],
            schedule_to_close_timeout=timedelta(minutes=60)
        )
        workflow.logger.info(f"Ray processing result: {ray_result}")
        results['ray'] = ray_result

        # Step 5: Run Iceberg integration
        workflow.logger.info("Step 5: Running Iceberg integration")
        iceberg_result = await workflow.execute_activity(
            "run_iceberg_integration",
            schedule_to_close_timeout=timedelta(minutes=5)
        )
        workflow.logger.info(f"Iceberg integration result: {iceberg_result}")
        results['iceberg'] = iceberg_result

        # Check if Iceberg failed
        if iceberg_result.get('status') == 'error':
            return {
                'status': 'FAILED',
                'failed_at': 'iceberg_integration',
                'error': iceberg_result.get('message'),
                'results': results
            }

        # Step 6: Generate final summary
        workflow.logger.info("Step 6: Generating final report")
        final_report = {
            'status': 'SUCCESS',
            'pipeline_completed': True,
            'components': {
                'daft_processing': daft_result,
                'pydantic_validation': pydantic_result,
                'ray_distributed': ray_result,
                'iceberg_integration': iceberg_result
            },
            'summary': {
                'total_processed': ray_result.get('total_processed', 0),
                'features_extracted': ray_result.get('features_extracted', 0),
                'anomalies_detected': ray_result.get('anomalies', {}).get('summary_statistics', {}),
                'data_lake_ready': iceberg_result.get('status') == 'success'
            }
        }

        workflow.logger.info("Complete pipeline finished successfully")
        return final_report
