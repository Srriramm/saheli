"""
test_triage.py — Unit tests for the TriageEngine and TriageResult.

These tests use a mocked GemmaRunner so they run without the GGUF model file,
making them suitable for CI and quick local verification.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import asdict

from core.triage_engine import TriageEngine, TriageResult
from core.risk_classifier import classify_risk, merge_risk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_engine(mock_output: dict = None):
    """Return a TriageEngine whose GemmaRunner is fully mocked."""
    engine = TriageEngine.__new__(TriageEngine)
    runner = MagicMock()
    runner.call_with_tools.return_value = mock_output or {
        "name": "assess_danger_signs",
        "arguments": {"symptoms": ["mild nausea"], "vitals": {}}
    }
    runner.generate_with_image.return_value = json.dumps(mock_output or {
        "name": "assess_danger_signs",
        "arguments": {"symptoms": ["mild nausea"], "vitals": {}}
    })
    runner._format_tool_prompt.side_effect = lambda p, t: p
    engine.runner = runner
    return engine


# ---------------------------------------------------------------------------
# TriageResult dataclass
# ---------------------------------------------------------------------------

class TestTriageResult:
    def test_fields_present(self):
        result = TriageResult(
            risk_level="GREEN",
            spoken_response="All fine.",
            referral_info=None,
            patient_record_id="REC-001",
            danger_signs_found=[],
            image_analysis_summary="No image."
        )
        d = asdict(result)
        assert "risk_level" in d
        assert "spoken_response" in d
        assert "referral_info" in d
        assert "patient_record_id" in d
        assert "danger_signs_found" in d
        assert "image_analysis_summary" in d


# ---------------------------------------------------------------------------
# TriageEngine._build_system_prompt
# ---------------------------------------------------------------------------

class TestBuildSystemPrompt:
    def test_english_prompt(self):
        engine = _make_engine()
        prompt = engine._build_system_prompt("en")
        assert "Saheli" in prompt
        assert "ASHA" in prompt

    def test_kannada_prompt(self):
        engine = _make_engine()
        prompt = engine._build_system_prompt("kn")
        assert len(prompt) > 20

    def test_unknown_language_falls_back(self):
        engine = _make_engine()
        prompt = engine._build_system_prompt("xx")
        # Should fall back to DEFAULT_LANGUAGE (kn) without raising
        assert len(prompt) > 20


# ---------------------------------------------------------------------------
# TriageEngine._execute_function_calls
# ---------------------------------------------------------------------------

class TestExecuteFunctionCalls:
    def test_assess_danger_signs_route(self):
        engine = _make_engine()
        output = {
            "name": "assess_danger_signs",
            "arguments": {"symptoms": ["severe headache", "blurred vision"], "vitals": {"bp_sys": 155, "bp_dia": 105}}
        }
        result = engine._execute_function_calls(output, "severe headache")
        assert result["risk_level"] == "RED"

    def test_green_symptoms(self):
        engine = _make_engine()
        output = {
            "name": "assess_danger_signs",
            "arguments": {"symptoms": ["mild nausea"], "vitals": {}}
        }
        result = engine._execute_function_calls(output, "mild nausea")
        assert result["risk_level"] == "GREEN"

    def test_none_output_returns_green_default(self):
        engine = _make_engine()
        result = engine._execute_function_calls(None, "")
        assert result["risk_level"] == "GREEN"


# ---------------------------------------------------------------------------
# TriageEngine._format_response
# ---------------------------------------------------------------------------

class TestFormatResponse:
    def test_red_response_english(self):
        engine = _make_engine()
        assessment = {"risk_level": "RED", "danger_signs": ["convulsions"], "reasoning": ""}
        resp = engine._format_response(assessment, "en", None)
        assert "ambulance" in resp.lower() or "danger" in resp.lower()

    def test_green_response_kannada(self):
        engine = _make_engine()
        assessment = {"risk_level": "GREEN", "danger_signs": [], "reasoning": ""}
        resp = engine._format_response(assessment, "kn", None)
        assert len(resp) > 5

    def test_referral_appended_for_yellow(self):
        engine = _make_engine()
        assessment = {"risk_level": "YELLOW", "danger_signs": [], "reasoning": ""}
        referral = {"facility_name": "PHC Doddaballapur", "distance_km": 4.2}
        resp = engine._format_response(assessment, "en", referral)
        assert "PHC Doddaballapur" in resp

    def test_referral_appended_in_tamil(self):
        engine = _make_engine()
        assessment = {"risk_level": "RED", "danger_signs": ["severe headache"], "reasoning": ""}
        referral = {"facility_name": "GH Hosur", "distance_km": 8.4}
        resp = engine._format_response(assessment, "ta", referral)
        assert "GH Hosur" in resp
        assert "கி.மீ" in resp


# ---------------------------------------------------------------------------
# Full run_triage integration (mocked runner + real DB/tools)
# ---------------------------------------------------------------------------

class TestRunTriage:
    def test_green_triage(self, tmp_path):
        engine = _make_engine({
            "name": "assess_danger_signs",
            "arguments": {"symptoms": ["mild nausea"], "vitals": {}}
        })
        with patch("core.triage_engine.log_patient_record", return_value={"record_id": "TEST-REC"}):
            result = engine.run_triage(
                patient_id="TEST-001",
                language="en",
                voice_input="Patient has mild nausea at 12 weeks."
            )
        assert result.risk_level == "GREEN"
        assert isinstance(result.spoken_response, str)
        assert result.referral_info is None

    def test_red_triage_triggers_referral(self):
        engine = _make_engine({
            "name": "assess_danger_signs",
            "arguments": {
                "symptoms": ["severe headache", "blurred vision"],
                "vitals": {"bp_sys": 160, "bp_dia": 110}
            }
        })
        with patch("core.triage_engine.log_patient_record", return_value={"record_id": "TEST-REC"}), \
             patch("core.triage_engine.get_nearest_referral", return_value={
                 "facility_name": "PHC Doddaballapur",
                 "distance_km": 3.1,
                 "phone": "080-27631234"
             }):
            result = engine.run_triage(
                patient_id="TEST-002",
                language="en",
                voice_input="Severe headache and blurred vision at 32 weeks."
            )
        assert result.risk_level == "RED"
        assert result.referral_info is not None
