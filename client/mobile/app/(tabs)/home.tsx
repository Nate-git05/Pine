import { useCallback, useState } from "react";
import { router, useFocusEffect } from "expo-router";
import { Pressable, Text, View } from "react-native";
import { customerApi } from "../../src/api/mobile-session";
import type { HiredAgentList } from "../../src/api/customer-api";
import { ActionButton } from "../../src/components/action-button";
import { Page, pageStyles } from "../../src/components/page";
import { colors } from "../../src/theme/colors";

export default function HomePage() {
  const [agents, setAgents] = useState<HiredAgentList["hiredAgents"]>([]);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");

  const loadAgents = useCallback(async () => {
    if (!customerApi) {
      setError("The app is missing EXPO_PUBLIC_PINE_API_URL.");
      setBusy(false);
      return;
    }
    setBusy(true);
    try {
      const result = await customerApi.getHiredAgents("active");
      setAgents(result.activeHiredAgents?.hiredAgents ?? []);
      setError("");
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load your agents.");
    } finally {
      setBusy(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { void loadAgents(); }, [loadAgents]));

  return (
    <Page title="Your workspace" subtitle="Your hired agents, ready when you need them.">
      {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
      {busy ? <Text style={pageStyles.muted}>Loading your agents…</Text> : null}

      {!busy && !error && !agents?.length ? (
        <View style={styles.emptyWrap}>
          <View style={styles.sparkle}><Text style={styles.sparkleText}>✳</Text></View>
          <Text style={styles.emptyTitle}>Hire an agent to start.</Text>
          <Text style={[pageStyles.muted, { textAlign: "center", maxWidth: 270 }]}>Find someone built for the work you need done. Your hired agents will appear here.</Text>
          <ActionButton onPress={() => router.push("/(tabs)/search")} title="Find an agent" />
        </View>
      ) : null}

      {!busy && Boolean(agents?.length) ? (
        <View style={styles.section}>
          <View style={styles.sectionHeading}>
            <Text style={pageStyles.sectionLabel}>Your agents</Text>
            <Pressable onPress={() => router.push("/(tabs)/search")}><Text style={pageStyles.secondaryText}>Find another  →</Text></Pressable>
          </View>
          {agents?.map((agent) => (
            <Pressable
              key={agent.id}
              accessibilityRole="button"
              onPress={() => router.push({ pathname: "/chat/[hiredAgentId]", params: { hiredAgentId: agent.id, name: agent.name } })}
              style={({ pressed }) => [styles.agentCard, pressed && { opacity: 0.86 }]}
            >
              <View style={styles.agentTop}>
                <View style={styles.avatar}><Text style={styles.avatarText}>{agent.name.slice(0, 1).toUpperCase()}</Text></View>
                <View style={{ flex: 1, gap: 4 }}>
                  <Text style={styles.agentName}>{agent.name}</Text>
                  <Text style={pageStyles.muted} numberOfLines={2}>{agent.description}</Text>
                </View>
                <Text style={styles.arrow}>›</Text>
              </View>
              <View style={styles.agentFooter}>
                <View style={pageStyles.pill}><Text style={pageStyles.pillText}>HIRED</Text></View>
                <Text style={styles.rating}>★ {agent.rating.toFixed(1)}</Text>
                <Text style={styles.chatCta}>Open chat</Text>
              </View>
            </Pressable>
          ))}
        </View>
      ) : null}
      {!busy && error ? <ActionButton onPress={() => void loadAgents()} title="Try again" /> : null}
    </Page>
  );
}

const styles = {
  emptyWrap: { alignItems: "center" as const, backgroundColor: colors.paper, borderColor: colors.line, borderRadius: 24, borderWidth: 1, gap: 17, justifyContent: "center" as const, minHeight: 350, padding: 28 },
  sparkle: { alignItems: "center" as const, backgroundColor: colors.sand, borderColor: colors.line, borderRadius: 24, borderWidth: 1, height: 66, justifyContent: "center" as const, width: 66 },
  sparkleText: { color: colors.wine, fontSize: 34 },
  emptyTitle: { color: colors.wineDeep, fontFamily: "Georgia", fontSize: 25, fontWeight: "700" as const, textAlign: "center" as const },
  section: { gap: 12 },
  sectionHeading: { alignItems: "center" as const, flexDirection: "row" as const, justifyContent: "space-between" as const, paddingHorizontal: 2 },
  agentCard: { backgroundColor: colors.paper, borderColor: colors.line, borderRadius: 20, borderWidth: 1, gap: 16, padding: 16 },
  agentTop: { alignItems: "center" as const, flexDirection: "row" as const, gap: 12 },
  avatar: { alignItems: "center" as const, backgroundColor: colors.rose, borderRadius: 24, height: 48, justifyContent: "center" as const, width: 48 },
  avatarText: { color: colors.wine, fontFamily: "Georgia", fontSize: 21, fontWeight: "700" as const },
  agentName: { color: colors.wineDeep, fontSize: 17, fontWeight: "700" as const },
  arrow: { color: colors.muted, fontSize: 28 },
  agentFooter: { alignItems: "center" as const, borderTopColor: colors.line, borderTopWidth: 1, flexDirection: "row" as const, gap: 12, paddingTop: 12 },
  rating: { color: colors.wineDeep, fontSize: 13, fontWeight: "700" as const },
  chatCta: { color: colors.wine, fontSize: 13, fontWeight: "700" as const, marginLeft: "auto" as const },
};
