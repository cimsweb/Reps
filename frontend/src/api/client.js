import { withAiProviderSettings } from "../utils/aiSettingsStorage.js";

const API_BASE = "/api/v1";

export class ApiError extends Error {
  constructor(status, code, message, extra = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.fallback = extra.fallback;
    this.requestPath = extra.requestPath ?? null;
    this.requestBody = extra.requestBody ?? null;
  }
}

async function parseResponse(response, requestMeta) {
  if (response.status === 204) {
    return null;
  }

  const data = await response.json();
  if (!response.ok) {
    throw new ApiError(response.status, data.error, data.message, {
      fallback: data.fallback,
      requestPath: requestMeta.requestPath,
      requestBody: requestMeta.requestBody,
    });
  }
  return data;
}

export async function apiRequest(path, { method = "GET", body, token } = {}) {
  const requestPath = `${API_BASE}${path}`;
  const requestMeta = {
    requestPath,
    requestBody: body ?? null,
  };
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(requestPath, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "network_error", "Сервер недоступен. Запустите API: npm run dev:api", requestMeta);
  }

  return parseResponse(response, requestMeta);
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

function trainingPeriodQuery({ period = "week", anchorDate } = {}) {
  const params = new URLSearchParams({ period });
  if (anchorDate) {
    params.set("anchor_date", anchorDate);
  }
  return params.toString();
}

export function fetchCoachAthleteTrainingPlan(token, athleteId, options = {}) {
  const query = trainingPeriodQuery(options);
  return apiRequest(`/coach/athletes/${athleteId}/training-plan?${query}`, { token });
}

export function fetchAthleteTrainingPlan(token, options = {}) {
  const query = trainingPeriodQuery(options);
  return apiRequest(`/athlete/training-plan?${query}`, { token });
}

export function fetchCoachAthleteWorkoutReports(token, athleteId, options = {}) {
  const query = trainingPeriodQuery(options);
  return apiRequest(`/coach/athletes/${athleteId}/workout-reports?${query}`, { token });
}

export function fetchAthleteWorkoutReports(token, options = {}) {
  const query = trainingPeriodQuery(options);
  return apiRequest(`/athlete/workout-reports?${query}`, { token });
}

export function submitWorkoutReport(token, workoutId, payload) {
  return apiRequest(`/athlete/planned-workouts/${workoutId}/report`, {
    method: "POST",
    token,
    body: payload,
  });
}

export function parseTrainingPlanText(token, athleteId, payload) {
  return apiRequest(`/coach/athletes/${athleteId}/training-plans/parse`, {
    method: "POST",
    token,
    body: payload,
  });
}

export function createTrainingPlanFromText(token, athleteId, payload) {
  return apiRequest(`/coach/athletes/${athleteId}/training-plans/from-text`, {
    method: "POST",
    token,
    body: payload,
  });
}

export function updateTrainingPlanRawText(token, planId, payload) {
  return apiRequest(`/coach/training-plans/${planId}/raw-text`, {
    method: "PATCH",
    token,
    body: payload,
  });
}

export function fetchCoachAthleteTrainingPlanText(token, athleteId, options = {}) {
  const query = trainingPeriodQuery(options);
  return apiRequest(`/coach/athletes/${athleteId}/training-plan/text?${query}`, { token });
}

export function fetchAthleteTrainingPlanText(token, options = {}) {
  const query = trainingPeriodQuery(options);
  return apiRequest(`/athlete/training-plan/text?${query}`, { token });
}

async function getActiveAgentSession(path, token) {
  try {
    return await apiRequest(path, { token });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export function startPlanAgentSession(token, athleteId, payload) {
  return apiRequest(`/coach/athletes/${athleteId}/training-plans/ai/sessions`, {
    method: "POST",
    token,
    body: withAiProviderSettings(payload),
  });
}

export function sendPlanAgentMessage(token, sessionId, payload) {
  return apiRequest(`/coach/training-plans/ai/sessions/${sessionId}/messages`, {
    method: "POST",
    token,
    body: withAiProviderSettings(payload),
  });
}

export function getPlanAgentSession(token, sessionId) {
  return apiRequest(`/coach/training-plans/ai/sessions/${sessionId}`, { token });
}

export function getActivePlanAgentSession(token, athleteId) {
  return getActiveAgentSession(
    `/coach/athletes/${athleteId}/training-plans/ai/sessions/active`,
    token,
  );
}

export function confirmPlanAgentDraft(token, sessionId, payload = {}) {
  return apiRequest(`/coach/training-plans/ai/sessions/${sessionId}/confirm`, {
    method: "POST",
    token,
    body: payload,
  });
}

export function startReportAgentSession(token, workoutId) {
  return apiRequest(`/athlete/planned-workouts/${workoutId}/report/ai/sessions`, {
    method: "POST",
    token,
  });
}

export function sendReportAgentMessage(token, sessionId, payload) {
  return apiRequest(`/athlete/report/ai/sessions/${sessionId}/messages`, {
    method: "POST",
    token,
    body: withAiProviderSettings(payload),
  });
}

export function getReportAgentSession(token, sessionId) {
  return apiRequest(`/athlete/report/ai/sessions/${sessionId}`, { token });
}

export function getActiveReportAgentSession(token, workoutId) {
  return getActiveAgentSession(
    `/athlete/planned-workouts/${workoutId}/report/ai/sessions/active`,
    token,
  );
}

export function confirmReportAgentDraft(token, sessionId, payload = {}) {
  return apiRequest(`/athlete/report/ai/sessions/${sessionId}/confirm`, {
    method: "POST",
    token,
    body: payload,
  });
}

export function fetchAthleteConversations(token) {
  return apiRequest("/athlete/conversations", { token });
}

export function fetchAthleteConversationMessages(token, conversationId, options = {}) {
  const params = new URLSearchParams();
  if (options.offset != null) {
    params.set("offset", String(options.offset));
  }
  if (options.limit != null) {
    params.set("limit", String(options.limit));
  }
  const query = params.toString();
  const suffix = query ? `?${query}` : "";
  return apiRequest(`/athlete/conversations/${conversationId}/messages${suffix}`, { token });
}

export function sendAthleteCoachMessage(token, coachId, payload) {
  return apiRequest(`/athlete/coaches/${coachId}/messages`, {
    method: "POST",
    token,
    body: payload,
  });
}

export function markAthleteConversationRead(token, conversationId) {
  return apiRequest(`/athlete/conversations/${conversationId}/read`, {
    method: "POST",
    token,
  });
}

export function fetchCoachConversations(token) {
  return apiRequest("/coach/conversations", { token });
}

export function fetchCoachConversationMessages(token, conversationId, options = {}) {
  const params = new URLSearchParams();
  if (options.offset != null) {
    params.set("offset", String(options.offset));
  }
  if (options.limit != null) {
    params.set("limit", String(options.limit));
  }
  const query = params.toString();
  const suffix = query ? `?${query}` : "";
  return apiRequest(`/coach/conversations/${conversationId}/messages${suffix}`, { token });
}

export function sendCoachAthleteMessage(token, athleteId, payload) {
  return apiRequest(`/coach/athletes/${athleteId}/messages`, {
    method: "POST",
    token,
    body: payload,
  });
}

export function markCoachConversationRead(token, conversationId) {
  return apiRequest(`/coach/conversations/${conversationId}/read`, {
    method: "POST",
    token,
  });
}
