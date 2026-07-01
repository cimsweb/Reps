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
