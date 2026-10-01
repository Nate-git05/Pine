import * as SecureStore from "expo-secure-store";
import EventSource from "react-native-sse";
import {
  CustomerApi,
  type CustomerSessionStore,
  type EventSourceAdapter,
} from "./customer-api";

const CUSTOMER_TOKEN_KEY = "pine.customer.session";

export const customerSessionStore: CustomerSessionStore = {
  getToken: () => SecureStore.getItemAsync(CUSTOMER_TOKEN_KEY),
  saveToken: (token) => SecureStore.setItemAsync(CUSTOMER_TOKEN_KEY, token),
  clearToken: () => SecureStore.deleteItemAsync(CUSTOMER_TOKEN_KEY),
};

// The native EventSource package supports the Bearer header required by Pine.
export const createCustomerEventSource: EventSourceAdapter = (url, options) => {
  const eventSource = new EventSource(url, { headers: options.headers });

  return {
    addEventListener: (eventName, listener) => {
      eventSource.addEventListener(eventName, (event) => {
        listener({ data: "data" in event ? event.data : undefined });
      });
    },
    close: () => eventSource.close(),
  };
};

// Set EXPO_PUBLIC_PINE_API_URL in the mobile app's local environment.
const apiBaseUrl = process.env.EXPO_PUBLIC_PINE_API_URL;

export const customerApi = apiBaseUrl
  ? new CustomerApi({ baseUrl: apiBaseUrl, sessionStore: customerSessionStore })
  : null;
