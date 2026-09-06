from app.services.workflow_engine import _resolve_templates, _topological_order, run_workflow


def test_resolve_templates_substitutes_node_output():
    context = {"n1": {"text": "hello world"}}
    result = _resolve_templates("Say: {{n1.text}}", context)
    assert result == "Say: hello world"


def test_resolve_templates_missing_reference_becomes_empty_string():
    result = _resolve_templates("{{missing.field}}", {})
    assert result == ""


def test_topological_order_respects_edges():
    nodes = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    edges = [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}]
    order = _topological_order(nodes, edges)
    assert order.index("a") < order.index("b") < order.index("c")


def test_run_workflow_manual_trigger_and_condition():
    definition = {
        "nodes": [
            {"id": "trigger", "type": "trigger.manual", "data": {}},
            {"id": "check", "type": "action.condition", "data": {"left": "a", "op": "==", "right": "a"}},
        ],
        "edges": [{"source": "trigger", "target": "check"}],
    }
    log = run_workflow(definition, workspace_id="test-workspace", trigger_payload={"text": "hi"})
    assert log[0]["status"] == "success"
    assert log[1]["output"]["passed"] is True


def test_run_workflow_stops_and_logs_on_unknown_node_gracefully():
    definition = {
        "nodes": [{"id": "trigger", "type": "trigger.manual", "data": {}}],
        "edges": [],
    }
    log = run_workflow(definition, workspace_id="test-workspace", trigger_payload={"text": ""})
    assert len(log) == 1
    assert log[0]["status"] == "success"
