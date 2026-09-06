"""
A small but real automation engine, in the spirit of Zapier/n8n:

A Workflow.definition looks like:
{
  "nodes": [
    {"id": "n1", "type": "trigger.manual", "data": {}},
    {"id": "n2", "type": "action.ai_summarize", "data": {"input": "{{n1.text}}"}},
    {"id": "n3", "type": "action.send_email", "data": {"to": "you@x.com",
        "subject": "Summary", "body": "{{n2.output}}"}}
  ],
  "edges": [{"source": "n1", "target": "n2"}, {"source": "n2", "target": "n3"}]
}

Execution walks the DAG in topological order, resolves "{{node_id.field}}"
placeholders against prior node outputs, and runs each node's handler.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import httpx

from app.core.config import get_settings
from app.services import ai_provider, mailer, rag

settings = get_settings()

TEMPLATE_RE = re.compile(r"\{\{\s*([\w\-]+)\.([\w\-]+)\s*\}\}")


def _resolve_templates(value: Any, context: dict[str, dict[str, Any]]) -> Any:
    if isinstance(value, str):
        def replace(match: re.Match) -> str:
            node_id, field = match.group(1), match.group(2)
            return str(context.get(node_id, {}).get(field, ""))
        return TEMPLATE_RE.sub(replace, value)
    if isinstance(value, dict):
        return {k: _resolve_templates(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_templates(v, context) for v in value]
    return value


def _topological_order(nodes: list[dict], edges: list[dict]) -> list[str]:
    node_ids = [n["id"] for n in nodes]
    incoming = {nid: set() for nid in node_ids}
    for e in edges:
        incoming[e["target"]].add(e["source"])

    ordered: list[str] = []
    remaining = set(node_ids)
    while remaining:
        ready = [nid for nid in remaining if incoming[nid] <= set(ordered)]
        if not ready:
            # Cycle or bad edge - bail out with whatever's left, in given order
            ordered.extend(sorted(remaining))
            break
        ready.sort()
        ordered.extend(ready)
        remaining -= set(ready)
    return ordered


def _run_node(node: dict, context: dict[str, dict[str, Any]], user_id: str, trigger_payload: dict) -> dict[str, Any]:
    node_type = node["type"]
    data = _resolve_templates(node.get("data", {}), context)

    if node_type.startswith("trigger."):
        # Triggers simply surface the payload that started the run.
        return {**trigger_payload}

    if node_type == "action.http_request":
        method = data.get("method", "GET").upper()
        with httpx.Client(timeout=15) as client:
            resp = client.request(method, data["url"], json=data.get("json"), headers=data.get("headers"))
        return {"status_code": resp.status_code, "output": resp.text[:2000]}

    if node_type == "action.send_email":
        mailer.send_email(to=data["to"], subject=data.get("subject", "Notification"), body=data.get("body", ""))
        return {"output": f"email sent to {data['to']}"}

    if node_type == "action.ai_summarize":
        text = data.get("input", "")
        result = ai_provider.generate(f"Summarize this in 2-3 sentences:\n\n{text}", max_tokens=250)
        summary = result["text"] or rag.summarize_text(text)
        return {"output": summary, "ai_provider": result["provider"] or "extractive"}

    if node_type == "action.document_search":
        hits = rag.search(user_id, data.get("query", ""), k=data.get("k", 3))
        joined = "\n".join(h["snippet"] for h in hits)
        return {"output": joined, "hit_count": len(hits)}

    if node_type == "action.condition":
        left, op, right = data.get("left"), data.get("op", "=="), data.get("right")
        ops = {"==": lambda a, b: str(a) == str(b), "!=": lambda a, b: str(a) != str(b),
               "contains": lambda a, b: str(b) in str(a)}
        passed = ops.get(op, ops["=="])(left, right)
        return {"output": passed, "passed": passed}

    return {"output": None, "error": f"unknown node type: {node_type}"}


def run_workflow(definition: dict, user_id: str, trigger_payload: dict | None = None) -> list[dict[str, Any]]:
    """Execute every node in topological order and return a step-by-step log."""
    nodes = {n["id"]: n for n in definition.get("nodes", [])}
    edges = definition.get("edges", [])
    order = _topological_order(list(nodes.values()), edges)

    context: dict[str, dict[str, Any]] = {}
    log: list[dict[str, Any]] = []

    for node_id in order:
        node = nodes[node_id]
        started = datetime.utcnow().isoformat()
        try:
            output = _run_node(node, context, user_id, trigger_payload or {})
            context[node_id] = output
            log.append({"node_id": node_id, "type": node["type"], "status": "success",
                        "output": output, "started_at": started})
        except Exception as exc:  # noqa: BLE001
            log.append({"node_id": node_id, "type": node["type"], "status": "failed",
                        "error": str(exc), "started_at": started})
            break

    return log
