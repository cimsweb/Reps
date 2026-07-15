import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";

import { ApiError } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";
import { AuthErrorBanner, AuthRoleSelector } from "../components/auth/index.js";
import { AuthLayout } from "../components/layout/AuthLayout.jsx";
import { Button } from "../components/ui/Button.jsx";
import { Input } from "../components/ui/Input.jsx";

function resolveInitialRole(searchParams) {
  const roleParam = searchParams.get("role");
  return roleParam === "coach" ? "coach" : "athlete";
}

export function RegisterPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { register, isAuthenticated, user } = useAuth();
  const [role, setRole] = useState(() => resolveInitialRole(searchParams));
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (isAuthenticated && user) {
    return <Navigate to={`/${user.role}`} replace />;
  }

  const subtitle =
    role === "coach"
      ? "Создайте аккаунт тренера и приглашайте спортсменов"
      : "Создайте аккаунт спортсмена и принимайте приглашения";

  async function handleSubmit(event) {
    event.preventDefault();
    setFieldErrors({});
    setFormError("");

    if (!email.trim() || !password.trim()) {
      setFormError("Введите email и пароль");
      return;
    }

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
    <AuthLayout>
      <div className="auth-heading">
        <h1 className="auth-heading__title">Регистрация</h1>
        <p className="auth-heading__subtitle">{subtitle}</p>
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
          error={fieldErrors.email}
          required
        />

        <Input
          label="Пароль"
          type="password"
          name="password"
          autoComplete="new-password"
          placeholder="••••••••"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />

        <AuthErrorBanner message={formError} />

        <Button type="submit" variant="primary" block loading={submitting}>
          {submitting ? "Создаём аккаунт…" : "Зарегистрироваться"}
        </Button>
      </form>

      <p className="auth-footer">
        Уже есть аккаунт? <Link to="/login">Войти</Link>
      </p>
    </AuthLayout>
  );
}
