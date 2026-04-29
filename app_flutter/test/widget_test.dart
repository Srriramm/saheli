// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';

import 'package:saheli/main.dart';

void main() {
  testWidgets('Saheli app smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const SaheliApp());

    expect(find.text('SAHELI'), findsOneWidget);
    await tester.pump(const Duration(milliseconds: 2800));
    await tester.pump();
    expect(find.text('Choose Language'), findsOneWidget);
  });
}
