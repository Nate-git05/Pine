import { useState } from "react";
import { router } from "expo-router";
import { Pressable, Text, TextInput, View } from "react-native";
import { customerApi } from "../../src/api/mobile-session";
import type { SearchAgent } from "../../src/api/customer-api";
import { ActionButton } from "../../src/components/action-button";
import { DataCard } from "../../src/components/data-card";
import { Page, pageStyles } from "../../src/components/page";

export default function SearchPage() {
  const [search, setSearch] = useState("");
  const [agents, setAgents] = useState<SearchAgent[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function findAgents() {
    if (!customerApi) return setError("The app is missing EXPO_PUBLIC_PINE_API_URL.");
    if (!search.trim()) return setError("Describe the kind of help you’re looking for.");
    setBusy(true);
    setError("");
    try {
      const result = await customerApi.searchAgents({ search_request: search.trim() });
      setAgents(result.returned_agents ?? []);
      if (!result.returned_agents?.length) setError(result.response ?? "No agents matched that search.");
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : "Unable to search agents.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title="Find an agent">
      <Text style={pageStyles.body}>Tell Pine what kind of work you want help with.</Text>
      <View style={pageStyles.card}>
        <TextInput multiline onChangeText={setSearch} placeholder="What would you like an agent to help with?" style={[pageStyles.input, { minHeight: 90, paddingTop: 14 }]} value={search} />
        <ActionButton busy={busy} onPress={findAgents} title="Search agents" />
        {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
      </View>
      {agents.map((agent) => (
        <Pressable key={agent.agent_id} onPress={() => router.push({ pathname: "/agents/[agentId]", params: { agentId: agent.agent_id } })}>
          <DataCard title={agent.agent_name} subtitle={agent.agent_description}>
            <Text style={pageStyles.muted}>${agent.agent_price.toFixed(2)} per job · View details →</Text>
          </DataCard>
        </Pressable>
      ))}
    </Page>
  );
}
