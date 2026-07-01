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
    throw new ApiError(0, "network_error", "Сервер недоступен. Запустите API: npm run dev:api");
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

function paginationQuery({ offset = 0, limit = 20 } = {}) {
  return new URLSearchParams({
    offset: String(offset),
    limit: String(limit),
  }).toString();
}

export function sendInvitation(token, email) {
  return apiRequest("/coach/invitations", {
    method: "POST",
    token,
    body: { email },
  });
}

export function fetchCoachInvitations(token) {
  return apiRequest("/coach/invitations", { token });
}

export function fetchAthleteInvitations(token) {
  return apiRequest("/athlete/invitations", { token });
}

export function acceptInvitation(token, invitationId) {
  return apiRequest(`/athlete/invitations/${invitationId}/accept`, {
    method: "POST",
    token,
  });
}

export function declineInvitation(token, invitationId) {
  return apiRequest(`/athlete/invitations/${invitationId}/decline`, {
    method: "POST",
    token,
  });
}

export function fetchCoachAthletes(token) {
  return apiRequest("/coach/athletes", { token });
}

export function fetchAthleteCoaches(token) {
  return apiRequest("/athlete/coaches", { token });
}

export function fetchAthleteProfile(token) {
  return apiRequest("/athlete/profile", { token });
}

export function saveAthleteProfile(token, payload) {
  return apiRequest("/athlete/profile", {
    method: "PUT",
    token,
    body: payload,
  });
}

export function fetchLinkedAthleteProfile(token, athleteId) {
  return apiRequest(`/coach/athletes/${athleteId}/profile`, { token });
}

export function fetchAthleteRecords(token, pagination = {}) {
  const query = paginationQuery(pagination);
  return apiRequest(`/athlete/records?${query}`, { token });
}

export function createPersonalRecord(token, payload) {
  return apiRequest("/athlete/records", {
    method: "POST",
    token,
    body: payload,
  });
}

export function updatePersonalRecord(token, recordId, payload) {
  return apiRequest(`/athlete/records/${recordId}`, {
    method: "PUT",
    token,
    body: payload,
  });
}

export function deletePersonalRecord(token, recordId) {
  return apiRequest(`/athlete/records/${recordId}`, {
    method: "DELETE",
    token,
  });
}

export function fetchLinkedAthleteRecords(token, athleteId, pagination = {}) {
  const query = paginationQuery(pagination);
  return apiRequest(`/coach/athletes/${athleteId}/records?${query}`, { token });
}

export function fetchAthleteFeedback(token, pagination = {}) {
  const query = paginationQuery(pagination);
  return apiRequest(`/athlete/feedback?${query}`, { token });
}

export function submitWorkoutFeedback(token, payload) {
  return apiRequest("/athlete/feedback", {
    method: "POST",
    token,
    body: payload,
  });
}

export function fetchLinkedAthleteFeedback(token, athleteId, pagination = {}) {
  const query = paginationQuery(pagination);
  return apiRequest(`/coach/athletes/${athleteId}/feedback?${query}`, { token });
}
