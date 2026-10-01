import { useCallback, useEffect, useState } from "react";
import { Pressable, Text } from "react-native";
import { router } from "expo-router";
import { customerApi } from "../../src/api/mobile-session";
import type { JobList, JobRequestList, PaymentHistory } from "../../src/api/customer-api";
import { DataCard } from "../../src/components/data-card";
import { Page, pageStyles } from "../../src/components/page";
import { colors } from "../../src/theme/colors";

type ActivitySection = "requests" | "active" | "completed" | "payments";

export default function ActivityPage() {
  const [section, setSection] = useState<ActivitySection>("active");
  const [requests, setRequests] = useState<JobRequestList["returnedJobRequests"]>([]);
  const [jobs, setJobs] = useState<JobList["jobsReturned"]>([]);
  const [payments, setPayments] = useState<PaymentHistory["paymentsReturned"]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const loadActivity = useCallback(async () => {
    if (!customerApi) return setError("The app is missing EXPO_PUBLIC_PINE_API_URL.");
    setBusy(true);
    setError("");
    try {
      if (section === "requests") {
        const result = await customerApi.getActivityJobRequests();
        setRequests(result.jobRequests.returnedJobRequests ?? []);
      } else if (section === "active" || section === "completed") {
        const result = await customerApi.getActivityJobs(section);
        setJobs((section === "active" ? result.activeJobs : result.completedJobs)?.jobsReturned ?? []);
      } else {
        const result = await customerApi.getPaymentHistory();
        setPayments(result.customerJobPayments.paymentsReturned ?? []);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load activity.");
    } finally {
      setBusy(false);
    }
  }, [section]);

  useEffect(() => { void loadActivity(); }, [loadActivity]);

  const sections: ActivitySection[] = ["requests", "active", "completed", "payments"];
  return (
    <Page title="Activity">
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
        {sections.map((item) => (
          <Pressable key={item} onPress={() => setSection(item)} style={{ backgroundColor: section === item ? colors.wine : colors.sand, borderRadius: 20, paddingHorizontal: 14, paddingVertical: 10 }}>
            <Text style={{ color: section === item ? colors.white : colors.wineDeep, fontWeight: "600", textTransform: "capitalize" }}>{item}</Text>
          </Pressable>
        ))}
      </View>
      {busy ? <Text style={pageStyles.muted}>Loading activity…</Text> : null}
      {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
      {section === "requests" && requests?.map((request) => (
        <Pressable key={request.requestId} onPress={() => router.push({ pathname: "/activity/request/[requestId]", params: { requestId: request.requestId } })}>
          <DataCard title={request.requestName} subtitle={request.requestDescription}>
            <Text style={pageStyles.muted}>{request.rrequestCreatedAt} · Review request →</Text>
          </DataCard>
        </Pressable>
      ))}
      {(section === "active" || section === "completed") && jobs?.map((job) => (
        <Pressable key={job.agentJobId} onPress={() => router.push({ pathname: "/activity/job/[jobId]", params: { jobId: job.agentJobId } })}>
          <DataCard title={job.agentJobName} subtitle={job.agentJobDescription}>
            <Text style={pageStyles.muted}>{section === "active" ? "Started" : "Completed"}: {section === "active" ? job.createdAt ?? "—" : job.completedAt ?? "—"} · View details →</Text>
          </DataCard>
        </Pressable>
      ))}
      {section === "payments" && payments?.map((payment) => (
        <DataCard key={payment.paymentId} title={payment.jobName} subtitle={payment.paidAt}>
          <Text style={pageStyles.muted}>${payment.paymentAmount.toFixed(2)}</Text>
        </DataCard>
      ))}
      {!busy && !error && section === "requests" && !requests?.length ? <Text style={pageStyles.muted}>No open requests.</Text> : null}
      {!busy && !error && (section === "active" || section === "completed") && !jobs?.length ? <Text style={pageStyles.muted}>No {section} jobs.</Text> : null}
      {!busy && !error && section === "payments" && !payments?.length ? <Text style={pageStyles.muted}>No payments yet.</Text> : null}
    </Page>
  );
}
