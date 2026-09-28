"""Progressive translation/source-first parsing with no real network or library."""

from __future__ import annotations

import argparse
import copy
import io
import json
from pathlib import Path
import shutil
import sys
import threading
import time
import unittest
from unittest import mock
import urllib.error
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paper_reader_agent as reader


class TranslationFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parent / f".translation-fixture-{uuid.uuid4().hex}"
        self.root.mkdir()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.workspace = self.root / "workspace"
        self.paper_dir = self.make_paper("paper-a")
        self.env = {"PAPER_READER_TRANSLATION_PROVIDER": "copilot"}
        self.patch(reader, "env_value", side_effect=lambda *names, default="": next((self.env[key] for key in names if key in self.env), default))
        for name in (
            "load_env_files", "agent_chat", "kimi_request", "kimi_chat", "ollama_generate",
            "update_paper_brief_from_pdf", "update_explanation_from_pdf", "ensure_takeaway_doc_skeleton",
            "metadata_with_citation", "refresh_paper_citations", "refresh_paper_videos",
            "build_presentation_flow", "render_pdf_preview_image", "serve",
        ):
            self.patch(reader, name, side_effect=AssertionError(f"Forbidden fixture call: {name}"))
        self.patch(reader.urllib.request, "urlopen", side_effect=AssertionError("No real network"))
        self.patch(reader.urllib.request, "build_opener", side_effect=AssertionError("No real network"))
        self.patch(reader.subprocess, "run", side_effect=AssertionError("No real converter/process"))
        self.patch(reader.subprocess, "Popen", side_effect=AssertionError("No real converter/process"))
        self.patch(reader, "run_mineru", side_effect=AssertionError("Converter must be stubbed"))
        self.patch(reader, "schedule_export_notes_and_annotated")
        self.manager = reader.TranslationJobManager()
        self.patch(reader, "TRANSLATION_JOBS", new=self.manager)
        self.releases: list[threading.Event] = []
        self.addCleanup(self.stop_jobs)

    def patch(self, target: object, name: str, **kwargs):
        patcher = mock.patch.object(target, name, **kwargs)
        value = patcher.start()
        self.addCleanup(patcher.stop)
        return value

    def stop_jobs(self) -> None:
        with self.manager.lock:
            self.manager.stopped = True
        for event in self.releases:
            event.set()
        self.manager.close()
        self.assertFalse(self.manager.thread and self.manager.thread.is_alive(), "Fixture worker did not stop")

    def make_paper(self, paper_id: str) -> Path:
        paper_dir = self.workspace / "papers" / paper_id
        paper_dir.mkdir(parents=True)
        self.write(paper_dir / "metadata.json", {"id": paper_id, "title": "Fixture", "read_status": "unread", "processing_mode": "deep", "custom": "preserve"})
        self.write(paper_dir / "segments.json", [
            {"id": "p-1", "kind": "paragraph", "markdown": "Source paragraph one.", "translation": "", "custom": {"keep": 1}},
            {"id": "p-2", "kind": "paragraph", "markdown": "Source paragraph two.", "translation": "", "custom": {"keep": 2}},
        ])
        self.write(paper_dir / "annotations.json", {"annotations": [{"id": "a-1", "segment_id": "p-1", "note": "PRIVATE NOTE MUST NOT BE SENT", "tags": ["question"]}]})
        self.write(paper_dir / "thinking.json", {"explain": {"content": "PRIVATE SAVED BRIEF"}, "annotations": [], "blocks": []})
        self.write(paper_dir / "takeaway_doc.json", {"blocks": [{"id": "t-1", "text": "PRIVATE HUMAN TAKEAWAY"}]})
        library = reader.read_json(self.workspace / "library.json", {"papers": []})
        library["papers"].append({"id": paper_id, "title": "Fixture", "paper_dir": str(paper_dir.relative_to(self.workspace))})
        self.write(self.workspace / "library.json", library)
        return paper_dir

    @staticmethod
    def write(path: Path, value: object) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    def state(self, paper_dir: Path | None = None) -> dict:
        return reader.translation_snapshot(paper_dir or self.paper_dir)["translation"]

    def wait_status(self, status: str, paper_dir: Path | None = None) -> dict:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            value = self.state(paper_dir)
            if value["status"] == status:
                return value
            time.sleep(0.01)
        self.fail(f"Expected {status}, got {self.state(paper_dir)}")

    def gate_model(self):
        entered = threading.Event()
        release = threading.Event()
        self.releases.append(release)

        def translate(text, config):
            entered.set()
            if not release.wait(5):
                raise AssertionError("Fixture model gate timed out")
            return "译文：" + text

        return self.patch(reader, "translate_text", side_effect=translate), entered, release

    def request(self, path: str, *, data: object = None, method: str = "GET", headers: dict | None = None, body: bytes | None = None):
        content = body if body is not None else (json.dumps(data).encode("utf-8") if data is not None else b"")
        handler = object.__new__(reader.ReaderHandler)
        handler.workspace = self.workspace
        handler.path = path
        handler.command = method
        handler.request_version = "HTTP/1.1"
        handler.requestline = f"{method} {path} HTTP/1.1"
        handler.headers = {"Content-Length": str(len(content)), **(headers or {})}
        handler.rfile = io.BytesIO(content)
        handler.wfile = io.BytesIO()
        handler.log_message = lambda *args: None
        with mock.patch.object(reader.traceback, "print_exc"):
            getattr(handler, f"do_{method}")()
        header, _, payload = handler.wfile.getvalue().partition(b"\r\n\r\n")
        status = int(header.split(b"\r\n", 1)[0].split()[1])
        return status, json.loads(payload)


class TranslationJobTests(TranslationFixture):
    def test_post_returns_before_model_finishes_and_same_paper_deduplicates(self) -> None:
        model, entered, release = self.gate_model()
        status, first = self.request("/api/papers/paper-a/translate", method="POST", data={"automatic": True})
        self.assertEqual(status, 200)
        self.assertTrue(entered.wait(2))
        self.assertFalse(release.is_set())
        status, second = self.request("/api/papers/paper-a/translate", method="POST", data={"automatic": True})
        self.assertEqual(status, 200)
        self.assertEqual(first["translation"]["job_id"], second["translation"]["job_id"])
        self.assertEqual(model.call_count, 1)
        self.assertEqual(reader.load_segments(self.paper_dir)[0]["translation"], "")
        release.set()
        self.assertEqual(self.wait_status("ready")["completed"], 2)

    def test_incremental_updates_are_persisted_before_publication(self) -> None:
        second_started = threading.Event()
        release = threading.Event()
        self.releases.append(release)

        def translate(text, config):
            if "two" in text:
                second_started.set()
                self.assertTrue(release.wait(5))
            return "完整译文 " + text

        self.patch(reader, "translate_text", side_effect=translate)
        _, initial = self.request("/api/papers/paper-a/translate", method="POST", data={})
        self.assertTrue(second_started.wait(2))
        job = initial["translation"]["job_id"]
        status, data = self.request(f"/api/papers/paper-a/translation?job_id={job}&after=0")
        self.assertEqual(status, 200)
        self.assertEqual(data["translation"]["completed"], 1)
        self.assertEqual(data["updates"], [{"id": "p-1", "markdown": "Source paragraph one.", "translation": "完整译文 Source paragraph one."}])
        self.assertEqual(reader.load_segments(self.paper_dir)[0]["translation"], data["updates"][0]["translation"])
        after = data["translation"]["revision"]
        _, unchanged = self.request(f"/api/papers/paper-a/translation?job_id={job}&after={after}")
        self.assertEqual(unchanged["updates"], [])
        release.set()
        self.wait_status("ready")
        _, changed = self.request(f"/api/papers/paper-a/translation?job_id={job}&after={after}")
        self.assertEqual([item["id"] for item in changed["updates"]], ["p-2"])
        _, all_data = self.request("/api/papers/paper-a/translation?job_id=stale&after=999")
        self.assertEqual(len(all_data["updates"]), 2)

    def test_pause_keeps_completed_work_and_automatic_reopen_does_not_resume(self) -> None:
        second_started = threading.Event()
        release = threading.Event()
        self.releases.append(release)

        def translate(text, config):
            if "two" in text:
                second_started.set()
                self.assertTrue(release.wait(5))
            return "译 " + text

        model = self.patch(reader, "translate_text", side_effect=translate)
        self.manager.submit("paper-a", self.paper_dir, {})
        self.assertTrue(second_started.wait(2))
        paused = self.manager.submit("paper-a", self.paper_dir, {"action": "pause"})
        self.assertEqual(paused["status"], "paused")
        self.assertEqual(paused["completed"], 1)
        self.assertEqual(self.manager.submit("paper-a", self.paper_dir, {"automatic": True})["status"], "paused")
        release.set()
        resumed = self.manager.submit("paper-a", self.paper_dir, {"action": "resume"})
        self.assertNotEqual(resumed["job_id"], paused["job_id"])
        self.wait_status("ready")
        self.assertEqual(model.call_count, 3)
        self.assertEqual(reader.load_segments(self.paper_dir)[0]["translation"], "译 Source paragraph one.")

    def test_failed_job_is_visible_and_requires_manual_retry(self) -> None:
        model = self.patch(reader, "translate_text", side_effect=RuntimeError("Fixture model unavailable"))
        self.manager.submit("paper-a", self.paper_dir, {"automatic": True})
        failure = self.wait_status("failed")
        self.assertIn("Fixture model unavailable", failure["error"])
        self.assertEqual(self.manager.submit("paper-a", self.paper_dir, {"automatic": True}), failure)
        self.assertEqual(model.call_count, 1)
        model.side_effect = lambda text, config: "译文"
        self.manager.submit("paper-a", self.paper_dir, {"action": "resume"})
        self.wait_status("ready")
        self.assertEqual(model.call_count, 3)

    def test_restart_get_is_read_only_then_post_resumes_missing_segments(self) -> None:
        segments = reader.load_segments(self.paper_dir)
        segments[0]["translation"] = "持久化的人工翻译  "
        self.write(self.paper_dir / "segments.json", segments)
        self.write(self.paper_dir / "translation_state.json", {
            "version": 1, "job_id": "old-process", "status": "processing", "revision": 3,
            "backend": "copilot:gpt-4.1", "fingerprint": reader.translation_fingerprint(segments),
        })
        before = (self.paper_dir / "translation_state.json").read_bytes()
        status, data = self.request("/api/papers/paper-a/translation")
        self.assertEqual(status, 200)
        self.assertEqual(data["translation"]["status"], "interrupted")
        self.assertEqual((self.paper_dir / "translation_state.json").read_bytes(), before)
        self.assertIsNone(self.manager.thread)
        model = self.patch(reader, "translate_text", return_value="新译文")
        self.manager.submit("paper-a", self.paper_dir, {"automatic": True})
        self.wait_status("ready")
        self.assertEqual(model.call_count, 1)
        self.assertEqual(reader.load_segments(self.paper_dir)[0], segments[0])

    def test_existing_translations_metadata_annotations_and_unknown_fields_are_preserved(self) -> None:
        segments = reader.load_segments(self.paper_dir)
        segments[0]["translation"] = "  Human-corrected translation\n"
        self.write(self.paper_dir / "segments.json", segments)
        protected = ["annotations.json", "thinking.json", "takeaway_doc.json", "metadata.json"]
        original = {name: (self.paper_dir / name).read_bytes() for name in protected}
        model = self.patch(reader, "translate_text", return_value="新增译文")
        self.manager.submit("paper-a", self.paper_dir, {"automatic": True, "force": True})
        self.wait_status("ready")
        latest = reader.load_segments(self.paper_dir)
        self.assertEqual(latest[0], segments[0])
        self.assertEqual(latest[1]["custom"], segments[1]["custom"])
        self.assertEqual(model.call_count, 1)
        for name, content in original.items():
            self.assertEqual((self.paper_dir / name).read_bytes(), content)
        self.assertNotIn("PRIVATE", model.call_args.args[0])

    def test_source_change_during_request_rejects_stale_result(self) -> None:
        _, entered, release = self.gate_model()
        self.manager.submit("paper-a", self.paper_dir, {})
        self.assertTrue(entered.wait(2))
        segments = reader.load_segments(self.paper_dir)
        segments[0]["markdown"] = "Externally corrected source."
        segments[0]["new_field"] = "preserved"
        self.write(self.paper_dir / "segments.json", segments)
        release.set()
        self.assertIn("Source changed", self.wait_status("failed")["error"])
        self.assertEqual(reader.load_segments(self.paper_dir), segments)

    def test_translation_correction_during_request_is_never_overwritten(self) -> None:
        _, entered, release = self.gate_model()
        self.manager.submit("paper-a", self.paper_dir, {})
        self.assertTrue(entered.wait(2))
        segments = reader.load_segments(self.paper_dir)
        segments[0]["translation"] = "实时人工更正"
        self.write(self.paper_dir / "segments.json", segments)
        release.set()
        self.assertIn("edited", self.wait_status("failed")["error"])
        self.assertEqual(reader.load_segments(self.paper_dir), segments)

    def test_other_edits_during_model_request_survive_successful_merge(self) -> None:
        _, entered, release = self.gate_model()
        self.manager.submit("paper-a", self.paper_dir, {})
        self.assertTrue(entered.wait(2))
        segments = reader.load_segments(self.paper_dir)
        segments[0]["custom"] = {"new_user_field": "retain"}
        self.write(self.paper_dir / "segments.json", segments)
        metadata = reader.read_json(self.paper_dir / "metadata.json", {})
        metadata.update({"read_status": "read", "title": "User title changed while translating"})
        self.write(self.paper_dir / "metadata.json", metadata)
        metadata_bytes = (self.paper_dir / "metadata.json").read_bytes()
        release.set()
        self.wait_status("ready")
        self.assertEqual(reader.load_segments(self.paper_dir)[0]["custom"], {"new_user_field": "retain"})
        self.assertEqual((self.paper_dir / "metadata.json").read_bytes(), metadata_bytes)

    def test_deleted_paper_is_not_recreated_by_inflight_translation(self) -> None:
        _, entered, release = self.gate_model()
        self.manager.submit("paper-a", self.paper_dir, {})
        self.assertTrue(entered.wait(2))
        shutil.rmtree(self.paper_dir)
        release.set()
        deadline = time.monotonic() + 2
        while self.manager.jobs and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertFalse(self.manager.jobs)
        self.assertFalse(self.paper_dir.exists())

    def test_appendix_text_and_heading_are_translated_but_image_only_is_skipped(self) -> None:
        segments = [
            {"id": "a", "kind": "heading", "markdown": "# Appendix A"},
            {"id": "b", "markdown": "The complete appendix text."},
            {"id": "c", "markdown": "![image](assets/image.png)"},
        ]
        self.write(self.paper_dir / "segments.json", segments)
        model = self.patch(reader, "translate_text", return_value="译文")
        self.manager.submit("paper-a", self.paper_dir, {})
        status = self.wait_status("ready")
        self.assertEqual((status["completed"], status["total"]), (2, 2))
        self.assertEqual([call.args[0] for call in model.call_args_list], ["# Appendix A", "The complete appendix text."])
        self.assertEqual(reader.load_segments(self.paper_dir)[2], segments[2])

    def test_other_papers_queue_without_concurrent_model_requests(self) -> None:
        model, entered, release = self.gate_model()
        self.manager.submit("paper-a", self.paper_dir, {})
        self.assertTrue(entered.wait(2))
        others = [self.make_paper(f"paper-{index}") for index in range(4)]
        for paper in others:
            self.manager.submit(paper.name, paper, {})
        self.assertEqual(model.call_count, 1)
        self.assertEqual(len(self.manager.jobs), 5)
        release.set()
        for paper in [self.paper_dir, *others]:
            self.wait_status("ready", paper)
        self.assertEqual(model.call_count, 10)

    def test_unknown_job_and_external_edits_refresh_cached_translations(self) -> None:
        self.patch(reader, "translate_text", return_value="AI translation")
        self.manager.submit("paper-a", self.paper_dir, {})
        state = self.wait_status("ready")
        segments = reader.load_segments(self.paper_dir)
        segments[0]["translation"] = "Externally edited translation"
        self.write(self.paper_dir / "segments.json", segments)
        _, payload = self.request(f"/api/papers/paper-a/translation?job_id={state['job_id']}&after={state['revision']}")
        self.assertEqual(payload["updates"][0]["translation"], "Externally edited translation")

    def test_manual_force_can_replace_but_pause_does_not_erase_originals(self) -> None:
        segments = reader.load_segments(self.paper_dir)
        for item in segments:
            item["translation"] = "Original translation"
        self.write(self.paper_dir / "segments.json", segments)
        _, entered, release = self.gate_model()
        self.manager.submit("paper-a", self.paper_dir, {"force": True})
        self.assertTrue(entered.wait(2))
        self.assertEqual(reader.load_segments(self.paper_dir), segments)
        release.set()
        self.wait_status("ready")
        self.assertTrue(all(item["translation"].startswith("译文：") for item in reader.load_segments(self.paper_dir)))

    def test_empty_result_fails_without_persisting_partial_data(self) -> None:
        self.patch(reader, "translate_text", return_value=" \n ")
        original = (self.paper_dir / "segments.json").read_bytes()
        self.manager.submit("paper-a", self.paper_dir, {})
        self.assertIn("empty", self.wait_status("failed")["error"])
        self.assertEqual((self.paper_dir / "segments.json").read_bytes(), original)

    def test_repeated_ready_or_waiting_start_is_idempotent_and_new_source_is_detected(self) -> None:
        model = self.patch(reader, "translate_text", return_value="译文")
        self.manager.submit("paper-a", self.paper_dir, {})
        completed = self.wait_status("ready")
        self.assertEqual(self.manager.submit("paper-a", self.paper_dir, {"automatic": True}), completed)
        self.assertEqual(model.call_count, 2)
        segments = reader.load_segments(self.paper_dir)
        segments.append({"id": "p-new", "markdown": "New externally added source."})
        self.write(self.paper_dir / "segments.json", segments)
        self.assertEqual(self.state()["status"], "not_started")
        self.manager.submit("paper-a", self.paper_dir, {"automatic": True})
        self.wait_status("ready")
        self.assertEqual(model.call_count, 3)
        empty = self.make_paper("empty")
        self.write(empty / "segments.json", [])
        waiting = self.manager.submit("empty", empty, {"automatic": True})
        self.assertEqual(self.manager.submit("empty", empty, {"automatic": True}), waiting)

    def test_gets_report_config_progress_without_creating_state_or_starting_worker(self) -> None:
        for path in ("/api/library", "/api/papers/paper-a", "/api/papers/paper-a/translation"):
            status, data = self.request(path)
            self.assertEqual(status, 200, data)
            if "translation_config" in data:
                self.assertEqual(data["translation_config"], {"auto_start": True, "provider": "copilot", "model": "gpt-4.1"})
        self.assertFalse((self.paper_dir / "translation_state.json").exists())
        self.assertIsNone(self.manager.thread)
        status, _ = self.request("/api/papers/paper-a/translation?after=bad")
        self.assertEqual(status, 400)

    def test_legacy_install_is_not_opted_in_by_automatic_post(self) -> None:
        self.env.clear()
        model = self.patch(reader, "translate_text", return_value="unused")
        self.assertFalse(reader.translation_config()["auto_start"])
        status, _ = self.request("/api/papers/paper-a/translate", method="POST", data={"automatic": True})
        self.assertEqual(status, 200)
        model.assert_not_called()
        self.assertFalse((self.paper_dir / "translation_state.json").exists())


class TranslationMediaTests(TranslationFixture):
    def test_mixed_figures_translate_prose_and_captions_without_sending_or_saving_images(self) -> None:
        source = "Original prose. ![Diagram](images/figure.jpg) Figure 2: The workflow."
        self.write(self.paper_dir / "segments.json", [{"id": "p-1", "markdown": source, "translation": ""}])
        model = self.patch(reader, "translate_text", return_value="原文说明。 ![Diagram](images/figure.jpg) 图2：工作流程。")
        self.manager.submit("paper-a", self.paper_dir, {})
        self.wait_status("ready")
        sent = model.call_args.args[0]
        self.assertIn("Original prose.", sent)
        self.assertIn("Figure 2: The workflow.", sent)
        self.assertNotIn("![", sent)
        self.assertNotIn("images/figure.jpg", sent)
        saved = reader.load_segments(self.paper_dir)[0]
        self.assertEqual(saved["markdown"], source)
        self.assertIn("图2：工作流程。", saved["translation"])
        self.assertNotIn("![", saved["translation"])

    def test_image_only_segments_and_image_only_old_translations_are_not_text(self) -> None:
        for markdown in (
            "![](figure.jpg)", "![](one.png) ![](two.pdf)",
            '<img src="figure.jpg" alt="diagram" />',
            "![Panel](images/panel(1).png)",
        ):
            with self.subTest(markdown=markdown):
                self.assertFalse(reader.should_translate_segment({"markdown": markdown}))
                self.assertFalse(reader.has_translation({"translation": markdown}))

    def test_real_text_tables_keep_structure_numbers_and_text_but_not_embedded_images(self) -> None:
        sources = [
            "| Method | Score |\n|---|---|\n| Workflow ![](figure.png) | 0.87 |",
            '<table><tr><th>Method</th><th>Score</th></tr><tr><td>Workflow<img src="figure.png"></td><td>0.87</td></tr></table>',
        ]
        for source in sources:
            with self.subTest(source=source):
                text = reader.translation_source_for_segment({"kind": "table", "markdown": source})
                self.assertIn("Method", text)
                self.assertIn("Workflow", text)
                self.assertIn("0.87", text)
                self.assertNotIn("figure.png", text)
                self.assertEqual(text.count("|"), source.count("|"))
                self.assertEqual(text.count("<td>"), source.count("<td>"))

    def test_image_only_model_output_fails_instead_of_claiming_a_caption_was_translated(self) -> None:
        self.write(self.paper_dir / "segments.json", [{"id": "p-1", "markdown": "Figure 2: The workflow.", "translation": ""}])
        self.patch(reader, "translate_text", return_value="![](figure.png)")
        self.manager.submit("paper-a", self.paper_dir, {})
        failure = self.wait_status("failed")
        self.assertTrue(failure["error"])
        self.assertEqual(reader.load_segments(self.paper_dir)[0]["translation"], "")

    def test_derived_reading_copies_hide_old_duplicate_images_without_rewriting_raw_data(self) -> None:
        segments = [
            {"id": "p-1", "markdown": "![](figure.jpg) Figure 2: The workflow.", "translation": "![](figure.jpg) 图2：工作流程。"},
            {"id": "p-2", "markdown": "![](table-scan.jpg)", "translation": "![](table-scan.jpg)"},
        ]
        self.write(self.paper_dir / "segments.json", segments)
        before = {name: (self.paper_dir / name).read_bytes() for name in ("segments.json", "annotations.json", "thinking.json")}
        reader_copy = reader.make_reader_markdown(segments, "synthetic.pdf")
        paper_copy = reader.make_source_grounded_paper_markdown({}, segments, {"blocks": []}, {"terms": []}, "synthetic.pdf")
        reader.write_notes_and_annotated(self.paper_dir)
        annotated = (self.paper_dir / "annotated.md").read_text(encoding="utf-8")
        for text in (reader_copy, paper_copy, annotated):
            self.assertEqual(text.count("![](figure.jpg)"), 1)
            self.assertEqual(text.count("![](table-scan.jpg)"), 1)
            self.assertIn("图2：工作流程。", text)
        self.assertNotIn("<!-- zh:p-2 -->", reader_copy)
        self.assertEqual(before, {name: (self.paper_dir / name).read_bytes() for name in before})
        self.assertEqual(reader.load_reading_data(self.paper_dir)["files"]["segments.json"], segments)


class TranslationMathTests(TranslationFixture):
    FORMULA = "$$\n" + r"s_i = \frac{\sum_{j=1}^{n} w_{ij} x_j}{\sum_{j=1}^{n} w_{ij}} \tag{1}" + "\n$$"

    def test_math_spans_are_ordered_nonoverlapping_and_do_not_double_match(self) -> None:
        parts = [
            "$x_i$", self.FORMULA,
            r"\[\begin{aligned}x&=1\\y&=2\end{aligned}\]",
            r"\begin{gather}a=b\\c=d\end{gather}",
        ]
        text = "中文 $price is not math\n\n" + "\n\n".join(parts) + "\n\n`$$not_math$$`"
        spans = reader.math_spans(text)
        self.assertEqual([text[span["start"]:span["end"]] for span in spans], parts)
        self.assertEqual([span["mode"] for span in spans], ["inline", "display", "display", "display"])
        self.assertEqual(spans[0]["latex"], "x_i")
        self.assertEqual(spans[-1]["latex"], parts[-1])
        self.assertTrue(all(left["end"] <= right["start"] for left, right in zip(spans, spans[1:])))

    def test_standalone_math_and_attached_equation_numbers_do_not_need_translation(self) -> None:
        sources = [
            self.FORMULA, "$x_i$", "$ x_i $", "$ x = 1 $", r"\(x = 1\)", r"\[x = 1\]",
            "$x$, $y$.", "$x$, $y$ (1)", r"$$x = 1$$ (1)", r"\[x=1\]\tag*{A.1}",
            "\\[x=1\\]\n(A.1)", "\\[x=1\\]\r\n(1a)",
            "\u00a0$x$\u00a0", "\u00a0$$x=1$$\u00a0(1)",
            "![](figure.png)\n\n" + self.FORMULA,
        ]
        environments = (
            "equation", "equation*", "align", "align*", "alignat", "alignat*",
            "gather", "gather*", "multline", "multline*", "eqnarray", "eqnarray*",
            "aligned", "alignedat", "gathered", "multlined", "split", "array",
            "matrix", "pmatrix", "bmatrix", "Bmatrix", "vmatrix", "Vmatrix",
            "smallmatrix", "cases", "displaymath",
        )
        sources.extend(r"\begin{" + name + r"}x&=1\\y&=2\end{" + name + "}" for name in environments)
        for source in sources:
            with self.subTest(source=source):
                segment = {"markdown": source, "translation": source}
                self.assertEqual(reader.translation_source_for_segment(segment), "")
                self.assertEqual(reader.translation_text_for_segment(segment), "")
                self.assertFalse(reader.should_translate_segment(segment))
                self.assertFalse(reader.has_translation(segment))
                self.assertEqual(reader.translation_counts([segment]), (0, 0))

    def test_mixed_source_keeps_prose_inline_notation_and_separate_numbered_paragraphs(self) -> None:
        source = (
            "The score uses $x_i$ and \\(n\\), costing $5 to $10.\n\n"
            + self.FORMULA + " (1)\n\n"
            "Here \\(w_{ij}\\) is a weight.\n\n(2) This is a numbered paragraph."
        )
        segment = {"markdown": source}
        sent = reader.translation_source_for_segment(segment)
        self.assertIn("The score uses $x_i$ and \\(n\\), costing $5 to $10.", sent)
        self.assertIn("Here \\(w_{ij}\\) is a weight.", sent)
        self.assertIn("(2) This is a numbered paragraph.", sent)
        self.assertNotIn("\\sum", sent)
        self.assertNotIn("\\tag", sent)
        self.assertNotIn("(1)", sent)
        self.assertEqual(segment["markdown"], source)
        self.assertTrue(reader.should_translate_segment(segment))

    def test_prose_currency_escaped_delimiters_code_and_malformed_math_are_not_swallowed(self) -> None:
        sources = [
            "The variables x and y are useful.", "The variable $x$ is useful.",
            "$5 to $10", "$10-$20", "$5.00", r"\$x=1\$", r"\$\$x=1\$\$",
            r"\\[x=1\\]", "Prose $ x $ not math markup.", "$x=1", "$$x=1", r"\[x=1", r"\(x=1",
            "$$$x$$$", r"$$x_{1$$", r"$$\frac{x}{1$$", r"$$\left(x$$",
            r"\[x+\[y\]", r"\begin{align}x&=1", r"\begin{align}x&=1\end{gather}",
            "`$$x=1$$`", "``before ` $x$ after``", "```latex\n$$x=1$$\n```",
            "~~~math\n\\[x=1\\]\n~~~", "<code>$$x=1$$</code>",
            "<pre>\n$$x=1$$\n</pre>", "    $$x=1$$", "\t$$x=1$$",
            "<!-- $$x=1$$ -->", "$$x=1$$\n\n(1)",
        ]
        for source in sources:
            with self.subTest(source=source):
                segment = {"markdown": source}
                if source == "$$x=1$$\n\n(1)":
                    self.assertEqual(reader.translation_source_for_segment(segment), "(1)")
                else:
                    self.assertEqual(reader.translation_source_for_segment(segment), source.strip())
                self.assertTrue(reader.should_translate_segment(segment))

    def test_explicit_code_kind_keeps_literal_math_with_existing_image_filtering(self) -> None:
        for text, expected in (
            ("$$x=y$$", "$$x=y$$"),
            ("$$x=y$$ where $x$ is a score.", "$$x=y$$ where $x$ is a score."),
            ("$$x=y$$ ![](figure.png)", "$$x=y$$"),
            ('$$x=y$$ <img src="figure.png">', "$$x=y$$"),
            ("![](figure.png)", ""),
        ):
            with self.subTest(text=text):
                segment = {"id": "p-code", "kind": "code", "markdown": text, "translation": text}
                before = copy.deepcopy(segment)
                self.assertEqual(reader.translation_source_for_segment(segment), expected)
                self.assertEqual(reader.translation_text_for_segment(segment), expected)
                self.assertEqual(reader.translation_text_for_segment(segment, text), expected)
                self.assertEqual(reader.should_translate_segment(segment), bool(expected))
                self.assertEqual(reader.has_translation(segment), bool(expected))
                self.assertEqual(reader.translation_counts([segment]), (int(bool(expected)), int(bool(expected))))
                self.assertEqual(segment, before)

    def test_explicit_code_literal_math_reaches_worker_and_is_saved(self) -> None:
        segment = {"id": "p-code", "kind": "code", "markdown": "$$x=y$$", "translation": ""}
        self.write(self.paper_dir / "segments.json", [segment])
        model = self.patch(reader, "translate_text", return_value="$$x=y$$")
        self.manager.submit("paper-a", self.paper_dir, {})
        state = self.wait_status("ready")
        self.assertEqual((state["completed"], state["total"]), (1, 1))
        model.assert_called_once()
        self.assertEqual(model.call_args.args[0], "$$x=y$$")
        self.assertEqual(reader.load_segments(self.paper_dir), [{**segment, "translation": "$$x=y$$"}])

    def test_math_only_legacy_translation_keeps_explanations_without_rewriting_data(self) -> None:
        segment = {
            "id": "p-0112", "markdown": self.FORMULA,
            "translation": self.FORMULA + "\n\n式中 $n$ 表示参与者数量。",
            "custom": {"untouched": True},
        }
        before = copy.deepcopy(segment)
        self.assertEqual(reader.translation_text_for_segment(segment), "式中 $n$ 表示参与者数量。")
        self.assertEqual(reader.translation_text_for_segment(segment, r"\(z=2\) 另一种解释。"), r"\(z=2\) 另一种解释。")
        self.assertEqual(reader.translation_text_for_segment(segment, ""), "")
        self.assertTrue(reader.has_translation(segment))
        self.assertEqual(segment, before)

    def test_math_only_sources_keep_inline_notation_and_unmatched_displays_in_explanations(self) -> None:
        for source in ("$$x=y$$", r"\[x=y\]", "$x=y$", r"\(x=y\)"):
            with self.subTest(source=source):
                segment = {"markdown": source, "translation": "$$x=y$$ where $x$ is a score."}
                before = copy.deepcopy(segment)
                self.assertEqual(reader.translation_text_for_segment(segment), "where $x$ is a score.")
                translation = "\\[x=y\\] where \\(x\\) is a score.\n\n$$z=2$$"
                self.assertEqual(reader.translation_text_for_segment(segment, translation), "where \\(x\\) is a score.\n\n$$z=2$$")
                inline_explanation = "Use $x=y$ with $x$ as a score.\n\n$$z=2$$"
                self.assertEqual(reader.translation_text_for_segment(segment, inline_explanation), inline_explanation)
                for math_only in ("$$z=2$$", r"\(z=2\)", "$$x=y$$\n\n$$z=2$$"):
                    self.assertEqual(reader.translation_text_for_segment(segment, math_only), "")
                self.assertEqual(segment, before)

    def test_mixed_translation_removes_only_matching_display_math(self) -> None:
        source_math = r"$$x = \frac{a + b}{c} + \left( y \right) \tag{1}$$"
        segment = {"markdown": "The score is:\n\n" + source_math + "\n\nwhere $a$ is input."}
        variants = [
            r"$$ x=\frac{a+b}{c}+(y) $$",
            "\\[\nx=\\frac {a+b}{c}+(y)\\tag*{2}\\label{eq:score}\n\\]",
            r"\begin{equation*}x=\frac{a+b}{c}+(y)\end{equation*}",
            r"\begin{gather*}x=\frac{a+b}{c}+(y)\end{gather*}",
            r"$$\begin{aligned}x=\frac{a+b}{c}+(y)\end{aligned}\tag{2}$$",
        ]
        for formula in variants:
            with self.subTest(formula=formula):
                translation = "得分为：\n\n" + formula + " (1)\n\n其中 $a$ 是输入。\n\n$$z=2$$"
                result = reader.translation_text_for_segment(segment, translation)
                self.assertIn("得分为：", result)
                self.assertIn("其中 $a$ 是输入。", result)
                self.assertIn("$$z=2$$", result)
                self.assertNotIn("\\frac", result)
                self.assertNotIn("(1)", result)
        inline = r"$x=\frac{a+b}{c}+(y)$"
        self.assertEqual(reader.translation_text_for_segment(segment, inline), "")
        self.assertEqual(reader.translation_text_for_segment(segment, r"$ x = \frac{a + b}{c} + (y) $"), "")
        self.assertEqual(reader.translation_text_for_segment(segment, r"\(x=\frac{a+b}{c}+(y)\) (1)"), "")
        self.assertEqual(reader.translation_text_for_segment(segment, "仍保留 " + inline + " 这一行内表达式。"), "仍保留 " + inline + " 这一行内表达式。")
        self.assertEqual(reader.translation_text_for_segment({"markdown": r"Prose. \begin{gather}x=1\end{gather}"}, "$x=1$"), "")

    def test_math_comparison_does_not_equate_different_commands_text_or_parentheses(self) -> None:
        pairs = [
            (r"\alpha x", r"\alphax"),
            (r"\text{a b}", r"\text{ab}"),
            (r"\left(x\right)", "x"),
            ("x+y", "x-y"),
            (r"\begin{matrix}a&b\end{matrix}", r"\begin{cases}a&b\end{cases}"),
            (r"\begin{aligned}x\end{aligned}\begin{aligned}y\end{aligned}", "xy"),
        ]
        for source, translated in pairs:
            with self.subTest(source=source, translated=translated):
                segment = {"markdown": "Prose.\n\n$$" + source + "$$"}
                translation = "\\[" + translated + "\\]"
                self.assertEqual(reader.translation_text_for_segment(segment, translation), translation)
        segment = {"markdown": r"Prose. $$\left\{x\right\}$$"}
        self.assertEqual(reader.translation_text_for_segment(segment, r"\[\{ x \}\]"), "")

    def test_counts_exclude_standalone_math_and_do_not_credit_duplicate_only_translations(self) -> None:
        segments = [
            {"markdown": self.FORMULA, "translation": self.FORMULA},
            {"markdown": "A score.\n\n$$x=1$$", "translation": r"\(x=1\)"},
            {"markdown": "A score.\n\n$$x=1$$", "translation": "得分。\n\n$$x=1$$"},
            {"markdown": "![](figure.png)", "translation": "![](figure.png)"},
        ]
        self.assertEqual(reader.translation_counts(segments), (1, 2))

    def test_math_only_jobs_including_force_and_old_resumes_make_no_model_calls(self) -> None:
        segments = [
            {"id": "p-0112", "markdown": self.FORMULA, "translation": self.FORMULA, "custom": {"keep": 1}},
            {"id": "p-inline", "markdown": r"\(x=1\)", "translation": ""},
        ]
        self.write(self.paper_dir / "segments.json", segments)
        (self.paper_dir / "notes.md").write_text("Original user notes.\n", encoding="utf-8")
        protected = ("segments.json", "annotations.json", "notes.md", "thinking.json", "takeaway_doc.json")
        before = {name: (self.paper_dir / name).read_bytes() for name in protected}
        model = self.patch(reader, "translate_text", side_effect=AssertionError("Math must not reach a model"))
        for data in ({}, {"force": True}, {"automatic": True, "force": True}):
            state = self.manager.submit("paper-a", self.paper_dir, data)
            self.assertEqual((state["status"], state["completed"], state["total"]), ("ready", 0, 0))
        for expected_markdown in (self.FORMULA, "An obsolete prose snapshot."):
            pending = [{"id": "p-0112", "markdown": expected_markdown, "translation": self.FORMULA}]
            self.write(self.paper_dir / "translation_state.json", {"status": "paused", "job_id": "old", "force_pending": pending})
            state = self.manager.submit("paper-a", self.paper_dir, {"action": "resume"})
            self.assertEqual(state["status"], "ready")
            self.assertEqual(reader.read_json(self.paper_dir / "translation_state.json", {})["force_pending"], [])
        model.assert_not_called()
        self.assertIsNone(self.manager.thread)
        self.assertEqual(before, {name: (self.paper_dir / name).read_bytes() for name in protected})

    def test_already_queued_legacy_force_is_rechecked_before_calling_model(self) -> None:
        segment = {"id": "p-0112", "markdown": self.FORMULA, "translation": self.FORMULA}
        self.write(self.paper_dir / "segments.json", [segment])
        self.write(self.paper_dir / "translation_state.json", {
            "status": "queued", "job_id": "old", "config": reader.translation_config(), "force_pending": [segment],
        })
        original = (self.paper_dir / "segments.json").read_bytes()
        model = self.patch(reader, "translate_text", side_effect=AssertionError("Math must not reach a model"))
        self.assertFalse(self.manager._step(self.paper_dir.resolve(), "old"))
        state = reader.read_json(self.paper_dir / "translation_state.json", {})
        self.assertEqual((state["status"], state["force_pending"]), ("ready", []))
        model.assert_not_called()
        self.assertEqual((self.paper_dir / "segments.json").read_bytes(), original)

    def test_resumed_force_keeps_eligible_work_but_skips_legacy_math(self) -> None:
        segments = [
            {"id": "p-math", "markdown": self.FORMULA, "translation": self.FORMULA},
            {"id": "p-prose", "markdown": "Original prose.", "translation": "Previous translation."},
        ]
        self.write(self.paper_dir / "segments.json", segments)
        self.write(self.paper_dir / "translation_state.json", {"status": "paused", "force_pending": segments})
        model = self.patch(reader, "translate_text", return_value="更新后的译文。")
        self.manager.submit("paper-a", self.paper_dir, {"action": "resume"})
        state = self.wait_status("ready")
        self.assertEqual((state["completed"], state["total"]), (1, 1))
        self.assertEqual([call.args[0] for call in model.call_args_list], ["Original prose."])
        self.assertEqual(reader.load_segments(self.paper_dir)[0], segments[0])
        self.assertEqual(reader.read_json(self.paper_dir / "translation_state.json", {})["force_pending"], [])

    def test_worker_omits_display_input_and_saves_only_sanitized_new_output(self) -> None:
        segments = [
            {"id": "p-0112", "markdown": self.FORMULA, "translation": self.FORMULA},
            {"id": "p-mixed", "markdown": "The score uses $x$.\n\n" + self.FORMULA, "translation": "", "custom": 7},
        ]
        self.write(self.paper_dir / "segments.json", segments)
        model = self.patch(reader, "translate_text", return_value="得分使用 $x$。\n\n" + self.FORMULA + "\n\n额外说明。\n\n$$z=2$$")
        self.manager.submit("paper-a", self.paper_dir, {})
        self.assertEqual(self.wait_status("ready")["total"], 1)
        model.assert_called_once()
        self.assertEqual(model.call_args.args[0], "The score uses $x$.")
        saved = reader.load_segments(self.paper_dir)
        self.assertEqual(saved[0], segments[0])
        self.assertEqual(saved[1]["markdown"], segments[1]["markdown"])
        self.assertEqual(saved[1]["custom"], 7)
        self.assertNotIn("\\sum", saved[1]["translation"])
        self.assertIn("得分使用 $x$。", saved[1]["translation"])
        self.assertIn("额外说明。", saved[1]["translation"])
        self.assertIn("$$z=2$$", saved[1]["translation"])

    def test_empty_invalid_and_duplicate_only_worker_results_still_fail(self) -> None:
        model = self.patch(reader, "translate_text")
        for index, result in enumerate((None, {}, [], 1, "", " \n ", "$$x=1$$", r"\(x=1\)", "![](figure.png)\n$$x=1$$")):
            with self.subTest(result=result):
                paper_dir = self.make_paper(f"invalid-{index}")
                self.write(paper_dir / "segments.json", [{"id": "p-1", "markdown": "Prose.\n\n$$x=1$$", "translation": ""}])
                original = (paper_dir / "segments.json").read_bytes()
                model.return_value = result
                self.manager.submit(paper_dir.name, paper_dir, {})
                state = self.wait_status("failed", paper_dir)
                self.assertIn("no translation was saved", state["error"])
                self.assertEqual((state["completed"], state["total"]), (0, 1))
                self.assertEqual((paper_dir / "segments.json").read_bytes(), original)

    def test_old_ready_state_does_not_prevent_translating_missing_prose(self) -> None:
        segments = [{"id": "p-1", "markdown": "Prose.\n\n$$x=1$$", "translation": "$$x=1$$"}]
        self.write(self.paper_dir / "segments.json", segments)
        self.write(self.paper_dir / "translation_state.json", {"status": "ready", "fingerprint": reader.translation_fingerprint(segments)})
        model = self.patch(reader, "translate_text", return_value="说明。")
        self.assertEqual(self.state()["status"], "not_started")
        self.manager.submit("paper-a", self.paper_dir, {"automatic": True})
        self.wait_status("ready")
        model.assert_called_once()

    def test_all_reading_copies_show_equations_once_and_raw_reading_data_stays_lossless(self) -> None:
        segments = [
            {"id": "p-0112", "markdown": self.FORMULA, "translation": self.FORMULA},
            {"id": "p-2", "markdown": "Prose.\n\n$$y=2\\tag{2}$$", "translation": "解释。\n\n\\[y=2\\]"},
            {"id": "p-3", "markdown": "More prose.\n\n$$z=3$$", "translation": "说明 $z$。\n\n$$u=4$$"},
            {"id": "p-4", "markdown": "$$v=4$$", "translation": "$$v=4$$\n\n额外的解释，其中 $v$ 是得分。\n\n$$q=6$$"},
            {"id": "p-5", "markdown": "An expression.\n\n$$w=5$$", "translation": "$w=5$"},
            {"id": "p-code", "kind": "code", "markdown": "$$literal=1$$", "translation": "$$literal=1$$"},
        ]
        self.write(self.paper_dir / "segments.json", segments)
        self.write(self.paper_dir / "annotations.json", {"annotations": [{
            "id": "math-note", "segment_id": "p-0112", "target": "translation",
            "start": 3, "end": 8, "quote": "s_i =", "note": "Original personal note.", "color": "yellow",
        }]})
        protected = ("segments.json", "annotations.json", "thinking.json", "metadata.json", "takeaway_doc.json")
        before = {name: (self.paper_dir / name).read_bytes() for name in protected}
        reader_copy = reader.make_reader_markdown(segments, "synthetic.pdf")
        paper_copy = reader.make_source_grounded_paper_markdown({}, segments, {"blocks": []}, {"terms": []}, "synthetic.pdf")
        reader.write_notes_and_annotated(self.paper_dir)
        annotated = (self.paper_dir / "annotated.md").read_text(encoding="utf-8")
        for text in (reader_copy, paper_copy, annotated):
            self.assertEqual(text.count(self.FORMULA), 1)
            for equation in ("y=2", "z=3", "v=4", "w=5", "u=4", "q=6"):
                self.assertEqual(text.count(equation), 1)
            self.assertIn("解释。", text)
            self.assertIn("说明 $z$。", text)
            self.assertIn("额外的解释，其中 $v$ 是得分。", text)
            self.assertEqual(text.count("$$literal=1$$"), 2)
        self.assertNotIn("<!-- zh:p-0112 -->", reader_copy)
        self.assertIn("Original personal note.", annotated)
        self.assertEqual(before, {name: (self.paper_dir / name).read_bytes() for name in protected})
        self.assertEqual(reader.load_reading_data(self.paper_dir)["files"]["segments.json"], segments)
        self.assertEqual(segments, json.loads(before["segments.json"]))

    def test_hidden_saved_math_still_protects_a_source_from_reparsing(self) -> None:
        self.write(self.paper_dir / "annotations.json", {"annotations": []})
        segments = [{"id": "p-1", "markdown": self.FORMULA, "translation": self.FORMULA}]
        self.assertFalse(reader.has_translation(segments[0]))
        self.assertTrue(reader.reusable_parsed_source(self.paper_dir, {"source_type": "reference"}, segments))


class CopilotProviderTests(TranslationFixture):
    def proxy_result(self, result):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps(result).encode("utf-8")
        opener = mock.Mock()
        opener.open.return_value = response
        builder = self.patch(reader.urllib.request, "build_opener", return_value=opener)
        return opener, builder

    def test_minimal_openai_payload_uses_only_source_and_no_authorization(self) -> None:
        opener, builder = self.proxy_result({"choices": [{"finish_reason": "stop", "message": {"content": "  完整译文\n"}}]})
        result = reader.translate_text("Synthetic source only.")
        self.assertEqual(result, "  完整译文\n")
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:4141/v1/chat/completions")
        payload = json.loads(request.data)
        self.assertEqual(set(payload), {"model", "messages", "max_tokens", "stream"})
        self.assertEqual((payload["model"], payload["max_tokens"], payload["stream"]), ("gpt-4.1", 1400, False))
        self.assertIn("Synthetic source only.", payload["messages"][1]["content"])
        self.assertNotIn("PRIVATE", json.dumps(payload))
        self.assertIsNone(request.get_header("Authorization"))
        self.assertIsInstance(builder.call_args.args[0], reader.urllib.request.ProxyHandler)
        self.assertEqual(builder.call_args.args[0].proxies, {})
        self.assertIsNone(builder.call_args.args[1].redirect_request(None, None, 302, "", {}, "https://example.com"))

    def test_config_restricts_endpoints_to_loopback_and_does_not_fallback(self) -> None:
        for value in ("https://example.com/v1", "http://192.168.1.1/v1", "file:///C:/data", "http://user:secret@127.0.0.1/v1", "http://127.0.0.1/v1?key=secret", "http://localhost.evil/v1"):
            with self.subTest(value=value):
                self.env["PAPER_READER_COPILOT_BASE_URL"] = value
                with self.assertRaisesRegex(ValueError, "loopback"):
                    reader.translate_text("Synthetic paragraph")
        self.env["PAPER_READER_COPILOT_BASE_URL"] = "http://localhost:4141/v1/"
        self.assertEqual(reader.copilot_translation_endpoint(), "http://127.0.0.1:4141/v1/chat/completions")
        self.assertEqual(reader.copilot_translation_endpoint("https://[::1]:4141/v1"), "https://[::1]:4141/v1/chat/completions")

    def test_empty_truncated_refused_and_malformed_outputs_fail_visibly(self) -> None:
        cases = [
            {"choices": []},
            {"choices": [{"finish_reason": "length", "message": {"content": "Truncated"}}]},
            {"choices": [{"finish_reason": "stop", "message": {"content": " \n"}}]},
            {"choices": [{"finish_reason": "stop", "message": {"content": "No", "refusal": "blocked"}}]},
            {"unexpected": "format"},
        ]
        for value in cases:
            with self.subTest(value=value):
                self.proxy_result(value)
                with self.assertRaises(RuntimeError):
                    reader.translate_text("Synthetic source")

    def test_http_errors_do_not_expose_response_body_or_fallback(self) -> None:
        opener, _ = self.proxy_result({})
        opener.open.side_effect = urllib.error.HTTPError("http://127.0.0.1", 400, "bad", {}, io.BytesIO(b"PRIVATE echoed notes or secret"))
        with self.assertRaisesRegex(RuntimeError, "HTTP 400") as failure:
            reader.translate_text("Synthetic source")
        self.assertNotIn("PRIVATE", str(failure.exception))

    def test_rate_limits_service_unavailability_and_timeouts_are_retryable(self) -> None:
        opener, _ = self.proxy_result({})
        for status in (429, 503):
            opener.open.side_effect = urllib.error.HTTPError("http://127.0.0.1", status, "wait", {"Retry-After": "3"}, io.BytesIO(b"PRIVATE"))
            with self.assertRaises(reader.RetryableTranslationError) as caught:
                reader.translate_text("Synthetic source")
            self.assertEqual(caught.exception.retry_after, 3)
            self.assertNotIn("PRIVATE", str(caught.exception))
        opener.open.side_effect = TimeoutError()
        with self.assertRaises(reader.RetryableTranslationError):
            reader.translate_text("Synthetic source")

    def test_retry_after_accepts_http_dates_and_rejects_nonfinite_values(self) -> None:
        with mock.patch.object(reader.time, "time", return_value=0):
            self.assertEqual(reader.translation_retry_after("Thu, 01 Jan 1970 00:00:05 GMT"), 5)
        for value in ("invalid", "NaN", "Infinity", ""):
            self.assertIsNone(reader.translation_retry_after(value))

    def test_legacy_kimi_and_ollama_routing_remains_available(self) -> None:
        self.env.clear()
        local = self.patch(reader, "translate_text_local", return_value="local")
        cloud = self.patch(reader, "translate_text_cloud", return_value="cloud")
        self.assertEqual(reader.translate_text("source"), "local")
        self.env["PAPER_READER_KIMI_API_KEY"] = "synthetic-test-key"
        self.assertEqual(reader.translate_text("source"), "cloud")
        self.assertEqual((local.call_count, cloud.call_count), (1, 1))


class ParallelTranslationTests(TranslationFixture):
    def setUp(self) -> None:
        super().setUp()
        self.manager.close()
        self.env["PAPER_READER_TRANSLATION_CONCURRENCY"] = "2"
        self.manager = reader.TranslationJobManager()
        reader.TRANSLATION_JOBS = self.manager

    def wait_completed(self, count: int, paper_dir: Path | None = None) -> dict:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            value = self.state(paper_dir)
            if value["completed"] == count:
                return value
            time.sleep(0.01)
        self.fail(f"Expected {count} completed, got {self.state(paper_dir)}")

    def test_two_segments_share_capacity_and_out_of_order_results_merge_by_id(self) -> None:
        entered = [threading.Event(), threading.Event()]
        releases = [threading.Event(), threading.Event()]
        self.releases.extend(releases)

        def translate(text, config):
            index = 0 if "one" in text else 1
            entered[index].set()
            self.assertTrue(releases[index].wait(5))
            return "Translated " + text

        model = self.patch(reader, "translate_text", side_effect=translate)
        self.manager.submit("paper-a", self.paper_dir, {})
        self.assertTrue(all(event.wait(2) for event in entered))
        status, snapshot = self.request("/api/translation-queue")
        self.assertEqual(status, 200)
        self.assertEqual(snapshot["concurrency"], 2)
        self.assertEqual(snapshot["active_requests"], 2)
        self.assertEqual(snapshot["jobs"][0]["active_requests"], 2)
        releases[1].set()
        self.wait_completed(1)
        segments = reader.load_segments(self.paper_dir)
        self.assertEqual(segments[0]["translation"], "")
        self.assertEqual(segments[1]["translation"], "Translated Source paragraph two.")
        self.assertEqual(self.state()["status"], "processing")
        releases[0].set()
        self.wait_status("ready")
        self.assertEqual(model.call_count, 2)
        self.assertEqual(reader.load_segments(self.paper_dir)[0]["custom"], {"keep": 1})

    def test_global_limit_and_round_robin_allow_another_paper_to_progress(self) -> None:
        other = self.make_paper("paper-b")
        self.write(self.paper_dir / "segments.json", [
            {"id": f"a-{index}", "markdown": f"Paper A paragraph {index}", "translation": ""} for index in range(4)
        ])
        self.write(other / "segments.json", [
            {"id": f"b-{index}", "markdown": f"Paper B paragraph {index}", "translation": ""} for index in range(2)
        ])
        lock = threading.Lock()
        both_started, release = threading.Event(), threading.Event()
        self.releases.append(release)
        calls = []
        active = peak = 0

        def translate(text, config):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
                calls.append(text)
                if len(calls) == 2:
                    both_started.set()
            try:
                self.assertTrue(release.wait(5))
                time.sleep(0.005)
                return "Translated " + text
            finally:
                with lock:
                    active -= 1

        self.patch(reader, "translate_text", side_effect=translate)
        self.manager.submit("paper-a", self.paper_dir, {})
        self.assertTrue(both_started.wait(2))
        self.manager.submit("paper-b", other, {})
        release.set()
        self.wait_status("ready")
        self.wait_status("ready", other)
        self.assertEqual(peak, 2)
        self.assertEqual(len(calls), 6)
        self.assertEqual(len(set(calls)), 6)
        self.assertIn("Paper B", calls[2])

    def test_a_failed_request_does_not_discard_its_successful_inflight_peer(self) -> None:
        entered, release = threading.Event(), threading.Event()
        self.releases.append(release)

        def translate(text, config):
            if "one" in text:
                self.assertTrue(entered.wait(2))
                raise RuntimeError("Synthetic permanent failure")
            entered.set()
            self.assertTrue(release.wait(5))
            return "Successful peer translation"

        model = self.patch(reader, "translate_text", side_effect=translate)
        self.manager.submit("paper-a", self.paper_dir, {})
        self.wait_status("failed")
        release.set()
        result = self.wait_completed(1)
        self.assertEqual(result["status"], "failed")
        self.assertIn("Synthetic permanent failure", result["error"])
        self.assertEqual(reader.load_segments(self.paper_dir)[1]["translation"], "Successful peer translation")
        self.assertEqual(model.call_count, 2)

    def test_retry_after_is_shared_across_papers_and_does_not_lose_peer_results(self) -> None:
        other = self.make_paper("paper-b")
        self.write(other / "segments.json", [{"id": "b-1", "markdown": "Paper B", "translation": ""}])
        peer_started, release = threading.Event(), threading.Event()
        self.releases.append(release)
        lock = threading.Lock()
        calls = []
        first_failed_at = []

        def translate(text, config):
            with lock:
                calls.append((text, time.time()))
                first = sum(source == text for source, _ in calls) == 1
            if "one" in text and first:
                self.assertTrue(peer_started.wait(2))
                first_failed_at.append(time.time())
                raise reader.RetryableTranslationError("Synthetic HTTP 429", retry_after=0.2)
            if "two" in text:
                peer_started.set()
                self.assertTrue(release.wait(5))
            return "Translated " + text

        self.patch(reader, "translate_text", side_effect=translate)
        self.manager.submit("paper-a", self.paper_dir, {})
        retrying = self.wait_status("retrying")
        self.assertIn("429", retrying["error"])
        self.assertEqual(retrying["retry_attempts"], 1)
        self.manager.submit("paper-b", other, {})
        release.set()
        self.wait_completed(1)
        time.sleep(0.05)
        self.assertEqual(len(calls), 2)
        self.wait_status("ready")
        self.wait_status("ready", other)
        self.assertEqual(len(calls), 4)
        self.assertTrue(all(started >= first_failed_at[0] + 0.19 for _, started in calls[2:]))

    def test_transient_retries_are_bounded_and_automatic_reopen_does_not_restart_failure(self) -> None:
        segments = reader.load_segments(self.paper_dir)[:1]
        self.write(self.paper_dir / "segments.json", segments)
        model = self.patch(reader, "translate_text", side_effect=reader.RetryableTranslationError("Synthetic HTTP 503", retry_after=0.01))
        self.manager.submit("paper-a", self.paper_dir, {})
        failed = self.wait_status("failed")
        self.assertEqual(model.call_count, 4)
        self.assertEqual(failed["retry_attempts"], 4)
        self.assertIn("retries exhausted", failed["error"])
        self.manager.submit("paper-a", self.paper_dir, {"automatic": True})
        self.assertEqual(model.call_count, 4)

    def test_pause_and_resume_never_exceeds_limit_or_accepts_stale_job_results(self) -> None:
        both_started, release = threading.Event(), threading.Event()
        self.releases.append(release)
        lock = threading.Lock()
        started = active = peak = 0

        def translate(text, config):
            nonlocal started, active, peak
            with lock:
                started += 1
                call = started
                active += 1
                peak = max(peak, active)
                if started == 2:
                    both_started.set()
            try:
                self.assertTrue(release.wait(5))
                return ("Old job " if call <= 2 else "New job ") + text
            finally:
                with lock:
                    active -= 1

        self.patch(reader, "translate_text", side_effect=translate)
        original = self.manager.submit("paper-a", self.paper_dir, {})
        self.assertTrue(both_started.wait(2))
        self.manager.submit("paper-a", self.paper_dir, {"action": "pause"})
        resumed = self.manager.submit("paper-a", self.paper_dir, {"action": "resume"})
        self.assertNotEqual(original["job_id"], resumed["job_id"])
        release.set()
        self.wait_status("ready")
        self.assertEqual((started, peak), (4, 2))
        self.assertTrue(all(item["translation"].startswith("New job ") for item in reader.load_segments(self.paper_dir)))

    def test_parallel_force_removes_pending_segments_by_id_not_completion_order(self) -> None:
        segments = reader.load_segments(self.paper_dir)
        for item in segments:
            item["translation"] = "Original manual translation"
        self.write(self.paper_dir / "segments.json", segments)
        first_started, release = threading.Event(), threading.Event()
        self.releases.append(release)

        def translate(text, config):
            if "one" in text:
                first_started.set()
                self.assertTrue(release.wait(5))
            else:
                self.assertTrue(first_started.wait(2))
            return "Forced " + text

        self.patch(reader, "translate_text", side_effect=translate)
        self.manager.submit("paper-a", self.paper_dir, {"force": True})
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and not reader.load_segments(self.paper_dir)[1]["translation"].startswith("Forced"):
            time.sleep(0.01)
        self.assertTrue(reader.load_segments(self.paper_dir)[1]["translation"].startswith("Forced"))
        state = reader.read_json(self.paper_dir / "translation_state.json", {})
        self.assertEqual([item["id"] for item in state["force_pending"]], ["p-1"])
        release.set()
        self.wait_status("ready")
        self.assertTrue(all(item["translation"].startswith("Forced") for item in reader.load_segments(self.paper_dir)))

    def test_queue_get_is_read_only_and_configuration_is_validated(self) -> None:
        before = {str(path): path.read_bytes() for path in self.workspace.rglob("*") if path.is_file()}
        status, body = self.request("/api/translation-queue")
        self.assertEqual((status, body["concurrency"], body["active_requests"], body["jobs"]), (200, 2, 0, []))
        self.assertIsNone(self.manager.thread)
        self.assertEqual(before, {str(path): path.read_bytes() for path in self.workspace.rglob("*") if path.is_file()})
        for value in ("0", "5", "two"):
            self.env["PAPER_READER_TRANSLATION_CONCURRENCY"] = value
            with self.assertRaisesRegex(ValueError, "1 to 4"):
                reader.TranslationJobManager()


class SourceFirstParsingTests(TranslationFixture):
    @staticmethod
    def queue_without_worker(workspace, paper_id, paper_dir, options, **kwargs):
        reader.save_processing_fields(workspace, paper_id, paper_dir, {
            "processing_mode": kwargs["mode"], "processing_status": "processing_queued",
            "processing_background": "queued",
        })
        return True

    def prepare_unparsed(self) -> Path:
        self.write(self.paper_dir / "segments.json", [])
        (self.paper_dir / "original.pdf").write_bytes(b"%PDF-fixture")
        generated = self.root / "converted.md"
        generated.write_text("# Synthetic Paper\n\nFull paragraph.\n\n# Appendix\n\nAppendix paragraph.", encoding="utf-8")
        self.patch(reader, "run_mineru", return_value=generated)
        return generated

    def test_deep_parse_never_briefs_or_synthesizes_and_keeps_existing_human_files(self) -> None:
        self.prepare_unparsed()
        (self.paper_dir / "notes.md").write_text("HUMAN ORIGINAL NOTES\n", encoding="utf-8")
        protected = ["thinking.json", "annotations.json", "takeaway_doc.json", "notes.md"]
        before = {name: (self.paper_dir / name).read_bytes() for name in protected}
        result = reader.process_paper_deep(self.workspace, "paper-a", self.paper_dir)
        self.assertEqual(result["processing_status"], "ready")
        self.assertTrue(reader.load_segments(self.paper_dir))
        for name, content in before.items():
            self.assertEqual((self.paper_dir / name).read_bytes(), content)
        self.assertFalse((self.paper_dir / "translation_state.json").exists())

    def test_already_parsed_annotated_source_is_reused_even_on_process_post(self) -> None:
        original = (self.paper_dir / "segments.json").read_bytes()
        status, data = self.request("/api/papers/paper-a/process", method="POST", data={"mode": "deep"})
        self.assertEqual(status, 200, data)
        self.assertEqual(data["metadata"]["processing_status"], "ready")
        self.assertEqual((self.paper_dir / "segments.json").read_bytes(), original)

    def test_deep_process_and_all_intake_helpers_queue_without_waiting_for_brief(self) -> None:
        self.prepare_unparsed()
        queue_work = self.patch(reader, "start_background_paper_processing", side_effect=self.queue_without_worker)
        status, data = self.request("/api/papers/paper-a/process", method="POST", data={"mode": "deep"})
        self.assertEqual(status, 200, data)
        self.assertEqual(data["metadata"]["processing_status"], "processing_queued")
        self.assertEqual(queue_work.call_args.kwargs["refresh_citations"], False)
        self.assertEqual(queue_work.call_args.kwargs["refresh_videos"], False)
        self.assertEqual(reader.load_segments(self.paper_dir), [])

    def test_waiting_translation_starts_after_source_parse_only_when_requested(self) -> None:
        self.prepare_unparsed()
        model = self.patch(reader, "translate_text", return_value="译文")
        state = self.manager.submit("paper-a", self.paper_dir, {"automatic": True})
        self.assertEqual(state["status"], "waiting_for_source")
        model.assert_not_called()
        reader.process_paper_deep(self.workspace, "paper-a", self.paper_dir)
        self.wait_status("ready")
        self.assertEqual(model.call_count, 4)

    def test_reading_metadata_edits_during_conversion_are_not_overwritten(self) -> None:
        generated = self.prepare_unparsed()

        def convert(*args, **kwargs):
            metadata = reader.read_json(self.paper_dir / "metadata.json", {})
            metadata.update({"read_status": "read", "tags": ["new-user-tag"], "title": "User title", "title_source": "user"})
            self.write(self.paper_dir / "metadata.json", metadata)
            return generated

        self.patch(reader, "run_mineru", side_effect=convert)
        reader.process_paper_deep(self.workspace, "paper-a", self.paper_dir)
        latest = reader.read_json(self.paper_dir / "metadata.json", {})
        self.assertEqual((latest["read_status"], latest["title"], latest["tags"]), ("read", "User title", ["new-user-tag"]))

    def test_import_registration_has_no_citation_or_preview_prerequisite(self) -> None:
        result = reader.register_uploaded_pdf(self.workspace, "new-source.pdf", b"%PDF-fake", title="Unique new paper")
        self.assertTrue(result["ok"])
        path = self.workspace / "papers" / result["paper_id"]
        self.assertEqual(reader.read_json(path / "metadata.json", {})["title"], "Unique new paper")
        other = reader.register_metadata_only_paper(self.workspace, "Another unique fixture")
        self.assertTrue(other["ok"])

    def test_upload_attachment_and_local_import_endpoints_queue_source_only(self) -> None:
        self.prepare_unparsed()
        queued = self.patch(reader, "start_background_paper_processing", side_effect=self.queue_without_worker)
        boundary = "fixture-multipart"
        body = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"endpoint-new.pdf\"\r\n"
            "Content-Type: application/pdf\r\n\r\n%PDF-fixture-endpoint\r\n"
            f"--{boundary}--\r\n"
        ).encode("ascii")
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        status, uploaded = self.request("/api/library/papers/upload", method="POST", body=body, headers=headers)
        self.assertEqual(status, 200, uploaded)
        self.assertEqual(uploaded["papers"][0]["metadata"]["processing_status"], "processing_queued")
        status, attached = self.request("/api/papers/paper-a/pdf", method="POST", body=body, headers=headers)
        self.assertEqual(status, 200, attached)
        self.assertEqual(attached["metadata"]["processing_status"], "processing_queued")
        local_pdf = self.root / "local-new-source.pdf"
        local_pdf.write_bytes(b"%PDF-fixture-local")
        status, imported = self.request("/api/library/papers", method="POST", data={"path": str(local_pdf), "title": "Unique local intake"})
        self.assertEqual(status, 200, imported)
        self.assertEqual(imported["metadata"]["processing_status"], "processing_queued")
        self.assertEqual(queued.call_count, 3)
        for call in queued.call_args_list:
            self.assertFalse(call.kwargs["refresh_citations"])
            self.assertFalse(call.kwargs["refresh_videos"])

    def test_cli_ingest_is_source_only_and_repeat_ingest_preserves_identifiers(self) -> None:
        raw = self.root / "input.md"
        raw.write_text("# Synthetic Input\n\nOnly source.", encoding="utf-8")
        args = argparse.Namespace(workspace=str(self.workspace), pdf=None, raw_md=str(raw), paper_id="new-cli", title=None, backend="pipeline", method="auto", lang="en", start=None, end=None)
        with mock.patch.object(reader, "resolve_workspace", return_value=self.workspace), mock.patch("builtins.print"):
            reader.ingest_pdf(args)
            paper = self.workspace / "papers" / "new-cli"
            segments = reader.load_segments(paper)
            segments[0]["id"] = "human-stable-id"
            segments[0]["translation"] = "人工译文"
            self.write(paper / "segments.json", segments)
            reader.ingest_pdf(args)
        self.assertEqual(reader.load_segments(paper), segments)
        self.assertFalse((paper / "thinking.json").exists())
        self.assertFalse((paper / "takeaway_doc.json").exists())


if __name__ == "__main__":
    unittest.main()
