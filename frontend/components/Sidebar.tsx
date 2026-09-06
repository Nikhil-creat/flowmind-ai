"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, FileText, Workflow, Users, LogOut, ChevronDown } from "lucide-react";
import { workspaces, WorkspaceItem } from "@/lib/api";

const links = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/documents", label: "Documents", icon: FileText },
  { href: "/dashboard/workflows", label: "Workflows", icon: Workflow },
  { href: "/dashboard/settings", label: "Team & Billing", icon: Users },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [list, setList] = useState<WorkspaceItem[]>([]);
  const [currentId, setCurrentId] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    workspaces.list().then((res) => {
      setList(res.data);
      const stored = localStorage.getItem("flowmind_workspace_id");
      const valid = res.data.find((w) => w.id === stored);
      const active = valid || res.data[0];
      if (active) {
        setCurrentId(active.id);
        localStorage.setItem("flowmind_workspace_id", active.id);
      }
    });
  }, []);

  function switchWorkspace(id: string) {
    localStorage.setItem("flowmind_workspace_id", id);
    setCurrentId(id);
    setOpen(false);
    window.location.href = "/dashboard"; // reload so every list refetches under the new workspace
  }

  function logout() {
    localStorage.removeItem("flowmind_token");
    localStorage.removeItem("flowmind_workspace_id");
    router.push("/login");
  }

  const current = list.find((w) => w.id === currentId);

  return (
    <aside className="w-56 shrink-0 bg-deep text-paper min-h-screen flex flex-col justify-between">
      <div>
        <div className="px-5 py-6">
          <span className="font-display text-lg">FlowMind AI</span>
        </div>

        <div className="px-3 mb-3 relative">
          <button
            onClick={() => setOpen(!open)}
            className="w-full flex items-center justify-between px-3 py-2 rounded-md bg-white/10 text-sm"
          >
            <span className="truncate">{current?.name || "Workspace"}</span>
            <ChevronDown size={14} />
          </button>
          {open && (
            <div className="absolute left-3 right-3 mt-1 bg-white text-ink rounded-md shadow-lg overflow-hidden z-10">
              {list.map((w) => (
                <button
                  key={w.id}
                  onClick={() => switchWorkspace(w.id)}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-mist flex items-center justify-between"
                >
                  {w.name}
                  <span className="text-xs text-slatetext">{w.role}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <nav className="mt-2 flex flex-col gap-1 px-3">
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
