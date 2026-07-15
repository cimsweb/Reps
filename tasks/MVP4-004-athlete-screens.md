# MVP4-004 — Athlete Screens (Today, Week, Progress)

## Goal

Реализовать контент вкладок кабинета спортсмена по шаблону `Athlete Cabinet.dc.html`, подключив существующие API и компоненты тренировок / Garmin.

## Requirements

### Вкладка «Сегодня»
- Карточка тренировки дня: тип, статус chip, блоки Разминка / Основная / Заминка
- Темп и пульсовая зона (из плана)
- Встроить `FeedbackForm` (см. MVP4-007) или промежуточную обёртку
- Состояния: план есть / план пуст / отчёт отправлен
- `WeekStrip` с выбором дня (синхронизация с данными плана)

### Вкладка «Неделя»
- Список дней недели: дата, тип тренировки, status chip
- Клик по дню → переход на «Сегодня» с выбранным днём
- Пустое состояние, если план не назначен

### Вкладка «Прогресс»
- Переключатель периода Месяц / Год (segmented)
- График успешности: рестайл `GarminSuccessChart` под шаблон (line + bar)
- Сетка личных рекордов (карточки 2 колонки)
- Секция Garmin: рестайл `GarminIntegrationSection` (подключение, синхронизация, список активностей)
- Сохранить все текущие API-вызовы Garmin

### Вкладка «Чат»
- Визуал по шаблону: список сообщений, bubbles coach/athlete
- Интеграция с API conversations (MVP4-000)

### Общее
- Миграция логики из монолитного `AthleteDashboard.jsx` в `components/athlete/*`
- Сохранить invite banner / coach info, если есть в текущем UI

## Acceptance Criteria

- [x] Четыре вкладки заполнены контентом (чат — placeholder допустим)
- [x] Данные плана и отчётов отображаются как до редизайна
- [x] Garmin: connect, sync, chart, activities работают
- [x] Week strip и список недели согласованы по выбранному дню
- [x] Визуал соответствует `Athlete Cabinet.dc.html`
- [x] `npm run lint`, `npm run build:web` проходят

## Status

**Done** — `TodayScreen`, `WeekScreen`, `ProgressScreen`, `ChatScreen` в `components/athlete/`; общий `AthleteDayContext` для week strip; conversations API на фронте.

## Dependencies

- [MVP4-003-athlete-shell.md](MVP4-003-athlete-shell.md)

## Декомпозиция

```
MVP4-004 — Athlete Screens
 ├── TodayScreen (plan card + week strip)
 ├── WeekScreen (day list)
 ├── ProgressScreen (charts + PR + Garmin)
 └── ChatScreen (placeholder UI)
```
