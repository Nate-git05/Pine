import { useCallback, useEffect, useState } from "react";
import { router } from "expo-router";
import { Pressable, Text, View } from "react-native";
import { customerApi } from "../../src/api/mobile-session";
import type { HiredAgentList } from "../../src/api/customer-api";
import { ActionButton } from "../../src/components/action-button";
import { DataCard } from "../../src/components/data-card";
import { Page, pageStyles } from "../../src/components/page";

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
      setError(loadError instanceof Error ? loadError.message : "Unable to load agents.");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => { void loadAgents(); }, [loadAgents]);

  return (
    <Page title="Your workspace">
      <Text style={pageStyles.body}>Your Pine agents are ready when you are.</Text>
      {busy ? <Text style={pageStyles.muted}>Loading your agents…</Text> : null}
      {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
      {!busy && !error && agents?.length === 0 ? (
        <DataCard title="Start with an agent" subtitle="Find an agent for the work you want to get done.">
          <ActionButton onPress={() => router.push("/(tabs)/search")} title="Explore agents" />
        </DataCard>
      ) : null}
      {agents?.map((agent) => (
        <Pressable key={agent.id} onPress={() => router.push({ pathname: "/chat/[hiredAgentId]", params: { hiredAgentId: agent.id, name: agent.name } })}>
          <DataCard title={agent.name} subtitle={agent.description}>
            <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
              <Text style={pageStyles.muted}>Rating {agent.rating.toFixed(1)}</Text>
              <Text style={pageStyles.secondaryText}>Open chat →</Text>
            </View>
          </DataCard>
        </Pressable>
      ))}
    </Page>
  );
}
