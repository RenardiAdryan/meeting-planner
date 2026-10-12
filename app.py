"""Streamlit UI for the Borderless Meeting Planner.

Display-only: every computation (overlap scan, local times, cell states)
comes from logic.py. The wall clock is read here and passed in explicitly.
"""

from datetime import datetime, timedelta, timezone
import html

import streamlit as st

import logic

# state -> (background, text) for the 24-hour view and legend chips
STATE_COLORS = {
    "working": ("#cfe2ff", "#084298"),
    "overlap": ("#8ce0a5", "#146c2e"),
    "outside": ("#f1f3f5", "#868e96"),
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def render_legend() -> None:
    """Colored legend chips: Working / Overlapping / Outside working hours."""
    chips = []
    for label, state in [
        ("Working hours", "working"),
        ("Overlapping hours", "overlap"),
        ("Outside working hours", "outside"),
    ]:
        bg, fg = STATE_COLORS[state]
        chips.append(
            f'<span style="background:{bg};color:{fg};border-radius:999px;'
            f'padding:3px 12px;font-size:0.85rem;font-weight:600">{label}</span>'
        )
    st.markdown(
        f'<div style="display:flex;gap:8px;margin-bottom:8px">{"".join(chips)}</div>',
        unsafe_allow_html=True,
    )


def render_hour_row(city: logic.City, cells: list[str], now: datetime) -> None:
    """One 24-hour row: bold label + 24 colored hour cells (00-23)."""
    st.markdown(f"**{html.escape(logic.row_label(city, now))}**")
    spans = []
    for hour, state in enumerate(cells):
        bg, fg = STATE_COLORS[state]
        spans.append(
            f'<span style="background:{bg};color:{fg};border-radius:6px;padding:6px 0;'
            f"min-width:34px;text-align:center;font-size:0.75rem;"
            f'display:inline-block">{hour:02d}</span>'
        )
    st.markdown(
        f'<div style="display:flex;flex-wrap:wrap;gap:4px">{"".join(spans)}</div>',
        unsafe_allow_html=True,
    )


@st.fragment(run_every=timedelta(seconds=1))
def render_clocks(cities: list[logic.City]) -> None:
    """Live local clocks, refreshed every second without rerunning the page."""
    now = utc_now()
    columns = st.columns(len(cities))
    for column, city in zip(columns, cities):
        with column:
            st.markdown(f"**{html.escape(city.name)}**")
            st.markdown(
                f'<div style="font-size:2rem;font-weight:600;line-height:1.2">'
                f"{logic.local_clock(city, now)}</div>",
                unsafe_allow_html=True,
            )
            badge = html.escape(logic.clock_badge(city, now))
            st.markdown(
                f'<span style="display:inline-block;background:#f1f3f5;border-radius:999px;'
                f'padding:2px 10px;font-size:0.8rem;color:#495057">{badge}</span>',
                unsafe_allow_html=True,
            )


st.set_page_config(page_title="Borderless Meeting Planner", layout="wide")

# --- Sidebar: add / remove cities -----------------------------------------
st.sidebar.header("Cities")
city_by_name = {c.name: c for c in logic.CITIES}
selected_names = st.sidebar.multiselect(
    "Add or remove cities",
    options=[c.name for c in logic.CITIES],
    default=["London", "Bali"],
)
selected = [city_by_name[name] for name in selected_names]
st.sidebar.caption(logic.selection_caption(selected))

# --- Header and stats -------------------------------------------------------
st.title("Borderless Meeting Planner")
st.caption("Find a window where every city is inside 09:00–17:00 local time.")

now = utc_now()
overlap = logic.overlap_hours(selected, now)

col1, col2 = st.columns(2)
col1.metric("Cities", len(selected))
col2.metric("Overlapping hours (next 7 days)", logic.format_hours(overlap))

if not selected:
    st.info("Select at least one city in the sidebar.")
elif overlap == 0:
    st.warning(
        "No overlapping window in the next 7 days — every pair of cities is "
        "more than the working-hours length apart."
    )

# --- Local clocks -----------------------------------------------------------
if selected:
    st.subheader("Local clocks")
    render_clocks(selected)

    # --- 24-hour local view -------------------------------------------------
    st.subheader("24-hour local view")
    render_legend()
    states = logic.hour_states(selected, now)
    for city in selected:
        render_hour_row(city, states[city.name], now)
