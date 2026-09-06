"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import ReactFlow, {
  addEdge, applyEdgeChanges, applyNodeChanges, Background, Connection,
  Controls, Edge, EdgeChange, Node, NodeChange,
} from "reactflow";
import "reactflow/dist/style.css";
import { workflows } from "@/lib/api";

const NODE_TYPES = [
  { type: "trigger.manual", label: "Trigger: Manual" },
  { type: "trigger.schedule", label: "Trigger: Schedule", defaultData: { cron: "0 9 * * *" } },
  { type: "trigger.webhook", label: "Trigger: Webhook" },
  { type: "action.document_search", label: "Action: Search documents", defaultData: { query: "", k: 3 } },
  { type: "action.ai_summarize", label: "Action: AI summarize", defaultData: { input: "" } },
  { type: "action.send_email", label: "Action: Send email", defaultData: { to: "", subject: "", body: "" } },
  { type: "action.http_request", label: "Action: HTTP request", defaultData: { method: "GET", url: "" } },
  { type: "action.condition", label: "Action: Condition", defaultData: { left: "", op: "==", right: "" } },
];

export default function WorkflowBuilderPage() {
  const params = useParams();
  const workflowId = params.id as string;

  const [name, setName] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [runs, setRuns] = useState<any[]>([]);

  useEffect(() => {
    workflows.get(workflowId).then((res) => {
      const wf = res.data;
      setName(wf.name);
      setIsActive(wf.is_active);
      setNodes(
        wf.definition.nodes.map((n: any) => ({
          id: n.id,
          type: "default",
          data: { label: n.type, nodeType: n.type, payload: n.data },
          position: n.position || { x: 100, y: 100 },
        }))
      );
      setEdges(wf.definition.edges.map((e: any) => ({ id: `${e.source}-${e.target}`, ...e })));
    });
    workflows.runs(workflowId).then((res) => setRuns(res.data));
  }, [workflowId]);

  const onNodesChange = useCallback((changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);
  const onConnect = useCallback((connection: Connection) => setEdges((eds) => addEdge(connection, eds)), []);

  function addNode(nodeType: string, defaultData: any = {}) {
    const id = `${nodeType.split(".")[1]}_${Date.now().toString(36)}`;
    setNodes((nds) => [
      ...nds,
      {
        id,
        type: "default",
        data: { label: nodeType, nodeType, payload: defaultData },
        position: { x: 120 + nds.length * 40, y: 80 + nds.length * 60 },
      },
    ]);
  }

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);

  function updateSelectedNodePayload(raw: string) {
    if (!selectedNodeId) return;
    try {
      const payload = JSON.parse(raw);
      setNodes((nds) => nds.map((n) => (n.id === selectedNodeId ? { ...n, data: { ...n.data, payload } } : n)));
    } catch {
      // ignore invalid JSON while typing
    }
  }

  async function save() {
    setSaving(true);
    try {
      const definition = {
        nodes: nodes.map((n) => ({ id: n.id, type: n.data.nodeType, data: n.data.payload, position: n.position })),
        edges: edges.map((e) => ({ source: e.source, target: e.target })),
      };
      await workflows.update(workflowId, { name, is_active: isActive, definition });
    } finally {
      setSaving(false);
    }
  }

  async function runNow() {
    await save();
    await workflows.run(workflowId);
    const res = await workflows.runs(workflowId);
    setRuns(res.data);
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="font-display text-2xl text-ink border-none bg-transparent px-0"
        />
        <div className="flex gap-3 items-center">
          <label className="text-sm text-slatetext flex items-center gap-2">
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} className="w-auto" />
            Active
          </label>
          <button onClick={save} disabled={saving} className="px-4 py-2 border border-mist rounded-md text-sm">
            {saving ? "Saving..." : "Save"}
          </button>
          <button onClick={runNow} className="btn-signal text-sm">Run now</button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-[200px_1fr_260px] gap-4 min-h-0">
        <div className="card p-3 overflow-y-auto">
          <p className="text-xs text-slatetext mb-2 uppercase tracking-wide">Add node</p>
          <div className="flex flex-col gap-2">
            {NODE_TYPES.map((n) => (
              <button
                key={n.type}
                onClick={() => addNode(n.type, n.defaultData || {})}
                className="text-left text-sm px-2 py-1.5 rounded-md hover:bg-mist"
              >
                {n.label}
              </button>
            ))}
          </div>
        </div>

        <div className="card overflow-hidden">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, node) => setSelectedNodeId(node.id)}
            fitView
          >
            <Background />
            <Controls />
          </ReactFlow>
        </div>

        <div className="card p-4 overflow-y-auto">
          {selectedNode ? (
            <>
              <p className="text-xs text-slatetext mb-1 uppercase tracking-wide">{selectedNode.data.nodeType}</p>
              <textarea
                className="h-40 font-mono text-xs"
                defaultValue={JSON.stringify(selectedNode.data.payload, null, 2)}
                onBlur={(e) => updateSelectedNodePayload(e.target.value)}
              />
              <p className="text-xs text-slatetext mt-2">
                Use <code>{"{{node_id.field}}"}</code> to reference another node's output.
              </p>
            </>
          ) : (
            <p className="text-sm text-slatetext">Select a node to edit its configuration.</p>
          )}

          <div className="mt-6">
            <p className="text-xs text-slatetext mb-2 uppercase tracking-wide">Recent runs</p>
            <div className="space-y-2">
              {runs.map((r) => (
                <div key={r.id} className="text-sm">
                  <span className={r.status === "success" ? "text-deep" : "text-red-600"}>{r.status}</span>
                  <span className="text-slatetext"> - {r.trigger_type} - {new Date(r.started_at).toLocaleString()}</span>
                </div>
              ))}
              {runs.length === 0 && <p className="text-sm text-slatetext">No runs yet.</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
