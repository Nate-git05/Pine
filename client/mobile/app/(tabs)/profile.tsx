import { useCallback, useEffect, useState } from "react";
import { router } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import { Alert, Pressable, Text, View } from "react-native";
import { customerApi } from "../../src/api/mobile-session";
import type { CustomerProfile, EmailIntegrationList, HiredAgentList } from "../../src/api/customer-api";
import { ActionButton } from "../../src/components/action-button";
import { DataCard } from "../../src/components/data-card";
import { Page, pageStyles } from "../../src/components/page";

export default function ProfilePage() {
  const [profile, setProfile] = useState<CustomerProfile | null>(null);
  const [integrations, setIntegrations] = useState<EmailIntegrationList["integrations"]>([]);
  const [activeAgents, setActiveAgents] = useState<HiredAgentList["hiredAgents"]>([]);
  const [firedAgents, setFiredAgents] = useState<HiredAgentList["hiredAgents"]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const loadProfile = useCallback(async () => {
    if (!customerApi) return setError("The app is missing EXPO_PUBLIC_PINE_API_URL.");
    setBusy(true);
    try {
      const [profileResult, integrationResult, activeResult, firedResult] = await Promise.all([
        customerApi.getCustomerProfile(),
        customerApi.getEmailIntegrations(),
        customerApi.getHiredAgents("active"),
        customerApi.getHiredAgents("fired"),
      ]);
      setProfile(profileResult);
      setIntegrations(integrationResult.customerEmailIntegrations.integrations ?? []);
      setActiveAgents(activeResult.activeHiredAgents?.hiredAgents ?? []);
      setFiredAgents(firedResult.firedHiredAgents?.hiredAgents ?? []);
      setError("");
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load your profile.");
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => { void loadProfile(); }, [loadProfile]);

  async function connectGmail() {
    if (!customerApi) return;
    setBusy(true);
    setError("");
    try {
      const { redirect_url } = await customerApi.startGmailConnection();
      await WebBrowser.openBrowserAsync(redirect_url);
      // The current server callback ends on a Pine web page, not an app deep link.
      // Refresh after the customer closes the in-app browser to show the saved connection.
      await loadProfile();
    } catch (connectError) {
      setError(connectError instanceof Error ? connectError.message : "Unable to open Google authorization.");
    } finally {
      setBusy(false);
    }
  }

  async function removeIntegration(integrationId: string, email: string) {
    if (!customerApi) return;
    Alert.alert("Remove email integration?", `Pine will disconnect ${email}.`, [
      { text: "Cancel", style: "cancel" },
      {
        text: "Remove",
        style: "destructive",
        onPress: () => {
          void customerApi.deleteEmailIntegration(integrationId).then(loadProfile).catch((removeError: unknown) => {
            setError(removeError instanceof Error ? removeError.message : "Unable to remove this email.");
          });
        },
      },
    ]);
  }

  async function changeAgentState(agentId: string, action: "fire" | "rehire") {
    if (!customerApi) return;
    setBusy(true);
    setError("");
    try {
      if (action === "fire") await customerApi.fireAgent(agentId);
      else await customerApi.rehireAgent(agentId);
      await loadProfile();
    } catch (agentError) {
      setError(agentError instanceof Error ? agentError.message : "Unable to update this agent.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title="Profile">
      {busy ? <Text style={pageStyles.muted}>Updating your profile…</Text> : null}
      {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
      {profile ? (
        <DataCard title={profile.customer_name} subtitle={profile.customer_email}>
          <Text style={pageStyles.muted}>{profile.customer_number}</Text>
          <Text style={pageStyles.muted}>{profile.number_of_agents} active agents · {profile.jobs_completed} completed jobs</Text>
          {profile.active_card_last4 ? <Text style={pageStyles.muted}>Last used: {profile.card_type} ending {profile.active_card_last4} · expires {profile.expire_date}</Text> : <Text style={pageStyles.muted}>No card used for a payment yet.</Text>}
        </DataCard>
      ) : null}

      <DataCard title="Email integrations" subtitle="Connected email accounts are available to agents when their tools need them.">
        <ActionButton busy={busy} onPress={connectGmail} title="Connect Gmail" />
        {integrations?.map((integration) => (
          <View key={integration.id} style={{ borderTopColor: "#E4EAE5", borderTopWidth: 1, gap: 5, paddingTop: 12 }}>
            <Text style={pageStyles.label}>{integration.integrationType} · {integration.integratedEmail}</Text>
            <Text style={pageStyles.muted}>Connected {new Date(integration.integratedAt).toLocaleDateString()}</Text>
            <Text onPress={() => removeIntegration(integration.id, integration.integratedEmail)} style={pageStyles.error}>Remove integration</Text>
          </View>
        ))}
        {!integrations?.length ? <Text style={pageStyles.muted}>No email integrations connected.</Text> : null}
        <Text style={pageStyles.muted}>After Google authorization, close its in-app browser page to refresh the connection list.</Text>
      </DataCard>

      <DataCard title="Your agents">
        {activeAgents?.map((agent) => (
          <View key={agent.id} style={{ borderTopColor: "#E4EAE5", borderTopWidth: 1, gap: 7, paddingTop: 12 }}>
            <Text style={pageStyles.label}>{agent.name}</Text>
            <Text style={pageStyles.muted}>{agent.description}</Text>
            <Pressable disabled={busy} onPress={() => void changeAgentState(agent.id, "fire")}><Text style={pageStyles.error}>Fire agent</Text></Pressable>
          </View>
        ))}
        {firedAgents?.map((agent) => (
          <View key={agent.id} style={{ borderTopColor: "#E4EAE5", borderTopWidth: 1, gap: 7, paddingTop: 12 }}>
            <Text style={pageStyles.label}>{agent.name} · Fired</Text>
            <Text style={pageStyles.muted}>{agent.description}</Text>
            <Pressable disabled={busy} onPress={() => void changeAgentState(agent.id, "rehire")}><Text style={pageStyles.secondaryText}>Rehire agent</Text></Pressable>
          </View>
        ))}
        {!activeAgents?.length && !firedAgents?.length ? <Text style={pageStyles.muted}>Your hired agents will appear here.</Text> : null}
      </DataCard>

      <Text style={pageStyles.muted}>Profile details are read-only on the current server. Signing out clears this device’s saved session.</Text>
      <ActionButton onPress={() => {
        void customerApi?.logoutLocal().then(() => router.replace("/auth"));
      }} title="Sign out" />
    </Page>
  );
}
