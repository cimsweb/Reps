# MVP4-003 — Athlete Shell & Navigation

## Goal

Внедрить mobile-first оболочку кабинета спортсмена из `Athlete Cabinet.dc.html`: phone frame, header, bottom tab bar и роутинг между вкладками.

## Requirements

- `AthleteShell` с фоном `#e4e8e1` (desktop) / full-bleed (mobile)
- Контейнер контента: max-width 393px, белый фон, скругление 24px на desktop
- Header: приветствие, имя спортсмена, аватар (инициалы)
- Bottom tab bar (4 вкладки):
  - **Сегодня** — default route
  - **Неделя**
  - **Прогресс**
  - **Чат**
- Навигация через React Router (nested routes или state + URL hash/query — зафиксировать один подход)
- Активная вкладка: зелёный акцент `#1f9d55`, неактивная — muted
- Компонент `WeekStrip` — горизонтальная полоса дней недели с точками статуса (переиспользуется на экране «Сегодня»)
- Рефакторинг `AthleteDashboard.jsx`: стать layout-роутером или thin wrapper над shell + outlet
- Garmin OAuth callback (`AthleteGarminCallbackPage`) — вне shell или с минимальным layout

## Acceptance Criteria

- [x] Athlete routes обёрнуты в `AthleteShell`
- [x] Переключение вкладок работает без перезагрузки
- [x] Header и tab bar соответствуют шаблону
- [x] `WeekStrip` вынесен в переиспользуемый компонент
- [x] Desktop: phone frame по центру; mobile: full width
- [x] `npm run lint`, `npm run build:web` проходят

## Status

**Done** — nested routes `/athlete/today|week|progress|chat`, `AthleteLayout`, placeholder-вкладки, контент dashboard на «Сегодня» с `WeekStrip`. Garmin callback и AI report — вне shell.

## Dependencies

- [MVP4-001-design-system.md](MVP4-001-design-system.md)

## Декомпозиция

```
MVP4-003 — Athlete Shell
 ├── AthleteShell + routing
 ├── bottom tab bar
 ├── header + avatar
 └── WeekStrip component
```
