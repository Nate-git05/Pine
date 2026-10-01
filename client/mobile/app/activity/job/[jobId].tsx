import { useEffect, useState } from "react";
import { useLocalSearchParams } from "expo-router";
import { Text, View } from "react-native";
import { customerApi } from "../../../src/api/mobile-session";
import type { CustomerJob } from "../../../src/api/customer-api";
import { ActionButton } from "../../../src/components/action-button";
import { DataCard } from "../../../src/components/data-card";
import { Page, pageStyles } from "../../../src/components/page";

export default function ActivityJobPage() {
  const { jobId } = useLocalSearchParams<{ jobId: string }>();
  const [job, setJob] = useState<CustomerJob | null>(null);
  const [rating, setRating] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!customerApi || !jobId) return;
    customerApi.getJob(jobId).then(setJob).catch((loadError: unknown) => {
      setError(loadError instanceof Error ? loadError.message : "Unable to load this job.");
    });
  }, [jobId]);

  async function submitRating() {
    if (!customerApi || !jobId) return;
    const numericRating = Number(rating);
    if (!Number.isInteger(numericRating) || numericRating < 1 || numericRating > 5) {
      setError("Choose a rating from 1 to 5.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const result = await customerApi.rateJob(jobId, numericRating);
      setJob((current) => current ? { ...current, job_rating: numericRating } : current);
      setMessage(result.response ?? "Thank you for your rating.");
      setRating("");
    } catch (rateError) {
      setError(rateError instanceof Error ? rateError.message : "Unable to submit your rating.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title={job?.job_name ?? "Job details"}>
      {job ? (
        <DataCard title={job.job_name} subtitle={job.job_description}>
          <Text style={pageStyles.body}>{job.job_summary}</Text>
          <Text style={pageStyles.muted}>${job.job_price.toFixed(2)} · Agent: {job.hired_agent_name}</Text>
          {job.completed_at ? <Text style={pageStyles.muted}>Completed {job.completed_at}</Text> : null}
        </DataCard>
      ) : null}
      {job?.completed_at && job.job_rating == null ? (
        <View style={pageStyles.card}>
          <Text style={pageStyles.label}>Rate this job</Text>
          <Text style={pageStyles.muted}>Enter a rating from 1 to 5.</Text>
          <Text onPress={() => setRating("1")} style={pageStyles.secondaryText}>1</Text>
          <Text onPress={() => setRating("2")} style={pageStyles.secondaryText}>2</Text>
          <Text onPress={() => setRating("3")} style={pageStyles.secondaryText}>3</Text>
          <Text onPress={() => setRating("4")} style={pageStyles.secondaryText}>4</Text>
          <Text onPress={() => setRating("5")} style={pageStyles.secondaryText}>5</Text>
          <Text style={pageStyles.muted}>Selected rating: {rating || "none"}</Text>
          <ActionButton busy={busy} disabled={!rating} onPress={submitRating} title="Submit rating" />
        </View>
      ) : null}
      {message ? <Text style={pageStyles.secondaryText}>{message}</Text> : null}
      {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
    </Page>
  );
}
