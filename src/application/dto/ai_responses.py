from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class AIQuestionPayload(BaseModel):
    type: Literal["question"] = "question"
    text: str = Field(min_length=1)


class AIPlanDraftPayload(BaseModel):
    type: Literal["plan_draft"] = "plan_draft"
    start_date: date
    scope: Literal["day", "week"]
    raw_text: str = Field(min_length=1)


class AIReportDraftPayload(BaseModel):
    type: Literal["report_draft"] = "report_draft"
    suggested_difficulty_rating: int | None = Field(default=None, ge=0, le=10)
    suggested_mood_rating: int | None = Field(default=None, ge=0, le=10)
    comment_body: str | None = None
    garmin_url: str | None = None
