import { ApiError } from "../api/client.js";

export function getErrorMessage(error, fallback = "Произошла ошибка") {
  if (error instanceof ApiError) {
    return error.message;
  }
  return fallback;
}

export function isAiUnavailableError(error) {
  return error instanceof ApiError && (error.status === 503 || error.code === "ai_unavailable");
}
