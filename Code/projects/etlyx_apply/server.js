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
const HAIKU  = "claude-haiku-4-5-20251001";   // match scoring — cheap + fast
const SONNET = "claude-sonnet-4-20250514";     // resume tweaks, cover letters, interview prep, parsing

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
    .select("plan, stripe_customer_id, stripe_sub_id")
    .eq("id", user.id).single();
  req.user    = user;
  req.profile = profile || { plan: "free" };
  next();
}

// ─── Claude helper ────────────────────────────────────────────────────────────
async function callClaude({ model = HAIKU, system = "", messages, maxTokens = 1000 }) {
  const body = { model, max_tokens: maxTokens, messages };
  if (system) body.system = system;
  const res  = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
      "anthropic-beta": "web-search-2025-03-05",
    },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error.message);
  return (data.content || []).filter(b => b.type === "text").map(b => b.text).join("");
}

// ─── Job Match Analysis (Haiku — cheap, returns full JSON) ────────────────────
app.post("/api/match", requireAuth, async (req, res) => {
  const { user, profile } = req;

  // Check and increment usage for free users
  if (profile.plan !== "pro") {
    const resetAt    = profile.searches_reset_at ? new Date(profile.searches_reset_at) : null;
    const now        = new Date();
    const needsReset = !resetAt || now.getFullYear() !== resetAt.getFullYear() || now.getMonth() !== resetAt.getMonth();

    if (needsReset) {
      await supabaseAdmin.from("profiles").update({ searches_used: 1, searches_reset_at: now.toISOString() }).eq("id", user.id);
    } else {
      const used = profile.searches_used || 0;
      if (used >= 5) {
        return res.status(403).json({ error: { message: "analyses_exhausted", plan: "free", searches_used: used } });
      }
      await supabaseAdmin.from("profiles").update({ searches_used: used + 1 }).eq("id", user.id);
    }
  }

  const { profile: candidateProfile, jobDescription, company, jobTitle } = req.body;

  const profileText = `
Name: ${candidateProfile.name || ""}
Current Title: ${candidateProfile.title || ""}
Summary: ${candidateProfile.summary || ""}
Skills: ${(candidateProfile.skills || []).slice(0, 20).join(", ") || "none listed"}
Experience:
${(candidateProfile.experience || []).slice(0, 3).map(e =>
  `- ${e.role} at ${e.company} (${e.period || ""})\n${(e.accomplishments || []).slice(0, 3).map(a => `  • ${a}`).join("\n")}`
).join("\n")}
`.trim();

  const prompt = `You are an expert recruiter and career coach. Analyze how well this candidate matches this job.

CANDIDATE PROFILE:
${profileText}

JOB: ${jobTitle || "Not specified"} at ${company || "Not specified"}
JOB DESCRIPTION:
${jobDescription.substring(0, 2000)}

Scoring rules — follow these exactly:
- 9-10: Strong Match — candidate clearly meets nearly all requirements
- 7-8: Good Match — candidate meets most requirements, minor gaps
- 5-6: Partial Match — candidate meets some requirements, notable gaps
- 3-4: Weak Match — significant gaps, domain or level mismatch
- 1-2: Poor Match — major misalignment

shouldApply rules — must be consistent with score:
- Score 7+: shouldApply must be true
- Score 5-6: shouldApply only true if gaps are learnable/addressable
- Score 4 or below: shouldApply must be false

Return ONLY a JSON object with this exact structure (keep all string values concise — under 20 words each):
{
  "overallScore": <integer 1-10>,
  "verdict": "Strong Match|Good Match|Partial Match|Weak Match|Poor Match",
  "shouldApply": true/false,
  "shouldApplyReason": "one sentence max",
  "skillsMatch": [{"skill":"...","have":true/false,"importance":"high|medium|low"}],
  "experienceAlignment": [{"area":"...","score":1-5,"comment":"one sentence"}],
  "topStrengths": ["strength 1","strength 2","strength 3"],
  "gapSummary": "2-3 sentences",
  "interviewLikelihood": "High|Medium|Low",
  "interviewLikelihoodReason": "one sentence"
}`;

  try {
    const text = await callClaude({
      model: HAIKU, maxTokens: 2500,
      system: "You are an expert recruiter. Return only valid raw JSON, no markdown, no explanation.",
      messages: [{ role: "user", content: prompt }],
    });
    const s = text.indexOf("{"), e = text.lastIndexOf("}");
    const result = JSON.parse(text.slice(s, e + 1));

    // Hard enforce: score and shouldApply must never contradict each other
    if (result.overallScore >= 7)  result.shouldApply = true;
    if (result.overallScore <= 4)  result.shouldApply = false;
    // Hard enforce: verdict must match score band
    if      (result.overallScore >= 9) result.verdict = "Strong Match";
    else if (result.overallScore >= 7) result.verdict = "Good Match";
    else if (result.overallScore >= 5) result.verdict = "Partial Match";
    else if (result.overallScore >= 3) result.verdict = "Weak Match";
    else                               result.verdict = "Poor Match";

    res.json(result);
  } catch (err) {
    console.error("[Match] error:", err.message);
    res.status(500).json({ error: { message: err.message } });
  }
});

// ─── Resume Tweaks (Sonnet — quality matters, Pro only) ───────────────────────
app.post("/api/tweaks", requireAuth, async (req, res) => {
  if (req.profile.plan !== "pro") return res.status(403).json({ error: { message: "pro_required" } });

  const { profile, jobDescription, company, jobTitle } = req.body;

  const bullets = (profile.experience || []).flatMap(e =>
    (e.accomplishments || []).map(a => ({ role: e.role, company: e.company, bullet: a }))
  ).slice(0, 10);

  const prompt = `You are an expert resume writer. Suggest specific tweaks to this candidate's resume bullets to better match this job.

JOB: ${jobTitle || ""} at ${company || ""}
JOB DESCRIPTION:
${jobDescription.substring(0, 1500)}

CURRENT RESUME BULLETS:
${bullets.map((b, i) => `${i + 1}. [${b.role} @ ${b.company}] ${b.bullet}`).join("\n")}

Return ONLY a JSON array of suggested improvements:
[
  {
    "original": "exact original bullet text",
    "improved": "rewritten version optimized for this job",
    "reason": "why this change helps",
    "role": "role it belongs to",
    "company": "company name",
    "impact": "high|medium|low"
  }
]
Focus on the 3-5 most impactful changes only. Don't suggest changes that aren't genuinely needed.`;

  try {
    const text = await callClaude({
      model: SONNET, maxTokens: 1500,
      system: "You are an expert resume writer and recruiter. Return only valid raw JSON array, no markdown.",
      messages: [{ role: "user", content: prompt }],
    });
    const s = text.indexOf("["), e = text.lastIndexOf("]");
    res.json(JSON.parse(text.slice(s, e + 1)));
  } catch (err) {
    console.error("[Tweaks] error:", err.message);
    res.status(500).json({ error: { message: err.message } });
  }
});

// ─── Interview Prep (Sonnet — Pro only) ───────────────────────────────────────
app.post("/api/interview", requireAuth, async (req, res) => {
  if (req.profile.plan !== "pro") return res.status(403).json({ error: { message: "pro_required" } });

  const { profile, jobDescription, company, jobTitle, matchData } = req.body;

  const gaps    = (matchData?.skillsMatch || []).filter(s => !s.have && s.importance === "high").map(s => s.skill).join(", ");
  const strengths = (matchData?.topStrengths || []).join(", ");

  const prompt = `You are an expert interview coach. Generate targeted interview prep for this candidate applying to this specific role.

CANDIDATE: ${profile.name || ""}, ${profile.title || ""}
JOB: ${jobTitle || ""} at ${company || ""}
CANDIDATE STRENGTHS FOR THIS ROLE: ${strengths}
CANDIDATE GAPS TO ADDRESS: ${gaps || "none identified"}

JOB DESCRIPTION (excerpt):
${jobDescription.substring(0, 1000)}

Return ONLY a JSON object:
{
  "likelyQuestions": [
    {
      "question": "...",
      "type": "behavioral|technical|situational|culture",
      "why": "why they'll likely ask this",
      "suggestedAnswer": "2-3 sentence suggested answer using candidate's background",
      "starExample": "which experience from their resume to draw from"
    }
  ],
  "questionsToAsk": ["smart question to ask interviewer 1", "smart question 2", "smart question 3"],
  "keyThemesToEmphasize": ["theme 1", "theme 2", "theme 3"],
  "potentialConcerns": ["concern they might have about you", "how to address it proactively"]
}
Include 5-6 likely questions. Focus on what's specific to this role and this candidate's profile.`;

  try {
    const text = await callClaude({
      model: SONNET, maxTokens: 2000,
      system: "You are an expert interview coach. Return only valid raw JSON, no markdown.",
      messages: [{ role: "user", content: prompt }],
    });
    const s = text.indexOf("{"), e = text.lastIndexOf("}");
    res.json(JSON.parse(text.slice(s, e + 1)));
  } catch (err) {
    console.error("[Interview] error:", err.message);
    res.status(500).json({ error: { message: err.message } });
  }
});

// ─── Cover Letter (Sonnet — Pro only) ─────────────────────────────────────────
app.post("/api/cover", requireAuth, async (req, res) => {
  if (req.profile.plan !== "pro") return res.status(403).json({ error: { message: "pro_required" } });

  const { profile, jobDescription, company, jobTitle, tone, matchData } = req.body;

  const strengths = (matchData?.topStrengths || []).join(", ");
  const topAccomplishments = (profile.experience || []).slice(0, 2)
    .flatMap(e => (e.accomplishments || []).slice(0, 2).map(a => `[${e.role} @ ${e.company}] ${a}`))
    .join("\n");

  const prompt = `Write a ${tone || "professional"} cover letter for this application.

CANDIDATE:
Name: ${profile.name || ""}
Title: ${profile.title || ""}
Location: ${profile.location || ""}
Summary: ${profile.summary || ""}
Key accomplishments:
${topAccomplishments}
Core strengths for this role: ${strengths}

JOB: ${jobTitle || ""} at ${company || ""}
JOB DESCRIPTION:
${jobDescription.substring(0, 1200)}

Write 3-4 compelling paragraphs. Reference specific accomplishments. Show genuine understanding of the company and role. No placeholder brackets. Address the hiring manager professionally.`;

  try {
    const text = await callClaude({
      model: SONNET, maxTokens: 1000,
      messages: [{ role: "user", content: prompt }],
    });
    res.json({ letter: text });
  } catch (err) {
    console.error("[Cover] error:", err.message);
    res.status(500).json({ error: { message: err.message } });
  }
});

// ─── Resume parsing proxy (Sonnet — handles PDF/image) ────────────────────────
app.post("/api/messages", requireAuth, async (req, res) => {
  try {
    const body = { ...req.body };
    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "web-search-2025-03-05",
      },
      body: JSON.stringify(body),
    });
    res.json(await response.json());
  } catch (err) { res.status(500).json({ error: { message: err.message } }); }
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
      cancel_url: `${FRONTEND_URL}/pricing`,
      metadata: { supabase_user_id: user.id },
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
  const uid = o => o?.metadata?.supabase_user_id;
  switch (event.type) {
    case "checkout.session.completed": {
      const s = event.data.object;
      if (uid(s) && s.payment_status === "paid")
        await supabaseAdmin.from("profiles").update({ plan: "pro", stripe_sub_id: s.subscription }).eq("id", uid(s));
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

app.get("/api/usage", requireAuth, (req, res) => {
  res.json({ plan: req.profile.plan });
});

// ─── Serve Vite build in production ──────────────────────────────────────────
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { existsSync } from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname  = dirname(__filename);
const distPath   = join(__dirname, "dist");

console.log("Looking for dist at:", distPath, "exists:", existsSync(distPath));

// Always serve static files and catch-all — Express returns 404 if file not found
app.use(express.static(distPath));

app.get("*", (req, res) => {
  const indexPath = join(distPath, "index.html");
  if (existsSync(indexPath)) {
    res.sendFile(indexPath);
  } else {
    res.status(404).send("Build not found. Run npm run build first.");
  }
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log(`✅  Etlyx Apply running on port ${PORT}`));
