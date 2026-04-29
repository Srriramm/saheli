# Saheli Mobile App

React Native + Expo mobile frontend for the Saheli maternal health triage system.

## Prerequisites

- Node.js 18+
- Expo CLI: `npm install -g expo-cli`
- Expo Go app on your phone (iOS / Android)

## Setup

```bash
cd app
npm install
```

## Configure backend URL

Open `src/api/saheliApi.ts` and set `BASE_URL` to your laptop's LAN IP:

```typescript
export const BASE_URL = 'http://192.168.1.XX:5000';  // replace XX with your IP
```

Find your IP with `ipconfig` (Windows) or `ifconfig` (Mac/Linux).

## Run

**Terminal 1 — Backend:**
```bash
cd ..   # project root
pip install flask-cors
python run.py
```

**Terminal 2 — Mobile:**
```bash
cd app
npx expo start
```

Scan the QR code with Expo Go on your phone. Both must be on the same Wi-Fi network.

## App Flow

```
Splash → Language Select → Triage (voice / camera / text) → Result → History
```

## Demo Script (3 min)

1. Splash screen — Saheli logo animation
2. Select **தமிழ்** (Tamil)
3. Tap mic, speak: *"32 வார கர்ப்பிணி, கடுமையான தலைவலி, பார்வை மங்கல், BP 150/100"*
4. **RED emergency overlay** fills screen, AI speaks Tamil response
5. Tap "CALL 108" — shows dialer
6. Demo YELLOW: type "swollen face and hands, 28 weeks"
7. Show History screen
