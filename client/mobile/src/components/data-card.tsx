import type { PropsWithChildren } from "react";
import { StyleSheet, Text, View } from "react-native";
import { colors } from "../theme/colors";

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
  card: { backgroundColor: colors.paper, borderColor: colors.line, borderRadius: 18, borderWidth: 1, gap: 12, padding: 18 },
  heading: { gap: 4 },
  title: { color: colors.wineDeep, fontSize: 18, fontWeight: "700" },
  subtitle: { color: colors.muted, fontSize: 14, lineHeight: 20 },
});
