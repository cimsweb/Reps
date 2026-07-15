# MVP 4 — UI Redesign (Design System & Templates)

**Статус:** завершён (код); manual QA — по чеклисту в MVP4-008  
**Предыдущий:** [mvp-3.md](mvp-3.md)  
**Референсы дизайна:** `frontend/template/`

## Цель

Применить подготовленные UI-шаблоны ко всему React-приложению: единая дизайн-система, новые layout'ы для спортсмена и тренера, обновлённые формы и состояния. Backend для human chat — [MVP4-000](MVP4-000-conversations-backend.md); остальной scope MVP4 — фронтенд.

## Источники дизайна

| Шаблон             | Файл                      | Назначение                                                 |
| ------------------ | ------------------------- | ---------------------------------------------------------- |
| Авторизация        | `Login.dc.html`           | Login, Register                                            |
| Кабинет спортсмена | `Athlete Cabinet.dc.html` | Mobile-first: Сегодня / Неделя / Прогресс / Чат            |
| Кабинет тренера    | `Trainer Cabinet.dc.html` | Desktop sidebar: список, карточка спортсмена, чат, модалки |
| Отчёт о тренировке | `FeedbackForm.dc.html`    | RPE, ИИ, ссылка на активность, вопрос тренеру              |

Файл `support.js` — runtime Design Components, **не переносить** в production.

## Дизайн-система (из шаблонов)

### Типографика

- Шрифт: **Manrope** (400–800)
- Заголовки: `font-weight: 800`, 18–22px
- Метки полей: 11–12px, uppercase, `letter-spacing: 0.3–0.5px`, muted

### Цвета

| Токен                   | Значение              | Использование                             |
| ----------------------- | --------------------- | ----------------------------------------- |
| `--color-ink`           | `#12181a`             | Текст, кнопки primary dark, sidebar coach |
| `--color-accent-green`  | `#1f9d55`             | Primary CTA, активные табы, успех         |
| `--color-accent-blue`   | `#1f6feb`             | Ссылки, вторичные акценты                 |
| `--color-accent-orange` | `#ff8c1a`             | Вопросы, unread badge                     |
| `--color-bg-page`       | `#f3f5f1` / `#f6f7f5` | Фон приложения                            |
| `--color-bg-muted`      | `#e4e8e1` / `#f0f2ee` | Segmented controls, зоны карточек         |
| `--color-text-muted`    | `#8a9a96`             | Вторичный текст                           |
| `--color-text-body`     | `#42504d`             | Основной body                             |
| `--color-border`        | `#e7ece5` / `#e0e5dd` | Границы карточек и полей                  |
| `--color-error`         | `#c23b4a`             | Ошибки                                    |
| `--color-success-bg`    | `#f0f9f3`             | Отчёт спортсмена, success states          |

### Радиусы и отступы

- Карточки: 16–20px
- Кнопки и поля: 10–12px
- Pills / chips: 20px
- Модалки: 20px
- Стандартные отступы секций: 16–24px

### UI-паттерны

- Segmented control (роль, режим, вид списка)
- Status chips (Выполнено, Сегодня, Скоро, Пропущено)
- Week strip / 7-day grid
- Bottom tab bar (mobile athlete)
- Sidebar navigation (desktop coach)
- Карточки с `border: 1px solid var(--color-border)`
- Модальные окна с overlay `rgba(15,20,18,0.45)`
- Loading dots animation (`tp-dot`)

## Маппинг: шаблон → текущий код

| Экран шаблона                 | Текущие страницы / компоненты                                                       |
| ----------------------------- | ----------------------------------------------------------------------------------- |
| Login (роль + email + пароль) | `LoginPage`, `RegisterPage`                                                         |
| Athlete: Сегодня              | `AthleteDashboard` → `AthleteTrainingSections`, план дня                            |
| Athlete: Неделя               | список дней плана (сейчас в dashboard)                                              |
| Athlete: Прогресс             | `GarminSuccessChart`, личные рекорды, `GarminIntegrationSection`                    |
| Athlete: Чат                  | `GET/POST /athlete/conversations/*` — [MVP4-000](MVP4-000-conversations-backend.md) |
| FeedbackForm                  | `WorkoutReportForm`, `AthleteReportAgentChatPage`                                   |
| Coach: список спортсменов     | `CoachDashboard`                                                                    |
| Coach: карточка спортсмена    | `CoachAthletePage`                                                                  |
| Coach: чат                    | `GET/POST /coach/conversations/*` — [MVP4-000](MVP4-000-conversations-backend.md)   |
| Coach: приглашение            | форма invite в `CoachDashboard` → модалка                                           |
| Coach: + тренировка / неделя  | `CoachCreateTrainingPlanPage`, `CoachPlanAgentChatPage`                             |
| Garmin OAuth callback         | `AthleteGarminCallbackPage`                                                         |
| Admin                         | `AdminDashboard` (в шаблонах нет — минимальный редизайн в токенах)                  |

## Архитектура фронтенда (целевая)

```
frontend/src/
  styles/
    tokens.css          # CSS-переменные дизайн-системы
    base.css            # reset, typography, globals
  components/
    ui/                 # Button, Input, Card, Badge, Modal, SegmentedControl…
    layout/
      AuthLayout.jsx
      AthleteShell.jsx      # mobile frame + bottom tabs
      CoachShell.jsx        # sidebar + main
    athlete/            # экраны и блоки кабинета спортсмена
    coach/              # экраны и блоки кабинета тренера
  pages/                # тонкие обёртки над layout + screens
```

Принцип: **страницы остаются точками входа роутера**, визуальная логика уходит в `layout/` и `components/`.

## Принципы реализации

1. **Reference-first** — сверять пиксели и паттерны с `frontend/template/*.dc.html`, не изобретать новый стиль.
2. **Токены, не хардкод** — цвета и радиусы только через CSS variables.
3. **Сохранить поведение** — все существующие API-вызовы, роуты и user flows работают как до редизайна.
4. **Mobile-first для спортсмена** — max-width ~393px на мобильных, адаптив на tablet/desktop.
5. **Desktop-first для тренера** — sidebar 232px, main content fluid.
6. **Постепенная миграция** — после MVP4-001 можно параллелить athlete/coach ветки, но merge только после прохождения lint/build.

## Вне scope MVP 4

- Новые backend API (кроме conversations — MVP4-000)
- Изменение доменной логики и use cases
- Новые фичи (кроме визуальных placeholder для чата)
- Удаление `frontend/template/` (остаётся как reference)

## Задачи

| ID                                             | Название                     | Зависимости        |
| ---------------------------------------------- | ---------------------------- | ------------------ |
| [MVP4-000](MVP4-000-conversations-backend.md)  | Conversations Backend        | MVP 3 закрыт       |
| [MVP4-001](MVP4-001-design-system.md)          | Design System & Foundation   | MVP4-000           |
| [MVP4-002](MVP4-002-auth-ui.md)                | Auth UI (Login, Register)    | MVP4-001           |
| [MVP4-003](MVP4-003-athlete-shell.md)          | Athlete Shell & Navigation   | MVP4-001           |
| [MVP4-004](MVP4-004-athlete-screens.md)        | Athlete Screens              | MVP4-003           |
| [MVP4-005](MVP4-005-coach-shell.md)            | Coach Shell & Dashboard      | MVP4-001           |
| [MVP4-006](MVP4-006-coach-athlete-training.md) | Coach Athlete & Training     | MVP4-005           |
| [MVP4-007](MVP4-007-chat-ai-modals.md)         | Chat, AI Flows & Modals      | MVP4-004, MVP4-006 |
| [MVP4-008](MVP4-008-polish-qa.md)              | Integrations, Admin & Polish | MVP4-002–007       |

## Порядок выполнения

```
MVP4-000 (conversations backend)
MVP4-001 (foundation)
    ├── MVP4-002 (auth)
    ├── MVP4-003 → MVP4-004 (athlete)
    └── MVP4-005 → MVP4-006 (coach)
            └── MVP4-007 (chat + AI + modals)
                    └── MVP4-008 (polish & QA)
```

## Критерии готовности MVP 4

- [x] Все страницы используют дизайн-систему (токены + базовые компоненты)
- [x] Login / Register соответствуют `Login.dc.html`
- [x] Кабинет спортсмена: bottom tabs, экраны Сегодня / Неделя / Прогресс / Чат
- [x] Кабинет тренера: sidebar, список, карточка спортсмена, invite modal
- [x] FeedbackForm соответствует шаблону; AI-отчёт в том же визуальном языке
- [x] Garmin UI встроен в «Прогресс» без регрессии функциональности
- [x] `npm run build:web` и `eslint frontend/src` проходят
- [ ] Manual QA checklist (см. MVP4-008) и end-to-end flows в браузере

## Команды проверки

```bash
npm run lint
npm run format:check
npm run build:web
```
