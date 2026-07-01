import { ApiError } from "../api/client.js";

export function getErrorMessage(error, fallback = "Произошла ошибка") {
  if (error instanceof ApiError) {
    return error.message;
  }
  return fallback;
}
