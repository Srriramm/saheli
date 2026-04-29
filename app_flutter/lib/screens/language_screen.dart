import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../widgets/saheli_logo.dart';

class LanguageScreen extends StatelessWidget {
  const LanguageScreen({super.key});

  static const _languages = [
    {'code': 'ta', 'label': 'Tamil',   'native': 'தமிழ்'},
    {'code': 'kn', 'label': 'Kannada', 'native': 'ಕನ್ನಡ'},
    {'code': 'en', 'label': 'English', 'native': 'English'},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: warmBg,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const SaheliLogo(size: 44),
              const SizedBox(height: 16),
              const Text('Choose Language', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: textPrimary, letterSpacing: 1)),
              const SizedBox(height: 6),
              const Text('भाषा चुनें · மொழி தேர்வு · ಭಾಷೆ ಆಯ್ಕೆ',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 12, color: textMuted, height: 1.6),
              ),
              const SizedBox(height: 36),

              ..._languages.map((lang) => Padding(
                padding: const EdgeInsets.only(bottom: 14),
                child: _LanguageTile(
                  code:   lang['code']!,
                  label:  lang['label']!,
                  native: lang['native']!,
                  onTap:  () => Navigator.pushReplacementNamed(context, '/triage', arguments: lang['code']),
                ),
              )),

              const SizedBox(height: 24),
              const Text('Tap to continue · தொடர தட்டவும்',
                style: TextStyle(fontSize: 11, color: textMuted, letterSpacing: 1)),
            ],
          ),
        ),
      ),
    );
  }
}

class _LanguageTile extends StatelessWidget {
  final String code, label, native;
  final VoidCallback onTap;
  const _LanguageTile({required this.code, required this.label, required this.native, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Material(
      color: surfaceColor,
      borderRadius: BorderRadius.circular(16),
      elevation: 2,
      shadowColor: Colors.black12,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          constraints: const BoxConstraints(minHeight: 100),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: const Border(left: BorderSide(color: brandColor, width: 4)),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(native, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w700, color: brandColor)),
                    const SizedBox(height: 4),
                    Text(label, style: const TextStyle(fontSize: 13, color: textMuted, letterSpacing: 1)),
                  ],
                ),
              ),
              const Icon(Icons.arrow_forward_ios, color: brandColor, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}
