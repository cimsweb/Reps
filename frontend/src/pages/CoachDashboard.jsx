import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchCoachAthletes, fetchCoachInvitations, sendInvitation } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { getToken } from "../auth/tokenStorage.js";
import { DashboardLayout } from "../components/DashboardLayout.jsx";
import { EmptyState } from "../components/EmptyState.jsx";
import { FieldError } from "../components/FieldError.jsx";
import { LoadingMessage } from "../components/LoadingMessage.jsx";
import { StatusBadge } from "../components/StatusBadge.jsx";
import { getErrorMessage } from "../utils/apiErrors.js";
import { formatDateTime } from "../utils/formatters.js";

export function CoachDashboard() {
  const { user, logout } = useAuth();
  const [invitations, setInvitations] = useState([]);
  const [athletes, setAthletes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteError, setInviteError] = useState("");
  const [inviting, setInviting] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const token = getToken();
      const [invitationResult, athleteResult] = await Promise.all([
        fetchCoachInvitations(token),
        fetchCoachAthletes(token),
      ]);
      setInvitations(invitationResult.items);
      setAthletes(athleteResult.items);
    } catch (loadError) {
      setError(getErrorMessage(loadError, "Не удалось загрузить данные"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleInviteSubmit(event) {
    event.preventDefault();
    setInviteError("");
    setInviting(true);
    try {
      const token = getToken();
      await sendInvitation(token, inviteEmail.trim());
      setInviteEmail("");
      await loadData();
    } catch (submitError) {
      setInviteError(getErrorMessage(submitError, "Не удалось отправить приглашение"));
    } finally {
      setInviting(false);
    }
  }

  return (
    <DashboardLayout title="Кабинет тренера" subtitle={user.email} onLogout={logout}>
      <section className="section">
        <h2>Пригласить спортсмена</h2>
        <form className="form inline-form" onSubmit={handleInviteSubmit}>
          <label>
            Email спортсмена
            <input
              type="email"
              value={inviteEmail}
              onChange={(event) => setInviteEmail(event.target.value)}
              placeholder="athlete@example.com"
              required
            />
            <FieldError message={inviteError} />
          </label>
          <button type="submit" disabled={inviting}>
            {inviting ? "Отправляем..." : "Отправить приглашение"}
          </button>
        </form>
      </section>

      <section className="section">
        <h2>Приглашения</h2>
        {loading ? <LoadingMessage /> : null}
        {error ? <p className="form-error">{error}</p> : null}
        {!loading && !error && invitations.length === 0 ? (
          <EmptyState message="Приглашений пока нет. Отправьте первое приглашение по email." />
        ) : null}
        {!loading && !error && invitations.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Статус</th>
                <th>Отправлено</th>
              </tr>
            </thead>
            <tbody>
              {invitations.map((item) => (
                <tr key={item.id}>
                  <td>{item.athlete_email}</td>
                  <td>
                    <StatusBadge status={item.status} />
                  </td>
                  <td>{formatDateTime(item.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </section>

      <section className="section">
        <h2>Мои спортсмены</h2>
        {loading ? <LoadingMessage /> : null}
        {!loading && !error && athletes.length === 0 ? (
          <EmptyState message="Связанных спортсменов пока нет. Дождитесь принятия приглашения." />
        ) : null}
        {!loading && !error && athletes.length > 0 ? (
          <ul className="link-list">
            {athletes.map((athlete) => (
              <li key={athlete.id}>
                <Link to={`/coach/athletes/${athlete.athlete_id}`}>
                  Спортсмен {athlete.athlete_id.slice(0, 8)}…
                </Link>
                <span className="meta">с {formatDateTime(athlete.created_at)}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    </DashboardLayout>
  );
}
