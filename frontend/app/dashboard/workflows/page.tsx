"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { workflows, WorkflowItem } from "@/lib/api";

const BLANK_DEFINITION = {
  nodes: [{ id: "trigger", type: "trigger.manual", data: {}, position: { x: 50, y: 100 } }],
  edges: [],
};

// A ready-made pipeline that chains RAG (document_search), AI (ai_summarize),
// and automation (schedule trigger + send_email) into one working example -
// the three pillars of the project, wired together end to end.
const RAG_AI_AUTOMATION_TEMPLATE = {
  name: "Daily Document Digest (RAG + AI + Automation)",
  description:
    "Every morning: search your documents, summarize the results with AI, and email the digest - RAG, AI, and automation in a single pipeline.",
  definition: {
    nodes: [
      { id: "trigger", type: "trigger.schedule", data: { cron: "0 9 * * *" }, position: { x: 40, y: 120 } },
      { id: "search", type: "action.document_search", data: { query: "latest updates", k: 5 }, position: { x: 320, y: 40 } },
      { id: "summarize", type: "action.ai_summarize", data: { input: "{{search.output}}" }, position: { x: 600, y: 120 } },
      { id: "notify", type: "action.send_email", data: { to: "you@example.com", subject: "Your daily document digest", body: "{{summarize.output}}" }, position: { x: 880, y: 200 } },
    ],
    edges: [
      { source: "trigger", target: "search" },
      { source: "search", target: "summarize" },
      { source: "summarize", target: "notify" },
    ],
  },
};

export default function WorkflowsPage() {
  const [items, setItems] = useState<WorkflowItem[]>([]);
  const [creating, setCreating] = useState<"blank" | "template" | null>(null);

  function load() {
    workflows.list().then((res) => setItems(res.data));
  }
  useEffect(load, []);

  async function createWorkflow() {
    setCreating("blank");
    try {
      const res = await workflows.create({
        name: "Untitled workflow",
        description: "",
        definition: BLANK_DEFINITION,
        is_active: true,
      });
      window.location.href = `/dashboard/workflows/${res.data.id}`;
    } finally {
      setCreating(null);
    }
  }

  async function createFromTemplate() {
    setCreating("template");
    try {
      const res = await workflows.create({
        name: RAG_AI_AUTOMATION_TEMPLATE.name,
        description: RAG_AI_AUTOMATION_TEMPLATE.description,
        definition: RAG_AI_AUTOMATION_TEMPLATE.definition,
        is_active: true,
      });
      window.location.href = `/dashboard/workflows/${res.data.id}`;
    } finally {
      setCreating(null);
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="font-display text-3xl text-ink mb-1">Workflows</h1>
          <p className="text-slatetext">Trigger-and-action automations you build visually.</p>
        </div>
        <div className="flex gap-3">
          <button onClick={createFromTemplate} disabled={creating !== null} className="btn-signal">
            {creating === "template" ? "Creating..." : "Try RAG + AI + Automation template"}
          </button>
          <button onClick={createWorkflow} disabled={creating !== null} className="btn-primary">
            {creating === "blank" ? "Creating..." : "New workflow"}
          </button>
        </div>
      </div>

      <div className="space-y-3">
        {items.map((w) => (
          <div key={w.id} className="card p-4 flex justify-between items-center">
            <div>
              <Link href={`/dashboard/workflows/${w.id}`} className="text-ink font-medium hover:underline">
                {w.name}
              </Link>
              <p className="text-sm text-slatetext">
                {w.definition.nodes.length} nodes - {w.is_active ? "active" : "paused"}
              </p>
            </div>
            <div className="flex gap-3">
              <button onClick={() => workflows.run(w.id)} className="text-sm text-violet">Run now</button>
              <button onClick={() => workflows.remove(w.id).then(load)} className="text-sm text-coral">Delete</button>
            </div>
          </div>
        ))}
        {items.length === 0 && (
          <p className="text-slatetext text-sm">
            No workflows yet - try the RAG + AI + Automation template above to see all three pieces work together.
          </p>
        )}
      </div>
    </div>
  );
}
