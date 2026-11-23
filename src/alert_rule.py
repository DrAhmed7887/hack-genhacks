"""PollenPlan alert rule: trap first (docs/PREREG_NOWCAST_2026.md, H1 and H3).

Today's alert = yesterday's observed trap count at or above the signed
threshold (rules/thresholds.json, daily mean grains/m3). On the untouched
2026 season this rule (P0) caught 164 of 215 high-pollen days against 70 for
the CAMS forecast for the same day; the fusion model F1 did not beat it (H3
failed), so the product ships this rule, the simpler one.

If yesterday's reading is missing, the rule does not alert (it never falls
back to the forecast silently). `reading_age_days` lets a clinic whose
network publishes late use a two-day-old count; the 2026 sensitivity check
(P0 with D-2) also beat the forecast.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrapAlert:
    species: str
    count: float
    threshold: float
    reading_age_days: int


def trap_alerts(readings: dict[str, float | None], thresholds: dict[str, float],
                reading_age_days: int = 1) -> list[TrapAlert]:
    """Every species whose trap reading is at or above its alert threshold.

    `readings` maps species -> daily mean grains/m3 from the clinic's local
    trap for day D - reading_age_days (None = no reading). Species without a
    signed threshold are ignored.
    """
    if reading_age_days not in (1, 2):
        raise ValueError("reading_age_days must be 1 (yesterday) or 2 (pre-registered sensitivity)")
    out = []
    for species, threshold in thresholds.items():
        count = readings.get(species)
        if count is not None and count >= threshold:
            out.append(TrapAlert(species, float(count), float(threshold), reading_age_days))
    return out
