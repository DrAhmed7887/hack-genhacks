"""PollenPlan Clinical Assistant: prompt assembly, model call, clinician Q&A guard.

The model is a free text model run offline (RWTHgpt Qwen via the local
`rwth-ask` CLI; synthetic patients only, no real data leaves the machine).
Its output is never trusted: drafts go through src/message_guard.py, and
Q&A answers go through `check_answer` below. Symptom questions never reach
the model (`is_symptom_question`).
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path

from src import message_guard as g

ROOT = Path(__file__).resolve().parents[1]
PROMPT_FILE = ROOT / "rules" / "assistant_prompt.md"
MODEL = "qwen3.8-27b (RWTHgpt, via rwth-ask)"
SYMPTOM_REPLY = "Please contact your clinic, or emergency services if it is severe."
NOT_IN_DATA = "Not in today's data."
WITHHELD = "Answer withheld: it failed the code safety check."
SYMPTOM_RX = re.compile(
    r"\b(?:symptom\w*|burn\w*|itch\w*|sting\w*|sore|pain\w*|ache\w*|chest|tight\w*|wheez\w*|breath\w*|cough\w*|"
    r"sneez\w*|runny|blocked|congest\w*|swell\w*|swollen|rash|hives|fever|dizz\w*|faint\w*|attack|emergency|"
    r"bleed\w*|vomit\w*|eyes?|throat|nose|feel\w*|unwell|sick|worse|"
    # widened after the 23 Nov 2026 review: these reached the model
    r"scratch\w*|gasp\w*|blue|lips?|rub\w*|hoarse|red|puffy|headache\w*|nause\w*|tired|sleep\w*|wak\w*|"
    r"struggl\w*|can'?t|cannot|choking|crying|distress\w*|hurt\w*|skin|face|mouth)\b|"
    r"\b(?:says|reports|complain\w*|is having|has an?|have an?|mentions?|told me)\b", re.I)
NUMBER_WORDS = re.compile(r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|"
                          r"forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|dozen|half|double|twice)\b")
ADVICE = re.compile(r"\b(?:has (?:an? )?(?:asthma|allergy|hay fever|infection)|should (?:stop|start|increase|decrease|"
                    r"double|take|use|skip|see|go)|must (?:take|use|stop))\b")


def system_prompt() -> str:
    """The signed prompt body (front matter stripped)."""
    text = PROMPT_FILE.read_text()
    return text.split("---", 2)[2].strip() if text.startswith("---") else text.strip()


def prompt_sha256() -> str:
    return hashlib.sha256(system_prompt().encode()).hexdigest()


def call_model(prompt: str, timeout: int = 120) -> str | None:
    try:
        out = subprocess.run(["rwth-ask", "Follow the instructions below exactly."], input=prompt, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = out.stdout.strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()  # drop any reasoning block
    return text if out.returncode == 0 and text else None


def draft_prompt(f: g.Facts, age_band: str, clinician_note: str | None = None) -> str:
    facts = {"species": f.species, "trap_count_yesterday_grains_m3": f.count, "alert_threshold_grains_m3": f.threshold,
             "medicine_class": f.medicine_class, "age_band": age_band, "language": "English"}
    note = f"\nCLINICIAN NOTE: {clinician_note}\n" if clinician_note else "\n"
    return (system_prompt() + "\n\nTASK: Write the opening of today's reminder for this patient: at most two short "
            "sentences, plain English, no greeting line, no sign-off. Output only the opening text.\n"
            + note + "FACTS:\n" + json.dumps(facts, ensure_ascii=False))


def is_symptom_question(q: str) -> bool:
    """Conservative: any symptom, body-part or patient-report wording routes to the fixed reply."""
    return bool(SYMPTOM_RX.search(unicodedata.normalize("NFKC", q)))


def qa_prompt(question: str, facts: dict) -> str:
    return (system_prompt() + "\n\nTASK: Answer the clinician's question in at most three sentences, using only the "
            "FACTS. If the FACTS do not contain the answer, reply exactly: " + NOT_IN_DATA +
            "\n\nFACTS:\n" + json.dumps(facts, ensure_ascii=False) + "\n\nQUESTION: " + question)


def _numbers(obj) -> set[str]:
    out: set[str] = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            out |= _numbers(k) | _numbers(v)  # keys too: e.g. tier labels "1", "2", "3"
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            out |= _numbers(v)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        x = float(obj)
        out |= {f"{x:g}", f"{x:.0f}" if x.is_integer() else f"{x:.1f}", f"{x:.1f}", f"{x:.3f}"}
        if 0 < x < 1:
            out |= {f"{100 * x:.1f}", f"{100 * x:.0f}"}
    elif isinstance(obj, str):
        out |= set(re.findall(r"\d+(?:\.\d+)?", obj))
    return out


def check_answer(answer: str, facts: dict, question: str = "") -> list[str]:
    """Rules a clinician Q&A answer breaks: every number must come from FACTS; no dose/drug/symptom advice."""
    v: list[str] = []
    answer = unicodedata.normalize("NFKC", answer)
    low = answer.lower()
    allowed = _numbers(facts) | set(re.findall(r"\d+(?:\.\d+)?", question))  # e.g. patient IDs the clinician typed
    if NUMBER_WORDS.search(low):
        v.append("number_word")
    if ADVICE.search(low):
        v.append("advice")
    for n in re.findall(r"\d+(?:[.,]\d+)?", answer.replace("m³", "m")):
        if n.replace(",", ".").rstrip(".") not in allowed:
            v.append(f"ungrounded_number:{n}")
    for name in ("dose", "amount_words", "dose_change", "link_or_contact", "frequency", "efficacy_claim"):
        if g.PATTERNS[name].search(low):
            v.append(name)
    if any(re.search(rf"\b{d}\b", low) for d in g.DRUG_NAMES):
        v.append("drug_or_brand_name")
    if re.search(r"\b(?:diagnos\w*|you have (?:an? )?(?:allergy|asthma|infection))\b", low):
        v.append("diagnosis")
    return sorted(set(v))


def answer(question: str, facts: dict) -> dict:
    """Clinician Q&A with both guards. Returns what was shown and why."""
    if is_symptom_question(question):
        return {"question": question, "route": "symptom_router", "model_called": False, "answer": SYMPTOM_REPLY,
                "violations": []}
    raw = call_model(qa_prompt(question, facts))
    if raw is None:
        return {"question": question, "route": "model", "model_called": True, "answer": NOT_IN_DATA,
                "raw": None, "violations": ["no_model_output"]}
    viol = check_answer(raw, facts, question)
    return {"question": question, "route": "model", "model_called": True,
            "answer": WITHHELD if viol else " ".join(raw.split()), "raw": raw, "violations": viol}
