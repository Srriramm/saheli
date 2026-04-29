import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, Radius, FontSize } from '../theme';

type RiskLevel = 'RED' | 'YELLOW' | 'GREEN';

const RISK_CONFIG: Record<RiskLevel, { bg: string; text: string; label: string }> = {
  RED:    { bg: Colors.red,    text: '#fff',            label: '⚠ RED'    },
  YELLOW: { bg: Colors.yellow, text: Colors.textPrimary, label: '⚡ YELLOW' },
  GREEN:  { bg: Colors.green,  text: '#fff',            label: '✓ GREEN'  },
};

export default function RiskBadge({ level }: { level: string }) {
  const cfg = RISK_CONFIG[(level as RiskLevel)] ?? RISK_CONFIG.GREEN;
  return (
    <View style={[styles.badge, { backgroundColor: cfg.bg }]}>
      <Text style={[styles.text, { color: cfg.text }]}>{cfg.label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: Radius.full,
    alignSelf: 'flex-start',
  },
  text: {
    fontSize: FontSize.sm,
    fontWeight: '700',
    letterSpacing: 1,
  },
});
