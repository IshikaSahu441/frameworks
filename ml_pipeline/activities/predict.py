import requests
from temporalio import activity


@activity.defn
async def call_prediction(age: int, income: float) -> dict:
# Ray Serve default HTTP port for detached Serve is 8000
    url = "http://localhost:8000/predict"
    resp = requests.post(url, json={"age": age, "income": income}, timeout=10)
    resp.raise_for_status()
    activity.logger.info("Prediction response: %s", resp.text)
    return resp.json()