import { formatDateTime } from "./formatters.js";

const AVATAR_COLORS = ["#1f9d55", "#1f6feb", "#8a6d1a", "#c23b4a", "#5b6b68"];

function pickAvatarColor(seed) {
  const hash = [...seed].reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return AVATAR_COLORS[hash % AVATAR_COLORS.length];
}

function buildInitials(label) {
  const parts = label.split(/[\s@._-]+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return label.slice(0, 2).toUpperCase();
}

function buildLinkedAthleteItem(athlete) {
  const shortId = athlete.athlete_id.slice(0, 8);
  const name = `Спортсмен ${shortId}`;

  return {
    key: athlete.id,
    kind: "active",
    athleteId: athlete.athlete_id,
    name,
    email: null,
    level: "Подключён",
    compliancePercent: null,
    todayType: "Тренировка не загружена",
    status: { variant: "done", label: "Активен" },
    lastActivity: formatDateTime(athlete.created_at),
    initials: buildInitials(shortId),
    avatarColor: pickAvatarColor(athlete.athlete_id),
    invitePending: false,
    invitationId: null,
  };
}

function buildPendingInvitationItem(invitation) {
  const email = invitation.athlete_email;
  const name = email.split("@")[0] ?? email;

  return {
    key: invitation.id,
    kind: "pending",
    athleteId: null,
    name,
    email,
    level: "Ожидает регистрации",
    compliancePercent: null,
    todayType: null,
    status: { variant: "pending", label: "Приглашение отправлено" },
    lastActivity: formatDateTime(invitation.created_at),
    initials: buildInitials(name),
    avatarColor: "#8a9a96",
    invitePending: true,
    invitationId: invitation.id,
  };
}

export function buildCoachAthleteListItems(athletes, invitations) {
  const linked = athletes.map(buildLinkedAthleteItem);
  const pending = invitations
    .filter((invitation) => invitation.status === "pending")
    .map(buildPendingInvitationItem);

  return [...linked, ...pending];
}
