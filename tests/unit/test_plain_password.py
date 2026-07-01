"""Tests for plain password validation."""

import pytest

from domain.exceptions import WeakPasswordError
from domain.value_objects.plain_password import PlainPassword


def test_plain_password_accepts_valid_value() -> None:
    password = PlainPassword("secure1A")
    assert password.value == "secure1A"


@pytest.mark.parametrize(
    "password",
    [
        "short1A",
        "a" * 129,
        "onlyletters",
        "12345678",
    ],
)
def test_plain_password_rejects_invalid_values(password: str) -> None:
    with pytest.raises(WeakPasswordError):
        PlainPassword(password)
