MODEL_PATH = "./models/gemma-4-E4B-IT-Q4_K_M.gguf"
WHISPER_MODEL = "small"          # small = 244MB on CPU, Gemma keeps GPU
MAX_TOKENS = 512
CONTEXT_LENGTH = 1024
DEFAULT_LANGUAGE = "ta"          # Tamil demo default
SUPPORTED_LANGUAGES = ["hi", "kn", "te", "ta", "en"]
DATABASE_PATH = "./data/saheli.db"
REFERRAL_DATA_PATH = "./data/referral_data.json"
RISK_LEVELS = {"GREEN": 0, "YELLOW": 1, "RED": 2}
