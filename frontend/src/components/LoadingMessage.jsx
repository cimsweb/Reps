export function LoadingMessage({ message = "Загрузка..." }) {
  return <p className="status">{message}</p>;
}
