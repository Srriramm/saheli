"""
Translation maps for clinical strings returned by the triage engine.

Danger sign labels are normalised English internally (matching the WHO ANC
checklist), and translated at the API boundary so the mobile UI can display
them verbatim. This keeps the rule-based classifier language-agnostic while
delivering a first-class Tamil/Kannada experience to the ASHA worker.
"""

DANGER_SIGN_TRANSLATIONS = {
    "ta": {
        "severe headache":               "கடுமையான தலைவலி",
        "blurred vision":                "மங்கலான பார்வை",
        "visual disturbance":            "பார்வை மாற்றம்",
        "seeing spots":                  "கண்ணில் புள்ளிகள்",
        "severe bleeding":               "கடுமையான ரத்தப்போக்கு",
        "heavy vaginal bleeding":        "அதிக யோனி ரத்தப்போக்கு",
        "convulsions":                   "வலிப்பு",
        "fits":                          "வலிப்பு",
        "loss of consciousness":         "மயக்கம் / நினைவிழப்பு",
        "no foetal movement":            "குழந்தை அசைவு இல்லை",
        "severe abdominal pain":         "கடுமையான வயிற்று வலி",
        "sudden abdominal pain":         "திடீர் வயிற்று வலி",
        "high fever":                    "அதிக காய்ச்சல்",
        "fever":                         "காய்ச்சல்",
        "fever during pregnancy":        "கர்ப்ப காலத்தில் காய்ச்சல்",
        "headache during pregnancy":     "கர்ப்ப காலத்தில் தலைவலி",
        "vomiting during pregnancy":     "கர்ப்ப காலத்தில் வாந்தி",
        "vaginal bleeding":              "யோனி ரத்தப்போக்கு",
        "oedema":                        "உடல் வீக்கம்",
        "dizziness":                     "தலைச்சுற்றல்",
        "chills":                        "சளி நடுக்கம்",
        "reduced foetal movement":       "குழந்தை அசைவு குறைவு",
        "oedema above ankles":           "கணுக்கால் மேல் வீக்கம்",
        "swelling above ankles":         "கணுக்கால் மேல் வீக்கம்",
        "swollen face":                  "முகத்தில் வீக்கம்",
        "swollen hands":                 "கைகளில் வீக்கம்",
        "jaundice":                      "மஞ்சள் காமாலை",
        "yellowing of eyes":             "கண்களில் மஞ்சள்",
        "persistent headache":           "தொடர்ச்சியான தலைவலி",
        "headache for":                  "நீடித்த தலைவலி",
        "headache since":                "நீடித்த தலைவலி",
        "BP >140/90":                    "உயர் ரத்த அழுத்தம் (>140/90)",
        "high blood pressure":           "உயர் ரத்த அழுத்தம்",
        "haemoglobin <7g/dL":            "கடுமையான இரத்த சோகை (Hb<7)",
        "severe anaemia":                "கடுமையான இரத்த சோகை",
        "severe anaemia (Hb<7)":         "கடுமையான இரத்த சோகை (Hb<7)",
        "fever >38C":                    "அதிக காய்ச்சல் (>38°C)",
        "hypertension (BP>140/90)":      "உயர் ரத்த அழுத்தம் (>140/90)",
        "severe hypertension":           "மிக உயர் ரத்த அழுத்தம்",
    },
    "kn": {
        "severe headache":               "ತೀವ್ರ ತಲೆನೋವು",
        "blurred vision":                "ಮಸುಕು ದೃಷ್ಟಿ",
        "heavy vaginal bleeding":        "ಅಧಿಕ ಯೋನಿ ರಕ್ತಸ್ರಾವ",
        "convulsions":                   "ಫಿಟ್ಸ್",
        "no foetal movement":            "ಶಿಶುವಿನ ಚಲನೆ ಇಲ್ಲ",
        "severe abdominal pain":         "ತೀವ್ರ ಹೊಟ್ಟೆ ನೋವು",
        "high fever":                    "ತೀವ್ರ ಜ್ವರ",
        "fever during pregnancy":        "ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ಜ್ವರ",
        "headache during pregnancy":     "ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ತಲೆನೋವು",
        "swollen face":                  "ಮುಖದಲ್ಲಿ ಊತ",
        "swollen hands":                 "ಕೈಗಳಲ್ಲಿ ಊತ",
        "jaundice":                      "ಕಾಮಾಲೆ",
        "severe anaemia (Hb<7)":         "ತೀವ್ರ ರಕ್ತಹೀನತೆ (Hb<7)",
        "hypertension (BP>140/90)":      "ಅಧಿಕ ರಕ್ತದೊತ್ತಡ (>140/90)",
    },
}


def translate_danger_signs(signs, language: str):
    """Translate a list of English danger-sign labels into the target language.
    Falls back to the English label if no translation exists, so output is
    never empty."""
    if not signs:
        return []
    table = DANGER_SIGN_TRANSLATIONS.get(language, {})
    return [table.get(s, s) for s in signs]


def explain_triage_result(risk_level: str, danger_signs, language: str) -> str:
    """Short ASHA-facing explanation for why this triage level was chosen."""
    translated_signs = translate_danger_signs(danger_signs, language)
    signs_text = ", ".join(translated_signs)

    if language == "ta":
        if risk_level == "RED":
            return f"{signs_text} கண்டறியப்பட்டது. இது கர்ப்ப கால ஆபத்தான அறிகுறி; உடனடி பரிந்துரை தேவை."
        if risk_level == "YELLOW":
            return f"{signs_text} கண்டறியப்பட்டது. 24 மணி நேரத்திற்குள் மருத்துவ பரிசோதனை தேவை."
        return "ஆபத்தான அறிகுறிகள் எதுவும் கண்டறியப்படவில்லை. வழக்கமான கண்காணிப்பை தொடரவும்."

    if language == "kn":
        if risk_level == "RED":
            return f"{signs_text} ಪತ್ತೆಯಾಗಿದೆ. ಇದು ಗರ್ಭಾವಸ್ಥೆಯ ಅಪಾಯಕಾರಿ ಲಕ್ಷಣ; ತಕ್ಷಣ ರೆಫರ್ ಮಾಡಿ."
        if risk_level == "YELLOW":
            return f"{signs_text} ಪತ್ತೆಯಾಗಿದೆ. 24 ಗಂಟೆಯೊಳಗೆ ವೈದ್ಯಕೀಯ ಪರಿಶೀಲನೆ ಬೇಕು."
        return "ಅಪಾಯಕಾರಿ ಲಕ್ಷಣಗಳು ಪತ್ತೆಯಾಗಿಲ್ಲ. ಸಾಮಾನ್ಯ ಮೇಲ್ವಿಚಾರಣೆ ಮುಂದುವರಿಸಿ."

    if risk_level == "RED":
        return f"Detected {signs_text}. This is a pregnancy danger sign and needs immediate referral."
    if risk_level == "YELLOW":
        return f"Detected {signs_text}. Clinical review is recommended within 24 hours."
    return "No danger signs were detected. Continue routine monitoring."
