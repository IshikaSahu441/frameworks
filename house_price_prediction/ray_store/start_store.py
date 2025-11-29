import ray
from ray_store.dataset_store import DatasetStore

if __name__ == "__main__":
    ray.init(ignore_reinit_error=True)
    try:
        DatasetStore.options(name="dataset_store", lifetime="detached").remote()
        print("DatasetStore actor created (name=dataset_store)")
    except Exception as e:
        print("DatasetStore actor may already exist:", e)
