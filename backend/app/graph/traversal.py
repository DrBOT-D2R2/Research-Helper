from __future__ import annotations

from collections import deque

from .builder import build_concept_graph


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

