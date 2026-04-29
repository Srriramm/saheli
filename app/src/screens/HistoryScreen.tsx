import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../App';
import RiskBadge from '../components/RiskBadge';
import { Colors, FontSize, Spacing, Radius, Shadow } from '../theme';
import { getPatientHistory, PatientRecord } from '../api/saheliApi';

type Props = NativeStackScreenProps<RootStackParamList, 'History'>;

export default function HistoryScreen({ route, navigation }: Props) {
  const [patientId, setPatientId] = useState(route.params?.patientId ?? '');
  const [records, setRecords]     = useState<PatientRecord[]>([]);
  const [loading, setLoading]     = useState(false);
  const [searched, setSearched]   = useState(false);

  async function search() {
    if (!patientId.trim()) { Alert.alert('Enter a patient ID'); return; }
    setLoading(true);
    try {
      const data = await getPatientHistory(patientId.trim());
      setRecords(Array.isArray(data) ? data : []);
      setSearched(true);
    } catch (e: any) {
      Alert.alert('Could not load history', e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  function formatDate(ts: string) {
    try { return new Date(ts).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }); }
    catch { return ts; }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>

        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Patient History</Text>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Text style={styles.back}>← Back</Text>
          </TouchableOpacity>
        </View>

        {/* Search bar */}
        <View style={styles.searchRow}>
          <TextInput
            style={styles.input}
            value={patientId}
            onChangeText={setPatientId}
            placeholder="Patient ID (e.g. ANON-001)"
            placeholderTextColor={Colors.textMuted}
            returnKeyType="search"
            onSubmitEditing={search}
          />
          <TouchableOpacity style={styles.searchBtn} onPress={search} disabled={loading}>
            <Text style={styles.searchBtnText}>Search</Text>
          </TouchableOpacity>
        </View>

        {/* Results */}
        {loading ? (
          <View style={styles.center}>
            <ActivityIndicator color={Colors.brand} size="large" />
            <Text style={styles.hint}>Loading…</Text>
          </View>
        ) : searched && records.length === 0 ? (
          <View style={styles.center}>
            <Text style={styles.emptyIcon}>📋</Text>
            <Text style={styles.emptyText}>No records found for {patientId}</Text>
          </View>
        ) : (
          <FlatList
            data={records}
            keyExtractor={(item) => item.record_id}
            contentContainerStyle={styles.list}
            showsVerticalScrollIndicator={false}
            renderItem={({ item }) => (
              <View style={styles.card}>
                <View style={styles.cardTop}>
                  <RiskBadge level={item.risk_level} />
                  <Text style={styles.date}>{formatDate(item.timestamp)}</Text>
                </View>
                {item.danger_signs?.length > 0 && (
                  <View style={styles.chipRow}>
                    {item.danger_signs.map((s, i) => (
                      <View key={i} style={styles.chip}>
                        <Text style={styles.chipText}>{s}</Text>
                      </View>
                    ))}
                  </View>
                )}
                {item.recommendation ? (
                  <Text style={styles.rec} numberOfLines={2}>{item.recommendation}</Text>
                ) : null}
              </View>
            )}
          />
        )}

      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:      { flex: 1, backgroundColor: Colors.warmBg },
  container: { flex: 1, padding: Spacing.lg, gap: Spacing.lg },

  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title:  { fontSize: FontSize.xl, fontWeight: '700', color: Colors.textPrimary },
  back:   { fontSize: FontSize.sm, color: Colors.brand, fontWeight: '600' },

  searchRow: { flexDirection: 'row', gap: Spacing.sm },
  input: {
    flex: 1,
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
  searchBtn: {
    backgroundColor: Colors.brand,
    borderRadius: Radius.sm,
    paddingHorizontal: Spacing.lg,
    justifyContent: 'center',
    ...Shadow.card,
  },
  searchBtnText: { color: '#fff', fontWeight: '700', fontSize: FontSize.sm },

  center:    { flex: 1, alignItems: 'center', justifyContent: 'center', gap: Spacing.md },
  emptyIcon: { fontSize: 48 },
  emptyText: { fontSize: FontSize.md, color: Colors.textMuted, textAlign: 'center' },
  hint:      { fontSize: FontSize.sm, color: Colors.textMuted },

  list: { gap: Spacing.md, paddingBottom: Spacing.xxl },

  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.md,
    padding: Spacing.md,
    gap: Spacing.sm,
    ...Shadow.card,
  },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  date:    { fontSize: FontSize.xs, color: Colors.textMuted },

  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.xs },
  chip:    { backgroundColor: Colors.warmBg, paddingHorizontal: Spacing.sm, paddingVertical: 2, borderRadius: Radius.full },
  chipText: { fontSize: FontSize.xs, color: Colors.brand, fontWeight: '600' },

  rec: { fontSize: FontSize.sm, color: Colors.textMuted, fontStyle: 'italic' },
});
