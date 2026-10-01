import type { PropsWithChildren } from "react";
import { StyleSheet, Text, View } from "react-native";

export function DataCard({
  title,
  subtitle,
  children,
}: PropsWithChildren<{ title: string; subtitle?: string }>) {
  return (
    <View style={styles.card}>
      <View style={styles.heading}>
        <Text style={styles.title}>{title}</Text>
        {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
      </View>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: "#FFFFFF", borderColor: "#E4EAE5", borderRadius: 18, borderWidth: 1, gap: 12, padding: 18 },
  heading: { gap: 4 },
  title: { color: "#1D2B24", fontSize: 18, fontWeight: "700" },
  subtitle: { color: "#65736B", fontSize: 14, lineHeight: 20 },
});
