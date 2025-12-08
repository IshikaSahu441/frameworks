# Temporal Local Setup Guide

This project now uses a **local Temporal server** instead of Docker.

## Prerequisites

1. **Temporal CLI installed** - You already have this running!
2. **Python dependencies** - Install with: `pip install -r requirements.txt`

## Your Temporal Server

You have Temporal running locally at:
- **Server Address**: `localhost:7233`
- **Web UI**: `http://localhost:8233`
- **Metrics**: `http://localhost:64121/metrics`
- **Database**: `C:\temporal-data\temporal.db`

## Quick Start

### Option 1: Run Complete Pipeline (Recommended)

This runs everything in the correct order:

```bash
python run_complete_pipeline.py
```

The script will guide you through:
1. Daft data processing
2. Pydantic validation
3. Ray distributed computing
4. Iceberg integration
5. Temporal workflow orchestration

### Option 2: Run Temporal Workflow Only

If you've already processed the data and just want to test Temporal:

**Step 1: Start the Worker** (in one terminal)
```bash
python temporal_worker.py
```

**Step 2: Start the Workflow** (in another terminal)
```bash
python temporal_start_workflow.py
```

Or with custom parameters:
```bash
python temporal_start_workflow.py Dataset/ADMISSIONS.csv 100
```

### Option 3: Run Individual Components

**Daft Processing:**
```bash
python admission_daft_complete.py
```

**Pydantic Validation:**
```bash
python admission_pydantic_validation.py
```

**Ray Distributed:**
```bash
python run_admission_system.py
```

**Iceberg Integration:**
```bash
python admission_iceberg_integration.py
```

## Temporal Workflow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Temporal Server                          │
│                   (localhost:7233)                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────────┐                  ┌──────────────────┐
│  Temporal Worker │                  │  Workflow Client │
│                  │                  │                  │
│  - Workflows     │                  │  - Start         │
│  - Activities    │                  │  - Monitor       │
│                  │                  │  - Query         │
└──────────────────┘                  └──────────────────┘
        │
        │ Executes Activities
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│              Admission Processing Activities                │
│                                                             │
│  1. simple_ping - Health check                             │
│  2. run_distributed_pipeline - Ray processing              │
│     - Load CSV data                                        │
│     - Extract features (distributed)                       │
│     - Detect anomalies (distributed)                       │
│     - Run predictions (distributed)                        │
│     - Score priorities                                     │
└─────────────────────────────────────────────────────────────┘
```

## Files Overview

### Temporal Files (Root Directory)
- `temporal_workflows.py` - Workflow definitions
- `temporal_activities.py` - Activity implementations
- `temporal_worker.py` - Worker that executes workflows
- `temporal_start_workflow.py` - Client to start workflows

### Pipeline Files
- `run_complete_pipeline.py` - Orchestrates entire pipeline
- `admission_daft_complete.py` - Daft data processing
- `admission_pydantic_validation.py` - Pydantic validation
- `admission_ray_distributed.py` - Ray distributed computing
- `admission_iceberg_integration.py` - Iceberg integration

## Monitoring

### Temporal Web UI
Open `http://localhost:8233` to:
- View workflow executions
- Monitor activity progress
- Check workflow history
- Debug failures

### Workflow Status
```bash
temporal workflow list
temporal workflow describe --workflow-id admission_workflow_<id>
```

## Troubleshooting

### Temporal Server Not Running
```bash
temporal server start-dev --db-filename "C:\temporal-data\temporal.db"
```

### Worker Not Connecting
1. Check Temporal server is running: `http://localhost:8233`
2. Verify port 7233 is not blocked
3. Check worker logs for connection errors

### Workflow Stuck
1. Check worker is running
2. View workflow in Web UI: `http://localhost:8233`
3. Check worker logs for activity errors

### Ray Initialization Errors
If Ray fails to initialize:
```python
import ray
ray.shutdown()  # Clean up any existing Ray instances
ray.init(ignore_reinit_error=True)
```

## What Changed from Docker?

### Before (Docker):
- Temporal server in Docker container
- Worker in Docker container
- Complex docker-compose setup
- Network configuration needed

### Now (Local):
- Temporal server runs locally via CLI
- Worker runs as Python process
- Simple connection to localhost:7233
- No Docker overhead

## Benefits of Local Setup

✅ **Faster startup** - No container overhead
✅ **Easier debugging** - Direct access to logs
✅ **Simpler development** - No Docker complexity
✅ **Better performance** - Native execution
✅ **Persistent data** - SQLite database at `C:\temporal-data\temporal.db`

## Next Steps

1. **Start Temporal server** (if not running):
   ```bash
   temporal server start-dev --db-filename "C:\temporal-data\temporal.db"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the complete pipeline**:
   ```bash
   python run_complete_pipeline.py
   ```

4. **Monitor in Web UI**:
   Open `http://localhost:8233`

Enjoy your local Temporal setup! 🚀
