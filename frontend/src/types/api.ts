export type Concept = {
  id: number;
  name: string;
  description?: string | null;
  frequency: number;
  created_at: string;
};

export type GraphNode = {
  id: string;
  label: string;
  frequency: number;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  relationship_type: string;
  weight: number;
};

export type GraphResponse = {
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type LearningPathStep = {
  concept_id: number;
  name: string;
  depth: number;
};

export type LearningPathResponse = {
  target_concept_id: number;
  steps: LearningPathStep[];
};

export type SearchResult = {
  concept_id: number;
  name: string;
  score: number;
  frequency: number;
};

export type UploadResult = {
  document: {
    id: number;
    filename: string;
    file_type: string;
    checksum: string;
    storage_path: string;
    status: string;
    created_at: string;
  };
  chunk_count: number;
  concept_count: number;
  relationship_count: number;
};

