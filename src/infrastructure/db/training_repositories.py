from datetime import date, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from domain.entities.planned_workout import PlannedWorkout
from domain.entities.training_plan import TrainingPlan
from domain.entities.workout_completion_report import WorkoutCompletionReport
from domain.entities.workout_cycle import WorkoutCycle
from domain.entities.workout_exercise import WorkoutExercise
from domain.value_objects.difficulty_rating import DifficultyRating
from domain.value_objects.mood_rating import MoodRating
from domain.value_objects.planned_workout_id import PlannedWorkoutId
from domain.value_objects.training_plan_id import TrainingPlanId
from domain.value_objects.user_id import UserId
from domain.value_objects.workout_completion_report_id import WorkoutCompletionReportId
from domain.value_objects.workout_cycle_id import WorkoutCycleId
from domain.value_objects.workout_exercise_id import WorkoutExerciseId
from infrastructure.db.models import (
    PlannedWorkoutRecord,
    TrainingPlanRecord,
    WorkoutCompletionReportRecord,
    WorkoutCycleRecord,
    WorkoutExerciseRecord,
)


def _to_domain_plan(record: TrainingPlanRecord) -> TrainingPlan:
    return TrainingPlan(
        id=TrainingPlanId(record.id),
        coach_id=UserId(record.coach_id),
        athlete_id=UserId(record.athlete_id),
        scope=record.scope,
        start_date=record.start_date,
        created_at=record.created_at,
        raw_text=record.raw_text,
    )


def _to_domain_workout(record: PlannedWorkoutRecord) -> PlannedWorkout:
    return PlannedWorkout(
        id=PlannedWorkoutId(record.id),
        plan_id=TrainingPlanId(record.plan_id),
        coach_id=UserId(record.coach_id),
        athlete_id=UserId(record.athlete_id),
        planned_date=record.planned_date,
        workout_type=record.workout_type,
        title=record.title,
        created_at=record.created_at,
    )


def _to_domain_cycle(record: WorkoutCycleRecord) -> WorkoutCycle:
    return WorkoutCycle(
        id=WorkoutCycleId(record.id),
        planned_workout_id=PlannedWorkoutId(record.planned_workout_id),
        name=record.name,
        sort_order=record.sort_order,
    )


def _to_domain_exercise(record: WorkoutExerciseRecord) -> WorkoutExercise:
    return WorkoutExercise(
        id=WorkoutExerciseId(record.id),
        cycle_id=WorkoutCycleId(record.cycle_id),
        name=record.name,
        details=record.details,
        sort_order=record.sort_order,
    )


def _to_domain_report(record: WorkoutCompletionReportRecord) -> WorkoutCompletionReport:
    return WorkoutCompletionReport(
        id=WorkoutCompletionReportId(record.id),
        planned_workout_id=PlannedWorkoutId(record.planned_workout_id),
        athlete_id=UserId(record.athlete_id),
        difficulty_rating=DifficultyRating(record.difficulty_rating),
        mood_rating=MoodRating(record.mood_rating),
        comment=record.comment,
        garmin_url=record.garmin_url,
        raw_report_text=record.raw_report_text,
        created_at=record.created_at,
    )


class SqlAlchemyTrainingPlanRepository:
    """SQLAlchemy implementation of TrainingPlanRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def save(self, plan: TrainingPlan) -> TrainingPlan:
        record = self._db_session.get(TrainingPlanRecord, plan.id.value)
        if record is None:
            record = TrainingPlanRecord(
                id=plan.id.value,
                coach_id=plan.coach_id.value,
                athlete_id=plan.athlete_id.value,
                scope=plan.scope,
                start_date=plan.start_date,
                created_at=plan.created_at,
                raw_text=plan.raw_text,
            )
            self._db_session.add(record)
        else:
            record.coach_id = plan.coach_id.value
            record.athlete_id = plan.athlete_id.value
            record.scope = plan.scope
            record.start_date = plan.start_date
            record.created_at = plan.created_at
            record.raw_text = plan.raw_text

        self._db_session.flush()
        return _to_domain_plan(record)

    def get_by_id(self, plan_id: TrainingPlanId) -> TrainingPlan | None:
        record = self._db_session.get(TrainingPlanRecord, plan_id.value)
        return _to_domain_plan(record) if record else None


class SqlAlchemyPlannedWorkoutRepository:
    """SQLAlchemy implementation of PlannedWorkoutRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def save(self, workout: PlannedWorkout) -> PlannedWorkout:
        record = self._db_session.get(PlannedWorkoutRecord, workout.id.value)
        if record is None:
            record = PlannedWorkoutRecord(
                id=workout.id.value,
                plan_id=workout.plan_id.value,
                coach_id=workout.coach_id.value,
                athlete_id=workout.athlete_id.value,
                planned_date=workout.planned_date,
                workout_type=workout.workout_type,
                title=workout.title,
                created_at=workout.created_at,
            )
            self._db_session.add(record)
        else:
            record.plan_id = workout.plan_id.value
            record.coach_id = workout.coach_id.value
            record.athlete_id = workout.athlete_id.value
            record.planned_date = workout.planned_date
            record.workout_type = workout.workout_type
            record.title = workout.title
            record.created_at = workout.created_at

        self._db_session.flush()
        return _to_domain_workout(record)

    def get_by_id(self, workout_id: PlannedWorkoutId) -> PlannedWorkout | None:
        record = self._db_session.get(PlannedWorkoutRecord, workout_id.value)
        return _to_domain_workout(record) if record else None

    def delete(self, workout_id: PlannedWorkoutId) -> None:
        # Use bulk delete to rely on DB-level ON DELETE CASCADE without ORM
        # trying to null-out child FKs (workout_cycles.planned_workout_id is NOT NULL).
        stmt = delete(PlannedWorkoutRecord).where(PlannedWorkoutRecord.id == workout_id.value)
        self._db_session.execute(stmt)
        self._db_session.flush()

    def list_by_plan(self, plan_id: TrainingPlanId) -> list[PlannedWorkout]:
        stmt = (
            select(PlannedWorkoutRecord)
            .where(PlannedWorkoutRecord.plan_id == plan_id.value)
            .order_by(PlannedWorkoutRecord.planned_date.asc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_workout(record) for record in records]

    def list_by_athlete_and_date_range(
        self,
        athlete_id: UserId,
        *,
        start_date: date,
        end_date: date,
    ) -> list[PlannedWorkout]:
        stmt = (
            select(PlannedWorkoutRecord)
            .where(
                PlannedWorkoutRecord.athlete_id == athlete_id.value,
                PlannedWorkoutRecord.planned_date >= start_date,
                PlannedWorkoutRecord.planned_date <= end_date,
            )
            .order_by(PlannedWorkoutRecord.planned_date.asc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_workout(record) for record in records]

    def list_by_coach_and_athlete_date_range(
        self,
        coach_id: UserId,
        athlete_id: UserId,
        *,
        start_date: date,
        end_date: date,
    ) -> list[PlannedWorkout]:
        stmt = (
            select(PlannedWorkoutRecord)
            .where(
                PlannedWorkoutRecord.coach_id == coach_id.value,
                PlannedWorkoutRecord.athlete_id == athlete_id.value,
                PlannedWorkoutRecord.planned_date >= start_date,
                PlannedWorkoutRecord.planned_date <= end_date,
            )
            .order_by(PlannedWorkoutRecord.planned_date.asc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_workout(record) for record in records]

    def get_by_athlete_and_date(
        self,
        athlete_id: UserId,
        planned_date: date,
    ) -> PlannedWorkout | None:
        stmt = select(PlannedWorkoutRecord).where(
            PlannedWorkoutRecord.athlete_id == athlete_id.value,
            PlannedWorkoutRecord.planned_date == planned_date,
        )
        record = self._db_session.scalar(stmt)
        return _to_domain_workout(record) if record else None


class SqlAlchemyWorkoutCycleRepository:
    """SQLAlchemy implementation of WorkoutCycleRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def save(self, cycle: WorkoutCycle) -> WorkoutCycle:
        record = self._db_session.get(WorkoutCycleRecord, cycle.id.value)
        if record is None:
            record = WorkoutCycleRecord(
                id=cycle.id.value,
                planned_workout_id=cycle.planned_workout_id.value,
                name=cycle.name,
                sort_order=cycle.sort_order,
            )
            self._db_session.add(record)
        else:
            record.planned_workout_id = cycle.planned_workout_id.value
            record.name = cycle.name
            record.sort_order = cycle.sort_order

        self._db_session.flush()
        return _to_domain_cycle(record)

    def get_by_id(self, cycle_id: WorkoutCycleId) -> WorkoutCycle | None:
        record = self._db_session.get(WorkoutCycleRecord, cycle_id.value)
        return _to_domain_cycle(record) if record else None

    def list_by_workout(self, workout_id: PlannedWorkoutId) -> list[WorkoutCycle]:
        stmt = (
            select(WorkoutCycleRecord)
            .where(WorkoutCycleRecord.planned_workout_id == workout_id.value)
            .order_by(WorkoutCycleRecord.sort_order.asc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_cycle(record) for record in records]

    def delete_by_workout(self, workout_id: PlannedWorkoutId) -> None:
        stmt = delete(WorkoutCycleRecord).where(
            WorkoutCycleRecord.planned_workout_id == workout_id.value
        )
        self._db_session.execute(stmt)
        self._db_session.flush()


class SqlAlchemyWorkoutExerciseRepository:
    """SQLAlchemy implementation of WorkoutExerciseRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def save(self, exercise: WorkoutExercise) -> WorkoutExercise:
        record = self._db_session.get(WorkoutExerciseRecord, exercise.id.value)
        if record is None:
            record = WorkoutExerciseRecord(
                id=exercise.id.value,
                cycle_id=exercise.cycle_id.value,
                name=exercise.name,
                details=exercise.details,
                sort_order=exercise.sort_order,
            )
            self._db_session.add(record)
        else:
            record.cycle_id = exercise.cycle_id.value
            record.name = exercise.name
            record.details = exercise.details
            record.sort_order = exercise.sort_order

        self._db_session.flush()
        return _to_domain_exercise(record)

    def get_by_id(self, exercise_id: WorkoutExerciseId) -> WorkoutExercise | None:
        record = self._db_session.get(WorkoutExerciseRecord, exercise_id.value)
        return _to_domain_exercise(record) if record else None

    def list_by_cycle(self, cycle_id: WorkoutCycleId) -> list[WorkoutExercise]:
        stmt = (
            select(WorkoutExerciseRecord)
            .where(WorkoutExerciseRecord.cycle_id == cycle_id.value)
            .order_by(WorkoutExerciseRecord.sort_order.asc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_exercise(record) for record in records]

    def delete_by_cycle(self, cycle_id: WorkoutCycleId) -> None:
        stmt = delete(WorkoutExerciseRecord).where(WorkoutExerciseRecord.cycle_id == cycle_id.value)
        self._db_session.execute(stmt)
        self._db_session.flush()


class SqlAlchemyWorkoutCompletionReportRepository:
    """SQLAlchemy implementation of WorkoutCompletionReportRepository."""

    def __init__(self, db_session: Session) -> None:
        self._db_session = db_session

    def save(self, report: WorkoutCompletionReport) -> WorkoutCompletionReport:
        record = self._db_session.get(WorkoutCompletionReportRecord, report.id.value)
        if record is None:
            record = WorkoutCompletionReportRecord(
                id=report.id.value,
                planned_workout_id=report.planned_workout_id.value,
                athlete_id=report.athlete_id.value,
                difficulty_rating=report.difficulty_rating.value,
                mood_rating=report.mood_rating.value,
                comment=report.comment,
                garmin_url=report.garmin_url,
                raw_report_text=report.raw_report_text,
                created_at=report.created_at,
            )
            self._db_session.add(record)
        else:
            record.planned_workout_id = report.planned_workout_id.value
            record.athlete_id = report.athlete_id.value
            record.difficulty_rating = report.difficulty_rating.value
            record.mood_rating = report.mood_rating.value
            record.comment = report.comment
            record.garmin_url = report.garmin_url
            record.raw_report_text = report.raw_report_text
            record.created_at = report.created_at

        self._db_session.flush()
        return _to_domain_report(record)

    def get_by_id(self, report_id: WorkoutCompletionReportId) -> WorkoutCompletionReport | None:
        record = self._db_session.get(WorkoutCompletionReportRecord, report_id.value)
        return _to_domain_report(record) if record else None

    def get_by_planned_workout(
        self,
        planned_workout_id: PlannedWorkoutId,
    ) -> WorkoutCompletionReport | None:
        stmt = select(WorkoutCompletionReportRecord).where(
            WorkoutCompletionReportRecord.planned_workout_id == planned_workout_id.value
        )
        record = self._db_session.scalar(stmt)
        return _to_domain_report(record) if record else None

    def list_by_athlete_and_date_range(
        self,
        athlete_id: UserId,
        *,
        start_at: datetime,
        end_at: datetime,
    ) -> list[WorkoutCompletionReport]:
        stmt = (
            select(WorkoutCompletionReportRecord)
            .where(
                WorkoutCompletionReportRecord.athlete_id == athlete_id.value,
                WorkoutCompletionReportRecord.created_at >= start_at,
                WorkoutCompletionReportRecord.created_at <= end_at,
            )
            .order_by(WorkoutCompletionReportRecord.created_at.desc())
        )
        records = self._db_session.scalars(stmt).all()
        return [_to_domain_report(record) for record in records]
