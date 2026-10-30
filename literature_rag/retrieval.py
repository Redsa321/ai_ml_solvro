"""Identical candidates and tokenization, two independent scoring methods."""

import sqlite3
from time import perf_counter

from .chunking import tokenize
from .domain import SOURCE_KINDS, conference_id
from .store import HIT_COLUMNS, HIT_JOIN, metadata


def search(
    connection: sqlite3.Connection, query: str, *, method: str = "bm25",
    conference: str | None = None, kind: str | None = None, top_k: int = 5,
) -> dict:
    if method not in ("bm25", "overlap"):
        raise ValueError("Metoda musi mieć wartość bm25 albo overlap.")
    if top_k < 1:
        raise ValueError("top-k musi być dodatnie.")
    if kind is not None and kind not in SOURCE_KINDS:
        raise ValueError("Nieznany rodzaj źródła.")
    conference = conference_id(conference)
    started = perf_counter()
    tokens = sorted(set(tokenize(query)))
    info = metadata(connection)
    result = {
        "query": query, "query_tokens": tokens, "method": method,
        "score_order": "ascending" if method == "bm25" else "descending",
        "conference": conference, "kind": kind, "top_k": top_k,
        "dataset_type": info["dataset_type"],
        "corpus_fingerprint": info["corpus_fingerprint"],
        "index_fingerprint": info["index_fingerprint"],
        "hits": [],
    }
    if tokens:
        clauses, parameters = [], []
        if conference:
            clauses.append("p.conference=?")
            parameters.append(conference)
        if kind:
            clauses.append("s.kind=?")
            parameters.append(kind)
        if method == "bm25":
            # Only ASCII alphanumeric tokens reach MATCH; quotes and OR are ours.
            match = " OR ".join('"' + token + '"' for token in tokens)
            sql = "SELECT " + HIT_COLUMNS + ", bm25(chunks_fts) AS score" + HIT_JOIN
            sql += " JOIN chunks_fts ON chunks_fts.chunk_id=c.chunk_id"
            sql += " WHERE chunks_fts MATCH ?"
            if clauses:
                sql += " AND " + " AND ".join(clauses)
            rows = [dict(row) for row in connection.execute(sql, [match, *parameters])]
        else:
            sql = "SELECT " + HIT_COLUMNS + ", c.terms" + HIT_JOIN
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            rows = []
            query_terms = set(tokens)
            for row in connection.execute(sql, parameters):
                hit = dict(row)
                score = len(query_terms.intersection(hit.pop("terms").split()))
                if score:
                    rows.append({**hit, "score": score})
        rows.sort(key=lambda hit: (
            hit["score"] if method == "bm25" else -hit["score"],
            hit["source_id"], hit["chunk_id"],
        ))
        seen = set()
        for hit in rows:
            if hit["source_id"] in seen:
                continue
            seen.add(hit["source_id"])
            result["hits"].append({**hit, "rank": len(result["hits"]) + 1})
            if len(result["hits"]) == top_k:
                break
    result["elapsed_ms"] = (perf_counter() - started) * 1000
    return result
