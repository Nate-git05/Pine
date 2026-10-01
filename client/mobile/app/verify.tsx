import { useState } from "react";
import { router, useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, TextInput, View } from "react-native";
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
        <Text style={styles.eyebrow}>CHECK YOUR MESSAGES</Text>
        <Text style={pageStyles.label}>Verification code</Text>
        <TextInput
          autoComplete="sms-otp"
          keyboardType="number-pad"
          maxLength={6}
          onChangeText={setCode}
          placeholder="••••••"
          placeholderTextColor="#D9C6B9"
          style={styles.codeInput}
          textContentType="oneTimeCode"
          value={code}
        />
        {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
        <ActionButton busy={busy} onPress={verify} title="Verify and continue" />
        <Text onPress={resend} style={pageStyles.secondaryText}>Send a new code</Text>
      </View>
    </Page>
  );
}

const styles = StyleSheet.create({
  eyebrow: { color: "#9B514D", fontSize: 11, fontWeight: "800", letterSpacing: 1.4 },
  codeInput: {
    backgroundColor: "#FFFFFF",
    borderColor: "#D9C6B9",
    borderRadius: 14,
    borderWidth: 1,
    color: "#301923",
    fontSize: 28,
    fontWeight: "700",
    letterSpacing: 13,
    minHeight: 64,
    paddingLeft: 22,
    textAlign: "center",
  },
});
