import { Redirect } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, View } from "react-native";
import { customerSessionStore } from "../src/api/mobile-session";

export default function IndexPage() {
  const [hasSession, setHasSession] = useState<boolean | null>(null);

  useEffect(() => {
    customerSessionStore.getToken().then((token) => setHasSession(Boolean(token)));
  }, []);

  if (hasSession === null) {
    return <View style={{ alignItems: "center", flex: 1, justifyContent: "center" }}><ActivityIndicator color="#174C3A" /></View>;
  }

  return <Redirect href={hasSession ? "/(tabs)/home" : "/auth"} />;
}
