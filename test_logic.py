"""Tests for logic.py — acceptance criteria from SPEC.md section 6.

All time-dependent tests pin NOW so results are deterministic.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import logic
from logic import CITIES, City


def utc(iso: str) -> datetime:
    return datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)


# 2026-10-13: London=BST(+1), New York=EDT(-4), Sydney=AEDT(+11), Bali=+8
NOW = utc("2026-10-13T00:00")

LONDON = next(c for c in CITIES if c.name == "London")
NEW_YORK = next(c for c in CITIES if c.name == "New York")
SYDNEY = next(c for c in CITIES if c.name == "Sydney")
BALI = next(c for c in CITIES if c.name == "Bali")


def test_registry():
    assert len(CITIES) == 36
    assert len({c.name for c in CITIES}) == 36
    for city in CITIES:
        ZoneInfo(city.tz)  # must resolve, raises on invalid zone


def test_working_boundaries():
    """End-exclusive: [09:00, 17:00) local."""
    for hour, minute, expected in [
        (8, 59, False),
        (9, 0, True),
        (16, 59, True),
        (17, 0, False),
    ]:
        instant = utc("2026-10-13T00:00").astimezone(ZoneInfo(LONDON.tz))
        instant = instant.replace(hour=hour, minute=minute, second=0)
        assert logic.is_working(instant, LONDON) is expected, (hour, minute)


def test_single_city_overlap():
    assert logic.overlap_hours([LONDON], NOW) == 56.0  # 8 h x 7 days
    windows = logic.overlap_windows([LONDON], NOW)
    assert len(windows) == 7
    # London works 09:00-17:00 BST == 08:00-16:00 UTC
    assert windows[0] == (utc("2026-10-13T08:00"), utc("2026-10-13T16:00"))


def test_london_bali():
    assert logic.overlap_hours([LONDON, BALI], NOW) == 7.0
    windows = logic.overlap_windows([LONDON, BALI], NOW)
    assert len(windows) == 7
    # 08:00-09:00 UTC == London 09:00-10:00 == Bali 16:00-17:00
    assert windows[0] == (utc("2026-10-13T08:00"), utc("2026-10-13T09:00"))
    start, end = windows[0]
    assert logic.local_time(start, LONDON).strftime("%H:%M") == "09:00"
    assert logic.local_time(end, BALI).strftime("%H:%M") == "17:00"


def test_london_new_york():
    assert logic.overlap_hours([LONDON, NEW_YORK], NOW) == 21.0  # 3 h x 7 days
    windows = logic.overlap_windows([LONDON, NEW_YORK], NOW)
    # 13:00-16:00 UTC == London 14:00-17:00 == NY 09:00-12:00
    assert windows[0] == (utc("2026-10-13T13:00"), utc("2026-10-13T16:00"))


def test_london_sydney():
    assert logic.overlap_hours([LONDON, SYDNEY], NOW) == 0.0
    assert logic.overlap_windows([LONDON, SYDNEY], NOW) == []


def test_third_city_collapses_overlap():
    assert logic.overlap_hours([LONDON, BALI, NEW_YORK], NOW) == 0.0


def test_empty_selection():
    assert logic.overlap_hours([], NOW) == 0.0
    assert logic.overlap_windows([], NOW) == []


def test_dst_fall_back():
    """BST ends 2026-10-25 02:00 local -> back to GMT."""
    assert logic.utc_offset_hours(LONDON, utc("2026-10-25T00:30")) == 1.0
    assert logic.utc_offset_hours(LONDON, utc("2026-10-25T02:30")) == 0.0


def test_hour_states_london_bali():
    states = logic.hour_states([LONDON, BALI], NOW)
    london = states["London"]
    bali = states["Bali"]
    assert len(london) == 24 and len(bali) == 24
    # London: overlap 09, working 10-16, outside elsewhere
    assert london[9] == "overlap"
    assert all(london[h] == "working" for h in range(10, 17))
    assert all(london[h] == "outside" for h in list(range(0, 9)) + list(range(17, 24)))
    # Bali: overlap 16, working 09-15, outside elsewhere
    assert bali[16] == "overlap"
    assert all(bali[h] == "working" for h in range(9, 16))
    assert all(bali[h] == "outside" for h in list(range(0, 9)) + list(range(17, 24)))


def test_format_hours():
    assert logic.format_hours(7.0) == "7.0 h"
    assert logic.format_hours(0.0) == "0.0 h"


def test_selection_caption():
    assert logic.selection_caption([LONDON, BALI]) == "2 of 36 cities selected"


def test_local_clock_and_badge():
    assert logic.local_clock(LONDON, NOW) == "01:00:00"  # BST
    badge = logic.clock_badge(LONDON, NOW)
    assert "2026-10-13" in badge and "UTC+1" in badge
    assert logic.row_label(BALI, NOW).startswith("Bali — Tue 2026-10-13 local")


def test_format_offset():
    assert logic.format_offset(1.0) == "UTC+1"
    assert logic.format_offset(-4.0) == "UTC-4"
    assert logic.format_offset(5.5) == "UTC+5:30"
    assert logic.format_offset(-3.0) == "UTC-3"


def test_city_lookup():
    names = {c.name for c in CITIES}
    assert {"London", "Bali", "New York", "Sydney"} <= names
    assert isinstance(CITIES[0], City)
