# MVP4-001 — Design System & Foundation

**Статус:** закрыта ✅  
**Зависимость:** [MVP4-000-conversations-backend.md](MVP4-000-conversations-backend.md) — закрыта ✅

## Goal

Заложить единую дизайн-систему Reps на основе шаблонов `frontend/template/`: CSS-токены, базовые UI-компоненты и layout-оболочки. Заменить ad-hoc стили в `App.css` на структурированную систему.

---

## Аудит: сделано ли уже?

**Вердикт: нет, задачу нужно выполнять с нуля.**

| Требование MVP4-001 | Текущее состояние | Статус |
|---------------------|-------------------|--------|
| `frontend/src/styles/tokens.css` | Папки `styles/` нет | ❌ |
| `frontend/src/styles/base.css` | — | ❌ |
| Шрифт Manrope | `App.css`: `Inter, system-ui` | ❌ |
| Палитра из шаблонов (`#12181a`, `#1f9d55`, `#f3f5f1`…) | Старая синяя тема (`#1f6feb`, `#f4f7fb`, `#142033`) | ❌ |
| `components/ui/*` (Button, Input, Card…) | Нет; только разрозненные компоненты | ❌ |
| `layout/AuthLayout` | `LoginPage` использует `.page` + `.card` из App.css | ❌ |
| `layout/AthleteShell` | `DashboardLayout` — универсальная карточка, не mobile tabs | ❌ |
| `layout/CoachShell` | Нет sidebar 232px | ❌ |
| Рефакторинг `App.css` | ~781 строка монолита, 118 CSS-классов | ❌ |
| Существующие страницы работают | Да, MVP 3 UI на старых стилях | ✅ (не ломать) |

**Что уже есть и можно переиспользовать при миграции (не заменяет MVP4-001):**

- `DashboardLayout.jsx` — временная обёртка до AthleteShell/CoachShell
- `StatusBadge.jsx` — только invitation status, не design-system chips
- `EmptyState`, `FieldError`, `LoadingMessage` — перенести на токены в MVP4-008
- `AgentChatLayout.jsx` — bubbles для AI; стилизовать под новую систему в MVP4-007
- Garmin/training компоненты — работают, миграция в MVP4-004…006

**MVP4-000 (backend чат)** к дизайн-системе не относится — блокеров для старта MVP4-001 нет.

---

## План выполнения (порядок шагов)

### Шаг 1 — Стили и токены (~2–3 ч)

1. Создать `frontend/src/styles/tokens.css` по [mvp-4.md](mvp-4.md) и шаблонам:
   - цвета: `--color-ink`, `--color-accent-green`, `--color-accent-blue`, `--color-accent-orange`, backgrounds, borders, error, success
   - `--radius-sm` … `--radius-xl` (10–24px)
   - `--space-1` … `--space-6` (4–24px)
   - типографика: `--font-family`, `--font-size-*`, `--font-weight-*`
2. Создать `frontend/src/styles/base.css`:
   - reset / `box-sizing`, `body`, ссылки, `:focus-visible`
   - utilities: `.text-muted`, `.sr-only`
3. Подключить Manrope в `index.html` (как в шаблонах) или `@import` в base.css
4. В `main.jsx` или `App.jsx` импортировать `tokens.css` → `base.css` → `App.css`
5. В `:root` `App.css` заменить хардкод на `var(--…)` **только для глобальных правил** (остальное — в шаге 5)

**Критерий:** страницы открываются, шрифт Manrope виден, цвета не сломаны критично.

### Шаг 2 — UI-компоненты (~4–5 ч)

Создать `frontend/src/components/ui/` + `index.js` (barrel export):

| Компонент | Props / variants | CSS |
|-----------|------------------|-----|
| `Button` | `variant`: primary, primaryDark, outline, ghost; `loading`, `disabled` | modules или BEM + tokens |
| `Input` | `label`, `error`, стандартные input attrs | |
| `Textarea` | аналогично Input | |
| `Label` | uppercase muted (как в шаблоне) | |
| `Card` | `padding`, optional `title` | border `#e7ece5`, radius 16px |
| `Badge` / `StatusChip` | `variant`: done, today, soon, missed, pending | из Athlete/Trainer template |
| `SegmentedControl` | `options`, `value`, `onChange` | фон `#f0f2ee` |
| `Avatar` | `initials`, `size`: sm/md/lg | |
| `Modal` | `open`, `onClose`, `title`, `children` | overlay `rgba(15,20,18,0.45)` |
| `LoadingDots` | — | animation `tp-dot` из шаблона |

Каждый компонент — отдельный файл + co-located `.css` или один `ui.css` с BEM-префиксом `ui-`.

**Критерий:** Storybook не обязателен; достаточно временной dev-страницы или unit smoke в одном файле `ui/__demo__.jsx` (удалить перед merge MVP4-008).

### Шаг 3 — Layout shells (~2–3 ч)

`frontend/src/components/layout/`:

1. **`AuthLayout`**
   - тёмный фон `#12181a`, центрированная белая карточка max-width ~400px
   - слот: `children` (форма), опционально `logo`
   - **не** подключать к Login/Register в этом шаге (это MVP4-002)

2. **`AthleteShell`**
   - desktop: phone frame 393px на фоне `#e4e8e1`
   - header slot + `children` + placeholder bottom tab bar (4 вкладки без роутинга)
   - props: `activeTab`, `onTabChange` (заглушки)

3. **`CoachShell`**
   - sidebar 232px `#12181a`, main `#f3f5f1`
   - nav items: Спортсмены, Чат (без роутинга)
   - props: `activeNav`, `children`

**Критерий:** три layout рендерятся с mock-контентом без ошибок в консоли.

### Шаг 4 — Рефакторинг App.css (~1–2 ч)

- Оставить в `App.css` только:
  - page-specific стили (dashboard sections, garmin, agent-chat, training) **пока на старых классах**
  - постепенная замена цветов на `var(--color-*)` где безопасно
- **Не** мигрировать все страницы на ui-компоненты — это MVP4-002…008
- Удалить дубли с `base.css` (`box-sizing`, body margin)

### Шаг 5 — Проверка

```bash
npm run lint
npm run format:check
npm run build:web
```

Ручной smoke: `/login`, `/coach`, `/athlete` — без визуального регресса функциональности.

---

## Acceptance Criteria

- [x] `tokens.css` и `base.css` подключены в entry point
- [x] Manrope применяется глобально
- [x] Все базовые UI-компоненты экспортированы и имеют prop variants
- [x] `AuthLayout`, `AthleteShell`, `CoachShell` рендерятся без ошибок
- [x] Существующие страницы не ломаются (временная совместимость со старыми классами допустима)
- [x] `npm run lint`, `npm run build:web` проходят

## Dependencies

- [mvp-3.md](mvp-3.md) полностью закрыт
- [MVP4-000-conversations-backend.md](MVP4-000-conversations-backend.md) закрыт
- Шаблоны в `frontend/template/` доступны как reference

## Что НЕ входит в MVP4-001

| Задача | Где |
|--------|-----|
| Login/Register по шаблону | MVP4-002 |
| Подключение shells к роутеру | MVP4-003, MVP4-005 |
| Миграция страниц на новые компоненты | MVP4-002…008 |
| Chat UI + API | MVP4-007 |

## Декомпозиция

```
MVP4-001 — Design System
 ├── 1. tokens.css + base.css + Manrope
 ├── 2. ui/ (Button, Input, Card, Badge, Modal…)
 ├── 3. layout/ (AuthLayout, AthleteShell, CoachShell)
 ├── 4. рефакторинг App.css (импорты, var(), без миграции страниц)
 └── 5. lint + build + smoke
```

## Оценка

**~1–1.5 рабочих дня** при последовательной реализации без миграции контента страниц.

## Следующая задача после закрытия

[MVP4-002-auth-ui.md](MVP4-002-auth-ui.md) — первый потребитель `AuthLayout` + ui-компонентов.
