import { useState } from "react";
import { router, useLocalSearchParams } from "expo-router";
import { Text, TextInput, View } from "react-native";
import { customerApi } from "../src/api/mobile-session";
import { ActionButton } from "../src/components/action-button";
import { Page, pageStyles } from "../src/components/page";

export default function VerifyPage() {
  const { token } = useLocalSearchParams<{ token: string }>();
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function verify() {
    if (!customerApi || !token) return setError("The verification session is missing.");
    setBusy(true);
    setError("");
    try {
      await customerApi.verify(token, code);
      router.replace("/(tabs)/home");
    } catch (verifyError) {
      setError(verifyError instanceof Error ? verifyError.message : "Unable to verify your account.");
    } finally {
      setBusy(false);
    }
  }

  async function resend() {
    if (!customerApi || !token) return setError("The verification session is missing.");
    setBusy(true);
    setError("");
    try {
      await customerApi.resendVerificationCode(token);
      setError("A new verification code was sent.");
    } catch (resendError) {
      setError(resendError instanceof Error ? resendError.message : "Unable to resend the code.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title="Verify your phone">
      <Text style={pageStyles.body}>Enter the code sent to your phone to finish signing in.</Text>
      <View style={pageStyles.card}>
        <Text style={pageStyles.label}>Verification code</Text>
        <TextInput keyboardType="number-pad" onChangeText={setCode} style={pageStyles.input} value={code} />
        {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
        <ActionButton busy={busy} onPress={verify} title="Verify and continue" />
        <Text onPress={resend} style={pageStyles.secondaryText}>Send a new code</Text>
      </View>
    </Page>
  );
}
