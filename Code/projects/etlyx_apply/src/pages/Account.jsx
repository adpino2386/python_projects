import { useState } from "react";
import { useAuth } from "../lib/auth";
import { supabase } from "../lib/supabase";

const css = `
  .account-wrap {
    min-height: 100vh;
    background: #0d0f14;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'DM Sans', sans-serif;
    padding: 24px;
  }
  .account-card {
    background: #111318;
    border: 1px solid #1e2330;
    border-radius: 20px;
    padding: 40px;
    max-width: 480px;
    width: 100%;
  }
  .account-logo { font-family: 'Instrument Serif', serif; font-size: 20px; color: #e8e4dc; margin-bottom: 28px; }
  .account-logo span { color: #c8a96e; }
  .account-row { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid #1e2330; }
  .account-row:last-of-type { border-bottom: none; }
  .account-label { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: #6b7280; }
  .account-value { font-size: 13.5px; color: #e8e4dc; }
  .plan-pro { color: #c8a96e; font-weight: 600; }
  .plan-free { color: #6b7280; }
  .divider { border: none; border-top: 1px solid #1e2330; margin: 24px 0; }
  .acct-btn {
    width: 100%;
    border: none;
    border-radius: 8px;
    padding: 11px;
    font-family: 'DM Sans', sans-serif;
    font-size: 13.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
  }
  .acct-btn.primary { background: #c8a96e; color: #0d0f14; }
  .acct-btn.primary:hover { background: #d4b87e; }
  .acct-btn.ghost { background: transparent; color: #9ca3af; border: 1px solid #1e2330; }
  .acct-btn.ghost:hover { background: #161922; color: #e8e4dc; }
  .acct-btn.danger { background: transparent; color: #f87171; border: 1px solid #2a1515; }
  .acct-btn.danger:hover { background: #1a0a0a; }
  .acct-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .spinner { display: inline-block; width: 13px; height: 13px; border: 2px solid rgba(0,0,0,0.2); border-top-color: #0d0f14; border-radius: 50%; animation: spin 0.7s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
`;

export default function AccountPage({ onBack, onUpgrade }) {
  const { user, isPro, signOut, refreshProfile } = useAuth();
  const [loading, setLoading] = useState(null);

  const openPortal = async () => {
    setLoading("portal");
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const res  = await fetch("/api/stripe/portal", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${session?.access_token}` },
      });
      const data = await res.json();
      if (data.url) window.location.href = data.url;
      else alert("Could not open billing portal. Please try again.");
    } catch (err) {
      alert("Error: " + err.message);
    }
    setLoading(null);
  };

  const handleSignOut = async () => {
    await signOut();
  };

  return (
    <>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap'); ${css}`}</style>
      <div className="account-wrap">
        <div className="account-card">
          <div className="account-logo">etlyx <span>apply</span></div>

          <div className="account-row">
            <span className="account-label">Email</span>
            <span className="account-value">{user?.email}</span>
          </div>
          <div className="account-row">
            <span className="account-label">Plan</span>
            <span className={`account-value ${isPro ? "plan-pro" : "plan-free"}`}>
              {isPro ? "✓ Pro — $15/month" : "Free"}
            </span>
          </div>

          <hr className="divider" />

          {isPro ? (
            <>
              <button className="acct-btn ghost" onClick={openPortal} disabled={loading === "portal"}>
                {loading === "portal" ? <><div className="spinner"/>Opening…</> : "Manage subscription & billing"}
              </button>
              <button className="acct-btn danger" onClick={openPortal} disabled={loading === "portal"}>
                Cancel subscription
              </button>
              <div style={{ fontSize: 12, color: "#4b5563", textAlign: "center", marginTop: 4 }}>
                Cancellation takes effect at the end of your billing period
              </div>
            </>
          ) : (
            <button className="acct-btn primary" onClick={onUpgrade}>
              Upgrade to Pro — $15/month
            </button>
          )}

          <hr className="divider" />

          <button className="acct-btn ghost" onClick={onBack}>← Back to app</button>
          <button className="acct-btn danger" onClick={handleSignOut}>Sign out</button>
        </div>
      </div>
    </>
  );
}
