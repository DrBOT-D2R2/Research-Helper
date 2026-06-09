import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { GraphResponse } from "../../types/api";

type GraphCanvasProps = {
  graph: GraphResponse;
};

export default function GraphCanvas({ graph }: GraphCanvasProps) {
  const nodes: Node[] = graph.nodes.map((node, index) => ({
    id: node.id,
    data: { label: `${node.label} (${node.frequency})` },
    position: {
      x: 120 + (index % 4) * 220,
      y: 120 + Math.floor(index / 4) * 140,
    },
    style: {
      background: "#f4f1e8",
      border: "1px solid #ab8d57",
      borderRadius: 14,
      padding: 10,
      width: 180,
    },
  }));

  const edges: Edge[] = graph.edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.relationship_type,
  }));

  return (
    <div className="graph-canvas">
      <ReactFlow fitView nodes={nodes} edges={edges}>
        <MiniMap />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
}

