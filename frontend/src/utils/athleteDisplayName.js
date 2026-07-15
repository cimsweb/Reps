export function buildAthleteDisplayName(user) {
  if (!user?.email) {
    return "Спортсмен";
  }

  const localPart = user.email.split("@")[0] ?? "Спортсмен";
  if (!localPart) {
    return "Спортсмен";
  }

  return localPart.charAt(0).toUpperCase() + localPart.slice(1);
}

export function buildAthleteGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) {
    return "Доброе утро";
  }
  if (hour < 18) {
    return "Добрый день";
  }
  return "Добрый вечер";
}
