import { useEffect, useMemo, useState } from "react";
import { useLocalSearchParams } from "expo-router";
import { Alert, AppState, Modal, Pressable, ScrollView, Text, TextInput, View } from "react-native";
import * as WebBrowser from "expo-web-browser";
import { customerApi, createCustomerEventSource } from "../../src/api/mobile-session";
import type { HiredAgentProfile, JobOfferEvent, PaymentCard } from "../../src/api/customer-api";
import { ActionButton } from "../../src/components/action-button";
import { DataCard } from "../../src/components/data-card";
import { Page, pageStyles } from "../../src/components/page";

type ChatLine = { id: string; author: "you" | "agent"; text: string };

export default function AgentChatPage() {
  const { hiredAgentId, name } = useLocalSearchParams<{ hiredAgentId: string; name?: string }>();
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatLine[]>([]);
  const [offers, setOffers] = useState<JobOfferEvent[]>([]);
  const [cards, setCards] = useState<PaymentCard[]>([]);
  const [hiredAgent, setHiredAgent] = useState<HiredAgentProfile | null>(null);
  const [selectedOffer, setSelectedOffer] = useState<JobOfferEvent | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const agentTitle = useMemo(
    () => Array.isArray(name) ? name[0] : name ?? hiredAgent?.name ?? "Your agent",
    [hiredAgent?.name, name],
  );

  useEffect(() => {
    if (!customerApi || !hiredAgentId) return;
    const stopListening = customerApi.getOfferEvents(createCustomerEventSource, {
      onMessage: (offer) => {
        // A customer's stream can deliver offers for each active hired agent.
        if (offer.agent_id === hiredAgentId) {
          setOffers((current) => current.some((item) => item.offer_id === offer.offer_id) ? current : [offer, ...current]);
        }
      },
      onError: (streamError) => setError(streamError instanceof Error ? streamError.message : "Live job updates disconnected."),
    });
    void loadCards();
    void customerApi.getHiredAgent(hiredAgentId).then(setHiredAgent).catch((profileError: unknown) => {
      setError(profileError instanceof Error ? profileError.message : "Unable to load this agent profile.");
    });
    return stopListening;
  }, [hiredAgentId]);

  useEffect(() => {
    const appStateListener = AppState.addEventListener("change", (state) => {
      // Stripe's hosted card setup returns through the browser; refresh when the app resumes.
      if (state === "active") void loadCards();
    });
    return () => appStateListener.remove();
  }, []);

  async function loadCards() {
    if (!customerApi) return;
    try {
      const result = await customerApi.getSavedCards();
      setCards(result.payments_lst ?? []);
    } catch (cardError) {
      setError(cardError instanceof Error ? cardError.message : "Unable to load saved cards.");
    }
  }

  async function sendMessage() {
    if (!customerApi || !hiredAgentId || !message.trim()) return;
    const sentMessage = message.trim();
    setMessage("");
    setError("");
    setBusy(true);
    setMessages((current) => [...current, { id: `${Date.now()}-you`, author: "you", text: sentMessage }]);
    try {
      const result = await customerApi.sendAgentMessage(hiredAgentId, sentMessage);
      setMessages((current) => [...current, { id: `${Date.now()}-agent`, author: "agent", text: result.response ?? "Your agent has replied." }]);
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : "Unable to send your message.");
    } finally {
      setBusy(false);
    }
  }

  async function payWithCard(card: PaymentCard) {
    if (!customerApi || !selectedOffer) return;
    setBusy(true);
    setError("");
    try {
      await customerApi.payForOffer(card.payment_id, hiredAgentId, selectedOffer.offer_id);
      setOffers((current) => current.filter((offer) => offer.offer_id !== selectedOffer.offer_id));
      Alert.alert("Job sent", `Pine paid with the card ending in ${card.payment_last4} and sent the job to ${agentTitle}.`);
      setSelectedOffer(null);
    } catch (paymentError) {
      setError(paymentError instanceof Error ? paymentError.message : "Unable to complete this payment.");
    } finally {
      setBusy(false);
    }
  }

  async function addCard() {
    if (!customerApi) return;
    setBusy(true);
    setError("");
    try {
      const checkout = await customerApi.addPaymentCard();
      const checkoutUrl = typeof checkout === "string" ? checkout : checkout.response;
      if (!checkoutUrl) throw new Error("Pine did not return a card setup link.");
      await WebBrowser.openBrowserAsync(checkoutUrl);
    } catch (cardError) {
      setError(cardError instanceof Error ? cardError.message : "Unable to open card setup.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Page title={agentTitle}>
      <Text style={pageStyles.muted}>Messages go to your agent. Job offers arrive here as payment cards.</Text>
      {hiredAgent ? (
        <DataCard title={`${hiredAgent.state} agent`} subtitle={hiredAgent.description}>
          <Text style={pageStyles.muted}>${hiredAgent.price_per_job.toFixed(2)} per job</Text>
          {hiredAgent.agent_abilities.map((ability) => <Text key={ability} style={pageStyles.muted}>• {ability}</Text>)}
          {hiredAgent.agent_restrictions?.map((restriction) => <Text key={restriction} style={pageStyles.muted}>Restriction: {restriction}</Text>)}
        </DataCard>
      ) : null}
      {error ? <Text accessibilityRole="alert" style={pageStyles.error}>{error}</Text> : null}
      {offers.map((offer) => (
        <DataCard key={offer.offer_id} title={offer.job_name} subtitle={offer.job_description_str}>
          <Text style={pageStyles.muted}>${offer.job_price.toFixed(2)}</Text>
          <ActionButton onPress={() => setSelectedOffer(offer)} title="Review payment" />
        </DataCard>
      ))}
      <View style={pageStyles.card}>
        <Text style={pageStyles.label}>Conversation</Text>
        {!messages.length ? <Text style={pageStyles.muted}>Send a message to start talking with {agentTitle}.</Text> : null}
        {messages.map((line) => (
          <View key={line.id} style={{ alignSelf: line.author === "you" ? "flex-end" : "flex-start", backgroundColor: line.author === "you" ? "#E4F0E8" : "#F0F3F0", borderRadius: 14, maxWidth: "90%", padding: 12 }}>
            <Text style={pageStyles.body}>{line.text}</Text>
          </View>
        ))}
        <TextInput multiline onChangeText={setMessage} onSubmitEditing={() => void sendMessage()} placeholder="Message your agent" style={[pageStyles.input, { minHeight: 54, paddingTop: 14 }]} value={message} />
        <ActionButton busy={busy} disabled={!message.trim()} onPress={sendMessage} title="Send message" />
      </View>
      <Modal animationType="slide" onRequestClose={() => setSelectedOffer(null)} transparent visible={Boolean(selectedOffer)}>
        <View style={{ backgroundColor: "rgba(15, 30, 22, 0.45)", flex: 1, justifyContent: "flex-end" }}>
          <View style={{ backgroundColor: "#F3F6F2", borderTopLeftRadius: 24, borderTopRightRadius: 24, gap: 14, maxHeight: "80%", padding: 24 }}>
            <Text style={{ color: "#1D2B24", fontSize: 24, fontWeight: "700" }}>Choose a card</Text>
            <Text style={pageStyles.body}>Pay ${selectedOffer?.job_price.toFixed(2)} for “{selectedOffer?.job_name}”.</Text>
            <ScrollView contentContainerStyle={{ gap: 10 }}>
              {cards.map((card) => (
                <Pressable key={card.payment_id} disabled={busy} onPress={() => void payWithCard(card)} style={pageStyles.card}>
                  <Text style={pageStyles.label}>{card.payment_card_type} ending in {card.payment_last4}</Text>
                  <Text style={pageStyles.muted}>Expires {card.expires_at}</Text>
                </Pressable>
              ))}
            </ScrollView>
            {cards.length === 0 ? <Text style={pageStyles.muted}>You don’t have a saved card yet. Add one to pay for this job.</Text> : null}
            <ActionButton busy={busy} onPress={addCard} title="Add a card" />
            <Text onPress={() => setSelectedOffer(null)} style={pageStyles.secondaryText}>Cancel</Text>
          </View>
        </View>
      </Modal>
    </Page>
  );
}
