import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../core/theme.dart';
import '../core/api.dart';
import '../core/strings.dart';
import '../widgets/saheli_logo.dart';
import '../widgets/risk_badge.dart';

class ResultScreen extends StatefulWidget {
  const ResultScreen({super.key});
  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _cardCtrl;
  late final Animation<Offset> _cardSlide;
  late final Animation<double> _bgScale;

  TriageResult? _result;
  String _language = 'ta';

  @override
  void initState() {
    super.initState();
    _cardCtrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 450));
    _cardSlide = Tween(begin: const Offset(0, 0.3), end: Offset.zero)
        .animate(CurvedAnimation(parent: _cardCtrl, curve: Curves.easeOut));
    _bgScale = Tween(begin: 0.92, end: 1.0)
        .animate(CurvedAnimation(parent: _cardCtrl, curve: Curves.elasticOut));
    _cardCtrl.forward();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final args = ModalRoute.of(context)?.settings.arguments as Map?;
    if (args != null) {
      _result = args['result'] as TriageResult?;
      _language = args['language'] as String? ?? 'ta';
    }
  }

  @override
  void dispose() {
    _cardCtrl.dispose();
    super.dispose();
  }

  Color get _headerColor {
    switch (_result?.riskLevel) {
      case 'RED':
        return redColor;
      case 'YELLOW':
        return yellowColor;
      default:
        return greenColor;
    }
  }

  Color get _headerText =>
      _result?.riskLevel == 'YELLOW' ? textPrimary : Colors.white;

  String get _headerIcon {
    switch (_result?.riskLevel) {
      case 'RED':
        return '⚠';
      case 'YELLOW':
        return '⚡';
      default:
        return '✓';
    }
  }

  String _heading(S t) {
    switch (_result?.riskLevel) {
      case 'RED':
        return t.dangerSignsDetected;
      case 'YELLOW':
        return t.warningSignsDetected;
      default:
        return t.normalContinueMonitoring;
    }
  }

  String _primaryAction(S t, TriageResult result) {
    if (result.riskLevel == 'RED') return t.call108;
    if (result.riskLevel == 'YELLOW') return t.referNow;
    return t.continueMonitoring;
  }

  String _reasonText(TriageResult result) {
    if (result.reasoning.isNotEmpty) return result.reasoning;
    if (result.dangerSigns.isNotEmpty) {
      final signs = result.dangerSigns.join(', ');
      switch (_language) {
        case 'ta':
          return '$signs கண்டறியப்பட்டது. இது கர்ப்ப கால ஆபத்தான அறிகுறி; உடனடி பரிந்துரை தேவை.';
        case 'kn':
          return '$signs ಪತ್ತೆಯಾಗಿದೆ. ಇದು ಗರ್ಭಾವಸ್ಥೆಯ ಅಪಾಯಕಾರಿ ಲಕ್ಷಣ; ತಕ್ಷಣ ರೆಫರ್ ಮಾಡಿ.';
        default:
          return 'Detected $signs from the reported symptoms.';
      }
    }
    switch (_language) {
      case 'ta':
        return 'ஆபத்தான அறிகுறிகள் எதுவும் கண்டறியப்படவில்லை. வழக்கமான கண்காணிப்பை தொடரவும்.';
      case 'kn':
        return 'ಅಪಾಯಕಾರಿ ಲಕ್ಷಣಗಳು ಪತ್ತೆಯಾಗಿಲ್ಲ. ಸಾಮಾನ್ಯ ಮೇಲ್ವಿಚಾರಣೆ ಮುಂದುವರಿಸಿ.';
      default:
        return 'No danger signs were detected from the reported symptoms.';
    }
  }

  @override
  Widget build(BuildContext context) {
    final result = _result;
    if (result == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final t = S.of(_language);

    return Scaffold(
      backgroundColor: _headerColor,
      body: SafeArea(
        child: Column(
          children: [
            // Header
            ScaleTransition(
              scale: _bgScale,
              child: Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
                child: Column(children: [
                  SaheliLogo(
                      size: 36, whiteVariant: _result?.riskLevel != 'YELLOW'),
                  const SizedBox(height: 8),
                  Text(_headerIcon,
                      style: TextStyle(fontSize: 44, color: _headerText)),
                  Text(_heading(t),
                      textAlign: TextAlign.center,
                      style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: _headerText,
                          letterSpacing: 1)),
                ]),
              ),
            ),

            // White card slides up
            Expanded(
              child: SlideTransition(
                position: _cardSlide,
                child: Container(
                  decoration: const BoxDecoration(
                    color: surfaceColor,
                    borderRadius:
                        BorderRadius.vertical(top: Radius.circular(24)),
                    boxShadow: [
                      BoxShadow(
                          color: Colors.black26,
                          blurRadius: 20,
                          offset: Offset(0, -4))
                    ],
                  ),
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        RiskBadge(level: result.riskLevel),
                        const SizedBox(height: 20),

                        // Action first: the ASHA should know what to do before reading detail.
                        _SectionTitle(t.nextAction),
                        const SizedBox(height: 8),
                        _ActionCard(
                          text: _primaryAction(t, result),
                          riskLevel: result.riskLevel,
                          onTap: result.riskLevel == 'RED'
                              ? () => launchUrl(Uri.parse('tel:108'))
                              : null,
                        ),
                        const SizedBox(height: 20),

                        // AI response
                        _SectionTitle(t.aiAssessment),
                        const SizedBox(height: 6),
                        Text(result.response,
                            style: const TextStyle(
                                fontSize: 16, color: textPrimary, height: 1.5)),
                        const SizedBox(height: 20),

                        _SectionTitle(t.whyThisResult),
                        const SizedBox(height: 6),
                        Text(_reasonText(result),
                            style: const TextStyle(
                                fontSize: 14,
                                color: textPrimary,
                                height: 1.45)),
                        const SizedBox(height: 20),

                        // Danger signs
                        if (result.dangerSigns.isNotEmpty) ...[
                          _SectionTitle(t.dangerSignsFound),
                          const SizedBox(height: 8),
                          Wrap(
                              spacing: 8,
                              runSpacing: 6,
                              children: result.dangerSigns
                                  .map((s) => _DangerChip(s, result.riskLevel))
                                  .toList()),
                          const SizedBox(height: 20),
                        ],

                        // Referral
                        if (result.referral != null) ...[
                          _SectionTitle(t.nearestReferralFacility),
                          const SizedBox(height: 8),
                          Container(
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: warmBg,
                              borderRadius: BorderRadius.circular(12),
                              border: const Border(
                                  left:
                                      BorderSide(color: brandColor, width: 4)),
                            ),
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(result.referral!['facility_name'] ?? '',
                                      style: const TextStyle(
                                          fontSize: 18,
                                          fontWeight: FontWeight.w700,
                                          color: textPrimary)),
                                  Text(
                                      '${result.referral!['distance_km']} ${t.kmAway}',
                                      style: const TextStyle(
                                          fontSize: 13,
                                          color: brandColor,
                                          fontWeight: FontWeight.w600)),
                                  if (result.referral!['address'] != null)
                                    Text(result.referral!['address'],
                                        style: const TextStyle(
                                            fontSize: 13, color: textMuted)),
                                ]),
                          ),
                          const SizedBox(height: 20),
                        ],

                        _SectionTitle(t.locationUsed),
                        const SizedBox(height: 6),
                        Row(children: [
                          Icon(Icons.my_location,
                              size: 16,
                              color: result.locationSource == 'gps'
                                  ? greenColor
                                  : textMuted),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              result.locationSource == 'gps'
                                  ? t.gpsLocationUsed
                                  : t.fallbackLocationUsed,
                              style: const TextStyle(
                                  fontSize: 13, color: textMuted, height: 1.4),
                            ),
                          ),
                        ]),
                        const SizedBox(height: 20),

                        // Transcript
                        if (result.transcript?.isNotEmpty == true) ...[
                          _SectionTitle(t.transcript),
                          const SizedBox(height: 6),
                          Text(result.transcript!,
                              style: const TextStyle(
                                  fontSize: 13,
                                  color: textMuted,
                                  fontStyle: FontStyle.italic,
                                  height: 1.5)),
                          const SizedBox(height: 20),
                        ],

                        // Navigation buttons
                        Row(children: [
                          Expanded(
                            child: ElevatedButton(
                              onPressed: () => Navigator.pushReplacementNamed(
                                  context, '/triage',
                                  arguments: _language),
                              child: Text(t.newPatient),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: OutlinedButton(
                              style: OutlinedButton.styleFrom(
                                side: const BorderSide(color: brandColor),
                                minimumSize: const Size(0, 52),
                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(10)),
                              ),
                              onPressed: () =>
                                  Navigator.pushNamed(context, '/history'),
                              child: Text(t.history,
                                  style: const TextStyle(
                                      color: brandColor,
                                      fontWeight: FontWeight.w700)),
                            ),
                          ),
                        ]),
                        const SizedBox(height: 20),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ActionCard extends StatelessWidget {
  final String text;
  final String riskLevel;
  final VoidCallback? onTap;
  const _ActionCard({required this.text, required this.riskLevel, this.onTap});

  @override
  Widget build(BuildContext context) {
    final color = riskLevel == 'RED'
        ? redColor
        : riskLevel == 'YELLOW'
            ? yellowDark
            : greenColor;
    final fg = riskLevel == 'YELLOW' ? textPrimary : Colors.white;
    return Material(
      color: color,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          child: Row(children: [
            Icon(
                riskLevel == 'GREEN'
                    ? Icons.check_circle
                    : Icons.local_hospital,
                color: fg,
                size: 24),
            const SizedBox(width: 10),
            Expanded(
              child: Text(text,
                  style: TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.w800,
                      color: fg,
                      height: 1.25)),
            ),
          ]),
        ),
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);
  @override
  Widget build(BuildContext context) => Text(text.toUpperCase(),
      style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: textMuted,
          letterSpacing: 2));
}

class _DangerChip extends StatelessWidget {
  final String label;
  final String riskLevel;
  const _DangerChip(this.label, this.riskLevel);
  @override
  Widget build(BuildContext context) {
    final color = riskLevel == 'RED'
        ? redColor
        : riskLevel == 'YELLOW'
            ? yellowDark
            : greenColor;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(999)),
      child: Text(label,
          style: TextStyle(
              fontSize: 13, fontWeight: FontWeight.w600, color: color)),
    );
  }
}
