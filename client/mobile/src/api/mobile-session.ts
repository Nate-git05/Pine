import * as SecureStore from "expo-secure-store";
import { CustomerApi, type CustomerSessionStore } from "./customer-api";

const CUSTOMER_TOKEN_KEY = "pine.customer.session";

export const customerSessionStore: CustomerSessionStore = {
  getToken: () => SecureStore.getItemAsync(CUSTOMER_TOKEN_KEY),
  saveToken: (token) => SecureStore.setItemAsync(CUSTOMER_TOKEN_KEY, token),
  clearToken: () => SecureStore.deleteItemAsync(CUSTOMER_TOKEN_KEY),
};

// Set EXPO_PUBLIC_PINE_API_URL in the mobile app's local environment.
const apiBaseUrl = process.env.EXPO_PUBLIC_PINE_API_URL;

export const customerApi = apiBaseUrl
  ? new CustomerApi({ baseUrl: apiBaseUrl, sessionStore: customerSessionStore })
  : null;
