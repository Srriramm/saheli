import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { StatusBar } from 'expo-status-bar';
import { TriageResult } from './src/api/saheliApi';

import SplashScreen   from './src/screens/SplashScreen';
import LanguageScreen from './src/screens/LanguageScreen';
import TriageScreen   from './src/screens/TriageScreen';
import ResultScreen   from './src/screens/ResultScreen';
import HistoryScreen  from './src/screens/HistoryScreen';

export type RootStackParamList = {
  Splash:   undefined;
  Language: undefined;
  Triage:   { language: string };
  Result:   { result: TriageResult; language: string };
  History:  { patientId?: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="dark" />
      <Stack.Navigator
        initialRouteName="Splash"
        screenOptions={{ headerShown: false, animation: 'slide_from_right' }}
      >
        <Stack.Screen name="Splash"    component={SplashScreen}   />
        <Stack.Screen name="Language"  component={LanguageScreen}  />
        <Stack.Screen name="Triage"    component={TriageScreen}    />
        <Stack.Screen name="Result"    component={ResultScreen}    />
        <Stack.Screen name="History"   component={HistoryScreen}   />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
