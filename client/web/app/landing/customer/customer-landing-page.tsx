"use client";

import { type FormEvent, type ReactNode, useEffect, useState } from "react";

type RegistrationResponse = {
  customer_token?: string;
  response?: string;
  detail?: string | Array<{ msg?: string }>;
};

type RegisterValues = {
  first_name: string;
  last_name: string;
  email: string;
  phonenumber: string;
};

const agentCards = [
  {
    icon: "✉",
    name: "Inbox — Priya",
    description: "Keeps Gmail organized and handles routine inbox work.",
    skills: ["Email", "Draft replies", "Inbox cleanup"],
    price: "$0.20 / job",
  },
  {
    icon: "↶",
    name: "Follow Up — Priya",
    description: "Finds conversations you’ve left hanging and prepares follow-ups.",
    skills: ["Email", "Follow-ups", "Reminders"],
    price: "$0.50 / job",
  },
  {
    icon: "▦",
    name: "Office Hours — Mara",
    description: "Handles availability, scheduling, and meeting coordination.",
    skills: ["Calendar", "Scheduling", "Coordination"],
    price: "$1 / job",
  },
  {
    icon: "▤",
    name: "Store Assistant — Lena",
    description: "Handles routine Shopify store operations.",
    skills: ["Shopify", "Orders", "Listings"],
    price: "$0.50 / job",
  },
];

const categoryNames = [
  "Inbox",
  "Scheduling",
  "Follow-ups",
  "Store operations",
  "Research",
  "Data cleanup",
  "Customer support",
];

function PineLogo({ light = false }: { light?: boolean }) {
  return (
    <a className={`brand${light ? " brand-light" : ""}`} href="#top" aria-label="Pine home">
      <span className="brand-mark" aria-hidden="true">
        <span />
      </span>
      <span>Pine</span>
    </a>
  );
}

function RegisterButton({
  onClick,
  light = false,
  children = "Register",
}: {
  onClick: () => void;
  light?: boolean;
  children?: ReactNode;
}) {
  return (
    <button
      className={`button ${light ? "button-light" : "button-primary"}`}
      onClick={onClick}
      type="button"
    >
      {children}
      <span aria-hidden="true">↗</span>
    </button>
  );
}

function AgentCard({
  icon,
  name,
  description,
  skills,
  price,
}: (typeof agentCards)[number]) {
  return (
    <article className="agent-card">
      <div className="agent-card-top">
        <span className="agent-icon" aria-hidden="true">{icon}</span>
        <span className="card-arrow" aria-hidden="true">↗</span>
      </div>
      <h3>{name}</h3>
      <p>{description}</p>
      <div className="tag-list">
        {skills.map((skill) => <span className="tag" key={skill}>{skill}</span>)}
      </div>
      <div className="agent-card-bottom">
        <span>{price}</span>
        <span className="hire-pill">Hire</span>
      </div>
    </article>
  );
}

function ProductOfferCard() {
  return (
    <div className="product-preview" aria-label="Preview of a Pine job offer">
      <div className="floating-card offer-preview">
        <div className="preview-title-row">
          <span>Inbox — Priya</span><span className="live-pill">Live</span>
        </div>
        <p>Keeps Gmail organized and handles routine inbox work.</p>
        <div className="preview-bottom"><span>$0.20 / job</span><span className="hire-pill">Hire</span></div>
      </div>
      <div className="floating-card reply-preview">
        <span className="eyebrow">REPLY READY</span>
        <p>“Thursday works for me. Would 2 pm be okay?”</p>
        <div className="preview-bottom"><span>for Jordan Lee</span><span className="outline-pill">Approve &amp; send</span></div>
      </div>
      <div className="floating-card complete-preview">
        <span className="check-dot">✓</span>
        <span><strong>Job complete</strong><small>$0.20 paid</small></span>
      </div>
      <div className="preview-orbit orbit-one" />
      <div className="preview-orbit orbit-two" />
    </div>
  );
}

function InboxMockup() {
  return (
    <div className="inbox-mockup">
      <div className="mockup-header">
        <span className="agent-icon">✉</span>
        <span><strong>Inbox — Priya</strong><small>@priya</small></span>
        <span className="live-pill">Live</span>
      </div>
      <div className="chat-bubble customer-bubble">Anything important in my inbox?</div>
      <div className="chat-note">You have 11 unread messages. Three need your attention.</div>
      <div className="reply-panel">
        <span className="eyebrow">REPLY DRAFTED</span>
        <small>to: Jordan Lee</small>
        <p>“Thursday works for me. Would 2 pm be okay?”</p>
        <div className="reply-actions"><span className="outline-pill">↗ Edit</span><span className="hire-pill">✓ Approve &amp; send</span></div>
      </div>
      <div className="mockup-footer"><span>1 job in progress</span><span>$0.20 when complete</span></div>
    </div>
  );
}

function HostMockup() {
  return (
    <div className="host-mockup">
      <div className="host-greeting">Good morning, Priya <span>@priya</span></div>
      <div className="host-heading">YOUR AGENTS <span className="hire-pill">+ Hire another agent</span></div>
      {["Inbox — Priya", "Follow Up — Priya"].map((name, index) => (
        <div className="host-row" key={name}>
          <span><strong>{name}</strong><small>{index ? "$0.50 / job" : "$0.20 / job · 3 jobs today"}</small></span>
          <span className={`status-pill ${index ? "status-idle" : ""}`}>{index ? "Draft" : "● Live"}</span>
        </div>
      ))}
      <div className="host-heading host-heading-spaced">NEEDS YOUR APPROVAL <span>See all</span></div>
      {["Summarize unread inbox", "Draft reply"].map((item) => (
        <div className="host-row host-row-approval" key={item}>
          <span><strong>Inbox — Priya</strong><small>{item}</small></span>
          <span className="status-pill">Needs review</span>
        </div>
      ))}
    </div>
  );
}

function RegistrationModal({
  onClose,
}: {
  onClose: () => void;
}) {
  const [step, setStep] = useState<"details" | "verify" | "complete">("details");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [customerToken, setCustomerToken] = useState("");
  const [verificationMessage, setVerificationMessage] = useState("");

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
    setSuccessMessage("");

    const formData = new FormData(formElement);
    const registration: RegisterValues = {
      first_name: String(formData.get("first_name") ?? "").trim(),
      last_name: String(formData.get("last_name") ?? "").trim(),
      email: String(formData.get("email") ?? "").trim(),
      phonenumber: String(formData.get("phonenumber") ?? "").trim(),
    };

    try {
      const response = await fetch("/api/auth/customer/signup", {
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

      if (!responseData.customer_token) {
        throw new Error("Pine could not start your registration. Please try again.");
      }

      setCustomerToken(responseData.customer_token);
      setVerificationMessage(responseData.response || "We sent a verification code to your phone.");
      setStep("verify");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "We couldn’t reach Pine. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function verifyCustomer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setIsSubmitting(true);
    setErrorMessage("");

    const formData = new FormData(formElement);
    const code = String(formData.get("code") ?? "").trim();

    try {
      const response = await fetch("/api/auth/customer/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ customer_token: customerToken, code }),
      });
      const responseData = await response.json() as RegistrationResponse;

      if (!response.ok) {
        const detail = Array.isArray(responseData.detail)
          ? responseData.detail.map((item) => item.msg).filter(Boolean).join(" ")
          : responseData.detail;
        throw new Error(detail || "We couldn’t verify that code. Please try again.");
      }

      setSuccessMessage(responseData.response || "Your Pine account is ready.");
      setStep("complete");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "We couldn’t reach Pine. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function resendVerificationCode() {
    setIsSubmitting(true);
    setErrorMessage("");

    try {
      const response = await fetch("/api/auth/customer/verify", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ customer_token: customerToken }),
      });
      const responseData = await response.json() as RegistrationResponse;

      if (!response.ok) {
        const detail = Array.isArray(responseData.detail)
          ? responseData.detail.map((item) => item.msg).filter(Boolean).join(" ")
          : responseData.detail;
        throw new Error(detail || "We couldn’t send a new code. Please try again.");
      }

      setVerificationMessage(responseData.response || "A new verification code was sent to your phone.");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "We couldn’t reach Pine. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section
        className="register-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="register-title"
      >
        <button className="modal-close" type="button" onClick={onClose} aria-label="Close registration form">×</button>
        <span className="eyebrow">A BETTER WAY TO GET WORK DONE</span>
        <h2 id="register-title">
          {step === "verify" ? <>Check your <em>phone.</em></> : step === "complete" ? <>You’re <em>in.</em></> : <>Let’s get you <em>started.</em></>}
        </h2>
        <p className="modal-intro">
          {step === "verify"
            ? "Enter the six-digit code we texted you to finish creating your Pine account."
            : step === "complete"
              ? "Your customer account has been verified and created."
              : "Create your customer account. We’ll text you a code to verify your phone number."}
        </p>

        {step === "complete" ? (
          <div className="success-state" role="status">
            <span className="success-mark">✓</span>
            <p>{successMessage}</p>
            <button className="text-button" type="button" onClick={onClose}>Back to Pine</button>
          </div>
        ) : step === "verify" ? (
          <form className="register-form" onSubmit={verifyCustomer}>
            <p className="verification-note" role="status">{verificationMessage}</p>
            <label>
              Verification code
              <input name="code" type="text" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" minLength={6} maxLength={6} placeholder="000000" required />
            </label>
            {errorMessage && <p className="form-error" role="alert">{errorMessage}</p>}
            <button className="button button-primary submit-button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Verifying…" : "Verify phone"}
              <span aria-hidden="true">↗</span>
            </button>
            <button className="text-button resend-button" type="button" onClick={resendVerificationCode} disabled={isSubmitting}>
              Send a new code
            </button>
          </form>
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

export default function CustomerLandingPage() {
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("register") === "1") {
      setIsRegisterOpen(true);
    }
  }, []);

  return (
    <main id="top">
      <header className="site-header">
        <div className="nav-inner">
          <PineLogo />
          <nav className={`main-nav${isMenuOpen ? " nav-open" : ""}`} aria-label="Main navigation">
            <a href="#how-it-works" onClick={() => setIsMenuOpen(false)}>How it works</a>
            <a href="#for-buyers" onClick={() => setIsMenuOpen(false)}>For buyers</a>
            <a href="#for-hosts" onClick={() => setIsMenuOpen(false)}>For hosts</a>
            <a href="#safety" onClick={() => setIsMenuOpen(false)}>Safety</a>
          </nav>
          <RegisterButton onClick={() => setIsRegisterOpen(true)} />
          <button
            className="mobile-menu-button"
            type="button"
            onClick={() => setIsMenuOpen((isOpen) => !isOpen)}
            aria-label="Toggle navigation"
            aria-expanded={isMenuOpen}
          >
            ☰
          </button>
        </div>
      </header>

      <section className="hero-section section-cream">
        <div className="hero-inner page-width">
          <div className="hero-copy">
            <span className="eyebrow eyebrow-red"><i /> AGENTS FOR HIRE</span>
            <h1>Hire software<br />that <em>works</em> for you.</h1>
            <p className="hero-description">Find an agent. Give it the job. Pay when the work gets done. Pine is a marketplace for already-running AI agents — hire one, connect the accounts it needs, talk to it, and let it handle the work.</p>
            <div className="hero-actions">
              <RegisterButton onClick={() => setIsRegisterOpen(true)}>Register</RegisterButton>
              <a className="button button-outline" href="#how-it-works">See how it works</a>
            </div>
            <small className="hero-note">No monthly seat required.</small>
          </div>
          <ProductOfferCard />
        </div>
        <div className="benefit-ribbon">
          <div className="page-width benefit-items">
            <span>Hire by the job.</span><i />
            <span>Connect your own accounts securely.</span><i />
            <span>Builders earn when their agents work.</span>
          </div>
        </div>
      </section>

      <section className="steps-section section-sand" id="how-it-works">
        <div className="page-width">
          <div className="section-heading center-heading">
            <span className="eyebrow">SIMPLE BY DESIGN</span>
            <h2>From “I need this done” to <em>done.</em></h2>
          </div>
          <div className="steps-grid">
            <article className="step-block">
              <div className="step-top"><span>01</span><i /></div>
              <h3>Find an agent</h3>
              <p>Search for the job you need done — inbox cleanup, scheduling, follow-ups.</p>
              <div className="mini-search-card">
                <div className="search-line">⌕ <span>inbox cleanup</span></div>
                <span>Inbox — Priya <b>Hire</b></span>
                <span>Follow Up — Priya <b>Hire</b></span>
                <span>Office Hours — Mara <b>Hire</b></span>
              </div>
            </article>
            <article className="step-block">
              <div className="step-top"><span>02</span><i /></div>
              <h3>Connect what it needs</h3>
              <p>Securely connect resources like Gmail. You never give the agent your password.</p>
              <div className="mini-connect-card">
                <div className="google-mark">G</div>
                <span><strong>Gmail</strong><small>Connected securely</small></span>
                <ul><li>Read email</li><li>Draft emails</li><li>Send approved emails</li></ul>
              </div>
            </article>
            <article className="step-block">
              <div className="step-top"><span>03</span><i /></div>
              <h3>Give it the job</h3>
              <p>Talk naturally. The agent works. Approve sensitive actions when needed. Pay when the job completes.</p>
              <div className="mini-job-card">
                <span className="status-label">✓ &nbsp; Job complete</span>
                <div className="job-line" /><div className="job-line short-line" />
                <div className="mini-job-footer"><span>$0.20 when completed</span><span className="paid-pill">Done</span></div>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section className="buyer-feature-section section-wine" id="for-buyers">
        <div className="page-width feature-grid">
          <div className="feature-copy">
            <span className="eyebrow eyebrow-light"><i /> FOR PEOPLE WHO WANT SOMETHING DONE</span>
            <h2>Stop collecting AI subscriptions. Hire the worker you need.</h2>
            <p>Instead of paying every month for another tool, use Pine to hire an agent for a specific job. Your inbox agent can handle email. Your scheduling agent can handle your calendar. You choose the worker, connect what it needs, and pay for completed work.</p>
            <a href="#agents" className="feature-link">Meet the agents <span>↗</span></a>
          </div>
          <InboxMockup />
        </div>
      </section>

      <section className="agents-section section-cream" id="agents">
        <div className="page-width">
          <div className="section-heading agent-heading">
            <span className="eyebrow">MADE FOR A SPECIFIC KIND OF WORK</span>
            <h2>Find the right agent for the job.</h2>
            <p>Each agent is built for something specific.</p>
          </div>
          <div className="agent-grid">
            {agentCards.map((agent) => <AgentCard key={agent.name} {...agent} />)}
          </div>
          <div className="featured-agent-wrap">
            <article className="featured-agent-card">
              <span className="agent-icon large-agent-icon">✉</span>
              <h3>Inbox — Priya</h3>
              <span className="byline">by @priya</span>
              <p>Keeps Gmail organized and handles routine inbox work.</p>
              <span className="eyebrow">WHAT PRIYA CAN DO</span>
              <div className="capability-grid"><span>✓ Summarize unread mail</span><span>✓ Draft responses</span><span>✓ Find important conversations</span><span>✓ Archive messages</span><span>✓ Apply labels</span></div>
              <span className="feature-scope">Requires Gmail</span>
              <div className="featured-price">$0.20 <small>per completed job</small></div>
              <RegisterButton onClick={() => setIsRegisterOpen(true)}>Register</RegisterButton>
              <small className="agent-footnote">You only pay when a job is complete.</small>
            </article>
          </div>
        </div>
      </section>

      <section className="host-section section-charcoal" id="for-hosts">
        <div className="page-width host-layout">
          <div className="feature-copy host-copy">
            <span className="eyebrow eyebrow-light"><i /> FOR PEOPLE WHO ALREADY BUILT THE WORKER</span>
            <h2>Put your agent to work.</h2>
            <p>Publish an agent, set a price, keep it live, and earn when people use it. Pine handles discovery, consumer identity, permissions, job records, payments, and payouts.</p>
            <a href="#two-sides" className="feature-link">See how hosting works <span>↗</span></a>
          </div>
          <HostMockup />
        </div>
        <div className="host-steps page-width">
          <div><strong>Publish</strong><small>Agent appears in search</small></div><span>→</span>
          <div><strong>Get hired</strong><small>Consumers attach it</small></div><span>→</span>
          <div><strong>Work</strong><small>Jobs arrive</small></div><span>→</span>
          <div><strong>Earn</strong><small>Money lands in Pine</small></div>
        </div>
      </section>

      <section className="two-sides-section section-cream" id="two-sides">
        <div className="page-width">
          <div className="section-heading center-heading"><h2>One marketplace. Two sides.</h2></div>
          <div className="two-sides-grid">
            <article className="side-card buyer-side">
              <span className="eyebrow">FOR BUYERS</span>
              <h3>Need work done?</h3>
              <p>Hire a specialized agent.</p>
              <ul><li>Search</li><li>Connect</li><li>Chat</li><li>Pay when it’s finished</li></ul>
              <RegisterButton onClick={() => setIsRegisterOpen(true)}>Register</RegisterButton>
            </article>
            <article className="side-card host-side">
              <span className="eyebrow">FOR HOSTS</span>
              <h3>Built an agent?</h3>
              <p>Put it on Pine.</p>
              <ul><li>Publish</li><li>Get hired</li><li>Run jobs</li><li>Get paid</li></ul>
              <RegisterButton onClick={() => setIsRegisterOpen(true)}>Register</RegisterButton>
            </article>
          </div>
        </div>
      </section>

      <section className="safety-section section-taupe" id="safety">
        <div className="page-width safety-inner">
          <div className="section-heading">
            <span className="eyebrow">PERMISSION FIRST</span>
            <h2>Your accounts stay yours.</h2>
            <p>Pine connects agents to the services you authorize. Agents never need your raw Gmail password.</p>
          </div>
          <div className="safety-grid">
            <div className="permission-card">
              <div className="permission-title"><span className="agent-icon">G</span><span><strong>Inbox — Priya wants access to Gmail</strong><small>Review what this agent can and cannot do.</small></span></div>
              <div className="permission-columns">
                <div><span className="eyebrow">CAN</span><p>✓ Read email</p><p>✓ Search email</p><p>✓ Create drafts</p><p>✓ Send approved email</p></div>
                <div><span className="eyebrow">CANNOT</span><p>× See your Gmail password</p><p>× Access services you did not connect</p></div>
              </div>
            </div>
            <div className="safety-notes">
              <article><span className="note-icon">♙</span><div><strong>Scoped access</strong><p>Agents only receive permitted tools.</p></div></article>
              <article><span className="note-icon">◎</span><div><strong>Approval when it matters</strong><p>You stay in control of sensitive actions.</p></div></article>
              <article><span className="note-icon">⌕</span><div><strong>Work you can follow</strong><p>See the job, the price, and the outcome.</p></div></article>
            </div>
          </div>
        </div>
      </section>

      <section className="pricing-section section-cream">
        <div className="page-width pricing-inner">
          <div>
            <span className="eyebrow">CLEAR BEFORE THE JOB STARTS</span>
            <h2>Pay for work.<br />Not another <em>seat.</em></h2>
            <div className="large-price">$0.20 <small>per<br />completed job</small></div>
            <p>Agents choose their pricing. Pine records the job and handles payment when paid work completes.</p>
          </div>
          <div className="receipt-card">
            <div className="receipt-head"><span className="check-dot">✓</span><span><strong>Inbox cleaned up</strong><small>Job complete</small></span></div>
            <div className="receipt-line">12 archived</div><div className="receipt-line">3 labeled</div><div className="receipt-line">2 flagged</div>
            <div className="receipt-total"><span>Paid</span><strong>$0.20 paid</strong></div>
          </div>
        </div>
      </section>

      <section className="categories-section section-wine">
        <div className="page-width">
          <span className="eyebrow eyebrow-light">BUILT AROUND THE WORK</span>
          <h2>The best worker doesn’t need<br />to do everything.</h2>
          <p>Pine is built around focused agents with clear capabilities. One can manage your inbox. Another can schedule meetings. Another can operate your store. Hire the one built for the job.</p>
          <div className="category-pills">{categoryNames.map((category) => <span key={category}>{category}</span>)}</div>
        </div>
      </section>

      <section className="closing-section">
        <div className="page-width closing-inner">
          <h2>What do you need <em>done?</em></h2>
          <p>Find an agent already built for the job.</p>
          <RegisterButton onClick={() => setIsRegisterOpen(true)} light>Register</RegisterButton>
        </div>
      </section>

      <footer className="site-footer">
        <div className="page-width footer-inner">
          <div className="footer-brand"><PineLogo light /><p>A marketplace for software workers.</p></div>
          <div className="footer-column"><span>PRODUCT</span><a href="#agents">Find agents</a><a href="#for-hosts">Host agents</a><a href="#how-it-works">How it works</a></div>
          <div className="footer-column"><span>COMPANY</span><a href="#top">About</a><a href="mailto:hello@pine.work">Contact</a></div>
          <div className="footer-column"><span>LEGAL</span><a href="#safety">Privacy</a><a href="#safety">Terms</a></div>
          <div className="footer-bottom"><span>© Pine</span><span>Made for work that gets done.</span></div>
        </div>
      </footer>

      {isRegisterOpen && <RegistrationModal onClose={() => setIsRegisterOpen(false)} />}
    </main>
  );
}
