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
.footer { margin-top: 64px; padding-top: 32px; border-top: 1px solid #1e2330; font-size: 13px; color: #4b5563; }
`;

export default function TermsPage() {
  return (
    <>
      <style>{css}</style>
      <div className="wrap">
        <a href="https://apply.etlyx.com" className="logo">apply by <span>etlyx</span></a>

        <h1>Terms of Service</h1>
        <div className="date">Last updated: March 28, 2026</div>

        <p>These Terms of Service ("Terms") govern your use of apply by etlyx, operated by etlyx ("we", "our", or "us"). By using our service, you agree to these Terms.</p>

        <h2>1. The Service</h2>
        <p>apply by etlyx is an AI-powered tool that helps job seekers analyze their fit for job opportunities, generate tailored cover letters, prepare for interviews, and improve their resumes. The service is available at <a href="https://apply.etlyx.com">apply.etlyx.com</a>.</p>

        <h2>2. Accounts</h2>
        <p>You must create an account to use the service. You are responsible for maintaining the security of your account and password. You must provide accurate information when creating your account. You must be at least 13 years old to use the service.</p>

        <h2>3. Free and Pro Plans</h2>
        <p>We offer two plans:</p>
        <ul>
          <li><strong style={{color:"#e8e4dc"}}>Free plan</strong> — 5 job match analyses per month at no cost. No credit card required.</li>
          <li><strong style={{color:"#e8e4dc"}}>Pro plan</strong> — unlimited analyses plus resume tweaks, interview prep, and cover letter generation for $15 CAD per month, billed monthly.</li>
        </ul>
        <p>Free plan limits reset on the first day of each calendar month. We reserve the right to change pricing with 30 days notice.</p>

        <h2>4. Payments and Cancellation</h2>
        <p>Pro subscriptions are billed monthly via Stripe. You may cancel at any time through your Account page. Cancellation takes effect at the end of your current billing period — you retain Pro access until then. We do not offer refunds for partial months.</p>

        <h2>5. AI-Generated Content</h2>
        <p>Our service uses AI to generate match analyses, resume suggestions, cover letters, and interview preparation content. This content is provided for informational purposes only. We do not guarantee that AI-generated content will result in job interviews or offers. You are responsible for reviewing and verifying all AI-generated content before using it in job applications.</p>

        <h2>6. Your Content</h2>
        <p>You retain ownership of your resume, job descriptions, and other content you upload or paste into the service. By using the service, you grant us a limited license to process your content to provide the service. We do not use your content to train AI models or share it with third parties except as necessary to provide the service (e.g., sending to Anthropic's API for processing).</p>

        <h2>7. Acceptable Use</h2>
        <p>You agree not to:</p>
        <ul>
          <li>Use the service for any unlawful purpose</li>
          <li>Attempt to circumvent usage limits or access controls</li>
          <li>Upload malicious content or attempt to compromise the service</li>
          <li>Resell or redistribute the service without permission</li>
          <li>Use the service to generate misleading or fraudulent application materials</li>
        </ul>

        <h2>8. Availability</h2>
        <p>We aim to keep the service available at all times but cannot guarantee uninterrupted access. We may perform maintenance, experience outages, or modify the service at any time. We are not liable for any losses resulting from service unavailability.</p>

        <h2>9. Disclaimer of Warranties</h2>
        <p>The service is provided "as is" without warranties of any kind. We do not warrant that the service will be error-free, that AI-generated content will be accurate or suitable for your needs, or that using the service will result in employment outcomes.</p>

        <h2>10. Limitation of Liability</h2>
        <p>To the maximum extent permitted by law, etlyx shall not be liable for any indirect, incidental, or consequential damages arising from your use of the service. Our total liability to you shall not exceed the amount you paid us in the 3 months preceding the claim.</p>

        <h2>11. Changes to These Terms</h2>
        <p>We may update these Terms from time to time. Continued use of the service after changes constitutes acceptance of the new Terms. We will notify you of significant changes by email or via the service.</p>

        <h2>12. Governing Law</h2>
        <p>These Terms are governed by the laws of the Province of Quebec, Canada. Any disputes shall be resolved in the courts of Quebec.</p>

        <h2>13. Contact</h2>
        <p>Questions about these Terms? Contact us at:<br />
        <a href="mailto:hello@etlyx.com">hello@etlyx.com</a><br />
        etlyx — Montreal, Quebec, Canada</p>

        <div className="footer">
          © 2026 etlyx. All rights reserved. ·{" "}
          <a href="/privacy">Privacy Policy</a> ·{" "}
          <a href="https://apply.etlyx.com">Back to app</a>
        </div>
      </div>
    </>
  );
}
