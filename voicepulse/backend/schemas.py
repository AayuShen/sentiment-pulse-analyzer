from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from models import PyObjectId, Turn

class CallOut(BaseModel):
    id: PyObjectId
    cid: str
    rec: str
    tag: str
    score: float
    summary: str
    topics: list[str]
    shift: str
    brief: str
    processed_at: datetime
    turns: list[Turn] = []

class CallBrief(BaseModel):
    cid: str
    brief: str
    tag: str
    score: float
    processed_at: datetime

class SentimentHistory(BaseModel):
    cid: str
    calls: list[CallOut]

class AnalyticsSummary(BaseModel):
    total: int
    unique_customers: int = 0
    tag_counts: dict[str, int]
    negative_pct: float
    positive_pct: float = 0.0
    avg_score: float

class TrendPoint(BaseModel):
    week: str
    tag: str
    count: int

class JobStatus(BaseModel):
    job_id: str
    status: str
    result: Optional[dict] = None
