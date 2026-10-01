import { NextResponse } from "next/server";

type MerchantRegistrationRequest = {
  first_name?: unknown;
  last_name?: unknown;
  email?: unknown;
  phonenumber?: unknown;
};

const registrationFields = ["first_name", "last_name", "email", "phonenumber"] as const;

export async function POST(request: Request) {
  const apiBaseUrl = process.env.PINE_API_BASE_URL?.replace(/\/$/, "")
    || (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "");

  if (!apiBaseUrl) {
    return NextResponse.json(
      { detail: "Merchant registration is not configured yet. Please try again later." },
      { status: 503 },
    );
  }

  let registrationData: MerchantRegistrationRequest;
  try {
    registrationData = await request.json() as MerchantRegistrationRequest;
  } catch {
    return NextResponse.json({ detail: "Registration data must be valid JSON." }, { status: 400 });
  }

  // Forward only the fields accepted by the merchant lead-registration route.
  const merchantRegistration: Record<(typeof registrationFields)[number], string> = {
    first_name: "",
    last_name: "",
    email: "",
    phonenumber: "",
  };

  for (const field of registrationFields) {
    const value = registrationData[field];
    if (typeof value !== "string" || !value.trim()) {
      return NextResponse.json(
        { detail: `Please enter a valid ${field.replace("_", " ")}.` },
        { status: 422 },
      );
    }
    merchantRegistration[field] = value.trim();
  }

  try {
    const backendResponse = await fetch(`${apiBaseUrl}/landing/register/merchant`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(merchantRegistration),
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
