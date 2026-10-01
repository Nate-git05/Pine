import type { PropsWithChildren } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { colors } from "../theme/colors";

export function Page({ children, title, subtitle, eyebrow = "PINE  /  CUSTOMER" }: PropsWithChildren<{ title: string; subtitle?: string; eyebrow?: string }>) {
  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.heading}>
          <Text style={styles.eyebrow}>{eyebrow}</Text>
          <Text style={styles.title}>{title}</Text>
          {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
        </View>
        {children}
      </ScrollView>
    </SafeAreaView>
  );
}

export const pageStyles = StyleSheet.create({
  card: { backgroundColor: colors.paper, borderColor: colors.line, borderRadius: 20, borderWidth: 1, padding: 18, gap: 12 },
  body: { color: colors.ink, fontSize: 15, lineHeight: 23 },
  label: { color: colors.wineDeep, fontSize: 14, fontWeight: "700" },
  input: {
    backgroundColor: colors.white,
    borderColor: colors.taupe,
    borderRadius: 12,
    borderWidth: 1,
    color: colors.ink,
    fontSize: 16,
    minHeight: 50,
    paddingHorizontal: 14,
  },
  button: {
    alignItems: "center",
    backgroundColor: colors.wine,
    borderRadius: 15,
    justifyContent: "center",
    minHeight: 52,
    paddingHorizontal: 18,
  },
  buttonText: { color: colors.white, fontSize: 16, fontWeight: "700" },
  secondaryButton: { alignItems: "center", padding: 12 },
  secondaryText: { color: colors.wine, fontSize: 15, fontWeight: "700" },
  error: { color: "#9B514D", fontSize: 14, lineHeight: 20 },
  muted: { color: colors.muted, fontSize: 14, lineHeight: 21 },
  sectionLabel: { color: colors.muted, fontSize: 11, fontWeight: "800", letterSpacing: 1.5, textTransform: "uppercase" },
  pill: { alignSelf: "flex-start", backgroundColor: colors.rose, borderRadius: 20, paddingHorizontal: 10, paddingVertical: 6 },
  pillText: { color: colors.wine, fontSize: 12, fontWeight: "700" },
});

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.cream, flex: 1 },
  content: { flexGrow: 1, gap: 18, paddingHorizontal: 20, paddingTop: 22, paddingBottom: 30 },
  heading: { gap: 7, marginBottom: 3, marginTop: 7 },
  eyebrow: { color: colors.wine, fontSize: 10, fontWeight: "800", letterSpacing: 2 },
  title: { color: colors.wineDeep, fontSize: 34, fontWeight: "700", letterSpacing: -1 },
  subtitle: { color: colors.muted, fontSize: 15, lineHeight: 22, maxWidth: 360 },
});
