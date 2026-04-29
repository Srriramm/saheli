import 'package:flutter/material.dart';
import '../core/theme.dart';
import '../core/api.dart';
import '../widgets/risk_badge.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});
  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final _ctrl = TextEditingController();
  Future<List<PatientRecord>>? _future;
  bool _searched = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final arg = ModalRoute.of(context)?.settings.arguments;
    if (arg is String && arg.isNotEmpty && !_searched) {
      _ctrl.text = arg;
      _search();
    }
  }

  void _search() {
    if (_ctrl.text.trim().isEmpty) return;
    setState(() {
      _future = getPatientHistory(_ctrl.text.trim());
      _searched = true;
    });
  }

  String _formatDate(String ts) {
    try {
      final dt = DateTime.parse(ts).toLocal();
      return '${dt.day.toString().padLeft(2, '0')} ${[
        'Jan',
        'Feb',
        'Mar',
        'Apr',
        'May',
        'Jun',
        'Jul',
        'Aug',
        'Sep',
        'Oct',
        'Nov',
        'Dec'
      ][dt.month - 1]} ${dt.year}  ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return ts;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: warmBg,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(children: [
            // Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Patient History',
                    style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: textPrimary)),
                TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('← Back',
                        style: TextStyle(
                            color: brandColor, fontWeight: FontWeight.w600))),
              ],
            ),
            const SizedBox(height: 16),

            // Search row
            Row(children: [
              Expanded(
                child: TextField(
                  controller: _ctrl,
                  onSubmitted: (_) => _search(),
                  decoration: const InputDecoration(
                      hintText: 'Patient ID (e.g. ANON-001)'),
                ),
              ),
              const SizedBox(width: 10),
              ElevatedButton(
                onPressed: _search,
                style:
                    ElevatedButton.styleFrom(minimumSize: const Size(80, 52)),
                child: const Text('Search'),
              ),
            ]),
            const SizedBox(height: 20),

            // Results
            Expanded(
              child: _future == null
                  ? const Center(
                      child: Text('Enter a patient ID to search',
                          style: TextStyle(color: textMuted)))
                  : FutureBuilder<List<PatientRecord>>(
                      future: _future,
                      builder: (ctx, snap) {
                        if (snap.connectionState == ConnectionState.waiting) {
                          return const Center(
                              child:
                                  CircularProgressIndicator(color: brandColor));
                        }
                        if (snap.hasError) {
                          return Center(
                              child: Text('Error: ${snap.error}',
                                  style: const TextStyle(color: redColor)));
                        }
                        final records = snap.data ?? [];
                        if (records.isEmpty) {
                          return Center(
                            child: Column(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Text('📋',
                                      style: TextStyle(fontSize: 48)),
                                  const SizedBox(height: 12),
                                  Text('No records found for ${_ctrl.text}',
                                      textAlign: TextAlign.center,
                                      style: const TextStyle(
                                          fontSize: 16, color: textMuted)),
                                ]),
                          );
                        }
                        return ListView.separated(
                          itemCount: records.length,
                          separatorBuilder: (_, __) =>
                              const SizedBox(height: 12),
                          itemBuilder: (_, i) {
                            final r = records[i];
                            return Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: surfaceColor,
                                borderRadius: BorderRadius.circular(14),
                                boxShadow: [
                                  BoxShadow(
                                      color:
                                          Colors.black.withValues(alpha: 0.06),
                                      blurRadius: 8)
                                ],
                              ),
                              child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.spaceBetween,
                                      children: [
                                        RiskBadge(level: r.riskLevel),
                                        Text(_formatDate(r.timestamp),
                                            style: const TextStyle(
                                                fontSize: 11,
                                                color: textMuted)),
                                      ],
                                    ),
                                    if (r.dangerSigns.isNotEmpty) ...[
                                      const SizedBox(height: 10),
                                      Wrap(
                                        spacing: 6,
                                        runSpacing: 4,
                                        children: r.dangerSigns
                                            .map((s) => Container(
                                                  padding: const EdgeInsets
                                                      .symmetric(
                                                      horizontal: 10,
                                                      vertical: 3),
                                                  decoration: BoxDecoration(
                                                      color: warmBg,
                                                      borderRadius:
                                                          BorderRadius.circular(
                                                              999)),
                                                  child: Text(s,
                                                      style: const TextStyle(
                                                          fontSize: 11,
                                                          color: brandColor,
                                                          fontWeight:
                                                              FontWeight.w600)),
                                                ))
                                            .toList(),
                                      ),
                                    ],
                                    if (r.recommendation.isNotEmpty) ...[
                                      const SizedBox(height: 8),
                                      Text(r.recommendation,
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                          style: const TextStyle(
                                              fontSize: 13,
                                              color: textMuted,
                                              fontStyle: FontStyle.italic)),
                                    ],
                                  ]),
                            );
                          },
                        );
                      },
                    ),
            ),
          ]),
        ),
      ),
    );
  }
}
