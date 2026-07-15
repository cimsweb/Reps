import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchAthleteTrainingPlan, fetchAthleteWorkoutReports } from "../api/client.js";
import { getToken } from "../auth/tokenStorage.js";
import {
  buildDayViewModel,
  buildReportIndex,
  calculateWeekCompliance,
  resolveWorkoutForDate,
} from "../utils/athleteWorkoutDay.js";
import { getErrorMessage } from "../utils/apiErrors.js";
import { addDaysToDateString, toDateInputValue } from "../utils/formatters.js";
import { buildWeekStripDays, findWeekDayIndex } from "../utils/weekStrip.js";

export function useAthleteWeekData() {
  const [anchorDate, setAnchorDate] = useState(() => toDateInputValue());
  const [workouts, setWorkouts] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadWeekData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const token = getToken();
      const [planResult, reportsResult] = await Promise.all([
        fetchAthleteTrainingPlan(token, { period: "week", anchorDate }),
        fetchAthleteWorkoutReports(token, { period: "month", anchorDate }),
      ]);
      setWorkouts(planResult.workouts);
      setReports(reportsResult.reports);
    } catch (loadError) {
      setWorkouts([]);
      setReports([]);
      setError(getErrorMessage(loadError, "Не удалось загрузить план на неделю"));
    } finally {
      setLoading(false);
    }
  }, [anchorDate]);

  useEffect(() => {
    loadWeekData();
  }, [loadWeekData]);

  const reportIndex = useMemo(() => buildReportIndex(reports), [reports]);
  const today = useMemo(() => new Date(), []);
  const anchorDateObject = useMemo(
    () => new Date(`${anchorDate}T00:00:00`),
    [anchorDate],
  );

  const weekDays = useMemo(() => {
    const baseDays = buildWeekStripDays(anchorDateObject);
    return baseDays.map((day) => {
      const workout = resolveWorkoutForDate(workouts, day.date);
      const report = workout ? reportIndex.get(workout.id) : null;
      const { stripStatus } = buildDayViewModel(workout, report, day.date, today).status;
      return { ...day, status: stripStatus };
    });
  }, [anchorDateObject, reportIndex, today, workouts]);

  const compliancePercent = useMemo(
    () => calculateWeekCompliance(workouts, reports, today, anchorDateObject),
    [anchorDateObject, reports, today, workouts],
  );

  const getDayViewModel = useCallback(
    (date) => {
      const workout = resolveWorkoutForDate(workouts, date);
      const report = workout ? reportIndex.get(workout.id) : null;
      return buildDayViewModel(workout, report, date, today);
    },
    [reportIndex, today, workouts],
  );

  const shiftWeek = useCallback((direction) => {
    setAnchorDate((current) => addDaysToDateString(current, direction * 7));
  }, []);

  const pickWeekDate = useCallback((dateString) => {
    if (!dateString) {
      return null;
    }
    setAnchorDate(dateString);
    const pickedDate = new Date(`${dateString}T00:00:00`);
    const nextDays = buildWeekStripDays(pickedDate);
    return findWeekDayIndex(nextDays, pickedDate);
  }, []);

  return {
    anchorDate,
    setAnchorDate,
    shiftWeek,
    pickWeekDate,
    workouts,
    reports,
    weekDays,
    compliancePercent,
    loading,
    error,
    reload: loadWeekData,
    getDayViewModel,
  };
}
