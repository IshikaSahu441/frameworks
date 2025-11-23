from models.record import UserRecord
from temporalio import activity

@activity.defn
async def validate_records(raw_records: list[dict]) -> list[dict]:
    validated = []
    for r in raw_records:
        record = UserRecord(**r)
        validated.append(record.model_dump())
    return validated
