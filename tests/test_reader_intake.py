"""On-demand Feishu-to-reader handoff using synthetic PDFs and a mocked cloud."""

import copy
import io
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

import feishu_metadata as feishu
import paper_reader_agent as reader


class FeishuIntakeTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="reader-intake-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = self.root / "workspace"
        reader.write_json(self.workspace / "library.json", {"papers": []})
        self.pdf = b"%PDF-1.4\nSynthetic paper chosen for reading.\n%%EOF\n"
        self.local_pdf = self.root / "local.pdf"
        self.local_pdf.write_bytes(self.pdf)
        self.source = {
            "record_id": "recSynthetic",
            "metadata": {key: "" for key in feishu.FIELD_MAPPING},
            "field_sources": {key: value[0] for key, value in feishu.FIELD_MAPPING.items()},
            "briefings": {"raw text": "# Title: Not the mapped title", "raw text_中文": "  Existing screening brief.\n"},
            "attachments": [{"field_id": "fldE2HGqZA", "file_token": "fileSynthetic", "name": "Example.pdf", "size": len(self.pdf)}],
        }
        self.source["metadata"].update(title="Mapped cloud title", authors="Mapped author", year="2026")
        settings = {"PAPER_READER_FEISHU_BASE_TOKEN": "SyntheticBase", "PAPER_READER_FEISHU_TABLE_ID": "tblSynthetic"}
        self.patch(reader, "env_value", side_effect=lambda *names, default="": next((settings[key] for key in names if key in settings), default))
        self.patch(reader, "PROCESSING_JOBS", new=None)
        self.resolve = self.patch(feishu, "resolve_record_reference", return_value="recSynthetic")
        self.fetch = self.patch(feishu, "read_intake_record", side_effect=lambda *args, **kwargs: copy.deepcopy(self.source))
        self.download = self.patch(feishu, "download_record_attachment", side_effect=self.download_pdf)
        self.queued = self.patch(reader, "start_background_paper_processing", side_effect=self.queue_pdf)
        self.patch(reader, "find_paper_record", side_effect=AssertionError("Intake must not scan/enrich every paper"))
        for name in ("run_mineru", "agent_chat", "update_paper_brief_from_pdf", "refresh_paper_citations", "refresh_paper_videos"):
            self.patch(reader, name, side_effect=AssertionError(f"Unexpected model/converter: {name}"))
        self.patch(reader.urllib.request, "urlopen", side_effect=AssertionError("No external network"))

    def patch(self, target, name, **kwargs):
        patcher = mock.patch.object(target, name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def download_pdf(self, base, table, record_id, file_token, destination, **kwargs):
        destination.write_bytes(self.pdf)
        return destination

    def queue_pdf(self, workspace, paper_id, paper_dir, options, **kwargs):
        reader.save_processing_fields(workspace, paper_id, paper_dir, {
            "processing_mode": "deep", "processing_status": "processing_queued", "processing_background": "queued",
        })
        return True

    def request(self, path, method="GET", data=None):
        body = json.dumps({} if data is None else data).encode("utf-8")
        handler = object.__new__(reader.ReaderHandler)
        handler.workspace, handler.path, handler.command = self.workspace, path, method
        handler.request_version = "HTTP/1.1"
        handler.requestline = f"{method} {path} HTTP/1.1"
        handler.headers = {"Content-Length": str(len(body))}
        handler.rfile, handler.wfile = io.BytesIO(body), io.BytesIO()
        handler.log_message = lambda *args: None
        getattr(handler, f"do_{method}")()
        header, _, response = handler.wfile.getvalue().partition(b"\r\n\r\n")
        return int(header.split()[1]), json.loads(response)

    def snapshot(self):
        return {str(path.relative_to(self.workspace)): path.read_bytes() for path in self.workspace.rglob("*") if path.is_file()}

    def intake(self, **options):
        return self.request("/api/feishu/intake", "POST", {
            "record_id": "recSynthetic", "file_token": "fileSynthetic", **options,
        })

    def test_preview_and_queue_listing_are_read_only_and_do_not_import(self):
        before = self.snapshot()
        status, preview = self.request("/api/feishu/preview?reference=recSynthetic")
        self.assertEqual(status, 200)
        self.assertEqual(preview["record"]["briefings"], self.source["briefings"])
        self.assertIsNone(preview["local_paper"])
        status, queue = self.request("/api/processing-queue")
        self.assertEqual((status, queue["concurrency"], queue["jobs"]), (200, 1, []))
        self.download.assert_not_called()
        self.queued.assert_not_called()
        self.assertEqual(self.snapshot(), before)

    def test_explicit_local_pdf_is_copied_and_bound_without_download_or_brief_generation(self):
        status, result = self.intake(local_pdf_path=str(self.local_pdf))
        self.assertEqual(status, 200, result)
        folder = self.workspace / "papers" / result["paper_id"]
        metadata = reader.read_json(folder / "metadata.json", {})
        self.assertEqual(metadata["feishu"]["record_id"], "recSynthetic")
        self.assertEqual(metadata["title"], "Mapped cloud title")
        self.assertEqual(metadata["title_source"], "feishu")
        self.assertEqual(metadata["authors"], "Mapped author")
        self.assertEqual(metadata["processing_status"], "processing_queued")
        self.assertEqual(metadata["feishu_attachment"]["verification"], "user_selected_local_pdf")
        self.assertEqual((folder / "original.pdf").read_bytes(), self.pdf)
        self.assertFalse((folder / "thinking.json").exists())
        self.assertEqual(reader.read_json(folder / "feishu_metadata.json", {})["briefings"], self.source["briefings"])
        self.download.assert_not_called()
        self.assertEqual(self.queued.call_count, 1)
        self.assertFalse(self.queued.call_args.kwargs["refresh_citations"])

    def test_repeat_import_reuses_one_pdf_and_preserves_original_reading_data(self):
        status, first = self.intake()
        self.assertEqual(status, 200, first)
        folder = self.workspace / "papers" / first["paper_id"]
        annotations = {"annotations": [{"id": "note-original", "note": "  My original thought.\n"}]}
        reader.write_json(folder / "annotations.json", annotations)
        source_files = {name: (folder / name).read_bytes() for name in ("original.pdf", "annotations.json", "segments.json", "outline.json")}
        status, repeated = self.intake()
        self.assertEqual(status, 200, repeated)
        self.assertEqual(first["paper_id"], repeated["paper_id"])
        self.assertTrue(repeated["reused"])
        self.assertEqual(self.download.call_count, 1)
        self.assertEqual(len(reader.read_library_index(self.workspace)["papers"]), 1)
        self.assertEqual(source_files, {name: (folder / name).read_bytes() for name in source_files})
        self.assertFalse(Path(self.download.call_args.args[4]).exists(), "The temporary download is removed, not the registered PDF")
        self.assertEqual(reader.read_json(folder / "metadata.json", {})["original_path"], str(folder / "original.pdf"))

    def test_existing_same_pdf_with_a_different_local_title_keeps_its_identity_and_notes(self):
        existing = reader.register_uploaded_pdf(self.workspace, "previous-upload.pdf", self.pdf, title="My local title")
        folder = self.workspace / "papers" / existing["paper_id"]
        reader.write_json(folder / "annotations.json", {"annotations": [{"id": "keep", "note": "Original note"}]})
        before = (folder / "annotations.json").read_bytes()
        status, result = self.intake()
        self.assertEqual(status, 200, result)
        self.assertEqual(result["paper_id"], existing["paper_id"])
        self.assertEqual(result["metadata"]["title"], "My local title")
        self.assertEqual(before, (folder / "annotations.json").read_bytes())
        self.assertEqual(len(reader.read_library_index(self.workspace)["papers"]), 1)

    def test_changed_cloud_attachment_never_overwrites_a_linked_source(self):
        self.intake()
        before = self.snapshot()
        self.source["attachments"][0]["file_token"] = "fileReplacement"
        status, result = self.intake(file_token="fileReplacement")
        self.assertEqual(status, 400)
        self.assertIn("different PDF attachment", result["error"])
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.download.call_count, 1)

    def test_local_source_changed_after_import_is_not_silently_reused(self):
        _, result = self.intake()
        (self.workspace / "papers" / result["paper_id"] / "original.pdf").write_bytes(b"%PDF-changed")
        before = self.snapshot()
        status, error = self.intake()
        self.assertEqual(status, 400)
        self.assertIn("local PDF changed", error["error"])
        self.assertEqual(before, self.snapshot())

    def test_missing_record_wrong_attachment_and_bad_local_pdf_leave_library_unchanged(self):
        before = self.snapshot()
        status, _ = self.intake(file_token="fileUnselected")
        self.assertEqual(status, 400)
        self.local_pdf.write_bytes(b"not a PDF" + b" " * (len(self.pdf) - 9))
        status, error = self.intake(local_pdf_path=str(self.local_pdf))
        self.assertEqual(status, 400)
        self.assertIn("not a PDF", error["error"])
        self.fetch.side_effect = ValueError("The Feishu record no longer exists")
        status, error = self.intake()
        self.assertEqual(status, 400)
        self.assertIn("no longer exists", error["error"])
        self.assertEqual(before, self.snapshot())
        self.download.assert_not_called()
        self.queued.assert_not_called()

    def test_concurrent_requests_do_not_duplicate_the_import_or_download(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.intake(), range(2)))
        self.assertEqual([status for status, _ in results], [200, 200], results)
        self.assertEqual(len({result["paper_id"] for _, result in results}), 1)
        self.assertEqual(self.download.call_count, 1)
        self.assertEqual(len(reader.read_library_index(self.workspace)["papers"]), 1)

    def test_distinct_cloud_papers_with_similar_titles_do_not_use_fuzzy_identity_matching(self):
        self.source["metadata"]["title"] = "Understanding collaborative reading at scale: Experiment One"
        status, first = self.intake()
        self.assertEqual(status, 200, first)
        self.source["record_id"] = "recSecond"
        self.source["metadata"]["title"] = "Understanding collaborative reading at scale: Experiment Two"
        self.pdf += b"A distinct synthetic PDF"
        self.source["attachments"][0].update(file_token="fileSecond", size=len(self.pdf))
        status, second = self.intake(record_id="recSecond", file_token="fileSecond")
        self.assertEqual(status, 200, second)
        self.assertNotEqual(first["paper_id"], second["paper_id"])
        self.assertEqual(len(reader.read_library_index(self.workspace)["papers"]), 2)

    def test_preview_without_title_or_brief_still_allows_an_explicit_pdf_intake(self):
        self.source["metadata"]["title"] = ""
        self.source["briefings"] = {"raw text": "", "raw text_中文": ""}
        status, preview = self.request("/api/feishu/preview?reference=recSynthetic")
        self.assertEqual(status, 200)
        self.assertEqual(preview["record"]["metadata"]["title"], "")
        self.queued.assert_not_called()
        status, result = self.intake()
        self.assertEqual(status, 200, result)
        self.assertEqual(result["metadata"]["title"], "Example")
        self.assertEqual(result["metadata"]["title_source"], "filename")
        self.assertEqual(self.queued.call_count, 1)

    def test_intake_and_retry_reject_invalid_requests_without_false_success(self):
        for endpoint in ("/api/feishu/intake", "/api/processing-queue/retry"):
            status, result = self.request(endpoint, "POST", [])
            self.assertEqual(status, 400)
            self.assertFalse(result["ok"])
        status, result = self.request("/api/processing-queue/retry", "POST", {"paper_id": "missing"})
        self.assertEqual(status, 400)
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
