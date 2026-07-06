import pytest

from stealthbench.__main__ import _stamp


def test_stamp_is_filesystem_safe_and_ordered():
    assert _stamp("2026-07-06T15:52:31.123456+00:00") == "20260706T155231123456"
    # no timezone / separator characters survive
    assert ":" not in _stamp("2026-07-06T15:52:31.1+00:00")
    assert "+" not in _stamp("2026-07-06T15:52:31.1+00:00")


def test_stamp_disambiguates_two_runs_in_the_same_second():
    a = _stamp("2026-07-06T15:52:31.100000+00:00")
    b = _stamp("2026-07-06T15:52:31.900000+00:00")
    assert a != b  # same wall-clock second, distinct microseconds -> distinct filenames


def test_stamp_handles_negative_offset_and_missing_micros():
    # tz sign must not leak; a whole-second timestamp still yields digits+T only
    assert _stamp("2026-07-06T15:52:31-03:00") == "20260706T155231"


def test_stamp_rejects_unparseable_timestamp():
    with pytest.raises(ValueError):
        _stamp("not-a-timestamp")
