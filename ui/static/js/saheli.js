/* Saheli — Triage UI logic */
'use strict';

/* ── Demo case data ─────────────────────────────────────────── */
const DEMOS = {
  red: {
    patient: 'KA-VLG-042',
    weeks:   '32',
    text:    'Patient is 32 weeks pregnant with severe headache and blurred vision. BP is 150 over 100.'
  },
  yellow: {
    patient: 'KA-VLG-017',
    weeks:   '24',
    text:    'Patient is 24 weeks pregnant, feeling very weak. Haemoglobin is 6.5.'
  },
  green: {
    patient: 'KA-VLG-008',
    weeks:   '10',
    text:    'Patient is 10 weeks pregnant with mild nausea and morning sickness.'
  }
};

const RISK_ICONS = { 
  RED: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>', 
  YELLOW: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>', 
  GREEN: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>' 
};
const RISK_LABELS = {
  RED:    'EMERGENCY',
  YELLOW: 'CAUTION',
  GREEN:  'ROUTINE'
};

/* ── DOM helpers ────────────────────────────────────────────── */
const $ = id => document.getElementById(id);

function show(el, cls) {
  el.classList.add(cls || 'active');
}
function hide(el, cls) {
  el.classList.remove(cls || 'active');
}

/* ── Fill quick-demo ────────────────────────────────────────── */
function fillDemo(level) {
  const d = DEMOS[level];
  $('patient-id').value    = d.patient;
  $('weeks').value         = d.weeks;
  $('symptom-text').value  = d.text;
  updateCharCount();
  $('symptom-text').focus();
}
window.fillDemo = fillDemo;

/* ── Char count ─────────────────────────────────────────────── */
function updateCharCount() {
  const len = $('symptom-text').value.length;
  $('char-count').textContent = len + ' chars';
}

/* ── Reset all result UI ────────────────────────────────────── */
function resetResult() {
  hide($('result-card'));
  hide($('referral-card'));
  hide($('emergency-overlay'));
  $('result-card').className = 'result-card';
}

/* ── Show result ────────────────────────────────────────────── */
function showResult(data) {
  resetResult();
  const level   = (data.risk_level || 'UNKNOWN').toUpperCase();
  const signs   = data.danger_signs || [];
  const response= data.response || '';
  const referral= data.referral;

  if (level === 'RED') {
    /* Full-screen emergency overlay */
    $('em-msg').textContent   = response;
    $('em-signs').textContent = signs.length ? 'Signs: ' + signs.join(' · ') : '';
    show($('emergency-overlay'));
  } else {
    /* Inline result card */
    const header = $('result-header');
    header.className = 'result-header ' + level;

    $('result-icon').innerHTML      = RISK_ICONS[level]  || '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>';
    $('result-level').textContent   = RISK_LABELS[level] || level;
    $('result-keysign').textContent = signs.length ? signs[0] : '';
    $('result-response').textContent = response;

    /* Danger sign chips */
    const chips = $('result-chips');
    chips.innerHTML = '';
    signs.forEach(s => {
      const chip = document.createElement('span');
      chip.className  = 'sign-chip ' + level;
      chip.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>' + s;
      chips.appendChild(chip);
    });
    $('signs-section').style.display = signs.length ? 'block' : 'none';

    show($('result-card'));
  }

  /* Referral info */
  if (referral) {
    $('ref-name').textContent = referral.facility_name || '';
    $('ref-dist').textContent = `${referral.distance_km} km away`;
    const phone = referral.phone || '104';
    $('ref-phone').innerHTML   = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg> ' + phone;
    $('ref-phone').href        = 'tel:' + phone;
    show($('referral-card'));
  }
}

/* ── Dismiss emergency overlay ──────────────────────────────── */
function dismissEmergency() {
  hide($('emergency-overlay'));
}
window.dismissEmergency = dismissEmergency;

/* ── Loading state ──────────────────────────────────────────── */
function setLoading(on) {
  const card  = $('loading-card');
  const submit= $('btn-submit');
  if (on) {
    show(card);
    submit.disabled = true;
    resetResult();
  } else {
    hide(card);
    submit.disabled = false;
  }
}

/* ── GPS location (best-effort) ─────────────────────────────── */
let _cachedGps = null;
function _fetchGps() {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(
    pos => { _cachedGps = { latitude: pos.coords.latitude, longitude: pos.coords.longitude }; },
    ()  => { /* denied or unavailable — fall back to server default */ }
  );
}
document.addEventListener('DOMContentLoaded', _fetchGps);

/* ── Text-based triage (primary path) ──────────────────────── */
async function runTriage() {
  const transcript = $('symptom-text').value.trim();
  if (!transcript) {
    alert('Please describe the patient\'s symptoms, or tap a Quick Demo button.');
    return;
  }

  setLoading(true);

  try {
    const body = {
      patient_id: $('patient-id').value || 'ANON-001',
      language:   $('lang-select').value,
      transcript,
      ...(_cachedGps || {})
    };
    const resp = await fetch('/run-triage', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(body)
    });
    const data = await resp.json();
    setLoading(false);
    if (data.error) { alert('Error: ' + data.error); return; }
    showResult(data);
  } catch (e) {
    setLoading(false);
    alert('Network error. Is the server running?');
  }
}
window.runTriage = runTriage;

/* ── Mic recording (browser WebRTC) ────────────────────────── */
let mediaRecorder = null;
let audioChunks   = [];

async function toggleMic() {
  const btn = $('btn-mic');

  if (mediaRecorder && mediaRecorder.state === 'recording') {
    mediaRecorder.stop();
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks   = [];
    btn.classList.add('recording');
    btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/></svg>';
    btn.title = 'Tap to stop recording';

    mediaRecorder.ondataavailable = e => { if (e.data.size) audioChunks.push(e.data); };

    mediaRecorder.onstop = async () => {
      btn.classList.remove('recording');
      btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/></svg>';
      btn.title = 'Record voice';
      stream.getTracks().forEach(t => t.stop());

      const blob = new Blob(audioChunks, { type: 'audio/webm' });
      if (blob.size < 1000) {
        alert('Recording too short — please hold the button and speak, then tap again to stop.');
        setLoading(false);
        return;
      }
      const form = new FormData();
      form.append('audio',      blob, 'recording.webm');
      form.append('language',   $('lang-select').value);
      form.append('patient_id', $('patient-id').value || 'ANON-001');

      setLoading(true);
      try {
        const resp = await fetch('/transcribe-and-triage', { method: 'POST', body: form });
        const data = await resp.json();
        setLoading(false);
        if (data.transcript) $('symptom-text').value = data.transcript;
        if (data.error)      { alert(data.error); return; }
        showResult(data);
      } catch (e) {
        setLoading(false);
        alert('Audio upload failed: ' + e.message);
      }
    };

    mediaRecorder.start();
  } catch (e) {
    alert('Microphone unavailable. Use the text input below instead.');
  }
}
window.toggleMic = toggleMic;

/* ── Audio file upload (mp3, wav, m4a, ogg, webm, etc.) ─────── */
async function handleAudio(input) {
  const file = input.files[0];
  if (!file) return;

  const form = new FormData();
  form.append('audio',      file, file.name);
  form.append('language',   $('lang-select').value);
  form.append('patient_id', $('patient-id').value || 'ANON-001');

  setLoading(true);
  try {
    const resp = await fetch('/transcribe-and-triage', { method: 'POST', body: form });
    const data = await resp.json();
    setLoading(false);
    if (data.transcript) $('symptom-text').value = data.transcript;
    if (data.error) { alert('Audio error: ' + data.error); return; }
    showResult(data);
  } catch (e) {
    setLoading(false);
    alert('Upload failed: ' + e.message);
  }
  input.value = '';  // allow re-selecting same file
}
window.handleAudio = handleAudio;

/* ── Photo upload ───────────────────────────────────────────── */
async function handlePhoto(input) {
  const file = input.files[0];
  if (!file) return;
  const transcript = $('symptom-text').value.trim() || 'Visual assessment via camera.';

  setLoading(true);
  const form = new FormData();
  form.append('photo',      file);
  form.append('language',   $('lang-select').value);
  form.append('patient_id', $('patient-id').value || 'ANON-001');
  form.append('transcript', transcript);

  try {
    const resp = await fetch('/submit-photo', { method: 'POST', body: form });
    const data = await resp.json();
    setLoading(false);
    if (data.error) { alert('Photo error: ' + data.error); return; }
    showResult(data);
  } catch (e) {
    setLoading(false);
    alert('Upload failed: ' + e.message);
  }
}
window.handlePhoto = handlePhoto;

/* ── Enter key submits ──────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  $('symptom-text').addEventListener('keydown', e => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) runTriage();
  });
  $('symptom-text').addEventListener('input', updateCharCount);
});
