import { useEffect, useState } from "react";
import { Modal, Pressable, Text, View } from "react-native";
import { customerApi, createCustomerEventSource } from "../../src/api/mobile-session";
import type { NotificationDetails, NotificationEvent, NotificationList } from "../../src/api/customer-api";
import { ActionButton } from "../../src/components/action-button";
import { DataCard } from "../../src/components/data-card";
import { Page, pageStyles } from "../../src/components/page";
import { colors } from "../../src/theme/colors";

export default function NotificationsPage() {
  const [items, setItems] = useState<NotificationList["returnedNotifications"]>([]);
  const [selected, setSelected] = useState<NotificationDetails | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function loadNotifications() {
    if (!customerApi) return setError("The app is missing EXPO_PUBLIC_PINE_API_URL.");
    setBusy(true);
    try {
      const result = await customerApi.getNotifications();
      setItems(result.customerNotifications.returnedNotifications ?? []);
      setSelectedIds([]);
      setError("");
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Unable to load notifications.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void loadNotifications();
    if (!customerApi) return;
    return customerApi.getNotificationEvents(createCustomerEventSource, {
      onMessage: (notification: NotificationEvent) => {
        setItems((current) => [
          { notiId: notification.notification_id, notiHeader: notification.notification_header, notiMessage: notification.notification_message, notiType: notification.notification_type, notificationDate: new Date().toISOString() },
          ...(current ?? []).filter((item) => item.notiId !== notification.notification_id),
        ]);
      },
      onError: (streamError) => setError(streamError instanceof Error ? streamError.message : "Live notifications disconnected."),
    });
  }, []);

  async function openNotification(notificationId: string) {
    if (!customerApi) return;
    setBusy(true);
    try {
      setSelected(await customerApi.getNotification(notificationId));
    } catch (detailError) {
      setError(detailError instanceof Error ? detailError.message : "Unable to open this notification.");
    } finally {
      setBusy(false);
      await loadNotifications();
    }
  }

  async function clearSelected() {
    if (!customerApi || !selectedIds.length) return;
    setBusy(true);
    try {
      await customerApi.clearNotifications(selectedIds);
      await loadNotifications();
    } catch (clearError) {
      setError(clearError instanceof Error ? clearError.message : "Unable to clear notifications.");
    } finally {
      setBusy(false);
    }
  }

  function toggleSelection(notificationId: string) {
    setSelectedIds((current) => current.includes(notificationId)
      ? current.filter((id) => id !== notificationId)
      : [...current, notificationId]);
  }

  return (
    <Page title="Notifications">
      <Text style={pageStyles.body}>Updates from your agents and Pine.</Text>
      {selectedIds.length > 0 ? <ActionButton busy={busy} onPress={clearSelected} title={`Mark ${selectedIds.length} selected as read`} /> : null}
      {busy ? <Text style={pageStyles.muted}>Loading notifications…</Text> : null}
      {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
      {items?.map((item) => {
        const isSelected = selectedIds.includes(item.notiId);
        return (
          <DataCard key={item.notiId} title={item.notiHeader} subtitle={`${item.notiType} · ${item.notificationDate}`}>
            <Pressable onPress={() => void openNotification(item.notiId)}>
              <Text numberOfLines={2} style={pageStyles.body}>{item.notiMessage}</Text>
            </Pressable>
            <Text onPress={() => toggleSelection(item.notiId)} style={pageStyles.secondaryText}>{isSelected ? "✓ Selected for clear" : "Select to mark read"}</Text>
          </DataCard>
        );
      })}
      {!busy && !error && !items?.length ? <Text style={pageStyles.muted}>You’re all caught up.</Text> : null}
      <Modal animationType="fade" onRequestClose={() => setSelected(null)} transparent visible={Boolean(selected)}>
        <Pressable onPress={() => setSelected(null)} style={{ alignItems: "center", backgroundColor: "rgba(15, 30, 22, 0.45)", flex: 1, justifyContent: "center", padding: 24 }}>
          <View style={{ backgroundColor: colors.paper, borderRadius: 20, gap: 12, padding: 22, width: "100%" }}>
            <Text style={{ color: colors.wineDeep, fontSize: 21, fontWeight: "700" }}>{selected?.notification_header}</Text>
            <Text style={pageStyles.body}>{selected?.notification_message}</Text>
            <Text style={pageStyles.muted}>{selected?.notification_type} · {selected?.notification_date}</Text>
            <Text onPress={() => setSelected(null)} style={pageStyles.secondaryText}>Close</Text>
          </View>
        </Pressable>
      </Modal>
    </Page>
  );
}
