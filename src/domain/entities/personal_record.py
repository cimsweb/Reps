from dataclasses import dataclass
from datetime import datetime

from domain.entities.record_type import RecordType
from domain.value_objects.personal_record_id import PersonalRecordId
from domain.value_objects.record_unit import RecordUnit
from domain.value_objects.record_value import RecordValue
from domain.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class PersonalRecord:
    """Personal best on a distance or exercise."""

    id: PersonalRecordId
    athlete_id: UserId
    record_type: RecordType
    name: str
    value: RecordValue
    unit: RecordUnit
    achieved_at: datetime
    created_at: datetime
