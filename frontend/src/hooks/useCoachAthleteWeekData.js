import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchCoachAthleteTrainingPlan,
  fetchCoachAthleteWorkoutReports,
  fetchLinkedAthleteProfile,
} from "../api/client.js";
import { getToken } from "../auth/tokenStorage.js";
import {
  buildDayViewModel,
  buildReportIndex,
  calculateWeekCompliance,
  resolveWorkoutForDate,
} from "../utils/athleteWorkoutDay.js";
import { getErrorMessage } from "../utils/apiErrors.js";
import { toDateInputValue } from "../utils/formatters.js";
import { buildWeekStripDays, findWeekDayIndex } from "../utils/weekStrip.js";

export function useCoachAthleteWeekData(athleteId) {
  const [anchorDate, setAnchorDate] = useState(() => toDateInputValue());
  const [workouts, setWorkouts] = useState([]);
  const [reports, setReports] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = useCallback(async () => {
    if (!athleteId) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const token = getToken();
      const [planResult, reportsResult, profileResult] = await Promise.all([
        fetchCoachAthleteTrainingPlan(token, athleteId, { period: "week", anchorDate }),
        fetchCoachAthleteWorkoutReports(token, athleteId, { period: "month", anchorDate }),
        fetchLinkedAthleteProfile(token, athleteId),
      ]);
      setWorkouts(planResult.workouts);
      setReports(reportsResult.reports);
      setProfile(profileResult);
    } catch (loadError) {
      setWorkouts([]);
      setReports([]);
      setProfile(null);
      setError(getErrorMessage(loadError, "Не удалось загрузить данные спортсмена"));
    } finally {
      setLoading(false);
    }
  }, [anchorDate, athleteId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

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
      const view = buildDayViewModel(workout, report, day.date, today);
      return {
        ...day,
        status: view.status.stripStatus,
        type: view.type,
        statusLabel: view.status.label,
        statusVariant: view.status.variant,
      };
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
    pickWeekDate,
    workouts,
    reports,
    profile,
    weekDays,
    compliancePercent,
    loading,
    error,
    reload: loadData,
    getDayViewModel,
  };
}
