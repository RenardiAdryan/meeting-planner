"""Pure logic for the Borderless Meeting Planner.

No Streamlit imports here -- everything takes an explicit ``now`` and is
testable with pytest alone (see SPEC.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# Working hours are local, start-inclusive, end-exclusive: [09:00, 17:00).
WORK_START = 9
WORK_END = 17
HORIZON_DAYS = 7
STEP = timedelta(minutes=1)


@dataclass(frozen=True)
class City:
    name: str
    tz: str  # IANA zone name, e.g. "Europe/London"


CITIES: list[City] = [
    City("Honolulu", "Pacific/Honolulu"),
    City("Anchorage", "America/Anchorage"),
    City("Los Angeles", "America/Los_Angeles"),
    City("Denver", "America/Denver"),
    City("Phoenix", "America/Phoenix"),
    City("Mexico City", "America/Mexico_City"),
    City("Chicago", "America/Chicago"),
    City("New York", "America/New_York"),
    City("Toronto", "America/Toronto"),
    City("Bogota", "America/Bogota"),
    City("Lima", "America/Lima"),
    City("Santiago", "America/Santiago"),
    City("São Paulo", "America/Sao_Paulo"),
    City("Buenos Aires", "America/Argentina/Buenos_Aires"),
    City("Reykjavik", "Atlantic/Reykjavik"),
    City("London", "Europe/London"),
    City("Lisbon", "Europe/Lisbon"),
    City("Paris", "Europe/Paris"),
    City("Berlin", "Europe/Berlin"),
    City("Amsterdam", "Europe/Amsterdam"),
    City("Madrid", "Europe/Madrid"),
    City("Rome", "Europe/Rome"),
    City("Warsaw", "Europe/Warsaw"),
    City("Athens", "Europe/Athens"),
    City("Istanbul", "Europe/Istanbul"),
    City("Cairo", "Africa/Cairo"),
    City("Dubai", "Asia/Dubai"),
    City("Mumbai", "Asia/Kolkata"),
    City("Dhaka", "Asia/Dhaka"),
    City("Bali", "Asia/Makassar"),  # WITA, UTC+8 (Asia/Denpasar missing from tzdata pkg)
    City("Singapore", "Asia/Singapore"),
    City("Hong Kong", "Asia/Hong_Kong"),
    City("Tokyo", "Asia/Tokyo"),
    City("Sydney", "Australia/Sydney"),
    City("Auckland", "Pacific/Auckland"),
    City("Kiritimati", "Pacific/Kiritimati"),
]


def local_time(instant: datetime, city: City) -> datetime:
    """Convert a UTC instant to the city's local time (DST-safe)."""
    return instant.astimezone(ZoneInfo(city.tz))


def is_working(instant: datetime, city: City) -> bool:
    """True if the city is inside [09:00, 17:00) local time at ``instant``."""
    local = local_time(instant, city)
    minutes = local.hour * 60 + local.minute
    return WORK_START * 60 <= minutes < WORK_END * 60


def overlap_windows(cities: list[City], now: datetime) -> list[tuple[datetime, datetime]]:
    """Merged UTC windows in [now, now + 7 days) where every city is working.

    Scanned in 1-minute steps; empty list when no cities or no overlap.
    """
    if not cities:
        return []
    end = now + timedelta(days=HORIZON_DAYS)
    windows: list[tuple[datetime, datetime]] = []
    window_start: datetime | None = None
    t = now
    while t < end:
        if all(is_working(t, city) for city in cities):
            if window_start is None:
                window_start = t
        elif window_start is not None:
            windows.append((window_start, t))
            window_start = None
        t += STEP
    if window_start is not None:
        windows.append((window_start, end))
    return windows


def overlap_hours(cities: list[City], now: datetime) -> float:
    """Total overlapping hours over the next 7 days."""
    windows = overlap_windows(cities, now)
    total = sum((end - start).total_seconds() for start, end in windows)
    return total / 3600


def hour_states(cities: list[City], now: datetime) -> dict[str, list[str]]:
    """Per-city 24 cell states for the city's current local date.

    Returns city name -> list of 24 values:
    "overlap" (green), "working" (blue), "outside" (gray).
    A cell is "overlap" if any of its 60 minutes is a good minute for all cities.
    """
    states: dict[str, list[str]] = {}
    for city in cities:
        day = local_time(now, city).replace(hour=0, minute=0, second=0, microsecond=0)
        cells: list[str] = []
        for hour in range(24):
            cell_start = day + timedelta(hours=hour)
            if not is_working(cell_start, city):
                cells.append("outside")
                continue
            overlap = any(
                all(is_working(cell_start + timedelta(minutes=m), c) for c in cities)
                for m in range(60)
            )
            cells.append("overlap" if overlap else "working")
        states[city.name] = cells
    return states


def local_clock(city: City, now: datetime) -> str:
    """City's current local time as HH:MM:SS."""
    return local_time(now, city).strftime("%H:%M:%S")


def utc_offset_hours(city: City, instant: datetime) -> float:
    """The city's UTC offset in hours at ``instant`` (may be fractional)."""
    offset = local_time(instant, city).utcoffset()
    assert offset is not None
    return offset.total_seconds() / 3600


def format_offset(hours: float) -> str:
    """Format an offset like 1.0 -> 'UTC+1', -4.0 -> 'UTC-4', 5.5 -> 'UTC+5:30'."""
    total_minutes = int(round(hours * 60))
    sign = "+" if total_minutes >= 0 else "-"
    hh, mm = divmod(abs(total_minutes), 60)
    return f"UTC{sign}{hh}" if mm == 0 else f"UTC{sign}{hh}:{mm:02d}"


def clock_badge(city: City, now: datetime) -> str:
    """Badge text, e.g. 'Up Monday 2026-10-13 | UTC+1' (uses ASCII arrows)."""
    local = local_time(now, city)
    arrow = "↑"  # up arrow
    return f"{arrow} {local.strftime('%A %Y-%m-%d')} · {format_offset(utc_offset_hours(city, now))}"


def row_label(city: City, now: datetime) -> str:
    """24-hour view row label, e.g. 'London — Tue 2026-10-13 local · green = overlap'."""
    local = local_time(now, city)
    return f"{city.name} — {local.strftime('%a %Y-%m-%d')} local · green = overlap"


def format_hours(value: float) -> str:
    """Format overlap hours for display: 7.0 -> '7.0 h'."""
    return f"{value:.1f} h"


def selection_caption(cities: list[City]) -> str:
    """Sidebar caption, e.g. '2 of 36 cities selected'."""
    return f"{len(cities)} of {len(CITIES)} cities selected"
