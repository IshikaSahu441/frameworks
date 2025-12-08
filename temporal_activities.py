"""
Temporal Activities for Admission Processing Pipeline
Connects to local Temporal server at localhost:7233
"""
import asyncio
from datetime import timedelta
from temporalio import activity
import pandas as pd

@activity.defn
async def run_distributed_pipeline(csv_path: str, batch_size: int = 50) -> dict:
    """Activity that loads admissions CSV and runs the Ray distributed pipeline.
    This uses a thread to run blocking CPU-bound code so the activity stays async.
    """
    # Import inside function to avoid import-time side-effects during worker startup
    import admission_ray_distributed as ard

    # Load CSV in thread
    def _load_and_run():
        df = pd.read_csv(csv_path)
        return ard.process_admissions_distributed(df, batch_size=batch_size)

    result = await asyncio.to_thread(_load_and_run)
    return result

@activity.defn
async def simple_ping(message: str) -> str:
    """Simple health check activity"""
    return f"PONG: {message}"
