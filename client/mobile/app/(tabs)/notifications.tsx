import { useCallback, useState } from "react";
import { useFocusEffect } from "expo-router";
import { Modal, Pressable, Text, View } from "react-native";
import { customerApi, createCustomerEventSource } from "../../src/api/mobile-session";
import type { NotificationDetails, NotificationEvent, NotificationList } from "../../src/api/customer-api";
import { ActionButton } from "../../src/components/action-button";
import { Page, pageStyles } from "../../src/components/page";
import { colors } from "../../src/theme/colors";

export default function NotificationsPage() {
  const [items, setItems] = useState<NotificationList["returnedNotifications"]>([]);
  const [selected, setSelected] = useState<NotificationDetails | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const loadNotifications = useCallback(async () => {
    if (!customerApi) {
      setError("The app is missing EXPO_PUBLIC_PINE_API_URL.");
      return;
    }
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
  }, []);

  useFocusEffect(useCallback(() => {
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
  }, [loadNotifications]));

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
    <Page title="Notifications" subtitle="Updates from Pine and your agents. Open one to mark it as read.">
      {selectedIds.length > 0 ? <ActionButton busy={busy} onPress={clearSelected} title={`Mark ${selectedIds.length} selected as read`} /> : null}
      {busy ? <Text style={pageStyles.muted}>Loading your inbox…</Text> : null}
      {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
      {items?.map((item) => {
        const isSelected = selectedIds.includes(item.notiId);
        return (
          <View key={item.notiId} style={{ backgroundColor: colors.paper, borderColor: isSelected ? colors.wine : colors.line, borderRadius: 20, borderWidth: isSelected ? 2 : 1, overflow: "hidden" }}>
            <Pressable accessibilityRole="button" onPress={() => void openNotification(item.notiId)} style={{ flexDirection: "row", gap: 12, padding: 16 }}>
              <View style={{ alignItems: "center", backgroundColor: colors.rose, borderRadius: 15, height: 42, justifyContent: "center", width: 42 }}>
                <Text style={{ color: colors.wine, fontSize: 19 }}>•</Text>
              </View>
              <View style={{ flex: 1, gap: 6 }}>
                <View style={{ alignItems: "center", flexDirection: "row", gap: 7 }}>
                  <Text style={{ color: colors.wineDeep, flex: 1, fontSize: 16, fontWeight: "700" }}>{item.notiHeader}</Text>
                  <View style={pageStyles.pill}><Text style={pageStyles.pillText}>NEW</Text></View>
                </View>
                <Text numberOfLines={2} style={pageStyles.body}>{item.notiMessage}</Text>
                <Text style={pageStyles.muted}>{item.notiType} · {new Date(item.notificationDate).toLocaleString()}</Text>
              </View>
            </Pressable>
            <Pressable accessibilityRole="checkbox" accessibilityState={{ checked: isSelected }} onPress={() => toggleSelection(item.notiId)} style={{ alignItems: "center", borderTopColor: colors.line, borderTopWidth: 1, flexDirection: "row", gap: 8, paddingHorizontal: 16, paddingVertical: 11 }}>
              <Text style={{ color: isSelected ? colors.wine : colors.muted, fontSize: 14 }}>{isSelected ? "☑" : "□"}</Text>
              <Text style={{ color: colors.wine, fontSize: 13, fontWeight: "700" }}>{isSelected ? "Selected to mark as read" : "Select to mark as read"}</Text>
            </Pressable>
          </View>
        );
      })}
      {!busy && !error && !items?.length ? (
        <View style={{ alignItems: "center", backgroundColor: colors.paper, borderColor: colors.line, borderRadius: 22, borderWidth: 1, gap: 11, justifyContent: "center", minHeight: 270, padding: 25 }}>
          <View style={{ alignItems: "center", backgroundColor: colors.sand, borderRadius: 25, height: 62, justifyContent: "center", width: 62 }}><Text style={{ color: colors.wine, fontSize: 28 }}>✓</Text></View>
          <Text style={{ color: colors.wineDeep, fontFamily: "Georgia", fontSize: 23, fontWeight: "700" }}>You’re all caught up.</Text>
          <Text style={[pageStyles.muted, { maxWidth: 270, textAlign: "center" }]}>New updates from Pine and your agents will appear here.</Text>
          <Pressable onPress={() => void loadNotifications()}><Text style={pageStyles.secondaryText}>Refresh inbox</Text></Pressable>
        </View>
      ) : null}
      <Modal animationType="fade" onRequestClose={() => setSelected(null)} transparent visible={Boolean(selected)}>
        <View style={{ alignItems: "center", flex: 1, justifyContent: "center", padding: 24 }}>
          <Pressable accessibilityLabel="Close notification details" onPress={() => setSelected(null)} style={{ backgroundColor: "rgba(15, 30, 22, 0.45)", bottom: 0, left: 0, position: "absolute", right: 0, top: 0 }} />
          <View style={{ backgroundColor: colors.paper, borderColor: colors.line, borderRadius: 22, borderWidth: 1, gap: 12, padding: 22, width: "100%" }}>
            <Text style={{ color: colors.wineDeep, fontFamily: "Georgia", fontSize: 23, fontWeight: "700" }}>{selected?.notification_header}</Text>
            <Text style={pageStyles.body}>{selected?.notification_message}</Text>
            <Text style={pageStyles.muted}>{selected?.notification_type} · {selected?.notification_date}</Text>
            <Pressable accessibilityRole="button" onPress={() => setSelected(null)} style={{ alignItems: "center", backgroundColor: colors.sand, borderRadius: 13, minHeight: 45, justifyContent: "center" }}><Text style={pageStyles.secondaryText}>Close</Text></Pressable>
          </View>
        </View>
      </Modal>
    </Page>
  );
}
