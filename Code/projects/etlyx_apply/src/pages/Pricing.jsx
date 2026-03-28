import { useState } from "react";
import { useAuth } from "../lib/auth.jsx";
import { supabase } from "../lib/supabase.js";

const css = `
  .pricing-wrap { min-height:100vh; background:#0d0f14; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:48px 24px; font-family:'DM Sans',sans-serif; }
  .pricing-logo { font-family:'Instrument Serif',serif; font-size:22px; color:#e8e4dc; margin-bottom:8px; }
  .pricing-logo span { color:#c8a96e; }
  .pricing-title { font-family:'Instrument Serif',serif; font-size:36px; color:#e8e4dc; text-align:center; margin-bottom:8px; }
  .pricing-sub { color:#6b7280; font-size:14px; text-align:center; margin-bottom:48px; max-width:480px; line-height:1.6; }
  .pricing-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; max-width:700px; width:100%; }
  .plan-card { background:#111318; border:1px solid #1e2330; border-radius:16px; padding:32px 28px; display:flex; flex-direction:column; position:relative; }
  .plan-card.featured { border-color:#c8a96e; }
  .plan-badge { position:absolute; top:-12px; left:50%; transform:translateX(-50%); background:#c8a96e; color:#0d0f14; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1px; padding:4px 14px; border-radius:20px; white-space:nowrap; }
  .plan-name { font-size:13px; font-weight:600; text-transform:uppercase; letter-spacing:1px; color:#6b7280; margin-bottom:12px; }
  .plan-price { font-family:'Instrument Serif',serif; font-size:48px; color:#e8e4dc; line-height:1; margin-bottom:4px; }
  .plan-price span { font-size:18px; color:#6b7280; font-family:'DM Sans',sans-serif; }
  .plan-desc { color:#6b7280; font-size:13px; margin-bottom:24px; }
  .plan-features { list-style:none; padding:0; margin:0 0 28px 0; flex:1; }
  .plan-features li { display:flex; align-items:flex-start; gap:10px; color:#9ca3af; font-size:13.5px; padding:7px 0; border-bottom:1px solid #1e2330; }
  .plan-features li:last-child { border-bottom:none; }
  .plan-features li.on { color:#e8e4dc; }
  .plan-features li.off { color:#4b5563; }
  .feat-icon { flex-shrink:0; font-size:13px; margin-top:2px; }
  .plan-btn { border:none; border-radius:8px; padding:12px; font-family:'DM Sans',sans-serif; font-size:13.5px; font-weight:600; cursor:pointer; transition:all 0.15s; width:100%; display:flex; align-items:center; justify-content:center; gap:7px; }
  .plan-btn.free-btn { background:transparent; color:#9ca3af; border:1px solid #1e2330; }
  .plan-btn.free-btn:hover { background:#161922; color:#e8e4dc; }
  .plan-btn.pro-btn { background:#c8a96e; color:#0d0f14; }
  .plan-btn.pro-btn:hover { background:#d4b87e; }
  .plan-btn:disabled { opacity:0.5; cursor:not-allowed; }
  .pricing-footer { margin-top:32px; color:#4b5563; font-size:12px; text-align:center; line-height:1.8; }
  .pricing-back { margin-top:20px; background:none; border:none; color:#4b5563; font-family:'DM Sans',sans-serif; font-size:13px; cursor:pointer; text-decoration:underline; }
  .pricing-back:hover { color:#9ca3af; }
  .stripe-error { background:#1a0a0a; border:1px solid #3d1515; border-radius:8px; color:#f87171; font-size:13px; padding:10px 14px; margin-top:12px; text-align:center; }
  .spinner { display:inline-block; width:13px; height:13px; border:2px solid rgba(13,15,20,0.3); border-top-color:#0d0f14; border-radius:50%; animation:spin 0.7s linear infinite; }
  @keyframes spin { to { transform:rotate(360deg); } }
  @media(max-width:600px){ .pricing-grid { grid-template-columns:1fr; } }
`;

const FREE_FEATURES = [
  { text: "Upload & parse resume",          on: true },
  { text: "Match Analysis — score 1–10",    on: true },
  { text: "Skills gap breakdown",           on: true },
  { text: "Application tracker",            on: true },
  { text: "Resume Tweaks",                  on: false },
  { text: "Interview Prep",                 on: false },
  { text: "Cover Letter generation",        on: false },
];

const PRO_FEATURES = [
  { text: "Everything in Free",             on: true },
  { text: "Resume Tweaks for each job",     on: true },
  { text: "Interview Prep — questions & answers tailored to you", on: true },
  { text: "Cover Letter — auto-written, any tone", on: true },
  { text: "Unlimited analyses",             on: true },
  { text: "Priority support",               on: true },
];

export default function PricingPage({ onContinueFree }) {
  const { isPro } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  const handleUpgrade = async () => {
    setLoading(true); setError("");
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const res  = await fetch("/api/stripe/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${session?.access_token}` },
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error.message);
      window.location.href = data.url;
    } catch (err) {
      setError(err.message || "Could not start checkout. Please try again.");
      setLoading(false);
    }
  };

  return (
    <>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap'); ${css}`}</style>
      <div className="pricing-wrap">
        <div className="pricing-logo">apply by <span>etlyx</span></div>
        <div className="pricing-title">Simple, honest pricing</div>
        <div className="pricing-sub">Paste any job description and know in seconds if you should apply — plus everything you need to actually land it.</div>

        <div className="pricing-grid">
          {/* Free */}
          <div className="plan-card">
            <div className="plan-name">Free</div>
            <div className="plan-price">$0 <span>/month</span></div>
            <div className="plan-desc">No credit card needed</div>
            <ul className="plan-features">
              {FREE_FEATURES.map((f, i) => (
                <li key={i} className={f.on ? "on" : "off"}>
                  <span className="feat-icon">{f.on ? "✓" : "🔒"}</span>
                  <span style={{ textDecoration: f.on ? "none" : "line-through" }}>{f.text}</span>
                </li>
              ))}
            </ul>
            <button className="plan-btn free-btn" onClick={onContinueFree}>
              {isPro ? "Your previous plan" : "Continue with Free"}
            </button>
          </div>

          {/* Pro */}
          <div className="plan-card featured">
            <div className="plan-badge">Most popular</div>
            <div className="plan-name">Pro</div>
            <div className="plan-price">$15 <span>/month</span></div>
            <div className="plan-desc">Everything you need to land the interview</div>
            <ul className="plan-features">
              {PRO_FEATURES.map((f, i) => (
                <li key={i} className="on">
                  <span className="feat-icon">✓</span>{f.text}
                </li>
              ))}
            </ul>
            <button className="plan-btn pro-btn" onClick={handleUpgrade} disabled={loading || isPro}>
              {isPro ? "✓ Current plan" : loading ? <><div className="spinner" />Redirecting to Stripe…</> : "Upgrade to Pro — $15/mo"}
            </button>
            {error && <div className="stripe-error">{error}</div>}
          </div>
        </div>

        <div className="pricing-footer">
          Cancel anytime · Billed monthly · Secure payments via Stripe<br />
          Questions? <a href="mailto:hello@etlyx.io" style={{ color: "#6b7280" }}>hello@etlyx.io</a>
        </div>
        <button className="pricing-back" onClick={onContinueFree}>← Back to app</button>
      </div>
    </>
  );
}
