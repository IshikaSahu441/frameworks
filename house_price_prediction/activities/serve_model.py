from temporalio import activity
import ray
from ray import serve
import pickle
import pandas as pd
from ray_store.dataset_store import DatasetStore
import asyncio
import requests
from starlette.responses import JSONResponse, PlainTextResponse

def get_dataset_store():
    if not ray.is_initialized():
        ray.init(address="auto", namespace="ml_pipeline", ignore_reinit_error=True)
    try:
        store = ray.get_actor("dataset_store")
    except ValueError:
        store = DatasetStore.options(name="dataset_store", lifetime="detached").remote()
    return store

@activity.defn
async def serve_model(model_key: str, metadata_key: str) -> str:
    """
    Deploys the trained model with metadata for encoding locations.
    """
    ray.init(ignore_reinit_error=True)

    # Start Serve if not already running
    try:
        serve.start(detached=True)
    except Exception:
        pass

    store = get_dataset_store()

    # Retrieve model bytes
    ref_model = await store.get_ref.remote(model_key)
    if ref_model is None:
        raise RuntimeError(f"Model key not found: {model_key}")
    model_bytes = ray.get(ref_model)
    model = pickle.loads(model_bytes)

    # Retrieve metadata
    ref_meta = await store.get_ref.remote(metadata_key)
    if ref_meta is None:
        raise RuntimeError(f"Metadata key not found: {metadata_key}")
    metadata = ray.get(ref_meta)
    location_categories = metadata.get("location_categories", [])

    @serve.deployment(name="house_predictor")
    class Predictor:
        def __init__(self, model, location_categories):
            self.model = model
            self.location_categories = location_categories

        def _encode_location(self, loc):
            try:
                return self.location_categories.index(str(loc))
            except ValueError:
                return 0  # unknown

        async def __call__(self, request):
            # ---- FIX: Handle OPTIONS ----
            if request.method == "OPTIONS":
                return PlainTextResponse("", status_code=204)

            data = await request.json()

            df = pd.DataFrame([{
                "area": float(data.get("area", 0)),
                "bedrooms": int(data.get("bedrooms", 0)),
                "bathrooms": float(data.get("bathrooms", 0)),
                "floors": int(data.get("floors", 0)),
                "age": 2025 - int(data.get("yearbuilt", 2025)),
                "location_encoded": self._encode_location(data.get("location", "")),
                "condition": int(data.get("condition", 0)),
                "garage": int(data.get("garage", 0)),
            }])

            pred = float(self.model.predict(df.values)[0])
            return JSONResponse({"predicted_price": pred})

    serve.run(Predictor.bind(model, location_categories), route_prefix="/predict")

    # Wait for serve endpoint to be ready
    for _ in range(10):
        try:
            r = requests.options("http://localhost:8000/predict", timeout=2)
            if r.status_code in [200, 204, 405]:
                break
        except:
            await asyncio.sleep(1)

    activity.logger.info("Model deployed and Serve endpoint ready at /predict")
    return "model_served"
