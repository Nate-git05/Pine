import { useCallback, useState } from "react";
import { router, useFocusEffect } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import { Alert, Pressable, Text, View } from "react-native";
import { customerApi } from "../../src/api/mobile-session";
import type { CustomerProfile, EmailIntegrationList, HiredAgentList } from "../../src/api/customer-api";
import { ActionButton } from "../../src/components/action-button";
import { DataCard } from "../../src/components/data-card";
import { Page, pageStyles } from "../../src/components/page";
import { colors } from "../../src/theme/colors";

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

  useFocusEffect(useCallback(() => { void loadProfile(); }, [loadProfile]));

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

  async function signOut() {
    if (!customerApi) {
      router.replace("/auth");
      return;
    }

    try {
      await customerApi.logout();
    } catch (logoutError) {
      Alert.alert(
        "Signed out on this device",
        logoutError instanceof Error
          ? `Pine could not confirm server session revocation: ${logoutError.message}`
          : "Pine could not confirm server session revocation. Sign in again when you reconnect.",
      );
    } finally {
      router.replace("/auth");
    }
  }

  return (
    <Page title="You" subtitle="Your account, email connections, and hired agents.">
      {busy ? <Text style={pageStyles.muted}>Updating your account…</Text> : null}
      {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
      {profile ? (
        <View style={{ alignItems: "center", backgroundColor: colors.paper, borderColor: colors.line, borderRadius: 22, borderWidth: 1, flexDirection: "row", gap: 14, padding: 17 }}>
          <View style={{ alignItems: "center", backgroundColor: colors.rose, borderRadius: 29, height: 58, justifyContent: "center", width: 58 }}><Text style={{ color: colors.wine, fontFamily: "Georgia", fontSize: 25, fontWeight: "700" }}>{profile.customer_name.slice(0, 1).toUpperCase()}</Text></View>
          <View style={{ flex: 1, gap: 3 }}>
            <Text style={{ color: colors.wineDeep, fontSize: 17, fontWeight: "700" }}>{profile.customer_name}</Text>
            <Text style={pageStyles.muted}>{profile.customer_email}</Text>
            <Text style={pageStyles.muted}>{profile.customer_number}</Text>
          </View>
        </View>
      ) : null}

      <View style={{ gap: 9 }}>
        <Text style={pageStyles.sectionLabel}>PAYMENT</Text>
        <DataCard title="Last used payment method" subtitle={profile?.active_card_last4 ? `${profile.card_type ?? "Card"} •••• ${profile.active_card_last4}` : "No card has been used for a job payment yet."}>
          {profile?.active_card_last4 ? <Text style={pageStyles.muted}>Expires {profile.expire_date ?? "date not available"}</Text> : <Text style={pageStyles.muted}>Pine asks you to choose a saved card when you accept a job offer.</Text>}
          <Text style={pageStyles.muted}>Card setup and selection happen in the job payment flow.</Text>
        </DataCard>
      </View>

      <View style={{ gap: 9 }}>
        <Text style={pageStyles.sectionLabel}>CONNECTIONS</Text>
        <DataCard title="Email integrations" subtitle="Connected email accounts can be used by your agents when their tools need them.">
          {integrations?.map((integration) => (
            <View key={integration.id} style={{ borderTopColor: colors.line, borderTopWidth: 1, gap: 5, paddingTop: 12 }}>
              <Text style={pageStyles.label}>{integration.integrationType}</Text>
              <Text style={pageStyles.body}>{integration.integratedEmail}</Text>
              <Text style={pageStyles.muted}>Connected {new Date(integration.integratedAt).toLocaleDateString()}</Text>
              <Pressable accessibilityRole="button" onPress={() => removeIntegration(integration.id, integration.integratedEmail)}><Text style={pageStyles.error}>Remove integration</Text></Pressable>
            </View>
          ))}
          {!integrations?.length ? <Text style={pageStyles.muted}>No email integrations connected.</Text> : null}
          <ActionButton busy={busy} onPress={connectGmail} title="Connect Gmail" />
          <Text style={pageStyles.muted}>Google authorization opens in a secure browser. Close it when finished, then refresh this page to see the connection.</Text>
        </DataCard>
      </View>

      <View style={{ gap: 9 }}>
        <Text style={pageStyles.sectionLabel}>YOUR AGENTS</Text>
        <DataCard title="Hired agents" subtitle={`${profile?.number_of_agents ?? activeAgents?.length ?? 0} active · ${profile?.jobs_completed ?? 0} completed jobs`}>
          {activeAgents?.map((agent) => (
            <View key={agent.id} style={{ borderTopColor: colors.line, borderTopWidth: 1, gap: 7, paddingTop: 12 }}>
              <View style={{ alignItems: "center", flexDirection: "row", justifyContent: "space-between" }}>
                <Text style={pageStyles.label}>{agent.name}</Text>
                <View style={pageStyles.pill}><Text style={pageStyles.pillText}>HIRED</Text></View>
              </View>
              <Text style={pageStyles.muted}>{agent.description}</Text>
              <Text style={pageStyles.muted}>Rating ★ {agent.rating.toFixed(1)}</Text>
              <Pressable disabled={busy} onPress={() => void changeAgentState(agent.id, "fire")}><Text style={pageStyles.error}>Fire agent</Text></Pressable>
            </View>
          ))}
          {firedAgents?.map((agent) => (
            <View key={agent.id} style={{ borderTopColor: colors.line, borderTopWidth: 1, gap: 7, paddingTop: 12 }}>
              <View style={{ alignItems: "center", flexDirection: "row", justifyContent: "space-between" }}>
                <Text style={pageStyles.label}>{agent.name}</Text>
                <View style={{ ...pageStyles.pill, backgroundColor: colors.sand }}><Text style={{ ...pageStyles.pillText, color: colors.muted }}>FIRED</Text></View>
              </View>
              <Text style={pageStyles.muted}>{agent.description}</Text>
              <Pressable disabled={busy} onPress={() => void changeAgentState(agent.id, "rehire")}><Text style={pageStyles.secondaryText}>Rehire agent</Text></Pressable>
            </View>
          ))}
          {!activeAgents?.length && !firedAgents?.length ? <Text style={pageStyles.muted}>Your hired agents will appear here.</Text> : null}
        </DataCard>
      </View>

      <View style={{ gap: 9 }}>
        <Text style={pageStyles.sectionLabel}>ACCOUNT</Text>
        <DataCard title="Account details" subtitle="Your profile details are read-only right now.">
          {profile ? <Text style={pageStyles.muted}>{profile.number_of_agents} active agents · {profile.jobs_completed} completed jobs</Text> : null}
          <Text style={pageStyles.muted}>Signing out clears this device’s saved Pine session.</Text>
          <ActionButton onPress={() => void signOut()} title="Sign out" />
        </DataCard>
      </View>
    </Page>
  );
}
