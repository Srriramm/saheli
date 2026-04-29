import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';
import { Colors, Radius, FontSize } from '../theme';

interface GlassPillProps {
  label: string;
  style?: ViewStyle;
}

// iOS 26 Liquid Glass pill — frosted white pill with brand accent
export default function GlassPill({ label, style }: GlassPillProps) {
  return (
    <View style={[styles.pill, style]}>
      <View style={styles.shine} />
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  pill: {
    paddingHorizontal: 18,
    paddingVertical: 8,
    borderRadius: Radius.full,
    backgroundColor: 'rgba(255,255,255,0.72)',
    borderWidth: 0.5,
    borderColor: 'rgba(255,255,255,0.9)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.10,
    shadowRadius: 6,
    elevation: 3,
    overflow: 'hidden',
  },
  shine: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '50%',
    backgroundColor: 'rgba(255,255,255,0.45)',
    borderTopLeftRadius: Radius.full,
    borderTopRightRadius: Radius.full,
  },
  label: {
    fontSize: FontSize.sm,
    fontWeight: '600',
    color: Colors.textPrimary,
    letterSpacing: 1,
  },
});
