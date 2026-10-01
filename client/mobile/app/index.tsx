import { Redirect } from "expo-router";
import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { customerSessionStore } from "../src/api/mobile-session";
import { colors } from "../src/theme/colors";

export default function IndexPage() {
  const [hasSession, setHasSession] = useState<boolean | null>(null);

  useEffect(() => {
    // Let the wordmark read as a real brand moment instead of a flash between screens.
    const splashTimer = setTimeout(() => {
      customerSessionStore.getToken()
        .then((token) => setHasSession(Boolean(token)))
        .catch(() => setHasSession(false));
    }, 900);

    return () => clearTimeout(splashTimer);
  }, []);

  if (hasSession === null) return <SplashScreen />;

  return <Redirect href={hasSession ? "/(tabs)/home" : "/auth"} />;
}

function SplashScreen() {
  return (
    <View style={styles.splash}>
      <Text style={styles.wordmark}>Pine</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  splash: { alignItems: "center", backgroundColor: colors.white, flex: 1, justifyContent: "center" },
  wordmark: { color: colors.taupe, fontFamily: "Georgia", fontSize: 58, letterSpacing: 1, paddingBottom: 8 },
});
