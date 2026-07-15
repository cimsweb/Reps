export function formatDateTime(value) {
  if (!value) {
    return "—";
  }
  return new Date(value).toLocaleString();
}

export function formatGender(value) {
  const labels = {
    male: "Мужской",
    female: "Женский",
    other: "Другой",
    prefer_not_to_say: "Не указан",
  };
  return labels[value] ?? value;
}

export function formatRecordType(value) {
  const labels = {
    distance: "Дистанция",
    exercise: "Упражнение",
  };
  return labels[value] ?? value;
}

export function toDateTimeLocalValue(isoString) {
  if (!isoString) {
    return "";
  }
  const date = new Date(isoString);
  const offset = date.getTimezoneOffset();
  const local = new Date(date.getTime() - offset * 60_000);
  return local.toISOString().slice(0, 16);
}

export function fromDateTimeLocalValue(value) {
  if (!value) {
    return new Date().toISOString();
  }
  return new Date(value).toISOString();
}

export function formatWorkoutType(value) {
  const labels = {
    run: "Бег",
    bike: "Велосипед",
    gym: "Зал",
  };
  return labels[value] ?? value;
}

export function formatDate(value) {
  if (!value) {
    return "—";
  }
  return new Date(`${value}T00:00:00`).toLocaleDateString();
}

export function toDateInputValue(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function addDaysToDateString(dateString, days) {
  const date = new Date(`${dateString}T00:00:00`);
  date.setDate(date.getDate() + days);
  return toDateInputValue(date);
}

export function formatPaceSecondsPerKm(seconds) {
  if (!seconds) {
    return null;
  }
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${String(secs).padStart(2, "0")}/км`;
}
