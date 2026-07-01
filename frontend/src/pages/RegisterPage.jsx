import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { FieldError } from "../components/FieldError.jsx";

export function RegisterPage() {
  const navigate = useNavigate();
  const { register, isAuthenticated, user } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("coach");
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated && user) {
    return <Navigate to={`/${user.role}`} replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setFieldErrors({});
    setFormError("");
    setSubmitting(true);

    try {
      await register(email, password, role);
      navigate("/login");
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.code === "validation_error") {
          setFormError(error.message);
        } else if (error.code === "email_already_exists") {
          setFieldErrors({ email: error.message });
        } else {
          setFormError(error.message);
        }
      } else {
        setFormError("Не удалось зарегистрироваться");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page">
      <section className="card">
        <h1>Регистрация</h1>
        <form className="form" onSubmit={handleSubmit}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
            <FieldError message={fieldErrors.email} />
          </label>
          <label>
            Пароль
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            <FieldError message={fieldErrors.password} />
          </label>
          <label>
            Роль
            <select value={role} onChange={(event) => setRole(event.target.value)}>
              <option value="coach">Тренер</option>
              <option value="athlete">Спортсмен</option>
            </select>
          </label>
          {formError ? <p className="form-error">{formError}</p> : null}
          <button type="submit" disabled={submitting}>
            {submitting ? "Создаём аккаунт..." : "Зарегистрироваться"}
          </button>
        </form>
        <p>
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </section>
    </main>
  );
}
