import { useState } from "react";
import { router } from "expo-router";
import { Text, TextInput, View } from "react-native";
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
      <Text style={pageStyles.body}>Talk to your Pine agent and get work moving from one place.</Text>
      <View style={pageStyles.card}>
        {mode === "signup" && <>
          <Text style={pageStyles.label}>First name</Text>
          <TextInput autoCapitalize="words" onChangeText={setFirstName} style={pageStyles.input} value={firstName} />
          <Text style={pageStyles.label}>Last name</Text>
          <TextInput autoCapitalize="words" onChangeText={setLastName} style={pageStyles.input} value={lastName} />
        </>}
        <Text style={pageStyles.label}>Email</Text>
        <TextInput autoCapitalize="none" keyboardType="email-address" onChangeText={setEmail} style={pageStyles.input} value={email} />
        <Text style={pageStyles.label}>Phone number</Text>
        <TextInput keyboardType="phone-pad" onChangeText={setPhone} style={pageStyles.input} value={phone} />
        {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
        <ActionButton busy={busy} onPress={submit} title={mode === "login" ? "Continue" : "Create account"} />
        <Text style={pageStyles.muted}>We’ll send a verification code to your phone.</Text>
      </View>
      <Text onPress={() => { setMode(mode === "login" ? "signup" : "login"); setError(""); }} style={pageStyles.secondaryText}>
        {mode === "login" ? "New to Pine? Create an account" : "Already have an account? Sign in"}
      </Text>
    </Page>
  );
}
