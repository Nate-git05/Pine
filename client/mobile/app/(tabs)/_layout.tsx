import { Tabs } from "expo-router";
import { Text } from "react-native";
import { colors } from "../../src/theme/colors";

export default function CustomerTabs() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.wine,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: { backgroundColor: colors.paper, borderTopColor: colors.line, height: 68, paddingTop: 8, paddingBottom: 8 },
        tabBarLabelStyle: { fontSize: 11, fontWeight: "700" },
        tabBarItemStyle: { paddingTop: 1 },
      }}
    >
      <Tabs.Screen name="home" options={{ title: "Home", tabBarIcon: ({ color }) => <TabMark mark="⌂" color={color} /> }} />
      <Tabs.Screen name="search" options={{ title: "Search", tabBarIcon: ({ color }) => <TabMark mark="⌕" color={color} /> }} />
      <Tabs.Screen name="activity" options={{ title: "Activity", tabBarIcon: ({ color }) => <TabMark mark="◷" color={color} /> }} />
      <Tabs.Screen name="notifications" options={{ title: "Updates", tabBarIcon: ({ color }) => <TabMark mark="♧" color={color} /> }} />
      <Tabs.Screen name="profile" options={{ title: "You", tabBarIcon: ({ color }) => <TabMark mark="○" color={color} /> }} />
    </Tabs>
  );
}

function TabMark({ mark, color }: { mark: string; color: string }) {
  return <Text style={{ color, fontSize: 23, fontWeight: "500", lineHeight: 25 }}>{mark}</Text>;
}
