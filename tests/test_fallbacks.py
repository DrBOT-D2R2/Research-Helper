from __future__ import annotations

import pytest

from backend.app.pipeline import MockModel, MockNLP, cosine_similarity, extract_concepts


def test_mock_nlp() -> None:
    nlp = MockNLP()
    doc = nlp("This is a simple sentence. Artificial Intelligence and Neural Networks are cool.")

    assert len(doc.sents) == 2
    assert doc.sents[0].text == "This is a simple sentence."
    assert doc.sents[1].text == "Artificial Intelligence and Neural Networks are cool."

    # Capitalized entity extraction
    ents = [e.text for e in doc.ents]
    assert "Artificial Intelligence" in ents
    assert "Neural Networks" in ents

    # Noun chunks
    noun_chunks = [nc.text for nc in doc.noun_chunks]
    assert any("sentence" in chunk.lower() for chunk in noun_chunks)
    assert any("intelligence" in chunk.lower() for chunk in noun_chunks)


def test_mock_model() -> None:
    model = MockModel()

    # Test encoding single string
    emb_single = model.encode("Artificial Intelligence")
    assert len(emb_single) == 128
    assert hasattr(emb_single, "tolist")
    assert isinstance(emb_single.tolist(), list)

    # Test encoding list of strings
    embeddings = model.encode(["Artificial Intelligence", "Neural Networks", "Pizza"])
    assert len(embeddings) == 3
    assert all(len(emb) == 128 for emb in embeddings)

    # Semantic/lexical similarity check using character trigrams
    sim_similar = cosine_similarity(embeddings[0].tolist(), embeddings[0].tolist())
    assert pytest.approx(sim_similar) == 1.0

    sim_different = cosine_similarity(embeddings[0].tolist(), embeddings[2].tolist())
    # "Artificial Intelligence" and "Pizza" should be less similar than self-similarity
    assert sim_different < 0.5


def test_extract_concepts_with_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force get_nlp and get_model to use our mock classes by mocking imports/load
    # or by patching get_nlp / get_model in pipeline.py
    import backend.app.pipeline as pipeline

    monkeypatch.setattr(pipeline, "get_nlp", lambda: MockNLP())
    monkeypatch.setattr(pipeline, "get_model", lambda: MockModel())

    text = (
        "Artificial Intelligence is a branch of computer science. "
        "Neural Networks are used in Artificial Intelligence to build models. "
        "Deep Learning is a subset of Neural Networks."
    )

    concepts, relationships = extract_concepts(text, sim_threshold=-0.1)

    assert len(concepts) > 0
    # There should be some extracted concepts
    concept_names = {c.name for c in concepts}
    assert "artificial intelligence" in concept_names or "neural network" in concept_names

    # There should be relationships extracted
    assert len(relationships) > 0
