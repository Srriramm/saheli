# Saheli: Offline Maternal Health AI for India's 1 Million ASHA Workers

*Built with Gemma 4 E4B · Runs 100% Offline · Multilingual Text & Vision · Fine-tuned on WHO ANC Guidelines*

---

## The Problem

India has over **1 million ASHA (Accredited Social Health Activists) workers** — the world's largest all-female community health workforce. These women are the first and often only healthcare contact for pregnant women in rural villages.

The critical gap: ASHA workers carry paper registers, have no smartphone tools designed for them, serve areas with **zero internet connectivity**, speak only local languages (Hindi, Kannada, Telugu, Tamil), and are not trained to reliably identify high-risk pregnancy warning signs.

India's maternal mortality ratio (MMR) has dropped from 130 to 97 per 100,000 live births — largely due to ASHA-led care. But missed danger signs — pre-eclampsia, severe anaemia, foetal distress — still cause **preventable maternal deaths every day**. The gap is not medical knowledge. It is a tool gap.

---

## The Solution

**Saheli** (meaning *friend* in Hindi) is a multilingual AI triage agent that runs **entirely offline** on a sub-₹5,000 Android phone. It is designed specifically for ASHA workers — not doctors, not urban users.

**How it works in one visit:**
1. ASHA types symptoms in Tamil, Kannada, or English using their phone keyboard (including keyboard voice-to-text)
2. ASHA photographs swollen feet or jaundiced eyes — Gemma 4's multimodal vision analyses the image
3. Saheli classifies risk: 🟢 GREEN (routine) / 🟡 YELLOW (refer in 24h) / 🔴 RED (emergency)
4. For RED cases: a full-screen emergency overlay shows facility name, distance, and ambulance number
5. Every visit is saved to SQLite — no internet needed at any point

The key demo: **enable airplane mode, run a full triage, get a result with referral.** The system makes zero network calls.

---

## Why Gemma 4 — Not GPT-4, Not Cloud APIs

This is not a preference — it is a hard architectural requirement:

1. **Runs offline on 3 GB RAM** — Gemma 4 E4B Q4_K_M (2.5 GB) via llama.cpp is the only model that fits on ₹5,000 Android hardware with clinical reasoning quality
2. **Native multimodal** — photo + text in a single model call; no separate vision API, no internet
3. **Native function calling** — structured JSON tool calls without external orchestration; the model calls `assess_danger_signs()` with symptoms and vitals it extracts from voice
4. **Fine-tunable with Unsloth** — we publish domain-specific WHO ANC weights; base Gemma 4 has no maternal health grounding
5. **Multilingual by design** — 140+ languages including all major Indic scripts; Hindi and Kannada work out of the box

Replacing Gemma 4 with any cloud API breaks the entire product. **No internet = no product.**

---

## Technical Architecture

```
ASHA Typed Input (Tamil / Kannada / English)
        ↓
Gemma 4 E4B — Fine-tuned (GGUF Q4_K_M, llama.cpp)
   ├── Function calling → assess_danger_signs() [WHO ANC rules]
   ├── Function calling → get_nearest_referral() [geopy + offline JSON]
   ├── Multimodal vision → photo analysis (swollen feet, jaundice)
   └── Multilingual output (Tamil / Kannada / English)
        ↓
Risk Level: RED / YELLOW / GREEN
        ↓
SQLite offline patient DB
        ↓
Flutter App (Android)
```

The entire stack runs on a single device with no background services, no cloud sync, no API keys. GPS from the device drives the referral lookup — the model finds the nearest PHC/CHC from 20 offline-cached Karnataka facilities using geopy geodesic distance.

---

## Fine-Tuning Results

We fine-tuned **Gemma 4 E4B** using Unsloth LoRA (rank=16, alpha=32) for 3 epochs on a custom WHO ANC dataset of **1,500 hybrid-format conversations** generated from clinical guidelines.

**Dataset composition:**
| Type | Count | Purpose |
|---|---|---|
| Single-symptom | 700 | Core paraphrase coverage |
| Multi-symptom combinations | 400 | Pre-eclampsia triad, eclampsia, abruption |
| Confuser / edge cases | 150 | Mild headache ≠ severe; ankle ≠ facial oedema |
| Hindi code-mix | 150 | Multilingual generalisation |
| Free-form narrative | 100 | ASHA diary-style inputs |

Each training sample uses a **hybrid output format**: a JSON function call (`assess_danger_signs`) followed by a plain-language RED/YELLOW/GREEN recommendation — matching the exact production inference path.

**Evaluation on 35 illustrative test cases** covering single-symptom, multi-symptom, vitals-bearing, confuser edge cases, Hindi code-mix, and ASHA diary narratives:

| Method | RED recall | Notes |
|---|---|---|
| Rule-based baseline | 100% | Deterministic — catches all keyword-matched danger signs |
| **Pure fine-tuned LLM** | **85%** | Clinically conservative — biased toward over-referral |
| LLM + Rule safety-net (production) | **100% by design** | Structural guarantee: merge = max(LLM, rule) |

The production path's 100% RED recall is a **structural guarantee**, not a benchmark result. `merge_risk()` returns the higher of LLM output and rule output — RED can never be suppressed regardless of LLM quality.

The fine-tuned LLM's 85% RED recall (vs base Gemma 4 E4B which produces unparseable prose) shows the fine-tune adds two concrete things: (1) consistent JSON function-call output that enables the rule safety-net to operate, and (2) clinical conservatism — when uncertain, it calls RED rather than GREEN.

When the LLM fails entirely (e.g. responding in Turkish to Hindi input, a known base-model behaviour), the rule fallback still returns the correct verdict. The architecture is resilient to LLM failure modes by design.

---

## Demo Description

The demo video shows a simulated ASHA visit in Doddaballapur taluk, Karnataka:

1. **Airplane mode enabled** on camera — shows no network dependency
2. ASHA types Tamil symptoms: *"32 weeks, severe headache, blurred vision, BP 155/106"*
3. Saheli returns RED immediately — full-screen emergency overlay with "PHC Doddaballapur (1.14 km)" and ambulance button
4. ASHA switches to YELLOW case: anaemia + reduced foetal movement — referral card appears in 24h
5. App language switched to Kannada — same flow, same result
6. Architecture diagram + benchmark table displayed
7. Closing: *"ASHA means hope in Hindi. Saheli means friend."*

Total runtime: under 3 minutes.

---

## Impact and Scalability

**Immediate reach:** 1 million ASHA workers across India, each serving 800–1,200 people. Karnataka alone has 42,000 ASHAs.

**Cost:** ₹0 per ASHA worker. The model runs on phones they already carry. No subscription, no cloud bill, no data plan required.

**Deployment path:** Integration with India's National Health Mission (NHM) ASHA portal (asha.nhp.gov.in) is a direct fit — NHM already distributes smartphones to ASHAs under the SASHAKT programme. Saheli needs only a one-time APK install.

**Languages:** Currently Tamil, Kannada, and English. Adding Hindi, Telugu, and Odia requires only new system prompt translations — zero retraining.

**Privacy:** Patient data never leaves the device. SQLite records stay local. Fully compliant with India's Digital Personal Data Protection Act (DPDPA) 2023.

---

## Challenges and Learnings

**Separator masking was the hardest bug.** The Gemma 4 chat template uses `<|turn>user` / `<|turn>model` separators. When `train_on_responses_only` receives the wrong separator string, it silently trains on the full sequence — loss looks normal but the model learns nothing. We added a mandatory separator check that aborts training if the formatted sample doesn't match.

**Gemma 4's native tool call format** (`<|tool_call>call:FUNC{args}<tool_call|>`) differs from the OpenAI JSON schema format we trained on. We built a multi-path parser in `GemmaRunner._parse_tool_output()` that handles both formats plus a bare-JSON fallback.

**Spelling normalisation** was safety-critical: "no fetal movement" (American) vs "no foetal movement" (WHO British standard) caused GREEN misclassification on two test cases. The `_normalise()` function in `function_tools.py` bridges 12 spelling variants and synonym mappings.

---

## Conclusion

Saheli is not a prototype — it is a deployable system that works today on hardware that costs less than a textbook. Every technical choice (Gemma 4, offline-first, Whisper, SQLite) is driven by a single constraint: **it must work where there is no internet, no doctor, and no margin for error.**

ASHA means hope in Hindi. Saheli means friend. We built hope, delivered by a friend, for 1 million women who have neither.

**Code:** github.com/[your-username]/saheli  
**Model weights:** huggingface.co/[your-username]/saheli-gemma4-e4b  
**Live demo:** [HuggingFace Spaces link]
