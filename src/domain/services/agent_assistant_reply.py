from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from domain.entities.plan_scope import PlanScope
from domain.services.training_text_parsing import ParsedTrainingDraft, ReportDraft


@dataclass(frozen=True, slots=True)
class TrainingPlanDraft:
    """AI-suggested training plan draft before user confirmation."""

    start_date: date
    scope: PlanScope
    raw_text: str | None = None
    parsed: ParsedTrainingDraft | None = None


@dataclass(frozen=True, slots=True)
class AgentQuestionReply:
    """Assistant asks a clarifying question."""

    type: Literal["question"] = "question"
    text: str = ""


@dataclass(frozen=True, slots=True)
class AgentPlanDraftReply:
    """Assistant returns a training plan draft."""

    type: Literal["plan_draft"] = "plan_draft"
    draft: TrainingPlanDraft | None = None


@dataclass(frozen=True, slots=True)
class AgentReportDraftReply:
    """Assistant returns a workout report draft."""

    type: Literal["report_draft"] = "report_draft"
    draft: ReportDraft | None = None


AgentAssistantReply = AgentQuestionReply | AgentPlanDraftReply | AgentReportDraftReply
