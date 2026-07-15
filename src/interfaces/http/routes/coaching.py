from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from application.dto.coaching import (
    AthleteProfileView,
    CoachAthleteView,
    InvitationView,
    PaginatedPersonalRecords,
    PaginatedWorkoutFeedback,
    PersonalRecordView,
    WorkoutFeedbackView,
)
from application.use_cases.accept_invitation import AcceptInvitationUseCase
from application.use_cases.decline_invitation import DeclineInvitationUseCase
from application.use_cases.list_coaching_data import (
    GetAthleteProfileUseCase,
    ListAthleteCoachesUseCase,
    ListCoachAthletesUseCase,
    ListCoachInvitationsUseCase,
    ListPendingInvitationsUseCase,
    ListPersonalRecordsUseCase,
    ListWorkoutFeedbackUseCase,
)
from application.use_cases.personal_record_commands import (
    CreatePersonalRecordUseCase,
    DeletePersonalRecordUseCase,
    UpdatePersonalRecordUseCase,
)
from application.use_cases.save_athlete_profile import SaveAthleteProfileUseCase
from application.use_cases.send_invitation import SendInvitationUseCase
from application.use_cases.submit_workout_feedback import SubmitWorkoutFeedbackUseCase
from domain.entities.athlete_profile import AthleteProfile
from domain.entities.coach_athlete_link import CoachAthleteLink
from domain.entities.invitation import Invitation
from domain.entities.personal_record import PersonalRecord
from domain.entities.workout_feedback import WorkoutFeedback
from domain.services.authorization import Permission
from domain.value_objects.pagination import PageRequest
from domain.value_objects.user_id import UserId
from infrastructure.db.coaching_repositories import (
    SqlAlchemyAthleteProfileRepository,
    SqlAlchemyCoachAthleteLinkRepository,
    SqlAlchemyInvitationRepository,
    SqlAlchemyPersonalRecordRepository,
    SqlAlchemyWorkoutFeedbackRepository,
)
from infrastructure.db.repositories import SqlAlchemyUserRepository
from interfaces.http.dependencies import (
    AuthorizationGuardDep,
    CoachingAccessGuardDep,
    DbSession,
    get_bearer_token,
)
from interfaces.http.schemas import (
    AthleteProfileResponse,
    CoachAthleteListResponse,
    CoachAthleteResponse,
    CreatePersonalRecordRequest,
    InvitationListResponse,
    InvitationResponse,
    PersonalRecordListResponse,
    PersonalRecordResponse,
    SaveAthleteProfileRequest,
    SendInvitationRequest,
    SubmitWorkoutFeedbackRequest,
    UpdatePersonalRecordRequest,
    WorkoutFeedbackListResponse,
    WorkoutFeedbackResponse,
)

router = APIRouter(tags=["coaching"])


def _invitation_to_response(view: InvitationView) -> InvitationResponse:
    return InvitationResponse(
        id=view.id,
        coach_id=view.coach_id,
        athlete_email=view.athlete_email,
        status=view.status,
        created_at=view.created_at,
        responded_at=view.responded_at,
    )


def _invitation_entity_to_response(invitation: Invitation) -> InvitationResponse:
    return InvitationResponse(
        id=str(invitation.id.value),
        coach_id=str(invitation.coach_id.value),
        athlete_email=str(invitation.athlete_email),
        status=invitation.status.value,
        created_at=invitation.created_at,
        responded_at=invitation.responded_at,
    )


def _coach_athlete_to_response(view: CoachAthleteView) -> CoachAthleteResponse:
    return CoachAthleteResponse(
        id=view.id,
        coach_id=view.coach_id,
        athlete_id=view.athlete_id,
        created_at=view.created_at,
    )


def _link_entity_to_response(link: CoachAthleteLink) -> CoachAthleteResponse:
    return CoachAthleteResponse(
        id=str(link.id.value),
        coach_id=str(link.coach_id.value),
        athlete_id=str(link.athlete_id.value),
        created_at=link.created_at,
    )


def _profile_to_response(view: AthleteProfileView) -> AthleteProfileResponse:
    return AthleteProfileResponse(
        athlete_id=view.athlete_id,
        height_cm=view.height_cm,
        weight_kg=view.weight_kg,
        age=view.age,
        gender=view.gender,
        updated_at=view.updated_at,
    )


def _profile_entity_to_response(profile: AthleteProfile) -> AthleteProfileResponse:
    return AthleteProfileResponse(
        athlete_id=str(profile.athlete_id.value),
        height_cm=profile.height_cm.value,
        weight_kg=profile.weight_kg.value,
        age=profile.age.value,
        gender=profile.gender.value,
        updated_at=profile.updated_at,
    )


def _record_to_response(view: PersonalRecordView) -> PersonalRecordResponse:
    return PersonalRecordResponse(
        id=view.id,
        athlete_id=view.athlete_id,
        record_type=view.record_type,
        name=view.name,
        value=view.value,
        unit=view.unit,
        achieved_at=view.achieved_at,
        created_at=view.created_at,
    )


def _record_entity_to_response(record: PersonalRecord) -> PersonalRecordResponse:
    return PersonalRecordResponse(
        id=str(record.id.value),
        athlete_id=str(record.athlete_id.value),
        record_type=record.record_type.value,
        name=record.name,
        value=str(record.value),
        unit=str(record.unit),
        achieved_at=record.achieved_at,
        created_at=record.created_at,
    )


def _feedback_to_response(view: WorkoutFeedbackView) -> WorkoutFeedbackResponse:
    return WorkoutFeedbackResponse(
        id=view.id,
        athlete_id=view.athlete_id,
        text=view.text,
        created_at=view.created_at,
    )


def _feedback_entity_to_response(feedback: WorkoutFeedback) -> WorkoutFeedbackResponse:
    return WorkoutFeedbackResponse(
        id=str(feedback.id.value),
        athlete_id=str(feedback.athlete_id.value),
        text=feedback.text,
        created_at=feedback.created_at,
    )


def _records_to_response(result: PaginatedPersonalRecords) -> PersonalRecordListResponse:
    return PersonalRecordListResponse(
        items=[_record_to_response(item) for item in result.items],
        total=result.total,
    )


def _feedback_list_to_response(result: PaginatedWorkoutFeedback) -> WorkoutFeedbackListResponse:
    return WorkoutFeedbackListResponse(
        items=[_feedback_to_response(item) for item in result.items],
        total=result.total,
    )


def _parse_athlete_id(athlete_id: str) -> UserId:
    return UserId(UUID(athlete_id))


@router.post("/coach/invitations", response_model=InvitationResponse, status_code=201)
def send_invitation(
    body: SendInvitationRequest,
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> InvitationResponse:
    """Send an invitation to an athlete email."""
    authenticated_user = guard.authorize(token, Permission.VIEW_OWN_ACCOUNT)
    invitation_repository = SqlAlchemyInvitationRepository(db)
    link_repository = SqlAlchemyCoachAthleteLinkRepository(db)
    user_repository = SqlAlchemyUserRepository(db)
    invitation = SendInvitationUseCase(
        invitation_repository,
        link_repository,
        user_repository,
    ).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        body.email,
    )
    return _invitation_entity_to_response(invitation)


@router.get("/coach/invitations", response_model=InvitationListResponse)
def list_coach_invitations(
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> InvitationListResponse:
    """List invitations created by the authenticated coach."""
    authenticated_user = guard.authorize(token, Permission.VIEW_OWN_ACCOUNT)
    items = ListCoachInvitationsUseCase(SqlAlchemyInvitationRepository(db)).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
    )
    return InvitationListResponse(items=[_invitation_to_response(item) for item in items])


@router.get("/athlete/invitations", response_model=InvitationListResponse)
def list_pending_invitations(
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> InvitationListResponse:
    """List pending invitations for the authenticated athlete."""
    authenticated_user = guard.authorize(token, Permission.VIEW_OWN_ACCOUNT)
    items = ListPendingInvitationsUseCase(SqlAlchemyInvitationRepository(db)).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        str(authenticated_user.user.email),
    )
    return InvitationListResponse(items=[_invitation_to_response(item) for item in items])


@router.post("/athlete/invitations/{invitation_id}/accept", response_model=CoachAthleteResponse)
def accept_invitation(
    invitation_id: str,
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> CoachAthleteResponse:
    """Accept a pending invitation."""
    authenticated_user = guard.authorize(token, Permission.VIEW_OWN_ACCOUNT)
    link = AcceptInvitationUseCase(
        SqlAlchemyInvitationRepository(db),
        SqlAlchemyCoachAthleteLinkRepository(db),
    ).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        str(authenticated_user.user.email),
        invitation_id,
    )
    return _link_entity_to_response(link)


@router.post("/athlete/invitations/{invitation_id}/decline", status_code=204)
def decline_invitation(
    invitation_id: str,
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> Response:
    """Decline a pending invitation."""
    authenticated_user = guard.authorize(token, Permission.VIEW_OWN_ACCOUNT)
    DeclineInvitationUseCase(SqlAlchemyInvitationRepository(db)).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        str(authenticated_user.user.email),
        invitation_id,
    )
    return Response(status_code=204)


@router.get("/coach/athletes", response_model=CoachAthleteListResponse)
def list_coach_athletes(
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> CoachAthleteListResponse:
    """List athletes linked to the authenticated coach."""
    authenticated_user = guard.authorize(token, Permission.VIEW_OWN_ACCOUNT)
    items = ListCoachAthletesUseCase(SqlAlchemyCoachAthleteLinkRepository(db)).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
    )
    return CoachAthleteListResponse(items=[_coach_athlete_to_response(item) for item in items])


@router.get("/athlete/coaches", response_model=CoachAthleteListResponse)
def list_athlete_coaches(
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> CoachAthleteListResponse:
    """List coaches linked to the authenticated athlete."""
    authenticated_user = guard.authorize(token, Permission.VIEW_OWN_ACCOUNT)
    items = ListAthleteCoachesUseCase(SqlAlchemyCoachAthleteLinkRepository(db)).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
    )
    return CoachAthleteListResponse(items=[_coach_athlete_to_response(item) for item in items])


@router.get("/athlete/profile", response_model=AthleteProfileResponse)
def get_own_athlete_profile(
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: CoachingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> AthleteProfileResponse:
    """Get own athlete profile."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_OWN_COACHING_DATA)
    profile = GetAthleteProfileUseCase(
        SqlAlchemyAthleteProfileRepository(db),
        access_guard,
    ).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        authenticated_user.user.id,
    )
    return _profile_to_response(profile)


@router.put("/athlete/profile", response_model=AthleteProfileResponse)
def save_athlete_profile(
    body: SaveAthleteProfileRequest,
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> AthleteProfileResponse:
    """Create or update own athlete profile."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_OWN_COACHING_DATA)
    profile = SaveAthleteProfileUseCase(SqlAlchemyAthleteProfileRepository(db)).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        body.height_cm,
        body.weight_kg,
        body.age,
        body.gender,
    )
    return _profile_entity_to_response(profile)


@router.get("/coach/athletes/{athlete_id}/profile", response_model=AthleteProfileResponse)
def get_linked_athlete_profile(
    athlete_id: str,
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: CoachingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> AthleteProfileResponse:
    """View linked athlete profile."""
    authenticated_user = guard.authorize(token, Permission.VIEW_LINKED_ATHLETE_DATA)
    profile = GetAthleteProfileUseCase(
        SqlAlchemyAthleteProfileRepository(db),
        access_guard,
    ).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        _parse_athlete_id(athlete_id),
    )
    return _profile_to_response(profile)


@router.get("/athlete/records", response_model=PersonalRecordListResponse)
def list_own_personal_records(
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: CoachingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PersonalRecordListResponse:
    """List own personal records."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_OWN_COACHING_DATA)
    result = ListPersonalRecordsUseCase(
        SqlAlchemyPersonalRecordRepository(db),
        access_guard,
    ).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        authenticated_user.user.id,
        PageRequest(offset=offset, limit=limit),
    )
    return _records_to_response(result)


@router.post("/athlete/records", response_model=PersonalRecordResponse, status_code=201)
def create_personal_record(
    body: CreatePersonalRecordRequest,
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> PersonalRecordResponse:
    """Create a personal record."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_OWN_COACHING_DATA)
    record = CreatePersonalRecordUseCase(SqlAlchemyPersonalRecordRepository(db)).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        body.record_type,
        body.name,
        body.value,
        body.unit,
        body.achieved_at,
    )
    return _record_entity_to_response(record)


@router.put("/athlete/records/{record_id}", response_model=PersonalRecordResponse)
def update_personal_record(
    record_id: str,
    body: UpdatePersonalRecordRequest,
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> PersonalRecordResponse:
    """Update own personal record."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_OWN_COACHING_DATA)
    record = UpdatePersonalRecordUseCase(SqlAlchemyPersonalRecordRepository(db)).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        record_id,
        body.record_type,
        body.name,
        body.value,
        body.unit,
        body.achieved_at,
    )
    return _record_entity_to_response(record)


@router.delete("/athlete/records/{record_id}", status_code=204)
def delete_personal_record(
    record_id: str,
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> Response:
    """Delete own personal record."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_OWN_COACHING_DATA)
    DeletePersonalRecordUseCase(SqlAlchemyPersonalRecordRepository(db)).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        record_id,
    )
    return Response(status_code=204)


@router.get("/coach/athletes/{athlete_id}/records", response_model=PersonalRecordListResponse)
def list_linked_athlete_records(
    athlete_id: str,
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: CoachingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PersonalRecordListResponse:
    """List records for a linked athlete."""
    authenticated_user = guard.authorize(token, Permission.VIEW_LINKED_ATHLETE_DATA)
    result = ListPersonalRecordsUseCase(
        SqlAlchemyPersonalRecordRepository(db),
        access_guard,
    ).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        _parse_athlete_id(athlete_id),
        PageRequest(offset=offset, limit=limit),
    )
    return _records_to_response(result)


@router.get("/athlete/feedback", response_model=WorkoutFeedbackListResponse)
def list_own_workout_feedback(
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: CoachingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> WorkoutFeedbackListResponse:
    """List own workout feedback."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_OWN_COACHING_DATA)
    result = ListWorkoutFeedbackUseCase(
        SqlAlchemyWorkoutFeedbackRepository(db),
        access_guard,
    ).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        authenticated_user.user.id,
        PageRequest(offset=offset, limit=limit),
    )
    return _feedback_list_to_response(result)


@router.post("/athlete/feedback", response_model=WorkoutFeedbackResponse, status_code=201)
def submit_workout_feedback(
    body: SubmitWorkoutFeedbackRequest,
    db: DbSession,
    guard: AuthorizationGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
) -> WorkoutFeedbackResponse:
    """Submit workout feedback."""
    authenticated_user = guard.authorize(token, Permission.MANAGE_OWN_COACHING_DATA)
    feedback = SubmitWorkoutFeedbackUseCase(SqlAlchemyWorkoutFeedbackRepository(db)).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        body.text,
    )
    return _feedback_entity_to_response(feedback)


@router.get("/coach/athletes/{athlete_id}/feedback", response_model=WorkoutFeedbackListResponse)
def list_linked_athlete_feedback(
    athlete_id: str,
    db: DbSession,
    guard: AuthorizationGuardDep,
    access_guard: CoachingAccessGuardDep,
    token: Annotated[str, Depends(get_bearer_token)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> WorkoutFeedbackListResponse:
    """List feedback for a linked athlete."""
    authenticated_user = guard.authorize(token, Permission.VIEW_LINKED_ATHLETE_DATA)
    result = ListWorkoutFeedbackUseCase(
        SqlAlchemyWorkoutFeedbackRepository(db),
        access_guard,
    ).execute(
        authenticated_user.user.id,
        authenticated_user.user.role,
        _parse_athlete_id(athlete_id),
        PageRequest(offset=offset, limit=limit),
    )
    return _feedback_list_to_response(result)
