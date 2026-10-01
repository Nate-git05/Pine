import { useEffect, useState } from "react";
import { useLocalSearchParams } from "expo-router";
import { Text, TextInput, View } from "react-native";
import { customerApi } from "../../../src/api/mobile-session";
import type { CustomerJobRequest } from "../../../src/api/customer-api";
import { ActionButton } from "../../../src/components/action-button";
import { DataCard } from "../../../src/components/data-card";
import { Page, pageStyles } from "../../../src/components/page";

export default function ActivityRequestPage() {
  const { requestId } = useLocalSearchParams<{ requestId: string }>();
  const [request, setRequest] = useState<CustomerJobRequest | null>(null);
  const [response, setResponse] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!customerApi || !requestId) return;
    customerApi.getJobRequest(requestId).then(setRequest).catch((loadError: unknown) => {
      setError(loadError instanceof Error ? loadError.message : "Unable to load this request.");
    });
  }, [requestId]);

  async function sendResponse() {
    if (!customerApi || !requestId) return;
    if (!response.trim() || response.trim().length > 150) {
      setError("Write a response with 1 to 150 characters.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const result = await customerApi.answerJobRequest(requestId, response.trim());
      setMessage(result?.response ?? "Your response was sent to the agent.");
      setResponse("");
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : "Unable to send this response.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title={request?.request_name ?? "Request details"}>
      {request ? (
        <DataCard title={request.request_name} subtitle={request.request_description}>
          <Text style={pageStyles.body}>Current job summary: {request.agent_current_job_summary}</Text>
          <Text style={pageStyles.muted}>{request.hired_agent_name} · {request.requested_at}</Text>
        </DataCard>
      ) : null}
      <View style={pageStyles.card}>
        <Text style={pageStyles.label}>Reply to the agent</Text>
        <Text style={pageStyles.muted}>Your response is sent to the agent’s server and the request is marked handled after it accepts.</Text>
        <TextInput maxLength={150} multiline onChangeText={setResponse} placeholder="Write a response" style={[pageStyles.input, { minHeight: 90, paddingTop: 14 }]} value={response} />
        <Text style={pageStyles.muted}>{response.trim().length}/150 characters</Text>
        {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
        {message ? <Text style={pageStyles.secondaryText}>{message}</Text> : null}
        <ActionButton busy={busy} disabled={!response.trim()} onPress={sendResponse} title="Send response" />
      </View>
    </Page>
  );
}
