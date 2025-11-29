import uuid
from temporalio import activity
import ray
import pandas as pd
import daft
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
async def preprocess(validated_key: str) -> dict:
    store = get_dataset_store()

    # Load from Ray
    ref = await store.get_ref.remote(validated_key)
    if ref is None:
        raise RuntimeError(f"Dataset key not found: {validated_key}")

    df_pd = ray.get(ref)
    if not isinstance(df_pd, pd.DataFrame):
        raise RuntimeError("Expected pandas DataFrame as stored object")

    # Convert pandas -> daft
    df = daft.from_pandas(df_pd)

    # Feature engineering
    df = df.with_column("age", 2025 - df["yearbuilt"])
    df = df.with_column("price_per_sqft", df["price"] / df["area"])
    df = df.with_column("location", df["location"].cast(daft.DataType.string()))

    # Extract categories
    loc_unique_df = df.select("location").distinct().collect()
    location_categories = loc_unique_df.to_pandas()["location"].tolist()
    category_to_code = {loc: i for i, loc in enumerate(location_categories)}

    # Apply Python UDF using Daft .apply()
    df = df.with_column(
        "location_encoded",
        df["location"].apply(
            lambda x: category_to_code.get(x, 0),
            return_dtype=daft.DataType.int64()
        )
    )

    # Ensure numeric types
    df = df.with_column("floors", df["floors"].cast(daft.DataType.int64()))
    df = df.with_column("garage", df["garage"].cast(daft.DataType.int64()))
    df = df.with_column("condition", df["condition"].cast(daft.DataType.int64()))

    # Filtering
    df = df.where(df["area"] > 100)
    df = df.where(df["price_per_sqft"] > 0)

    # Collect back to pandas
    df_out = df.collect().to_pandas()

    processed_key = f"{validated_key}-processed-{uuid.uuid4()}"
    await store.put.remote(processed_key, df_out)

    metadata_key = f"{validated_key}-metadata-{uuid.uuid4()}"
    await store.put.remote(metadata_key, {"location_categories": location_categories})

    activity.logger.info(
        "Preprocessed %d rows using Daft -> processed_key=%s metadata_key=%s",
        len(df_out),
        processed_key,
        metadata_key,
    )

    return {"processed_key": processed_key, "metadata_key": metadata_key}
