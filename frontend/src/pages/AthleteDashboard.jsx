import { useCallback, useEffect, useState } from "react";

import {
  acceptInvitation,
  ApiError,
  createPersonalRecord,
  declineInvitation,
  deletePersonalRecord,
  fetchAthleteCoaches,
  fetchAthleteFeedback,
  fetchAthleteInvitations,
  fetchAthleteProfile,
  fetchAthleteRecords,
  saveAthleteProfile,
  submitWorkoutFeedback,
  updatePersonalRecord,
} from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { getToken } from "../auth/tokenStorage.js";
import { DashboardLayout } from "../components/DashboardLayout.jsx";
import { EmptyState } from "../components/EmptyState.jsx";
import { FieldError } from "../components/FieldError.jsx";
import { LoadingMessage } from "../components/LoadingMessage.jsx";
import { getErrorMessage } from "../utils/apiErrors.js";
import {
  formatDateTime,
  formatRecordType,
  fromDateTimeLocalValue,
  toDateTimeLocalValue,
} from "../utils/formatters.js";

const PAGE_SIZE = 20;

const EMPTY_PROFILE = {
  height_cm: "",
  weight_kg: "",
  age: "",
  gender: "male",
};

const EMPTY_RECORD = {
  record_type: "distance",
  name: "",
  value: "",
  unit: "time",
  achieved_at: toDateTimeLocalValue(new Date().toISOString()),
};

const EMPTY_FEEDBACK = {
  text: "",
  garmin_url: "",
};

export function AthleteDashboard() {
  const { user, logout } = useAuth();

  const [invitations, setInvitations] = useState([]);
  const [coaches, setCoaches] = useState([]);
  const [invitationsLoading, setInvitationsLoading] = useState(true);
  const [invitationsError, setInvitationsError] = useState("");
  const [invitationActionId, setInvitationActionId] = useState("");

  const [profileForm, setProfileForm] = useState(EMPTY_PROFILE);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState("");
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState("");

  const [records, setRecords] = useState([]);
  const [recordsTotal, setRecordsTotal] = useState(0);
  const [recordsLoading, setRecordsLoading] = useState(true);
  const [recordsError, setRecordsError] = useState("");
  const [recordForm, setRecordForm] = useState(EMPTY_RECORD);
  const [recordFormError, setRecordFormError] = useState("");
  const [recordSaving, setRecordSaving] = useState(false);
  const [editingRecordId, setEditingRecordId] = useState("");

  const [feedbackItems, setFeedbackItems] = useState([]);
  const [feedbackTotal, setFeedbackTotal] = useState(0);
  const [feedbackLoading, setFeedbackLoading] = useState(true);
  const [feedbackError, setFeedbackError] = useState("");
  const [feedbackForm, setFeedbackForm] = useState(EMPTY_FEEDBACK);
  const [feedbackFormError, setFeedbackFormError] = useState("");
  const [feedbackSaving, setFeedbackSaving] = useState(false);

  const loadInvitations = useCallback(async () => {
    setInvitationsLoading(true);
    setInvitationsError("");
    try {
      const token = getToken();
      const [invitationResult, coachResult] = await Promise.all([
        fetchAthleteInvitations(token),
        fetchAthleteCoaches(token),
      ]);
      setInvitations(invitationResult.items);
      setCoaches(coachResult.items);
    } catch (loadError) {
      setInvitationsError(getErrorMessage(loadError, "Не удалось загрузить приглашения"));
    } finally {
      setInvitationsLoading(false);
    }
  }, []);

  const loadProfile = useCallback(async () => {
    setProfileLoading(true);
    setProfileError("");
    try {
      const token = getToken();
      const profile = await fetchAthleteProfile(token);
      setProfileForm({
        height_cm: String(profile.height_cm),
        weight_kg: String(profile.weight_kg),
        age: String(profile.age),
        gender: profile.gender,
      });
    } catch (loadError) {
      if (loadError instanceof ApiError && loadError.status === 404) {
        setProfileForm(EMPTY_PROFILE);
      } else {
        setProfileError(getErrorMessage(loadError, "Не удалось загрузить профиль"));
      }
    } finally {
      setProfileLoading(false);
    }
  }, []);

  const loadRecords = useCallback(async () => {
    setRecordsLoading(true);
    setRecordsError("");
    try {
      const token = getToken();
      const result = await fetchAthleteRecords(token, { offset: 0, limit: PAGE_SIZE });
      setRecords(result.items);
      setRecordsTotal(result.total);
    } catch (loadError) {
      setRecordsError(getErrorMessage(loadError, "Не удалось загрузить рекорды"));
    } finally {
      setRecordsLoading(false);
    }
  }, []);

  const loadFeedback = useCallback(async () => {
    setFeedbackLoading(true);
    setFeedbackError("");
    try {
      const token = getToken();
      const result = await fetchAthleteFeedback(token, { offset: 0, limit: PAGE_SIZE });
      setFeedbackItems(result.items);
      setFeedbackTotal(result.total);
    } catch (loadError) {
      setFeedbackError(getErrorMessage(loadError, "Не удалось загрузить обратную связь"));
    } finally {
      setFeedbackLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInvitations();
    loadProfile();
    loadRecords();
    loadFeedback();
  }, [loadInvitations, loadProfile, loadRecords, loadFeedback]);

  async function handleInvitationAction(invitationId, action) {
    setInvitationActionId(invitationId);
    setInvitationsError("");
    try {
      const token = getToken();
      if (action === "accept") {
        await acceptInvitation(token, invitationId);
      } else {
        await declineInvitation(token, invitationId);
      }
      await loadInvitations();
    } catch (actionError) {
      setInvitationsError(getErrorMessage(actionError, "Не удалось обработать приглашение"));
    } finally {
      setInvitationActionId("");
    }
  }

  async function handleProfileSubmit(event) {
    event.preventDefault();
    setProfileError("");
    setProfileMessage("");
    setProfileSaving(true);
    try {
      const token = getToken();
      await saveAthleteProfile(token, {
        height_cm: Number(profileForm.height_cm),
        weight_kg: Number(profileForm.weight_kg),
        age: Number(profileForm.age),
        gender: profileForm.gender,
      });
      setProfileMessage("Профиль сохранён");
      await loadProfile();
    } catch (submitError) {
      setProfileError(getErrorMessage(submitError, "Не удалось сохранить профиль"));
    } finally {
      setProfileSaving(false);
    }
  }

  function startEditRecord(record) {
    setEditingRecordId(record.id);
    setRecordForm({
      record_type: record.record_type,
      name: record.name,
      value: record.value,
      unit: record.unit,
      achieved_at: toDateTimeLocalValue(record.achieved_at),
    });
    setRecordFormError("");
  }

  function resetRecordForm() {
    setEditingRecordId("");
    setRecordForm(EMPTY_RECORD);
    setRecordFormError("");
  }

  async function handleRecordSubmit(event) {
    event.preventDefault();
    setRecordFormError("");
    setRecordSaving(true);
    try {
      const token = getToken();
      const payload = {
        record_type: recordForm.record_type,
        name: recordForm.name,
        value: recordForm.value,
        unit: recordForm.unit,
        achieved_at: fromDateTimeLocalValue(recordForm.achieved_at),
      };
      if (editingRecordId) {
        await updatePersonalRecord(token, editingRecordId, payload);
      } else {
        await createPersonalRecord(token, payload);
      }
      resetRecordForm();
      await loadRecords();
    } catch (submitError) {
      setRecordFormError(getErrorMessage(submitError, "Не удалось сохранить рекорд"));
    } finally {
      setRecordSaving(false);
    }
  }

  async function handleRecordDelete(recordId) {
    if (!window.confirm("Удалить этот рекорд?")) {
      return;
    }
    setRecordsError("");
    try {
      const token = getToken();
      await deletePersonalRecord(token, recordId);
      if (editingRecordId === recordId) {
        resetRecordForm();
      }
      await loadRecords();
    } catch (deleteError) {
      setRecordsError(getErrorMessage(deleteError, "Не удалось удалить рекорд"));
    }
  }

  async function handleFeedbackSubmit(event) {
    event.preventDefault();
    setFeedbackFormError("");
    setFeedbackSaving(true);
    try {
      const token = getToken();
      await submitWorkoutFeedback(token, {
        text: feedbackForm.text,
        garmin_url: feedbackForm.garmin_url.trim() || null,
      });
      setFeedbackForm(EMPTY_FEEDBACK);
      await loadFeedback();
    } catch (submitError) {
      setFeedbackFormError(getErrorMessage(submitError, "Не удалось отправить обратную связь"));
    } finally {
      setFeedbackSaving(false);
    }
  }

  return (
    <DashboardLayout title="Кабинет спортсмена" subtitle={user.email} onLogout={logout}>
      <section className="section">
        <h2>Приглашения от тренеров</h2>
        {invitationsLoading ? <LoadingMessage /> : null}
        {invitationsError ? <p className="form-error">{invitationsError}</p> : null}
        {!invitationsLoading && invitations.length === 0 ? (
          <EmptyState message="Новых приглашений нет." />
        ) : null}
        {!invitationsLoading && invitations.length > 0 ? (
          <ul className="invitation-list">
            {invitations.map((invitation) => (
              <li key={invitation.id} className="invitation-item">
                <div>
                  <strong>Приглашение от тренера</strong>
                  <p className="meta">ID тренера: {invitation.coach_id.slice(0, 8)}…</p>
                </div>
                <div className="stack-actions">
                  <button
                    type="button"
                    disabled={invitationActionId === invitation.id}
                    onClick={() => handleInvitationAction(invitation.id, "accept")}
                  >
                    Принять
                  </button>
                  <button
                    type="button"
                    className="button-secondary"
                    disabled={invitationActionId === invitation.id}
                    onClick={() => handleInvitationAction(invitation.id, "decline")}
                  >
                    Отклонить
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : null}
        {coaches.length > 0 ? <p className="meta">Ваши тренеры: {coaches.length}</p> : null}
      </section>

      <section className="section">
        <h2>Профиль</h2>
        {profileLoading ? <LoadingMessage /> : null}
        {profileError ? <p className="form-error">{profileError}</p> : null}
        {!profileLoading ? (
          <form className="form" onSubmit={handleProfileSubmit}>
            <label>
              Рост (см)
              <input
                type="number"
                min="1"
                value={profileForm.height_cm}
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, height_cm: event.target.value }))
                }
                required
              />
            </label>
            <label>
              Вес (кг)
              <input
                type="number"
                min="1"
                value={profileForm.weight_kg}
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, weight_kg: event.target.value }))
                }
                required
              />
            </label>
            <label>
              Возраст
              <input
                type="number"
                min="1"
                value={profileForm.age}
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, age: event.target.value }))
                }
                required
              />
            </label>
            <label>
              Пол
              <select
                value={profileForm.gender}
                onChange={(event) =>
                  setProfileForm((current) => ({ ...current, gender: event.target.value }))
                }
              >
                <option value="male">Мужской</option>
                <option value="female">Женский</option>
                <option value="other">Другой</option>
                <option value="prefer_not_to_say">Не указан</option>
              </select>
            </label>
            {profileMessage ? <p className="status success">{profileMessage}</p> : null}
            <button type="submit" disabled={profileSaving}>
              {profileSaving ? "Сохраняем..." : "Сохранить профиль"}
            </button>
          </form>
        ) : null}
      </section>

      <section className="section">
        <h2>Личные рекорды</h2>
        {recordsLoading ? <LoadingMessage /> : null}
        {recordsError ? <p className="form-error">{recordsError}</p> : null}
        <form className="form" onSubmit={handleRecordSubmit}>
          <label>
            Тип
            <select
              value={recordForm.record_type}
              onChange={(event) =>
                setRecordForm((current) => ({ ...current, record_type: event.target.value }))
              }
            >
              <option value="distance">Дистанция</option>
              <option value="exercise">Упражнение</option>
            </select>
          </label>
          <label>
            Название
            <input
              type="text"
              value={recordForm.name}
              onChange={(event) =>
                setRecordForm((current) => ({ ...current, name: event.target.value }))
              }
              required
            />
          </label>
          <label>
            Результат
            <input
              type="text"
              value={recordForm.value}
              onChange={(event) =>
                setRecordForm((current) => ({ ...current, value: event.target.value }))
              }
              required
            />
          </label>
          <label>
            Единица
            <input
              type="text"
              value={recordForm.unit}
              onChange={(event) =>
                setRecordForm((current) => ({ ...current, unit: event.target.value }))
              }
              required
            />
          </label>
          <label>
            Дата достижения
            <input
              type="datetime-local"
              value={recordForm.achieved_at}
              onChange={(event) =>
                setRecordForm((current) => ({ ...current, achieved_at: event.target.value }))
              }
              required
            />
          </label>
          <FieldError message={recordFormError} />
          <div className="stack-actions">
            <button type="submit" disabled={recordSaving}>
              {recordSaving
                ? "Сохраняем..."
                : editingRecordId
                  ? "Обновить рекорд"
                  : "Добавить рекорд"}
            </button>
            {editingRecordId ? (
              <button type="button" className="button-secondary" onClick={resetRecordForm}>
                Отмена
              </button>
            ) : null}
          </div>
        </form>
        {!recordsLoading && records.length === 0 ? (
          <EmptyState message="Рекордов пока нет." />
        ) : null}
        {!recordsLoading && records.length > 0 ? (
          <>
            <p className="meta">Всего: {recordsTotal}</p>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Тип</th>
                  <th>Название</th>
                  <th>Результат</th>
                  <th>Дата</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.id}>
                    <td>{formatRecordType(record.record_type)}</td>
                    <td>{record.name}</td>
                    <td>
                      {record.value} {record.unit}
                    </td>
                    <td>{formatDateTime(record.achieved_at)}</td>
                    <td className="table-actions">
                      <button
                        type="button"
                        className="button-link"
                        onClick={() => startEditRecord(record)}
                      >
                        Изменить
                      </button>
                      <button
                        type="button"
                        className="button-link danger"
                        onClick={() => handleRecordDelete(record.id)}
                      >
                        Удалить
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : null}
      </section>

      <section className="section">
        <h2>Обратная связь по тренировке</h2>
        <form className="form" onSubmit={handleFeedbackSubmit}>
          <label>
            Комментарий
            <textarea
              value={feedbackForm.text}
              onChange={(event) =>
                setFeedbackForm((current) => ({ ...current, text: event.target.value }))
              }
              rows={4}
              required
            />
          </label>
          <label>
            Ссылка Garmin Connect (необязательно)
            <input
              type="url"
              value={feedbackForm.garmin_url}
              onChange={(event) =>
                setFeedbackForm((current) => ({ ...current, garmin_url: event.target.value }))
              }
              placeholder="https://connect.garmin.com/..."
            />
          </label>
          <FieldError message={feedbackFormError} />
          <button type="submit" disabled={feedbackSaving}>
            {feedbackSaving ? "Отправляем..." : "Отправить"}
          </button>
        </form>
        {feedbackLoading ? <LoadingMessage /> : null}
        {feedbackError ? <p className="form-error">{feedbackError}</p> : null}
        {!feedbackLoading && feedbackItems.length === 0 ? (
          <EmptyState message="История обратной связи пуста." />
        ) : null}
        {!feedbackLoading && feedbackItems.length > 0 ? (
          <>
            <p className="meta">Всего: {feedbackTotal}</p>
            <ul className="feedback-list">
              {feedbackItems.map((item) => (
                <li key={item.id} className="feedback-item">
                  <p>{item.text}</p>
                  <p className="meta">{formatDateTime(item.created_at)}</p>
                  {item.garmin_url ? (
                    <a href={item.garmin_url} target="_blank" rel="noopener noreferrer">
                      Открыть в Garmin Connect
                    </a>
                  ) : null}
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </section>
    </DashboardLayout>
  );
}
