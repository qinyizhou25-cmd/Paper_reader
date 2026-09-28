from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest import mock
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feishu_metadata as feishu


BASE, TABLE, RECORD = "SyntheticBase", "tblSynthetic", "recSynthetic"
PRIMARY, FALLBACK = "fldE2HGqZA", "fldJAb4POc"
URL = f"https://example.feishu.cn/base/{BASE}?table={TABLE}&record={RECORD}"
PDF = b"%PDF-1.7\nSynthetic unit-test bytes only.\n%%EOF\n"


def attachment(token: str = "fileSynthetic", name: str = "paper.pdf", **extra: object) -> dict:
    return {"file_token": token, "name": name, "size": len(PDF), **extra}


def record_table(*, attachments: bool = True) -> dict:
    fields = [value[1] for value in feishu.FIELD_MAPPING.values()] + list(feishu.BRIEF_FIELDS.values())
    values = [f"  Exact {key}.\n" for key in feishu.FIELD_MAPPING]
    values.extend(["# Author: Never infer this\n", "  # 作者：不要重新提取。\n"])
    if attachments:
        fields.extend([PRIMARY, FALLBACK])
        values.extend([None, None])
    return {"field_id_list": fields, "record_id_list": [RECORD], "data": [values], "record_not_found": []}


def set_cell(data: dict, field_id: str, value: object) -> None:
    data["data"][0][data["field_id_list"].index(field_id)] = value


def cli_success(data: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], 0, stdout=json.dumps({"ok": True, "data": data or {}}), stderr="")


class FeishuIntakeRecordTests(unittest.TestCase):
    def test_normalizes_pdfs_in_primary_then_fallback_order_without_duplicate_tokens(self) -> None:
        data = record_table()
        set_cell(data, PRIMARY, [
            attachment("filePrimary", "Original.PDF", type="application/octet-stream", tmp_url="PRIVATE_URL"),
            attachment("fileShared", "Shared.pdf"),
            attachment("filePrimary", "Duplicate.pdf"),
        ])
        set_cell(data, FALLBACK, [
            attachment("fileImage", "image.png", type="image/png"),
            attachment("fileShared", "Another shared name.pdf"),
            attachment("fileFallback", "download.bin", type="application/pdf"),
            attachment("fileFallback", "Duplicate fallback.pdf"),
        ])
        original = copy.deepcopy(data)
        with mock.patch.object(feishu, "run_cli", return_value=data) as run:
            result = feishu.read_intake_record(BASE, TABLE, RECORD, executable="chosen.exe")
        self.assertEqual(result["attachments"], [
            {"field_id": PRIMARY, "file_token": "filePrimary", "name": "Original.PDF", "size": len(PDF)},
            {"field_id": PRIMARY, "file_token": "fileShared", "name": "Shared.pdf", "size": len(PDF)},
            {"field_id": FALLBACK, "file_token": "fileFallback", "name": "download.bin", "size": len(PDF)},
        ])
        self.assertEqual(data, original)
        arguments = run.call_args.args[0]
        self.assertEqual(arguments[0], "+record-get")
        projected = [arguments[index + 1] for index, value in enumerate(arguments) if value == "--field-id"]
        self.assertEqual(projected, data["field_id_list"])
        self.assertEqual(run.call_args.kwargs, {"executable": "chosen.exe"})
        self.assertNotIn("PRIVATE_URL", repr(result))
        self.assertEqual(set(result), {"record_id", "metadata", "field_sources", "briefings", "attachments"})

    def test_preview_preserves_metadata_and_briefings_without_reparsing_or_cleaning(self) -> None:
        data = record_table()
        title = "  [Original title](https://example.invalid/paper)\n"
        set_cell(data, feishu.FIELD_MAPPING["title"][1], [{"text": title}])
        set_cell(data, feishu.FIELD_MAPPING["authors"][1], None)
        before = copy.deepcopy(data)
        with mock.patch.object(feishu, "run_cli", return_value=data):
            result = feishu.read_intake_record(BASE, TABLE, RECORD)
        self.assertEqual(result["metadata"]["title"], title)
        self.assertEqual(result["metadata"]["authors"], "")
        self.assertEqual(result["metadata"]["year"], "  Exact year.\n")
        self.assertEqual(result["field_sources"], {key: value[0] for key, value in feishu.FIELD_MAPPING.items()})
        self.assertEqual(result["briefings"], {
            "raw text": "# Author: Never infer this\n", "raw text_中文": "  # 作者：不要重新提取。\n",
        })
        self.assertEqual(data, before)

    def test_empty_cells_are_a_valid_preview_and_fallback_remains_available(self) -> None:
        for primary, fallback, expected in [
            (None, None, []), ([], [], []), (None, [], []),
            ([], [attachment()], [{"field_id": FALLBACK, **attachment()}]),
            ([attachment(name="figure.png")], [attachment()], [{"field_id": FALLBACK, **attachment()}]),
        ]:
            with self.subTest(primary=primary, fallback=fallback):
                data = record_table()
                set_cell(data, PRIMARY, primary)
                set_cell(data, FALLBACK, fallback)
                with mock.patch.object(feishu, "run_cli", return_value=data):
                    self.assertEqual(feishu.read_intake_record(BASE, TABLE, RECORD)["attachments"], expected)

    def test_original_read_record_does_not_request_or_require_attachment_fields(self) -> None:
        data = record_table(attachments=False)
        with mock.patch.object(feishu, "run_cli", return_value=data) as run:
            result = feishu.read_record(BASE, TABLE, RECORD)
        self.assertNotIn("attachments", result)
        self.assertNotIn(PRIMARY, run.call_args.args[0])
        self.assertNotIn(FALLBACK, run.call_args.args[0])
        self.assertEqual(len(result["metadata"]), 10)
        self.assertEqual(len(result["briefings"]), 2)

    def test_missing_record_guard_precedes_null_row_or_attachment_parsing(self) -> None:
        for row in (None, [None] * 14):
            with self.subTest(row=row):
                data = record_table()
                data.update(data=[row], record_not_found=[RECORD])
                with mock.patch.object(feishu, "run_cli", return_value=data):
                    with self.assertRaisesRegex(ValueError, "no longer exists or is not accessible"):
                        feishu.read_intake_record(BASE, TABLE, RECORD)

    def test_missing_or_ambiguous_record_tables_are_rejected(self) -> None:
        variants = [
            {"record_id_list": [], "data": []},
            {"record_id_list": ["recOther"]},
            {"record_id_list": [RECORD, "recOther"], "data": [[None] * 14, [None] * 14]},
            {"data": [[]]}, {"data": None}, {"field_id_list": None},
        ]
        for changes in variants:
            with self.subTest(changes=changes):
                data = record_table()
                data.update(changes)
                with mock.patch.object(feishu, "run_cli", return_value=data):
                    with self.assertRaises(ValueError):
                        feishu.read_intake_record(BASE, TABLE, RECORD)

    def test_missing_required_columns_are_not_silently_empty(self) -> None:
        for missing in (PRIMARY, FALLBACK, feishu.FIELD_MAPPING["authors"][1], feishu.BRIEF_FIELDS["raw text"]):
            with self.subTest(missing=missing):
                data = record_table()
                index = data["field_id_list"].index(missing)
                data["field_id_list"].pop(index)
                data["data"][0].pop(index)
                with mock.patch.object(feishu, "run_cli", return_value=data):
                    with self.assertRaisesRegex(ValueError, "fields"):
                        feishu.read_intake_record(BASE, TABLE, RECORD)

    def test_malformed_attachment_structures_are_explicit_errors(self) -> None:
        malformed = [
            "", {}, [None], ["fileSynthetic"], [{}],
            [attachment(file_token=None)], [attachment(file_token="--as=bot")],
            [attachment(file_token="fileSynthetic & command")],
            [attachment(name=None)], [attachment(name=" ")], [attachment(name="bad\x00.pdf")],
            [attachment(size=None)], [attachment(size=-1)], [attachment(size=True)],
            [attachment(size="12")], [attachment(size=12.5)], [attachment(type={})],
        ]
        for cell in malformed:
            with self.subTest(cell=cell):
                data = record_table()
                set_cell(data, FALLBACK, cell)
                with mock.patch.object(feishu, "run_cli", return_value=data):
                    with self.assertRaisesRegex(ValueError, "attachment"):
                        feishu.read_intake_record(BASE, TABLE, RECORD)

    def test_invalid_record_identifiers_never_invoke_cli(self) -> None:
        with mock.patch.object(feishu, "run_cli") as run:
            for record in ("", None, False, "--record-id", "recOne;command"):
                with self.subTest(record=record), self.assertRaises(ValueError):
                    feishu.read_intake_record(BASE, TABLE, record)
        run.assert_not_called()


class FeishuRecordReferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.resolution = {"base_token": BASE, "table_id": TABLE, "record_id": RECORD, "resource_type": "bitable"}

    def test_raw_record_id_is_validated_without_cli_resolution(self) -> None:
        with mock.patch.object(feishu, "run_cli") as run:
            self.assertEqual(feishu.resolve_record_reference(BASE, TABLE, f" {RECORD}\n"), RECORD)
        run.assert_not_called()

    def test_url_is_passed_unchanged_to_cli_and_only_returned_coordinates_are_used(self) -> None:
        url = URL + "&from=reader;echo%20not-a-command"
        with mock.patch.object(feishu, "run_cli", return_value=self.resolution) as run:
            self.assertEqual(feishu.resolve_record_reference(BASE, TABLE, url, executable="chosen.exe"), RECORD)
        run.assert_called_once_with(["+url-resolve", "--url", url, "--format", "json"], executable="chosen.exe")

    def test_wiki_and_record_share_links_need_authoritative_resolution(self) -> None:
        for url in (
            "https://example.feishu.cn/wiki/SyntheticWiki",
            "https://example.larkoffice.com/share/base/record/SyntheticShare",
            "https://example.larksuite.com/base/SyntheticBase",
            "https://example.doubao.com/base/SyntheticBase",
        ):
            with self.subTest(url=url), mock.patch.object(feishu, "run_cli", return_value=self.resolution):
                self.assertEqual(feishu.resolve_record_reference(BASE, TABLE, url), RECORD)

    def test_mismatched_or_missing_base_table_is_rejected(self) -> None:
        for change in (
            {"base_token": "AnotherBase"}, {"table_id": "tblOther"},
            {"base_token": None}, {"table_id": None}, {"table_id": ["tblSynthetic"]},
            {"resource_type": "docx"},
        ):
            with self.subTest(change=change), mock.patch.object(feishu, "run_cli", return_value={**self.resolution, **change}):
                with self.assertRaisesRegex(ValueError, "Base"):
                    feishu.resolve_record_reference(BASE, TABLE, URL)

    def test_table_view_and_unsupported_record_id_query_urls_never_guess_a_record(self) -> None:
        for suffix in ("", "&view=vewSynthetic", "&record_id=recSynthetic"):
            url = f"https://example.feishu.cn/base/{BASE}?table={TABLE}{suffix}"
            data = {"base_token": BASE, "table_id": TABLE, "input_type": "base_url", "resource_type": "bitable"}
            with self.subTest(url=url), mock.patch.object(feishu, "run_cli", return_value=data):
                with self.assertRaisesRegex(ValueError, "did not resolve to a record ID"):
                    feishu.resolve_record_reference(BASE, TABLE, url)

    def test_invalid_or_ambiguous_resolved_record_identifiers_are_rejected(self) -> None:
        for record in (None, "", False, [RECORD], {"id": RECORD}, "--as=bot", "recOne,recTwo"):
            with self.subTest(record=record), mock.patch.object(feishu, "run_cli", return_value={**self.resolution, "record_id": record}):
                with self.assertRaises(ValueError):
                    feishu.resolve_record_reference(BASE, TABLE, URL)
        for extra in (
            {"record_id_list": [RECORD, "recOther"]},
            {"record_ids": ["recOther"]}, {"record_id_list": RECORD},
            {"record_id": None, "record_id_list": [RECORD]},
        ):
            with self.subTest(extra=extra), mock.patch.object(feishu, "run_cli", return_value={**self.resolution, **extra}):
                with self.assertRaises(ValueError):
                    feishu.resolve_record_reference(BASE, TABLE, URL)

    def test_ambiguous_query_selectors_are_rejected_before_cli(self) -> None:
        with mock.patch.object(feishu, "run_cli") as run:
            for suffix in ("&record=recOther", "&record_id=recOther", "&table=tblOther", "&view=vewOne&view=vewTwo"):
                with self.subTest(suffix=suffix), self.assertRaisesRegex(ValueError, "ambiguous"):
                    feishu.resolve_record_reference(BASE, TABLE, URL + suffix)
        run.assert_not_called()

    def test_unsafe_or_unsupported_references_are_rejected_before_cli(self) -> None:
        invalid = [
            "", None, False, "recOne & command", "--url=https://example.feishu.cn",
            URL.replace("https:", "http:"), "file:///C:/paper.pdf",
            URL.replace("example.feishu.cn", "example.feishu.cn.evil.invalid"),
            URL.replace("example.feishu.cn", "user:password@example.feishu.cn"),
            URL.replace("example.feishu.cn", "example.feishu.cn:444"),
            URL.replace("example.feishu.cn", "example.feishu.cn:bad"),
            URL + "#record=recOther", URL + "\n&from=other", URL + "\\other", "https://[",
        ]
        with mock.patch.object(feishu, "run_cli") as run:
            for reference in invalid:
                with self.subTest(reference=reference), self.assertRaises(ValueError):
                    feishu.resolve_record_reference(BASE, TABLE, reference)
            with self.assertRaises(ValueError):
                feishu.resolve_record_reference("bad;base", TABLE, RECORD)
        run.assert_not_called()


class FeishuAttachmentDownloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = Path(f".reader-feishu-intake-{uuid.uuid4().hex}").absolute()
        self.workspace.mkdir()
        self.addCleanup(shutil.rmtree, self.workspace)
        self.destination = self.workspace / "folder & spaces" / "selected.pdf"
        self.command = mock.patch.object(feishu, "cli_command", return_value="lark-cli.exe").start()
        self.run = mock.patch.object(feishu.subprocess, "run").start()
        self.addCleanup(mock.patch.stopall)
        self.run.side_effect = self.write_pdf

    def output_path(self, argv: list[str], **kwargs: object) -> Path:
        output = Path(argv[argv.index("--output") + 1])
        self.assertFalse(output.is_absolute())
        self.assertEqual(len(output.parts), 1)
        self.assertEqual(kwargs["cwd"], self.destination.parent)
        self.assertTrue(Path(kwargs["cwd"]).is_dir())
        return Path(kwargs["cwd"]) / output

    def write_pdf(self, argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        self.output_path(argv, **kwargs).write_bytes(PDF)
        return cli_success({"files": [{"name": "untrusted.pdf", "type": "application/pdf"}]})

    def download(self, **kwargs: object) -> Path:
        return feishu.download_record_attachment(BASE, TABLE, RECORD, "fileSynthetic", self.destination, **kwargs)

    def assert_no_staging_files(self) -> None:
        self.assertEqual(list(self.workspace.rglob(".feishu-download-*")), [])

    def test_downloads_only_selected_file_using_relative_output_cwd_and_no_shell(self) -> None:
        result = self.download(executable="chosen.exe")
        self.assertEqual(result, self.destination)
        self.assertEqual(result.read_bytes(), PDF)
        self.command.assert_called_once_with("chosen.exe")
        self.run.assert_called_once()
        argv = self.run.call_args.args[0]
        self.assertEqual(argv[:3], ["lark-cli.exe", "base", "+record-download-attachment"])
        self.assertEqual(argv.count("--file-token"), 1)
        self.assertEqual(argv[argv.index("--file-token") + 1], "fileSynthetic")
        self.assertEqual(argv[-2:], ["--as", "user"])
        self.assertEqual(self.run.call_args.kwargs["timeout"], 180)
        self.assertFalse(self.run.call_args.kwargs["shell"])
        self.assertNotIn(str(self.destination), argv)
        self.assert_no_staging_files()

    def test_output_overwrite_is_limited_to_our_exclusively_created_empty_staging_file(self) -> None:
        def download(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            output = self.output_path(argv, **kwargs)
            self.assertEqual(output.read_bytes(), b"")
            self.assertNotEqual(output, self.destination)
            self.assertFalse(self.destination.exists())
            self.assertIn("--overwrite", argv)
            output.write_bytes(PDF)
            return cli_success()
        self.run.side_effect = download
        self.download()
        self.assert_no_staging_files()

    def test_relative_destination_returns_absolute_verified_path(self) -> None:
        relative = self.destination.relative_to(Path.cwd())
        result = feishu.download_record_attachment(BASE, TABLE, RECORD, "fileSynthetic", relative)
        self.assertEqual(result, self.destination)
        self.assertTrue(result.is_absolute())

    def test_valid_pdf_bytes_do_not_require_a_pdf_destination_extension(self) -> None:
        self.destination = self.destination.with_name("--not-a-shell-command & attachment.bin")
        self.assertEqual(self.download().read_bytes(), PDF)

    def test_preexisting_destination_file_and_directory_are_preserved(self) -> None:
        self.destination.parent.mkdir()
        self.destination.write_bytes(b"original, not ours")
        with self.assertRaises(FileExistsError):
            self.download()
        self.assertEqual(self.destination.read_bytes(), b"original, not ours")
        self.destination.unlink()
        self.destination.mkdir()
        marker = self.destination / "preserve.txt"
        marker.write_bytes(b"preserve directory")
        with self.assertRaises(FileExistsError):
            self.download()
        self.assertEqual(marker.read_bytes(), b"preserve directory")
        self.run.assert_not_called()
        self.assert_no_staging_files()

    def test_preexisting_broken_symlink_is_preserved(self) -> None:
        self.destination.parent.mkdir()
        try:
            self.destination.symlink_to(self.workspace / "nonexistent.pdf")
        except (OSError, NotImplementedError):
            self.skipTest("Creating symlinks is unavailable on this machine.")
        with self.assertRaises(FileExistsError):
            self.download()
        self.assertTrue(self.destination.is_symlink())
        self.run.assert_not_called()

    def test_existing_staging_path_is_not_overwritten_or_cleaned_up(self) -> None:
        self.destination.parent.mkdir()
        staging = self.destination.parent / ".feishu-download-collision.part"
        staging.write_bytes(b"not our staging file")
        with mock.patch.object(feishu.uuid, "uuid4", return_value=mock.Mock(hex="collision")):
            with self.assertRaises(FileExistsError):
                self.download()
        self.assertEqual(staging.read_bytes(), b"not our staging file")
        self.assertFalse(self.destination.exists())
        self.run.assert_not_called()

    def test_symlink_output_is_rejected_without_modifying_its_target(self) -> None:
        target = self.workspace / "preserved.pdf"
        target.write_bytes(PDF)
        def symlink_output(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            output = self.output_path(argv, **kwargs)
            output.unlink()
            try:
                output.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Creating symlinks is unavailable on this machine.")
            return cli_success()
        self.run.side_effect = symlink_output
        with self.assertRaisesRegex(ValueError, "regular PDF"):
            self.download()
        self.assertEqual(target.read_bytes(), PDF)
        self.assertFalse(self.destination.exists())
        self.assert_no_staging_files()

    def test_invalid_pdf_bytes_are_rejected_and_only_staging_is_removed(self) -> None:
        for payload in (b"", b"%PDF", b"<html>Not a PDF</html>", b"\x89PNG\r\n", b"prefix %PDF-1.7"):
            def download(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
                self.output_path(argv, **kwargs).write_bytes(payload)
                return cli_success({"files": [{"name": "paper.pdf", "type": "application/pdf"}]})
            with self.subTest(payload=payload):
                self.run.side_effect = download
                with self.assertRaisesRegex(ValueError, "PDF"):
                    self.download()
                self.assertFalse(self.destination.exists())
                self.assert_no_staging_files()

    def test_no_output_or_missing_output_is_not_a_successful_download(self) -> None:
        self.run.return_value = cli_success()
        self.run.side_effect = None
        with self.assertRaisesRegex(ValueError, "nonempty"):
            self.download()
        def no_output(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            self.output_path(argv, **kwargs).unlink()
            return cli_success()
        self.run.side_effect = no_output
        with self.assertRaisesRegex(ValueError, "nonempty"):
            self.download()
        self.assertFalse(self.destination.exists())
        self.assert_no_staging_files()

    def test_cli_error_timeout_and_startup_failure_clean_up_without_exposing_secrets(self) -> None:
        outcomes = [
            subprocess.CompletedProcess([], 1, stdout="", stderr=json.dumps({
                "ok": False, "error": {"type": "auth", "message": "SECRET_VALUE", "code": 123},
            })),
            subprocess.CompletedProcess([], 1, stdout="", stderr="SECRET_VALUE"),
            subprocess.CompletedProcess([], 1, stdout=json.dumps({
                "ok": False, "error": {"type": "SECRET_VALUE", "message": "SECRET_VALUE"},
            }), stderr=""),
            subprocess.TimeoutExpired(["SECRET_VALUE"], 180, stderr="SECRET_VALUE"),
            OSError("SECRET_VALUE"),
            UnicodeDecodeError("utf-8", b"\xff", 0, 1, "SECRET_VALUE"),
        ]
        for outcome in outcomes:
            def fail(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
                self.output_path(argv, **kwargs).write_bytes(b"partial")
                if isinstance(outcome, Exception):
                    raise outcome
                return outcome
            with self.subTest(outcome=type(outcome).__name__):
                self.run.side_effect = fail
                with self.assertRaises(RuntimeError) as caught:
                    self.download()
                self.assertNotIn("SECRET_VALUE", str(caught.exception))
                self.assertFalse(self.destination.exists())
                self.assert_no_staging_files()

    def test_destination_created_during_download_is_not_overwritten_or_cleaned_up(self) -> None:
        for success in (True, False):
            def concurrent_file(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess:
                self.output_path(argv, **kwargs).write_bytes(PDF)
                self.destination.write_bytes(b"created independently")
                if not success:
                    raise subprocess.TimeoutExpired([], 180)
                return cli_success()
            with self.subTest(success=success):
                self.run.side_effect = concurrent_file
                with self.assertRaises(FileExistsError if success else RuntimeError):
                    self.download()
                self.assertEqual(self.destination.read_bytes(), b"created independently")
                self.assert_no_staging_files()
                self.destination.unlink()

    def test_publish_failure_removes_our_download_without_exposing_system_error(self) -> None:
        with mock.patch.object(feishu.os, "link", side_effect=OSError("SECRET_VALUE")):
            with self.assertRaisesRegex(RuntimeError, "Could not save") as caught:
                self.download()
        self.assertNotIn("SECRET_VALUE", str(caught.exception))
        self.assertFalse(self.destination.exists())
        self.assert_no_staging_files()

    def test_invalid_identifiers_are_rejected_before_creating_files_or_invoking_cli(self) -> None:
        invalid_arguments = [
            ("bad;command", TABLE, RECORD, "fileSynthetic"),
            (BASE, "tblOne --as bot", RECORD, "fileSynthetic"),
            (BASE, TABLE, "", "fileSynthetic"),
            (BASE, TABLE, None, "fileSynthetic"),
            (BASE, TABLE, "recOne & command", "fileSynthetic"),
        ]
        invalid_arguments.extend((BASE, TABLE, RECORD, token) for token in (
            "", None, False, "--as", "../file", 'file"token', "fileToken\ncommand", "fileToken;command",
        ))
        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                feishu.download_record_attachment(*arguments, self.destination)
        self.assertFalse(self.destination.parent.exists())
        self.run.assert_not_called()

    def test_existing_run_cli_default_timeout_remains_compatible(self) -> None:
        self.run.side_effect = None
        self.run.return_value = cli_success()
        keyword = 'A title & "not a command"'
        feishu.run_cli(["+record-search", "--keyword", keyword])
        self.assertEqual(self.run.call_args.kwargs["timeout"], 45)
        self.assertIsNone(self.run.call_args.kwargs["cwd"])
        self.assertIn(keyword, self.run.call_args.args[0])
        self.assertFalse(self.run.call_args.kwargs["shell"])


class FeishuCliPathTests(unittest.TestCase):
    def test_native_cli_path_is_absolute_before_changing_download_cwd(self) -> None:
        with mock.patch.object(feishu.shutil, "which", return_value=str(Path("relative") / "lark-cli.cmd")):
            with mock.patch.object(feishu.Path, "is_file", return_value=True):
                command = feishu.cli_command()
        self.assertTrue(Path(command).is_absolute())
        self.assertNotEqual(Path(command).suffix, ".cmd")


if __name__ == "__main__":
    unittest.main()
