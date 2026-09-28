"""Read existing Feishu fields and PDF attachments without writing cloud content."""

from __future__ import annotations

import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unicodedata
from typing import Any
from urllib.parse import parse_qsl, urlsplit
import uuid


FIELD_MAPPING = {
    "title": ("资料名称", "fldHGsQoto"),
    "authors": ("作者AI", "fldazVdCrW"),
    "institutions": ("发表机构", "fldcKJ8IxL"),
    "venue": ("发表期刊/会议", "fld2o8gsbt"),
    "year": ("时间", "fldHCtRIwO"),
    "abstract": ("Abstract", "fld9InCF3B"),
    "research_question": ("Research Question", "flddfccaTl"),
    "method": ("Method", "fldCoWXykm"),
    "result": ("Result", "fldYQ4FSKU"),
    "discussion": ("Discussion", "fldmH2Qo5u"),
}
BRIEF_FIELDS = {"raw text": "fldHblyRK0", "raw text_中文": "fldogK1Whx"}
ATTACHMENT_FIELDS = {"原文 pdf": "fldE2HGqZA", "附件": "fldJAb4POc"}


def clean_title(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"<img\b[^>]*>", " ", text, flags=re.I)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s*#{1,6}\s+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def title_key(value: Any) -> str:
    text = unicodedata.normalize("NFKC", clean_title(value)).casefold()
    return "".join(char for char in text if char.isalnum())


def cell_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "".join(cell_text(item) for item in value)
    if isinstance(value, dict) and isinstance(value.get("text"), str):
        return value["text"]
    raise ValueError("Feishu returned a non-text value for a mapped text field.")


def cli_command(configured: str = "") -> str:
    candidate = Path(configured).expanduser() if configured else Path(shutil.which("lark-cli") or "")
    if candidate.is_file() and candidate.suffix.lower() not in {".cmd", ".bat", ".ps1"}:
        return str(candidate.resolve())
    if not configured and candidate.is_file():
        native = candidate.parent / "node_modules" / "@larksuite" / "cli" / "bin" / ("lark-cli.exe" if os.name == "nt" else "lark-cli")
        if native.is_file():
            return str(native.resolve())
    raise RuntimeError("Set PAPER_READER_LARK_CLI to the installed lark-cli executable. Shell wrappers are not used.")


class FeishuCLIError(RuntimeError):
    """A sanitized CLI error; response is retained only for recovering write receipts."""

    def __init__(self, message: str, *, category: str = "cli_error", uncertain: bool = False,
                 response: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.category = category
        self.uncertain = uncertain
        self.response = response or {}


def run_cli(
    arguments: list[str], *, executable: str = "", cwd: Path | None = None, timeout: int = 45,
    service: str = "base", input_text: str | None = None, write: bool = False,
    full_response: bool = False,
) -> dict[str, Any]:
    if service not in {"base", "docs"}:
        raise ValueError("Unsupported Feishu CLI service.")
    input_options = {"input": input_text} if input_text is not None else {}
    try:
        command = cli_command(executable)
    except RuntimeError:
        raise FeishuCLIError("Set PAPER_READER_LARK_CLI to the installed native executable. Shell wrappers are not used.",
                             category="startup") from None
    try:
        result = subprocess.run(
            [command, service, *arguments, "--as", "user"],
            capture_output=True, text=True, encoding="utf-8", timeout=timeout, check=False,
            cwd=cwd, shell=False, **input_options,
        )
    except subprocess.TimeoutExpired:
        message = ("Feishu write timed out; the cloud outcome is unknown. Verify the saved publication before retrying."
                   if write else "Feishu request timed out. Cached metadata is unchanged; retry when available.")
        raise FeishuCLIError(message, category="timeout", uncertain=write) from None
    except OSError:
        raise FeishuCLIError("Feishu CLI could not be started. Check the configured executable and download directory.",
                             category="startup") from None
    except UnicodeError:
        raise FeishuCLIError("Feishu CLI did not return UTF-8 JSON. Check the local CLI installation.",
                             uncertain=write) from None
    try:
        envelope = json.loads(result.stdout.strip() or result.stderr)
    except json.JSONDecodeError:
        raise FeishuCLIError(f"Feishu CLI did not return JSON (exit {result.returncode}). Check local login and permissions.",
                             uncertain=write) from None
    if not isinstance(envelope, dict):
        if write:
            raise FeishuCLIError("Feishu returned an invalid write envelope; verify the cloud outcome before retrying.",
                                 uncertain=True)
        raise ValueError("Feishu returned an invalid JSON envelope.")
    if result.returncode or not envelope.get("ok"):
        error = envelope.get("error") or {}
        category = error.get("type") if isinstance(error, dict) else ""
        if category not in (
            "api", "auth", "permission_denied", "validation", "invalid_argument",
            "not_found", "network", "timeout", "confirmation_required", "rate_limit",
        ):
            category = "cli_error"
        code = error.get("code") if isinstance(error, dict) else None
        detail = f", code {code}" if isinstance(code, int) else ""
        if write:
            if category == "confirmation_required":
                advice = "The CLI requires separate high-risk confirmation; no confirmation gate was bypassed."
            elif category in {"auth", "permission_denied"}:
                advice = "Restore the required user scopes with lark-cli auth login --scope in a terminal; do not switch to bot."
            else:
                advice = "Verify the publication's cloud receipts before retrying; check user scopes and field configuration."
            raise FeishuCLIError(
                f"Feishu write failed ({category or result.returncode}{detail}). {advice}",
                category=category,
                uncertain=category not in {"auth", "permission_denied", "validation", "invalid_argument",
                                           "not_found", "confirmation_required", "rate_limit"},
                response=envelope,
            )
        raise FeishuCLIError(
            f"Feishu read failed ({category or result.returncode}{detail}). Check user login, table read permission, and field configuration.",
            category=category, response=envelope,
        )
    data = envelope.get("data")
    if not isinstance(data, dict):
        if write:
            raise FeishuCLIError("Feishu returned invalid write data; verify the cloud outcome before retrying.",
                                 uncertain=True, response=envelope)
        raise ValueError("Feishu returned an invalid data envelope.")
    return envelope if full_response else data


def validate_ids(base_token: str, table_id: str, record_id: str = "") -> None:
    if (
        not isinstance(base_token, str) or not re.fullmatch(r"[A-Za-z0-9]+", base_token)
        or not isinstance(table_id, str) or not re.fullmatch(r"tbl[A-Za-z0-9]+", table_id)
    ):
        raise ValueError("Configure a resolved Feishu Base token and table ID, not a Wiki URL.")
    if not isinstance(record_id, str) or (record_id and not re.fullmatch(r"rec[A-Za-z0-9]+", record_id)):
        raise ValueError("Invalid Feishu record ID.")


def records_from_result(data: dict[str, Any]) -> list[dict[str, Any]]:
    fields = data.get("field_id_list")
    ids = data.get("record_id_list")
    rows = data.get("data")
    if not all(isinstance(value, list) for value in (fields, ids, rows)) or len(ids) != len(rows):
        raise ValueError("Feishu returned an invalid record table.")
    if any(not isinstance(field_id, str) for field_id in fields) or len(fields) != len(set(fields)):
        raise ValueError("Feishu returned invalid or duplicate field identifiers.")
    records = []
    for record_id, row in zip(ids, rows):
        if not isinstance(record_id, str) or not isinstance(row, list) or len(row) != len(fields):
            raise ValueError("Feishu returned an invalid record row.")
        records.append({"record_id": record_id, "fields": dict(zip(fields, row))})
    return records


def search_records(base_token: str, table_id: str, keyword: str, *, executable: str = "") -> dict[str, Any]:
    validate_ids(base_token, table_id)
    keyword = clean_title(keyword).strip()
    if len(keyword) < 3 or len(keyword) > 500:
        raise ValueError("Use a title keyword between 3 and 500 characters.")
    title_field = FIELD_MAPPING["title"][1]
    data = run_cli([
        "+record-search", "--base-token", base_token, "--table-id", table_id,
        # Base limits search keywords to 50 characters; callers compare full titles.
        "--keyword", keyword[:50], "--search-field", title_field, "--field-id", title_field,
        "--limit", "10", "--format", "json",
    ], executable=executable)
    if title_field not in (data.get("field_id_list") or []):
        raise ValueError("Feishu did not return the configured title column.")
    return {
        "records": [{"record_id": row["record_id"], "title": cell_text(row["fields"].get(title_field))}
                    for row in records_from_result(data)],
        "has_more": bool(data.get("has_more")),
    }


def _read_record(
    base_token: str, table_id: str, record_id: str, *, executable: str = "", include_attachments: bool = False,
) -> dict[str, Any]:
    validate_ids(base_token, table_id, record_id)
    arguments = ["+record-get", "--base-token", base_token, "--table-id", table_id, "--record-id", record_id, "--format", "json"]
    field_ids = [value[1] for value in FIELD_MAPPING.values()] + list(BRIEF_FIELDS.values())
    if include_attachments:
        field_ids.extend(ATTACHMENT_FIELDS.values())
    for field_id in field_ids:
        arguments.extend(["--field-id", field_id])
    data = run_cli(arguments, executable=executable)
    if record_id in (data.get("record_not_found") or []):
        raise ValueError("The linked Feishu record no longer exists or is not accessible. Cached metadata is unchanged; select the current record explicitly.")
    records = records_from_result(data)
    if len(records) != 1 or records[0]["record_id"] != record_id:
        raise ValueError("The linked Feishu record was not returned. Existing metadata is unchanged.")
    cells = records[0]["fields"]
    expected = {value[1] for value in FIELD_MAPPING.values()} | set(BRIEF_FIELDS.values())
    if not expected.issubset(cells):
        raise ValueError("The configured Feishu table no longer contains the mapped fields. Check the field mapping.")
    metadata = {key: cell_text(cells.get(field_id)) for key, (_name, field_id) in FIELD_MAPPING.items()}
    result = {
        "record_id": record_id,
        "metadata": metadata,
        "field_sources": {key: name for key, (name, _field_id) in FIELD_MAPPING.items()},
        "briefings": {name: cell_text(cells.get(field_id)) for name, field_id in BRIEF_FIELDS.items()},
    }
    if include_attachments:
        result["attachments"] = _pdf_attachments(cells)
    return result


def read_record(base_token: str, table_id: str, record_id: str, *, executable: str = "") -> dict[str, Any]:
    return _read_record(base_token, table_id, record_id, executable=executable)


def _validate_file_token(file_token: str) -> None:
    if not isinstance(file_token, str) or not re.fullmatch(r"[A-Za-z0-9]+", file_token):
        raise ValueError("Invalid Feishu attachment file token.")


def _pdf_attachments(cells: dict[str, Any]) -> list[dict[str, Any]]:
    if not set(ATTACHMENT_FIELDS.values()).issubset(cells):
        raise ValueError("The configured Feishu table no longer contains the attachment fields. Check the field mapping.")
    attachments = []
    seen = set()
    for field_id in ATTACHMENT_FIELDS.values():
        cell = cells[field_id]
        if cell is None:
            continue
        if not isinstance(cell, list):
            raise ValueError("Feishu returned an invalid attachment cell; expected an attachment list.")
        for item in cell:
            if not isinstance(item, dict):
                raise ValueError("Feishu returned an invalid attachment entry.")
            file_token, name, size = item.get("file_token"), item.get("name"), item.get("size")
            _validate_file_token(file_token)
            if not isinstance(name, str) or not name.strip() or "\x00" in name:
                raise ValueError("Feishu returned an attachment without a valid name.")
            if not isinstance(size, int) or isinstance(size, bool) or size < 0:
                raise ValueError("Feishu returned an attachment without a valid byte size.")
            mime_type = item.get("type")
            if mime_type is not None and not isinstance(mime_type, str):
                raise ValueError("Feishu returned an invalid attachment MIME type.")
            # Preview uses declared names/types; downloading verifies the actual PDF bytes.
            if not name.lower().endswith(".pdf") and (mime_type or "").lower() != "application/pdf":
                continue
            if file_token not in seen:
                attachments.append({"field_id": field_id, "file_token": file_token, "name": name, "size": size})
                seen.add(file_token)
    return attachments


def read_intake_record(base_token: str, table_id: str, record_id: str, *, executable: str = "") -> dict[str, Any]:
    """Return read_record's unchanged fields plus ordered, token-deduplicated PDF candidates."""
    if not isinstance(record_id, str) or not record_id:
        raise ValueError("A Feishu record ID is required for intake.")
    return _read_record(base_token, table_id, record_id, executable=executable, include_attachments=True)


def resolve_record_reference(base_token: str, table_id: str, reference: str, *, executable: str = "") -> str:
    """Resolve a record ID or HTTPS Feishu URL; never infer a record from a table/view."""
    validate_ids(base_token, table_id)
    if not isinstance(reference, str) or not reference.strip():
        raise ValueError("A Feishu record ID or record URL is required.")
    reference = reference.strip()
    if re.fullmatch(r"rec[A-Za-z0-9]+", reference):
        validate_ids(base_token, table_id, reference)
        return reference
    try:
        url = urlsplit(reference)
        host = url.hostname or ""
        valid_host = any(
            host == domain or host.endswith("." + domain)
            for domain in ("feishu.cn", "larkoffice.com", "larksuite.com", "doubao.com")
        )
        valid_url = (
            url.scheme == "https" and valid_host and url.port in (None, 443)
            and not url.username and not url.password and not url.fragment
            and not re.search(r"[\s\\\x00-\x1f\x7f]", reference)
        )
    except ValueError:
        valid_url = False
    if not valid_url:
        raise ValueError("Use a record ID or an HTTPS Feishu Base record URL without credentials or fragments.")
    selectors = (
        {"record", "record_id", "recordid", "records", "record_id_list"},
        {"table", "table_id", "tableid"}, {"view", "view_id", "viewid"},
        {"base_token", "basetoken"},
    )
    query = parse_qsl(url.query, keep_blank_values=True)
    if any(sum(key.lower() in names for key, _value in query) > 1 for names in selectors):
        raise ValueError("The Feishu URL is ambiguous; provide a single record reference.")
    data = run_cli(["+url-resolve", "--url", reference, "--format", "json"], executable=executable)
    if data.get("base_token") != base_token or data.get("table_id") != table_id:
        raise ValueError("The Feishu URL does not resolve to the configured Base and table.")
    if data.get("resource_type", "bitable") != "bitable":
        raise ValueError("The Feishu URL does not resolve to a Base record.")
    record_id = data.get("record_id")
    if not isinstance(record_id, str) or not record_id:
        raise ValueError("The Feishu URL did not resolve to a record ID; table/view or unsupported record links cannot be imported.")
    for key in ("record_id_list", "record_ids"):
        if key in data and data[key] != [record_id]:
            raise ValueError("The Feishu URL resolved ambiguously; provide a single record reference.")
    validate_ids(base_token, table_id, record_id)
    return record_id


def download_record_attachment(
    base_token: str, table_id: str, record_id: str, file_token: str, destination: Path, *, executable: str = "",
) -> Path:
    """Download one PDF to an absolute destination, publishing only validated bytes without clobbering."""
    validate_ids(base_token, table_id, record_id)
    if not isinstance(record_id, str) or not record_id:
        raise ValueError("A Feishu record ID is required for attachment download.")
    _validate_file_token(file_token)
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("The attachment destination already exists; it was not overwritten.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".feishu-download-{uuid.uuid4().hex}.part"
    with staging.open("xb"):
        pass
    try:
        # --overwrite applies only to our exclusively reserved staging file, never to destination.
        run_cli([
            "+record-download-attachment", "--base-token", base_token, "--table-id", table_id,
            "--record-id", record_id, "--file-token", file_token, "--output", staging.name,
            "--overwrite", "--format", "json",
        ], executable=executable, cwd=destination.parent, timeout=180)
        if staging.is_symlink() or not staging.is_file() or not staging.stat().st_size:
            raise ValueError("Feishu did not download a nonempty regular PDF file.")
        with staging.open("rb") as downloaded:
            if downloaded.read(5) != b"%PDF-":
                raise ValueError("The downloaded Feishu attachment is not a PDF (missing PDF magic bytes).")
        try:
            # A hard link atomically refuses even a destination created during the CLI request.
            os.link(staging, destination)
        except FileExistsError:
            raise FileExistsError("The attachment destination already exists; it was not overwritten.") from None
        except OSError:
            raise RuntimeError("Could not save the verified Feishu PDF to the requested destination.") from None
        return destination
    finally:
        try:
            staging.unlink(missing_ok=True)
        except OSError:
            raise RuntimeError("Could not remove the attachment download staging file.") from None
