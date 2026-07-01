const STATUS_LABELS = {
  pending: "Ожидает",
  accepted: "Принято",
  declined: "Отклонено",
};

export function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{STATUS_LABELS[status] ?? status}</span>;
}
