import type { ReactNode } from 'react'
import { ArrowLeft, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'

const lastUpdated = 'October 27, 2026'
const githubUrl = 'https://github.com/sharadvyas123/AdaptEd_Shifu'

function LegalShell({ title, eyebrow, summary, children }: { title: string; eyebrow: string; summary: string; children: ReactNode }) {
  return <main className="phase-shell"><header className="phase-nav"><Link to="/" className="brand-mark-lockup" aria-label="AdaptEd home"><span className="brand-symbol">A</span><span>Adapt<span className="brand-dot">Ed</span></span></Link><span className="phase-nav-note"><span className="live-dot" /> PROJECT INFORMATION</span><Link className="legal-back" to="/"><ArrowLeft size={14} /> Back to AdaptEd</Link></header><div className="phase-main legal-main"><article className="legal-document"><div className="section-kicker">{eyebrow}</div><h1>{title}</h1><p className="legal-summary">{summary}</p><p className="legal-updated">Last updated {lastUpdated}</p><div className="legal-sections">{children}</div><div className="legal-contact"><span className="legal-contact-mark"><Sparkles size={17} /></span><div><b>Questions about this page?</b><p>Contact the AdaptEd team through the project repository.</p></div><a href={githubUrl} target="_blank" rel="noreferrer" aria-label="Open AdaptEd project on GitHub"><span className="github-mark" aria-hidden="true">GH</span></a></div></article></div><footer className="phase-footer"><span>AdaptEd © 2026</span><nav className="phase-footer-links" aria-label="Policies and project links"><Link to="/terms">Terms &amp; Conditions</Link><Link to="/privacy">Privacy Policy</Link><a href={githubUrl} target="_blank" rel="noreferrer"><span className="github-mark" aria-hidden="true">GH</span> GitHub</a></nav><span>Built for focused learning <Sparkles size={13} /></span></footer></main>
}

export function PrivacyPage() {
  return <LegalShell eyebrow="PRIVACY POLICY" title="Your learning data stays yours." summary="This page describes how information is handled in the current AdaptEd frontend preview.">
    <section><span className="legal-number">01</span><div><h2>What this version stores</h2><p>The current frontend stores a local demo session and classroom records in your browser's local storage. These records can include your name and email, classroom name and invite code, class level, academic year, exam target, selected subjects, and classroom membership details. Passwords are not stored by the local demo sign-in flow.</p></div></section>
    <section><span className="legal-number">02</span><div><h2>Where information is kept</h2><p>In this preview, session and classroom records are kept on the device and browser where you use AdaptEd. The authentication and classroom services currently use local browser storage; they do not call an application backend. Clearing this browser's site data removes those local records.</p></div></section>
    <section><span className="legal-number">03</span><div><h2>Google sign-in and connected services</h2><p>Google OAuth is not configured in this build. Selecting Google sign-in reports that configuration is missing and does not send you through a Google authentication flow. No connected analytics or third-party learning service is configured by this frontend.</p></div></section>
    <section><span className="legal-number">04</span><div><h2>Demo information</h2><p>Some classroom and learner examples are synthetic demo data. Do not enter real student records, passwords, or sensitive personal information into this preview. Local demo data should not be treated as a secure account or school record.</p></div></section>
    <section><span className="legal-number">05</span><div><h2>Changes to this policy</h2><p>When AdaptEd adds a backend, authentication provider, analytics, or other service that handles personal information, this policy should be updated to explain what is collected, why it is used, where it is stored, and how users can contact the team.</p></div></section>
  </LegalShell>
}

export function TermsPage() {
  return <LegalShell eyebrow="TERMS & CONDITIONS" title="A clear start for your learning." summary="These terms apply to the current AdaptEd frontend preview and its local demo features.">
    <section><span className="legal-number">01</span><div><h2>Preview service</h2><p>AdaptEd is an evolving educational product preview. Sign-in and classroom creation or joining currently operate with local demo data in your browser. They do not create a verified online account or shared classroom on a server.</p></div></section>
    <section><span className="legal-number">02</span><div><h2>Educational information</h2><p>Learning paths, practice content, progress indicators, and recommendations are intended to support study. They are not official exam guidance and should not replace a teacher's judgment or a learner's own review.</p></div></section>
    <section><span className="legal-number">03</span><div><h2>Use of the preview</h2><p>Use the preview lawfully and do not attempt to disrupt or gain unauthorized access to it. Do not submit confidential, sensitive, or real student information. You are responsible for any information you enter into your local browser session.</p></div></section>
    <section><span className="legal-number">04</span><div><h2>Demo content and availability</h2><p>Examples may be synthetic and features may change as the team develops the product. The preview is provided for evaluation and may be unavailable or altered without notice.</p></div></section>
    <section><span className="legal-number">05</span><div><h2>Future services</h2><p>Production accounts, classroom sharing, Google sign-in, and backend data services are not configured in this build. If those services are introduced, the team should provide updated terms and privacy information before enabling them.</p></div></section>
  </LegalShell>
}
