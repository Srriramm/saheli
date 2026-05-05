/// Per-language UI strings. ASHA workers in Tamil Nadu read Tamil natively;
/// English fallback is for development and judges.
///
/// Resolved at the call site via `S.of(language).<key>` so no widget needs
/// to know about Localizations or codegen.
library;

class S {
  final String appBarTitle;
  final String patientId;
  final String patientIdHint;
  final String typeSymptoms;
  final String typeSymptomsHint;
  final String analyseSymptoms;
  final String photographSymptoms;
  final String viewPatientHistory;
  final String analysingWithGemma;
  final String dangerSignsDetected;
  final String warningSignsDetected;
  final String normalContinueMonitoring;
  final String aiAssessment;
  final String nextAction;
  final String whyThisResult;
  final String locationUsed;
  final String gpsLocationUsed;
  final String fallbackLocationUsed;
  final String referNow;
  final String continueMonitoring;
  final String dangerSignsFound;
  final String nearestReferralFacility;
  final String transcript;
  final String call108;
  final String newPatient;
  final String history;
  final String kmAway;
  final String cameraPermission;
  final String locationDisabled;
  final String describeSymptomsRequired;
  final String selectLanguage;

  const S({
    required this.appBarTitle,
    required this.patientId,
    required this.patientIdHint,
    required this.typeSymptoms,
    required this.typeSymptomsHint,
    required this.analyseSymptoms,
    required this.photographSymptoms,
    required this.viewPatientHistory,
    required this.analysingWithGemma,
    required this.dangerSignsDetected,
    required this.warningSignsDetected,
    required this.normalContinueMonitoring,
    required this.aiAssessment,
    required this.nextAction,
    required this.whyThisResult,
    required this.locationUsed,
    required this.gpsLocationUsed,
    required this.fallbackLocationUsed,
    required this.referNow,
    required this.continueMonitoring,
    required this.dangerSignsFound,
    required this.nearestReferralFacility,
    required this.transcript,
    required this.call108,
    required this.newPatient,
    required this.history,
    required this.kmAway,
    required this.cameraPermission,
    required this.locationDisabled,
    required this.describeSymptomsRequired,
    required this.selectLanguage,
  });

  static const _ta = S(
    appBarTitle: 'ஆஷா முதன்மை மதிப்பீடு',
    patientId: 'நோயாளி அடையாளம்',
    patientIdHint: 'எ.கா. PATIENT-001',
    typeSymptoms: 'அறிகுறிகளை தட்டச்சு செய்க',
    typeSymptomsHint:
        'எ.கா. 32 வாரம் கர்ப்பம், கடுமையான தலைவலி, மங்கலான பார்வை',
    analyseSymptoms: 'பகுப்பாய்வு செய் →',
    photographSymptoms: 'புகைப்படம் எடு',
    viewPatientHistory: '📋  நோயாளி வரலாறு',
    analysingWithGemma: 'Gemma 4 மூலம் பகுப்பாய்வு…',
    dangerSignsDetected: 'ஆபத்தான அறிகுறிகள் கண்டறியப்பட்டன',
    warningSignsDetected: 'எச்சரிக்கை அறிகுறிகள் கண்டறியப்பட்டன',
    normalContinueMonitoring: 'சாதாரணம் — தொடர்ந்து கண்காணி',
    aiAssessment: 'AI மதிப்பீடு',
    nextAction: 'அடுத்த நடவடிக்கை',
    whyThisResult: 'ஏன் இந்த முடிவு?',
    locationUsed: 'இருப்பிடம்',
    gpsLocationUsed: 'தற்போதைய GPS இடம் பயன்படுத்தப்பட்டது',
    fallbackLocationUsed: 'இயல்புநிலை இடம் பயன்படுத்தப்பட்டது',
    referNow: 'உடனே பரிந்துரை மையத்திற்கு செல்லவும்',
    continueMonitoring: 'வழக்கமான கண்காணிப்பை தொடரவும்',
    dangerSignsFound: 'கண்டறியப்பட்ட அறிகுறிகள்',
    nearestReferralFacility: 'அருகிலுள்ள மருத்துவ மையம்',
    transcript: 'பதிவு செய்த உரை',
    call108: '📞  108 ஆம்புலன்ஸ் அழைக்க',
    newPatient: '+ புதிய நோயாளி',
    history: '📋 வரலாறு',
    kmAway: 'கி.மீ தொலைவில்',
    cameraPermission: 'கேமரா அனுமதி தேவை',
    locationDisabled: 'இருப்பிட சேவை முடக்கப்பட்டுள்ளது',
    describeSymptomsRequired: 'அறிகுறிகளை விவரிக்கவும்',
    selectLanguage: 'மொழியைத் தேர்ந்தெடுக்கவும்',
  );

  static const _en = S(
    appBarTitle: 'ASHA TRIAGE',
    patientId: 'Patient ID',
    patientIdHint: 'e.g. PATIENT-001',
    typeSymptoms: 'Type Symptoms',
    typeSymptomsHint: 'e.g. 32 week pregnant, severe headache, blurred vision',
    analyseSymptoms: 'Analyse Symptoms →',
    photographSymptoms: 'Photograph Symptoms',
    viewPatientHistory: '📋  View Patient History',
    analysingWithGemma: 'Analysing with Gemma 4…',
    dangerSignsDetected: 'DANGER SIGNS DETECTED',
    warningSignsDetected: 'WARNING SIGNS DETECTED',
    normalContinueMonitoring: 'NORMAL — CONTINUE MONITORING',
    aiAssessment: 'AI Assessment',
    nextAction: 'Next Action',
    whyThisResult: 'Why This Result?',
    locationUsed: 'Location',
    gpsLocationUsed: 'Current GPS location used',
    fallbackLocationUsed: 'Default demo location used',
    referNow: 'Refer to facility now',
    continueMonitoring: 'Continue routine monitoring',
    dangerSignsFound: 'Danger Signs Found',
    nearestReferralFacility: 'Nearest Referral Facility',
    transcript: 'Transcript',
    call108: '📞  CALL 108 AMBULANCE',
    newPatient: '+ New Patient',
    history: '📋 History',
    kmAway: 'km away',
    cameraPermission: 'Camera permission required',
    locationDisabled: 'Location services disabled',
    describeSymptomsRequired: "Please describe the patient's symptoms",
    selectLanguage: 'Select Language',
  );

  static const _kn = S(
    appBarTitle: 'ಆಶಾ ಟ್ರಯಾಜ್',
    patientId: 'ರೋಗಿಯ ಐಡಿ',
    patientIdHint: 'ಉದಾ. PATIENT-001',
    typeSymptoms: 'ಲಕ್ಷಣಗಳನ್ನು ಟೈಪ್ ಮಾಡಿ',
    typeSymptomsHint: 'ಉದಾ. 32 ವಾರದ ಗರ್ಭಿಣಿ, ತೀವ್ರ ತಲೆನೋವು',
    analyseSymptoms: 'ವಿಶ್ಲೇಷಿಸಿ →',
    photographSymptoms: 'ಫೋಟೋ ತೆಗೆಯಿರಿ',
    viewPatientHistory: '📋  ರೋಗಿಯ ಇತಿಹಾಸ',
    analysingWithGemma: 'Gemma 4 ನೊಂದಿಗೆ ವಿಶ್ಲೇಷಣೆ…',
    dangerSignsDetected: 'ಅಪಾಯಕಾರಿ ಲಕ್ಷಣಗಳು ಪತ್ತೆಯಾಗಿವೆ',
    warningSignsDetected: 'ಎಚ್ಚರಿಕೆಯ ಲಕ್ಷಣಗಳು ಪತ್ತೆಯಾಗಿವೆ',
    normalContinueMonitoring: 'ಸಾಮಾನ್ಯ — ಮೇಲ್ವಿಚಾರಣೆ ಮುಂದುವರಿಸಿ',
    aiAssessment: 'AI ಮೌಲ್ಯಮಾಪನ',
    nextAction: 'ಮುಂದಿನ ಕ್ರಮ',
    whyThisResult: 'ಈ ಫಲಿತಾಂಶ ಏಕೆ?',
    locationUsed: 'ಸ್ಥಳ',
    gpsLocationUsed: 'ಪ್ರಸ್ತುತ GPS ಸ್ಥಳ ಬಳಸಲಾಗಿದೆ',
    fallbackLocationUsed: 'ಡೀಫಾಲ್ಟ್ ಡೆಮೊ ಸ್ಥಳ ಬಳಸಲಾಗಿದೆ',
    referNow: 'ಈಗಲೇ ಆಸ್ಪತ್ರೆಗೆ ರೆಫರ್ ಮಾಡಿ',
    continueMonitoring: 'ಸಾಮಾನ್ಯ ಮೇಲ್ವಿಚಾರಣೆ ಮುಂದುವರಿಸಿ',
    dangerSignsFound: 'ಪತ್ತೆಯಾದ ಲಕ್ಷಣಗಳು',
    nearestReferralFacility: 'ಹತ್ತಿರದ ಆಸ್ಪತ್ರೆ',
    transcript: 'ಪಠ್ಯ',
    call108: '📞  108 ಆಂಬ್ಯುಲೆನ್ಸ್ ಕರೆ',
    newPatient: '+ ಹೊಸ ರೋಗಿ',
    history: '📋 ಇತಿಹಾಸ',
    kmAway: 'ಕಿ.ಮೀ ದೂರ',
    cameraPermission: 'ಕ್ಯಾಮೆರಾ ಅನುಮತಿ ಬೇಕು',
    locationDisabled: 'ಸ್ಥಳ ಸೇವೆ ನಿಷ್ಕ್ರಿಯ',
    describeSymptomsRequired: 'ಲಕ್ಷಣಗಳನ್ನು ವಿವರಿಸಿ',
    selectLanguage: 'ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ',
  );

  static const _hi = S(
    appBarTitle: 'आशा ट्रायज',
    patientId: 'रोगी पहचान',
    patientIdHint: 'उदा. PATIENT-001',
    typeSymptoms: 'लक्षण लिखें',
    typeSymptomsHint: 'उदा. 32 सप्ताह गर्भवती, तेज सिरदर्द, धुंधली दृष्टि',
    analyseSymptoms: 'विश्लेषण करें →',
    photographSymptoms: 'फ़ोटो लें',
    viewPatientHistory: '📋  रोगी इतिहास',
    analysingWithGemma: 'Gemma 4 से विश्लेषण…',
    dangerSignsDetected: 'खतरे के लक्षण मिले',
    warningSignsDetected: 'चेतावनी के लक्षण मिले',
    normalContinueMonitoring: 'सामान्य — निगरानी जारी रखें',
    aiAssessment: 'AI मूल्यांकन',
    nextAction: 'अगला कदम',
    whyThisResult: 'यह परिणाम क्यों?',
    locationUsed: 'स्थान',
    gpsLocationUsed: 'वर्तमान GPS स्थान उपयोग किया',
    fallbackLocationUsed: 'डिफ़ॉल्ट स्थान उपयोग किया',
    referNow: 'अभी अस्पताल भेजें',
    continueMonitoring: 'सामान्य निगरानी जारी रखें',
    dangerSignsFound: 'मिले लक्षण',
    nearestReferralFacility: 'निकटतम अस्पताल',
    transcript: 'पाठ',
    call108: '📞  108 एम्बुलेंस कॉल करें',
    newPatient: '+ नया रोगी',
    history: '📋 इतिहास',
    kmAway: 'किमी दूर',
    cameraPermission: 'कैमरा अनुमति आवश्यक',
    locationDisabled: 'स्थान सेवा बंद है',
    describeSymptomsRequired: 'कृपया रोगी के लक्षण बताएं',
    selectLanguage: 'भाषा चुनें',
  );

  static S of(String? code) {
    switch (code) {
      case 'ta': return _ta;
      case 'kn': return _kn;
      case 'hi': return _hi;
      default:   return _en;
    }
  }
}
