import { Github, Linkedin, Mail, Phone, Instagram, Facebook } from "lucide-react";

const links = [
  {
    label: "GitHub",
    value: "Nikhil-creat",
    href: "https://github.com/Nikhil-creat",
    icon: Github,
    accent: "bg-violet/10 text-violet",
  },
  {
    label: "LinkedIn",
    value: "nikhil-chary-sriramoju",
    href: "https://in.linkedin.com/in/nikhil-chary-sriramoju-95041b38a",
    icon: Linkedin,
    accent: "bg-cyan/10 text-cyan",
  },
  {
    label: "Email",
    value: "sriramojunikhil66@gmail.com",
    href: "mailto:sriramojunikhil66@gmail.com",
    icon: Mail,
    accent: "bg-amber/10 text-amber",
  },
  {
    label: "Mobile",
    value: "+91 63005 56302",
    href: "tel:+916300556302",
    icon: Phone,
    accent: "bg-mint/10 text-mint",
  },
  {
    label: "Instagram",
    value: "@nikhil__sriramoju",
    href: "https://www.instagram.com/nikhil__sriramoju",
    icon: Instagram,
    accent: "bg-coral/10 text-coral",
  },
  {
    label: "Facebook",
    value: "Profile",
    href: "https://www.facebook.com/profile.php?id=100079201124141",
    icon: Facebook,
    accent: "bg-violet/10 text-violet",
  },
];

export default function DeveloperSection() {
  return (
    <section className="max-w-6xl mx-auto px-6 py-20">
      <div className="grid md:grid-cols-[1fr_1.4fr] gap-10 items-start">
        <div>
          <span className="text-sm font-medium text-cyan">Built &amp; maintained by</span>
          <h2 className="font-display text-3xl text-ink mt-2 mb-3">Nikhil Chary Sriramoju</h2>
          <p className="text-slatetext leading-relaxed max-w-sm">
            Final-year BTech CSE student building FlowMind AI as a full-stack, AI-and-automation
            major project - open to internships, collaborations, and feedback.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 gap-3">
          {links.map(({ label, value, href, icon: Icon, accent }) => (
            <a
              key={label}
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="card p-4 flex items-center gap-3 hover:-translate-y-0.5 transition-transform"
            >
              <span className={`h-9 w-9 rounded-md flex items-center justify-center shrink-0 ${accent}`}>
                <Icon size={18} />
              </span>
              <span>
                <span className="block text-xs text-slatetext">{label}</span>
                <span className="block text-sm text-ink font-medium">{value}</span>
              </span>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
