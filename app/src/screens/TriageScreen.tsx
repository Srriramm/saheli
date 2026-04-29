import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Animated,
  ActivityIndicator,
  Alert,
  ScrollView,
  Easing,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Audio } from 'expo-av';
import * as ImagePicker from 'expo-image-picker';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../App';
import { SaheliIcon } from '../components/SaheliLogo';
import GlassPill from '../components/GlassPill';
import { Colors, FontSize, Spacing, Radius, Shadow } from '../theme';
import {
  transcribeAndTriage,
  submitPhoto,
  runTriageText,
  TriageResult,
} from '../api/saheliApi';

type Props = NativeStackScreenProps<RootStackParamList, 'Triage'>;

type InputMode = 'idle' | 'recording' | 'loading';

const LANG_LABELS: Record<string, string> = {
  ta: 'Tamil · தமிழ்',
  kn: 'Kannada · ಕನ್ನಡ',
  en: 'English',
};

export default function TriageScreen({ route, navigation }: Props) {
  const { language } = route.params;
  const [mode, setMode]       = useState<InputMode>('idle');
  const [patientId, setPatientId] = useState('ANON-001');
  const [symptoms, setSymptoms]   = useState('');
  const recordingRef = useRef<Audio.Recording | null>(null);
  const pulseAnim    = useRef(new Animated.Value(1)).current;
  const pulseLoop    = useRef<Animated.CompositeAnimation | null>(null);

  function startPulse() {
    pulseLoop.current = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.25, duration: 600, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1.0,  duration: 600, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    );
    pulseLoop.current.start();
  }

  function stopPulse() {
    pulseLoop.current?.stop();
    pulseAnim.setValue(1);
  }

  async function startRecording() {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Microphone permission required');
        return;
      }
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      recordingRef.current = recording;
      setMode('recording');
      startPulse();
    } catch (e) {
      Alert.alert('Could not start recording', String(e));
    }
  }

  async function stopRecording() {
    stopPulse();
    setMode('loading');
    try {
      const recording = recordingRef.current;
      if (!recording) return;
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      if (!uri) throw new Error('No audio recorded');

      const result = await transcribeAndTriage(uri, language, patientId);
      navigation.navigate('Result', { result, language });
    } catch (e: any) {
      Alert.alert('Triage failed', e?.message ?? String(e));
      setMode('idle');
    }
  }

  async function pickPhoto() {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Camera permission required');
      return;
    }
    const picked = await ImagePicker.launchCameraAsync({ quality: 0.7 });
    if (picked.canceled) return;
    setMode('loading');
    try {
      const result = await submitPhoto(picked.assets[0].uri, language, patientId, symptoms);
      navigation.navigate('Result', { result, language });
    } catch (e: any) {
      Alert.alert('Photo analysis failed', e?.message ?? String(e));
      setMode('idle');
    }
  }

  async function submitText() {
    if (!symptoms.trim()) {
      Alert.alert('Please describe the patient\'s symptoms.');
      return;
    }
    setMode('loading');
    try {
      const result = await runTriageText(symptoms.trim(), language, patientId);
      navigation.navigate('Result', { result, language });
    } catch (e: any) {
      Alert.alert('Triage failed', e?.message ?? String(e));
      setMode('idle');
    }
  }

  const isLoading   = mode === 'loading';
  const isRecording = mode === 'recording';

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">

          {/* ── Nav bar ── */}
          <View style={styles.nav}>
            <SaheliIcon size={32} />
            <GlassPill label="ASHA TRIAGE" style={styles.navPill} />
            <TouchableOpacity onPress={() => navigation.replace('Language')}>
              <Text style={styles.langChip}>{LANG_LABELS[language] ?? language}</Text>
            </TouchableOpacity>
          </View>

          {/* ── Patient ID ── */}
          <View style={styles.section}>
            <Text style={styles.label}>Patient ID</Text>
            <TextInput
              style={styles.input}
              value={patientId}
              onChangeText={setPatientId}
              placeholder="e.g. PATIENT-001"
              placeholderTextColor={Colors.textMuted}
              editable={!isLoading}
            />
          </View>

          {/* ── Voice button ── */}
          <View style={styles.voiceSection}>
            <Text style={styles.voiceHint}>
              {isRecording ? 'Recording… tap to stop' : 'Hold to record patient voice'}
            </Text>
            <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
              <TouchableOpacity
                style={[styles.micBtn, isRecording && styles.micBtnActive]}
                onPress={isRecording ? stopRecording : startRecording}
                disabled={isLoading}
                activeOpacity={0.8}
              >
                <Text style={styles.micIcon}>{isRecording ? '⏹' : '🎙'}</Text>
              </TouchableOpacity>
            </Animated.View>
            {isRecording && (
              <View style={styles.recDot}>
                <View style={styles.redDot} />
                <Text style={styles.recLabel}>REC</Text>
              </View>
            )}
          </View>

          {/* ── Divider ── */}
          <View style={styles.dividerRow}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>OR</Text>
            <View style={styles.dividerLine} />
          </View>

          {/* ── Text input ── */}
          <View style={styles.section}>
            <Text style={styles.label}>Type Symptoms</Text>
            <TextInput
              style={[styles.input, styles.multiline]}
              value={symptoms}
              onChangeText={setSymptoms}
              placeholder="e.g. 32 week pregnant, severe headache, blurred vision, BP 150/100"
              placeholderTextColor={Colors.textMuted}
              multiline
              numberOfLines={4}
              editable={!isLoading}
            />
            <TouchableOpacity
              style={[styles.submitBtn, isLoading && styles.btnDisabled]}
              onPress={submitText}
              disabled={isLoading}
            >
              <Text style={styles.submitBtnText}>Analyse Symptoms →</Text>
            </TouchableOpacity>
          </View>

          {/* ── Camera ── */}
          <View style={styles.section}>
            <TouchableOpacity style={styles.cameraBtn} onPress={pickPhoto} disabled={isLoading}>
              <Text style={styles.cameraBtnText}>📷  Photograph Symptoms</Text>
            </TouchableOpacity>
          </View>

          {/* ── Loading overlay ── */}
          {isLoading && (
            <View style={styles.loadingRow}>
              <ActivityIndicator color={Colors.brand} size="large" />
              <Text style={styles.loadingText}>Analysing with Gemma 4…</Text>
            </View>
          )}

          {/* History shortcut */}
          <TouchableOpacity
            style={styles.historyLink}
            onPress={() => navigation.navigate('History', { patientId })}
          >
            <Text style={styles.historyLinkText}>📋  View Patient History</Text>
          </TouchableOpacity>

        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:   { flex: 1, backgroundColor: Colors.warmBg },
  scroll: { padding: Spacing.lg, gap: Spacing.lg },

  nav: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: Spacing.sm,
  },
  navPill: { flex: 1, marginHorizontal: Spacing.md, alignItems: 'center' },
  langChip: {
    fontSize: FontSize.xs,
    color: Colors.brand,
    fontWeight: '600',
    letterSpacing: 0.5,
  },

  section: { gap: Spacing.sm },
  label:   { fontSize: FontSize.sm, fontWeight: '600', color: Colors.textPrimary, letterSpacing: 0.5 },
  input: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.sm,
    borderWidth: 1,
    borderColor: Colors.border,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    fontSize: FontSize.md,
    color: Colors.textPrimary,
    ...Shadow.card,
  },
  multiline: {
    minHeight: 90,
    textAlignVertical: 'top',
    paddingTop: Spacing.sm,
  },

  voiceSection: { alignItems: 'center', gap: Spacing.md, paddingVertical: Spacing.md },
  voiceHint:    { fontSize: FontSize.sm, color: Colors.textMuted, letterSpacing: 0.5 },
  micBtn: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: Colors.brand,
    alignItems: 'center',
    justifyContent: 'center',
    ...Shadow.strong,
  },
  micBtnActive: { backgroundColor: Colors.redDark },
  micIcon: { fontSize: 36 },
  recDot: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  redDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: Colors.red },
  recLabel: { fontSize: FontSize.xs, color: Colors.red, fontWeight: '700', letterSpacing: 2 },

  dividerRow:  { flexDirection: 'row', alignItems: 'center', gap: Spacing.md },
  dividerLine: { flex: 1, height: 1, backgroundColor: Colors.border },
  dividerText: { fontSize: FontSize.xs, color: Colors.textMuted, letterSpacing: 2 },

  submitBtn: {
    backgroundColor: Colors.brand,
    borderRadius: Radius.sm,
    paddingVertical: Spacing.md,
    alignItems: 'center',
    ...Shadow.card,
  },
  submitBtnText: { color: '#fff', fontWeight: '700', fontSize: FontSize.md, letterSpacing: 1 },
  btnDisabled:   { opacity: 0.5 },

  cameraBtn: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.sm,
    borderWidth: 1,
    borderColor: Colors.brand + '55',
    paddingVertical: Spacing.md,
    alignItems: 'center',
    ...Shadow.card,
  },
  cameraBtnText: { color: Colors.brand, fontWeight: '600', fontSize: FontSize.md },

  loadingRow: { alignItems: 'center', gap: Spacing.sm, paddingVertical: Spacing.md },
  loadingText: { color: Colors.textMuted, fontSize: FontSize.sm },

  historyLink: { alignItems: 'center', paddingVertical: Spacing.sm },
  historyLinkText: { color: Colors.brand, fontSize: FontSize.sm, fontWeight: '600' },
});
