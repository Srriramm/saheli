import json
import os
from datetime import datetime
from geopy.distance import geodesic
from typing import Dict, List
from data.database import log_patient_record, get_patient_history

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WHO_PATH      = os.path.join(_ROOT, "data", "who_anc_checklist.json")
_REFERRAL_PATH = os.path.join(_ROOT, "data", "referral_data.json")

def load_who_guidelines() -> Dict:
    with open(_WHO_PATH, "r") as f:
        return json.load(f)

def load_referrals() -> List[Dict]:
    with open(_REFERRAL_PATH, "r") as f:
        return json.load(f)

# === Gemma 4 Function Implementations ===

def calculate_gestational_age(lmp_date: str) -> Dict:
    """
    Computes precise gestational weeks from Last Menstrual Period.
    Expects format: YYYY-MM-DD
    """
    try:
        lmp = datetime.strptime(lmp_date, "%Y-%m-%d")
        delta = datetime.now() - lmp
        weeks = delta.days // 7
        days = delta.days % 7
        
        trimester = "First"
        if weeks > 13: trimester = "Second"
        if weeks > 28: trimester = "Third"
        
        return {"weeks": weeks, "days": days, "trimester": trimester}
    except ValueError:
        return {"error": "Invalid date format, expect YYYY-MM-DD"}

def _normalise(text: str) -> str:
    """Normalise spelling variants and synonyms for robust keyword matching."""
    t = text.lower()
    # American → British spelling
    t = t.replace("fetal", "foetal").replace("hemoglobin", "haemoglobin")
    t = t.replace("anemia", "anaemia").replace("hemorrhage", "haemorrhage")
    t = t.replace("edema", "oedema")
    # Synonym mapping
    t = t.replace("baby movement", "foetal movement")
    t = t.replace("baby kick", "foetal movement")
    t = t.replace("baby not moving", "no foetal movement")
    t = t.replace("no kicks", "no foetal movement")
    t = t.replace("fitting", "convulsions")
    t = t.replace("seizure", "convulsions")
    t = t.replace("pale eyes", "jaundice")
    t = t.replace("yellow eyes", "jaundice")
    t = t.replace("yellowing of eyes", "jaundice")
    # Tamil demo phrases from ASHA speech; map them into the English checklist.
    tamil_negations = [
        "ரத்தப்போக்கு இல்லை",
        "இரத்தப்போக்கு இல்லை",
        "காய்ச்சல் இல்லை",
        "தலைவலி இல்லை",
        "வயிற்று வலி இல்லை",
        "வீக்கம் இல்லை",
        "வலிப்பு இல்லை",
    ]
    for phrase in tamil_negations:
        t = t.replace(phrase, " ")

    tamil_phrase_map = {
        "கடுமையான தலைவலி": "severe headache",
        "தலைவலி": "headache",
        "கண் மங்கலாக": "blurred vision",
        "கண் மங்கல்": "blurred vision",
        "பார்வை மங்கல்": "blurred vision",
        "மங்கலாக தெரிகிறது": "blurred vision",
        "ரத்தப்போக்கு": "heavy vaginal bleeding",
        "அதிக ரத்தப்போக்கு": "heavy vaginal bleeding",
        "வலிப்பு": "convulsions",
        "மயக்கம்": "loss of consciousness",
        "நினைவிழப்பு": "loss of consciousness",
        "குழந்தை அசைவில்லை": "no foetal movement",
        "குழந்தை நகரவில்லை": "no foetal movement",
        "வயிற்று வலி": "severe abdominal pain",
        "கடுமையான வயிற்று வலி": "severe abdominal pain",
        "காய்ச்சல்": "high fever",
        "சளி நடுக்கம்": "chills",
        "நடுக்கம்": "chills",
        "கால்களில் வீக்கம்": "swelling above ankles",
        "கால் வீக்கம்": "swelling above ankles",
        "முகம் வீக்கம்": "swollen face",
        "கைகள் வீக்கம்": "swollen hands",
        "மஞ்சள் கண்": "jaundice",
        "கண் மஞ்சள்": "jaundice",
        "வாந்தி உணர்வு": "mild nausea",
        "வாந்தி": "mild nausea",
    }
    for tamil, english in tamil_phrase_map.items():
        t = t.replace(tamil, english)
    # Strip articles so "above the ankles" matches "above ankles"
    t = t.replace(" the ", " ").replace(" a ", " ").replace(" an ", " ")
    return t


def assess_danger_signs(symptoms: List[str], vitals: Dict = None) -> Dict:
    """
    Evaluates reported symptoms and vitals against the WHO ANC danger signs checklist.
    vitals (optional dict) example: {"bp_sys": 150, "bp_dia": 100, "hb": 6.0}
    """
    who = load_who_guidelines()

    found_signs = []
    risk_level = "GREEN"
    reasoning = "Routine monitoring. Symptoms typical for pregnancy."

    # Process Vitals natively
    vitals = vitals or {}
    if vitals.get("hb", 10.0) < 7.0:
        found_signs.append("severe anaemia (Hb<7)")
        risk_level = "YELLOW"

    if vitals.get("bp_sys", 120) > 140 or vitals.get("bp_dia", 80) > 90:
        found_signs.append("hypertension (BP>140/90)")
        risk_level = "YELLOW"

    if vitals.get("bp_sys", 120) >= 160 or vitals.get("bp_dia", 80) >= 110:
        found_signs.append("severe hypertension")
        risk_level = "RED"

    # Evaluate explicit text symptoms (normalise spelling before matching)
    norm_symptoms = [_normalise(s) for s in symptoms]
    for sym_group in who["RED"]:
        if any(_normalise(sym_group) in s for s in norm_symptoms):
            found_signs.append(sym_group)
            risk_level = "RED"
            reasoning = "Immediate referral required. Red danger sign detected."

    if risk_level != "RED":
        for sym_group in who["YELLOW"]:
            if any(_normalise(sym_group) in s for s in norm_symptoms):
                found_signs.append(sym_group)
                risk_level = "YELLOW"
                reasoning = "Refer to facility within 24 hours."

    # Additional fallback heuristics: catch single-word symptom mentions that the
    # WHO checklist phrasings miss (e.g. "fever" without "high", "headache"
    # without "severe"). These are still flagged YELLOW because in pregnancy
    # any persistent fever or headache warrants a clinic visit.
    if risk_level == "GREEN":
        joined = " ".join(norm_symptoms)
        soft_yellow = {
            "fever":     "fever during pregnancy",
            "headache":  "headache during pregnancy",
            "vomiting":  "vomiting during pregnancy",
            "bleeding":  "vaginal bleeding",
            "swelling":  "oedema",
            "dizzy":     "dizziness",
            "dizziness": "dizziness",
        }
        for keyword, label in soft_yellow.items():
            if keyword in joined:
                found_signs.append(label)
                risk_level = "YELLOW"
                reasoning = "Refer to facility within 24 hours — symptom needs clinical review."
                break

    return {
        "risk_level": risk_level,
        "danger_signs": found_signs,
        "reasoning": reasoning
    }

def get_nearest_referral(latitude: float, longitude: float, risk_level: str) -> Dict:
    """
    Maps ASHA's GPS location to the nearest appropriate offline facility via geopy.
    RED risk enforces facilities with ambulances.
    """
    facilities = load_referrals()
    asha_coord = (latitude, longitude)
    
    best_facility = None
    min_dist = float('inf')

    for fac in facilities:
        # Mandatory requirement if risk is RED
        if risk_level == "RED" and not fac.get("has_ambulance", False):
            continue
            
        fac_coord = (fac["latitude"], fac["longitude"])
        dist_km = geodesic(asha_coord, fac_coord).km
        
        if dist_km < min_dist:
            min_dist = dist_km
            best_facility = fac

    if not best_facility:
        return {"error": "No appropriate facility found."}
        
    return {
        "facility_name": best_facility["name"],
        "distance_km": round(min_dist, 2),
        "phone": best_facility["phone"],
        "ambulance": best_facility.get("emergency_phone", "108")
    }

# === Gemma 4 Function Definitions Schema ===
# These JSON schemas get passed into GemmaRunner so the LLM knows what to call.

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "calculate_gestational_age",
            "description": "Calculate exact weeks pregnant from last menstrual period date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lmp_date": {"type": "string", "description": "Last menstrual period date formatted as YYYY-MM-DD"}
                },
                "required": ["lmp_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assess_danger_signs",
            "description": "Evaluates symptoms and vitals against WHO guidelines to determine maternal risk level.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symptoms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of qualitative symptoms reported by the patient"
                    },
                    "vitals": {
                        "type": "object",
                        "description": "Optional vitals like bp_sys, bp_dia, hb"
                    }
                },
                "required": ["symptoms"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_nearest_referral",
            "description": "Locate the nearest offline primary health center based on patient risk tier.",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number", "description": "Current ASHA location latitude"},
                    "longitude": {"type": "number", "description": "Current ASHA location longitude"},
                    "risk_level": {"type": "string", "enum": ["GREEN", "YELLOW", "RED"], "description": "Computed risk level from assessment"}
                },
                "required": ["latitude", "longitude", "risk_level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_patient_record",
            "description": "Saves current consultation details into the local SQLite offline database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string", "description": "Unique ID of the patient (Village-Name-Num)"},
                    "visit_data": {
                        "type": "object",
                        "description": "Dictionary of risk_level, symptoms, and recommendations"
                    }
                },
                "required": ["patient_id", "visit_data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patient_history",
            "description": "Loads past records for a patient to determine longitudinal risk trends.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {"type": "string"}
                },
                "required": ["patient_id"]
            }
        }
    }
]
