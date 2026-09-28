"""Explicit, local-first publication of reading snapshots; never generates content.

Only preview/start contact Feishu. A confirmed start runs in a background thread;
status only reads local state. The journal is a receipt, not a startup work queue.
Table mode keeps separate cell receipts, shares immutable backups with legacy
Docx mode, and writes four single-writer cells using a controlled UTF-8 @file.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import time
from typing import Any
from urllib.parse import urlsplit
import uuid
import xml.etree.ElementTree as ET

import feishu_metadata
from reading_archive import TABLE_COLUMN_NAMES, archive_fingerprint, build_archive, build_table_archive


STATE_DIRECTORY = ".feishu-publication"
JOURNAL_FILENAME = "journal.json"
TABLE_JOURNAL_FILENAME = "table-journal.json"
TABLE_TEXT_LIMIT = 100_000
TABLE_WRITE_WARNING = (
    "Reader-managed, single-writer columns. Edit in the reader; avoid simultaneous changes in Feishu."
)
_CELL_VERIFY_DELAYS = (0.5, 1.0, 2.0, 4.0)
MAX_CHUNK_BYTES = 60_000
MAX_CHUNK_BLOCKS = 100
MAX_CREATE_TITLE_BYTES = 4_096
_INLINE_XML = {"a", "b", "em", "u", "del", "span", "code", "br", "latex", "cite", "time"}
_READING_FILES = {
    "metadata.json", "segments.json", "annotations.json", "thinking.json",
    "reading_progress.json", "outline.json", "takeaway_doc.json",
    "translation_state.json", "reading_teacher.json",
}
_STATUSES = {"idle", "publishing", "synced", "pending", "failed", "conflict", "interrupted", "recovery_required"}


class PublicationConflict(ValueError):
    """The preview, association, dedicated fields, or cloud revision has changed."""


class PublicationConfigurationError(ValueError):
    """The paper binding or dedicated field schema cannot safely be published."""


class PublicationStorageError(RuntimeError):
    """Local publication receipts could not be saved durably."""


class PublicationRecoveryRequired(RuntimeError):
    """A previous write may have succeeded; automatic repetition is unsafe."""


class PublicationCloudError(RuntimeError):
    """A cloud operation failed or returned an explicitly partial result."""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _hash(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _token(value: Any, prefix: str = "") -> str:
    if not isinstance(value, str) or not re.fullmatch(re.escape(prefix) + r"[A-Za-z0-9]+", value):
        raise PublicationConfigurationError("Feishu returned an invalid resource identifier.")
    return value


def _regular(path: Path) -> None:
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        raise PublicationStorageError("Publication paths must not be symlinks or junctions.")


def _paper_path(value: Path) -> Path:
    path = Path(value).absolute()
    if ".." in path.parts:
        raise PublicationStorageError("Publication paths must not contain parent traversal.")
    for parent in (path, *path.parents):
        _regular(parent)
    if not path.is_dir():
        raise PublicationStorageError("The paper directory does not exist.")
    return path


def _path(paper: Path, name: str = "") -> Path:
    folder = paper / STATE_DIRECTORY
    _regular(paper)
    _regular(folder)
    if name and (Path(name).name != name or not re.fullmatch(r"[A-Za-z0-9_.-]+", name)):
        raise PublicationStorageError("Unsafe publication filename.")
    result = folder / name if name else folder
    _regular(result)
    return result


def _mode(value: dict) -> str:
    if not isinstance(value, dict):
        raise PublicationConfigurationError("Publication settings must be an object.")
    mode = value.get("mode", "document")
    if mode not in ("document", "table"):
        raise PublicationConfigurationError("Publication mode must be 'table' or 'document'.")
    return mode


def _field_name(name: Any) -> str:
    if not isinstance(name, str) or not name.strip() or len(name) > 200 or re.search(r"[\x00-\x1f\x7f]", name):
        raise PublicationConfigurationError("Configure nonempty dedicated publication field names.")
    return name


def _settings(value: dict) -> dict:
    mode = _mode(value)
    result = {
        "mode": mode,
        "base_token": value.get("base_token", ""), "table_id": value.get("table_id", ""),
        "executable": value.get("executable", ""), "parent_token": value.get("parent_token", ""),
        "archive_field": value.get("archive_field", "阅读档案"),
        "backup_field": value.get("backup_field", "阅读数据备份"),
    }
    try:
        feishu_metadata.validate_ids(result["base_token"], result["table_id"])
    except ValueError:
        raise PublicationConfigurationError("Configure the resolved Feishu Base token and table ID first.") from None
    for key in ("archive_field", "backup_field"):
        _field_name(result[key])
    if result["archive_field"] == result["backup_field"]:
        raise PublicationConfigurationError("Archive and backup must use different dedicated fields.")
    if not isinstance(result["executable"], str):
        raise PublicationConfigurationError("The configured CLI executable must be a path string.")
    if result["parent_token"]:
        _token(result["parent_token"])
    if mode == "table":
        names = value.get("text_fields", TABLE_COLUMN_NAMES)
        if not isinstance(names, dict) or set(names) != set(TABLE_COLUMN_NAMES):
            raise PublicationConfigurationError("Configure exactly the four reading-archive section field names.")
        result["text_fields"] = {key: _field_name(names[key]) for key in TABLE_COLUMN_NAMES}
        all_names = [*result["text_fields"].values(), result["backup_field"], result["archive_field"]]
        if len(all_names) != len(set(all_names)):
            raise PublicationConfigurationError("Text, backup and legacy archive fields must not alias one another.")
    return result


def _binding(raw: dict, settings: dict) -> dict:
    files = raw.get("files")
    if (raw.get("format") != "paper-reader-reading-data" or raw.get("version") != 1
            or not isinstance(files, dict) or set(files) - _READING_FILES):
        raise PublicationConfigurationError("Expected a lossless reading-data v1 snapshot containing only reading JSON files.")
    metadata = files.get("metadata.json")
    link = metadata.get("feishu") if isinstance(metadata, dict) else None
    if not isinstance(link, dict) or not link.get("record_id"):
        raise PublicationConfigurationError("Link this paper to its Feishu record before publishing.")
    if any(link.get(key) != settings[key] for key in ("base_token", "table_id")):
        raise PublicationConflict("The paper is bound to a different Feishu Base/table. Restore or explicitly change its association first.")
    try:
        feishu_metadata.validate_ids(settings["base_token"], settings["table_id"], link["record_id"])
    except ValueError:
        raise PublicationConfigurationError("The paper's Feishu record ID is invalid.") from None
    paper_id = raw.get("paper_id")
    if not isinstance(paper_id, str) or not paper_id:
        raise PublicationConfigurationError("The reading snapshot has no paper identity.")
    return {key: link[key] for key in ("base_token", "table_id", "record_id")} | {"paper_id": paper_id}


def _record_url(binding: dict) -> str:
    return (f"https://feishu.cn/base/{binding['base_token']}?table={binding['table_id']}&record={binding['record_id']}"
            if binding else "")


def _text_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(_text_cell(item) for item in value)
    if (isinstance(value, dict) and isinstance(value.get("text"), str)
            and set(value).issubset({"text", "type"}) and value.get("type", "text") == "text"):
        return value["text"]
    raise PublicationConflict("A dedicated plain-text cell returned an unsupported value; it was not overwritten.")


def _cell_hashes(values: dict) -> dict:
    return {key: hashlib.sha256(value.encode("utf-8")).hexdigest() for key, value in values.items()}


def _table_archive(raw: dict) -> dict:
    archive = build_table_archive(raw)
    columns = archive.get("columns")
    if (not isinstance(columns, list) or len(columns) != len(TABLE_COLUMN_NAMES)
            or any(not isinstance(column, dict) for column in columns)
            or {column.get("id") for column in columns} != set(TABLE_COLUMN_NAMES)):
        raise PublicationConfigurationError("The table formatter must return exactly the four reading sections.")
    for column in columns:
        text = column.get("text")
        if not isinstance(text, str):
            raise PublicationConfigurationError("Each reading-archive column must contain literal plain text.")
        try:
            units = len(text.encode("utf-16-le")) // 2
        except UnicodeEncodeError:
            raise PublicationConfigurationError("A reading-archive cell contains invalid Unicode.") from None
        if units > TABLE_TEXT_LIMIT:
            raise PublicationConfigurationError(
                "A reading-archive cell exceeds 100,000 UTF-16 units. Split the saved records before publishing; no text was truncated."
            )
        if (not isinstance(column.get("characters"), int) or isinstance(column["characters"], bool)
                or column["characters"] != units or column.get("limit") != TABLE_TEXT_LIMIT):
            raise PublicationConfigurationError("The table formatter's cell-size receipt is inconsistent.")
    return archive


def _record_fields(state: dict) -> list[str]:
    if state.get("mode") == "table":
        return [field["id"] for field in state["text_fields"]] + [state["backup_field"]["id"]]
    return [state[key]["id"] for key in ("archive_field", "backup_field")]


def _document_url(value: Any, document_id: str = "") -> str:
    if not isinstance(value, str):
        raise PublicationConflict("The archive field is not a single document URL.")
    try:
        url = urlsplit(value)
        host = url.hostname or ""
        match = re.fullmatch(r"/docx/([A-Za-z0-9]+)", url.path)
        valid = (url.scheme == "https" and not url.username and not url.password and not url.fragment
                 and not url.query and url.port in (None, 443)
                 and any(host == domain or host.endswith("." + domain)
                         for domain in ("feishu.cn", "larkoffice.com", "larksuite.com"))
                 and not re.search(r"[\s\\\x00-\x1f\x7f]", value) and match)
    except ValueError:
        valid = False
    if not valid or (document_id and match.group(1) != document_id):
        raise PublicationConflict("The archive field/document URL is unrelated or unsafe; it was not overwritten.")
    return value


def _link_cell(value: Any) -> str:
    if value is None or value == "" or value == []:
        return ""
    if isinstance(value, list) and len(value) == 1:
        return _link_cell(value[0])
    if isinstance(value, dict):
        keys = [key for key in ("link", "url") if key in value]
        if keys:
            urls = [_link_cell(value[key]) for key in keys]
            if len(set(urls)) != 1:
                raise PublicationConflict("The archive field contains ambiguous URL values.")
            return urls[0]
        if "text" in value:
            return _link_cell(value["text"])
        raise PublicationConflict("The archive field returned an unrecognized cell value; it was not overwritten.")
    if isinstance(value, str):
        match = re.fullmatch(r"\[[^\]]*\]\((https://[^)]+)\)", value)
        return _document_url(match.group(1) if match else value)
    raise PublicationConflict("The archive field is not a single URL; preserve it and check the dedicated field.")


def _xml_root(content: str) -> ET.Element:
    if not isinstance(content, str) or re.search(r"<!DOCTYPE|<!ENTITY", content, re.I):
        raise PublicationCloudError("Document XML is invalid or contains unsupported declarations.")
    try:
        return ET.fromstring("<publication-root>" + content + "</publication-root>")
    except ET.ParseError:
        raise PublicationCloudError("Document XML could not be verified. No unverified revision will be overwritten.") from None


def _content_hash(content: str) -> str:
    # Full fetch adds block IDs and default presentation attributes. Text, order,
    # links and resource identities remain part of the verification signature.
    ignored = {"id", "block-id", "align", "text-color", "background-color", "border-color", "seq"}
    text_containers = {"p", "title", "li", "b", "em", "u", "del", "a", "span", "code", "pre", "latex",
                       "checkbox", *("h" + str(level) for level in range(1, 10))}

    def node(element: ET.Element) -> Any:
        text = element.text or ""
        if len(element) and not text.strip() and element.tag not in text_containers:
            text = ""
        children = []
        for child in element:
            tail = child.tail or ""
            if not tail.strip() and element.tag not in text_containers:
                tail = ""
            children.append([node(child), tail.replace("\r\n", "\n")])
        return [element.tag, {key: val for key, val in element.attrib.items() if key not in ignored},
                text.replace("\r\n", "\n"), children]

    return _hash(node(_xml_root(content)))


def _owner(binding: dict) -> str:
    return "paper-reader:owner:" + _hash(binding)


def _owns(content: str, owner: str) -> bool:
    return owner in "".join(_xml_root(content).itertext())


def _block_count(element: ET.Element) -> int:
    return sum(node.tag not in _INLINE_XML and node.tag != "publication-root" for node in element.iter())


def _fits_block(element: ET.Element) -> bool:
    return (len(ET.tostring(element, encoding="utf-8")) <= MAX_CHUNK_BYTES
            and _block_count(element) <= MAX_CHUNK_BLOCKS)


def _bounded_blocks(element: ET.Element) -> list[ET.Element]:
    if _fits_block(element):
        return [element]
    message = ("A single archive XML block exceeds the safe chunk limits. Split it into smaller text blocks "
               "before publishing; no cloud writes were attempted.")
    if element.tag not in {"blockquote", "ul", "ol"} or not len(element):
        raise PublicationConfigurationError(message)
    # Long quotes/lists can span calls at child-block boundaries without
    # truncating text, splitting an XML element, or losing the quote/list role.
    result = []
    group = ET.Element(element.tag, dict(element.attrib))
    group.text, group.tail = element.text, element.tail
    for child in element:
        for unit in _bounded_blocks(child):
            group.append(unit)
            if _fits_block(group):
                continue
            group.remove(unit)
            if not _fits_block(group):
                raise PublicationConfigurationError(message)
            if len(group) or (group.text and group.text.strip()):
                group.tail = None
                result.append(group)
            group = ET.Element(element.tag, dict(element.attrib))
            group.tail = element.tail
            group.append(unit)
            if not _fits_block(group):
                raise PublicationConfigurationError(message)
    if len(group) or (group.text and group.text.strip()):
        result.append(group)
    return result


def _chunks(archive: dict, binding: dict, fingerprint: str) -> list[str]:
    root = _xml_root(archive["xml"])
    forbidden = {"img", "source", "whiteboard", "sheet", "bitable", "task", "button", "iframe", "script"}
    if any(element.tag in forbidden for element in root.iter()):
        raise PublicationConfigurationError("Publication is text-only; the archive contains an unsupported resource block.")
    title = root.find("title")
    if title is None:
        raise PublicationConfigurationError("The archive formatter did not return a document title.")
    parts = [
        ET.tostring(title, encoding="unicode"),
        "<p>" + _owner(binding) + "</p>",
        "<p>paper-reader:snapshot:" + fingerprint + "</p>",
    ]
    parts.extend(ET.tostring(unit, encoding="unicode") for element in root if element.tag != "title"
                 for unit in _bounded_blocks(element))
    parts.append("<p>paper-reader:complete:" + fingerprint + "</p>")
    result, current, size, blocks = [], [], 0, 0
    for part in parts:
        part_size = len(part.encode("utf-8"))
        part_blocks = _block_count(_xml_root(part))
        if part_size > MAX_CHUNK_BYTES or part_blocks > MAX_CHUNK_BLOCKS:
            raise PublicationConfigurationError("An archive title/block exceeds the safe XML chunk limits; split it before publishing.")
        separator = 1 if current else 0
        if current and (size + separator + part_size > MAX_CHUNK_BYTES or blocks + part_blocks > MAX_CHUNK_BLOCKS):
            result.append("\n".join(current))
            current, size, blocks = [], 0, 0
            separator = 0
        current.append(part)
        size += separator + part_size
        blocks += part_blocks
    if current:
        result.append("\n".join(current))
    return result


_TABLE_WRITE_LOCKS = {}
_TABLE_WRITE_GUARD = threading.Lock()


def _table_write_lock(base_token: str, table_id: str):
    # Base rejects concurrent writes even when they address different records.
    # Share the gate across jobs, clients, and service instances in this reader.
    with _TABLE_WRITE_GUARD:
        return _TABLE_WRITE_LOCKS.setdefault((base_token, table_id), threading.RLock())


class FeishuPublicationClient:
    """Small CLI adapter. Every call uses the existing native, shell-free runner."""

    def __init__(self, settings: dict) -> None:
        self.settings = settings
        self.warnings: list[str] = []

    def _call(self, service: str, arguments: list[str], *, content: str | None = None,
              write: bool = False, cwd: Path | None = None) -> dict:
        try:
            envelope = feishu_metadata.run_cli(
                arguments + ["--format", "json"], executable=self.settings["executable"],
                service=service, input_text=content, write=write, full_response=True,
                cwd=cwd, timeout=180 if write or cwd else 60,
            )
        except feishu_metadata.FeishuCLIError as error:
            self._diagnostics(error.response)
            raise
        self._diagnostics(envelope)
        return envelope["data"]

    def _diagnostics(self, envelope: dict) -> None:
        # Never echo arbitrary CLI messages: they can contain auth tokens or URLs.
        for source in (envelope, envelope.get("data", {})):
            if not isinstance(source, dict):
                continue
            for key in ("warnings", "degrade_details", "ignored_fields", "permission_grant", "_notice"):
                value = source.get(key)
                if value:
                    count = len(value) if isinstance(value, (list, dict)) else 1
                    warning = f"Feishu CLI reported {key} ({count}); inspect the CLI locally for details."
                    if warning not in self.warnings:
                        self.warnings.append(warning)

    def _base(self, command: str, *arguments: str, **kwargs: Any) -> dict:
        argv = [command, "--base-token", self.settings["base_token"],
                "--table-id", self.settings["table_id"], *arguments]
        if kwargs.get("write"):
            with _table_write_lock(self.settings["base_token"], self.settings["table_id"]):
                return self._call("base", argv, **kwargs)
        return self._call("base", argv, **kwargs)

    def fields(self) -> list[dict]:
        result, offset = [], 0
        while offset < 10_000:
            data = self._base("+field-list", "--limit", "200", "--offset", str(offset))
            fields = data.get("fields", data.get("items"))
            if not isinstance(fields, list) or any(not isinstance(field, dict) for field in fields):
                raise PublicationConfigurationError("Feishu returned an invalid dedicated-field schema.")
            result.extend(fields)
            if not data.get("has_more"):
                return result
            if not fields:
                break
            offset += len(fields)
        raise PublicationConfigurationError("Feishu field pagination was incomplete; no writes were attempted.")

    def record(self, record_id: str, field_ids: list[str]) -> dict:
        arguments = ["--record-id", record_id]
        for field_id in field_ids:
            arguments.extend(["--field-id", field_id])
        data = self._base("+record-get", *arguments)
        if record_id in (data.get("record_not_found") or []):
            raise PublicationConflict("The linked record was removed or is not accessible.")
        records = feishu_metadata.records_from_result(data)
        if (len(records) != 1 or records[0]["record_id"] != record_id
                or not set(field_ids).issubset(records[0]["fields"])):
            raise PublicationConflict("Feishu did not return the exact linked record and dedicated field IDs.")
        return records[0]["fields"]

    def fetch_document(self, document_id: str) -> dict:
        data = self._call("docs", ["+fetch", "--api-version", "v2", "--doc", document_id,
                                   "--doc-format", "xml", "--detail", "full"])
        document = data.get("document")
        if (not isinstance(document, dict) or document.get("document_id") != document_id
                or isinstance(document.get("revision_id"), bool)
                or not isinstance(document.get("revision_id"), int) or document["revision_id"] < 0
                or not isinstance(document.get("content"), str)):
            raise PublicationCloudError("Feishu did not return the full document identity, content, and revision.")
        return document

    def create_document(self, content: str) -> dict:
        arguments = ["+create", "--api-version", "v2", "--doc-format", "xml", "--content", "-"]
        if self.settings["parent_token"]:
            arguments += ["--parent-token", self.settings["parent_token"]]
        return self._call("docs", arguments, content=content, write=True)

    def update_document(self, document_id: str, revision: int, content: str, command: str) -> dict:
        return self._call("docs", [
            "+update", "--api-version", "v2", "--doc", document_id, "--doc-format", "xml",
            "--command", command, "--revision-id", str(revision), "--content", "-",
        ], content=content, write=True)

    def upload(self, binding: dict, field_id: str, path: Path) -> dict:
        _regular(path)
        if not path.is_file():
            raise PublicationStorageError("The immutable reading backup is missing.")
        return self._base("+record-upload-attachment", "--record-id", binding["record_id"],
                          "--field-id", field_id, "--file", path.name, write=True, cwd=path.parent)

    def download(self, binding: dict, file_token: str, path: Path) -> None:
        _token(file_token)
        _regular(path)
        if path.exists():
            raise PublicationStorageError("Attachment verification refuses to overwrite an existing file.")
        self._base("+record-download-attachment", "--record-id", binding["record_id"],
                   "--file-token", file_token, "--output", path.name, cwd=path.parent)

    def link(self, binding: dict, field_id: str, url: str) -> dict:
        return self._base("+record-upsert", "--record-id", binding["record_id"],
                          "--json", _json({field_id: url}), write=True)

    def write_cells(self, binding: dict, path: Path, digest: str) -> dict:
        _regular(path)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise PublicationStorageError("The controlled text-cell request changed before CLI use; no PATCH was attempted.")
        return self._base("+record-upsert", "--record-id", binding["record_id"],
                          "--json", "@" + path.name, write=True, cwd=path.parent)


class _Runtime:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.thread: threading.Thread | None = None
        self.shadow: dict | None = None
        self.previews: dict[str, str] = {}


_RUNTIMES: dict[str, _Runtime] = {}
_RUNTIME_LOCK = threading.Lock()


def _runtime(paper: Path) -> _Runtime:
    with _RUNTIME_LOCK:
        return _RUNTIMES.setdefault(os.path.normcase(str(paper)), _Runtime())


def _lease(path: Path):
    """An OS-held lock prevents two reader processes from publishing one paper."""
    _regular(path)
    try:
        stream = path.open("a+b")
    except OSError:
        raise PublicationStorageError("Cannot acquire the local publication lock. Check paper-directory write permission.") from None
    try:
        if os.name == "nt":
            import msvcrt
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        stream.close()
        return None
    return stream


def _release(stream) -> None:
    if stream is None:
        return
    try:
        if os.name == "nt":
            import msvcrt
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass
    finally:
        stream.close()


def _idle(mode: str = "document") -> dict:
    result = {"version": 1, "status": "idle", "phase": "", "error": "", "document_url": "",
              "published_at": "", "fingerprint": "", "job_id": "", "warnings": []}
    if mode == "table":
        result.update(mode="table", record_url="", legacy_document_url="")
    return result


class PublicationService:
    def __init__(self, *, snapshot_reader, json_reader, json_writer, text_writer) -> None:
        self.snapshot_reader = snapshot_reader
        self.json_reader = json_reader
        self.json_writer = json_writer
        self.text_writer = text_writer

    def _raw(self, paper: Path) -> dict:
        try:
            for name in _READING_FILES:
                _regular(paper / name)
            raw = self.snapshot_reader(paper)
            if not isinstance(raw, dict):
                raise ValueError()
            return json.loads(_json(raw))
        except (OSError, ValueError, TypeError):
            raise PublicationStorageError("Reading data could not be read losslessly. Repair invalid/missing JSON before publishing.") from None

    def _read(self, path: Path, default: Any) -> Any:
        _regular(path)
        try:
            return self.json_reader(path, default, strict=True)
        except (OSError, ValueError, TypeError):
            raise PublicationStorageError("A publication receipt is unreadable. Preserve it and repair local storage before retrying.") from None

    def _state(self, paper: Path, mode: str = "document") -> dict:
        name = TABLE_JOURNAL_FILENAME if mode == "table" else JOURNAL_FILENAME
        state = self._read(_path(paper, name), None)
        if state is None:
            if mode == "table":
                legacy = self._read(_path(paper, JOURNAL_FILENAME), None)
                if legacy is not None:
                    if not isinstance(legacy, dict) or legacy.get("version") != 1 or legacy.get("status") not in _STATUSES:
                        raise PublicationStorageError("The legacy publication journal is invalid; recover it before migrating backup receipts.")
                    state = _idle("table")
                    for key in ("binding", "backup_field", "backups"):
                        if key in legacy:
                            state[key] = copy.deepcopy(legacy[key])
                    if (state.get("backups") or legacy.get("document_id")) and not state.get("binding"):
                        raise PublicationStorageError("Legacy receipts have no paper/record binding; they cannot be adopted safely.")
                    if legacy.get("document_url"):
                        state["legacy_document_url"] = _document_url(legacy["document_url"], legacy.get("document_id", ""))
                    state["record_url"] = _record_url(state.get("binding", {}))
                    state["legacy_journal_hash"] = _hash(legacy)
                    pending = legacy.get("pending_write") or {}
                    if pending.get("kind") == "upload" and pending.get("name"):
                        state["uncertain_uploads"] = {pending["name"]: copy.deepcopy(pending)}
                    return state
            else:
                table = self._read(_path(paper, TABLE_JOURNAL_FILENAME), None)
                if table is not None:
                    if (not isinstance(table, dict) or table.get("version") != 1
                            or table.get("mode") != "table" or table.get("status") not in _STATUSES):
                        raise PublicationStorageError("The table journal is invalid; recover its shared backup receipts first.")
                    if table.get("legacy_document_url") or table.get("legacy_journal_hash"):
                        raise PublicationRecoveryRequired("The original document journal is missing. Recover it; do not create another legacy document.")
                    state = _idle()
                    for key in ("binding", "backup_field", "backups", "uncertain_uploads"):
                        if key in table:
                            state[key] = copy.deepcopy(table[key])
                    state["table_journal_hash"] = _hash(table)
                    return state
            if any(_path(paper).glob("reading-data-*.json")):
                raise PublicationRecoveryRequired("The publication journal is missing but immutable backups remain. Recover the original journal/document receipt before creating another.")
            return _idle(mode)
        if not isinstance(state, dict) or state.get("version") != 1 or state.get("status") not in _STATUSES:
            raise PublicationStorageError("The publication journal is invalid. Preserve it; do not start another cloud document.")
        if mode == "table" and state.get("mode") != "table":
            raise PublicationStorageError("The table publication journal has an invalid mode; it was not replaced.")
        return state

    def _save_json(self, paper: Path, name: str, value: dict) -> None:
        path = _path(paper, name)
        try:
            path.parent.mkdir(exist_ok=True)
            _regular(path.parent)
            self.json_writer(path, copy.deepcopy(value))
            if self._read(path, None) != value:
                raise ValueError()
        except (OSError, ValueError, TypeError, PublicationStorageError):
            raise PublicationStorageError("Could not durably save the publication journal/preview. Stop and repair local storage before retrying.") from None

    def _save(self, paper: Path, state: dict, **changes: Any) -> None:
        state.update(changes)
        runtime = _runtime(paper)
        with runtime.lock:
            runtime.shadow = copy.deepcopy(state)
            name = TABLE_JOURNAL_FILENAME if state.get("mode") == "table" else JOURNAL_FILENAME
            self._save_json(paper, name, state)

    def _resolve_fields(self, client: FeishuPublicationClient, settings: dict, previous: dict) -> dict:
        fields = client.fields()
        resolved = {}
        protected = {value[1] for value in feishu_metadata.FIELD_MAPPING.values()}
        protected.update(feishu_metadata.BRIEF_FIELDS.values())
        protected.update(feishu_metadata.ATTACHMENT_FIELDS.values())
        if settings["mode"] == "table":
            protected_names = {value[0] for value in feishu_metadata.FIELD_MAPPING.values()}
            protected_names.update(feishu_metadata.BRIEF_FIELDS)
            protected_names.update(feishu_metadata.ATTACHMENT_FIELDS)
            protected_names.add(settings["archive_field"])
            protected.update(field.get("id", field.get("field_id")) for field in fields
                             if field.get("name") == settings["archive_field"])
            text_fields = []
            for section_id, name in settings["text_fields"].items():
                if name in protected_names:
                    raise PublicationConflict("An original notes/Brief/metadata/archive field cannot be repurposed for table publication.")
                matches = [field for field in fields if field.get("name") == name]
                if len(matches) != 1:
                    error_type = PublicationConflict if previous.get("text_fields") else PublicationConfigurationError
                    raise error_type("Each configured reading-text column must exist exactly once; a managed column may have been renamed or removed.")
                field = matches[0]
                field_id = _token(field.get("id", field.get("field_id")), "fld")
                if (field_id in protected or field.get("field_id", field_id) != field_id
                        or sum(item.get("id", item.get("field_id")) == field_id for item in fields) != 1):
                    raise PublicationConflict("A reading-text column resolves to a protected or ambiguous field ID.")
                style = field.get("style")
                if style is None:
                    style = {}
                if (field.get("type") != "text" or not isinstance(style, dict)
                        or style.get("type", "plain") != "plain"):
                    error_type = PublicationConflict if previous.get("text_fields") else PublicationConfigurationError
                    raise error_type("All four reading-text columns must remain writable text fields with plain style.")
                text_fields.append({"section_id": section_id, "id": field_id, "name": name})
            if previous.get("text_fields") and previous["text_fields"] != text_fields:
                raise PublicationConflict("A managed reading-text column was renamed or replaced; its identity will not be overwritten.")
            resolved["text_fields"] = text_fields
            protected.update(field["id"] for field in text_fields)
        keys = ("backup_field",) if settings["mode"] == "table" else ("archive_field", "backup_field")
        for key in keys:
            candidates = [field for field in fields if field.get("name") == settings[key]]
            if len(candidates) != 1:
                if settings["mode"] == "table" and previous.get(key):
                    raise PublicationConflict("The managed backup field was renamed, removed or duplicated.")
                raise PublicationConfigurationError("Each configured dedicated publication field must exist exactly once; create/select it explicitly.")
            field = candidates[0]
            field_id = _token(field.get("id", field.get("field_id")), "fld")
            if field.get("field_id", field_id) != field_id or field_id in protected:
                raise PublicationConflict("A publication field resolves to a protected or ambiguous field ID.")
            if (key == "archive_field" and (field.get("type") != "text"
                    or not isinstance(field.get("style"), dict) or field["style"].get("type") != "url")):
                raise PublicationConfigurationError("The archive field must be a dedicated text field with style.type=url.")
            if key == "backup_field" and field.get("type") != "attachment":
                if settings["mode"] == "table" and previous.get(key):
                    raise PublicationConflict("The managed backup field no longer has attachment type.")
                raise PublicationConfigurationError("The backup field must be a dedicated attachment field.")
            resolved[key] = {"id": field_id, "name": settings[key]}
            if previous.get(key) and previous[key] != resolved[key]:
                raise PublicationConflict("A dedicated publication field was renamed/replaced. Its existing identity will not be overwritten.")
        if settings["mode"] == "document" and resolved["archive_field"]["id"] == resolved["backup_field"]["id"]:
            raise PublicationConflict("Archive and backup resolved to the same field.")
        return resolved

    @staticmethod
    def _cell_receipt(values: dict, fingerprint: str = "") -> dict:
        return {"values": copy.deepcopy(values), "hashes": _cell_hashes(values), "fingerprint": fingerprint}

    @staticmethod
    def _validate_cell_receipt(receipt: dict, field_ids: set[str]) -> dict:
        values = receipt.get("values") if isinstance(receipt, dict) else None
        if (not isinstance(values, dict) or set(values) != field_ids
                or any(not isinstance(value, str) for value in values.values())
                or receipt.get("hashes") != _cell_hashes(values)):
            raise PublicationStorageError("The saved text-cell receipt is invalid. Recover it rather than adopting cloud contents.")
        return values

    def _table_cloud(self, client: FeishuPublicationClient, settings: dict, binding: dict, state: dict) -> dict:
        if state.get("binding") and state["binding"] != binding:
            raise PublicationConflict("The saved publication belongs to a different paper/record binding.")
        fields = self._resolve_fields(client, settings, state)
        ids = [field["id"] for field in fields["text_fields"]]
        record = client.record(binding["record_id"], ids + [fields["backup_field"]["id"]])
        values = {field_id: record[field_id] for field_id in ids}
        cells = {field_id: _text_cell(value) for field_id, value in values.items()}
        receipt = state.get("cell_receipt")
        previous = self._validate_cell_receipt(receipt, set(ids)) if receipt is not None else None
        pending = state.get("pending_write") or {}
        recovered = None
        if pending.get("kind") == "cells":
            after = self._validate_cell_receipt(pending.get("after"), set(ids))
            before = self._validate_cell_receipt(pending.get("before"), set(ids))
            if cells == after and pending.get("outcome") != "rejected":
                recovered = copy.deepcopy(pending["after"])
                client.warnings.append("An uncertain four-cell PATCH was recovered by verifying every expected text value; it will not be repeated.")
            elif pending.get("outcome") == "partial" and all(cells[key] in (before[key], after[key]) for key in cells):
                recovered = self._cell_receipt(cells)
                client.warnings.append("A recorded partial PATCH was reconciled to its exact expected partial values; any retry still requires a fresh confirmation.")
            elif pending.get("outcome") == "rejected" and cells == before:
                recovered = self._cell_receipt(cells, receipt.get("fingerprint", "") if receipt else "")
                client.warnings.append("A rejected PATCH was verified to have left the previous values unchanged.")
            elif cells == before:
                raise PublicationRecoveryRequired("The previous four-cell PATCH outcome is not verified. Wait/check the managed cells; it will not be blindly repeated.")
            else:
                raise PublicationConflict("The managed cells differ from both complete write receipts. Preserve cloud edits and resolve the partial/uncertain write explicitly.")
        elif previous is not None:
            if cells != previous:
                raise PublicationConflict("Reader-managed text cells were edited in Feishu. Those cloud edits will not be overwritten.")
        elif any(cells.values()):
            raise PublicationConflict("A configured text cell is nonempty without a trusted reader receipt. It cannot be adopted or overwritten.")
        return {**fields, "values": values, "cells": cells, "recovered_cells": recovered,
                "attachments": self._attachments(record[fields["backup_field"]["id"]])}

    @staticmethod
    def _attachments(value: Any) -> list[dict]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise PublicationConflict("The backup field returned invalid attachment data.")
        result = []
        for item in value:
            if (not isinstance(item, dict) or not isinstance(item.get("name"), str)
                    or not isinstance(item.get("size"), int) or isinstance(item["size"], bool) or item["size"] < 0):
                raise PublicationConflict("An attachment has no immutable name/token/size receipt.")
            result.append({"name": item["name"], "size": item["size"], "file_token": _token(item.get("file_token"))})
        if len({item["file_token"] for item in result}) != len(result):
            raise PublicationConflict("The backup field contains duplicate attachment tokens.")
        return result

    def _cloud(self, client: FeishuPublicationClient, settings: dict, binding: dict, state: dict) -> dict:
        if settings["mode"] == "table":
            return self._table_cloud(client, settings, binding, state)
        if state.get("binding") and state["binding"] != binding:
            raise PublicationConflict("The saved publication belongs to a different paper/record binding.")
        pending = state.get("pending_write") or {}
        if pending.get("kind") == "create" and not state.get("document_id"):
            raise PublicationRecoveryRequired("A document creation outcome is unknown. Find the previously created document and recover its receipt; do not create another.")
        fields = self._resolve_fields(client, settings, state)
        record = client.record(binding["record_id"], [fields[key]["id"] for key in ("archive_field", "backup_field")])
        link = _link_cell(record[fields["archive_field"]["id"]])
        attachments = self._attachments(record[fields["backup_field"]["id"]])
        document = None
        if state.get("document_id"):
            document_id = _token(state["document_id"])
            url = _document_url(state["document_url"], document_id)
            if link and link != url:
                raise PublicationConflict("The dedicated archive URL was changed in Feishu. It will not be overwritten.")
            if state.get("linked") and not link:
                raise PublicationConflict("The previously published archive link was cleared. Review the record before republishing.")
            document = client.fetch_document(document_id)
            if not _owns(document["content"], _owner(binding)):
                raise PublicationConflict("The cloud document has no matching paper/binding ownership marker.")
            digest = _content_hash(document["content"])
            revision = document["revision_id"]
            exact_receipt = revision == state.get("revision_id") and digest == state.get("document_hash")
            recovered = pending.get("kind") == "document" and (
                digest == pending.get("after_hash") and revision > pending.get("before_revision", revision)
            )
            recovered_create = pending.get("kind") == "create" and digest == pending.get("after_hash")
            if not exact_receipt and not recovered and not recovered_create:
                raise PublicationConflict("The cloud document revision/content changed outside this publication. Preserve those edits; do not overwrite.")
            if recovered:
                client.warnings.append("An uncertain document write was recovered by verifying its complete content and revision.")
            if recovered_create:
                client.warnings.append("The known created document was recovered by verifying its complete initial ownership-marked content.")
            document_fingerprint = (state.get("document_fingerprint", "") if exact_receipt
                                    else pending.get("fingerprint", "") if recovered and pending.get("final") else "")
            document = {"document_id": document_id, "revision_id": revision, "hash": digest,
                        "complete": bool(document_fingerprint), "fingerprint": document_fingerprint}
        elif link:
            raise PublicationConflict("The archive field already links a document without a local ownership receipt. It was not adopted or overwritten.")
        return {**fields, "link": link, "attachments": attachments, "document": document}

    def preview(self, paper_dir: Path, settings: dict) -> dict:
        paper, settings = _paper_path(paper_dir), _settings(settings)
        runtime = _runtime(paper)
        with runtime.lock:
            if runtime.thread and runtime.thread.is_alive():
                raise PublicationConflict("Publication is already running; wait for its status before previewing again.")
            state = self._state(paper, settings["mode"])
            state_hash = _hash(state)
        raw = self._raw(paper)
        binding = _binding(raw, settings)
        fingerprint = archive_fingerprint(raw)
        archive = _table_archive(raw) if settings["mode"] == "table" else build_archive(raw)
        chunks = [] if settings["mode"] == "table" else _chunks(archive, binding, fingerprint)
        client = FeishuPublicationClient(settings)
        cloud = self._cloud(client, settings, binding, state)
        warnings = list(archive.get("warnings") or []) + client.warnings
        if state["status"] in {"failed", "conflict", "interrupted", "recovery_required", "publishing"}:
            warnings.append("A previous attempt did not finish. Only verified existing document/backup receipts will be reused.")
        if (state.get("pending_write") or {}).get("kind") == "upload":
            warnings.append("An earlier attachment upload needs content verification; it will not be blindly repeated.")
        if state.get("uncertain_uploads"):
            warnings.append("An earlier backup upload may still be unresolved. Matching registered content is verified before reuse, never blindly uploaded again.")
        preview_id = uuid.uuid4().hex
        public = {
            "preview_id": preview_id, "fingerprint": fingerprint, "counts": archive["counts"],
            "sections": archive["sections"], "warnings": warnings,
            "snapshot_bytes": len(_json(raw).encode("utf-8")),
            "destination": {"record_id": binding["record_id"], "record_url": _record_url(binding),
                            "title": archive["title"], "backup_field": cloud["backup_field"]},
        }
        backup_matches = any(all(item[key] == (state.get("backups") or {}).get(fingerprint, {}).get(key)
                                 for key in ("name", "size", "file_token")) for item in cloud["attachments"])
        if settings["mode"] == "table":
            warnings.append(TABLE_WRITE_WARNING)
            identities = {field["section_id"]: field for field in cloud["text_fields"]}
            columns = [{**column, "name": identities[column["id"]]["name"],
                        "field_id": identities[column["id"]]["id"]} for column in archive["columns"]]
            targets = {column["field_id"]: column["text"] for column in columns}
            public.update(mode="table", columns=columns, changed=not (
                state.get("published_fingerprint") == fingerprint and state.get("cell_receipt")
                and cloud["cells"] == targets and backup_matches))
            public["destination"].update(
                mode="table", legacy_document_url=state.get("legacy_document_url", ""),
                text_fields=[{"section_id": column["id"], "id": column["field_id"], "name": column["name"],
                              "characters": column["characters"], "limit": column["limit"]} for column in columns],
            )
        else:
            public["changed"] = not (state.get("published_fingerprint") == fingerprint and cloud["document"]
                                     and cloud["document"]["fingerprint"] == fingerprint and cloud["link"] and backup_matches)
            public["destination"].update(archive_field=cloud["archive_field"], document_url=state.get("document_url", ""))
        saved = {"version": 1, "public": public, "raw": raw, "binding": binding, "settings_hash": _hash(settings),
                 "cloud": cloud, "chunks": chunks, "journal_hash": state_hash}
        with runtime.lock:
            if (runtime.thread and runtime.thread.is_alive()) or _hash(self._state(paper, settings["mode"])) != state_hash:
                raise PublicationConflict("Publication changed while previewing. Generate a fresh preview.")
            name = f"preview-{preview_id}.json"
            if _path(paper, name).exists():
                raise PublicationStorageError("An immutable preview already exists; it was not replaced.")
            self._save_json(paper, name, saved)
            runtime.previews[preview_id] = _hash(saved)
        return copy.deepcopy(public)

    def _public_status(self, state: dict) -> dict:
        keys = ("status", "phase", "error", "error_type", "next_action", "document_url", "published_at",
                "fingerprint", "published_fingerprint", "job_id", "warnings", "preview_id", "storage_error",
                "mode", "record_url", "legacy_document_url")
        result = {key: copy.deepcopy(state[key]) for key in keys if key in state}
        return {key: value for key, value in _idle().items() if key != "version"} | result

    def status(self, paper_dir: Path, settings: dict) -> dict:
        paper = _paper_path(paper_dir)
        mode = _mode(settings)
        runtime = _runtime(paper)
        with runtime.lock:
            if runtime.shadow and ((runtime.thread and runtime.thread.is_alive()) or runtime.shadow.get("storage_error")):
                state = copy.deepcopy(runtime.shadow)
                if mode == "table" and state.get("mode") != "table":
                    state.update(mode="table", legacy_document_url=state.get("document_url", ""),
                                 document_url="", record_url=_record_url(state.get("binding", {})))
                return self._public_status(state)
            try:
                state = self._state(paper, mode)
            except (PublicationStorageError, PublicationRecoveryRequired) as error:
                return self._public_status({**_idle(mode), "status": "recovery_required",
                                            "error": str(error), "next_action": "repair_local_journal"})
        if mode == "table" and not state.get("record_url"):
            try:
                state["record_url"] = _record_url(_binding(self._raw(paper), _settings(settings)))
            except (PublicationConflict, PublicationConfigurationError, PublicationStorageError) as error:
                state.update(status="conflict" if isinstance(error, ValueError) else "failed",
                             error=str(error), next_action="repair_local_data_or_binding")
        if state["status"] == "publishing":
            stream = _lease(_path(paper, "job.lock"))
            if stream is None:
                return self._public_status(state)
            _release(stream)
            ambiguous_create = (state.get("pending_write") or {}).get("kind") == "create" and not state.get("document_id")
            state.update(status="recovery_required" if ambiguous_create else "interrupted",
                         error="Publication stopped before completion; no cloud writes were resumed.",
                         next_action="recover_created_document" if ambiguous_create else "preview_and_confirm_retry")
        elif state["status"] in {"synced", "pending"}:
            try:
                raw = self._raw(paper)
                current_binding = _binding(raw, _settings(settings))
                if current_binding != state.get("binding"):
                    raise PublicationConflict("The paper's association changed since publication.")
                configured = _settings(settings)
                fields_changed = (any((state.get(key) or {}).get("name") != configured[key]
                                      for key in ("archive_field", "backup_field")) if mode == "document"
                                  else ({field["section_id"]: field["name"] for field in state.get("text_fields", [])}
                                        != configured["text_fields"]
                                        or (state.get("backup_field") or {}).get("name") != configured["backup_field"]))
                if fields_changed:
                    raise PublicationConflict("The configured dedicated field names changed since publication.")
                state["status"] = "synced" if archive_fingerprint(raw) == state.get("published_fingerprint") else "pending"
                state["next_action"] = "" if state["status"] == "synced" else "preview_new_changes"
            except (PublicationConflict, PublicationConfigurationError, PublicationStorageError) as error:
                state.update(status="conflict" if isinstance(error, (ValueError, PublicationConflict)) else "failed",
                             error=str(error), next_action="repair_local_data_or_binding")
        return self._public_status(state)

    def start(self, paper_dir: Path, settings: dict, preview_id: str, confirmed: bool) -> dict:
        if confirmed is not True:
            raise PublicationConfigurationError("Explicit confirmation of the displayed publication preview is required.")
        if not isinstance(preview_id, str) or not re.fullmatch(r"[a-f0-9]{32}", preview_id):
            raise PublicationConflict("Invalid or expired preview. Generate a fresh preview.")
        paper, settings = _paper_path(paper_dir), _settings(settings)
        runtime = _runtime(paper)
        with runtime.lock:
            if runtime.thread and runtime.thread.is_alive():
                if (runtime.shadow and runtime.shadow.get("preview_id") == preview_id
                        and runtime.shadow.get("mode", "document") == settings["mode"]):
                    return self.status(paper, settings)
                raise PublicationConflict("Another publication for this paper is already running.")
            state = (runtime.shadow if runtime.shadow and runtime.shadow.get("storage_error")
                     else self._state(paper, settings["mode"]))
            if state.get("preview_id") == preview_id:
                return self.status(paper, settings)
            if runtime.thread and runtime.thread.is_alive():
                raise PublicationConflict("Another publication for this paper is already running.")
            if state.get("storage_error"):
                raise PublicationRecoveryRequired("A cloud receipt could not be saved. Repair the journal before starting another publication.")
            saved = self._read(_path(paper, f"preview-{preview_id}.json"), None)
            if not isinstance(saved, dict) or runtime.previews.get(preview_id) != _hash(saved):
                raise PublicationConflict("Preview was edited, expired, or belongs to an earlier reader session. Generate a fresh preview.")
            if saved["settings_hash"] != _hash(settings) or saved["journal_hash"] != _hash(state):
                raise PublicationConflict("Publication settings or saved receipts changed since preview. Generate a fresh preview.")
            raw = self._raw(paper)
            if _binding(raw, settings) != saved["binding"] or archive_fingerprint(raw) != saved["public"]["fingerprint"]:
                raise PublicationConflict("Reading data or the paper's Feishu binding changed since preview. Preview the current snapshot first.")
            stream = _lease(_path(paper, "job.lock"))
            if stream is None:
                raise PublicationConflict("Another reader process is publishing this paper. Wait for it to finish.")
            state = copy.deepcopy(state)
            state.update(status="publishing", phase="queued", error="", error_type="", next_action="",
                         job_id=uuid.uuid4().hex, preview_id=preview_id, fingerprint=saved["public"]["fingerprint"],
                         binding=saved["binding"], warnings=list(saved["public"]["warnings"]), mode=settings["mode"])
            if settings["mode"] == "table":
                state.update(document_url="", record_url=_record_url(saved["binding"]),
                             text_fields=copy.deepcopy(saved["cloud"]["text_fields"]),
                             backup_field=copy.deepcopy(saved["cloud"]["backup_field"]))
            try:
                self._save(paper, state)
                thread = threading.Thread(target=self._worker, args=(paper, settings, saved, state, stream),
                                          name="feishu-publication-" + state["job_id"][:8], daemon=True)
                runtime.thread = thread
                result = self._public_status(state)
                thread.start()
            except Exception:
                _release(stream)
                raise
            return result

    def _check_binding(self, paper: Path, settings: dict, binding: dict) -> None:
        if _binding(self._raw(paper), settings) != binding:
            raise PublicationConflict("The paper's association changed during publication; remaining cloud writes were stopped.")

    def _backup(self, paper: Path, raw: dict, binding: dict, fingerprint: str) -> tuple[Path, dict]:
        name = f"reading-data-{fingerprint}.json"
        path = _path(paper, name)
        if path.exists():
            backup = self._read(path, None)
            if (not isinstance(backup, dict) or backup.get("format") != "paper-reader-publication-backup"
                    or backup.get("version") != 1 or not isinstance(backup.get("manifest"), dict)
                    or backup["manifest"].get("fingerprint") != fingerprint
                    or backup["manifest"].get("binding") != binding
                    or not isinstance(backup.get("reading_data"), dict)
                    or _hash(backup["reading_data"]) != backup["manifest"].get("raw_sha256")
                    or archive_fingerprint(backup["reading_data"]) != fingerprint):
                raise PublicationStorageError("The immutable backup is invalid or was changed; preserve it and recover the original version.")
        else:
            backup = {
                "format": "paper-reader-publication-backup", "version": 1,
                "manifest": {"fingerprint": fingerprint, "raw_sha256": _hash(raw), "binding": binding},
                "reading_data": raw,
            }
            text = _json(backup)
            try:
                self.text_writer(path, text)
                _regular(path)
                if path.read_bytes() != text.encode("utf-8"):
                    raise ValueError()
            except (OSError, ValueError, TypeError):
                raise PublicationStorageError("The reading backup could not be saved exactly; no upload was attempted.") from None
        _regular(path)
        content = path.read_bytes()
        return path, {"name": name, "size": len(content), "sha256": hashlib.sha256(content).hexdigest()}

    def _remember_created(self, paper: Path, state: dict, data: dict) -> None:
        document = data.get("document")
        if not isinstance(document, dict) or not document.get("document_id"):
            raise PublicationRecoveryRequired("Document creation returned no usable identity. Locate the created document; do not retry creation blindly.")
        try:
            document_id = _token(document["document_id"])
        except PublicationConfigurationError:
            raise PublicationRecoveryRequired("Document creation returned an invalid identity. Locate the created document; do not create another.") from None
        url = document.get("url") or f"https://feishu.cn/docx/{document_id}"
        # Record the identity before validating any later part of the response.
        self._save(paper, state, document_id=document_id, document_url=f"https://feishu.cn/docx/{document_id}",
                   phase="document_created")
        url = _document_url(url, document_id)
        self._save(paper, state, document_url=url)

    def _document(self, paper: Path, settings: dict, client: FeishuPublicationClient,
                  saved: dict, state: dict, cloud: dict) -> None:
        binding, fingerprint = saved["binding"], state["fingerprint"]
        document = cloud["document"]
        if document:
            changes = {"revision_id": document["revision_id"], "document_hash": document["hash"],
                       "document_fingerprint": document["fingerprint"]}
            if document["complete"] and document["fingerprint"] == fingerprint:
                self._save(paper, state, **changes, pending_write={})
                return
            self._save(paper, state, **changes, pending_write={})
        else:
            self._check_binding(paper, settings, binding)
            title = ET.tostring(_xml_root(saved["chunks"][0]).find("title"), encoding="unicode")
            if len(title.encode("utf-8")) > MAX_CREATE_TITLE_BYTES:
                title = "<title>阅读档案</title>"
            skeleton = (title + "<p>"
                        + _owner(binding) + "</p><p>paper-reader:snapshot:" + fingerprint + "</p>")
            self._save(paper, state, phase="creating_document",
                       pending_write={"kind": "create", "after_hash": _content_hash(skeleton)})
            try:
                data = client.create_document(skeleton)
            except feishu_metadata.FeishuCLIError as error:
                data = error.response.get("data", {})
                if isinstance(data, dict) and isinstance(data.get("document"), dict) and data["document"].get("document_id"):
                    self._remember_created(paper, state, data)
                elif not error.uncertain:
                    self._save(paper, state, pending_write={})
                    raise
                else:
                    raise PublicationRecoveryRequired("Document creation may have succeeded. Locate its ownership-marked document before any retry.") from None
                raise PublicationRecoveryRequired("A document was created but the CLI reported failure. Its identity is saved; verify it before continuing.") from None
            self._remember_created(paper, state, data)
            fetched = client.fetch_document(state["document_id"])
            if not _owns(fetched["content"], _owner(binding)) or _content_hash(fetched["content"]) != _content_hash(skeleton):
                raise PublicationRecoveryRequired("The created document is saved but its initial content was not verified.")
            self._save(paper, state, revision_id=fetched["revision_id"], document_hash=_content_hash(skeleton), pending_write={})
            if data.get("result") not in (None, "success"):
                raise PublicationCloudError("Feishu document creation returned " + str(data.get("result") if data.get("result") in {"partial_success", "failed"} else "an unknown result") + ". The created document was retained.")
        cumulative = ""
        for index, chunk in enumerate(saved["chunks"]):
            self._check_binding(paper, settings, binding)
            before = client.fetch_document(state["document_id"])
            if (before["revision_id"] != state["revision_id"] or _content_hash(before["content"]) != state["document_hash"]
                    or not _owns(before["content"], _owner(binding))):
                raise PublicationConflict("The cloud document changed before a write; expected revision was not overwritten.")
            cumulative = cumulative + "\n" + chunk if cumulative else chunk
            target_hash = _content_hash(cumulative)
            intent = {"kind": "document", "before_revision": state["revision_id"],
                      "before_hash": state["document_hash"], "after_hash": target_hash,
                      "fingerprint": fingerprint, "final": index == len(saved["chunks"]) - 1}
            self._save(paper, state, phase="writing_document", pending_write=intent)
            error = None
            try:
                data = client.update_document(state["document_id"], state["revision_id"], chunk,
                                              "overwrite" if index == 0 else "append")
            except feishu_metadata.FeishuCLIError as caught:
                error = caught
                data = caught.response.get("data", {})
            fetched = client.fetch_document(state["document_id"])
            observed_hash = _content_hash(fetched["content"])
            observed_revision = fetched["revision_id"]
            response_document = data.get("document", {}) if isinstance(data, dict) else {}
            response_revision = response_document.get("revision_id") if isinstance(response_document, dict) else None
            result = data.get("result") if isinstance(data, dict) else None
            complete = (observed_hash == target_hash and observed_revision > intent["before_revision"]
                        and _owns(fetched["content"], _owner(binding)))
            if response_revision is not None and response_revision != observed_revision:
                raise PublicationConflict("The document revision changed after the CLI write; newer cloud edits were not overwritten.")
            if not complete:
                if (observed_revision == intent["before_revision"] and observed_hash == intent["before_hash"]):
                    self._save(paper, state, pending_write={})
                elif response_revision == observed_revision and _owns(fetched["content"], _owner(binding)):
                    self._save(paper, state, revision_id=observed_revision, document_hash=observed_hash,
                               document_fingerprint="", pending_write={})
                else:
                    raise PublicationRecoveryRequired("A document write has an uncertain/partial outcome. Verify the saved document before retrying.")
                if error:
                    raise error
                raise PublicationCloudError("Feishu document update was incomplete (" +
                                            (result if result in {"partial_success", "failed"} else "verification_failed") + ").")
            self._save(paper, state, revision_id=observed_revision, document_hash=observed_hash,
                       document_fingerprint=fingerprint if intent["final"] else "", pending_write={})
            if result in {"partial_success", "failed"}:
                raise PublicationCloudError("Feishu document update reported " + result +
                                            "; do not treat this attempt as fully successful.")
            if error:
                if not error.uncertain:
                    raise error
                state["warnings"].append("A document write response was uncertain; its entire content and resulting revision were verified.")
            elif result != "success":
                raise PublicationCloudError("Feishu document update reported " +
                                            (result if result in {"partial_success", "failed"} else "an unknown result") +
                                            "; do not treat this attempt as fully successful.")

    def _verify_attachment(self, paper: Path, client: FeishuPublicationClient, binding: dict,
                           attachment: dict, receipt: dict) -> None:
        if attachment["size"] != receipt["size"]:
            raise PublicationConflict("An existing deterministic backup filename has a different size; it was not replaced or duplicated.")
        path = _path(paper, f"verify-{uuid.uuid4().hex}.json")
        try:
            client.download(binding, attachment["file_token"], path)
            _regular(path)
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != receipt["sha256"]:
                raise PublicationConflict("The existing backup's bytes differ from the immutable snapshot. Preserve it; do not append a duplicate.")
        finally:
            if path.exists() or path.is_symlink():
                path.unlink()

    def _upload(self, paper: Path, settings: dict, client: FeishuPublicationClient,
                state: dict, backup_path: Path, receipt: dict, *, verify_existing: bool = False,
                expected_cells: dict | None = None) -> None:
        binding = state["binding"]
        field_ids = _record_fields(state)
        field = state["backup_field"]["id"]
        record = client.record(binding["record_id"], field_ids)
        if expected_cells is not None and any(record[key] != value for key, value in expected_cells.items()):
            raise PublicationConflict("The managed cells changed before backup upload; no text PATCH was attempted.")
        attachments = self._attachments(record[field])
        matches = [item for item in attachments if item["name"] == receipt["name"]]
        if len(matches) > 1:
            raise PublicationConflict("Multiple backups have the same deterministic filename. Resolve them explicitly; none were removed.")
        previous = (state.get("backups") or {}).get(state["fingerprint"])
        if matches:
            attachment = matches[0]
            if verify_existing or not (
                previous and all(previous.get(key) == attachment[key] for key in ("name", "size", "file_token"))
                and previous.get("sha256") == receipt["sha256"]
            ):
                self._verify_attachment(paper, client, binding, attachment, receipt)
        else:
            if (previous or (state.get("pending_write") or {}).get("kind") == "upload"
                    or receipt["name"] in (state.get("uncertain_uploads") or {})):
                raise PublicationRecoveryRequired("A previously registered/uncertain backup is not visible. Check the record; an upload will not be blindly repeated.")
            self._check_binding(paper, settings, binding)
            _regular(backup_path)
            if hashlib.sha256(backup_path.read_bytes()).hexdigest() != receipt["sha256"]:
                raise PublicationStorageError("The immutable backup changed before upload. Generate/recover its original snapshot before retrying.")
            changes = {"phase": "uploading_backup", "pending_write": {"kind": "upload", **receipt}}
            if state.get("mode") == "table":
                changes["uncertain_uploads"] = {**(state.get("uncertain_uploads") or {}), receipt["name"]: receipt}
            self._save(paper, state, **changes)
            error = None
            try:
                data = client.upload(binding, field, backup_path)
            except feishu_metadata.FeishuCLIError as caught:
                error = caught
                data = caught.response.get("data", {})
                if not isinstance(data, dict):
                    data = {}
            after = client.record(binding["record_id"], field_ids)
            if expected_cells is not None and any(after[key] != value for key, value in expected_cells.items()):
                raise PublicationConflict("Managed cells changed during backup upload. The backup was retained; no text PATCH was attempted.")
            registered = self._attachments(after[field])
            if not {item["file_token"] for item in attachments}.issubset({item["file_token"] for item in registered}):
                raise PublicationConflict("An existing backup attachment disappeared during upload. No attachment deletion was requested; inspect the record.")
            matches = [item for item in registered if item["name"] == receipt["name"]]
            if len(matches) != 1:
                if error and not error.uncertain and not matches:
                    uncertain = dict(state.get("uncertain_uploads") or {})
                    uncertain.pop(receipt["name"], None)
                    self._save(paper, state, pending_write={}, uncertain_uploads=uncertain)
                    raise error
                raise PublicationRecoveryRequired("Attachment upload outcome is unknown; verify registration before retrying, rather than appending a duplicate.")
            attachment = matches[0]
            self._verify_attachment(paper, client, binding, attachment, receipt)
            if error:
                state["warnings"].append("An attachment upload response was uncertain; the registered token, size and downloaded bytes were verified.")
            if data.get("result") in {"partial_success", "failed"}:
                self._save(paper, state, backups={**(state.get("backups") or {}), state["fingerprint"]: {**receipt, "file_token": attachment["file_token"]}}, pending_write={})
                raise PublicationCloudError("Feishu attachment upload reported " + data["result"] + "; its verified receipt was retained.")
            if error and not error.uncertain:
                self._save(paper, state, backups={**(state.get("backups") or {}), state["fingerprint"]: {**receipt, "file_token": attachment["file_token"]}}, pending_write={})
                raise error
        backups = dict(state.get("backups") or {})
        backups[state["fingerprint"]] = {**receipt, "file_token": attachment["file_token"]}
        changes = {"backups": backups, "pending_write": {}}
        if state.get("mode") == "table":
            uncertain = dict(state.get("uncertain_uploads") or {})
            uncertain.pop(receipt["name"], None)
            changes["uncertain_uploads"] = uncertain
        self._save(paper, state, **changes)

    def _table_backup(self, paper: Path, saved: dict, state: dict) -> tuple[Path, dict]:
        fingerprint = state["fingerprint"]
        expected = (state.get("backups") or {}).get(fingerprint)
        if expected is None:
            return self._backup(paper, saved["raw"], saved["binding"], fingerprint)
        name = f"reading-data-{fingerprint}.json"
        if (not isinstance(expected, dict) or expected.get("name") != name
                or not isinstance(expected.get("size"), int) or isinstance(expected["size"], bool) or expected["size"] < 0
                or not isinstance(expected.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", expected["sha256"])):
            raise PublicationStorageError("An existing backup receipt is invalid; it must not be replaced by a newly generated snapshot.")
        _token(expected.get("file_token"))
        path = _path(paper, name)
        receipt = {key: expected[key] for key in ("name", "size", "sha256")}
        if path.exists():
            _path_value, actual = self._backup(paper, saved["raw"], saved["binding"], fingerprint)
            if actual != receipt:
                raise PublicationStorageError("The immutable local backup differs from its saved receipt. Recover its original bytes; do not regenerate it.")
        # A missing local copy must not regenerate different passive timestamps.
        # _upload verifies the registered immutable token's bytes before reuse.
        return path, receipt

    def _cell_request(self, paper: Path, state: dict, values: dict) -> tuple[Path, str]:
        name = f"cells-{state['job_id']}-{uuid.uuid4().hex}.json"
        path = _path(paper, name)
        if path.exists():
            raise PublicationStorageError("The immutable text-cell request already exists; it was not overwritten.")
        text = _json(values)
        expected = text.encode("utf-8")
        try:
            self.text_writer(path, text)
            _regular(path)
            if path.read_bytes() != expected:
                raise ValueError()
        except (OSError, ValueError, TypeError):
            raise PublicationStorageError("The text-cell request could not be saved exactly; no PATCH was attempted.") from None
        return path, hashlib.sha256(expected).hexdigest()

    def _write_table(self, paper: Path, settings: dict, client: FeishuPublicationClient,
                     saved: dict, state: dict, expected: dict) -> None:
        targets = {column["field_id"]: column["text"] for column in saved["public"]["columns"]}
        current = self._table_cloud(client, settings, saved["binding"], state)
        if current["values"] != expected["values"]:
            raise PublicationConflict("Managed text cells changed since preflight. Preserve those edits and generate a fresh preview.")
        if state.get("cell_receipt") and current["cells"] == targets:
            self._save(paper, state, cell_receipt=self._cell_receipt(targets, state["fingerprint"]), pending_write={})
            return
        request, digest = self._cell_request(paper, state, targets)
        self._check_binding(paper, settings, saved["binding"])
        current = self._table_cloud(client, settings, saved["binding"], state)
        if current["values"] != expected["values"]:
            raise PublicationConflict("Managed text cells changed while saving the request; no PATCH was attempted.")
        intent = {
            "kind": "cells", "before": self._cell_receipt(current["cells"]),
            "after": self._cell_receipt(targets, state["fingerprint"]), "outcome": "unknown",
            "request_file": request.name, "request_sha256": digest,
        }
        self._save(paper, state, phase="writing_record", pending_write=intent)
        error = None
        try:
            data = client.write_cells(saved["binding"], request, digest)
        except feishu_metadata.FeishuCLIError as caught:
            error = caught
            data = caught.response.get("data", {})
            if not isinstance(data, dict):
                data = {}
        partial = bool(data.get("ignored_fields")) or data.get("result") in ("partial_success", "failed")
        positive = error is None and data.get("updated") is True and not data.get("created")
        intent["outcome"] = ("partial" if partial else "rejected" if error and not error.uncertain else
                             "acknowledged" if positive else "unknown")
        self._save(paper, state, phase="verifying_record", pending_write=intent)
        record = client.record(saved["binding"]["record_id"], _record_fields(state))
        observed = {field_id: _text_cell(record[field_id]) for field_id in targets}
        if error and not error.uncertain and not partial:
            if observed == current["cells"]:
                self._save(paper, state, pending_write={})
                raise error
            raise PublicationConflict("Cells changed despite a rejected PATCH. They were not adopted as reader-owned data.")
        response_record = data.get("record")
        returned_id = response_record.get("id", response_record.get("record_id")) if isinstance(response_record, dict) else None
        if data.get("created") or (returned_id is not None and returned_id != saved["binding"]["record_id"]):
            raise PublicationRecoveryRequired("The CLI returned an unexpected record identity/creation result. Verify the existing row before retrying.")
        if intent["outcome"] in ("acknowledged", "unknown"):
            for delay in _CELL_VERIFY_DELAYS:
                if observed == targets or any(observed[key] not in (current["cells"][key], targets[key]) for key in targets):
                    break
                if delay:
                    time.sleep(delay)
                record = client.record(saved["binding"]["record_id"], _record_fields(state))
                observed = {field_id: _text_cell(record[field_id]) for field_id in targets}
        if observed == targets:
            if error:
                state["warnings"].append("The four-cell PATCH response was uncertain; every exact text value was verified before accepting its receipt.")
            self._save(paper, state, cell_receipt=intent["after"], pending_write={})
            if partial:
                raise PublicationCloudError("The four-cell PATCH reported partial_success/failed/ignored fields. Verified receipts were retained; confirm a fresh preview before continuing.")
            if not positive and error is None:
                raise PublicationCloudError("The four-cell PATCH gave no positive update acknowledgement. Exact values were verified and retained, but this attempt is not reported as synced.")
            return
        if partial and all(observed[key] in (current["cells"][key], targets[key]) for key in targets):
            self._save(paper, state, cell_receipt=self._cell_receipt(observed), pending_write={})
            raise PublicationCloudError("The four-cell PATCH was partial or ignored fields. Its exact partial receipt is saved; review and confirm a fresh preview.")
        if observed == current["cells"]:
            raise PublicationRecoveryRequired("The four-cell PATCH outcome is still uncertain. Verify its expected values before retrying; it will not be repeated blindly.")
        raise PublicationConflict("Cloud text cells changed or only partly match after PATCH. Preserve them and resolve the conflict before any further write.")

    def _publish_table(self, paper: Path, settings: dict, client: FeishuPublicationClient,
                       saved: dict, state: dict, cloud: dict) -> None:
        self._save(paper, state, text_fields=cloud["text_fields"], backup_field=cloud["backup_field"],
                   phase="saving_snapshot")
        pending = state.get("pending_write") or {}
        if pending.get("kind") == "upload" and pending.get("name"):
            self._save(paper, state, pending_write={},
                       uncertain_uploads={**(state.get("uncertain_uploads") or {}), pending["name"]: pending})
        if cloud["recovered_cells"]:
            self._save(paper, state, cell_receipt=cloud["recovered_cells"], pending_write={})
        backup_path, receipt = self._table_backup(paper, saved, state)
        self._save(paper, state, phase="uploading_backup")
        with _table_write_lock(settings["base_token"], settings["table_id"]):
            current = self._table_cloud(client, settings, saved["binding"], state)
            if current["values"] != cloud["values"]:
                raise PublicationConflict("Managed cells changed while publication waited for the table write lock.")
            raw = self._raw(paper)
            if _binding(raw, settings) != saved["binding"] or archive_fingerprint(raw) != state["fingerprint"]:
                raise PublicationConflict("Reading data changed before the table write began; generate a fresh preview.")
            self._upload(paper, settings, client, state, backup_path, receipt,
                         verify_existing=True, expected_cells=current["values"])
            self._write_table(paper, settings, client, saved, state, current)
            self._save(paper, state, phase="verifying")
            verified = self._table_cloud(client, settings, saved["binding"], state)
            targets = {column["field_id"]: column["text"] for column in saved["public"]["columns"]}
            if verified["cells"] != targets:
                raise PublicationConflict("Final verification found changed managed text cells.")
            receipt = state["backups"][state["fingerprint"]]
            matches = [item for item in verified["attachments"] if item["name"] == receipt["name"]]
            if len(matches) != 1 or any(matches[0][key] != receipt[key] for key in ("name", "size", "file_token")):
                raise PublicationConflict("Final backup registration differs from its immutable receipt.")
            if not {item["file_token"] for item in current["attachments"]}.issubset(
                {item["file_token"] for item in verified["attachments"]}
            ):
                raise PublicationConflict("An earlier backup disappeared during publication; none were removed by this reader.")

    def _link_and_verify(self, paper: Path, settings: dict, client: FeishuPublicationClient,
                         saved: dict, state: dict) -> None:
        binding, url = state["binding"], state["document_url"]
        fields = [state[key]["id"] for key in ("archive_field", "backup_field")]
        archive_field = state["archive_field"]["id"]
        self._resolve_fields(client, settings, state)
        record = client.record(binding["record_id"], fields)
        current = _link_cell(record[archive_field])
        if current != url:
            if current != saved["cloud"]["link"]:
                raise PublicationConflict("The archive URL changed since preview; no unrelated link was overwritten.")
            self._check_binding(paper, settings, binding)
            self._save(paper, state, phase="linking_record", pending_write={"kind": "link", "previous_link": current})
            error = None
            try:
                data = client.link(binding, archive_field, url)
            except feishu_metadata.FeishuCLIError as caught:
                error = caught
                data = caught.response.get("data", {})
                if not isinstance(data, dict):
                    data = {}
            record = client.record(binding["record_id"], fields)
            if _link_cell(record[archive_field]) != url:
                if error:
                    raise error
                raise PublicationCloudError("The archive URL update did not verify. Check dedicated-field write permission.")
            self._save(paper, state, linked=True, pending_write={})
            if error:
                state["warnings"].append("The archive-link write response was uncertain; the exact registered URL was verified.")
            if data.get("ignored_fields") or data.get("result") in {"partial_success", "failed"}:
                raise PublicationCloudError("Feishu reported a partial/ignored archive URL update; its verified receipt was retained.")
            if error and not error.uncertain:
                raise error
        self._save(paper, state, phase="verifying", linked=True, pending_write={})
        document = client.fetch_document(state["document_id"])
        if (document["revision_id"] != state["revision_id"] or _content_hash(document["content"]) != state["document_hash"]
                or state.get("document_fingerprint") != state["fingerprint"]
                or not _owns(document["content"], _owner(binding))):
            raise PublicationConflict("Final document verification found a different or incomplete cloud revision.")
        record = client.record(binding["record_id"], fields)
        if _link_cell(record[archive_field]) != url:
            raise PublicationConflict("The archive URL changed during final verification.")
        receipt = state["backups"][state["fingerprint"]]
        attachments = self._attachments(record[state["backup_field"]["id"]])
        matches = [item for item in attachments if item["name"] == receipt["name"]]
        if len(matches) != 1 or any(matches[0][key] != receipt[key] for key in ("name", "size", "file_token")):
            raise PublicationConflict("Final backup registration does not match its immutable receipt.")

    def _worker(self, paper: Path, settings: dict, saved: dict, state: dict, stream) -> None:
        client = FeishuPublicationClient(settings)
        try:
            self._save(paper, state, phase="preflight")
            cloud = self._cloud(client, settings, saved["binding"], state)
            expected = saved["cloud"]
            keys = (("text_fields", "backup_field", "values", "cells", "recovered_cells") if settings["mode"] == "table"
                    else ("archive_field", "backup_field", "link", "document"))
            for key in keys:
                if cloud[key] != expected[key]:
                    raise PublicationConflict("Cloud schema/link/revision changed after preview. Generate a new preview before writing.")
            current = self._raw(paper)
            if (_binding(current, settings) != saved["binding"]
                    or archive_fingerprint(current) != saved["public"]["fingerprint"]):
                raise PublicationConflict("Reading data or the paper's binding changed during preflight. Generate a fresh preview before any cloud write.")
            if settings["mode"] == "table":
                self._publish_table(paper, settings, client, saved, state, cloud)
            else:
                self._save(paper, state, archive_field=cloud["archive_field"], backup_field=cloud["backup_field"], phase="saving_snapshot")
                backup_path, receipt = self._backup(paper, saved["raw"], saved["binding"], state["fingerprint"])
                upload_intent = state.get("pending_write") if (state.get("pending_write") or {}).get("kind") == "upload" else None
                self._document(paper, settings, client, saved, state, cloud)
                if upload_intent:
                    self._save(paper, state, pending_write=upload_intent)
                self._save(paper, state, phase="uploading_backup")
                with _table_write_lock(settings["base_token"], settings["table_id"]):
                    self._upload(paper, settings, client, state, backup_path, receipt)
                    self._link_and_verify(paper, settings, client, saved, state)
            current = self._raw(paper)
            if _binding(current, settings) != saved["binding"]:
                raise PublicationConflict("The local record association changed during publication. Review the saved destination.")
            pending = archive_fingerprint(current) != state["fingerprint"]
            published_at = state.get("published_at") if state.get("published_fingerprint") == state["fingerprint"] else _now()
            self._save(paper, state, status="pending" if pending else "synced", phase="complete", error="",
                       published_at=published_at or _now(), published_fingerprint=state["fingerprint"],
                       warnings=list(dict.fromkeys(state["warnings"] + client.warnings)),
                       next_action="preview_new_changes" if pending else "")
        except Exception as error:
            if isinstance(error, PublicationConflict):
                status, action = "conflict", "review_conflict_and_preview"
            elif isinstance(error, (PublicationRecoveryRequired, PublicationStorageError)):
                status, action = "recovery_required", "verify_receipts_before_retry"
            elif (state.get("pending_write") or {}).get("kind") == "create" and not state.get("document_id"):
                status, action = "recovery_required", "recover_created_document"
            else:
                status, action = "failed", "preview_and_confirm_retry"
            safe_error = str(error) if isinstance(error, (
                PublicationConflict, PublicationConfigurationError, PublicationRecoveryRequired,
                PublicationStorageError, PublicationCloudError, feishu_metadata.FeishuCLIError,
            )) else "Publication failed unexpectedly. Inspect local storage and CLI permissions; verify saved receipts before retrying."
            state.update(status=status, error=safe_error, error_type=type(error).__name__, next_action=action,
                         warnings=list(dict.fromkeys(state["warnings"] + client.warnings)))
            try:
                self._save(paper, state)
            except PublicationStorageError:
                state.update(status="recovery_required", storage_error=True,
                             error="Could not save a cloud receipt. Stop publication and repair the local journal; do not create another document.",
                             next_action="repair_local_journal")
                with _runtime(paper).lock:
                    _runtime(paper).shadow = copy.deepcopy(state)
        finally:
            _release(stream)
