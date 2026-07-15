# MVP4-006 — Coach Athlete Detail & Training

## Goal

Перевести карточку спортсмена и управление планом на дизайн из `Trainer Cabinet.dc.html` (athlete view): недельная сетка, детали дня, отчёты, Garmin, создание тренировок.

## Requirements

### CoachAthletePage (view: athlete)
- Back link «← Все спортсмены»
- Header: avatar lg, имя, уровень, compliance %
- Action buttons: «+ Тренировка», «+ Неделя целиком»
- 7-day grid: день, тип, status dot, status label; клик выбирает active day
- Detail card активного дня:
  - warmup / main / cooldown grid
  - tempo + HR zone
  - блок «Отчёт спортсмена» (green card + RPE + activity link)
  - empty states: нет плана / нет отчёта
- Рестайл `GarminIntegrationSection` для coach context (read-only stats)
- Сохранить существующие data fetching и mutations

### Training creation flow
- Кнопки открывают существующие flows:
  - `CoachCreateTrainingPlanPage` — в modal или dedicated route внутри shell
  - AI plan generation UI — согласовать с MVP4-007
- Week/day picker pills в модалке (если переносим modal из шаблона)

### Состояния
- Loading skeletons для плана и отчётов
- Error banner в стиле дизайн-системы

## Acceptance Criteria

- [x] `CoachAthletePage` соответствует athlete view в шаблоне
- [x] 7-day grid и detail card работают с реальными данными
- [x] Отчёты спортсмена отображаются (текст, RPE, ссылка)
- [x] Garmin-секция coach не регрессирует
- [x] Создание плана доступно из карточки спортсмена
- [x] `npm run lint`, `npm run build:web` проходят

## Status

**Done** — `CoachAthleteScreen`, `CoachWeekGrid`, `CoachDayDetailCard`, `useCoachAthleteWeekData`; кнопки ведут на create flow с `?scope=day|week`.

## Dependencies

- [MVP4-005-coach-shell.md](MVP4-005-coach-shell.md)

## Декомпозиция

```
MVP4-006 — Coach Athlete
 ├── CoachAthletePage layout
 ├── week grid + day detail card
 ├── athlete report block
 └── Garmin + plan creation entry points
```
