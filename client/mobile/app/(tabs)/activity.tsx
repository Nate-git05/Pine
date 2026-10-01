import { useCallback, useState } from "react";
import { Pressable, Text, View } from "react-native";
import { router, useFocusEffect } from "expo-router";
import { customerApi } from "../../src/api/mobile-session";
import type { JobList, JobRequestList, PaymentHistory } from "../../src/api/customer-api";
import { DataCard } from "../../src/components/data-card";
import { Page, pageStyles } from "../../src/components/page";
import { colors } from "../../src/theme/colors";

type ActivitySection = "requests" | "active" | "completed" | "payments";

export default function ActivityPage() {
  const [section, setSection] = useState<ActivitySection>("requests");
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

  useFocusEffect(useCallback(() => { void loadActivity(); }, [loadActivity]));

  const sections: { id: ActivitySection; title: string; mark: string }[] = [
    { id: "requests", title: "Requests", mark: "↗" },
    { id: "active", title: "Active", mark: "◷" },
    { id: "completed", title: "Completed", mark: "✓" },
    { id: "payments", title: "Payments", mark: "$" },
  ];
  return (
    <Page title="Activity" subtitle="Requests, jobs, and payment records in one place.">
      <View style={{ backgroundColor: colors.sand, borderColor: colors.line, borderRadius: 18, borderWidth: 1, flexDirection: "row", flexWrap: "wrap", gap: 7, padding: 6 }}>
        {sections.map((item) => (
          <Pressable key={item.id} accessibilityRole="tab" accessibilityState={{ selected: section === item.id }} onPress={() => setSection(item.id)} style={{ alignItems: "center", backgroundColor: section === item.id ? colors.wine : "transparent", borderRadius: 13, flexBasis: "48%", flexDirection: "row", flexGrow: 1, gap: 7, justifyContent: "center", minHeight: 42, paddingHorizontal: 8 }}>
            <Text style={{ color: section === item.id ? colors.white : colors.muted, fontSize: 14, fontWeight: "800" }}>{item.mark}</Text>
            <Text style={{ color: section === item.id ? colors.white : colors.wineDeep, fontSize: 13, fontWeight: "700" }}>{item.title}</Text>
          </Pressable>
        ))}
      </View>
      <View style={{ alignItems: "center", flexDirection: "row", justifyContent: "space-between" }}>
        <Text style={pageStyles.sectionLabel}>{sections.find((item) => item.id === section)?.title}</Text>
        {busy ? <Text style={pageStyles.muted}>Loading…</Text> : null}
      </View>
      {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
      {section === "requests" && requests?.map((request) => (
        <Pressable key={request.requestId} onPress={() => router.push({ pathname: "/activity/request/[requestId]", params: { requestId: request.requestId } })}>
          <DataCard title={request.requestName} subtitle={request.requestDescription}>
            <Text style={pageStyles.muted}>{request.rrequestCreatedAt} · Tap to review →</Text>
          </DataCard>
        </Pressable>
      ))}
      {(section === "active" || section === "completed") && jobs?.map((job) => (
        <Pressable key={job.agentJobId} onPress={() => router.push({ pathname: "/activity/job/[jobId]", params: { jobId: job.agentJobId } })}>
          <DataCard title={job.agentJobName} subtitle={job.agentJobDescription}>
            <Text style={pageStyles.muted}>{section === "active" ? "Started" : "Completed"}: {section === "active" ? job.createdAt ?? "—" : job.completedAt ?? "—"}</Text>
            <Text style={pageStyles.secondaryText}>View job details →</Text>
          </DataCard>
        </Pressable>
      ))}
      {section === "payments" && payments?.map((payment) => (
        <DataCard key={payment.paymentId} title={payment.jobName} subtitle={`Paid ${payment.paidAt}`}>
          <View style={{ alignItems: "center", flexDirection: "row", justifyContent: "space-between" }}>
            <Text style={pageStyles.muted}>Job payment</Text>
            <Text style={{ color: colors.wine, fontSize: 17, fontWeight: "800" }}>${payment.paymentAmount.toFixed(2)}</Text>
          </View>
        </DataCard>
      ))}
      {!busy && !error && section === "requests" && !requests?.length ? <EmptyActivity title="No requests" message="If an agent needs a response from you, the request will show up here." /> : null}
      {!busy && !error && (section === "active" || section === "completed") && !jobs?.length ? <EmptyActivity title={`No ${section} jobs`} message={section === "active" ? "Jobs you accept and pay for will appear here while they are in progress." : "Finished jobs will be listed here."} /> : null}
      {!busy && !error && section === "payments" && !payments?.length ? <EmptyActivity title="No payments yet" message="When you accept a job offer, its payment record will appear here." /> : null}
      {!busy && error ? <Pressable onPress={() => void loadActivity()}><Text style={pageStyles.secondaryText}>Try again →</Text></Pressable> : null}
    </Page>
  );
}

function EmptyActivity({ title, message }: { title: string; message: string }) {
  return (
    <View style={{ alignItems: "center", backgroundColor: colors.paper, borderColor: colors.line, borderRadius: 20, borderWidth: 1, gap: 8, paddingHorizontal: 22, paddingVertical: 30 }}>
      <Text style={{ color: colors.wine, fontSize: 24 }}>◷</Text>
      <Text style={{ color: colors.wineDeep, fontSize: 17, fontWeight: "700" }}>{title}</Text>
      <Text style={[pageStyles.muted, { textAlign: "center" }]}>{message}</Text>
    </View>
  );
}
