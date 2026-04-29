import 'package:flutter/material.dart';

const brandColor   = Color(0xFFC1390E);
const brandDark    = Color(0xFFB5330A);
const brandLight   = Color(0xFFE0622A);
const warmBg       = Color(0xFFFDF0EB);
const surfaceColor = Color(0xFFFFFFFF);
const textPrimary  = Color(0xFF1A1A1A);
const textMuted    = Color(0xFFAAAAAA);
const borderColor  = Color(0xFFE8E8E8);

const redColor    = Color(0xFFD32F2F);
const redDark     = Color(0xFFB71C1C);
const redBg       = Color(0xFFFFEBEE);
const yellowColor = Color(0xFFF57F17);
const yellowDark  = Color(0xFFE65100);
const yellowBg    = Color(0xFFFFF8E1);
const greenColor  = Color(0xFF2E7D32);
const greenDark   = Color(0xFF1B5E20);
const greenBg     = Color(0xFFE8F5E9);

ThemeData saheliTheme() => ThemeData(
  useMaterial3: true,
  colorSchemeSeed: brandColor,
  scaffoldBackgroundColor: warmBg,
  fontFamily: 'Roboto',
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: brandColor,
      foregroundColor: Colors.white,
      minimumSize: const Size(double.infinity, 52),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, letterSpacing: 1),
    ),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: surfaceColor,
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(10),
      borderSide: const BorderSide(color: borderColor),
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(10),
      borderSide: const BorderSide(color: borderColor),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(10),
      borderSide: const BorderSide(color: brandColor, width: 2),
    ),
  ),
);

Color riskColor(String level) {
  switch (level) {
    case 'RED':    return redColor;
    case 'YELLOW': return yellowColor;
    default:       return greenColor;
  }
}

Color riskBgColor(String level) {
  switch (level) {
    case 'RED':    return redBg;
    case 'YELLOW': return yellowBg;
    default:       return greenBg;
  }
}
