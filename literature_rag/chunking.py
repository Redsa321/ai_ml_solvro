import re
from dataclasses import asdict, dataclass

from .domain import Chunk, Source
from .files import fingerprint

STOPWORDS = frozenset("""
a an and are as at be been by can do does for from had has have how i if in into is it
its may of on or our paper that the their these they this those to was we were what
when where which who why will with would you your
""".split())


def tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9]+", text.casefold()) if token not in STOPWORDS]


@dataclass(frozen=True)
class ChunkConfig:
    words: int = 180
    overlap: int = 30

    def __post_init__(self):
        if (
            type(self.words) is not int or type(self.overlap) is not int
            or self.words < 1 or not 0 <= self.overlap < self.words
        ):
            raise ValueError("Chunk wymaga words > 0 oraz 0 <= overlap < words.")

    @property
    def signature(self) -> dict:
        return {
            **asdict(self), "chunker_version": 1, "tokenizer_version": 1,
            "stopwords": sorted(STOPWORDS),
        }


def chunk_source(source: Source, config: ChunkConfig) -> list[Chunk]:
    chunks = []
    for field, text in sorted(source.sections.items()):
        words = list(re.finditer(r"\S+", text))
        start = 0
        while start < len(words):
            stop = min(start + config.words, len(words))
            char_start, char_end = words[start].start(), words[stop - 1].end()
            fragment = text[char_start:char_end]
            chunk_id = fingerprint({
                "source_id": source.source_id, "field": field, "start": char_start,
                "end": char_end, "text": fragment, "version": 1,
            })
            chunks.append(Chunk(chunk_id, source.source_id, field, fragment, char_start, char_end))
            if stop == len(words):
                break
            start = stop - config.overlap
    return chunks
