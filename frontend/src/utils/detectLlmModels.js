export async function detectLlmModels(apiUrl, apiKey) {
  const normalizedUrl = (apiUrl || "").trim().replace(/\/$/, "");
  const normalizedKey = (apiKey || "").trim();

  if (!normalizedUrl || !normalizedKey) {
    return [];
  }

  try {
    const response = await fetch(`${normalizedUrl}/models`, {
      headers: {
        Authorization: `Bearer ${normalizedKey}`,
      },
    });
    if (!response.ok) {
      return [];
    }
    const payload = await response.json();
    const models = payload.data ?? payload.models ?? [];
    return models
      .map((item) => (typeof item === "string" ? item : item.id))
      .filter(Boolean);
  } catch {
    return [];
  }
}
