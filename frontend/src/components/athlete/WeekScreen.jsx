import { useNavigate } from "react-router-dom";

import { useAthleteDay } from "../../pages/athlete/AthleteDayContext.jsx";
import { WeekNavigator } from "../training/WeekNavigator.jsx";
import { StatusChip } from "../ui/StatusChip.jsx";
import { EmptyState } from "../EmptyState.jsx";
import { LoadingMessage } from "../LoadingMessage.jsx";

export function WeekScreen() {
  const navigate = useNavigate();
  const {
    anchorDate,
    setAnchorDate,
    pickWeekDate,
    weekDays,
    compliancePercent,
    loading,
    error,
    getDayViewModel,
    setSelectedDayIndex,
  } = useAthleteDay();

  const hasAnyPlan = weekDays.some((day) => getDayViewModel(day.date).hasPlan);

  function handleDayClick(index) {
    setSelectedDayIndex(index);
    navigate("/athlete/today");
  }

  return (
    <div className="athlete-shell-section athlete-week-screen">
      <h2 className="athlete-screen-title">Эта неделя</h2>
      {compliancePercent != null ? (
        <p className="athlete-week-screen__compliance">Соблюдение плана: {compliancePercent}%</p>
      ) : null}

        <WeekNavigator
        anchorDate={anchorDate}
        onAnchorDateChange={setAnchorDate}
        onDayIndexChange={pickWeekDate}
        compact
      />

      {loading ? <LoadingMessage /> : null}
      {error ? <p className="form-error">{error}</p> : null}

      {!loading && !error && !hasAnyPlan ? (
        <EmptyState message="На этой неделе тренировки не назначены." />
      ) : null}

      {!loading && !error && hasAnyPlan ? (
        <div className="athlete-week-list">
          {weekDays.map((day, index) => {
            const view = getDayViewModel(day.date);
            return (
              <button
                key={day.key}
                type="button"
                className="athlete-week-list__item"
                onClick={() => handleDayClick(index)}
              >
                <div>
                  <p className="athlete-week-list__date">
                    {view.dayFull}
                    {view.type !== "Отдых" ? ` — ${view.type}` : ""}
                  </p>
                  <p className="athlete-week-list__type">{view.shortDateLabel}</p>
                </div>
                <StatusChip variant={view.status.variant} label={view.status.label} />
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
