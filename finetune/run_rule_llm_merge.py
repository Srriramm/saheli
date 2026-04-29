"""
run_rule_llm_merge.py

Runs Rule-only and LLM+Rule rows only.
Pure-LLM results are hard-coded from the previous run to save time.
"""
import sys as _sys, os as _os
_project_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _project_root)

import json
import logging
from sklearn.metrics import f1_score, accuracy_score, classification_report
from core.function_tools import assess_danger_signs
from core.risk_classifier import classify_risk, merge_risk
from core.triage_engine import TriageEngine
from models.gemma_runner import GemmaRunner
from config.settings import MODEL_PATH

# ── Pure-LLM results from previous run (saved to avoid re-running) ────────────
PURE_LLM_RESULTS = {
    "CASE-001": "YELLOW",
    "CASE-002": "RED",
    "CASE-003": "RED",
    "CASE-004": "GREEN",
    "CASE-005": "YELLOW",
    "CASE-006": "GREEN",
    "CASE-007": "YELLOW",
    "CASE-008": "RED",
    "CASE-009": "RED",
    "CASE-010": "RED",
    "CASE-011": "YELLOW",
    "CASE-012": "GREEN",
    "CASE-013": "GREEN",
    "CASE-014": "GREEN",
    "CASE-015": "RED",
    "CASE-016": "YELLOW",
    "CASE-017": "GREEN",
    "CASE-018": "YELLOW",
    "CASE-019": "RED",
    "CASE-020": "YELLOW",
}


def load_test_cases():
    with open("./tests/sample_cases.json") as f:
        return json.load(f)


def _build_voice_sim(case):
    vitals = case.get("vitals", {})
    vitals_str = ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in vitals.items())
    msg = f"Patient has {case['symptoms']} at {case['weeks']} weeks."
    if vitals_str:
        msg += f" Vitals: {vitals_str}."
    return msg


def _rule_predict(case):
    symptoms_list = [s.strip() for s in case["symptoms"].replace(",", ";").split(";")]
    assessment = assess_danger_signs(symptoms_list, case.get("vitals", {}))
    rule_risk = classify_risk(assessment["danger_signs"], case.get("vitals", {}))
    return merge_risk(assessment["risk_level"], rule_risk)


def main():
    cases = load_test_cases()
    y_true  = [c["expected_risk"] for c in cases]
    y_pure  = [PURE_LLM_RESULTS[c["id"]] for c in cases]

    # Row 1: Rule-only
    y_rule = [_rule_predict(c) for c in cases]

    # Row 2: LLM + Rule
    print("Loading GGUF model...", flush=True)
    runner = GemmaRunner(model_path=MODEL_PATH)
    engine = TriageEngine.__new__(TriageEngine)
    engine.runner = runner

    print(f"Running LLM+Rule predictions (0/{len(cases)})...", flush=True)
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
            logging.error(f"{case['id']} failed: {e}")
            y_merge.append("ERROR")
        print(f"  [{i+1:02d}/{len(cases)}] {case['id']} → {y_merge[-1]}", flush=True)

    # Metrics
    def _metrics(y_pred):
        acc = accuracy_score(y_true, y_pred)
        f1  = f1_score(y_true, y_pred, average="weighted", zero_division=0)
        return acc, f1

    rule_acc,  rule_f1  = _metrics(y_rule)
    pure_acc,  pure_f1  = _metrics(y_pure)
    merge_acc, merge_f1 = _metrics(y_merge)

    print("\n" + "=" * 64)
    print("  SAHELI EVALUATION BENCHMARKS")
    print("=" * 64)
    print(f"{'Metric':<25} {'Rule-only':>12} {'Pure LLM':>12} {'LLM+Rule':>12}")
    print("-" * 64)
    print(f"{'Accuracy':<25} {rule_acc*100:>11.1f}% {pure_acc*100:>11.1f}% {merge_acc*100:>11.1f}%")
    print(f"{'F1 (weighted)':<25} {rule_f1*100:>11.1f}% {pure_f1*100:>11.1f}% {merge_f1*100:>11.1f}%")
    print("=" * 64)

    print("\nDetailed report — Pure LLM:")
    print(classification_report(y_true, y_pure, labels=["RED","YELLOW","GREEN"], zero_division=0))

    print("Detailed report — LLM + Rule safety-net:")
    print(classification_report(y_true, y_merge, labels=["RED","YELLOW","GREEN"], zero_division=0))

    print(f"\n{'ID':<12} {'Expected':<10} {'Rule':>8} {'Pure':>8} {'Merge':>8} {'OK?':>5}")
    print("-" * 55)
    for case, r, p, m in zip(cases, y_rule, y_pure, y_merge):
        ok = "✓" if m == case["expected_risk"] else "✗"
        print(f"{case['id']:<12} {case['expected_risk']:<10} {r:>8} {p:>8} {m:>8} {ok:>5}")


if __name__ == "__main__":
    main()
