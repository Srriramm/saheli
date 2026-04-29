// Change this to your laptop's LAN IP when running Flask on a local network.
// Example: 'http://192.168.1.42:5000'
// For Android emulator pointing at host: 'http://10.0.2.2:5000'
export const BASE_URL = 'http://192.168.0.5:5000';

export interface TriageResult {
  transcript?: string;
  risk_level: 'RED' | 'YELLOW' | 'GREEN';
  danger_signs: string[];
  referral?: {
    facility_name: string;
    distance_km: number;
    contact?: string;
    address?: string;
  } | null;
  response: string;
  record_id?: string;
}

export interface PatientRecord {
  record_id: string;
  timestamp: string;
  risk_level: string;
  danger_signs: string[];
  recommendation: string;
}

async function checkJson(res: Response) {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

export async function transcribeAndTriage(
  audioUri: string,
  language: string,
  patientId: string
): Promise<TriageResult> {
  const form = new FormData();
  form.append('audio', { uri: audioUri, type: 'audio/m4a', name: 'recording.m4a' } as any);
  form.append('language', language);
  form.append('patient_id', patientId);
  const res = await fetch(`${BASE_URL}/transcribe-and-triage`, { method: 'POST', body: form });
  return checkJson(res);
}

export async function submitPhoto(
  photoUri: string,
  language: string,
  patientId: string,
  transcript = ''
): Promise<TriageResult> {
  const form = new FormData();
  form.append('photo', { uri: photoUri, type: 'image/jpeg', name: 'photo.jpg' } as any);
  form.append('language', language);
  form.append('patient_id', patientId);
  form.append('transcript', transcript);
  const res = await fetch(`${BASE_URL}/submit-photo`, { method: 'POST', body: form });
  return checkJson(res);
}

export async function runTriageText(
  transcript: string,
  language: string,
  patientId: string,
  latitude?: number,
  longitude?: number
): Promise<TriageResult> {
  const res = await fetch(`${BASE_URL}/run-triage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transcript, language, patient_id: patientId, latitude, longitude }),
  });
  return checkJson(res);
}

export async function getPatientHistory(patientId: string): Promise<PatientRecord[]> {
  const res = await fetch(`${BASE_URL}/patient/${encodeURIComponent(patientId)}`);
  return checkJson(res);
}

export async function newPatient(data: {
  patient_id: string;
  name?: string;
  age?: number;
  lmp_date?: string;
  village?: string;
  asha_id?: string;
}): Promise<{ success: boolean; patient_id: string }> {
  const res = await fetch(`${BASE_URL}/new-patient`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return checkJson(res);
}
