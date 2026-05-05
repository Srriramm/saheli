import 'package:shared_preferences/shared_preferences.dart';

const _kLang = 'saheli_language';

Future<void> saveLanguage(String code) async {
  final p = await SharedPreferences.getInstance();
  await p.setString(_kLang, code);
}

Future<String?> loadLanguage() async {
  final p = await SharedPreferences.getInstance();
  return p.getString(_kLang);
}
