import express from "express";
import fetch from "node-fetch";
import dotenv from "dotenv";
import Stripe from "stripe";
import { createClient } from "@supabase/supabase-js";

dotenv.config();

const {
  ANTHROPIC_API_KEY,
  SUPABASE_URL,
  SUPABASE_SERVICE_ROLE_KEY,
  STRIPE_SECRET_KEY,
  STRIPE_WEBHOOK_SECRET,
  STRIPE_PRICE_ID,
  FRONTEND_URL = "http://localhost:5173",
} = process.env;

for (const [k, v] of Object.entries({ ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_ID })) {
  if (!v) { console.error(`❌  Missing ${k} in .env`); process.exit(1); }
}

const stripe        = new Stripe(STRIPE_SECRET_KEY);
const supabaseAdmin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

// ─── Models ───────────────────────────────────────────────────────────────────
const HAIKU  = "claude-haiku-4-5-20251001";   // evaluation, recommendations, expansion
const SONNET = "claude-sonnet-4-20250514";     // web search, resume parse, cover letters

// ─── Cache (2 hour TTL, never caches empty results) ──────────────────────────
const cache    = new Map();
const CACHE_MS = 2 * 60 * 60 * 1000;

function cacheGet(key) {
  const e = cache.get(key);
  if (!e) return null;
  if (Date.now() - e.ts > CACHE_MS) { cache.delete(key); return null; }
  return e.value;
}

function cacheSet(key, value) {
  if (Array.isArray(value) && value.length === 0) return; // never cache empty
  cache.set(key, { value, ts: Date.now() });
  if (cache.size > 500) for (const [k, v] of cache.entries()) if (Date.now() - v.ts > CACHE_MS) cache.delete(k);
}

// ─── Investment banks ─────────────────────────────────────────────────────────
const CA_BANKS = "RBC Capital Markets, TD Securities, BMO Capital Markets, Scotia Capital, CIBC Capital Markets, National Bank Financial, Desjardins Capital Markets, Laurentian Bank, Canaccord Genuity, Raymond James Canada";
const GL_BANKS = "Goldman Sachs, JPMorgan Chase, Morgan Stanley, Barclays, Deutsche Bank, UBS, HSBC, BNP Paribas, Citigroup, Jefferies, Evercore, Lazard, Nomura, Mizuho";

// ─── App setup ────────────────────────────────────────────────────────────────
const app = express();
app.use("/api/stripe/webhook", express.raw({ type: "application/json" }));
app.use(express.json({ limit: "10mb" }));

// ─── Auth middleware ──────────────────────────────────────────────────────────
async function requireAuth(req, res, next) {
  const token = req.headers.authorization?.replace("Bearer ", "");
  if (!token) return res.status(401).json({ error: { message: "Not authenticated" } });
  const { data: { user }, error } = await supabaseAdmin.auth.getUser(token);
  if (error || !user) return res.status(401).json({ error: { message: "Invalid session" } });
  const { data: profile } = await supabaseAdmin
    .from("profiles")
    .select("plan, searches_used, searches_reset_at, stripe_customer_id, stripe_sub_id")
    .eq("id", user.id).single();
  req.user    = user;
  req.profile = profile || { plan: "free", searches_used: 0 };
  next();
}

// ─── Usage ────────────────────────────────────────────────────────────────────
async function checkAndIncrementUsage(userId, profile) {
  if (profile.plan === "pro") return { allowed: true };
  const resetAt    = profile.searches_reset_at ? new Date(profile.searches_reset_at) : null;
  const now        = new Date();
  const needsReset = !resetAt || now.getFullYear() !== resetAt.getFullYear() || now.getMonth() !== resetAt.getMonth();
  if (needsReset) {
    await supabaseAdmin.from("profiles").update({ searches_used: 1, searches_reset_at: now.toISOString() }).eq("id", userId);
    return { allowed: true };
  }
  const used = profile.searches_used || 0;
  if (used >= 5) return { allowed: false };
  await supabaseAdmin.from("profiles").update({ searches_used: used + 1 }).eq("id", userId);
  return { allowed: true };
}

// ─── Claude helper ────────────────────────────────────────────────────────────
async function callClaude({ model = HAIKU, system = "", messages, useWebSearch = false, maxTokens = 800 }) {
  const body = { model, max_tokens: maxTokens, messages };
  if (system) body.system = system;
  if (useWebSearch) body.tools = [{ type: "web_search_20250305", name: "web_search" }];
  const res  = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "anthropic-beta": "web-search-2025-03-05" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error.message);
  return (data.content || []).filter(b => b.type === "text").map(b => b.text).join("");
}

function extractJSON(text, fallback = []) {
  const s = text.indexOf("["), e = text.lastIndexOf("]");
  if (s === -1 || e <= s) return fallback;
  try { const r = JSON.parse(text.slice(s, e + 1)); return Array.isArray(r) ? r : fallback; } catch { return fallback; }
}

// ─── XML helper for RSS ───────────────────────────────────────────────────────
function xmlGet(block, tag) {
  const cdata = block.match(new RegExp(`<${tag}[^>]*><!\\[CDATA\\[([\\s\\S]*?)\\]\\]><\\/${tag}>`, "i"));
  if (cdata) return cdata[1].trim();
  const plain = block.match(new RegExp(`<${tag}[^>]*>([^<]*)<\\/${tag}>`, "i"));
  return plain ? plain[1].trim() : "";
}

// ─── Job fetchers (all free, no API key) ──────────────────────────────────────

// Indeed Canada RSS — reliable, structured
async function fetchIndeed(query, location, limit = 8) {
  const cacheKey = `indeed:${query}:${location}`;
  const cached   = cacheGet(cacheKey);
  if (cached) { console.log(`[Indeed] cache hit (${cached.length})`); return cached; }

  try {
    const q   = encodeURIComponent(query);
    const loc = encodeURIComponent(location || "Montreal, QC");
    const res = await fetch(`https://ca.indeed.com/rss?q=${q}&l=${loc}&sort=date&limit=20`, {
      headers: { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36", Accept: "application/rss+xml,text/xml,*/*" },
    });
    const xml   = await res.text();
    const items = [];
    const re    = /<item>([\s\S]*?)<\/item>/gi;
    let m;
    while ((m = re.exec(xml)) !== null && items.length < limit) {
      const b       = m[1];
      const title   = xmlGet(b, "title");
      const link    = (b.match(/<link>([^<]+)<\/link>/) || [])[1] || xmlGet(b, "link");
      const company = xmlGet(b, "source");
      const pubDate = xmlGet(b, "pubDate");
      const desc    = xmlGet(b, "description").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").substring(0, 220).trim();
      const salary  = (desc.match(/\$[\d,]+(?:\s*[-–]\s*\$[\d,]+)?/i) || [])[0] || "";
      if (title && !title.toLowerCase().includes("indeed jobs")) {
        items.push({ title, company: company || "Not specified", location: location || "Montreal, QC", url: link, salary, posted: pubDate ? new Date(pubDate).toLocaleDateString("en-CA") : "", description: desc });
      }
    }
    console.log(`[Indeed] ${items.length} jobs for "${query}"`);
    cacheSet(cacheKey, items);
    return items;
  } catch (err) {
    console.error("[Indeed] error:", err.message);
    return [];
  }
}

// Remotive — remote jobs worldwide, strong in tech/analytics, free
async function fetchRemotive(query, limit = 8) {
  const cacheKey = `remotive:${query}`;
  const cached   = cacheGet(cacheKey);
  if (cached) { console.log(`[Remotive] cache hit (${cached.length})`); return cached; }

  try {
    const q   = encodeURIComponent(query);
    const res = await fetch(`https://remotive.com/api/remote-jobs?search=${q}&limit=20`, {
      headers: { "User-Agent": "Mozilla/5.0", Accept: "application/json" },
    });
    const data  = await res.json();
    const items = (data.jobs || []).slice(0, limit).map(j => ({
      title:       j.title,
      company:     j.company_name,
      location:    j.candidate_required_location || "Remote",
      url:         j.url,
      salary:      j.salary || "",
      posted:      j.publication_date ? new Date(j.publication_date).toLocaleDateString("en-CA") : "",
      description: (j.description || "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").substring(0, 220).trim(),
    }));
    console.log(`[Remotive] ${items.length} jobs for "${query}"`);
    cacheSet(cacheKey, items);
    return items;
  } catch (err) {
    console.error("[Remotive] error:", err.message);
    return [];
  }
}

// The Muse — US companies, many remote-friendly, strong for analytics/data/finance
async function fetchTheMuse(query, limit = 8) {
  const cacheKey = `muse:${query}`;
  const cached   = cacheGet(cacheKey);
  if (cached) { console.log(`[The Muse] cache hit (${cached.length})`); return cached; }

  try {
    const q   = encodeURIComponent(query);
    const res = await fetch(`https://www.themuse.com/api/public/jobs?page=0&descending=true&company_size=Large,Enterprise&query=${q}`, {
      headers: { "User-Agent": "Mozilla/5.0", Accept: "application/json" },
    });
    const data  = await res.json();
    const items = (data.results || []).slice(0, limit).map(j => ({
      title:       j.name,
      company:     j.company?.name || "Unknown",
      location:    (j.locations || [{ name: "Remote" }]).map(l => l.name).join(", "),
      url:         j.refs?.landing_page || "",
      salary:      "",
      posted:      j.publication_date ? new Date(j.publication_date).toLocaleDateString("en-CA") : "",
      description: (j.contents || "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").substring(0, 220).trim(),
    }));
    console.log(`[The Muse] ${items.length} jobs for "${query}"`);
    cacheSet(cacheKey, items);
    return items;
  } catch (err) {
    console.error("[The Muse] error:", err.message);
    return [];
  }
}

// Jobicy — remote jobs with Canada geo filter
async function fetchJobicy(query, limit = 6) {
  const cacheKey = `jobicy:${query}`;
  const cached   = cacheGet(cacheKey);
  if (cached) { console.log(`[Jobicy] cache hit (${cached.length})`); return cached; }

  try {
    const tag = encodeURIComponent(query.split(/\s+/)[0].toLowerCase());
    const res = await fetch(`https://jobicy.com/api/v0/remote-jobs?count=15&tag=${tag}&geo=canada`, {
      headers: { "User-Agent": "Mozilla/5.0", Accept: "application/json" },
    });
    const data  = await res.json();
    const items = (data.jobs || []).slice(0, limit).map(j => ({
      title:       j.jobTitle,
      company:     j.companyName,
      location:    j.jobGeo || "Remote / Canada",
      url:         j.url,
      salary:      j.annualSalaryMin ? `$${Number(j.annualSalaryMin).toLocaleString()}–$${Number(j.annualSalaryMax||0).toLocaleString()}` : "",
      posted:      j.pubDate ? new Date(j.pubDate).toLocaleDateString("en-CA") : "",
      description: (j.jobExcerpt || "").substring(0, 220),
    }));
    console.log(`[Jobicy] ${items.length} jobs for "${query}"`);
    cacheSet(cacheKey, items);
    return items;
  } catch (err) {
    console.error("[Jobicy] error:", err.message);
    return [];
  }
}

// Investment Banks — Claude Sonnet web search targeting IB career pages in two focused batches
async function fetchInvestmentBanks(query, location, limit = 8) {
  const cacheKey = `banks:${query}:${location}`;
  const cached   = cacheGet(cacheKey);
  if (cached) { console.log(`[Banks] cache hit (${cached.length})`); return cached; }

  const loc = location || "Montreal or Canada or Remote";

  const [caJobs, glJobs] = await Promise.all([
    callClaude({
      model: SONNET, maxTokens: 1200, useWebSearch: true,
      messages: [{ role: "user", content: `Search careers pages of these Canadian banks for "${query}" jobs in ${loc}: ${CA_BANKS}. Return ONLY a JSON array [ {"title":"...","company":"...","location":"...","url":"...","salary":"","posted":"","description":"2 sentences"} ]. Return [] if none found.` }],
    }).then(t => extractJSON(t)).catch(() => []),

    callClaude({
      model: SONNET, maxTokens: 1200, useWebSearch: true,
      messages: [{ role: "user", content: `Search careers pages of these global investment banks for "${query}" jobs in ${loc}: ${GL_BANKS}. Return ONLY a JSON array [ {"title":"...","company":"...","location":"...","url":"...","salary":"","posted":"","description":"2 sentences"} ]. Return [] if none found.` }],
    }).then(t => extractJSON(t)).catch(() => []),
  ]);

  const jobs = [...caJobs, ...glJobs].filter(j => j.title && j.company).slice(0, limit);
  console.log(`[Banks] ${jobs.length} jobs (${caJobs.length} CA + ${glJobs.length} GL)`);
  cacheSet(cacheKey, jobs);
  return jobs;
}

// ─── Profile recommendations (Haiku — cheap) ─────────────────────────────────
async function generateRecommendations(profile) {
  const p = `Title: ${profile.title||""}\nSkills: ${(profile.skills||[]).slice(0,15).join(", ")}\nSummary: ${(profile.summary||"").substring(0,300)}\nExperience: ${(profile.experience||[]).slice(0,2).map(e=>`${e.role} at ${e.company}`).join(", ")}`;

  const text = await callClaude({
    model: HAIKU, maxTokens: 400,
    system: "You are a career advisor. Return only valid JSON, no other text.",
    messages: [{ role: "user", content: `Based on this candidate profile, suggest 5 specific job titles they should apply for right now. Mix current-level roles and 1 stretch role. Return ONLY a JSON array of objects:\n[{"title":"...","reason":"one sentence why this fits","stretch":false}]\nProfile:\n${p}` }],
  });

  const start = text.indexOf("["), end = text.lastIndexOf("]");
  if (start === -1 || end <= start) return [];
  try { return JSON.parse(text.slice(start, end + 1)); } catch { return []; }
}

// ─── Search endpoints ─────────────────────────────────────────────────────────

// Indeed Canada — free + pro
app.post("/api/search/indeed", requireAuth, async (req, res) => {
  const usage = await checkAndIncrementUsage(req.user.id, req.profile);
  if (!usage.allowed) return res.status(403).json({ error: { message: "searches_exhausted", plan: "free" } });
  try {
    const jobs = await fetchIndeed(req.body.query, req.body.location);
    res.json({ jobs });
  } catch (err) { console.error("Indeed endpoint:", err.message); res.json({ jobs: [] }); }
});

// Remotive (remote/international) — Pro only
app.post("/api/search/linkedin", requireAuth, async (req, res) => {
  if (req.profile.plan !== "pro") return res.status(403).json({ error: { message: "sources_locked" } });
  try {
    const jobs = await fetchRemotive(req.body.query);
    res.json({ jobs });
  } catch (err) { console.error("Remotive endpoint:", err.message); res.json({ jobs: [] }); }
});

// The Muse + Jobicy (US/remote) — Pro only
app.post("/api/search/hiring", requireAuth, async (req, res) => {
  if (req.profile.plan !== "pro") return res.status(403).json({ error: { message: "sources_locked" } });
  try {
    const [muse, jobicy] = await Promise.all([
      fetchTheMuse(req.body.query),
      fetchJobicy(req.body.query),
    ]);
    // Merge and dedupe by title+company
    const seen = new Set();
    const jobs = [...muse, ...jobicy].filter(j => {
      const k = `${j.title}:${j.company}`.toLowerCase();
      if (seen.has(k)) return false;
      seen.add(k); return true;
    }).slice(0, 8);
    res.json({ jobs });
  } catch (err) { console.error("Muse/Jobicy endpoint:", err.message); res.json({ jobs: [] }); }
});

// Investment Banks — Pro only
app.post("/api/search/banks", requireAuth, async (req, res) => {
  if (req.profile.plan !== "pro") return res.status(403).json({ error: { message: "sources_locked" } });
  try {
    const jobs = await fetchInvestmentBanks(req.body.query, req.body.location);
    res.json({ jobs });
  } catch (err) { console.error("Banks endpoint:", err.message); res.json({ jobs: [] }); }
});

// ─── Profile recommendations ──────────────────────────────────────────────────
app.post("/api/recommendations", requireAuth, async (req, res) => {
  try {
    const recs = await generateRecommendations(req.body.profile);
    res.json({ recommendations: recs });
  } catch (err) {
    console.error("Recs error:", err.message);
    res.json({ recommendations: [] });
  }
});

// ─── On-demand job evaluation (Haiku) ────────────────────────────────────────
app.post("/api/evaluate", requireAuth, async (req, res) => {
  if (req.profile.plan !== "pro") return res.status(403).json({ error: { message: "evaluator_locked", plan: "free" } });

  const { job, profile } = req.body;
  const expSummary = (profile.experience || []).slice(0, 3).map(e =>
    `${e.role} at ${e.company}: ${(e.accomplishments || []).slice(0, 2).join("; ")}`
  ).join("\n");

  const p = `Title: ${profile.title||""}\nSkills: ${(profile.skills||[]).join(", ")||"none"}\nSummary: ${profile.summary||""}\n${expSummary}`;
  const j = `Title: ${job.title}\nCompany: ${job.company}\nLocation: ${job.location}\nDescription: ${job.description}`;

  try {
    const text = await callClaude({
      model: HAIKU, maxTokens: 400,
      system: "You are an expert recruiter. Return only valid raw JSON, no markdown.",
      messages: [{ role: "user", content: `Evaluate candidate fit for this job.\nCANDIDATE:\n${p}\n\nJOB:\n${j}\n\nReturn ONLY JSON: {"overall":1-5,"roleFit":1-5,"skillsMatch":1-5,"seniorityMatch":1-5,"locationFit":1-5,"companyAppeal":1-5,"summary":"one sentence"}` }],
    });
    const clean = text.replace(/```json|```/g, "").trim();
    const s = clean.indexOf("{"), e = clean.lastIndexOf("}");
    res.json(JSON.parse(clean.slice(s, e + 1)));
  } catch (err) {
    console.error("Eval error:", err.message);
    res.status(500).json({ error: { message: err.message } });
  }
});

// ─── AI proxy (parse + cover letter — Sonnet) ─────────────────────────────────
app.post("/api/messages", requireAuth, async (req, res) => {
  const { profile } = req;
  const { action }  = req.body;
  if (profile.plan !== "pro" && action === "cover") return res.status(403).json({ error: { message: "cover_locked", plan: "free" } });
  try {
    const body = { ...req.body };
    delete body.action;
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "anthropic-beta": "web-search-2025-03-05" },
      body: JSON.stringify(body),
    });
    res.json(await response.json());
  } catch (err) { res.status(500).json({ error: { message: err.message } }); }
});

// ─── Usage ────────────────────────────────────────────────────────────────────
app.get("/api/usage", requireAuth, (req, res) => {
  const { plan, searches_used } = req.profile;
  res.json({ plan, searches_used: searches_used || 0, searches_limit: plan === "pro" ? null : 5, searches_remaining: plan === "pro" ? null : Math.max(0, 5 - (searches_used || 0)) });
});

// ─── Stripe ───────────────────────────────────────────────────────────────────
app.post("/api/stripe/checkout", requireAuth, async (req, res) => {
  const { user, profile } = req;
  if (profile.plan === "pro") return res.status(400).json({ error: { message: "Already Pro" } });
  try {
    let customerId = profile.stripe_customer_id;
    if (!customerId) {
      const customer = await stripe.customers.create({ email: user.email, metadata: { supabase_user_id: user.id } });
      customerId = customer.id;
      await supabaseAdmin.from("profiles").update({ stripe_customer_id: customerId }).eq("id", user.id);
    }
    const session = await stripe.checkout.sessions.create({
      customer: customerId, payment_method_types: ["card"],
      line_items: [{ price: STRIPE_PRICE_ID, quantity: 1 }], mode: "subscription",
      success_url: `${FRONTEND_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${FRONTEND_URL}/pricing`, metadata: { supabase_user_id: user.id },
      subscription_data: { metadata: { supabase_user_id: user.id } },
    });
    res.json({ url: session.url });
  } catch (err) { res.status(500).json({ error: { message: err.message } }); }
});

app.post("/api/stripe/portal", requireAuth, async (req, res) => {
  if (!req.profile.stripe_customer_id) return res.status(400).json({ error: { message: "No Stripe customer" } });
  try {
    const session = await stripe.billingPortal.sessions.create({ customer: req.profile.stripe_customer_id, return_url: `${FRONTEND_URL}/account` });
    res.json({ url: session.url });
  } catch (err) { res.status(500).json({ error: { message: err.message } }); }
});

app.post("/api/stripe/webhook", async (req, res) => {
  let event;
  try { event = stripe.webhooks.constructEvent(req.body, req.headers["stripe-signature"], STRIPE_WEBHOOK_SECRET); }
  catch (err) { return res.status(400).send(`Webhook Error: ${err.message}`); }
  const uid = obj => obj?.metadata?.supabase_user_id;
  switch (event.type) {
    case "checkout.session.completed": {
      const s = event.data.object;
      if (uid(s) && s.payment_status === "paid") await supabaseAdmin.from("profiles").update({ plan: "pro", stripe_sub_id: s.subscription }).eq("id", uid(s));
      break;
    }
    case "invoice.payment_succeeded": {
      const inv = event.data.object;
      if (inv.billing_reason === "subscription_cycle") {
        const sub = await stripe.subscriptions.retrieve(inv.subscription);
        if (uid(sub)) await supabaseAdmin.from("profiles").update({ plan: "pro" }).eq("id", uid(sub));
      }
      break;
    }
    case "customer.subscription.deleted":
    case "invoice.payment_failed": {
      const o = event.data.object;
      const s = o.subscription ? await stripe.subscriptions.retrieve(o.subscription) : o;
      if (uid(s)) await supabaseAdmin.from("profiles").update({ plan: "free", stripe_sub_id: null }).eq("id", uid(s));
      break;
    }
  }
  res.json({ received: true });
});

app.listen(3001, () => console.log("✅  Etlyx Apply — real job APIs + on-demand Haiku evaluation"));
