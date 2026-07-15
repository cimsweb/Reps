# MVP2.1-001 — Project Setup

## Goal

Подготовить домен и контракты для **текстового ввода** планов и отчётов без ИИ: парсер, черновики, расширенные поля отчёта, API-описание. Без реализации парсера и UI.

## Requirements

### Домен

- `ParsedTrainingDraft` — результат парсинга: список `PlannedWorkout` черновиков + warnings (неоднозначности)
- `TrainingTextParser` — интерфейс в `domain/services/`:
    - `parse_day(text, planned_date) -> ParsedTrainingDraft`
    - `parse_week(text, start_date) -> ParsedTrainingDraft`
- `ReportTextParser` — интерфейс:
    - `parse_report_text(text) -> ReportDraft` (garmin_url, suggested_difficulty, suggested_mood, comment_body)
- `ReportDraft` — value object с опциональными полями и списком warnings
- Расширение `WorkoutCompletionReport`:
    - `garmin_url: str | None`
    - `raw_report_text: str | None` — исходная вставка спортсмена
- Расширение `TrainingPlan`:
    - `raw_text: str | None` — исходный текст тренера (день или неделя)

### Правила парсинга (зафиксировать в docs, не реализовывать здесь)

Поддерживаемые паттерны из реальных примеров:

| Паттерн                | Пример                                    | Структура                                     |
| ---------------------- | ----------------------------------------- | --------------------------------------------- |
| Заголовок дня          | `8 Июня`                                  | `planned_date`                                |
| Зона                   | `20 мин бега в 1-2 зоне`                  | exercise: name + details                      |
| Раунды                 | `5 раундов (40 сек каждая станция)`       | cycle name                                    |
| Список                 | `- Разножка на лавке`                     | exercise в текущем cycle                      |
| Отдых                  | `60 сек Отдых`, `отдых 3-4 мин`           | exercise или cycle separator                  |
| Тип по ключевым словам | `Велостанок`, `СБУ`, силовые              | `workout_type` inference                      |
| Garmin                 | URL `connect.garmin.com/.../activity/\d+` | `garmin_url`                                  |
| Нагрузка               | `нагрузка 6-7`, `нагрузка 5`              | `suggested_difficulty` (среднее или диапазон) |

### API (документация)

Новые эндпоинты в `docs/api/training.md`:

| Method | Path                                            | Назначение                            |
| ------ | ----------------------------------------------- | ------------------------------------- |
| POST   | `/coach/athletes/{id}/training-plans/parse`     | Превью парсинга без сохранения        |
| POST   | `/coach/athletes/{id}/training-plans/from-text` | Создать план из текста (day/week)     |
| PATCH  | `/coach/training-plans/{id}/raw-text`           | Обновить исходный текст + перепарсить |

Расширение `POST .../report`:

```json
{
    "difficulty_rating": 7,
    "mood_rating": 6,
    "comment": "...",
    "garmin_url": "https://connect.garmin.com/...",
    "raw_report_text": "Просмотрите мое занятие..."
}
```

### Инфраструктура

- Миграция: `raw_text` на `training_plans`, `garmin_url` + `raw_report_text` на `workout_completion_reports`
- Заготовки use cases: `ParseTrainingPlanText`, `CreateTrainingPlanFromText`, `ParseWorkoutReportText`
- Заглушки парсеров в `infrastructure/` (`NotImplementedError`)

### Не входит

- Реализация rule-based парсера (MVP2.1-002)
- LLM / AIService
- UI

## Acceptance Criteria

- [ ] Доменные типы и интерфейсы парсеров в `src/domain/`
- [ ] Миграция применяется на чистой БД
- [ ] API задокументирован в `docs/api/training.md` и `docs/db/training-schema.md`
- [ ] Заготовки use cases и smoke-тесты импорта
- [ ] `ruff`, `mypy`, `pytest` проходят

## Dependencies

- [mvp-2.md](mvp-2.md) полностью закрыт

## Декомпозиция

```
MVP2.1-001 — Project Setup
 ├── ParsedTrainingDraft, ReportDraft
 ├── TrainingTextParser, ReportTextParser (интерфейсы)
 ├── миграция raw_text, garmin_url
 └── API-контракты + заготовки use cases
```
