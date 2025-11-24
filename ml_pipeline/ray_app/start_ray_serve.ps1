ray start --head
python - <<'PY'
import ray
from ray import serve
ray.init()
serve.start()
print("Serve started")
PY