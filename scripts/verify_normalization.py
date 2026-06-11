import sys
import os
import re
from pathlib import Path
from collections import Counter

# Add the project root to sys.path
sys.path.append(os.getcwd())

from backend.app.pipeline import parse_document, normalize_concept, is_valid_concept, get_nlp

def verify_normalization(file_path: str):
    path = Path(file_path)
    if not path.exists():
        print(f"File {file_path} not found.")
        return

    print(f"Processing {file_path}...")
    text = parse_document(path)
    nlp = get_nlp()
    doc = nlp(text)

    original_candidates = []
    
    # Track entities
    for ent in doc.ents:
        if len(ent.text.strip()) > 2:
            original_candidates.append(ent.text.strip())

    # Track noun chunks
    if doc.has_annotation("DEP"):
        for chunk in doc.noun_chunks:
            if not chunk.root.is_stop and len(chunk.text.strip()) > 2:
                original_candidates.append(chunk.text.strip())

    print(f"Extracted {len(original_candidates)} raw candidates.")

    # Show some examples of raw vs normalized
    unique_raw = sorted(list(set(original_candidates)))
    print("\n--- Normalization Examples ---")
    examples = [c for c in unique_raw if any(c.lower().startswith(art) for art in ["a ", "an ", "the "])][:10]
    for ex in examples:
        print(f"Raw: '{ex}' -> Normalized: '{normalize_concept(ex)}'")

    # Perform full normalization and filtering
    normalized_counts = Counter()
    ner_names = set() # We'll just assume none for this simple count check or track them
    
    # We'll just do a pass to see what stays
    for raw in original_candidates:
        norm = normalize_concept(raw)
        normalized_counts[norm] += 1

    before_filter_count = len(normalized_counts)
    
    final_concepts = {}
    removed_concepts = []
    
    for name, count in normalized_counts.items():
        if is_valid_concept(name, count, False): # Simplified is_ner=False
            final_concepts[name] = count
        else:
            removed_concepts.append(name)

    print("\n--- Results ---")
    print(f"Original unique candidates: {len(unique_raw)}")
    print(f"Normalized unique candidates: {before_filter_count}")
    print(f"Final concept count (after filtering): {len(final_concepts)}")
    print(f"Concepts removed: {len(removed_concepts)}")
    
    print("\nTop 20 Concepts:")
    top_20 = sorted(final_concepts.items(), key=lambda x: x[1], reverse=True)[:20]
    for name, count in top_20:
        print(f"- {name} ({count})")

    print("\n--- Target Concept Check ---")
    targets = ["standing wave", "transverse wave", "wavelength", "frequency", "amplitude", "node", "antinode", "tension", "wave speed", "superposition"]
    for t in targets:
        norm_t = normalize_concept(t)
        count = final_concepts.get(norm_t, 0)
        status = "OK" if count > 0 else "MISSING/FILTERED"
        print(f"Target: '{t}' (Norm: '{norm_t}') -> Count: {count} [{status}]")

if __name__ == "__main__":
    pdf_path = "data/uploads/wave-on-strings-3.0-with-practice-2.pdf"
    verify_normalization(pdf_path)
