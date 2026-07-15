import json
from pathlib import Path

from pydantic import BaseModel

from application.dto.ai import ChatCompletion, ChatMessage
from application.ports.ai_service import AIService
from domain.entities.agent_message_role import AgentMessageRole
from domain.entities.agent_session_kind import AgentSessionKind

_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_week_draft_text() -> str:
    fixture_path = _FIXTURES_DIR / "week_draft_raw_text.txt"
    if fixture_path.exists():
        return fixture_path.read_text(encoding="utf-8")
    return "8 Июня\n\nСуставная разминка"


class StubAIService:
    """Deterministic AI service driven by session kind and user message count."""

    def __init__(
        self,
        *,
        session_kind: AgentSessionKind,
        responses: list[str] | None = None,
    ) -> None:
        self._session_kind = session_kind
        self._responses = responses

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        response_schema: type[BaseModel] | None = None,
    ) -> ChatCompletion:
        del response_schema
        user_count = sum(1 for message in messages if message.role is AgentMessageRole.USER)
        content = self._pick_response(user_count)
        return ChatCompletion(content=content, model="stub")

    def _pick_response(self, user_count: int) -> str:
        if self._responses is not None:
            index = min(max(user_count - 1, 0), len(self._responses) - 1)
            return self._responses[index]

        if self._session_kind is AgentSessionKind.PLAN_CREATION:
            return self._plan_response(user_count)
        return self._report_response(user_count)

    def _plan_response(self, user_count: int) -> str:
        if user_count <= 1:
            return json.dumps(
                {
                    "type": "question",
                    "text": "Какой объём длительного бега в субботу — 90 или 120 минут?",
                },
                ensure_ascii=False,
            )
        return json.dumps(
            {
                "type": "plan_draft",
                "start_date": "2024-06-08",
                "scope": "week",
                "raw_text": _load_week_draft_text(),
            },
            ensure_ascii=False,
        )

    def _report_response(self, user_count: int) -> str:
        if user_count <= 1:
            return json.dumps(
                {
                    "type": "question",
                    "text": "Что было самым тяжёлым на тренировке?",
                },
                ensure_ascii=False,
            )
        if user_count == 2:
            return json.dumps(
                {
                    "type": "question",
                    "text": "Как настроение после тренировки?",
                },
                ensure_ascii=False,
            )
        return json.dumps(
            {
                "type": "report_draft",
                "suggested_difficulty_rating": 5,
                "suggested_mood_rating": 7,
                "comment_body": "Тяжело на интервалах, в целом нормально",
                "garmin_url": None,
            },
            ensure_ascii=False,
        )


def build_stub_ai_service(session_kind: AgentSessionKind) -> StubAIService:
    return StubAIService(session_kind=session_kind)


def satisfies_ai_service_protocol(service: StubAIService) -> AIService:
    return service
