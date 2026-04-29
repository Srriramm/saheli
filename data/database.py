import sqlite3
import json
import logging
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from config.settings import DATABASE_PATH

def get_connection():
    """Returns a SQLite connection to the patient offline database."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Initializes SQLite schema for Patients and Visits."""
    logging.info(f"Initializing database at {DATABASE_PATH}")
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            name TEXT,
            age INTEGER,
            lmp_date TEXT,
            village TEXT,
            asha_id TEXT,
            created_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id TEXT PRIMARY KEY,
            patient_id TEXT,
            visit_date TEXT,
            symptoms_reported TEXT,
            image_path TEXT,
            risk_level TEXT,
            danger_signs TEXT,
            recommendation TEXT,
            referral_facility TEXT,
            gestational_week INTEGER,
            model_version TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    """)
    
    conn.commit()
    conn.close()

def log_patient_record(patient_id: str, visit_data: Dict) -> Dict:
    """Inserts a new visit for a given patient."""
    # Ensure patient exists
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM patients WHERE id = ?", (patient_id,))
    if not c.fetchone():
        # Auto-create minimal patient if not found
        c.execute("""
            INSERT INTO patients (id, asha_id, created_at)
            VALUES (?, ?, ?)
        """, (patient_id, "ASHA-DEFAULT", datetime.now().isoformat()))
        conn.commit()

    record_id = str(uuid.uuid4())
    symptoms = json.dumps(visit_data.get('symptoms', []))
    danger_signs = json.dumps(visit_data.get('danger_signs', []))
    
    c.execute("""
        INSERT INTO visits (
            id, patient_id, visit_date, symptoms_reported, 
            image_path, risk_level, danger_signs, recommendation, 
            referral_facility, gestational_week, model_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record_id,
        patient_id,
        datetime.now().isoformat(),
        symptoms,
        visit_data.get('image_path', ''),
        visit_data.get('risk_level', ''),
        danger_signs,
        visit_data.get('recommendation', ''),
        visit_data.get('referral_facility', ''),
        visit_data.get('gestational_week', 0),
        "saheli-gemma4-e4b-v1"
    ))
    
    conn.commit()
    conn.close()
    
    logging.info(f"Logged visit {record_id} for patient {patient_id}")
    return {"success": True, "record_id": record_id}

def get_patient_history(patient_id: str) -> Dict:
    """Retrieves all visits for a patient to determine historical risk trend."""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT * FROM visits WHERE patient_id = ? ORDER BY visit_date DESC", (patient_id,))
    rows = c.fetchall()
    conn.close()
    
    visits = [dict(row) for row in rows]
    
    # Simple risk trend heuristic
    trend = "Stable"
    if len(visits) >= 2:
        prev_risk = visits[1]['risk_level']
        curr_risk = visits[0]['risk_level']
        if prev_risk == 'GREEN' and curr_risk in ['YELLOW', 'RED']:
            trend = "Deteriorating"
        elif prev_risk in ['YELLOW', 'RED'] and curr_risk == 'GREEN':
            trend = "Improving"
            
    return {"visits": visits, "risk_trend": trend}

# Auto-initialize on module load
initialize_database()
