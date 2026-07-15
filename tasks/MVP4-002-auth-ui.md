# MVP4-002 — Auth UI (Login & Register)

**Статус:** закрыта ✅  
**Зависимость:** [MVP4-001-design-system.md](MVP4-001-design-system.md) — закрыта ✅

## Goal

Перевести страницы авторизации на дизайн из `Login.dc.html`: брендинг Reps, выбор роли, форма входа/регистрации, состояния ошибок и загрузки.

## План выполнения (выполнен)

1. **Общие auth-компоненты** — `AuthRoleSelector` (тёмный segmented), `AuthErrorBanner`, `auth.css`
2. **LoginPage** — `AuthLayout`, заголовок по шаблону, роль для ссылки на register, forgot password (placeholder)
3. **RegisterPage** — тот же визуальный язык, роль из `?role=`, `SegmentedControl` → `AuthRoleSelector`
4. **Интеграция** — импорт `auth.css` в `App.jsx`, правка `Button` loading state
5. **Проверка** — eslint `frontend/src`, `build:web`

## Requirements

- Обновить `LoginPage.jsx` и `RegisterPage.jsx` с использованием `AuthLayout` и UI-компонентов
- Визуальные элементы по шаблону:
  - логотип «R» в зелёном квадрате + название Reps
  - segmented control: Спортсмен / Тренер (на Register — предзаполнение роли из query/state)
  - поля Email, Пароль с uppercase labels
  - primary CTA зелёная кнопка «Войти» / «Зарегистрироваться»
  - ссылка на противоположное действие (войти ↔ регистрация)
- Сохранить текущую логику:
  - вызов API login/register
  - редирект по роли после успеха
  - отображение ошибок API в стиле шаблона (красный блок `#fdeaec`)
- Состояние loading на кнопке submit
- Адаптив: карточка max-width ~400px, padding 32–40px

## Acceptance Criteria

- [x] Login визуально соответствует `Login.dc.html`
- [x] Register использует тот же визуальный язык
- [x] Переключение роли работает и влияет на register payload
- [x] Ошибки и loading отображаются корректно
- [x] Существующие auth E2E flows не сломаны (логика API сохранена)
- [x] `npm run lint`, `npm run build:web` проходят (eslint на `frontend/src`)

## Dependencies

- [MVP4-001-design-system.md](MVP4-001-design-system.md)

## Декомпозиция

```
MVP4-002 — Auth UI
 ├── LoginPage + AuthLayout
 ├── RegisterPage (единый стиль)
 └── error/loading states
```

## Следующая задача

[MVP4-003-athlete-shell.md](MVP4-003-athlete-shell.md)
