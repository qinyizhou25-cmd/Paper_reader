"""Validate local, source-anchored teaching cards without running a model."""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urlsplit


class StaleTeacherAnchor(ValueError):
    pass


def is_teacher_definition(annotation: Any) -> bool:
    origin = annotation.get("origin") if isinstance(annotation, dict) else None
    return isinstance(origin, dict) and origin.get("kind") == "reading-teacher" and origin.get("content_type") == "definition"


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string.")
    return value


def _identifier(value: Any, label: str) -> str:
    text = _text(value, label)
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", text):
        raise ValueError(f"{label} is not a valid identifier.")
    return text


def _records(value: Any, label: str, limit: int) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) > limit or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{label} must be a list of at most {limit} objects.")
    return value


def _unique_ids(records: list[dict[str, Any]], label: str) -> set[str]:
    ids = [_identifier(record.get("id"), f"{label}.id") for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{label} contains duplicate IDs.")
    return set(ids)


def _anchor(value: Any, segments: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Each teacher anchor must be an object.")
    segment_id = _identifier(value.get("segment_id"), "anchor.segment_id")
    quote = _text(value.get("quote"), "anchor.quote")
    fingerprint = _text(value.get("source_sha256"), "anchor.source_sha256")
    if not re.fullmatch(r"[a-f0-9]{64}", fingerprint):
        raise ValueError("anchor.source_sha256 must be a SHA-256 fingerprint.")
    segment = segments.get(segment_id)
    if segment is None:
        raise StaleTeacherAnchor(f"{segment_id}: source segment no longer exists.")
    markdown = segment.get("markdown")
    if not isinstance(markdown, str) or hashlib.sha256(markdown.encode("utf-8")).hexdigest() != fingerprint:
        raise StaleTeacherAnchor(f"{segment_id}: source changed; regenerate this card against the current text.")
    start = markdown.find(quote)
    if start < 0 or markdown.find(quote, start + 1) >= 0:
        raise StaleTeacherAnchor(f"{segment_id}: quote must match exactly once; no whole-paragraph fallback.")
    # Let the client reject a late response for an older, still-open source copy.
    return {**value, "source_markdown": markdown}


def validate_reading_teacher(data: Any, segments: Any, paper_id: str) -> dict[str, Any]:
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError("reading_teacher.json must be a version 1 object.")
    if data.get("paper_id") != paper_id:
        raise ValueError("The teaching cards belong to another paper.")
    _identifier(data.get("id"), "teacher.id")
    _text(data.get("created_at"), "teacher.created_at")
    _text(data.get("created_by"), "teacher.created_by")
    segment_rows = _records(segments, "segments", 100000)
    _unique_ids(segment_rows, "segments")
    segment_lookup = {item["id"]: item for item in segment_rows}
    sources = _records(data.get("sources", []), "sources", 32)
    source_ids = _unique_ids(sources, "sources")
    for source in sources:
        _text(source.get("title"), "source.title")
        _text(source.get("accessed_at"), "source.accessed_at")
        url = urlsplit(_text(source.get("url"), "source.url"))
        if url.scheme not in {"https", "http"} or not url.hostname or url.username or url.password:
            raise ValueError("External teacher sources must use public HTTP(S) URLs without credentials.")
    context = data.get("project_context")
    context_ids: set[str] = set()
    if context is not None:
        if not isinstance(context, dict):
            raise ValueError("project_context must be an object.")
        for key in ("project", "source_path", "snapshot_at"):
            _text(context.get(key), f"project_context.{key}")
        context_cards = _records(context.get("cards"), "project_context.cards", 32)
        context_ids = _unique_ids(context_cards, "project_context.cards")
        for card in context_cards:
            _text(card.get("title"), "context.title")
            _text(card.get("summary"), "context.summary")
    cards = _records(data.get("cards"), "cards", 64)
    _unique_ids(cards, "cards")
    valid, issues = [], []
    for card in cards:
        if not isinstance(card.get("kind"), str) or card["kind"] not in {"cue", "focus", "question", "definition", "transfer"}:
            raise ValueError(f"{card['id']}: unsupported teacher card kind.")
        _text(card.get("title"), f"{card['id']}.title")
        if card["kind"] == "cue":
            text = _text(card.get("text"), f"{card['id']}.text")
            if len(text) > 180 or "\n" in text or "\r" in text:
                raise ValueError(f"{card['id']}: a reading cue must be one short paragraph of at most 180 characters.")
            if not isinstance(card.get("form"), str) or card["form"] not in {"statement", "question"}:
                raise ValueError(f"{card['id']}: a reading cue needs a statement or question form.")
        for key in ("why", "question", "hint", "explanation"):
            if card["kind"] not in {"cue", "definition"} or key in card:
                _text(card.get(key), f"{card['id']}.{key}")
        references = card.get("context_ids", [])
        if not isinstance(references, list) or any(not isinstance(ref, str) or ref not in context_ids for ref in references):
            raise ValueError(f"{card['id']}: unknown project context reference.")
        if card["kind"] == "cue" and references:
            raise ValueError(f"{card['id']}: project transfer belongs in a separate deeper-thinking card.")
        if card["kind"] == "transfer" and not references:
            raise ValueError(f"{card['id']}: a transfer question needs an explicit project context reference.")
        definition = card.get("definition")
        if card["kind"] == "cue" and definition is not None:
            raise ValueError(f"{card['id']}: definitions belong in a separate term card, not a reading cue.")
        if card["kind"] == "definition" or definition is not None:
            if not isinstance(definition, dict):
                raise ValueError(f"{card['id']}: a definition must distinguish paper and external meanings.")
            _text(definition.get("paper"), "definition.paper")
            if "paper_kind" in definition and (
                not isinstance(definition["paper_kind"], str) or definition["paper_kind"] not in {"quote", "usage"}
            ):
                raise ValueError("definition.paper_kind must distinguish a paper quote from an account of its usage.")
            if "comparison" in definition:
                _text(definition["comparison"], "definition.comparison")
            external = _records(definition.get("external"), "definition.external", 8)
            if not external:
                raise ValueError("A definition card needs a retrieved meaning or an explicitly labelled AI summary.")
            for item in external:
                if item.get("kind") == "ai-summary":
                    if any(key in item for key in ("source_id", "url", "accessed_at")):
                        raise ValueError("An AI-only definition must not impersonate a retrieved source.")
                elif "kind" in item or not isinstance(item.get("source_id"), str) or item["source_id"] not in source_ids:
                    raise ValueError("An external definition refers to an unknown source.")
                _text(item.get("summary"), "definition.external.summary")
        evidence = _records(card.get("evidence", []), "card.evidence", 8)
        for item in evidence:
            _text(item.get("label"), "evidence.label")
        try:
            anchor = _anchor(card.get("anchor"), segment_lookup)
            checked_evidence = [_anchor(item, segment_lookup) for item in evidence]
            if definition and definition.get("paper_kind") == "quote":
                meaning = definition["paper"]
                source = anchor["source_markdown"]
                start = source.find(meaning)
                if start < 0 or source.find(meaning, start + 1) >= 0:
                    raise StaleTeacherAnchor(f"{card['id']}: the quoted definition must match the anchored paragraph exactly once.")
        except StaleTeacherAnchor as exc:
            issues.append({"id": card["id"], "title": card["title"], "reason": str(exc)})
            continue
        valid.append({**card, "anchor": anchor, "evidence": checked_evidence})
    return {**data, "available": True, "cards": valid, "issues": issues}
