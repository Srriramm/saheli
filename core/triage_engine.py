import sys as _sys, os as _os
_project_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_sys.path.insert(0, _project_root)
for _k in list(_sys.modules.keys()):
    if _k == 'models' or _k.startswith('models.'):
        del _sys.modules[_k]

import json
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

from models.gemma_runner import GemmaRunner
from core.function_tools import (
    TOOLS_SCHEMA,
    calculate_gestational_age,
    assess_danger_signs,
    get_nearest_referral,
    log_patient_record,
    get_patient_history
)
from core.prompt_templates import SYSTEM_PROMPTS
from core.risk_classifier import classify_risk, merge_risk
from config.settings import DEFAULT_LANGUAGE


@dataclass
class TriageResult:
    risk_level: str
    spoken_response: str
    referral_info: Optional[Dict]
    patient_record_id: str
    danger_signs_found: list
    image_analysis_summary: str
    reasoning: str = ""
    location_source: str = "fallback"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class TriageEngine:
    """The brain of Saheli. Orchestrates multimodal generation, function routing, and UI formatting."""

    def __init__(self, model_path: str):
        self.runner = GemmaRunner(model_path=model_path)

    def _build_system_prompt(self, language: str) -> str:
        """Load language-appropriate system prompt from prompt_templates.py."""
        return SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS[DEFAULT_LANGUAGE])

    def _run_multimodal_assessment(self, transcript: str, image_path: str) -> Dict:
        """Combine voice transcript + image in one Gemma 4 call. Attempt structured parsing."""
        prompt = f"{transcript}\n\nPlease determine if the patient's symptoms or image indicate RED, YELLOW, or GREEN risk level."
        full_prompt = self.runner._format_tool_prompt(prompt, TOOLS_SCHEMA)
        
        output = self.runner.generate_with_image(full_prompt, image_path)
        
        try:
            clean_output = output.strip()
            if clean_output.startswith("```json"):
                clean_output = clean_output[7:-3].strip()
            elif clean_output.startswith("```"):
                clean_output = clean_output[3:-3].strip()
            return json.loads(clean_output)
        except json.JSONDecodeError:
            # Fallback if the vision model failed to structure its JSON correctly
            logging.warning(f"Failed to parse multimodal JSON: {output}")
            return {"name": "assess_danger_signs", "arguments": {"symptoms": [transcript]}}

    def _execute_function_calls(self, model_output: Dict, transcript: str) -> Dict:
        """Parse and execute any tool calls in model output."""
        result = {"risk_level": "GREEN", "danger_signs": [], "reasoning": "Normal."}
        
        if not model_output:
            return result
            
        function_name = model_output.get("name")
        args = model_output.get("arguments", model_output.get("parameters", {}))
        
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {"symptoms": [transcript]}

        # Route to exact function implementation
        if function_name == "assess_danger_signs":
            result = assess_danger_signs(args.get("symptoms", [transcript]), args.get("vitals", {}))
        elif function_name == "calculate_gestational_age":
            result = calculate_gestational_age(args.get("lmp_date", "2025-01-01"))
            # chain to danger signs default assessing if needed
        
        return result

    def _format_response(self, assessment: Dict, language: str, referral: Optional[Dict]) -> str:
        """Format result text for TTS and UI display."""
        risk = assessment.get("risk_level", "GREEN")
        
        # Simple local language mapping for the core response loop
        responses = {
            "en": {
                "RED": "Danger signs detected. Please call an ambulance immediately.",
                "YELLOW": "Warning signs detected. Refer to the nearest clinic within 24 hours.",
                "GREEN": "The symptoms appear normal for pregnancy. Continue standard monitoring."
            },
            "kn": {
                "RED": "ಅಪಾಯದ ಚಿಹ್ನೆಗಳು ಕಂಡುಬಂದಿವೆ. ದಯವಿಟ್ಟು ತಕ್ಷಣ ಆಂಬ್ಯುಲೆನ್ಸ್‌ಗೆ ಕರೆ ಮಾಡಿ.",
                "YELLOW": "ಎಚ್ಚರಿಕೆ ಚಿಹ್ನೆಗಳು ಕಂಡುಬಂದಿವೆ. 24 ಗಂಟೆಗಳ ಒಳಗೆ ಸಮೀಪದ ಕ್ಲಿನಿಕ್ ಅನ್ನು ಸಂಪರ್ಕಿಸಿ.",
                "GREEN": "ರೋಗಲಕ್ಷಣಗಳು ಗರ್ಭಧಾರಣೆಗೆ ಸಾಮಾನ್ಯವೆಂದು ತೋರುತ್ತದೆ. ಚಿಂತಿಸಬೇಡಿ."
            },
            "ta": {
                "RED": "ஆபத்தான அறிகுறிகள் உள்ளன. உடனே ஆம்புலன்ஸை அழைத்து மருத்துவமனைக்கு செல்லவும்.",
                "YELLOW": "எச்சரிக்கை அறிகுறிகள் உள்ளன. 24 மணி நேரத்திற்குள் அருகிலுள்ள சுகாதார மையத்திற்கு செல்லவும்.",
                "GREEN": "அறிகுறிகள் கர்ப்ப காலத்தில் சாதாரணமாக தெரிகின்றன. வழக்கமான கண்காணிப்பை தொடரவும்."
            }
        }

        referral_suffix = {
            "en": "Nearest facility: {facility} ({distance} km away).",
            "kn": "{facility} ({distance} ಕಿ.ಮೀ ದೂರ) ಗೆ ತೆರಳಿ.",
            "ta": "அருகிலுள்ள மையம்: {facility} ({distance} கி.மீ தொலைவில்).",
        }
        
        lang_dict = responses.get(language, responses["en"])
        base_resp = lang_dict.get(risk, lang_dict["GREEN"])
        
        if referral and risk in ["RED", "YELLOW"]:
            suffix_template = referral_suffix.get(language, referral_suffix["en"])
            base_resp += " " + suffix_template.format(
                facility=referral.get("facility_name", ""),
                distance=referral.get("distance_km", 0),
            )
            
        return base_resp

    def run_triage(self, patient_id: str, language: str, voice_input: Optional[str] = None, image_path: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None) -> TriageResult:
        """Main entry point representing a full consultation loop."""
        sys_prompt = self._build_system_prompt(language)
        input_text = f"System: {sys_prompt}\n\nASHA Input: {voice_input or ''}"
        
        # 1. LLM Generation (Text vs Vision paths)
        if image_path:
            model_output = self._run_multimodal_assessment(input_text, image_path)
            image_summary = "Image processed by vision layer."
        else:
            model_output = self.runner.call_with_tools(
                voice_input or "", TOOLS_SCHEMA, system=sys_prompt
            )
            image_summary = "No image provided."
            
            # Defensive fallback
            if not model_output and voice_input:
                model_output = {"name": "assess_danger_signs", "arguments": {"symptoms": [voice_input]}}

        # 2. Execute local reasoning tools
        assessment = self._execute_function_calls(model_output, voice_input or "No symptoms reported")

        # Always run the raw ASHA text through the deterministic checklist too.
        # This protects Tamil demo phrases if the model paraphrases them too softly.
        raw_assessment = assess_danger_signs([voice_input], {}) if voice_input else {
            "risk_level": "GREEN",
            "danger_signs": [],
            "reasoning": "",
        }
        assessment["risk_level"] = merge_risk(
            assessment.get("risk_level", "GREEN"),
            raw_assessment.get("risk_level", "GREEN"),
        )
        assessment["danger_signs"] = list(dict.fromkeys(
            assessment.get("danger_signs", []) + raw_assessment.get("danger_signs", [])
        ))
        if raw_assessment.get("risk_level") in ["RED", "YELLOW"]:
            assessment["reasoning"] = raw_assessment.get("reasoning", assessment.get("reasoning", ""))

        # 3. Safety-net: rule-based classifier can only raise, never lower, LLM output
        llm_risk = assessment.get("risk_level", "GREEN")
        danger_signs = assessment.get("danger_signs", [])
        vitals = model_output.get("arguments", {}).get("vitals", {}) if model_output else {}
        rule_risk = classify_risk(danger_signs, vitals)
        risk_level = merge_risk(llm_risk, rule_risk)
        assessment["risk_level"] = risk_level
        
        referral_info = None
        if risk_level in ["YELLOW", "RED"]:
            lat = latitude  if latitude  is not None else 13.29
            lng = longitude if longitude is not None else 77.53
            referral_info = get_nearest_referral(lat, lng, risk_level)
        else:
            lat = latitude
            lng = longitude

        location_source = "gps" if latitude is not None and longitude is not None else "fallback"
            
        # 4. Save to Offline DB
        log_res = log_patient_record(patient_id, {
            "symptoms": [voice_input],
            "danger_signs": danger_signs,
            "risk_level": risk_level,
            "recommendation": assessment.get("reasoning", ""),
            "image_path": image_path,
            "referral_facility": referral_info.get("facility_name") if referral_info else None,
            "gestational_week": 0
        })
        
        # 5. Format audio output
        spoken = self._format_response(assessment, language, referral_info)
        
        logging.info(f"Triage Complete for {patient_id} -> RISK: {risk_level}")

        return TriageResult(
            risk_level=risk_level,
            spoken_response=spoken,
            referral_info=referral_info,
            patient_record_id=log_res.get("record_id", "ERROR_DB"),
            danger_signs_found=danger_signs,
            image_analysis_summary=image_summary,
            reasoning=assessment.get("reasoning", ""),
            location_source=location_source,
            latitude=lat,
            longitude=lng,
        )
