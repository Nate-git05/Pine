import type { PropsWithChildren } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { colors } from "../theme/colors";

export function Page({ children, title }: PropsWithChildren<{ title: string }>) {
  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={styles.brand}>PINE</Text>
        <View style={styles.heading}>
          <Text style={styles.title}>{title}</Text>
        </View>
        {children}
      </ScrollView>
    </SafeAreaView>
  );
}

export const pageStyles = StyleSheet.create({
  card: { backgroundColor: colors.paper, borderColor: colors.line, borderRadius: 18, borderWidth: 1, padding: 18, gap: 12 },
  body: { color: colors.ink, fontSize: 16, lineHeight: 24 },
  label: { color: colors.wineDeep, fontSize: 14, fontWeight: "600" },
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
    borderRadius: 12,
    justifyContent: "center",
    minHeight: 50,
    paddingHorizontal: 18,
  },
  buttonText: { color: colors.white, fontSize: 16, fontWeight: "700" },
  secondaryButton: { alignItems: "center", padding: 12 },
  secondaryText: { color: colors.wine, fontSize: 15, fontWeight: "600" },
  error: { color: "#9B514D", fontSize: 14, lineHeight: 20 },
  muted: { color: colors.muted, fontSize: 14, lineHeight: 21 },
});

const styles = StyleSheet.create({
  safeArea: { backgroundColor: colors.cream, flex: 1 },
  content: { flexGrow: 1, gap: 20, padding: 24 },
  brand: { color: colors.wine, fontSize: 14, fontWeight: "800", letterSpacing: 4 },
  heading: { gap: 8, marginTop: 18 },
  title: { color: colors.wineDeep, fontSize: 32, fontWeight: "700", letterSpacing: -0.5 },
});
