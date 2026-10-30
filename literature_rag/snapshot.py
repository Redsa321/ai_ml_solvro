"""Normalize an explicit local snapshot; no live OpenReview access here."""

from collections import Counter
from datetime import datetime
from urllib.parse import urlencode

from .domain import CONFERENCES, Corpus, Paper, Source
from .files import file_hash, read_json


def value(content: dict, field: str):
    raw = content.get(field)
    return raw.get("value") if isinstance(raw, dict) and "value" in raw else raw


def required_text(raw: object, label: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"Brak niepustego pola tekstowego: {label}.")
    return raw.strip()


def note_url(forum: str, note_id: str, synthetic: bool) -> str:
    if synthetic:
        return "https://example.invalid/synthetic?" + urlencode({"forum": forum, "note": note_id})
    return "https://openreview.net/forum?" + urlencode({"id": forum, "noteId": note_id})


def normalize_snapshot(snapshot: dict) -> Corpus:
    """The venue invitation map must be verified before importing real notes.

    Unclassified replies are retained in the input snapshot but never indexed.
    Exact invitation -> submission mappings also catch cross-paper attribution.
    """
    if not isinstance(snapshot, dict) or snapshot.get("schema_version") != 1:
        raise ValueError("Nieobsługiwana wersja snapshotu; oczekiwano schema_version=1.")
    dataset_type = snapshot.get("dataset_type")
    if dataset_type not in ("synthetic", "openreview"):
        raise ValueError("dataset_type musi być synthetic albo openreview.")
    synthetic = dataset_type == "synthetic"
    provenance = snapshot.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("Snapshot wymaga opisu provenance.")
    required_text(provenance.get("selection_method"), "provenance.selection_method")
    timestamp = required_text(provenance.get("fetched_at"), "provenance.fetched_at")
    try:
        fetched_at = datetime.fromisoformat(timestamp)
    except ValueError:
        raise ValueError("provenance.fetched_at wymaga daty ISO 8601 ze strefą czasową.") from None
    if fetched_at.tzinfo is None:
        raise ValueError("provenance.fetched_at musi zawierać strefę czasową.")
    venues, notes = snapshot.get("venues"), snapshot.get("notes")
    if not isinstance(venues, list) or not venues or not isinstance(notes, list):
        raise ValueError("Snapshot wymaga list venues oraz notes.")

    submissions, reviews = {}, {}
    for venue in venues:
        if not isinstance(venue, dict) or venue.get("id") not in CONFERENCES.values():
            raise ValueError("Snapshot zawiera nieobsługiwaną konferencję.")
        if venue.get("year") != 2024:
            raise ValueError("Konferencje tego projektu muszą mieć year=2024.")
        if venue.get("verified") is not True:
            raise ValueError("Schemat invitations musi mieć verified=true po weryfikacji.")
        required_text(venue.get("verification_note"), "verification_note")
        invitation = required_text(venue.get("submission_invitation"), "submission_invitation")
        if not invitation.startswith(venue["id"] + "/") or invitation in submissions:
            raise ValueError("Niepoprawna lub powtórzona submission invitation.")
        submissions[invitation] = venue
        mapping = venue.get("review_invitations")
        if not isinstance(mapping, dict):
            raise ValueError("review_invitations musi mapować invitation na submission note ID.")
        rating_fields = venue.get("rating_fields", [])
        if not isinstance(rating_fields, list) or not all(
            isinstance(field, str) and field for field in rating_fields
        ):
            raise ValueError("rating_fields musi być listą oryginalnych nazw pól.")
        for review_invitation, paper_id in mapping.items():
            if (
                not review_invitation.startswith(venue["id"] + "/")
                or review_invitation in reviews
                or not isinstance(paper_id, str)
                or not paper_id
            ):
                raise ValueError("Niepoprawna lub powtórzona review invitation.")
            reviews[review_invitation] = (venue, paper_id)
    if set(submissions) & set(reviews):
        raise ValueError("Ta sama invitation nie może oznaczać submission i recenzji.")

    all_notes = {}
    for note in notes:
        if not isinstance(note, dict):
            raise ValueError("Każda notatka musi być obiektem.")
        note_id = required_text(note.get("id"), "note.id")
        if note_id in all_notes:
            raise ValueError(f"Powtórzony note ID: {note_id}.")
        if not isinstance(note.get("invitations"), list) or not all(
            isinstance(invitation, str) for invitation in note["invitations"]
        ):
            raise ValueError(f"Brak listy invitations: {note_id}.")
        if not isinstance(note.get("readers", []), list):
            raise ValueError(f"readers musi być listą: {note_id}.")
        if not isinstance(note.get("content"), dict):
            raise ValueError(f"Brak content: {note_id}.")
        all_notes[note_id] = note

    papers, sources, forum_to_paper = {}, {}, {}
    report = Counter(raw_notes=len(notes))
    for note_id, note in all_notes.items():
        matched = [inv for inv in note["invitations"] if inv in submissions]
        if not matched:
            continue
        if len(matched) != 1:
            raise ValueError(f"Niejednoznaczna submission invitation: {note_id}.")
        venue, content = submissions[matched[0]], note["content"]
        forum = required_text(note.get("forum"), f"{note_id}.forum")
        if forum in forum_to_paper:
            raise ValueError(f"Powtórzone forum submission: {forum}.")
        if "everyone" not in note.get("readers", []):
            raise ValueError(f"Submission nie jest publiczne: {note_id}.")
        if value(content, "venueid") != venue["id"]:
            raise ValueError(f"Submission nie ma statusu accepted wybranej konferencji: {note_id}.")
        paper = Paper(
            note_id, forum,
            required_text(value(content, "title"), f"{note_id}.title"),
            required_text(value(content, "abstract"), f"{note_id}.abstract"),
            venue["id"], venue["year"], "accepted", note_url(forum, note_id, synthetic),
        )
        papers[note_id] = paper
        forum_to_paper[forum] = note_id
        sources[note_id] = Source(
            note_id, note_id, "author_abstract", {"abstract": paper.abstract}, content, {},
            note["invitations"], _timestamps(note), paper.url,
        )

    review_counts = Counter()
    for note_id, note in all_notes.items():
        matched = [inv for inv in note["invitations"] if inv in reviews]
        if not matched:
            if note_id not in papers:
                report["ignored_other_replies"] += 1
            continue
        mappings = {(reviews[inv][0]["id"], reviews[inv][1]) for inv in matched}
        if len(mappings) != 1 or note_id in papers:
            raise ValueError(f"Niejednoznaczny typ lub przypisanie recenzji: {note_id}.")
        venue, expected_paper = reviews[matched[0]]
        paper = papers.get(expected_paper)
        if (
            paper is None or paper.conference != venue["id"]
            or forum_to_paper.get(note.get("forum")) != expected_paper
            or note.get("replyto") != expected_paper
        ):
            raise ValueError(f"Recenzja ma niepoprawną relację z publikacją: {note_id}.")
        if "everyone" not in note.get("readers", []):
            raise ValueError(f"Recenzja nie jest publiczna: {note_id}.")
        content = note["content"]
        rating_fields = venue.get("rating_fields", [])
        ratings = {field: content[field] for field in rating_fields if field in content}
        sections = {
            field: value(content, field).strip()
            for field in content
            if field not in rating_fields
            and isinstance(value(content, field), str)
            and value(content, field).strip()
        }
        if not sections:
            report["reviews_without_text"] += 1
            continue
        sources[note_id] = Source(
            note_id, expected_paper, "official_review", sections, content, ratings,
            note["invitations"], _timestamps(note), note_url(paper.forum_id, note_id, synthetic),
        )
        review_counts[expected_paper] += 1
    if not papers:
        raise ValueError("Brak zaakceptowanych publikacji w snapshotcie.")
    missing = sorted(set(papers) - set(review_counts))
    if missing:
        raise ValueError("Publikacje bez oficjalnych publicznych recenzji: " + ", ".join(missing))
    report["papers"] = len(papers)
    report["official_reviews"] = sum(review_counts.values())
    return Corpus(
        dataset_type, [papers[key] for key in sorted(papers)],
        [sources[key] for key in sorted(sources)], provenance, dict(report),
    )


def _timestamps(note: dict) -> dict:
    return {key: note[key] for key in ("cdate", "mdate", "tcdate", "tmdate") if key in note}


def load_snapshot(path):
    return normalize_snapshot(read_json(path)), file_hash(path)
