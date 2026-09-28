from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time
import unittest
from unittest import mock
import uuid
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feishu_metadata as metadata
import feishu_publish as publication
from reading_archive import archive_fingerprint


BASE, TABLE, RECORD = "SyntheticBase", "tblSynthetic", "recSynthetic"
ARCHIVE, BACKUP = "fldArchive", "fldBackup"
SETTINGS = {"base_token": BASE, "table_id": TABLE, "executable": "fake-lark-cli.exe",
            "archive_field": "阅读档案", "backup_field": "阅读数据备份", "parent_token": ""}
TEXT_FIELDS = {"my-notes": "fldTextNotes", "ai-discussions": "fldTextAI",
               "accepted-definitions": "fldTextDefinitions", "other-material": "fldTextOther"}
TABLE_SETTINGS = {**SETTINGS, "mode": "table", "text_fields": dict(publication.TABLE_COLUMN_NAMES)}


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path, default: object, *, strict: bool = True) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def success(data: dict, **extra: object) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], 0, json.dumps({"ok": True, "data": data, **extra}), "")


def failure(category: str, *, data: dict | None = None, code: int = 1) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], code, "", json.dumps({
        "ok": False, "error": {"type": category, "message": "SECRET_VALUE", "hint": "SECRET_VALUE"},
        "data": data or {},
    }))


class FakeCLI:
    def __init__(self) -> None:
        self.fields = [
            {"id": ARCHIVE, "name": "阅读档案", "type": "text", "style": {"type": "url"}},
            {"id": BACKUP, "name": "阅读数据备份", "type": "attachment"},
            {"id": "fldManual", "name": "Manual column", "type": "text"},
        ]
        self.record = {ARCHIVE: None, BACKUP: [], "fldManual": "Preserve this manual value.",
                       "read_status": "已读", "raw text": "Never replace the existing Paper Brief."}
        self.records = {RECORD: self.record}
        self.documents: dict[str, dict] = {}
        self.blobs: dict[str, bytes] = {}
        self.calls: list[tuple] = []
        self.writes: list[str] = []
        self.before: dict[str, object] = {}
        self.after: dict[str, object] = {}
        self.decorate = True
        self.forbid_docs = False
        self.empty_as_null = False
        self.table_fields = {}

    def enable_table_fields(self) -> None:
        self.table_fields = dict(TEXT_FIELDS)
        self.fields.extend({"id": field_id, "name": publication.TABLE_COLUMN_NAMES[section_id],
                            "type": "text", "style": {"type": "plain"}}
                           for section_id, field_id in self.table_fields.items())
        for record in self.records.values():
            record.update({field_id: None for field_id in self.table_fields.values()})

    @staticmethod
    def flag(argv: list[str], flag: str) -> str:
        return argv[argv.index(flag) + 1]

    def __call__(self, argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        if argv[0] != "fake-lark-cli.exe" or argv[1] not in {"base", "docs"}:
            raise AssertionError("Only the fake Feishu CLI is allowed; no models or other subprocesses.")
        if argv[-2:] != ["--as", "user"] or argv.count("--as") != 1 or "--yes" in argv or kwargs.get("shell") is not False:
            raise AssertionError("Identity/confirmation/subprocess safety contract was violated.")
        command = argv[2]
        self.calls.append((list(argv), dict(kwargs)))
        if self.forbid_docs and argv[1] == "docs":
            raise AssertionError("Table publication must never call a docs endpoint.")
        if command in {"+create", "+update", "+record-upload-attachment", "+record-upsert"}:
            self.writes.append(command)
        hook = self.before.pop(command, None)
        if hook:
            result = hook(argv, kwargs)
            if result is not None:
                return result
        record_id, record = RECORD, self.record
        if argv[1] == "base":
            if self.flag(argv, "--base-token") != BASE or self.flag(argv, "--table-id") != TABLE:
                raise AssertionError("A client-supplied destination escaped binding validation.")
            if "--record-id" in argv:
                record_id = self.flag(argv, "--record-id")
            if record_id not in self.records:
                raise AssertionError("Wrong record.")
            record = self.records[record_id]
        if command == "+field-list":
            data = {"fields": copy.deepcopy(self.fields), "has_more": False}
        elif command == "+record-get":
            fields = [argv[index + 1] for index, value in enumerate(argv) if value == "--field-id"]
            if set(fields) not in ({ARCHIVE, BACKUP}, {*self.table_fields.values(), BACKUP}):
                raise AssertionError("Read only the exact dedicated field IDs.")
            data = {"field_id_list": fields, "record_id_list": [record_id],
                    "data": [[copy.deepcopy(record[field]) for field in fields]]}
        elif command in {"+create", "+update"}:
            if self.flag(argv, "--api-version") != "v2" or self.flag(argv, "--content") != "-":
                raise AssertionError("Document writes require v2 and stdin.")
            content = kwargs["input"]
            if not isinstance(content, str):
                raise AssertionError("No document content on stdin.")
            if command == "+create":
                document_id = f"docCreated{len(self.documents) + 1}"
                self.documents[document_id] = {"document_id": document_id, "revision_id": 1, "content": content}
                data = {"document": {"document_id": document_id, "revision_id": 1,
                                     "url": f"https://example.feishu.cn/docx/{document_id}"}}
            else:
                document_id = self.flag(argv, "--doc")
                document = self.documents[document_id]
                if self.flag(argv, "--revision-id") != str(document["revision_id"]):
                    return failure("api")
                if self.flag(argv, "--command") == "overwrite":
                    document["content"] = content
                elif self.flag(argv, "--command") == "append":
                    document["content"] += "\n" + content
                else:
                    raise AssertionError("Unexpected document update.")
                document["revision_id"] += 1
                data = {"document": {"revision_id": document["revision_id"]}, "result": "success", "warnings": []}
        elif command == "+fetch":
            if self.flag(argv, "--detail") != "full" or self.flag(argv, "--api-version") != "v2":
                raise AssertionError("Full v2 revision-aware fetch is required.")
            document = copy.deepcopy(self.documents[self.flag(argv, "--doc")])
            if self.decorate:
                root = ET.fromstring("<root>" + document["content"] + "</root>")
                for index, element in enumerate(root.iter()):
                    if element is not root:
                        element.set("id", f"blk{index}")
                        element.set("align", "left")
                document["content"] = "\n".join(ET.tostring(element, encoding="unicode") for element in root)
            data = {"document": document}
        elif command == "+record-upload-attachment":
            if self.flag(argv, "--field-id") != BACKUP:
                raise AssertionError("Do not modify original PDF fields.")
            path = self.local_file(argv, kwargs, "--file")
            token = f"fileBackup{len(self.blobs) + 1}"
            self.blobs[token] = path.read_bytes()
            attachment = {"file_token": token, "name": path.name, "size": len(self.blobs[token])}
            record[BACKUP].append(attachment)
            data = {"files": [copy.deepcopy(attachment)]}
        elif command == "+record-download-attachment":
            path = self.local_file(argv, kwargs, "--output")
            if path.exists():
                raise AssertionError("Do not overwrite verification output.")
            path.write_bytes(self.blobs[self.flag(argv, "--file-token")])
            data = {"files": [{"path": path.name}]}
        elif command == "+record-upsert":
            value = self.flag(argv, "--json")
            if value.startswith("@"):
                path = self.local_file(argv, kwargs, "--json")
                payload = path.read_bytes()
                patch = json.loads(payload)
                if set(patch) != set(self.table_fields.values()) or payload != publication._json(patch).encode("utf-8"):
                    raise AssertionError("Table PATCH must contain exactly four fields in a canonical controlled UTF-8 file.")
                if len(" ".join(argv)) >= 2_000:
                    raise AssertionError("Table JSON must not be passed in Windows argv.")
            else:
                patch = json.loads(value)
                if set(patch) != {ARCHIVE}:
                    raise AssertionError("Plain-text publication must use a controlled @file, never a long argv payload.")
            record.update({key: None if self.empty_as_null and value == "" else value for key, value in patch.items()})
            data = {"updated": True, "record": {"id": record_id}}
        else:
            raise AssertionError("Unexpected CLI command: " + command)
        hook = self.after.pop(command, None)
        if hook:
            return hook(argv, kwargs, data)
        return success(data)

    @staticmethod
    def local_file(argv: list[str], kwargs: dict, flag: str) -> Path:
        name = FakeCLI.flag(argv, flag)
        if flag == "--json":
            if not name.startswith("@") or name == "@-":
                raise AssertionError("Use a controlled JSON file, not unsupported stdin syntax.")
            name = name[1:]
        if Path(name).is_absolute() or Path(name).name != name or ".." in Path(name).parts:
            raise AssertionError("All CLI file paths must be cwd-relative and reserved locally.")
        cwd = Path(kwargs["cwd"])
        if cwd.name != publication.STATE_DIRECTORY:
            raise AssertionError("The CLI must only access the publication sidecar.")
        return cwd / name


class PublicationFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = Path.cwd() / (".feishu-publish-tests-" + uuid.uuid4().hex)
        self.paper = self.workspace / "papers" / "synthetic-paper"
        self.papers = [self.paper]
        self.settings = copy.deepcopy(SETTINGS)
        self.paper.mkdir(parents=True)
        self.addCleanup(lambda: shutil.rmtree(self.workspace))
        self.original = {
            "metadata.json": {
                "id": "synthetic-paper", "title": "Synthetic <Study> & 原文", "read_status": "read",
                "feishu": {"base_token": BASE, "table_id": TABLE, "record_id": RECORD, "synced_at": "old"},
            },
            "segments.json": [{"id": "p-1", "markdown": " Exact original text.\n", "translation": " 精确中文。 \n"}],
            "annotations.json": {"annotations": [{"id": "a-1", "segment_id": "p-1", "quote": "Exact original",
                                                  "note": "  My verbatim note.\n", "origin": "user", "extension": {"keep": True}}]},
            "thinking.json": {"explain": {"content": "Original AI Brief."},
                              "report_thoughts": [{"id": "t-1", "text": "Question?"}],
                              "blocks": [{"id": "b-1", "type": "explain", "content": "Saved AI output.", "model": "do-not-run"}]},
            "reading_teacher.json": {"suggestions": [{"text": "Stored teacher content", "source": {"id": "p-1"}}]},
            "takeaway_doc.json": {"blocks": []},
            "reading_progress.json": {"anchor": "p-1", "updated_at": "old"},
        }
        for name, data in self.original.items():
            write_json(self.paper / name, data)
        self.fake = FakeCLI()
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(metadata, "cli_command", return_value="fake-lark-cli.exe").start()
        mock.patch.object(metadata.subprocess, "run", side_effect=self.fake).start()
        mock.patch.object(socket, "create_connection", side_effect=AssertionError("No network in unit tests")).start()
        self.service = self.make_service()
        self.addCleanup(self.finish_workers)

    def finish_workers(self) -> None:
        for paper in self.papers:
            thread = publication._runtime(paper).thread
            if thread:
                thread.join(10)
                self.assertFalse(thread.is_alive(), "Do not restore the real CLI while a fake publication is running.")
            with publication._RUNTIME_LOCK:
                publication._RUNTIMES.pop(publication.os.path.normcase(str(paper)), None)

    def make_service(self, **overrides: object) -> publication.PublicationService:
        callbacks = {"snapshot_reader": self.snapshot, "json_reader": read_json,
                     "json_writer": write_json, "text_writer": write_text}
        callbacks.update(overrides)
        return publication.PublicationService(**callbacks)

    def snapshot(self, paper: Path) -> dict:
        return {"format": "paper-reader-reading-data", "version": 1, "paper_id": paper.name,
                "sources": {"segments.json": "Original/translation text.", "thinking.json": "Stored mixed-origin outputs."},
                "files": {name: read_json(paper / name, None) for name in self.original if (paper / name).exists()}}

    def preview(self) -> dict:
        return self.service.preview(self.paper, self.settings)

    def start(self, preview: dict | None = None) -> dict:
        result = self.service.start(self.paper, self.settings, (preview or self.preview())["preview_id"], True)
        thread = publication._runtime(self.paper).thread
        if thread:
            thread.join(10)
            self.assertFalse(thread.is_alive(), "Publication worker did not finish.")
        return self.service.status(self.paper, self.settings)

    def journal(self) -> dict:
        name = publication.TABLE_JOURNAL_FILENAME if self.settings.get("mode") == "table" else publication.JOURNAL_FILENAME
        return read_json(self.paper / publication.STATE_DIRECTORY / name, {})

    def source_bytes(self) -> dict:
        return {name: (self.paper / name).read_bytes() for name in self.original if (self.paper / name).exists()}

    def edit_note(self, text: str = "A meaningful new note.") -> None:
        data = read_json(self.paper / "annotations.json", {})
        data["annotations"][0]["note"] = text
        write_json(self.paper / "annotations.json", data)

    def assert_synced(self, status: dict) -> None:
        self.assertEqual(status["status"], "synced", status)
        self.assertEqual(status["error"], "")
        self.assertTrue(status["published_at"])


class PublicationTests(PublicationFixture):
    def test_preview_only_reads_cloud_and_saves_one_immutable_preview(self) -> None:
        before = self.source_bytes()
        preview = self.preview()
        self.assertEqual(self.fake.writes, [])
        self.assertEqual(before, self.source_bytes())
        files = list((self.paper / publication.STATE_DIRECTORY).iterdir())
        self.assertEqual([file.name for file in files], [f"preview-{preview['preview_id']}.json"])
        self.assertEqual(preview["destination"]["archive_field"], {"id": ARCHIVE, "name": "阅读档案"})
        self.assertEqual(preview["destination"]["backup_field"], {"id": BACKUP, "name": "阅读数据备份"})
        self.assertEqual(preview["destination"]["record_id"], RECORD)
        self.assertTrue(preview["changed"])
        self.assertGreater(preview["snapshot_bytes"], 0)
        self.assertTrue(all(set(entry) == {"id", "label", "quote", "text", "source"}
                            for section in preview["sections"] for entry in section["entries"]))

    def test_complete_publication_preserves_raw_backup_and_all_other_fields(self) -> None:
        before, raw = self.source_bytes(), self.snapshot(self.paper)
        other_fields = {key: value for key, value in self.fake.record.items() if key not in {ARCHIVE, BACKUP}}
        status = self.start()
        self.assert_synced(status)
        self.assertEqual(before, self.source_bytes())
        self.assertEqual(other_fields, {key: value for key, value in self.fake.record.items() if key not in {ARCHIVE, BACKUP}})
        self.assertEqual(len(self.fake.documents), 1)
        self.assertEqual(len(self.fake.record[BACKUP]), 1)
        attachment = self.fake.record[BACKUP][0]
        backup = json.loads(self.fake.blobs[attachment["file_token"]])
        self.assertEqual(backup["reading_data"], raw)
        self.assertEqual(backup["manifest"]["raw_sha256"], publication._hash(raw))
        self.assertEqual(backup["manifest"]["fingerprint"], archive_fingerprint(raw))
        self.assertEqual(attachment["name"], f"reading-data-{archive_fingerprint(raw)}.json")
        self.assertEqual(self.fake.record[ARCHIVE], status["document_url"])
        self.assertIn("paper-reader:owner:", next(iter(self.fake.documents.values()))["content"])
        self.assertIn("paper-reader:complete:" + status["fingerprint"], next(iter(self.fake.documents.values()))["content"])

    def test_same_job_duplicate_and_unchanged_new_preview_do_not_repeat_writes(self) -> None:
        first_preview = self.preview()
        first = self.start(first_preview)
        self.assert_synced(first)
        writes = list(self.fake.writes)
        same = self.service.start(self.paper, SETTINGS, first_preview["preview_id"], True)
        self.assertEqual(same["job_id"], first["job_id"])
        self.assertEqual(self.fake.writes, writes)
        preview = self.preview()
        self.assertFalse(preview["changed"])
        second = self.start(preview)
        self.assert_synced(second)
        self.assertEqual(self.fake.writes, writes)
        self.assertEqual(first["published_at"], second["published_at"])

    def test_passive_progress_does_not_replace_exact_existing_backup(self) -> None:
        self.assert_synced(self.start())
        old_bytes = dict(self.fake.blobs)
        write_json(self.paper / "reading_progress.json", {"anchor": "p-99", "updated_at": "new"})
        local = read_json(self.paper / "metadata.json", {})
        local["feishu"]["synced_at"] = "new"
        local["read_status"] = "unread"
        write_json(self.paper / "metadata.json", local)
        preview = self.preview()
        self.assertFalse(preview["changed"])
        self.assert_synced(self.start(preview))
        self.assertEqual(self.fake.blobs, old_bytes)
        self.assertEqual(len(self.fake.documents), 1)

    def test_second_meaningful_revision_updates_the_same_document_and_appends_backup(self) -> None:
        first = self.start()
        self.assert_synced(first)
        original_backup = copy.deepcopy(self.fake.record[BACKUP])
        self.edit_note()
        preview = self.preview()
        self.assertTrue(preview["changed"])
        second = self.start(preview)
        self.assert_synced(second)
        self.assertNotEqual(first["fingerprint"], second["fingerprint"])
        self.assertEqual(first["document_url"], second["document_url"])
        self.assertEqual(len(self.fake.documents), 1)
        self.assertEqual(self.fake.record[BACKUP][:1], original_backup)
        self.assertEqual(len(self.fake.record[BACKUP]), 2)
        self.assertIn("A meaningful new note.", next(iter(self.fake.documents.values()))["content"])

    def test_returning_to_an_old_fingerprint_reuses_its_immutable_backup(self) -> None:
        first = self.start()
        self.assert_synced(first)
        original_blobs = dict(self.fake.blobs)
        self.edit_note()
        self.assert_synced(self.start())
        write_json(self.paper / "annotations.json", self.original["annotations.json"])
        reverted = self.start()
        self.assert_synced(reverted)
        self.assertEqual(reverted["fingerprint"], first["fingerprint"])
        self.assertEqual(len(self.fake.documents), 1)
        self.assertEqual(len(self.fake.record[BACKUP]), 2)
        self.assertTrue(all(self.fake.blobs[token] == content for token, content in original_blobs.items()))

    def test_stale_local_snapshot_rejected_before_remote_writes(self) -> None:
        preview = self.preview()
        self.edit_note()
        with self.assertRaises(publication.PublicationConflict):
            self.service.start(self.paper, SETTINGS, preview["preview_id"], True)
        self.assertEqual(self.fake.writes, [])

    def test_meaningful_edit_during_async_preflight_fails_before_any_cloud_write(self) -> None:
        preview = self.preview()

        def edit_during_preflight(argv, kwargs, data):
            self.edit_note("A note saved while the cloud preflight was reading.")
            return success(data)

        self.fake.after["+field-list"] = edit_during_preflight
        status = self.start(preview)
        self.assertEqual(status["status"], "conflict", status)
        self.assertEqual(status["error_type"], "PublicationConflict")
        self.assertEqual(status["phase"], "preflight")
        self.assertIn("preflight", status["error"])
        self.assertEqual(self.fake.writes, [])
        self.assertFalse(list((self.paper / publication.STATE_DIRECTORY).glob("reading-data-*.json")))

    def test_passive_edits_during_preflight_do_not_invalidate_meaningful_fingerprint(self) -> None:
        preview = self.preview()

        def progress_during_preflight(argv, kwargs, data):
            write_json(self.paper / "reading_progress.json", {"anchor": "p-new", "updated_at": "new"})
            local = read_json(self.paper / "metadata.json", {})
            local["feishu"]["synced_at"] = "new"
            write_json(self.paper / "metadata.json", local)
            return success(data)

        self.fake.after["+field-list"] = progress_during_preflight
        self.assert_synced(self.start(preview))
        backup = json.loads(next(iter(self.fake.blobs.values())))
        self.assertEqual(backup["reading_data"]["files"]["reading_progress.json"], self.original["reading_progress.json"])

    def test_changed_binding_and_settings_rejected_before_remote_writes(self) -> None:
        preview = self.preview()
        for key, value in (("parent_token", "otherFolder"), ("table_id", "tblOther"),
                           ("archive_field", "Other field"), ("executable", "other.exe")):
            with self.subTest(key=key), self.assertRaises(publication.PublicationConflict):
                self.service.start(self.paper, {**SETTINGS, key: value}, preview["preview_id"], True)
        raw = read_json(self.paper / "metadata.json", {})
        raw["feishu"]["record_id"] = "recDifferent"
        write_json(self.paper / "metadata.json", raw)
        with self.assertRaises(publication.PublicationConflict):
            self.service.start(self.paper, SETTINGS, preview["preview_id"], True)
        self.assertEqual(self.fake.writes, [])

    def test_edited_preview_is_rejected_even_with_unchanged_local_snapshot(self) -> None:
        preview = self.preview()
        path = self.paper / publication.STATE_DIRECTORY / f"preview-{preview['preview_id']}.json"
        saved = read_json(path, {})
        saved["public"]["destination"]["record_id"] = "recAttacker"
        saved["chunks"] = ["<title>Unapproved</title><p>content</p>"]
        write_json(path, saved)
        with self.assertRaises(publication.PublicationConflict):
            self.service.start(self.paper, SETTINGS, preview["preview_id"], True)
        self.assertEqual(self.fake.writes, [])

    def test_invalid_confirmation_nonce_and_unsafe_filenames_are_rejected(self) -> None:
        preview = self.preview()
        for confirmed in (False, None, 1, "true"):
            with self.subTest(confirmed=confirmed), self.assertRaises(ValueError):
                self.service.start(self.paper, SETTINGS, preview["preview_id"], confirmed)
        for nonce in ("", "..\\metadata", "c:\\private", "../outside", "a" * 31, "a" * 33, None):
            with self.subTest(nonce=nonce), self.assertRaises(publication.PublicationConflict):
                self.service.start(self.paper, SETTINGS, nonce, True)
        self.assertEqual(self.fake.writes, [])

    def test_invalid_binding_fails_without_any_cli_call(self) -> None:
        for link in (None, {}, {"base_token": BASE, "table_id": "tblOther", "record_id": RECORD},
                     {"base_token": BASE, "table_id": TABLE, "record_id": "rec --as bot"}):
            data = copy.deepcopy(self.original["metadata.json"])
            data["feishu"] = link
            write_json(self.paper / "metadata.json", data)
            with self.subTest(link=link), self.assertRaises(ValueError):
                self.preview()
        self.assertEqual(self.fake.calls, [])

    def test_invalid_or_replaced_schema_is_never_written(self) -> None:
        original = copy.deepcopy(self.fake.fields)
        variants = [
            [{"id": ARCHIVE, "name": "阅读档案", "type": "text", "style": {"type": "plain"}}, original[1]],
            [original[0], {"id": BACKUP, "name": "阅读数据备份", "type": "text"}],
            [original[0], original[0], original[1]],
            [original[1]],
            [{**original[0], "id": "fldHblyRK0"}, original[1]],
            [{**original[0], "field_id": "fldDifferent"}, original[1]],
        ]
        for fields in variants:
            with self.subTest(fields=fields):
                self.fake.fields = fields
                with self.assertRaises(ValueError):
                    self.preview()
        self.assertEqual(self.fake.writes, [])
        self.fake.fields = original
        self.assert_synced(self.start())
        self.fake.fields[0]["id"] = "fldReplacement"
        with self.assertRaises(publication.PublicationConflict):
            self.preview()

    def test_configurable_names_resolve_actual_field_ids(self) -> None:
        self.fake.fields[0]["name"] = "Dedicated Archive"
        self.fake.fields[1]["name"] = "Dedicated Backups"
        settings = {**SETTINGS, "archive_field": "Dedicated Archive", "backup_field": "Dedicated Backups"}
        preview = self.service.preview(self.paper, settings)
        self.assertEqual(preview["destination"]["archive_field"], {"id": ARCHIVE, "name": "Dedicated Archive"})
        self.assertEqual(self.fake.writes, [])

    def test_unrelated_existing_archive_link_is_never_adopted(self) -> None:
        self.fake.record[ARCHIVE] = "https://example.feishu.cn/docx/docUnrelated"
        with self.assertRaises(publication.PublicationConflict):
            self.preview()
        self.assertEqual(self.fake.writes, [])

    def test_unrecognized_or_ambiguous_archive_cells_fail_closed(self) -> None:
        for cell in ({}, {"unknown": "https://example.feishu.cn/docx/docUnrelated"},
                     {"url": "https://example.feishu.cn/docx/docOne", "link": "https://example.feishu.cn/docx/docTwo"}):
            self.fake.record[ARCHIVE] = cell
            with self.subTest(cell=cell), self.assertRaises(publication.PublicationConflict):
                self.preview()
        self.assertEqual(self.fake.writes, [])

    def test_cloud_link_changed_after_preview_fails_before_writes(self) -> None:
        preview = self.preview()
        self.fake.record[ARCHIVE] = "https://example.feishu.cn/docx/docUnrelated"
        status = self.start(preview)
        self.assertEqual(status["status"], "conflict", status)
        self.assertEqual(self.fake.writes, [])

    def test_cloud_revision_or_ownership_changes_are_conflicts(self) -> None:
        self.assert_synced(self.start())
        self.edit_note()
        preview = self.preview()
        writes = list(self.fake.writes)
        document = next(iter(self.fake.documents.values()))
        document["revision_id"] += 1
        document["content"] += "<p>User cloud edit.</p>"
        status = self.start(preview)
        self.assertEqual(status["status"], "conflict", status)
        self.assertEqual(self.fake.writes, writes)
        with self.assertRaises(publication.PublicationConflict):
            self.preview()
        document["content"] = "<title>Foreign</title><p>No ownership.</p>"
        with self.assertRaises(publication.PublicationConflict):
            self.preview()

    def test_cleared_published_archive_link_is_a_conflict(self) -> None:
        self.assert_synced(self.start())
        self.fake.record[ARCHIVE] = None
        with self.assertRaises(publication.PublicationConflict):
            self.preview()

    def test_local_edits_during_upload_are_pending_not_falsely_synced(self) -> None:
        preview = self.preview()
        def edit(argv, kwargs, data):
            self.edit_note("Saved while cloud upload was in flight.")
            return success(data)
        self.fake.after["+record-upload-attachment"] = edit
        status = self.start(preview)
        self.assertEqual(status["status"], "pending", status)
        self.assertEqual(status["published_fingerprint"], preview["fingerprint"])
        self.assertNotEqual(archive_fingerprint(self.snapshot(self.paper)), preview["fingerprint"])
        backup = json.loads(next(iter(self.fake.blobs.values())))
        self.assertEqual(backup["reading_data"]["files"]["annotations.json"], self.original["annotations.json"])
        self.assertEqual(read_json(self.paper / "annotations.json", {})["annotations"][0]["note"],
                         "Saved while cloud upload was in flight.")

    def test_async_serialization_and_status_are_local_and_nonblocking(self) -> None:
        first, other = self.preview(), self.preview()
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        def block(argv, kwargs):
            entered.set()
            if not release.wait(5):
                raise AssertionError("Test did not release fake cloud write.")
        self.fake.before["+create"] = block
        started = self.service.start(self.paper, SETTINGS, first["preview_id"], True)
        self.assertEqual(started["status"], "publishing")
        self.assertTrue(entered.wait(3))
        calls = len(self.fake.calls)
        then = time.monotonic()
        duplicate = self.service.start(self.paper, SETTINGS, first["preview_id"], True)
        self.assertEqual(duplicate["job_id"], started["job_id"])
        self.assertEqual(self.make_service().status(self.paper, SETTINGS)["status"], "publishing")
        self.assertLess(time.monotonic() - then, 1)
        self.assertEqual(len(self.fake.calls), calls)
        with self.assertRaises(publication.PublicationConflict):
            self.make_service().start(self.paper, SETTINGS, other["preview_id"], True)
        release.set()
        publication._runtime(self.paper).thread.join(10)
        self.assert_synced(self.service.status(self.paper, SETTINGS))
        self.assertEqual(len(self.fake.documents), 1)

    def test_two_paper_jobs_serialize_base_uploads_and_upserts_across_services(self) -> None:
        second_paper = self.paper.with_name("second-paper")
        second_paper.mkdir()
        self.papers.append(second_paper)
        for name, data in self.original.items():
            data = copy.deepcopy(data)
            if name == "metadata.json":
                data["id"] = second_paper.name
                data["feishu"]["record_id"] = "recSecond"
            write_json(second_paper / name, data)
        self.fake.records["recSecond"] = copy.deepcopy(self.fake.record)
        entered, release, queued, second_write = (threading.Event() for _ in range(4))
        self.addCleanup(release.set)

        def watch_state(path, value):
            write_json(path, value)
            if (path.parent.parent == second_paper and path.name == publication.JOURNAL_FILENAME
                    and value.get("phase") == "uploading_backup"):
                queued.set()

        second_service = self.make_service(json_writer=watch_state)
        first_preview = self.preview()
        second_preview = second_service.preview(second_paper, SETTINGS)
        active, maximum = 0, 0
        guard = threading.Lock()

        def measured_cli(argv, **kwargs):
            nonlocal active, maximum
            write = argv[1] == "base" and argv[2] in {"+record-upload-attachment", "+record-upsert"}
            if write:
                with guard:
                    active += 1
                    maximum = max(maximum, active)
                if FakeCLI.flag(argv, "--record-id") == "recSecond":
                    second_write.set()
            try:
                return self.fake(argv, **kwargs)
            finally:
                if write:
                    with guard:
                        active -= 1

        def hold_first_upload(argv, kwargs):
            entered.set()
            if not release.wait(5):
                raise AssertionError("Test did not release the first table write.")

        self.fake.before["+record-upload-attachment"] = hold_first_upload
        with mock.patch.object(metadata.subprocess, "run", side_effect=measured_cli):
            try:
                self.service.start(self.paper, SETTINGS, first_preview["preview_id"], True)
                self.assertTrue(entered.wait(3))
                second_service.start(second_paper, SETTINGS, second_preview["preview_id"], True)
                self.assertTrue(queued.wait(3), "The second paper should finish independent Docx work while Base is busy.")
                self.assertFalse(second_write.wait(0.15), "A second Base write overlapped the held attachment upload.")
                second_state = read_json(second_paper / publication.STATE_DIRECTORY / publication.JOURNAL_FILENAME, {})
                self.assertEqual(second_state.get("pending_write"), {}, "A merely queued job must not claim an uncertain upload.")
                self.assertEqual(second_service.status(second_paper, SETTINGS)["status"], "publishing")
            finally:
                release.set()
                for paper in self.papers:
                    thread = publication._runtime(paper).thread
                    if thread:
                        thread.join(10)
                        self.assertFalse(thread.is_alive())
        self.assertEqual(maximum, 1)
        self.assertTrue(second_write.is_set())
        self.assert_synced(self.service.status(self.paper, SETTINGS))
        self.assert_synced(second_service.status(second_paper, SETTINGS))
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 2)
        self.assertEqual(self.fake.writes.count("+record-upsert"), 2)
        self.assertEqual(len(self.fake.documents), 2)
        self.assertNotEqual(self.fake.records[RECORD][ARCHIVE], self.fake.records["recSecond"][ARCHIVE])

    def test_uncertain_upload_is_content_verified_and_never_duplicated(self) -> None:
        def timeout(argv, kwargs, data):
            raise subprocess.TimeoutExpired(argv, 180, stderr="SECRET_VALUE")
        self.fake.after["+record-upload-attachment"] = timeout
        status = self.start()
        self.assert_synced(status)
        self.assertTrue(any("uncertain" in warning for warning in status["warnings"]))
        self.assertNotIn("SECRET_VALUE", json.dumps(status))
        self.assert_synced(self.start())
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)
        self.assertEqual(len(self.fake.record[BACKUP]), 1)

    def test_uncertain_missing_attachment_blocks_blind_retry_then_recovers_visible_file(self) -> None:
        def timeout(argv, kwargs):
            raise subprocess.TimeoutExpired(argv, 180)
        self.fake.before["+record-upload-attachment"] = timeout
        first = self.start()
        self.assertEqual(first["status"], "recovery_required", first)
        second = self.start()
        self.assertEqual(second["status"], "recovery_required", second)
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)
        path = next((self.paper / publication.STATE_DIRECTORY).glob("reading-data-*.json"))
        self.fake.blobs["fileLate"] = path.read_bytes()
        self.fake.record[BACKUP] = [{"file_token": "fileLate", "name": path.name, "size": path.stat().st_size}]
        self.assert_synced(self.start())
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)
        self.assertEqual(len(self.fake.documents), 1)

    def test_retry_after_download_failure_reuses_attachment_without_another_upload(self) -> None:
        self.fake.before["+record-download-attachment"] = lambda argv, kwargs: failure("network")
        first = self.start()
        self.assertEqual(first["status"], "failed", first)
        self.assertEqual(len(self.fake.record[BACKUP]), 1)
        self.assert_synced(self.start())
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)

    def test_existing_deterministic_filename_with_wrong_content_is_not_replaced(self) -> None:
        preview = self.preview()
        name = f"reading-data-{preview['fingerprint']}.json"
        self.fake.record[BACKUP] = [{"file_token": "fileForeign", "name": name, "size": 1}]
        self.fake.blobs["fileForeign"] = b"x"
        status = self.start(preview)
        self.assertEqual(status["status"], "conflict", status)
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 0)
        self.assertEqual(self.fake.record[BACKUP][0]["file_token"], "fileForeign")

    def test_replaced_attachment_token_requires_verifying_bytes_not_only_filename_size(self) -> None:
        self.assert_synced(self.start())
        attachment = self.fake.record[BACKUP][0]
        size = attachment["size"]
        attachment["file_token"] = "fileReplacement"
        self.fake.blobs["fileReplacement"] = b"x" * size
        status = self.start()
        self.assertEqual(status["status"], "conflict", status)
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)

    def test_explicit_partial_document_result_stays_failed_and_retry_reuses_document(self) -> None:
        def partial(argv, kwargs, data):
            data["result"] = "partial_success"
            data["warnings"] = ["SECRET_VALUE"]
            return success(data)
        self.fake.after["+update"] = partial
        first = self.start()
        self.assertEqual(first["status"], "failed", first)
        self.assertIn("partial_success", first["error"])
        self.assertNotIn("SECRET_VALUE", json.dumps(first))
        self.assertTrue(first["warnings"])
        self.assert_synced(self.start())
        self.assertEqual(len(self.fake.documents), 1)
        self.assertEqual(self.fake.writes.count("+create"), 1)

    def test_actual_partial_document_content_is_not_claimed_complete(self) -> None:
        def partial(argv, kwargs, data):
            document = next(iter(self.fake.documents.values()))
            root = ET.fromstring("<root>" + document["content"] + "</root>")
            document["content"] = "\n".join(ET.tostring(element, encoding="unicode") for element in list(root)[:3])
            data["result"] = "partial_success"
            return success(data)
        self.fake.after["+update"] = partial
        first = self.start()
        self.assertEqual(first["status"], "failed", first)
        self.assertIn("partial_success", first["error"])
        self.assertEqual(first["published_at"], "")
        self.assertEqual(self.fake.record[BACKUP], [])
        self.assert_synced(self.start())
        self.assertEqual(len(self.fake.documents), 1)

    def test_partial_success_in_failed_envelope_is_not_hidden_by_full_content_verification(self) -> None:
        self.fake.after["+update"] = lambda argv, kwargs, data: failure("api", data={**data, "result": "partial_success"})
        status = self.start()
        self.assertEqual(status["status"], "failed", status)
        self.assertIn("partial_success", status["error"])
        self.assertEqual(status["published_at"], "")
        self.assertEqual(self.fake.record[BACKUP], [])

    def test_uncertain_document_write_can_be_recovered_only_after_full_content_verification(self) -> None:
        def timeout(argv, kwargs, data):
            raise subprocess.TimeoutExpired(argv, 180, stderr="SECRET_VALUE")
        self.fake.after["+update"] = timeout
        status = self.start()
        self.assert_synced(status)
        self.assertTrue(any("uncertain" in warning for warning in status["warnings"]))
        self.assertEqual(self.fake.writes.count("+update"), 1)
        self.assertNotIn("SECRET_VALUE", json.dumps(status))

    def test_partial_upload_or_link_results_keep_receipts_but_do_not_claim_success(self) -> None:
        self.fake.after["+record-upload-attachment"] = lambda argv, kwargs, data: failure(
            "api", data={**data, "result": "partial_success"})
        status = self.start()
        self.assertEqual(status["status"], "failed", status)
        self.assertIn("partial_success", status["error"])
        self.assertEqual(len(self.fake.record[BACKUP]), 1)
        self.fake.after["+record-upsert"] = lambda argv, kwargs, data: failure(
            "api", data={**data, "result": "partial_success"})
        status = self.start()
        self.assertEqual(status["status"], "failed", status)
        self.assertIn("partial", status["error"])
        self.assertTrue(self.fake.record[ARCHIVE])
        self.assert_synced(self.start())
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)
        self.assertEqual(len(self.fake.documents), 1)

    def test_backup_edited_during_document_write_is_not_uploaded(self) -> None:
        def edit_backup(argv, kwargs, data):
            path = next((self.paper / publication.STATE_DIRECTORY).glob("reading-data-*.json"))
            path.write_text("Unapproved edited backup.", encoding="utf-8")
            return success(data)
        self.fake.after["+update"] = edit_backup
        status = self.start()
        self.assertEqual(status["status"], "recovery_required", status)
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 0)
        self.assertEqual(self.fake.record[BACKUP], [])

    def test_ambiguous_creation_never_creates_a_second_document(self) -> None:
        def lost_response(argv, kwargs, data):
            return subprocess.CompletedProcess([], 0, "SECRET_VALUE not JSON", "")
        self.fake.after["+create"] = lost_response
        first = self.start()
        self.assertEqual(first["status"], "recovery_required", first)
        self.assertNotIn("SECRET_VALUE", json.dumps(first))
        self.assertEqual(len(self.fake.documents), 1)
        with self.assertRaises(publication.PublicationRecoveryRequired):
            self.preview()
        self.assertEqual(len(self.fake.documents), 1)

    def test_created_identity_in_error_response_is_retained_for_explicit_recovery(self) -> None:
        self.fake.after["+create"] = lambda argv, kwargs, data: failure("api", data=data)
        first = self.start()
        self.assertEqual(first["status"], "recovery_required", first)
        self.assertTrue(self.journal()["document_id"])
        self.assert_synced(self.start())
        self.assertEqual(self.fake.writes.count("+create"), 1)

    def test_failed_journal_save_before_start_prevents_all_remote_writes(self) -> None:
        preview = self.preview()
        def fail(path, value):
            if path.name == publication.JOURNAL_FILENAME:
                raise OSError("SECRET_VALUE")
            write_json(path, value)
        self.service.json_writer = fail
        with self.assertRaises(publication.PublicationStorageError) as caught:
            self.service.start(self.paper, SETTINGS, preview["preview_id"], True)
        self.assertNotIn("SECRET_VALUE", str(caught.exception))
        self.assertEqual(self.fake.writes, [])

    def test_failed_save_after_creation_keeps_identity_and_stops_more_writes(self) -> None:
        def fail(path, value):
            if path.name == publication.JOURNAL_FILENAME and value.get("document_id"):
                raise OSError("SECRET_VALUE")
            write_json(path, value)
        self.service.json_writer = fail
        first = self.start()
        self.assertEqual(first["status"], "recovery_required", first)
        self.assertTrue(first["storage_error"])
        self.assertTrue(first["document_url"])
        self.assertEqual(self.fake.writes, ["+create"])
        self.assertEqual(self.journal()["pending_write"]["kind"], "create")
        self.assertNotIn("SECRET_VALUE", json.dumps(first))
        with self.assertRaises(publication.PublicationRecoveryRequired):
            self.preview()

    def test_transient_receipt_save_error_is_persisted_and_same_document_can_recover(self) -> None:
        failed = False
        def fail_once(path, value):
            nonlocal failed
            if path.name == publication.JOURNAL_FILENAME and value.get("document_id") and not failed:
                failed = True
                raise OSError("SECRET_VALUE")
            write_json(path, value)
        self.service.json_writer = fail_once
        first = self.start()
        self.assertEqual(first["status"], "recovery_required", first)
        self.assertTrue(self.journal()["document_id"])
        self.assert_synced(self.start())
        self.assertEqual(self.fake.writes.count("+create"), 1)

    def test_backup_bytes_are_stable_with_windows_text_newline_conversion(self) -> None:
        self.service = self.make_service(
            text_writer=lambda path, text: write_text(path, text.replace("\n", "\r\n")),
        )
        self.assert_synced(self.start())

    def test_failed_or_silently_truncated_backup_save_precedes_cloud_writes(self) -> None:
        self.service.text_writer = lambda path, text: path.write_text("{}", encoding="utf-8")
        first = self.start()
        self.assertEqual(first["status"], "recovery_required", first)
        self.assertEqual(self.fake.writes, [])
        self.assertEqual(self.source_bytes(), {name: (self.paper / name).read_bytes() for name in self.original})

    def test_interrupted_job_status_is_local_only_and_never_auto_resumes(self) -> None:
        self.assert_synced(self.start())
        state = self.journal()
        state.update(status="publishing", phase="uploading_backup")
        write_json(self.paper / publication.STATE_DIRECTORY / publication.JOURNAL_FILENAME, state)
        calls = len(self.fake.calls)
        status = self.make_service().status(self.paper, SETTINGS)
        self.assertEqual(status["status"], "interrupted", status)
        self.assertEqual(len(self.fake.calls), calls)
        self.assert_synced(self.start())
        self.assertEqual(len(self.fake.documents), 1)

    def test_interrupted_unknown_creation_requires_recovery_without_any_cloud_calls(self) -> None:
        state = {**publication._idle(), "status": "publishing", "phase": "creating_document",
                 "pending_write": {"kind": "create"}}
        write_json(self.paper / publication.STATE_DIRECTORY / publication.JOURNAL_FILENAME, state)
        status = self.service.status(self.paper, SETTINGS)
        self.assertEqual(status["status"], "recovery_required", status)
        self.assertEqual(self.fake.calls, [])
        with self.assertRaises(publication.PublicationRecoveryRequired):
            self.preview()
        self.assertEqual(self.fake.calls, [])

    def test_missing_journal_with_existing_backups_does_not_create_another_document(self) -> None:
        self.assert_synced(self.start())
        (self.paper / publication.STATE_DIRECTORY / publication.JOURNAL_FILENAME).unlink()
        calls = len(self.fake.calls)
        status = self.service.status(self.paper, SETTINGS)
        self.assertEqual(status["status"], "recovery_required", status)
        self.assertEqual(len(self.fake.calls), calls)
        with self.assertRaises(publication.PublicationRecoveryRequired):
            self.preview()
        self.assertEqual(len(self.fake.documents), 1)

    def test_os_lease_prevents_a_second_process_style_writer(self) -> None:
        self.preview()
        path = self.paper / publication.STATE_DIRECTORY / "job.lock"
        first = publication._lease(path)
        self.assertIsNotNone(first)
        try:
            second = publication._lease(path)
            try:
                self.assertIsNone(second)
            finally:
                publication._release(second)
        finally:
            publication._release(first)
        third = publication._lease(path)
        self.assertIsNotNone(third)
        publication._release(third)

    def test_status_detects_new_local_edits_without_cli_or_models(self) -> None:
        self.assertEqual(self.service.status(self.paper, SETTINGS)["status"], "idle")
        self.assertEqual(self.fake.calls, [])
        self.assert_synced(self.start())
        calls = len(self.fake.calls)
        self.edit_note()
        self.assertEqual(self.service.status(self.paper, SETTINGS)["status"], "pending")
        self.assertEqual(len(self.fake.calls), calls)

    def test_unsafe_source_and_state_symlinks_are_rejected_without_touching_targets(self) -> None:
        target = self.workspace / "preserve.json"
        target.write_text('{"private":"never upload"}', encoding="utf-8")
        source = self.paper / "annotations.json"
        original = source.read_bytes()
        source.unlink()
        try:
            source.symlink_to(target)
        except (OSError, NotImplementedError):
            source.write_bytes(original)
            self.skipTest("Symlink creation is unavailable.")
        try:
            with self.assertRaises(publication.PublicationStorageError):
                self.preview()
            self.assertEqual(target.read_text(encoding="utf-8"), '{"private":"never upload"}')
            self.assertEqual(self.fake.calls, [])
        finally:
            source.unlink()
            source.write_bytes(original)
        folder = self.paper / publication.STATE_DIRECTORY
        folder.symlink_to(self.workspace, target_is_directory=True)
        try:
            with self.assertRaises(publication.PublicationStorageError):
                self.preview()
        finally:
            folder.unlink()

    def test_unknown_files_in_snapshot_are_rejected_not_uploaded(self) -> None:
        original_reader = self.service.snapshot_reader
        def unsafe(paper):
            raw = original_reader(paper)
            raw["files"][".env"] = "PRIVATE"
            return raw
        self.service.snapshot_reader = unsafe
        with self.assertRaises(publication.PublicationConfigurationError):
            self.preview()
        self.assertEqual(self.fake.calls, [])

    def test_corrupt_source_or_journal_fails_closed(self) -> None:
        path = self.paper / "annotations.json"
        original = path.read_bytes()
        path.write_text("{", encoding="utf-8")
        with self.assertRaises(publication.PublicationStorageError):
            self.preview()
        path.write_bytes(original)
        journal = self.paper / publication.STATE_DIRECTORY / publication.JOURNAL_FILENAME
        journal.parent.mkdir()
        journal.write_text("{", encoding="utf-8")
        with self.assertRaises(publication.PublicationStorageError):
            self.preview()
        self.assertEqual(self.fake.calls, [])

    def test_long_document_uses_stdin_and_revision_checked_chunks(self) -> None:
        self.edit_note("Verbatim long note & <quote>\n" * 500)
        with mock.patch.object(publication, "MAX_CHUNK_BYTES", 8_000), mock.patch.object(publication, "MAX_CHUNK_BLOCKS", 18):
            preview = self.preview()
        status = self.start(preview)
        self.assert_synced(status)
        updates = [call for call in self.fake.calls if call[0][2] == "+update"]
        self.assertGreater(len(updates), 2)
        self.assertEqual([FakeCLI.flag(argv, "--revision-id") for argv, kwargs in updates],
                         [str(number) for number in range(1, len(updates) + 1)])
        for argv, kwargs in updates:
            self.assertEqual(FakeCLI.flag(argv, "--content"), "-")
            self.assertIsInstance(kwargs["input"], str)
            self.assertNotIn(kwargs["input"], argv)
            self.assertLessEqual(len(kwargs["input"].encode("utf-8")), 8_000)
            self.assertLessEqual(publication._block_count(publication._xml_root(kwargs["input"])), 18)
        self.assertEqual(len(self.fake.documents), 1)

    def large_archive(self, *, quote: bool = False) -> dict:
        archive = publication.build_archive(self.snapshot(self.paper))
        paragraphs = "".join(f"<p>source-{index:04d} " + "exact stored text; " * 28 + "</p>" for index in range(626))
        archive["xml"] = "<title>Large synthetic reading archive</title>" + (
            "<blockquote>" + paragraphs + "</blockquote>" if quote else paragraphs)
        return archive

    def assert_bounded_document_calls(self) -> None:
        writes = [(argv, kwargs["input"]) for argv, kwargs in self.fake.calls if argv[2] in {"+create", "+update"}]
        self.assertLess(len(writes[0][1].encode("utf-8")), publication.MAX_CREATE_TITLE_BYTES + 512)
        updates = [(argv, content) for argv, content in writes if argv[2] == "+update"]
        self.assertGreater(len(updates), 1)
        for argv, content in updates:
            self.assertEqual(FakeCLI.flag(argv, "--content"), "-")
            self.assertLessEqual(len(content.encode("utf-8")), publication.MAX_CHUNK_BYTES)
            self.assertLessEqual(publication._block_count(publication._xml_root(content)), publication.MAX_CHUNK_BLOCKS)
            self.assertNotEqual(FakeCLI.flag(argv, "--revision-id"), "-1")
        document = next(iter(self.fake.documents.values()))
        texts = [element.text for element in publication._xml_root(document["content"]).iter("p")
                 if (element.text or "").startswith("source-")]
        self.assertEqual(texts, [f"source-{index:04d} " + "exact stored text; " * 28 for index in range(626)])

    def test_realistic_626_block_archive_uses_small_create_then_hard_bounded_chunks(self) -> None:
        archive = self.large_archive()
        self.assertGreater(len(archive["xml"].encode("utf-8")), 291_590)
        with mock.patch.object(publication, "build_archive", return_value=archive):
            status = self.start()
        self.assert_synced(status)
        self.assert_bounded_document_calls()

    def test_single_large_quote_container_is_split_without_losing_text_or_quote_role(self) -> None:
        archive = self.large_archive(quote=True)
        original_xml = archive["xml"]
        with mock.patch.object(publication, "build_archive", return_value=archive):
            status = self.start()
        self.assert_synced(status)
        self.assertEqual(archive["xml"], original_xml)
        self.assert_bounded_document_calls()
        root = publication._xml_root(next(iter(self.fake.documents.values()))["content"])
        self.assertGreater(len(root.findall("blockquote")), 1)
        self.assertEqual(sum(len(quote.findall("p")) for quote in root.findall("blockquote")), 626)

    def test_indivisible_oversized_block_is_rejected_before_cloud_calls(self) -> None:
        archive = publication.build_archive(self.snapshot(self.paper))
        archive["xml"] = "<title>Safe title</title><p>" + "x" * publication.MAX_CHUNK_BYTES + "</p>"
        with mock.patch.object(publication, "build_archive", return_value=archive):
            with self.assertRaisesRegex(publication.PublicationConfigurationError, "safe chunk limits"):
                self.preview()
        self.assertEqual(self.fake.calls, [])
        self.assertEqual(self.fake.writes, [])

    def test_large_title_uses_small_creation_stub_but_complete_title_in_update(self) -> None:
        archive = publication.build_archive(self.snapshot(self.paper))
        title = "合成标题" * 1_000
        archive["title"] = title
        archive["xml"] = "<title>" + title + "</title><p>Saved content.</p>"
        with mock.patch.object(publication, "build_archive", return_value=archive):
            status = self.start()
        self.assert_synced(status)
        create = next(kwargs["input"] for argv, kwargs in self.fake.calls if argv[2] == "+create")
        self.assertLess(len(create.encode("utf-8")), publication.MAX_CREATE_TITLE_BYTES + 512)
        self.assertEqual(publication._xml_root(next(iter(self.fake.documents.values()))["content"]).find("title").text, title)

    def test_uncertain_middle_chunk_keeps_journal_and_explicit_retry_reuses_same_document(self) -> None:
        archive = self.large_archive()

        def lose_second_write(argv, kwargs, data):
            self.fake.before["+fetch"] = lambda argv, kwargs: failure("network")
            raise subprocess.TimeoutExpired(argv, 180, stderr="SECRET_VALUE")

        def after_first_write(argv, kwargs, data):
            self.fake.after["+update"] = lose_second_write
            return success(data)

        self.fake.after["+update"] = after_first_write
        with mock.patch.object(publication, "build_archive", return_value=archive):
            failed = self.start()
            self.assertEqual(failed["status"], "failed", failed)
            state = self.journal()
            self.assertEqual(state["pending_write"]["kind"], "document")
            self.assertFalse(state["pending_write"]["final"])
            self.assertTrue(state["document_id"])
            self.assertEqual(self.fake.record[BACKUP], [])
            calls = len(self.fake.calls)
            self.assertEqual(self.service.status(self.paper, SETTINGS)["status"], "failed")
            self.assertEqual(len(self.fake.calls), calls)
            self.assert_synced(self.start())
        self.assertEqual(self.fake.writes.count("+create"), 1)
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)
        self.assert_bounded_document_calls()

    def test_permission_and_confirmation_errors_remain_actionable_without_bypass(self) -> None:
        self.fake.before["+create"] = lambda argv, kwargs: failure("confirmation_required", code=10)
        first = self.start()
        self.assertEqual(first["status"], "failed", first)
        self.assertIn("confirmation", first["error"])
        self.assertEqual(self.journal().get("pending_write"), {})
        self.fake.before["+create"] = lambda argv, kwargs: failure("permission_denied")
        second = self.start()
        self.assertEqual(second["status"], "failed", second)
        self.assertIn("--scope", second["error"])
        self.assertNotIn("SECRET_VALUE", json.dumps(second))
        self.assertTrue(all("--yes" not in argv and argv[-2:] == ["--as", "user"] for argv, kwargs in self.fake.calls))
        self.assertEqual(self.fake.documents, {})

    def test_cli_notices_and_warnings_are_visible_without_echoing_secrets(self) -> None:
        self.fake.after["+create"] = lambda argv, kwargs, data: success(
            {**data, "warnings": ["SECRET_VALUE"]}, _notice={"update": {"command": "SECRET_VALUE"}})
        status = self.start()
        self.assert_synced(status)
        self.assertTrue(any("warnings" in warning for warning in status["warnings"]))
        self.assertTrue(any("_notice" in warning for warning in status["warnings"]))
        self.assertNotIn("SECRET_VALUE", json.dumps(status))

    def test_cloud_text_verification_does_not_ignore_inline_whitespace(self) -> None:
        self.assertNotEqual(publication._content_hash("<p><b>A</b> <b>B</b></p>"),
                            publication._content_hash("<p><b>A</b><b>B</b></p>"))


class TablePublicationTests(PublicationFixture):
    def setUp(self) -> None:
        super().setUp()
        self.settings = copy.deepcopy(TABLE_SETTINGS)
        self.original["annotations.json"]["annotations"][0]["origin"] = {"kind": "user"}
        write_json(self.paper / "annotations.json", self.original["annotations.json"])
        self.fake.enable_table_fields()
        self.fake.forbid_docs = True
        mock.patch.object(publication, "_CELL_VERIFY_DELAYS", (0, 0, 0, 0)).start()

    def delay_cell_visibility(self, reads: int, *, mixed: bool = False) -> dict:
        before = {field_id: self.fake.record[field_id] for field_id in TEXT_FIELDS.values()}
        original_record = publication.FeishuPublicationClient.record
        lag = {"remaining": reads, "stale_reads": 0}

        def readback(client, record_id, field_ids):
            observed = original_record(client, record_id, field_ids)
            if self.table_calls() and lag["remaining"] and set(before).issubset(field_ids):
                lag["remaining"] -= 1
                lag["stale_reads"] += 1
                observed.update({TEXT_FIELDS["my-notes"]: before[TEXT_FIELDS["my-notes"]]} if mixed else before)
            return observed

        mock.patch.object(publication.FeishuPublicationClient, "record", new=readback).start()
        return lag

    def table_calls(self) -> list[tuple]:
        return [call for call in self.fake.calls if call[0][2] == "+record-upsert"]

    def test_copied_paper_keeps_publication_ownership_without_duplicate_cloud_writes(self) -> None:
        first = self.start()
        self.assert_synced(first)
        original = self.paper
        copied = self.workspace / "new computer" / "papers" / original.name
        shutil.copytree(original, copied)
        self.papers.append(copied)
        self.paper = copied
        before = self.source_bytes()
        writes = list(self.fake.writes)
        preview = self.preview()
        self.assertFalse(preview["changed"])
        status = self.start(preview)
        self.assert_synced(status)
        self.assertEqual(status["fingerprint"], first["fingerprint"])
        self.assertEqual(self.source_bytes(), before)
        self.assertEqual(self.fake.writes, writes)
        self.assertEqual(len(self.fake.record[BACKUP]), 1)
        self.assert_no_docs()

    def assert_no_docs(self) -> None:
        self.assertFalse(any(argv[1] == "docs" for argv, _kwargs in self.fake.calls))

    def make_legacy_publication(self) -> dict:
        self.fake.forbid_docs = False
        settings = self.settings
        self.settings = copy.deepcopy(SETTINGS)
        try:
            status = self.start()
            self.assert_synced(status)
            legacy = self.journal()
        finally:
            self.settings = settings
            self.fake.forbid_docs = True
        self.fake.calls.clear()
        self.fake.writes.clear()
        return legacy

    def literal_archive(self, texts: dict[str, str]) -> dict:
        archive = publication.build_table_archive(self.snapshot(self.paper))
        for column in archive["columns"]:
            text = texts.get(column["id"], "")
            column.update(text=text, characters=len(text.encode("utf-16-le")) // 2, limit=100_000)
        return archive

    def test_table_idle_status_is_local_and_targets_the_existing_record(self) -> None:
        status = self.service.status(self.paper, self.settings)
        self.assertEqual(status["status"], "idle")
        self.assertEqual(status["mode"], "table")
        self.assertIn("record=" + RECORD, status["record_url"])
        self.assertEqual(status["document_url"], "")
        self.assertEqual(status["legacy_document_url"], "")
        self.assertEqual(self.fake.calls, [])

    def test_table_preview_is_read_only_and_captures_exact_cells_and_raw_data(self) -> None:
        before = self.source_bytes()
        raw = self.snapshot(self.paper)
        preview = self.preview()
        self.assertEqual(preview["mode"], "table")
        self.assertEqual(preview["destination"]["mode"], "table")
        self.assertEqual(preview["destination"]["record_id"], RECORD)
        self.assertEqual({column["id"] for column in preview["columns"]}, set(TEXT_FIELDS))
        self.assertEqual({field["id"] for field in preview["destination"]["text_fields"]}, set(TEXT_FIELDS.values()))
        self.assertEqual(preview["destination"]["backup_field"], {"id": BACKUP, "name": "阅读数据备份"})
        self.assertNotIn("document_url", preview["destination"])
        self.assertTrue(any("single-writer" in warning and "simultaneous" in warning for warning in preview["warnings"]))
        saved = read_json(self.paper / publication.STATE_DIRECTORY / f"preview-{preview['preview_id']}.json", {})
        self.assertEqual(saved["raw"], raw)
        self.assertEqual(saved["cloud"]["values"], dict.fromkeys(TEXT_FIELDS.values()))
        self.assertFalse((self.paper / publication.STATE_DIRECTORY / publication.TABLE_JOURNAL_FILENAME).exists())
        self.assertEqual(before, self.source_bytes())
        self.assertEqual(self.fake.writes, [])
        self.assert_no_docs()

    def test_new_table_flow_writes_only_four_cells_and_backup_with_lossless_local_data(self) -> None:
        self.fake.record[ARCHIVE] = "https://example.feishu.cn/docx/docUnrelatedPreserved"
        before, raw = self.source_bytes(), self.snapshot(self.paper)
        protected = {key: value for key, value in self.fake.record.items() if key not in {*TEXT_FIELDS.values(), BACKUP}}
        preview = self.preview()
        status = self.start(preview)
        self.assert_synced(status)
        self.assertEqual(status["mode"], "table")
        self.assertEqual(status["document_url"], "")
        self.assertEqual(status["record_url"], preview["destination"]["record_url"])
        self.assertEqual(self.fake.writes, ["+record-upload-attachment", "+record-upsert"])
        self.assertEqual(protected, {key: value for key, value in self.fake.record.items() if key not in {*TEXT_FIELDS.values(), BACKUP}})
        self.assertEqual(before, self.source_bytes())
        self.assertEqual({column["field_id"]: column["text"] for column in preview["columns"]},
                         {field_id: self.fake.record[field_id] for field_id in TEXT_FIELDS.values()})
        backup = json.loads(next(iter(self.fake.blobs.values())))
        self.assertEqual(backup["reading_data"], raw)
        self.assertFalse((self.paper / publication.STATE_DIRECTORY / publication.JOURNAL_FILENAME).exists())
        self.assertEqual(self.journal()["mode"], "table")
        self.assert_no_docs()

    def test_long_unicode_json_uses_verified_compact_relative_file_and_short_argv(self) -> None:
        self.edit_note("汉字🧠\n" * 12_000)
        preview = self.preview()
        self.assert_synced(self.start(preview))
        argv, kwargs = self.table_calls()[0]
        argument = FakeCLI.flag(argv, "--json")
        self.assertTrue(argument.startswith("@cells-"))
        self.assertNotEqual(argument, "@-")
        self.assertNotIn("input", kwargs)
        self.assertLess(len(" ".join(argv)), 2_000)
        path = FakeCLI.local_file(argv, kwargs, "--json")
        payload = path.read_bytes()
        self.assertGreater(len(payload), 120_000)
        self.assertFalse(payload.endswith(b"\n"))
        targets = {column["field_id"]: column["text"] for column in preview["columns"]}
        self.assertEqual(json.loads(payload), targets)
        self.assertEqual(payload, publication._json(targets).encode("utf-8"))
        self.assertEqual(self.fake.record[TEXT_FIELDS["my-notes"]], targets[TEXT_FIELDS["my-notes"]])
        self.assert_no_docs()

    def test_table_noop_and_duplicate_start_perform_zero_additional_writes(self) -> None:
        first = self.preview()
        status = self.start(first)
        self.assert_synced(status)
        writes = list(self.fake.writes)
        calls = len(self.fake.calls)
        repeated = self.service.start(self.paper, self.settings, first["preview_id"], True)
        self.assertEqual(repeated["job_id"], status["job_id"])
        self.assertEqual(len(self.fake.calls), calls)
        next_preview = self.preview()
        self.assertFalse(next_preview["changed"])
        self.assert_synced(self.start(next_preview))
        self.assertEqual(self.fake.writes, writes)
        self.assertEqual(len(list((self.paper / publication.STATE_DIRECTORY).glob("cells-*.json"))), 1)
        self.assertTrue(any(argv[2] == "+record-download-attachment" for argv, _kwargs in self.fake.calls[calls:]))
        self.assert_no_docs()

    def test_passive_changes_reuse_original_backup_bytes_without_regeneration(self) -> None:
        self.assert_synced(self.start())
        old_blobs = copy.deepcopy(self.fake.blobs)
        old_backups = copy.deepcopy(self.fake.record[BACKUP])
        write_json(self.paper / "reading_progress.json", {"anchor": "new", "updated_at": "later"})
        metadata_value = read_json(self.paper / "metadata.json", {})
        metadata_value["feishu"]["synced_at"] = "later"
        write_json(self.paper / "metadata.json", metadata_value)
        preview = self.preview()
        self.assertFalse(preview["changed"])
        self.assert_synced(self.start(preview))
        self.assertEqual(self.fake.blobs, old_blobs)
        self.assertEqual(self.fake.record[BACKUP], old_backups)
        self.assertEqual(self.fake.writes.count("+record-upsert"), 1)

    def test_label_only_update_changes_cells_without_duplicate_backup(self) -> None:
        first = self.start()
        self.assert_synced(first)
        originals = self.source_bytes()
        backups = copy.deepcopy(self.fake.record[BACKUP])
        blobs = copy.deepcopy(self.fake.blobs)
        render = publication.build_table_archive

        def relabel(raw):
            archive = render(raw)
            column = archive["columns"][0]
            column["text"] = "Updated label:\n" + column["text"]
            column["characters"] = len(column["text"].encode("utf-16-le")) // 2
            return archive

        with mock.patch.object(publication, "build_table_archive", side_effect=relabel):
            preview = self.preview()
            self.assertTrue(preview["changed"])
            self.assertEqual(preview["fingerprint"], first["published_fingerprint"])
            self.assert_synced(self.start(preview))
            self.assertFalse(self.preview()["changed"])
        self.assertEqual(self.fake.record[BACKUP], backups)
        self.assertEqual(self.fake.blobs, blobs)
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)
        self.assertEqual(len(self.table_calls()), 2)
        self.assertEqual(self.source_bytes(), originals)
        self.assert_no_docs()

    def test_migration_preserves_legacy_doc_journal_url_and_matching_backup(self) -> None:
        legacy = self.make_legacy_publication()
        legacy_path = self.paper / publication.STATE_DIRECTORY / publication.JOURNAL_FILENAME
        legacy_bytes = legacy_path.read_bytes()
        documents = copy.deepcopy(self.fake.documents)
        blobs = copy.deepcopy(self.fake.blobs)
        backups = copy.deepcopy(self.fake.record[BACKUP])
        write_json(self.paper / "reading_progress.json", {"anchor": "newer-passive-progress"})
        preview = self.preview()
        self.assertEqual(preview["destination"]["legacy_document_url"], legacy["document_url"])
        status = self.start(preview)
        self.assert_synced(status)
        self.assertEqual(status["legacy_document_url"], legacy["document_url"])
        self.assertEqual(status["document_url"], "")
        self.assertEqual(self.fake.record[ARCHIVE], legacy["document_url"])
        self.assertEqual(legacy_path.read_bytes(), legacy_bytes)
        self.assertEqual(self.fake.documents, documents)
        self.assertEqual(self.fake.blobs, blobs)
        self.assertEqual(self.fake.record[BACKUP], backups)
        self.assertEqual(self.fake.writes, ["+record-upsert"])
        self.assertTrue(any(argv[2] == "+record-download-attachment" for argv, _kwargs in self.fake.calls))
        self.assert_no_docs()

    def test_migration_with_missing_local_backup_verifies_remote_bytes_not_new_timestamps(self) -> None:
        legacy = self.make_legacy_publication()
        fingerprint = legacy["published_fingerprint"]
        receipt = legacy["backups"][fingerprint]
        local = self.paper / publication.STATE_DIRECTORY / receipt["name"]
        original = self.fake.blobs[receipt["file_token"]]
        local.unlink()
        write_json(self.paper / "reading_progress.json", {"anchor": "updated-after-legacy-backup"})
        self.assert_synced(self.start())
        self.assertFalse(local.exists())
        self.assertEqual(self.fake.blobs[receipt["file_token"]], original)
        self.assertEqual(self.journal()["backups"][fingerprint], receipt)
        self.assertEqual(self.fake.writes, ["+record-upsert"])
        self.assert_no_docs()

    def test_table_mode_does_not_fetch_or_overwrite_edited_legacy_document(self) -> None:
        legacy = self.make_legacy_publication()
        document = self.fake.documents[legacy["document_id"]]
        document["content"] += "<p>A manual edit to the old Docx.</p>"
        document["revision_id"] += 1
        before = copy.deepcopy(document)
        self.assert_synced(self.start())
        self.assertEqual(document, before)
        self.assert_no_docs()

    def test_explicit_legacy_mode_after_table_only_publication_reuses_shared_backup(self) -> None:
        self.assert_synced(self.start())
        table_path = self.paper / publication.STATE_DIRECTORY / publication.TABLE_JOURNAL_FILENAME
        before = table_path.read_bytes()
        blobs = copy.deepcopy(self.fake.blobs)
        legacy = self.make_legacy_publication()
        self.assertTrue(legacy["document_url"])
        self.assertEqual(table_path.read_bytes(), before)
        self.assertEqual(self.fake.blobs, blobs)
        self.assertEqual(len(self.fake.record[BACKUP]), 1)

    def test_migration_binding_mismatch_refuses_receipt_adoption(self) -> None:
        self.make_legacy_publication()
        local = read_json(self.paper / "metadata.json", {})
        local["feishu"]["record_id"] = "recOther"
        write_json(self.paper / "metadata.json", local)
        with self.assertRaises(publication.PublicationConflict):
            self.preview()
        self.assertEqual(self.fake.writes, [])
        self.assert_no_docs()

    def test_new_meaningful_revision_updates_four_fields_and_keeps_old_backups(self) -> None:
        first = self.start()
        self.assert_synced(first)
        previous = copy.deepcopy(self.fake.record[BACKUP])
        self.edit_note("Exactly this next user note.")
        second = self.start()
        self.assert_synced(second)
        self.assertNotEqual(first["fingerprint"], second["fingerprint"])
        self.assertEqual(self.fake.record[BACKUP][:1], previous)
        self.assertEqual(len(self.fake.record[BACKUP]), 2)
        self.assertEqual(len(self.table_calls()), 2)
        self.assertIn("Exactly this next user note.", self.fake.record[TEXT_FIELDS["my-notes"]])
        self.assert_no_docs()

    def test_empty_category_clears_only_its_previously_managed_cell(self) -> None:
        self.assert_synced(self.start())
        original_manual = self.fake.record["fldManual"]
        write_json(self.paper / "annotations.json", {"annotations": []})
        write_json(self.paper / "thinking.json", {"blocks": [], "report_thoughts": []})
        self.fake.empty_as_null = True
        preview = self.preview()
        self.assertEqual(next(column["text"] for column in preview["columns"] if column["id"] == "my-notes"), "")
        self.assert_synced(self.start(preview))
        self.assertIsNone(self.fake.record[TEXT_FIELDS["my-notes"]])
        self.assertEqual(self.journal()["cell_receipt"]["values"][TEXT_FIELDS["my-notes"]], "")
        self.assertEqual(self.fake.record["fldManual"], original_manual)
        self.assertFalse(self.preview()["changed"])
        self.assert_no_docs()

    def test_nonempty_unmanaged_cells_are_never_adopted_even_if_content_matches(self) -> None:
        desired = publication.build_table_archive(self.snapshot(self.paper))["columns"][0]["text"]
        for value in (" ", "Unmanaged notes: do not overwrite.", desired):
            self.fake.record[TEXT_FIELDS["my-notes"]] = value
            with self.subTest(value=value[:20]), self.assertRaises(publication.PublicationConflict):
                self.preview()
        self.assertEqual(self.fake.writes, [])

    def test_table_local_staleness_and_edited_preview_fail_before_mutations(self) -> None:
        preview = self.preview()
        path = self.paper / publication.STATE_DIRECTORY / f"preview-{preview['preview_id']}.json"
        saved = read_json(path, {})
        saved["public"]["columns"][0]["text"] = "Unapproved"
        write_json(path, saved)
        with self.assertRaises(publication.PublicationConflict):
            self.service.start(self.paper, self.settings, preview["preview_id"], True)
        fresh = self.preview()
        self.edit_note()
        with self.assertRaises(publication.PublicationConflict):
            self.service.start(self.paper, self.settings, fresh["preview_id"], True)
        self.assertEqual(self.fake.writes, [])

    def test_configurable_names_resolve_real_ids_and_protected_columns_are_rejected(self) -> None:
        self.settings["text_fields"] = {key: "Managed " + key for key in TEXT_FIELDS}
        for field in self.fake.fields:
            for section_id, field_id in TEXT_FIELDS.items():
                if field["id"] == field_id:
                    field["name"] = self.settings["text_fields"][section_id]
        self.assert_synced(self.start())
        self.assertEqual({field["id"] for field in self.journal()["text_fields"]}, set(TEXT_FIELDS.values()))
        changed = {**self.settings, "text_fields": {**self.settings["text_fields"], "my-notes": "raw text"}}
        with self.assertRaises(publication.PublicationConflict):
            self.service.preview(self.paper, changed)

    def test_invalid_mode_schema_and_aliases_fail_closed(self) -> None:
        for mode in ("", "unknown", None, 1):
            settings = {**self.settings, "mode": mode}
            for method in ("preview", "status"):
                with self.subTest(mode=mode, method=method), self.assertRaises(ValueError):
                    getattr(self.service, method)(self.paper, settings)
        for text_fields in ({}, {**self.settings["text_fields"], "extra": "Extra"},
                            {**self.settings["text_fields"], "my-notes": "阅读档案"},
                            {**self.settings["text_fields"], "my-notes": "AI 讨论"}):
            with self.subTest(text_fields=text_fields), self.assertRaises(ValueError):
                self.service.preview(self.paper, {**self.settings, "text_fields": text_fields})
        original = copy.deepcopy(self.fake.fields)
        index = next(index for index, field in enumerate(original) if field["id"] == TEXT_FIELDS["my-notes"])
        for change in ({"type": "formula"}, {"style": {"type": "url"}}, {"id": "fldHblyRK0"}):
            self.fake.fields = copy.deepcopy(original)
            self.fake.fields[index].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.preview()
        self.assertEqual(self.fake.writes, [])

    def test_utf16_cell_limit_is_enforced_before_cloud_reads_or_writes(self) -> None:
        self.edit_note("🧠" * 50_001)
        with self.assertRaisesRegex(ValueError, "100,000|100000"):
            self.preview()
        self.assertEqual(self.fake.calls, [])
        self.assertEqual(self.fake.writes, [])

    def test_exact_utf16_boundary_is_preserved_and_incorrect_counts_are_rejected(self) -> None:
        text = "🧠" * 50_000
        archive = self.literal_archive({"my-notes": text})
        with mock.patch.object(publication, "build_table_archive", return_value=archive):
            self.assert_synced(self.start())
        self.assertEqual(self.fake.record[TEXT_FIELDS["my-notes"]], text)
        self.assert_no_docs()
        bad = copy.deepcopy(archive)
        bad["columns"][0]["characters"] = 50_000
        writes = list(self.fake.writes)
        with mock.patch.object(publication, "build_table_archive", return_value=bad), self.assertRaises(ValueError):
            self.preview()
        self.assertEqual(self.fake.writes, writes)

    def test_cloud_cell_edit_after_preview_stops_before_backup_or_patch(self) -> None:
        self.assert_synced(self.start())
        self.edit_note()
        preview = self.preview()
        writes = list(self.fake.writes)
        self.fake.record[TEXT_FIELDS["ai-discussions"]] = "New cloud edit"
        status = self.start(preview)
        self.assertEqual(status["status"], "conflict", status)
        self.assertEqual(self.fake.writes, writes)
        self.assertEqual(self.fake.record[TEXT_FIELDS["ai-discussions"]], "New cloud edit")

    def test_schema_change_after_preview_is_a_conflict_before_any_mutation(self) -> None:
        preview = self.preview()
        field = next(field for field in self.fake.fields if field["id"] == TEXT_FIELDS["my-notes"])
        field["style"] = {"type": "url"}
        status = self.start(preview)
        self.assertEqual(status["status"], "conflict", status)
        self.assertEqual(self.fake.writes, [])
        self.assert_no_docs()

    def test_binding_or_meaningful_data_change_during_table_preflight_stops_writes(self) -> None:
        preview = self.preview()
        def edit_local(argv, kwargs, data):
            self.edit_note("An edit during preflight.")
            return success(data)
        self.fake.after["+field-list"] = edit_local
        status = self.start(preview)
        self.assertEqual(status["status"], "conflict", status)
        self.assertEqual(self.fake.writes, [])
        fresh = self.preview()
        local = read_json(self.paper / "metadata.json", {})
        local["feishu"]["record_id"] = "recAnother"
        write_json(self.paper / "metadata.json", local)
        with self.assertRaises(publication.PublicationConflict):
            self.service.start(self.paper, self.settings, fresh["preview_id"], True)
        self.assertEqual(self.fake.writes, [])

    def test_cloud_edit_during_backup_is_not_overwritten_by_later_patch(self) -> None:
        def external_edit(argv, kwargs, data):
            self.fake.record[TEXT_FIELDS["my-notes"]] = "A cloud editor owns this."
            return success(data)
        self.fake.after["+record-upload-attachment"] = external_edit
        status = self.start()
        self.assertEqual(status["status"], "conflict", status)
        self.assertEqual(self.fake.writes, ["+record-upload-attachment"])
        self.assertEqual(self.fake.record[TEXT_FIELDS["my-notes"]], "A cloud editor owns this.")

    def test_cloud_edit_after_patch_is_detected_and_never_repaired_over_the_editor(self) -> None:
        def external_edit(argv, kwargs, data):
            self.fake.record[TEXT_FIELDS["my-notes"]] = "A newer manual cloud note."
            return success(data)
        self.fake.after["+record-upsert"] = external_edit
        status = self.start()
        self.assertEqual(status["status"], "conflict", status)
        with self.assertRaises(publication.PublicationConflict):
            self.preview()
        self.assertEqual(len(self.table_calls()), 1)
        self.assertEqual(self.fake.record[TEXT_FIELDS["my-notes"]], "A newer manual cloud note.")
        self.assertTrue(any("single-writer" in warning for warning in status["warnings"]))

    def test_local_edits_during_table_upload_result_in_pending(self) -> None:
        preview = self.preview()
        def save_newer_local_note(argv, kwargs, data):
            self.edit_note("Saved while publication was uploading its backup.")
            return success(data)
        self.fake.after["+record-upload-attachment"] = save_newer_local_note
        status = self.start(preview)
        self.assertEqual(status["status"], "pending", status)
        self.assertEqual(status["published_fingerprint"], preview["fingerprint"])
        self.assertNotEqual(archive_fingerprint(self.snapshot(self.paper)), status["published_fingerprint"])
        self.assertEqual(json.loads(next(iter(self.fake.blobs.values())))["reading_data"]["files"]["annotations.json"],
                         self.original["annotations.json"])
        self.assert_no_docs()

    def test_uncertain_successful_patch_is_verified_without_repeated_mutation(self) -> None:
        def timeout(argv, kwargs, data):
            raise subprocess.TimeoutExpired(argv, 180, stderr="SECRET_VALUE")
        self.fake.after["+record-upsert"] = timeout
        status = self.start()
        self.assert_synced(status)
        self.assertTrue(any("uncertain" in warning for warning in status["warnings"]))
        self.assertNotIn("SECRET_VALUE", json.dumps(status))
        self.assert_synced(self.start())
        self.assertEqual(len(self.table_calls()), 1)

    def test_acknowledged_patch_waits_for_stale_readback_without_writing_again(self) -> None:
        lag = self.delay_cell_visibility(2)
        status = self.start()
        self.assert_synced(status)
        self.assertEqual(lag["stale_reads"], 2)
        self.assertEqual(len(self.table_calls()), 1)
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)
        self.assertFalse(self.journal()["pending_write"])

    def test_acknowledged_patch_can_wait_for_mixed_expected_projection(self) -> None:
        lag = self.delay_cell_visibility(2, mixed=True)
        self.assert_synced(self.start())
        self.assertEqual(lag["stale_reads"], 2)
        self.assertEqual(len(self.table_calls()), 1)
        self.assert_no_docs()

    def test_readback_wait_is_bounded_and_retains_receipt_for_safe_recovery(self) -> None:
        lag = self.delay_cell_visibility(100)
        failed = self.start()
        self.assertEqual(failed["status"], "recovery_required", failed)
        self.assertEqual(failed["phase"], "verifying_record")
        self.assertEqual(lag["stale_reads"], 1 + len(publication._CELL_VERIFY_DELAYS))
        self.assertEqual(len(self.table_calls()), 1)
        self.assertEqual(self.journal()["pending_write"]["outcome"], "acknowledged")
        lag["remaining"] = 0
        self.assert_synced(self.start())
        self.assertEqual(len(self.table_calls()), 1)

    def test_uncertain_unapplied_patch_blocks_retry_until_all_expected_values_appear(self) -> None:
        def timeout(argv, kwargs):
            raise subprocess.TimeoutExpired(argv, 180)
        self.fake.before["+record-upsert"] = timeout
        status = self.start()
        self.assertEqual(status["status"], "recovery_required", status)
        pending = self.journal()["pending_write"]
        self.assertEqual(pending["kind"], "cells")
        with self.assertRaises(publication.PublicationRecoveryRequired):
            self.preview()
        self.assertEqual(len(self.table_calls()), 1)
        self.fake.record.update(pending["after"]["values"])
        self.assert_synced(self.start())
        self.assertEqual(len(self.table_calls()), 1)
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)

    def test_failed_post_patch_verification_recovers_receipt_without_repatching(self) -> None:
        def lose_verification(argv, kwargs, data):
            self.fake.before["+record-get"] = lambda argv, kwargs: failure("network")
            return success(data)
        self.fake.after["+record-upsert"] = lose_verification
        failed = self.start()
        self.assertEqual(failed["status"], "failed", failed)
        self.assertEqual(self.journal()["pending_write"]["kind"], "cells")
        self.assert_synced(self.start())
        self.assertEqual(len(self.table_calls()), 1)

    def test_reported_partial_result_keeps_verified_cells_but_requires_explicit_retry(self) -> None:
        self.fake.after["+record-upsert"] = lambda argv, kwargs, data: success(
            {**data, "result": "partial_success", "ignored_fields": ["SECRET_VALUE"]})
        failed = self.start()
        self.assertEqual(failed["status"], "failed", failed)
        self.assertIn("partial", failed["error"])
        self.assertNotIn("SECRET_VALUE", json.dumps(failed))
        self.assertTrue(self.journal()["cell_receipt"])
        self.assert_synced(self.start())
        self.assertEqual(len(self.table_calls()), 1)

    def test_partial_write_receipt_in_error_envelope_is_not_treated_as_wholly_rejected(self) -> None:
        self.fake.after["+record-upsert"] = lambda argv, kwargs, data: failure(
            "permission_denied", data={**data, "result": "partial_success"})
        failed = self.start()
        self.assertEqual(failed["status"], "failed", failed)
        self.assertIn("partial", failed["error"])
        self.assertTrue(self.journal()["cell_receipt"])
        self.assert_synced(self.start())
        self.assertEqual(len(self.table_calls()), 1)

    def test_actual_partial_patch_saves_only_observed_expected_values_for_retry(self) -> None:
        def partial(argv, kwargs):
            payload = json.loads(FakeCLI.local_file(argv, kwargs, "--json").read_bytes())
            self.fake.record[TEXT_FIELDS["my-notes"]] = payload[TEXT_FIELDS["my-notes"]]
            return success({"updated": True, "result": "partial_success", "record": {"id": RECORD}})
        self.fake.before["+record-upsert"] = partial
        failed = self.start()
        self.assertEqual(failed["status"], "failed", failed)
        values = self.journal()["cell_receipt"]["values"]
        self.assertTrue(values[TEXT_FIELDS["my-notes"]])
        self.assertEqual(values[TEXT_FIELDS["ai-discussions"]], "")
        self.assert_synced(self.start())
        self.assertEqual(len(self.table_calls()), 2)
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)

    def test_rejected_patch_is_actionable_and_does_not_repeat_backup_upload(self) -> None:
        self.fake.before["+record-upsert"] = lambda argv, kwargs: failure("permission_denied")
        failed = self.start()
        self.assertEqual(failed["status"], "failed", failed)
        self.assertIn("--scope", failed["error"])
        self.assertEqual(self.journal()["pending_write"], {})
        self.assert_synced(self.start())
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)
        self.assertEqual(len(self.table_calls()), 2)
        self.assertTrue(all("--yes" not in argv for argv, _kwargs in self.fake.calls))

    def test_rejected_patch_with_failed_read_can_reconcile_unchanged_values(self) -> None:
        def reject_then_lose_read(argv, kwargs):
            self.fake.before["+record-get"] = lambda argv, kwargs: failure("network")
            return failure("permission_denied")
        self.fake.before["+record-upsert"] = reject_then_lose_read
        failed = self.start()
        self.assertEqual(failed["status"], "failed", failed)
        self.assertEqual(self.journal()["pending_write"]["outcome"], "rejected")
        self.assert_synced(self.start())
        self.assertEqual(len(self.table_calls()), 2)
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)

    def test_recorded_partial_patch_with_failed_read_reconciles_only_expected_subset(self) -> None:
        def partial_then_lose_read(argv, kwargs):
            payload = json.loads(FakeCLI.local_file(argv, kwargs, "--json").read_bytes())
            self.fake.record[TEXT_FIELDS["my-notes"]] = payload[TEXT_FIELDS["my-notes"]]
            self.fake.before["+record-get"] = lambda argv, kwargs: failure("network")
            return success({"updated": True, "result": "partial_success"})
        self.fake.before["+record-upsert"] = partial_then_lose_read
        failed = self.start()
        self.assertEqual(failed["status"], "failed", failed)
        self.assertEqual(self.journal()["pending_write"]["outcome"], "partial")
        self.assert_synced(self.start())
        self.assertEqual(len(self.table_calls()), 2)
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)

    def test_old_uncertain_upload_is_preserved_when_new_snapshot_is_published(self) -> None:
        def timeout(argv, kwargs):
            raise subprocess.TimeoutExpired(argv, 180)
        self.fake.before["+record-upload-attachment"] = timeout
        old = self.start()
        self.assertEqual(old["status"], "recovery_required", old)
        old_name = self.journal()["pending_write"]["name"]
        self.edit_note("A separate new snapshot, not a retry of the unknown upload.")
        current = self.start()
        self.assert_synced(current)
        self.assertIn(old_name, self.journal()["uncertain_uploads"])
        self.assertTrue(any("unresolved" in warning for warning in current["warnings"]))
        self.assertTrue((self.paper / publication.STATE_DIRECTORY / old_name).exists())
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 2)
        write_json(self.paper / "annotations.json", self.original["annotations.json"])
        reverted = self.start()
        self.assertEqual(reverted["status"], "recovery_required", reverted)
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 2)

    def test_uncertain_attachment_retry_never_duplicates_a_registered_backup(self) -> None:
        self.fake.before["+record-download-attachment"] = lambda argv, kwargs: failure("network")
        failed = self.start()
        self.assertEqual(failed["status"], "failed", failed)
        self.assertEqual(len(self.fake.record[BACKUP]), 1)
        self.assertEqual(len(self.table_calls()), 0)
        self.assert_synced(self.start())
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)

    def test_tampered_or_unsaved_request_file_stops_before_patch(self) -> None:
        def bad_writer(path, text):
            write_text(path, "{}" if path.name.startswith("cells-") else text)
        self.service.text_writer = bad_writer
        failed = self.start()
        self.assertEqual(failed["status"], "recovery_required", failed)
        self.assertEqual(len(self.table_calls()), 0)
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)
        self.service.text_writer = write_text
        self.assert_synced(self.start())
        self.assertEqual(self.fake.writes.count("+record-upload-attachment"), 1)

    def test_request_modified_after_journaling_is_detected_by_cli_boundary_guard(self) -> None:
        def edit_request(path, value):
            write_json(path, value)
            pending = value.get("pending_write", {})
            if pending.get("kind") == "cells":
                (path.parent / pending["request_file"]).write_text("modified", encoding="utf-8")
        self.service.json_writer = edit_request
        failed = self.start()
        self.assertEqual(failed["status"], "recovery_required", failed)
        self.assertEqual(len(self.table_calls()), 0)

    def test_windows_crlf_writer_preserves_both_compact_backup_and_patch_payload(self) -> None:
        self.service.text_writer = lambda path, text: path.write_text(text, encoding="utf-8", newline="\r\n")
        self.assert_synced(self.start())
        for path in (self.paper / publication.STATE_DIRECTORY).glob("cells-*.json"):
            self.assertFalse(path.read_bytes().endswith(b"\n"))
        self.assert_no_docs()

    def test_cell_receipt_save_failure_recovers_from_durable_intent_after_restart(self) -> None:
        def fail_receipt(path, value):
            if path.name == publication.TABLE_JOURNAL_FILENAME and value.get("cell_receipt"):
                raise OSError("SECRET_VALUE")
            write_json(path, value)
        self.service.json_writer = fail_receipt
        failed = self.start()
        self.assertEqual(failed["status"], "recovery_required", failed)
        self.assertTrue(failed["storage_error"])
        self.assertEqual(self.journal()["pending_write"]["kind"], "cells")
        self.assertEqual(len(self.table_calls()), 1)
        self.service.json_writer = write_json
        with publication._RUNTIME_LOCK:
            publication._RUNTIMES.pop(publication.os.path.normcase(str(self.paper)), None)
        calls = len(self.fake.calls)
        status = self.service.status(self.paper, self.settings)
        self.assertEqual(status["status"], "interrupted", status)
        self.assertEqual(len(self.fake.calls), calls)
        self.assert_synced(self.start())
        self.assertEqual(len(self.table_calls()), 1)
        self.assert_no_docs()

    def test_same_table_jobs_serialize_backup_and_four_cell_mutations(self) -> None:
        second = self.paper.with_name("second-table-paper")
        second.mkdir()
        self.papers.append(second)
        for name, data in self.original.items():
            data = copy.deepcopy(data)
            if name == "metadata.json":
                data["feishu"]["record_id"] = "recSecond"
            write_json(second / name, data)
        self.fake.records["recSecond"] = copy.deepcopy(self.fake.record)
        entered, release, queued = (threading.Event() for _ in range(3))
        self.addCleanup(release.set)
        def hold_upload(argv, kwargs):
            entered.set()
            if not release.wait(5):
                raise AssertionError("Release the first table publication.")
        def watch_second(path, value):
            write_json(path, value)
            if path.parent.parent == second and value.get("phase") == "uploading_backup":
                queued.set()
        other = self.make_service(json_writer=watch_second)
        first_preview, second_preview = self.preview(), other.preview(second, self.settings)
        self.fake.before["+record-upload-attachment"] = hold_upload
        try:
            self.service.start(self.paper, self.settings, first_preview["preview_id"], True)
            self.assertTrue(entered.wait(3))
            other.start(second, self.settings, second_preview["preview_id"], True)
            self.assertTrue(queued.wait(3))
            self.assertEqual(self.fake.writes, ["+record-upload-attachment"])
            self.assertEqual(other.status(second, self.settings)["status"], "publishing")
        finally:
            release.set()
            for paper in self.papers:
                thread = publication._runtime(paper).thread
                if thread:
                    thread.join(10)
                    self.assertFalse(thread.is_alive())
        self.assert_synced(self.service.status(self.paper, self.settings))
        self.assert_synced(other.status(second, self.settings))
        self.assertEqual(self.fake.writes, [
            "+record-upload-attachment", "+record-upsert", "+record-upload-attachment", "+record-upsert",
        ])
        self.assert_no_docs()

    def test_same_paper_lease_serializes_table_and_legacy_jobs(self) -> None:
        table_preview = self.preview()
        legacy_preview = self.service.preview(self.paper, SETTINGS)
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)
        def hold(argv, kwargs):
            entered.set()
            if not release.wait(5):
                raise AssertionError("Release the table upload.")
        self.fake.before["+record-upload-attachment"] = hold
        try:
            self.service.start(self.paper, self.settings, table_preview["preview_id"], True)
            self.assertTrue(entered.wait(3))
            with self.assertRaises(publication.PublicationConflict):
                self.service.start(self.paper, SETTINGS, legacy_preview["preview_id"], True)
            lease = publication._lease(self.paper / publication.STATE_DIRECTORY / "job.lock")
            try:
                self.assertIsNone(lease)
            finally:
                publication._release(lease)
        finally:
            release.set()
            publication._runtime(self.paper).thread.join(10)
        self.assert_synced(self.service.status(self.paper, self.settings))
        self.assert_no_docs()


class RunnerCompatibilityTests(unittest.TestCase):
    def test_public_service_and_conflict_contract_remain_exact(self) -> None:
        import inspect
        constructor = inspect.signature(publication.PublicationService).parameters
        self.assertEqual(list(constructor), ["snapshot_reader", "json_reader", "json_writer", "text_writer"])
        self.assertTrue(all(parameter.kind == inspect.Parameter.KEYWORD_ONLY
                            and parameter.default == inspect.Parameter.empty for parameter in constructor.values()))
        for method, expected in (
            ("preview", ["self", "paper_dir", "settings"]),
            ("start", ["self", "paper_dir", "settings", "preview_id", "confirmed"]),
            ("status", ["self", "paper_dir", "settings"]),
        ):
            self.assertEqual(list(inspect.signature(getattr(publication.PublicationService, method)).parameters), expected)
        self.assertTrue(issubclass(publication.PublicationConflict, ValueError))

    def test_table_write_gate_is_shared_and_scoped_to_exact_base_and_table(self) -> None:
        same = publication._table_write_lock(BASE, TABLE)
        self.assertIs(same, publication._table_write_lock(BASE, TABLE))
        self.assertIsNot(same, publication._table_write_lock("OtherBase", TABLE))
        self.assertIsNot(same, publication._table_write_lock(BASE, "tblOther"))

    def test_existing_read_defaults_remain_shell_free_and_base_user(self) -> None:
        with mock.patch.object(metadata, "cli_command", return_value="fake-lark-cli.exe"), \
                mock.patch.object(metadata.subprocess, "run", return_value=success({"value": 1})) as run:
            self.assertEqual(metadata.run_cli(["+record-get"]), {"value": 1})
        self.assertEqual(run.call_args.args[0], ["fake-lark-cli.exe", "base", "+record-get", "--as", "user"])
        self.assertEqual(run.call_args.kwargs["timeout"], 45)
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertNotIn("input", run.call_args.kwargs)

    def test_write_timeout_is_unknown_and_never_claims_cached_metadata_unchanged(self) -> None:
        with mock.patch.object(metadata, "cli_command", return_value="fake-lark-cli.exe"), \
                mock.patch.object(metadata.subprocess, "run", side_effect=subprocess.TimeoutExpired([], 1, stderr="SECRET_VALUE")):
            with self.assertRaises(metadata.FeishuCLIError) as caught:
                metadata.run_cli(["+create", "--content", "-"], service="docs", input_text="saved XML", write=True)
        self.assertTrue(caught.exception.uncertain)
        self.assertNotIn("SECRET_VALUE", str(caught.exception))
        self.assertNotIn("Cached metadata is unchanged", str(caught.exception))

    def test_write_receipts_and_envelope_diagnostics_are_preserved(self) -> None:
        data = {"document": {"document_id": "docKnown", "revision_id": 2}, "result": "partial_success"}
        response = failure("api", data=data)
        with mock.patch.object(metadata, "cli_command", return_value="fake-lark-cli.exe"), \
                mock.patch.object(metadata.subprocess, "run", return_value=response):
            with self.assertRaises(metadata.FeishuCLIError) as caught:
                metadata.run_cli(["+create"], service="docs", write=True, full_response=True)
        self.assertEqual(caught.exception.response["data"], data)
        self.assertNotIn("SECRET_VALUE", str(caught.exception))

    def test_new_module_does_not_import_model_or_reader_runtime(self) -> None:
        import ast
        tree = ast.parse(Path(publication.__file__).read_text(encoding="utf-8"))
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        imports += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
        self.assertFalse(set(imports) & {"paper_reader_agent", "openai", "anthropic", "urllib.request", "requests"})


if __name__ == "__main__":
    unittest.main()
