import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../widgets/saheli_logo.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});
  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with TickerProviderStateMixin {
  late final AnimationController _iconCtrl;
  late final AnimationController _wordCtrl;
  late final AnimationController _tagCtrl;

  late final Animation<double> _iconScale;
  late final Animation<double> _wordOpacity;
  late final Animation<double> _tagOpacity;
  late final Animation<Offset> _tagSlide;

  @override
  void initState() {
    super.initState();

    _iconCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 800));
    _wordCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 500));
    _tagCtrl  = AnimationController(vsync: this, duration: const Duration(milliseconds: 400));

    _iconScale   = Tween(begin: 0.3, end: 1.0).animate(CurvedAnimation(parent: _iconCtrl, curve: Curves.elasticOut));
    _wordOpacity = Tween(begin: 0.0, end: 1.0).animate(_wordCtrl);
    _tagOpacity  = Tween(begin: 0.0, end: 1.0).animate(_tagCtrl);
    _tagSlide    = Tween(begin: const Offset(0, 0.4), end: Offset.zero).animate(
      CurvedAnimation(parent: _tagCtrl, curve: Curves.easeOut),
    );

    _iconCtrl.forward().whenComplete(() =>
      _wordCtrl.forward().whenComplete(() =>
        _tagCtrl.forward()
      )
    );

    Future.delayed(const Duration(milliseconds: 2800), () {
      if (mounted) Navigator.pushReplacementNamed(context, '/language');
    });
  }

  @override
  void dispose() {
    _iconCtrl.dispose();
    _wordCtrl.dispose();
    _tagCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: warmBg,
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Glow circle behind icon
            ScaleTransition(
              scale: _iconScale,
              child: const SaheliIconCircle(size: 150),
            ),
            const SizedBox(height: 28),

            // SAHELI wordmark
            FadeTransition(
              opacity: _wordOpacity,
              child: const Text(
                'SAHELI',
                style: TextStyle(
                  fontFamily: 'serif',
                  fontSize: 48,
                  fontWeight: FontWeight.w700,
                  color: textPrimary,
                  letterSpacing: 10,
                ),
              ),
            ),
            const SizedBox(height: 6),

            // Gradient rule
            FadeTransition(
              opacity: _wordOpacity,
              child: Container(
                width: 200,
                height: 2,
                decoration: const BoxDecoration(
                  gradient: LinearGradient(colors: [brandDark, brandLight, Colors.transparent]),
                  borderRadius: BorderRadius.all(Radius.circular(2)),
                ),
              ),
            ),
            const SizedBox(height: 8),

            // Tagline
            SlideTransition(
              position: _tagSlide,
              child: FadeTransition(
                opacity: _tagOpacity,
                child: const Text(
                  'MATERNAL HEALTH · EVERY VILLAGE',
                  style: TextStyle(fontSize: 11, letterSpacing: 3, color: textMuted, fontWeight: FontWeight.w500),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
