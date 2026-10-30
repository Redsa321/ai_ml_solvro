from dataclasses import asdict, dataclass

from .files import fingerprint

CONFERENCES = {
    "iclr2024": "ICLR.cc/2024/Conference",
    "neurips2024": "NeurIPS.cc/2024/Conference",
}
SOURCE_KINDS = ("author_abstract", "official_review")


def conference_id(value: str | None) -> str | None:
    if value is None:
        return None
    if value in CONFERENCES.values():
        return value
    if value in CONFERENCES:
        return CONFERENCES[value]
    raise ValueError(f"Nieznana konferencja: {value}.")


@dataclass(frozen=True)
class Paper:
    paper_id: str
    forum_id: str
    title: str
    abstract: str
    conference: str
    year: int
    status: str
    url: str


@dataclass(frozen=True)
class Source:
    source_id: str
    paper_id: str
    kind: str
    sections: dict[str, str]
    content: dict
    ratings: dict
    invitations: list[str]
    timestamps: dict
    url: str


@dataclass(frozen=True)
class Corpus:
    dataset_type: str
    papers: list[Paper]
    sources: list[Source]
    provenance: dict
    import_report: dict

    @property
    def fingerprint(self) -> str:
        return fingerprint({
            "normalizer_version": 1,
            "dataset_type": self.dataset_type,
            "papers": [asdict(paper) for paper in self.papers],
            "sources": [asdict(source) for source in self.sources],
        })


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source_id: str
    field: str
    text: str
    char_start: int
    char_end: int
