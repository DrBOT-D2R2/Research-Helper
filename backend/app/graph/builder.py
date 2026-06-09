from __future__ import annotations

import networkx as nx

from ..db import fetch_all


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

