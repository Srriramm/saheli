import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../App';
import { SaheliIcon } from '../components/SaheliLogo';
import { Colors, FontSize, Spacing, Radius, Shadow } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'Language'>;

const LANGUAGES = [
  { code: 'ta', label: 'Tamil',   native: 'தமிழ்',   flag: '🇮🇳' },
  { code: 'kn', label: 'Kannada', native: 'ಕನ್ನಡ',   flag: '🇮🇳' },
  { code: 'en', label: 'English', native: 'English', flag: '🇬🇧' },
];

export default function LanguageScreen({ navigation }: Props) {
  function selectLanguage(code: string) {
    navigation.replace('Triage', { language: code });
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <SaheliIcon size={44} />
          <Text style={styles.title}>Choose Language</Text>
          <Text style={styles.subtitle}>भाषा चुनें · மொழி தேர்வு · ಭಾಷೆ ಆಯ್ಕೆ</Text>
        </View>

        {/* Language tiles */}
        <View style={styles.tiles}>
          {LANGUAGES.map((lang) => (
            <TouchableOpacity
              key={lang.code}
              style={styles.tile}
              onPress={() => selectLanguage(lang.code)}
              activeOpacity={0.75}
            >
              <Text style={styles.flag}>{lang.flag}</Text>
              <Text style={styles.nativeLabel}>{lang.native}</Text>
              <Text style={styles.engLabel}>{lang.label}</Text>
              <View style={styles.tileAccent} />
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.hint}>Tap to continue · தொடர தட்டவும்</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.warmBg },
  container: {
    flex: 1,
    paddingHorizontal: Spacing.xl,
    justifyContent: 'center',
    gap: Spacing.xl,
  },
  header: {
    alignItems: 'center',
    gap: Spacing.sm,
  },
  title: {
    fontSize: FontSize.xl,
    fontWeight: '700',
    color: Colors.textPrimary,
    letterSpacing: 1,
  },
  subtitle: {
    fontSize: FontSize.xs,
    color: Colors.textMuted,
    textAlign: 'center',
    lineHeight: 20,
  },
  tiles: {
    gap: Spacing.md,
  },
  tile: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.md,
    padding: Spacing.xl,
    alignItems: 'center',
    gap: Spacing.sm,
    ...Shadow.card,
    overflow: 'hidden',
    minHeight: 110,
    justifyContent: 'center',
  },
  tileAccent: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
    backgroundColor: Colors.brand,
    borderTopLeftRadius: Radius.md,
    borderBottomLeftRadius: Radius.md,
  },
  flag: {
    fontSize: 28,
  },
  nativeLabel: {
    fontSize: FontSize.xl,
    fontWeight: '700',
    color: Colors.brand,
  },
  engLabel: {
    fontSize: FontSize.sm,
    color: Colors.textMuted,
    letterSpacing: 1,
  },
  hint: {
    textAlign: 'center',
    fontSize: FontSize.xs,
    color: Colors.textMuted,
    letterSpacing: 1,
  },
});
