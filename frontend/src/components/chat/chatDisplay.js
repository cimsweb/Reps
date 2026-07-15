export function buildPartnerLabel(email, roleLabel = "тренер") {
  const localPart = email?.split("@")[0] ?? roleLabel;
  const name = localPart.replace(/[._]/g, " ");
  const formatted = name.charAt(0).toUpperCase() + name.slice(1);
  return `${formatted}, ${roleLabel}`;
}

export function buildPartnerInitials(email, fallback = "??") {
  if (!email) {
    return fallback;
  }
  const parts = email.split("@")[0]?.split(/[._]/).filter(Boolean) ?? [];
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return email.slice(0, 2).toUpperCase();
}

export function buildAthleteListLabel(conversation) {
  const email = conversation.partner_email ?? "спортсмен";
  return buildPartnerLabel(email, "спортсмен").replace(", спортсмен", "");
}
