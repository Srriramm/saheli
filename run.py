"""
run.py — Main entry point for Saheli.

Usage:
  python run.py            # Start FastAPI server (default, port 5000)
  python run.py --cli      # Interactive CLI triage loop
  python run.py --test     # Run evaluation benchmark
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).parent))

from data.database import initialize_database
from config.settings import MODEL_PATH, DEFAULT_LANGUAGE


def start_ui():
    """Launch the FastAPI server with uvicorn."""
    import uvicorn
    print("Starting Saheli API at http://0.0.0.0:5000")
    print("Docs available at http://localhost:5000/docs")
    uvicorn.run("ui.app:app", host="0.0.0.0", port=5000, reload=False)


def start_cli():
    """Interactive command-line triage loop for testing / demo."""
    from core.triage_engine import TriageEngine

    engine = TriageEngine(model_path=MODEL_PATH)
    print("\nSaheli CLI — Offline Maternal Health Triage")
    print("Type 'quit' to exit.\n")

    while True:
        patient_id = input("Patient ID (e.g. KA-VLG-001): ").strip()
        if patient_id.lower() == "quit":
            break

        language = input(f"Language [{DEFAULT_LANGUAGE}]: ").strip() or DEFAULT_LANGUAGE
        voice_input = input("Describe symptoms: ").strip()
        image_path = input("Image path (leave blank to skip): ").strip() or None

        result = engine.run_triage(
            patient_id=patient_id,
            language=language,
            voice_input=voice_input,
            image_path=image_path or None
        )

        print(f"\n--- RESULT ---")
        print(f"Risk Level : {result.risk_level}")
        print(f"Danger Signs: {result.danger_signs_found}")
        print(f"Response   : {result.spoken_response}")
        if result.referral_info:
            print(f"Refer to   : {result.referral_info.get('facility_name')} "
                  f"({result.referral_info.get('distance_km')} km)")
        print(f"Record ID  : {result.patient_record_id}")
        print("--------------\n")


def run_benchmark():
    """Run evaluation benchmark on 20 test cases."""
    from finetune.evaluate_model import run_evaluation
    run_evaluation(MODEL_PATH)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    initialize_database()

    parser = argparse.ArgumentParser(description="Saheli — Offline Maternal Health Companion")
    parser.add_argument("--cli", action="store_true", help="Run interactive CLI triage")
    parser.add_argument("--test", action="store_true", help="Run evaluation benchmark")
    args = parser.parse_args()

    if args.cli:
        start_cli()
    elif args.test:
        run_benchmark()
    else:
        start_ui()
