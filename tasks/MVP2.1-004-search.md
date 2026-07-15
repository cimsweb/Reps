# MVP2.1-004 — Search

## Goal

Дать тренеру и спортсмену **читаемое** представление плана и отчётов: экспорт в текст, отображение Garmin в итогах периода.

## Requirements

### Экспорт плана в текст

- `FormatTrainingPlanAsText` — domain service: структура → текст, похожий на ввод тренера
- Формат блока дня:

```
8 Июня

Суставная разминка

20 мин бега в 1-2 зоне
...
```

- API: `GET /coach/athletes/{id}/training-plans/text?period=week&anchor_date=...`
- API: `GET /athlete/training-plans/text?...` — свой план

### Read models

Расширить существующие query use cases (MVP2-004):

- `PlannedWorkoutView` — опционально `has_raw_source: bool` на уровне плана
- `WorkoutReportView` — поля `garmin_url`, `raw_report_text` (athlete + coach)
- В списке итогов за неделю/месяц — иконка/ссылка Garmin если `garmin_url` задан

### Parse preview (read path)

- `POST .../parse` уже в MVP2.1-002; здесь — стабильный контракт ответа для UI:

```json
{
  "draft": { "workouts": [...] },
  "warnings": ["Строка 12: не распознан формат, добавлено в «Прочее»"],
  "detected_scope": "week"
}
```

### Не входит

- Сравнение план vs факт по метрикам Garmin (MVP 3)
- PDF export

## Acceptance Criteria

- [ ] Round-trip: from-text → export text сохраняет смысл (snapshot, не побайтово)
- [ ] Coach и athlete получают text export за week/month
- [ ] Итоги периода включают garmin_url
- [ ] HTTP-тесты на новые GET endpoints
- [ ] `ruff`, `mypy`, `pytest` проходят

## Dependencies

- [MVP2.1-003-indexing.md](MVP2.1-003-indexing.md) закрыт

## Декомпозиция

```
MVP2.1-004 — Search
 ├── FormatTrainingPlanAsText
 ├── GET plan as text (coach + athlete)
 └── расширенные WorkoutReportView в period queries
```
