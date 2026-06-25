from backend.app.pipeline import chunk_text

def test_chunk_text_splits_large_input() -> None:
    text = "Knowledge graphs help learners build context. " * 30
    chunks = chunk_text(text, max_chars=80)

    assert len(chunks) > 1
    assert chunks[0].token_estimate > 0
    assert chunks[0].char_end > chunks[0].char_start
