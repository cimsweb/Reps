import { useCallback, useEffect, useState } from "react";

import { fetchAthleteProfile, saveAthleteProfile } from "../../api/client.js";
import { getToken } from "../../auth/tokenStorage.js";
import { getErrorMessage } from "../../utils/apiErrors.js";
import { LoadingMessage } from "../LoadingMessage.jsx";

const EMPTY_PROFILE = {
  height_cm: "",
  weight_kg: "",
  age: "",
  gender: "male",
};

export function AthleteProfileSection() {
  const [form, setForm] = useState(EMPTY_PROFILE);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const loadProfile = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const token = getToken();
      const profile = await fetchAthleteProfile(token);
      setForm({
        height_cm: String(profile.height_cm),
        weight_kg: String(profile.weight_kg),
        age: String(profile.age),
        gender: profile.gender,
      });
    } catch (loadError) {
      setError(getErrorMessage(loadError, "Не удалось загрузить профиль"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const token = getToken();
      await saveAthleteProfile(token, {
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        age: Number(form.age),
        gender: form.gender,
      });
      setMessage("Профиль сохранён.");
    } catch (submitError) {
      setError(getErrorMessage(submitError, "Не удалось сохранить профиль"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="athlete-profile-section">
      <h3 className="athlete-section-label">Профиль</h3>
      {loading ? <LoadingMessage /> : null}
      {error ? <p className="form-error">{error}</p> : null}
      {!loading ? (
        <form className="athlete-records-form" onSubmit={handleSubmit}>
          <label>
            Рост (см)
            <input
              type="number"
              min="1"
              value={form.height_cm}
              onChange={(event) => setForm((current) => ({ ...current, height_cm: event.target.value }))}
              required
            />
          </label>
          <label>
            Вес (кг)
            <input
              type="number"
              min="1"
              value={form.weight_kg}
              onChange={(event) => setForm((current) => ({ ...current, weight_kg: event.target.value }))}
              required
            />
          </label>
          <label>
            Возраст
            <input
              type="number"
              min="1"
              value={form.age}
              onChange={(event) => setForm((current) => ({ ...current, age: event.target.value }))}
              required
            />
          </label>
          <label>
            Пол
            <select
              value={form.gender}
              onChange={(event) => setForm((current) => ({ ...current, gender: event.target.value }))}
            >
              <option value="male">Мужской</option>
              <option value="female">Женский</option>
              <option value="other">Другой</option>
              <option value="prefer_not_to_say">Не указан</option>
            </select>
          </label>
          {message ? <p className="status success">{message}</p> : null}
          <button type="submit" disabled={saving}>
            {saving ? "Сохраняем..." : "Сохранить профиль"}
          </button>
        </form>
      ) : null}
    </section>
  );
}
