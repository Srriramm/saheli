import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Easing } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../App';
import SaheliLogo, { SaheliIcon } from '../components/SaheliLogo';
import { Colors, FontSize, Spacing } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'Splash'>;

export default function SplashScreen({ navigation }: Props) {
  const iconScale   = useRef(new Animated.Value(0.3)).current;
  const iconOpacity = useRef(new Animated.Value(0)).current;
  const wordOpacity = useRef(new Animated.Value(0)).current;
  const taglineY    = useRef(new Animated.Value(20)).current;
  const taglineOp   = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Step 1: icon springs in
    Animated.parallel([
      Animated.spring(iconScale, {
        toValue: 1,
        tension: 60,
        friction: 8,
        useNativeDriver: true,
      }),
      Animated.timing(iconOpacity, {
        toValue: 1,
        duration: 400,
        useNativeDriver: true,
      }),
    ]).start(() => {
      // Step 2: wordmark fades in
      Animated.timing(wordOpacity, {
        toValue: 1,
        duration: 500,
        easing: Easing.out(Easing.quad),
        useNativeDriver: true,
      }).start(() => {
        // Step 3: tagline slides up
        Animated.parallel([
          Animated.timing(taglineOp, {
            toValue: 1,
            duration: 400,
            useNativeDriver: true,
          }),
          Animated.timing(taglineY, {
            toValue: 0,
            duration: 400,
            easing: Easing.out(Easing.quad),
            useNativeDriver: true,
          }),
        ]).start();
      });
    });

    const timer = setTimeout(() => {
      navigation.replace('Language');
    }, 2800);
    return () => clearTimeout(timer);
  }, []);

  return (
    <View style={styles.container}>
      {/* Subtle warm radial feel via layered views */}
      <View style={styles.glow} />

      <Animated.View style={[styles.iconWrap, { opacity: iconOpacity, transform: [{ scale: iconScale }] }]}>
        <View style={styles.iconCircle}>
          <SaheliIcon size={90} />
        </View>
      </Animated.View>

      <Animated.Text style={[styles.wordmark, { opacity: wordOpacity }]}>
        SAHELI
      </Animated.Text>

      <View style={styles.ruleRow}>
        <Animated.View style={[styles.rule, { opacity: wordOpacity }]} />
      </View>

      <Animated.Text style={[styles.tagline, { opacity: taglineOp, transform: [{ translateY: taglineY }] }]}>
        MATERNAL HEALTH · EVERY VILLAGE
      </Animated.Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.warmBg,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.md,
  },
  glow: {
    position: 'absolute',
    width: 320,
    height: 320,
    borderRadius: 160,
    backgroundColor: Colors.brand + '12',
    top: '30%',
  },
  iconCircle: {
    width: 150,
    height: 150,
    borderRadius: 75,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.brand,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.20,
    shadowRadius: 20,
    elevation: 10,
  },
  iconWrap: {
    marginBottom: Spacing.md,
  },
  wordmark: {
    fontFamily: 'Georgia',
    fontSize: FontSize.hero * 0.7,
    fontWeight: '700',
    color: Colors.textPrimary,
    letterSpacing: 10,
  },
  ruleRow: {
    width: 200,
  },
  rule: {
    height: 2,
    backgroundColor: Colors.brand,
    borderRadius: 2,
  },
  tagline: {
    fontSize: FontSize.xs,
    letterSpacing: 3,
    color: Colors.textMuted,
    fontWeight: '500',
  },
});
