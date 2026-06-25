from __future__ import annotations

from collections import deque
import networkx as nx

from .database import fetch_all

def build_concept_graph() -> nx.DiGraph:
    graph = nx.DiGraph()

    concepts = fetch_all("SELECT id, name, frequency FROM concepts ORDER BY name")
    for concept in concepts:
        graph.add_node(str(concept["id"]), label=concept["name"], frequency=concept["frequency"])

    edges = fetch_all(
        """
        SELECT id, source_concept_id, target_concept_id, relationship_type, weight
        FROM concept_relationships
        """
    )
    for edge in edges:
        graph.add_edge(
            str(edge["source_concept_id"]),
            str(edge["target_concept_id"]),
            id=str(edge["id"]),
            relationship_type=edge["relationship_type"],
            weight=edge["weight"],
        )
    return graph

def prerequisite_path(target_concept_id: int, depth: int = 5) -> list[dict[str, int | str]]:
    graph = build_concept_graph()
    target = str(target_concept_id)
    if target not in graph:
        return []

    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(target, 0)])
    steps: list[dict[str, int | str]] = []

    while queue:
        node, current_depth = queue.popleft()
        if node in visited or current_depth > depth:
            continue
        visited.add(node)
        steps.append(
            {
                "concept_id": int(node),
                "name": str(graph.nodes[node]["label"]),
                "depth": current_depth,
            }
        )
        for predecessor in graph.predecessors(node):
            queue.append((predecessor, current_depth + 1))

    steps.sort(key=lambda item: (int(item["depth"]), str(item["name"])))
    return steps
