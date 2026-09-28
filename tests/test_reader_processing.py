"""Serial parser queue regressions; never start a real converter or model."""

import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

import paper_reader_agent as reader


class ProcessingQueueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="reader-queue-test-")
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        reader.write_json(self.workspace / "library.json", {"papers": []})
        self.paths = {}
        for paper_id in ("A", "B", "C"):
            folder = self.workspace / "papers" / paper_id
            folder.mkdir(parents=True)
            (folder / "original.pdf").write_bytes(b"%PDF-synthetic-queue-fixture")
            reader.write_json(folder / "metadata.json", {
                "id": paper_id, "title": f"Synthetic {paper_id}", "title_source": "user",
                "processing_mode": "deep", "processing_status": "not_processed",
            })
            reader.write_json(folder / "segments.json", [])
            reader.write_json(folder / "annotations.json", {"annotations": [{"id": "original", "note": "  Keep my thought.\n"}]})
            reader.sync_library_from_metadata(self.workspace, paper_id, folder,
                                             reader.read_json(folder / "metadata.json", {}), generate_pdf_preview=False)
            self.paths[paper_id] = folder
        self.manager = reader.PaperProcessingJobManager()
        self.patch("PROCESSING_JOBS", new=self.manager)
        self.patch("process_paper_deep", side_effect=self.complete)
        self.patch("process_paper_skim", side_effect=self.complete)
        for name in ("run_mineru", "agent_chat", "refresh_paper_citations", "refresh_paper_videos"):
            self.patch(name, side_effect=AssertionError(f"Unexpected call: {name}"))
        self.releases = []
        self.addCleanup(self.stop)

    def patch(self, name, **kwargs):
        patcher = mock.patch.object(reader, name, **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def stop(self) -> None:
        for event in self.releases:
            event.set()
        self.manager.shutdown()

    def complete(self, workspace, paper_id, paper_dir, options):
        reader.write_json(paper_dir / "segments.json", [{"id": "p-0001", "markdown": "Synthetic source."}])
        return reader.save_processing_fields(workspace, paper_id, paper_dir, {"processing_status": "ready"})

    def wait_for(self, paper_id: str, status: str) -> dict:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            job = next((job for job in self.manager.snapshot(self.workspace)["jobs"] if job["paper_id"] == paper_id), {})
            if job.get("status") == status:
                return job
            time.sleep(0.01)
        self.fail(f"{paper_id} did not reach {status}: {self.manager.snapshot(self.workspace)}")

    def test_one_worker_fifo_dedup_and_queue_position(self) -> None:
        entered, release = threading.Event(), threading.Event()
        self.releases.append(release)
        order = []

        def process(workspace, paper_id, paper_dir, options):
            order.append(paper_id)
            if paper_id == "A":
                entered.set()
                if not release.wait(5):
                    raise TimeoutError("Synthetic gate was not released")
            return self.complete(workspace, paper_id, paper_dir, options)

        reader.process_paper_deep.side_effect = process
        self.manager.submit(self.workspace, "A", self.paths["A"])
        self.assertTrue(entered.wait(3))
        self.manager.submit(self.workspace, "B", self.paths["B"])
        self.manager.submit(self.workspace, "C", self.paths["C"])
        before = (self.paths["A"] / "metadata.json").read_bytes()
        self.assertFalse(self.manager.submit(self.workspace, "A", self.paths["A"]))
        self.assertEqual(before, (self.paths["A"] / "metadata.json").read_bytes())
        with self.assertRaisesRegex(ValueError, "another mode"):
            self.manager.submit(self.workspace, "A", self.paths["A"], mode="skim")
        result = self.manager.snapshot(self.workspace)
        self.assertEqual((result["concurrency"], result["active_jobs"], result["queued_count"]), (1, 1, 2))
        self.assertEqual([job["position"] for job in result["jobs"]], [None, 1, 2])
        self.assertEqual(order, ["A"])
        release.set()
        self.wait_for("C", "ready")
        self.assertEqual(order, ["A", "B", "C"])
        self.assertEqual(len({call.args[1] for call in reader.process_paper_deep.call_args_list}), 3)

    def test_failure_keeps_notes_and_does_not_block_the_next_paper(self) -> None:
        before = (self.paths["A"] / "annotations.json").read_bytes()

        def process(workspace, paper_id, paper_dir, options):
            if paper_id == "A":
                raise RuntimeError("Synthetic converter error")
            return self.complete(workspace, paper_id, paper_dir, options)

        reader.process_paper_deep.side_effect = process
        self.manager.submit(self.workspace, "A", self.paths["A"], {"lang": "en"})
        self.manager.submit(self.workspace, "B", self.paths["B"])
        self.wait_for("A", "failed")
        self.wait_for("B", "ready")
        metadata = reader.read_json(self.paths["A"] / "metadata.json", {})
        self.assertEqual(metadata["processing_background"], "failed")
        self.assertIn("Synthetic converter error", metadata["processing_error"])
        self.assertEqual(metadata["processing_request"]["options"], {"lang": "en"})
        self.assertEqual(before, (self.paths["A"] / "annotations.json").read_bytes())
        reader.process_paper_deep.side_effect = self.complete
        self.assertTrue(self.manager.submit(self.workspace, "A", self.paths["A"], {"lang": "en"}))
        self.wait_for("A", "ready")
        self.assertEqual(reader.read_json(self.paths["A"] / "metadata.json", {})["processing_error"], "")

    def test_reopening_an_active_paper_does_not_downgrade_it_to_queued(self) -> None:
        entered, release = threading.Event(), threading.Event()
        self.releases.append(release)

        def process(*args):
            entered.set()
            if not release.wait(5):
                raise TimeoutError("Synthetic gate was not released")
            return self.complete(*args)

        reader.process_paper_deep.side_effect = process
        reader.prepare_pdf_brief_then_background(self.workspace, "A", self.paths["A"])
        self.assertTrue(entered.wait(3))
        metadata = reader.prepare_pdf_brief_then_background(self.workspace, "A", self.paths["A"])
        self.assertEqual(metadata["processing_status"], "processing")
        self.assertEqual(reader.process_paper_deep.call_count, 1)
        release.set()
        self.wait_for("A", "ready")

    def test_restart_resumes_only_requested_papers_in_saved_order_and_keeps_options(self) -> None:
        for paper_id, timestamp in (("A", "2026-01-01T10:02:00"), ("B", "2026-01-01T10:01:00")):
            reader.save_processing_fields(self.workspace, paper_id, self.paths[paper_id], {
                "processing_status": "processing_queued", "processing_background": "queued",
                "processing_request": {"mode": "deep", "options": {"lang": "en", "start": 2, "end": 4}, "queued_at": timestamp},
            })
        resumed = reader.resume_interrupted_processing_tasks(self.workspace)
        self.assertEqual(resumed, ["B", "A"])
        self.wait_for("A", "ready")
        self.assertEqual([call.args[1] for call in reader.process_paper_deep.call_args_list], ["B", "A"])
        self.assertEqual(reader.process_paper_deep.call_args.args[3], {"lang": "en", "start": 2, "end": 4})
        self.assertEqual(reader.read_json(self.paths["C"] / "metadata.json", {})["processing_status"], "not_processed")
        self.manager.shutdown()
        restored = reader.PaperProcessingJobManager()
        try:
            with mock.patch.object(reader, "PROCESSING_JOBS", restored):
                self.assertEqual(reader.resume_interrupted_processing_tasks(self.workspace), [])
                self.assertEqual([job["status"] for job in restored.snapshot(self.workspace)["jobs"]], ["ready", "ready"])
                self.assertIsNone(restored.thread)
        finally:
            restored.shutdown()

    def test_failed_jobs_are_restored_for_explicit_retry_without_starting_a_worker(self) -> None:
        reader.save_processing_fields(self.workspace, "A", self.paths["A"], {
            "processing_status": "failed", "processing_background": "failed", "processing_error": "Original error",
            "processing_request": {"mode": "deep", "options": {}, "queued_at": "2026-01-01T10:00:00"},
        })
        self.assertEqual(reader.resume_interrupted_processing_tasks(self.workspace), [])
        self.assertIsNone(self.manager.thread)
        self.assertEqual(self.manager.snapshot(self.workspace)["jobs"][0]["error"], "Original error")

    def test_queued_paper_with_removed_metadata_is_not_recreated(self) -> None:
        entered, release = threading.Event(), threading.Event()
        self.releases.append(release)

        def process(*args):
            entered.set()
            if not release.wait(5):
                raise TimeoutError("Synthetic gate was not released")
            return self.complete(*args)

        reader.process_paper_deep.side_effect = process
        self.manager.submit(self.workspace, "A", self.paths["A"])
        self.assertTrue(entered.wait(3))
        self.manager.submit(self.workspace, "B", self.paths["B"])
        (self.paths["B"] / "metadata.json").unlink()
        release.set()
        failure = self.wait_for("B", "failed")
        self.assertIn("will not recreate", failure["error"])
        self.assertFalse((self.paths["B"] / "metadata.json").exists())
        self.assertEqual(reader.process_paper_deep.call_count, 1)

    def test_new_requests_keep_distinct_order_even_when_general_timestamps_share_a_second(self) -> None:
        with mock.patch.object(reader, "now_iso", return_value="2026-01-01T10:00:00+00:00"):
            self.manager.submit(self.workspace, "A", self.paths["A"])
            self.manager.submit(self.workspace, "B", self.paths["B"])
            self.wait_for("B", "ready")
        stamps = [reader.read_json(self.paths[paper_id] / "metadata.json", {})["processing_request"]["queued_at"]
                  for paper_id in ("A", "B")]
        self.assertLess(stamps[0], stamps[1])

    def test_parser_updates_cannot_overwrite_a_concurrent_library_import(self) -> None:
        original_load = reader.load_library_raw
        first_read, second_started, second_read, release = (threading.Event() for _ in range(4))
        read_count = 0
        counter_lock = threading.Lock()
        self.releases.append(release)

        def load(workspace):
            nonlocal read_count
            snapshot = original_load(workspace)
            with counter_lock:
                read_count += 1
                count = read_count
            if count == 1:
                first_read.set()
                if not release.wait(5):
                    raise TimeoutError("The first index update was not released")
            elif count == 2:
                second_read.set()
            return snapshot

        def second_update():
            second_started.set()
            reader.upsert_paper_record(self.workspace, {"id": "imported", "title": "A newly imported paper"})

        with mock.patch.object(reader, "load_library_raw", side_effect=load), ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(reader.upsert_paper_record, self.workspace, {"id": "A", "processing_status": "ready"})
            self.assertTrue(first_read.wait(3))
            second = pool.submit(second_update)
            try:
                self.assertTrue(second_started.wait(3))
                self.assertFalse(second_read.wait(0.1), "The second update must read after the first update is committed")
            finally:
                release.set()
            first.result(timeout=3)
            second.result(timeout=3)
        records = {item["id"]: item for item in reader.read_library_index(self.workspace)["papers"]}
        self.assertIn("imported", records)
        self.assertEqual(records["A"]["processing_status"], "ready")


if __name__ == "__main__":
    unittest.main()
