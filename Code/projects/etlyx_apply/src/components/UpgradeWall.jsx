const css = `
  .upgrade-wall {
    background: #111318;
    border: 1px solid #c8a96e40;
    border-radius: 14px;
    padding: 36px 32px;
    text-align: center;
    margin: 40px auto;
    max-width: 480px;
  }
  .uw-icon { font-size: 36px; margin-bottom: 14px; }
  .uw-title { font-family: 'Instrument Serif', serif; font-size: 22px; color: #e8e4dc; margin-bottom: 8px; }
  .uw-desc { color: #6b7280; font-size: 13.5px; line-height: 1.6; margin-bottom: 24px; }
  .uw-btn {
    background: #c8a96e;
    color: #0d0f14;
    border: none;
    border-radius: 8px;
    padding: 12px 28px;
    font-family: 'DM Sans', sans-serif;
    font-size: 13.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
  }
  .uw-btn:hover { background: #d4b87e; transform: translateY(-1px); }
  .uw-features { display: flex; flex-direction: column; gap: 6px; margin-bottom: 24px; text-align: left; }
  .uw-feat { display: flex; align-items: center; gap: 10px; font-size: 13px; color: #9ca3af; }
  .uw-feat span:first-child { color: #c8a96e; }
`;

const LOCKED_FEATURES = [
  "All 4 search agents (LinkedIn, Indeed, hiring.cafe, Banks)",
  "Evaluator Agent — 1–5 match scoring with full breakdown",
  "Unlimited searches",
  "Unlimited cover letter generation",
];

export default function UpgradeWall({ reason, onUpgrade }) {
  const messages = {
    searches: { icon: "🔍", title: "You've used your 5 free searches", desc: "Upgrade to Pro for unlimited searches across all 4 job sources." },
    evaluator: { icon: "🧠", title: "Evaluator Agent is a Pro feature", desc: "Upgrade to see how well each job matches your profile — scored across 5 criteria." },
    cover: { icon: "✉️", title: "Cover letters are a Pro feature", desc: "Upgrade to generate unlimited tailored cover letters for any job." },
    sources: { icon: "🏦", title: "Multiple sources are a Pro feature", desc: "Upgrade to search LinkedIn, Indeed, hiring.cafe, and Canadian investment banks simultaneously." },
  };

  const m = messages[reason] || messages.searches;

  return (
    <>
      <style>{css}</style>
      <div className="upgrade-wall">
        <div className="uw-icon">{m.icon}</div>
        <div className="uw-title">{m.title}</div>
        <div className="uw-desc">{m.desc}</div>
        <div className="uw-features">
          {LOCKED_FEATURES.map((f, i) => (
            <div className="uw-feat" key={i}>
              <span>✓</span><span>{f}</span>
            </div>
          ))}
        </div>
        <button className="uw-btn" onClick={onUpgrade}>Upgrade to Pro — $15/month</button>
      </div>
    </>
  );
}
