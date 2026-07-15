import { useNavigate } from "react-router-dom";

import { StatusChip } from "../ui/StatusChip.jsx";
import { Avatar } from "../ui/Avatar.jsx";

export function CoachAthleteRow({ athlete, onResendInvite }) {
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
    <button
      type="button"
      className="coach-athlete-row"
      disabled={!athlete.athleteId}
      onClick={handleOpen}
    >
      <div className="coach-athlete-row__athlete">
        <Avatar
          initials={athlete.initials}
          size="sm"
          style={{ background: athlete.avatarColor }}
        />
        <div>
          <p className="coach-athlete-row__name">{athlete.name}</p>
          <p className="coach-athlete-row__meta">{athlete.email ?? athlete.level}</p>
        </div>
      </div>
      <div className="coach-athlete-row__today">
        {athlete.invitePending ? (
          <button type="button" className="button-link" onClick={handleResend}>
            Напомнить
          </button>
        ) : (
          athlete.todayType
        )}
      </div>
      <div className="coach-athlete-row__status">
        <StatusChip variant={athlete.status.variant} label={athlete.status.label} />
      </div>
      <span className="coach-athlete-row__chevron" aria-hidden="true">
        ›
      </span>
    </button>
  );
}
