const css = `
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0a0c10; color: #e8e4dc; font-family: 'DM Sans', sans-serif; }
.wrap { max-width: 760px; margin: 0 auto; padding: 80px 32px; }
.logo { font-family: 'Instrument Serif', serif; font-size: 20px; color: #e8e4dc; margin-bottom: 48px; display: block; text-decoration: none; }
.logo span { color: #c8a96e; }
h1 { font-family: 'Instrument Serif', serif; font-size: 40px; color: #e8e4dc; margin-bottom: 8px; }
.date { font-size: 13px; color: #6b7280; margin-bottom: 48px; }
h2 { font-size: 18px; font-weight: 600; color: #e8e4dc; margin: 36px 0 12px; }
p { font-size: 15px; color: #9ca3af; line-height: 1.8; margin-bottom: 14px; }
ul { padding-left: 20px; margin-bottom: 14px; }
li { font-size: 15px; color: #9ca3af; line-height: 1.8; margin-bottom: 6px; }
a { color: #c8a96e; text-decoration: none; }
a:hover { text-decoration: underline; }
.divider { border: none; border-top: 1px solid #1e2330; margin: 36px 0; }
.footer { margin-top: 64px; padding-top: 32px; border-top: 1px solid #1e2330; font-size: 13px; color: #4b5563; }
`;

export default function PrivacyPage() {
  return (
    <>
      <style>{css}</style>
      <div className="wrap">
        <a href="https://apply.etlyx.com" className="logo">apply by <span>etlyx</span></a>

        <h1>Privacy Policy</h1>
        <div className="date">Last updated: March 28, 2026</div>

        <p>apply by etlyx ("we", "our", or "us") operates the website at <a href="https://apply.etlyx.com">apply.etlyx.com</a>. This Privacy Policy explains how we collect, use, and protect your information when you use our service.</p>

        <h2>1. Information We Collect</h2>
        <p>We collect the following types of information:</p>
        <ul>
          <li><strong style={{color:"#e8e4dc"}}>Account information</strong> — your name and email address when you sign up via email or Google.</li>
          <li><strong style={{color:"#e8e4dc"}}>Resume content</strong> — the resume you upload is parsed and stored to power match analyses. This includes your work history, skills, and contact details.</li>
          <li><strong style={{color:"#e8e4dc"}}>Job descriptions</strong> — the job descriptions you paste are used to generate match analyses and are saved with your application tracker entries.</li>
          <li><strong style={{color:"#e8e4dc"}}>Payment information</strong> — if you subscribe to Pro, your payment is processed by Stripe. We do not store your credit card details — Stripe handles all payment data securely.</li>
          <li><strong style={{color:"#e8e4dc"}}>Usage data</strong> — we track how many match analyses you have used this month to enforce free tier limits.</li>
        </ul>

        <h2>2. How We Use Your Information</h2>
        <p>We use your information to:</p>
        <ul>
          <li>Provide and improve the apply by etlyx service</li>
          <li>Generate job match analyses, resume tweaks, interview prep, and cover letters using AI</li>
          <li>Manage your subscription and process payments via Stripe</li>
          <li>Send transactional emails (account confirmation, password reset)</li>
          <li>Enforce free tier usage limits</li>
        </ul>
        <p>We do not sell your personal data to third parties. We do not use your resume or job description data to train AI models.</p>

        <h2>3. AI Processing</h2>
        <p>Our service uses the Anthropic Claude API to analyze your resume against job descriptions and generate content. When you run an analysis, your resume content and the job description are sent to Anthropic's API for processing. Anthropic's privacy policy applies to this processing. We do not store raw API requests beyond what is needed to deliver your results.</p>

        <h2>4. Data Storage</h2>
        <p>Your account data, resume content, and saved applications are stored securely in Supabase, a cloud database provider. Data is stored in the United States. We use row-level security to ensure you can only access your own data.</p>

        <h2>5. Third-Party Services</h2>
        <p>We use the following third-party services:</p>
        <ul>
          <li><strong style={{color:"#e8e4dc"}}>Supabase</strong> — authentication and database storage</li>
          <li><strong style={{color:"#e8e4dc"}}>Anthropic</strong> — AI processing for match analyses and content generation</li>
          <li><strong style={{color:"#e8e4dc"}}>Stripe</strong> — payment processing for Pro subscriptions</li>
          <li><strong style={{color:"#e8e4dc"}}>Google</strong> — optional sign-in via Google OAuth</li>
          <li><strong style={{color:"#e8e4dc"}}>Render</strong> — web hosting</li>
        </ul>

        <h2>6. Data Retention</h2>
        <p>We retain your data as long as your account is active. If you delete your account, your data will be removed from our systems within 30 days. You can request deletion of your data at any time by emailing <a href="mailto:hello@etlyx.com">hello@etlyx.com</a>.</p>

        <h2>7. Your Rights</h2>
        <p>You have the right to:</p>
        <ul>
          <li>Access the personal data we hold about you</li>
          <li>Request correction of inaccurate data</li>
          <li>Request deletion of your data</li>
          <li>Export your data</li>
          <li>Withdraw consent at any time</li>
        </ul>
        <p>To exercise any of these rights, contact us at <a href="mailto:hello@etlyx.com">hello@etlyx.com</a>.</p>

        <h2>8. Cookies</h2>
        <p>We use minimal cookies necessary to keep you logged in (authentication session cookies). We do not use advertising or tracking cookies.</p>

        <h2>9. Children's Privacy</h2>
        <p>Our service is not directed at children under 13. We do not knowingly collect personal information from children under 13.</p>

        <h2>10. Changes to This Policy</h2>
        <p>We may update this Privacy Policy from time to time. We will notify you of significant changes by posting the new policy on this page with an updated date.</p>

        <h2>11. Contact Us</h2>
        <p>If you have questions about this Privacy Policy, contact us at:<br />
        <a href="mailto:hello@etlyx.com">hello@etlyx.com</a><br />
        etlyx — Montreal, Quebec, Canada</p>

        <div className="footer">
          © 2026 etlyx. All rights reserved. ·{" "}
          <a href="/terms">Terms of Service</a> ·{" "}
          <a href="https://apply.etlyx.com">Back to app</a>
        </div>
      </div>
    </>
  );
}
