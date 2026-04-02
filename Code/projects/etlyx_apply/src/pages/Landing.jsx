import { useState, useEffect } from "react";

const css = `
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body { background: #0a0c10; color: #e8e4dc; font-family: 'DM Sans', sans-serif; overflow-x: hidden; }

:root {
  --gold: #c8a96e;
  --gold-light: #e4cc9a;
  --gold-dim: #c8a96e40;
  --bg: #0a0c10;
  --bg-card: #111318;
  --border: #1e2330;
  --text: #e8e4dc;
  --muted: #6b7280;
  --serif: 'Instrument Serif', serif;
}

/* ── Noise texture overlay ── */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events: none;
  z-index: 0;
  opacity: 0.4;
}

/* ── Nav ── */
.nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 48px;
  height: 64px;
  border-bottom: 1px solid transparent;
  transition: all 0.3s;
}
.nav.scrolled {
  background: rgba(10,12,16,0.92);
  border-bottom-color: var(--border);
  backdrop-filter: blur(12px);
}
.nav-logo { font-family: var(--serif); font-size: 20px; color: var(--text); text-decoration: none; }
.nav-logo span { color: var(--gold); }
.nav-links { display: flex; align-items: center; gap: 32px; }
.nav-link { color: var(--muted); font-size: 14px; text-decoration: none; transition: color 0.15s; }
.nav-link:hover { color: var(--text); }
.nav-cta { background: var(--gold); color: #0a0c10; border: none; border-radius: 8px; padding: 9px 20px; font-family: 'DM Sans', sans-serif; font-size: 13.5px; font-weight: 600; cursor: pointer; transition: all 0.15s; }
.nav-cta:hover { background: var(--gold-light); transform: translateY(-1px); }

/* ── Hero ── */
.hero {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 120px 24px 80px;
  position: relative;
  z-index: 1;
}

/* Radial glow behind hero */
.hero::before {
  content: '';
  position: absolute;
  top: 20%;
  left: 50%;
  transform: translateX(-50%);
  width: 700px;
  height: 500px;
  background: radial-gradient(ellipse, rgba(200,169,110,0.08) 0%, transparent 70%);
  pointer-events: none;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(200,169,110,0.08);
  border: 1px solid var(--gold-dim);
  color: var(--gold);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  padding: 6px 16px;
  border-radius: 20px;
  margin-bottom: 32px;
  animation: fadeUp 0.6s ease both;
}

.hero-title {
  font-family: var(--serif);
  font-size: clamp(48px, 7vw, 88px);
  line-height: 1.05;
  color: var(--text);
  margin-bottom: 24px;
  max-width: 900px;
  animation: fadeUp 0.6s 0.1s ease both;
}
.hero-title em {
  font-style: italic;
  color: var(--gold);
}

.hero-sub {
  font-size: clamp(16px, 2vw, 20px);
  color: var(--muted);
  max-width: 560px;
  line-height: 1.7;
  margin-bottom: 48px;
  animation: fadeUp 0.6s 0.2s ease both;
}

.hero-actions {
  display: flex;
  gap: 14px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: center;
  animation: fadeUp 0.6s 0.3s ease both;
}

.btn-primary {
  background: var(--gold);
  color: #0a0c10;
  border: none;
  border-radius: 10px;
  padding: 14px 32px;
  font-family: 'DM Sans', sans-serif;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.btn-primary:hover { background: var(--gold-light); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(200,169,110,0.25); }

.btn-secondary {
  background: transparent;
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 28px;
  font-family: 'DM Sans', sans-serif;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-secondary:hover { color: var(--text); border-color: #2a3040; background: rgba(255,255,255,0.03); }

.hero-note {
  margin-top: 20px;
  font-size: 12.5px;
  color: #4b5563;
  animation: fadeUp 0.6s 0.4s ease both;
}

/* ── Demo mockup ── */
.hero-mockup {
  margin-top: 72px;
  width: 100%;
  max-width: 860px;
  animation: fadeUp 0.8s 0.5s ease both;
  position: relative;
  z-index: 1;
}
.mockup-frame {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 40px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(200,169,110,0.05);
}
.mockup-bar {
  background: #0d0f14;
  border-bottom: 1px solid var(--border);
  padding: 14px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.mockup-dots { display: flex; gap: 6px; }
.mockup-dot { width: 10px; height: 10px; border-radius: 50%; }
.mockup-body { padding: 28px; }
.mockup-score-row { display: flex; gap: 20px; align-items: flex-start; margin-bottom: 24px; }
.mockup-ring { width: 80px; height: 80px; border-radius: 50%; border: 3px solid #60a5fa; background: #0a1220; display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0; }
.mockup-ring-num { font-family: var(--serif); font-size: 26px; font-weight: 700; color: #60a5fa; line-height: 1; }
.mockup-ring-denom { font-size: 10px; color: #60a5fa; opacity: 0.7; }
.mockup-verdict { flex: 1; }
.mockup-verdict-title { font-size: 13px; font-weight: 600; color: #34d399; margin-bottom: 6px; }
.mockup-verdict-text { font-size: 12px; color: var(--muted); line-height: 1.6; }
.mockup-skills { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 20px; }
.mockup-pill { padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 500; }
.mockup-pill.have { background: #0a1f17; border: 1px solid #34d39940; color: #34d399; }
.mockup-pill.miss { background: #1a0a0a; border: 1px solid #f8717140; color: #f87171; }
.mockup-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.mockup-btn { padding: 7px 14px; border-radius: 8px; font-size: 11px; font-weight: 600; cursor: default; }
.mockup-btn.gold { background: var(--gold); color: #0a0c10; }
.mockup-btn.ghost { background: #1a1c26; border: 1px solid var(--border); color: var(--muted); }

/* ── Section ── */
.section { padding: 100px 24px; position: relative; z-index: 1; }
.section-inner { max-width: 1100px; margin: 0 auto; }
.section-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: var(--gold); margin-bottom: 16px; }
.section-title { font-family: var(--serif); font-size: clamp(36px, 4vw, 52px); color: var(--text); margin-bottom: 16px; line-height: 1.1; }
.section-sub { font-size: 17px; color: var(--muted); max-width: 560px; line-height: 1.7; }

/* ── How it works ── */
.steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px; margin-top: 64px; }
.step {
  background: var(--bg-card);
  border: 1px solid var(--border);
  padding: 36px 32px;
  position: relative;
  transition: border-color 0.2s;
}
.step:first-child { border-radius: 14px 0 0 14px; }
.step:last-child { border-radius: 0 14px 14px 0; }
.step:hover { border-color: #2a3040; }
.step-num { font-family: var(--serif); font-size: 48px; color: rgba(200,169,110,0.15); font-weight: 700; line-height: 1; margin-bottom: 20px; }
.step-icon { font-size: 28px; margin-bottom: 16px; }
.step-title { font-size: 17px; font-weight: 600; color: var(--text); margin-bottom: 10px; }
.step-desc { font-size: 14px; color: var(--muted); line-height: 1.7; }

/* ── Features ── */
.features-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 64px; }
.feature-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 32px;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}
.feature-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--gold-dim), transparent);
  opacity: 0;
  transition: opacity 0.2s;
}
.feature-card:hover { border-color: #2a3040; transform: translateY(-2px); }
.feature-card:hover::before { opacity: 1; }
.feature-card.featured { border-color: var(--gold-dim); grid-column: span 2; display: grid; grid-template-columns: 1fr 1fr; gap: 32px; align-items: center; }
.feature-icon { font-size: 32px; margin-bottom: 16px; }
.feature-tag { display: inline-block; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--gold); background: rgba(200,169,110,0.1); border: 1px solid var(--gold-dim); padding: 2px 8px; border-radius: 20px; margin-bottom: 12px; }
.feature-title { font-size: 18px; font-weight: 600; color: var(--text); margin-bottom: 10px; }
.feature-desc { font-size: 14px; color: var(--muted); line-height: 1.7; }
.feature-list { list-style: none; margin-top: 12px; }
.feature-list li { font-size: 13.5px; color: var(--muted); padding: 5px 0; display: flex; align-items: center; gap: 8px; }
.feature-list li::before { content: '✓'; color: #34d399; font-weight: 700; flex-shrink: 0; }

/* ── Pricing ── */
.pricing-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 64px; max-width: 720px; }
.plan {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 36px 32px;
  display: flex;
  flex-direction: column;
  position: relative;
}
.plan.pro { border-color: var(--gold-dim); }
.plan-badge-top {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--gold);
  color: #0a0c10;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 4px 14px;
  border-radius: 20px;
  white-space: nowrap;
}
.plan-name { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--muted); margin-bottom: 12px; }
.plan-price { font-family: var(--serif); font-size: 52px; color: var(--text); line-height: 1; margin-bottom: 4px; }
.plan-price span { font-size: 18px; color: var(--muted); font-family: 'DM Sans', sans-serif; }
.plan-desc { font-size: 13px; color: var(--muted); margin-bottom: 28px; }
.plan-features { list-style: none; flex: 1; margin-bottom: 28px; }
.plan-features li { font-size: 13.5px; color: #9ca3af; padding: 7px 0; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 10px; }
.plan-features li:last-child { border-bottom: none; }
.plan-features li.on { color: var(--text); }
.plan-features li.off { color: #4b5563; text-decoration: line-through; }
.feat-check { flex-shrink: 0; font-size: 13px; }

/* ── Social proof ── */
.proof-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 48px; }
.proof-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 28px;
}
.proof-stars { color: var(--gold); font-size: 14px; margin-bottom: 14px; letter-spacing: 2px; }
.proof-text { font-size: 14px; color: #9ca3af; line-height: 1.7; margin-bottom: 18px; font-style: italic; }
.proof-author { font-size: 13px; font-weight: 600; color: var(--text); }
.proof-role { font-size: 12px; color: var(--muted); margin-top: 2px; }

/* ── CTA ── */
.cta-section {
  padding: 120px 24px;
  text-align: center;
  position: relative;
  z-index: 1;
}
.cta-section::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 600px;
  height: 400px;
  background: radial-gradient(ellipse, rgba(200,169,110,0.06) 0%, transparent 70%);
  pointer-events: none;
}
.cta-title { font-family: var(--serif); font-size: clamp(40px, 5vw, 64px); color: var(--text); margin-bottom: 20px; line-height: 1.1; }
.cta-sub { font-size: 17px; color: var(--muted); max-width: 480px; margin: 0 auto 40px; line-height: 1.7; }

/* ── Footer ── */
.footer {
  border-top: 1px solid var(--border);
  padding: 40px 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  z-index: 1;
}
.footer-logo { font-family: var(--serif); font-size: 18px; color: var(--text); }
.footer-logo span { color: var(--gold); }
.footer-links { display: flex; gap: 24px; }
.footer-link { font-size: 13px; color: var(--muted); text-decoration: none; transition: color 0.15s; }
.footer-link:hover { color: var(--text); }
.footer-copy { font-size: 12px; color: #374151; }

/* ── Divider ── */
.divider-line {
  border: none;
  border-top: 1px solid var(--border);
  margin: 0 48px;
  position: relative;
  z-index: 1;
}

/* ── Animations ── */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(24px); }
  to { opacity: 1; transform: translateY(0); }
}

.reveal {
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}
.reveal.visible { opacity: 1; transform: translateY(0); }

/* ── Responsive ── */
@media (max-width: 900px) {
  .nav { padding: 0 24px; }
  .nav-links { display: none; }
  .steps { grid-template-columns: 1fr; gap: 12px; }
  .step:first-child, .step:last-child, .step { border-radius: 12px; }
  .features-grid { grid-template-columns: 1fr; }
  .feature-card.featured { grid-column: span 1; grid-template-columns: 1fr; }
  .pricing-grid { grid-template-columns: 1fr; max-width: 400px; }
  .proof-grid { grid-template-columns: 1fr; }
  .footer { flex-direction: column; gap: 20px; text-align: center; padding: 32px 24px; }
  .footer-links { flex-wrap: wrap; justify-content: center; }
  .divider-line { margin: 0 24px; }
}
`;

export default function LandingPage({ onGetStarted }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Intersection observer for reveal animations
  useEffect(() => {
    const els = document.querySelectorAll(".reveal");
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add("visible"); obs.unobserve(e.target); } });
    }, { threshold: 0.1 });
    els.forEach(el => obs.observe(el));
    return () => obs.disconnect();
  }, []);

  return (
    <>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap'); ${css}`}</style>

      {/* Nav */}
      <nav className={`nav${scrolled ? " scrolled" : ""}`}>
        <a href="#" className="nav-logo">apply by <span>etlyx</span></a>
        <div className="nav-links">
          <a href="#how" className="nav-link">How it works</a>
          <a href="#features" className="nav-link">Features</a>
          <a href="#pricing" className="nav-link">Pricing</a>
        </div>
        <button className="nav-cta" onClick={onGetStarted}>Get started free</button>
      </nav>

      {/* Hero */}
      <section className="hero">
        <div className="hero-badge">✦ AI-Powered Job Matching</div>
        <h1 className="hero-title">
          Know your odds before<br />you <em>hit apply</em>
        </h1>
        <p className="hero-sub">
          Paste any job description. Get an instant match score, skill gap analysis, tailored resume tweaks, interview prep, and a cover letter — all in seconds.
        </p>
        <div className="hero-actions">
          <button className="btn-primary" onClick={onGetStarted}>
            Start for free →
          </button>
          <button className="btn-secondary" onClick={() => document.getElementById("how").scrollIntoView({ behavior: "smooth" })}>
            See how it works
          </button>
        </div>
        <p className="hero-note">Free plan includes 5 match analyses/month. No credit card required.</p>

        {/* Mini mockup */}
        <div className="hero-mockup">
          <div className="mockup-frame">
            <div className="mockup-bar">
              <div className="mockup-dots">
                <div className="mockup-dot" style={{background:"#ff5f57"}}/>
                <div className="mockup-dot" style={{background:"#febc2e"}}/>
                <div className="mockup-dot" style={{background:"#28c840"}}/>
              </div>
              <div style={{flex:1,height:8,background:"#1e2330",borderRadius:4,marginLeft:8}}/>
            </div>
            <div className="mockup-body">
              <div style={{display:"flex",gap:12,marginBottom:16,borderBottom:"1px solid #1e2330",paddingBottom:16}}>
                {["Match Analysis","Resume Tweaks","Interview Prep","Cover Letter"].map((t,i)=>
                  <div key={t} style={{fontSize:12,padding:"4px 0",borderBottom:i===0?"2px solid #c8a96e":"2px solid transparent",color:i===0?"#c8a96e":"#4b5563",cursor:"default"}}>{t}</div>
                )}
              </div>
              <div className="mockup-score-row">
                <div className="mockup-ring">
                  <div className="mockup-ring-num">8</div>
                  <div className="mockup-ring-denom">/10</div>
                </div>
                <div className="mockup-verdict">
                  <div className="mockup-verdict-title">✅ Good Match — You should apply</div>
                  <div className="mockup-verdict-text">Strong data background and leadership experience aligns well with this role. One key gap: Azure platform expertise. Interview likelihood: <span style={{color:"#34d399",fontWeight:600}}>High</span></div>
                </div>
              </div>
              <div style={{fontSize:11,fontWeight:600,color:"#6b7280",textTransform:"uppercase",letterSpacing:"0.8px",marginBottom:8}}>Skills Match</div>
              <div className="mockup-skills">
                {["Python","SQL","Power BI","Data Modeling","Team Leadership"].map(s=><span key={s} className="mockup-pill have">✓ {s}</span>)}
                {["Azure","Snowflake"].map(s=><span key={s} className="mockup-pill miss">✗ {s}</span>)}
              </div>
              <div className="mockup-actions">
                <div className="mockup-btn gold">✏️ Resume Tweaks</div>
                <div className="mockup-btn ghost">🎤 Interview Prep</div>
                <div className="mockup-btn ghost">✉️ Cover Letter</div>
                <div className="mockup-btn ghost">💾 Save</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <hr className="divider-line" />

      {/* How it works */}
      <section className="section" id="how">
        <div className="section-inner">
          <div className="reveal">
            <div className="section-label">How it works</div>
            <h2 className="section-title">Three steps to a stronger application</h2>
            <p className="section-sub">From resume upload to interview-ready in minutes — not hours.</p>
          </div>
          <div className="steps reveal">
            <div className="step">
              <div className="step-num">01</div>
              <div className="step-icon">📄</div>
              <div className="step-title">Upload your resume once</div>
              <div className="step-desc">Our parser extracts your skills, experience, and accomplishments. Store multiple versions for different role types.</div>
            </div>
            <div className="step">
              <div className="step-num">02</div>
              <div className="step-icon">🎯</div>
              <div className="step-title">Paste any job description</div>
              <div className="step-desc">Copy the JD from any job board — LinkedIn, Indeed, company career pages. Instant match score in seconds.</div>
            </div>
            <div className="step">
              <div className="step-num">03</div>
              <div className="step-icon">🚀</div>
              <div className="step-title">Apply with confidence</div>
              <div className="step-desc">Get your tweaked resume, tailored cover letter, and interview prep — everything you need before hitting submit.</div>
            </div>
          </div>
        </div>
      </section>

      <hr className="divider-line" />

      {/* Features */}
      <section className="section" id="features">
        <div className="section-inner">
          <div className="reveal">
            <div className="section-label">Features</div>
            <h2 className="section-title">Everything you need to land the interview</h2>
          </div>
          <div className="features-grid">
            {/* Featured card */}
            <div className="feature-card featured reveal">
              <div>
                <div className="feature-icon">🎯</div>
                <div className="feature-tag">Core feature</div>
                <div className="feature-title">Instant Match Analysis</div>
                <div className="feature-desc">Paste any job description and get a detailed breakdown of how well you fit — before you spend an hour crafting an application.</div>
                <ul className="feature-list">
                  <li>Match score 1–10 with honest verdict</li>
                  <li>Skills you have vs. skills you're missing</li>
                  <li>Experience alignment by area</li>
                  <li>Realistic interview likelihood</li>
                  <li>Clear "should you apply" recommendation</li>
                </ul>
              </div>
              <div style={{background:"#0d0f14",border:"1px solid #1e2330",borderRadius:12,padding:24}}>
                <div style={{display:"flex",alignItems:"center",gap:16,marginBottom:20}}>
                  <div style={{width:64,height:64,borderRadius:"50%",border:"3px solid #34d399",background:"#0a1f17",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",flexShrink:0}}>
                    <div style={{fontFamily:"'Instrument Serif',serif",fontSize:22,fontWeight:700,color:"#34d399",lineHeight:1}}>9</div>
                    <div style={{fontSize:9,color:"#34d399",opacity:0.7}}>/10</div>
                  </div>
                  <div>
                    <div style={{fontSize:12,fontWeight:600,color:"#34d399",marginBottom:4}}>Strong Match</div>
                    <div style={{fontSize:11,color:"#6b7280"}}>Interview likelihood: High</div>
                  </div>
                </div>
                {[["Data Governance","have"],["Risk Analytics","have"],["Python / SQL","have"],["Power BI","have"],["Azure DevOps","miss"]].map(([s,t])=>(
                  <div key={s} style={{display:"flex",alignItems:"center",gap:8,marginBottom:6}}>
                    <span style={{fontSize:11,color:t==="have"?"#34d399":"#f87171"}}>{t==="have"?"✓":"✗"}</span>
                    <span style={{fontSize:12,color:t==="have"?"#9ca3af":"#6b7280"}}>{s}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="feature-card reveal">
              <div className="feature-icon">✏️</div>
              <div className="feature-tag">Pro</div>
              <div className="feature-title">Resume Tweaks</div>
              <div className="feature-desc">Get specific, copy-ready rewrites of your resume bullets — optimized for each job you apply to. Before/after comparisons so you see exactly what changed and why.</div>
            </div>

            <div className="feature-card reveal">
              <div className="feature-icon">🎤</div>
              <div className="feature-tag">Pro</div>
              <div className="feature-title">Interview Prep</div>
              <div className="feature-desc">Likely questions for this specific role, with suggested answers drawn from your actual experience. Plus smart questions to ask the interviewer.</div>
            </div>

            <div className="feature-card reveal">
              <div className="feature-icon">✉️</div>
              <div className="feature-tag">Pro</div>
              <div className="feature-title">Cover Letter</div>
              <div className="feature-desc">A tailored cover letter written around your real accomplishments and this specific role. Choose your tone — professional, conversational, enthusiastic, or concise.</div>
            </div>

            <div className="feature-card reveal">
              <div className="feature-icon">📋</div>
              <div className="feature-tag">Free + Pro</div>
              <div className="feature-title">Application Tracker</div>
              <div className="feature-desc">Save every analysis with its match score, tweaked resume, interview prep, and cover letter. Track status from Saved → Applied → Interview → Offer.</div>
            </div>
          </div>
        </div>
      </section>

      <hr className="divider-line" />

      {/* Pricing */}
      <section className="section" id="pricing">
        <div className="section-inner">
          <div className="reveal">
            <div className="section-label">Pricing</div>
            <h2 className="section-title">Simple, honest pricing</h2>
            <p className="section-sub">Start free. Upgrade when you're ready to go all in on your job search.</p>
          </div>
          <div className="pricing-grid reveal">
            <div className="plan">
              <div className="plan-name">Free</div>
              <div className="plan-price">$0 <span>/month</span></div>
              <div className="plan-desc">No credit card needed</div>
              <ul className="plan-features">
                <li className="on"><span className="feat-check">✓</span>Upload & parse resume</li>
                <li className="on"><span className="feat-check">✓</span>5 match analyses per month</li>
                <li className="on"><span className="feat-check">✓</span>Skills gap breakdown</li>
                <li className="on"><span className="feat-check">✓</span>Application tracker</li>
                <li className="off"><span className="feat-check">🔒</span>Resume Tweaks</li>
                <li className="off"><span className="feat-check">🔒</span>Interview Prep</li>
                <li className="off"><span className="feat-check">🔒</span>Cover Letter</li>
              </ul>
              <button className="btn-secondary" style={{width:"100%",padding:"12px",textAlign:"center",justifyContent:"center"}} onClick={onGetStarted}>Get started free</button>
            </div>
            <div className="plan pro">
              <div className="plan-badge-top">Most popular</div>
              <div className="plan-name">Pro</div>
              <div className="plan-price">$15 <span>/month</span></div>
              <div className="plan-desc">Everything to land the interview</div>
              <ul className="plan-features">
                <li className="on"><span className="feat-check">✓</span>Everything in Free</li>
                <li className="on"><span className="feat-check">✓</span>Unlimited match analyses</li>
                <li className="on"><span className="feat-check">✓</span>Resume Tweaks per job</li>
                <li className="on"><span className="feat-check">✓</span>Interview Prep — tailored Q&A</li>
                <li className="on"><span className="feat-check">✓</span>Cover Letter generation</li>
                <li className="on"><span className="feat-check">✓</span>Multiple resume versions</li>
                <li className="on"><span className="feat-check">✓</span>Priority support</li>
              </ul>
              <button className="btn-primary" style={{width:"100%",justifyContent:"center"}} onClick={onGetStarted}>Start Pro — $15/mo</button>
            </div>
          </div>
          <p style={{marginTop:20,fontSize:12,color:"#374151",textAlign:"center"}}>Cancel anytime · Billed monthly · Secure payments via Stripe</p>
        </div>
      </section>

      <hr className="divider-line" />

      {/* Social proof */}
      <section className="section">
        <div className="section-inner">
          <div className="reveal">
            <div className="section-label">Why it works</div>
            <h2 className="section-title">Stop applying blind</h2>
            <p className="section-sub">Most job seekers apply to dozens of roles without knowing their actual fit. apply by etlyx changes that.</p>
          </div>
          <div className="proof-grid reveal">
            <div className="proof-card">
              <div className="proof-stars">★★★★★</div>
              <div className="proof-text">"I used to apply to 20 jobs and hear back from 2. Now I spend 10 minutes analyzing before applying and my response rate has tripled."</div>
              <div className="proof-author">Senior Data Analyst</div>
              <div className="proof-role">Montreal, QC</div>
            </div>
            <div className="proof-card">
              <div className="proof-stars">★★★★★</div>
              <div className="proof-text">"The resume tweaks feature alone is worth it. It shows me exactly which bullets to change for each role — took me from 6/10 to 9/10 on the same job."</div>
              <div className="proof-author">Analytics Manager</div>
              <div className="proof-role">Toronto, ON</div>
            </div>
            <div className="proof-card">
              <div className="proof-stars">★★★★★</div>
              <div className="proof-text">"The interview prep is scary good. Three of the five questions it predicted came up verbatim in my actual interview. I got the offer."</div>
              <div className="proof-author">Business Intelligence Lead</div>
              <div className="proof-role">Vancouver, BC</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <div className="reveal">
          <h2 className="cta-title">Ready to apply smarter?</h2>
          <p className="cta-sub">Join thousands of job seekers who know their match before they apply.</p>
          <button className="btn-primary" style={{fontSize:16,padding:"16px 40px"}} onClick={onGetStarted}>
            Get started for free →
          </button>
          <p style={{marginTop:16,fontSize:12,color:"#4b5563"}}>5 free analyses per month. No credit card required.</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-logo">apply by <span>etlyx</span></div>
        <div className="footer-links">
          <a href="mailto:hello@etlyx.com" className="footer-link">hello@etlyx.com</a>
          <a href="https://etlyx.com" className="footer-link">etlyx.com</a>
          <a href="/privacy" className="footer-link">Privacy Policy</a>
          <a href="/terms" className="footer-link">Terms of Service</a>
        </div>
        <div className="footer-copy">© 2026 etlyx. All rights reserved.</div>
      </footer>
    </>
  );
}
