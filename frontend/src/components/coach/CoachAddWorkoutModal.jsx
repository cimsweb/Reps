import { useCallback, useEffect, useState } from "react";

import {
  createTrainingPlanFromText,
  fetchCoachAthleteTrainingPlan,
  fetchCoachAthleteTrainingPlanText,
  sendPlanAgentMessage,
  startPlanAgentSession,
  updateTrainingPlanRawText,
} from "../../api/client.js";
import { getToken } from "../../auth/tokenStorage.js";
import {
  buildWeekRawText,
  computeTextDiff,
  countWeekDayHeaders,
  extractDayBodyFromBlock,
  mapWeekBlocksToFields,
  mergeDayIntoWeekRawText,
  splitWeekRawText,
} from "../../utils/workoutText.js";
import { getErrorMessage, isAiUnavailableError } from "../../utils/apiErrors.js";
import { addDaysToDateString, toDateInputValue } from "../../utils/formatters.js";
import { startOfWeek } from "../../utils/weekStrip.js";
import { Button } from "../ui/Button.jsx";
import { FieldError } from "../FieldError.jsx";
import { Modal } from "../ui/Modal.jsx";
import { SegmentedControl } from "../ui/SegmentedControl.jsx";

const MODE_OPTIONS = [
  { value: "day", label: "Один день" },
  { value: "week", label: "Целая неделя" },
];

const WEEKDAY_LABELS = [
  "Понедельник",
  "Вторник",
  "Среда",
  "Четверг",
  "Пятница",
  "Суббота",
  "Воскресенье",
];

function buildEmptyWeekFields() {
  return Array.from({ length: 7 }, () => ({ title: "", text: "" }));
}

function resolveWeekMonday(dateInput) {
  return toDateInputValue(startOfWeek(new Date(`${dateInput}T00:00:00`)));
}

export function CoachAddWorkoutModal({
  open,
  onClose,
  athleteId,
  anchorDate = toDateInputValue(),
  initialDate = anchorDate,
  initialMode = "day",
  onSaved,
}) {
  const [mode, setMode] = useState(initialMode);
  const [formDate, setFormDate] = useState(initialDate);
  const [formTitle, setFormTitle] = useState("");
  const [formText, setFormText] = useState("");
  const [weekStartDate, setWeekStartDate] = useState(() => resolveWeekMonday(anchorDate));
  const [loadedWeekStartDate, setLoadedWeekStartDate] = useState("");
  const [weekFields, setWeekFields] = useState(buildEmptyWeekFields);
  const [planId, setPlanId] = useState("");
  const [planScope, setPlanScope] = useState("");
  const [weekRawText, setWeekRawText] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [error, setError] = useState("");
  const [rewriteDiff, setRewriteDiff] = useState(null);
  const [createDraft, setCreateDraft] = useState("");

  const modalTitle = mode === "week" ? "Новая неделя тренировок" : "Новая тренировка";

  const loadPlanContext = useCallback(async () => {
    if (!athleteId) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const token = getToken();
      const weekMonday = resolveWeekMonday(anchorDate);
      const [planResult, textResult] = await Promise.all([
        fetchCoachAthleteTrainingPlan(token, athleteId, { period: "week", anchorDate: weekMonday }),
        fetchCoachAthleteTrainingPlanText(token, athleteId, { period: "week", anchorDate: weekMonday }),
      ]);

      const planWorkouts = planResult.workouts;
      const uniquePlanIds = [...new Set(planWorkouts.map((workout) => workout.plan_id))];
      const sharedPlanId = uniquePlanIds.length === 1 ? uniquePlanIds[0] : "";
      setPlanId(sharedPlanId);
      setPlanScope(
        planWorkouts.length > 1 || countWeekDayHeaders(textResult.text) >= 2 ? "week" : "",
      );
      setWeekRawText(textResult.text ?? "");
      setWeekStartDate(weekMonday);
      setLoadedWeekStartDate(weekMonday);

      const blocks = splitWeekRawText(textResult.text ?? "");
      setWeekFields(mapWeekBlocksToFields(blocks, weekMonday, planWorkouts));
    } catch (loadError) {
      setPlanId("");
      setPlanScope("");
      setWeekRawText("");
      setLoadedWeekStartDate("");
      setWeekFields(buildEmptyWeekFields());
      setError(getErrorMessage(loadError, "Не удалось загрузить текущий план"));
    } finally {
      setLoading(false);
    }
  }, [anchorDate, athleteId]);

  useEffect(() => {
    if (!open) {
      return;
    }
    setMode(initialMode);
    setFormDate(initialDate);
    setFormTitle("");
    setFormText("");
    setWeekStartDate(resolveWeekMonday(anchorDate));
    setRewriteDiff(null);
    setCreateDraft("");
    loadPlanContext();
  }, [anchorDate, initialDate, initialMode, loadPlanContext, open]);

  function buildWeekTitlesPayload(fields, startDate) {
    const titles = {};
    fields.forEach((field, index) => {
      if (!field.title.trim()) {
        return;
      }
      const date = addDaysToDateString(startDate, index);
      titles[date] = field.title.trim();
    });
    return Object.keys(titles).length > 0 ? titles : null;
  }

  async function handleSave() {
    setSaving(true);
    setError("");
    try {
      const token = getToken();
      if (mode === "day") {
        const titles = formTitle.trim() ? { [formDate]: formTitle.trim() } : null;
        const mergedWeekText = mergeDayIntoWeekRawText(weekRawText, formDate, formText);
        const isMultiDayWeek = countWeekDayHeaders(mergedWeekText) >= 2;
        if (planId && loadedWeekStartDate === resolveWeekMonday(formDate)) {
          await updateTrainingPlanRawText(token, planId, {
            raw_text: mergedWeekText,
            titles,
            scope: isMultiDayWeek ? "week" : "day",
            start_date: isMultiDayWeek ? resolveWeekMonday(formDate) : formDate,
          });
        } else {
          await createTrainingPlanFromText(token, athleteId, {
            scope: "day",
            start_date: formDate,
            text: formText,
            title: formTitle.trim() || null,
          });
        }
      } else {
        const rawText = buildWeekRawText(weekStartDate, weekFields.map((field) => field.text));
        const filledDays = weekFields.filter((field) => field.text.trim()).length;
        if (filledDays === 0) {
          setError("Заполните хотя бы один день недели.");
          return;
        }
        const titles = buildWeekTitlesPayload(weekFields, weekStartDate);
        const shouldUpdateExistingPlan =
          Boolean(planId) && planScope === "week" && weekStartDate === loadedWeekStartDate;
        if (shouldUpdateExistingPlan) {
          await updateTrainingPlanRawText(token, planId, {
            raw_text: rawText,
            titles,
            scope: "week",
            start_date: weekStartDate,
          });
        } else {
          await createTrainingPlanFromText(token, athleteId, {
            scope: "week",
            start_date: weekStartDate,
            text: rawText,
            titles,
          });
        }
      }
      onSaved?.();
      onClose();
    } catch (saveError) {
      setError(getErrorMessage(saveError, "Не удалось сохранить тренировку"));
    } finally {
      setSaving(false);
    }
  }

  async function requestPlanDraft(prompt) {
    setAiLoading(true);
    setError("");
    try {
      const token = getToken();
      const startDate = mode === "week" ? weekStartDate : formDate;
      let session = await startPlanAgentSession(token, athleteId, {
        start_date: startDate,
        initial_brief: prompt,
      });
      if (!session.can_confirm || session.latest_reply?.type !== "plan_draft") {
        session = await sendPlanAgentMessage(token, session.session_id, { content: prompt });
      }
      const draftText = session.latest_reply?.draft?.raw_text;
      return draftText?.trim() || null;
    } catch (aiError) {
      if (isAiUnavailableError(aiError)) {
        setError("ИИ недоступен. Заполните текст вручную.");
      } else {
        setError(getErrorMessage(aiError, "Не удалось получить ответ ИИ"));
      }
      return null;
    } finally {
      setAiLoading(false);
    }
  }

  async function handleRewriteWithAi() {
    if (!formText.trim()) {
      return;
    }
    const rewritten = await requestPlanDraft(`Перепиши и улучши тренировку, сохрани структуру:\n${formText}`);
    if (!rewritten) {
      return;
    }
    setRewriteDiff({ original: formText, result: rewritten });
  }

  async function handleCreateWithAi() {
    const seed = formText.trim() || "Сгенерируй тренировку на один день";
    const generated = await requestPlanDraft(seed);
    if (!generated) {
      return;
    }
    setCreateDraft(generated);
  }

  async function handleWeekAi() {
    const seed =
      weekFields.map((field) => field.text).some((text) => text.trim()) ?
        `Улучши неделю тренировок:\n${buildWeekRawText(weekStartDate, weekFields.map((f) => f.text))}`
      : "Сгенерируй тренировочную неделю для подготовленного спортсмена";
    const generated = await requestPlanDraft(seed);
    if (!generated) {
      return;
    }
    const blocks = splitWeekRawText(generated);
    const mapped = mapWeekBlocksToFields(blocks, weekStartDate);
    setWeekFields(
      mapped.map((field, index) => ({
        title: weekFields[index]?.title ?? "",
        text: field.text,
      })),
    );
  }

  return (
    <Modal open={open} onClose={onClose} title={modalTitle} wide>
      <div className="coach-add-workout-modal">
        <SegmentedControl options={MODE_OPTIONS} value={mode} onChange={setMode} />

        {loading ? <p className="coach-add-workout-modal__meta">Загружаем план…</p> : null}

        {mode === "day" ? (
          <>
            <div className="coach-add-workout-modal__row">
              <label className="coach-add-workout-modal__field">
                <span className="coach-add-workout-modal__label">Дата</span>
                <input
                  type="date"
                  className="coach-add-workout-modal__input"
                  value={formDate}
                  onChange={(event) => setFormDate(event.target.value)}
                />
              </label>
              <label className="coach-add-workout-modal__field">
                <span className="coach-add-workout-modal__label">Название (необязательно)</span>
                <input
                  className="coach-add-workout-modal__input"
                  value={formTitle}
                  placeholder="Например: Зал"
                  onChange={(event) => setFormTitle(event.target.value)}
                />
              </label>
            </div>

            <label className="coach-add-workout-modal__field">
              <span className="coach-add-workout-modal__label">Содержание тренировки</span>
              <textarea
                className="coach-add-workout-modal__textarea"
                rows={10}
                value={formText}
                placeholder="Впишите или вставьте текст тренировки — разминку, раунды, упражнения, заминку…"
                onChange={(event) => setFormText(event.target.value)}
              />
            </label>

            <div className="coach-add-workout-modal__actions">
              <Button type="button" onClick={handleSave} loading={saving}>
                Сохранить
              </Button>
              <Button type="button" variant="outline" loading={aiLoading} onClick={handleRewriteWithAi}>
                ✎ Переписать с ИИ
              </Button>
              <Button type="button" variant="primaryDark" loading={aiLoading} onClick={handleCreateWithAi}>
                ✨ Создать с ИИ
              </Button>
            </div>

            {rewriteDiff ? (
              <div className="coach-add-workout-modal__preview">
                <p className="coach-add-workout-modal__preview-label">ИИ предлагает изменения</p>
                <div className="coach-add-workout-modal__diff">
                  {computeTextDiff(rewriteDiff.original, rewriteDiff.result).map((line, index) => (
                    <div
                      key={`${line.type}-${index}`}
                      className={`coach-add-workout-modal__diff-line coach-add-workout-modal__diff-line--${line.type}`}
                    >
                      {(line.type === "removed" ? "− " : line.type === "added" ? "+ " : "  ") + line.text}
                    </div>
                  ))}
                </div>
                <div className="coach-add-workout-modal__actions">
                  <Button
                    type="button"
                    onClick={() => {
                      setFormText(rewriteDiff.result);
                      setRewriteDiff(null);
                    }}
                  >
                    Принять изменения
                  </Button>
                  <Button type="button" variant="outline" onClick={() => setRewriteDiff(null)}>
                    Отклонить
                  </Button>
                </div>
              </div>
            ) : null}

            {createDraft ? (
              <div className="coach-add-workout-modal__preview">
                <p className="coach-add-workout-modal__preview-label">ИИ сгенерировал тренировку</p>
                <pre className="coach-add-workout-modal__draft">{createDraft}</pre>
                <div className="coach-add-workout-modal__actions">
                  <Button
                    type="button"
                    onClick={() => {
                      setFormText(createDraft);
                      setCreateDraft("");
                    }}
                  >
                    Подтвердить и вставить
                  </Button>
                  <Button type="button" variant="outline" onClick={() => setCreateDraft("")}>
                    Отклонить
                  </Button>
                </div>
              </div>
            ) : null}
          </>
        ) : (
          <>
            <div className="coach-add-workout-modal__week-header">
              <label className="coach-add-workout-modal__field">
                <span className="coach-add-workout-modal__label">Начало недели</span>
                <input
                  type="date"
                  className="coach-add-workout-modal__input"
                  value={weekStartDate}
                  onChange={(event) => setWeekStartDate(event.target.value)}
                />
              </label>
              <Button type="button" variant="primaryDark" loading={aiLoading} onClick={handleWeekAi}>
                ✨ Создать с ИИ
              </Button>
            </div>

            <div className="coach-add-workout-modal__week-fields">
              {weekFields.map((field, index) => (
                <div key={WEEKDAY_LABELS[index]} className="coach-add-workout-modal__week-day">
                  <span className="coach-add-workout-modal__label">{WEEKDAY_LABELS[index]}</span>
                  <input
                    className="coach-add-workout-modal__input"
                    value={field.title}
                    placeholder="Название (необязательно)"
                    onChange={(event) =>
                      setWeekFields((current) =>
                        current.map((item, itemIndex) =>
                          itemIndex === index ? { ...item, title: event.target.value } : item,
                        ),
                      )
                    }
                  />
                  <textarea
                    className="coach-add-workout-modal__textarea coach-add-workout-modal__textarea--compact"
                    rows={3}
                    value={field.text}
                    placeholder="Текст тренировки на этот день…"
                    onChange={(event) =>
                      setWeekFields((current) =>
                        current.map((item, itemIndex) =>
                          itemIndex === index ? { ...item, text: event.target.value } : item,
                        ),
                      )
                    }
                  />
                </div>
              ))}
            </div>

            <Button type="button" block onClick={handleSave} loading={saving}>
              Сохранить неделю
            </Button>
          </>
        )}

        <FieldError message={error} />
      </div>
    </Modal>
  );
}
