import ray
import pyarrow as pa
from temporalio import activity
import pickle
from sklearn.ensemble import RandomForestClassifier


# Ray init is idempotent; ignore reinit errors
ray.init(ignore_reinit_error=True)


@ray.remote
def train_remote(X, y):
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)
    return pickle.dumps(model)


@activity.defn
async def train_model(arrow_bytes: bytes) -> bytes:
    reader = pa.ipc.open_file(pa.BufferReader(arrow_bytes))
    table = reader.read_all()


    # Build feature matrix and label
    # Features: age, income
    ages = table.column("age").to_pylist()
    incomes = table.column("income").to_pylist()
    X = [[int(a), float(i)] for a, i in zip(ages, incomes)]


    # Label: is_high_income (bool -> int)
    labels = [1 if v else 0 for v in table.column("is_high_income").to_pylist()]


    # Train remotely on Ray
    model_bytes = ray.get(train_remote.remote(X, labels))
    activity.logger.info("Trained model and serialized, size=%d bytes", len(model_bytes))
    return model_bytes