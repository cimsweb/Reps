from datetime import datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str


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


class ErrorResponse(BaseModel):
    error: str
    message: str


class PaginationQuery(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class SendInvitationRequest(BaseModel):
    email: str


class InvitationResponse(BaseModel):
    id: str
    coach_id: str
    athlete_email: str
    status: str
    created_at: datetime
    responded_at: datetime | None


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


class WorkoutFeedbackResponse(BaseModel):
    id: str
    athlete_id: str
    text: str
    garmin_url: str | None
    created_at: datetime


class WorkoutFeedbackListResponse(BaseModel):
    items: list[WorkoutFeedbackResponse]
    total: int


class SubmitWorkoutFeedbackRequest(BaseModel):
    text: str
    garmin_url: str | None = None
