from datetime import date

import pytest

from app.domain.auth_policy import is_adult, normalize_email, password_problem


@pytest.mark.parametrize("password", ["Password1", "abcdefg1", "1234567a", "a1" * 36])
def test_acceptable_passwords(password):
    assert password_problem(password) is None


@pytest.mark.parametrize(
    "password",
    ["", "short1", "alllettersss", "123456789", "a1" + "x" * 71, "1" + "é" * 40],
)
def test_unacceptable_passwords(password):
    assert password_problem(password)


def test_is_adult_boundaries():
    today = date(2026, 10, 7)
    assert is_adult(date(2008, 10, 7), today)  # turns 18 today
    assert not is_adult(date(2008, 10, 8), today)  # turns 18 tomorrow
    assert is_adult(date(1990, 1, 1), today)


def test_is_adult_leap_day_birthday():
    assert not is_adult(date(2008, 2, 29), date(2026, 2, 28))
    assert is_adult(date(2008, 2, 29), date(2026, 3, 1))


def test_normalize_email():
    assert normalize_email("  Harsh@Example.COM ") == "harsh@example.com"
