import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../core/theme.dart';
import '../core/api.dart' as api;
import '../core/strings.dart';
import '../core/location.dart';
import '../widgets/saheli_logo.dart';
import '../widgets/glass_pill.dart';

class TriageScreen extends StatefulWidget {
  const TriageScreen({super.key});
  @override
  State<TriageScreen> createState() => _TriageScreenState();
}

class _TriageScreenState extends State<TriageScreen> {
  final _textCtrl = TextEditingController();
  final _patientCtrl = TextEditingController(text: 'ANON-001');

  bool _isLoading = false;
  String? _language;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _language ??= ModalRoute.of(context)?.settings.arguments as String? ?? 'ta';
  }

  @override
  void dispose() {
    _textCtrl.dispose();
    _patientCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickPhoto() async {
    try {
      final picked = await ImagePicker()
          .pickImage(source: ImageSource.camera, imageQuality: 70);
      if (picked == null) return;
      setState(() => _isLoading = true);
      final loc = await getCurrentLocation();
      final result = await api.submitPhoto(
        picked.path,
        _language!,
        _patientCtrl.text,
        _textCtrl.text,
        latitude: loc?.latitude,
        longitude: loc?.longitude,
      );
      if (mounted) {
        Navigator.pushNamed(context, '/result',
            arguments: {'result': result, 'language': _language});
      }
    } catch (e) {
      _showError(e.toString());
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _submitText() async {
    final t = S.of(_language);
    if (_textCtrl.text.trim().isEmpty) {
      _showError(t.describeSymptomsRequired);
      return;
    }
    setState(() => _isLoading = true);
    try {
      final loc = await getCurrentLocation();
      final result = await api.runTriageText(
        _textCtrl.text.trim(),
        _language!,
        _patientCtrl.text,
        latitude: loc?.latitude,
        longitude: loc?.longitude,
      );
      if (mounted) {
        Navigator.pushNamed(context, '/result',
            arguments: {'result': result, 'language': _language});
      }
    } catch (e) {
      _showError(e.toString());
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(msg), backgroundColor: redColor));
  }

  static const _langLabels = {'ta': 'தமிழ்', 'kn': 'ಕನ್ನಡ', 'en': 'English'};

  @override
  Widget build(BuildContext context) {
    final t = S.of(_language);
    return Scaffold(
      backgroundColor: warmBg,
      body: SafeArea(
        child: Stack(
          children: [
            SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Nav bar
                  Row(
                    children: [
                      const SaheliLogo(size: 32),
                      const SizedBox(width: 12),
                      Expanded(
                          child:
                              Center(child: GlassPill(label: t.appBarTitle))),
                      const SizedBox(width: 12),
                      GestureDetector(
                        onTap: () => Navigator.pushReplacementNamed(
                            context, '/language'),
                        child: Text(_langLabels[_language] ?? _language ?? '',
                            style: const TextStyle(
                                fontSize: 13,
                                color: brandColor,
                                fontWeight: FontWeight.w700)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // Patient ID
                  Text(t.patientId,
                      style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: textPrimary,
                          letterSpacing: 0.5)),
                  const SizedBox(height: 6),
                  TextField(
                      controller: _patientCtrl,
                      enabled: !_isLoading,
                      decoration: InputDecoration(hintText: t.patientIdHint)),
                  const SizedBox(height: 28),

                  // Text input
                  Text(t.typeSymptoms,
                      style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: textPrimary,
                          letterSpacing: 0.5)),
                  const SizedBox(height: 6),
                  TextField(
                    controller: _textCtrl,
                    enabled: !_isLoading,
                    maxLines: 4,
                    decoration: InputDecoration(
                      hintText: t.typeSymptomsHint,
                      alignLabelWithHint: true,
                    ),
                  ),
                  const SizedBox(height: 10),
                  ElevatedButton(
                    onPressed: _isLoading ? null : _submitText,
                    child: Text(t.analyseSymptoms),
                  ),
                  const SizedBox(height: 14),

                  // Camera
                  OutlinedButton.icon(
                    onPressed: _isLoading ? null : _pickPhoto,
                    icon: const Icon(Icons.camera_alt, color: brandColor),
                    label: Text(t.photographSymptoms,
                        style: const TextStyle(
                            color: brandColor, fontWeight: FontWeight.w600)),
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: brandColor),
                      minimumSize: const Size(double.infinity, 52),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // History link
                  Center(
                    child: TextButton(
                      onPressed: () => Navigator.pushNamed(context, '/history',
                          arguments: _patientCtrl.text),
                      child: Text(t.viewPatientHistory,
                          style: const TextStyle(
                              color: brandColor, fontWeight: FontWeight.w600)),
                    ),
                  ),
                  const SizedBox(height: 40),
                ],
              ),
            ),

            // Loading overlay
            if (_isLoading)
              Container(
                color: Colors.black26,
                child: Center(
                  child: Column(mainAxisSize: MainAxisSize.min, children: [
                    const CircularProgressIndicator(color: brandColor),
                    const SizedBox(height: 16),
                    Text(t.analysingWithGemma,
                        style: const TextStyle(
                            color: Colors.white, fontWeight: FontWeight.w600)),
                  ]),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
