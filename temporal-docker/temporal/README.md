**Temporal Workflows - Admission Pipeline**

- **Purpose**: Orchestrate the admission pipeline using Temporal. The workflow runs the existing Ray-based distributed pipeline (`process_admissions_distributed`) as an activity.

Quick steps to run locally (Windows PowerShell):

1. Start Temporal server (Docker):

```powershell
cd temporal-docker/temporal
docker compose up -d
```

- Temporal gRPC: `localhost:7233`
- Temporal Web UI: `http://localhost:8088`

2. Create a virtual environment and install Python deps for worker/client:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r temporal-docker/temporal/requirements-temporal.txt
pip install -r requirements.txt
```

3. Start the Temporal worker (in a separate terminal):

```powershell
python temporal-docker/temporal/worker.py
```

4. Start a workflow run (after worker is running):

```powershell
python temporal-docker/temporal/start_workflow.py Dataset/ADMISSIONS.csv
```

Notes and assumptions:
- The activity `run_distributed_pipeline` will import and call `process_admissions_distributed` from `admission_ray_distributed.py` and therefore requires Ray to be installed and usable locally.
- The dataset path should be accessible from where you start the workflow; the default is `Dataset/ADMISSIONS.csv` relative to repo root.
- For production you should point Temporal to a persistent DB (Postgres) instead of `sqlite` used in the auto-setup image.

If you'd like, I can:
- Update the repository `requirements.txt` to include `temporalio` directly.
- Add a Dockerfile to package the worker and run it alongside Temporal.
- Extend activities to write outputs to Iceberg using `pyiceberg`.

Note: imported from `origin/temporal` branch into `project2.0` for local testing.
