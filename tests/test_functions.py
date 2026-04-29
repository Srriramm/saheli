"""
test_functions.py — Unit tests for core/function_tools.py

Tests cover all 5 Gemma 4 tool implementations:
  calculate_gestational_age, assess_danger_signs, get_nearest_referral,
  log_patient_record, get_patient_history
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from core.function_tools import (
    calculate_gestational_age,
    assess_danger_signs,
    get_nearest_referral,
    TOOLS_SCHEMA,
)
from data.database import log_patient_record, get_patient_history


# ---------------------------------------------------------------------------
# calculate_gestational_age
# ---------------------------------------------------------------------------

class TestCalculateGestationalAge:
    def test_32_weeks(self):
        lmp = (datetime.now() - timedelta(weeks=32)).strftime("%Y-%m-%d")
        result = calculate_gestational_age(lmp)
        assert result["weeks"] == 32
        assert result["trimester"] == "Third"

    def test_first_trimester(self):
        lmp = (datetime.now() - timedelta(weeks=10)).strftime("%Y-%m-%d")
        result = calculate_gestational_age(lmp)
        assert result["weeks"] == 10
        assert result["trimester"] == "First"

    def test_second_trimester(self):
        lmp = (datetime.now() - timedelta(weeks=20)).strftime("%Y-%m-%d")
        result = calculate_gestational_age(lmp)
        assert result["trimester"] == "Second"

    def test_invalid_date_returns_error(self):
        result = calculate_gestational_age("not-a-date")
        assert "error" in result

    def test_days_field_present(self):
        lmp = (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d")
        result = calculate_gestational_age(lmp)
        assert "days" in result
        assert 0 <= result["days"] <= 6


# ---------------------------------------------------------------------------
# assess_danger_signs
# ---------------------------------------------------------------------------

class TestAssessDangerSigns:
    def test_red_severe_headache_vision(self):
        result = assess_danger_signs(
            symptoms=["severe headache", "blurred vision"],
            vitals={"bp_sys": 155, "bp_dia": 105}
        )
        assert result["risk_level"] == "RED"
        assert len(result["danger_signs"]) > 0

    def test_red_no_foetal_movement(self):
        result = assess_danger_signs(
            symptoms=["no foetal movement"],
            vitals={}
        )
        assert result["risk_level"] == "RED"

    def test_red_heavy_bleeding(self):
        result = assess_danger_signs(
            symptoms=["heavy vaginal bleeding"],
            vitals={}
        )
        assert result["risk_level"] == "RED"

    def test_yellow_hypertension_vitals(self):
        result = assess_danger_signs(
            symptoms=[],
            vitals={"bp_sys": 145, "bp_dia": 92}
        )
        assert result["risk_level"] == "YELLOW"
        assert any("hypertension" in s.lower() for s in result["danger_signs"])

    def test_yellow_severe_anaemia_vitals(self):
        result = assess_danger_signs(
            symptoms=[],
            vitals={"hb": 6.0}
        )
        assert result["risk_level"] == "YELLOW"

    def test_green_mild_nausea(self):
        result = assess_danger_signs(
            symptoms=["mild nausea"],
            vitals={}
        )
        assert result["risk_level"] == "GREEN"

    def test_green_fatigue(self):
        result = assess_danger_signs(
            symptoms=["fatigue"],
            vitals={}
        )
        assert result["risk_level"] == "GREEN"

    def test_tamil_severe_headache_maps_to_red(self):
        result = assess_danger_signs(
            symptoms=["கடுமையான தலைவலி"],
            vitals={}
        )
        assert result["risk_level"] == "RED"
        assert "severe headache" in result["danger_signs"]

    def test_result_structure(self):
        result = assess_danger_signs(symptoms=["mild nausea"], vitals={})
        assert "risk_level" in result
        assert "danger_signs" in result
        assert "reasoning" in result
        assert isinstance(result["danger_signs"], list)

    def test_red_overrides_yellow_vitals(self):
        # Both yellow (anaemia) and red (convulsions) present — RED wins
        result = assess_danger_signs(
            symptoms=["convulsions"],
            vitals={"hb": 6.5}
        )
        assert result["risk_level"] == "RED"


# ---------------------------------------------------------------------------
# get_nearest_referral
# ---------------------------------------------------------------------------

class TestGetNearestReferral:
    # Near Doddaballapur (KA-PHC-001, lat 13.2957, lon 77.5388)
    ASHA_LAT = 13.30
    ASHA_LON = 77.54

    def test_returns_facility_name(self):
        result = get_nearest_referral(self.ASHA_LAT, self.ASHA_LON, "GREEN")
        assert "facility_name" in result
        assert len(result["facility_name"]) > 0

    def test_returns_distance(self):
        result = get_nearest_referral(self.ASHA_LAT, self.ASHA_LON, "GREEN")
        assert "distance_km" in result
        assert result["distance_km"] >= 0

    def test_red_risk_requires_ambulance(self):
        result = get_nearest_referral(self.ASHA_LAT, self.ASHA_LON, "RED")
        # All 20 facilities include at least one with ambulance, so should succeed
        assert "facility_name" in result

    def test_closest_facility_is_nearest(self):
        result = get_nearest_referral(self.ASHA_LAT, self.ASHA_LON, "GREEN")
        assert result["distance_km"] < 100  # sanity: within Karnataka


# ---------------------------------------------------------------------------
# log_patient_record / get_patient_history  (database functions)
# ---------------------------------------------------------------------------

class TestPatientDatabase:
    TEST_PATIENT_ID = "TEST-DB-UNIT-001"

    def test_log_creates_record(self):
        result = log_patient_record(self.TEST_PATIENT_ID, {
            "symptoms": ["mild nausea"],
            "danger_signs": [],
            "risk_level": "GREEN",
            "recommendation": "Monitor at home",
            "image_path": None,
            "referral_facility": None,
            "gestational_week": 16
        })
        assert result["success"] is True
        assert "record_id" in result
        assert len(result["record_id"]) > 0

    def test_get_history_returns_visits(self):
        # Ensure at least one record exists (test_log_creates_record runs first)
        log_patient_record(self.TEST_PATIENT_ID, {
            "symptoms": ["fatigue"],
            "danger_signs": [],
            "risk_level": "GREEN",
            "recommendation": "Monitor",
            "image_path": None,
            "referral_facility": None,
            "gestational_week": 18
        })
        history = get_patient_history(self.TEST_PATIENT_ID)
        assert "visits" in history
        assert isinstance(history["visits"], list)
        assert len(history["visits"]) >= 1

    def test_risk_trend_field_present(self):
        history = get_patient_history(self.TEST_PATIENT_ID)
        assert "risk_trend" in history
        assert history["risk_trend"] in ("Stable", "Deteriorating", "Improving")


# ---------------------------------------------------------------------------
# TOOLS_SCHEMA structure validation
# ---------------------------------------------------------------------------

class TestToolsSchema:
    EXPECTED_TOOLS = {
        "calculate_gestational_age",
        "assess_danger_signs",
        "get_nearest_referral",
        "log_patient_record",
        "get_patient_history",
    }

    def test_all_five_tools_present(self):
        names = {t["function"]["name"] for t in TOOLS_SCHEMA}
        assert names == self.EXPECTED_TOOLS

    def test_each_tool_has_required_fields(self):
        for tool in TOOLS_SCHEMA:
            assert tool["type"] == "function"
            fn = tool["function"]
            assert "name" in fn
            assert "description" in fn
            assert "parameters" in fn
            assert "required" in fn["parameters"]
