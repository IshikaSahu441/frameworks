from temporalio import activity
import ray
from ray import serve
import pickle

@activity.defn
async def serve_model(model_bytes: bytes) -> str:
    # Initialize Ray (ignore if already running)
    ray.init(ignore_reinit_error=True)

    # Start Ray Serve if not already active
    try:
        serve.start(detached=True)
    except Exception:
        pass  # Already running

    # Load model
    model = pickle.loads(model_bytes)

    # -------------------------------
    # Define deployment (NO route_prefix here)
    # -------------------------------
    @serve.deployment
    class Predictor:
        def __init__(self, model):
            self.model = model

        async def __call__(self, request):
            data = await request.json()
            age = int(data.get("age", 0))
            income = float(data.get("income", 0.0))
            pred = self.model.predict([[age, income]])[0]
            return {"prediction": int(pred)}

    # Bind model instance
    app = Predictor.bind(model)

    # -------------------------------
    # Serve the app WITH route_prefix here
    # -------------------------------
    serve.run(
        app,
        name="predictor_service",
        route_prefix="/predict"   # ✔ FIXED location
    )

    activity.logger.info("Model deployed to Ray Serve at /predict")
    return "model_served"
