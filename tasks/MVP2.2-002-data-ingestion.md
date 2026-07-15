# MVP2.2-002 — Data Ingestion

## Goal

Реализовать диалоговые use cases: **генерация черновика плана** и **оформление отчёта** через ИИ с обязательным подтверждением пользователя.

## Requirements

### Coach — создание плана с ИИ

**`StartPlanAgentSessionUseCase`**

- Вход: `athlete_id`, `start_date`, опционально `initial_brief` (например «бег зал бег отдых бег вело бег»)
- Создаёт сессию, если есть brief — сразу первый вызов AIService

**`SendPlanAgentMessageUseCase`**

- Добавляет user message, вызывает AIService с историей + system prompt
- Ответ ассистента — один из:
    - **question** — текст вопроса (показать в чате)
    - **draft** — `TrainingPlanDraft` (текст недели + structured workouts)
- При draft — также прогнать через `TrainingTextParser` MVP 2.1 для валидации структуры; warnings прикрепить к ответу

**`ConfirmPlanAgentDraftUseCase`**

- Вход: session_id, опциональные правки draft
- Сохраняет через существующий `CreateTrainingPlanFromText` или structured create
- Закрывает сессию `completed`
- **Не вызывается автоматически**

**Сценарий уточняющих вопросов (пример):**

```
Тренер: «бег зал бег отдых бег вело бег, неделя с 8 июня»
Агент: «Какой объём длительного бега в субботу — 90 или 120 минут?»
Тренер: «120»
Агент: [draft недели в стиле реального примера]
```

### Athlete — отчёт с ИИ

**`StartReportAgentSessionUseCase`**

- Привязка к `planned_workout_id`
- Контекст в prompt: краткое описание плана на этот день (из planned workout)

**`SendReportAgentMessageUseCase`**

- Вход спортсмена: «нагрузка 5», «тяжело на интервалах»
- Агент задаёт 1–3 уточняющих вопроса за сессию (не все сразу):
    - «Что было самым тяжёлым?»
    - «Как настроение после тренировки?»
    - «Есть ссылка на Garmin?»
- Когда достаточно данных — возвращает `ReportDraft` с suggested ratings

**`ConfirmReportAgentDraftUseCase`**

- Спортсмен может изменить ratings перед submit
- Вызов `SubmitWorkoutReportUseCase` MVP 2.1

### Guardrails

- System prompt: не назначать медицинские диагнозы, не менять план без тренера
- Валидация JSON-ответа от LLM (pydantic); при ошибке — retry 1 раз, затем ошибка `ai_response_invalid`
- Логировать `ai_session_started`, `ai_message_sent`, `ai_draft_proposed`, `ai_confirmed` без полного текста в prod (только hash/length)

### Fallback

- При `AIServiceError` — HTTP 503 + `fallback: "manual"` в теле; UI переключает на MVP 2.1

## Acceptance Criteria

- [ ] Диалог плана: brief → вопрос → draft на stub с фиксированными ответами
- [ ] Confirm сохраняет план в БД
- [ ] Диалог отчёта: «нагрузка 5» → вопросы → draft → confirm → report в БД
- [ ] Лимит сообщений и таймаут обрабатываются
- [ ] Unit-тесты с StubAIService; integration с recorded responses
- [ ] `ruff`, `mypy`, `pytest` проходят

## Dependencies

- [MVP2.2-001-project-setup.md](MVP2.2-001-project-setup.md) закрыт
- MVP 2.1 парсер и report submit работают

## Декомпозиция

```
MVP2.2-002 — Data Ingestion
 ├── plan agent: start → message → confirm
 ├── report agent: start → message → confirm
 ├── guardrails + fallback
 └── HTTP routes training-ai
```
