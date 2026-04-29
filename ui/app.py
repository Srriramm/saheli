import os
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.triage_engine import TriageEngine
from core.translations import explain_triage_result, translate_danger_signs
from config.settings import MODEL_PATH, DEFAULT_LANGUAGE

UPLOAD_FOLDER = Path('./data/uploads')
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Saheli API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    engine = TriageEngine(model_path=MODEL_PATH)
except Exception as e:
    logging.error(f"Failed to initialize TriageEngine: {e}")
    engine = None


def _result_payload(result, language: str, transcript: Optional[str] = None):
    return {
        "transcript":       transcript,
        "risk_level":       result.risk_level,
        "danger_signs":     translate_danger_signs(result.danger_signs_found, language),
        "referral":         result.referral_info,
        "response":         result.spoken_response,
        "reasoning":        explain_triage_result(result.risk_level, result.danger_signs_found, language),
        "location_source":  result.location_source,
        "latitude":         result.latitude,
        "longitude":        result.longitude,
        "record_id":        result.patient_record_id,
    }


@app.get("/")
def health():
    return {"service": "Saheli", "status": "running"}


@app.post("/submit-photo")
def submit_photo(
    photo: UploadFile = File(...),
    patient_id: str = Form(default="ANON-001"),
    language: str = Form(default=DEFAULT_LANGUAGE),
    transcript: str = Form(default="I took a photo of the patient's symptoms."),
    latitude: Optional[float] = Form(default=None),
    longitude: Optional[float] = Form(default=None),
):
    filepath = UPLOAD_FOLDER / (photo.filename or "photo.jpg")
    with open(filepath, "wb") as f:
        shutil.copyfileobj(photo.file, f)

    if not engine:
        raise HTTPException(status_code=503, detail="Triage engine not available")

    try:
        result = engine.run_triage(
            patient_id=patient_id,
            language=language,
            voice_input=transcript,
            image_path=str(filepath),
            latitude=latitude,
            longitude=longitude,
        )
        return _result_payload(result, language, transcript)
    except Exception as e:
        logging.error(f"Photo triage failed: {e}")
        raise HTTPException(status_code=500, detail="Image analysis failed")


class TriageRequest(BaseModel):
    patient_id: str = "ANON-001"
    language: str = DEFAULT_LANGUAGE
    transcript: str = ""
    image_path: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@app.post("/run-triage")
def run_triage(body: TriageRequest):
    if not body.transcript and not body.image_path:
        raise HTTPException(status_code=400, detail="transcript or image_path required")

    if not engine:
        raise HTTPException(status_code=503, detail="Triage engine not available")

    try:
        result = engine.run_triage(
            patient_id=body.patient_id,
            language=body.language,
            voice_input=body.transcript,
            image_path=body.image_path,
            latitude=body.latitude,
            longitude=body.longitude,
        )
        return _result_payload(result, body.language)
    except Exception as e:
        logging.error(f"run-triage failed: {e}")
        raise HTTPException(status_code=500, detail="Triage failed")


@app.get("/patient/{patient_id}")
def view_patient(patient_id: str):
    from data.database import get_patient_history
    return get_patient_history(patient_id)


class NewPatientRequest(BaseModel):
    patient_id: str
    name: str = ""
    age: Optional[int] = None
    lmp_date: str = ""
    village: str = ""
    asha_id: str = ""


@app.post("/new-patient")
def new_patient(body: NewPatientRequest):
    from data.database import get_connection
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO patients (id, name, age, lmp_date, village, asha_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (body.patient_id, body.name, body.age, body.lmp_date,
             body.village, body.asha_id, datetime.now().isoformat()),
        )
        conn.commit()
        return {"success": True, "patient_id": body.patient_id}
    except Exception as e:
        logging.error(f"new-patient failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/referrals")
def get_referrals():
    try:
        with open("./data/referral_data.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
