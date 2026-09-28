"""Reader teaching cards stay separate from original human reading data."""

import copy
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import paper_reader_agent as reader
from reading_teacher import validate_reading_teacher


def example():
    text = "The evidence supports a careful decision, not compulsory agreement."
    segments = [{"id": "p-0001", "kind": "paragraph", "markdown": text, "translation": "Stored translation."}]
    anchor = {"segment_id": "p-0001", "quote": "careful decision",
              "source_sha256": hashlib.sha256(text.encode()).hexdigest()}
    data = {
        "version": 1, "id": "example-v1", "paper_id": "A", "created_at": "2026-09-27",
        "created_by": "agent-curated-example",
        "sources": [{"id": "dictionary", "title": "Example dictionary", "url": "https://example.org/definition", "accessed_at": "2026-09-27"}],
        "cards": [{
            "id": "definition", "kind": "definition", "title": "A careful decision",
            "anchor": anchor, "why": "This defines the scope.", "question": "Does agreement imply understanding?",
            "hint": "Compare the outcome and the process.", "explanation": "They are distinct in this example.",
            "definition": {"paper": "Paper meaning.", "external": [{"source_id": "dictionary", "summary": "Dictionary meaning."}],
                           "comparison": "Do not assume these scopes coincide."},
        }],
    }
    return segments, data


class TeacherValidationTests(unittest.TestCase):
    def test_short_reading_cues_do_not_require_a_deeper_question(self):
        for form in ("statement", "question"):
            with self.subTest(form=form):
                segments, data = example()
                data["cards"] = [{
                    "id": "mechanism", "kind": "cue", "title": "Decision",
                    "anchor": data["cards"][0]["anchor"], "text": "Notice what the decision changes.", "form": form,
                }]
                result = validate_reading_teacher(data, segments, "A")
                self.assertEqual(result["issues"], [])
                self.assertNotIn("question", result["cards"][0])

    def test_reading_cues_reject_long_missing_or_misclassified_prompts(self):
        for field, value in (("text", ""), ("text", "x" * 181), ("text", "First.\nSecond."), ("text", "First.\rSecond."),
                             ("form", "transfer"), ("form", [])):
            with self.subTest(field=field, value=value):
                segments, data = example()
                data["cards"] = [{
                    "id": "mechanism", "kind": "cue", "title": "Decision", "anchor": data["cards"][0]["anchor"],
                    "text": "Read this part.", "form": "statement",
                }]
                data["cards"][0][field] = value
                with self.assertRaises(ValueError):
                    validate_reading_teacher(data, segments, "A")

    def test_reading_cues_do_not_mix_in_definitions_or_project_transfer(self):
        segments, data = example()
        card = data["cards"][0]
        card.update(kind="cue", text="Read this part.", form="statement")
        with self.assertRaisesRegex(ValueError, "separate term card"):
            validate_reading_teacher(data, segments, "A")
        card.pop("definition")
        data["project_context"] = {
            "project": "collaborative", "source_path": "context.html", "snapshot_at": "2026-09-27",
            "cards": [{"id": "goal", "title": "Goal", "summary": "A project hypothesis."}],
        }
        card["context_ids"] = ["goal"]
        with self.assertRaisesRegex(ValueError, "separate deeper-thinking card"):
            validate_reading_teacher(data, segments, "A")

    def test_definition_can_quote_the_paragraph_while_anchoring_only_the_term(self):
        segments, data = example()
        data["cards"][0]["definition"].update(paper=segments[0]["markdown"], paper_kind="quote")
        self.assertEqual(validate_reading_teacher(data, segments, "A")["issues"], [])
        data["cards"][0]["definition"]["paper"] = "A sentence the author did not write."
        result = validate_reading_teacher(data, segments, "A")
        self.assertEqual(result["cards"], [])
        self.assertIn("quoted definition", result["issues"][0]["reason"])

    def test_ai_glosses_are_explicit_and_do_not_require_or_invent_retrieval(self):
        segments, data = example()
        data["sources"] = []
        definition = data["cards"][0]["definition"]
        definition.update(paper_kind="usage", external=[{"kind": "ai-summary", "summary": "A general AI explanation."}])
        self.assertEqual(validate_reading_teacher(data, segments, "A")["issues"], [])
        for key in ("source_id", "url", "accessed_at"):
            with self.subTest(key=key):
                invented = copy.deepcopy(data)
                invented["cards"][0]["definition"]["external"][0][key] = "Invented retrieval"
                with self.assertRaises(ValueError):
                    validate_reading_teacher(invented, segments, "A")
        for value in ("summary", [], None):
            with self.subTest(paper_kind=value):
                definition["paper_kind"] = value
                with self.assertRaises(ValueError):
                    validate_reading_teacher(data, segments, "A")

    def test_definitions_do_not_require_a_question_or_comparison(self):
        segments, data = example()
        card = data["cards"][0]
        for key in ("why", "question", "hint", "explanation"):
            card.pop(key)
        card["definition"].pop("comparison")
        card["definition"]["paper"] = card["anchor"]["quote"]
        result = validate_reading_teacher(data, segments, "A")
        self.assertEqual(result["issues"], [])
        self.assertNotIn("question", result["cards"][0])
        self.assertEqual(result["cards"][0]["definition"]["paper"], "careful decision")

    def test_optional_definition_fields_still_reject_malformed_values(self):
        for key in ("why", "question", "hint", "explanation", "comparison"):
            for value in (None, "", []):
                with self.subTest(key=key, value=value):
                    segments, data = example()
                    target = data["cards"][0]["definition"] if key == "comparison" else data["cards"][0]
                    target[key] = value
                    with self.assertRaises(ValueError):
                        validate_reading_teacher(data, segments, "A")

    def test_non_definition_cards_still_require_thinking_prompts(self):
        for key in ("why", "question", "hint", "explanation"):
            with self.subTest(key=key):
                segments, data = example()
                data["cards"][0]["kind"] = "question"
                data["cards"][0].pop(key)
                with self.assertRaises(ValueError):
                    validate_reading_teacher(data, segments, "A")

    def test_validation_is_lossless_and_translation_independent(self):
        segments, data = example()
        before = copy.deepcopy(data)
        result = validate_reading_teacher(data, segments, "A")
        self.assertEqual(result["cards"][0]["anchor"]["source_markdown"], segments[0]["markdown"])
        self.assertEqual(result["issues"], [])
        self.assertEqual(data, before)
        segments[0]["translation"] = "Updated translation does not change the source."
        self.assertEqual(validate_reading_teacher(data, segments, "A")["issues"], [])

    def test_changed_or_missing_source_is_hidden_without_fallback(self):
        for change in ("changed", "missing", "quote"):
            with self.subTest(change=change):
                segments, data = example()
                if change == "changed":
                    segments[0]["markdown"] += " New evidence."
                elif change == "missing":
                    segments.clear()
                else:
                    data["cards"][0]["anchor"]["quote"] = "Invented phrase"
                result = validate_reading_teacher(data, segments, "A")
                self.assertEqual(result["cards"], [])
                self.assertEqual(len(result["issues"]), 1)
                self.assertEqual(result["issues"][0]["id"], "definition")

    def test_overlapping_repeated_quotes_are_not_unique(self):
        segments, data = example()
        segments[0]["markdown"] = "aaaa"
        data["cards"][0]["anchor"].update(quote="aaa", source_sha256=hashlib.sha256(b"aaaa").hexdigest())
        self.assertEqual(validate_reading_teacher(data, segments, "A")["cards"], [])

    def test_all_evidence_ends_must_match(self):
        segments, data = example()
        data["cards"][0]["evidence"] = [{**data["cards"][0]["anchor"], "label": "Methods", "quote": "Invented methods"}]
        self.assertEqual(validate_reading_teacher(data, segments, "A")["cards"], [])

    def test_structurally_invalid_or_cross_paper_cards_fail_explicitly(self):
        for change in ("paper", "version", "boolean-version", "duplicate", "url", "definition", "source", "source-type", "kind-type", "transfer", "context"):
            with self.subTest(change=change):
                segments, data = example()
                if change == "paper":
                    data["paper_id"] = "B"
                elif change == "version":
                    data["version"] = 2
                elif change == "boolean-version":
                    data["version"] = True
                elif change == "duplicate":
                    data["cards"].append(copy.deepcopy(data["cards"][0]))
                elif change == "url":
                    data["sources"][0]["url"] = "javascript:alert(1)"
                elif change == "definition":
                    del data["cards"][0]["definition"]["paper"]
                elif change == "source":
                    data["cards"][0]["definition"]["external"][0]["source_id"] = "invented"
                elif change == "source-type":
                    data["cards"][0]["definition"]["external"][0]["source_id"] = []
                elif change == "kind-type":
                    data["cards"][0]["kind"] = []
                elif change == "transfer":
                    data["cards"][0]["kind"] = "transfer"
                else:
                    data["cards"][0]["context_ids"] = ["invented-memory"]
                with self.assertRaises(ValueError):
                    validate_reading_teacher(data, segments, "A")

    def test_transfer_uses_an_explicit_dated_local_context_snapshot(self):
        segments, data = example()
        data["project_context"] = {
            "project": "collaborative", "source_path": "local-context.html", "snapshot_at": "2026-07-04",
            "cards": [{"id": "ctx-goal", "title": "Goal", "summary": "A project hypothesis, not a paper finding."}],
        }
        data["cards"][0].update(kind="transfer", context_ids=["ctx-goal"])
        self.assertEqual(validate_reading_teacher(data, segments, "A")["project_context"], data["project_context"])


class TeacherHandlerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="reader-teacher-test-")
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)
        self.paper = self.workspace / "papers" / "A"
        self.segments, self.teacher = example()
        metadata = {"id": "A", "title": "Synthetic paper", "processing_mode": "deep", "processing_status": "ready"}
        for name, data in {
            "metadata.json": metadata, "segments.json": self.segments,
            "annotations.json": {"annotations": [{"id": "my-note", "segment_id": "p-0001", "note": "  My original thought.\n"}],
                                 "extension": {"keep": True}},
            "reading_teacher.json": self.teacher,
        }.items():
            reader.write_json(self.paper / name, data)
        reader.write_json(self.workspace / "library.json", {"papers": [{**metadata, "paper_dir": "papers/A"}]})
        for name in ("agent_chat", "run_mineru", "schedule_export_notes_and_annotated"):
            patcher = mock.patch.object(reader, name, side_effect=AssertionError(f"Unexpected {name}"))
            patcher.start()
            self.addCleanup(patcher.stop)

    def request(self, endpoint, method="GET", data=None):
        raw = json.dumps(data or {}).encode()
        handler = object.__new__(reader.ReaderHandler)
        handler.workspace, handler.path, handler.command = self.workspace, endpoint, method
        handler.request_version = "HTTP/1.1"
        handler.requestline = f"{method} {endpoint} HTTP/1.1"
        handler.headers = {"Content-Length": str(len(raw))}
        handler.rfile, handler.wfile = io.BytesIO(raw), io.BytesIO()
        handler.log_message = lambda *args: None
        getattr(handler, f"do_{method}")()
        headers, _, content = handler.wfile.getvalue().partition(b"\r\n\r\n")
        return int(headers.split()[1]), content

    def test_teacher_get_is_read_only_and_source_get_does_not_load_teacher(self):
        before = {path.name: path.read_bytes() for path in self.paper.iterdir()}
        with mock.patch.object(reader, "validate_reading_teacher", side_effect=AssertionError("Source must not wait for teacher")):
            status, content = self.request("/api/papers/A")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(content)["teacher_available"])
        status, content = self.request("/api/papers/A/reading-teacher")
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(content)["teacher"]["cards"]), 1)
        self.assertEqual({path.name: path.read_bytes() for path in self.paper.iterdir()}, before)

    def test_malformed_teacher_does_not_break_paper_reading(self):
        for text in ("{broken", "null"):
            with self.subTest(text=text):
                (self.paper / "reading_teacher.json").write_text(text, encoding="utf-8")
                self.assertEqual(self.request("/api/papers/A")[0], 200)
                status, content = self.request("/api/papers/A/reading-teacher")
                self.assertEqual(status, 409)
                self.assertIn("Reading teacher unavailable", json.loads(content)["error"])
                status, content = self.request("/api/papers/A/notes-md")
                self.assertEqual(status, 200, "Optional teacher errors must not break personal-note exports.")
                self.assertIn(b"My original thought.", content)
                reader.write_notes_and_annotated(self.paper)
                self.assertIn("My original thought.", (self.paper / "notes.md").read_text(encoding="utf-8"))
                if text == "{broken":
                    with self.assertRaises(json.JSONDecodeError):
                        reader.load_reading_data(self.paper)

    def test_absent_teacher_is_normal_and_unknown_paper_is_not(self):
        (self.paper / "reading_teacher.json").unlink()
        status, content = self.request("/api/papers/A/reading-teacher")
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(content)["teacher"]["available"])
        self.assertEqual(self.request("/api/papers/missing/reading-teacher")[0], 404)

    def test_export_keeps_teacher_separate_and_accepted_definition_origin_verbatim(self):
        annotations = reader.read_json(self.paper / "annotations.json", {})
        original = copy.deepcopy(annotations["annotations"][0])
        definition = {
            "id": "ai-def-example", "segment_id": "p-0001", "target": "source", "quote": "careful decision",
            "range": {"start": 24, "end": 40}, "note": "Saved AI definition\nhttps://example.org/definition",
            "origin": {"kind": "reading-teacher", "content_type": "definition", "document_id": "example-v1",
                       "card_id": "definition", "definition": self.teacher["cards"][0]["definition"]},
        }
        annotations["annotations"].append(definition)
        with mock.patch.object(reader, "schedule_export_notes_and_annotated"):
            status, _ = self.request("/api/papers/A/annotations", "POST", annotations)
        self.assertEqual(status, 200)
        saved = reader.read_json(self.paper / "annotations.json", {})
        self.assertEqual(saved["annotations"][0]["note"], original["note"])
        self.assertEqual(saved["annotations"][1]["origin"], definition["origin"])
        self.assertEqual(saved["extension"], {"keep": True})
        snapshot = reader.load_reading_data(self.paper, "A")
        self.assertEqual(snapshot["files"]["reading_teacher.json"], self.teacher)
        markdown = reader.make_notes_markdown(snapshot)
        self.assertIn("Accepted AI definition (AI-origin; reader edits retained)", markdown)
        self.assertIn(original["note"], markdown)
        self.assertIn("https://example.org/definition", markdown)
        self.assertNotIn(self.teacher["cards"][0]["question"], markdown)

    def test_definition_adoption_does_not_count_as_independent_reflection(self):
        definition = {"id": "definition", "segment_id": "p-0001", "note": "Stored AI definition",
                      "origin": {"kind": "reading-teacher", "content_type": "definition"}}
        reader.write_json(self.paper / "annotations.json", {"annotations": [definition, {**definition, "id": "second"}]})
        self.assertEqual(reader.annotation_counts_by_segment(self.paper), {})
        reader.write_json(self.paper / "annotations.json", {"annotations": [definition, {
            "id": "my-response", "segment_id": "p-0001", "note": "My independent thought.",
            "teacher_prompt": {"card_id": "definition", "question": "What does this mean?"},
        }]})
        self.assertEqual(reader.annotation_counts_by_segment(self.paper), {"p-0001": {"highlight_count": 1, "note_count": 1}})


if __name__ == "__main__":
    unittest.main()
