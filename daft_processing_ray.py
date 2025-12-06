"""
daft_processing_ray.py

Ray-enabled rewrite of your daft_processing.py pipeline.

Workflow:
1. Read NDJSON (Dataset/MimicEncounter.ndjson)
2. (Optionally) flatten a sample with Daft for schema preview / stats
3. Parallel stage A: Validate raw records -> Pydantic MimicEncounter
4. Parallel stage B: Convert validated MimicEncounter -> ProcessedEncounter
5. Write outputs:
   - output/processed_encounters.ndjson  (validated, processed)
   - output/validation_errors.ndjson    (raw validation errors)
   - output/processing_errors.ndjson    (errors while creating ProcessedEncounter)
   - output/encounters_sample.parquet   (optional sample parquet via Daft)
Requirements:
  - ray
  - daft
  - pydantic (v2)
  - pyarrow, pandas (optional, for parquet writing)
"""

import os
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

import ray
from pydantic import ValidationError

# Import your existing models (assumes package path Pydantic.* matches your repo)
from Pydantic.mimic_encounter_models import (
    MimicEncounter,
    ProcessedEncounter,
)

# Optional: keep Daft usage for vectorized flattening, sampling, and parquet exports
import daft

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("daft_processing_ray")

# Config
INPUT_PATH = "Dataset/MimicEncounter.ndjson"
OUTPUT_DIR = "output"
PROCESSED_OUT = os.path.join(OUTPUT_DIR, "processed_encounters.ndjson")
RAW_VALIDATION_ERRORS = os.path.join(OUTPUT_DIR, "validation_errors.ndjson")
PROCESSING_ERRORS = os.path.join(OUTPUT_DIR, "processing_errors.ndjson")
SAMPLE_PARQUET = os.path.join(OUTPUT_DIR, "encounters_sample.parquet")

# Ray configuration
RAY_NUM_CPUS = None  # None -> Ray will use available CPUs. Set integer to limit.
RAY_IGNORE_REINIT_ERROR = True

# Ensure output dir exists
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


@ray.remote
def validate_raw_record(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate raw NDJSON dict to a MimicEncounter model.

    Returns dict:
      {
        "ok": bool,
        "id": <maybe id or None>,
        "encounter": <MimicEncounter instance if ok else None>,
        "error": <error string if not ok>
      }
    """
    try:
        encounter = MimicEncounter(**raw)
        return {"ok": True, "id": getattr(encounter, "id", None), "encounter": encounter, "error": None}
    except Exception as e:
        # Catch ValidationError / JSON errors etc.
        msg = str(e)
        return {"ok": False, "id": raw.get("id"), "encounter": None, "error": msg}


@ray.remote
def make_processed(encounter: MimicEncounter) -> Dict[str, Any]:
    """
    Convert a validated MimicEncounter model -> ProcessedEncounter (validated).
    Returns:
      {
        "ok": bool,
        "encounter_id": str or None,
        "record": ProcessedEncounter.model_dump() if ok else None,
        "error": str if failed else None
      }
    """
    try:
        # Build processed dict from the validated MimicEncounter instance (same logic as your prior script)
        record = {
            "encounter_id": encounter.id,
            "resourceType": encounter.resourceType,
            "status": encounter.status.value if encounter.status is not None else None,
            "encounter_class": encounter.encounter_class.code.value if encounter.encounter_class is not None else None,
            "encounter_class_display": encounter.encounter_class.display if encounter.encounter_class is not None else None,
            "period_start": encounter.period.start if encounter.period else None,
            "period_end": encounter.period.end if encounter.period else None,
            "patient_reference": encounter.subject.reference if encounter.subject else None,
            "patient_id": encounter.get_patient_id() if hasattr(encounter, "get_patient_id") else None,
            "priority_code": encounter.priority.coding[0].code if encounter.priority and encounter.priority.coding else None,
            "priority_display": encounter.priority.coding[0].display if encounter.priority and encounter.priority.coding else None,
            "service_type": encounter.serviceType.coding[0].code if encounter.serviceType and encounter.serviceType.coding else None,
            "admit_source": (
                encounter.hospitalization.admitSource.coding[0].code
                if encounter.hospitalization and getattr(encounter.hospitalization, "admitSource", None) and encounter.hospitalization.admitSource.coding
                else None
            ),
            "discharge_disposition": (
                encounter.hospitalization.dischargeDisposition.coding[0].code
                if encounter.hospitalization and getattr(encounter.hospitalization, "dischargeDisposition", None) and encounter.hospitalization.dischargeDisposition.coding
                else None
            ),
            "encounter_identifier": encounter.identifier[0].value if encounter.identifier else None,
            "location_count": encounter.get_location_count() if hasattr(encounter, "get_location_count") else 0,
            "encounter_duration_hours": encounter.get_encounter_duration_hours() if hasattr(encounter, "get_encounter_duration_hours") else None,
        }

        processed = ProcessedEncounter(**record)  # validate
        return {"ok": True, "encounter_id": processed.encounter_id, "record": processed.model_dump(), "error": None}
    except Exception as e:
        return {"ok": False, "encounter_id": getattr(encounter, "id", None), "record": None, "error": str(e)}


def stream_ndjson_to_list(path: str, max_items: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Read NDJSON file and return list of dictionaries.
    For very large files, consider chunked reading (this function collects into memory).
    """
    items = []
    with open(path, "r") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                # Log malformed JSON line as a validation error record later
                items.append({"__malformed_json__": True, "raw_line": line})
            if max_items and len(items) >= max_items:
                break
    return items


def write_ndjson_list(path: str, list_of_dicts: List[Dict[str, Any]]):
    with open(path, "w") as f:
        for item in list_of_dicts:
            f.write(json.dumps(item, default=str) + "\n")


def main(max_items: Optional[int] = None, do_sample_parquet: bool = True):
    # Initialize Ray
    if not ray.is_initialized():
        ray.init(num_cpus=RAY_NUM_CPUS)
    logger.info("Ray initialized")

    # 0) Read raw NDJSON to python list (optionally limit with max_items for testing)
    logger.info("Loading NDJSON into memory (stream)")
    raw_items = stream_ndjson_to_list(INPUT_PATH, max_items=max_items)
    logger.info(f"Loaded {len(raw_items)} raw rows (including any malformed placeholders)")

    # Optional sample via Daft to create a parquet sample and quick previews
    if do_sample_parquet:
        try:
            logger.info("Writing an optional sample parquet (via Daft) for quick inspection")
            # We will create a small sample JSON file and have Daft read it, avoiding full conversion issues
            sample_count = min(1000, len(raw_items))
            sample_path = os.path.join(OUTPUT_DIR, "sample_for_daft.ndjson")
            write_ndjson_list(sample_path, raw_items[:sample_count])
            df_sample = daft.read_json(sample_path)
            # Keep a small parquet for inspection
            df_sample.write_parquet(SAMPLE_PARQUET)
            logger.info("Sample parquet created: %s", SAMPLE_PARQUET)
        except Exception as e:
            logger.warning("Failed to create sample parquet with Daft: %s", e)

    # 1) Parallel raw validation: raw -> MimicEncounter
    logger.info("Stage A: validating raw records in parallel (to MimicEncounter)")
    validate_futures = []
    for raw in raw_items:
        # If the raw item was placeholder for malformed JSON, set a fast failing future
        if raw.get("__malformed_json__"):
            # create a trivial result without calling pydantic
            validate_futures.append(
                ray.put({
                    "ok": False,
                    "id": None,
                    "encounter": None,
                    "error": f"Malformed JSON line: {raw.get('raw_line')[:200]}"
                })
            )
        else:
            validate_futures.append(validate_raw_record.remote(raw))

    validate_results = ray.get(validate_futures)
    logger.info("Stage A complete")

    # Collect valid MimicEncounter objects and raw-validation errors
    valid_encounters = []
    raw_errors = []
    for res in validate_results:
        if res.get("ok"):
            valid_encounters.append(res["encounter"])
        else:
            raw_errors.append({"id": res.get("id"), "error": res.get("error")})

    logger.info("Valid raw records: %d; raw validation errors: %d", len(valid_encounters), len(raw_errors))

    # 2) Parallel processing: MimicEncounter -> ProcessedEncounter
    logger.info("Stage B: converting validated MimicEncounter -> ProcessedEncounter in parallel")
    processed_futures = [make_processed.remote(enc) for enc in valid_encounters]
    processed_results = ray.get(processed_futures)
    logger.info("Stage B complete")

    # Separate successes and processing errors
    successes = []
    processing_errors = []
    for res in processed_results:
        if res.get("ok"):
            successes.append(res["record"])
        else:
            processing_errors.append({"encounter_id": res.get("encounter_id"), "error": res.get("error")})

    logger.info("Processed successes: %d; processing errors: %d", len(successes), len(processing_errors))

    # 3) Persist outputs
    logger.info("Writing outputs to %s", OUTPUT_DIR)
    if successes:
        write_ndjson_list(PROCESSED_OUT, successes)
        logger.info("Processed encounters saved to %s", PROCESSED_OUT)
    else:
        logger.info("No successful processed records to write")

    if raw_errors:
        write_ndjson_list(RAW_VALIDATION_ERRORS, raw_errors)
        logger.info("Raw validation errors saved to %s", RAW_VALIDATION_ERRORS)
    else:
        logger.info("No raw validation errors")

    if processing_errors:
        write_ndjson_list(PROCESSING_ERRORS, processing_errors)
        logger.info("Processing errors saved to %s", PROCESSING_ERRORS)
    else:
        logger.info("No processing errors")

    # Close Ray (optional)
    ray.shutdown()
    logger.info("Pipeline complete and Ray shutdown")


if __name__ == "__main__":
    # You can pass max_items for testing smaller batches:
    # python daft_processing_ray.py  # full run
    # python -c "from daft_processing_ray import main; main(max_items=100)"
    main()
