import pyttsx3
import logging
from config.settings import DEFAULT_LANGUAGE

# Map languages to TTS voices (espeak/sapi5). Note: Voice IDs differ by OS.
# Usually to get native indicating languages, 'hi', 'kn', 'ta' will use specific indices.
TTS_VOICES = {
    "en": "en",
    "hi": "hi",
    "kn": "kn",
    "te": "te",
    "ta": "ta"
}

def speak(text: str, language_code: str = DEFAULT_LANGUAGE) -> None:
    """Uses pyttsx3/espeak to loudly speak the result in ASHA's selected language."""
    engine = pyttsx3.init()
    
    # Try fetching available voices and match the prefix
    # If the system doesn't have the specific language, fallback to English or default.
    voices = engine.getProperty('voices')
    target_voice_id = None
    
    # Look for matching language string
    for v in voices:
        if language_code in str(v.languages).lower() or language_code in str(v.id).lower() or language_code in str(v.name).lower():
            target_voice_id = v.id
            break

    if target_voice_id:
        engine.setProperty('voice', target_voice_id)
        
    engine.setProperty('rate', 150) # Slower for clear dictation
    
    logging.info(f"Speaking aloud in '{language_code}': {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logging.error(f"Failed to play TTS feedback: {e}")
