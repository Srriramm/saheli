import 'package:flutter/material.dart';
import 'core/theme.dart';
import 'screens/splash_screen.dart';
import 'screens/language_screen.dart';
import 'screens/triage_screen.dart';
import 'screens/result_screen.dart';
import 'screens/history_screen.dart';

void main() => runApp(const SaheliApp());

class SaheliApp extends StatelessWidget {
  const SaheliApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Saheli',
      debugShowCheckedModeBanner: false,
      theme: saheliTheme(),
      initialRoute: '/splash',
      routes: {
        '/splash':   (_) => const SplashScreen(),
        '/language': (_) => const LanguageScreen(),
        '/triage':   (_) => const TriageScreen(),
        '/result':   (_) => const ResultScreen(),
        '/history':  (_) => const HistoryScreen(),
      },
    );
  }
}
