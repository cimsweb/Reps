# MVP2.1-003 — Indexing

## Goal

Обеспечить хранение и выборку исходных текстов планов и отчётов с Garmin-ссылками; поддержать пере-парсинг при обновлении `raw_text`.

## Requirements

### Схема БД

- `training_plans.raw_text` — TEXT, nullable
- `workout_completion_reports.garmin_url` — VARCHAR, nullable, индекс не обязателен на MVP
- `workout_completion_reports.raw_report_text` — TEXT, nullable

### Инварианты

- `raw_text` заполняется только при создании через `from-text` или PATCH raw-text
- Структурный план (MVP 2) может не иметь `raw_text` — null допустим
- `garmin_url` уникальность не требуется (разные отчёты могут ссылаться на одну активность теоретически)

### Репозитории

- `TrainingPlanRepository` — save/load `raw_text`
- `WorkoutReportRepository` — save/load `garmin_url`, `raw_report_text`
- `UpdateTrainingPlanFromRawTextUseCase` — перепарсить и заменить workouts (только будущие даты или весь план — зафиксировать правило: **только даты ≥ сегодня**)

### Ownership

- Те же правила `TrainingAccessGuard`, что MVP 2
- Athlete видит только свои `raw_report_text`

## Acceptance Criteria

- [ ] Миграция идемпотентна, откат возможен
- [ ] CRUD raw_text и report extensions через репозитории
- [ ] Перепарсинг raw_text обновляет структуру без потери отчётов по прошедшим дням
- [ ] Integration-тесты на cascade и unique report per workout
- [ ] `ruff`, `mypy`, `pytest` проходят

## Dependencies

- [MVP2.1-002-data-ingestion.md](MVP2.1-002-data-ingestion.md) закрыт

## Декомпозиция

```
MVP2.1-003 — Indexing
 ├── поля raw_text, garmin_url, raw_report_text
 ├── репозитории + update from raw text
 └── правила перепарсинга (будущие даты)
```
