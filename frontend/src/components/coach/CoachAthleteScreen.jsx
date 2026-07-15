import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { CoachAddWorkoutModal } from "./CoachAddWorkoutModal.jsx";

import { useCoachAthleteWeekData } from "../../hooks/useCoachAthleteWeekData.js";
import { Avatar } from "../ui/Avatar.jsx";
import { Button } from "../ui/Button.jsx";
import { formatGender, toDateInputValue } from "../../utils/formatters.js";
import { findWeekDayIndex, isSameWeek } from "../../utils/weekStrip.js";
import { CoachDayDetailCard } from "./CoachDayDetailCard.jsx";
import { CoachWeekGrid } from "./CoachWeekGrid.jsx";
import { WeekNavigator } from "../training/WeekNavigator.jsx";

function buildAthleteTitle(athleteId) {
  return `Спортсмен ${athleteId.slice(0, 8)}`;
}

function buildAthleteLevel(profile) {
  if (!profile) {
    return "Уровень не указан";
  }
  return `${profile.age} лет · ${formatGender(profile.gender)}`;
}

function CoachAthleteSkeleton() {
  return (
    <div className="coach-athlete-skeleton" aria-hidden="true">
      <div className="coach-athlete-skeleton__header" />
      <div className="coach-athlete-skeleton__grid" />
      <div className="coach-athlete-skeleton__detail" />
    </div>
  );
}

export function CoachAthleteScreen() {
  const { athleteId } = useParams();
  const [addWorkoutOpen, setAddWorkoutOpen] = useState(false);
  const [addWorkoutMode, setAddWorkoutMode] = useState("day");
  const {
    anchorDate,
    setAnchorDate,
    pickWeekDate,
    weekDays,
    profile,
    compliancePercent,
    loading,
    error,
    getDayViewModel,
    reload,
  } = useCoachAthleteWeekData(athleteId);
  const [selectedDayIndex, setSelectedDayIndex] = useState(0);

  useEffect(() => {
    if (weekDays.length === 0) {
      return;
    }
    const anchorAsDate = new Date(`${anchorDate}T00:00:00`);
    const anchorIndex = findWeekDayIndex(weekDays, anchorAsDate);
    if (anchorIndex >= 0) {
      setSelectedDayIndex(anchorIndex);
      return;
    }
    const todayIndex = findWeekDayIndex(weekDays, new Date());
    if (todayIndex >= 0 && isSameWeek(weekDays[0]?.date, new Date())) {
      setSelectedDayIndex(todayIndex);
      return;
    }
    setSelectedDayIndex(0);
  }, [anchorDate, weekDays]);

  function handlePickWeekDate(dateString) {
    const dayIndex = pickWeekDate(dateString);
    if (dayIndex != null && dayIndex >= 0) {
      setSelectedDayIndex(dayIndex);
    }
  }

  const selectedDate = useMemo(
    () => weekDays[selectedDayIndex]?.date ?? new Date(),
    [selectedDayIndex, weekDays],
  );
  const activeDay = useMemo(
    () => getDayViewModel(selectedDate),
    [getDayViewModel, selectedDate],
  );

  const athleteName = buildAthleteTitle(athleteId);
  const complianceLabel =
    compliancePercent != null ? `Соблюдение плана ${compliancePercent}%` : "Соблюдение плана —";

  return (
    <div className="coach-athlete-screen">
      <Link to="/coach" className="coach-athlete-screen__back">
        ← Все спортсмены
      </Link>

      {loading ? <CoachAthleteSkeleton /> : null}
      {error ? <p className="form-error">{error}</p> : null}

      {!loading && !error ? (
        <>
          <header className="coach-athlete-screen__header">
            <div className="coach-athlete-screen__identity">
              <Avatar initials={athleteId.slice(0, 2).toUpperCase()} size="lg" />
              <div>
                <h1 className="coach-athlete-screen__name">{athleteName}</h1>
                <p className="coach-athlete-screen__meta">
                  {buildAthleteLevel(profile)} · {complianceLabel}
                </p>
              </div>
            </div>
            <div className="coach-athlete-screen__actions">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setAddWorkoutMode("day");
                  setAddWorkoutOpen(true);
                }}
              >
                + Тренировка
              </Button>
              <Button
                type="button"
                onClick={() => {
                  setAddWorkoutMode("week");
                  setAddWorkoutOpen(true);
                }}
              >
                <span className="coach-athlete-screen__week-btn-full">+ Неделя целиком</span>
                <span className="coach-athlete-screen__week-btn-short">+ Неделя</span>
              </Button>
            </div>
          </header>

          <WeekNavigator
            anchorDate={anchorDate}
            onAnchorDateChange={setAnchorDate}
            onDayIndexChange={handlePickWeekDate}
          />

          <CoachWeekGrid
            days={weekDays}
            selectedIndex={selectedDayIndex}
            onSelectDay={setSelectedDayIndex}
          />

          <CoachDayDetailCard day={activeDay} />

          <CoachAddWorkoutModal
            open={addWorkoutOpen}
            athleteId={athleteId}
            anchorDate={anchorDate}
            initialDate={toDateInputValue(selectedDate)}
            initialMode={addWorkoutMode}
            onClose={() => setAddWorkoutOpen(false)}
            onSaved={reload}
          />
        </>
      ) : null}
    </div>
  );
}
