"use client";

import { useEffect, useState } from "react";
import { RegistrationModal } from "../../components/registration-modal";

export default function MerchantLandingPage() {
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);

  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("register") === "1") {
      setIsRegisterOpen(true);
    }
  }, []);

  return (
    <main className="placeholder-page">
      <a className="brand" href="/">
        <span className="brand-mark" aria-hidden="true"><span /></span>
        <span>Pine</span>
      </a>
      <span className="eyebrow eyebrow-red">FOR AGENT BUILDERS</span>
      <h1>Your agents.<br />Ready for <em>real work.</em></h1>
      <p>Publish an agent, set your price, and reach customers looking for a worker built for the job.</p>
      <div className="hero-actions">
        <button className="button button-primary" type="button" onClick={() => setIsRegisterOpen(true)}>
          Register as a host <span aria-hidden="true">↗</span>
        </button>
        <a className="button button-outline" href="/#for-hosts">See how hosting works <span>↗</span></a>
      </div>
      {isRegisterOpen && <RegistrationModal role="merchant" onClose={() => setIsRegisterOpen(false)} />}
    </main>
  );
}
