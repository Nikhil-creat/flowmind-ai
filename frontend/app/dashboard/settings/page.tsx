"use client";

import { useEffect, useState } from "react";
import { workspaces, MemberItem, WorkspaceItem } from "@/lib/api";

export default function SettingsPage() {
  const [workspace, setWorkspace] = useState<WorkspaceItem | null>(null);
  const [members, setMembers] = useState<MemberItem[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [checkoutMessage, setCheckoutMessage] = useState<string | null>(null);

  function load() {
    workspaces.list().then((res) => {
      const id = localStorage.getItem("flowmind_workspace_id");
      const ws = res.data.find((w) => w.id === id) || res.data[0];
      setWorkspace(ws || null);
      if (ws) workspaces.members(ws.id).then((m) => setMembers(m.data));
    });
  }
  useEffect(load, []);

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    if (!workspace) return;
    setInviteError(null);
    try {
      await workspaces.invite(workspace.id, { email: inviteEmail, role: inviteRole });
      setInviteEmail("");
      load();
    } catch (err: any) {
      setInviteError(err?.response?.data?.detail || "Couldn't invite that email.");
    }
  }

  async function handleUpgrade() {
    if (!workspace) return;
    const res = await workspaces.checkout(workspace.id);
    if (res.data.checkout_url) {
      window.location.href = res.data.checkout_url;
    } else {
      setCheckoutMessage(res.data.message);
    }
  }

  const isOwner = workspace?.role === "owner";
  const canManage = workspace?.role === "owner" || workspace?.role === "admin";

  return (
    <div className="max-w-3xl">
      <h1 className="font-display text-3xl text-ink mb-1">Team & Billing</h1>
      <p className="text-slatetext mb-8">Manage who has access to {workspace?.name || "this workspace"}.</p>

      <div className="card p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-medium text-ink">Plan</h2>
          <span className={`text-xs px-2 py-1 rounded-full ${workspace?.plan === "pro" ? "bg-mint/15 text-mint" : "bg-mist text-slatetext"}`}>
            {workspace?.plan === "pro" ? "Pro" : "Free"}
          </span>
        </div>
        {workspace?.plan !== "pro" && (
          <>
            <p className="text-sm text-slatetext mb-4">
              Upgrade for unlimited teammates, higher rate limits, and priority AI throughput.
            </p>
            {isOwner ? (
              <button onClick={handleUpgrade} className="btn-signal">Upgrade to Pro</button>
            ) : (
              <p className="text-xs text-slatetext">Only the workspace owner can manage billing.</p>
            )}
            {checkoutMessage && <p className="text-xs text-slatetext mt-3">{checkoutMessage}</p>}
          </>
        )}
      </div>

      <div className="card p-6">
        <h2 className="font-medium text-ink mb-4">Members</h2>
        <div className="space-y-3 mb-6">
          {members.map((m) => (
            <div key={m.user_id} className="flex items-center justify-between text-sm">
              <div>
                <p className="text-ink">{m.full_name}</p>
                <p className="text-slatetext text-xs">{m.email}</p>
              </div>
              <span className="text-xs px-2 py-1 rounded-full bg-mist text-slatetext capitalize">{m.role}</span>
            </div>
          ))}
        </div>

        {canManage && (
          <form onSubmit={handleInvite} className="flex gap-2 items-end">
            <div className="flex-1">
              <label className="text-xs text-slatetext block mb-1">Invite by email</label>
              <input
                type="email"
                required
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="teammate@company.com"
              />
            </div>
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="border border-mist rounded-md px-2 py-2 text-sm"
            >
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
            <button type="submit" className="btn-primary shrink-0">Invite</button>
          </form>
        )}
        {inviteError && <p className="text-sm text-coral mt-2">{inviteError}</p>}
        <p className="text-xs text-slatetext mt-3">
          They need a FlowMind account already - ask them to sign up first, then invite their email.
        </p>
      </div>
    </div>
  );
}
