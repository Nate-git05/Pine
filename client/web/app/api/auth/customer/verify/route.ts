import { NextRequest, NextResponse } from "next/server";

type VerificationRequest = {
  customer_token?: unknown;
  code?: unknown;
};

function getCustomerToken(value: unknown): string | null {
  if (typeof value !== "string" || !/^[0-9a-f-]{36}$/i.test(value)) {
    return null;
  }

  return value;
}

async function parseRequest(request: Request): Promise<VerificationRequest | null> {
  try {
    return await request.json() as VerificationRequest;
  } catch {
    return null;
  }
}

export async function POST(request: NextRequest) {
  const apiBaseUrl = process.env.PINE_API_BASE_URL?.replace(/\/$/, "")
    || (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "");

  if (!apiBaseUrl) {
    return NextResponse.json(
      { detail: "Customer registration is not configured yet. Please try again later." },
      { status: 503 },
    );
  }

  const requestData = await parseRequest(request);
  const customerToken = getCustomerToken(requestData?.customer_token);
  const code = typeof requestData?.code === "string" ? requestData.code.trim() : "";

  if (!requestData || !customerToken || !/^\d{6}$/.test(code)) {
    return NextResponse.json({ detail: "Enter the six-digit verification code." }, { status: 422 });
  }

  try {
    const backendResponse = await fetch(
      `${apiBaseUrl}/auth/customer/verify/${encodeURIComponent(customerToken)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
        cache: "no-store",
      },
    );
    const responseBody = await backendResponse.json().catch(() => ({
      detail: "The verification server returned an unreadable response.",
    }));

    if (!backendResponse.ok) {
      return NextResponse.json(responseBody, { status: backendResponse.status });
    }

    if (typeof responseBody.customer_token !== "string") {
      return NextResponse.json(
        { detail: "Pine verified your phone but could not create your session. Please try signing in." },
        { status: 502 },
      );
    }

    const response = NextResponse.json({ response: responseBody.response });
    response.cookies.set("pine_customer_session", responseBody.customer_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 60,
    });

    return response;
  } catch {
    return NextResponse.json(
      { detail: "Pine could not reach the verification server. Please try again." },
      { status: 502 },
    );
  }
}

export async function PATCH(request: Request) {
  const apiBaseUrl = process.env.PINE_API_BASE_URL?.replace(/\/$/, "")
    || (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "");

  if (!apiBaseUrl) {
    return NextResponse.json(
      { detail: "Customer registration is not configured yet. Please try again later." },
      { status: 503 },
    );
  }
  const requestData = await parseRequest(request);
  const customerToken = getCustomerToken(requestData?.customer_token);

  if (!requestData || !customerToken) {
    return NextResponse.json({ detail: "Registration expired. Please start again." }, { status: 422 });
  }

  try {
    const backendResponse = await fetch(
      `${apiBaseUrl}/auth/customer/verify/update/${encodeURIComponent(customerToken)}`,
      { method: "PATCH", cache: "no-store" },
    );
    const responseBody = await backendResponse.json().catch(() => ({
      detail: "The verification server returned an unreadable response.",
    }));

    return NextResponse.json(responseBody, { status: backendResponse.status });
  } catch {
    return NextResponse.json(
      { detail: "Pine could not reach the verification server. Please try again." },
      { status: 502 },
    );
  }
}
