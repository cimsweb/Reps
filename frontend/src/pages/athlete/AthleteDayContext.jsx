import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { useAthleteWeekData } from "../../hooks/useAthleteWeekData.js";
import { findWeekDayIndex, isSameWeek } from "../../utils/weekStrip.js";

const AthleteDayContext = createContext(null);

export function AthleteDayProvider({ children }) {
  const {
    anchorDate,
    setAnchorDate,
    pickWeekDate,
    workouts,
    reports,
    weekDays,
    compliancePercent,
    loading,
    error,
    reload,
    getDayViewModel,
  } = useAthleteWeekData();
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

  const selectedDate = useMemo(
    () => weekDays[selectedDayIndex]?.date ?? new Date(),
    [selectedDayIndex, weekDays],
  );
  const activeDay = useMemo(
    () => getDayViewModel(selectedDate),
    [getDayViewModel, selectedDate],
  );

  const handlePickWeekDate = useCallback(
    (dateString) => {
      const dayIndex = pickWeekDate(dateString);
      if (dayIndex != null && dayIndex >= 0) {
        setSelectedDayIndex(dayIndex);
      }
    },
    [pickWeekDate],
  );

  const value = useMemo(
    () => ({
      anchorDate,
      setAnchorDate,
      pickWeekDate: handlePickWeekDate,
      workouts,
      reports,
      weekDays,
      compliancePercent,
      loading,
      error,
      reload,
      getDayViewModel,
      selectedDayIndex,
      setSelectedDayIndex,
      selectedDate,
      activeDay,
    }),
    [
      activeDay,
      anchorDate,
      compliancePercent,
      error,
      getDayViewModel,
      handlePickWeekDate,
      loading,
      reload,
      reports,
      selectedDate,
      selectedDayIndex,
      setAnchorDate,
      weekDays,
      workouts,
    ],
  );

  return <AthleteDayContext.Provider value={value}>{children}</AthleteDayContext.Provider>;
}

export function useAthleteDay() {
  const context = useContext(AthleteDayContext);
  if (!context) {
    throw new Error("useAthleteDay must be used within AthleteDayProvider");
  }
  return context;
}
