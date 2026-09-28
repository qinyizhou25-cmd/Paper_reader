from __future__ import annotations

import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feishu_metadata as feishu
import paper_reader_agent as reader


class FeishuMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="reader-feishu-test-")
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)
        self.paper = self.workspace / "papers" / "paper-a"
        self.paper.mkdir(parents=True)
        self.title = "Synthetic Study: Evidence and Reading"
        self.metadata = {
            "id": "paper-a", "title": self.title + "![](images/header.jpg)",
            "title_source": "paper", "authors": "Previous extraction",
            "read_status": "read", "tags": ["local-tag"], "processing_mode": "deep",
            "processing_status": "ready", "custom": {"preserve": True},
        }
        self.source_files = {
            "segments.json": [{"id": "p-1", "kind": "heading", "level": 1, "markdown": "# " + self.metadata["title"], "translation": "Existing translated title."}],
            "annotations.json": {"annotations": [{"id": "a-1", "segment_id": "p-1", "note": "  Original thought.\n", "custom": 7}]},
            "thinking.json": {"explain": {"content": "Original local brief."}, "blocks": [], "annotations": []},
            "outline.json": {"outline": [{"id": "p-1", "level": 1, "title": self.metadata["title"]}]},
        }
        reader.write_json(self.paper / "metadata.json", self.metadata)
        for name, value in self.source_files.items():
            reader.write_json(self.paper / name, value)
        reader.write_json(self.workspace / "library.json", {"papers": [{"id": "paper-a", "paper_dir": "papers/paper-a", "title": self.metadata["title"]}]})
        self.source = {
            "record_id": "recSynthetic", "metadata": {key: "" for key in feishu.FIELD_MAPPING},
            "field_sources": {key: value[0] for key, value in feishu.FIELD_MAPPING.items()},
            "briefings": {"raw text": "# Title: This is not the mapped title", "raw text_中文": "  An exact saved Feishu briefing.\n"},
        }
        self.source["metadata"].update({"title": self.title, "authors": "Feishu Author", "venue": "CHI", "year": "2026"})
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(reader, "ENV_FILES_LOADED", True).start()
        mock.patch.dict(os.environ, {
            "PAPER_READER_FEISHU_BASE_TOKEN": "SyntheticBase",
            "PAPER_READER_FEISHU_TABLE_ID": "tblSynthetic",
            "PAPER_READER_FEISHU_AUTO_SYNC": "1",
            "PAPER_READER_TRANSLATION_PROVIDER": "legacy",
        }).start()
        self.search = mock.patch.object(feishu, "search_records", return_value={
            "records": [{"record_id": "recSynthetic", "title": self.title}], "has_more": False,
        }).start()
        self.fetch = mock.patch.object(feishu, "read_record", side_effect=lambda *args, **kwargs: copy.deepcopy(self.source)).start()
        mock.patch.object(reader.urllib.request, "urlopen", side_effect=AssertionError("No network in unit tests")).start()

    def sync(self, **data: object) -> dict:
        return reader.sync_feishu_metadata(self.workspace, "paper-a", self.paper, dict(data))

    def request(self, path: str, method: str = "GET", data: object = None) -> tuple[int, dict]:
        body = json.dumps(data or {}).encode("utf-8")
        handler = object.__new__(reader.ReaderHandler)
        handler.workspace = self.workspace
        handler.path = path
        handler.command = method
        handler.request_version = "HTTP/1.1"
        handler.requestline = f"{method} {path} HTTP/1.1"
        handler.headers = {"Content-Length": str(len(body))}
        handler.rfile = io.BytesIO(body)
        handler.wfile = io.BytesIO()
        handler.log_message = lambda *args: None
        getattr(handler, f"do_{method}")()
        header, _, payload = handler.wfile.getvalue().partition(b"\r\n\r\n")
        return int(header.split()[1]), json.loads(payload)

    def test_title_cleaning_removes_image_markdown_and_keeps_real_name(self) -> None:
        self.assertEqual(feishu.clean_title(self.metadata["title"]), self.title)
        self.assertEqual(reader.guess_title_from_segments(self.source_files["segments.json"], ""), self.title)

    def test_unique_exact_match_copies_columns_without_rewriting_reading_data(self) -> None:
        before = {name: (self.paper / name).read_bytes() for name in self.source_files}
        result = self.sync(automatic=True)
        self.assertEqual(result["status"], "synced")
        metadata = reader.read_json(self.paper / "metadata.json", {})
        self.assertEqual(metadata["title"], self.title)
        self.assertEqual(metadata["authors"], "Feishu Author")
        self.assertEqual(metadata["title_source"], "feishu")
        self.assertEqual(metadata["feishu"]["record_id"], "recSynthetic")
        self.assertEqual(metadata["custom"], {"preserve": True})
        self.assertEqual(metadata["tags"], ["local-tag"])
        self.assertEqual(metadata["read_status"], "read")
        self.assertEqual(before, {name: (self.paper / name).read_bytes() for name in self.source_files})
        snapshot = reader.read_json(self.paper / "feishu_metadata.json", {})
        self.assertEqual(snapshot["briefings"], self.source["briefings"])
        self.assertEqual(snapshot["previous_metadata"]["title"], self.metadata["title"])
        self.assertEqual(reader.read_library_index(self.workspace)["papers"][0]["title"], self.title)

    def test_raw_brief_is_never_reparsed_to_generate_missing_metadata(self) -> None:
        self.source["metadata"]["authors"] = ""
        self.source["briefings"]["raw text_中文"] = "# 作者：Do not infer this"
        self.sync()
        self.assertEqual(reader.read_json(self.paper / "metadata.json", {})["authors"], "Previous extraction")

    def test_ambiguous_or_partial_search_never_silently_links(self) -> None:
        for results, has_more in [
            ([{"record_id": "recOther", "title": self.title + " Extended"}], False),
            ([{"record_id": "recOne", "title": self.title}, {"record_id": "recTwo", "title": self.title}], False),
            ([{"record_id": "recOne", "title": self.title}], True),
        ]:
            with self.subTest(has_more=has_more, count=len(results)):
                self.search.return_value = {"records": results, "has_more": has_more}
                self.assertEqual(self.sync(automatic=True)["status"], "needs_match")
        self.fetch.assert_not_called()
        self.assertFalse((self.paper / "feishu_metadata.json").exists())

    def test_linked_record_refreshes_by_id_even_when_title_changes(self) -> None:
        self.sync()
        self.search.reset_mock()
        self.source["metadata"]["title"] = "A renamed Feishu paper"
        result = self.sync(automatic=True)
        self.search.assert_not_called()
        self.assertEqual(result["metadata"]["title"], "A renamed Feishu paper")
        self.assertEqual(result["metadata"]["feishu"]["record_id"], "recSynthetic")

    def test_local_metadata_edits_are_retained_on_subsequent_refresh(self) -> None:
        self.sync()
        reader.apply_paper_metadata_update(self.workspace, "paper-a", self.paper, {"authors": "My correction", "title": "My local title"})
        result = self.sync(automatic=True)
        self.assertEqual(result["metadata"]["authors"], "My correction")
        self.assertEqual(result["metadata"]["title"], "My local title")
        self.assertIn("authors", result["local_overrides"])
        self.assertIn("title", result["local_overrides"])

    def test_metadata_changed_while_fetching_is_not_lost(self) -> None:
        def fetch(*args: object, **kwargs: object) -> dict:
            data = reader.read_json(self.paper / "metadata.json", {})
            data["authors"] = "Concurrent edit"
            reader.write_json(self.paper / "metadata.json", data)
            return copy.deepcopy(self.source)
        self.fetch.side_effect = fetch
        result = self.sync()
        self.assertEqual(result["metadata"]["authors"], "Concurrent edit")

    def test_feishu_title_cannot_be_replaced_by_pdf_title(self) -> None:
        result = self.sync()
        self.assertFalse(reader.should_replace_title(result["metadata"], self.title + " longer but incorrect"))
        self.assertFalse(reader.metadata_title_should_update(result["metadata"], "Wrong title", "paper_brief"))

    def test_error_preserves_cached_metadata(self) -> None:
        self.sync()
        before = {str(path): path.read_bytes() for path in self.workspace.rglob("*") if path.is_file()}
        for error in [RuntimeError("Feishu permission denied"), ValueError("The linked Feishu record no longer exists or is not accessible.")]:
            with self.subTest(error=error):
                self.fetch.side_effect = error
                status, body = self.request("/api/papers/paper-a/feishu-sync", "POST")
                self.assertEqual(status, 400)
                self.assertIn(str(error), body["error"])
                self.assertEqual(before, {str(path): path.read_bytes() for path in self.workspace.rglob("*") if path.is_file()})

    def test_automatic_request_cannot_arbitrarily_assign_record(self) -> None:
        with self.assertRaisesRegex(ValueError, "arbitrary"):
            self.sync(automatic=True, record_id="recDifferent")
        self.fetch.assert_not_called()

    def test_get_uses_cached_fields_without_cloud_requests(self) -> None:
        self.sync()
        self.fetch.reset_mock()
        self.search.reset_mock()
        before = {str(path): path.read_bytes() for path in self.workspace.rglob("*") if path.is_file()}
        status, body = self.request("/api/papers/paper-a")
        self.assertEqual(status, 200)
        self.assertEqual(body["metadata"]["authors"], "Feishu Author")
        self.assertEqual(body["feishu_metadata"]["briefings"], self.source["briefings"])
        self.fetch.assert_not_called()
        self.search.assert_not_called()
        self.assertEqual(before, {str(path): path.read_bytes() for path in self.workspace.rglob("*") if path.is_file()})


class FeishuCliTests(unittest.TestCase):
    def test_record_mapping_uses_actual_columns_not_brief_text(self) -> None:
        fields = [value[1] for value in feishu.FIELD_MAPPING.values()] + list(feishu.BRIEF_FIELDS.values())
        values = [""] * len(fields)
        values[0], values[1] = "Column title", "Column author"
        values[-2] = "# Title: Not the title\n# Author: Not the author"
        data = {"field_id_list": fields, "record_id_list": ["recSynthetic"], "data": [values]}
        with mock.patch.object(feishu, "run_cli", return_value=data) as run:
            result = feishu.read_record("SyntheticBase", "tblSynthetic", "recSynthetic")
        self.assertEqual(result["metadata"]["title"], "Column title")
        self.assertEqual(result["metadata"]["authors"], "Column author")
        self.assertIn("+record-get", run.call_args.args[0])
        self.assertNotIn("your questions", str(run.call_args))

    def test_rich_text_values_are_joined_without_rewriting(self) -> None:
        self.assertEqual(feishu.cell_text([{"text": "  Exact "}, {"text": "words.\n"}]), "  Exact words.\n")
        with self.assertRaises(ValueError):
            feishu.cell_text({"file_token": "not-a-text-field"})

    def test_missing_mapped_field_is_an_error_not_a_blank_cell(self) -> None:
        data = {"field_id_list": ["fldHGsQoto"], "record_id_list": ["recSynthetic"], "data": [["Title"]]}
        with mock.patch.object(feishu, "run_cli", return_value=data):
            with self.assertRaisesRegex(ValueError, "mapped fields"):
                feishu.read_record("SyntheticBase", "tblSynthetic", "recSynthetic")

    def test_missing_record_with_null_cells_is_not_a_successful_empty_record(self) -> None:
        fields = [value[1] for value in feishu.FIELD_MAPPING.values()] + list(feishu.BRIEF_FIELDS.values())
        data = {
            "field_id_list": fields, "record_id_list": ["recSynthetic"],
            "data": [[None] * len(fields)], "record_not_found": ["recSynthetic"],
        }
        with mock.patch.object(feishu, "run_cli", return_value=data):
            with self.assertRaisesRegex(ValueError, "no longer exists or is not accessible"):
                feishu.read_record("SyntheticBase", "tblSynthetic", "recSynthetic")

    def test_existing_record_with_empty_columns_remains_readable(self) -> None:
        fields = [value[1] for value in feishu.FIELD_MAPPING.values()] + list(feishu.BRIEF_FIELDS.values())
        data = {
            "field_id_list": fields, "record_id_list": ["recSynthetic"],
            "data": [[None] * len(fields)], "record_not_found": [],
        }
        with mock.patch.object(feishu, "run_cli", return_value=data):
            record = feishu.read_record("SyntheticBase", "tblSynthetic", "recSynthetic")
        self.assertEqual(record["metadata"], {key: "" for key in feishu.FIELD_MAPPING})
        self.assertEqual(record["record_id"], "recSynthetic")

    def test_long_titles_use_a_bounded_query_but_keep_the_full_returned_title(self) -> None:
        title = "An example full academic title longer than the fifty character search limit"
        data = {"field_id_list": ["fldHGsQoto"], "record_id_list": ["recSynthetic"], "data": [[title]]}
        with mock.patch.object(feishu, "run_cli", return_value=data) as run:
            result = feishu.search_records("SyntheticBase", "tblSynthetic", title)
        arguments = run.call_args.args[0]
        self.assertEqual(arguments[arguments.index("--keyword") + 1], title[:50])
        self.assertEqual(result["records"][0]["title"], title)

    def test_structured_cli_errors_on_stderr_are_not_misreported_as_invalid_json(self) -> None:
        result = subprocess.CompletedProcess([], 1, stdout="", stderr='{"ok":false,"error":{"type":"api","code":800010701,"message":"SECRET_VALUE"}}')
        with mock.patch.object(feishu, "cli_command", return_value="lark-cli.exe"), mock.patch.object(feishu.subprocess, "run", return_value=result):
            with self.assertRaisesRegex(RuntimeError, "code 800010701") as caught:
                feishu.run_cli(["+record-search"])
        self.assertNotIn("SECRET_VALUE", str(caught.exception))

    def test_cli_invocation_is_argv_only_and_read_only(self) -> None:
        result = subprocess.CompletedProcess([], 0, stdout='{"ok":true,"data":{"records":[]}}', stderr="")
        with mock.patch.object(feishu, "cli_command", return_value="lark-cli.exe"), mock.patch.object(feishu.subprocess, "run", return_value=result) as run:
            feishu.run_cli(["+record-search", "--keyword", 'A title & "not a command"'])
        argv = run.call_args.args[0]
        self.assertEqual(argv[-2:], ["--as", "user"])
        self.assertIn('A title & "not a command"', argv)
        self.assertFalse(run.call_args.kwargs.get("shell", False))
        self.assertEqual(run.call_args.kwargs["timeout"], 45)

    def test_cli_failures_do_not_echo_credentials_or_raw_output(self) -> None:
        result = subprocess.CompletedProcess([], 1, stdout='{"ok":false,"error":{"type":"auth","message":"SECRET_VALUE"}}', stderr="SECRET_VALUE")
        with mock.patch.object(feishu, "cli_command", return_value="lark-cli.exe"), mock.patch.object(feishu.subprocess, "run", return_value=result):
            with self.assertRaises(RuntimeError) as captured:
                feishu.run_cli(["+record-get"])
        self.assertNotIn("SECRET_VALUE", str(captured.exception))
        self.assertIn("auth", str(captured.exception))

    def test_invalid_identifiers_or_response_do_not_become_empty_success(self) -> None:
        with self.assertRaises(ValueError):
            feishu.validate_ids("https://feishu.cn/wiki/token", "tblSynthetic")
        with self.assertRaises(ValueError):
            feishu.validate_ids("SyntheticBase", "tblSynthetic", "recX & command")
        with self.assertRaises(ValueError):
            feishu.records_from_result({"field_id_list": ["a"], "record_id_list": ["recA"], "data": [[]]})


class PaperBriefLabelTests(unittest.TestCase):
    def test_title_label_does_not_require_a_markdown_heading(self) -> None:
        title = "Synthetic Study: Evidence and Reading"
        for label in ["# Title:", "Title:", "## title:", "**Title**:", "### **Title:**", "- Title:", "标题："]:
            with self.subTest(label=label):
                self.assertEqual(reader.extract_title_from_paper_brief(f"{label} {title}\nAuthor: Example Author"), title)

    def test_unlabelled_prose_is_not_mistaken_for_title_metadata(self) -> None:
        for prose in ["The title of this study is interesting.", "# Abstract\nThe work explores reading.", "Title:", "Title: Unknown"]:
            with self.subTest(prose=prose):
                self.assertEqual(reader.extract_title_from_paper_brief(prose), "")


if __name__ == "__main__":
    unittest.main()
