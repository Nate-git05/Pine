/**
 * Typed transport layer for the React Native customer application.
 *
 * Pass in the API origin and a secure token store from the mobile app shell.
 * This keeps this route layer independent of Expo, navigation, and UI choices.
 */

export interface CustomerSessionStore {
  getToken(): Promise<string | null>;
  saveToken(token: string): Promise<void>;
  clearToken(): Promise<void>;
}

export type CustomerApiOptions = {
  baseUrl: string;
  sessionStore: CustomerSessionStore;
  fetcher?: typeof fetch;
};

export type ApiErrorBody = {
  detail?: string | Array<{ msg?: string; loc?: Array<string | number> }>;
  [key: string]: unknown;
};

export class CustomerApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly body?: unknown,
  ) {
    super(message);
    this.name = "CustomerApiError";
  }
}

export type CustomerSignupRequest = {
  first_name: string;
  last_name: string;
  email: string;
  phonenumber: string;
};

export type CustomerTokenResponse = {
  customer_token?: string;
  token?: string;
  response?: string;
};

export type SearchAgentsRequest = {
  search_request: string;
  agent_ids_seen?: string[];
};

export type SearchAgent = {
  agent_id: string;
  agent_price: number;
  agent_name: string;
  agent_description: string;
};

export type SearchAgentsResponse = {
  response?: string | null;
  returned_agents?: SearchAgent[] | null;
  agent_seen_lst?: string[] | null;
};

export type AgentDetailsResponse = {
  returned_info?: {
    agent?: {
      agent_id?: string;
      agent_imgicon_key?: string;
      agent_price?: number;
      agent_rating?: number;
      agent_name?: string;
      agent_description?: string;
      agent_skills?: string[];
    };
    merchant?: {
      merchant_id?: string;
      merchant_name?: string;
      merchant_imgicon_key?: string;
    };
  };
};

export type HiredAgentResponse = {
  hired_agent_id?: string;
  hired_agent_name?: string;
  response?: string;
};

export type HiredAgentProfile = {
  id: string;
  name: string;
  description: string;
  state: string;
  rating: number;
  agent_imgicon_key: string;
  hired_at: string;
  price_per_job: number;
  agent_restrictions: string[] | null;
  agent_abilities: string[];
};

export type PaymentCard = {
  payment_id: string;
  payment_last4: string;
  payment_card_type: string;
  expires_at: string;
};

export type PaymentCardsResponse = {
  response?: string | null;
  payments_lst?: PaymentCard[] | null;
};

export type JobPaymentResponse = {
  response?: string | null;
  status: "succeeded" | "requires_action" | "processing";
  payment_intent_id?: string | null;
  client_secret?: string | null;
};

export type ApiMessageResponse = {
  response?: string;
};

export type JobOfferEvent = {
  offer_id: string;
  agent_name: string;
  agent_id: string;
  job_name: string;
  job_description_str: string;
  job_price: number;
};

export type NotificationEvent = {
  notification_id: string;
  notification_header: string;
  notification_message: string;
  notification_type: string;
};

export type GraphqlError = {
  message: string;
  path?: Array<string | number>;
};

type GraphqlEnvelope<TData> = {
  data?: TData;
  errors?: GraphqlError[];
};

export type ActivityCursor = {
  cursor?: boolean;
  last_id_seen?: string | null;
};

export type NotificationCursor = {
  cursor?: boolean;
  last_seen?: string | null;
};

export type JobRequestList = {
  statusCode: number;
  response?: string | null;
  cursor?: boolean | null;
  lastRequestDate?: string | null;
  returnedJobRequests?: Array<{
    requestId: string;
    requestName: string;
    requestDescription: string;
    rrequestCreatedAt: string;
  }> | null;
};

export type JobList = {
  statusCode: number;
  response?: string | null;
  cursor?: boolean | null;
  lastJobDate?: string | null;
  jobsReturned?: Array<{
    agentJobId: string;
    agentJobName: string;
    agentJobDescription: string;
    createdAt?: string | null;
    completedAt?: string | null;
  }> | null;
};

export type PaymentHistory = {
  statusCode: number;
  response?: string | null;
  cursor?: boolean | null;
  lastPaymentDate?: string | null;
  paymentsReturned?: Array<{
    paymentId: string;
    jobName: string;
    paymentAmount: number;
    paidAt: string;
  }> | null;
};

export type NotificationList = {
  statusCode: number;
  response?: string | null;
  cursor?: boolean | null;
  lastNotificationIdSeen?: string | null;
  returnedNotifications?: Array<{
    notiId: string;
    notiHeader: string;
    notiMessage: string;
    notiType: string;
    notificationDate: string;
  }> | null;
};

export type HiredAgentList = {
  statusCode: number;
  response?: string | null;
  hiredAgents?: Array<{
    id: string;
    name: string;
    description: string;
    state: "ACTIVE" | "FIRED" | string;
    rating: number;
  }> | null;
};

export type EmailIntegrationList = {
  statusCode: number;
  response?: string | null;
  integrations?: Array<{
    id: string;
    integrationType: string;
    integratedEmail: string;
    integratedAt: string;
  }> | null;
};

export type CustomerProfile = {
  customer_name: string;
  customer_email: string;
  customer_number: string;
  card_type?: string | null;
  active_card_last4?: string | null;
  expire_date?: string | null;
  number_of_agents: number;
  jobs_completed: number;
};

export type CustomerJob = {
  job_id: string;
  job_name: string;
  job_description: string;
  job_price: number;
  job_rating?: number | null;
  job_summary: string;
  hired_agent_id: string;
  hired_agent_name: string;
  assigned_at?: string | null;
  completed_at?: string | null;
};

export type CustomerJobRequest = {
  request_id: string;
  request_name: string;
  request_description: string;
  agent_current_job_summary: string;
  hired_agent_id: string;
  hired_agent_name: string;
  requested_at: string;
};

export type NotificationDetails = {
  notification_header: string;
  notification_message: string;
  notification_type: string;
  notification_date: string;
};

export type EventSourceAdapter = (
  url: string,
  options: { headers: Record<string, string> },
) => {
  addEventListener: (eventName: string, listener: (event: { data?: string }) => void) => void;
  close: () => void;
};

export type EventStreamCallbacks<TEvent> = {
  onMessage: (event: TEvent) => void;
  onError?: (error: unknown) => void;
};

/** API methods follow the route prefixes mounted in server/app.py. */
export class CustomerApi {
  private readonly baseUrl: string;
  private readonly fetcher: typeof fetch;
  private readonly sessionStore: CustomerSessionStore;

  constructor({ baseUrl, sessionStore, fetcher = fetch }: CustomerApiOptions) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.sessionStore = sessionStore;
    this.fetcher = fetcher;

    if (!this.baseUrl) {
      throw new Error("CustomerApi requires the deployed Pine API origin.");
    }
  }

  private async request<TResponse>(
    path: string,
    init: RequestInit = {},
    authenticated = true,
  ): Promise<TResponse> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");

    if (init.body !== undefined && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    if (authenticated) {
      const token = await this.sessionStore.getToken();
      if (!token) {
        throw new CustomerApiError("Your session has expired. Please sign in again.", 401);
      }
      headers.set("Authorization", `Bearer ${token}`);
    }

    let response: Response;
    try {
      response = await this.fetcher(`${this.baseUrl}${path}`, { ...init, headers });
    } catch (error) {
      throw new CustomerApiError(
        error instanceof Error ? error.message : "Unable to reach Pine.",
        0,
        error,
      );
    }

    const responseText = await response.text();
    let responseBody: unknown = undefined;
    if (responseText) {
      try {
        responseBody = JSON.parse(responseText);
      } catch {
        responseBody = responseText;
      }
    }

    if (!response.ok) {
      const errorBody = responseBody as ApiErrorBody | undefined;
      const detail = errorBody?.detail;
      const message = Array.isArray(detail)
        ? detail.map((item) => item.msg).filter(Boolean).join(" ")
        : typeof detail === "string" ? detail : `Pine returned HTTP ${response.status}.`;
      throw new CustomerApiError(message, response.status, responseBody);
    }

    return responseBody as TResponse;
  }

  private async graphql<TData, TVariables extends Record<string, unknown>>(
    path: string,
    query: string,
    variables: TVariables,
    cursorContext: ActivityCursor | NotificationCursor = {},
  ): Promise<TData> {
    const envelope = await this.request<GraphqlEnvelope<TData>>(
      path,
      {
        method: "POST",
        body: JSON.stringify({ query, variables, ...cursorContext }),
      },
    );

    if (envelope.errors?.length) {
      throw new CustomerApiError(
        envelope.errors.map((error) => error.message).join(" "),
        200,
        envelope.errors,
      );
    }
    if (!envelope.data) {
      throw new CustomerApiError("Pine returned an empty GraphQL response.", 502, envelope);
    }

    return envelope.data;
  }

  private openEventStream<TEvent>(
    path: string,
    createEventSource: EventSourceAdapter,
    callbacks: EventStreamCallbacks<TEvent>,
  ): () => void {
    let source: ReturnType<EventSourceAdapter> | undefined;
    let isClosed = false;

    void this.sessionStore.getToken().then((token) => {
      if (isClosed) return;
      if (!token) {
        callbacks.onError?.(new CustomerApiError("Your session has expired. Please sign in again.", 401));
        return;
      }

      source = createEventSource(`${this.baseUrl}${path}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      source.addEventListener("message", (event) => {
        if (!event.data) return;
        try {
          callbacks.onMessage(JSON.parse(event.data) as TEvent);
        } catch (error) {
          callbacks.onError?.(error);
        }
      });
      source.addEventListener("error", (event) => callbacks.onError?.(event));
    }).catch((error: unknown) => callbacks.onError?.(error));

    return () => {
      isClosed = true;
      source?.close();
    };
  }

  // SMS auth returns a temporary token first; verify() stores the session token.
  async signup(info: CustomerSignupRequest): Promise<CustomerTokenResponse> {
    return this.request("/auth/customer/signup", {
      method: "POST",
      body: JSON.stringify(info),
    }, false);
  }

  async login(info: Pick<CustomerSignupRequest, "email" | "phonenumber">): Promise<CustomerTokenResponse> {
    return this.request("/auth/customer/login", {
      method: "POST",
      body: JSON.stringify(info),
    }, false);
  }

  async verify(temporaryToken: string, code: string): Promise<CustomerTokenResponse> {
    const result = await this.request<CustomerTokenResponse>(
      `/auth/customer/verify/${encodeURIComponent(temporaryToken)}`,
      { method: "POST", body: JSON.stringify({ code }) },
      false,
    );

    if (!result.customer_token) {
      throw new CustomerApiError("Pine verified the code but did not return a session token.", 502, result);
    }
    await this.sessionStore.saveToken(result.customer_token);
    return result;
  }

  async resendVerificationCode(temporaryToken: string): Promise<CustomerTokenResponse> {
    return this.request(
      `/auth/customer/verify/update/${encodeURIComponent(temporaryToken)}`,
      { method: "PATCH" },
      false,
    );
  }

  async logout(): Promise<void> {
    try {
      await this.request<ApiMessageResponse>("/auth/customer/logout", { method: "POST" });
    } finally {
      // Clear the device session even if the network prevents server revocation.
      await this.sessionStore.clearToken();
    }
  }

  searchAgents(search: SearchAgentsRequest, limit = 10): Promise<SearchAgentsResponse> {
    return this.request(`/customer/search/agents?limit=${limit}`, {
      method: "POST",
      body: JSON.stringify(search),
    });
  }

  getAgent(agentId: string): Promise<AgentDetailsResponse> {
    return this.request(`/customer/search/agents/${encodeURIComponent(agentId)}`);
  }

  hireAgent(agentId: string, restrictions: string[] = []): Promise<HiredAgentResponse> {
    return this.request(`/customer/search/agent/hire/${encodeURIComponent(agentId)}`, {
      method: "POST",
      body: JSON.stringify({ agent_restrictions: restrictions }),
    });
  }

  getHiredAgent(hiredAgentId: string): Promise<HiredAgentProfile> {
    return this.request(`/profile/agents/${encodeURIComponent(hiredAgentId)}`);
  }

  fireAgent(hiredAgentId: string): Promise<ApiMessageResponse> {
    return this.request(`/profile/agents/fire/${encodeURIComponent(hiredAgentId)}`, { method: "PATCH" });
  }

  rehireAgent(hiredAgentId: string): Promise<ApiMessageResponse> {
    return this.request(`/profile/agents/hire/${encodeURIComponent(hiredAgentId)}`, { method: "PATCH" });
  }

  sendAgentMessage(hiredAgentId: string, message: string): Promise<ApiMessageResponse> {
    return this.request(`/customer/home/chat/${encodeURIComponent(hiredAgentId)}`, {
      method: "POST",
      body: JSON.stringify({ customer_message: message }),
    });
  }

  getSavedCards(): Promise<PaymentCardsResponse> {
    return this.request("/customer/home/cards");
  }

  addPaymentCard(): Promise<string | ApiMessageResponse> {
    return this.request("/customer/home/payment/add", { method: "POST" });
  }

  payForOffer(paymentId: string, hiredAgentId: string, offerId: string): Promise<JobPaymentResponse> {
    return this.request(
      `/customer/home/payment/${encodeURIComponent(paymentId)}/${encodeURIComponent(hiredAgentId)}/${encodeURIComponent(offerId)}`,
      { method: "POST" },
    );
  }

  confirmJobPayment(paymentIntentId: string): Promise<JobPaymentResponse> {
    return this.request(`/customer/home/payment/confirm/${encodeURIComponent(paymentIntentId)}`, {
      method: "POST",
    });
  }

  getOfferEvents(
    createEventSource: EventSourceAdapter,
    callbacks: EventStreamCallbacks<JobOfferEvent>,
  ): () => void {
    return this.openEventStream("/customer/webhooks/client/event", createEventSource, callbacks);
  }

  getCustomerProfile(): Promise<CustomerProfile> {
    return this.request("/profile/page");
  }

  async getActivityJobRequests(limit = 5, cursor: ActivityCursor = {}): Promise<{ jobRequests: JobRequestList }> {
    const query = `query CustomerJobRequests($limit: Int!) {
      jobRequests(limit: $limit) {
        statusCode response cursor lastRequestDate
        returnedJobRequests { requestId requestName requestDescription rrequestCreatedAt }
      }
    }`;
    return this.graphql("/customer/activity", query, { limit }, cursor);
  }

  async getActivityJobs(
    type: "active" | "completed",
    limit = 5,
    cursor: ActivityCursor = {},
  ): Promise<{ activeJobs?: JobList; completedJobs?: JobList }> {
    const fieldName = type === "active" ? "activeJobs" : "completedJobs";
    const query = `query Customer${type === "active" ? "Active" : "Completed"}Jobs($limit: Int!) {
      ${fieldName}(limit: $limit) {
        statusCode response cursor lastJobDate
        jobsReturned { agentJobId agentJobName agentJobDescription createdAt completedAt }
      }
    }`;
    return this.graphql(`/customer/activity`, query, { limit }, cursor);
  }

  async getPaymentHistory(limit = 5, cursor: ActivityCursor = {}): Promise<{ customerJobPayments: PaymentHistory }> {
    const query = `query CustomerJobPayments($limit: Int!) {
      customerJobPayments(limit: $limit) {
        statusCode response cursor lastPaymentDate
        paymentsReturned { paymentId jobName paymentAmount paidAt }
      }
    }`;
    return this.graphql("/customer/activity", query, { limit }, cursor);
  }

  getJob(jobId: string): Promise<CustomerJob> {
    return this.request(`/customer/activity/jobs/${encodeURIComponent(jobId)}`);
  }

  rateJob(jobId: string, rating: number): Promise<ApiMessageResponse> {
    return this.request(`/customer/activity/job/rating/${encodeURIComponent(jobId)}`, {
      method: "POST",
      body: JSON.stringify({ job_rating: rating }),
    });
  }

  getJobRequest(requestId: string): Promise<CustomerJobRequest> {
    return this.request(`/customer/activity/jobs/requests/${encodeURIComponent(requestId)}`);
  }

  answerJobRequest(requestId: string, response: string): Promise<ApiMessageResponse | undefined> {
    return this.request(`/customer/activity/request/answer/${encodeURIComponent(requestId)}`, {
      method: "POST",
      body: JSON.stringify({ customer_response: response }),
    });
  }

  async getNotifications(limit = 5, cursor: NotificationCursor = {}): Promise<{ customerNotifications: NotificationList }> {
    const query = `query CustomerNotifications($limit: Int!) {
      customerNotifications(limit: $limit) {
        statusCode response cursor lastNotificationIdSeen
        returnedNotifications { notiId notiHeader notiMessage notiType notificationDate }
      }
    }`;
    return this.graphql("/customer/notifications", query, { limit }, cursor);
  }

  getNotification(notificationId: string): Promise<NotificationDetails> {
    return this.request(`/customer/notifications/${encodeURIComponent(notificationId)}`);
  }

  clearNotifications(notificationIds: string[]): Promise<ApiMessageResponse> {
    if (notificationIds.length < 1 || notificationIds.length > 50) {
      throw new CustomerApiError("Select between 1 and 50 notifications to clear.", 400);
    }

    return this.request("/customer/notifications/clear", {
      method: "PATCH",
      body: JSON.stringify({ notification_ids: notificationIds }),
    });
  }

  getNotificationEvents(
    createEventSource: EventSourceAdapter,
    callbacks: EventStreamCallbacks<NotificationEvent>,
  ): () => void {
    return this.openEventStream("/customer/notifications/events", createEventSource, callbacks);
  }

  async getHiredAgents(state: "active" | "fired"): Promise<{ activeHiredAgents?: HiredAgentList; firedHiredAgents?: HiredAgentList }> {
    const fieldName = state === "active" ? "activeHiredAgents" : "firedHiredAgents";
    const query = `query Customer${state === "active" ? "Active" : "Fired"}Agents {
      ${fieldName} {
        statusCode response
        hiredAgents { id name description state rating }
      }
    }`;
    return this.graphql("/customer/profile/agents", query, {});
  }

  async getEmailIntegrations(): Promise<{ customerEmailIntegrations: EmailIntegrationList }> {
    const query = `query CustomerEmailIntegrations {
      customerEmailIntegrations {
        statusCode response
        integrations { id integrationType integratedEmail integratedAt }
      }
    }`;
    return this.graphql("/customer/profile/integrations/email", query, {});
  }

  deleteEmailIntegration(integrationId: string): Promise<ApiMessageResponse> {
    return this.request(`/profile/integrations/email/delete/${encodeURIComponent(integrationId)}`, {
      method: "POST",
    });
  }

  startGmailConnection(): Promise<{ redirect_url: string }> {
    return this.request("/profile/oauth2/email/gmail", { method: "POST" });
  }
}
