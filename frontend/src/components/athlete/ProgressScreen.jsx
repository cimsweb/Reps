import { PersonalRecordsSection } from "./PersonalRecordsSection.jsx";

export function ProgressScreen() {
  return (
    <div className="athlete-shell-section athlete-progress-screen">
      <h2 className="athlete-screen-title">Прогресс</h2>
      <PersonalRecordsSection />
    </div>
  );
}
