from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Chunk:
    index: int
    text: str


def estimate_tokens(text: str) -> int:
    words = text.split()
    return max(1, int(len(words) / 0.75))


def chunk_text(text: str, max_tokens: int, overlap_tokens: int, min_chunk_tokens: int = 2000) -> List[Chunk]:
    words = text.split()
    if not words:
        return []

    est_tokens_per_word = 1 / 0.75
    max_words = max(1, int(max_tokens / est_tokens_per_word))
    overlap_words = max(0, int(overlap_tokens / est_tokens_per_word))
    min_words = max(1, int(min_chunk_tokens / est_tokens_per_word))

    chunks = []
    start = 0
    index = 0
    while start < len(words):
        end = min(len(words), start + max_words)
        if end - start < min_words and start != 0:
            start = max(0, len(words) - min_words)
            end = len(words)
        chunk_value = " ".join(words[start:end]).strip()
        if chunk_value:
            chunks.append(Chunk(index=index, text=chunk_value))
            index += 1
        if end == len(words):
            break
        start = max(0, end - overlap_words)
    return chunks
