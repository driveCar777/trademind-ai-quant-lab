"""Minimal JSON knowledge graph. Not a graph database."""
from __future__ import print_function


def empty_graph():
    return {"nodes": [], "edges": []}


def add_node(graph, node_type, node_id, attrs=None):
    graph = dict(graph)
    nodes = list(graph.get("nodes") or [])
    nodes.append({"type": node_type, "id": node_id, "attrs": attrs or {}})
    graph["nodes"] = nodes
    return graph


def add_edge(graph, relation, src, dst):
    graph = dict(graph)
    edges = list(graph.get("edges") or [])
    edges.append({"relation": relation, "from": src, "to": dst})
    graph["edges"] = edges
    return graph


RELATIONS = (
    "USES_DATASET",
    "USES_FEATURE",
    "BELONGS_TO_FAMILY",
    "VALIDATED_BY",
    "FALSIFIED_BY",
    "DERIVED_FROM",
    "REJECTED_BY",
)
