# MVP2.1-002 — Data Ingestion

## Goal

Реализовать **rule-based** парсинг текста планов и отчётов, создание плана из текста и расширенную отправку отчёта. **Без ИИ.**

## Requirements

### Парсер плана (`RuleBasedTrainingTextParser`)

Реализация в `infrastructure/parsing/` (или `domain/services/` если чистая логика без I/O).

**Вход недели** — один из форматов:

1. **Табличный** — 7 колонок / ячеек (как Excel), разделитель `\t` между днями
2. **Блочный** — последовательность блоков `ДД Месяц` + текст до следующей даты
3. **С явной датой начала** — если в тексте нет дат, привязка к `start_date` + порядок дней

**Алгоритм (высокий уровень):**

1. Сегментация по дням
2. Определение `workout_type` по ключевым словам (бег/вело/зал/велостанок/СБУ)
3. Разбиение на циклы: «разминка», «раунды», «растяжка», блоки между пустыми строками
4. Строки со списком `- ...` → `WorkoutExercise`
5. Строки с зонами/временем → exercise с `details`
6. Warnings при нераспознанных строках (не падать, включить в `details` fallback-цикла)

**Эталонные тесты** — неделя 8–14 июня из product brief:

- 7 дней, разные типы (run/bike/gym)
- День 12 июня: два блока раундов с отдыхом между ними
- День 13 июня: `120мин бега во 2-й пульсовой зоне`

### Парсер отчёта (`RuleBasedReportTextParser`)

- Извлечение Garmin URL regex
- Паттерны нагрузки: `нагрузка\s*(\d+)(?:\s*[-–]\s*(\d+))?` → среднее в `suggested_difficulty`
- Остальной текст → `comment_body`
- Опционально: «N минут» в конце → дополнение к comment

### Use cases

- `ParseTrainingPlanTextUseCase` — только превью, без записи в БД
- `CreateTrainingPlanFromTextUseCase` — парсинг + сохранение + `raw_text`
- `SubmitWorkoutReportUseCase` — расширить: принимать `garmin_url`, `raw_report_text`; валидация URL

### Валидация

- `garmin_url` — только `https://connect.garmin.com/` (как в MVP 1 coaching feedback)
- При парсинге отчёта: если есть `suggested_difficulty`, не сохранять автоматически — только в ответе parse-preview; финальные rating задаёт клиент
- Конфликт даты при `from-text` — как в MVP 2 (409)

### Логирование

- `training_plan_parsed`, `training_plan_from_text_created`
- `report_text_parsed`, `workout_report_submitted` (с флагом has_garmin)

## Acceptance Criteria

- [ ] Парсер недели 8–14 июня даёт 7 workouts с ожидаемой структурой (snapshot-тест)
- [ ] Парсер дня работает для одного блока текста
- [ ] Warnings возвращаются при нераспознанных строках, парсинг не падает
- [ ] `POST .../parse` и `POST .../from-text` работают для coach
- [ ] Отчёт с Garmin-текстом сохраняет URL и raw text
- [ ] Unit-тесты парсера ≥ 20 кейсов; integration-тесты на from-text и report
- [ ] `ruff`, `mypy`, `pytest` проходят

## Dependencies

- [MVP2.1-001-project-setup.md](MVP2.1-001-project-setup.md) закрыт

## Декомпозиция

```
MVP2.1-002 — Data Ingestion
 ├── RuleBasedTrainingTextParser (день / неделя)
 ├── RuleBasedReportTextParser (Garmin, нагрузка)
 ├── use cases parse + from-text + report
 └── HTTP routes + тесты на эталонных примерах
```
