import { useEffect, useState } from "react";

import { detectLlmModels } from "../../utils/detectLlmModels.js";
import { loadAiSettings, saveAiSettings } from "../../utils/aiSettingsStorage.js";
import { Button } from "../ui/Button.jsx";
import { Input } from "../ui/Input.jsx";
import { Label } from "../ui/Label.jsx";

export function AiSettingsScreen({ compact = false }) {
  const [apiUrl, setApiUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [customModel, setCustomModel] = useState("");
  const [detecting, setDetecting] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const settings = loadAiSettings();
    setApiUrl(settings.apiUrl);
    setApiKey(settings.apiKey);
    setModels(settings.models);
    setSelectedModel(settings.model);
    const isCustom =
      settings.model && settings.models.length > 0 && !settings.models.includes(settings.model);
    setCustomModel(isCustom ? settings.model : "");
  }, []);

  function markDirty() {
    setSaved(false);
  }

  async function handleDetectModels() {
    setDetecting(true);
    markDirty();
    const detected = await detectLlmModels(apiUrl, apiKey);
    setModels(detected);
    if (detected.length > 0 && !detected.includes(selectedModel)) {
      setSelectedModel(detected[0]);
      setCustomModel("");
    }
    setDetecting(false);
  }

  function handleSave() {
    const model = customModel.trim() || selectedModel;
    saveAiSettings({
      apiUrl: apiUrl.trim(),
      apiKey: apiKey.trim(),
      models,
      model,
    });
    setSaved(true);
  }

  const activeModel = customModel.trim() || selectedModel;

  return (
    <div className={["ai-settings-screen", compact ? "ai-settings-screen--compact" : ""].filter(Boolean).join(" ")}>
      <h2 className="athlete-screen-title">Настройки ИИ</h2>
      <p className="ai-settings-screen__subtitle">
        {compact
          ? "Подключите провайдера LLM."
          : "Подключите провайдера LLM для составления отчётов и анализа прогресса."}
      </p>

      <div className="ai-settings-screen__card">
        <Label htmlFor="ai-api-url">URL API провайдера</Label>
        <Input
          id="ai-api-url"
          value={apiUrl}
          placeholder="https://api.openai.com/v1"
          onChange={(event) => {
            setApiUrl(event.target.value);
            markDirty();
          }}
          uppercaseLabel={false}
        />

        <Button
          type="button"
          variant="outline"
          className="ai-settings-screen__detect-btn"
          loading={detecting}
          onClick={handleDetectModels}
        >
          {detecting ? "Определяем модели…" : "Определить доступные модели"}
        </Button>

        {models.length > 0 ? (
          <div className="ai-settings-screen__models">
            <p className="ai-settings-screen__section-label">Модель по умолчанию</p>
            <div className="ai-settings-screen__model-list" role="radiogroup" aria-label="Модель по умолчанию">
              {models.map((model) => {
                const isActive = !customModel.trim() && selectedModel === model;
                return (
                  <button
                    key={model}
                    type="button"
                    role="radio"
                    aria-checked={isActive}
                    className={[
                      "ai-settings-screen__model-option",
                      isActive ? "ai-settings-screen__model-option--active" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    onClick={() => {
                      setSelectedModel(model);
                      setCustomModel("");
                      markDirty();
                    }}
                  >
                    <span className="ai-settings-screen__model-radio" aria-hidden="true" />
                    <span>{model}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ) : null}

        <Label htmlFor="ai-custom-model">Или укажите модель вручную</Label>
        <Input
          id="ai-custom-model"
          value={customModel}
          placeholder="gpt-4o-mini"
          onChange={(event) => {
            setCustomModel(event.target.value);
            markDirty();
          }}
          uppercaseLabel={false}
        />

        <Label htmlFor="ai-api-key">API Key</Label>
        <Input
          id="ai-api-key"
          type="password"
          value={apiKey}
          placeholder="sk-…"
          onChange={(event) => {
            setApiKey(event.target.value);
            markDirty();
          }}
          uppercaseLabel={false}
        />

        <Button
          type="button"
          className="ai-settings-screen__save-btn"
          disabled={!apiUrl.trim() || !activeModel || !apiKey.trim()}
          onClick={handleSave}
        >
          {saved ? "✓ Сохранено" : "Сохранить настройки"}
        </Button>
      </div>
    </div>
  );
}
