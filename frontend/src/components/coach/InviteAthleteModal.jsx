import { useState } from "react";

import { sendInvitation } from "../../api/client.js";
import { getToken } from "../../auth/tokenStorage.js";
import { getErrorMessage } from "../../utils/apiErrors.js";
import { Button } from "../ui/Button.jsx";
import { Input } from "../ui/Input.jsx";
import { Modal } from "../ui/Modal.jsx";
import { FieldError } from "../FieldError.jsx";

export function InviteAthleteModal({ open, onClose, onInvited }) {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);

  function handleClose() {
    setEmail("");
    setName("");
    setError("");
    setSent(false);
    onClose();
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      return;
    }

    setSending(true);
    setError("");
    try {
      const token = getToken();
      await sendInvitation(token, trimmedEmail);
      setSent(true);
      await onInvited?.();
    } catch (submitError) {
      setError(getErrorMessage(submitError, "Не удалось отправить приглашение"));
    } finally {
      setSending(false);
    }
  }

  return (
    <Modal open={open} onClose={handleClose} title="Пригласить спортсмена">
      {sent ? (
        <div className="coach-invite-success">
          <p className="coach-invite-success__title">Приглашение отправлено</p>
          <p className="coach-invite-success__text">
            Спортсмен получит письмо на <strong>{email.trim()}</strong> со ссылкой для регистрации.
            {name.trim() ? ` Имя для обращения: ${name.trim()}.` : ""}
          </p>
          <Button type="button" variant="primaryDark" block onClick={handleClose}>
            Готово
          </Button>
        </div>
      ) : (
        <form className="coach-invite-form" onSubmit={handleSubmit}>
          <Input
            label="Email спортсмена"
            type="email"
            value={email}
            placeholder="athlete@example.com"
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <Input
            label="Имя (необязательно)"
            value={name}
            placeholder="Как обращаться к спортсмену"
            uppercaseLabel={false}
            onChange={(event) => setName(event.target.value)}
          />
          <FieldError message={error} />
          <Button type="submit" block loading={sending} disabled={!email.trim()}>
            Отправить приглашение
          </Button>
        </form>
      )}
    </Modal>
  );
}
