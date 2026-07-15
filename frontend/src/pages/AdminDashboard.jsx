import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError, fetchUsers } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { getToken } from "../auth/tokenStorage.js";
import { EmptyState } from "../components/EmptyState.jsx";
import { LoadingMessage } from "../components/LoadingMessage.jsx";
import { StatusPage } from "../components/layout/StatusPage.jsx";
import { Button, Card, ErrorBanner } from "../components/ui/index.js";

export function AdminDashboard() {
  const { user, logout } = useAuth();
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadUsers() {
      setLoading(true);
      setError("");
      try {
        const token = getToken();
        const result = await fetchUsers(token);
        setUsers(result.items);
        setTotal(result.total);
      } catch (loadError) {
        if (loadError instanceof ApiError) {
          setError(loadError.message);
        } else {
          setError("Не удалось загрузить пользователей");
        }
      } finally {
        setLoading(false);
      }
    }

    loadUsers();
  }, []);

  return (
    <StatusPage wide>
      <Card className="admin-dashboard">
        <header className="admin-dashboard__header">
          <div>
            <h1 className="admin-dashboard__title">Кабинет администратора</h1>
            <p className="text-muted">
              {user.email} · {user.role}
            </p>
          </div>
          <Button variant="outline" onClick={logout}>
            Выйти
          </Button>
        </header>

        <h2 className="admin-dashboard__section-title">Пользователи</h2>
        {loading ? <LoadingMessage /> : null}
        {error ? <ErrorBanner message={error} /> : null}
        {!loading && !error && users.length === 0 ? (
          <EmptyState message="Пользователи не найдены." icon="👤" />
        ) : null}
        {!loading && !error && users.length > 0 ? (
          <>
            <p className="admin-dashboard__meta">Всего: {total}</p>
            <table className="admin-dashboard__table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Роль</th>
                  <th>Дата регистрации</th>
                </tr>
              </thead>
              <tbody>
                {users.map((item) => (
                  <tr key={item.id}>
                    <td>{item.email}</td>
                    <td>{item.role}</td>
                    <td>{new Date(item.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : null}

        <p className="admin-dashboard__footer">
          Разделы тренера и спортсмена скрыты для admin UI. <Link to="/login">Сменить аккаунт</Link>
        </p>
      </Card>
    </StatusPage>
  );
}
