# MVP2.2-005 — UI

## Goal

Чат-интерфейсы для тренера и спортсмена: ИИ как агент с вопросами, превью результата, подтверждение перед сохранением. Mobile-first.

## Requirements

### Тренер — «Создать с ИИ»

**Точка входа:** кнопка на `/coach/athletes/:id/training/create` рядом с режимами MVP 2.1

**Экран чата (`CoachPlanAgentChat`):**

- Лента сообщений (user справа, assistant слева)
- Поле ввода + send (Enter на desktop)
- При `type: question` — только текст, ждём ответ
- При `type: draft` — блок превью недели:
    - вкладки «Текст» / «Структура» (reuse MVP 2.1 preview)
    - warnings парсера
- Кнопки: **«Сохранить план»** (confirm), **«Продолжить правку»**, **«Отмена»**
- После confirm — redirect на карточку спортсмена с выбранной неделей

**Стартовый экран (опционально):**

- Быстрые шаблоны: «Беговая неделя», «Смешанная», «Силовая»
- Поле брифа: список типов через запятую + дата начала

### Спортсмен — «Помощник отчёта»

**Точка входа:** на карточке тренировки без отчёта — «Рассказать с помощью ИИ» рядом с формой MVP 2.1

**Экран (`AthleteReportAgentChat`):**

- Контекст сверху: дата, тип, краткий план (readonly)
- Чат: спортсмен пишет свободно («нагрузка 5», вставка Garmin)
- Агент задаёт вопросы по одному (не стена текста)
- Финальный блок: предзаполненная форма отчёта (слайдеры + comment + garmin link)
- **«Отправить отчёт»** — confirm; **«Заполнить вручную»** — fallback на WorkoutReportForm

### Общие компоненты

- `AgentChatLayout` — message list, input, typing indicator
- `AgentDraftPreview` — plan week / report form
- Обработка 503: toast «ИИ недоступен» + кнопка ручного ввода
- Resume: при открытии страницы — `GET .../sessions/active`

### Mobile

- Чат на весь экран, input fixed bottom (safe-area)
- Превью draft — bottom sheet на mobile

### Не входит

- Streaming токенов (можно добавить позже)
- Голосовой ввод

## Acceptance Criteria

- [x] Тренер проходит сценарий: бриф → вопрос → draft → confirm
- [x] Спортсмен: «нагрузка 5» → вопросы → форма → submit
- [x] Fallback на MVP 2.1 при ошибке ИИ
- [x] Возобновление активной сессии после перезагрузки страницы
- [x] UI на 375px без горизонтального скролла в чате
- [x] `npm run lint` и `npm run format:check` проходят

## Dependencies

- [MVP2.2-004-search.md](MVP2.2-004-search.md) закрыт
- MVP 2.1 UI (режимы ввода, preview components)

## Декомпозиция

```
MVP2.2-005 — UI
 ├── CoachPlanAgentChat + entry from create page
 ├── AthleteReportAgentChat + fallback
 ├── shared AgentChatLayout, AgentDraftPreview
 └── active session resume + 503 fallback
```
