import { useState } from "react";

import { useReportAgentSession } from "../../hooks/useReportAgentSession.js";
import { Button } from "../ui/Button.jsx";
import { FieldError } from "../FieldError.jsx";
import { formatDate, formatWorkoutType } from "../../utils/formatters.js";

const RPE_VALUES = Array.from({ length: 10 }, (_, index) => index + 1);

const EMPTY_FORM = {
  difficulty_rating: 6,
  comment: "",
  raw_report_text: "",
  garmin_url: "",
  coach_question: "",
};

export function WorkoutReportForm({
  workout,
  onSubmit,
  submitting,
  error,
  showCoachQuestion = true,
}) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [questionExpanded, setQuestionExpanded] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [aiResultVisible, setAiResultVisible] = useState(false);
  const { generatePolishedReport, generating, error: aiError } = useReportAgentSession(workout?.id);

  const dayLabel = formatDate(workout.planned_date);
  const workoutType = workout.title || formatWorkoutType(workout.workout_type);

  async function handleSubmit(event) {
    event.preventDefault();
    const rpe = Number(form.difficulty_rating);
    await onSubmit({
      difficulty_rating: rpe,
      mood_rating: rpe,
      comment: form.comment.trim() || form.raw_report_text.trim() || null,
      garmin_url: form.garmin_url.trim() || null,
      raw_report_text: form.raw_report_text.trim() || null,
      coach_question: form.coach_question.trim() || null,
    });
    setSubmitted(true);
    setForm(EMPTY_FORM);
    setQuestionExpanded(false);
    setAiResultVisible(false);
  }

  async function handleRunAi() {
    const polished = await generatePolishedReport(form.raw_report_text);
    if (!polished) {
      return;
    }
    setForm((current) => ({ ...current, comment: polished }));
    setAiResultVisible(true);
  }

  if (submitted) {
    return (
      <div className="feedback-form feedback-form--submitted">
        <p className="feedback-form__success-label">Отчёт отправлен</p>
        <p className="feedback-form__success-text">
          Тренер увидит ваш отчёт на вкладке «Сегодня» и в карточке спортсмена.
        </p>
        <Button type="button" variant="outline" onClick={() => setSubmitted(false)}>
          Отправить ещё один
        </Button>
      </div>
    );
  }

  return (
    <form className="feedback-form" onSubmit={handleSubmit}>
      <h3 className="feedback-form__title">Отчёт о тренировке</h3>
      <p className="feedback-form__subtitle">
        {dayLabel} · {workoutType}
      </p>

      <label className="feedback-form__label" htmlFor="report-raw-comment">
        Короткий комментарий
      </label>
      <textarea
        id="report-raw-comment"
        className="feedback-form__textarea"
        rows={3}
        value={form.raw_report_text}
        placeholder="Например: пробежала, было тяжело на 5-6 повторе, но темп держала"
        onChange={(event) =>
          setForm((current) => ({ ...current, raw_report_text: event.target.value }))
        }
      />

      <button
        type="button"
        className="feedback-form__ai-button"
        disabled={generating}
        onClick={handleRunAi}
      >
        {generating ? "ИИ пишет отчёт…" : "✨ Составить отчёт с ИИ"}
      </button>

      {aiResultVisible || form.comment ? (
        <div className="feedback-form__polished">
          <label className="feedback-form__label" htmlFor="report-polished">
            Развёрнутое описание для тренера
          </label>
          <textarea
            id="report-polished"
            className="feedback-form__textarea feedback-form__textarea--polished"
            rows={4}
            value={form.comment}
            onChange={(event) =>
              setForm((current) => ({ ...current, comment: event.target.value }))
            }
          />
        </div>
      ) : null}

      <hr className="feedback-form__divider" />

      <div className="feedback-form__rpe-header">
        <span className="feedback-form__label">Оценка нагрузки (RPE)</span>
        <span className="feedback-form__rpe-value">{form.difficulty_rating}/10</span>
      </div>
      <div className="feedback-form__rpe-row" role="group" aria-label="RPE 1-10">
        {RPE_VALUES.map((value) => (
          <button
            key={value}
            type="button"
            className={[
              "feedback-form__rpe-pill",
              Number(form.difficulty_rating) === value ? "feedback-form__rpe-pill--active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => setForm((current) => ({ ...current, difficulty_rating: value }))}
          >
            {value}
          </button>
        ))}
      </div>

      <label className="feedback-form__label" htmlFor="report-activity-link">
        Ссылка на тренировку с часов
      </label>
      <input
        id="report-activity-link"
        className="feedback-form__input"
        value={form.garmin_url}
        placeholder="strava.com/activities/…"
        onChange={(event) =>
          setForm((current) => ({ ...current, garmin_url: event.target.value }))
        }
      />

      {showCoachQuestion && !questionExpanded ? (
        <button
          type="button"
          className="feedback-form__question-toggle"
          onClick={() => setQuestionExpanded(true)}
        >
          <span aria-hidden="true">＋</span> Вопрос тренеру
        </button>
      ) : null}

      {showCoachQuestion && questionExpanded ? (
        <div className="feedback-form__question">
          <label className="feedback-form__label feedback-form__label--question" htmlFor="coach-question">
            Вопрос тренеру
          </label>
          <textarea
            id="coach-question"
            className="feedback-form__textarea feedback-form__textarea--question"
            rows={2}
            value={form.coach_question}
            placeholder="Например: болит колено после интервалов, стоит ли снизить объём завтра?"
            onChange={(event) =>
              setForm((current) => ({ ...current, coach_question: event.target.value }))
            }
          />
        </div>
      ) : null}

      <FieldError message={error || aiError} />

      <Button type="submit" block loading={submitting}>
        Отправить отчёт
      </Button>
    </form>
  );
}
