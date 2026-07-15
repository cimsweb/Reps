import { useEffect, useState } from "react";

import {
  fetchAthleteCoaches,
  sendAthleteCoachMessage,
  submitWorkoutReport,
} from "../../api/client.js";
import { getToken } from "../../auth/tokenStorage.js";
import { useAuth } from "../../auth/AuthContext.jsx";
import { useAthleteDay } from "../../pages/athlete/AthleteDayContext.jsx";
import { buildAthleteDisplayName } from "../../utils/athleteDisplayName.js";
import { getErrorMessage } from "../../utils/apiErrors.js";
import { WorkoutReportForm } from "../training/WorkoutReportForm.jsx";
import { WorkoutTextView } from "../training/WorkoutTextView.jsx";
import { InvitationsBanner } from "./InvitationsBanner.jsx";
import { SubmittedWorkoutReport } from "./SubmittedWorkoutReport.jsx";
import { WeekStrip } from "./WeekStrip.jsx";
import { LoadingMessage } from "../LoadingMessage.jsx";

const HOME_STYLE_KEY = "reps_athlete_home_style";

function readHomeStyle() {
  if (typeof window === "undefined") {
    return "full";
  }
  return window.localStorage.getItem(HOME_STYLE_KEY) === "tabs" ? "tabs" : "full";
}

export function TodayScreen() {
  const { user } = useAuth();
  const displayName = buildAthleteDisplayName(user);
  const {
    weekDays,
    selectedDayIndex,
    setSelectedDayIndex,
    activeDay,
    loading,
    error,
    reload,
  } = useAthleteDay();
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [coachId, setCoachId] = useState("");
  const [homeStyle, setHomeStyle] = useState(readHomeStyle);
  const [subView, setSubView] = useState("task");

  useEffect(() => {
    async function loadCoach() {
      try {
        const token = getToken();
        const result = await fetchAthleteCoaches(token);
        setCoachId(result.items[0]?.coach_id ?? "");
      } catch {
        setCoachId("");
      }
    }
    loadCoach();
  }, []);

  function toggleHomeStyle() {
    const next = homeStyle === "full" ? "tabs" : "full";
    setHomeStyle(next);
    window.localStorage.setItem(HOME_STYLE_KEY, next);
    setSubView("task");
  }

  async function handleReportSubmit(payload) {
    if (!activeDay.workout) {
      return;
    }
    const { coach_question: coachQuestion, ...reportPayload } = payload;
    const rpe = Number(reportPayload.difficulty_rating);
    setSubmitting(true);
    setSubmitError("");
    try {
      const token = getToken();
      await submitWorkoutReport(token, activeDay.workout.id, {
        ...reportPayload,
        mood_rating: rpe,
      });
      if (coachQuestion && coachId) {
        await sendAthleteCoachMessage(token, coachId, {
          content: coachQuestion,
          kind: "question",
        });
      }
      await reload();
    } catch (submitErr) {
      setSubmitError(getErrorMessage(submitErr, "Не удалось отправить отчёт"));
    } finally {
      setSubmitting(false);
    }
  }

  const planCard = (
    <WorkoutTextView
      dayFull={activeDay.dayFull}
      title={activeDay.type !== "Отдых" ? activeDay.type : ""}
      dateLabel={activeDay.shortDateLabel}
      status={activeDay.status}
      workout={activeDay.workout}
      emptyLabel={activeDay.emptyLabel}
    />
  );

  const reportSection = (
    <>
      <SubmittedWorkoutReport day={activeDay} />
      {activeDay.canReport ? (
        <div className="today-report-panel">
          <WorkoutReportForm
            workout={activeDay.workout}
            submitting={submitting}
            error={submitError}
            onSubmit={handleReportSubmit}
          />
        </div>
      ) : null}
    </>
  );

  return (
    <div className="athlete-shell-section athlete-today-screen">
      <InvitationsBanner />

      <div className="athlete-today-screen__header">
        <div>
          <p className="athlete-today-date">{activeDay.dateLabel}</p>
          <h1 className="athlete-today-screen__greeting">Привет, {displayName} 👋</h1>
        </div>
        <button type="button" className="athlete-today-style-toggle" onClick={toggleHomeStyle}>
          Вид:
          <br />
          {homeStyle === "full" ? "Лента" : "Вкладки"}
        </button>
      </div>

      <WeekStrip
        days={weekDays}
        selectedIndex={selectedDayIndex}
        onSelectDay={(index) => {
          setSelectedDayIndex(index);
          setSubView("task");
        }}
      />

      {loading ? <LoadingMessage /> : null}
      {error ? <p className="form-error">{error}</p> : null}

      {!loading ? (
        <>
          {homeStyle === "full" ? (
            <div className="athlete-today-screen__full-layout">
              <div className="athlete-today-screen__plan">{planCard}</div>
              <div className="athlete-today-screen__report">{reportSection}</div>
            </div>
          ) : (
            <>
              <div className="athlete-today-subtabs" role="tablist" aria-label="Задание и отчёт">
                <button
                  type="button"
                  role="tab"
                  aria-selected={subView === "task"}
                  className={subView === "task" ? "athlete-today-subtabs__item athlete-today-subtabs__item--active" : "athlete-today-subtabs__item"}
                  onClick={() => setSubView("task")}
                >
                  Задание
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={subView === "report"}
                  className={subView === "report" ? "athlete-today-subtabs__item athlete-today-subtabs__item--active" : "athlete-today-subtabs__item"}
                  onClick={() => setSubView("report")}
                >
                  Отчёт
                </button>
              </div>
              {subView === "task" ? planCard : reportSection}
            </>
          )}
        </>
      ) : null}
    </div>
  );
}
