import type { PropsWithChildren } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

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
  card: { backgroundColor: "#FFFFFF", borderRadius: 18, padding: 18, gap: 12 },
  body: { color: "#50605A", fontSize: 16, lineHeight: 24 },
  label: { color: "#34443D", fontSize: 14, fontWeight: "600" },
  input: {
    backgroundColor: "#FFFFFF",
    borderColor: "#D7E0DA",
    borderRadius: 12,
    borderWidth: 1,
    color: "#1D2B24",
    fontSize: 16,
    minHeight: 50,
    paddingHorizontal: 14,
  },
  button: {
    alignItems: "center",
    backgroundColor: "#174C3A",
    borderRadius: 12,
    justifyContent: "center",
    minHeight: 50,
    paddingHorizontal: 18,
  },
  buttonText: { color: "#FFFFFF", fontSize: 16, fontWeight: "700" },
  secondaryButton: { alignItems: "center", padding: 12 },
  secondaryText: { color: "#174C3A", fontSize: 15, fontWeight: "600" },
  error: { color: "#A63232", fontSize: 14, lineHeight: 20 },
  muted: { color: "#6C7A72", fontSize: 14, lineHeight: 21 },
});

const styles = StyleSheet.create({
  safeArea: { backgroundColor: "#F3F6F2", flex: 1 },
  content: { flexGrow: 1, gap: 20, padding: 24 },
  brand: { color: "#174C3A", fontSize: 14, fontWeight: "800", letterSpacing: 4 },
  heading: { gap: 8, marginTop: 18 },
  title: { color: "#1D2B24", fontSize: 32, fontWeight: "700", letterSpacing: -0.5 },
});
