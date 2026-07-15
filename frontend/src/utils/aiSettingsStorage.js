const AI_SETTINGS_STORAGE_KEY = "reps_ai_settings";

const EMPTY_SETTINGS = {
  apiUrl: "",
  apiKey: "",
  models: [],
  model: "",
};

export function loadAiSettings() {
  if (typeof window === "undefined") {
    return { ...EMPTY_SETTINGS };
  }

  try {
    const raw = window.localStorage.getItem(AI_SETTINGS_STORAGE_KEY);
    if (!raw) {
      return { ...EMPTY_SETTINGS };
    }
    const parsed = JSON.parse(raw);
    return {
      apiUrl: parsed.apiUrl ?? "",
      apiKey: parsed.apiKey ?? "",
      models: Array.isArray(parsed.models) ? parsed.models : [],
      model: parsed.model ?? "",
    };
  } catch {
    return { ...EMPTY_SETTINGS };
  }
}

export function saveAiSettings(settings) {
  window.localStorage.setItem(AI_SETTINGS_STORAGE_KEY, JSON.stringify(settings));
}
