# MVP4-008 — Integrations, Admin & Polish

## Goal

Завершить MVP 4: второстепенные страницы, empty/loading/error states, responsive QA, удаление legacy CSS, финальная проверка всех user flows.

## Requirements

### Garmin OAuth Callback

- `AthleteGarminCallbackPage` — минимальный centered layout в токенах дизайн-системы
- Success / error states с понятными CTA «Вернуться в кабинет»

### Admin Dashboard

- В шаблонах нет — применить токены, Card, Button, типографику
- Сохранить всю функциональность без redesign wireframes

### Cross-cutting polish

- Единые empty states (иконка + текст + CTA)
- Единые error banners (`#fdeaec` / `#c23b4a`)
- Loading: `LoadingDots` вместо разрозненных спиннеров
- Focus visible для a11y (keyboard navigation)
- Responsive:
    - athlete: 320px–768px+
    - coach: 1024px+ sidebar; collapse/hamburger на узких экранах (минимально)
- Удалить неиспользуемые классы из старого `App.css`
- Проверить все routes в `App.jsx` / router config

### QA checklist (manual)

- [ ] Login athlete → athlete tabs → submit report
- [ ] Login coach → list → athlete → view report
- [ ] Coach invite athlete
- [ ] Garmin connect → sync → progress chart
- [ ] AI report polish flow
- [ ] AI plan generation flow
- [ ] Logout / session expiry UI

## Acceptance Criteria

- [x] Все 10 страниц используют дизайн-систему (без raw hex в JSX, кроме исключений в charts)
- [x] Garmin callback и Admin не выбиваются визуально
- [x] Legacy CSS очищен или сведён к минимуму
- [ ] QA checklist пройден
- [x] `npm run lint`, `npm run format:check`, `npm run build:web` проходят (eslint: `frontend/src`; format: изменённые файлы)
- [ ] Нет console errors на основных flows

## Dependencies

- [MVP4-002-auth-ui.md](MVP4-002-auth-ui.md) … [MVP4-007-chat-ai-modals.md](MVP4-007-chat-ai-modals.md)

## Декомпозиция

```
MVP4-008 — Polish & QA
 ├── Garmin callback + Admin restyle ✅
 ├── empty/loading/error states ✅
 ├── responsive pass + a11y basics ✅
 ├── App.css cleanup ✅
 └── manual QA checklist
```

## Реализовано

- `StatusPage` — centered layout для Garmin callback и Admin
- `ErrorBanner`, обновлённые `EmptyState` и `LoadingMessage` (LoadingDots)
- `AthleteGarminCallbackPage` → `/athlete/today`, CTA при ошибке
- `AdminDashboard` — Card, Button, таблица в токенах
- Coach mobile: hamburger + overlay sidebar до 1023px
- `ProtectedRoute` — LoadingMessage в StatusPage
- Удалён неиспользуемый `DashboardLayout.jsx`
- `.form-error` приведён к стилю error banner
