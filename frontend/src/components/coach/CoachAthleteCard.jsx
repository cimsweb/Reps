import { useNavigate } from "react-router-dom";

import { StatusChip } from "../ui/StatusChip.jsx";
import { Avatar } from "../ui/Avatar.jsx";

export function CoachAthleteCard({ athlete, onResendInvite }) {
  const navigate = useNavigate();

  function handleOpen() {
    if (athlete.athleteId) {
      navigate(`/coach/athletes/${athlete.athleteId}`);
    }
  }

  function handleResend(event) {
    event.stopPropagation();
    onResendInvite?.(athlete);
  }

  return (
    <article
      className={[
        "coach-athlete-card",
        athlete.athleteId ? "coach-athlete-card--clickable" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      onClick={handleOpen}
      onKeyDown={(event) => {
        if (event.key === "Enter" && athlete.athleteId) {
          handleOpen();
        }
      }}
      role={athlete.athleteId ? "button" : undefined}
      tabIndex={athlete.athleteId ? 0 : undefined}
    >
      <div className="coach-athlete-card__header">
        <Avatar
          initials={athlete.initials}
          size="lg"
          style={{ background: athlete.avatarColor }}
        />
        <div>
          <p className="coach-athlete-card__name">{athlete.name}</p>
          <p className="coach-athlete-card__level">{athlete.level}</p>
        </div>
      </div>

      {athlete.invitePending ? (
        <div className="coach-athlete-card__pending">
          <p className="coach-athlete-card__pending-email">✉️ {athlete.email}</p>
          <button type="button" className="button-link" onClick={handleResend}>
            Напомнить
          </button>
        </div>
      ) : (
        <div className="coach-athlete-card__today">
          <p className="coach-athlete-card__today-type">{athlete.todayType}</p>
          <StatusChip variant={athlete.status.variant} label={athlete.status.label} />
        </div>
      )}

      {athlete.invitePending ? (
        <StatusChip variant="pending" label="Приглашение отправлено" />
      ) : null}
    </article>
  );
}
