import { useEffect, useState } from "react";
import { router, useLocalSearchParams } from "expo-router";
import { Text, TextInput, View } from "react-native";
import { customerApi } from "../../src/api/mobile-session";
import type { AgentDetailsResponse } from "../../src/api/customer-api";
import { ActionButton } from "../../src/components/action-button";
import { DataCard } from "../../src/components/data-card";
import { Page, pageStyles } from "../../src/components/page";

export default function AgentDetailsPage() {
  const { agentId } = useLocalSearchParams<{ agentId: string }>();
  const [details, setDetails] = useState<AgentDetailsResponse["returned_info"]>();
  const [restrictions, setRestrictions] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!customerApi || !agentId) return;
    customerApi.getAgent(agentId).then((result) => setDetails(result.returned_info)).catch((loadError: unknown) => {
      setError(loadError instanceof Error ? loadError.message : "Unable to load agent details.");
    });
  }, [agentId]);

  async function hire() {
    if (!customerApi || !agentId) return;
    setBusy(true);
    setError("");
    try {
      const result = await customerApi.hireAgent(agentId, restrictions.split("\n").map((item) => item.trim()).filter(Boolean));
      if (!result.hired_agent_id) throw new Error(result.response ?? "Pine did not return the hired agent ID.");
      router.replace({ pathname: "/chat/[hiredAgentId]", params: { hiredAgentId: result.hired_agent_id, name: details?.agent?.agent_name ?? "Agent" } });
    } catch (hireError) {
      setError(hireError instanceof Error ? hireError.message : "Unable to hire this agent.");
    } finally {
      setBusy(false);
    }
  }

  const agent = details?.agent;
  return (
    <Page title={agent?.agent_name ?? "Agent details"}>
      <DataCard title={agent?.agent_name ?? "Loading agent…"} subtitle={agent?.agent_description}>
        {agent?.agent_price !== undefined ? <Text style={pageStyles.muted}>${agent.agent_price.toFixed(2)} per job</Text> : null}
        {agent?.agent_skills?.map((skill) => <Text key={skill} style={pageStyles.muted}>• {skill}</Text>)}
      </DataCard>
      <View style={pageStyles.card}>
        <Text style={pageStyles.label}>Agent restrictions</Text>
        <Text style={pageStyles.muted}>Add one restriction per line. These guide what the agent may do on your behalf.</Text>
        <TextInput multiline onChangeText={setRestrictions} placeholder="Optional restrictions" style={[pageStyles.input, { minHeight: 90, paddingTop: 14 }]} value={restrictions} />
        {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
        <ActionButton busy={busy} onPress={hire} title="Hire agent" />
      </View>
    </Page>
  );
}
