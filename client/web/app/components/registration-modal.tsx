"use client";

import { type FormEvent, useEffect, useState } from "react";

type RegistrationRole = "customer" | "merchant";

type RegistrationResponse = {
  response?: string;
  detail?: string | Array<{ msg?: string }>;
};

export function RegistrationModal({
  role,
  onClose,
}: {
  role: RegistrationRole;
  onClose: () => void;
}) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [onClose]);

  async function submitRegistration(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setIsSubmitting(true);
    setErrorMessage("");

    const formData = new FormData(formElement);
    const registration = {
      first_name: String(formData.get("first_name") ?? "").trim(),
      last_name: String(formData.get("last_name") ?? "").trim(),
      email: String(formData.get("email") ?? "").trim(),
      phonenumber: String(formData.get("phonenumber") ?? "").trim(),
    };

    try {
      const response = await fetch(`/api/landing/register/${role}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(registration),
      });
      const responseData = await response.json() as RegistrationResponse;

      if (!response.ok) {
        const detail = Array.isArray(responseData.detail)
          ? responseData.detail.map((item) => item.msg).filter(Boolean).join(" ")
          : responseData.detail;
        throw new Error(detail || "We couldn’t complete your registration. Please try again.");
      }

      setSuccessMessage(responseData.response || "Thanks for registering. We’ll be in touch soon.");
      formElement.reset();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "We couldn’t reach Pine. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const isMerchant = role === "merchant";

  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section
        className="register-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="register-title"
      >
        <button className="modal-close" type="button" onClick={onClose} aria-label="Close registration form">×</button>
        <span className="eyebrow">{isMerchant ? "FOR AGENT BUILDERS" : "FOR PEOPLE WHO WANT WORK DONE"}</span>
        <h2 id="register-title">{isMerchant ? <>Bring your agent to <em>Pine.</em></> : <>Let’s get you <em>started.</em></>}</h2>
        <p className="modal-intro">
          {isMerchant
            ? "Register your interest in hosting an agent on Pine. We’ll be in touch as merchant onboarding opens."
            : "Register your interest in using Pine. We’ll be in touch as customer access opens."}
        </p>

        {successMessage ? (
          <div className="success-state" role="status">
            <span className="success-mark">✓</span>
            <p>{successMessage}</p>
            <button className="text-button" type="button" onClick={onClose}>Back to Pine</button>
          </div>
        ) : (
          <form className="register-form" onSubmit={submitRegistration}>
            <div className="form-name-row">
              <label>
                First name
                <input name="first_name" autoComplete="given-name" maxLength={50} required />
              </label>
              <label>
                Last name
                <input name="last_name" autoComplete="family-name" maxLength={50} required />
              </label>
            </div>
            <label>
              Email address
              <input name="email" type="email" autoComplete="email" maxLength={254} required />
            </label>
            <label>
              Phone number
              <input name="phonenumber" type="tel" autoComplete="tel" placeholder="+1 555 000 0000" required />
              <small>Include your country code.</small>
            </label>
            {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}
            <button className="button button-primary submit-button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Sending…" : "Register"}
              <span aria-hidden="true">↗</span>
            </button>
            <p className="form-footnote">No password or payment details required.</p>
          </form>
        )}
      </section>
    </div>
  );
}
