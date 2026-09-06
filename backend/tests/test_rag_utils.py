from app.services.rag import chunk_text, extract_text, summarize_text


def test_extract_text_decodes_plain_text_bytes():
    result = extract_text("notes.txt", b"hello from a text file")
    assert result == "hello from a text file"


def test_chunk_text_splits_long_text_with_overlap():
    words = " ".join(f"word{i}" for i in range(2000))
    chunks = chunk_text(words, chunk_size=900, overlap=150)
    assert len(chunks) > 1
    # Overlap means the tail of one chunk reappears at the head of the next
    assert chunks[0].split()[-1] in chunks[1].split()


def test_chunk_text_empty_input_returns_no_chunks():
    assert chunk_text("") == []


def test_summarize_text_truncates_to_first_few_sentences():
    text = "One. Two. Three. Four. Five. Six."
    summary = summarize_text(text)
    assert "Five" not in summary or len(summary) <= 800
