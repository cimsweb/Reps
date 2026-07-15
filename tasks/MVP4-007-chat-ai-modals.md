# MVP4-007 — Chat, AI Flows & Modals

## Goal

Унифицировать формы обратной связи, AI-чаты и модальные окна по шаблонам `FeedbackForm.dc.html` и `Trainer Cabinet.dc.html` (add workout modal, chat).

## Requirements

### FeedbackForm (`FeedbackForm.dc.html`)
- Рестайл `WorkoutReportForm`:
  - заголовок «Как прошла тренировка?»
  - RPE 1–10 selector (кнопки-pills)
  - textarea отчёта + кнопка «✨ Улучшить с ИИ»
  - поле ссылки на активность (Garmin)
  - collapsible «Вопрос тренеру» (оранжевый акцент)
  - submit «Отправить отчёт»
- Состояния: default, AI generating, submitted (green success card)
- Интеграция в Today screen (MVP4-004)

### AthleteReportAgentChatPage
- Chat bubbles в стиле athlete/coach template
- Input + send внизу
- Сохранить streaming / polling логику AI

### CoachPlanAgentChatPage + Add Workout Modal
- Modal по шаблону: title, mode toggle (один день / целая неделя)
- Week day picker pills
- AI textarea + «Сгенерировать план» button with loading dots
- Preview сгенерированного плана в modal
- `CoachCreateTrainingPlanPage` — визуально в том же языке (form fields, buttons)

### Coach Chat View
- Split layout: chat list 280px + conversation
- Message bubbles, question label оранжевый
- Input + «Отправить»
- Подключить API: `fetchCoachConversations`, `fetchConversationMessages`, `sendCoachMessage`, `markConversationRead`

### Athlete Chat tab
- Подключить API: `fetchAthleteConversations`, `sendAthleteMessage`, и т.д.

## Acceptance Criteria

- [x] `WorkoutReportForm` соответствует `FeedbackForm.dc.html`
- [x] RPE, AI polish, activity link, coach question работают
- [x] AI agent pages используют единые chat bubbles
- [x] Add workout modal (или эквивалент) соответствует шаблону trainer
- [x] Coach chat view рендерится в shell и работает с API
- [x] `npm run lint`, `npm run build:web` проходят

## Status

**Done** — `WorkoutReportForm` redesign, `CoachChatScreen` split layout + API, `CoachAddWorkoutModal`, shared `chat/*` components, `AgentChatLayout` bubbles.

## Dependencies

- [MVP4-000-conversations-backend.md](MVP4-000-conversations-backend.md)

## Декомпозиция

```
MVP4-007 — Chat & AI
 ├── FeedbackForm redesign
 ├── AthleteReportAgentChatPage styling
 ├── CoachPlanAgentChatPage + create plan modal
 └── CoachChatView + AthleteChatScreen (API)
```
