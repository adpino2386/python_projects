import { useState, useEffect, useRef } from "react";
import { useAuth } from "./lib/auth.jsx";
import { supabase } from "./lib/supabase.js";
import LoginPage from "./pages/Login.jsx";
import PricingPage from "./pages/Pricing.jsx";
import SuccessPage from "./pages/Success.jsx";
import AccountPage from "./pages/Account.jsx";
import LandingPage from "./pages/Landing.jsx";
import PrivacyPage from "./pages/Privacy.jsx";
import TermsPage from "./pages/Terms.jsx";

const css = `
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
*{box-sizing:border-box;margin:0;padding:0}html,body,#root{height:100%}body{background:#0d0f14}
.app{font-family:'DM Sans',sans-serif;background:#0d0f14;color:#e8e4dc;min-height:100vh;display:flex;flex-direction:column}
.topbar{display:flex;align-items:center;justify-content:space-between;padding:0 32px;height:60px;border-bottom:1px solid #1e2330;background:#0d0f14;position:sticky;top:0;z-index:100}
.logo{font-family:'Instrument Serif',serif;font-size:22px;color:#e8e4dc}.logo span{color:#c8a96e}
.nav{display:flex;gap:4px}
.nav-btn{background:none;border:none;color:#6b7280;padding:8px 16px;border-radius:8px;cursor:pointer;font-family:'DM Sans',sans-serif;font-size:13.5px;font-weight:500;transition:all 0.15s;display:flex;align-items:center;gap:6px}
.nav-btn:hover{color:#e8e4dc;background:#161922}.nav-btn.active{color:#c8a96e;background:#1a1710}
.content{flex:1;max-width:1000px;width:100%;margin:0 auto;padding:40px 32px}
.section-title{font-family:'Instrument Serif',serif;font-size:28px;color:#e8e4dc;margin-bottom:6px}
.section-sub{color:#6b7280;font-size:13.5px;margin-bottom:32px}
.card{background:#111318;border:1px solid #1e2330;border-radius:14px;padding:28px;margin-bottom:20px}
.card-title{font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:1px;color:#c8a96e;margin-bottom:18px}
.upload-zone{border:2px dashed #2a2f3e;border-radius:12px;padding:48px;text-align:center;cursor:pointer;transition:all 0.2s;background:#0d0f14}
.upload-zone:hover{border-color:#c8a96e;background:#1a1710}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.form-group{display:flex;flex-direction:column;gap:6px}.form-group.full{grid-column:1/-1}
label{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.8px;color:#6b7280}
input,textarea,select{background:#0d0f14;border:1px solid #1e2330;border-radius:8px;color:#e8e4dc;padding:10px 14px;font-family:'DM Sans',sans-serif;font-size:14px;outline:none;transition:border-color 0.15s}
input:focus,textarea:focus,select:focus{border-color:#c8a96e}textarea{resize:vertical;min-height:80px}select option{background:#111318}
.btn{background:#c8a96e;color:#0d0f14;border:none;border-radius:8px;padding:10px 20px;font-family:'DM Sans',sans-serif;font-size:13.5px;font-weight:600;cursor:pointer;transition:all 0.15s;display:inline-flex;align-items:center;gap:7px}
.btn:hover{background:#d4b87e;transform:translateY(-1px)}.btn:disabled{opacity:0.5;cursor:not-allowed;transform:none}
.btn-ghost{background:transparent;color:#9ca3af;border:1px solid #1e2330}
.btn-ghost:hover{background:#161922;color:#e8e4dc;transform:none}
.btn-danger{background:transparent;color:#ef4444;border:1px solid #2a1515}
.btn-danger:hover{background:#1a0a0a;transform:none}
.btn-sm{padding:6px 12px;font-size:12px}
.tag{display:inline-flex;align-items:center;gap:5px;background:#1a1c26;border:1px solid #2a2f3e;color:#9ca3af;padding:4px 10px;border-radius:20px;font-size:12px}
.tag-remove{cursor:pointer;color:#6b7280;font-size:14px;line-height:1}.tag-remove:hover{color:#ef4444}
.tags-wrap{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid rgba(200,169,110,0.2);border-top-color:#c8a96e;border-radius:50%;animation:spin 0.7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.loading-state{display:flex;align-items:center;gap:10px;color:#9ca3af;font-size:14px;padding:20px 0;justify-content:center}
.divider{border:none;border-top:1px solid #1e2330;margin:24px 0}
.empty{text-align:center;padding:60px 20px;color:#4b5563}
.empty-icon{font-size:40px;margin-bottom:12px}.empty-text{font-size:14px}
.toast{position:fixed;bottom:28px;right:28px;background:#1e2330;border:1px solid #2a3040;border-radius:10px;padding:12px 18px;color:#e8e4dc;font-size:13.5px;z-index:999;display:flex;align-items:center;gap:8px;animation:slideUp 0.2s ease}
@keyframes slideUp{from{transform:translateY(10px);opacity:0}to{transform:translateY(0);opacity:1}}
.status-dot{width:8px;height:8px;border-radius:50%;background:#34d399}
.modal-backdrop{position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:200;display:flex;align-items:center;justify-content:center;padding:20px}
.modal{background:#111318;border:1px solid #1e2330;border-radius:16px;padding:32px;width:100%;max-width:600px;max-height:85vh;overflow-y:auto}
.modal-title{font-family:'Instrument Serif',serif;font-size:22px;margin-bottom:6px}
.modal-sub{color:#6b7280;font-size:13px;margin-bottom:24px}
.modal-actions{display:flex;gap:10px;margin-top:24px;justify-content:flex-end}

/* Score ring */
.score-ring-wrap{display:flex;flex-direction:column;align-items:center;gap:6px}
.score-ring{width:96px;height:96px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-direction:column;border:3px solid}
.score-ring.s-high{border-color:#34d399;background:#0a1f17;color:#34d399}
.score-ring.s-good{border-color:#60a5fa;background:#0a1220;color:#60a5fa}
.score-ring.s-mid{border-color:#c8a96e;background:#1a1710;color:#c8a96e}
.score-ring.s-low{border-color:#f87171;background:#1a0a0a;color:#f87171}
.score-num{font-family:'Instrument Serif',serif;font-size:32px;font-weight:700;line-height:1}
.score-denom{font-size:11px;opacity:0.7}
.score-verdict{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.8px}

/* Skills */
.skill-pill{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:500;margin:2px}
.skill-have{background:#0a1f17;border:1px solid #34d39940;color:#34d399}
.skill-missing-high{background:#1a0a0a;border:1px solid #f8717140;color:#f87171}
.skill-missing-med{background:#1a1400;border:1px solid #f59e0b40;color:#f59e0b}
.skill-missing-low{background:#1a1c26;border:1px solid #4b556340;color:#6b7280}

/* Experience bars */
.exp-row{display:flex;align-items:center;gap:12px;margin-bottom:10px}
.exp-label{font-size:13px;color:#9ca3af;width:180px;flex-shrink:0}
.exp-bar-wrap{flex:1;height:6px;background:#1e2330;border-radius:3px;overflow:hidden}
.exp-bar{height:100%;border-radius:3px;transition:width 0.6s ease}
.eb-5{background:#34d399}.eb-4{background:#60a5fa}.eb-3{background:#c8a96e}.eb-2{background:#f59e0b}.eb-1{background:#f87171}
.exp-comment{font-size:12px;color:#4b5563;flex-shrink:0;max-width:220px}

/* Tweaks */
.tweak-card{background:#0d0f14;border:1px solid #1e2330;border-radius:10px;padding:16px;margin-bottom:12px}
.tweak-impact-high{border-left:3px solid #34d399}.tweak-impact-medium{border-left:3px solid #c8a96e}.tweak-impact-low{border-left:3px solid #4b5563}
.tweak-original{font-size:13px;color:#6b7280;line-height:1.5;margin-bottom:8px;text-decoration:line-through}
.tweak-improved{font-size:13px;color:#e8e4dc;line-height:1.5;margin-bottom:8px}
.tweak-reason{font-size:12px;color:#c8a96e;font-style:italic}

/* Interview */
.iq-card{background:#0d0f14;border:1px solid #1e2330;border-radius:10px;padding:16px;margin-bottom:12px}
.iq-type{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;padding:2px 8px;border-radius:20px;margin-bottom:8px;display:inline-block}
.iq-behavioral{background:#0a1220;color:#60a5fa}.iq-technical{background:#1a1710;color:#c8a96e}
.iq-situational{background:#0a1f17;color:#34d399}.iq-culture{background:#1a100a;color:#f59e0b}
.iq-question{font-size:14px;color:#e8e4dc;font-weight:500;margin-bottom:8px;line-height:1.4}
.iq-answer{font-size:13px;color:#9ca3af;line-height:1.6;margin-bottom:6px}
.iq-star{font-size:12px;color:#c8a96e}

/* Action buttons row */
.action-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:4px}
.action-btn{background:#0d0f14;border:1px solid #1e2330;border-radius:10px;padding:14px 16px;cursor:pointer;font-family:'DM Sans',sans-serif;transition:all 0.15s;display:flex;flex-direction:column;gap:4px;text-align:left}
.action-btn:hover:not(:disabled){border-color:#c8a96e;background:#1a1710}
.action-btn:disabled{opacity:0.4;cursor:not-allowed}
.action-btn-icon{font-size:20px}
.action-btn-label{font-size:13px;font-weight:600;color:#e8e4dc}
.action-btn-desc{font-size:11px;color:#6b7280}
.action-btn.active-tab{border-color:#c8a96e;background:#1a1710}

/* Resume switcher */
.resume-tab{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;border-radius:8px;cursor:pointer;font-family:'DM Sans',sans-serif;font-size:13px;font-weight:500;border:1px solid #1e2330;background:#0d0f14;color:#6b7280;transition:all 0.15s}
.resume-tab:hover{border-color:#2a3040;color:#e8e4dc}
.resume-tab.active{border-color:#c8a96e;background:#1a1710;color:#c8a96e}
.resume-tab-add{border-style:dashed;color:#4b5563}
.resume-tab-add:hover{border-color:#c8a96e;color:#c8a96e}

/* Match history stats */
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:0}
.stat-box{background:#0d0f14;border:1px solid #1e2330;border-radius:10px;padding:14px 16px;text-align:center}
.stat-num{font-family:'Instrument Serif',serif;font-size:28px;font-weight:700;line-height:1;margin-bottom:3px}
.stat-label{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:0.6px}
.gap-pill{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:20px;font-size:11px;font-weight:500;background:#1a0a0a;border:1px solid #f8717130;color:#f87171;margin:2px}
.strength-pill{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:20px;font-size:11px;font-weight:500;background:#0a1f17;border:1px solid #34d39930;color:#34d399;margin:2px}

/* Tweaked resume snapshot */
.snapshot-badge{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;padding:2px 7px;border-radius:20px;background:#0a1f17;border:1px solid #34d39930;color:#34d399}
.cover-letter-text{background:#0d0f14;border:1px solid #1e2330;border-radius:8px;padding:24px;color:#d1cdc7;font-size:14px;line-height:1.9;white-space:pre-wrap}

/* Tracker */
.tracker-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;align-items:start}
.tracker-col{background:#111318;border:1px solid #1e2330;border-radius:12px;padding:16px}
.col-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.col-title{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.8px}
.col-count{background:#1a1c26;color:#9ca3af;border-radius:20px;padding:2px 8px;font-size:11px}
.tracker-item{background:#0d0f14;border:1px solid #1e2330;border-radius:8px;padding:12px;margin-bottom:8px;cursor:pointer;transition:border-color 0.15s}
.tracker-item:hover{border-color:#2a3040}
.tracker-item-title{font-size:13px;color:#e8e4dc;font-weight:500;margin-bottom:3px}
.tracker-item-company{font-size:12px;color:#c8a96e}
.tracker-item-score{font-size:11px;margin-top:5px;font-weight:600}
.tracker-item-date{font-size:11px;color:#4b5563;margin-top:4px}
.s-saved{color:#60a5fa}.s-applied{color:#a78bfa}.s-interview{color:#34d399}.s-offer{color:#c8a96e}.s-rejected{color:#f87171}

::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:#2a2f3e;border-radius:3px}

/* ── Bottom nav for mobile ── */
.bottom-nav{display:none}

/* ── Mobile responsive ── */
@media(max-width:768px){
  /* Hide desktop top nav buttons, show bottom nav */
  .nav{display:none}
  .bottom-nav{
    display:flex;position:fixed;bottom:0;left:0;right:0;
    background:#0d0f14;border-top:1px solid #1e2330;
    padding:8px 0 env(safe-area-inset-bottom,8px);
    z-index:100;justify-content:space-around;align-items:center;
  }
  .bottom-nav-btn{
    display:flex;flex-direction:column;align-items:center;gap:3px;
    background:none;border:none;cursor:pointer;padding:6px 16px;
    font-family:'DM Sans',sans-serif;color:#6b7280;transition:color 0.15s;
    flex:1;
  }
  .bottom-nav-btn.active{color:#c8a96e}
  .bottom-nav-icon{font-size:20px;line-height:1}
  .bottom-nav-label{font-size:10px;font-weight:500;text-transform:uppercase;letter-spacing:0.5px}

  /* Topbar — compact on mobile */
  .topbar{padding:0 16px;height:52px}
  .logo{font-size:18px}

  /* Add padding at bottom so content doesn't hide behind bottom nav */
  .content{padding:20px 16px 90px;max-width:100%}

  /* Cards */
  .card{padding:18px;border-radius:10px}
  .section-title{font-size:22px}
  .section-sub{font-size:13px;margin-bottom:20px}

  /* Forms — single column */
  .form-grid{grid-template-columns:1fr}
  input,textarea,select{font-size:16px} /* prevents iOS zoom on focus */

  /* Upload zone — more compact */
  .upload-zone{padding:32px 20px}

  /* Resume tabs — wrap */
  .resume-tab{font-size:12px;padding:5px 10px}

  /* Stats — 2x2 grid on mobile */
  .stat-grid{grid-template-columns:1fr 1fr}
  .stat-num{font-size:22px}

  /* Match analysis — stack score and details vertically */
  .score-ring{width:72px;height:72px}
  .score-num{font-size:24px}

  /* Experience bars — hide comment on small screens */
  .exp-row{flex-wrap:wrap;gap:6px}
  .exp-label{width:100%;flex-shrink:unset}
  .exp-comment{font-size:11px;max-width:100%}

  /* Action grid — single column on small phones */
  .action-grid{grid-template-columns:1fr}
  .action-btn{padding:12px}
  .action-btn-desc{display:none} /* hide description to save space */

  /* Tracker — scrollable horizontal on mobile */
  .tracker-grid{
    grid-template-columns:repeat(5,220px);
    overflow-x:auto;padding-bottom:8px;
    scrollbar-width:thin;
  }

  /* Modal — full screen on mobile */
  .modal-backdrop{padding:0;align-items:flex-end}
  .modal{
    border-radius:16px 16px 0 0;max-width:100%;
    max-height:92vh;padding:24px 20px;
  }
  .modal-actions{flex-wrap:wrap}

  /* Toast — full width on mobile */
  .toast{left:16px;right:16px;bottom:80px;font-size:13px}

  /* Job match input area */
  textarea[rows="10"]{min-height:160px}

  /* Result tabs — scrollable */
  .result-tabs-scroll{overflow-x:auto;white-space:nowrap;margin:0 -20px;padding:0 20px}

  /* Cover letter */
  .cover-letter-text{padding:16px;font-size:13px}
}

@media(max-width:400px){
  .action-grid{grid-template-columns:1fr}
  .stat-grid{grid-template-columns:1fr 1fr}
  .content{padding:16px 12px 90px}
  .card{padding:14px}
}
`;

const TABS = [
  { id: "profile", label: "Profile",   icon: "👤" },
  { id: "match",   label: "Job Match", icon: "🎯" },
  { id: "tracker", label: "Tracker",   icon: "📋" },
];

const STATUS_COLS = [
  { id: "saved",     label: "Saved",     cls: "s-saved" },
  { id: "applied",   label: "Applied",   cls: "s-applied" },
  { id: "interview", label: "Interview", cls: "s-interview" },
  { id: "offer",     label: "Offer",     cls: "s-offer" },
  { id: "rejected",  label: "Rejected",  cls: "s-rejected" },
];

// ─── API helper ────────────────────────────────────────────────────────────────
async function authedPost(endpoint, body) {
  const { data: { session } } = await supabase.auth.getSession();
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}) },
    body: JSON.stringify(body),
  });
  const d = await res.json();
  if (!res.ok) throw Object.assign(new Error(d.error?.message || "Request failed"), { code: d.error?.message });
  return d;
}

async function parseResume(base64, mediaType) {
  const block = mediaType.startsWith("image/")
    ? { type: "image", source: { type: "base64", media_type: mediaType, data: base64 } }
    : { type: "document", source: { type: "base64", media_type: "application/pdf", data: base64 } };
  const d = await authedPost("/api/messages", {
    model: "claude-sonnet-4-20250514", max_tokens: 2000,
    system: `Extract resume data. Return ONLY a JSON object:
{"name":"","email":"","phone":"","location":"","title":"","summary":"","skills":[],"experience":[{"company":"","role":"","period":"","accomplishments":[]}]}
No markdown, raw JSON only.`,
    messages: [{ role: "user", content: [block, { type: "text", text: "Extract the full resume data as JSON." }] }],
  });
  const text = d.content.map(b => b.text || "").join("");
  return JSON.parse(text.replace(/```json|```/g, "").trim());
}

function scoreClass(s) {
  if (s >= 8) return "s-high"; if (s >= 6) return "s-good"; if (s >= 4) return "s-mid"; return "s-low";
}
function scoreColor(s) {
  if (s >= 8) return "#34d399"; if (s >= 6) return "#60a5fa"; if (s >= 4) return "#c8a96e"; return "#f87171";
}

function Toast({ msg, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 3500); return () => clearTimeout(t); }, []);
  return <div className="toast"><div className="status-dot" />{msg}</div>;
}

// ─── Match History helpers ─────────────────────────────────────────────────────
function computeMatchHistory(applications) {
  const scored = applications.filter(a => a.matchScore);
  if (!scored.length) return null;
  const avg = Math.round(scored.reduce((s, a) => s + a.matchScore, 0) / scored.length * 10) / 10;
  // Count missing skills across all analyses
  const gapCounts = {};
  const strengthCounts = {};
  scored.forEach(a => {
    (a.matchData?.skillsMatch || []).filter(s => !s.have && s.importance === "high").forEach(s => { gapCounts[s.skill] = (gapCounts[s.skill] || 0) + 1; });
    (a.matchData?.topStrengths || []).forEach(s => { strengthCounts[s] = (strengthCounts[s] || 0) + 1; });
  });
  const topGaps      = Object.entries(gapCounts).sort((a,b)=>b[1]-a[1]).slice(0,6).map(([s])=>s);
  const topStrengths = Object.entries(strengthCounts).sort((a,b)=>b[1]-a[1]).slice(0,4).map(([s])=>s);
  const shouldApply  = scored.filter(a => a.matchData?.shouldApply).length;
  return { avg, total: scored.length, shouldApply, topGaps, topStrengths };
}

// ─── Profile Tab ───────────────────────────────────────────────────────────────
function ProfileTab({ profile, setProfile, resumes, setResumes, activeResumeIdx, setActiveResumeIdx, applications, toast }) {
  const fileRef = useRef();
  const [parsing, setParsing]   = useState(false);
  const [newSkill, setNewSkill] = useState("");
  const [renamingIdx, setRenamingIdx] = useState(null);
  const [renameVal, setRenameVal]     = useState("");
  const set = k => e => setProfile(p => ({ ...p, [k]: e.target.value }));

  const handleFile = async file => {
    if (!file) return;
    setParsing(true);
    try {
      const base64 = await new Promise((res, rej) => { const r = new FileReader(); r.onload = () => res(r.result.split(",")[1]); r.onerror = rej; r.readAsDataURL(file); });
      const parsed = await parseResume(base64, file.type);
      setProfile(p => ({ ...p, name: parsed.name||p.name, email: parsed.email||p.email, phone: parsed.phone||p.phone, location: parsed.location||p.location, title: parsed.title||p.title, summary: parsed.summary||p.summary, skills: parsed.skills?.length ? parsed.skills : p.skills, experience: parsed.experience?.length ? parsed.experience : p.experience, resumeFileName: file.name }));
      toast("✅ Resume parsed successfully!");
    } catch (e) { console.error(e); toast("⚠️ Could not parse resume — fill in manually."); }
    setParsing(false);
  };

  const addResume = () => {
    const newId = `r-${Date.now()}`;
    setResumes(rs => [...rs, { id: newId, name: `Resume ${rs.length + 1}`, skills: [], experience: [] }]);
    setActiveResumeIdx(resumes.length);
  };

  const deleteResume = (idx) => {
    if (resumes.length <= 1) { toast("You need at least one resume"); return; }
    setResumes(rs => rs.filter((_, i) => i !== idx));
    setActiveResumeIdx(0);
  };

  const addSkill = () => { const s = newSkill.trim(); if (s && !(profile.skills||[]).includes(s)) { setProfile(p => ({ ...p, skills: [...(p.skills||[]), s] })); setNewSkill(""); } };

  const history = computeMatchHistory(applications);

  return (
    <div>
      <div className="section-title">Your Profile</div>
      <div className="section-sub">Manage your resume versions — switch between them when analyzing different types of roles</div>

      {/* Resume switcher */}
      <div className="card">
        <div className="card-title">Resume Versions</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          {resumes.map((r, i) => (
            <div key={r.id} style={{ display: "flex", alignItems: "center", gap: 4 }}>
              {renamingIdx === i ? (
                <input
                  autoFocus
                  value={renameVal}
                  onChange={e => setRenameVal(e.target.value)}
                  onBlur={() => { setResumes(rs => rs.map((x, j) => j===i ? {...x, name: renameVal||x.name} : x)); setRenamingIdx(null); }}
                  onKeyDown={e => { if (e.key==="Enter"||e.key==="Escape") { setResumes(rs => rs.map((x, j) => j===i ? {...x, name: renameVal||x.name} : x)); setRenamingIdx(null); } }}
                  style={{ width: 140, padding: "4px 8px", fontSize: 13 }}
                />
              ) : (
                <button
                  className={`resume-tab${i===activeResumeIdx?" active":""}`}
                  onClick={() => setActiveResumeIdx(i)}
                  onDoubleClick={() => { setRenamingIdx(i); setRenameVal(r.name); }}
                  title="Click to switch · Double-click to rename"
                >
                  📄 {r.name}
                  {r.resumeFileName && <span style={{ fontSize: 10, color: "#4b5563" }}>· {r.resumeFileName}</span>}
                </button>
              )}
              {i === activeResumeIdx && resumes.length > 1 && (
                <button onClick={() => deleteResume(i)} style={{ background: "none", border: "none", color: "#4b5563", cursor: "pointer", fontSize: 14, padding: "0 2px" }} title="Delete this resume">×</button>
              )}
            </div>
          ))}
          {resumes.length < 4 && (
            <button className="resume-tab resume-tab-add" onClick={addResume}>+ Add resume version</button>
          )}
        </div>
        <div style={{ fontSize: 11, color: "#4b5563", marginTop: 10 }}>Double-click a tab to rename it · Up to 4 versions · Active version is used for all job analyses</div>
      </div>

      {/* Upload */}
      {!profile.resumeFileName ? (
        <div className="upload-zone" onClick={() => fileRef.current.click()} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); handleFile(e.dataTransfer.files[0]); }}>
          <input ref={fileRef} type="file" accept=".pdf,.png,.jpg,.jpeg" style={{ display: "none" }} onChange={e => handleFile(e.target.files[0])} />
          {parsing ? <div className="loading-state"><div className="spinner" />Extracting your resume…</div>
            : <><div style={{ fontSize: 40, marginBottom: 12 }}>📄</div><div style={{ color: "#9ca3af", fontSize: 14 }}><strong style={{ color: "#c8a96e" }}>Click or drag</strong> your resume here</div><div style={{ color: "#6b7280", fontSize: 12, marginTop: 4 }}>PDF or image accepted</div></>}
        </div>
      ) : (
        <div className="card" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: 24 }}>📄</span>
            <div><div style={{ fontSize: 14, color: "#e8e4dc" }}>{profile.resumeFileName}</div><div style={{ fontSize: 12, color: "#6b7280" }}>{(profile.skills||[]).length} skills · {(profile.experience||[]).length} positions extracted</div></div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => fileRef.current.click()}>Replace</button>
          <input ref={fileRef} type="file" accept=".pdf,.png,.jpg,.jpeg" style={{ display: "none" }} onChange={e => handleFile(e.target.files[0])} />
        </div>
      )}

      {/* Match History Dashboard */}
      {history && (
        <div className="card">
          <div className="card-title">Match History</div>
          <div className="stat-grid">
            <div className="stat-box">
              <div className="stat-num" style={{ color: scoreColor(history.avg) }}>{history.avg}</div>
              <div className="stat-label">Avg Match Score</div>
            </div>
            <div className="stat-box">
              <div className="stat-num" style={{ color: "#60a5fa" }}>{history.total}</div>
              <div className="stat-label">Jobs Analyzed</div>
            </div>
            <div className="stat-box">
              <div className="stat-num" style={{ color: "#34d399" }}>{history.shouldApply}</div>
              <div className="stat-label">Should Apply</div>
            </div>
            <div className="stat-box">
              <div className="stat-num" style={{ color: "#c8a96e" }}>{Math.round(history.shouldApply/history.total*100)}%</div>
              <div className="stat-label">Apply Rate</div>
            </div>
          </div>
          {history.topGaps.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: 8 }}>Most Common Skill Gaps — invest here</div>
              <div>{history.topGaps.map((g, i) => <span key={i} className="gap-pill">✗ {g}</span>)}</div>
            </div>
          )}
          {history.topStrengths.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: 8 }}>Your Consistent Strengths</div>
              <div>{history.topStrengths.map((s, i) => <span key={i} className="strength-pill">✓ {s}</span>)}</div>
            </div>
          )}
        </div>
      )}

      <div className="card">
        <div className="card-title">Basic Info</div>
        <div className="form-grid">
          <div className="form-group"><label>Full Name</label><input value={profile.name||""} onChange={set("name")} placeholder="Angel Pino" /></div>
          <div className="form-group"><label>Current Title</label><input value={profile.title||""} onChange={set("title")} placeholder="Senior Data Analyst" /></div>
          <div className="form-group"><label>Email</label><input value={profile.email||""} onChange={set("email")} placeholder="you@email.com" /></div>
          <div className="form-group"><label>Phone</label><input value={profile.phone||""} onChange={set("phone")} placeholder="+1 514 555 0100" /></div>
          <div className="form-group"><label>Location</label><input value={profile.location||""} onChange={set("location")} placeholder="Montreal, QC" /></div>
          <div className="form-group"><label>LinkedIn</label><input value={profile.linkedin||""} onChange={set("linkedin")} placeholder="linkedin.com/in/angel-pino" /></div>
          <div className="form-group full"><label>Professional Summary</label><textarea rows={4} value={profile.summary||""} onChange={set("summary")} placeholder="Used in cover letters and match analysis…" /></div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Skills</div>
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <input value={newSkill} onChange={e => setNewSkill(e.target.value)} onKeyDown={e => e.key === "Enter" && addSkill()} placeholder="Add a skill and press Enter…" style={{ flex: 1 }} />
          <button className="btn" onClick={addSkill}>Add</button>
        </div>
        <div className="tags-wrap">
          {(profile.skills||[]).map(sk => <span className="tag" key={sk}>{sk}<span className="tag-remove" onClick={() => setProfile(p => ({ ...p, skills: p.skills.filter(s => s !== sk) }))}>×</span></span>)}
          {!(profile.skills||[]).length && <span style={{ color: "#4b5563", fontSize: 13 }}>No skills yet</span>}
        </div>
      </div>

      {(profile.experience||[]).length > 0 && (
        <div className="card">
          <div className="card-title">Experience & Accomplishments</div>
          {(profile.experience||[]).map((exp, ei) => (
            <div key={ei} style={{ marginBottom: 20, paddingBottom: 20, borderBottom: ei < profile.experience.length-1 ? "1px solid #1e2330" : "none" }}>
              <div style={{ marginBottom: 8 }}><div style={{ fontSize: 14, color: "#e8e4dc", fontWeight: 600 }}>{exp.role}</div><div style={{ fontSize: 13, color: "#c8a96e" }}>{exp.company}{exp.period && <span style={{ color: "#4b5563", fontWeight: 400 }}> · {exp.period}</span>}</div></div>
              {(exp.accomplishments||[]).map((acc, ai) => (
                <div key={ai} style={{ display: "flex", gap: 8, marginBottom: 6, alignItems: "flex-start" }}>
                  <span style={{ color: "#c8a96e", fontSize: 12, marginTop: 3, flexShrink: 0 }}>•</span>
                  <textarea rows={2} value={acc} onChange={e => { const u=[...profile.experience]; u[ei]={...u[ei],accomplishments:u[ei].accomplishments.map((a,i)=>i===ai?e.target.value:a)}; setProfile(p=>({...p,experience:u})); }} style={{ flex: 1, fontSize: 13, lineHeight: 1.5, minHeight: "auto" }} />
                  <button onClick={() => { const u=[...profile.experience]; u[ei]={...u[ei],accomplishments:u[ei].accomplishments.filter((_,i)=>i!==ai)}; setProfile(p=>({...p,experience:u})); }} style={{ background: "none", border: "none", color: "#4b5563", cursor: "pointer", fontSize: 16, flexShrink: 0 }}>×</button>
                </div>
              ))}
              <button onClick={() => { const u=[...profile.experience]; u[ei]={...u[ei],accomplishments:[...(u[ei].accomplishments||[]),""] }; setProfile(p=>({...p,experience:u})); }} className="btn btn-ghost btn-sm" style={{ marginTop: 4, fontSize: 11 }}>+ Add bullet</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Job Match Tab ─────────────────────────────────────────────────────────────
function JobMatchTab({ profile, resumeName, applications, setApplications, toast, isPro, onUpgrade, persisted, setPersisted, saveApplication, analysesUsed, setAnalysesUsed }) {
  const { company="", jobTitle="", jd="", tone="professional", matchData=null, tweaks=null, interviewData=null, coverLetter="", activeResultTab="match" } = persisted || {};

  const set = k => v => setPersisted(p => ({ ...p, [k]: v }));

  const [loading, setLoading]       = useState(false);
  const [activeStep, setActiveStep] = useState(null);

  const profileReady  = !!(profile.title || profile.skills?.length || profile.summary);
  const canAnalyze    = profileReady && company && jd.trim().length > 50;
  const analysesLeft  = isPro ? null : Math.max(0, 5 - (analysesUsed || 0));

  const runMatch = async () => {
    if (!canAnalyze || loading) return;
    setLoading(true); setActiveStep("matching");
    setPersisted(p => ({ ...p, matchData: null, tweaks: null, interviewData: null, coverLetter: "", activeResultTab: "match" }));
    try {
      const data = await authedPost("/api/match", { profile, jobDescription: jd, company, jobTitle });
      setPersisted(p => ({ ...p, matchData: data }));
      if (!isPro) setAnalysesUsed(n => (n || 0) + 1);
    } catch (e) {
      if (e.code === "analyses_exhausted") {
        onUpgrade();
        toast("You've used all 5 free analyses this month — upgrade to Pro for unlimited.");
      } else {
        toast("⚠️ Analysis failed. Try again.");
      }
    }
    setLoading(false); setActiveStep(null);
  };

  const runTweaks = async () => {
    if (!isPro) { onUpgrade(); return; }
    setLoading(true); setActiveStep("tweaks");
    try {
      const data = await authedPost("/api/tweaks", { profile, jobDescription: jd, company, jobTitle });
      setPersisted(p => ({ ...p, tweaks: data, activeResultTab: "tweaks" }));
    } catch (e) { toast("⚠️ Resume tweaks failed. Try again."); }
    setLoading(false); setActiveStep(null);
  };

  const runInterview = async () => {
    if (!isPro) { onUpgrade(); return; }
    setLoading(true); setActiveStep("interview");
    try {
      const data = await authedPost("/api/interview", { profile, jobDescription: jd, company, jobTitle, matchData });
      setPersisted(p => ({ ...p, interviewData: data, activeResultTab: "interview" }));
    } catch (e) { toast("⚠️ Interview prep failed. Try again."); }
    setLoading(false); setActiveStep(null);
  };

  const runCover = async () => {
    if (!isPro) { onUpgrade(); return; }
    setLoading(true); setActiveStep("cover");
    try {
      const data = await authedPost("/api/cover", { profile, jobDescription: jd, company, jobTitle, tone, matchData });
      setPersisted(p => ({ ...p, coverLetter: data.letter, activeResultTab: "cover" }));
    } catch (e) { toast("⚠️ Cover letter failed. Try again."); }
    setLoading(false); setActiveStep(null);
  };

  const saveToTracker = async () => {
    if (!matchData) return;
    if (applications.find(a => a.jobTitle === (persisted.jobTitle||"") && a.company === (persisted.company||""))) { toast("Already in tracker"); return; }

    // Build tweaked resume snapshot — apply suggested tweaks to original bullets
    let tweakedResume = null;
    if (persisted.tweaks?.length) {
      const tweakMap = {};
      persisted.tweaks.forEach(t => { tweakMap[t.original] = t.improved; });
      tweakedResume = {
        resumeName: resumeName || "My Resume",
        experience: (profile.experience || []).map(exp => ({
          ...exp,
          accomplishments: (exp.accomplishments || []).map(a => tweakMap[a] || a),
        })),
        appliedTweaks: persisted.tweaks.length,
        generatedAt: new Date().toISOString(),
      };
    }

    const app = {
      id:            `m-${Date.now()}`,
      jobTitle:      persisted.jobTitle      || "",
      company:       persisted.company       || "",
      matchScore:    persisted.matchData?.overallScore,
      verdict:       persisted.matchData?.verdict,
      status:        "saved",
      added:         new Date().toLocaleDateString("en-CA"),
      jd:            persisted.jd            || "",
      matchData:     persisted.matchData     || null,
      tweaks:        persisted.tweaks        || null,
      tweakedResume: tweakedResume,
      interviewData: persisted.interviewData || null,
      coverLetter:   persisted.coverLetter   || "",
      resumeName:    resumeName              || "My Resume",
    };
    const ok = await saveApplication(app);
    if (ok) {
      setApplications(a => [app, ...a]);
      toast("💾 Saved to tracker!");
    }
  };

  return (
    <div>
      <div className="section-title">Job Match Analysis</div>
      <div className="section-sub">Paste a job description — get match score, resume tweaks, interview prep, and cover letter</div>

      {!profileReady && (
        <div style={{ background: "#1a1710", border: "1px solid #c8a96e30", borderRadius: 10, padding: "12px 16px", marginBottom: 20, fontSize: 13, color: "#c8a96e" }}>
          ⚠️ Upload your resume in Profile first to enable match analysis
        </div>
      )}

      {!isPro && analysesLeft !== null && (
        <div style={{ background: "#111318", border: "1px solid #1e2330", borderRadius: 10, padding: "10px 16px", marginBottom: 16, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontSize: 13, color: analysesLeft <= 1 ? "#f87171" : "#9ca3af" }}>
            {analysesLeft === 0 ? "⚠️ No analyses left this month" : `🎯 ${analysesLeft} free ${analysesLeft === 1 ? "analysis" : "analyses"} remaining this month`}
          </span>
          <button className="btn btn-sm" onClick={onUpgrade} style={{ fontSize: 11 }}>Upgrade for unlimited →</button>
        </div>
      )}

      {/* Input card */}
      <div className="card">
        <div className="card-title">Job Details</div>
        <div className="form-grid">
          <div className="form-group"><label>Company Name</label><input value={company} onChange={e => set("company")(e.target.value)} placeholder="e.g. Goldman Sachs" /></div>
          <div className="form-group"><label>Job Title</label><input value={jobTitle} onChange={e => set("jobTitle")(e.target.value)} placeholder="e.g. Analytics Manager" /></div>
          <div className="form-group full"><label>Job Description</label><textarea rows={10} value={jd} onChange={e => set("jd")(e.target.value)} placeholder="Paste the full job description here…" /></div>
        </div>
        <div style={{ marginTop: 16 }}>
          <button className="btn" onClick={runMatch} disabled={!canAnalyze || loading || (!isPro && analysesLeft === 0)}>
            {activeStep === "matching" ? <><div className="spinner" />Analyzing match…</> : analysesLeft === 0 ? "No analyses left — upgrade" : "🎯 Analyze Match"}
          </button>
        </div>
      </div>

      {/* Action buttons — always visible after first match */}
      {matchData && (
        <div className="card">
          <div className="card-title">Next Steps</div>
          <div className="action-grid">
            <button className={`action-btn${activeResultTab==="tweaks"&&tweaks?" active-tab":""}`} onClick={runTweaks} disabled={loading}>
              {activeStep === "tweaks" ? <div className="loading-state" style={{padding:0}}><div className="spinner"/>Generating…</div> : <>
                <span className="action-btn-icon">✏️</span>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                  <span className="action-btn-label">Resume Tweaks</span>
                  {!isPro&&<span style={{fontSize:10,fontWeight:700,color:"#c8a96e",background:"#1a1710",border:"1px solid #c8a96e40",padding:"1px 6px",borderRadius:10}}>PRO</span>}
                </div>
                <span className="action-btn-desc">Reword bullets to match this JD</span>
              </>}
            </button>
            <button className={`action-btn${activeResultTab==="interview"&&interviewData?" active-tab":""}`} onClick={runInterview} disabled={loading}>
              {activeStep === "interview" ? <div className="loading-state" style={{padding:0}}><div className="spinner"/>Preparing…</div> : <>
                <span className="action-btn-icon">🎤</span>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                  <span className="action-btn-label">Interview Prep</span>
                  {!isPro&&<span style={{fontSize:10,fontWeight:700,color:"#c8a96e",background:"#1a1710",border:"1px solid #c8a96e40",padding:"1px 6px",borderRadius:10}}>PRO</span>}
                </div>
                <span className="action-btn-desc">Likely questions + suggested answers</span>
              </>}
            </button>
            <button className={`action-btn${activeResultTab==="cover"&&coverLetter?" active-tab":""}`} onClick={runCover} disabled={loading}>
              {activeStep === "cover" ? <div className="loading-state" style={{padding:0}}><div className="spinner"/>Writing…</div> : <>
                <span className="action-btn-icon">✉️</span>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                  <span className="action-btn-label">Cover Letter</span>
                  {!isPro&&<span style={{fontSize:10,fontWeight:700,color:"#c8a96e",background:"#1a1710",border:"1px solid #c8a96e40",padding:"1px 6px",borderRadius:10}}>PRO</span>}
                </div>
                <span className="action-btn-desc">Tailored to this role and company</span>
              </>}
            </button>
          </div>
          <div style={{ marginTop: 14, display:"flex", alignItems:"center", justifyContent:"space-between" }}>
            <button className="btn btn-ghost btn-sm" onClick={saveToTracker}>💾 Save to Tracker</button>
            {!isPro && <button className="btn btn-sm" onClick={onUpgrade} style={{fontSize:12}}>✨ Upgrade to Pro — unlock tweaks, interview prep & cover letters</button>}
          </div>
        </div>
      )}

      {/* Results */}
      {(matchData || tweaks || interviewData || coverLetter) && (
        <div className="card">
          {/* Tab bar - scrollable on mobile */}
          <div className="result-tabs-scroll">
            <div style={{ display: "flex", gap: 4, marginBottom: 24, borderBottom: "1px solid #1e2330" }}>
            {[{id:"match",label:"Match Analysis",show:!!matchData},{id:"tweaks",label:"Resume Tweaks",show:!!tweaks},{id:"interview",label:"Interview Prep",show:!!interviewData},{id:"cover",label:"Cover Letter",show:!!coverLetter}].filter(t=>t.show).map(t => (
              <button key={t.id} onClick={() => setPersisted(p=>({...p,activeResultTab:t.id}))} style={{ background: "none", border: "none", borderBottom: activeResultTab===t.id ? "2px solid #c8a96e" : "2px solid transparent", color: activeResultTab===t.id ? "#c8a96e" : "#6b7280", padding: "8px 14px", cursor: "pointer", fontFamily: "'DM Sans',sans-serif", fontSize: 13.5, fontWeight: 500, marginBottom: -1, transition: "color 0.15s" }}>{t.label}</button>
            ))}
            </div>
          </div>

          {/* Match Analysis */}
          {activeResultTab === "match" && matchData && (
            <div>
              <div style={{ display: "flex", gap: 28, marginBottom: 24, flexWrap: "wrap", alignItems: "flex-start" }}>
                <div className="score-ring-wrap">
                  <div className={`score-ring ${scoreClass(matchData.overallScore)}`}>
                    <span className="score-num">{matchData.overallScore}</span>
                    <span className="score-denom">/10</span>
                  </div>
                  <span className="score-verdict" style={{ color: scoreColor(matchData.overallScore) }}>{matchData.verdict}</span>
                </div>
                <div style={{ flex: 1, minWidth: 220 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: matchData.shouldApply ? "#34d399" : "#f87171", marginBottom: 4 }}>
                    {matchData.shouldApply ? "✅ You should apply" : "⚠️ Consider carefully before applying"}
                  </div>
                  <div style={{ fontSize: 13, color: "#9ca3af", lineHeight: 1.6, marginBottom: 12 }}>{matchData.shouldApplyReason}</div>
                  <div style={{ fontSize: 12, color: "#6b7280" }}>Interview likelihood: <span style={{ color: matchData.interviewLikelihood==="High"?"#34d399":matchData.interviewLikelihood==="Medium"?"#c8a96e":"#f87171", fontWeight: 600 }}>{matchData.interviewLikelihood}</span></div>
                  <div style={{ fontSize: 12, color: "#4b5563", marginTop: 3 }}>{matchData.interviewLikelihoodReason}</div>
                </div>
                {matchData.topStrengths?.length > 0 && (
                  <div style={{ minWidth: 200 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: 8 }}>Your strengths</div>
                    {matchData.topStrengths.map((s,i) => <div key={i} style={{ fontSize: 13, color: "#34d399", marginBottom: 4 }}>✓ {s}</div>)}
                  </div>
                )}
              </div>
              {matchData.skillsMatch?.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <div className="card-title">Skills Match</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {matchData.skillsMatch.map((s,i) => (
                      <span key={i} className={`skill-pill ${s.have?"skill-have":s.importance==="high"?"skill-missing-high":s.importance==="medium"?"skill-missing-med":"skill-missing-low"}`}>
                        {s.have?"✓":"✗"} {s.skill}{!s.have&&s.importance==="high"?" ★":""}
                      </span>
                    ))}
                  </div>
                  <div style={{ fontSize: 12, color: "#4b5563", marginTop: 8 }}>✓ = you have it · ✗ = gap · ★ = high priority gap</div>
                </div>
              )}
              {matchData.experienceAlignment?.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <div className="card-title">Experience Alignment</div>
                  {matchData.experienceAlignment.map((e,i) => (
                    <div key={i} className="exp-row">
                      <span className="exp-label">{e.area}</span>
                      <div className="exp-bar-wrap"><div className={`exp-bar eb-${e.score}`} style={{ width: `${e.score*20}%` }} /></div>
                      <span className="exp-comment">{e.comment}</span>
                    </div>
                  ))}
                </div>
              )}
              {matchData.gapSummary && (
                <div style={{ background: "#0d0f14", border: "1px solid #1e2330", borderRadius: 8, padding: 14 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: 6 }}>Gap Summary</div>
                  <div style={{ fontSize: 13, color: "#9ca3af", lineHeight: 1.7 }}>{matchData.gapSummary}</div>
                </div>
              )}
            </div>
          )}

          {/* Resume Tweaks */}
          {activeResultTab === "tweaks" && tweaks && (
            <div>
              <div style={{ color: "#6b7280", fontSize: 13, marginBottom: 16 }}>{tweaks.length} suggested improvements — copy and paste into your resume before applying</div>
              {tweaks.map((t,i) => (
                <div key={i} className={`tweak-card tweak-impact-${t.impact}`}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                    <span style={{ fontSize: 11, color: "#6b7280" }}>{t.role} @ {t.company}</span>
                    <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", color: t.impact==="high"?"#34d399":t.impact==="medium"?"#c8a96e":"#6b7280" }}>{t.impact} impact</span>
                  </div>
                  <div className="tweak-original">Before: {t.original}</div>
                  <div className="tweak-improved">After: {t.improved}</div>
                  <div className="tweak-reason">{t.reason}</div>
                  <button className="btn btn-ghost btn-sm" style={{ marginTop: 10 }} onClick={() => { navigator.clipboard.writeText(t.improved); toast("📋 Copied!"); }}>📋 Copy</button>
                </div>
              ))}
            </div>
          )}

          {/* Interview Prep */}
          {activeResultTab === "interview" && interviewData && (
            <div>
              {interviewData.keyThemesToEmphasize?.length > 0 && (
                <div style={{ marginBottom: 20, background: "#0a1f17", border: "1px solid #34d39920", borderRadius: 8, padding: 14 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "#34d399", textTransform: "uppercase", letterSpacing: "0.8px", marginBottom: 8 }}>Key themes to emphasize</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {interviewData.keyThemesToEmphasize.map((t,i) => <span key={i} style={{ background: "#0a1f17", border: "1px solid #34d39940", color: "#34d399", padding: "3px 10px", borderRadius: 20, fontSize: 12 }}>{t}</span>)}
                  </div>
                </div>
              )}
              <div className="card-title">Likely Interview Questions</div>
              {(interviewData.likelyQuestions||[]).map((q,i) => (
                <div key={i} className="iq-card">
                  <span className={`iq-type iq-${q.type}`}>{q.type}</span>
                  <div className="iq-question">{q.question}</div>
                  <div style={{ fontSize: 12, color: "#4b5563", marginBottom: 8 }}>💡 {q.why}</div>
                  <div className="iq-answer">{q.suggestedAnswer}</div>
                  {q.starExample && <div className="iq-star">📌 Draw from: {q.starExample}</div>}
                </div>
              ))}
              {interviewData.potentialConcerns?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div className="card-title">Potential Concerns to Address</div>
                  {interviewData.potentialConcerns.map((c,i) => <div key={i} style={{ background: "#1a0a0a", border: "1px solid #f8717120", borderRadius: 8, padding: 12, marginBottom: 8, fontSize: 13, color: "#f87171" }}>⚠️ {c}</div>)}
                </div>
              )}
              {interviewData.questionsToAsk?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div className="card-title">Smart Questions to Ask</div>
                  {interviewData.questionsToAsk.map((q,i) => <div key={i} style={{ background: "#0d0f14", border: "1px solid #1e2330", borderRadius: 8, padding: 12, marginBottom: 8, fontSize: 13, color: "#9ca3af" }}>❓ {q}</div>)}
                </div>
              )}
            </div>
          )}

          {/* Cover Letter */}
          {activeResultTab === "cover" && coverLetter && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <label style={{ margin: 0 }}>Tone:</label>
                  <select value={tone} onChange={e => set("tone")(e.target.value)} style={{ width: "auto" }}>
                    <option value="professional">Professional</option>
                    <option value="confident and conversational">Conversational</option>
                    <option value="enthusiastic">Enthusiastic</option>
                    <option value="concise and direct">Concise</option>
                  </select>
                  <button className="btn btn-ghost btn-sm" onClick={runCover} disabled={loading}>{activeStep==="cover"?<><div className="spinner"/>Rewriting…</>:"Regenerate"}</button>
                </div>
                <button className="btn btn-ghost btn-sm" onClick={() => { navigator.clipboard.writeText(coverLetter); toast("📋 Copied!"); }}>📋 Copy</button>
              </div>
              <div className="cover-letter-text">{coverLetter}</div>
            </div>
          )}
        </div>
      )}

      {!matchData && !loading && (
        <div className="empty"><div className="empty-icon">🎯</div><div className="empty-text">Paste a job description above and click Analyze Match</div></div>
      )}
    </div>
  );
}

// ─── Tracker Tab ───────────────────────────────────────────────────────────────
function TrackerTab({ applications, setApplications, toast, updateApplicationStatus, deleteApplication }) {
  const [sel, setSel]             = useState(null);
  const [detailTab, setDetailTab] = useState("match");
  const job = applications.find(a => a.id === sel);

  // Reset detail tab when opening a different job
  const openJob = (id) => {
    setSel(id);
    setDetailTab("match");
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
        <div className="section-title">Application Tracker</div>
      </div>
      <div className="section-sub">{applications.length} job{applications.length!==1?"s":""} tracked</div>

      {applications.length === 0 ? (
        <div className="empty"><div className="empty-icon">📋</div><div className="empty-text">No applications yet — analyze a job and click "Save to Tracker"</div></div>
      ) : (
        <div className="tracker-grid">
          {STATUS_COLS.map(col => {
            const jobs = applications.filter(a => a.status === col.id);
            return (
              <div className="tracker-col" key={col.id}>
                <div className="col-header"><span className={`col-title ${col.cls}`}>{col.label}</span><span className="col-count">{jobs.length}</span></div>
                {jobs.map(j => (
                  <div className="tracker-item" key={j.id} onClick={() => openJob(j.id)}>
                    <div className="tracker-item-title">{j.jobTitle}</div>
                    <div className="tracker-item-company">{j.company}</div>
                    {j.matchScore && <div className="tracker-item-score" style={{ color: scoreColor(j.matchScore) }}>{j.matchScore}/10 · {j.verdict}</div>}
                    <div className="tracker-item-date">{j.added}</div>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}

      {job && (
        <div className="modal-backdrop" onClick={e => e.target===e.currentTarget && setSel(null)}>
          <div className="modal" style={{maxWidth:"680px"}}>
            {/* Header */}
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:4}}>
              <div>
                <div className="modal-title">{job.jobTitle}</div>
                <div style={{color:"#c8a96e",fontSize:14,marginBottom:8}}>{job.company}</div>
              </div>
              <button onClick={()=>setSel(null)} style={{background:"none",border:"none",color:"#4b5563",cursor:"pointer",fontSize:20,lineHeight:1,padding:4}}>×</button>
            </div>

            {/* Score + status row */}
            {job.matchScore && (
              <div style={{display:"flex",alignItems:"center",gap:12,marginBottom:16}}>
                <div className={`score-ring ${scoreClass(job.matchScore)}`} style={{width:52,height:52,flexShrink:0}}>
                  <span style={{fontFamily:"'Instrument Serif',serif",fontSize:18,fontWeight:700,lineHeight:1}}>{job.matchScore}</span>
                  <span style={{fontSize:9,opacity:0.7}}>/10</span>
                </div>
                <div>
                  <div style={{fontSize:13,fontWeight:600,color:scoreColor(job.matchScore)}}>{job.verdict}</div>
                  {job.matchData?.shouldApplyReason&&<div style={{fontSize:12,color:"#6b7280",marginTop:2}}>{job.matchData.shouldApplyReason}</div>}
                </div>
                <div style={{marginLeft:"auto",display:"flex",flexWrap:"wrap",gap:6}}>
                  {STATUS_COLS.map(c=>(
                    <button key={c.id} onClick={()=>{
                      setApplications(a=>a.map(x=>x.id===sel?{...x,status:c.id}:x));
                      updateApplicationStatus(sel, c.id);
                    }}
                      style={{fontSize:11,fontWeight:600,padding:"3px 10px",borderRadius:20,cursor:"pointer",fontFamily:"'DM Sans',sans-serif",
                        background:job.status===c.id?"#1a1c26":"transparent",
                        border:`1px solid ${job.status===c.id?"#2a3040":"#1e2330"}`,
                        color:job.status===c.id?"#e8e4dc":"#6b7280"}}>
                      {c.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <hr className="divider" style={{margin:"12px 0"}}/>

            {/* Detail tabs */}
            {job && (() => {
              const detailTabs = [
                {id:"match",         label:"Match",              show: !!job.matchData},
                {id:"tweakedResume", label:"Tweaked Resume",     show: !!job.tweakedResume},
                {id:"tweaks",        label:"Resume Tweaks",      show: !!(job.tweaks?.length)},
                {id:"interview",     label:"Interview Prep",     show: !!job.interviewData},
                {id:"cover",         label:"Cover Letter",       show: !!job.coverLetter},
                {id:"jd",            label:"Job Description",    show: !!job.jd},
              ].filter(t=>t.show);
              const activeTab = detailTabs.find(t=>t.id===detailTab) ? detailTab : (detailTabs[0]?.id||"match");
              return detailTabs.length > 0 ? (
                <div>
                  <div style={{display:"flex",gap:2,marginBottom:16,borderBottom:"1px solid #1e2330",flexWrap:"wrap"}}>
                    {detailTabs.map(t=>(
                      <button key={t.id} onClick={()=>setDetailTab(t.id)}
                        style={{background:"none",border:"none",borderBottom:activeTab===t.id?"2px solid #c8a96e":"2px solid transparent",
                          color:activeTab===t.id?"#c8a96e":"#6b7280",padding:"6px 12px",cursor:"pointer",
                          fontFamily:"'DM Sans',sans-serif",fontSize:12.5,fontWeight:500,marginBottom:-1,whiteSpace:"nowrap"}}>
                        {t.label}
                      </button>
                    ))}
                  </div>
                  {activeTab==="match" && job.matchData && (
                    <div>
                      {job.matchData.skillsMatch?.length>0 && (
                        <div style={{marginBottom:14}}>
                          <div style={{fontSize:12,fontWeight:600,color:"#6b7280",textTransform:"uppercase",letterSpacing:"0.8px",marginBottom:8}}>Skills</div>
                          <div style={{display:"flex",flexWrap:"wrap",gap:5}}>
                            {job.matchData.skillsMatch.map((s,i)=>(
                              <span key={i} className={`skill-pill ${s.have?"skill-have":s.importance==="high"?"skill-missing-high":s.importance==="medium"?"skill-missing-med":"skill-missing-low"}`}>
                                {s.have?"✓":"✗"} {s.skill}{!s.have&&s.importance==="high"?" ★":""}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                      {job.matchData.topStrengths?.length>0 && (
                        <div style={{marginBottom:14}}>
                          <div style={{fontSize:12,fontWeight:600,color:"#6b7280",textTransform:"uppercase",letterSpacing:"0.8px",marginBottom:6}}>Strengths</div>
                          {job.matchData.topStrengths.map((s,i)=><div key={i} style={{fontSize:13,color:"#34d399",marginBottom:3}}>✓ {s}</div>)}
                        </div>
                      )}
                      {job.matchData.gapSummary && (
                        <div style={{background:"#0d0f14",border:"1px solid #1e2330",borderRadius:8,padding:12}}>
                          <div style={{fontSize:11,fontWeight:600,color:"#6b7280",textTransform:"uppercase",letterSpacing:"0.8px",marginBottom:5}}>Gap Summary</div>
                          <div style={{fontSize:13,color:"#9ca3af",lineHeight:1.6}}>{job.matchData.gapSummary}</div>
                        </div>
                      )}
                    </div>
                  )}
                  {activeTab==="tweakedResume" && job.tweakedResume && (
                    <div>
                      <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:14}}>
                        <span className="snapshot-badge">✓ Tweaked Resume Snapshot</span>
                        <span style={{fontSize:12,color:"#6b7280"}}>{job.tweakedResume.appliedTweaks} tweaks applied · Based on "{job.tweakedResume.resumeName}"</span>
                      </div>
                      <div style={{fontSize:12,color:"#4b5563",marginBottom:14}}>This is the exact resume version you should send to {job.company} — bullets already rewritten for this role.</div>
                      <div style={{maxHeight:400,overflowY:"auto"}}>
                        {(job.tweakedResume.experience||[]).map((exp,ei)=>(
                          <div key={ei} style={{marginBottom:16,paddingBottom:16,borderBottom:ei<job.tweakedResume.experience.length-1?"1px solid #1e2330":"none"}}>
                            <div style={{fontSize:13,color:"#e8e4dc",fontWeight:600,marginBottom:2}}>{exp.role}</div>
                            <div style={{fontSize:12,color:"#c8a96e",marginBottom:8}}>{exp.company}{exp.period&&<span style={{color:"#4b5563"}}> · {exp.period}</span>}</div>
                            {(exp.accomplishments||[]).filter(a=>a).map((acc,ai)=>{
                              // Highlight tweaked bullets
                              const wasTweaked = (job.tweaks||[]).some(t=>t.improved===acc);
                              return (
                                <div key={ai} style={{display:"flex",gap:8,marginBottom:5,alignItems:"flex-start"}}>
                                  <span style={{color:wasTweaked?"#34d399":"#c8a96e",fontSize:11,marginTop:2,flexShrink:0}}>{wasTweaked?"✓":"•"}</span>
                                  <div style={{fontSize:12,color:wasTweaked?"#e8e4dc":"#9ca3af",lineHeight:1.5}}>{acc}</div>
                                </div>
                              );
                            })}
                          </div>
                        ))}
                      </div>
                      <button className="btn btn-ghost btn-sm" style={{marginTop:10}} onClick={()=>{
                        const text = (job.tweakedResume.experience||[]).map(exp =>
                          `${exp.role} @ ${exp.company}${exp.period?` (${exp.period})`:""}\n${(exp.accomplishments||[]).filter(a=>a).map(a=>`• ${a}`).join("\n")}`
                        ).join("\n\n");
                        navigator.clipboard.writeText(text);
                        toast("📋 Tweaked resume copied!");
                      }}>📋 Copy all bullets</button>
                    </div>
                  )}
                  {activeTab==="tweaks" && job.tweaks && (
                    <div style={{maxHeight:360,overflowY:"auto"}}>
                      {job.tweaks.map((t,i)=>(
                        <div key={i} className={`tweak-card tweak-impact-${t.impact}`}>
                          <div style={{display:"flex",justifyContent:"space-between",marginBottom:6}}>
                            <span style={{fontSize:11,color:"#6b7280"}}>{t.role} @ {t.company}</span>
                            <span style={{fontSize:10,fontWeight:700,textTransform:"uppercase",color:t.impact==="high"?"#34d399":t.impact==="medium"?"#c8a96e":"#6b7280"}}>{t.impact}</span>
                          </div>
                          <div className="tweak-original" style={{fontSize:12}}>Before: {t.original}</div>
                          <div className="tweak-improved" style={{fontSize:12}}>After: {t.improved}</div>
                          <div className="tweak-reason" style={{fontSize:11}}>{t.reason}</div>
                          <button className="btn btn-ghost btn-sm" style={{marginTop:8,fontSize:11}} onClick={()=>{navigator.clipboard.writeText(t.improved);toast("📋 Copied!");}}>📋 Copy</button>
                        </div>
                      ))}
                    </div>
                  )}
                  {activeTab==="interview" && job.interviewData && (
                    <div style={{maxHeight:380,overflowY:"auto"}}>
                      {job.interviewData.keyThemesToEmphasize?.length>0 && (
                        <div style={{marginBottom:12,background:"#0a1f17",border:"1px solid #34d39920",borderRadius:8,padding:10}}>
                          <div style={{fontSize:11,fontWeight:600,color:"#34d399",textTransform:"uppercase",letterSpacing:"0.8px",marginBottom:6}}>Key themes</div>
                          <div style={{display:"flex",flexWrap:"wrap",gap:5}}>
                            {job.interviewData.keyThemesToEmphasize.map((t,i)=><span key={i} style={{background:"#0a1f17",border:"1px solid #34d39940",color:"#34d399",padding:"2px 8px",borderRadius:20,fontSize:11}}>{t}</span>)}
                          </div>
                        </div>
                      )}
                      {(job.interviewData.likelyQuestions||[]).map((q,i)=>(
                        <div key={i} className="iq-card" style={{marginBottom:10}}>
                          <span className={`iq-type iq-${q.type}`}>{q.type}</span>
                          <div className="iq-question" style={{fontSize:13}}>{q.question}</div>
                          <div className="iq-answer" style={{fontSize:12}}>{q.suggestedAnswer}</div>
                          {q.starExample&&<div className="iq-star" style={{fontSize:11}}>📌 {q.starExample}</div>}
                        </div>
                      ))}
                      {job.interviewData.questionsToAsk?.length>0 && (
                        <div style={{marginTop:10}}>
                          <div style={{fontSize:11,fontWeight:600,color:"#6b7280",textTransform:"uppercase",letterSpacing:"0.8px",marginBottom:6}}>Questions to ask</div>
                          {job.interviewData.questionsToAsk.map((q,i)=><div key={i} style={{background:"#0d0f14",border:"1px solid #1e2330",borderRadius:6,padding:"8px 10px",marginBottom:6,fontSize:12,color:"#9ca3af"}}>❓ {q}</div>)}
                        </div>
                      )}
                    </div>
                  )}
                  {activeTab==="cover" && job.coverLetter && (
                    <div>
                      <div style={{display:"flex",justifyContent:"flex-end",marginBottom:8}}>
                        <button className="btn btn-ghost btn-sm" onClick={()=>{navigator.clipboard.writeText(job.coverLetter);toast("📋 Copied!");}}>📋 Copy</button>
                      </div>
                      <div className="cover-letter-text" style={{fontSize:13,maxHeight:360,overflowY:"auto"}}>{job.coverLetter}</div>
                    </div>
                  )}
                  {activeTab==="jd" && job.jd && (
                    <div style={{background:"#0d0f14",border:"1px solid #1e2330",borderRadius:8,padding:12,maxHeight:340,overflowY:"auto",fontSize:13,color:"#9ca3af",lineHeight:1.7,whiteSpace:"pre-wrap"}}>
                      {job.jd}
                    </div>
                  )}
                </div>
              ) : null;
            })()}

            <div className="modal-actions" style={{marginTop:16}}>
              <button className="btn btn-danger btn-sm" onClick={()=>{
                setApplications(a=>a.filter(x=>x.id!==sel));
                deleteApplication(sel);
                setSel(null);
                toast("Removed");
              }}>Remove</button>
              <button className="btn btn-ghost" onClick={()=>setSel(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Root ──────────────────────────────────────────────────────────────────────
export default function App() {
  const { user, loading: authLoading, isPro } = useAuth();
  const [tab, setTab]         = useState("profile");
  const [showLogin, setShowLogin] = useState(false); // landing → login transition
  // Multiple resume profiles — array of profile objects, activeResumeIdx tracks which is selected
  const [resumes, setResumes]         = useState([{ id: "r-default", name: "My Resume", skills: [], experience: [] }]);
  const [activeResumeIdx, setActiveResumeIdx] = useState(0);
  const profile    = resumes[activeResumeIdx] || resumes[0];
  const setProfile = updater => setResumes(rs => rs.map((r, i) => i === activeResumeIdx ? (typeof updater === "function" ? updater(r) : updater) : r));
  const [applications, setApplications] = useState([]);
  const [toastMsg, setToastMsg] = useState(null);
  const [matchPersisted, setMatchPersisted] = useState({});
  const [analysesUsed, setAnalysesUsed]     = useState(0);
  const [page, setPage] = useState(() => {
    const p = window.location.pathname;
    if (p === "/success") return "success";
    if (p === "/account") return "account";
    if (p === "/privacy") return "privacy";
    if (p === "/terms")   return "terms";
    return "app";
  });

  const toast = msg => { setToastMsg(null); setTimeout(() => setToastMsg(msg), 10); };
  const key   = k => user ? `ea:${user.id}:${k}` : null;

  // Clean up OAuth redirect params from URL after login
  useEffect(() => {
    const url = window.location.href;
    if (url.includes("error=") || url.includes("access_token=") || url.includes("code=")) {
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // ── Load profile/resumes from localStorage ────────────────────────────────
  useEffect(() => {
    if (!user) return;
    try {
      const r = localStorage.getItem(key("resumes"));
      if (r) { setResumes(JSON.parse(r)); }
      else {
        // Migrate old single profile to new resumes array
        const p = localStorage.getItem(key("profile"));
        if (p) setResumes([{ ...JSON.parse(p), id: "r-default", name: "My Resume" }]);
      }
    } catch {}
  }, [user?.id]);
  useEffect(() => { if (user) try { localStorage.setItem(key("resumes"), JSON.stringify(resumes)); } catch {} }, [resumes]);

  // ── Load applications from Supabase on login ──────────────────────────────
  useEffect(() => {
    if (!user) return;
    (async () => {
      const { data, error } = await supabase
        .from("applications")
        .select("*")
        .eq("user_id", user.id)
        .order("added_at", { ascending: false });
      if (error) { console.error("Load applications error:", error.message); return; }
      // Map snake_case DB columns back to camelCase used in the app
      setApplications((data || []).map(r => ({
        id:            r.id,
        jobTitle:      r.job_title,
        company:       r.company,
        status:        r.status,
        matchScore:    r.match_score,
        verdict:       r.verdict,
        jd:            r.jd,
        matchData:     r.match_data,
        tweaks:        r.tweaks,
        interviewData: r.interview_data,
        coverLetter:   r.cover_letter,
        tweakedResume: r.tweaked_resume || null,
        resumeName:    r.resume_name    || "My Resume",
        added:         r.added_at ? new Date(r.added_at).toLocaleDateString("en-CA") : "",
      })));
    })();
  }, [user?.id]);

  // ── Supabase helpers called directly by child components ──────────────────
  const saveApplication = async (app) => {
    const row = {
      id:             app.id,
      user_id:        user.id,
      job_title:      app.jobTitle,
      company:        app.company,
      status:         app.status,
      match_score:    app.matchScore,
      verdict:        app.verdict,
      jd:             app.jd,
      match_data:     app.matchData,
      tweaks:         app.tweaks,
      interview_data: app.interviewData,
      cover_letter:   app.coverLetter,
      tweaked_resume: app.tweakedResume || null,
      resume_name:    app.resumeName    || null,
    };
    const { error } = await supabase.from("applications").upsert(row);
    if (error) { console.error("Save application error:", error.message); toast("⚠️ Could not save — try again."); return false; }
    return true;
  };

  const updateApplicationStatus = async (id, status) => {
    const { error } = await supabase.from("applications").update({ status }).eq("id", id).eq("user_id", user.id);
    if (error) console.error("Status update error:", error.message);
  };

  const deleteApplication = async (id) => {
    const { error } = await supabase.from("applications").delete().eq("id", id).eq("user_id", user.id);
    if (error) console.error("Delete error:", error.message);
  };

  if (authLoading) return <><style>{css}</style><div style={{ minHeight: "100vh", background: "#0d0f14", display: "flex", alignItems: "center", justifyContent: "center" }}><div className="spinner" style={{ width: 28, height: 28, borderWidth: 3 }} /></div></>;
  if (page === "privacy") return <PrivacyPage />;
  if (page === "terms")   return <TermsPage />;
  if (!user && !showLogin)    return <LandingPage onGetStarted={() => setShowLogin(true)} />;
  if (!user)                  return <LoginPage />;
  if (page === "privacy")     return <PrivacyPage />;
  if (page === "terms")       return <TermsPage />;
  if (page === "success")     return <SuccessPage onContinue={() => setPage("app")} />;
  if (page === "account")     return <AccountPage onBack={() => setPage("app")} onUpgrade={() => setPage("pricing")} />;
  if (page === "pricing")     return <PricingPage onContinueFree={() => setPage("app")} />;

  return (
    <>
      <style>{css}</style>
      <div className="app">
        <div className="topbar">
          <div className="logo">apply by <span>etlyx</span></div>
          <nav className="nav">
            {TABS.map(t => <button key={t.id} className={`nav-btn${tab===t.id?" active":""}`} onClick={() => setTab(t.id)}>{t.icon} {t.label}</button>)}
          </nav>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {isPro
              ? <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.8px", color: "#c8a96e", background: "#1a1710", border: "1px solid #c8a96e40", padding: "3px 10px", borderRadius: 20 }}>Pro</span>
              : <button onClick={() => setPage("pricing")} style={{ fontSize: 11, fontWeight: 600, color: "#6b7280", background: "#111318", border: "1px solid #1e2330", padding: "4px 10px", borderRadius: 20, cursor: "pointer", fontFamily: "'DM Sans',sans-serif" }}>Free · Upgrade</button>
            }
            <button onClick={() => setPage("account")} style={{ fontSize: 12, color: "#4b5563", background: "none", border: "1px solid #1e2330", cursor: "pointer", padding: "5px 12px", borderRadius: 8, fontFamily: "'DM Sans',sans-serif", transition: "all 0.15s" }} onMouseEnter={e => { e.currentTarget.style.color="#e8e4dc"; e.currentTarget.style.borderColor="#2a3040"; }} onMouseLeave={e => { e.currentTarget.style.color="#4b5563"; e.currentTarget.style.borderColor="#1e2330"; }}>Account</button>
          </div>
        </div>
        <div className="content">
          {tab === "profile" && <ProfileTab profile={profile} setProfile={setProfile} resumes={resumes} setResumes={setResumes} activeResumeIdx={activeResumeIdx} setActiveResumeIdx={setActiveResumeIdx} applications={applications} toast={toast} />}
          {tab === "match"   && <JobMatchTab profile={profile} resumeName={profile.name||"My Resume"} applications={applications} setApplications={setApplications} toast={toast} isPro={isPro} onUpgrade={() => setPage("pricing")} persisted={matchPersisted} setPersisted={setMatchPersisted} saveApplication={saveApplication} analysesUsed={analysesUsed} setAnalysesUsed={setAnalysesUsed} />}
          {tab === "tracker" && <TrackerTab applications={applications} setApplications={setApplications} toast={toast} updateApplicationStatus={updateApplicationStatus} deleteApplication={deleteApplication} />}
        </div>

        {/* Bottom nav for mobile */}
        <nav className="bottom-nav">
          {TABS.map(t => (
            <button key={t.id} className={`bottom-nav-btn${tab===t.id?" active":""}`} onClick={() => setTab(t.id)}>
              <span className="bottom-nav-icon">{t.icon}</span>
              <span className="bottom-nav-label">{t.label}</span>
            </button>
          ))}
        </nav>
        {toastMsg && <Toast msg={toastMsg} onDone={() => setToastMsg(null)} />}
      </div>
    </>
  );
}
