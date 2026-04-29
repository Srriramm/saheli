"""
prepare_dataset.py — Build Saheli training dataset from WHO ANC guidelines.

1 500 synthetic conversations in HYBRID output format:
  model message = JSON function-call block + plain-language RED/YELLOW/GREEN summary.

Composition:
  700  single-symptom   (varied paraphrases, vitals, templates)
  400  multi-symptom    (2-3 combined clinical signs — pre-eclampsia, eclampsia, etc.)
  150  confuser/edge    (boundary cases: mild headache ≠ severe, ankle ≠ face swelling)
  150  Hindi code-mix   (Roman transliteration — teaches multilingual generalisation)
  100  free-form narrative (ASHA diary-style longer inputs)
  = 1 500 total

Saves to finetune/datasets/saheli_anc_dataset/ (HuggingFace DatasetDict format)
Also exports Unsloth Studio JSONL.
"""

import json
import os
import random
from datasets import Dataset, DatasetDict


SYSTEM_PROMPT = (
    "You are Saheli, a maternal health assistant for ASHA workers. "
    "Given the patient's symptoms and vitals, output a JSON tool call to "
    "assess_danger_signs followed by a short RED/YELLOW/GREEN recommendation "
    "in plain language. Use WHO Antenatal Care guidelines."
)


# ── Single-symptom paraphrase bank ────────────────────────────────────────────
PARAPHRASES = {
    "RED": {
        "severe headache": [
            "severe headache", "terrible headache", "very bad headache",
            "pounding headache that won't go away", "unbearable head pain",
            "extremely bad headache since morning",
        ],
        "blurred vision": [
            "blurred vision", "seeing spots", "can't see clearly",
            "vision is hazy", "flashing lights in the eyes",
            "dark spots before eyes", "visual disturbance",
        ],
        "heavy vaginal bleeding": [
            "heavy vaginal bleeding", "bleeding a lot from down below",
            "soaked two pads in an hour", "heavy bleeding",
            "bleeding heavily", "excessive vaginal bleeding",
        ],
        "convulsions": [
            "convulsions", "fits", "seizure", "shaking uncontrollably",
            "fitting episode", "body shaking fits", "had a fit",
        ],
        "no foetal movement": [
            "no foetal movement for 14 hours", "baby has not moved all day",
            "no kicks since yesterday", "no foetal movement",
            "baby not moving at all", "no movement from the baby",
        ],
        "severe abdominal pain": [
            "severe abdominal pain", "sudden severe stomach pain",
            "very bad pain in the belly", "tearing pain in the abdomen",
            "sharp sudden stomach pain", "unbearable belly pain",
        ],
        "loss of consciousness": [
            "loss of consciousness", "fainted and did not wake",
            "unconscious for several minutes", "became unconscious",
            "passed out completely",
        ],
    },
    "YELLOW": {
        "high blood pressure": [
            "high blood pressure", "BP is high",
            "blood pressure 145 over 95", "hypertension reading",
            "BP elevated", "high BP",
        ],
        "severe anaemia": [
            "severe anaemia", "feeling very weak", "pale eyes, extreme weakness",
            "looks very pale and tired", "Hb is 6.5", "haemoglobin 6.0",
            "haemoglobin only 6.2", "very low haemoglobin",
        ],
        "high fever": [
            "high fever", "fever 39 degrees", "very hot with chills",
            "fever and shivering", "temperature 39.5", "fever above 38",
            "fever with body ache",
        ],
        "reduced foetal movement": [
            "reduced foetal movement", "baby moving less than usual",
            "fewer kicks than yesterday", "baby not moving much",
            "reduced baby movements",
        ],
        "oedema above ankles": [
            "oedema above ankles", "swelling above the knees",
            "swollen face and hands", "puffy face in the morning",
            "facial swelling", "hands swollen", "generalised swelling",
        ],
        "jaundice": [
            "jaundice", "yellowing of eyes", "yellow skin and eyes",
            "eyes look yellow", "skin and eyes turning yellow",
        ],
        "persistent headache": [
            "persistent headache", "headache for three days",
            "headache that keeps coming back", "headache since two days",
            "recurring headache", "headache for two days",
        ],
    },
    "GREEN": {
        "mild nausea": [
            "mild nausea", "a bit queasy", "morning sickness",
            "some nausea in the mornings", "slight nausea",
            "nausea that passes by midday",
        ],
        "mild ankle swelling": [
            "mild ankle swelling", "feet slightly swollen after walking",
            "a little puffiness in the feet", "slight ankle puffiness",
            "mild swelling in feet",
        ],
        "fatigue": [
            "fatigue", "feeling tired", "mild backache and tiredness",
            "low energy", "feeling a bit weak", "easily tired",
        ],
        "mild breast tenderness": [
            "mild breast tenderness", "sore breasts", "breast discomfort",
        ],
        "frequent urination": [
            "frequent urination", "going to the toilet often",
            "urinating frequently",
        ],
        "mild heartburn": [
            "mild heartburn", "burning feeling after eating", "acid reflux",
        ],
    },
}


# ── Vitals generators ─────────────────────────────────────────────────────────
def _vitals_for_sign(risk: str, canonical_sign: str) -> dict:
    v = {}
    if risk == "RED":
        if "headache" in canonical_sign or "blurred vision" in canonical_sign or "visual" in canonical_sign:
            v["bp_sys"] = random.randint(150, 180)
            v["bp_dia"] = random.randint(100, 115)
        elif "convulsions" in canonical_sign or "loss of consciousness" in canonical_sign:
            v["bp_sys"] = random.randint(160, 185)
            v["bp_dia"] = random.randint(105, 120)
    elif risk == "YELLOW":
        if "blood pressure" in canonical_sign:
            v["bp_sys"] = random.randint(142, 158)
            v["bp_dia"] = random.randint(92, 99)
        elif "anaemia" in canonical_sign:
            v["hb"] = round(random.uniform(5.5, 7.8), 1)
        elif "fever" in canonical_sign:
            v["temp_c"] = round(random.uniform(38.5, 40.0), 1)
        elif "oedema" in canonical_sign:
            v["bp_sys"] = random.randint(135, 145)
            v["bp_dia"] = random.randint(88, 94)
    return v


def _vitals_str(v: dict) -> str:
    parts = []
    if "bp_sys" in v and "bp_dia" in v:
        parts.append(f"BP {v['bp_sys']}/{v['bp_dia']}")
    if "hb" in v:
        parts.append(f"haemoglobin {v['hb']}")
    if "temp_c" in v:
        parts.append(f"temperature {v['temp_c']}C")
    return ", ".join(parts)


# ── Single-symptom user message templates ─────────────────────────────────────
USER_TMPL_NO_VITALS = [
    "Patient is {w} weeks pregnant and has {sign}.",
    "ASHA reports: {w}-week patient, {sign}.",
    "{w}w patient complains of {sign}. What do we do?",
    "Pregnant woman at {w} weeks. She reports {sign}.",
    "Visited a patient today — {w} weeks pregnant, {sign}. Risk level?",
    "Mother is {w} weeks along. Main complaint: {sign}.",
    "{w} weeks pregnant. ASHA reports {sign}.",
]

USER_TMPL_WITH_VITALS = [
    "Patient is {w} weeks pregnant with {sign}. Vitals: {vstr}.",
    "{w}-week patient, {sign}. {vstr}.",
    "ASHA visit: {w}w, {sign}, {vstr}.",
    "Pregnant woman at {w} weeks. {sign}. Measurements: {vstr}.",
]


def _build_single_response(canonical: str, risk: str, weeks: int, vitals: dict) -> str:
    vstr = _vitals_str(vitals)
    vsuffix = f" with {vstr}" if vstr else ""
    args = {"symptoms": [canonical], "vitals": vitals} if vitals else {"symptoms": [canonical]}
    tool_call = {"name": "assess_danger_signs", "arguments": args}
    tool_block = f"```json\n{json.dumps(tool_call)}\n```"
    if risk == "RED":
        reasoning = (
            f"RED. {canonical.capitalize()}{vsuffix} at {weeks} weeks is a "
            "danger sign. Refer to PHC immediately and call 108 ambulance."
        )
    elif risk == "YELLOW":
        reasoning = (
            f"YELLOW. {canonical.capitalize()}{vsuffix} at {weeks} weeks needs "
            "attention. Refer to the nearest clinic within 24 hours."
        )
    else:
        reasoning = (
            f"GREEN. {canonical.capitalize()} at {weeks} weeks is common in "
            "pregnancy. Continue routine monitoring and keep the ASHA informed."
        )
    return f"{tool_block}\n\n{reasoning}"


def generate_single_symptom(n: int = 700) -> list:
    data = []
    risk_dist = [("RED", 0.40), ("YELLOW", 0.35), ("GREEN", 0.25)]

    def _pick_risk():
        r = random.random()
        cum = 0.0
        for risk, p in risk_dist:
            cum += p
            if r <= cum:
                return risk
        return "GREEN"

    for _ in range(n):
        risk = _pick_risk()
        canonical = random.choice(list(PARAPHRASES[risk].keys()))
        spoken = random.choice(PARAPHRASES[risk][canonical])
        weeks = random.randint(8, 40)
        vitals = _vitals_for_sign(risk, canonical)

        use_vitals = risk in ("RED", "YELLOW") and bool(vitals) and random.random() < 0.55
        if use_vitals:
            tmpl = random.choice(USER_TMPL_WITH_VITALS)
            user_msg = tmpl.format(w=weeks, sign=spoken, vstr=_vitals_str(vitals))
        else:
            tmpl = random.choice(USER_TMPL_NO_VITALS)
            user_msg = tmpl.format(w=weeks, sign=spoken)
            if random.random() < 0.15:
                vitals = {}

        model_msg = _build_single_response(canonical, risk, weeks, vitals)
        data.append({
            "conversations": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
                {"role": "model",  "content": model_msg},
            ]
        })
    return data


# ── Multi-symptom combinations ────────────────────────────────────────────────
# Real ASHA cases present 2-3 danger signs simultaneously.
# Training on these teaches the model to: list ALL symptoms in the JSON array,
# pick the highest risk level, and explain the combined clinical picture.

MULTI_COMBOS = [
    # RED
    {
        "risk": "RED",
        "canonical": ["severe headache", "blurred vision"],
        "phrases_a": ["severe headache", "terrible headache", "very bad headache", "pounding headache"],
        "phrases_b": ["blurred vision", "seeing spots", "can't see clearly", "hazy vision", "visual disturbance"],
        "vitals_gen": lambda: {"bp_sys": random.randint(150, 175), "bp_dia": random.randint(100, 115)},
        "clinical": "pre-eclampsia",
        "response": "Refer to PHC immediately and call 108 ambulance.",
    },
    {
        "risk": "RED",
        "canonical": ["convulsions", "loss of consciousness"],
        "phrases_a": ["convulsions", "fits", "seizure", "shaking fits", "fitting episode"],
        "phrases_b": ["loss of consciousness", "fainted", "became unconscious", "passed out"],
        "vitals_gen": lambda: {"bp_sys": random.randint(160, 185), "bp_dia": random.randint(108, 120)},
        "clinical": "eclampsia",
        "response": "Call 108 ambulance immediately. Do not move the patient.",
    },
    {
        "risk": "RED",
        "canonical": ["severe abdominal pain", "heavy vaginal bleeding"],
        "phrases_a": ["severe abdominal pain", "sudden belly pain", "sharp pain in abdomen", "tearing stomach pain"],
        "phrases_b": ["heavy vaginal bleeding", "heavy bleeding", "bleeding a lot", "soaked two pads"],
        "vitals_gen": lambda: {},
        "clinical": "placental abruption",
        "response": "Emergency referral immediately. Call 108.",
    },
    {
        "risk": "RED",
        "canonical": ["severe headache", "loss of consciousness"],
        "phrases_a": ["severe headache", "terrible headache", "unbearable headache"],
        "phrases_b": ["loss of consciousness", "fainted", "became unconscious", "passed out"],
        "vitals_gen": lambda: {"bp_sys": random.randint(158, 180), "bp_dia": random.randint(105, 118)},
        "clinical": "hypertensive emergency",
        "response": "Life-threatening emergency. Refer to PHC and call 108 immediately.",
    },
    {
        "risk": "RED",
        "canonical": ["no foetal movement", "severe abdominal pain"],
        "phrases_a": ["no foetal movement", "baby not moving at all", "no kicks at all", "baby stopped moving"],
        "phrases_b": ["severe abdominal pain", "bad stomach pain", "belly pain and cramping"],
        "vitals_gen": lambda: {},
        "clinical": "foetal distress with abruption risk",
        "response": "Immediate referral required. Call 108 ambulance.",
    },
    {
        "risk": "RED",
        "canonical": ["blurred vision", "severe headache"],
        "phrases_a": ["seeing spots", "can't see properly", "flashing lights", "everything looks blurry"],
        "phrases_b": ["severe headache", "head pain", "pounding headache"],
        "vitals_gen": lambda: {"bp_sys": random.randint(155, 178), "bp_dia": random.randint(102, 116)},
        "clinical": "imminent eclampsia",
        "response": "Refer to PHC immediately. This is pre-eclampsia. Call 108.",
    },
    # YELLOW
    {
        "risk": "YELLOW",
        "canonical": ["oedema above ankles", "persistent headache"],
        "phrases_a": ["swollen face and hands", "swelling above ankles", "puffy face", "swollen face"],
        "phrases_b": ["persistent headache", "headache for two days", "headache since yesterday", "recurring headache"],
        "vitals_gen": lambda: {"bp_sys": random.randint(138, 152), "bp_dia": random.randint(88, 97)},
        "clinical": "early pre-eclampsia warning",
        "response": "Refer to clinic within 24 hours. Monitor BP daily.",
    },
    {
        "risk": "YELLOW",
        "canonical": ["jaundice", "high fever"],
        "phrases_a": ["yellowing of eyes", "yellow skin and eyes", "jaundice", "eyes turning yellow"],
        "phrases_b": ["high fever", "fever 39 degrees", "fever with chills", "temperature high"],
        "vitals_gen": lambda: {"temp_c": round(random.uniform(38.5, 39.8), 1)},
        "clinical": "possible malaria or hepatitis in pregnancy",
        "response": "Refer to facility within 24 hours for blood tests.",
    },
    {
        "risk": "YELLOW",
        "canonical": ["severe anaemia", "reduced foetal movement"],
        "phrases_a": ["feeling very weak", "pale and very weak", "Hb is 6.5", "haemoglobin very low"],
        "phrases_b": ["reduced foetal movement", "baby moving less", "fewer kicks", "baby not moving much"],
        "vitals_gen": lambda: {"hb": round(random.uniform(5.5, 7.5), 1)},
        "clinical": "severe anaemia with reduced foetal movement",
        "response": "Urgent referral within 24 hours. Both signs require evaluation.",
    },
    {
        "risk": "YELLOW",
        "canonical": ["high blood pressure", "oedema above ankles"],
        "phrases_a": ["BP is high", "blood pressure elevated", "hypertension", "high BP reading"],
        "phrases_b": ["swollen face", "swelling above ankles", "oedema above ankles", "puffy hands and face"],
        "vitals_gen": lambda: {"bp_sys": random.randint(140, 158), "bp_dia": random.randint(90, 100)},
        "clinical": "hypertension with oedema",
        "response": "Refer to clinic within 24 hours.",
    },
    {
        "risk": "YELLOW",
        "canonical": ["high fever", "reduced foetal movement"],
        "phrases_a": ["fever 38.5", "high fever", "temperature 39", "fever and chills"],
        "phrases_b": ["baby not moving much", "reduced foetal movement", "fewer kicks than yesterday"],
        "vitals_gen": lambda: {"temp_c": round(random.uniform(38.5, 40.0), 1)},
        "clinical": "fever with reduced foetal activity",
        "response": "Refer to facility within 24 hours.",
    },
]

MULTI_TMPL_NO_VITALS = [
    "Patient is {w} weeks pregnant with {a} and {b}.",
    "ASHA reports: {w}-week patient has {a} and also {b}.",
    "{w}w patient — {a} and {b} observed. What is the risk?",
    "Pregnant woman at {w} weeks. She has {a}. Also noticed {b}.",
    "Patient {w} weeks, complaining of {a}. Additionally, {b}.",
    "Visited patient today — {w} weeks pregnant. Found {a} and {b}.",
    "Mother at {w} weeks: both {a} and {b}. Risk assessment needed.",
]

MULTI_TMPL_WITH_VITALS = [
    "Patient is {w} weeks pregnant with {a} and {b}. Vitals: {vstr}.",
    "{w}-week patient: {a}, {b}. {vstr}.",
    "ASHA visit: {w}w, {a} also {b}. Measurements: {vstr}.",
    "{w}w pregnant woman — {a} and {b}. I measured {vstr}.",
    "Pregnant woman {w} weeks. {a} and {b}. {vstr} recorded today.",
]


def generate_multi_symptom(n: int = 400) -> list:
    data = []
    for _ in range(n):
        combo = random.choice(MULTI_COMBOS)
        risk = combo["risk"]
        w = random.randint(8, 40)
        a = random.choice(combo["phrases_a"])
        b = random.choice(combo["phrases_b"])
        vitals = combo["vitals_gen"]()
        vstr = _vitals_str(vitals)

        if vitals and random.random() < 0.60:
            tmpl = random.choice(MULTI_TMPL_WITH_VITALS)
            user_msg = tmpl.format(w=w, a=a, b=b, vstr=vstr)
        else:
            tmpl = random.choice(MULTI_TMPL_NO_VITALS)
            user_msg = tmpl.format(w=w, a=a, b=b)

        args = {"symptoms": combo["canonical"], "vitals": vitals} if vitals else {"symptoms": combo["canonical"]}
        tool_call = {"name": "assess_danger_signs", "arguments": args}
        tool_block = f"```json\n{json.dumps(tool_call)}\n```"

        if risk == "RED":
            reasoning = (
                f"RED. {a.capitalize()} with {b} at {w} weeks indicates {combo['clinical']}. "
                f"{combo['response']}"
            )
        else:
            reasoning = (
                f"YELLOW. {a.capitalize()} with {b} at {w} weeks — {combo['clinical']}. "
                f"{combo['response']}"
            )

        model_msg = f"{tool_block}\n\n{reasoning}"
        data.append({
            "conversations": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
                {"role": "model",  "content": model_msg},
            ]
        })
    return data


# ── Confuser / edge cases ─────────────────────────────────────────────────────
# Teach thresholds: mild headache ≠ severe, ankle swelling ≠ facial oedema,
# 37.5C ≠ fever, Hb 7.5 is borderline YELLOW not GREEN.

CONFUSER_SPECS = [
    {
        "user_tmpl": "Patient is {w} weeks pregnant with a mild headache. BP is normal.",
        "signs": ["mild headache"], "risk": "GREEN", "vitals": {},
        "reasoning": "GREEN. Mild headache with normal BP at {w} weeks is a common pregnancy complaint, not a danger sign. Continue routine monitoring and advise rest.",
    },
    {
        "user_tmpl": "ASHA visit: {w}-week patient, mild ankle swelling only. BP 120/80.",
        "signs": ["mild ankle swelling"], "risk": "GREEN", "vitals": {"bp_sys": 120, "bp_dia": 80},
        "reasoning": "GREEN. Mild ankle swelling with normal BP at {w} weeks is physiological oedema, a normal finding. Continue monitoring.",
    },
    {
        "user_tmpl": "{w}w patient, temperature 37.5C. No other complaints.",
        "signs": ["low-grade fever"], "risk": "GREEN", "vitals": {"temp_c": 37.5},
        "reasoning": "GREEN. Temperature 37.5C is below the 38C danger threshold at {w} weeks. Monitor and advise paracetamol if uncomfortable.",
    },
    {
        "user_tmpl": "Patient is {w} weeks, Hb 7.5 on report. Feels mildly tired.",
        "signs": ["fatigue"], "risk": "YELLOW", "vitals": {"hb": 7.5},
        "reasoning": "YELLOW. Haemoglobin 7.5 at {w} weeks is borderline low and warrants evaluation for iron supplementation. Refer to clinic.",
    },
    {
        "user_tmpl": "{w}-week patient: headache persisting for 3 days. BP 140/90.",
        "signs": ["persistent headache"], "risk": "YELLOW", "vitals": {"bp_sys": 140, "bp_dia": 90},
        "reasoning": "YELLOW. Persistent headache with BP at the 140/90 threshold at {w} weeks requires evaluation. Refer to clinic within 24 hours.",
    },
    {
        "user_tmpl": "Patient is {w} weeks, swollen face and hands. BP 143/94.",
        "signs": ["oedema above ankles"], "risk": "YELLOW", "vitals": {"bp_sys": 143, "bp_dia": 94},
        "reasoning": "YELLOW. Facial and hand swelling with elevated BP at {w} weeks indicates fluid retention. Refer within 24 hours.",
    },
    {
        "user_tmpl": "ASHA visit: {w}w patient, Hb 6.2, feeling very weak and dizzy.",
        "signs": ["severe anaemia"], "risk": "YELLOW", "vitals": {"hb": 6.2},
        "reasoning": "YELLOW. Haemoglobin 6.2 is severe anaemia at {w} weeks. Refer to facility within 24 hours for iron infusion or transfusion evaluation.",
    },
    {
        "user_tmpl": "Patient is {w} weeks pregnant with breast tenderness and frequent urination.",
        "signs": ["mild breast tenderness", "frequent urination"], "risk": "GREEN", "vitals": {},
        "reasoning": "GREEN. Breast tenderness and frequent urination at {w} weeks are normal early pregnancy symptoms. Reassure and continue routine ANC.",
    },
    {
        "user_tmpl": "{w}-week patient — mild heartburn after eating. No other complaints.",
        "signs": ["mild heartburn"], "risk": "GREEN", "vitals": {},
        "reasoning": "GREEN. Mild heartburn at {w} weeks is very common in pregnancy. Advise small frequent meals and avoid lying down after eating.",
    },
    {
        "user_tmpl": "Patient is {w} weeks with fever 38.1C. Feels unwell but no other signs.",
        "signs": ["high fever"], "risk": "YELLOW", "vitals": {"temp_c": 38.1},
        "reasoning": "YELLOW. Fever of 38.1C just above the 38C threshold at {w} weeks needs evaluation. Refer to clinic and advise hydration.",
    },
    {
        "user_tmpl": "{w}w patient. Morning sickness and mild nausea, especially after waking up.",
        "signs": ["mild nausea"], "risk": "GREEN", "vitals": {},
        "reasoning": "GREEN. Morning sickness is very common at {w} weeks. Reassure and advise small frequent meals.",
    },
    {
        "user_tmpl": "Pregnant woman {w} weeks. Fatigue and mild back pain. Eating and sleeping normally.",
        "signs": ["fatigue"], "risk": "GREEN", "vitals": {},
        "reasoning": "GREEN. Fatigue and mild back pain at {w} weeks are expected in pregnancy. No danger signs. Continue routine ANC monitoring.",
    },
]


def generate_confuser(n: int = 150) -> list:
    data = []
    for _ in range(n):
        spec = random.choice(CONFUSER_SPECS)
        w = random.randint(8, 40)
        user_msg = spec["user_tmpl"].format(w=w)
        reasoning = spec["reasoning"].format(w=w)
        vitals = spec["vitals"]
        args = {"symptoms": spec["signs"], "vitals": vitals} if vitals else {"symptoms": spec["signs"]}
        tool_call = {"name": "assess_danger_signs", "arguments": args}
        tool_block = f"```json\n{json.dumps(tool_call)}\n```"
        data.append({
            "conversations": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
                {"role": "model",  "content": f"{tool_block}\n\n{reasoning}"},
            ]
        })
    return data


# ── Hindi code-mix samples ────────────────────────────────────────────────────
# Roman transliteration of Hindi — as ASHA workers type on phone keyboards.
# Teaches the model to extract clinical facts from code-mixed inputs
# and output canonical English JSON + risk classification.

HINDI_CASES = [
    (
        "{w} hafte ki patient ko bahut tez sar dard hai aur aankhein dhundhli ho gayi hain. BP {bp}.",
        ["severe headache", "blurred vision"], "RED",
        lambda: {"bp_sys": random.randint(150, 170), "bp_dia": random.randint(100, 112)},
        "RED. Severe headache with blurred vision and elevated BP is pre-eclampsia. Refer immediately and call 108.",
    ),
    (
        "Meri patient {w} hafte ki pregnant hai. Pichle 12 ghante se bacha bilkul nahi hila.",
        ["no foetal movement"], "RED",
        lambda: {},
        "RED. No foetal movement for 12+ hours is a danger sign. Refer to PHC immediately and call 108 ambulance.",
    ),
    (
        "{w} hafte ki aurat bahut kamzor hai. Blood test mein haemoglobin sirf {hb} aaya.",
        ["severe anaemia"], "YELLOW",
        lambda: {"hb": round(random.uniform(5.5, 6.9), 1)},
        "YELLOW. Severe anaemia (Hb <7) needs urgent evaluation. Refer to clinic within 24 hours.",
    ),
    (
        "Patient {w} hafte pregnant, sar dard {days} din se hai. BP {bp}.",
        ["persistent headache"], "YELLOW",
        lambda: {"bp_sys": random.randint(140, 152), "bp_dia": random.randint(90, 98)},
        "YELLOW. Persistent headache with elevated BP needs evaluation. Refer to clinic within 24 hours.",
    ),
    (
        "{w} hafte ki patient ko bahut tej pet dard ho raha hai aur bleeding bhi hai.",
        ["severe abdominal pain", "heavy vaginal bleeding"], "RED",
        lambda: {},
        "RED. Severe abdominal pain with vaginal bleeding is an emergency. Call 108 immediately.",
    ),
    (
        "Patient {w} hafte ki pregnant, sirf subah ki ulti aur halka ji ghabrana hai.",
        ["mild nausea"], "GREEN",
        lambda: {},
        "GREEN. Morning sickness and mild nausea at {w} weeks is normal in pregnancy. Continue routine monitoring.",
    ),
    (
        "{w} hafte ki maa ko tej bukhaar hai, temperature {temp}C. Kaanp bhi rahi hai.",
        ["high fever"], "YELLOW",
        lambda: {"temp_c": round(random.uniform(38.5, 40.0), 1)},
        "YELLOW. Fever above 38C at {w} weeks needs evaluation. Refer to clinic within 24 hours.",
    ),
    (
        "Patient ke haath aur chehra sooja hua hai. {w} hafte, BP {bp}.",
        ["oedema above ankles"], "YELLOW",
        lambda: {"bp_sys": random.randint(138, 152), "bp_dia": random.randint(88, 97)},
        "YELLOW. Facial and hand swelling with elevated BP needs attention. Refer within 24 hours.",
    ),
    (
        "{w} hafte ki patient — aankhein peeli ho gayi hain. Bukhaar bhi hai {temp}C.",
        ["jaundice", "high fever"], "YELLOW",
        lambda: {"temp_c": round(random.uniform(38.5, 39.5), 1)},
        "YELLOW. Jaundice with fever at {w} weeks needs urgent evaluation. Refer to facility within 24 hours.",
    ),
    (
        "Patient ko fits aayi. {w} hafte pregnant. BP {bp}. Hosh bhi chali gayi thi.",
        ["convulsions", "loss of consciousness"], "RED",
        lambda: {"bp_sys": random.randint(160, 185), "bp_dia": random.randint(108, 120)},
        "RED. Convulsions with loss of consciousness is eclampsia. Call 108 immediately.",
    ),
    (
        "{w} hafte — thodi thakaan aur halki kamar dard. Koi aur problem nahi.",
        ["fatigue"], "GREEN",
        lambda: {},
        "GREEN. Fatigue and mild backache at {w} weeks are normal in pregnancy. Reassure and continue monitoring.",
    ),
    (
        "ASHA report: {w}w patient, bleeding bahut zyada ho rahi hai.",
        ["heavy vaginal bleeding"], "RED",
        lambda: {},
        "RED. Heavy vaginal bleeding is a danger sign. Refer to PHC immediately and call 108.",
    ),
    (
        "{w} hafte ki patient — pichle 2 din se sar dard hai. Chehra bhi thoda sooja.",
        ["persistent headache", "oedema above ankles"], "YELLOW",
        lambda: {"bp_sys": random.randint(138, 150), "bp_dia": random.randint(88, 95)},
        "YELLOW. Persistent headache with facial swelling is an early warning sign. Refer within 24 hours.",
    ),
    (
        "Patient {w} hafte pregnant. Haemoglobin 6.0, bahut pale aur kamzor dikh rahi hai.",
        ["severe anaemia"], "YELLOW",
        lambda: {"hb": 6.0},
        "YELLOW. Haemoglobin 6.0 is severe anaemia. Refer to facility within 24 hours.",
    ),
    (
        "{w} hafte — pet mein bahut dard. Bacha hil nahi raha.",
        ["severe abdominal pain", "no foetal movement"], "RED",
        lambda: {},
        "RED. Severe abdominal pain with no foetal movement is a danger sign. Call 108 immediately.",
    ),
]


def generate_hindi(n: int = 150) -> list:
    data = []
    for _ in range(n):
        tmpl, signs, risk, vitals_gen, reasoning_tmpl = random.choice(HINDI_CASES)
        w = random.randint(8, 40)
        vitals = vitals_gen()
        days = random.randint(1, 5)

        fmt = {"w": w, "days": days}
        if "bp_sys" in vitals and "bp_dia" in vitals:
            fmt["bp"] = f"{vitals['bp_sys']}/{vitals['bp_dia']}"
        if "hb" in vitals:
            fmt["hb"] = vitals["hb"]
        if "temp_c" in vitals:
            fmt["temp"] = vitals["temp_c"]

        try:
            user_msg = tmpl.format(**fmt)
        except KeyError:
            user_msg = tmpl.format(w=w, days=days, bp="150/100", hb=6.5, temp=39.0)

        reasoning = reasoning_tmpl.replace("{w}", str(w))
        args = {"symptoms": signs, "vitals": vitals} if vitals else {"symptoms": signs}
        tool_call = {"name": "assess_danger_signs", "arguments": args}
        tool_block = f"```json\n{json.dumps(tool_call)}\n```"

        data.append({
            "conversations": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
                {"role": "model",  "content": f"{tool_block}\n\n{reasoning}"},
            ]
        })
    return data


# ── Narrative / free-form samples ─────────────────────────────────────────────
# Longer ASHA diary-style inputs. Teaches the model to extract clinical
# facts from conversational prose — closer to real-world usage.

NAMES = [
    "Lakshmi", "Kavitha", "Meena", "Savitri", "Radha",
    "Suma", "Geeta", "Anitha", "Usha", "Priya",
    "Shobha", "Vimala", "Manjula", "Rekha", "Saritha",
]

NARRATIVE_CASES = [
    (
        "I visited {name}, a {age}-year-old woman in the village. She is {w} weeks pregnant. "
        "She told me she has had a very bad headache since this morning and everything looks blurry. "
        "When I measured her BP it was {bp}. I am very worried. What should I do?",
        ["severe headache", "blurred vision"], "RED",
        lambda: {"bp_sys": random.randint(152, 172), "bp_dia": random.randint(100, 113)},
        "RED. Severe headache with blurred vision and elevated BP is pre-eclampsia. Refer to PHC immediately and call 108 ambulance.",
    ),
    (
        "Today during home visit I found {name}, {w} weeks pregnant. "
        "Her husband said she had a fit last night — shook all over and went unconscious for a few minutes. "
        "BP is {bp}. She is scared.",
        ["convulsions", "loss of consciousness"], "RED",
        lambda: {"bp_sys": random.randint(160, 182), "bp_dia": random.randint(108, 119)},
        "RED. Convulsions with loss of consciousness is eclampsia. Call 108 ambulance immediately.",
    ),
    (
        "{name} is {w} weeks pregnant. She came to me saying the baby has not moved at all "
        "since yesterday afternoon. She is very scared. No pain, no bleeding.",
        ["no foetal movement"], "RED",
        lambda: {},
        "RED. No foetal movement for 12+ hours is a danger sign. Refer to PHC immediately and call 108.",
    ),
    (
        "I am doing my monthly rounds. {name} is {w} weeks, feeling very tired and weak for the past week. "
        "The ANM says the haemoglobin report last month was only {hb}. Should I refer her?",
        ["severe anaemia"], "YELLOW",
        lambda: {"hb": round(random.uniform(5.5, 7.5), 1)},
        "YELLOW. Haemoglobin below 7 is severe anaemia requiring evaluation. Refer to clinic within 24 hours.",
    ),
    (
        "Visited {name} today — {w} weeks pregnant. Headache for three days. "
        "Her face looked puffy and hands were swollen. BP measured: {bp}. Not sure how serious.",
        ["oedema above ankles", "persistent headache"], "YELLOW",
        lambda: {"bp_sys": random.randint(138, 153), "bp_dia": random.randint(88, 98)},
        "YELLOW. Persistent headache with facial swelling and elevated BP is an early pre-eclampsia warning. Refer within 24 hours.",
    ),
    (
        "The patient {name} is {w} weeks pregnant. She has fever since morning — temperature {temp}C. "
        "Shivering and body aches. I noticed her eyes look slightly yellow.",
        ["high fever", "jaundice"], "YELLOW",
        lambda: {"temp_c": round(random.uniform(38.5, 39.8), 1)},
        "YELLOW. Fever with jaundice at {w} weeks needs urgent evaluation. Refer to facility within 24 hours.",
    ),
    (
        "{name} is {age} years old, {w} weeks pregnant. She is only complaining of morning sickness — "
        "nauseous every morning but it passes by 10am. All other vitals are normal. First pregnancy.",
        ["mild nausea"], "GREEN",
        lambda: {},
        "GREEN. Morning sickness at {w} weeks is a normal early pregnancy symptom. Reassure and advise small frequent meals.",
    ),
    (
        "During today's ANC visit I checked {name}, {w} weeks pregnant. A bit tired but says it is normal. "
        "Mild backache. Eating well. BP is normal. Baby movements felt normal.",
        ["fatigue"], "GREEN",
        lambda: {"bp_sys": random.randint(110, 125), "bp_dia": random.randint(70, 82)},
        "GREEN. Fatigue and mild back pain at {w} weeks are expected in pregnancy. No danger signs. Continue routine monitoring.",
    ),
    (
        "{name} had sudden very severe abdominal pain this morning at {w} weeks. "
        "Started without warning. Also has some vaginal bleeding. Very scared.",
        ["severe abdominal pain", "heavy vaginal bleeding"], "RED",
        lambda: {},
        "RED. Severe abdominal pain with vaginal bleeding suggests placental abruption. Call 108 immediately.",
    ),
    (
        "I visited a {w}-week patient this evening. She woke up and suddenly could not see clearly — "
        "spots in front of her eyes. Also has a bad headache. BP reading was {bp}.",
        ["blurred vision", "severe headache"], "RED",
        lambda: {"bp_sys": random.randint(155, 175), "bp_dia": random.randint(102, 115)},
        "RED. Visual disturbance with severe headache and elevated BP is pre-eclampsia. Refer immediately and call 108.",
    ),
    (
        "{name} is {w} weeks pregnant. She mentioned fewer baby kicks — maybe half of what she usually feels. "
        "No pain. I also noticed she looks quite pale. Hb {hb} from last report.",
        ["reduced foetal movement", "severe anaemia"], "YELLOW",
        lambda: {"hb": round(random.uniform(5.5, 7.5), 1)},
        "YELLOW. Reduced foetal movement with severe anaemia needs urgent evaluation. Refer within 24 hours.",
    ),
    (
        "Today I met {name} in the village, {w} weeks pregnant. Only complains of frequent trips to the bathroom "
        "and sore breasts. No headache, no swelling, BP normal. First pregnancy.",
        ["frequent urination", "mild breast tenderness"], "GREEN",
        lambda: {},
        "GREEN. Frequent urination and breast tenderness at {w} weeks are normal early pregnancy symptoms. Continue routine ANC.",
    ),
]


def generate_narrative(n: int = 100) -> list:
    data = []
    attempts = 0
    while len(data) < n and attempts < n * 3:
        attempts += 1
        tmpl, signs, risk, vitals_gen, reasoning = random.choice(NARRATIVE_CASES)
        w = random.randint(8, 40)
        vitals = vitals_gen()
        name = random.choice(NAMES)
        age = random.randint(18, 38)

        fmt = {"w": w, "name": name, "age": age}
        if "bp_sys" in vitals and "bp_dia" in vitals:
            fmt["bp"] = f"{vitals['bp_sys']}/{vitals['bp_dia']}"
        if "hb" in vitals:
            fmt["hb"] = vitals["hb"]
        if "temp_c" in vitals:
            fmt["temp"] = vitals["temp_c"]

        try:
            user_msg = tmpl.format(**fmt)
        except (KeyError, ValueError):
            continue

        args = {"symptoms": signs, "vitals": vitals} if vitals else {"symptoms": signs}
        tool_call = {"name": "assess_danger_signs", "arguments": args}
        tool_block = f"```json\n{json.dumps(tool_call)}\n```"

        data.append({
            "conversations": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
                {"role": "model",  "content": f"{tool_block}\n\n{reasoning}"},
            ]
        })
    return data


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    random.seed(42)
    print("Generating 1,500-sample Saheli ANC training dataset...")
    print("  700  single-symptom")
    print("  400  multi-symptom combinations")
    print("  150  confuser / edge cases")
    print("  150  Hindi code-mix")
    print("  100  free-form narrative")

    single    = generate_single_symptom(700)
    multi     = generate_multi_symptom(400)
    confuser  = generate_confuser(150)
    hindi     = generate_hindi(150)
    narrative = generate_narrative(100)

    all_data = single + multi + confuser + hindi + narrative
    random.shuffle(all_data)
    print(f"\nTotal samples generated: {len(all_data)}")

    ds = Dataset.from_list(all_data)
    split1 = ds.train_test_split(test_size=0.2, seed=42)
    split2 = split1["test"].train_test_split(test_size=0.5, seed=42)

    final = DatasetDict({
        "train":      split1["train"],
        "validation": split2["train"],
        "test":       split2["test"],
    })

    output_dir = "./finetune/datasets/saheli_anc_dataset"
    os.makedirs(output_dir, exist_ok=True)
    final.save_to_disk(output_dir)

    print(f"\nSaved to: {output_dir}")
    print(f"  Train      : {len(final['train'])}")
    print(f"  Validation : {len(final['validation'])}")
    print(f"  Test       : {len(final['test'])}")

    print("\nSample conversation (first train row):")
    for turn in final["train"][0]["conversations"]:
        print(f"  [{turn['role']}]")
        print(f"    {turn['content'][:120]}")

    # ── Export Unsloth Studio JSONL ───────────────────────────────────────────
    role_map = {"system": "system", "user": "human", "model": "gpt"}
    jsonl_path = "./finetune/datasets/saheli_anc_dataset.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for row in all_data:
            sharegpt = {
                "conversations": [
                    {"from": role_map[t["role"]], "value": t["content"]}
                    for t in row["conversations"]
                ]
            }
            f.write(json.dumps(sharegpt, ensure_ascii=False) + "\n")
    print(f"\nUnsloth Studio JSONL: {jsonl_path}  ({len(all_data)} rows)")


if __name__ == "__main__":
    main()
