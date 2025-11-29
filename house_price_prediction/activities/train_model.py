import ray
from temporalio import activity
import uuid
import pickle
from sklearn.ensemble import RandomForestRegressor
from ray_store.dataset_store import DatasetStore

def get_dataset_store():
    if not ray.is_initialized():
        ray.init(address="auto", namespace="ml_pipeline", ignore_reinit_error=True)
    try:
        store = ray.get_actor("dataset_store")
    except ValueError:
        store = DatasetStore.options(name="dataset_store", lifetime="detached").remote()
    return store

@activity.defn
async def train_model(processed_key: str) -> str:
    store = get_dataset_store()

    ref = await store.get_ref.remote(processed_key)
    if ref is None:
        raise RuntimeError(f"Processed key not found: {processed_key}")

    df = ray.get(ref)

    feature_cols = [
        "area", "bedrooms", "bathrooms", "floors",
        "age", "location_encoded", "condition", "garage"
    ]

    for c in feature_cols + ["price"]:
        if c not in df.columns:
            raise RuntimeError(f"Missing required column for training: {c}")

    X = df[feature_cols].fillna(0).values
    y = df["price"].fillna(0).values

    if len(X) < 5:
        activity.logger.warning("Training with very small dataset: %d rows", len(X))

    model = RandomForestRegressor(n_estimators=300, max_depth=18, random_state=42)
    model.fit(X, y)

    # Store model in Ray
    model_bytes = pickle.dumps(model)
    model_key = f"model-{uuid.uuid4()}"
    await store.put.remote(model_key, model_bytes)

    activity.logger.info("Training complete. Trained on %d rows -> model_key=%s", len(X), model_key)
    return model_key
