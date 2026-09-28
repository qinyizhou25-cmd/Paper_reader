"""Cross-platform paths and startup, using disposable data and no external tools."""

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feishu_metadata
import paper_reader_agent as reader


class PortableWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="reader-portability-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.workspace = self.root / "reading space \u8bba\u6587"
        self.paper = self.workspace / "papers" / "paper-a"
        self.paper.mkdir(parents=True)
        self.record = {
            "id": "paper-a", "title": "Synthetic paper",
            "paper_dir": r"papers\paper-a",
            "metadata": r"papers\paper-a\metadata.json",
            "reader_md": r"papers\paper-a\reader.md",
            "notes_md": r"papers\paper-a\notes.md",
            "source_pdf": r"papers\paper-a\original.pdf",
        }
        self.write(self.workspace / "library.json", {"papers": [self.record]})
        self.write(self.paper / "metadata.json", {
            "id": "paper-a", "title": "Synthetic paper", "processing_status": "ready",
            "processing_mode": "deep", "source_pdf": "original.pdf",
            "original_path": r"E:\old machine\original.pdf",
            "feishu": {"base_token": "SyntheticBase", "table_id": "tblSynthetic", "record_id": "recSynthetic"},
        })
        self.write(self.paper / "segments.json", [{
            "id": "p-1", "kind": "paragraph", "markdown": "Original source.",
            "translation": "\u539f\u59cb\u8bd1\u6587",
        }])
        self.write(self.paper / "annotations.json", {"annotations": [{
            "id": "note-1", "segment_id": "p-1", "quote": "Original",
            "note": "  My note with a literal Windows path E:\\research\\notes.\n",
        }]})
        self.write(self.paper / "thinking.json", {"explain": {"content": "Saved briefing."}})
        self.write(self.paper / ".feishu-publication" / "journal.json", {"receipt": "keep exactly"})
        (self.paper / "original.pdf").write_bytes(b"%PDF-1.4 synthetic fixture")
        (self.paper / "notes.md").write_text("My saved note.", encoding="utf-8")
        (self.paper / "reader.md").write_text("Original source.", encoding="utf-8")
        self.env = {}
        patcher = mock.patch.object(reader, "env_value", side_effect=self.env_value)
        patcher.start()
        self.addCleanup(patcher.stop)

    def env_value(self, *names: str, default: str = "") -> str:
        return next((self.env[name] for name in names if self.env.get(name)), default)

    def write(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(json.dumps(value, ensure_ascii=False).encode("utf-8") + b"\r\n")

    def snapshot(self, folder: Path | None = None) -> dict:
        folder = folder or self.workspace
        return {path.relative_to(folder).as_posix(): path.read_bytes()
                for path in folder.rglob("*") if path.is_file()}

    def test_old_windows_relative_paths_resolve_without_rewriting_any_saved_data(self) -> None:
        before = self.snapshot()
        for value in (r"papers\paper-a", "papers/paper-a", r".\papers\paper-a"):
            with self.subTest(value=value):
                record = {**self.record, "paper_dir": value}
                self.assertEqual(reader.paper_record_dir(self.workspace, record), self.paper)
        self.assertEqual(reader.paper_record_artifact(self.workspace, self.record, "notes_md", "notes.md"),
                         self.paper / "notes.md")
        handler = object.__new__(reader.ReaderHandler)
        handler.workspace = self.workspace
        self.assertEqual(handler.get_paper_dir("paper-a"), self.paper)
        data = reader.load_reading_data(handler.get_paper_dir("paper-a"), "paper-a")
        self.assertEqual(data["files"]["annotations.json"]["annotations"][0]["id"], "note-1")
        self.assertIn(r"E:\research\notes", data["files"]["annotations.json"]["annotations"][0]["note"])
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(reader.read_library_index(self.workspace)["papers"][0], self.record)

    def test_relocated_workspace_keeps_ids_notes_sources_and_receipts(self) -> None:
        destination = self.root / "moved reading library"
        before = self.snapshot()
        shutil.copytree(self.workspace, destination)
        record = reader.read_library_index(destination)["papers"][0]
        paper = reader.paper_record_dir(destination, record)
        self.assertEqual(paper, destination / "papers" / "paper-a")
        self.assertEqual(reader.load_reading_data(paper, record["id"]),
                         reader.load_reading_data(self.paper, self.record["id"]))
        self.assertEqual(self.snapshot(destination), before)

    def test_normal_metadata_update_writes_portable_paths_only(self) -> None:
        originals = self.snapshot()
        metadata = reader.read_json(self.paper / "metadata.json", {})
        reader.sync_library_from_metadata(self.workspace, "paper-a", self.paper, metadata,
                                          generate_pdf_preview=False)
        record = reader.read_library_index(self.workspace)["papers"][0]
        for field in ("paper_dir", "metadata", "reader_md", "annotated_md", "notes_md", "source_pdf"):
            with self.subTest(field=field):
                self.assertTrue(record[field].startswith("papers/paper-a"))
                self.assertNotIn("\\", record[field])
        for path, data in originals.items():
            if path != "library.json":
                self.assertEqual((self.workspace / path).read_bytes(), data, path)

    def test_missing_directory_field_uses_stable_paper_identity(self) -> None:
        self.assertEqual(reader.paper_record_dir(self.workspace, {"id": "paper-a"}), self.paper)
        self.assertEqual(reader.paper_record_artifact(self.workspace, {"id": "paper-a"}, "notes_md", "notes.md"),
                         self.paper / "notes.md")
        for paper_id in ("", ".", "..", "../outside", r"..\outside", "C:outside"):
            with self.subTest(paper_id=paper_id), self.assertRaises(ValueError):
                reader.paper_record_dir(self.workspace, {"id": paper_id})

    def test_stored_paths_reject_parent_traversal_drive_relative_and_outside_workspace(self) -> None:
        for value in ("", ".", "../outside", r"..\outside", r"C:papers\paper-a", str(self.root / "outside")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                reader.stored_workspace_path(self.workspace, value)
        self.assertEqual(reader.stored_workspace_path(self.workspace, str(self.paper)), self.paper)

    @unittest.skipIf(os.name == "nt", "Foreign Windows absolute paths are rejected on POSIX hosts.")
    def test_posix_rejects_old_absolute_drive_and_unc_paths_instead_of_guessing_a_new_folder(self) -> None:
        before = self.snapshot()
        for value in (r"E:\old library\papers\paper-a", r"\\server\share\papers\paper-a"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                reader.stored_workspace_path(self.workspace, value)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "Windows"):
                reader.resolve_local_path(value, base=self.root)
        self.assertEqual(self.snapshot(), before)

    def test_explicit_workspace_overrides_machine_config(self) -> None:
        self.env["PAPER_READER_WORKSPACE"] = str(self.root / "unused library")
        self.assertEqual(reader.resolve_workspace(str(self.workspace)), self.workspace)
        self.assertEqual(reader.resolve_workspace(None), self.root / "unused library")

    def test_relative_windows_config_path_resolves_from_config_location_without_rewriting_it(self) -> None:
        config = self.root / reader.CONFIG_FILE
        self.write(config, {"workspace": ".\\" + self.workspace.name})
        before = config.read_bytes()
        self.assertEqual(reader.resolve_workspace(None, start=self.root), self.workspace)
        self.assertEqual(config.read_bytes(), before)

    def test_home_expansion_and_relative_base(self) -> None:
        with mock.patch.dict(os.environ, {"HOME": str(self.root), "USERPROFILE": str(self.root)}):
            self.assertEqual(reader.resolve_local_path("~/reading space \u8bba\u6587"), self.workspace)
        self.assertEqual(reader.resolve_local_path(r"papers\paper-a", base=self.workspace), self.paper)
        with self.assertRaisesRegex(ValueError, "Drive-relative"):
            reader.resolve_local_path("E:paper-library")

    def test_initialization_handles_different_windows_drives_and_saves_portable_config(self) -> None:
        with mock.patch.object(reader.Path, "cwd", return_value=self.root), \
             mock.patch.object(reader.os.path, "relpath", side_effect=ValueError("different drives")), \
             contextlib.redirect_stdout(io.StringIO()):
            reader.init_workspace(argparse.Namespace(workspace=str(self.workspace), no_config=False))
        self.assertEqual(reader.read_json(self.root / reader.CONFIG_FILE, {})["workspace"],
                         self.workspace.as_posix())

    def test_read_commands_do_not_create_a_missing_library(self) -> None:
        missing = self.root / "unavailable drive" / "library"
        commands = (["status"], ["query"], ["rebuild"], ["citations"], ["process", "paper-a", "--mode", "deep"])
        for command in commands:
            stderr = io.StringIO()
            with self.subTest(command=command), contextlib.redirect_stderr(stderr):
                code = reader.main(["--workspace", str(missing), *command])
                self.assertEqual(code, 1)
                self.assertIn("workspace is unavailable", stderr.getvalue())
                self.assertFalse(missing.exists())

    def test_query_and_cli_library_find_briefings_through_legacy_paths(self) -> None:
        before = self.snapshot()
        with contextlib.redirect_stdout(io.StringIO()):
            code = reader.main(["--workspace", str(self.workspace), "query", "--include-briefs",
                                "--output", "query-output.json"])
        self.assertEqual(code, 0)
        result = reader.read_json(self.workspace / "query-output.json", {})
        self.assertEqual(result["papers"][0]["briefing"]["content"], "Saved briefing.")
        self.assertEqual(Path(result["papers"][0]["notes_path"]), self.paper / "notes.md")
        self.assertEqual(reader.load_library(self.workspace)["papers"][0]["processing_status"], "ready")
        for path, data in before.items():
            self.assertEqual((self.workspace / path).read_bytes(), data, path)

    def test_cached_project_memory_is_preserved_even_when_its_original_source_is_on_another_computer(self) -> None:
        context = {"project": "collaborative", "source_path": r"E:\old project\memory.md",
                   "cards": [{"id": "c-1", "title": "Saved context", "summary": "Original project idea."}]}
        self.write(self.workspace / "project_contexts.json", {"version": 1, "contexts": {"collaborative": context}})
        before = self.snapshot()
        self.assertEqual(reader.load_project_context(self.workspace, "collaborative")["cards"], context["cards"])
        if os.name != "nt":
            with self.assertRaisesRegex(ValueError, "Windows"):
                reader.refresh_project_context_from_source(self.workspace, "collaborative")
        self.assertEqual(self.snapshot(), before)


class StartupAndToolTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="reader-startup-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.workspace = self.root / "workspace"
        self.addCleanup(setattr, reader.ReaderHandler, "workspace", reader.ReaderHandler.workspace)
        patcher = mock.patch.object(reader, "env_value", return_value="")
        patcher.start()
        self.addCleanup(patcher.stop)

    def args(self, *extra: str) -> argparse.Namespace:
        return reader.build_parser().parse_args(["--workspace", str(self.workspace), "serve", *extra])

    def test_serve_requires_existing_index_before_binding_or_resuming_work(self) -> None:
        for existing_directory in (False, True):
            if existing_directory:
                self.workspace.mkdir()
            with self.subTest(existing_directory=existing_directory), \
                 mock.patch.object(reader, "ThreadingHTTPServer") as bind, \
                 mock.patch.object(reader, "resume_interrupted_processing_tasks") as resume:
                with self.assertRaisesRegex(FileNotFoundError, "Connect the drive"):
                    reader.serve(self.args())
                bind.assert_not_called()
                resume.assert_not_called()
                self.assertFalse((self.workspace / "library.json").exists())

    def test_corrupt_index_is_not_hidden_even_with_explicit_creation(self) -> None:
        self.workspace.mkdir()
        index = self.workspace / "library.json"
        for content in ('{"papers":[', '{"papers":{}}'):
            index.write_text(content, encoding="utf-8")
            for extra in ((), ("--create-workspace",)):
                with self.subTest(content=content, extra=extra), \
                     mock.patch.object(reader, "ThreadingHTTPServer") as bind:
                    with self.assertRaises(ValueError):
                        reader.serve(self.args(*extra))
                    bind.assert_not_called()
                    self.assertEqual(index.read_text(encoding="utf-8"), content)

    def test_busy_port_never_creates_a_library_or_starts_background_jobs(self) -> None:
        with mock.patch.object(reader, "ThreadingHTTPServer", side_effect=OSError("address already in use")), \
             mock.patch.object(reader, "resume_interrupted_processing_tasks") as resume:
            with self.assertRaisesRegex(OSError, "address already in use"):
                reader.serve(self.args("--create-workspace"))
            self.assertFalse(self.workspace.exists())
            resume.assert_not_called()

    def test_explicit_new_library_binds_first_and_closes_cleanly(self) -> None:
        events = []
        server = mock.Mock(server_address=("127.0.0.1", 12345))
        server.serve_forever.side_effect = lambda: events.append("serve")
        server.server_close.side_effect = lambda: events.append("close")

        def bind(*args):
            events.append("bind")
            self.assertFalse(self.workspace.exists())
            return server

        def resume(workspace):
            events.append("resume")
            self.assertEqual(reader.read_library_index(workspace)["papers"], [])
            return []

        with mock.patch.object(reader, "ThreadingHTTPServer", side_effect=bind), \
             mock.patch.object(reader, "resume_interrupted_processing_tasks", side_effect=resume), \
             contextlib.redirect_stdout(io.StringIO()):
            reader.serve(self.args("--create-workspace"))
        self.assertEqual(events, ["bind", "resume", "serve", "close"])

    def test_native_mineru_next_to_selected_python_is_found_without_shell_activation(self) -> None:
        executable = self.root / ("mineru.exe" if os.name == "nt" else "mineru")
        executable.write_text("synthetic executable", encoding="utf-8")
        executable.chmod(0o755)
        with mock.patch.object(reader.sys, "executable", str(self.root / "python")), \
             mock.patch.object(reader.shutil, "which", return_value=None):
            self.assertEqual(reader.find_mineru(), str(executable))

    def test_explicit_missing_mineru_is_not_silently_replaced_by_another_install(self) -> None:
        with mock.patch.object(reader, "env_value", return_value=str(self.root / "missing-mineru")), \
             mock.patch.object(reader.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "installed for this computer"):
                reader.find_mineru()

    def test_explicit_mineru_home_path_is_expanded(self) -> None:
        executable = self.root / ("mineru.bat" if os.name == "nt" else "mineru")
        executable.write_text("synthetic executable", encoding="utf-8")
        executable.chmod(0o755)
        with mock.patch.object(reader, "env_value", return_value="~/" + executable.name), \
             mock.patch.dict(os.environ, {"HOME": str(self.root), "USERPROFILE": str(self.root)}), \
             mock.patch.object(reader.shutil, "which", return_value=None):
            self.assertEqual(reader.find_mineru(), str(executable))

    @unittest.skipIf(os.name == "nt", "Windows wrappers are not executable on macOS/POSIX.")
    def test_posix_refuses_a_copied_windows_mineru_wrapper(self) -> None:
        executable = self.root / "mineru.bat"
        executable.write_text("synthetic wrapper", encoding="utf-8")
        executable.chmod(0o755)
        with mock.patch.object(reader, "env_value", return_value=str(executable)):
            with self.assertRaisesRegex(RuntimeError, "installed for this computer"):
                reader.find_mineru()

    def test_feishu_cli_expands_home_and_resolves_native_path(self) -> None:
        executable = self.root / ("lark-cli.exe" if os.name == "nt" else "lark-cli")
        executable.write_text("synthetic executable", encoding="utf-8")
        executable.chmod(0o755)
        with mock.patch.dict(os.environ, {"HOME": str(self.root), "USERPROFILE": str(self.root)}):
            self.assertEqual(feishu_metadata.cli_command("~/" + executable.name), str(executable))


if __name__ == "__main__":
    unittest.main()
