import sys as _sys, os as _os
_project_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _project_root)
# Remove any conflicting 'models' cached from Colab's environment
for _k in list(_sys.modules.keys()):
    if _k == 'models' or _k.startswith('models.'):
        del _sys.modules[_k]

import json
import logging
import os
import re
from sklearn.metrics import f1_score, accuracy_score, classification_report
from core.function_tools import assess_danger_signs
from core.risk_classifier import classify_risk, merge_risk
from core.triage_engine import TriageEngine
from models.gemma_runner import GemmaRunner
from config.settings import MODEL_PATH


SYSTEM_PROMPT_EVAL = (
    "You are Saheli, a maternal health assistant for ASHA workers. "
    "Given the patient's symptoms and vitals, output a JSON tool call to "
    "assess_danger_signs followed by a short RED/YELLOW/GREEN recommendation "
    "in plain language. Use WHO Antenatal Care guidelines."
)


def load_test_cases():
    path = _os.path.join(_project_root, "tests", "sample_cases.json")
    with open(path, "r") as f:
        return json.load(f)


def _build_voice_sim(case: dict) -> str:
    """Build the natural-language input the model would receive from Whisper.

    If the case has a 'voice_input' field, use it verbatim (for Hindi/narrative cases).
    Otherwise build from the structured symptoms + vitals fields.
    """
    if case.get("voice_input"):
        return case["voice_input"]
    vitals = case.get("vitals", {})
    vitals_str = ", ".join(
        f"{k.replace('_', ' ')} {v}" for k, v in vitals.items()
    )
    voice_sim = f"Patient has {case['symptoms']} at {case['weeks']} weeks."
    if vitals_str:
        voice_sim += f" Vitals: {vitals_str}."
    return voice_sim


def _rule_based_predict(case: dict) -> str:
    """Deterministic prediction using only the rule-based pipeline (no LLM)."""
    try:
        symptoms_text = case["symptoms"]
        vitals = case.get("vitals", {})
        symptoms_list = [s.strip() for s in symptoms_text.replace(",", ";").split(";")]
        assessment = assess_danger_signs(symptoms_list, vitals)
        rule_risk = classify_risk(assessment["danger_signs"], vitals)
        return merge_risk(assessment["risk_level"], rule_risk)
    except Exception as e:
        logging.error(f"Rule-based prediction failed for {case.get('id', '?')}: {e}")
        return "ERROR"


_RED_SIGNALS = [
    "medical emergency", "call emergency", "emergency services",
    "call 108", "ambulance", "do not wait",
    "danger sign", "refer to phc", "life-threatening",
    "go to the hospital immediately", "go to the er",
]
_YELLOW_SIGNALS = [
    "needs attention", "within 24 hours", "24 hours",
    "refer to clinic", "needs monitoring", "warning sign",
    "requires monitoring", "needs further", "concerning presentation",
    "should be seen", "follow up", "consult", "midwife",
    "obstetrician", "anemia", "anaemia", "jaundice",
    "immediately by a doctor", "promptly",
]
_GREEN_SIGNALS = [
    "normal", "common in pregnancy", "routine monitoring",
    "no cause for alarm", "expected", "not a concern",
    "physiological", "reassure", "very common", "morning sickness",
    "first trimester", "second trimester", "typical", "nothing to worry",
    "usually normal", "generally normal", "common symptom",
]


def _extract_risk(text: str, debug_id: str = "") -> str:
    """Pull RED/YELLOW/GREEN from an LLM response string.

    Tries explicit labels first, then JSON risk_level, then natural-language signals.
    """
    upper = text.upper()

    # 1. Explicit label
    m = re.search(r"\b(RED|YELLOW|GREEN)\b", upper)
    if m:
        return m.group(1)

    # 2. JSON risk_level field
    m = re.search(r'"RISK_LEVEL"\s*:\s*"(RED|YELLOW|GREEN)"', upper)
    if m:
        return m.group(1)

    # 3. Natural-language signals (score and pick the strongest)
    scores = {"RED": 0, "YELLOW": 0, "GREEN": 0}
    for sig in _RED_SIGNALS:
        if sig.upper() in upper:
            scores["RED"] += 1
    for sig in _YELLOW_SIGNALS:
        if sig.upper() in upper:
            scores["YELLOW"] += 1
    for sig in _GREEN_SIGNALS:
        if sig.upper() in upper:
            scores["GREEN"] += 1

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best

    if debug_id:
        print(f"  [DEBUG {debug_id}] raw output: {text[:300]!r}", flush=True)
    return "UNKNOWN"


def _pure_llm_predict(runner: GemmaRunner, case: dict) -> str:
    """Pure LLM call with no rule-based merge — isolates fine-tune quality."""
    try:
        output = runner.call_raw(
            system_prompt=SYSTEM_PROMPT_EVAL,
            user_prompt=_build_voice_sim(case),
            max_tokens=512,
        )
        return _extract_risk(output, debug_id=case.get("id", ""))
    except Exception as e:
        logging.error(f"Pure-LLM case {case['id']} failed: {e}")
        return "ERROR"


def run_evaluation(model_path: str, base_model_path: str = None):
    """
    Compute accuracy + F1 on test cases. Prints up to four rows:
      0. Base Gemma 4 E4B (no fine-tuning) — only if base_model_path is given
      1. Rule-based baseline    — no LLM at all
      2. Fine-tuned LLM         — model output only, no rule merge
      3. Fine-tuned LLM + Rule  — production path (TriageEngine.run_triage)

    Row 0 vs Row 2 is the delta that proves fine-tuning worked.
    """
    cases = load_test_cases()
    print(f"\nEvaluating Saheli on {len(cases)} maternal health test cases...")
    y_true = [c["expected_risk"] for c in cases]

    # ── Row 1: Rule-based baseline ────────────────────────────────────────
    y_rule = [_rule_based_predict(c) for c in cases]
    rule_acc = accuracy_score(y_true, y_rule)
    rule_f1  = f1_score(y_true, y_rule, average="weighted", zero_division=0)

    print("\n" + "=" * 76)
    print("  SAHELI EVALUATION BENCHMARKS")
    print("=" * 76)

    llm_available = os.path.exists(model_path)
    if not llm_available:
        print(f"{'Metric':<25} {'Rule-only':>15}")
        print("-" * 76)
        print(f"{'Accuracy':<25} {rule_acc*100:>14.1f}%")
        print(f"{'F1 (weighted)':<25} {rule_f1*100:>14.1f}%")
        print("=" * 76)
        print(f"\nNOTE: LLM rows skipped — model not found at:\n  {model_path}")
        print("Run './models/download_model.sh' then re-run evaluation.\n")
        print("Detailed report — Rule-based baseline:")
        print(classification_report(y_true, y_rule, labels=["RED", "YELLOW", "GREEN"],
                                    zero_division=0))
        return {"rule_accuracy": rule_acc, "rule_f1": rule_f1}

    # ── Row 0: Base model (no fine-tuning) — optional ─────────────────────
    y_base = None
    base_acc = base_f1 = None
    if base_model_path and os.path.exists(base_model_path):
        print(f"Loading BASE model (no fine-tuning) from:\n  {base_model_path}", flush=True)
        base_runner = GemmaRunner(model_path=base_model_path)
        print(f"Running Base-LLM predictions (0/{len(cases)})...", flush=True)
        y_base = []
        for i, c in enumerate(cases):
            y_base.append(_pure_llm_predict(base_runner, c))
            print(f"  [{i+1:02d}/{len(cases)}] {c['id']} → {y_base[-1]}", flush=True)
        base_acc = accuracy_score(y_true, y_base)
        base_f1  = f1_score(y_true, y_base, average="weighted", zero_division=0)
    elif base_model_path:
        print(f"NOTE: Base model not found at {base_model_path} — Row 0 skipped.")

    # ── Load fine-tuned model once, share across Rows 2 and 3 ────────────
    print(f"\nLoading fine-tuned model from:\n  {model_path}", flush=True)
    runner = GemmaRunner(model_path=model_path)
    engine = TriageEngine.__new__(TriageEngine)
    engine.runner = runner

    # Row 2: Fine-tuned pure LLM
    print(f"\nRunning Fine-tuned LLM predictions (0/{len(cases)})...", flush=True)
    y_pure = []
    for i, c in enumerate(cases):
        y_pure.append(_pure_llm_predict(runner, c))
        print(f"  [{i+1:02d}/{len(cases)}] {c['id']} → {y_pure[-1]}", flush=True)
    pure_acc = accuracy_score(y_true, y_pure)
    pure_f1  = f1_score(y_true, y_pure, average="weighted", zero_division=0)

    # Row 3: Fine-tuned LLM + Rule merge (production)
    print(f"\nRunning Fine-tuned LLM+Rule predictions (0/{len(cases)})...", flush=True)
    y_merge = []
    for i, case in enumerate(cases):
        try:
            result = engine.run_triage(
                patient_id=f"EVAL-{case['id']}",
                language="en",
                voice_input=_build_voice_sim(case),
            )
            y_merge.append(result.risk_level)
        except Exception as e:
            logging.error(f"Merge case {case['id']} failed: {e}")
            y_merge.append("ERROR")
        print(f"  [{i+1:02d}/{len(cases)}] {case['id']} → {y_merge[-1]}", flush=True)

    merge_acc = accuracy_score(y_true, y_merge)
    merge_f1  = f1_score(y_true, y_merge, average="weighted", zero_division=0)

    # ── Summary table ─────────────────────────────────────────────────────
    print("\n" + "=" * 76)
    if y_base is not None:
        print(f"{'Metric':<25} {'Rule-only':>12} {'Base LLM':>12} {'Fine-tuned':>12} {'Finetuned+Rule':>14}")
        print("-" * 76)
        print(f"{'Accuracy':<25} {rule_acc*100:>11.1f}% {base_acc*100:>11.1f}% {pure_acc*100:>11.1f}% {merge_acc*100:>13.1f}%")
        print(f"{'F1 (weighted)':<25} {rule_f1*100:>11.1f}% {base_f1*100:>11.1f}% {pure_f1*100:>11.1f}% {merge_f1*100:>13.1f}%")
        delta_acc = pure_acc - base_acc
        delta_f1  = pure_f1  - base_f1
        print(f"\n  Fine-tuning delta  →  Accuracy: {delta_acc*100:+.1f}%   F1: {delta_f1*100:+.1f}%")
    else:
        print(f"{'Metric':<25} {'Rule-only':>12} {'Fine-tuned':>12} {'Finetuned+Rule':>14}")
        print("-" * 76)
        print(f"{'Accuracy':<25} {rule_acc*100:>11.1f}% {pure_acc*100:>11.1f}% {merge_acc*100:>13.1f}%")
        print(f"{'F1 (weighted)':<25} {rule_f1*100:>11.1f}% {pure_f1*100:>11.1f}% {merge_f1*100:>13.1f}%")
        if not base_model_path:
            print("\n  TIP: pass base_model_path= to show fine-tuning delta (Row 0 vs Row 2).")
    print("=" * 76)

    if y_base is not None:
        print("\nDetailed report — Base LLM (no fine-tuning):")
        print(classification_report(y_true, y_base, labels=["RED", "YELLOW", "GREEN"],
                                    zero_division=0))

    print("\nDetailed report — Fine-tuned LLM (in isolation):")
    print(classification_report(y_true, y_pure, labels=["RED", "YELLOW", "GREEN"],
                                zero_division=0))

    print("Detailed report — Fine-tuned LLM + Rule safety-net (production):")
    print(classification_report(y_true, y_merge, labels=["RED", "YELLOW", "GREEN"],
                                zero_division=0))

    # Per-case breakdown
    print("\nPer-case results:")
    if y_base is not None:
        print(f"{'ID':<12} {'Expected':<10} {'Rule':>8} {'Base':>8} {'FT':>8} {'FT+Rule':>8} {'Match?':>8}")
        print("-" * 76)
        for case, r, b, p, m in zip(cases, y_rule, y_base, y_pure, y_merge):
            ok = "✓" if m == case["expected_risk"] else "✗"
            print(f"{case['id']:<12} {case['expected_risk']:<10} {r:>8} {b:>8} {p:>8} {m:>8} {ok:>8}")
    else:
        print(f"{'ID':<12} {'Expected':<10} {'Rule':>8} {'FT':>8} {'FT+Rule':>8} {'Match?':>8}")
        print("-" * 76)
        for case, r, p, m in zip(cases, y_rule, y_pure, y_merge):
            ok = "✓" if m == case["expected_risk"] else "✗"
            print(f"{case['id']:<12} {case['expected_risk']:<10} {r:>8} {p:>8} {m:>8} {ok:>8}")

    results = {
        "rule_accuracy":  rule_acc,  "rule_f1":  rule_f1,
        "pure_accuracy":  pure_acc,  "pure_f1":  pure_f1,
        "merge_accuracy": merge_acc, "merge_f1": merge_f1,
    }
    if y_base is not None:
        results.update({"base_accuracy": base_acc, "base_f1": base_f1,
                        "finetune_delta_acc": pure_acc - base_acc,
                        "finetune_delta_f1":  pure_f1  - base_f1})
    return results


if __name__ == "__main__":
    import sys as _argv_sys
    _base = _argv_sys.argv[2] if len(_argv_sys.argv) > 2 else None
    run_evaluation(MODEL_PATH, base_model_path=_base)
