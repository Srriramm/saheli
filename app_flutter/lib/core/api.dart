import 'dart:convert';
import 'package:http/http.dart' as http;

// Laptop hotspot IP — always 192.168.137.1 on Windows Mobile Hotspot
const baseUrl = 'http://192.168.137.1:5000';

class TriageResult {
  final String riskLevel;
  final List<String> dangerSigns;
  final Map<String, dynamic>? referral;
  final String response;
  final String reasoning;
  final String locationSource;
  final double? latitude;
  final double? longitude;
  final String? recordId;
  final String? transcript;

  TriageResult({
    required this.riskLevel,
    required this.dangerSigns,
    this.referral,
    required this.response,
    required this.reasoning,
    required this.locationSource,
    this.latitude,
    this.longitude,
    this.recordId,
    this.transcript,
  });

  factory TriageResult.fromJson(Map<String, dynamic> j) => TriageResult(
        riskLevel: j['risk_level'] ?? 'GREEN',
        dangerSigns: List<String>.from(j['danger_signs'] ?? []),
        referral: j['referral'] as Map<String, dynamic>?,
        response: j['response'] ?? '',
        reasoning: j['reasoning'] ?? '',
        locationSource: j['location_source'] ?? 'fallback',
        latitude: (j['latitude'] as num?)?.toDouble(),
        longitude: (j['longitude'] as num?)?.toDouble(),
        recordId: j['record_id'],
        transcript: j['transcript'],
      );
}

class PatientRecord {
  final String recordId;
  final String timestamp;
  final String riskLevel;
  final List<String> dangerSigns;
  final String recommendation;

  PatientRecord({
    required this.recordId,
    required this.timestamp,
    required this.riskLevel,
    required this.dangerSigns,
    required this.recommendation,
  });

  factory PatientRecord.fromJson(Map<String, dynamic> j) => PatientRecord(
        recordId: j['record_id'] ?? '',
        timestamp: j['timestamp'] ?? '',
        riskLevel: j['risk_level'] ?? 'GREEN',
        dangerSigns: List<String>.from(j['danger_signs'] ?? []),
        recommendation: j['recommendation'] ?? '',
      );
}

Future<TriageResult> submitPhoto(
  String photoPath,
  String language,
  String patientId,
  String transcript, {
  double? latitude,
  double? longitude,
}) async {
  final req = http.MultipartRequest('POST', Uri.parse('$baseUrl/submit-photo'));
  req.fields['language'] = language;
  req.fields['patient_id'] = patientId;
  req.fields['transcript'] = transcript;
  if (latitude != null) req.fields['latitude'] = latitude.toString();
  if (longitude != null) req.fields['longitude'] = longitude.toString();
  req.files.add(await http.MultipartFile.fromPath('photo', photoPath));
  final streamed = await req.send();
  final body = await streamed.stream.bytesToString();
  if (streamed.statusCode != 200) throw Exception('Photo triage failed: $body');
  return TriageResult.fromJson(jsonDecode(body));
}

Future<TriageResult> runTriageText(
  String transcript,
  String language,
  String patientId, {
  double? latitude,
  double? longitude,
}) async {
  final res = await http.post(
    Uri.parse('$baseUrl/run-triage'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'transcript': transcript,
      'language': language,
      'patient_id': patientId,
      if (latitude != null) 'latitude': latitude,
      if (longitude != null) 'longitude': longitude,
    }),
  );
  if (res.statusCode != 200) throw Exception('Triage failed: ${res.body}');
  return TriageResult.fromJson(jsonDecode(res.body));
}

Future<List<PatientRecord>> getPatientHistory(String patientId) async {
  final res = await http.get(
    Uri.parse('$baseUrl/patient/${Uri.encodeComponent(patientId)}'),
  );
  if (res.statusCode != 200) throw Exception('History failed: ${res.body}');
  final data = jsonDecode(res.body);
  if (data is List) return data.map((e) => PatientRecord.fromJson(e)).toList();
  return [];
}
