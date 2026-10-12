"""Smoke tests for app.py using Streamlit's built-in AppTest (no extra deps)."""

from streamlit.testing.v1 import AppTest


def make_app() -> AppTest:
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    return at


def test_default_render():
    at = make_app()
    assert not at.exception
    assert at.title[0].value == "Borderless Meeting Planner"
    assert at.multiselect[0].value == ["London", "Bali"]
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Cities"] == "2"
    assert metrics["Overlapping hours (next 7 days)"] == "7.0 h"
    assert [s.value for s in at.subheader] == ["Local clocks", "24-hour local view"]


def test_no_city_selected():
    at = make_app()
    at.multiselect[0].set_value([]).run()
    assert not at.exception
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Cities"] == "0"
    assert metrics["Overlapping hours (next 7 days)"] == "0.0 h"
    # no clocks / 24-hour view without a selection
    assert [s.value for s in at.subheader] == []
    assert any("Select at least one city" in i.value for i in at.info)


def test_no_overlap_message():
    at = make_app()
    at.multiselect[0].set_value(["London", "Sydney"]).run()
    assert not at.exception
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Overlapping hours (next 7 days)"] == "0.0 h"
    assert any("No overlapping window" in w.value for w in at.warning)


def test_warning_when_no_overlap_at_all():
    """Zero overlap (e.g. Tokyo + London) must surface as a warning, not a caption."""
    at = make_app()
    at.multiselect[0].set_value(["Tokyo", "London"]).run()
    assert not at.exception
    metrics = {m.label: m.value for m in at.metric}
    assert metrics["Overlapping hours (next 7 days)"] == "0.0 h"
    assert len(at.warning) >= 1
    assert any("No overlapping window" in w.value for w in at.warning)
