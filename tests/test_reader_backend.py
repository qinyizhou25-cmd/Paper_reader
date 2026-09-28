"""Focused reader regressions; fixtures stay under tests, never in the real library."""

from __future__ import annotations

import copy
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import shutil
import sys
import threading
import time
import unittest
from unittest import mock
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paper_reader_agent as reader


class ReaderBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parent / f".reader-fixture-{uuid.uuid4().hex}"
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.workspace = self.root / "workspace"
        self.paper_dir = self.workspace / "papers" / "paper-a"
        self.paper_dir.mkdir(parents=True)
        self.note = "  我的问题：为什么？\n\n```text\nkeep this literally\n```  \n"
        self.files = {
            "metadata.json": {
                "title": "Original title",
                "processing_mode": "deep",
                "processing_status": "ready",
                "custom": {"source": "external agent"},
            },
            "segments.json": [
                {
                    "id": "p-0001",
                    "kind": "paragraph",
                    "markdown": "Original source paragraph.",
                    "translation": "原始翻译。",
                    "source_page": 3,
                    "custom": {"stable": True},
                },
            ],
            "annotations.json": {
                "version": 7,
                "custom": {"keep": "envelope"},
                "annotations": [
                    {
                        "id": "highlight-only",
                        "segment_id": "p-0001",
                        "target": "translation",
                        "type": "range",
                        "color": "yellow",
                        "quote": "原始翻译",
                        "note": "",
                        "range": {"start": 0, "end": 4, "unit": "utf16"},
                        "paired_range": {"start": 0, "end": 8, "target": "source", "quote": "Original"},
                        "annotation_group_id": "group-1",
                        "group_index": 0,
                        "group_count": 2,
                        "custom": {"keep": [1, 2]},
                    },
                    {
                        "id": "orphan-note",
                        "segment_id": "missing-segment",
                        "target": "source",
                        "quote": "  a verbatim quote\nwith a second line  ",
                        "note": self.note,
                    },
                    {
                        "id": "whole-segment",
                        "segment_id": "p-0001",
                        "type": "segment",
                        "target": "source",
                        "color": "blue",
                        "quote": "",
                        "note": "",
                    },
                ],
            },
            "thinking.json": {
                "version": 4,
                "custom": {"keep": "thinking envelope"},
                "explain": {
                    "content": "Existing AI briefing; not a human note.",
                    "source": "agent",
                    "custom": "brief metadata",
                },
                "blocks": [
                    {
                        "id": "ai-1",
                        "type": "ai_output",
                        "content": "Existing AI answer; not a human note.",
                        "prompt": "  Original human question?\n",
                        "model": "stored-model",
                        "selection_refs": [
                            {
                                "segment_id": "p-0001",
                                "target": "translation",
                                "quote": "Long original selected text " * 70,
                                "range": {"start": 0, "end": 1890, "unit": "utf16"},
                                "custom": "keep reference",
                            },
                        ],
                        "source_refs": [{"quote": "Untruncated source " * 80, "custom": "keep source"}],
                        "custom": {"keep": "block metadata"},
                    },
                ],
                "annotations": [
                    {
                        "id": "thinking-highlight",
                        "block_id": reader.PAPER_BRIEF_BLOCK_ID,
                        "target": "thinking",
                        "quote": "Existing AI briefing",
                        "note": "",
                        "range": {"start": 0, "end": 20, "unit": "utf16"},
                        "custom": {"keep": "annotation metadata"},
                    },
                    {
                        "id": "orphan-thinking",
                        "block_id": "missing-block",
                        "target": "thinking",
                        "quote": "Orphaned selected text",
                        "note": "  Do not silently drop this question.  ",
                    },
                ],
                "report_thoughts": [
                    {"id": "thought-1", "note": "  Original thought?\n", "custom": {"keep": True}},
                ],
            },
            "reading_progress.json": {
                "version": 9,
                "segments": {"p-0001": {"visible_ms": 5000, "visits": 2, "custom": "keep"}},
                "position": {"segment_id": "p-0001", "offset": 17},
                "custom": "do not recalculate",
            },
            "outline.json": {"outline": [], "custom": "original outline"},
            "takeaway_doc.json": {
                "blocks": [
                    {
                        "id": "takeaway-1",
                        "type": "bullet",
                        "text": "  Human takeaway text\nwith a second line.  \n",
                        "note": "Original takeaway question?",
                        "source": "user",
                    },
                ],
                "custom": "mixed-origin legacy data",
            },
        }
        for name, value in self.files.items():
            self.write_json(self.paper_dir / name, value)
        self.write_json(
            self.workspace / "library.json",
            {"version": "index-version", "papers": [{"id": "paper-a", "title": "Alpha", "paper_dir": str(Path("papers") / "paper-a")}]},
        )
        self.env_mock = mock.patch.object(reader, "env_value", return_value="")
        self.env_mock.start()
        self.addCleanup(self.env_mock.stop)
        for name in (
            "load_env_files", "agent_chat", "kimi_chat", "kimi_request",
            "start_background_paper_processing", "resume_interrupted_processing_tasks",
        ):
            guard = mock.patch.object(reader, name, side_effect=AssertionError(f"{name} is forbidden in backend fixtures"))
            guard.start()
            self.addCleanup(guard.stop)
        for target, name in ((reader.urllib.request, "urlopen"), (reader.subprocess, "run"), (reader.subprocess, "Popen")):
            guard = mock.patch.object(target, name, side_effect=AssertionError(f"{name} is forbidden in backend fixtures"))
            guard.start()
            self.addCleanup(guard.stop)
        self.schedule_patch = mock.patch.object(reader, "schedule_export_notes_and_annotated")
        self.export_schedule = self.schedule_patch.start()
        self.addCleanup(self.schedule_patch.stop)

    @staticmethod
    def write_json(path: Path, value: object) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def tree_state(self) -> dict[str, tuple[bytes, int]]:
        return {
            str(path.relative_to(self.root)): (path.read_bytes(), path.stat().st_mtime_ns)
            for path in self.root.rglob("*")
            if path.is_file()
        }

    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        data: object = None,
        headers: dict[str, str] | None = None,
        workspace: Path | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        body = b"" if data is None else json.dumps(data, ensure_ascii=False).encode("utf-8")
        handler = object.__new__(reader.ReaderHandler)
        handler.workspace = workspace or self.workspace
        handler.path = path
        handler.command = method
        handler.request_version = "HTTP/1.1"
        handler.requestline = f"{method} {path} HTTP/1.1"
        handler.headers = {"Content-Length": str(len(body)), **(headers or {})}
        handler.rfile = io.BytesIO(body)
        handler.wfile = io.BytesIO()
        handler.log_message = lambda *args: None
        with mock.patch.object(reader.traceback, "print_exc"):
            getattr(handler, f"do_{method}")()
        raw_headers, _, payload = handler.wfile.getvalue().partition(b"\r\n\r\n")
        lines = raw_headers.decode("latin-1").splitlines()
        status = int(lines[0].split()[1])
        response_headers = dict(line.split(": ", 1) for line in lines[1:])
        return status, response_headers, payload

    def test_snapshot_preserves_every_original_json_value_without_normalization(self) -> None:
        before = self.tree_state()
        snapshot = reader.load_reading_data(self.paper_dir, "paper-a")
        self.assertEqual(snapshot["format"], "paper-reader-reading-data")
        self.assertEqual(snapshot["version"], 1)
        self.assertEqual(snapshot["paper_id"], "paper-a")
        self.assertEqual(snapshot["files"], self.files)
        self.assertIn("AI", snapshot["sources"]["thinking.json#/blocks"])
        self.assertEqual(self.tree_state(), before)

    def test_app_publication_settings_select_table_mode_and_named_columns(self) -> None:
        from reading_archive import TABLE_COLUMN_NAMES

        with mock.patch.object(reader, "feishu_settings", return_value=("Fixture", "tblFixture", "local-cli")), \
                mock.patch.object(reader, "env_value", side_effect=lambda key, default="": default):
            settings = reader.publication_settings()
        self.assertEqual(settings["mode"], "table")
        self.assertEqual(settings["text_fields"], TABLE_COLUMN_NAMES)
        self.assertEqual(settings["backup_field"], "阅读数据备份")
        self.assertEqual(settings["executable"], "local-cli")
        overrides = {"PAPER_READER_FEISHU_NOTES_FIELD": "Approved notes column",
                     "PAPER_READER_FEISHU_BACKUP_FIELD": "Approved backup"}
        with mock.patch.object(reader, "feishu_settings", return_value=("Fixture", "tblFixture", "local-cli")), \
                mock.patch.object(reader, "env_value", side_effect=lambda key, default="": overrides.get(key, default)):
            changed = reader.publication_settings()
        self.assertEqual(changed["text_fields"]["my-notes"], "Approved notes column")
        self.assertEqual(changed["backup_field"], "Approved backup")
        self.assertEqual(settings["text_fields"], TABLE_COLUMN_NAMES)

    def test_publication_http_routes_use_current_paper_and_require_explicit_confirmation(self) -> None:
        before = self.tree_state()
        service = mock.Mock()
        service.status.return_value = {"status": "idle", "error": ""}
        service.preview.return_value = {"preview_id": "preview-token", "sections": [], "changed": True}
        service.start.return_value = {"status": "publishing", "job_id": "publication-job", "error": ""}
        settings = {"base_token": "Fixture", "table_id": "tblFixture"}
        headers = {"Host": "127.0.0.1:8765", "Origin": "http://127.0.0.1:8765", "Content-Type": "application/json"}
        with mock.patch.object(reader, "publication_service", return_value=service), mock.patch.object(reader, "publication_settings", return_value=settings):
            status, _, body = self.request("/api/papers/paper-a/feishu-publication", headers=headers)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["publication"]["status"], "idle")
            status, _, body = self.request("/api/papers/paper-a/feishu-publication/preview", method="POST", data={}, headers=headers)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["preview"]["preview_id"], "preview-token")
            service.start.assert_not_called()
            status, _, body = self.request("/api/papers/paper-a/feishu-publication/publish", method="POST",
                                          data={"preview_id": "preview-token", "confirm": True}, headers=headers)
            self.assertEqual(status, 200)
            service.start.assert_called_once_with(self.paper_dir.resolve(), settings, "preview-token", True)
            self.assertEqual(json.loads(body)["publication"]["job_id"], "publication-job")
        self.assertEqual(self.tree_state(), before)

    def test_publication_http_rejects_foreign_origins_nonlocal_hosts_and_unconfirmed_data(self) -> None:
        service = mock.Mock()
        valid = {"Host": "localhost:8765", "Origin": "http://localhost:8765", "Content-Type": "application/json"}
        cases = [
            ({**valid, "Origin": "https://unrelated.example"}, {"preview_id": "p", "confirm": True}, 403),
            ({**valid, "Host": "unrelated.example", "Origin": "http://unrelated.example"}, {"preview_id": "p", "confirm": True}, 403),
            ({**valid, "Content-Type": "text/plain"}, {"preview_id": "p", "confirm": True}, 400),
            (valid, {"preview_id": "p", "confirm": False}, 400),
            (valid, {"preview_id": "p", "confirm": 1}, 400),
            (valid, {"preview_id": "p", "confirm": True, "document_url": "https://example.org"}, 400),
            (valid, ["not", "an", "object"], 400),
        ]
        with mock.patch.object(reader, "publication_service", return_value=service):
            for headers, data, expected in cases:
                with self.subTest(headers=headers, data=data):
                    status, _, body = self.request("/api/papers/paper-a/feishu-publication/publish", method="POST", data=data, headers=headers)
                    self.assertEqual(status, expected)
                    self.assertFalse(json.loads(body)["ok"])
        service.start.assert_not_called()
        service.preview.assert_not_called()

    def test_publication_http_reports_conflicts_and_does_not_write_reading_files(self) -> None:
        before = self.tree_state()
        service = mock.Mock()
        service.start.side_effect = reader.feishu_publish.PublicationConflict("The original preview changed.")
        headers = {"Host": "127.0.0.1:8765", "Content-Type": "application/json"}
        with mock.patch.object(reader, "publication_service", return_value=service), mock.patch.object(reader, "publication_settings", return_value={}):
            status, _, body = self.request("/api/papers/paper-a/feishu-publication/publish", method="POST",
                                          data={"preview_id": "old-preview", "confirm": True}, headers=headers)
        self.assertEqual(status, 409)
        self.assertIn("preview changed", json.loads(body)["error"])
        self.assertEqual(self.tree_state(), before)

    def test_real_http_publication_preserves_originals_and_skips_unchanged_uploads(self) -> None:
        self.assert_http_publication()

    def test_real_http_table_publication_uses_exact_cells_without_docs_or_duplicate_backups(self) -> None:
        self.assert_http_publication(table=True)

    def assert_http_publication(self, *, table: bool = False) -> None:
        from test_feishu_publish import ARCHIVE, BACKUP, BASE, RECORD, TABLE, FakeCLI, SETTINGS, TABLE_SETTINGS
        from reading_archive import build_table_archive

        settings = TABLE_SETTINGS if table else SETTINGS
        self.files["metadata.json"]["feishu"] = {
            "base_token": BASE, "table_id": TABLE, "record_id": RECORD,
        }
        self.write_json(self.paper_dir / "metadata.json", self.files["metadata.json"])
        original_bytes = {name: (self.paper_dir / name).read_bytes() for name in self.files}
        fake = FakeCLI()
        if table:
            fake.enable_table_fields()
            fake.forbid_docs = True
        service = reader.feishu_publish.PublicationService(
            snapshot_reader=reader.load_reading_data,
            json_reader=reader.read_json,
            json_writer=reader.write_json,
            text_writer=reader.write_text_atomic,
        )
        handler_type = type("PublicationFixtureHandler", (reader.ReaderHandler,), {
            "workspace": self.workspace, "log_message": lambda *args: None,
        })
        with mock.patch.object(reader, "publication_service", return_value=service), \
                mock.patch.object(reader, "publication_settings", return_value=settings), \
                mock.patch.object(reader.feishu_metadata, "cli_command", return_value="fake-lark-cli.exe"), \
                mock.patch.object(reader.feishu_metadata.subprocess, "run", side_effect=fake), \
                ThreadingHTTPServer(("127.0.0.1", 0), handler_type) as server:
            port = server.server_address[1]
            server_thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
            server_thread.start()

            def request(suffix: str = "", data: object = None) -> dict:
                connection = HTTPConnection("127.0.0.1", port, timeout=5)
                body = None if data is None else json.dumps(data)
                headers = {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{port}"}
                try:
                    connection.request("GET" if data is None else "POST",
                                       f"/api/papers/paper-a/feishu-publication{suffix}", body, headers)
                    response = connection.getresponse()
                    payload = json.loads(response.read())
                    self.assertEqual(response.status, 200, payload)
                    self.assertTrue(payload["ok"], payload)
                    return payload
                finally:
                    connection.close()

            def wait_for_publication() -> dict:
                deadline = time.monotonic() + 10
                status = request()["publication"]
                while status["status"] == "publishing" and time.monotonic() < deadline:
                    time.sleep(0.02)
                    status = request()["publication"]
                self.assertEqual(status["status"], "synced", status)
                return status

            try:
                self.assertEqual(request()["publication"]["status"], "idle")
                preview = request("/preview", {})["preview"]
                self.assertEqual(fake.writes, [])
                request("/publish", {"preview_id": preview["preview_id"], "confirm": True})
                status = wait_for_publication()
                if table:
                    self.assertEqual(status["mode"], "table")
                    self.assertEqual(preview["mode"], "table")
                    self.assertIn(RECORD, status["record_url"])
                    self.assertEqual(len(preview["destination"]["text_fields"]), 4)
                    self.assertEqual(status["document_url"], "")
                    self.assertIsNone(fake.record[ARCHIVE])
                    self.assertFalse(fake.documents)
                    columns = build_table_archive(reader.load_reading_data(self.paper_dir, "paper-a"))["columns"]
                    self.assertEqual([column["text"] for column in preview["columns"]], [column["text"] for column in columns])
                    for column in columns:
                        self.assertEqual(fake.record[fake.table_fields[column["id"]]], column["text"])
                    self.assertEqual(fake.writes.count("+record-upsert"), 1)
                else:
                    self.assertEqual(fake.record[ARCHIVE], status["document_url"])
                self.assertEqual(len(fake.record[BACKUP]), 1)
                backup = json.loads(next(iter(fake.blobs.values())))
                self.assertEqual(backup["reading_data"]["files"], self.files)
                self.assertEqual(fake.record["fldManual"], "Preserve this manual value.")
                self.assertEqual({name: (self.paper_dir / name).read_bytes() for name in self.files}, original_bytes)
                writes = list(fake.writes)
                unchanged = request("/preview", {})["preview"]
                self.assertFalse(unchanged["changed"])
                request("/publish", {"preview_id": unchanged["preview_id"], "confirm": True})
                wait_for_publication()
                self.assertEqual(fake.writes, writes)
            finally:
                server.shutdown()
                server_thread.join(5)
                worker = reader.feishu_publish._runtime(self.paper_dir.resolve()).thread
                if worker:
                    worker.join(10)
                    self.assertFalse(worker.is_alive(), "Do not restore the real CLI while a fixture upload is running.")
                with reader.feishu_publish._RUNTIME_LOCK:
                    reader.feishu_publish._RUNTIMES.pop(os.path.normcase(str(self.paper_dir.resolve())), None)

    def test_markdown_keeps_highlights_orphans_verbatim_notes_and_source_distinctions(self) -> None:
        text = reader.make_notes_markdown(reader.load_reading_data(self.paper_dir, "paper-a"))
        for value in [
            "highlight-only", "whole-segment", "orphan-note", "thinking-highlight", "orphan-thinking",
            "group-1", '"unit": "utf16"', '"paired_range"', '"target": "translation"',
            "原始翻译", "Orphaned selected text", "Original takeaway question?",
            "  Original thought?\n", "  Original human question?\n", self.note,
            "annotations.json#/annotations/0", "thinking.json#/annotations/0",
            "thinking.json#/report_thoughts/0", "Stored thinking blocks", "Original AI Paper Brief",
        ]:
            with self.subTest(value=value):
                self.assertIn(value, text)
        self.assertIn("````text\n" + self.note, text)
        self.assertIn("Target segment context (not a recorded quote)", text)
        self.assertIn("Original source paragraph.", text)

    def test_export_writes_only_derivatives_and_uses_the_same_faithful_renderer(self) -> None:
        original_bytes = {name: (self.paper_dir / name).read_bytes() for name in self.files}
        reader.export_notes_and_annotated(self.paper_dir)
        self.assertEqual(
            (self.paper_dir / "notes.md").read_text(encoding="utf-8"),
            reader.make_notes_markdown(reader.load_reading_data(self.paper_dir)),
        )
        self.assertIn("Original source paragraph.", (self.paper_dir / "annotated.md").read_text(encoding="utf-8"))
        for name, value in original_bytes.items():
            self.assertEqual((self.paper_dir / name).read_bytes(), value)

    def test_chat_records_export_verbatim_by_recorded_role_without_classifying_prose(self) -> None:
        user_message = {"id": "chat-user", "role": "user", "content": self.note, "custom": {"keep": True}}
        assistant_message = {"id": "chat-ai", "role": "assistant", "content": "An AI question? Not a user-authored question."}
        unknown_message = {"id": "chat-unknown", "message": "  Unknown role; do not guess?\n"}
        for chat in (
            [user_message, assistant_message, unknown_message],
            {"id": "chat-thread", "messages": [user_message, assistant_message, unknown_message], "custom": "keep thread"},
        ):
            with self.subTest(chat=chat):
                thinking = {**self.files["thinking.json"], "chat": chat, "messages": [unknown_message]}
                self.write_json(self.paper_dir / "thinking.json", thinking)
                before = self.tree_state()
                snapshot = reader.load_reading_data(self.paper_dir)
                text = reader.make_notes_markdown(snapshot)
                self.assertEqual(snapshot["files"]["thinking.json"], thinking)
                self.assertIn(self.note, text)
                self.assertIn('"role": "user"', text)
                self.assertIn('"role": "assistant"', text)
                self.assertIn(assistant_message["content"], text)
                self.assertIn(unknown_message["message"], text)
                self.assertIn("recorded roles/sources; not classified", text)
                self.assertNotIn('"role": "unknown"', text)
                self.assertIn("thinking.json#/messages/0", text)
                expected_source = "thinking.json#/chat/0" if isinstance(chat, list) else "thinking.json#/chat/messages/0"
                self.assertIn(expected_source, text)
                self.assertEqual(self.tree_state(), before)

    def test_takeaway_human_text_and_note_whitespace_survive_save_and_export(self) -> None:
        doc = copy.deepcopy(self.files["takeaway_doc.json"])
        doc["blocks"][0]["note"] = self.note
        status, _, body = self.request("/api/papers/paper-a/takeaway-doc", method="POST", data=doc)
        self.assertEqual(status, 200, body)
        saved = json.loads(body)["takeaway_doc"]["blocks"][0]
        self.assertEqual(saved["text"], doc["blocks"][0]["text"])
        self.assertEqual(saved["note"], self.note)
        status, _, body = self.request("/api/papers/paper-a/notes-md")
        self.assertEqual(status, 200)
        self.assertIn(saved["text"], body.decode("utf-8"))
        self.assertIn(self.note, body.decode("utf-8"))
        self.export_schedule.assert_called_once_with(self.paper_dir)

    def test_explicit_chat_saves_original_prompt_whitespace_without_real_generation(self) -> None:
        with (
            mock.patch.object(reader, "generate_chat_reply", return_value=("Fixture-only AI output", "fixture")) as generate,
            mock.patch.object(reader, "load_paper_markdown_for_chat", return_value="Fixture-only source"),
        ):
            result = reader.append_chat_output_block("paper-a", self.paper_dir, {"message": self.note, "mode": "free"})
        self.assertEqual(generate.call_args.args[3], self.note)
        self.assertEqual(result["block"]["prompt"], self.note)
        saved = reader.read_json(self.paper_dir / "thinking.json", {})
        self.assertEqual(saved["blocks"][0]["prompt"], self.note)
        self.export_schedule.assert_called_once_with(self.paper_dir)
        with self.assertRaisesRegex(ValueError, "message is required"):
            reader.append_chat_output_block("paper-a", self.paper_dir, {"message": " \n\t"})

    def test_notes_download_is_fresh_no_store_and_does_not_write_even_derivatives(self) -> None:
        (self.paper_dir / "notes.md").write_text("STALE FILE", encoding="utf-8")
        before = self.tree_state()
        status, headers, body = self.request("/api/papers/paper-a/notes-md")
        self.assertEqual(status, 200)
        self.assertIn("text/markdown", headers["Content-Type"])
        self.assertIn("attachment;", headers["Content-Disposition"])
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn(self.note, body.decode("utf-8"))
        self.assertNotIn(b"STALE FILE", body)
        self.assertEqual(self.tree_state(), before)
        annotations = copy.deepcopy(self.files["annotations.json"])
        annotations["annotations"][0]["note"] = "Fresh external agent edit"
        self.write_json(self.paper_dir / "annotations.json", annotations)
        before = self.tree_state()
        status, _, body = self.request("/api/papers/paper-a/notes-md", headers={"If-None-Match": "*"})
        self.assertEqual(status, 200)
        self.assertIn(b"Fresh external agent edit", body)
        self.assertEqual(self.tree_state(), before)
        self.export_schedule.assert_not_called()

    def test_raw_download_is_lossless_fresh_and_not_cacheable(self) -> None:
        before = self.tree_state()
        status, headers, body = self.request("/api/papers/paper-a/reading-data", headers={"If-None-Match": "*"})
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn("attachment;", headers["Content-Disposition"])
        self.assertEqual(json.loads(body)["files"], self.files)
        self.assertEqual(self.tree_state(), before)
        changed = {**self.files["thinking.json"], "external": ["new", "data"]}
        self.write_json(self.paper_dir / "thinking.json", changed)
        _, _, body = self.request("/api/papers/paper-a/reading-data")
        self.assertEqual(json.loads(body)["files"]["thinking.json"], changed)

    def test_missing_export_files_are_not_synthesized_on_disk(self) -> None:
        empty_paper = self.workspace / "papers" / "empty-paper"
        empty_paper.mkdir()
        before = self.tree_state()
        status, _, body = self.request("/api/papers/empty-paper/reading-data")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["files"], {})
        status, _, body = self.request("/api/papers/empty-paper/notes-md")
        self.assertEqual(status, 200)
        self.assertIn(b"empty-paper", body)
        self.assertEqual(list(empty_paper.iterdir()), [])
        self.assertEqual(self.tree_state(), before)

    def test_malformed_export_source_fails_instead_of_silently_exporting_empty_data(self) -> None:
        (self.paper_dir / "annotations.json").write_text('{"annotations": [', encoding="utf-8")
        (self.paper_dir / "notes.md").write_text("KEEP PREVIOUS EXPORT", encoding="utf-8")
        before = self.tree_state()
        for endpoint in ("notes-md", "reading-data"):
            status, headers, _ = self.request(f"/api/papers/paper-a/{endpoint}")
            self.assertEqual(status, 500)
            self.assertEqual(headers["Cache-Control"], "no-store")
        with self.assertRaises(json.JSONDecodeError):
            reader.export_notes_and_annotated(self.paper_dir)
        self.assertEqual(self.tree_state(), before)

    def test_windows_utf8_bom_files_are_exported_without_rewriting_them(self) -> None:
        path = self.paper_dir / "annotations.json"
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        before = self.tree_state()
        status, _, body = self.request("/api/papers/paper-a/reading-data")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["files"], self.files)
        self.assertEqual(self.tree_state(), before)

    def test_paper_get_does_not_generate_previews_parse_pdfs_or_initialize_workspace(self) -> None:
        before = self.tree_state()
        with (
            mock.patch.object(reader, "figure_fallbacks_from_pdf", side_effect=AssertionError("PDF fallback")),
            mock.patch.object(reader, "infer_paper_preview_image", side_effect=AssertionError("preview discovery")),
            mock.patch.object(reader, "ensure_workspace", side_effect=AssertionError("workspace initialization")),
            mock.patch.object(reader, "start_background_paper_processing", side_effect=AssertionError("AI processing")),
        ):
            status, headers, body = self.request("/api/papers/paper-a")
        self.assertEqual(status, 200, body)
        self.assertEqual(json.loads(body)["figure_fallbacks"], {})
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(self.tree_state(), before)
        self.export_schedule.assert_not_called()

    def test_paper_get_advertises_existing_original_pdf_without_metadata_rewrites(self) -> None:
        pdf = self.paper_dir / "original.pdf"
        pdf.write_bytes(b"%PDF-1.4 fixture-only content; no parsing allowed")
        before = self.tree_state()
        with mock.patch.object(reader, "figure_fallbacks_from_pdf", side_effect=AssertionError("No PDF parsing")):
            status, _, body = self.request("/api/papers/paper-a")
        self.assertEqual(status, 200, body)
        self.assertEqual(json.loads(body)["metadata"]["source_pdf"], "original.pdf")
        status, headers, body = self.request("/api/papers/paper-a/pdf")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/pdf")
        self.assertEqual(body, pdf.read_bytes())
        self.assertEqual(self.tree_state(), before)
        pdf.unlink()
        self.write_json(self.paper_dir / "metadata.json", {**self.files["metadata.json"], "source_pdf": "stale.pdf"})
        before = self.tree_state()
        status, _, body = self.request("/api/papers/paper-a")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["metadata"]["source_pdf"], "")
        self.assertEqual(self.tree_state(), before)

    def test_library_index_keeps_cached_pdf_field_without_opening_papers(self) -> None:
        library = reader.read_library_index(self.workspace)
        library["papers"][0]["source_pdf"] = str(Path("papers") / "paper-a" / "original.pdf")
        self.write_json(self.workspace / "library.json", library)
        with mock.patch.object(reader, "normalized_metadata", side_effect=AssertionError("No paper reads")):
            status, _, body = self.request("/api/library")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["library"]["papers"][0]["source_pdf"], library["papers"][0]["source_pdf"])

    def test_library_routes_read_only_the_index_and_project_contexts(self) -> None:
        before = self.tree_state()
        with (
            mock.patch.object(reader, "load_library", side_effect=AssertionError("heavy CLI library")),
            mock.patch.object(reader, "normalized_metadata", side_effect=AssertionError("per-paper metadata")),
            mock.patch.object(reader, "ensure_workspace", side_effect=AssertionError("workspace initialization")),
            mock.patch.object(reader, "read_json", wraps=reader.read_json) as reads,
        ):
            for path in ("/api/library", "/api/papers"):
                status, _, body = self.request(path)
                self.assertEqual(status, 200, body)
        self.assertTrue(all(call.args[0].name in {"library.json", "project_contexts.json"} for call in reads.call_args_list))
        self.assertEqual(self.tree_state(), before)

    def test_library_index_reflects_same_size_same_mtime_external_edits_and_mutations(self) -> None:
        path = self.workspace / "library.json"
        stat = path.stat()
        self.request("/api/library")
        path.write_bytes(path.read_bytes().replace(b"Alpha", b"Bravo"))
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        status, _, body = self.request("/api/library")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["library"]["papers"][0]["title"], "Bravo")
        reader.upsert_paper_record(self.workspace, {"id": "paper-a", "title": "Mutation"})
        _, _, body = self.request("/api/papers")
        self.assertEqual(json.loads(body)["papers"][0]["title"], "Mutation")

    def test_cli_library_still_enriches_records(self) -> None:
        library = reader.load_library(self.workspace)
        self.assertEqual(library["papers"][0]["processing_mode"], "deep")
        self.assertEqual(library["papers"][0]["processing_status"], "ready")

    def test_unknown_paper_and_empty_workspace_gets_do_not_create_a_workspace(self) -> None:
        workspace = self.root / "does-not-exist"
        for path in ("/api/library", "/api/papers", "/api/project-contexts"):
            status, _, body = self.request(path, workspace=workspace)
            self.assertEqual(status, 200, body)
        for path in ("/api/papers/missing", "/api/papers/missing/notes-md", "/api/papers/missing/reading-data"):
            status, _, _ = self.request(path, workspace=workspace)
            self.assertEqual(status, 404)
        self.assertFalse(workspace.exists())

    def test_partial_thinking_save_preserves_untouched_data_and_record_extensions(self) -> None:
        original = self.files["thinking.json"]
        incoming = [
            {"id": "thinking-highlight", "note": self.note},
            copy.deepcopy(original["annotations"][1]),
        ]
        status, _, body = self.request("/api/papers/paper-a/thinking", method="POST", data={"annotations": incoming})
        self.assertEqual(status, 200, body)
        saved = reader.read_json(self.paper_dir / "thinking.json", {})
        for key in ("version", "explain", "blocks", "report_thoughts", "custom"):
            self.assertEqual(saved[key], original[key])
        first = saved["annotations"][0]
        for key in ("id", "block_id", "target", "quote", "range", "custom"):
            self.assertEqual(first[key], original["annotations"][0][key])
        self.assertEqual(first["note"], self.note)
        self.assertEqual(saved["annotations"][1]["id"], "orphan-thinking")
        self.export_schedule.assert_called_once_with(self.paper_dir)
        _, _, body = self.request("/api/papers/paper-a/notes-md")
        self.assertIn(self.note, body.decode("utf-8"))

    def test_thinking_cleaner_keeps_orphans_whitespace_ranges_and_extensions(self) -> None:
        original = self.files["thinking.json"]
        cleaned = reader.clean_thinking(copy.deepcopy(original))
        self.assertEqual(cleaned["annotations"][1]["id"], "orphan-thinking")
        self.assertEqual(cleaned["annotations"][0]["range"], original["annotations"][0]["range"])
        self.assertEqual(cleaned["report_thoughts"][0]["note"], original["report_thoughts"][0]["note"])
        self.assertEqual(cleaned["report_thoughts"][0]["custom"], original["report_thoughts"][0]["custom"])
        self.assertEqual(cleaned["blocks"][0]["custom"], original["blocks"][0]["custom"])
        self.assertEqual(cleaned["blocks"][0]["selection_refs"], original["blocks"][0]["selection_refs"])
        self.assertEqual(cleaned["blocks"][0]["source_refs"], original["blocks"][0]["source_refs"])
        self.assertEqual(cleaned["explain"]["custom"], original["explain"]["custom"])
        self.assertEqual(cleaned["custom"], original["custom"])

    def test_full_thinking_save_keeps_all_supplied_fields_and_untruncated_references(self) -> None:
        original = self.files["thinking.json"]
        status, _, body = self.request("/api/papers/paper-a/thinking", method="POST", data=original)
        self.assertEqual(status, 200, body)
        saved = json.loads(body)["thinking"]
        for section in ("annotations", "blocks", "report_thoughts"):
            self.assertEqual(len(saved[section]), len(original[section]))
            for source_record, saved_record in zip(original[section], saved[section]):
                for key, value in source_record.items():
                    self.assertEqual(saved_record[key], value)
        for key, value in original["explain"].items():
            self.assertEqual(saved["explain"][key], value)

    def test_invalid_thinking_update_does_not_replace_existing_data(self) -> None:
        before = self.tree_state()
        for data in ([], {"annotations": {}}, {"blocks": None}, {"explain": "bad"}, {"report_thoughts": "bad"}):
            status, _, _ = self.request("/api/papers/paper-a/thinking", method="POST", data=data)
            self.assertEqual(status, 400)
        self.assertEqual(self.tree_state(), before)
        self.export_schedule.assert_not_called()

    def test_report_thought_update_keeps_original_wording_and_untouched_sections(self) -> None:
        status, _, body = self.request(
            "/api/papers/paper-a/thinking",
            method="POST",
            data={"report_thoughts": [{"id": "thought-1", "note": self.note}]},
        )
        self.assertEqual(status, 200, body)
        saved = json.loads(body)["thinking"]
        self.assertEqual(saved["report_thoughts"][0]["note"], self.note)
        self.assertEqual(saved["report_thoughts"][0]["custom"], {"keep": True})
        for key in ("annotations", "blocks", "explain"):
            self.assertEqual(saved[key], self.files["thinking.json"][key])
        self.export_schedule.assert_called_once_with(self.paper_dir)

    def test_deleting_a_block_schedules_export_but_preserves_unrelated_orphan_notes(self) -> None:
        status, _, body = self.request("/api/papers/paper-a/thinking/blocks/ai-1", method="DELETE")
        self.assertEqual(status, 200, body)
        saved = json.loads(body)["thinking"]
        self.assertEqual(saved["blocks"], [])
        self.assertEqual(saved["annotations"][1]["id"], "orphan-thinking")
        self.assertEqual(saved["report_thoughts"][0]["note"], "  Original thought?\n")
        self.export_schedule.assert_called_once_with(self.paper_dir)

    def test_paper_annotation_save_preserves_envelope_targeting_and_extensions(self) -> None:
        original = self.files["annotations.json"]
        incoming = [
            {"id": "highlight-only", "note": self.note},
            copy.deepcopy(original["annotations"][1]),
        ]
        status, _, body = self.request("/api/papers/paper-a/annotations", method="POST", data={"annotations": incoming})
        self.assertEqual(status, 200, body)
        saved = reader.read_json(self.paper_dir / "annotations.json", {})
        self.assertEqual(saved["custom"], original["custom"])
        self.assertEqual(saved["version"], original["version"])
        for key, value in original["annotations"][0].items():
            if key != "note":
                self.assertEqual(saved["annotations"][0][key], value)
        self.assertEqual(saved["annotations"][0]["note"], self.note)
        self.export_schedule.assert_called_once_with(self.paper_dir)

    def test_question_tags_and_original_note_whitespace_survive_paper_and_thinking_saves(self) -> None:
        tags = ["question", "  Custom tag  ", ""]
        for endpoint, annotation_id in (("annotations", "highlight-only"), ("thinking", "thinking-highlight")):
            with self.subTest(endpoint=endpoint):
                status, _, body = self.request(
                    f"/api/papers/paper-a/{endpoint}",
                    method="POST",
                    data={"annotations": [{"id": annotation_id, "note": self.note, "tags": tags}]},
                )
                self.assertEqual(status, 200, body)
                filename = "annotations.json" if endpoint == "annotations" else "thinking.json"
                saved = reader.read_json(self.paper_dir / filename, {})["annotations"][0]
                self.assertEqual(saved["note"], self.note)
                self.assertEqual(saved["tags"], tags)
                if endpoint == "thinking":
                    self.assertEqual(reader.clean_thinking({"annotations": [saved]})["annotations"][0]["tags"], tags)
                _, _, body = self.request("/api/papers/paper-a/notes-md")
                text = body.decode("utf-8")
                self.assertIn(self.note, text)
                self.assertIn('"question"', text)
                self.assertIn('"  Custom tag  "', text)

    def test_invalid_annotation_updates_fail_instead_of_silently_dropping_records(self) -> None:
        before = self.tree_state()
        for data in ([], {"annotations": {}}, {"annotations": [None]}, {"annotations": [{"id": "unknown"}]}):
            status, _, _ = self.request("/api/papers/paper-a/annotations", method="POST", data=data)
            self.assertEqual(status, 400)
        self.assertEqual(self.tree_state(), before)
        self.export_schedule.assert_not_called()

    def test_new_thinking_annotations_get_unique_ids_and_explicit_deletions_still_work(self) -> None:
        incoming = [{"block_id": "ai-1", "quote": "one"}, {"block_id": "ai-1", "quote": "two"}]
        with mock.patch.object(reader, "now_iso", return_value="fixed-time"):
            status, _, body = self.request("/api/papers/paper-a/thinking", method="POST", data={"annotations": incoming})
        self.assertEqual(status, 200, body)
        annotations = json.loads(body)["thinking"]["annotations"]
        self.assertEqual(len({item["id"] for item in annotations}), 2)
        status, _, _ = self.request("/api/papers/paper-a/thinking", method="POST", data={"annotations": []})
        self.assertEqual(status, 200)
        self.assertEqual(reader.read_json(self.paper_dir / "thinking.json", {})["annotations"], [])

    def test_static_validators_revalidate_content_while_api_always_returns_fresh_data(self) -> None:
        web = self.root / "web"
        web.mkdir()
        path = web / "app.js"
        path.write_bytes(b"first")
        with mock.patch.object(reader, "WEB_DIR", web):
            status, headers, body = self.request("/app.js")
            self.assertEqual((status, body), (200, b"first"))
            self.assertEqual(headers["Cache-Control"], "no-cache")
            etag = headers["ETag"]
            status, headers, body = self.request("/app.js", headers={"If-None-Match": "W/" + etag})
            self.assertEqual((status, body), (304, b""))
            self.assertEqual(headers["ETag"], etag)
            stat = path.stat()
            path.write_bytes(b"other")
            os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            status, headers, body = self.request("/app.js", headers={"If-None-Match": etag})
            self.assertEqual((status, body), (200, b"other"))
            self.assertNotEqual(headers["ETag"], etag)
        status, headers, _ = self.request("/api/library", headers={"If-None-Match": "*"})
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")


if __name__ == "__main__":
    unittest.main()
