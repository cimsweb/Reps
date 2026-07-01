const API_BASE = "/api/v1";

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function parseResponse(response) {
  if (response.status === 204) {
    return null;
  }

  const data = await response.json();
  if (!response.ok) {
    throw new ApiError(response.status, data.error, data.message);
  }
  return data;
}

export async function apiRequest(path, { method = "GET", body, token } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(
      0,
      "network_error",
      "Сервер недоступен. Запустите API: npm run dev:api",
    );
  }

  return parseResponse(response);
}

export function registerUser(payload) {
  return apiRequest("/auth/register", { method: "POST", body: payload });
}

export function loginUser(payload) {
  return apiRequest("/auth/login", { method: "POST", body: payload });
}

export function logoutUser(token) {
  return apiRequest("/auth/logout", { method: "POST", token });
}

export function fetchCurrentUser(token) {
  return apiRequest("/auth/me", { token });
}

export function fetchUsers(token, { offset = 0, limit = 20 } = {}) {
  const params = new URLSearchParams({
    offset: String(offset),
    limit: String(limit),
  });
  return apiRequest(`/admin/users?${params.toString()}`, { token });
}
