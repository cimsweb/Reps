import { useCallback, useEffect, useState } from "react";

import {
  acceptInvitation,
  declineInvitation,
  fetchAthleteCoaches,
  fetchAthleteInvitations,
} from "../../api/client.js";
import { getToken } from "../../auth/tokenStorage.js";
import { Card } from "../ui/Card.jsx";
import { getErrorMessage } from "../../utils/apiErrors.js";
import { LoadingMessage } from "../LoadingMessage.jsx";

export function InvitationsBanner() {
  const [invitations, setInvitations] = useState([]);
  const [coaches, setCoaches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionId, setActionId] = useState("");

  const loadInvitations = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const token = getToken();
      const [invitationResult, coachResult] = await Promise.all([
        fetchAthleteInvitations(token),
        fetchAthleteCoaches(token),
      ]);
      setInvitations(invitationResult.items);
      setCoaches(coachResult.items);
    } catch (loadError) {
      setError(getErrorMessage(loadError, "Не удалось загрузить приглашения"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInvitations();
  }, [loadInvitations]);

  async function handleAction(invitationId, action) {
    setActionId(invitationId);
    try {
      const token = getToken();
      if (action === "accept") {
        await acceptInvitation(token, invitationId);
      } else {
        await declineInvitation(token, invitationId);
      }
      await loadInvitations();
    } catch (actionError) {
      setError(getErrorMessage(actionError, "Не удалось обработать приглашение"));
    } finally {
      setActionId("");
    }
  }

  if (loading) {
    return <LoadingMessage />;
  }

  if (!error && invitations.length === 0 && coaches.length === 0) {
    return null;
  }

  return (
    <div className="athlete-invitations">
      {error ? <p className="form-error">{error}</p> : null}
      {invitations.map((invitation) => (
        <Card key={invitation.id} className="athlete-invitation-card">
          <p className="athlete-invitation-card__title">Приглашение от тренера</p>
          <p className="athlete-invitation-card__meta">
            ID тренера: {invitation.coach_id.slice(0, 8)}…
          </p>
          <div className="athlete-invitation-card__actions">
            <button
              type="button"
              disabled={actionId === invitation.id}
              onClick={() => handleAction(invitation.id, "accept")}
            >
              Принять
            </button>
            <button
              type="button"
              className="button-secondary"
              disabled={actionId === invitation.id}
              onClick={() => handleAction(invitation.id, "decline")}
            >
              Отклонить
            </button>
          </div>
        </Card>
      ))}
      {coaches.length > 0 ? (
        <p className="athlete-coaches-meta">Ваши тренеры: {coaches.length}</p>
      ) : null}
    </div>
  );
}
