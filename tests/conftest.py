from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture(autouse=True)
def mock_sentence_transformer(monkeypatch):
    class DummyModel:
        def encode(self, sentences, **kwargs):
            # If a single sentence is passed, return a 1D array
            if isinstance(sentences, str):
                return np.zeros(384, dtype=np.float32)
            # If a list of sentences is passed, return a 2D array of shape (len, 384)
            return np.zeros((len(sentences), 384), dtype=np.float32)

    import backend.app.pipeline

    monkeypatch.setattr(backend.app.pipeline, "get_model", lambda: DummyModel())
