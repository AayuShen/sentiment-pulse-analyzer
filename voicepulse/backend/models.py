from datetime import datetime
from typing import Annotated, Any
from pydantic import BaseModel, Field, BeforeValidator
from bson import ObjectId

def _validate_oid(v: Any) -> str:
    if isinstance(v, ObjectId):
        return str(v)
    if v is not None and ObjectId.is_valid(v):
        return str(v)
    raise ValueError("Invalid ObjectId")

PyObjectId = Annotated[str, BeforeValidator(_validate_oid)]

class Segment(BaseModel):
    speaker: str
    start: float
    end: float
    text: str

class Turn(BaseModel):
    speaker: str
    text: str
    tag: str
    score: float

class Call(BaseModel):
    cid: str
    rec: str
    transcript: list[Segment] = []
    tag: str = ""
    score: float = 0.0
    turns: list[Turn] = []
    summary: str = ""
    topics: list[str] = []
    shift: str = ""
    brief: str = ""
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class Customer(BaseModel):
    cid: str
    name: str = ""
    notes: list[str] = []
    calls: list[str] = []


