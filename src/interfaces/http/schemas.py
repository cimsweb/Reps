from datetime import date, datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = Field(pattern="^(coach|athlete)$")


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime


class LoginResponse(BaseModel):
    token: str
    expires_at: datetime
    user: UserResponse


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int


class SendInvitationRequest(BaseModel):
    email: str


class InvitationResponse(BaseModel):
    id: str
    coach_id: str
    athlete_email: str
    status: str
    created_at: datetime
    responded_at: datetime | None = None


class InvitationListResponse(BaseModel):
    items: list[InvitationResponse]


class CoachAthleteResponse(BaseModel):
    id: str
    coach_id: str
    athlete_id: str
    created_at: datetime


class CoachAthleteListResponse(BaseModel):
    items: list[CoachAthleteResponse]


class AthleteProfileResponse(BaseModel):
    athlete_id: str
    height_cm: int
    weight_kg: int
    age: int
    gender: str
    updated_at: datetime


class SaveAthleteProfileRequest(BaseModel):
    height_cm: int
    weight_kg: int
    age: int
    gender: str


class CreatePersonalRecordRequest(BaseModel):
    record_type: str
    name: str
    value: str
    unit: str
    achieved_at: datetime


class UpdatePersonalRecordRequest(BaseModel):
    record_type: str
    name: str
    value: str
    unit: str
    achieved_at: datetime


class PersonalRecordResponse(BaseModel):
    id: str
    athlete_id: str
    record_type: str
    name: str
    value: str
    unit: str
    achieved_at: datetime
    created_at: datetime


class PersonalRecordListResponse(BaseModel):
    items: list[PersonalRecordResponse]
    total: int


class SubmitWorkoutFeedbackRequest(BaseModel):
    text: str


class WorkoutFeedbackResponse(BaseModel):
    id: str
    athlete_id: str
    text: str
    created_at: datetime


class WorkoutFeedbackListResponse(BaseModel):
    items: list[WorkoutFeedbackResponse]
    total: int


class WorkoutExerciseRequest(BaseModel):
    name: str
    details: str
    sort_order: int


class WorkoutCycleRequest(BaseModel):
    name: str
    sort_order: int
    exercises: list[WorkoutExerciseRequest]


class PlannedWorkoutRequest(BaseModel):
    planned_date: date
    workout_type: str
    title: str | None = None
    cycles: list[WorkoutCycleRequest]


class CreateTrainingPlanRequest(BaseModel):
    start_date: date
    workouts: list[PlannedWorkoutRequest]


class WorkoutExerciseResponse(BaseModel):
    id: str
    name: str
    details: str
    sort_order: int


class WorkoutCycleResponse(BaseModel):
    id: str
    name: str
    sort_order: int
    exercises: list[WorkoutExerciseResponse]


class PlannedWorkoutResponse(BaseModel):
    id: str
    plan_id: str
    coach_id: str
    athlete_id: str
    planned_date: date
    workout_type: str
    title: str | None = None
    created_at: datetime
    cycles: list[WorkoutCycleResponse] = []


class TrainingPlanResponse(BaseModel):
    id: str
    coach_id: str
    athlete_id: str
    scope: str
    start_date: date
    created_at: datetime
    raw_text: str | None = None
    workouts: list[PlannedWorkoutResponse] = []


class TrainingCalendarResponse(BaseModel):
    anchor_date: date
    period: str
    workouts: list[PlannedWorkoutResponse]


class TrainingPlanTextResponse(BaseModel):
    anchor_date: date
    period: str
    text: str


class WorkoutCompletionReportResponse(BaseModel):
    id: str
    planned_workout_id: str
    athlete_id: str
    difficulty_rating: int
    mood_rating: int
    comment: str | None = None
    garmin_url: str | None = None
    raw_report_text: str | None = None
    created_at: datetime


class WorkoutReportSummaryResponse(BaseModel):
    anchor_date: date
    period: str
    reports: list[WorkoutCompletionReportResponse]


class SubmitWorkoutReportRequest(BaseModel):
    difficulty_rating: int
    mood_rating: int
    comment: str | None = None
    garmin_url: str | None = None
    raw_report_text: str | None = None


class ParseTrainingPlanTextRequest(BaseModel):
    scope: str = Field(pattern="^(day|week)$")
    start_date: date
    text: str
    title: str | None = None
    titles: dict[str, str] | None = None


class UpdateTrainingPlanRawTextRequest(BaseModel):
    raw_text: str | None = None
    titles: dict[str, str] | None = None
    scope: str | None = Field(default=None, pattern="^(day|week)$")
    start_date: date | None = None


class ParsedWorkoutExerciseDraftResponse(BaseModel):
    name: str
    details: str
    sort_order: int


class ParsedWorkoutCycleDraftResponse(BaseModel):
    name: str
    sort_order: int
    exercises: list[ParsedWorkoutExerciseDraftResponse]


class ParsedPlannedWorkoutDraftResponse(BaseModel):
    planned_date: date
    workout_type: str
    title: str | None = None
    cycles: list[ParsedWorkoutCycleDraftResponse]


class ParseTrainingPlanTextResponse(BaseModel):
    detected_scope: str
    warnings: list[str] = []
    workouts: list[ParsedPlannedWorkoutDraftResponse] = []


class UpdateTrainingPlanRawTextResponse(BaseModel):
    plan: TrainingPlanResponse
    replaced_workouts_count: int


class StartPlanAgentSessionRequest(BaseModel):
    start_date: date
    initial_brief: str | None = None
    api_url: str | None = None
    api_key: str | None = None
    model: str | None = None


class SendAgentMessageRequest(BaseModel):
    content: str
    api_url: str | None = None
    api_key: str | None = None
    model: str | None = None


class AgentMessageResponse(BaseModel):
    role: str
    content: str
    sort_order: int


class AgentQuestionReplyResponse(BaseModel):
    type: str = "question"
    text: str


class TrainingPlanDraftResponse(BaseModel):
    start_date: date
    scope: str
    raw_text: str | None = None
    warnings: list[str] = []
    workouts: list[ParsedPlannedWorkoutDraftResponse] = []


class AgentPlanDraftReplyResponse(BaseModel):
    type: str = "plan_draft"
    draft: TrainingPlanDraftResponse


class AgentReportDraftReplyResponse(BaseModel):
    type: str = "report_draft"
    suggested_difficulty_rating: int | None = None
    suggested_mood_rating: int | None = None
    comment_body: str | None = None
    garmin_url: str | None = None
    warnings: list[str] = []


class AgentSessionResponse(BaseModel):
    session_id: str
    kind: str
    status: str
    messages: list[AgentMessageResponse] = []
    messages_remaining: int
    can_confirm: bool
    latest_reply: (
        AgentQuestionReplyResponse
        | AgentPlanDraftReplyResponse
        | AgentReportDraftReplyResponse
        | None
    ) = None


class ConfirmPlanAgentDraftRequest(BaseModel):
    start_date: date | None = None
    scope: str | None = Field(default=None, pattern="^(day|week)$")
    raw_text: str | None = None


class ConfirmReportAgentDraftRequest(BaseModel):
    difficulty_rating: int | None = None
    mood_rating: int | None = None
    comment: str | None = None
    garmin_url: str | None = None
    raw_report_text: str | None = None


class SendConversationMessageRequest(BaseModel):
    content: str
    kind: str = Field(default="text", pattern="^(text|question)$")


class ConversationMessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    kind: str
    content: str
    sort_order: int
    read_at: datetime | None = None
    created_at: datetime
    is_mine: bool


class ConversationSummaryResponse(BaseModel):
    id: str
    coach_id: str
    athlete_id: str
    partner_id: str
    partner_email: str
    unread_count: int
    last_message_content: str | None = None
    last_message_at: datetime | None = None
    updated_at: datetime


class ConversationListResponse(BaseModel):
    items: list[ConversationSummaryResponse]


class ConversationMessageListResponse(BaseModel):
    items: list[ConversationMessageResponse]
    total: int
    offset: int
    limit: int


class MarkConversationReadResponse(BaseModel):
    marked_count: int
