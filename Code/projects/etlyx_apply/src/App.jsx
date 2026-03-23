import { useState, useEffect, useRef } from "react";
import { useAuth } from "./lib/auth.jsx";
import { supabase } from "./lib/supabase.js";
import LoginPage from "./pages/Login.jsx";
import PricingPage from "./pages/Pricing.jsx";
import SuccessPage from "./pages/Success.jsx";
import AccountPage from "./pages/Account.jsx";
import UpgradeWall from "./components/UpgradeWall.jsx";

// ─── Styles ────────────────────────────────────────────────────────────────

const FONTS = `@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');`;

const css = `
  ${FONTS}
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body, #root { height: 100%; }
  body { background: #0d0f14; }
  .app { font-family: 'DM Sans', sans-serif; background: #0d0f14; color: #e8e4dc; min-height: 100vh; display: flex; flex-direction: column; }
  .topbar { display: flex; align-items: center; justify-content: space-between; padding: 0 32px; height: 60px; border-bottom: 1px solid #1e2330; background: #0d0f14; position: sticky; top: 0; z-index: 100; }
  .logo { font-family: 'Instrument Serif', serif; font-size: 22px; letter-spacing: -0.3px; color: #e8e4dc; }
  .logo span { color: #c8a96e; }
  .nav { display: flex; gap: 4px; }
  .nav-btn { background: none; border: none; color: #6b7280; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-family: 'DM Sans', sans-serif; font-size: 13.5px; font-weight: 500; transition: all 0.15s; display: flex; align-items: center; gap: 6px; }
  .nav-btn:hover { color: #e8e4dc; background: #161922; }
  .nav-btn.active { color: #c8a96e; background: #1a1710; }
  .content { flex: 1; max-width: 1100px; width: 100%; margin: 0 auto; padding: 40px 32px; }
  .section-title { font-family: 'Instrument Serif', serif; font-size: 28px; color: #e8e4dc; margin-bottom: 6px; }
  .section-sub { color: #6b7280; font-size: 13.5px; margin-bottom: 32px; }
  .card { background: #111318; border: 1px solid #1e2330; border-radius: 14px; padding: 28px; margin-bottom: 20px; }
  .card-title { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #c8a96e; margin-bottom: 18px; }
  .upload-zone { border: 2px dashed #2a2f3e; border-radius: 12px; padding: 48px; text-align: center; cursor: pointer; transition: all 0.2s; background: #0d0f14; }
  .upload-zone:hover { border-color: #c8a96e; background: #1a1710; }
  .upload-icon { font-size: 40px; margin-bottom: 12px; }
  .upload-text { color: #9ca3af; font-size: 14px; }
  .upload-text strong { color: #c8a96e; }
  .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .form-group { display: flex; flex-direction: column; gap: 6px; }
  .form-group.full { grid-column: 1 / -1; }
  label { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: #6b7280; }
  input, textarea, select { background: #0d0f14; border: 1px solid #1e2330; border-radius: 8px; color: #e8e4dc; padding: 10px 14px; font-family: 'DM Sans', sans-serif; font-size: 14px; outline: none; transition: border-color 0.15s; }
  input:focus, textarea:focus, select:focus { border-color: #c8a96e; }
  textarea { resize: vertical; min-height: 80px; }
  select option { background: #111318; }
  .btn { background: #c8a96e; color: #0d0f14; border: none; border-radius: 8px; padding: 10px 20px; font-family: 'DM Sans', sans-serif; font-size: 13.5px; font-weight: 600; cursor: pointer; transition: all 0.15s; display: inline-flex; align-items: center; gap: 7px; }
  .btn:hover { background: #d4b87e; transform: translateY(-1px); }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
  .btn-ghost { background: transparent; color: #9ca3af; border: 1px solid #1e2330; }
  .btn-ghost:hover { background: #161922; color: #e8e4dc; transform: none; }
  .btn-danger { background: transparent; color: #ef4444; border: 1px solid #2a1515; }
  .btn-danger:hover { background: #1a0a0a; transform: none; }
  .btn-sm { padding: 6px 12px; font-size: 12px; }
  .tag { display: inline-flex; align-items: center; gap: 5px; background: #1a1c26; border: 1px solid #2a2f3e; color: #9ca3af; padding: 4px 10px; border-radius: 20px; font-size: 12px; }
  .tag-remove { cursor: pointer; color: #6b7280; font-size: 14px; line-height: 1; }
  .tag-remove:hover { color: #ef4444; }
  .tags-wrap { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }

  /* Source badges */
  .source-badge { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px; padding: 2px 7px; border-radius: 4px; flex-shrink: 0; }
  .src-linkedin  { background: #0a1628; color: #3b82f6; border: 1px solid #1e3a5f; }
  .src-indeed    { background: #1a1200; color: #f59e0b; border: 1px solid #3d2e00; }
  .src-hiring    { background: #0a1a0a; color: #34d399; border: 1px solid #1a3d1a; }
  .src-bank      { background: #1a100a; color: #c8a96e; border: 1px solid #3d2a10; }
  .src-other     { background: #1a1c26; color: #9ca3af; border: 1px solid #2a2f3e; }

  /* Job cards */
  .job-card { background: #111318; border: 1px solid #1e2330; border-radius: 12px; padding: 20px 24px; margin-bottom: 12px; transition: border-color 0.15s; cursor: pointer; }
  .job-card:hover { border-color: #2a3040; }
  .job-card.score-5 { border-left: 3px solid #34d399; }
  .job-card.score-4 { border-left: 3px solid #60a5fa; }
  .job-card.score-3 { border-left: 3px solid #c8a96e; }
  .job-card.score-2 { border-left: 3px solid #f59e0b; }
  .job-card.score-1 { border-left: 3px solid #f87171; }
  .job-card-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
  .job-title { font-family: 'Instrument Serif', serif; font-size: 18px; color: #e8e4dc; margin-bottom: 4px; }
  .job-company { color: #c8a96e; font-size: 13.5px; font-weight: 500; }
  .job-meta { display: flex; gap: 12px; margin-top: 10px; flex-wrap: wrap; align-items: center; }
  .job-meta span { color: #6b7280; font-size: 12.5px; display: flex; align-items: center; gap: 4px; }
  .job-desc { color: #9ca3af; font-size: 13.5px; line-height: 1.6; margin-top: 12px; }
  .job-actions { display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap; }

  /* Score circle */
  .score-badge { display: flex; flex-direction: column; align-items: center; gap: 3px; flex-shrink: 0; }
  .score-circle { width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 700; font-family: 'Instrument Serif', serif; border: 2px solid; }
  .score-circle.s5 { color: #34d399; border-color: #34d399; background: #0a1f17; }
  .score-circle.s4 { color: #60a5fa; border-color: #60a5fa; background: #0a1220; }
  .score-circle.s3 { color: #c8a96e; border-color: #c8a96e; background: #1a1710; }
  .score-circle.s2 { color: #f59e0b; border-color: #f59e0b; background: #1a1400; }
  .score-circle.s1 { color: #f87171; border-color: #f87171; background: #1a0a0a; }
  .score-circle.pending { color: #4b5563; border-color: #2a2f3e; background: transparent; font-size: 11px; }
  .score-label { font-size: 10px; color: #4b5563; text-transform: uppercase; letter-spacing: 0.5px; }

  /* Eval breakdown */
  .score-breakdown { background: #0d0f14; border: 1px solid #1e2330; border-radius: 10px; padding: 16px; margin-top: 14px; }
  .score-breakdown-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: #6b7280; margin-bottom: 12px; }
  .criteria-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
  .criteria-name { font-size: 12.5px; color: #9ca3af; width: 130px; flex-shrink: 0; }
  .criteria-bar-wrap { flex: 1; height: 5px; background: #1e2330; border-radius: 3px; overflow: hidden; }
  .criteria-bar { height: 100%; border-radius: 3px; transition: width 0.6s ease; }
  .bar-5{background:#34d399}.bar-4{background:#60a5fa}.bar-3{background:#c8a96e}.bar-2{background:#f59e0b}.bar-1{background:#f87171}
  .criteria-score { font-size: 12px; font-weight: 600; width: 20px; text-align: right; flex-shrink: 0; }
  .cs-5{color:#34d399}.cs-4{color:#60a5fa}.cs-3{color:#c8a96e}.cs-2{color:#f59e0b}.cs-1{color:#f87171}
  .eval-summary { font-size: 12.5px; color: #6b7280; margin-top: 10px; line-height: 1.6; font-style: italic; }

  /* Recommendation cards */
  .rec-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 4px; }
  .rec-card { background: #0d0f14; border: 1px solid #1e2330; border-radius: 10px; padding: 14px 16px; display: flex; flex-direction: column; gap: 6px; transition: border-color 0.15s; }
  .rec-card:hover { border-color: #2a3040; }
  .rec-card.stretch { border-color: #c8a96e40; }
  .rec-title { font-size: 14px; color: #e8e4dc; font-weight: 500; }
  .rec-reason { font-size: 12px; color: #6b7280; line-height: 1.5; }
  .rec-stretch { font-size: 10px; color: #c8a96e; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }

  /* Per-job evaluate button */
  .eval-btn { background: #1a1c26; border: 1px solid #2a2f3e; color: #9ca3af; border-radius: 6px; padding: 5px 10px; font-size: 11px; font-weight: 600; cursor: pointer; font-family: 'DM Sans', sans-serif; transition: all 0.15s; display: inline-flex; align-items: center; gap: 5px; }
  .eval-btn:hover { background: #1a1710; border-color: #c8a96e; color: #c8a96e; }
  .eval-btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .pipeline { display: flex; align-items: flex-start; margin-bottom: 24px; background: #111318; border: 1px solid #1e2330; border-radius: 10px; padding: 16px 20px; overflow-x: auto; gap: 0; flex-wrap: wrap; }
  .pipeline-section { display: flex; flex-direction: column; gap: 6px; padding: 0 12px; border-right: 1px solid #1e2330; }
  .pipeline-section:last-child { border-right: none; }
  .pipeline-section-title { font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; color: #4b5563; margin-bottom: 4px; }
  .agent-step { display: flex; align-items: center; gap: 7px; }
  .agent-dot { width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; flex-shrink: 0; }
  .agent-dot.idle { background: #1a1c26; border: 1px solid #2a2f3e; }
  .agent-dot.running { background: #1a1710; border: 1px solid #c8a96e; animation: pulse 1.2s ease-in-out infinite; }
  .agent-dot.done { background: #0a1f17; border: 1px solid #34d399; }
  .agent-dot.error { background: #1a0a0a; border: 1px solid #f87171; }
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5}}
  .agent-name { font-size: 12px; font-weight: 500; color: #e8e4dc; }
  .agent-status { font-size: 11px; color: #4b5563; }
  .agent-status.running{color:#c8a96e}.agent-status.done{color:#34d399}.agent-status.error{color:#f87171}
  .pipeline-arrow { color: #2a2f3e; font-size: 18px; padding: 0 8px; align-self: center; flex-shrink: 0; }

  /* Filters */
  .filter-row { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; align-items: center; }
  .filter-btn { background: #111318; border: 1px solid #1e2330; color: #6b7280; padding: 5px 12px; border-radius: 20px; font-size: 12px; cursor: pointer; font-family: 'DM Sans', sans-serif; transition: all 0.15s; }
  .filter-btn:hover, .filter-btn.active { background: #1a1710; border-color: #c8a96e; color: #c8a96e; }
  .filter-label { font-size: 12px; color: #4b5563; }
  .results-count { font-size: 12px; color: #4b5563; margin-left: auto; }

  .search-row { display: flex; gap: 10px; margin-bottom: 16px; }

  /* Tracker */
  .tracker-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; align-items: start; }
  .tracker-col { background: #111318; border: 1px solid #1e2330; border-radius: 12px; padding: 16px; }
  .col-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
  .col-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; }
  .col-count { background: #1a1c26; color: #9ca3af; border-radius: 20px; padding: 2px 8px; font-size: 11px; }
  .tracker-item { background: #0d0f14; border: 1px solid #1e2330; border-radius: 8px; padding: 12px; margin-bottom: 8px; cursor: pointer; transition: border-color 0.15s; }
  .tracker-item:hover { border-color: #2a3040; }
  .tracker-item.ts5{border-left:2px solid #34d399}.tracker-item.ts4{border-left:2px solid #60a5fa}
  .tracker-item.ts3{border-left:2px solid #c8a96e}.tracker-item.ts2{border-left:2px solid #f59e0b}
  .tracker-item.ts1{border-left:2px solid #f87171}
  .tracker-item-title { font-size: 13px; color: #e8e4dc; font-weight: 500; margin-bottom: 4px; }
  .tracker-item-company { font-size: 12px; color: #c8a96e; }
  .tracker-item-date { font-size: 11px; color: #4b5563; margin-top: 6px; }
  .tracker-score { font-size: 11px; margin-top: 4px; }
  .status-saved{color:#60a5fa}.status-applied{color:#a78bfa}.status-interview{color:#34d399}.status-offer{color:#c8a96e}.status-rejected{color:#f87171}

  .cover-letter-text { background: #0d0f14; border: 1px solid #1e2330; border-radius: 8px; padding: 20px; color: #d1cdc7; font-size: 14px; line-height: 1.8; white-space: pre-wrap; min-height: 300px; }

  .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #2a2f3e; border-top-color: #c8a96e; border-radius: 50%; animation: spin 0.7s linear infinite; }
  @keyframes spin{to{transform:rotate(360deg)}}
  .loading-state { display: flex; align-items: center; gap: 10px; color: #9ca3af; font-size: 14px; padding: 20px 0; justify-content: center; }

  .modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 20px; }
  .modal { background: #111318; border: 1px solid #1e2330; border-radius: 16px; padding: 32px; width: 100%; max-width: 580px; max-height: 85vh; overflow-y: auto; }
  .modal-title { font-family: 'Instrument Serif', serif; font-size: 22px; margin-bottom: 6px; }
  .modal-sub { color: #6b7280; font-size: 13px; margin-bottom: 24px; }
  .modal-actions { display: flex; gap: 10px; margin-top: 24px; justify-content: flex-end; }
  .qa-item { border-bottom: 1px solid #1e2330; padding: 16px 0; }
  .qa-item:last-child { border-bottom: none; }
  .qa-question { font-size: 13.5px; color: #9ca3af; margin-bottom: 8px; }
  .divider { border: none; border-top: 1px solid #1e2330; margin: 24px 0; }
  .empty { text-align: center; padding: 60px 20px; color: #4b5563; }
  .empty-icon { font-size: 40px; margin-bottom: 12px; }
  .empty-text { font-size: 14px; }
  .toast { position: fixed; bottom: 28px; right: 28px; background: #1e2330; border: 1px solid #2a3040; border-radius: 10px; padding: 12px 18px; color: #e8e4dc; font-size: 13.5px; z-index: 999; display: flex; align-items: center; gap: 8px; animation: slideUp 0.2s ease; }
  @keyframes slideUp{from{transform:translateY(10px);opacity:0}to{transform:translateY(0);opacity:1}}
  .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #34d399; }
  ::-webkit-scrollbar{width:6px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:#2a2f3e;border-radius:3px}
  @media(max-width:900px){.form-grid{grid-template-columns:1fr}.tracker-grid{grid-template-columns:1fr 1fr}.topbar{padding:0 16px}.content{padding:24px 16px}}
`;

// ─── Constants ─────────────────────────────────────────────────────────────

const TABS = [
  { id:"profile", label:"Profile",       icon:"👤" },
  { id:"search",  label:"Search Jobs",   icon:"🔍" },
  { id:"tracker", label:"Tracker",       icon:"📋" },
  { id:"cover",   label:"Cover Letters", icon:"✉️" },
];

const STATUS_COLS = [
  { id:"saved",     label:"Saved",     cls:"status-saved" },
  { id:"applied",   label:"Applied",   cls:"status-applied" },
  { id:"interview", label:"Interview", cls:"status-interview" },
  { id:"offer",     label:"Offer",     cls:"status-offer" },
  { id:"rejected",  label:"Rejected",  cls:"status-rejected" },
];

const EVAL_CRITERIA = [
  { key:"roleFit",        label:"Role Fit" },
  { key:"skillsMatch",    label:"Skills Match" },
  { key:"seniorityMatch", label:"Seniority" },
  { key:"locationFit",    label:"Location Fit" },
  { key:"companyAppeal",  label:"Company Appeal" },
];

const COMMON_QA = [
  "Tell me about yourself",
  "Why are you looking for a new job?",
  "What are your salary expectations?",
  "What is your notice period / availability?",
  "Describe your greatest professional achievement",
  "Why do you want to work here?",
  "What are your strengths and weaknesses?",
];

// Investment banks active in Canada / Montreal
const INVESTMENT_BANKS = [
  "RBC Capital Markets", "TD Securities", "BMO Capital Markets",
  "Scotia Capital", "CIBC Capital Markets", "National Bank Financial",
  "Goldman Sachs Canada", "Morgan Stanley Canada", "J.P. Morgan Canada",
  "Desjardins Capital Markets", "Laurentian Bank Securities",
  "Canaccord Genuity", "Raymond James Canada",
];

// Search sources — each maps to a dedicated server endpoint
const SEARCH_SOURCES = [
  { id: "linkedin", name: "Remotive",          icon: "🌍", cls: "src-linkedin", endpoint: "/api/search/linkedin" },
  { id: "indeed",   name: "Indeed Canada",     icon: "🔎", cls: "src-indeed",   endpoint: "/api/search/indeed"   },
  { id: "hiring",   name: "The Muse / Jobicy", icon: "🌐", cls: "src-hiring",   endpoint: "/api/search/hiring"   },
  { id: "banks",    name: "Investment Banks",  icon: "🏦", cls: "src-bank",     endpoint: "/api/search/banks"    },
];

// ─── Agents ────────────────────────────────────────────────────────────────

function filterRealJobs(jobs) {
  const bad = ["no current job", "no job posting", "no results found", "could not find", "no matching", "no open position"];
  return jobs.filter(j => !bad.some(p => (j.title||"").toLowerCase().includes(p)));
}

// On-demand per-job evaluation (Haiku on server — cheap)
async function onDemandEvaluate(job, profile) {
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;
  const res = await fetch("/api/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify({ job, profile }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw Object.assign(new Error(err.error?.message || "Eval failed"), { code: err.error?.message });
  }
  return res.json();
}

// Profile-based job recommendations (Haiku on server — cheap)
async function fetchRecommendations(profile) {
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;
  const res = await fetch("/api/recommendations", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify({ profile }),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.recommendations || [];
}

// Each source calls its own server endpoint (real APIs, no Claude for fetching)
async function agentSearchSource(source, query, location) {
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;
  const res = await fetch(source.endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify({ query, location }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw Object.assign(new Error(err.error?.message || "Search failed"), { code: err.error?.message });
  }
  const data = await res.json();
  return filterRealJobs(data.jobs || []).map(j => ({ ...j, source: source.id, sourceLabel: source.name, sourceCls: source.cls }));
}

async function agentEvaluate(job, profile, authedFetch) {
  // Build a rich experience summary from accomplishments
  const experienceSummary = (profile.experience||[]).slice(0,3).map(e =>
    `${e.role} at ${e.company} (${e.period||""}):\n${(e.accomplishments||[]).map(a=>`  - ${a}`).join("\n")}`
  ).join("\n\n");

  const titles = (profile.targetTitles||[]).length > 0
    ? profile.targetTitles.join(", ")
    : (profile.title || "not set");

  const p = `Target roles: ${titles}
Location: ${profile.location||"not set"}
Skills: ${(profile.skills||[]).join(", ")||"none"}
Summary: ${profile.summary||"not provided"}
${experienceSummary ? `\nWork experience & accomplishments:\n${experienceSummary}` : ""}`.trim();

  const j = `Title: ${job.title}\nCompany: ${job.company}\nLocation: ${job.location}\nDescription: ${job.description}`;
  const d = await authedFetch({
    action: "evaluate",
    model: "claude-sonnet-4-20250514",
    max_tokens: 1000,
    system: "You are an expert recruiter. Evaluate the candidate's fit based on their full background including specific accomplishments, not just skills. Return only valid raw JSON, no markdown.",
    messages: [{ role:"user", content:`Evaluate candidate vs job.\nCANDIDATE:\n${p}\n\nJOB:\n${j}\n\nReturn ONLY JSON: {overall,roleFit,skillsMatch,seniorityMatch,locationFit,companyAppeal,summary} — integers 1-5, summary is one sentence explaining the match.` }],
  });
  const text = d.content.filter(b=>b.type==="text").map(b=>b.text).join("");
  return JSON.parse(text.replace(/```json|```/g,"").trim());
}

async function agentParseResume(base64, mediaType, authedFetch) {
  const block = mediaType.startsWith("image/")
    ? { type:"image", source:{type:"base64", media_type:mediaType, data:base64} }
    : { type:"document", source:{type:"base64", media_type:"application/pdf", data:base64} };
  const d = await authedFetch({
    action: "parse",
    model: "claude-sonnet-4-20250514",
    max_tokens: 2000,
    system: `Extract resume data. Return ONLY a JSON object with these exact fields:
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "location": "string",
  "title": "string (most recent job title)",
  "summary": "string (professional summary or generate one from the resume)",
  "skills": ["array", "of", "technical", "skills"],
  "experience": [
    {
      "company": "string",
      "role": "string",
      "period": "string",
      "accomplishments": ["bullet point 1", "bullet point 2"]
    }
  ]
}
No markdown, no explanation, raw JSON only.`,
    messages: [{ role:"user", content:[block,{type:"text",text:"Extract the full resume data as JSON including all experience and accomplishments."}] }],
  });
  const text = d.content.map(b=>b.text||"").join("");
  return JSON.parse(text.replace(/```json|```/g,"").trim());
}

async function agentCoverLetter(profile, jobInfo, tone, authedFetch) {
  const titles = (profile.targetTitles||[]).join(", ") || profile.title || "";
  const topAccomplishments = (profile.experience||[]).slice(0,2).flatMap(e=>
    (e.accomplishments||[]).slice(0,2).map(a=>`[${e.role} @ ${e.company}] ${a}`)
  ).join("\n");

  const p = `Name: ${profile.name||""}
Target roles: ${titles}
Location: ${profile.location||""}
Summary: ${profile.summary||""}
Skills: ${(profile.skills||[]).join(", ")}
${topAccomplishments ? `Key accomplishments:\n${topAccomplishments}` : ""}`.trim();

  const d = await authedFetch({
    action: "cover",
    model: "claude-sonnet-4-20250514",
    max_tokens: 1000,
    messages: [{ role:"user", content:`Write a ${tone} cover letter.\nCANDIDATE:\n${p}\n\nJOB:\n${jobInfo}\n\n3-4 paragraphs. Reference specific accomplishments where relevant. No placeholder brackets.` }],
  });
  return d.content.filter(b=>b.type==="text").map(b=>b.text).join("\n");
}

// ─── Deduplication ─────────────────────────────────────────────────────────

function dedupeJobs(jobs) {
  const seen = new Set();
  return jobs.filter(j => {
    const key = `${j.title?.toLowerCase().trim()}::${j.company?.toLowerCase().trim()}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// ─── UI Components ─────────────────────────────────────────────────────────

function ScoreCircle({ score, size=44 }) {
  const cls = score ? `s${score}` : "pending";
  return <div className={`score-circle ${cls}`} style={{width:size,height:size,fontSize:score?size*0.36:11}}>{score||"—"}</div>;
}

function ScoreBreakdown({ ev }) {
  if (!ev) return null;
  return (
    <div className="score-breakdown">
      <div className="score-breakdown-title">🧠 Evaluator Agent — Match Breakdown</div>
      {EVAL_CRITERIA.map(c=>(
        <div className="criteria-row" key={c.key}>
          <span className="criteria-name">{c.label}</span>
          <div className="criteria-bar-wrap"><div className={`criteria-bar bar-${ev[c.key]||1}`} style={{width:`${(ev[c.key]||0)*20}%`}}/></div>
          <span className={`criteria-score cs-${ev[c.key]}`}>{ev[c.key]}/5</span>
        </div>
      ))}
      {ev.summary && <div className="eval-summary">"{ev.summary}"</div>}
    </div>
  );
}

function SourceBadge({ job }) {
  return <span className={`source-badge ${job.sourceCls||"src-other"}`}>{job.sourceLabel||"Web"}</span>;
}

/** Multi-section pipeline for parallel search agents */
function Pipeline({ searchSteps, evalStep }) {
  return (
    <div className="pipeline">
      <div className="pipeline-section">
        <div className="pipeline-section-title">Search Agents (parallel)</div>
        {searchSteps.map(s=>(
          <div className="agent-step" key={s.id} style={{marginBottom:4}}>
            <div className={`agent-dot ${s.status}`}>{s.icon}</div>
            <div>
              <div className="agent-name">{s.name}</div>
              <div className={`agent-status ${s.status}`}>{s.label}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="pipeline-arrow">→</div>
      <div className="pipeline-section">
        <div className="pipeline-section-title">Evaluator Agent</div>
        <div className="agent-step">
          <div className={`agent-dot ${evalStep.status}`}>{evalStep.icon}</div>
          <div>
            <div className="agent-name">{evalStep.name}</div>
            <div className={`agent-status ${evalStep.status}`}>{evalStep.label}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Toast({ msg, onDone }) {
  useEffect(()=>{const t=setTimeout(onDone,3000);return()=>clearTimeout(t);},[]);
  return <div className="toast"><div className="status-dot"/>{msg}</div>;
}

function AddJobModal({ onClose, onAdd }) {
  const [f,setF]=useState({title:"",company:"",location:"",url:"",notes:""});
  const s=k=>e=>setF(p=>({...p,[k]:e.target.value}));
  return (
    <div className="modal-backdrop" onClick={e=>e.target===e.currentTarget&&onClose()}>
      <div className="modal">
        <div className="modal-title">Add Job to Tracker</div>
        <div className="modal-sub">Manually track a position</div>
        <div className="form-grid">
          <div className="form-group"><label>Job Title</label><input value={f.title} onChange={s("title")} placeholder="Software Engineer"/></div>
          <div className="form-group"><label>Company</label><input value={f.company} onChange={s("company")} placeholder="Acme Corp"/></div>
          <div className="form-group"><label>Location</label><input value={f.location} onChange={s("location")} placeholder="Montreal / Remote"/></div>
          <div className="form-group"><label>URL</label><input value={f.url} onChange={s("url")} placeholder="https://..."/></div>
          <div className="form-group full"><label>Notes</label><textarea value={f.notes} onChange={s("notes")} placeholder="Anything to remember..."/></div>
        </div>
        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn" onClick={()=>{if(f.title){onAdd(f);onClose();}}}>Add Job</button>
        </div>
      </div>
    </div>
  );
}

// ─── Profile Tab ───────────────────────────────────────────────────────────

function ProfileTab({ profile, setProfile, toast, authedFetch, onSearchWithQuery }) {
  const fileRef=useRef();
  const [parsing,setParsing]=useState(false);
  const [newSkill,setNewSkill]=useState("");
  const [recs,setRecs]=useState([]);
  const [loadingRecs,setLoadingRecs]=useState(false);
  const set=k=>e=>setProfile(p=>({...p,[k]:e.target.value}));

  const handleFile=async file=>{
    if(!file)return;
    setParsing(true);
    try{
      const base64=await new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res(r.result.split(",")[1]);r.onerror=rej;r.readAsDataURL(file);});
      const parsed=await agentParseResume(base64,file.type,authedFetch);
      const newProf={...profile,name:parsed.name||profile.name,email:parsed.email||profile.email,phone:parsed.phone||profile.phone,location:parsed.location||profile.location,title:parsed.title||profile.title,summary:parsed.summary||profile.summary,skills:parsed.skills?.length?parsed.skills:profile.skills,experience:parsed.experience?.length?parsed.experience:profile.experience,resumeFileName:file.name};
      setProfile(newProf);
      toast("✅ Resume parsed! Generating role recommendations…");
      setLoadingRecs(true);
      try{ const r=await fetchRecommendations(newProf); setRecs(r); }catch{}
      setLoadingRecs(false);
    }catch(e){console.error(e);toast("⚠️ Could not parse resume. Fill in manually.");}
    setParsing(false);
  };

  const addSkill=()=>{const s=newSkill.trim();if(s&&!(profile.skills||[]).includes(s)){setProfile(p=>({...p,skills:[...(p.skills||[]),s]}));setNewSkill("");}};

  return (
    <div>
      <div className="section-title">Your Profile</div>
      <div className="section-sub">Upload your resume — AI extracts your skills and experience, then recommends matching roles</div>

      {!profile.resumeFileName?(
        <div className="upload-zone" onClick={()=>fileRef.current.click()} onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();handleFile(e.dataTransfer.files[0]);}}>
          <input ref={fileRef} type="file" accept=".pdf,.png,.jpg,.jpeg" style={{display:"none"}} onChange={e=>handleFile(e.target.files[0])}/>
          {parsing?<div className="loading-state"><div className="spinner"/>Parser Agent reading your resume…</div>:<><div className="upload-icon">📄</div><div className="upload-text"><strong>Click or drag</strong> your resume here</div><div className="upload-text" style={{marginTop:4,fontSize:12}}>PDF or image accepted</div></>}
        </div>
      ):(
        <div className="card" style={{display:"flex",alignItems:"center",justifyContent:"space-between"}}>
          <div style={{display:"flex",alignItems:"center",gap:12}}>
            <span style={{fontSize:24}}>📄</span>
            <div><div style={{fontSize:14,color:"#e8e4dc"}}>{profile.resumeFileName}</div><div style={{fontSize:12,color:"#6b7280"}}>On file · {(profile.skills||[]).length} skills · {(profile.experience||[]).length} positions extracted</div></div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={()=>fileRef.current.click()}>Replace</button>
          <input ref={fileRef} type="file" accept=".pdf,.png,.jpg,.jpeg" style={{display:"none"}} onChange={e=>handleFile(e.target.files[0])}/>
        </div>
      )}

      {(recs.length>0||loadingRecs)&&(
        <div className="card" style={{marginTop:16}}>
          <div className="card-title">🎯 Recommended Positions <span style={{color:"#4b5563",fontWeight:400,fontSize:11}}>— based on your profile</span></div>
          {loadingRecs?<div className="loading-state"><div className="spinner"/>Generating recommendations…</div>:(
            <>
              <div style={{color:"#6b7280",fontSize:13,marginBottom:14}}>Click any role to search for it immediately</div>
              <div className="rec-grid">
                {recs.map((r,i)=>(
                  <div key={i} className={`rec-card${r.stretch?" stretch":""}`}>
                    {r.stretch&&<div className="rec-stretch">✦ Stretch role</div>}
                    <div className="rec-title">{r.title}</div>
                    <div className="rec-reason">{r.reason}</div>
                    <button className="btn btn-ghost btn-sm" style={{marginTop:8,fontSize:11,alignSelf:"flex-start"}} onClick={()=>onSearchWithQuery&&onSearchWithQuery(r.title)}>Search this role →</button>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      <div className="card" style={{marginTop:16}}>
        <div className="card-title">Basic Info</div>
        <div className="form-grid">
          <div className="form-group"><label>Full Name</label><input value={profile.name||""} onChange={set("name")} placeholder="Angel Pino"/></div>
          <div className="form-group"><label>Email</label><input value={profile.email||""} onChange={set("email")} placeholder="you@email.com"/></div>
          <div className="form-group"><label>Phone</label><input value={profile.phone||""} onChange={set("phone")} placeholder="+1 514 555 0100"/></div>
          <div className="form-group"><label>Location</label><input value={profile.location||""} onChange={set("location")} placeholder="Montreal, QC"/></div>
          <div className="form-group"><label>LinkedIn URL</label><input value={profile.linkedin||""} onChange={set("linkedin")} placeholder="linkedin.com/in/your-profile"/></div>
          <div className="form-group full"><label>Professional Summary</label><textarea rows={4} value={profile.summary||""} onChange={set("summary")} placeholder="Used by the Evaluator Agent to score your fit against each job…"/></div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Skills <span style={{color:"#4b5563",fontWeight:400,fontSize:11}}>— used by Evaluator Agent</span></div>
        <div style={{display:"flex",gap:8,marginBottom:8}}>
          <input value={newSkill} onChange={e=>setNewSkill(e.target.value)} onKeyDown={e=>e.key==="Enter"&&addSkill()} placeholder="Add a skill and press Enter…" style={{flex:1}}/>
          <button className="btn" onClick={addSkill}>Add</button>
        </div>
        <div className="tags-wrap">
          {(profile.skills||[]).map(sk=><span className="tag" key={sk}>{sk}<span className="tag-remove" onClick={()=>setProfile(p=>({...p,skills:p.skills.filter(s=>s!==sk)}))}>×</span></span>)}
          {!(profile.skills||[]).length&&<span style={{color:"#4b5563",fontSize:13}}>No skills yet</span>}
        </div>
      </div>

      {(profile.experience||[]).length>0&&(
        <div className="card">
          <div className="card-title">Experience & Accomplishments <span style={{color:"#4b5563",fontWeight:400,fontSize:11}}>— Evaluator reads these for scoring</span></div>
          {(profile.experience||[]).map((exp,ei)=>(
            <div key={ei} style={{marginBottom:20,paddingBottom:20,borderBottom:ei<(profile.experience.length-1)?"1px solid #1e2330":"none"}}>
              <div style={{marginBottom:8}}><div style={{fontSize:14,color:"#e8e4dc",fontWeight:600}}>{exp.role}</div><div style={{fontSize:13,color:"#c8a96e"}}>{exp.company}{exp.period&&<span style={{color:"#4b5563",fontWeight:400}}> · {exp.period}</span>}</div></div>
              {(exp.accomplishments||[]).map((acc,ai)=>(
                <div key={ai} style={{display:"flex",gap:8,marginBottom:6,alignItems:"flex-start"}}>
                  <span style={{color:"#c8a96e",fontSize:12,marginTop:3,flexShrink:0}}>•</span>
                  <textarea rows={2} value={acc} onChange={e=>{const u=[...profile.experience];u[ei]={...u[ei],accomplishments:u[ei].accomplishments.map((a,i)=>i===ai?e.target.value:a)};setProfile(p=>({...p,experience:u}));}} style={{flex:1,fontSize:13,lineHeight:1.5,minHeight:"auto"}}/>
                  <button onClick={()=>{const u=[...profile.experience];u[ei]={...u[ei],accomplishments:u[ei].accomplishments.filter((_,i)=>i!==ai)};setProfile(p=>({...p,experience:u}));}} style={{background:"none",border:"none",color:"#4b5563",cursor:"pointer",fontSize:16,flexShrink:0,padding:"2px 4px"}}>×</button>
                </div>
              ))}
              <button onClick={()=>{const u=[...profile.experience];u[ei]={...u[ei],accomplishments:[...(u[ei].accomplishments||[]),""]};setProfile(p=>({...p,experience:u}));}} className="btn btn-ghost btn-sm" style={{marginTop:4,fontSize:11}}>+ Add bullet</button>
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <div className="card-title">Common Interview Answers</div>
        <div style={{color:"#6b7280",fontSize:13,marginBottom:16}}>Pre-write once — copy into any application form</div>
        {COMMON_QA.map(q=>(
          <div className="qa-item" key={q}>
            <div className="qa-question">{q}</div>
            <textarea rows={3} value={(profile.qa||{})[q]||""} onChange={e=>setProfile(p=>({...p,qa:{...p.qa,[q]:e.target.value}}))} placeholder="Your answer…"/>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Search Tab ────────────────────────────────────────────────────────────

function SearchTab({ profile, applications, setApplications, toast, isPro, onUpgrade, onSearchComplete, authedFetch, initialQuery }) {
  const [query,setQuery]=useState(initialQuery||"");
  const [location,setLocation]=useState(profile.location||"Montreal");
  const [results,setResults]=useState([]);
  const [expanded,setExpanded]=useState(null);
  const [srcFilter,setSrcFilter]=useState("all");
  const [evaluating,setEvaluating]=useState({}); // jobId → true/false

  // Update query when initialQuery changes (from profile recommendations)
  useEffect(()=>{ if(initialQuery) setQuery(initialQuery); },[initialQuery]);

  const activeSources = isPro ? SEARCH_SOURCES : SEARCH_SOURCES.filter(s=>s.id==="indeed");
  const initSearchSteps = () => activeSources.map(s=>({...s, status:"idle", label:"Waiting"}));
  const [searchSteps,setSearchSteps]=useState(initSearchSteps());

  const updSearch=(id,patch)=>setSearchSteps(s=>s.map(x=>x.id===id?{...x,...patch}:x));
  const busy = searchSteps.some(s=>s.status==="running");
  const profileReady = !!(profile.title || profile.skills?.length || profile.summary);

  // Per-job on-demand evaluation
  const evaluateJob = async (jobId) => {
    if (!isPro) { onUpgrade(); return; }
    const job = results.find(j=>j.id===jobId);
    if (!job || job.evalScore) return;
    setEvaluating(e=>({...e,[jobId]:true}));
    try {
      const ev = await onDemandEvaluate(job, profile);
      setResults(r=>r.map(j=>j.id===jobId?{...j,evalScore:ev.overall,evalData:ev}:j));
    } catch(e) {
      console.error("Eval error:", e.message);
      toast("⚠️ Could not evaluate this job. Try again.");
    }
    setEvaluating(e=>({...e,[jobId]:false}));
  };

  const runSearch = async () => {
    if (!query||busy) return;
    setResults([]); setExpanded(null);
    setSearchSteps(initSearchSteps().map(s=>({...s,status:"idle",label:"Waiting"})));
    activeSources.forEach(s=>updSearch(s.id,{status:"running",label:"Searching…"}));

    const searchResults = await Promise.allSettled(
      activeSources.map(async source => {
        try {
          const jobs = await agentSearchSource(source, query, location);
          updSearch(source.id,{status:"done",label:`Found ${jobs.length}`});
          return jobs;
        } catch(err) {
          console.error(`[${source.name}]`, err.message);
          if (err.code==="searches_exhausted") { updSearch(source.id,{status:"error",label:"Limit reached"}); onUpgrade(); }
          else updSearch(source.id,{status:"error",label:"No results"});
          return [];
        }
      })
    );

    let allJobs = searchResults.flatMap(r=>r.status==="fulfilled"?r.value:[]);
    allJobs = dedupeJobs(allJobs);
    allJobs = allJobs.map((j,i)=>({...j,id:`j-${Date.now()}-${i}`,evalScore:null,evalData:null}));
    setResults(allJobs);
    if (onSearchComplete) onSearchComplete();
  };

  const saveJob = job => {
    if (applications.find(a=>a.title===job.title&&a.company===job.company)){toast("Already tracked");return;}
    setApplications(a=>[...a,{...job,status:"saved",added:new Date().toLocaleDateString()}]);
    toast("💾 Saved to tracker!");
  };

  const filtered = results.filter(j=>srcFilter==="all"||j.source===srcFilter);
  const sourceCount = src => results.filter(j=>j.source===src).length;

  return (
    <div>
      <div className="section-title">Search Jobs</div>
      <div className="section-sub">{isPro ? "4 sources in parallel — click ⚡ Evaluate on any job to score it against your profile" : "Free: Indeed Canada only, 5 searches/month — upgrade for all sources + Evaluator Agent"}</div>

      {!isPro&&(
        <div style={{background:"#1a1710",border:"1px solid #c8a96e40",borderRadius:10,padding:"12px 16px",marginBottom:20,display:"flex",alignItems:"center",justifyContent:"space-between",gap:12}}>
          <div style={{fontSize:13,color:"#c8a96e"}}>🔒 Free plan — Indeed only · Upgrade for Remotive, The Muse, Jobicy, Investment Banks + Evaluator</div>
          <button className="btn btn-sm" onClick={onUpgrade} style={{flexShrink:0}}>Upgrade to Pro</button>
        </div>
      )}

      <div className="pipeline" style={{flexWrap:"wrap",gap:8,marginBottom:20}}>
        {searchSteps.map(s=>(
          <div key={s.id} className="agent-step" style={{padding:"0 8px"}}>
            <div className={`agent-dot ${s.status}`}>{s.icon}</div>
            <div><div className="agent-name">{s.name}</div><div className={`agent-status ${s.status}`}>{s.label}</div></div>
          </div>
        ))}
      </div>

      <div className="search-row">
        <input value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>e.key==="Enter"&&runSearch()} placeholder='"Analytics Manager" OR "Data Lead" OR "Head of Data"' style={{flex:2}}/>
        <input value={location} onChange={e=>setLocation(e.target.value)} onKeyDown={e=>e.key==="Enter"&&runSearch()} placeholder="Montreal / Remote Canada" style={{flex:1}}/>
        <button className="btn" onClick={runSearch} disabled={!query||busy}>
          {busy?<><div className="spinner"/>Searching</>:"🔍 Search All Sources"}
        </button>
      </div>
      <div style={{fontSize:12,color:"#4b5563",marginBottom:16,marginTop:-8}}>
        💡 Use <strong style={{color:"#6b7280"}}>OR</strong> for multiple roles — e.g. <em>"Analytics Manager" OR "Senior Data Analyst" OR "Head of Analytics"</em>
      </div>

      {results.length>0&&(
        <div className="filter-row">
          <span className="filter-label">Source:</span>
          <button className={`filter-btn${srcFilter==="all"?" active":""}`} onClick={()=>setSrcFilter("all")}>All ({results.length})</button>
          {SEARCH_SOURCES.map(s=><button key={s.id} className={`filter-btn${srcFilter===s.id?" active":""}`} onClick={()=>setSrcFilter(s.id)}>{s.icon} {s.name} ({sourceCount(s.id)})</button>)}
          <span className="results-count">{filtered.length} shown</span>
        </div>
      )}

      {filtered.length===0&&results.length===0&&<div className="empty"><div className="empty-icon">🔍</div><div className="empty-text">Search to see results from Indeed, Remotive, The Muse, Jobicy, and Investment Banks</div></div>}
      {filtered.length===0&&results.length>0&&<div className="empty"><div className="empty-icon">🔎</div><div className="empty-text">No results match your filter</div></div>}

      {filtered.map(job=>(
        <div className={`job-card${job.evalScore?` score-${job.evalScore}`:""}`} key={job.id} onClick={()=>setExpanded(expanded===job.id?null:job.id)}>
          <div className="job-card-header">
            <div style={{flex:1}}>
              <div className="job-title">{job.title}</div>
              <div className="job-company">{job.company}</div>
              <div className="job-meta">
                <SourceBadge job={job}/>
                {job.location&&<span>📍 {job.location}</span>}
                {job.salary&&<span>💰 {job.salary}</span>}
                {job.posted&&<span>🕐 {job.posted}</span>}
              </div>
            </div>
            <div className="score-badge">
              {job.evalScore
                ?<><ScoreCircle score={job.evalScore}/><span className="score-label">Match</span></>
                :<button className="eval-btn" onClick={e=>{e.stopPropagation();evaluateJob(job.id);}} disabled={evaluating[job.id]||!profileReady} title={!isPro?"Pro feature":!profileReady?"Fill in your profile first":"Score this job against your profile"}>
                  {evaluating[job.id]?<><div className="spinner"/>Scoring…</>:<>⚡ {isPro?"Evaluate":"Pro"}</>}
                </button>
              }
            </div>
          </div>
          {expanded===job.id&&(
            <>
              <div className="job-desc">{job.description}</div>
              {job.evalData&&<ScoreBreakdown ev={job.evalData}/>}
              <div className="job-actions">
                <button className="btn btn-sm" onClick={e=>{e.stopPropagation();saveJob(job);}}>💾 Save to Tracker</button>
                {job.url&&<a href={job.url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm" onClick={e=>e.stopPropagation()}>🔗 Open Listing</a>}
              </div>
            </>
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Tracker Tab ───────────────────────────────────────────────────────────

function TrackerTab({ applications, setApplications, toast }) {
  const [showAdd,setShowAdd]=useState(false);
  const [sel,setSel]=useState(null);
  const job=applications.find(a=>a.id===sel);

  return (
    <div>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:6}}>
        <div className="section-title">Application Tracker</div>
        <button className="btn" onClick={()=>setShowAdd(true)}>+ Add Job</button>
      </div>
      <div className="section-sub">{applications.length} job{applications.length!==1?"s":""} tracked — Evaluator scores shown on cards</div>

      {applications.length===0
        ?<div className="empty"><div className="empty-icon">📋</div><div className="empty-text">No applications yet — search for jobs or add manually</div></div>
        :<div className="tracker-grid">
          {STATUS_COLS.map(col=>{
            const jobs=applications.filter(a=>a.status===col.id);
            return (
              <div className="tracker-col" key={col.id}>
                <div className="col-header"><span className={`col-title ${col.cls}`}>{col.label}</span><span className="col-count">{jobs.length}</span></div>
                {jobs.map(j=>(
                  <div className={`tracker-item${j.evalScore?` ts${j.evalScore}`:""}`} key={j.id} onClick={()=>setSel(j.id)}>
                    <div className="tracker-item-title">{j.title}</div>
                    <div className="tracker-item-company">{j.company}</div>
                    {j.source&&<div style={{marginTop:4}}><SourceBadge job={j}/></div>}
                    {j.evalScore&&<div className={`tracker-score cs-${j.evalScore}`}>{"★".repeat(j.evalScore)}{"☆".repeat(5-j.evalScore)}</div>}
                    <div className="tracker-item-date">{j.added}</div>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      }

      {showAdd&&<AddJobModal onClose={()=>setShowAdd(false)} onAdd={j=>{setApplications(a=>[...a,{...j,id:`m-${Date.now()}`,status:"saved",added:new Date().toLocaleDateString()}]);toast("✅ Added!");}}/>}

      {job&&(
        <div className="modal-backdrop" onClick={e=>e.target===e.currentTarget&&setSel(null)}>
          <div className="modal">
            <div className="modal-title">{job.title}</div>
            <div style={{color:"#c8a96e",marginBottom:8}}>{job.company}</div>
            {job.source&&<div style={{marginBottom:12}}><SourceBadge job={job}/></div>}
            {job.evalScore&&<div style={{display:"flex",alignItems:"center",gap:12,marginBottom:12}}><ScoreCircle score={job.evalScore} size={36}/><span style={{fontSize:13,color:"#6b7280"}}>Evaluator Agent match score</span></div>}
            {job.evalData&&<ScoreBreakdown ev={job.evalData}/>}
            <hr className="divider"/>
            <div style={{marginBottom:12}}>
              <label style={{display:"block",marginBottom:8}}>Status</label>
              <div style={{display:"flex",flexWrap:"wrap",gap:8}}>
                {STATUS_COLS.map(c=><button key={c.id} className={`btn btn-ghost btn-sm ${c.cls}`} style={job.status===c.id?{borderColor:"currentColor"}:{}} onClick={()=>setApplications(a=>a.map(x=>x.id===sel?{...x,status:c.id}:x))}>{c.label}</button>)}
              </div>
            </div>
            {job.url&&<a href={job.url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm" style={{marginBottom:8,display:"inline-flex"}}>🔗 Open Listing</a>}
            <div className="modal-actions">
              <button className="btn btn-danger btn-sm" onClick={()=>{setApplications(a=>a.filter(x=>x.id!==sel));setSel(null);toast("Removed");}}>Remove</button>
              <button className="btn btn-ghost" onClick={()=>setSel(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Cover Letters Tab ─────────────────────────────────────────────────────

function CoverTab({ profile, applications, toast, isPro, onUpgrade, authedFetch }) {
  const [jobDesc,setJobDesc]=useState("");
  const [selApp,setSelApp]=useState("");
  const [tone,setTone]=useState("professional");
  const [letter,setLetter]=useState("");
  const [loading,setLoading]=useState(false);

  if (!isPro) return <UpgradeWall reason="cover" onUpgrade={onUpgrade}/>;

  const generate=async()=>{
    if(!jobDesc&&!selApp)return;
    setLoading(true);setLetter("");
    try{
      const app=applications.find(a=>a.id===selApp);
      const jobInfo=app?`${app.title} at ${app.company}. ${app.description||""}`:jobDesc;
      setLetter(await agentCoverLetter(profile,jobInfo,tone,authedFetch));
    }catch{toast("⚠️ Generation failed.");}
    setLoading(false);
  };

  return (
    <div>
      <div className="section-title">Cover Letters</div>
      <div className="section-sub">Cover Letter Agent writes a tailored letter using your profile + job details</div>
      <div className="card">
        <div className="card-title">Generate</div>
        <div className="form-grid">
          <div className="form-group full">
            <label>Pick from Tracker (optional)</label>
            <select value={selApp} onChange={e=>setSelApp(e.target.value)}>
              <option value="">— Select a tracked job —</option>
              {applications.map(a=><option key={a.id} value={a.id}>{a.title} at {a.company}{a.evalScore?` — ${a.evalScore}/5`:""}</option>)}
            </select>
          </div>
          <div className="form-group full"><label>Or paste job description</label><textarea rows={5} value={jobDesc} onChange={e=>setJobDesc(e.target.value)} placeholder="Paste job description here…"/></div>
          <div className="form-group">
            <label>Tone</label>
            <select value={tone} onChange={e=>setTone(e.target.value)}>
              <option value="professional">Professional & Formal</option>
              <option value="confident and conversational">Confident & Conversational</option>
              <option value="enthusiastic and energetic">Enthusiastic & Energetic</option>
              <option value="concise and direct">Concise & Direct</option>
            </select>
          </div>
        </div>
        <div style={{marginTop:16}}>
          <button className="btn" onClick={generate} disabled={loading||(!jobDesc&&!selApp)}>
            {loading?<><div className="spinner"/>Cover Letter Agent working…</>:"✨ Generate Cover Letter"}
          </button>
        </div>
      </div>
      {letter&&(
        <div className="card">
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:16}}>
            <div className="card-title" style={{margin:0}}>Your Cover Letter</div>
            <button className="btn btn-ghost btn-sm" onClick={()=>{navigator.clipboard.writeText(letter);toast("📋 Copied!");}}>📋 Copy</button>
          </div>
          <div className="cover-letter-text">{letter}</div>
        </div>
      )}
      {!letter&&!loading&&<div className="empty"><div className="empty-icon">✉️</div><div className="empty-text">Your generated cover letter will appear here</div></div>}
    </div>
  );
}

// ─── API helper (attaches auth token) ─────────────────────────────────────

async function authedFetch(body) {
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;
  const res = await fetch("/api/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify(body),
  });
  const d = await res.json();
  if (d.error) throw Object.assign(new Error(d.error.message), { code: d.error.message, plan: d.error.plan });
  return d;
}

// ─── Root ──────────────────────────────────────────────────────────────────

export default function App() {
  const { user, profile: userPlan, loading: authLoading, signOut, isPro } = useAuth();
  const [tab,setTab]               = useState("profile");
  const [profile,setProfile]       = useState({skills:[],qa:{}});
  const [applications,setApplications] = useState([]);
  const [toastMsg,setToastMsg]     = useState(null);
  const [initialQuery,setInitialQuery] = useState(""); // cross-tab: profile → search
  const [page, setPage]            = useState(() => {
    const path = window.location.pathname;
    if (path === "/success") return "success";
    if (path === "/account") return "account";
    return "app";
  });
  const [usage,setUsage] = useState(null);
  const toast = msg => { setToastMsg(null); setTimeout(()=>setToastMsg(msg), 10); };

  // Navigate to Search tab with a pre-filled query (called from Profile recommendations)
  const searchWithQuery = (query) => {
    setInitialQuery(query);
    setTab("search");
  };

  const storageKey = k => user ? `ea:${user.id}:${k}` : null;

  useEffect(()=>{
    if (!user) return;
    try{const p=localStorage.getItem(storageKey("profile"));if(p)setProfile(JSON.parse(p));}catch{}
    try{const a=localStorage.getItem(storageKey("apps"));if(a)setApplications(JSON.parse(a));}catch{}
  },[user?.id]);

  useEffect(()=>{ if(user) try{localStorage.setItem(storageKey("profile"),JSON.stringify(profile));}catch{} },[profile]);
  useEffect(()=>{ if(user) try{localStorage.setItem(storageKey("apps"),JSON.stringify(applications));}catch{} },[applications]);

  const refreshUsage = async () => {
    if (!user) return;
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const res = await fetch("/api/usage", { headers: { Authorization: `Bearer ${session?.access_token}` } });
      setUsage(await res.json());
    } catch {}
  };

  useEffect(()=>{ if(user) refreshUsage(); },[user?.id, isPro]);

  useEffect(()=>{
    const paths = { app: "/", success: "/success", account: "/account", pricing: "/pricing" };
    window.history.replaceState(null, "", paths[page] || "/");
  },[page]);

  if (authLoading) {
    return (
      <>
        <style>{css}</style>
        <div style={{minHeight:"100vh",background:"#0d0f14",display:"flex",alignItems:"center",justifyContent:"center"}}>
          <div className="spinner" style={{width:28,height:28,borderWidth:3}}/>
        </div>
      </>
    );
  }

  if (!user)                return <LoginPage />;
  if (page === "success")   return <SuccessPage onContinue={() => setPage("app")} />;
  if (page === "account")   return <AccountPage onBack={() => setPage("app")} onUpgrade={() => setPage("pricing")} />;
  if (page === "pricing")   return <PricingPage onContinueFree={() => setPage("app")} />;

  const searchesLeft = usage?.searches_remaining;

  return (
    <>
      <style>{css}</style>
      <div className="app">
        <div className="topbar">
          <div className="logo">apply by <span>etlyx</span></div>
          <nav className="nav">
            {TABS.map(t=><button key={t.id} className={`nav-btn${tab===t.id?" active":""}`} onClick={()=>setTab(t.id)}>{t.icon} {t.label}</button>)}
          </nav>
          <div style={{display:"flex",alignItems:"center",gap:10}}>
            {isPro
              ? <span style={{fontSize:11,fontWeight:700,textTransform:"uppercase",letterSpacing:"0.8px",color:"#c8a96e",background:"#1a1710",border:"1px solid #c8a96e40",padding:"3px 10px",borderRadius:20}}>Pro</span>
              : <button onClick={()=>setPage("pricing")} style={{fontSize:11,fontWeight:600,color:"#6b7280",background:"#111318",border:"1px solid #1e2330",padding:"4px 10px",borderRadius:20,cursor:"pointer",fontFamily:"'DM Sans',sans-serif"}}>
                  {searchesLeft != null ? `${searchesLeft} left` : "Free"} · Upgrade
                </button>
            }
            <button
              onClick={() => setPage("account")}
              style={{fontSize:12,color:"#4b5563",background:"none",border:"1px solid #1e2330",cursor:"pointer",padding:"5px 12px",borderRadius:8,fontFamily:"'DM Sans',sans-serif",transition:"all 0.15s"}}
              onMouseEnter={e=>{e.currentTarget.style.color="#e8e4dc";e.currentTarget.style.borderColor="#2a3040";}}
              onMouseLeave={e=>{e.currentTarget.style.color="#4b5563";e.currentTarget.style.borderColor="#1e2330";}}
            >Account</button>
          </div>
        </div>

        <div className="content">
          {tab==="profile" && (
            <ProfileTab
              profile={profile}
              setProfile={setProfile}
              toast={toast}
              authedFetch={authedFetch}
              onSearchWithQuery={searchWithQuery}
            />
          )}
          {tab==="search" && (
            <SearchTab
              profile={profile}
              applications={applications}
              setApplications={setApplications}
              toast={toast}
              isPro={isPro}
              onUpgrade={()=>setPage("pricing")}
              onSearchComplete={refreshUsage}
              authedFetch={authedFetch}
              initialQuery={initialQuery}
            />
          )}
          {tab==="tracker" && <TrackerTab applications={applications} setApplications={setApplications} toast={toast}/>}
          {tab==="cover" && (
            <CoverTab
              profile={profile}
              applications={applications}
              toast={toast}
              isPro={isPro}
              onUpgrade={()=>setPage("pricing")}
              authedFetch={authedFetch}
            />
          )}
        </div>
        {toastMsg&&<Toast msg={toastMsg} onDone={()=>setToastMsg(null)}/>}
      </div>
    </>
  );
}
