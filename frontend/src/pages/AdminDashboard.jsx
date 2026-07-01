import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ApiError, fetchUsers } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { getToken } from "../auth/tokenStorage.js";

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
    <main className="page">
      <section className="card wide">
        <header className="dashboard-header">
          <div>
            <h1>Кабинет администратора</h1>
            <p>
              {user.email} · {user.role}
            </p>
          </div>
          <button type="button" onClick={logout}>
            Выйти
          </button>
        </header>

        <h2>Пользователи</h2>
        {loading ? <p className="status">Загрузка...</p> : null}
        {error ? <p className="form-error">{error}</p> : null}
        {!loading && !error && users.length === 0 ? (
          <p className="status">Пользователи не найдены</p>
        ) : null}
        {!loading && !error && users.length > 0 ? (
          <>
            <p className="meta">Всего: {total}</p>
            <table className="users-table">
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

        <p className="meta">
          Разделы тренера и спортсмена скрыты для admin UI. <Link to="/login">Сменить аккаунт</Link>
        </p>
      </section>
    </main>
  );
}
