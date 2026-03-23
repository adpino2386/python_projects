import { useEffect, useState } from "react";
import { useAuth } from "../lib/auth";

const css = `
  .success-wrap {
    min-height: 100vh;
    background: #0d0f14;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'DM Sans', sans-serif;
    padding: 24px;
  }
  .success-card {
    background: #111318;
    border: 1px solid #1a4a30;
    border-radius: 20px;
    padding: 52px 44px;
    text-align: center;
    max-width: 440px;
    width: 100%;
  }
  .success-icon { font-size: 52px; margin-bottom: 20px; }
  .success-title {
    font-family: 'Instrument Serif', serif;
    font-size: 30px;
    color: #e8e4dc;
    margin-bottom: 10px;
  }
  .success-sub { color: #6b7280; font-size: 14px; line-height: 1.6; margin-bottom: 32px; }
  .success-features {
    background: #0a1f17;
    border: 1px solid #1a4a30;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 28px;
    text-align: left;
  }
  .sf-item { display: flex; align-items: center; gap: 10px; color: #34d399; font-size: 13px; padding: 5px 0; }
  .sf-item span:first-child { font-size: 14px; }
  .success-btn {
    background: #c8a96e;
    color: #0d0f14;
    border: none;
    border-radius: 8px;
    padding: 13px 32px;
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    width: 100%;
  }
  .success-btn:hover { background: #d4b87e; }
`;

const PRO_FEATURES = [
  "All 4 search agents now active",
  "Evaluator Agent scoring unlocked",
  "Unlimited searches every month",
  "Unlimited cover letter generation",
];

export default function SuccessPage({ onContinue }) {
  const { refreshProfile } = useAuth();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Refresh auth profile to pick up the new plan from the webhook
    // Poll a few times since webhook may take a second to process
    let tries = 0;
    const poll = async () => {
      await refreshProfile();
      tries++;
      if (tries < 5) setTimeout(poll, 1500);
      else setReady(true);
    };
    poll();
    const t = setTimeout(() => setReady(true), 8000);
    return () => clearTimeout(t);
  }, []);

  return (
    <>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap'); ${css}`}</style>
      <div className="success-wrap">
        <div className="success-card">
          <div className="success-icon">🎉</div>
          <div className="success-title">Welcome to Pro!</div>
          <div className="success-sub">
            Your payment was successful. Your account has been upgraded and all Pro features are now unlocked.
          </div>
          <div className="success-features">
            {PRO_FEATURES.map((f, i) => (
              <div className="sf-item" key={i}>
                <span>✓</span><span>{f}</span>
              </div>
            ))}
          </div>
          <button className="success-btn" onClick={onContinue}>
            Start searching →
          </button>
        </div>
      </div>
    </>
  );
}
