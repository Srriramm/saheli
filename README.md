# Saheli — Offline Maternal Health AI for India's 1 Million ASHA Workers

*ASHA means hope in Hindi. Saheli means friend.*

![License](https://img.shields.io/badge/license-Apache%202.0-blue)
![Model](https://img.shields.io/badge/model-Gemma%204%20E4B-orange)
![Offline](https://img.shields.io/badge/runs-100%25%20offline-green)
![Languages](https://img.shields.io/badge/languages-Tamil%20%7C%20Kannada%20%7C%20Hindi%20%7C%20Telugu%20%7C%20English-purple)
![Platform](https://img.shields.io/badge/platform-Android%20%7C%20Raspberry%20Pi-lightgrey)

---

## The Problem

India has over **1 million ASHA (Accredited Social Health Activist) workers** — the world's largest all-female community health workforce. These women are the first and often only healthcare contact for pregnant women in rural villages.

The gap is structural:

- ASHA workers carry **paper registers** and have no smartphone tools built for their context
- They serve areas with **zero internet connectivity**
- They speak only local languages — Hindi, Kannada, Telugu, Tamil — and are not trained to reliably identify high-risk pregnancy warning signs
- Missed danger signs such as pre-eclampsia, severe anaemia, and foetal distress cause **preventable maternal deaths every day**

India's maternal mortality ratio (MMR) dropped from 130 to 97 per 100,000 live births — largely through ASHA-led care. The tool gap is what remains.

---

## What Saheli Does

**Saheli** is a voice-first, multilingual AI triage agent that runs **entirely offline** on a sub-₹5,000 Android phone or Raspberry Pi 5. It is designed specifically for ASHA workers — not doctors, not urban users.

A complete visit in 4 steps:

1. ASHA speaks or types symptoms in Tamil, Kannada, or Hindi
2. ASHA photographs swollen feet or jaundiced eyes — Gemma 4's multimodal vision analyses the image on-device
3. Saheli classifies risk: 🟢 **GREEN** (routine) / 🟡 **YELLOW** (refer within 24 h) / 🔴 **RED** (emergency — call ambulance now)
4. For RED cases: a full-screen emergency overlay shows facility name, distance, and ambulance number, spoken aloud in the ASHA's language

Every visit is saved to a local SQLite database. The system makes zero network calls at any point.

---

## Why Gemma 4

The offline constraint is not a preference — it is the product. Every technical choice flows from it:

| Requirement | Why Gemma 4 |
|---|---|
| **Runs on ₹5,000 phone offline** | Gemma 4 E4B Q4_K_M (~2.5 GB) via llama.cpp fits in 3 GB RAM with clinical reasoning quality |
| **Photo analysis without a vision API** | Native multimodal — photo + text in a single on-device model call |
| **Structured clinical tool calls** | Native function calling — the model calls `assess_danger_signs()` with symptoms and vitals it extracts from the ASHA's input |
| **Domain-specific grounding** | Fine-tunable with Unsloth on a consumer GPU — we publish WHO ANC maternal health weights |
| **Indic language support** | Supports 140+ languages including Tamil, Kannada, Hindi, and Telugu natively |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               ASHA Worker's Android Phone / Raspberry Pi 5  │
│                        (Airplane Mode)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  INPUT                                                       │
│  ├── Voice / keyboard text  →  Whisper small (244 MB, CPU)  │
│  └── Camera photo           →  OpenCV → letterbox 336×336   │
│                                                              │
│  CORE AI                                                     │
│  └── Gemma 4 E4B  (Q4_K_M GGUF, ~2.5 GB, via llama.cpp)   │
│       ├── Fine-tuned on 1,500 WHO ANC conversations          │
│       ├── Native multimodal  — text + image in one call      │
│       └── Native function calling                            │
│            ├── assess_danger_signs()   ← WHO ANC checklist   │
│            ├── calculate_gestational_age()                   │
│            ├── get_nearest_referral()  ← 20 Karnataka PHCs  │
│            ├── log_patient_record()    ← SQLite              │
│            └── get_patient_history()                         │
│                                                              │
│  SAFETY NET                                                  │
│  └── risk_classifier.py — deterministic rule merge          │
│       merge_risk() = max(LLM_risk, rule_risk)               │
│       RED cannot be suppressed regardless of LLM quality    │
│                                                              │
│  OUTPUT                                                      │
│  ├── Flutter app  — large-button UI, RED emergency overlay   │
│  ├── pyttsx3 / espeak  — spoken result in ASHA's language   │
│  └── SQLite  — patient record saved offline                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**API layer:** FastAPI server (`ui/app.py`) runs locally on port 5000. The Flutter mobile app communicates with it over localhost — no external network calls at any point.

---

## Evaluation Metrics

Evaluated on **20 held-out maternal health test cases** covering single-symptom, multi-symptom, vitals-bearing, confuser/edge-case, Hindi code-mix, and ASHA diary narrative scenarios.

| Method | RED Recall | Notes |
|---|---|---|
| Rule-based baseline | **100%** | Deterministic WHO ANC checklist — catches all keyword-matched danger signs |
| Pure fine-tuned LLM | **85%** | Clinically conservative — biased toward over-referral when uncertain |
| **LLM + Rule safety-net (production)** | **100% by design** | `merge_risk()` = max(LLM, rule) — RED is structurally guaranteed |

> Run `python finetune/evaluate_model.py` with the GGUF model in place to reproduce full accuracy and F1 numbers.

**Why 100% RED recall is a structural guarantee:**
`merge_risk()` always returns the higher of the LLM risk and the rule-based risk. The deterministic checker uses the WHO ANC danger signs list — if any RED keyword appears (severe headache + visual disturbance, convulsions, no foetal movement >12 h, heavy bleeding), the output is RED regardless of LLM quality. The fine-tuned LLM contributes: (1) consistent JSON function-call output that enables the safety net to operate, (2) clinical conservatism when uncertain, and (3) natural-language response in the ASHA's language.

**Fine-tuning dataset (1,500 training samples):**

| Type | Count | Purpose |
|---|---|---|
| Single-symptom paraphrases | 700 | Core coverage — spelling variants, voice phrasing |
| Multi-symptom combinations | 400 | Pre-eclampsia triad, eclampsia, placental abruption |
| Confuser / edge cases | 150 | Mild headache ≠ severe; ankle ≠ facial oedema |
| Hindi code-mix | 150 | Roman transliteration ASHA inputs |
| Free-form narrative | 100 | ASHA diary-style inputs |

**Fine-tuning config:** Unsloth LoRA · rank=16 · alpha=32 · target: q_proj, v_proj · 3 epochs · batch=1 · grad accumulation=4 · lr=2e-4 · exported to GGUF Q4_K_M for llama.cpp.

---

## Quick Start

### Option A — Docker (recommended)

```bash
# 1. Clone
git clone https://github.com/Srriramm/saheli.git
cd saheli

# 2. Download model weights (~2.5 GB GGUF + ~1 GB mmproj)
chmod +x models/download_model.sh
./models/download_model.sh

# 3. Build and start
docker compose up --build
# API at http://localhost:5000  |  Docs at http://localhost:5000/docs
```

**GPU inference (CUDA 12.2):**
```bash
docker compose up --build \
    --build-arg LLAMA_CPP_INDEX=https://abetlen.github.io/llama-cpp-python/whl/cu122
```

---

### Option B — Local Python

**Requirements:** Python 3.10+ · ~3 GB RAM · ~4 GB disk · Linux / macOS / Windows

```bash
git clone https://github.com/Srriramm/saheli.git
cd saheli
pip install -r requirements.txt
chmod +x models/download_model.sh && ./models/download_model.sh

python run.py          # FastAPI server at http://localhost:5000
python run.py --cli    # Interactive CLI triage loop
python run.py --test   # Evaluation benchmark on 20 test cases
```

---

### Offline Verification

Before any deployment or demo, run the airplane mode test:

```
1. Enable airplane mode on the device
2. POST /run-triage with: transcript="severe headache blurred vision BP 155/106 32 weeks", language="ta"
3. Confirm RED response with referral facility returned
4. Verify zero outbound network connections in device logs
```

---

## Fine-Tuning (Reproducible)

```bash
# Generate 1,500 synthetic WHO ANC training conversations
python finetune/prepare_dataset.py

# Fine-tune on Kaggle or Colab GPU
# Open: finetune/kaggle_unsloth_train.ipynb  or  finetune/colab_unsloth_train.ipynb

# Convert to GGUF for llama.cpp
# Open: finetune/kaggle_gguf_convert.ipynb

# Evaluate and print benchmark table
python finetune/evaluate_model.py
```

---

## API Reference

Interactive docs at `http://localhost:5000/docs`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/run-triage` | Full triage from text transcript |
| `POST` | `/submit-photo` | Multimodal triage from camera photo |
| `GET` | `/patient/{id}` | Patient visit history and risk trend |
| `POST` | `/new-patient` | Register a new patient |
| `GET` | `/referrals` | List all 20 offline Karnataka PHC/CHC facilities |

**Example request:**
```json
POST /run-triage
{
  "patient_id": "KA-VLG-042",
  "language": "ta",
  "transcript": "32 வாரம் கர்ப்பம், கடுமையான தலைவலி, பார்வை மங்கல், BP 155/106",
  "latitude": 13.2957,
  "longitude": 77.5388
}
```

**Example response:**
```json
{
  "risk_level": "RED",
  "danger_signs": ["severe headache", "visual disturbance", "hypertension ≥140/90"],
  "referral": {
    "facility_name": "PHC Doddaballapur",
    "distance_km": 1.14,
    "phone": "080-27631234",
    "emergency_phone": "108"
  },
  "response": "இது மிகவும் ஆபத்தான நிலை. உடனே PHC Doddaballapur-க்கு அனுப்புங்கள்.",
  "record_id": "a3f2c1d0-..."
}
```

---

## Mobile App

The Flutter app (`app_flutter/`) is the primary ASHA-facing interface targeting Android:

| Screen | Description |
|---|---|
| Splash / Language | Language selection on first launch |
| Triage | Symptom input + camera photo capture |
| Result | Large GREEN / YELLOW / RED risk banner with danger signs listed |
| Emergency | Full-screen RED overlay — facility name, distance, ambulance number in large text |
| History | Per-patient visit timeline with risk trend (Stable / Deteriorating / Improving) |

The app communicates with the local FastAPI backend over `http://localhost:5000`. On Android it runs via Termux or as a packaged APK service; on Raspberry Pi as a systemd service. A React Native / Expo version (`app/`) is included for browser-based demo access.

---

## Project Structure

```
saheli/
├── Dockerfile                      # Backend container (CPU default, GPU via build-arg)
├── docker-compose.yml              # Production deployment with volume mounts
├── run.py                          # Entry point: server | CLI | benchmark
├── requirements.txt
├── config/
│   ├── settings.py                 # MODEL_PATH, supported languages, paths
│   └── languages.py                # TTS voice mapping per language code
├── models/
│   ├── download_model.sh           # Pull Gemma 4 E4B GGUF from HuggingFace
│   ├── gemma_runner.py             # llama.cpp inference (text, multimodal, function calling)
│   └── whisper_runner.py           # Offline Whisper STT with Tamil fine-tune fallback
├── core/
│   ├── triage_engine.py            # Orchestration: LLM → tools → safety-net → response
│   ├── function_tools.py           # 5 tool implementations + WHO symptom normaliser
│   ├── risk_classifier.py          # Deterministic RED/YELLOW/GREEN + merge_risk()
│   ├── prompt_templates.py         # System prompts in 5 languages
│   └── translations.py             # Danger sign translations for UI display
├── data/
│   ├── database.py                 # SQLite schema + CRUD (patients, visits, risk trend)
│   ├── referral_data.json          # 20 Karnataka PHC/CHC facilities (GPS, phone, ambulance)
│   └── who_anc_checklist.json      # WHO ANC danger signs: 14 RED · 20 YELLOW · 8 GREEN
├── finetune/
│   ├── prepare_dataset.py          # Generate 1,500 WHO ANC training conversations
│   ├── train_unsloth.py            # Unsloth LoRA fine-tuning script
│   ├── evaluate_model.py           # 3-path benchmark: rule / LLM / LLM+rule
│   ├── kaggle_unsloth_train.ipynb  # Kaggle GPU training notebook
│   ├── colab_unsloth_train.ipynb   # Colab GPU training notebook
│   └── kaggle_gguf_convert.ipynb   # GGUF export notebook
├── audio/
│   ├── recorder.py                 # PyAudio mic capture → .wav
│   └── speaker.py                  # pyttsx3 / espeak TTS in ASHA's language
├── vision/
│   └── image_processor.py          # Letterbox resize 336×336 + base64 encode for Gemma 4
├── ui/
│   └── app.py                      # FastAPI server — 6 REST endpoints
├── app_flutter/                    # Flutter mobile app (Android primary target)
│   └── lib/
│       ├── screens/                # Triage, Result, History, Splash, Language
│       ├── widgets/                # RiskBadge, GlassPill, SaheliLogo
│       └── core/                   # API client, theme, location, strings
├── app/                            # React Native / Expo (browser demo)
└── tests/
    ├── test_triage.py              # TriageEngine unit tests (mocked LLM — no GGUF needed)
    ├── test_functions.py           # Function tool unit tests (all 5 tools)
    └── sample_cases.json           # 20 evaluation cases: RED × 8, YELLOW × 7, GREEN × 5
```

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use a mocked `GemmaRunner` — no GGUF model file required. Covers TriageEngine orchestration, all 5 function tools (including Tamil symptom mapping, vitals thresholds, geopy referral distance), and SQLite patient CRUD.

---

## Impact

| Metric | Value |
|---|---|
| ASHA workers in India | 1,000,000+ |
| Cost per ASHA worker | ₹0 — runs on phones they already carry |
| Languages supported | Tamil, Kannada, Hindi, Telugu, English |
| Supported hardware | Any Android phone ≥3 GB RAM, Raspberry Pi 5 |
| Patient data leaves device | Never — fully offline, DPDPA 2023 compliant |

Deployment path: India's National Health Mission (NHM) SASHAKT programme already distributes smartphones to ASHA workers. Saheli requires only a one-time APK install — no subscription, no data plan, no cloud dependency. Adding new languages requires only new system prompt translations with zero model retraining.

---

## License

Apache 2.0 — free for government, NGO, and community health use.
