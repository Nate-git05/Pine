import { ActivityIndicator, Pressable, Text } from "react-native";
import { pageStyles } from "./page";

export function ActionButton({
  title,
  onPress,
  disabled = false,
  busy = false,
}: {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  busy?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled || busy}
      onPress={onPress}
      style={({ pressed }) => [pageStyles.button, pressed && { opacity: 0.85 }, (disabled || busy) && { opacity: 0.6 }]}
    >
      {busy ? <ActivityIndicator color="#FFFFFF" /> : <Text style={pageStyles.buttonText}>{title}</Text>}
    </Pressable>
  );
}
