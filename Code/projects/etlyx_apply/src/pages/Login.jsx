import { useState } from "react";
import { supabase } from "../lib/supabase";

const css = `
  .auth-wrap {
    min-height: 100vh;
    background: #0d0f14;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    font-family: 'DM Sans', sans-serif;
  }
  .auth-card {
    background: #111318;
    border: 1px solid #1e2330;
    border-radius: 20px;
    padding: 48px 40px;
    width: 100%;
    max-width: 420px;
  }
  .auth-logo {
    font-family: 'Instrument Serif', serif;
    font-size: 26px;
    color: #e8e4dc;
    margin-bottom: 4px;
  }
  .auth-logo span { color: #c8a96e; }
  .auth-tagline {
    color: #6b7280;
    font-size: 13.5px;
    margin-bottom: 36px;
  }
  .auth-tabs {
    display: flex;
    gap: 0;
    background: #0d0f14;
    border: 1px solid #1e2330;
    border-radius: 10px;
    padding: 4px;
    margin-bottom: 28px;
  }
  .auth-tab {
    flex: 1;
    background: none;
    border: none;
    color: #6b7280;
    padding: 9px;
    border-radius: 7px;
    cursor: pointer;
    font-family: 'DM Sans', sans-serif;
    font-size: 13.5px;
    font-weight: 500;
    transition: all 0.15s;
  }
  .auth-tab.active { background: #1a1c26; color: #e8e4dc; }
  .auth-field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }
  .auth-label { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: #6b7280; }
  .auth-input {
    background: #0d0f14;
    border: 1px solid #1e2330;
    border-radius: 8px;
    color: #e8e4dc;
    padding: 11px 14px;
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    outline: none;
    transition: border-color 0.15s;
    width: 100%;
    box-sizing: border-box;
  }
  .auth-input:focus { border-color: #c8a96e; }
  .auth-btn {
    width: 100%;
    background: #c8a96e;
    color: #0d0f14;
    border: none;
    border-radius: 8px;
    padding: 12px;
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    margin-top: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }
  .auth-btn:hover { background: #d4b87e; }
  .auth-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .auth-error {
    background: #1a0a0a;
    border: 1px solid #3d1515;
    border-radius: 8px;
    color: #f87171;
    font-size: 13px;
    padding: 10px 14px;
    margin-bottom: 16px;
  }
  .auth-success {
    background: #0a1f17;
    border: 1px solid #1a4a30;
    border-radius: 8px;
    color: #34d399;
    font-size: 13px;
    padding: 10px 14px;
    margin-bottom: 16px;
  }
  .auth-divider { border: none; border-top: 1px solid #1e2330; margin: 24px 0; }
  .auth-google-btn {
    width: 100%;
    background: transparent;
    color: #9ca3af;
    border: 1px solid #1e2330;
    border-radius: 8px;
    padding: 11px;
    font-family: 'DM Sans', sans-serif;
    font-size: 13.5px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    box-sizing: border-box;
  }
  .auth-google-btn:hover { background: #161922; color: #e8e4dc; border-color: #2a3040; }
  .auth-fine-print { font-size: 12px; color: #4b5563; text-align: center; margin-top: 20px; line-height: 1.5; }
  .auth-fine-print a { color: #6b7280; text-decoration: underline; }
  .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(13,15,20,0.3); border-top-color: #0d0f14; border-radius: 50%; animation: spin 0.7s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
`;

export default function LoginPage() {
  const [tab, setTab]       = useState("login");
  const [email, setEmail]   = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const [success, setSuccess]   = useState("");

  const handle = async () => {
    setError(""); setSuccess(""); setLoading(true);
    try {
      if (tab === "login") {
        const { error: e } = await supabase.auth.signInWithPassword({ email, password });
        if (e) throw e;
      } else {
        const { error: e } = await supabase.auth.signUp({
          email, password,
          options: { emailRedirectTo: window.location.origin },
        });
        if (e) throw e;
        setSuccess("Check your email to confirm your account, then log in.");
        setLoading(false);
        return;
      }
    } catch (e) {
      setError(e.message || "Something went wrong.");
    }
    setLoading(false);
  };

  const googleLogin = async () => {
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: window.location.origin },
    });
  };

  return (
    <>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap'); ${css}`}</style>
      <div className="auth-wrap">
        <div className="auth-card">
          <div className="auth-logo">apply by <span>etlyx</span></div>
          <div className="auth-tagline">Paste any job description. Know your match in seconds.</div>

          <div className="auth-tabs">
            <button className={`auth-tab ${tab === "login" ? "active" : ""}`} onClick={() => { setTab("login"); setError(""); setSuccess(""); }}>Log in</button>
            <button className={`auth-tab ${tab === "signup" ? "active" : ""}`} onClick={() => { setTab("signup"); setError(""); setSuccess(""); }}>Sign up free</button>
          </div>

          {error   && <div className="auth-error">{error}</div>}
          {success && <div className="auth-success">{success}</div>}

          {!success && (
            <>
              <div className="auth-field">
                <label className="auth-label">Email</label>
                <input className="auth-input" type="email" value={email} onChange={e => setEmail(e.target.value)} onKeyDown={e => e.key === "Enter" && handle()} placeholder="you@email.com" />
              </div>
              <div className="auth-field">
                <label className="auth-label">Password</label>
                <input className="auth-input" type="password" value={password} onChange={e => setPassword(e.target.value)} onKeyDown={e => e.key === "Enter" && handle()} placeholder="••••••••" />
              </div>

              <button className="auth-btn" onClick={handle} disabled={loading || !email || !password}>
                {loading ? <><div className="spinner" /> {tab === "login" ? "Logging in…" : "Creating account…"}</> : tab === "login" ? "Log in" : "Create free account"}
              </button>

              <hr className="auth-divider" />

              <button className="auth-google-btn" onClick={googleLogin}>
                <svg width="16" height="16" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
                Continue with Google
              </button>
            </>
          )}

          <div className="auth-fine-print">
            {tab === "signup"
              ? "By signing up you agree to our terms. Free plan includes unlimited match analyses."
              : "Forgot your password? Contact hello@etlyx.com for a reset."}
          </div>
        </div>
      </div>
    </>
  );
}
