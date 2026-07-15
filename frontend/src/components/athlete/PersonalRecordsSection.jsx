import { useCallback, useEffect, useState } from "react";

import {
  createPersonalRecord,
  deletePersonalRecord,
  fetchAthleteRecords,
  updatePersonalRecord,
} from "../../api/client.js";
import { getToken } from "../../auth/tokenStorage.js";
import { FieldError } from "../FieldError.jsx";
import { EmptyState } from "../EmptyState.jsx";
import { LoadingMessage } from "../LoadingMessage.jsx";
import { getErrorMessage } from "../../utils/apiErrors.js";
import {
  fromDateTimeLocalValue,
  toDateTimeLocalValue,
} from "../../utils/formatters.js";

const PAGE_SIZE = 20;

const EMPTY_RECORD = {
  record_type: "distance",
  name: "",
  value: "",
  unit: "time",
  achieved_at: toDateTimeLocalValue(new Date().toISOString()),
};

const RECORD_ICONS = {
  distance: "🏅",
  exercise: "💪",
};

function formatRecordDate(value) {
  if (!value) {
    return "—";
  }
  return new Date(value).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export function PersonalRecordsSection() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState(EMPTY_RECORD);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState("");
  const [formOpen, setFormOpen] = useState(false);

  const loadRecords = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const token = getToken();
      const result = await fetchAthleteRecords(token, { offset: 0, limit: PAGE_SIZE });
      setRecords(result.items);
    } catch (loadError) {
      setError(getErrorMessage(loadError, "Не удалось загрузить рекорды"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRecords();
  }, [loadRecords]);

  function resetForm() {
    setForm(EMPTY_RECORD);
    setEditingId("");
    setFormError("");
    setFormOpen(false);
  }

  function startEdit(record) {
    setFormOpen(true);
    setEditingId(record.id);
    setForm({
      record_type: record.record_type,
      name: record.name,
      value: record.value,
      unit: record.unit,
      achieved_at: toDateTimeLocalValue(record.achieved_at),
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      const token = getToken();
      const payload = {
        record_type: form.record_type,
        name: form.name.trim(),
        value: form.value.trim(),
        unit: form.unit.trim(),
        achieved_at: fromDateTimeLocalValue(form.achieved_at),
      };
      if (editingId) {
        await updatePersonalRecord(token, editingId, payload);
      } else {
        await createPersonalRecord(token, payload);
      }
      resetForm();
      await loadRecords();
    } catch (submitError) {
      setFormError(getErrorMessage(submitError, "Не удалось сохранить рекорд"));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(recordId) {
    try {
      const token = getToken();
      await deletePersonalRecord(token, recordId);
      if (editingId === recordId) {
        resetForm();
      }
      await loadRecords();
    } catch (deleteError) {
      setError(getErrorMessage(deleteError, "Не удалось удалить рекорд"));
    }
  }

  return (
    <section className="athlete-records-section">
      <div className="athlete-records-section__header">
        <h3 className="athlete-section-label">Личные рекорды</h3>
        <button
          type="button"
          className="athlete-records-section__add-btn"
          onClick={() => {
            resetForm();
            setFormOpen(true);
          }}
        >
          + Добавить
        </button>
      </div>

      {formOpen ? (
        <form className="athlete-records-form" onSubmit={handleSubmit}>
        <label>
          Тип
          <select
            value={form.record_type}
            onChange={(event) => setForm((current) => ({ ...current, record_type: event.target.value }))}
          >
            <option value="distance">Дистанция</option>
            <option value="exercise">Упражнение</option>
          </select>
        </label>
        <label>
          Название
          <input
            type="text"
            value={form.name}
            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
            required
          />
        </label>
        <label>
          Результат
          <input
            type="text"
            value={form.value}
            onChange={(event) => setForm((current) => ({ ...current, value: event.target.value }))}
            required
          />
        </label>
        <label>
          Единица
          <input
            type="text"
            value={form.unit}
            onChange={(event) => setForm((current) => ({ ...current, unit: event.target.value }))}
            required
          />
        </label>
        <label>
          Дата достижения
          <input
            type="datetime-local"
            value={form.achieved_at}
            onChange={(event) =>
              setForm((current) => ({ ...current, achieved_at: event.target.value }))
            }
            required
          />
        </label>
        <FieldError message={formError} />
        <div className="stack-actions">
          <button type="submit" disabled={saving}>
            {saving ? "Сохраняем..." : editingId ? "Обновить рекорд" : "Добавить рекорд"}
          </button>
          {editingId ? (
            <button type="button" className="button-secondary" onClick={resetForm}>
              Отмена
            </button>
          ) : null}
        </div>
      </form>
      ) : null}

      {loading ? <LoadingMessage /> : null}
      {error ? <p className="form-error">{error}</p> : null}

      {!loading && records.length === 0 ? <EmptyState message="Рекордов пока нет." /> : null}

      {!loading && records.length > 0 ? (
        <div className="athlete-records-grid">
          {records.map((record) => (
            <article key={record.id} className="athlete-record-card">
              <span className="athlete-record-card__icon" aria-hidden="true">
                {RECORD_ICONS[record.record_type] ?? "🏅"}
              </span>
              <p className="athlete-record-card__value">
                {record.value}
                {record.unit && record.unit !== "time" ? ` ${record.unit}` : ""}
              </p>
              <p className="athlete-record-card__name">{record.name}</p>
              <p className="athlete-record-card__date">{formatRecordDate(record.achieved_at)}</p>
              <div className="athlete-record-card__actions">
                <button type="button" className="button-link" onClick={() => startEdit(record)}>
                  Изменить
                </button>
                <button
                  type="button"
                  className="button-link danger"
                  onClick={() => handleDelete(record.id)}
                >
                  Удалить
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
