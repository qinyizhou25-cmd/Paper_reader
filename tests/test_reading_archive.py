"""Pure archive regressions: in-memory fixtures, no library, network or model."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reading_archive import TABLE_COLUMN_NAMES, TABLE_TEXT_LIMIT, archive_fingerprint, build_archive, build_table_archive


def snapshot() -> dict:
    return {
        "format": "paper-reader-reading-data",
        "version": 1,
        "paper_id": "paper-a",
        "sources": {
            "annotations.json#/annotations": "Original paper notes; accepted definitions retain origin.",
            "thinking.json#/blocks": "Stored AI outputs and original prompts.",
        },
        "files": {
            "metadata.json": {
                "title": "A paper & its readers",
                "authors": ["Original Author"],
                "year": 2026,
                "project": "collaborative",
                "updated_at": "poll-1",
                "last_opened_at": "open-1",
                "feishu": {"synced_at": "sync-1", "doc_token": "existing-doc"},
            },
            "segments.json": [
                {"id": "p-0001", "markdown": "Exact paper words.", "translation": "原始译文。"},
            ],
            "annotations.json": {"version": 1, "annotations": [
                {"id": "paper-note", "segment_id": "p-0001", "target": "source",
                 "quote": "Exact paper words.", "note": "  我的原始问题？\n\n不改写。  \n",
                 "range": {"start": 0, "end": 18, "unit": "utf16"}},
                {"id": "translation-highlight", "segment_id": "p-0001", "target": "translation",
                 "quote": "原始译文", "note": ""},
            ]},
            "thinking.json": {
                "version": 1,
                "explain": {"content": "EXISTING BRIEF MUST NOT BE DUPLICATED.", "source": "agent"},
                "blocks": [
                    {"id": "new-chat", "type": "ai_output", "mode": "free", "model": "stored-model",
                     "prompt": "  Newer question?\n", "content": "Newer AI reply.",
                     "created_at": "2026-09-27T10:00:00Z",
                     "selection_refs": [{"segment_id": "p-0001", "quote": "Exact paper words."}]},
                    {"id": "old-chat", "type": "ai_output", "mode": "source", "model": "stored-model",
                     "prompt": "Old question?", "content": "Old AI reply.",
                     "created_at": "2026-09-26T10:00:00Z"},
                ],
                "annotations": [
                    {"id": "brief-note", "block_id": "paper-brief", "quote": "Quoted AI words only.",
                     "note": "  我的 Brief 批注。\n", "target": "thinking"},
                    {"id": "ai-note", "block_id": "old-chat", "quote": "Old AI reply.",
                     "note": "My comment, not the quoted AI answer."},
                ],
                "report_thoughts": [
                    {"id": "report-1", "note": "  Original personal thought.\r\nSecond line.\n", "group": "gap"},
                ],
            },
            "reading_progress.json": {"segments": {"p-0001": {"visible_ms": 1000, "visits": 1}}},
            "translation_state.json": {"job_id": "job-1", "status": "running"},
            "outline.json": {"core_locations": [{"segment_id": "p-0001", "summary": "Saved guidance."}]},
            "reading_teacher.json": {
                "id": "teacher-1", "cards": [{"id": "card-1", "content": "UNACCEPTED TEACHER CONTENT."}],
            },
            "takeaway_doc.json": {"version": 1, "blocks": [
                {"id": "takeaway-1", "type": "bullet", "text": "  Existing mixed-origin Takeaway.\n",
                 "note": "Existing Takeaway comment.", "source": "user", "source_item_id": "paper-note",
                 "source_refs": [{"segment_id": "p-0001", "annotation_id": "paper-note"}]},
            ]},
        },
    }


def duplication_snapshot() -> dict:
    """Synthetic normalized records with the same category sizes as the report."""
    data = snapshot()
    files = data["files"]
    files["annotations.json"]["annotations"] = [
        {"id": f"paper-note-{index}", "segment_id": "p-0001", "target": "source",
         "quote": f"Selected paper passage {index}.",
         "note": f"  Original personal reading note {index}.\n",
         "range": {"start": index, "end": index + 5, "unit": "utf16"}}
        for index in range(16)
    ] + [{
        "id": "definition", "segment_id": "p-0001", "note": "Current accepted definition.",
        "origin": {"kind": "reading-teacher", "content_type": "definition",
                   "card_id": "card-1", "document_id": "teacher-1",
                   "initial_note": "Initial definition copy.", "definition": {"paper": "Definition snapshot."}},
    }]
    files["thinking.json"]["annotations"] = [
        {"id": f"thinking-note-{index}", "block_id": "paper-brief",
         "quote": f"Selected Brief words {index}.", "note": f"My Brief comment {index}."}
        for index in range(5)
    ]
    files["thinking.json"]["report_thoughts"] = []
    files["thinking.json"]["blocks"] = [
        {"id": f"chat-{index}", "type": "ai_output", "mode": "source", "model": "stored-model",
         "prompt": f"Original question {index}?",
         "content": f"Original AI answer {index}.\n" + "Stored answer paragraph.\n" * 12,
         "source_refs": [{"segment_id": "p-0001", "quote": "Stored paper context. " * 20}]}
        for index in range(5, 0, -1)
    ] + [{
        "id": "narrative", "type": "ai_output", "mode": "reading_narrative",
        "content": "Existing narrative, not a new summary.\n" + "Stored narrative paragraph.\n" * 20,
        "prompt": "Existing generation instruction.",
    }]
    files["takeaway_doc.json"]["blocks"] = []
    for index in range(34):
        text = f"TAKEAWAY {index:02d}: original saved mixed-origin words.\n" + "Original paragraph.\n" * 5
        files["takeaway_doc.json"]["blocks"].append({
            "id": f"takeaway-{index:02d}", "type": "bullet", "text": text,
            "note": text if index % 2 else "", "content": text,
            "quote": text, "source": "paper", "source_item_id": f"paper-note-{index % 16}",
            "source_label": text, "meta": "OPAQUE_METADATA_DO_NOT_REPLAY " + text * 3,
            "color": "yellow", "tags": [], "indent": 1, "level": 2, "locked": False,
            "created_at": "2026-09-27", "updated_at": "2026-09-27",
            "source_refs": [
                {"segment_id": "p-0001", "annotation_id": f"paper-note-{index % 16}", "quote": text}
                for _ in range(3)
            ],
            "extension_metadata": {"snapshot": {"content": "OPAQUE_EXTENSION_DO_NOT_REPLAY " + text * 3}},
        })
    files["takeaway_doc.json"]["extension_metadata"] = {"cache": "OPAQUE_ENVELOPE_DO_NOT_REPLAY" * 30}
    return data


def section(archive: dict, key: str) -> list[dict]:
    return next(item["entries"] for item in archive["sections"] if item["id"] == key)


def all_entries(archive: dict) -> list[dict]:
    return [entry for item in archive["sections"] for entry in item["entries"]]


def element_text(element: ET.Element) -> str:
    value = element.text or ""
    for child in element:
        value += "\n" if child.tag == "br" else element_text(child)
        value += child.tail or ""
    return value


class TableArchiveTests(unittest.TestCase):
    def test_columns_preserve_categorized_originals_without_mutation_or_xml(self) -> None:
        data = snapshot()
        data["files"]["annotations.json"]["annotations"][0]["note"] = "  <img src=x> & 原话\r\n\tEnd.  "
        before = copy.deepcopy(data)
        with mock.patch("reading_archive._xml_chunks", side_effect=AssertionError("Table output must not build XML")):
            archive = build_table_archive(data)
        self.assertEqual(data, before)
        self.assertNotIn("xml", archive)
        self.assertEqual(archive["title"], data["files"]["metadata.json"]["title"])
        self.assertEqual([column["id"] for column in archive["columns"]], list(TABLE_COLUMN_NAMES))
        self.assertEqual([column["name"] for column in archive["columns"]], list(TABLE_COLUMN_NAMES.values()))
        for column in archive["columns"]:
            for entry in section(archive, column["id"]):
                for key in ("label", "text", "quote", "source"):
                    if entry[key]:
                        self.assertIn(entry[key], column["text"])
            self.assertEqual(column["characters"], len(column["text"].encode("utf-16-le")) // 2)
            self.assertEqual(column["limit"], TABLE_TEXT_LIMIT)
        self.assertLess(archive["columns"][0]["text"].index("<img src=x>"), archive["columns"][0]["text"].index("\n\n引用：\n"))
        self.assertNotIn("EXISTING BRIEF MUST NOT BE DUPLICATED.", "\n".join(column["text"] for column in archive["columns"]))
        self.assertEqual(archive, build_table_archive(data))

    def test_empty_categories_are_empty_cells(self) -> None:
        archive = build_table_archive({"paper_id": "empty-paper", "files": {}})
        self.assertEqual(len(archive["columns"]), 4)
        self.assertTrue(all(column["text"] == "" and column["characters"] == 0 for column in archive["columns"]))

    def test_json_key_order_does_not_change_cell_text(self) -> None:
        def reordered(value):
            if isinstance(value, dict):
                return {key: reordered(item) for key, item in reversed(list(value.items()))}
            if isinstance(value, list):
                return [reordered(item) for item in value]
            return value

        data = snapshot()
        self.assertEqual(build_table_archive(data), build_table_archive(reordered(data)))

    def test_chat_uses_short_speaker_labels_without_rewriting_original_words(self) -> None:
        data = snapshot()
        original = "  Keep the literal words AI 回复（原文） and 我的提问（原文）.\r\n"
        data["files"]["thinking.json"]["blocks"][0]["content"] = original
        before = copy.deepcopy(data)
        archive = build_table_archive(data)
        messages = section(archive, "ai-discussions")
        self.assertEqual([entry["label"] for entry in messages], ["我:", "AI:", "我:", "AI:"])
        self.assertEqual(messages[-1]["text"], original)
        text = next(column["text"] for column in archive["columns"] if column["id"] == "ai-discussions")
        self.assertTrue(text.startswith("我:\n\nOld question?"))
        self.assertIn("\n\nAI:\n\n", text)
        self.assertNotRegex(text, r"(?m)^\d+\. (?:AI|我):")
        self.assertIn(original, text)
        self.assertEqual(data, before)

    def test_short_labels_keep_explicit_message_roles_in_provenance(self) -> None:
        data = snapshot()
        roles = ["user", "human", "assistant", "ai", "system", "developer", "tool", "function"]
        data["files"]["thinking.json"]["blocks"] = []
        data["files"]["thinking.json"]["messages"] = [
            {"id": role, "role": role, "content": "Unmodified " + role} for role in roles
        ]
        messages = section(build_table_archive(data), "ai-discussions")
        self.assertEqual([entry["label"] for entry in messages],
                         ["我:", "我:", "AI:", "AI:", "System:", "Developer:", "Tool:", "Tool:"])
        for role, entry in zip(roles, messages):
            self.assertIn("role=" + role, entry["source"])
            self.assertEqual(entry["text"], "Unmodified " + role)

    def test_cell_limit_includes_labels_quotes_and_unicode_units(self) -> None:
        for character in ("a", "中", "😀"):
            with self.subTest(character=character):
                note = {"id": "note", "note": "a", "quote": "Original reference."}
                data = {"paper_id": "paper-a", "files": {"annotations.json": {"annotations": [note]}}}
                overhead = build_table_archive(data)["columns"][0]["characters"] - 1
                budget = TABLE_TEXT_LIMIT - overhead
                units = len(character.encode("utf-16-le")) // 2
                note["note"] = character * (budget // units) + "x" * (budget % units)
                column = build_table_archive(data)["columns"][0]
                self.assertEqual(column["characters"], TABLE_TEXT_LIMIT)
                self.assertIn(note["note"], column["text"])
                note["note"] += "x"
                before = copy.deepcopy(data)
                with self.assertRaisesRegex(ValueError, "阅读笔记 exceeds.*100,000.*No content was truncated"):
                    build_table_archive(data)
                self.assertEqual(data, before)

    def test_limits_apply_to_other_material_too(self) -> None:
        data = snapshot()
        data["files"]["takeaway_doc.json"]["blocks"][0]["text"] = "x" * TABLE_TEXT_LIMIT
        with self.assertRaisesRegex(ValueError, "其他阅读材料 exceeds"):
            build_table_archive(data)

    def test_invalid_unicode_fails_without_rewriting(self) -> None:
        data = snapshot()
        data["files"]["annotations.json"]["annotations"][0]["note"] = "Keep this surrogate: \ud800"
        before = copy.deepcopy(data)
        with self.assertRaisesRegex(ValueError, "invalid Unicode"):
            build_table_archive(data)
        self.assertEqual(data, before)

    def test_long_title_does_not_inherit_document_limits(self) -> None:
        data = snapshot()
        data["files"]["metadata.json"]["title"] = "Long paper title & 中文 " * 400
        archive = build_table_archive(data)
        self.assertEqual(archive["title"], data["files"]["metadata.json"]["title"])
        self.assertFalse(any("XML" in warning or "标题过长" in warning for warning in archive["warnings"]))


class ReadingArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = snapshot()

    def test_contract_counts_and_no_mutation(self) -> None:
        original = copy.deepcopy(self.data)
        serialized = json.dumps(self.data, ensure_ascii=False)
        archive = build_archive(self.data)
        fingerprint = archive_fingerprint(self.data)
        self.assertEqual(self.data, original)
        self.assertEqual(json.dumps(self.data, ensure_ascii=False), serialized)
        self.assertEqual(archive, build_archive(self.data))
        self.assertEqual(fingerprint, archive_fingerprint(self.data))
        self.assertEqual(set(archive), {"title", "xml", "sections", "counts", "warnings"})
        self.assertEqual([item["id"] for item in archive["sections"]], [
            "my-notes", "ai-discussions", "accepted-definitions", "other-material",
        ])
        self.assertEqual(archive["counts"], {
            "paper_annotations": 2, "thinking_annotations": 2, "report_thoughts": 1,
            "chat_turns": 2, "accepted_definitions": 0, "takeaway_blocks": 1,
            "unclassified_records": 0,
        })
        self.assertEqual(archive["warnings"], [])
        for entry in all_entries(archive):
            self.assertEqual(set(entry), {"id", "label", "quote", "text", "source"})
            self.assertTrue(all(isinstance(value, str) for value in entry.values()))
        archive["sections"][0]["entries"][0]["text"] = "Changed output only."
        self.assertEqual(self.data, original)

    def test_original_phrases_and_provenance_remain_explicit(self) -> None:
        archive = build_archive(self.data)
        entries = {entry["id"]: entry for entry in section(archive, "my-notes")}
        self.assertEqual(entries["paper-note"]["text"], "  我的原始问题？\n\n不改写。  \n")
        self.assertEqual(entries["paper-note"]["quote"], "Exact paper words.")
        for marker in ("annotations.json#/annotations/0", "p-0001", "range.unit=utf16", "range.start=0"):
            self.assertIn(marker, entries["paper-note"]["source"])
        self.assertNotIn("Original paper notes", entries["paper-note"]["source"])
        self.assertIn("原文引用", entries["paper-note"]["label"])
        self.assertIn("译文引用", entries["translation-highlight"]["label"])
        self.assertIn("AI Brief 引用", entries["brief-note"]["label"])
        self.assertIn("AI 引用", entries["ai-note"]["label"])
        self.assertEqual(entries["report-1"]["text"], "  Original personal thought.\r\nSecond line.\n")
        discussion = section(archive, "ai-discussions")
        self.assertEqual(discussion[-2]["text"], "  Newer question?\n")
        self.assertIn("stored-model", discussion[-1]["source"])
        self.assertIn("segment_id=p-0001", discussion[-1]["source"])

    def test_brief_and_unaccepted_teacher_material_are_not_repeated(self) -> None:
        archive = build_archive(self.data)
        self.assertNotIn("EXISTING BRIEF MUST NOT BE DUPLICATED.", archive["xml"])
        self.assertNotIn("UNACCEPTED TEACHER CONTENT.", archive["xml"])
        self.assertNotIn("Saved guidance.", archive["xml"])
        self.assertIn("Quoted AI words only.", archive["xml"])
        self.assertIn("Existing mixed-origin Takeaway.", archive["xml"])
        self.assertIn("EXISTING BRIEF MUST NOT BE DUPLICATED.", json.dumps(self.data))

    def test_accepted_definitions_keep_reader_edits_and_never_restore_initial_note(self) -> None:
        original_definition = "INITIAL AI DEFINITION MUST NOT REAPPEAR."
        origin = {
            "kind": "reading-teacher", "content_type": "definition", "document_id": "teacher-1",
            "card_id": "card-1", "initial_note": original_definition,
            "anchor": {"segment_id": "p-0001", "quote": "Exact paper words."},
            "definition": {"paper": "OLD DEFINITION SNAPSHOT."},
            "sources": [{"id": "dictionary", "url": "https://example.org/source"}],
        }
        records = self.data["files"]["annotations.json"]["annotations"]
        for number, note in enumerate(("", "  Edited definition by the reader.\n", "   \n")):
            records.append({
                "id": f"definition-{number}", "segment_id": "p-0001", "quote": "Exact paper words.",
                "note": note, "origin": copy.deepcopy(origin),
            })
        original = copy.deepcopy(self.data)
        archive = build_archive(self.data)
        accepted = section(archive, "accepted-definitions")
        self.assertEqual([entry["text"] for entry in accepted], ["", "  Edited definition by the reader.\n", "   \n"])
        self.assertEqual(archive["counts"]["accepted_definitions"], 3)
        self.assertEqual(archive["counts"]["paper_annotations"], 2)
        self.assertFalse(any(entry["id"].startswith("definition-") for entry in section(archive, "my-notes")))
        for entry in accepted:
            self.assertEqual(entry["label"], "AI 定义:")
            for marker in ("reading-teacher", "definition", "teacher-1", "card-1", "p-0001", "https://example.org/source"):
                self.assertIn(marker, entry["source"])
        self.assertNotIn(original_definition, archive["xml"])
        self.assertNotIn("OLD DEFINITION SNAPSHOT.", archive["xml"])
        self.assertEqual(self.data, original)

    def test_missing_definition_note_is_not_filled_from_teacher(self) -> None:
        self.data["files"]["annotations.json"]["annotations"].append({
            "id": "empty-definition", "origin": {"kind": "reading-teacher", "content_type": "definition",
                                                "initial_note": "Do not restore me."},
        })
        archive = build_archive(self.data)
        self.assertEqual(section(archive, "accepted-definitions")[0]["text"], "")
        self.assertEqual(archive["counts"]["accepted_definitions"], 1)
        self.assertNotIn("Do not restore me.", archive["xml"])
        self.assertTrue(any("锚点缺失" in warning for warning in archive["warnings"]))

    def test_orphan_annotations_and_unknown_records_survive(self) -> None:
        self.data["files"]["annotations.json"]["annotations"].extend([
            {"id": "orphan-paper", "segment_id": "missing-segment", "note": "  Orphan paper words.\n", "quote": "Missing source quote."},
            {"id": "unknown-paper", "type": "future", "payload": {"words": "Future annotation payload."}},
            "Scalar annotation, verbatim.",
            {"id": "not-human", "quote": "Some quote", "note": "Generated, not my note.",
             "origin": {"kind": "future-agent", "content_type": "summary"}},
        ])
        self.data["files"]["thinking.json"]["annotations"].append({
            "id": "orphan-thinking", "thinking_block_id": "gone", "quote": "Saved orphan quote.",
            "note": "  My orphan comment.\n",
        })
        self.data["files"]["thinking.json"]["blocks"].append({
            "id": "future-block", "type": "future", "content": "Unknown block, not labelled human.",
            "custom": {"source_id": "future-source"},
        })
        self.data["files"]["thinking.json"]["future/field~"] = {"retained": "Extension payload."}
        self.data["files"]["takeaway_doc.json"]["blocks"].append(17)
        archive = build_archive(self.data)
        mine = {entry["id"]: entry for entry in section(archive, "my-notes")}
        self.assertEqual(mine["orphan-paper"]["text"], "  Orphan paper words.\n")
        self.assertEqual(mine["orphan-thinking"]["quote"], "Saved orphan quote.")
        self.assertIn("作者未确认", mine["orphan-thinking"]["label"])
        self.assertNotIn("not-human", mine)
        other = section(archive, "other-material")
        for original in ("Future annotation payload.", "Scalar annotation, verbatim.",
                         "Generated, not my note.", "Unknown block, not labelled human."):
            self.assertIn(original, "\n".join(entry["text"] for entry in other))
        self.assertIn("future-source", next(entry["source"] for entry in other if entry["id"] == "future-block"))
        self.assertNotIn("Extension payload.", archive["xml"])
        self.assertIn("thinking.json#/future~1field~0", "\n".join(archive["warnings"]))
        self.assertEqual(self.data["files"]["thinking.json"]["future/field~"], {"retained": "Extension payload."})
        self.assertEqual(archive["counts"]["unclassified_records"], 6)
        self.assertTrue(any("missing-segment" in warning for warning in archive["warnings"]))
        self.assertTrue(any("gone" in warning for warning in archive["warnings"]))

    def test_whole_segment_highlight_is_retained_without_inventing_a_quote(self) -> None:
        self.data["files"]["annotations.json"]["annotations"] = [
            {"id": "whole-segment", "type": "segment", "segment_id": "p-0001", "note": "", "quote": ""},
        ]
        entry = section(build_archive(self.data), "my-notes")[0]
        self.assertEqual(entry["id"], "whole-segment")
        self.assertEqual(entry["quote"], "")
        self.assertEqual(entry["text"], "")
        self.assertIn("p-0001", entry["source"])

    def test_discussion_blocks_are_chronological_with_original_pointer_indices(self) -> None:
        original_blocks = copy.deepcopy(self.data["files"]["thinking.json"]["blocks"])
        archive = build_archive(self.data)
        entries = section(archive, "ai-discussions")
        self.assertEqual([entry["text"] for entry in entries], [
            "Old question?", "Old AI reply.", "  Newer question?\n", "Newer AI reply.",
        ])
        self.assertIn("thinking.json#/blocks/1", entries[0]["source"])
        self.assertIn("thinking.json#/blocks/0", entries[-1]["source"])
        self.assertEqual(self.data["files"]["thinking.json"]["blocks"], original_blocks)

    def test_legacy_messages_sort_complete_timestamps_and_keep_roles_and_parent_provenance(self) -> None:
        self.data["files"]["thinking.json"]["chat"] = {
            "id": "thread-1", "source": "saved-import", "source_refs": [{"segment_id": "p-0001"}],
            "messages": [
                {"id": "answer", "role": "assistant", "content": "Stored answer.", "created_at": "2026-09-27T10:00:00+08:00"},
                {"id": "question", "role": "user", "content": "Stored question.", "timestamp": "2026-09-27T01:59:00Z"},
                {"id": "unknown-role", "role": "reviewer", "content": "No authorship assumption.", "timestamp": "2026-09-27T02:01:00Z"},
                {"id": "tool", "role": "tool", "content": {"result": "Stored tool data."}, "timestamp": "2026-09-27T02:02:00Z"},
            ],
        }
        original = copy.deepcopy(self.data)
        archive = build_archive(self.data)
        entries = section(archive, "ai-discussions")[4:]
        self.assertEqual([entry["id"] for entry in entries], ["question", "answer", "tool"])
        self.assertEqual([entry["label"] for entry in entries], ["我:", "AI:", "Tool:"])
        self.assertIn("role=user", entries[0]["source"])
        self.assertIn("role=assistant", entries[1]["source"])
        self.assertIn("role=tool", entries[2]["source"])
        self.assertIn("thinking.json#/chat/messages/1", entries[0]["source"])
        self.assertIn("thread-1", entries[0]["source"])
        self.assertIn("saved-import", entries[0]["source"])
        self.assertEqual(archive["counts"]["chat_turns"], 5)
        unknown = next(entry for entry in section(archive, "other-material") if entry["id"] == "unknown-role")
        self.assertIn("reviewer", unknown["source"])
        self.assertIn("作者未确认", unknown["label"])
        self.assertEqual(self.data, original)

    def test_messages_without_complete_timestamps_keep_stored_order(self) -> None:
        self.data["files"]["thinking.json"]["messages"] = [
            {"id": "one", "role": "user", "text": "First stored message.", "created_at": "invalid-date"},
            {"id": "two", "role": "assistant", "message": "Second stored message.", "created_at": "2026-01-01"},
        ]
        entries = section(build_archive(self.data), "ai-discussions")[-2:]
        self.assertEqual([entry["id"] for entry in entries], ["one", "two"])
        self.assertEqual([entry["text"] for entry in entries], ["First stored message.", "Second stored message."])

    def test_takeaway_narrative_and_pasted_material_are_distinct_from_personal_notes(self) -> None:
        self.data["files"]["thinking.json"]["blocks"] = [
            {"id": "narrative", "type": "ai_output", "mode": "reading_narrative", "model": "stored-model",
             "prompt": "Saved automatic instruction.", "content": "Existing generated narrative."},
            {"id": "pasted", "type": "ai_output", "prompt": "Unverified pasted prompt.",
             "content": "Pasted response in original wording."},
        ]
        archive = build_archive(self.data)
        other = {entry["id"]: entry for entry in section(archive, "other-material")}
        self.assertIn("AI 阅读叙事", other["narrative"]["label"])
        self.assertIn("粘贴内容", other["pasted"]["label"])
        self.assertIn("作者未确认", other["pasted"]["label"])
        self.assertIn("Unverified pasted prompt.", other["pasted"]["text"])
        self.assertIn("Saved automatic instruction.", other["narrative"]["text"])
        self.assertIn("混合来源", other["takeaway-1"]["label"])
        self.assertEqual(other["takeaway-1"]["text"],
                         "  Existing mixed-origin Takeaway.\n\n\nnote:\nExisting Takeaway comment.")
        self.assertIn("source=user", other["takeaway-1"]["source"])
        self.assertIn("source_item_id=paper-note", other["takeaway-1"]["source"])
        self.assertEqual(len(other), 3)
        self.assertEqual(archive["counts"]["chat_turns"], 0)
        self.assertFalse(section(archive, "ai-discussions"))
        self.assertNotIn("Existing generated narrative.", "\n".join(entry["text"] for entry in section(archive, "my-notes")))

    def test_xml_injection_is_literal_and_creates_no_resources(self) -> None:
        payload = """</p><img href="https://example.org/private"/><title>Injected</title>&"'"""
        self.data["files"]["metadata.json"]["title"] = payload
        annotation = self.data["files"]["annotations.json"]["annotations"][0]
        annotation.update(id='"><source name="secret"/>', note=payload + "\n\n# Literal Markdown",
                          quote="<a href='file:secret'>literal link</a>")
        annotation["origin_detail"] = {"url": "https://example.org/unfetched", "attack": payload}
        archive = build_archive(self.data)
        root = ET.fromstring("<doc>" + archive["xml"] + "</doc>")
        self.assertEqual(len(root.findall("title")), 1)
        self.assertEqual(element_text(root.find("title")), "阅读档案｜" + payload)
        self.assertLessEqual({node.tag for node in root.iter()}, {"doc", "title", "h1", "h2", "p", "br", "blockquote"})
        self.assertFalse(any(node.attrib for node in root.iter()))
        entry = section(archive, "my-notes")[0]
        self.assertEqual(entry["id"], annotation["id"])
        self.assertEqual(entry["text"], payload + "\n\n# Literal Markdown")
        self.assertIn("&lt;img", archive["xml"])
        self.assertIn("&amp;", archive["xml"])
        self.assertIn("&quot;", archive["xml"])
        self.assertIn("# Literal Markdown", archive["xml"])

    def test_newlines_and_whitespace_survive_xml(self) -> None:
        text = "  First\tline.\r\n\n\nSecond line.\rLast line.  \n"
        self.data["files"]["annotations.json"]["annotations"][0]["note"] = text
        archive = build_archive(self.data)
        root = ET.fromstring("<doc>" + archive["xml"] + "</doc>")
        self.assertIn(text, [element_text(node) for node in root.iter("p")])
        self.assertEqual(section(archive, "my-notes")[0]["text"], text)

    def test_long_records_and_source_fields_are_split_not_truncated(self) -> None:
        text = "LONG_RECORD_START\n" + ("<&>\"' 中文😀  \n" * 1700) + "LONG_RECORD_END"
        quote = "LONG_QUOTE_START\n" + ("Quote&<>\n" * 900) + "LONG_QUOTE_END"
        annotation = self.data["files"]["annotations.json"]["annotations"][0]
        annotation.update(note=text, quote=quote,
                          source_refs=[{"segment_id": "p-0001", "quote": "Reference 原文 " * 1200}])
        archive = build_archive(self.data)
        entry = section(archive, "my-notes")[0]
        self.assertEqual(entry["text"], text)
        self.assertEqual(entry["quote"], quote)
        self.assertNotIn("Reference 原文", entry["source"])
        self.assertIn("source_refs[0].segment_id=p-0001", entry["source"])
        self.assertEqual(annotation["source_refs"][0]["quote"], "Reference 原文 " * 1200)
        self.assertLess(len(entry["source"]), 500)
        root = ET.fromstring("<doc>" + archive["xml"] + "</doc>")
        joined = "".join(element_text(node) for node in root.iter("p"))
        self.assertIn(text, joined)
        self.assertIn(quote, joined)
        self.assertIn(entry["source"], joined)
        for node in root.iter():
            if node.tag in {"title", "h1", "h2", "p"}:
                self.assertLessEqual(len(element_text(node)), 4000)
        self.assertGreater(archive["xml"].count("<p>"), 30)

    def test_overlong_title_is_kept_in_full_in_bibliographic_text(self) -> None:
        title = "Very long title & 中文 " * 400
        self.data["files"]["metadata.json"]["title"] = title
        archive = build_archive(self.data)
        root = ET.fromstring("<doc>" + archive["xml"] + "</doc>")
        self.assertEqual(archive["title"], "阅读档案")
        self.assertEqual(len(root.findall("title")), 1)
        self.assertIn(title, "".join(element_text(node) for node in root.iter("p")))
        self.assertTrue(any("标题过长" in warning for warning in archive["warnings"]))

    def test_xml_forbidden_characters_are_visible_escapes_only_in_xml(self) -> None:
        text = "Null:\x00; control:\x0b; surrogate:\ud800; noncharacter:\uffff."
        self.data["files"]["annotations.json"]["annotations"][0]["note"] = text
        archive = build_archive(self.data)
        ET.fromstring("<doc>" + archive["xml"] + "</doc>")
        self.assertEqual(section(archive, "my-notes")[0]["text"], text)
        self.assertIn(r"Null:\u0000; control:\u000b; surrogate:\ud800; noncharacter:\uffff.", archive["xml"])
        self.assertTrue(any("XML 1.0" in warning for warning in archive["warnings"]))
        self.assertEqual(len(archive_fingerprint(self.data)), 64)

    def test_legacy_arrays_malformed_collections_and_unknown_files_are_not_dropped(self) -> None:
        self.data["files"]["annotations.json"] = [
            {"id": "legacy-note", "note": "Legacy array note.", "segment_id": "p-0001"},
        ]
        self.data["files"]["takeaway_doc.json"] = ["Legacy scalar Takeaway."]
        self.data["files"]["thinking.json"].update(blocks={"unusual": "Malformed blocks retained."}, report_thoughts=None)
        self.data["files"]["future.json"] = {"id": "future-file", "content": "Future file contents."}
        archive = build_archive(self.data)
        self.assertIn("annotations.json#/0", section(archive, "my-notes")[0]["source"])
        texts = "\n".join(entry["text"] for entry in section(archive, "other-material"))
        for value in ("Legacy scalar Takeaway.", "Malformed blocks retained.", "null", "Future file contents."):
            self.assertIn(value, texts)
        self.assertEqual(archive["counts"]["unclassified_records"], 4)

    def test_duplicate_ids_and_unknown_message_roles_are_never_deduplicated(self) -> None:
        self.data["files"]["thinking.json"]["blocks"][1]["id"] = "new-chat"
        self.data["files"]["thinking.json"]["annotations"][1]["block_id"] = "new-chat"
        self.data["files"]["thinking.json"]["messages"] = [
            {"id": "same", "role": "user", "content": "Stored once."},
            {"id": "same", "role": "assistant", "content": "Stored twice."},
        ]
        archive = build_archive(self.data)
        messages = section(archive, "ai-discussions")
        self.assertEqual([entry["text"] for entry in messages[-2:]], ["Stored once.", "Stored twice."])
        self.assertEqual([entry["id"] for entry in messages[-2:]], ["same", "same"])
        self.assertTrue(any("不唯一" in warning for warning in archive["warnings"]))

    def test_unknown_origin_and_empty_or_malformed_chat_containers_keep_their_records(self) -> None:
        self.data["files"]["annotations.json"]["annotations"].append({
            "id": "unknown-origin", "note": "Unknown origin, no authorship inference.",
            "origin": {"kind": ["future", "format"]},
        })
        self.data["files"]["thinking.json"]["messages"] = [
            {"id": "empty-thread", "source": "original-empty-thread", "messages": []},
            {"id": "malformed-thread", "source": "original-malformed-thread", "messages": 23},
        ]
        archive = build_archive(self.data)
        other = section(archive, "other-material")
        unknown = next(entry for entry in other if entry["id"] == "unknown-origin")
        self.assertIn("作者未确认", unknown["label"])
        self.assertEqual(unknown["text"], "Unknown origin, no authorship inference.")
        self.assertTrue(any(entry["id"] == "empty-thread" for entry in other))
        self.assertIn("original-empty-thread", "\n".join(entry["text"] + entry["source"] for entry in other))
        malformed = next(entry for entry in other if entry["text"] == "23")
        self.assertIn("original-malformed-thread", malformed["source"])
        self.assertIn("malformed-thread", malformed["source"])
        self.assertEqual(archive["counts"]["unclassified_records"], 3)

    def test_synthetic_duplication_is_one_entry_per_takeaway_and_one_saved_narrative(self) -> None:
        data = duplication_snapshot()
        original = copy.deepcopy(data)
        fingerprint = archive_fingerprint(data)
        archive = build_archive(data)
        root = ET.fromstring("<doc>" + archive["xml"] + "</doc>")
        self.assertEqual({item["id"]: len(item["entries"]) for item in archive["sections"]}, {
            "my-notes": 21, "ai-discussions": 10, "accepted-definitions": 1, "other-material": 35,
        })
        self.assertEqual(archive["counts"], {
            "paper_annotations": 16, "thinking_annotations": 5, "report_thoughts": 0,
            "chat_turns": 5, "accepted_definitions": 1, "takeaway_blocks": 34, "unclassified_records": 1,
        })
        entries = {entry["id"]: entry for entry in section(archive, "other-material")}
        visible = "".join(element_text(node) for node in root.iter("p"))
        for block in data["files"]["takeaway_doc.json"]["blocks"]:
            entry = entries[block["id"]]
            self.assertEqual(entry["text"], block["text"])
            self.assertEqual(entry["quote"], "")
            self.assertEqual(visible.count(block["text"]), 1)
            for marker in (block["id"], block["source_item_id"], "p-0001", "source=paper"):
                self.assertIn(marker, entry["source"])
        for marker in ("OPAQUE_METADATA_DO_NOT_REPLAY", "OPAQUE_EXTENSION_DO_NOT_REPLAY", "OPAQUE_ENVELOPE_DO_NOT_REPLAY"):
            self.assertNotIn(marker, archive["xml"])
        self.assertLess(len(archive["xml"].encode("utf-8")), 100_000)
        self.assertLess(len(root), 300)
        self.assertEqual(data, original)
        self.assertEqual(archive_fingerprint(data), fingerprint)

    def test_metadata_copy_size_does_not_inflate_document_but_remains_in_fingerprint(self) -> None:
        data = duplication_snapshot()
        archive = build_archive(data)
        fingerprint = archive_fingerprint(data)
        for block in data["files"]["takeaway_doc.json"]["blocks"]:
            block["meta"] *= 10
            block["source_label"] *= 10
            block["extension_metadata"]["snapshot"]["content"] *= 10
            for reference in block["source_refs"]:
                reference["quote"] *= 10
        enlarged = copy.deepcopy(data)
        self.assertEqual(build_archive(data)["xml"], archive["xml"])
        self.assertNotEqual(archive_fingerprint(data), fingerprint)
        self.assertEqual(data, enlarged)

    def test_distinct_takeaway_prose_is_combined_verbatim_without_extra_record_entries(self) -> None:
        text = "  Original mixed-origin body.\n"
        note = "  A different saved note, not a metadata copy.\n"
        message = "Different additional words.\n"
        block = self.data["files"]["takeaway_doc.json"]["blocks"][0]
        block.update(text=text, content=text, note=note, message=message, prompt="",
                     quote="A distinct selected quotation.",
                     meta="OPAQUE COPY " + text + note, source_label=text)
        original = copy.deepcopy(block)
        archive = build_archive(self.data)
        other = section(archive, "other-material")
        self.assertEqual(len(other), 1)
        entry = other[0]
        self.assertEqual(entry["id"], block["id"])
        self.assertEqual(entry["text"], text + "\n\nnote:\n" + note
                         + "\n\nmessage:\n" + message)
        self.assertEqual(entry["quote"], "A distinct selected quotation.")
        self.assertIn("混合来源", entry["label"])
        self.assertNotIn("OPAQUE COPY", archive["xml"])
        self.assertEqual(block, original)

    def test_unknown_and_orphan_prose_survives_while_opaque_extensions_stay_in_backup(self) -> None:
        annotation = self.data["files"]["annotations.json"]["annotations"][0]
        annotation.update(segment_id="missing", note="  Orphan human words.\n")
        annotation["custom"] = {
            "reader_note": "  Additional saved words in an extension.\n",
            "snapshot": {"note": "DO_NOT_REPLAY_SNAPSHOT"},
            "opaque_payload": "DO_NOT_REPLAY_PAYLOAD" * 500,
        }
        thinking = self.data["files"]["thinking.json"]
        thinking["future_notes"] = {"records": [
            {"id": "future-personal-words", "note": "  Unknown saved prose.\n",
             "metadata": {"note": "DO_NOT_REPLAY_METADATA"}},
        ]}
        thinking["opaque_extension"] = {"checksum": "DO_NOT_REPLAY_CHECKSUM" * 500}
        original = copy.deepcopy(self.data)
        archive = build_archive(self.data)
        other = section(archive, "other-material")
        for text in ("  Additional saved words in an extension.\n", "  Unknown saved prose.\n"):
            entry = next(item for item in other if item["text"] == text)
            self.assertIn("作者未确认", entry["label"])
        self.assertEqual(section(archive, "my-notes")[0]["text"], "  Orphan human words.\n")
        for marker in ("SNAPSHOT", "PAYLOAD", "METADATA", "CHECKSUM"):
            self.assertNotIn("DO_NOT_REPLAY_" + marker, archive["xml"])
        self.assertTrue(any("opaque_extension" in warning for warning in archive["warnings"]))
        self.assertEqual(self.data, original)

    def test_empty_archive_and_pure_calls_need_no_files_or_services(self) -> None:
        with mock.patch("builtins.open", side_effect=AssertionError("No file I/O")):
            archive = build_archive({})
            fingerprint = archive_fingerprint({})
        self.assertEqual(archive["title"], "阅读档案｜未命名论文")
        self.assertTrue(all(value == 0 for value in archive["counts"].values()))
        self.assertTrue(all(not item["entries"] for item in archive["sections"]))
        self.assertEqual(archive["warnings"], [])
        self.assertEqual(fingerprint, hashlib.sha256(b"{}").hexdigest())
        self.assertEqual(len(ET.fromstring("<doc>" + archive["xml"] + "</doc>").findall("title")), 1)


class ArchiveFingerprintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = snapshot()
        self.original = copy.deepcopy(self.data)
        self.fingerprint = archive_fingerprint(self.data)

    def test_deterministic_sha256_is_independent_of_mapping_insertion_order(self) -> None:
        def reverse_maps(value):
            if isinstance(value, dict):
                return {key: reverse_maps(item) for key, item in reversed(list(value.items()))}
            if isinstance(value, list):
                return [reverse_maps(item) for item in value]
            return value

        self.assertRegex(self.fingerprint, r"^[a-f0-9]{64}$")
        self.assertEqual(archive_fingerprint(reverse_maps(self.data)), self.fingerprint)
        self.assertEqual(self.data, self.original)

    def test_passive_progress_polling_and_translation_jobs_do_not_dirty_publication(self) -> None:
        data = copy.deepcopy(self.data)
        data["files"]["reading_progress.json"] = {"segments": {"p-0001": {"visible_ms": 900000, "visits": 50}},
                                                 "position": {"segment_id": "p-0001", "offset": 77}}
        data["files"]["translation_state.json"] = {"job_id": "new-job", "status": "complete", "updated_at": "now"}
        data["files"]["metadata.json"].update(
            updated_at="poll-99", last_opened_at="open-99", reading_progress_summary={"total_visible_ms": 900000},
            reading_progress_updated_at="now", read_status="read", status="read", read_status_source="auto",
            translation_status="complete", translation_error="", translation_backend="another-backend",
            translated_segments=1, translation_total=1, translation_progress=1, translation_updated_at="now",
        )
        data["files"]["metadata.json"]["feishu"]["synced_at"] = "sync-99"
        data["sources"]["thinking.json#/blocks"] = "Updated exporter explanation, not a note."
        original = copy.deepcopy(data)
        self.assertEqual(archive_fingerprint(data), self.fingerprint)
        self.assertEqual(data, original)
        self.assertEqual(self.data, self.original)

    def test_adding_or_removing_volatile_files_and_first_sync_timestamp_is_a_noop(self) -> None:
        data = copy.deepcopy(self.data)
        del data["files"]["reading_progress.json"]
        del data["files"]["translation_state.json"]
        self.assertEqual(archive_fingerprint(data), self.fingerprint)
        data["files"]["metadata.json"].pop("feishu")
        before = archive_fingerprint(data)
        data["files"]["metadata.json"]["feishu"] = {"synced_at": "first-sync"}
        self.assertEqual(archive_fingerprint(data), before)
        data["files"]["metadata.json"]["feishu"] = {}
        self.assertEqual(archive_fingerprint(data), before)

    def test_meaningful_saved_content_and_metadata_changes_are_detected(self) -> None:
        changes = [
            ("paper note", lambda files: files["annotations.json"]["annotations"][0].update(note="Changed original note.")),
            ("paper quote", lambda files: files["annotations.json"]["annotations"][0].update(quote="Changed quote.")),
            ("anchor", lambda files: files["annotations.json"]["annotations"][0].update(segment_id="different-anchor")),
            ("thinking annotation", lambda files: files["thinking.json"]["annotations"][0].update(note="New personal comment.")),
            ("report thought", lambda files: files["thinking.json"]["report_thoughts"][0].update(note="New report thought.")),
            ("AI answer", lambda files: files["thinking.json"]["blocks"][0].update(content="New AI answer.")),
            ("question", lambda files: files["thinking.json"]["blocks"][0].update(prompt="New prompt.")),
            ("chat provenance", lambda files: files["thinking.json"]["blocks"][0].update(model="different-origin")),
            ("stored message", lambda files: files["thinking.json"].update(messages=[{"role": "user", "content": "New message."}])),
            ("Brief", lambda files: files["thinking.json"]["explain"].update(content="Changed stored Brief.")),
            ("segment", lambda files: files["segments.json"][0].update(markdown="Changed paper source.")),
            ("translation", lambda files: files["segments.json"][0].update(translation="更改的译文。")),
            ("teacher", lambda files: files["reading_teacher.json"]["cards"][0].update(content="New saved suggestion.")),
            ("outline", lambda files: files["outline.json"]["core_locations"][0].update(summary="Changed saved guide.")),
            ("Takeaway", lambda files: files["takeaway_doc.json"]["blocks"][0].update(text="Changed Takeaway.")),
            ("title", lambda files: files["metadata.json"].update(title="Changed bibliographic title")),
            ("authors", lambda files: files["metadata.json"].update(authors=["Changed author"])),
            ("venue", lambda files: files["metadata.json"].update(venue="CHI")),
            ("year", lambda files: files["metadata.json"].update(year=2025)),
            ("project", lambda files: files["metadata.json"].update(project="another-project")),
            ("projects", lambda files: files["metadata.json"].update(projects=["project-a", "project-b"])),
            ("tags", lambda files: files["metadata.json"].update(tags=["new-tag"])),
            ("importance", lambda files: files["metadata.json"].update(importance=3)),
            ("Feishu provenance", lambda files: files["metadata.json"]["feishu"].update(doc_token="different-doc")),
            ("unknown field", lambda files: files["thinking.json"].update(future={"text": "Future substantive data."})),
            ("unknown file", lambda files: files.update({"future.json": {"text": "Future substantive file."}})),
        ]
        for label, change in changes:
            with self.subTest(change=label):
                data = copy.deepcopy(self.data)
                change(data["files"])
                self.assertNotEqual(archive_fingerprint(data), self.fingerprint)

    def test_definition_adoption_edit_clear_and_provenance_changes_are_detected(self) -> None:
        data = copy.deepcopy(self.data)
        definition = {"id": "definition", "note": "Saved AI definition.",
                      "origin": {"kind": "reading-teacher", "content_type": "definition", "card_id": "first"}}
        data["files"]["annotations.json"]["annotations"].append(definition)
        adopted = archive_fingerprint(data)
        self.assertNotEqual(adopted, self.fingerprint)
        definition["note"] = "Reader edited this."
        edited = archive_fingerprint(data)
        self.assertNotEqual(edited, adopted)
        definition["note"] = ""
        cleared = archive_fingerprint(data)
        self.assertNotEqual(cleared, edited)
        definition["origin"]["card_id"] = "second"
        self.assertNotEqual(archive_fingerprint(data), cleared)

    def test_whitespace_list_order_deletions_and_nested_timestamp_fields_remain_significant(self) -> None:
        for action in ("whitespace", "order", "delete", "nested updated_at", "nested synced_at", "paper identity"):
            with self.subTest(action=action):
                data = copy.deepcopy(self.data)
                if action == "whitespace":
                    data["files"]["annotations.json"]["annotations"][0]["note"] += " "
                elif action == "order":
                    data["files"]["thinking.json"]["blocks"].reverse()
                elif action == "delete":
                    data["files"]["thinking.json"]["blocks"].pop()
                elif action == "nested updated_at":
                    data["files"]["annotations.json"]["annotations"][0]["updated_at"] = "meaningful-edit-time"
                elif action == "nested synced_at":
                    data["files"]["metadata.json"]["custom"] = {"synced_at": "not-the-excluded-field"}
                else:
                    data["paper_id"] = "different-paper"
                self.assertNotEqual(archive_fingerprint(data), self.fingerprint)


if __name__ == "__main__":
    unittest.main()
