import asyncio
import requests
from temporalio import activity

@activity.defn
async def call_prediction(features: dict) -> dict:
    url = "http://localhost:8000/predict"

    # Retry loop
    for i in range(10):
        try:
            resp = requests.post(url, json=features, timeout=10)
            resp.raise_for_status()
            activity.logger.info("Prediction response: %s", resp.text)
            return resp.json()
        except requests.exceptions.RequestException as e:
            activity.logger.warning("Prediction attempt %d failed: %s", i+1, e)
            await asyncio.sleep(1)

    raise RuntimeError("Failed to call prediction after retries")
