import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Circle, Line, Path, Defs, LinearGradient, Stop } from 'react-native-svg';
import { Colors, FontSize } from '../theme';

interface SaheliLogoProps {
  size?: number;
  variant?: 'icon' | 'full' | 'iconCircle' | 'iconSquare';
  color?: string;
}

export function SaheliIcon({ size = 80, color }: { size?: number; color?: string }) {
  const stroke = color ?? 'url(#ig)';
  const fill = color ?? Colors.brand;
  const sw = size * (5 / 90);

  return (
    <Svg width={size} height={size * (120 / 90)} viewBox="0 0 90 120" fill="none">
      <Defs>
        <LinearGradient id="ig" x1="0" y1="0" x2="90" y2="120" gradientUnits="userSpaceOnUse">
          <Stop offset="0%" stopColor={Colors.brandDark} />
          <Stop offset="100%" stopColor={Colors.brandLight} />
        </LinearGradient>
      </Defs>
      {/* Head */}
      <Circle cx="45" cy="22" r="18" stroke={stroke} strokeWidth={sw} fill="none" />
      {/* Bindi */}
      <Circle cx="45" cy="13" r="4.5" fill={fill} />
      {/* Neck */}
      <Line x1="45" y1="40" x2="45" y2="52" stroke={stroke} strokeWidth={sw} strokeLinecap="round" />
      {/* Shoulders */}
      <Path
        d="M 12 72 Q 12 52 45 52 Q 78 52 78 72"
        stroke={stroke} strokeWidth={sw} fill="none" strokeLinecap="round"
      />
      {/* Pregnant belly */}
      <Path
        d="M 20 72 Q 14 100 45 108 Q 76 100 70 72"
        stroke={stroke} strokeWidth={sw} fill="none" strokeLinecap="round"
      />
      {/* Heart inside belly */}
      <Path
        d="M45 97 C45 97 35 90 35 84 C35 80 38.5 78 41.5 80 C43 81 44 83 45 84.5 C46 83 47 81 48.5 80 C51.5 78 55 80 55 84 C55 90 45 97 45 97Z"
        fill={fill} opacity={0.85}
      />
    </Svg>
  );
}

export default function SaheliLogo({ size = 80, variant = 'full' }: SaheliLogoProps) {
  if (variant === 'iconCircle') {
    return (
      <View style={[styles.iconCircle, { width: size, height: size, borderRadius: size / 2 }]}>
        <SaheliIcon size={size * 0.55} />
      </View>
    );
  }

  if (variant === 'iconSquare') {
    return (
      <View style={[styles.iconSquare, { width: size, height: size, borderRadius: size * 0.22 }]}>
        <SaheliIcon size={size * 0.55} color="white" />
      </View>
    );
  }

  if (variant === 'icon') {
    return <SaheliIcon size={size} />;
  }

  // Full logo: icon + divider + text
  const textScale = size / 80;
  return (
    <View style={styles.full}>
      <SaheliIcon size={size} />
      <View style={[styles.divider, { height: size * 0.9 }]} />
      <View style={styles.textMark}>
        <Text style={[styles.wordmark, { fontSize: FontSize.xl * textScale, letterSpacing: 6 * textScale }]}>
          SAHELI
        </Text>
        <View style={styles.rule} />
        <Text style={[styles.tagline, { fontSize: 10 * textScale, letterSpacing: 2.5 * textScale }]}>
          MATERNAL HEALTH · EVERY VILLAGE
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  full: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 20,
  },
  divider: {
    width: 1.5,
    backgroundColor: Colors.brand + '55',
  },
  textMark: {
    gap: 4,
  },
  wordmark: {
    fontFamily: 'Georgia',
    fontWeight: '700',
    color: Colors.textPrimary,
    lineHeight: 36,
  },
  rule: {
    height: 2,
    width: '100%',
    backgroundColor: Colors.brand,
    borderRadius: 2,
  },
  tagline: {
    fontWeight: '400',
    color: Colors.textMuted,
    letterSpacing: 2.5,
  },
  iconCircle: {
    backgroundColor: Colors.warmBg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconSquare: {
    backgroundColor: Colors.brand,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
