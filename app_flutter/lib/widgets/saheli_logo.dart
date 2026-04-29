import 'package:flutter/material.dart';
import '../core/theme.dart';

class SaheliLogo extends StatelessWidget {
  final double size;
  final bool whiteVariant; // white strokes on colored bg

  const SaheliLogo({super.key, this.size = 80, this.whiteVariant = false});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size * (120 / 90),
      child: CustomPaint(painter: _SaheliPainter(whiteVariant: whiteVariant)),
    );
  }
}

// Icon inside a warm circle — for splash and nav bar
class SaheliIconCircle extends StatelessWidget {
  final double size;
  const SaheliIconCircle({super.key, this.size = 64});

  @override
  Widget build(BuildContext context) => Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          color: surfaceColor,
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
                color: brandColor.withValues(alpha: 0.22),
                blurRadius: 20,
                offset: const Offset(0, 6))
          ],
        ),
        child: Center(child: SaheliLogo(size: size * 0.55)),
      );
}

// Icon on solid brand-red rounded square — for app icon variant
class SaheliIconSquare extends StatelessWidget {
  final double size;
  const SaheliIconSquare({super.key, this.size = 48});

  @override
  Widget build(BuildContext context) => Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
            color: brandColor,
            borderRadius: BorderRadius.circular(size * 0.22)),
        child: Center(child: SaheliLogo(size: size * 0.55, whiteVariant: true)),
      );
}

class _SaheliPainter extends CustomPainter {
  final bool whiteVariant;
  _SaheliPainter({required this.whiteVariant});

  @override
  void paint(Canvas canvas, Size size) {
    final w = size.width;
    final h = size.height;
    final sw = w * (5 / 90); // stroke width proportional

    final strokePaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = sw
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    if (whiteVariant) {
      strokePaint.color = Colors.white;
    } else {
      strokePaint.shader = const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [brandDark, brandLight],
      ).createShader(Rect.fromLTWH(0, 0, w, h));
    }

    final fillPaint = Paint()
      ..style = PaintingStyle.fill
      ..color = whiteVariant ? Colors.white : brandColor;

    // Head circle (stroke only)
    canvas.drawCircle(Offset(w * 0.5, h * 0.183), w * 0.2, strokePaint);

    // Bindi (filled dot above center of head)
    canvas.drawCircle(Offset(w * 0.5, h * 0.108), w * 0.05, fillPaint);

    // Neck
    canvas.drawLine(
        Offset(w * 0.5, h * 0.333), Offset(w * 0.5, h * 0.433), strokePaint);

    // Shoulders arc
    final shoulders = Path()
      ..moveTo(w * 0.133, h * 0.6)
      ..quadraticBezierTo(w * 0.133, h * 0.433, w * 0.5, h * 0.433)
      ..quadraticBezierTo(w * 0.867, h * 0.433, w * 0.867, h * 0.6);
    canvas.drawPath(shoulders, strokePaint);

    // Pregnant belly arc
    final belly = Path()
      ..moveTo(w * 0.222, h * 0.6)
      ..quadraticBezierTo(w * 0.156, h * 0.833, w * 0.5, h * 0.9)
      ..quadraticBezierTo(w * 0.844, h * 0.833, w * 0.778, h * 0.6);
    canvas.drawPath(belly, strokePaint);

    // Heart inside belly
    final heart = Path();
    // Scaled from original SVG viewBox 90x120 path
    final sx = w / 90;
    final sy = h / 120;
    heart.moveTo(45 * sx, 97 * sy);
    heart.cubicTo(45 * sx, 97 * sy, 35 * sx, 90 * sy, 35 * sx, 84 * sy);
    heart.cubicTo(35 * sx, 80 * sy, 38.5 * sx, 78 * sy, 41.5 * sx, 80 * sy);
    heart.cubicTo(43 * sx, 81 * sy, 44 * sx, 83 * sy, 45 * sx, 84.5 * sy);
    heart.cubicTo(46 * sx, 83 * sy, 47 * sx, 81 * sy, 48.5 * sx, 80 * sy);
    heart.cubicTo(51.5 * sx, 78 * sy, 55 * sx, 80 * sy, 55 * sx, 84 * sy);
    heart.cubicTo(55 * sx, 90 * sy, 45 * sx, 97 * sy, 45 * sx, 97 * sy);
    heart.close();
    canvas.drawPath(
        heart,
        fillPaint
          ..color = (whiteVariant ? Colors.white : brandColor)
              .withValues(alpha: 0.85));
  }

  @override
  bool shouldRepaint(_SaheliPainter old) => old.whiteVariant != whiteVariant;
}
