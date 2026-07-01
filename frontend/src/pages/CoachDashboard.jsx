import { useAuth } from "../auth/AuthContext.jsx";

export function CoachDashboard() {
  const { user, logout } = useAuth();

  return (
    <main className="page">
      <section className="card">
        <header className="dashboard-header">
          <div>
            <h1>Кабинет тренера</h1>
            <p>Добро пожаловать, {user.email}</p>
          </div>
          <button type="button" onClick={logout}>
            Выйти
          </button>
        </header>
        <dl className="profile-list">
          <div>
            <dt>ID</dt>
            <dd>{user.id}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{user.email}</dd>
          </div>
          <div>
            <dt>Роль</dt>
            <dd>{user.role}</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
