import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  Animated,
  Linking,
  Easing,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../App';
import { SaheliIcon } from '../components/SaheliLogo';
import RiskBadge from '../components/RiskBadge';
import { Colors, FontSize, Spacing, Radius, Shadow } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'Result'>;

const RISK_BG: Record<string, string> = {
  RED:    Colors.red,
  YELLOW: Colors.yellow,
  GREEN:  Colors.green,
};

const RISK_ICON: Record<string, string> = {
  RED:    '⚠',
  YELLOW: '⚡',
  GREEN:  '✓',
};

const RISK_HEADING: Record<string, string> = {
  RED:    'DANGER SIGNS DETECTED',
  YELLOW: 'WARNING SIGNS DETECTED',
  GREEN:  'NORMAL — CONTINUE MONITORING',
};

export default function ResultScreen({ route, navigation }: Props) {
  const { result, language } = route.params;
  const { risk_level, danger_signs = [], referral, response, transcript } = result;

  const cardSlide = useRef(new Animated.Value(60)).current;
  const cardOp    = useRef(new Animated.Value(0)).current;
  const bgScale   = useRef(new Animated.Value(0.92)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(bgScale, { toValue: 1, tension: 70, friction: 9, useNativeDriver: true }),
      Animated.timing(cardOp,  { toValue: 1, duration: 400, easing: Easing.out(Easing.quad), useNativeDriver: true }),
      Animated.timing(cardSlide, { toValue: 0, duration: 400, easing: Easing.out(Easing.quad), useNativeDriver: true }),
    ]).start();
  }, []);

  const isRed    = risk_level === 'RED';
  const isYellow = risk_level === 'YELLOW';
  const bgColor  = RISK_BG[risk_level] ?? Colors.green;
  const textColor = isYellow ? Colors.textPrimary : '#fff';

  function call108() {
    Linking.openURL('tel:108');
  }

  return (
    <SafeAreaView style={[styles.safe, { backgroundColor: bgColor }]}>
      <Animated.View style={[styles.header, { transform: [{ scale: bgScale }] }]}>
        <SaheliIcon size={36} color={isYellow ? Colors.brandDark : '#fff'} />
        <Text style={[styles.headerIcon, { color: textColor }]}>{RISK_ICON[risk_level]}</Text>
        <Text style={[styles.heading, { color: textColor }]}>{RISK_HEADING[risk_level]}</Text>
      </Animated.View>

      <Animated.View style={[styles.card, { opacity: cardOp, transform: [{ translateY: cardSlide }] }]}>
        <ScrollView contentContainerStyle={styles.cardContent} showsVerticalScrollIndicator={false}>

          {/* Risk badge */}
          <View style={styles.row}>
            <RiskBadge level={risk_level} />
          </View>

          {/* AI response */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>AI Assessment</Text>
            <Text style={styles.responseText}>{response}</Text>
          </View>

          {/* Danger signs */}
          {danger_signs.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Danger Signs Found</Text>
              <View style={styles.chipRow}>
                {danger_signs.map((sign, i) => (
                  <View key={i} style={[styles.chip, { backgroundColor: bgColor + '22' }]}>
                    <Text style={[styles.chipText, { color: isRed ? Colors.red : isYellow ? Colors.yellowDark : Colors.green }]}>
                      {sign}
                    </Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Referral info */}
          {referral && (
            <View style={[styles.section, styles.referralCard]}>
              <Text style={styles.sectionTitle}>Nearest Referral Facility</Text>
              <Text style={styles.facilityName}>{referral.facility_name}</Text>
              <Text style={styles.facilityDist}>{referral.distance_km} km away</Text>
              {referral.address && (
                <Text style={styles.facilityAddr}>{referral.address}</Text>
              )}
            </View>
          )}

          {/* Transcript */}
          {transcript ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Transcript</Text>
              <Text style={styles.transcript}>{transcript}</Text>
            </View>
          ) : null}

          {/* Action buttons */}
          {isRed && (
            <TouchableOpacity style={styles.callBtn} onPress={call108}>
              <Text style={styles.callBtnText}>📞  CALL 108 AMBULANCE</Text>
            </TouchableOpacity>
          )}

          <View style={styles.navRow}>
            <TouchableOpacity
              style={styles.navBtn}
              onPress={() => navigation.navigate('Triage', { language })}
            >
              <Text style={styles.navBtnText}>+ New Patient</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.navBtn, styles.navBtnOutline]}
              onPress={() => navigation.navigate('History', { patientId: 'ANON-001' })}
            >
              <Text style={[styles.navBtnText, { color: Colors.brand }]}>📋 History</Text>
            </TouchableOpacity>
          </View>

        </ScrollView>
      </Animated.View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },

  header: {
    padding: Spacing.xl,
    paddingTop: Spacing.lg,
    alignItems: 'center',
    gap: Spacing.sm,
  },
  headerIcon: {
    fontSize: 44,
    fontWeight: '900',
  },
  heading: {
    fontSize: FontSize.lg,
    fontWeight: '800',
    textAlign: 'center',
    letterSpacing: 1,
  },

  card: {
    flex: 1,
    backgroundColor: Colors.surface,
    borderTopLeftRadius: Radius.lg,
    borderTopRightRadius: Radius.lg,
    ...Shadow.strong,
  },
  cardContent: {
    padding: Spacing.xl,
    gap: Spacing.lg,
    paddingBottom: Spacing.xxl,
  },

  row: { flexDirection: 'row' },

  section:      { gap: Spacing.sm },
  sectionTitle: { fontSize: FontSize.xs, fontWeight: '700', color: Colors.textMuted, letterSpacing: 2, textTransform: 'uppercase' },

  responseText: {
    fontSize: FontSize.md,
    color: Colors.textPrimary,
    lineHeight: 24,
  },

  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  chip: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: Radius.full,
  },
  chipText: { fontSize: FontSize.sm, fontWeight: '600' },

  referralCard: {
    backgroundColor: Colors.warmBg,
    padding: Spacing.md,
    borderRadius: Radius.md,
    borderLeftWidth: 4,
    borderLeftColor: Colors.brand,
  },
  facilityName: { fontSize: FontSize.lg, fontWeight: '700', color: Colors.textPrimary },
  facilityDist: { fontSize: FontSize.sm, color: Colors.brand, fontWeight: '600' },
  facilityAddr: { fontSize: FontSize.sm, color: Colors.textMuted },

  transcript: {
    fontSize: FontSize.sm,
    color: Colors.textMuted,
    fontStyle: 'italic',
    lineHeight: 20,
  },

  callBtn: {
    backgroundColor: Colors.red,
    borderRadius: Radius.md,
    paddingVertical: Spacing.lg,
    alignItems: 'center',
    ...Shadow.strong,
  },
  callBtnText: { color: '#fff', fontWeight: '800', fontSize: FontSize.lg, letterSpacing: 1 },

  navRow: { flexDirection: 'row', gap: Spacing.md },
  navBtn: {
    flex: 1,
    backgroundColor: Colors.brand,
    borderRadius: Radius.md,
    paddingVertical: Spacing.md,
    alignItems: 'center',
    ...Shadow.card,
  },
  navBtnOutline: {
    backgroundColor: Colors.surface,
    borderWidth: 1.5,
    borderColor: Colors.brand,
  },
  navBtnText: { color: '#fff', fontWeight: '700', fontSize: FontSize.sm },
});
