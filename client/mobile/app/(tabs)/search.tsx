import { useState } from "react";
import { router } from "expo-router";
import { Pressable, Text, TextInput, View } from "react-native";
import { customerApi } from "../../src/api/mobile-session";
import type { SearchAgent } from "../../src/api/customer-api";
import { ActionButton } from "../../src/components/action-button";
import { Page, pageStyles } from "../../src/components/page";
import { colors } from "../../src/theme/colors";

const suggestions = ["Organize my inbox", "Find meeting times", "Summarize a document"];

export default function SearchPage() {
  const [search, setSearch] = useState("");
  const [agents, setAgents] = useState<SearchAgent[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [emptyMessage, setEmptyMessage] = useState("");

  async function findAgents(searchText = search) {
    if (!customerApi) return setError("The app is missing EXPO_PUBLIC_PINE_API_URL.");
    if (!searchText.trim()) return setError("Describe the kind of help you’re looking for.");
    setBusy(true);
    setError("");
    setEmptyMessage("");
    setHasSearched(true);
    try {
      const result = await customerApi.searchAgents({ search_request: searchText.trim() });
      const matches = result.returned_agents ?? [];
      setAgents(matches);
      setEmptyMessage(matches.length ? "" : result.response ?? "No agents matched that search. Try describing the task another way.");
    } catch (searchError) {
      setAgents([]);
      setError(searchError instanceof Error ? searchError.message : "Unable to search agents.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title="Find an agent" subtitle="Describe the work you need done and explore agents built for it.">
      <View style={styles.searchPanel}>
        <View style={styles.searchRow}>
          <Text style={styles.searchIcon}>⌕</Text>
          <TextInput
            accessibilityLabel="Describe the work you need done"
            onChangeText={setSearch}
            onSubmitEditing={() => void findAgents()}
            placeholder="What do you need done?"
            placeholderTextColor={colors.muted}
            returnKeyType="search"
            style={styles.input}
            value={search}
          />
        </View>
        <ActionButton busy={busy} onPress={() => void findAgents()} title="Search agents" />
        {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
        {!hasSearched ? (
          <View style={styles.suggestions}>
            <Text style={pageStyles.sectionLabel}>Try describing a task</Text>
            {suggestions.map((suggestion) => (
              <Pressable key={suggestion} disabled={busy} onPress={() => { setSearch(suggestion); void findAgents(suggestion); }} style={styles.suggestion}>
                <Text style={styles.suggestionText}>{suggestion}</Text><Text style={styles.suggestionArrow}>↗</Text>
              </Pressable>
            ))}
          </View>
        ) : null}
      </View>

      {busy ? <Text style={pageStyles.muted}>Finding agents…</Text> : null}
      {!busy && emptyMessage ? (
        <View style={styles.emptyBox}>
          <Text style={styles.emptyMark}>⌕</Text>
          <Text style={styles.emptyTitle}>No matches yet</Text>
          <Text style={[pageStyles.muted, { textAlign: "center" }]}>{emptyMessage}</Text>
        </View>
      ) : null}
      {!busy && agents.length > 0 ? (
        <View style={{ gap: 12 }}>
          <Text style={pageStyles.sectionLabel}>{agents.length} {agents.length === 1 ? "AGENT" : "AGENTS"} FOUND</Text>
          {agents.map((agent) => (
            <Pressable
              key={agent.agent_id}
              accessibilityRole="button"
              onPress={() => router.push({ pathname: "/agents/[agentId]", params: { agentId: agent.agent_id } })}
              style={({ pressed }) => [styles.resultCard, pressed && { opacity: 0.86 }]}
            >
              <View style={styles.resultTop}>
                <View style={styles.agentIcon}><Text style={styles.agentIconText}>{agent.agent_name.slice(0, 1).toUpperCase()}</Text></View>
                <View style={{ flex: 1, gap: 4 }}>
                  <Text style={styles.agentName}>{agent.agent_name}</Text>
                  <Text style={pageStyles.muted}>{agent.agent_description}</Text>
                </View>
                <Text style={styles.price}>${agent.agent_price.toFixed(2)}<Text style={styles.perJob}> / job</Text></Text>
              </View>
              <View style={styles.resultFooter}>
                <Text style={styles.detailLink}>View agent details</Text><Text style={styles.detailArrow}>→</Text>
              </View>
            </Pressable>
          ))}
        </View>
      ) : null}
    </Page>
  );
}

const styles = {
  searchPanel: { backgroundColor: colors.paper, borderColor: colors.line, borderRadius: 22, borderWidth: 1, gap: 12, padding: 15 },
  searchRow: { alignItems: "center" as const, backgroundColor: colors.white, borderColor: colors.taupe, borderRadius: 15, borderWidth: 1, flexDirection: "row" as const, minHeight: 54, paddingHorizontal: 13 },
  searchIcon: { color: colors.wine, fontSize: 29, marginRight: 9 },
  input: { color: colors.ink, flex: 1, fontSize: 15, minHeight: 48 },
  suggestions: { gap: 8, paddingTop: 9 },
  suggestion: { alignItems: "center" as const, backgroundColor: colors.cream, borderColor: colors.line, borderRadius: 13, borderWidth: 1, flexDirection: "row" as const, justifyContent: "space-between" as const, paddingHorizontal: 13, paddingVertical: 12 },
  suggestionText: { color: colors.ink, fontSize: 14 },
  suggestionArrow: { color: colors.wine, fontSize: 16, fontWeight: "700" as const },
  emptyBox: { alignItems: "center" as const, backgroundColor: colors.paper, borderColor: colors.line, borderRadius: 20, borderWidth: 1, gap: 9, padding: 28 },
  emptyMark: { color: colors.wine, fontSize: 34 },
  emptyTitle: { color: colors.wineDeep, fontFamily: "Georgia", fontSize: 22, fontWeight: "700" as const },
  resultCard: { backgroundColor: colors.paper, borderColor: colors.line, borderRadius: 20, borderWidth: 1, gap: 14, padding: 15 },
  resultTop: { alignItems: "flex-start" as const, flexDirection: "row" as const, gap: 11 },
  agentIcon: { alignItems: "center" as const, backgroundColor: colors.rose, borderColor: colors.line, borderRadius: 17, borderWidth: 1, height: 44, justifyContent: "center" as const, width: 44 },
  agentIconText: { color: colors.wine, fontFamily: "Georgia", fontSize: 20, fontWeight: "700" as const },
  agentName: { color: colors.wineDeep, fontSize: 16, fontWeight: "700" as const },
  price: { color: colors.wine, fontSize: 14, fontWeight: "800" as const },
  perJob: { color: colors.muted, fontSize: 11, fontWeight: "500" as const },
  resultFooter: { alignItems: "center" as const, borderTopColor: colors.line, borderTopWidth: 1, flexDirection: "row" as const, justifyContent: "space-between" as const, paddingTop: 11 },
  detailLink: { color: colors.wine, fontSize: 13, fontWeight: "700" as const },
  detailArrow: { color: colors.muted, fontSize: 18 },
};
