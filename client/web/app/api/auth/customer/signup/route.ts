import { NextResponse } from "next/server";

type CustomerSignupRequest = {
  first_name?: unknown;
  last_name?: unknown;
  email?: unknown;
  phonenumber?: unknown;
};

const signupFields = ["first_name", "last_name", "email", "phonenumber"] as const;

export async function POST(request: Request) {
  const apiBaseUrl = process.env.PINE_API_BASE_URL?.replace(/\/$/, "")
    || (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "");

  if (!apiBaseUrl) {
    return NextResponse.json(
      { detail: "Customer registration is not configured yet. Please try again later." },
      { status: 503 },
    );
  }

  let signupData: CustomerSignupRequest;
  try {
    signupData = await request.json() as CustomerSignupRequest;
  } catch {
    return NextResponse.json({ detail: "Registration data must be valid JSON." }, { status: 400 });
  }

  const customerSignup: Record<(typeof signupFields)[number], string> = {
    first_name: "",
    last_name: "",
    email: "",
    phonenumber: "",
  };

  for (const field of signupFields) {
    const value = signupData[field];
    if (typeof value !== "string" || !value.trim()) {
      return NextResponse.json(
        { detail: `Please enter a valid ${field.replace("_", " ")}.` },
        { status: 422 },
      );
    }
    customerSignup[field] = value.trim();
  }

  try {
    const backendResponse = await fetch(`${apiBaseUrl}/auth/customer/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(customerSignup),
      cache: "no-store",
    });
    const responseBody = await backendResponse.json().catch(() => ({
      detail: "The registration server returned an unreadable response.",
    }));

    return NextResponse.json(responseBody, { status: backendResponse.status });
  } catch {
    return NextResponse.json(
      { detail: "Pine could not reach the registration server. Please try again." },
      { status: 502 },
    );
  }
}
