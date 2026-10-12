# SPEC — Borderless Meeting Planner

## 1. Overview

Streamlit app that finds a time window where every selected city is inside
09:00–17:00 local time, over the next 7 days.

## 2. Constraints

- Python 3.13 (`.venv`). Files: `app.py` (UI only), `logic.py` (pure logic),
  `test_logic.py` (pytest).
- Only third-party libraries allowed: `streamlit`, `pytest`. Time zones via stdlib
  `zoneinfo` — never fixed offsets.
- All computation must be testable without starting Streamlit.

## 3. Features (matches UI template image)

### Sidebar — Cities

- Multiselect of 36 curated cities, removable tag chips.
- Caption: `N of 36 cities selected`.

### Header

- Title: **Borderless Meeting Planner**
- Subtitle: "Find a window where every city is inside 09:00–17:00 local time."

### Stats row

- `Cities` — selected count.
- `Overlapping hours (next 7 days)` — e.g. `5.0 h`, one decimal.
  No cities → prompt to select; zero overlap → **warning**: "No overlapping window
  in the next 7 days …" (e.g. Tokyo + London, exactly 8 h apart).

### Local clocks (one per city)

- City name, live local time `HH:MM:SS` (ticks every second),
  badge `↑ Weekday YYYY-MM-DD · UTC±H` in the city's local date.

### 24-hour local view

- Legend chips: Working hours (blue) / Overlapping hours (green) / Outside working hours (gray).
- Row per city: `City — Weekday YYYY-MM-DD local · green = overlap` + 24 cells `00`–`23`.
- Cell is green if any overlap minute falls in that local hour, blue if in working
  hours but not overlap, otherwise gray.

## 4. Data structures

- `City(name: str, tz: str)` — `tz` is an IANA zone name (e.g. `Europe/London`).
- `CITIES: list[City]` — exactly 36 unique, valid entries (appendix).
- Constants: `WORK_START = 9`, `WORK_END = 17` (end-exclusive), horizon = 7 days, step = 1 minute.
- Inputs: `selected: list[City]`, `now: datetime` (timezone-aware, passed explicitly —
  never reads the wall clock inside `logic.py`).
- Output: `windows: list[tuple[datetime, datetime]]` (UTC, sorted, merged);
  `overlap_hours = total duration / 3600`.
- Core functions: `is_working(instant, city)`, `overlap_windows(cities, now)`,
  `overlap_hours(cities, now)`, `hour_states(cities, now)`, `local_clock(city, now)`,
  `utc_offset_hours(city, instant)`.

## 5. Computation rules

- Scan `[now, now + 7 days)` in 1-minute steps.
- A minute is "good" iff every selected city's local time is in `[09:00, 17:00)`.
- Merge consecutive good minutes into windows; hours = merged minutes / 60.
- Local time is always derived per-instant via `ZoneInfo` (DST-safe).

## 6. Acceptance criteria — example test cases

All tests use a fixed `now = 2026-10-13T00:00Z` (London=BST +1, New York=EDT −4,
Sydney=AEDT +11, Bali=+8) so results are deterministic.

- `test_registry`: `len(CITIES) == 36`, names unique, every `tz` resolves via `ZoneInfo`.
- `test_working_boundaries` (London, end-exclusive):
  08:59 → False, 09:00 → True, 16:59 → True, 17:00 → False.
- `test_single_city_overlap`: `[London]` → `56.0 h` (8 h × 7 days).
- `test_london_bali`: `7.0 h`, 7 daily windows of exactly 1 h,
  `08:00–09:00 UTC` = London `09:00–10:00` = Bali `16:00–17:00`.
- `test_london_new_york`: `21.0 h` (3 h/day: London `14:00–17:00` = NY `09:00–12:00`).
- `test_london_sydney`: `0.0 h`, `windows == []` (10 h apart, 8 h windows can't meet).
- `test_third_city_collapses_overlap`: `[London, Bali, New York]` → `0.0 h`.
- `test_dst_fall_back`: London offset is `UTC+1` at `2026-10-25T00:30Z`,
  `UTC+0` at `2026-10-25T02:30Z`.
- `test_hour_states_london_bali`: London row → 09 green, 10–16 blue, rest gray;
  Bali row → 16 green, 09–15 blue, rest gray.
- `test_format_hours`: `7.0` → `"7.0 h"`.
- `test_selection_caption`: 2 cities → `"2 of 36 cities selected"`.

## 7. Manual UI checklist

- Layout matches the template image (sidebar Cities, stats, clocks, legend, 24-h rows).
- Clocks tick; changing selection updates stats and rows without restart.

## Appendix: CITIES (36)

| City | IANA zone |
|---|---|
| Honolulu | Pacific/Honolulu |
| Anchorage | America/Anchorage |
| Los Angeles | America/Los_Angeles |
| Denver | America/Denver |
| Phoenix | America/Phoenix |
| Mexico City | America/Mexico_City |
| Chicago | America/Chicago |
| New York | America/New_York |
| Toronto | America/Toronto |
| Bogota | America/Bogota |
| Lima | America/Lima |
| Santiago | America/Santiago |
| São Paulo | America/Sao_Paulo |
| Buenos Aires | America/Argentina/Buenos_Aires |
| Reykjavik | Atlantic/Reykjavik |
| London | Europe/London |
| Lisbon | Europe/Lisbon |
| Paris | Europe/Paris |
| Berlin | Europe/Berlin |
| Amsterdam | Europe/Amsterdam |
| Madrid | Europe/Madrid |
| Rome | Europe/Rome |
| Warsaw | Europe/Warsaw |
| Athens | Europe/Athens |
| Istanbul | Europe/Istanbul |
| Cairo | Africa/Cairo |
| Dubai | Asia/Dubai |
| Mumbai | Asia/Kolkata |
| Dhaka | Asia/Dhaka |
| Bali | Asia/Makassar |
| Singapore | Asia/Singapore |
| Hong Kong | Asia/Hong_Kong |
| Tokyo | Asia/Tokyo |
| Sydney | Australia/Sydney |
| Auckland | Pacific/Auckland |
| Kiritimati | Pacific/Kiritimati |
