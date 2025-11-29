from pydantic import BaseModel, Field
from temporalio import activity
import uuid
import ray
import pandas as pd
from ray_store.dataset_store import DatasetStore

# --- Pydantic model ---
class HouseRecord(BaseModel):
    area: float = Field(..., gt=0)
    bedrooms: int = Field(..., ge=0)
    bathrooms: float = Field(..., ge=0)
    floors: int = Field(..., ge=1)
    yearbuilt: int
    location: str
    condition: int = Field(..., ge=1, le=5)
    garage: int = Field(..., ge=0)
    price: float = Field(..., ge=0)

# --- DatasetStore getter ---
def get_dataset_store():
    if not ray.is_initialized():
        ray.init(address="auto", namespace="ml_pipeline", ignore_reinit_error=True)
    try:
        store = ray.get_actor("dataset_store")
    except ValueError:
        store = DatasetStore.options(name="dataset_store", lifetime="detached").remote()
    return store

# --- Mapping dictionaries ---
CONDITION_MAP = {
    "Poor": 1,
    "Fair": 2,
    "Average": 3,
    "Good": 4,
    "Excellent": 5
}

GARAGE_MAP = {
    "No": 0,
    "Yes": 1
}

# --- Activity ---
@activity.defn
async def validate_records(dataset_key: str) -> str:
    store = get_dataset_store()

    ref = await store.get_ref.remote(dataset_key)
    if ref is None:
        raise RuntimeError(f"Dataset key not found: {dataset_key}")

    df = ray.get(ref)

    validated = []
    for r in df.to_dict(orient="records"):
        r_norm = {k.lower(): v for k, v in r.items()}

        if "condition" in r_norm and isinstance(r_norm["condition"], str):
            r_norm["condition"] = CONDITION_MAP.get(r_norm["condition"], 3)

        if "garage" in r_norm and isinstance(r_norm["garage"], str):
            r_norm["garage"] = GARAGE_MAP.get(r_norm["garage"], 0)

        rec = HouseRecord(**r_norm)
        validated.append(rec.dict())

    validated_df = pd.DataFrame(validated)
    new_key = f"validated-{uuid.uuid4()}"
    await store.put.remote(new_key, validated_df)

    activity.logger.info("Validated %d rows -> key=%s", len(validated_df), new_key)
    return new_key
