from enum import StrEnum


class Gender(StrEnum):
    """Athlete gender for profile display and analytics."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
