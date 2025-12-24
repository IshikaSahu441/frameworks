"""
Temporal Activities for Complete Admission Processing Pipeline
Connects to local Temporal server at localhost:7233
"""
import asyncio
from datetime import timedelta
from temporalio import activity
import pandas as pd
import os
import sys

@activity.defn
async def run_daft_processing() -> dict:
    """Activity that runs Daft data processing"""
    activity.logger.info("Starting Daft processing activity...")

    def _run_daft():
        try:
            # Import and run Daft processing
            import admission_daft_complete
            return {"status": "success", "message": "Daft processing completed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    result = await asyncio.to_thread(_run_daft)
    return result

@activity.defn
async def run_pydantic_validation() -> dict:
    """Activity that runs Pydantic validation"""
    activity.logger.info("Starting Pydantic validation activity...")

    def _run_pydantic():
        try:
            # Import and run Pydantic validation
            import admission_pydantic_validation
            return {"status": "success", "message": "Pydantic validation completed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    result = await asyncio.to_thread(_run_pydantic)
    return result

@activity.defn
async def run_distributed_pipeline(csv_path: str, batch_size: int = 50) -> dict:
    """Activity that loads admissions CSV and runs the Ray distributed pipeline.
    This uses a thread to run blocking CPU-bound code so the activity stays async.
    """
    activity.logger.info(f"Starting Ray distributed processing for {csv_path}...")

    # Import inside function to avoid import-time side-effects during worker startup
    import admission_ray_distributed as ard

    # Load CSV in thread
    def _load_and_run():
        try:
            df = pd.read_csv(csv_path)
            result = ard.process_admissions_distributed(df, batch_size=batch_size)
            # Add status field for consistency with other activities
            result['status'] = 'success'
            result['message'] = 'Ray distributed processing completed'
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    result = await asyncio.to_thread(_load_and_run)
    return result

@activity.defn
async def run_iceberg_integration() -> dict:
    """Activity that runs Iceberg integration"""
    activity.logger.info("Starting Iceberg integration activity...")

    def _run_iceberg():
        try:
            # Import and run Iceberg integration
            from admission_iceberg_integration import AdmissionIcebergIntegration

            integration = AdmissionIcebergIntegration()
            integration.run_integration()
            return {"status": "success", "message": "Iceberg integration completed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    result = await asyncio.to_thread(_run_iceberg)
    return result

@activity.defn
async def simple_ping(message: str) -> str:
    """Simple health check activity"""
    return f"PONG: {message}"
