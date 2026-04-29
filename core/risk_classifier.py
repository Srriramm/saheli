"""
risk_classifier.py — Deterministic GREEN / YELLOW / RED classification logic.

This module is the rule-based safety net that runs *after* Gemma 4's LLM
assessment. It ensures critical danger signs are never silently downgraded,
regardless of model output quality.

Priority order (highest wins):
  RED    > YELLOW > GREEN
"""

from config.settings import RISK_LEVELS


def classify_risk(danger_signs: list, vitals: dict = None) -> str:
    """
    Classify overall maternal risk level from detected danger signs and vitals.

    Parameters
    ----------
    danger_signs : list of str
        Danger sign strings already matched against WHO ANC checklist.
    vitals : dict, optional
        Keys: bp_sys, bp_dia, hb, temp_c

    Returns
    -------
    str — "RED", "YELLOW", or "GREEN"
    """
    vitals = vitals or {}
    level = "GREEN"

    # --- Vital sign thresholds ---
    bp_sys = vitals.get("bp_sys", 0)
    bp_dia = vitals.get("bp_dia", 0)
    hb = vitals.get("hb", 10.0)
    temp_c = vitals.get("temp_c", 37.0)

    # YELLOW thresholds (WHO: BP ≥130/85 in pregnancy is borderline gestational hypertension)
    if bp_sys >= 130 or bp_dia >= 85:
        level = _elevate(level, "YELLOW")
    if hb < 7.0:
        level = _elevate(level, "YELLOW")
    if temp_c >= 38.0:
        level = _elevate(level, "YELLOW")

    # RED thresholds (severe)
    if bp_sys >= 160 or bp_dia >= 110:
        level = _elevate(level, "RED")

    # --- Danger sign strings ---
    red_keywords = [
        "severe headache", "visual disturbance", "blurred vision",
        "severe bleeding", "heavy vaginal bleeding", "convulsions",
        "no foetal movement", "severe abdominal pain", "eclampsia",
        "postpartum haemorrhage", "loss of consciousness"
    ]
    yellow_keywords = [
        "hypertension", "haemoglobin", "severe anaemia",
        "fever", "chills", "reduced foetal movement",
        "oedema above ankles", "swollen face", "jaundice"
    ]

    signs_lower = [s.lower() for s in danger_signs]

    for kw in red_keywords:
        if any(kw in s for s in signs_lower):
            level = _elevate(level, "RED")
            break

    if level != "RED":
        for kw in yellow_keywords:
            if any(kw in s for s in signs_lower):
                level = _elevate(level, "YELLOW")
                break

    return level


def merge_risk(llm_risk: str, rule_risk: str) -> str:
    """
    Return the higher of two risk levels (LLM output vs rule-based result).
    Ensures the rule-based classifier can only *raise*, never lower, LLM output.
    """
    return max(llm_risk, rule_risk, key=lambda r: RISK_LEVELS.get(r, 0))


def _elevate(current: str, candidate: str) -> str:
    """Return candidate if it is a higher risk level than current."""
    return candidate if RISK_LEVELS.get(candidate, 0) > RISK_LEVELS.get(current, 0) else current
