import ray

@ray.remote
class DatasetStore:
    def __init__(self):
        # maps key -> ObjectRef
        self.store = {}

    def put(self, key: str, obj):
        """Store an object (e.g., pandas.DataFrame or dict) in Ray object store and keep its ObjectRef."""
        self.store[key] = ray.put(obj)
        return key

    def get_ref(self, key: str):
        """Return the ObjectRef for a key, or None if missing."""
        return self.store.get(key)

    def has(self, key: str):
        return key in self.store
