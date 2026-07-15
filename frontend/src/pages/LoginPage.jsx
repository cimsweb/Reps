import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { AuthErrorBanner, AuthRoleSelector } from "../components/auth/index.js";
import { AuthLayout } from "../components/layout/AuthLayout.jsx";
import { Button } from "../components/ui/Button.jsx";
import { Input } from "../components/ui/Input.jsx";
import { Label } from "../components/ui/Label.jsx";

export function LoginPage() {
  const navigate = useNavigate();
  const { login, isAuthenticated, user } = useAuth();
  const [role, setRole] = useState("athlete");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated && user) {
    return <Navigate to={`/${user.role}`} replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setFormError("");

    if (!email.trim() || !password.trim()) {
      setFormError("Введите email и пароль");
      return;
    }

    setSubmitting(true);

    try {
      const loggedInUser = await login(email, password);
      navigate(`/${loggedInUser.role}`);
    } catch (error) {
      if (error instanceof ApiError) {
        setFormError(error.message);
      } else {
        setFormError("Не удалось выполнить вход");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <div className="auth-heading">
        <h1 className="auth-heading__title">С возвращением</h1>
        <p className="auth-heading__subtitle">Войдите, чтобы продолжить тренировки</p>
      </div>

      <AuthRoleSelector value={role} onChange={setRole} />

      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <Input
          label="Email"
          type="email"
          name="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />

        <div>
          <div className="auth-password-label">
            <Label htmlFor="login-password">Пароль</Label>
            <button type="button" className="auth-forgot-link" disabled title="Скоро">
              Забыли пароль?
            </button>
          </div>
          <Input
            id="login-password"
            type="password"
            name="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            uppercaseLabel={false}
          />
        </div>

        <AuthErrorBanner message={formError} />

        <Button type="submit" variant="primary" block loading={submitting}>
          {submitting ? "Входим…" : "Войти"}
        </Button>
      </form>

      <p className="auth-footer">
        Нет аккаунта? <Link to={`/register?role=${role}`}>Зарегистрироваться</Link>
      </p>
    </AuthLayout>
  );
}
