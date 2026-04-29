"""
languages.py — Language codes, display names, and TTS voice mappings for Saheli.

Supported languages: Hindi, Kannada, Telugu, Tamil, English.
Voice IDs are espeak voice names (Linux/Raspberry Pi).
On Windows with pyttsx3/SAPI5 the voice is matched by language prefix in speaker.py.
"""

# ISO 639-1 code → human-readable display name (shown in UI selector)
LANGUAGE_DISPLAY_NAMES = {
    "hi": "हिंदी (Hindi)",
    "kn": "ಕನ್ನಡ (Kannada)",
    "te": "తెలుగు (Telugu)",
    "ta": "தமிழ் (Tamil)",
    "en": "English",
}

# ISO 639-1 code → espeak voice name (used on Linux / Raspberry Pi)
ESPEAK_VOICES = {
    "hi": "hi",
    "kn": "kn",
    "te": "te",
    "ta": "ta",
    "en": "en-us",
}

# ISO 639-1 code → pyttsx3 / SAPI5 voice name fragment (Windows fallback)
PYTTSX3_VOICE_HINTS = {
    "hi": "Hindi",
    "kn": "Kannada",
    "te": "Telugu",
    "ta": "Tamil",
    "en": "English",
}

# Whisper language codes (mostly the same as ISO 639-1 but listed explicitly)
WHISPER_LANGUAGE_CODES = {
    "hi": "hi",
    "kn": "kn",
    "te": "te",
    "ta": "ta",
    "en": "en",
}

# Default fallback when language is unknown or not supported
DEFAULT_LANGUAGE = "ta"
