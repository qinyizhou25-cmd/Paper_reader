"""Pure, verbatim reading-archive formatting; no I/O, models, or normalization.

The input is the untouched ``load_reading_data`` snapshot. The four stable
section IDs are ``my-notes``, ``ai-discussions``, ``accepted-definitions`` and
``other-material``. Counts describe source records, not XML paragraphs:
``paper_annotations`` excludes accepted definitions and unclassified records;
``chat_turns`` counts a stored question/answer block once, or each explicit
role-bearing message. Unknown envelope fields count as unclassified records.

Paper Brief, full segments/translations, outline and unaccepted teacher cards
stay in the raw snapshot, not in the main notes. The fingerprint includes them.
Readable entries contain saved prose and compact provenance, not copies of
record metadata. Opaque extensions are acknowledged in the raw backup; unique
text-bearing extensions remain visible without inferring their authorship.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any


_SECTIONS = (
    ("my-notes", "我的阅读笔记"),
    ("ai-discussions", "与 AI 的讨论"),
    ("accepted-definitions", "已采纳的 AI 定义"),
    ("other-material", "其他已保存材料（混合来源／未分类）"),
)
TABLE_COLUMN_NAMES = {
    "my-notes": "阅读笔记",
    "ai-discussions": "AI 讨论",
    "accepted-definitions": "已采纳定义",
    "other-material": "其他阅读材料",
}
TABLE_TEXT_LIMIT = 100_000
_COUNT_KEYS = (
    "paper_annotations", "thinking_annotations", "report_thoughts", "chat_turns",
    "accepted_definitions", "takeaway_blocks", "unclassified_records",
)
_PROSE_FIELDS = ("note", "content", "text", "prompt", "message")
_PROSE_NAMES = {
    *_PROSE_FIELDS, "quote", "body", "comment", "comments", "notes", "question",
    "questions", "thought", "thoughts", "words", "markdown", "summary",
}
_PROVENANCE_KEYS = {
    "id", "source", "target", "role", "type", "mode", "model", "kind",
    "content_type", "created_by", "author", "url", "href", "project",
    "created_at", "timestamp", "start", "end", "unit",
}
_PROVENANCE_CONTAINERS = {
    "origin", "anchor", "range", "paired_range", "selection_refs",
    "source_refs", "sources", "project_context",
}
_STRUCTURAL_FIELDS = {
    "title", "version", "updated_at", "color", "tags", "indent", "level", "locked",
    "source_label", "source_scope", "status", "group", "group_index", "group_count",
    "context_mode", "context_chars", "context_error",
}
_OPAQUE_FIELDS = {
    "metadata", "meta", "cache", "snapshot", "snapshots", "raw", "raw_data",
    "initial_note", "definition", "source_markdown", "context", "context_markdown",
}
_RAW_ONLY_FILES = {
    "segments.json", "outline.json", "reading_teacher.json",
    "reading_progress.json", "translation_state.json",
}
_VOLATILE_METADATA = {
    "updated_at", "last_opened_at", "reading_progress_summary",
    "reading_progress_updated_at", "read_status", "read_status_source", "status",
    "translation_status", "translation_error", "translation_backend",
    "translated_segments", "translation_total", "translation_progress",
    "translation_updated_at",
}
_XML_LIMIT = 4000
_XML_WARNING = (
    "XML 1.0 不支持的字符在 XML 中以 Unicode 转义显示；预览和原始快照保持不变。"
)


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)


def _text(value: Any) -> str:
    return value if isinstance(value, str) else _json(value)


def _pointer(path: str, key: Any) -> str:
    return path + "/" + str(key).replace("~", "~0").replace("/", "~1")


def _record_id(record: Any, path: str) -> str:
    return _text(record["id"]) if isinstance(record, dict) and "id" in record else path


def _prose_key(key: str) -> bool:
    key = key.lower().replace("-", "_")
    return key in _PROSE_NAMES or any(key.endswith("_" + name) for name in _PROSE_NAMES)


def _opaque_key(key: str) -> bool:
    return key in _OPAQUE_FIELDS or key.endswith(("_metadata", "_snapshot", "_cache"))


def _provenance_key(key: str) -> bool:
    return key in _PROVENANCE_KEYS or key.endswith(("_id", "_ids"))


def _provenance(value: Any) -> list[tuple[str, str]]:
    """Keep identifiers/roles/anchors, never replay quoted context or caches."""
    if isinstance(value, list):
        fields: list[tuple[str, str]] = []
        seen: set[tuple[tuple[str, str], ...]] = set()
        for index, item in enumerate(value):
            child = _provenance(item)
            signature = tuple(child)
            if signature in seen:
                continue
            seen.add(signature)
            fields.extend((f"[{index}].{key}", text) for key, text in child)
        return fields
    if not isinstance(value, dict):
        return []
    fields = []
    for key, item in value.items():
        if _opaque_key(key):
            continue
        if _provenance_key(key) and isinstance(item, (str, int, float, bool)):
            text = _text(item)
            if text:
                identifier = key == "id" or key.endswith(("_id", "_ids")) or key in {"url", "href"}
                fields.append((key, text if identifier or len(text) <= 240 else "（完整字段见原始快照）"))
        elif isinstance(item, (dict, list)) and (key in _PROVENANCE_CONTAINERS or not _prose_key(key)):
            fields.extend((key + ("." if not child.startswith("[") else "") + child, text)
                          for child, text in _provenance(item))
    return fields


def _saved_prose(value: Any, *, strict: bool = False, prefix: str = "") -> list[tuple[str, str]]:
    """Unknown records retain prose; extensions require text-bearing fields."""
    if isinstance(value, str):
        return [(prefix, value)] if not strict and value.strip() else []
    parts: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if (_opaque_key(key) or _provenance_key(key) or key in _STRUCTURAL_FIELDS
                    or key in _PROVENANCE_CONTAINERS):
                continue
            child = f"{prefix}.{key}" if prefix else key
            parts.extend(_saved_prose(item, strict=strict and not _prose_key(key), prefix=child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            parts.extend(_saved_prose(item, strict=strict, prefix=f"{prefix}[{index}]"))
    return parts


def _unique_prose(parts: list[tuple[str, str]], excluded: set[str] | None = None) -> list[tuple[str, str]]:
    seen = set(excluded or ())
    unique = []
    for field, text in parts:
        if text.strip() and text not in seen:
            unique.append((field, text))
            seen.add(text)
    return unique


def _join_prose(parts: list[tuple[str, str]]) -> str:
    if not parts:
        return ""
    return parts[0][1] + "".join(
        f"\n\n{field}:\n{text}" for field, text in parts[1:]
    )


def _definition(record: Any) -> bool:
    origin = record.get("origin") if isinstance(record, dict) else None
    return (
        isinstance(origin, dict)
        and origin.get("kind") == "reading-teacher"
        and origin.get("content_type") == "definition"
    )


def _ordinary_note(record: Any, anchor: str = "") -> bool:
    if not isinstance(record, dict):
        return False
    origin = record.get("origin")
    if origin not in (None, "", {}) and not (
        isinstance(origin, dict) and origin.get("kind") in ("user", "human")
    ):
        return False
    if record.get("role") not in (None, "", "user", "human"):
        return False
    return any(key in record for key in ("quote", "note", anchor) if key)


def _block_kind(block: Any) -> str:
    if not isinstance(block, dict):
        return "unknown"
    if block.get("mode") == "reading_narrative":
        return "narrative"
    if block.get("type") not in (None, "", "ai_output"):
        return "unknown"
    if block.get("mode") in ("source", "free") or block.get("model"):
        return "discussion"
    if block.get("type") == "ai_output":
        return "pasted"
    return "unknown"


def _timestamp(record: Any) -> datetime | None:
    if not isinstance(record, dict):
        return None
    value = record.get("created_at") or record.get("timestamp")
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return stamp.replace(tzinfo=timezone.utc) if stamp.tzinfo is None else stamp.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None


def _xml_chunks(text: str, warnings: list[str]) -> list[str]:
    """Bound escaped payloads, without cutting entities or discarding text."""
    chunks: list[str] = []
    buffer: list[str] = []
    size = 0
    entities = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;",
                "\n": "<br/>", "\r": "&#13;"}
    for char in text:
        number = ord(char)
        if not (
            number in (9, 10, 13)
            or 0x20 <= number <= 0xD7FF
            or 0xE000 <= number <= 0xFFFD
            or 0x10000 <= number <= 0x10FFFF
        ):
            token = f"\\u{number:04x}"
            if _XML_WARNING not in warnings:
                warnings.append(_XML_WARNING)
        else:
            token = entities.get(char, char)
        if buffer and size + len(token) > _XML_LIMIT:
            chunks.append("".join(buffer))
            buffer, size = [], 0
        buffer.append(token)
        size += len(token)
    chunks.append("".join(buffer))
    return chunks


class _Archive:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.files = data.get("files", {})
        self.sections = [
            {"id": key, "title": title, "entries": []} for key, title in _SECTIONS
        ]
        self.entries = {section["id"]: section["entries"] for section in self.sections}
        self.counts = dict.fromkeys(_COUNT_KEYS, 0)
        self.warnings: list[str] = []
        self.handled_extensions: set[str] = set()
        if not isinstance(self.files, dict):
            self.unknown(self.files, "snapshot#/files")
            self.files = {}
        segments = self.files.get("segments.json", [])
        self.segment_ids = {
            _text(record["id"]) for record in segments
            if isinstance(record, dict) and "id" in record
        } if isinstance(segments, list) else set()
        thinking = self.files.get("thinking.json", {})
        self.blocks: dict[str, list[dict[str, Any]]] = {}
        if isinstance(thinking, dict) and isinstance(thinking.get("blocks"), list):
            for block in thinking["blocks"]:
                if isinstance(block, dict) and "id" in block:
                    self.blocks.setdefault(_text(block["id"]), []).append(block)
        self.has_brief = isinstance(thinking, dict) and isinstance(thinking.get("explain"), dict)

    def source(self, record: Any, path: str, omitted: set[str], context: str = "") -> str:
        parts = [path]
        if isinstance(record, dict):
            fields = {key: value for key, value in record.items() if key not in omitted}
            fields = _provenance(fields)
            if fields:
                parts.append(" · ".join(f"{key}={value}" for key, value in fields))
        if context:
            parts.append("父记录：" + context)
        return "\n".join(parts)

    def add(
        self, section: str, record: Any, path: str, label: str,
        field: str = "note", *, omitted: set[str] | None = None,
        suffix: str = "", quote: bool = True, context: str = "",
    ) -> None:
        is_record = isinstance(record, dict)
        text = _text(record[field]) if is_record and field in record else ""
        selected = _text(record["quote"]) if is_record and quote and "quote" in record else ""
        hidden = {field} | ({"quote"} if quote else set()) | (omitted or set())
        self.entries[section].append({
            "id": _record_id(record, path) + suffix,
            "label": label,
            "quote": selected,
            "text": text,
            "source": self.source(record, path, hidden, context),
        })
        if is_record:
            self.extension_prose(record, path, hidden | {"quote"})

    def extension_prose(self, record: dict[str, Any], path: str, shown: set[str]) -> None:
        if path in self.handled_extensions:
            return
        self.handled_extensions.add(path)
        excluded = {record[key] for key in shown if isinstance(record.get(key), str)}
        for key, value in record.items():
            if key in shown or key == "messages":
                continue
            extension = {key: value}
            if _unique_prose(_saved_prose(extension, strict=True), excluded):
                self.unknown(extension, _pointer(path, key),
                             self.source(record, path, shown), strict=True, excluded=excluded)

    def mixed(self, record: dict[str, Any], path: str, label: str, fields: tuple[str, ...]) -> None:
        parts = _unique_prose([(key, _text(record[key])) for key in fields if key in record])
        text = _join_prose(parts)
        if not parts and fields[0] in record:
            text = _text(record[fields[0]])
        quote = _text(record["quote"]) if "quote" in record else ""
        if any(quote == value for _, value in parts):
            quote = ""
        self.entries["other-material"].append({
            "id": _record_id(record, path), "label": label,
            "quote": quote, "text": text,
            "source": self.source(record, path, {*fields, "quote"}),
        })
        self.extension_prose(record, path, {*fields, "quote"})

    def unknown(
        self, record: Any, path: str, context: str = "", *,
        strict: bool = False, excluded: set[str] | None = None,
    ) -> None:
        self.counts["unclassified_records"] += 1
        parts = _unique_prose(_saved_prose(record, strict=strict), excluded)
        if strict and not parts:
            self.warnings.append(f"{path}：扩展结构保留于原始快照，不在正文重放。")
            return
        self.warnings.append(f"{path}：未分类记录已保留，不推断作者；完整结构见原始快照。")
        quote = record.get("quote", "") if isinstance(record, dict) else ""
        quote = quote if isinstance(quote, str) else ""
        body = [(field, text) for field, text in parts if field != "quote"]
        if any(quote == value for _, value in body):
            quote = ""
        text = _join_prose(body)
        if not body and not isinstance(record, (dict, list, str)):
            text = _text(record)
        self.entries["other-material"].append({
            "id": _record_id(record, path),
            "label": "未分类（作者未确认）:",
            "quote": quote, "text": text,
            "source": self.source(record, path, set(), context),
        })

    def records(self, value: Any, path: str, *, reverse: bool = False) -> list[tuple[Any, str]]:
        if not isinstance(value, list):
            self.unknown(value, path)
            return []
        rows = [(record, _pointer(path, index)) for index, record in enumerate(value)]
        return list(reversed(rows)) if reverse else rows

    def extras(self, envelope: dict[str, Any], known: set[str], path: str) -> None:
        for key, value in envelope.items():
            if key not in known:
                self.unknown({key: value}, _pointer(path, key), strict=True)

    def paper_notes(self) -> None:
        if "annotations.json" not in self.files:
            return
        value = self.files["annotations.json"]
        path = "annotations.json#"
        if isinstance(value, dict):
            self.extras(value, {"annotations", "version", "updated_at"}, path)
            value, path = value.get("annotations", []), _pointer(path, "annotations")
        for record, source in self.records(value, path):
            accepted = _definition(record)
            if not accepted and not _ordinary_note(record, "segment_id"):
                self.unknown(record, source)
                continue
            segment_id = _text(record["segment_id"]) if "segment_id" in record else ""
            if not segment_id or segment_id not in self.segment_ids:
                self.warnings.append(f"{source}：论文锚点缺失（{segment_id}）；批注原文已保留。")
            if accepted:
                self.counts["accepted_definitions"] += 1
                self.add(
                    "accepted-definitions", record, source,
                    "AI 定义:",
                )
            else:
                self.counts["paper_annotations"] += 1
                target = record.get("target")
                attribution = (
                    "原文" if target == "source" else
                    "译文" if target == "translation" else
                    "选文"
                )
                self.add(
                    "my-notes", record, source,
                    f"笔记 · {attribution}引用:",
                )

    def thinking_notes(self, thinking: dict[str, Any]) -> None:
        for record, path in self.records(thinking.get("annotations", []), "thinking.json#/annotations"):
            if not _ordinary_note(record, "block_id") and not _ordinary_note(record, "thinking_block_id"):
                self.unknown(record, path)
                continue
            block_id = _text(record.get("block_id") or record.get("thinking_block_id") or "")
            blocks = self.blocks.get(block_id, [])
            if block_id == "paper-brief" and self.has_brief:
                attribution = "AI Brief"
            elif len(blocks) == 1:
                attribution = {
                    "discussion": "AI",
                    "narrative": "AI 阅读叙事",
                    "pasted": "粘贴内容（作者未确认）",
                    "unknown": "原有内容（作者未确认）",
                }[_block_kind(blocks[0])]
            else:
                attribution = "作者未确认"
                self.warnings.append(f"{path}：思考区锚点缺失或不唯一（{block_id}）；批注原文已保留。")
            self.counts["thinking_annotations"] += 1
            self.add(
                "my-notes", record, path,
                f"批注 · {attribution} 引用:",
            )
        for record, path in self.records(thinking.get("report_thoughts", []), "thinking.json#/report_thoughts"):
            if not _ordinary_note(record) or "note" not in record:
                self.unknown(record, path)
                continue
            self.counts["report_thoughts"] += 1
            self.add("my-notes", record, path, "我:")

    def message(self, record: Any, path: str, context: str = "") -> None:
        if not isinstance(record, dict):
            self.unknown(record, path, context)
            return
        labels = {
            "user": "我:",
            "human": "我:",
            "assistant": "AI:",
            "ai": "AI:",
            "system": "System:",
            "developer": "Developer:",
            "tool": "Tool:",
            "function": "Tool:",
        }
        role = record.get("role")
        prose = [key for key in ("content", "text", "message") if key in record]
        nested = "messages" in record
        if isinstance(role, str) and role in labels:
            self.counts["chat_turns"] += 1
            for index, field in enumerate(prose or ["content"]):
                self.add(
                    "ai-discussions", record, path, labels[role], field,
                    omitted=set(prose) | ({"messages"} if nested else set()),
                    suffix="" if index == 0 else ":" + field, quote=index == 0, context=context,
                )
        elif not nested or role is not None or prose or record["messages"] == []:
            self.unknown(
                {key: value for key, value in record.items() if key != "messages"} if nested else record,
                path, context,
            )
        if nested:
            self.extension_prose(record, path, {"messages", *prose, "quote"})
            parent = self.source(record, path, {"messages", *prose}, context)
            self.messages(record["messages"], _pointer(path, "messages"), parent)

    def messages(self, value: Any, path: str, context: str = "") -> None:
        if isinstance(value, dict):
            self.message(value, path, context)
            return
        if not isinstance(value, list):
            self.unknown(value, path, context)
            return
        rows = self.records(value, path)
        stamps = [_timestamp(record) for record, _ in rows]
        if rows and all(stamp is not None for stamp in stamps):
            rows = [row for _, row in sorted(zip(stamps, rows), key=lambda item: item[0])]
        for record, source in rows:
            self.message(record, source, context)

    def thinking_blocks(self, thinking: dict[str, Any]) -> None:
        for record, path in self.records(thinking.get("blocks", []), "thinking.json#/blocks", reverse=True):
            kind = _block_kind(record)
            if kind == "unknown":
                if isinstance(record, dict) and ("role" in record or "messages" in record):
                    self.message(record, path)
                else:
                    self.unknown(record, path)
                continue
            fields = {"prompt", "content", "messages"}
            if kind == "discussion":
                self.counts["chat_turns"] += 1
                if record.get("prompt"):
                    self.add(
                        "ai-discussions", record, path, "我:", "prompt",
                        omitted=fields, suffix=":prompt", quote=False,
                    )
                self.add("ai-discussions", record, path, "AI:", "content", omitted=fields)
            else:
                self.mixed(
                    record, path,
                    "AI 阅读叙事:" if kind == "narrative" else
                    "粘贴内容（作者未确认）:",
                    ("content", "prompt", "text", "note", "message"),
                )
            if "messages" in record:
                self.messages(
                    record["messages"], _pointer(path, "messages"),
                    self.source(record, path, fields),
                )

    def takeaway(self) -> None:
        if "takeaway_doc.json" not in self.files:
            return
        value = self.files["takeaway_doc.json"]
        path = "takeaway_doc.json#"
        if isinstance(value, dict):
            self.extras(value, {"blocks", "version", "updated_at"}, path)
            value, path = value.get("blocks", []), _pointer(path, "blocks")
        for record, source in self.records(value, path):
            if not isinstance(record, dict) or not any(key in record for key in ("text", "content", "note", "quote")):
                self.unknown(record, source)
                continue
            self.counts["takeaway_blocks"] += 1
            self.mixed(record, source, "Takeaway（混合来源）:",
                       ("text", "content", "note", "prompt", "message"))

    def build(self, *, include_xml: bool = True) -> dict[str, Any]:
        self.paper_notes()
        if "thinking.json" in self.files:
            thinking = self.files["thinking.json"]
            if isinstance(thinking, dict):
                self.thinking_notes(thinking)
                self.thinking_blocks(thinking)
                for field in ("chat", "messages"):
                    if field in thinking:
                        self.messages(thinking[field], _pointer("thinking.json#", field))
                self.extras(thinking, {
                    "annotations", "blocks", "report_thoughts", "chat", "messages",
                    "explain", "version", "updated_at",
                }, "thinking.json#")
            else:
                self.unknown(thinking, "thinking.json#")
        self.takeaway()
        for name, value in self.files.items():
            if name not in _RAW_ONLY_FILES | {"metadata.json", "annotations.json", "thinking.json", "takeaway_doc.json"}:
                self.unknown(value, _text(name) + "#")
        self.extras(self.data, {"format", "version", "paper_id", "sources", "files"}, "snapshot#")
        metadata = self.files.get("metadata.json", {})
        if not isinstance(metadata, dict):
            self.unknown(metadata, "metadata.json#")
            metadata = {}
        original_title = _text(metadata.get("title") or self.data.get("paper_id") or "未命名论文")
        if not include_xml:
            return {
                "title": original_title, "sections": self.sections,
                "counts": self.counts, "warnings": self.warnings,
            }
        title = "阅读档案｜" + original_title
        title_chunks = _xml_chunks(title, self.warnings)
        if len(title_chunks) > 1:
            title, title_chunks = "阅读档案", ["阅读档案"]
            self.warnings.append("论文标题过长；完整标题保留在文档的论文信息中。")
        xml = ["<title>" + title_chunks[0] + "</title>"]

        def blocks(text: str, tag: str = "p") -> None:
            xml.extend(f"<{tag}>{chunk}</{tag}>" for chunk in _xml_chunks(text, self.warnings))

        blocks(
            "按保存原文分类；不生成摘要，不改写正文。引用不等同于本人原创。\n"
            "完整来源说明、元数据、扩展结构和引用上下文保留于原始快照，正文只列简要来源与锚点。\n"
            "Paper Brief、论文全文／译文、导读和未采纳的教师建议不在此重复。"
        )
        bibliography = ["论文 ID：" + _text(self.data.get("paper_id", ""))]
        for key, label in (
            ("title", "论文标题"), ("authors", "作者"), ("institutions", "机构"),
            ("venue", "发表载体"), ("year", "年份"), ("doi", "DOI"),
            ("arxiv_id", "arXiv ID"), ("project", "项目"), ("projects", "项目"),
            ("tags", "标签"), ("importance", "重要性"),
        ):
            if key in metadata and (key != "title" or title == "阅读档案"):
                bibliography.append(label + "：" + _text(metadata[key]))
        blocks("\n".join(bibliography))
        for section in self.sections:
            blocks(section["title"], "h1")
            if not section["entries"]:
                blocks("暂无保存记录。")
            for entry in section["entries"]:
                blocks(entry["label"], "h2")
                blocks("来源：\n" + entry["source"])
                if entry["quote"]:
                    xml.append("<blockquote>")
                    blocks(entry["quote"])
                    xml.append("</blockquote>")
                if entry["text"]:
                    blocks(entry["text"])
                elif not entry["quote"] or section["id"] == "accepted-definitions":
                    blocks("（当前保存的正文为空；完整记录见原始快照。）")
        return {
            "title": title, "xml": "\n".join(xml), "sections": self.sections,
            "counts": self.counts, "warnings": self.warnings,
        }


def build_archive(reading_data: dict[str, Any]) -> dict[str, Any]:
    """Build a categorized preview and resource-free DocxXML, without mutation.

    Preview strings are literal text, not HTML. Original IDs and JSON-pointer
    locations remain visible; callers must escape previews for their own UI.
    One mixed-origin entry represents each Takeaway/narrative/pasted record.
    Empty fields and exact duplicate prose within those records are not replayed;
    distinct extra prose is included verbatim with mechanical field labels.
    Metadata, cached source quotations and opaque extensions stay in the backup,
    not in ``source`` dumps. Unknown prose is shown without inferring authorship.
    XML payloads are split at 4,000 escaped characters, never truncated. XML 1.0
    forbidden characters use visible Unicode escapes only in the XML rendering.
    """
    if not isinstance(reading_data, dict):
        raise TypeError("reading_data must be a dict")
    return _Archive(reading_data).build()


def build_table_archive(reading_data: dict[str, Any]) -> dict[str, Any]:
    """Render the same original records as four bounded, literal text cells."""
    if not isinstance(reading_data, dict):
        raise TypeError("reading_data must be a dict")
    # Persisting previews sorts JSON keys; provenance must not depend on their insertion order.
    canonical = json.loads(_json(reading_data))
    archive = _Archive(canonical).build(include_xml=False)
    columns = []
    for section in archive["sections"]:
        entries = []
        for index, entry in enumerate(section["entries"], 1):
            parts = [entry["label"] if section["id"] == "ai-discussions" else f"{index}. {entry['label']}"]
            if entry["text"]:
                parts.append(entry["text"])
            if entry["quote"]:
                parts.append("引用：\n" + entry["quote"])
            if entry["source"]:
                parts.append("来源：\n" + entry["source"])
            entries.append("\n\n".join(parts))
        text = "\n\n".join(entries)
        name = TABLE_COLUMN_NAMES[section["id"]]
        try:
            characters = len(text.encode("utf-16-le")) // 2
        except UnicodeEncodeError:
            raise ValueError(f"{name} contains invalid Unicode; the original records were not changed.") from None
        if characters > TABLE_TEXT_LIMIT:
            raise ValueError(
                f"{name} exceeds the {TABLE_TEXT_LIMIT:,}-character cell limit "
                f"({characters:,} UTF-16 units). No content was truncated; split the records before publishing."
            )
        columns.append({
            "id": section["id"], "name": name, "text": text,
            "characters": characters, "limit": TABLE_TEXT_LIMIT,
        })
    return {**archive, "columns": columns}


def archive_fingerprint(reading_data: dict[str, Any]) -> str:
    """SHA-256 of canonical substantive snapshot data, without changing it.

    Exclude progress files, translation-job state, their metadata projections
    (including read-status UI fields), metadata polling times and only
    ``metadata.feishu.synced_at`` within Feishu metadata. All other metadata,
    unknown fields/records and saved content remain significant. Top-level
    ``sources`` is the exporter's descriptive legend, not reading content.
    """
    if not isinstance(reading_data, dict):
        raise TypeError("reading_data must be a dict")
    substantive = {key: value for key, value in reading_data.items() if key != "sources"}
    files = reading_data.get("files")
    if isinstance(files, dict):
        stable_files = {
            key: value for key, value in files.items()
            if key not in {"reading_progress.json", "translation_state.json"}
        }
        metadata = stable_files.get("metadata.json")
        if isinstance(metadata, dict):
            metadata = {key: value for key, value in metadata.items() if key not in _VOLATILE_METADATA}
            feishu = metadata.get("feishu")
            if isinstance(feishu, dict):
                feishu = {key: value for key, value in feishu.items() if key != "synced_at"}
                metadata = {key: value for key, value in metadata.items() if key != "feishu"}
                if feishu:
                    metadata["feishu"] = feishu
            stable_files["metadata.json"] = metadata
        substantive["files"] = stable_files
    payload = json.dumps(substantive, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
