import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchCoachAthletes, fetchCoachInvitations, sendInvitation } from "../../api/client.js";
import { getToken } from "../../auth/tokenStorage.js";
import { buildCoachAthleteListItems } from "../../utils/coachAthleteDisplay.js";
import { getErrorMessage } from "../../utils/apiErrors.js";
import { Button } from "../ui/Button.jsx";
import { SegmentedControl } from "../ui/SegmentedControl.jsx";
import { EmptyState } from "../EmptyState.jsx";
import { LoadingMessage } from "../LoadingMessage.jsx";
import { CoachAthleteCard } from "./CoachAthleteCard.jsx";
import { CoachAthleteRow } from "./CoachAthleteRow.jsx";
import { InviteAthleteModal } from "./InviteAthleteModal.jsx";

const VIEW_OPTIONS = [
  { value: "cards", label: "Плитка" },
  { value: "compact", label: "Список" },
];

function buildTodayLabel() {
  return new Date().toLocaleDateString("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

export function CoachListScreen() {
  const [athletes, setAthletes] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [viewMode, setViewMode] = useState("cards");
  const [inviteOpen, setInviteOpen] = useState(false);
  const [resendError, setResendError] = useState("");

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
      setError(getErrorMessage(loadError, "Не удалось загрузить список спортсменов"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const listItems = useMemo(
    () => buildCoachAthleteListItems(athletes, invitations),
    [athletes, invitations],
  );

  async function handleResendInvite(athlete) {
    if (!athlete.email) {
      return;
    }
    setResendError("");
    try {
      const token = getToken();
      await sendInvitation(token, athlete.email);
      await loadData();
    } catch (resendErr) {
      setResendError(getErrorMessage(resendErr, "Не удалось отправить напоминание"));
    }
  }

  return (
    <div className="coach-list-screen">
      <header className="coach-list-screen__header">
        <div>
          <p className="coach-list-screen__date">{buildTodayLabel()}</p>
          <h1 className="coach-list-screen__title">Спортсмены</h1>
        </div>
        <div className="coach-list-screen__actions">
          <SegmentedControl options={VIEW_OPTIONS} value={viewMode} onChange={setViewMode} />
          <Button type="button" className="coach-list-screen__invite-btn" onClick={() => setInviteOpen(true)}>
            <span className="coach-list-screen__invite-btn-full">+ Пригласить спортсмена</span>
            <span className="coach-list-screen__invite-btn-short">+ Пригласить</span>
          </Button>
        </div>
      </header>

      {loading ? <LoadingMessage /> : null}
      {error ? <p className="form-error">{error}</p> : null}
      {resendError ? <p className="form-error">{resendError}</p> : null}

      {!loading && !error && listItems.length === 0 ? (
        <div className="coach-list-screen__empty">
          <EmptyState message="Спортсменов пока нет. Отправьте первое приглашение." />
          <Button type="button" onClick={() => setInviteOpen(true)}>
            Пригласить спортсмена
          </Button>
        </div>
      ) : null}

      {!loading && !error && listItems.length > 0 && viewMode === "cards" ? (
        <div className="coach-athlete-grid">
          {listItems.map((athlete) => (
            <CoachAthleteCard
              key={athlete.key}
              athlete={athlete}
              onResendInvite={handleResendInvite}
            />
          ))}
        </div>
      ) : null}

      {!loading && !error && listItems.length > 0 && viewMode === "compact" ? (
        <div className="coach-athlete-table">
          <div className="coach-athlete-table__head">
            <span>Спортсмен</span>
            <span>Сегодня</span>
            <span>Статус</span>
            <span />
          </div>
          {listItems.map((athlete) => (
            <CoachAthleteRow
              key={athlete.key}
              athlete={athlete}
              onResendInvite={handleResendInvite}
            />
          ))}
        </div>
      ) : null}

      <InviteAthleteModal
        open={inviteOpen}
        onClose={() => setInviteOpen(false)}
        onInvited={loadData}
      />
    </div>
  );
}
