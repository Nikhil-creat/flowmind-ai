"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, FileText, Workflow, LogOut } from "lucide-react";

const links = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/documents", label: "Documents", icon: FileText },
  { href: "/dashboard/workflows", label: "Workflows", icon: Workflow },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  function logout() {
    localStorage.removeItem("flowmind_token");
    router.push("/login");
  }

  return (
    <aside className="w-56 shrink-0 bg-deep text-paper min-h-screen flex flex-col justify-between">
      <div>
        <div className="px-5 py-6">
          <span className="font-display text-lg">FlowMind AI</span>
        </div>
        <nav className="mt-4 flex flex-col gap-1 px-3">
          {links.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm ${
                  active ? "bg-white/10 text-signal" : "text-paper/80 hover:bg-white/5"
                }`}
              >
                <Icon size={16} />
                {label}
              </Link>
            );
          })}
        </nav>
      </div>
      <button onClick={logout} className="flex items-center gap-3 px-5 py-4 text-sm text-paper/70 hover:text-paper">
        <LogOut size={16} /> Log out
      </button>
    </aside>
  );
}
