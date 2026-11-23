"""Offline tests for src/assistant.py guards (no model call)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import assistant as ai  # noqa: E402

FACTS = {"species": "grass", "trap_count_yesterday_grains_m3": 104.0, "alert_threshold_grains_m3": 35,
         "cams_forecast_today_grains_m3": 19.5, "batch": {"roster": 200, "drafted": 111},
         "test_2026": {"high_days": 215, "trap_flagged": 164, "cams_flagged": 70}}


@pytest.mark.parametrize("q", [
    "A patient says her eyes are burning and she is going out tomorrow morning. What should she do?",
    "Patient P009 reports chest tightness. Can you advise?",
    "One of the children has a bad cough today, what should the parent do?",
    "He feels worse since yesterday",
    "Is sneezing normal at this count?",
])
def test_symptom_questions_never_reach_the_model(q, monkeypatch):
    monkeypatch.setattr(ai, "call_model", lambda *a, **k: pytest.fail("model must not be called"))
    r = ai.answer(q, FACTS)
    assert r["route"] == "symptom_router" and r["answer"] == ai.SYMPTOM_REPLY and r["model_called"] is False


@pytest.mark.parametrize("q", ["Why did grass alert today?", "Which patients should I review first?",
                               "How well does yesterday's trap count do against the CAMS forecast?"])
def test_operational_questions_go_to_the_model(q):
    assert not ai.is_symptom_question(q)


def test_grounded_answer_passes():
    a = "Yesterday's grass count was 104 grains/m³, above the alert line of 35; the forecast said 19.5, so it would not have alerted."
    assert ai.check_answer(a, FACTS) == []


@pytest.mark.parametrize("a,rule", [
    ("Grass was 140 yesterday.", "ungrounded_number:140"),
    ("Use 2 sprays of mometasone.", "dose"),
    ("They can use mometasone.", "drug_or_brand_name"),
    ("They should double the spray today.", "dose_change"),
    ("This patient has an allergy flare; you have asthma risk.", "diagnosis"),
])
def test_bad_answers_are_blocked(a, rule):
    assert rule in ai.check_answer(a, FACTS)


def test_blocked_answer_is_replaced(monkeypatch):
    monkeypatch.setattr(ai, "call_model", lambda *a, **k: "Use 2 sprays of mometasone twice daily.")
    r = ai.answer("What should P002 use?", FACTS)
    assert r["answer"] == ai.NOT_IN_DATA and r["violations"]


def test_prompt_file_is_signed_and_keeps_signed_threshold():
    text = ai.PROMPT_FILE.read_text()
    assert "status: signed" in text and "grass 35" in ai.system_prompt()
    import re
    assert not re.search(r"grass\D{0,25}\b30\b", ai.system_prompt(), re.I)  # 30 is birch, not grass
