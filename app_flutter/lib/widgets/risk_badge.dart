import 'package:flutter/material.dart';
import '../core/theme.dart';

class RiskBadge extends StatelessWidget {
  final String level;
  const RiskBadge({super.key, required this.level});

  @override
  Widget build(BuildContext context) {
    final Color bg;
    final Color fg;
    final String label;

    switch (level) {
      case 'RED':
        bg = redColor; fg = Colors.white; label = '⚠ RED';
        break;
      case 'YELLOW':
        bg = yellowColor; fg = textPrimary; label = '⚡ YELLOW';
        break;
      default:
        bg = greenColor; fg = Colors.white; label = '✓ GREEN';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999)),
      child: Text(label, style: TextStyle(color: fg, fontSize: 12, fontWeight: FontWeight.w700, letterSpacing: 1)),
    );
  }
}
