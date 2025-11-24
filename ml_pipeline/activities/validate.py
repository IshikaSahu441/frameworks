from pydantic import BaseModel, Field
from typing import Optional
from temporalio import activity


class UserRecord(BaseModel):
    user_id: int
    name: str
    age: int = Field(..., ge=0, le=150)
    income: float 


@activity.defn
async def validate_records(raw_records: list[dict]) -> list[dict]:
    validated = []
    for r in raw_records:
        rec = UserRecord(**r)
        validated.append(rec.dict())
    # small log for debugging
    activity.logger.info("Validated %d records", len(validated))
    return validated