# UX

## Main Screens

### Dashboard

- Shows ingestion summary, concept count, relationship count, and recent uploads
- Acts as the landing page for a single-user local app

### Upload

- Drag-and-drop or select files
- Shows validation feedback and ingestion result metrics

### Graph Explorer

- Renders concepts and edges with React Flow
- Supports clicking a node to inspect concept details

### Concept Explorer

- Search-first list of concepts
- Displays related concepts and source evidence counts

### Learning Path

- User selects a target concept
- The app returns an ordered prerequisite path and rationale labels

## Primary User Journeys

1. Upload a document, wait for ingestion, then open Graph Explorer to verify extracted ideas.
2. Search for a concept, inspect its neighbors, and identify prerequisite topics.
3. Choose a target concept and generate a learning path for study planning.

## MVP UX Constraints

- No login or onboarding wizard
- Keep controls obvious and task-oriented
- Favor inspectability over automation magic

