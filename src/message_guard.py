"""Code-side safety gate for AI-written reminder drafts (rules/assistant_prompt.md).

The model only proposes the opening sentences of a reminder. Code then:
  1. checks that opening against hard rules (no dose, frequency, drug or brand
     name, other species or medicine class, symptom or diagnostic wording,
     unexplained numbers, links), and
  2. appends the signed lines itself, so a model can never drop or reword them.
If the opening fails any rule, the deterministic template (built only from
signed wording) is used instead, and the failure is recorded.

Also: risk ordering for the nurse batch (Ahmed, 23 Nov 2026: "triage severe
asthma patients first").
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.reminders import ASTHMA_LINE, SAFETY_LINE, Patient

# Ahmed, 23 Nov 2026: every message ends with this directive.
DIRECTIVE = "Contact your clinic if your symptoms worsen or if you have questions about your prescription."
MAX_OPENING_WORDS = 45

DRUG_NAMES = (  # INNs and brands common in allergic rhinitis / asthma (lower case)
    "mometasone", "fluticasone", "budesonide", "beclomethasone", "beclometasone", "triamcinolone", "ciclesonide",
    "cetirizine", "levocetirizine", "loratadine", "desloratadine", "fexofenadine", "bilastine", "rupatadine",
    "ebastine", "chlorphenamine", "chlorpheniramine", "diphenhydramine", "azelastine", "olopatadine", "ketotifen",
    "montelukast", "salbutamol", "albuterol", "formoterol", "salmeterol", "prednisolone", "prednisone",
    "epinephrine", "adrenaline", "cromoglicate", "cromolyn", "nasonex", "flonase", "avamys", "flixonase",
    "rhinocort", "zyrtec", "claritin", "clarityne", "aerius", "telfast", "allegra", "ventolin", "singulair",
    "dymista", "benadryl", "xyzal", "epipen", "symbicort", "seretide",
)
MED_CLASS_WORDS = ("antihistamine", "steroid", "corticosteroid", "spray", "tablet", "pill", "drops", "inhaler",
                   "reliever", "preventer", "immunotherapy")
SPECIES_WORDS = ("grass", "olive", "birch", "cypress", "plane", "ragweed", "mugwort", "alder", "hazel", "oak",
                 "pine", "nettle", "parietaria", "plantain", "ash", "chenopod")
PATTERNS = {
    "dose": re.compile(r"\b\d+(?:[.,]\d+)?\s*(?:mg|mcg|µg|ug|ml|puffs?|sprays?|squirts?|tablets?|pills?|drops?|doses?|units?)\b"),
    "amount_words": re.compile(r"\b(?:one|two|three|four|a couple of|several|extra|double|another)\s+(?:puffs?|sprays?|squirts?|tablets?|pills?|drops?|doses?)\b"),
    "frequency": re.compile(r"\b(?:once|twice|thrice|three times|daily|every day|each day|per day|a day|"
                            r"every \w+ hours?|morning and (?:night|evening)|at night|at bedtime|each morning|"
                            r"every morning|regularly|schedule|(?:one|two|three|four|five|\d+) times?)\b"),
    "dose_change": re.compile(r"\b(?:increase|decrease|reduce|double|stop taking|stop using|skip|extra dose|top up)\b"),
    "diagnosis_or_symptoms": re.compile(r"\b(?:diagnos\w*|symptom\w*|you have (?:an? )?(?:allergy|asthma|infection|hay fever)|"
                                        r"itch\w*|burning|sneez\w*|wheez\w*|chest|breath\w*|cough\w*|congest\w*|"
                                        r"runny|watery eyes|swell\w*|rash|fever|attack\w*|asthma\w*)\b"),
    # added after red-team run 1 (23 Nov 2026): "to help prevent asthma attacks" passed the gate
    "efficacy_claim": re.compile(r"\b(?:prevent\w*|protect\w*|control\w*|reliev\w*|relief|reduc\w*|avoid\w*|"
                                r"eas(?:e|es|ing)|cure\w*|work(?:s)? best|effective\w*|stop\w* (?:it|them|the))\b"),
    "link_or_contact": re.compile(r"(?:https?://|www\.|@|\+?\d[\d ]{7,})"),
}


@dataclass(frozen=True)
class Facts:
    species: str
    count: float
    threshold: float
    medicine_class: str  # exact phrase from src.reminders.MED_CLASS_LABELS
    asthma: bool


@dataclass
class Checked:
    opening: str
    violations: list[str] = field(default_factory=list)
    used_fallback: bool = False

    @property
    def ok(self) -> bool:
        return not self.violations


def _num(x: float) -> str:
    return f"{x:.0f}" if float(x).is_integer() else f"{x:g}"


def template_opening(f: Facts) -> str:
    """Deterministic opening from Ahmed's approved items (trap count, timing line)."""
    return (f"{f.species.capitalize()} pollen measured {_num(f.count)} grains/m³ yesterday, above the clinic's "
            f"alert line of {_num(f.threshold)}. Please use {f.medicine_class} today before you go out.")


def check_opening(text: str, f: Facts) -> list[str]:
    """Every rule the model's opening breaks (empty list = passes)."""
    v: list[str] = []
    t = " ".join(text.split())
    low = t.lower()
    if not t:
        return ["empty"]
    if len(t.split()) > MAX_OPENING_WORDS:
        v.append("too_long")
    for name, rx in PATTERNS.items():
        if rx.search(low):
            v.append(name)
    if any(re.search(rf"\b{d}\b", low) for d in DRUG_NAMES):
        v.append("drug_or_brand_name")
    if f.medicine_class.lower() not in low:
        v.append("medicine_class_on_file_missing")
    rest = low.replace(f.medicine_class.lower(), " ")
    if any(re.search(rf"\b{w}s?\b", rest) for w in MED_CLASS_WORDS):
        v.append("other_medicine_mentioned")
    if f.species not in low:
        v.append("species_missing")
    if any(re.search(rf"\b{s}\b", low) for s in SPECIES_WORDS if s != f.species):
        v.append("other_species_mentioned")
    allowed = {_num(f.count), _num(f.threshold), f"{f.count:g}", f"{f.threshold:g}"}
    for n in re.findall(r"\d+(?:[.,]\d+)?", t.replace("m³", "m3").replace("m3", "m")):
        if n.replace(",", ".") not in allowed:
            v.append(f"unexplained_number:{n}")
    if SAFETY_LINE.lower()[:30] in low or DIRECTIVE.lower()[:30] in low:
        v.append("model_wrote_signed_line")  # code appends signed lines; the model must not
    return sorted(set(v))


def finalise(model_opening: str | None, f: Facts) -> tuple[str, Checked]:
    """Full message = checked opening (or template) + signed lines appended by code."""
    if model_opening is None:
        chk = Checked(template_opening(f), ["no_model_output"], used_fallback=True)
    else:
        viol = check_opening(model_opening, f)
        chk = Checked(" ".join(model_opening.split()), viol, used_fallback=bool(viol))
        if viol:
            chk.opening = template_opening(f)
    lines = [chk.opening, SAFETY_LINE] + ([ASTHMA_LINE] if f.asthma else []) + [DIRECTIVE]
    return " ".join(lines), chk


def risk_tier(p: Patient) -> tuple[int, str]:
    """1 = asthma flag and moderate/severe; 2 = asthma flag or moderate/severe; 3 = mild, no asthma."""
    severe = p.severity == "moderate_severe"
    if p.asthma_flag and severe:
        return 1, "asthma flag + moderate/severe rhinitis"
    if p.asthma_flag:
        return 2, "asthma flag"
    if severe:
        return 2, "moderate/severe rhinitis"
    return 3, "mild, no asthma flag"
