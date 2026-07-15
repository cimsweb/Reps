import { useEffect, useState } from "react";

import { TrainingPlanPreview } from "../training/TrainingPlanPreview.jsx";

const EMPTY_REPORT_FORM = {
  difficulty_rating: 5,
  mood_rating: 5,
  comment: "",
  garmin_url: "",
  raw_report_text: "",
};

function buildReportFormFromDraft(draft) {
  return {
    difficulty_rating: draft.suggested_difficulty_rating ?? 5,
    mood_rating: draft.suggested_mood_rating ?? 5,
    comment: draft.comment_body || "",
    garmin_url: draft.garmin_url || "",
    raw_report_text: "",
  };
}

export function PlanDraftPreview({ draft, onConfirm, onContinueEditing, onCancel, confirming }) {
  const [tab, setTab] = useState("structure");

  if (!draft) {
    return null;
  }

  const preview = {
    warnings: draft.warnings || [],
    workouts: draft.workouts || [],
  };

  return (
    <div className="agent-draft-preview agent-draft-sheet">
      <h3>Черновик плана</h3>
      <div className="segmented small">
        <button
          type="button"
          className={tab === "text" ? "active" : ""}
          onClick={() => setTab("text")}
        >
          Текст
        </button>
        <button
          type="button"
          className={tab === "structure" ? "active" : ""}
          onClick={() => setTab("structure")}
        >
          Структура
        </button>
      </div>
      {tab === "text" ? (
        <pre className="plan-text">{draft.raw_text || "Текст черновика пуст."}</pre>
      ) : (
        <TrainingPlanPreview preview={preview} />
      )}
      <div className="button-row agent-draft-actions">
        <button type="button" onClick={onConfirm} disabled={confirming}>
          {confirming ? "Сохраняем…" : "Сохранить план"}
        </button>
        <button type="button" className="button-secondary" onClick={onContinueEditing}>
          Продолжить правку
        </button>
        <button type="button" className="button-secondary" onClick={onCancel}>
          Отмена
        </button>
      </div>
    </div>
  );
}

export function ReportDraftPreview({ draft, onConfirm, onManualFallback, confirming }) {
  const [form, setForm] = useState(() =>
    draft ? buildReportFormFromDraft(draft) : EMPTY_REPORT_FORM,
  );

  useEffect(() => {
    if (draft) {
      setForm(buildReportFormFromDraft(draft));
    }
  }, [draft]);

  if (!draft) {
    return null;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    await onConfirm({
      difficulty_rating: Number(form.difficulty_rating),
      mood_rating: Number(form.mood_rating),
      comment: form.comment.trim() || null,
      garmin_url: form.garmin_url.trim() || null,
      raw_report_text: form.raw_report_text.trim() || null,
    });
  }

  return (
    <div className="agent-draft-preview agent-draft-sheet">
      <h3>Черновик отчёта</h3>
      {draft.warnings?.length > 0 ? (
        <div className="warnings">
          <p className="meta">Предупреждения:</p>
          <ul>
            {draft.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
      <form className="form workout-report-form" onSubmit={handleSubmit}>
        <label>
          Garmin URL (необязательно)
          <input
            value={form.garmin_url}
            placeholder="https://connect.garmin.com/..."
            onChange={(event) =>
              setForm((current) => ({ ...current, garmin_url: event.target.value }))
            }
          />
        </label>
        <label className="rating-input">
          Трудность (0–10)
          <input
            type="range"
            min="0"
            max="10"
            value={form.difficulty_rating}
            onChange={(event) =>
              setForm((current) => ({ ...current, difficulty_rating: event.target.value }))
            }
          />
          <span>{form.difficulty_rating}</span>
        </label>
        <label className="rating-input">
          Эмоции (0–10)
          <input
            type="range"
            min="0"
            max="10"
            value={form.mood_rating}
            onChange={(event) =>
              setForm((current) => ({ ...current, mood_rating: event.target.value }))
            }
          />
          <span>{form.mood_rating}</span>
        </label>
        <label>
          Комментарий
          <textarea
            rows={3}
            value={form.comment}
            onChange={(event) =>
              setForm((current) => ({ ...current, comment: event.target.value }))
            }
          />
        </label>
        <div className="button-row agent-draft-actions">
          <button type="submit" disabled={confirming}>
            {confirming ? "Отправляем…" : "Отправить отчёт"}
          </button>
          <button type="button" className="button-secondary" onClick={onManualFallback}>
            Заполнить вручную
          </button>
        </div>
      </form>
    </div>
  );
}
