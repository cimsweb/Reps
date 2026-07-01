import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  fetchLinkedAthleteFeedback,
  fetchLinkedAthleteProfile,
  fetchLinkedAthleteRecords,
} from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { getToken } from "../auth/tokenStorage.js";
import { DashboardLayout } from "../components/DashboardLayout.jsx";
import { EmptyState } from "../components/EmptyState.jsx";
import { LoadingMessage } from "../components/LoadingMessage.jsx";
import { getErrorMessage } from "../utils/apiErrors.js";
import { formatDateTime, formatGender, formatRecordType } from "../utils/formatters.js";

const PAGE_SIZE = 20;

export function CoachAthletePage() {
  const { athleteId } = useParams();
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState(null);
  const [records, setRecords] = useState([]);
  const [recordsTotal, setRecordsTotal] = useState(0);
  const [feedback, setFeedback] = useState([]);
  const [feedbackTotal, setFeedbackTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const token = getToken();
      const [profileResult, recordsResult, feedbackResult] = await Promise.all([
        fetchLinkedAthleteProfile(token, athleteId),
        fetchLinkedAthleteRecords(token, athleteId, { offset: 0, limit: PAGE_SIZE }),
        fetchLinkedAthleteFeedback(token, athleteId, { offset: 0, limit: PAGE_SIZE }),
      ]);
      setProfile(profileResult);
      setRecords(recordsResult.items);
      setRecordsTotal(recordsResult.total);
      setFeedback(feedbackResult.items);
      setFeedbackTotal(feedbackResult.total);
    } catch (loadError) {
      setProfile(null);
      setRecords([]);
      setFeedback([]);
      setError(getErrorMessage(loadError, "Не удалось загрузить данные спортсмена"));
    } finally {
      setLoading(false);
    }
  }, [athleteId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <DashboardLayout
      title="Карточка спортсмена"
      subtitle={`${user.email} · ${athleteId}`}
      onLogout={logout}
    >
      <p className="meta">
        <Link to="/coach">← Назад к списку</Link>
      </p>

      {loading ? <LoadingMessage /> : null}
      {error ? <p className="form-error">{error}</p> : null}

      {!loading && !error && profile ? (
        <>
          <section className="section">
            <h2>Профиль</h2>
            <dl className="profile-list">
              <div>
                <dt>Рост</dt>
                <dd>{profile.height_cm} см</dd>
              </div>
              <div>
                <dt>Вес</dt>
                <dd>{profile.weight_kg} кг</dd>
              </div>
              <div>
                <dt>Возраст</dt>
                <dd>{profile.age}</dd>
              </div>
              <div>
                <dt>Пол</dt>
                <dd>{formatGender(profile.gender)}</dd>
              </div>
              <div>
                <dt>Обновлён</dt>
                <dd>{formatDateTime(profile.updated_at)}</dd>
              </div>
            </dl>
          </section>

          <section className="section">
            <h2>Личные рекорды</h2>
            {records.length === 0 ? (
              <EmptyState message="Рекордов пока нет." />
            ) : (
              <>
                <p className="meta">Всего: {recordsTotal}</p>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Тип</th>
                      <th>Название</th>
                      <th>Результат</th>
                      <th>Дата</th>
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
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </section>

          <section className="section">
            <h2>Обратная связь</h2>
            {feedback.length === 0 ? (
              <EmptyState message="Обратной связи пока нет." />
            ) : (
              <>
                <p className="meta">Всего: {feedbackTotal}</p>
                <ul className="feedback-list">
                  {feedback.map((item) => (
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
            )}
          </section>
        </>
      ) : null}
    </DashboardLayout>
  );
}
