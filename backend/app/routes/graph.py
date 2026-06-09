from __future__ import annotations

from fastapi import APIRouter

from ..graph.builder import build_concept_graph
from ..schemas import GraphEdge, GraphNode, GraphResponse


router = APIRouter(prefix="/api", tags=["graph"])


@router.get("/graph", response_model=GraphResponse)
def get_graph() -> GraphResponse:
    graph = build_concept_graph()
    nodes = [
        GraphNode(id=node_id, label=str(attrs["label"]), frequency=int(attrs["frequency"]))
        for node_id, attrs in graph.nodes(data=True)
    ]
    edges = [
        GraphEdge(
            id=str(attrs["id"]),
            source=str(source),
            target=str(target),
            relationship_type=str(attrs["relationship_type"]),
            weight=float(attrs["weight"]),
        )
        for source, target, attrs in graph.edges(data=True)
    ]
    return GraphResponse(nodes=nodes, edges=edges)

