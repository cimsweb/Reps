# MVP4-005 — Coach Shell & Dashboard

## Goal

Внедрить desktop-оболочку тренера из `Trainer Cabinet.dc.html`: тёмный sidebar, список спортсменов, переключение видов, модалка приглашения.

## Requirements

### CoachShell
- Sidebar ширина 232px, фон `#12181a`
- Логотип Reps + подпись «Кабинет тренера»
- Навигация: **Спортсмены**, **Чат** (badge unread — static 0 до backend)
- Main area: светлый фон `#f3f5f1`, padding 28–32px
- Header main: заголовок раздела + кнопки действий

### CoachDashboard (view: list)
- Заголовок «Мои спортсмены» + кнопка «Пригласить»
- Segmented control: **Карточки** / **Компактно**
- Карточный вид: avatar, имя, уровень, compliance %, status chip, последняя активность
- Компактный вид: строки таблицы-списка
- Клик по спортсмену → `CoachAthletePage` (внутри того же shell)
- Пустое состояние: нет спортсменов + CTA пригласить

### Invite Modal
- По шаблону: email, имя (optional), submit, success state
- Подключить существующий API invite
- Loading dots на кнопке

### Роутинг
- `/coach` — list view
- `/coach/chat` — chat view (shell, контент в MVP4-007)
- `/coach/athletes/:id` — athlete detail (MVP4-006)

## Acceptance Criteria

- [x] `CoachShell` с sidebar и main area
- [x] Список спортсменов: card + compact modes
- [x] Invite modal работает end-to-end
- [x] Навигация sidebar переключает list / chat routes
- [x] Визуал соответствует `Trainer Cabinet.dc.html` (list section)
- [x] `npm run lint`, `npm run build:web` проходят

## Status

**Done** — `CoachLayout`, `CoachListScreen`, `InviteAthleteModal`, `/coach/chat` placeholder, nested coach routes.

## Dependencies

- [MVP4-001-design-system.md](MVP4-001-design-system.md)

## Декомпозиция

```
MVP4-005 — Coach Shell
 ├── CoachShell + sidebar nav
 ├── CoachDashboard list (cards + compact)
 └── InviteAthleteModal
```
