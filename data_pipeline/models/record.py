from pydantic import BaseModel, Field
from typing import Optional

class UserRecord(BaseModel):
    user_id: int
    name: str
    age: int = Field(..., ge=0, le=120)
    email: Optional[str] = None
