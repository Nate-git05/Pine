import { useState } from "react";
import { router } from "expo-router";
import { StyleSheet, Text, TextInput, View } from "react-native";
import { customerApi } from "../src/api/mobile-session";
import { ActionButton } from "../src/components/action-button";
import { Page, pageStyles } from "../src/components/page";

export default function AuthPage() {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (!customerApi) {
      setError("The app is missing EXPO_PUBLIC_PINE_API_URL.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const response = mode === "signup"
        ? await customerApi.signup({ first_name: firstName, last_name: lastName, email, phonenumber: phone })
        : await customerApi.login({ email, phonenumber: phone });
      const temporaryToken = response.customer_token ?? response.token;
      if (!temporaryToken) throw new Error(response.response ?? "Pine did not return a verification token.");
      router.push({ pathname: "/verify", params: { token: temporaryToken } });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to continue.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title={mode === "login" ? "Welcome back" : "Create your account"}>
      <View style={styles.welcomeRow}>
        <View style={styles.accentMark} />
        <Text style={styles.eyebrow}>YOUR WORK, MOVING FORWARD</Text>
      </View>
      <Text style={pageStyles.body}>One conversation can get good work moving. Sign in or create your Pine account to get started.</Text>
      <View style={pageStyles.card}>
        {mode === "signup" && <>
          <Text style={pageStyles.label}>First name</Text>
          <TextInput autoCapitalize="words" onChangeText={setFirstName} style={pageStyles.input} value={firstName} />
          <Text style={pageStyles.label}>Last name</Text>
          <TextInput autoCapitalize="words" onChangeText={setLastName} style={pageStyles.input} value={lastName} />
        </>}
        <Text style={pageStyles.label}>Email</Text>
        <TextInput autoCapitalize="none" keyboardType="email-address" onChangeText={setEmail} placeholder="you@example.com" placeholderTextColor="#A48D83" style={pageStyles.input} value={email} />
        <Text style={pageStyles.label}>Phone number</Text>
        <TextInput keyboardType="phone-pad" onChangeText={setPhone} placeholder="+1 555 000 0000" placeholderTextColor="#A48D83" style={pageStyles.input} value={phone} />
        {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
        <ActionButton busy={busy} onPress={submit} title={mode === "login" ? "Continue" : "Create account"} />
        <Text style={pageStyles.muted}>We’ll send a verification code to your phone.</Text>
      </View>
      <Text onPress={() => { setMode(mode === "login" ? "signup" : "login"); setError(""); }} style={pageStyles.secondaryText}>
        {mode === "login" ? "New to Pine? Create an account" : "Already have an account? Sign in"}
      </Text>
      <Text style={styles.footnote}>No password needed. We’ll verify your phone with a text message.</Text>
    </Page>
  );
}

const styles = StyleSheet.create({
  welcomeRow: { alignItems: "center", flexDirection: "row", gap: 9, marginTop: 3 },
  accentMark: { backgroundColor: "#DBA895", borderRadius: 5, height: 9, width: 9 },
  eyebrow: { color: "#9B514D", fontSize: 11, fontWeight: "800", letterSpacing: 1.4 },
  footnote: { color: "#806B68", fontSize: 12, lineHeight: 18, textAlign: "center" },
});
