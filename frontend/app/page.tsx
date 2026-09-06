import Link from "next/link";
import DeveloperSection from "@/components/DeveloperSection";

const pipeline = [
  { step: "01", title: "Drop in a document", body: "PDFs, notes, reports - FlowMind reads and indexes them in seconds.", accent: "text-violet" },
  { step: "02", title: "Ask it anything", body: "Get grounded answers pulled straight from your files, with sources attached.", accent: "text-cyan" },
  { step: "03", title: "Wire up an automation", body: "Connect triggers to actions - emails, webhooks, AI summaries - no code required.", accent: "text-amber" },
  { step: "04", title: "Let it run itself", body: "Schedules and webhooks keep your workflows firing while you do other work.", accent: "text-mint" },
];

const badges = [
  { label: "Claude + Gemini", dot: "bg-violet" },
  { label: "Real-time streaming", dot: "bg-cyan" },
  { label: "Redis-backed caching", dot: "bg-amber" },
  { label: "Google Sign-In", dot: "bg-mint" },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-paper">
      <header className="max-w-6xl mx-auto flex items-center justify-between px-6 py-6">
        <span className="font-display text-xl text-ink">FlowMind AI</span>
        <nav className="flex gap-3 items-center">
          <Link href="/login" className="px-4 py-2 text-slatetext">Log in</Link>
          <Link href="/signup" className="btn-primary">Get started</Link>
        </nav>
      </header>

      <section className="bg-hero-gradient text-white">
        <div className="max-w-6xl mx-auto px-6 pt-16 pb-20 grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="flex flex-wrap gap-2 mb-6">
              {badges.map((b) => (
                <span key={b.label} className="inline-flex items-center gap-2 bg-white/15 backdrop-blur-sm rounded-full px-3 py-1 text-xs font-medium">
                  <span className={`h-1.5 w-1.5 rounded-full ${b.dot}`} />
                  {b.label}
                </span>
              ))}
            </div>
            <h1 className="font-display font-semibold text-5xl leading-tight mb-6">
              Your documents, turned into answers and automations.
            </h1>
            <p className="text-white/85 text-lg leading-relaxed max-w-md mb-8">
              FlowMind AI reads what you give it and acts on what it learns - a document
              intelligence engine and a workflow automation builder, in one workspace.
            </p>
            <div className="flex gap-4">
              <Link href="/signup" className="bg-white text-ink font-semibold px-5 py-2.5 rounded-md">
                Create free account
              </Link>
              <Link href="/login" className="px-5 py-2.5 border border-white/40 rounded-md">
                I already have one
              </Link>
            </div>
          </div>

          <div className="card p-8 text-ink">
            <div className="space-y-5">
              {[
                { line: "Invoice_Q3.pdf indexed", dot: "bg-violet" },
                { line: "Ask: \"What's the payment term?\"", dot: "bg-cyan" },
                { line: "Workflow: notify finance@co.com", dot: "bg-amber" },
                { line: "Live answer streamed via WebSocket", dot: "bg-mint" },
              ].map((row, i) => (
                <div key={i} className="flex items-center gap-3">
                  <span className={`h-2 w-2 rounded-full shrink-0 ${row.dot}`} />
                  <span className="text-slatetext text-sm">{row.line}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="bg-ink text-paper">
        <div className="max-w-6xl mx-auto px-6 py-20">
          <h2 className="font-display text-3xl mb-12 max-w-lg">
            From a raw file to a running automation, in four steps.
          </h2>
          <div className="grid md:grid-cols-4 gap-8">
            {pipeline.map((p) => (
              <div key={p.step} className="border-t-2 border-white/15 pt-4">
                <span className={`font-display text-2xl ${p.accent}`}>{p.step}</span>
                <h3 className="font-medium mt-3 mb-2">{p.title}</h3>
                <p className="text-sm text-paper/70 leading-relaxed">{p.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <DeveloperSection />

      <footer className="max-w-6xl mx-auto px-6 py-10 flex items-center justify-between text-sm text-slatetext border-t border-mist">
        <span>FlowMind AI</span>
        <span>Built by Nikhil Chary Sriramoju</span>
      </footer>
    </main>
  );
}
