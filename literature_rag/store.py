"""Atomic SQLite builds and read-only access to an identified local corpus."""

import json
import os
import sqlite3
import tempfile
from collections import Counter
from contextlib import closing, contextmanager
from dataclasses import asdict
from pathlib import Path

from .chunking import ChunkConfig, chunk_source, tokenize
from .domain import Corpus
from .files import canonical, fingerprint, utc_now

SCHEMA_VERSION = 1
SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE metadata (id INTEGER PRIMARY KEY CHECK (id = 1), value TEXT NOT NULL);
CREATE TABLE papers (
    paper_id TEXT PRIMARY KEY, forum_id TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
    abstract TEXT NOT NULL, conference TEXT NOT NULL, year INTEGER NOT NULL,
    status TEXT NOT NULL, url TEXT NOT NULL
);
CREATE TABLE sources (
    source_id TEXT PRIMARY KEY, paper_id TEXT NOT NULL REFERENCES papers(paper_id),
    kind TEXT NOT NULL CHECK (kind IN ('author_abstract', 'official_review')),
    sections TEXT NOT NULL, content TEXT NOT NULL, ratings TEXT NOT NULL,
    invitations TEXT NOT NULL, timestamps TEXT NOT NULL, url TEXT NOT NULL
);
CREATE TABLE chunks (
    chunk_id TEXT PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(source_id),
    field TEXT NOT NULL, text TEXT NOT NULL, char_start INTEGER NOT NULL,
    char_end INTEGER NOT NULL, terms TEXT NOT NULL,
    CHECK (char_start >= 0 AND char_end > char_start),
    UNIQUE(source_id, field, char_start, char_end)
);
CREATE INDEX sources_paper ON sources(paper_id, kind);
CREATE INDEX chunks_source ON chunks(source_id);
CREATE VIRTUAL TABLE chunks_fts USING fts5(chunk_id UNINDEXED, terms, tokenize='ascii');
"""

# Joined columns shared by ranked chunks and abstracts added through their paper.
HIT_COLUMNS = """
    c.chunk_id, c.source_id, c.field, c.text, c.char_start, c.char_end,
    s.paper_id, s.kind, s.url, p.title, p.conference, p.year
"""
HIT_JOIN = """
    FROM chunks c JOIN sources s ON c.source_id = s.source_id
    JOIN papers p ON p.paper_id = s.paper_id
"""


@contextmanager
def open_index(path: Path):
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError(f"Brak indeksu: {path}. Najpierw wykonaj build albo demo.")
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        info = metadata(connection)
        if info.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Nieobsługiwana wersja indeksu; odbuduj go ze snapshotu.")
        yield connection


def metadata(connection: sqlite3.Connection) -> dict:
    row = connection.execute("SELECT value FROM metadata WHERE id=1").fetchone()
    if row is None:
        raise ValueError("Indeks nie ma metadanych.")
    return json.loads(row[0])


def build_index(
    corpus: Corpus, path: Path, config: ChunkConfig, *, replace: bool = False,
) -> dict:
    index_fingerprint = fingerprint({
        "corpus": corpus.fingerprint, "config": config.signature, "schema": SCHEMA_VERSION,
    })
    if path.exists():
        with open_index(path) as connection:
            existing = metadata(connection)
        if existing["index_fingerprint"] == index_fingerprint:
            return {**existing, "reused": True}
        if not replace:
            raise ValueError("Indeks zawiera inny snapshot lub konfigurację. Wybierz nowy --db.")
    chunks = [chunk for source in corpus.sources for chunk in chunk_source(source, config)]
    papers_per_conference = Counter(paper.conference for paper in corpus.papers)
    paper_conferences = {paper.paper_id: paper.conference for paper in corpus.papers}
    reviews_per_conference = Counter(
        paper_conferences[source.paper_id]
        for source in corpus.sources if source.kind == "official_review"
    )
    info = {
        "schema_version": SCHEMA_VERSION,
        "dataset_type": corpus.dataset_type,
        "corpus_fingerprint": corpus.fingerprint,
        "index_fingerprint": index_fingerprint,
        "chunk_config": config.signature,
        "created_at": utc_now(),
        "provenance": corpus.provenance,
        "import_report": corpus.import_report,
        "counts": {"papers": len(corpus.papers), "sources": len(corpus.sources),
                   "chunks": len(chunks)},
        "papers_per_conference": dict(papers_per_conference),
        "reviews_per_conference": dict(reviews_per_conference),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".build-", suffix=".sqlite", dir=path.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with closing(sqlite3.connect(temporary)) as connection:
            connection.executescript(SCHEMA)
            connection.executemany(
                """INSERT INTO papers VALUES
                (:paper_id, :forum_id, :title, :abstract, :conference, :year, :status, :url)""",
                [asdict(paper) for paper in corpus.papers],
            )
            for source in corpus.sources:
                row = asdict(source)
                for key in ("sections", "content", "ratings", "invitations", "timestamps"):
                    row[key] = canonical(row[key])
                connection.execute(
                    """INSERT INTO sources VALUES
                    (:source_id, :paper_id, :kind, :sections, :content, :ratings,
                     :invitations, :timestamps, :url)""", row,
                )
            for chunk in chunks:
                row = {**asdict(chunk), "terms": " ".join(tokenize(chunk.text))}
                connection.execute(
                    """INSERT INTO chunks VALUES
                    (:chunk_id, :source_id, :field, :text, :char_start, :char_end, :terms)""", row,
                )
                connection.execute(
                    "INSERT INTO chunks_fts(chunk_id, terms) VALUES (?, ?)",
                    (chunk.chunk_id, row["terms"]),
                )
            connection.execute("INSERT INTO metadata VALUES (1, ?)", (canonical(info),))
            if connection.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Import narusza relacje między źródłami.")
            connection.execute("INSERT INTO chunks_fts(chunks_fts) VALUES ('integrity-check')")
            connection.commit()
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return {**info, "reused": False}


def related_abstract(connection: sqlite3.Connection, paper_id: str) -> dict | None:
    row = connection.execute(
        "SELECT " + HIT_COLUMNS + HIT_JOIN + """
        WHERE s.paper_id=? AND s.kind='author_abstract'
        ORDER BY c.char_start, c.chunk_id LIMIT 1""", (paper_id,),
    ).fetchone()
    return dict(row) if row else None


def source_record(connection: sqlite3.Connection, source_id: str) -> dict | None:
    row = connection.execute(
        """SELECT s.*, p.conference, p.title FROM sources s
        JOIN papers p ON p.paper_id=s.paper_id WHERE s.source_id=?""", (source_id,),
    ).fetchone()
    if row is None:
        return None
    result = dict(row)
    for key in ("sections", "content", "ratings", "invitations", "timestamps"):
        result[key] = json.loads(result[key])
    return result
