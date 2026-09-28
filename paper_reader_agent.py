#!/usr/bin/env python3
"""Local paper reader agent helper.

This tool is intentionally dependency-light. It uses MinerU when available for
PDF-to-Markdown conversion, then builds a portable reading workspace that can be
served from any folder.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import html
import ipaddress
import json
import math
import mimetypes
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import feishu_metadata
import feishu_publish
from reading_teacher import is_teacher_definition, validate_reading_teacher

TOOL_VERSION = "0.1.0"
DEFAULT_WORKSPACE_NAME = "paper_reading_workspace"
CONFIG_FILE = ".paper-reader-agent.json"
SCRIPT_DIR = Path(__file__).resolve().parent
WEB_DIR = SCRIPT_DIR / "web"
WRITE_LOCKS: dict[Path, threading.RLock] = {}
WRITE_LOCKS_GUARD = threading.Lock()
EXPORT_TIMERS: dict[Path, threading.Timer] = {}
EXPORT_TIMERS_GUARD = threading.Lock()
PROCESSING_JOBS: PaperProcessingJobManager | None = None
PROCESSING_JOBS_GUARD = threading.Lock()
CLIENT_DISCONNECT_ERRORS = (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)
ENV_FILES_LOADED = False
TRANSLATION_JOBS: TranslationJobManager | None = None
TRANSLATION_JOBS_GUARD = threading.Lock()
PUBLICATION_SERVICE: feishu_publish.PublicationService | None = None
PUBLICATION_SERVICE_GUARD = threading.Lock()


def write_lock_for(path: Path) -> threading.RLock:
    key = path.resolve()
    with WRITE_LOCKS_GUARD:
        lock = WRITE_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            WRITE_LOCKS[key] = lock
        return lock


def replace_with_retry(tmp: Path, path: Path) -> None:
    last_error: PermissionError | None = None
    for attempt in range(8):
        try:
            tmp.replace(path)
            return
        except PermissionError as exc:
            last_error = exc
            time.sleep(0.04 * (attempt + 1))
    if last_error:
        raise last_error


def load_env_files() -> None:
    global ENV_FILES_LOADED
    if ENV_FILES_LOADED:
        return
    ENV_FILES_LOADED = True
    seen: set[Path] = set()
    for candidate in (SCRIPT_DIR / ".env", Path.cwd() / ".env"):
        path = candidate.resolve()
        if path in seen or not path.exists():
            continue
        seen.add(path)
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except OSError:
            continue
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            key, separator, value = line.partition("=")
            key = key.strip()
            if not separator or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            os.environ.setdefault(key, value)


def env_value(*names: str, default: str = "") -> str:
    load_env_files()
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    if os.name == "nt":
        try:
            import winreg  # type: ignore[import-not-found]

            locations = [
                (winreg.HKEY_CURRENT_USER, "Environment"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
            ]
            for name in names:
                for root, path in locations:
                    try:
                        with winreg.OpenKey(root, path) as key:
                            value, _kind = winreg.QueryValueEx(key, name)
                        if value:
                            return str(value)
                    except OSError:
                        continue
        except Exception:  # noqa: BLE001 - environment fallback should never block the app
            pass
    return default

SKIM_ANALYSIS_PROMPT = """You will receive a paper converted into paragraph-id text, where each paragraph begins with an id like [p-0013].
Analyze the paper in Chinese and output ONLY one valid JSON object. Do not output markdown outside JSON. Do not invent paragraph ids.

Goal:
Generate one unified skim analysis that can be used both for human reading and for the reader UI's Presentation/Core flow.

Requirements:
1. Follow this paper's own argumentative flow. Do not force every paper into Motivation/Method/Evaluation/Discussion if the paper uses a different structure.
2. The skim_summary should be concise but specific enough for a reader to understand the paper's main story.
3. presentation_flow must contain 4-7 nodes. Each node is one shareable step in the paper's own flow.
4. Each flow node must include anchors from the provided paragraph ids. Prefer 1-5 representative anchors.
5. Each flow node may include anchor_ranges as continuous paragraph ranges, e.g. [["p-0013", "p-0024"]].
6. Keep fields minimal and consistent. Use title + core as both human-readable content and machine-matchable content.

Output JSON schema:
{
    "metadata": {
        "authors": "",
        "institutions": "",
        "venue": "",
        "year": "",
        "abstract": "",
        "research_question": ""
    },
    "skim_summary": "中文略读总结。按论文自己的叙事逻辑写，使用结构化要点。",
    "presentation_flow": [
        {
            "id": "flow-1",
            "title": "问题设定：...",
            "core": "这一节点的主干论点，用中文一句到两句说明。",
            "anchors": ["p-0013"],
            "anchor_ranges": [["p-0013", "p-0024"]],
            "keywords": ["decision-making", "automation"]
        }
    ]
}"""

EXPLANATION_PROMPT = """Analyze the paper according to the file I provide, and output the analysis of the paper as per my requirements. Do NOT output anything other than what I ask for. Analyze it point by point（in to markdown format).Make the summary content into structured bulletpoints. Use abbreviation if needed. 
Your output format: 
# Title: The full title of the paper
# Author: The author's name in the paper 
# Institution: List all the insitutions. Use abbreviations if the institutions are very familiar, for example: UW, CMU 
# Journal: The journal to which the paper belongs. Use abbreviations uniformly, for example: CHI, UIST, IEEE, arxiv 
# Publication Year: Only take the year number. For example: 2024 
# Abstract: Locate the position of the abstract in the article and output it. 
# Research Question: Locate the position of the research question in the article and output it. If not found, summarize it by yourself. 
#  Explain the paper in a vivid and understandable way, can be fluid structured based on the paper framing. 
This should be as specific as possible and relatively long. (Try to use simple and understandable language).
# Reminder: you MUST finish the summary in one response. do NOT make the not-finished response.
# language:中文，除了专有名词是英文"""

PROCESSING_MODE_LABELS = {
    "library-only": "未处理",
    "skim": "略读",
    "deep": "精读",
    "reference-card": "参考文献卡片",
}

DEFAULT_PDF_LIBRARY_PATH = "E:\\论文库\\"
PAPER_BRIEF_BLOCK_ID = "paper-brief"
DEFAULT_CHROME_BRIEF_PROMPT_ID = "chrome-paper-brief-v1"
CANONICAL_PROJECTS = ["collaborative", "memories"]
PROJECT_CONTEXT_SOURCE_ENV_PREFIX = "PAPER_READER_PROJECT_CONTEXT_"
PROJECT_ALIASES = {
    "collaborative": "collaborative",
    "collective": "collaborative",
    "memories": "memories",
    "memoies": "memories",
}
MINDMAP_NODE_LIMIT = 4000
CANONICAL_PAPER_TAGS = [
    {"id": "HAI theory", "label": "HAI theory", "group": "paper-tag", "project_scope": "shared", "color": "#d8c3ff"},
    {"id": "How AI influence creativity?", "label": "How AI influence creativity?", "group": "paper-tag", "project_scope": "shared", "color": "#ffd27a"},
    {"id": "M_emperical study", "label": "M_emperical study", "group": "paper-tag", "project_scope": "memories", "color": "#f7b4ad"},
    {"id": "M_记忆管理工具", "label": "M_记忆管理工具", "group": "paper-tag", "project_scope": "memories", "color": "#f08a84"},
    {"id": "M_Theory_Memories influence creativity", "label": "M_Theory_Memories influence creativity", "group": "paper-tag", "project_scope": "memories", "color": "#c94d58"},
    {"id": "M_系统设计参考", "label": "M_系统设计参考", "group": "paper-tag", "project_scope": "memories", "color": "#e76666"},
    {"id": "M_写法参考", "label": "M_写法参考", "group": "paper-tag", "project_scope": "memories", "color": "#f4a1c2"},
    {"id": "M_visual narrative art _method/ strategies", "label": "M_visual narrative art _method/ strategies", "group": "paper-tag", "project_scope": "memories", "color": "#d94f7d"},
    {"id": "C_human-ai-deliberation", "label": "C_Human-AI Deliberation / Group Decision + AI", "group": "paper-tag", "project_scope": "collaborative", "color": "#79d4c8"},
    {"id": "C_private-public-flow", "label": "C_Private-Public Flow", "group": "paper-tag", "project_scope": "collaborative", "color": "#55b6c8"},
    {"id": "C_reasoning-externalization", "label": "C_Reasoning Externalization / Sensemaking", "group": "paper-tag", "project_scope": "collaborative", "color": "#5ec5a8"},
    {"id": "C_handoff", "label": "C_Handoff / Bridge", "group": "paper-tag", "project_scope": "collaborative", "color": "#8edbd0"},
    {"id": "C_boundary-object", "label": "C_Boundary Object", "group": "paper-tag", "project_scope": "collaborative", "color": "#72b7e6"},
    {"id": "C_group-chat-bot", "label": "C_Group Chat + Public AI/Bot", "group": "paper-tag", "project_scope": "collaborative", "color": "#6fcf97"},
    {"id": "C_branching-conversation", "label": "C_Branching Conversation", "group": "paper-tag", "project_scope": "collaborative", "color": "#9ad7b5"},
    {"id": "C_context-management", "label": "C_Context Management", "group": "paper-tag", "project_scope": "collaborative", "color": "#85c3dd"},
    {"id": "C_common-ground", "label": "C_Common Ground", "group": "paper-tag", "project_scope": "collaborative", "color": "#b0d7cf"},
    {"id": "C_materialization", "label": "C_Materialization of Cognitive Work", "group": "paper-tag", "project_scope": "collaborative", "color": "#7fcfb1"},
    {"id": "C_ai-mediated-communication", "label": "C_AI-mediated Communication", "group": "paper-tag", "project_scope": "collaborative", "color": "#67c7da"},
    {"id": "C_interface-reference", "label": "C_Interface Reference", "group": "paper-tag", "project_scope": "collaborative", "color": "#a7d8ef"},
    {"id": "C_hci-method", "label": "C_HCI Research Method", "group": "paper-tag", "project_scope": "collaborative", "color": "#98d5a4"},
    {"id": "C_potential-scenario", "label": "C_Potential Scenario", "group": "paper-tag", "project_scope": "collaborative", "color": "#6fbfb6"},
    {"id": "C_design-for-deliberation", "label": "C_Design for Deliberation", "group": "paper-tag", "project_scope": "collaborative", "color": "#8ac6c0"},
    {"id": "C_analytical-provenance", "label": "C_Analytical Provenance", "group": "paper-tag", "project_scope": "collaborative", "color": "#79b9d6"},
    {"id": "C_user-interview-dataset", "label": "C_用户访谈dataset", "group": "paper-tag", "project_scope": "collaborative", "color": "#9dddc7"},
]

CANONICAL_NOTE_TAGS = [
    {"id": "motivation参考", "label": "Motivation", "group": "note-tag"},
    {"id": "related works参考", "label": "Related Work", "group": "note-tag"},
    {"id": "system设计参考", "label": "System Design", "group": "note-tag"},
    {"id": "evaluation参考", "label": "Evaluation", "group": "note-tag"},
    {"id": "理论参考", "label": "Theory", "group": "note-tag"},
    {"id": "写法参考", "label": "Writing", "group": "note-tag"},
]

TAG_ALIAS_GROUPS = {
    "HAI theory": ["theory", "theory lens", "hai theory", "c_ 传统理论", "c_传统理论", "传统理论（你用来“抬高问题高度”的;最好收敛到1-2个理论）", "理论参考", "reference"],
    "How AI influence creativity?": ["how ai influence creativity", "ai influence creativity", "ai creativity impact", "genai creativity", "generative ai creativity"],
    "M_emperical study": ["m_empirical study", "m_emperical study", "empirical study", "用户研究", "实证研究"],
    "M_记忆管理工具": ["m_memory management tools", "memory management tools", "记忆管理工具", "personal memory tools"],
    "M_Theory_Memories influence creativity": ["memories influence creativity", "memory and creativity", "memory creativity theory", "记忆影响创造力"],
    "M_系统设计参考": ["m_system design reference", "系统设计参考", "system design reference"],
    "M_写法参考": ["m_writing reference", "写法参考", "writing reference"],
    "M_visual narrative art _method/ strategies": ["m_visual narrative art_method/strategies", "m_visual narrative art _method/strategies", "visual narrative art method strategies", "visual storytelling method strategies", "视觉叙事方法"],
    "C_human-ai-deliberation": ["human-ai-deliberation", "c_human-ai deliberation/group decision + ai", "human-ai deliberation/group decision + ai", "场景相同，方法/形式类似/human-ai deliberation/group decision + ai"],
    "C_private-public-flow": ["private-public-flow", "c_private ↔ public", "private ↔ public", "private ↔ public 信息流（dm ↔ group）", "问题同构、场景不同（最危险，但最值钱）/private ↔ public 信息流（dm ↔ group）"],
    "C_reasoning-externalization": ["reasoning-externalization", "c_reasoning externalization/sensemaking", "reasoning externalization/sensemaking", "问题同构、场景不同（最危险，但最值钱）/reasoning externalization/sensemaking（⚠️最重要的一类）", "human-ai sensemaking tools"],
    "C_handoff": ["handoff", "support handoff", "问题同构、场景不同（最危险，但最值钱）/private ↔ public 信息流（dm ↔ group）/support handoff"],
    "C_boundary-object": ["boundary-object", "boundry object", "boundary object", "boundary object theory", "ai as boundry object", "传统理论（你用来“抬高问题高度”的;最好收敛到1-2个理论）/boundry object", "传统理论（你用来“抬高问题高度”的;最好收敛到1-2个理论）/boundry object/理论", "传统理论（你用来“抬高问题高度”的;最好收敛到1-2个理论）/boundry object/ai act as dynamic boundry object"],
    "C_group-chat-bot": ["group-chat-bot", "c_group chat + 公共 ai/bot", "group chat + 公共 ai/bot", "方法/机制高度相似的工作/group chat + 公共 ai/bot"],
    "C_branching-conversation": ["branching-conversation", "c_branch conversations", "branch conversations", "branching conversations", "c_branch conversations; conctext management", "c_branch conversations; context management"],
    "C_context-management": ["context-management", "conctext management", "context management", "c_branch conversations; conctext management", "c_branch conversations; context management"],
    "C_common-ground": ["common-ground", "common groud", "common ground", "传统理论（你用来“抬高问题高度”的;最好收敛到1-2个理论）/common groud"],
    "C_materialization": ["materialization", "“materialization” of cognitive work", "materialization of cognitive work", "传统理论（你用来“抬高问题高度”的;最好收敛到1-2个理论）/“materialization” of cognitive work"],
    "C_ai-mediated-communication": ["ai-mediated-communication", "ai-mediated communication（agency/authorship）", "场景相似，但动机不同的工作/ai-mediated communication（agency/authorship）", "场景相似，但动机不同的工作/ai-mediated communication（agency/authorship）/把 ai 参与痕迹显式暴露给别人看"],
    "C_interface-reference": ["interface-reference", "c_interface refer", "interface refer"],
    "C_hci-method": ["hci-method", "hci 研究方法"],
    "C_potential-scenario": ["potential-scenario", "c_潜在场景"],
    "C_design-for-deliberation": ["design for deliberation"],
    "C_analytical-provenance": ["analytical provenance", "rationale/provenance anchoring"],
    "C_user-interview-dataset": ["用户访谈dataset", "user interview dataset"],
}

FRAME_ONLY_TAG_ALIASES = {
    "场景相同，方法/形式类似",
    "问题同构、场景不同（最危险，但最值钱）",
    "方法/机制高度相似的工作",
    "场景相似，但动机不同的工作",
    "传统理论（你用来“抬高问题高度”的;最好收敛到1-2个理论）",
}

TAG_ALIAS_TO_IDS: dict[str, list[str]] = {}


def tag_alias_key(value: Any) -> str:
    text = unicodedata.normalize("NFKC", html.unescape(str(value or ""))).casefold().strip()
    text = text.replace("boundry", "boundary").replace("groud", "ground").replace("conctext", "context")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*[/\\]+\s*", "/", text)
    text = text.strip(" /\\\t\r\n")
    return text


for canonical_id, aliases in TAG_ALIAS_GROUPS.items():
    TAG_ALIAS_TO_IDS.setdefault(tag_alias_key(canonical_id), [canonical_id])
    for alias in aliases:
        ids = TAG_ALIAS_TO_IDS.setdefault(tag_alias_key(alias), [])
        if canonical_id not in ids:
            ids.append(canonical_id)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path, default: Any, *, strict: bool = False) -> Any:
    for attempt in range(8):
        try:
            if not path.exists():
                return default
            with write_lock_for(path):
                if not path.exists():
                    return default
                return json.loads(path.read_text(encoding="utf-8-sig"))
        except PermissionError:
            if attempt == 7:
                raise
            time.sleep(0.04 * (attempt + 1))
        except json.JSONDecodeError:
            if strict:
                raise
            return default
    return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = write_lock_for(path)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp")
    with lock:
        try:
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            replace_with_retry(tmp, path)
        finally:
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = write_lock_for(path)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp")
    with lock:
        try:
            tmp.write_text(text, encoding="utf-8")
            replace_with_retry(tmp, path)
        finally:
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass


def copy_markdown_assets(markdown_path: Path | None, paper_dir: Path) -> None:
    if not markdown_path:
        return
    for folder_name in {"images", "assets"}:
        source = markdown_path.parent / folder_name
        if source.exists() and source.is_dir():
            shutil.copytree(source, paper_dir / folder_name, dirs_exist_ok=True)


def slugify(value: str, fallback: str = "paper") -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    value = value.strip("-")
    return value[:80] or fallback


def file_hash(path: Path, limit: int | None = None) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        remaining = limit
        while True:
            if remaining is None:
                chunk = handle.read(1024 * 1024)
            elif remaining <= 0:
                break
            else:
                chunk = handle.read(min(1024 * 1024, remaining))
                remaining -= len(chunk)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def find_config(start: Path) -> Path | None:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for folder in [current, *current.parents]:
        candidate = folder / CONFIG_FILE
        if candidate.exists():
            return candidate
    return None


def resolve_workspace(workspace_arg: str | None, start: Path | None = None) -> Path:
    if workspace_arg:
        return Path(workspace_arg).expanduser().resolve()
    configured_workspace = env_value("PAPER_READER_WORKSPACE")
    if configured_workspace:
        return Path(configured_workspace).expanduser().resolve()
    start = start or Path.cwd()
    config_path = find_config(start)
    if config_path:
        config = read_json(config_path, {})
        workspace = config.get("workspace")
        if workspace:
            workspace_path = Path(workspace)
            if not workspace_path.is_absolute():
                workspace_path = config_path.parent / workspace_path
            return workspace_path.resolve()
    return (Path.cwd() / DEFAULT_WORKSPACE_NAME).resolve()


def ensure_workspace(workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "papers").mkdir(parents=True, exist_ok=True)
    (workspace / "assets").mkdir(parents=True, exist_ok=True)
    (workspace / "paper_candidates").mkdir(parents=True, exist_ok=True)
    (workspace / "prompts").mkdir(parents=True, exist_ok=True)
    library_path = workspace / "library.json"
    if not library_path.exists():
        write_json(library_path, {"version": TOOL_VERSION, "papers": []})


def infer_processing_fields(paper_dir: Path, metadata: dict[str, Any] | None = None) -> dict[str, str]:
    metadata = metadata or {}
    mode = str(metadata.get("processing_mode") or metadata.get("reading_mode") or "").strip()
    status = str(metadata.get("processing_status") or "").strip()
    if not mode:
        segments = read_json(paper_dir / "segments.json", []) if (paper_dir / "segments.json").exists() else []
        if segments:
            mode = "deep"
            status = status or "ready"
        elif (paper_dir / "skim_summary.md").exists():
            mode = "skim"
            status = status or "ready"
        else:
            mode = "library-only"
            status = status or "not_processed"
    if not status:
        status = "ready" if mode in {"deep", "skim", "reference-card"} else "not_processed"
    return {"processing_mode": mode, "reading_mode": metadata.get("reading_mode") or mode, "processing_status": status}


def clean_preview_image_path(value: Any, paper_dir: Path) -> str:
    raw = str(value or "").strip().strip("<>").strip("'\"").replace("\\", "/")
    if not raw:
        return ""
    if re.match(r"^(https?:|data:)", raw, flags=re.I):
        return raw
    clean = urllib.parse.unquote(raw.split("#", 1)[0].split("?", 1)[0]).strip().lstrip("./")
    if not clean or clean.startswith("/") or ".." in Path(clean).parts:
        return ""
    if Path(clean).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
        return ""
    try:
        (paper_dir / clean).resolve().relative_to(paper_dir.resolve())
    except ValueError:
        return ""
    return clean if (paper_dir / clean).exists() else ""


def image_dimensions(path: Path) -> tuple[int, int]:
    try:
        data = path.read_bytes()[:512]
    except OSError:
        return 0, 0
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data.startswith((b"GIF87a", b"GIF89a")) and len(data) >= 10:
        return int.from_bytes(data[6:8], "little"), int.from_bytes(data[8:10], "little")
    if data.startswith(b"\xff\xd8"):
        try:
            raw = path.read_bytes()
        except OSError:
            return 0, 0
        index = 2
        while index + 9 < len(raw):
            if raw[index] != 0xFF:
                index += 1
                continue
            marker = raw[index + 1]
            index += 2
            if marker in {0xD8, 0xD9}:
                continue
            if index + 2 > len(raw):
                break
            length = int.from_bytes(raw[index : index + 2], "big")
            if length < 2 or index + length > len(raw):
                break
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF} and length >= 7:
                height = int.from_bytes(raw[index + 3 : index + 5], "big")
                width = int.from_bytes(raw[index + 5 : index + 7], "big")
                return width, height
            index += length
    return 0, 0


def is_logo_like_image(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return False
    size = path.stat().st_size
    width, height = image_dimensions(path)
    area = width * height if width and height else 0
    ratio = max(width / height, height / width) if width and height else 1
    return size < 6000 or bool(width and height and (width < 220 or height < 120 or area < 30000 or ratio > 8))


def local_preview_score(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return -1
    size = path.stat().st_size
    width, height = image_dimensions(path)
    area = width * height if width and height else 0
    if is_logo_like_image(path):
        return -1
    return int(min(size, 400000) / 1000) + int(min(area, 2_000_000) / 10000)


def best_preview_candidate(candidates: list[dict[str, str]], paper_dir: Path, *, allow_fallback: bool = True) -> dict[str, str]:
    scored: list[tuple[int, dict[str, str]]] = []
    fallback: list[dict[str, str]] = []
    for candidate in candidates:
        path = clean_preview_image_path(candidate.get("preview_image"), paper_dir)
        if not path or re.match(r"^(https?:|data:)", path, flags=re.I):
            continue
        normalized = {**candidate, "preview_image": path}
        fallback.append(normalized)
        score = local_preview_score(paper_dir / path)
        if score >= 0:
            scored.append((score, normalized))
    if scored:
        return max(scored, key=lambda item: item[0])[1]
    return fallback[0] if allow_fallback and fallback else {}


def first_markdown_image(markdown: str, paper_dir: Path) -> dict[str, str]:
    candidates: list[dict[str, str]] = []
    for match in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", str(markdown or "")):
        path = clean_preview_image_path(match.group(2), paper_dir)
        if path:
            candidates.append({"preview_image": path, "preview_image_alt": str(match.group(1) or "Figure 1").strip() or "Figure 1"})
    return best_preview_candidate(candidates, paper_dir, allow_fallback=False)


def folder_preview_image(paper_dir: Path, folder_name: str) -> dict[str, str]:
    folder = paper_dir / folder_name
    if not folder.exists() or not folder.is_dir():
        return {}
    candidates = []
    for path in sorted(folder.iterdir(), key=lambda item: item.name.lower()):
        preview = clean_preview_image_path(str(path.relative_to(paper_dir)), paper_dir)
        if preview:
            candidates.append({"preview_image": preview, "preview_image_alt": "Figure 1"})
    return best_preview_candidate(candidates, paper_dir, allow_fallback=False)


def render_pdf_preview_image(paper_dir: Path) -> dict[str, str]:
    pdf_path = paper_dir / "original.pdf"
    if not pdf_path.exists() or not pdf_path.is_file():
        return {}
    preview_rel = "assets/preview_page_1.png"
    preview_path = paper_dir / preview_rel
    if preview_path.exists() and local_preview_score(preview_path) >= 0:
        return {"preview_image": preview_rel, "preview_image_alt": "PDF page 1 preview"}
    try:
        import pypdfium2 as pdfium  # type: ignore[import-not-found]

        pdf = pdfium.PdfDocument(str(pdf_path))
        if len(pdf) < 1:
            return {}
        page = pdf[0]
        bitmap = page.render(scale=1.5)
        image = bitmap.to_pil()
        if image.mode == "RGBA":
            from PIL import Image  # type: ignore[import-not-found]

            background = Image.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")
        image.thumbnail((1200, 1600))
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(preview_path, format="PNG", optimize=True)
        for resource in (bitmap, page, pdf):
            close = getattr(resource, "close", None)
            if callable(close):
                close()
    except Exception:  # noqa: BLE001 - preview generation is best-effort
        return {}
    return {"preview_image": preview_rel, "preview_image_alt": "PDF page 1 preview"} if preview_path.exists() else {}


def render_pdf_page_preview(paper_dir: Path, page_number: int) -> str:
    pdf_path = paper_dir / "original.pdf"
    if page_number < 1 or not pdf_path.exists() or not pdf_path.is_file():
        return ""
    preview_rel = f"assets/page_previews/page_{page_number}.png"
    preview_path = paper_dir / preview_rel
    if preview_path.exists() and preview_path.stat().st_size > 0:
        return preview_rel
    try:
        import pypdfium2 as pdfium  # type: ignore[import-not-found]

        pdf = pdfium.PdfDocument(str(pdf_path))
        if page_number > len(pdf):
            return ""
        page = pdf[page_number - 1]
        bitmap = page.render(scale=1.8)
        image = bitmap.to_pil()
        if image.mode == "RGBA":
            from PIL import Image  # type: ignore[import-not-found]

            background = Image.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")
        image.thumbnail((1500, 2000))
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(preview_path, format="PNG", optimize=True)
        for resource in (bitmap, page, pdf):
            close = getattr(resource, "close", None)
            if callable(close):
                close()
    except Exception:  # noqa: BLE001 - page fallback generation is best-effort
        return ""
    return preview_rel if preview_path.exists() else ""


def pdf_page_texts(pdf_path: Path) -> list[str]:
    if not pdf_path.exists() or not pdf_path.is_file():
        return []
    try:
        import pypdf  # type: ignore[import-not-found]

        reader = pypdf.PdfReader(str(pdf_path))
        return [str(page.extract_text() or "") for page in reader.pages]
    except Exception:  # noqa: BLE001 - figure fallback should not block opening a paper
        return []


def first_markdown_image_path(markdown: str) -> str:
    match = re.search(r"!\[[^\]]*\]\(([^)]+)\)", str(markdown or ""))
    return match.group(1).strip() if match else ""


def figure_caption_image_presence(paper_dir: Path, segments: list[dict[str, Any]]) -> dict[str, bool]:
    presence: dict[str, bool] = {}
    pending_image_path = ""
    pending_image_exists = False
    for segment in segments:
        markdown = str(segment.get("markdown") or "")
        image_path = first_markdown_image_path(markdown)
        if image_path:
            pending_image_path = image_path
            pending_image_exists = (paper_dir / image_path).exists()
        caption_match = re.search(r"(?:^|\n)\s*(?:fig(?:ure)?\.?)\s*(\d+)(?:\s*(?:[.\-]\s*)?\(?[a-z]\)?)?\s*[:.]\s*(.+)", markdown, flags=re.I | re.S)
        if caption_match:
            presence[caption_match.group(1)] = bool(pending_image_path and pending_image_exists)
            pending_image_path = ""
            pending_image_exists = False
    return presence


def figure_fallbacks_from_pdf(paper_dir: Path, segments: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Explicit/offline fallback generation, never part of a reader GET."""
    caption_numbers: list[str] = []
    for segment in segments:
        caption_match = re.search(r"(?:^|\n)\s*(?:fig(?:ure)?\.?)\s*(\d+)(?:\s*(?:[.\-]\s*)?\(?[a-z]\)?)?\s*[:.]\s*(.+)", str(segment.get("markdown") or ""), flags=re.I | re.S)
        if caption_match and caption_match.group(1) not in caption_numbers:
            caption_numbers.append(caption_match.group(1))
    if not caption_numbers:
        return {}
    image_presence = figure_caption_image_presence(paper_dir, segments)
    if all(image_presence.get(number, False) for number in caption_numbers):
        return {}
    page_texts = pdf_page_texts(paper_dir / "original.pdf")
    if not page_texts:
        return {}
    fallbacks: dict[str, dict[str, Any]] = {}
    for segment in segments:
        markdown = str(segment.get("markdown") or "")
        caption_match = re.search(r"(?:^|\n)\s*(?:fig(?:ure)?\.?)\s*(\d+)(?:\s*(?:[.\-]\s*)?\(?[a-z]\)?)?\s*[:.]\s*(.+)", markdown, flags=re.I | re.S)
        if not caption_match:
            continue
        number = caption_match.group(1)
        if number in fallbacks:
            continue
        caption = markdown_plain_text(markdown)
        caption_probe = re.sub(r"\s+", " ", caption[:180]).strip()
        if not caption_probe:
            continue
        page_number = 0
        caption_key = re.sub(r"\s+", " ", f"Figure {number}")
        for index, page_text in enumerate(page_texts, start=1):
            normalized_page = re.sub(r"\s+", " ", page_text)
            if caption_probe in normalized_page or (caption_key in normalized_page and caption_probe[:60] in normalized_page):
                page_number = index
                break
        if not page_number:
            continue
        src = render_pdf_page_preview(paper_dir, page_number)
        if not src:
            continue
        fallbacks[number] = {
            "number": number,
            "src": src,
            "caption_segment_id": str(segment.get("id") or ""),
            "caption": markdown,
            "page": page_number,
            "fallback": "pdf-page",
            "replace_existing": not image_presence.get(number, False),
        }
    return fallbacks


def infer_paper_preview_image(paper_dir: Path, metadata: dict[str, Any] | None = None, *, generate_pdf_preview: bool = False) -> dict[str, str]:
    metadata = metadata or {}
    explicit = clean_preview_image_path(metadata.get("preview_image") or metadata.get("cover_image") or metadata.get("thumbnail"), paper_dir)
    if explicit:
        explicit_preview = {"preview_image": explicit, "preview_image_alt": str(metadata.get("preview_image_alt") or metadata.get("title") or "Paper preview image")}
        if re.match(r"^(https?:|data:)", explicit, flags=re.I) or local_preview_score(paper_dir / explicit) >= 0:
            return explicit_preview
    else:
        explicit_preview = {}
    segments = read_json(paper_dir / "segments.json", []) if (paper_dir / "segments.json").exists() else []
    if isinstance(segments, list):
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            preview = first_markdown_image(str(segment.get("markdown") or segment.get("text") or ""), paper_dir)
            if preview:
                return preview
    reader_path = paper_dir / "reader.md"
    if reader_path.exists():
        preview = first_markdown_image(reader_path.read_text(encoding="utf-8", errors="ignore"), paper_dir)
        if preview:
            return preview
    for folder_name in ("images", "assets"):
        preview = folder_preview_image(paper_dir, folder_name)
        if preview:
            return preview
    if generate_pdf_preview:
        preview = render_pdf_preview_image(paper_dir)
        if preview:
            return preview
    return explicit_preview


def paper_brief_annotation_counts(paper_dir: Path) -> dict[str, int]:
    thinking = read_json(paper_dir / "thinking.json", {"annotations": []})
    annotations = thinking.get("annotations") if isinstance(thinking, dict) else []
    highlight_count = 0
    note_count = 0
    for item in annotations if isinstance(annotations, list) else []:
        if not isinstance(item, dict):
            continue
        if str(item.get("block_id") or item.get("thinking_block_id") or "").strip() != PAPER_BRIEF_BLOCK_ID:
            continue
        if not str(item.get("quote") or item.get("note") or "").strip():
            continue
        highlight_count += 1
        if str(item.get("note") or "").strip():
            note_count += 1
    return {
        "paper_brief_annotation_count": highlight_count,
        "paper_brief_highlight_count": highlight_count,
        "paper_brief_note_count": note_count,
    }


def normalized_metadata(paper_dir: Path, metadata: dict[str, Any], *, generate_pdf_preview: bool = False, discover_preview: bool = True) -> dict[str, Any]:
    fields = infer_processing_fields(paper_dir, metadata)
    result = {**metadata}
    if "author" in result and not result.get("authors"):
        result["authors"] = result.get("author")
    if "institution" in result and not result.get("institutions"):
        result["institutions"] = result.get("institution")
    if "journal" in result and not result.get("venue"):
        result["venue"] = result.get("journal")
    if "publication_year" in result and not result.get("year"):
        result["year"] = result.get("publication_year")
    result.setdefault("processing_mode", fields["processing_mode"])
    result.setdefault("reading_mode", fields["reading_mode"])
    result.setdefault("processing_status", fields["processing_status"])
    result.setdefault("processing_error", "")
    if result.get("preview_image") and not clean_preview_image_path(result.get("preview_image"), paper_dir):
        result["preview_image"] = ""
        result["preview_image_alt"] = ""
    if discover_preview and not result.get("preview_image"):
        preview = infer_paper_preview_image(paper_dir, result, generate_pdf_preview=generate_pdf_preview)
        if preview.get("preview_image"):
            result.update(preview)
    counts = paper_brief_annotation_counts(paper_dir)
    summary = result.get("reading_progress_summary") if isinstance(result.get("reading_progress_summary"), dict) else {}
    if summary or counts.get("paper_brief_annotation_count"):
        result["reading_progress_summary"] = {**summary, **counts}
    return result


def official_title_from_segments(segments: list[dict[str, Any]], fallback: str = "") -> str:
    title = guess_title_from_segments(segments, fallback or "")
    clean = title.strip()
    return clean if clean and clean != fallback else ""


def should_replace_title(metadata: dict[str, Any], candidate: str) -> bool:
    candidate = str(candidate or "").strip()
    if not candidate:
        return False
    if metadata.get("title_locked") or metadata.get("title_source") in {"user", "feishu"}:
        return False
    current = str(metadata.get("title") or "").strip()
    if not current:
        return True
    current_slug = slugify(current, "")
    candidate_slug = slugify(candidate, "")
    if current_slug and candidate_slug and (current_slug in candidate_slug or candidate_slug in current_slug):
        return len(candidate) > len(current)
    return bool((metadata.get("title_source") or "") in {"filename", "library", "reference", ""})


def update_title_from_segments(metadata: dict[str, Any], segments: list[dict[str, Any]], fallback: str = "") -> str:
    candidate = official_title_from_segments(segments, fallback)
    if should_replace_title(metadata, candidate):
        metadata["title"] = candidate
        metadata["title_source"] = "paper"
    return str(metadata.get("title") or candidate or fallback)


def normalize_year(value: Any) -> str:
    match = re.search(r"\b(19|20)\d{2}\b", str(value or ""))
    return match.group(0) if match else str(value or "").strip()


def normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        raw_values = value
    else:
        raw_values = str(value or "").split(",")
    result: list[str] = []
    seen: set[str] = set()
    for item in raw_values:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def normalize_project_name(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    key = re.sub(r"\s+", "", unicodedata.normalize("NFKC", text).casefold())
    return PROJECT_ALIASES.get(key, text)


def normalize_project_list(value: Any) -> list[str]:
    projects = []
    seen: set[str] = set()
    for item in normalize_string_list(value):
        project = normalize_project_name(item)
        if project and project not in seen:
            seen.add(project)
            projects.append(project)
    return projects


def normalize_tag_path(value: Any) -> str:
    text = html.unescape(str(value or "")).strip()
    if not text:
        return ""
    parts = [re.sub(r"\s+", " ", part).strip(" /\\\t\r\n") for part in re.split(r"[/\\]+", text)]
    return "/".join(part for part in parts if part)


def canonical_tag_ids(value: Any) -> list[str]:
    tag = normalize_tag_path(value)
    if not tag:
        return []
    key = tag_alias_key(tag)
    if key in {tag_alias_key(alias) for alias in FRAME_ONLY_TAG_ALIASES}:
        return []
    if key in TAG_ALIAS_TO_IDS:
        return TAG_ALIAS_TO_IDS[key]
    parts = [part for part in tag.split("/") if part]
    for part in reversed(parts):
        part_key = tag_alias_key(part)
        if part_key in TAG_ALIAS_TO_IDS:
            return TAG_ALIAS_TO_IDS[part_key]
    return [tag]


def normalize_tag_paths(value: Any) -> list[str]:
    tags = []
    seen: set[str] = set()
    raw_values = value if isinstance(value, list) else str(value or "").split(",")
    for item in raw_values:
        for tag in canonical_tag_ids(item):
            if tag and tag not in seen:
                seen.add(tag)
                tags.append(tag)
    return tags


def tag_dictionary() -> dict[str, Any]:
    return {
        "paper_tags": CANONICAL_PAPER_TAGS,
        "note_tags": CANONICAL_NOTE_TAGS,
        "aliases": {alias: ids for alias, ids in sorted(TAG_ALIAS_TO_IDS.items())},
        "frames": [
            {"id": "same-scene", "label": "场景相同，方法/形式类似"},
            {"id": "analogous-problem", "label": "问题同构、场景不同"},
            {"id": "similar-mechanism", "label": "方法/机制高度相似"},
            {"id": "adjacent-scene", "label": "场景相似，但动机不同"},
            {"id": "theory-lens", "label": "传统理论"},
            {"id": "potential-scenario", "label": "潜在场景"},
        ],
    }


class ContextHTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0
        self.heading_level = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
        elif re.fullmatch(r"h[1-6]", tag):
            self.heading_level = int(tag[1])
            self.parts.append("\n" + "#" * self.heading_level + " ")
        elif tag in {"p", "div", "section", "article", "header", "footer", "li", "tr", "br", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1
        elif re.fullmatch(r"h[1-6]", tag):
            self.heading_level = 0
            self.parts.append("\n")
        elif tag in {"p", "div", "section", "article", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth and data:
            self.parts.append(data)

    def text(self) -> str:
        clean = html.unescape("".join(self.parts))
        clean = re.sub(r"[ \t\r\f\v]+", " ", clean)
        clean = re.sub(r"\n\s*\n\s*\n+", "\n\n", clean)
        return clean.strip()


def project_contexts_path(workspace: Path) -> Path:
    return workspace / "project_contexts.json"


def default_project_context_source(project: str) -> str:
    key = re.sub(r"[^A-Z0-9]+", "_", normalize_project_name(project).upper()).strip("_")
    return env_value(f"{PROJECT_CONTEXT_SOURCE_ENV_PREFIX}{key}") if key else ""


def read_project_contexts(workspace: Path) -> dict[str, Any]:
    raw = read_json(project_contexts_path(workspace), {"version": 1, "contexts": {}})
    contexts = raw.get("contexts") if isinstance(raw.get("contexts"), dict) else {}
    for project in CANONICAL_PROJECTS:
        if project not in contexts:
            contexts[project] = {"project": project, "source_path": default_project_context_source(project), "cards": []}
    return {"version": 1, "contexts": contexts, "updated_at": raw.get("updated_at", "")}


def save_project_contexts(workspace: Path, data: dict[str, Any]) -> dict[str, Any]:
    payload = {"version": 1, "contexts": data.get("contexts", {}), "updated_at": now_iso()}
    write_json(project_contexts_path(workspace), payload)
    return payload


def clean_context_source_text(text: str, suffix: str = "") -> str:
    raw = str(text or "")
    if suffix.lower() in {".html", ".htm"} or re.search(r"<\s*(html|body|section|article|div|p|h[1-6])\b", raw, flags=re.I):
        parser = ContextHTMLTextExtractor()
        parser.feed(raw)
        raw = parser.text()
    else:
        raw = markdown_plain_text(raw)
    raw = re.sub(r"\n\s*\n\s*\n+", "\n\n", raw)
    raw = re.sub(r"[ \t]+", " ", raw)
    return raw.strip()


def context_card_type(title: str, body: str) -> str:
    text = f"{title}\n{body}".lower()
    if re.search(r"\b(claim|contribution|thesis|argument)\b|贡献|主张", text):
        return "claim"
    if re.search(r"\b(question|rq|problem|gap|challenge)\b|问题|缺口|挑战", text):
        return "problem"
    if re.search(r"\b(method|system|design|workflow|pipeline|interface)\b|方法|系统|设计|流程|界面", text):
        return "method"
    if re.search(r"\b(study|evaluation|participant|finding|result|dataset)\b|实验|评估|发现|访谈|数据", text):
        return "evidence"
    if re.search(r"\b(outline|section|paper skeleton|draft)\b|大纲|章节|论文", text):
        return "outline"
    return "background"


def compact_context_body(text: str, max_chars: int = 720) -> str:
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(clean) <= max_chars:
        return clean
    return clean[:max_chars].rstrip(" ,.;:，。；：") + "..."


def build_project_context_cards(project: str, source_text: str, max_cards: int = 16) -> list[dict[str, Any]]:
    raw = str(source_text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = clean_context_source_text(raw) if re.search(r"<\s*(html|body|section|article|div|p|h[1-6])\b", raw, flags=re.I) else raw.strip()
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    if not text:
        return []
    lines = [line.strip() for line in text.splitlines()]
    sections: list[tuple[str, list[str]]] = []
    major_heading_indexes = [index for index, line in enumerate(lines) if re.match(r"^\d{2}\s*[·.:-]\s+", line)]
    if major_heading_indexes:
        intro = [line for line in lines[: major_heading_indexes[0]] if line and not re.match(r"^[A-Z][A-Za-z &/]+$", line)]
        if intro:
            sections.append(("Project Overview", intro))
        for position, start in enumerate(major_heading_indexes):
            end = major_heading_indexes[position + 1] if position + 1 < len(major_heading_indexes) else len(lines)
            title = re.sub(r"^#{1,6}\s*", "", lines[start]).strip()
            body = [line for line in lines[start + 1 : end] if line]
            sections.append((title, body))
    else:
        current_title = "Project Background"
        current_body: list[str] = []
        heading_pattern = re.compile(r"^(?:#{1,6}\s*)?((?:\d+(?:\.\d+)*|\d{2})\s*(?:[.)·:-]\s*)?[A-Z0-9][^\n]{3,110}|[A-Z][^\n]{3,100})$")
        for line in lines:
            if not line:
                continue
            markdown_heading = bool(re.match(r"^#{1,6}\s+", line))
            is_heading = markdown_heading or (bool(heading_pattern.match(line)) and len(line.split()) <= 14 and not line.endswith("."))
            if is_heading and current_body:
                sections.append((current_title, current_body))
                current_title = re.sub(r"^#{1,6}\s*", "", line).strip()
                current_body = []
            elif is_heading and current_title == "Project Background" and not current_body:
                current_title = re.sub(r"^#{1,6}\s*", "", line).strip()
            else:
                current_body.append(line)
        if current_body:
            sections.append((current_title, current_body))
    if not sections:
        chunks = re.split(r"(?<=[。.!?？])\s+", text)
        sections = [("Project Background", chunks)]

    cards: list[dict[str, Any]] = []
    for index, (title, body_lines) in enumerate(sections):
        body = " ".join(body_lines).strip()
        summary = compact_context_body(body)
        if not summary:
            continue
        card_id = hashlib.sha1(f"{project}\n{title}\n{body[:400]}".encode("utf-8", errors="ignore")).hexdigest()[:12]
        cards.append(
            {
                "id": f"ctx-{card_id}",
                "project": project,
                "title": compact_context_body(title, 120) or f"Context {index + 1}",
                "summary": summary,
                "type": context_card_type(title, body),
                "source": "local-file",
                "order": index,
            }
        )
        if len(cards) >= max_cards:
            break
    return cards


def project_context_summary_for_prompt(context: dict[str, Any], max_chars: int = 5200) -> str:
    cards = context.get("cards") if isinstance(context.get("cards"), list) else []
    lines = []
    for card in cards:
        title = str(card.get("title") or "Context").strip()
        card_type = str(card.get("type") or "background").strip()
        summary = compact_context_body(str(card.get("summary") or ""), 520)
        if summary:
            lines.append(f"- [{card_type}] {title}: {summary}")
    result = "\n".join(lines).strip()
    return result[:max_chars].rstrip() + ("\n..." if len(result) > max_chars else "")


def load_project_context(workspace: Path, project: Any) -> dict[str, Any]:
    clean_project = normalize_project_name(project) or "collaborative"
    contexts = read_project_contexts(workspace)
    context = contexts.get("contexts", {}).get(clean_project, {})
    if not context:
        context = {"project": clean_project, "source_path": default_project_context_source(clean_project), "cards": []}
    return {**context, "project": clean_project}


def upsert_project_context(workspace: Path, project: Any, data: dict[str, Any]) -> dict[str, Any]:
    clean_project = normalize_project_name(project) or "collaborative"
    contexts = read_project_contexts(workspace)
    current = contexts.setdefault("contexts", {}).get(clean_project, {})
    next_context = {**current, "project": clean_project}
    if "source_path" in data:
        next_context["source_path"] = str(data.get("source_path") or "").strip()
    if "cards" in data and isinstance(data.get("cards"), list):
        next_context["cards"] = data.get("cards")
    next_context["updated_at"] = now_iso()
    contexts["contexts"][clean_project] = next_context
    save_project_contexts(workspace, contexts)
    return next_context


def refresh_project_context_from_source(workspace: Path, project: Any, source_path: str = "") -> dict[str, Any]:
    clean_project = normalize_project_name(project) or "collaborative"
    current = load_project_context(workspace, clean_project)
    raw_path = str(source_path or current.get("source_path") or default_project_context_source(clean_project) or "").strip()
    if not raw_path:
        raise ValueError("source_path is required")
    path = Path(raw_path).expanduser()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Project context source not found: {raw_path}")
    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    source_text = clean_context_source_text(raw_text, path.suffix)
    cards = build_project_context_cards(clean_project, source_text)
    context = upsert_project_context(
        workspace,
        clean_project,
        {
            "source_path": str(path),
            "cards": cards,
        },
    )
    context.update(
        {
            "source_size": path.stat().st_size,
            "source_mtime": dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc).isoformat(),
            "source_chars": len(source_text),
            "card_count": len(cards),
            "refreshed_at": now_iso(),
        }
    )
    contexts = read_project_contexts(workspace)
    contexts.setdefault("contexts", {})[clean_project] = context
    save_project_contexts(workspace, contexts)
    return context


def metadata_projects(metadata: dict[str, Any]) -> list[str]:
    projects = normalize_project_list(metadata.get("projects", []))
    legacy_project = normalize_project_name(metadata.get("project") or "")
    if legacy_project and legacy_project not in projects:
        projects.insert(0, legacy_project)
    return projects


def normalize_title_key(title: Any) -> str:
    normalized = unicodedata.normalize("NFKC", html.unescape(str(title or ""))).casefold()
    return "".join(char for char in normalized if char.isalnum())


def normalize_title_key_without_leading_articles(title: Any) -> str:
    normalized = unicodedata.normalize("NFKC", html.unescape(str(title or ""))).casefold()
    normalized = re.sub(r"^\s*(?:the|a|an)\s+", "", normalized)
    return "".join(char for char in normalized if char.isalnum())


def title_key_is_usable(title_key: str) -> bool:
    if not title_key:
        return False
    cjk_count = sum(1 for char in title_key if "\u4e00" <= char <= "\u9fff")
    return len(title_key) >= 12 or cjk_count >= 6


def count_paper_notes(paper_dir: Path) -> int:
    annotations = read_json(paper_dir / "annotations.json", {"annotations": []}).get("annotations", [])
    return sum(1 for item in annotations if isinstance(item, dict) and str(item.get("note") or "").strip())


def duplicate_existing_summary(workspace: Path, paper: dict[str, Any]) -> dict[str, Any]:
    paper_dir = workspace / paper.get("paper_dir", "")
    metadata = read_json(paper_dir / "metadata.json", {}) if paper_dir.exists() else {}
    return {
        "id": paper.get("id", ""),
        "title": metadata.get("title") or paper.get("title") or paper.get("id", ""),
        "authors": metadata.get("authors") or paper.get("authors", ""),
        "year": normalize_year(metadata.get("year") or paper.get("year", "")),
        "venue": metadata.get("venue") or paper.get("venue", ""),
        "read_status": metadata.get("read_status") or paper.get("read_status", "unread"),
        "note_count": count_paper_notes(paper_dir) if paper_dir.exists() else 0,
        "source_pdf_name": metadata.get("source_pdf_name") or paper.get("source_pdf_name", ""),
        "paper_dir": paper.get("paper_dir", ""),
    }


def find_duplicate_paper_by_title(workspace: Path, title: Any, exclude_paper_id: str | None = None) -> dict[str, Any] | None:
    title_key = normalize_title_key(title)
    if not title_key_is_usable(title_key):
        return None
    title_keys = {title_key, normalize_title_key_without_leading_articles(title)}
    title_keys = {key for key in title_keys if title_key_is_usable(key)}
    library = load_library_raw(workspace)
    for paper in library.get("papers", []):
        paper_id = str(paper.get("id") or "")
        if exclude_paper_id and paper_id == exclude_paper_id:
            continue
        paper_dir = workspace / paper.get("paper_dir", "")
        metadata = {}
        existing_key = str(paper.get("title_key") or "")
        if not existing_key:
            existing_title = paper.get("title") or ""
            existing_key = normalize_title_key(existing_title) if existing_title else ""
        if not existing_key and paper_dir.exists():
            metadata = read_json(paper_dir / "metadata.json", {})
            existing_key = str(metadata.get("title_key") or normalize_title_key(metadata.get("title") or ""))
        existing_title = paper.get("title") or metadata.get("title") or ""
        existing_keys = {existing_key, normalize_title_key_without_leading_articles(existing_title)}
        existing_keys = {key for key in existing_keys if title_key_is_usable(key)}
        if title_keys & existing_keys:
            return paper
        if existing_title and reference_title_match_score(title, existing_title) >= 0.9:
            return paper
    return None


def duplicate_paper_response(workspace: Path, title: str, source_name: str, existing: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": False,
        "duplicate": True,
        "candidate": {"title": title, "source_name": source_name, "title_key": normalize_title_key(title)},
        "existing": duplicate_existing_summary(workspace, existing),
    }


def paper_record_dir(workspace: Path, paper: dict[str, Any]) -> Path:
    return workspace / str(paper.get("paper_dir") or f"papers/{paper.get('id', '')}")


def paper_record_has_pdf(workspace: Path, paper: dict[str, Any]) -> bool:
    paper_dir = paper_record_dir(workspace, paper)
    if (paper_dir / "original.pdf").exists():
        return True
    metadata = read_json(paper_dir / "metadata.json", {}) if paper_dir.exists() else {}
    return bool(metadata.get("source_pdf") or paper.get("source_pdf"))


def duplicate_can_accept_pdf(workspace: Path, paper: dict[str, Any]) -> bool:
    return bool(paper.get("id")) and not paper_record_has_pdf(workspace, paper)


def backup_paper_before_replace(paper_dir: Path) -> str:
    if not paper_dir.exists():
        return ""
    backup_dir = paper_dir / "backups" / ("replace-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    backup_dir.mkdir(parents=True, exist_ok=True)
    for name in {
        "metadata.json",
        "annotations.json",
        "thinking.json",
        "takeaway_doc.json",
        "reading_progress.json",
        "segments.json",
        "outline.json",
        "reference_cards.json",
        "source_map.json",
        "translation_notes.md",
        "terminology_ledger.json",
        "paper.md",
        "reader.md",
        "annotated.md",
        "notes.md",
        "raw.md",
        "skim_analysis.json",
        "skim_summary.md",
        "original.pdf",
    }:
        source = paper_dir / name
        if source.exists() and source.is_file():
            shutil.copy2(source, backup_dir / name)
    return str(backup_dir)


def metadata_with_citation(metadata: dict[str, Any], *, force: bool = False) -> dict[str, Any]:
    if not force and metadata.get("citation_count") not in {None, ""}:
        return metadata
    citation = fetch_citation_info(metadata)
    metadata.update(citation)
    metadata["citation_updated_at"] = now_iso()
    return metadata


READING_SKIMMED_MS = 2500
READING_CAREFUL_MS = 20000
READ_STATUS_RANK = {"unread": 0, "skimming": 1, "skimmed": 2, "deep-reading": 3, "read": 4, "archived": 5}


def clean_progress_segment(value: Any) -> dict[str, Any]:
    value = value if isinstance(value, dict) else {}
    visible_ms = max(0, min(24 * 60 * 60 * 1000, int(float(value.get("visible_ms") or 0))))
    visits = max(0, min(10000, int(float(value.get("visits") or 0))))
    return {
        "visible_ms": visible_ms,
        "visits": visits,
        "updated_at": str(value.get("updated_at") or now_iso()),
    }


def clean_reading_progress(data: Any) -> dict[str, Any]:
    data = data if isinstance(data, dict) else {}
    raw_segments = data.get("segments") if isinstance(data.get("segments"), dict) else {}
    segments: dict[str, dict[str, Any]] = {}
    for segment_id, value in raw_segments.items():
        clean_id = str(segment_id or "").strip()
        if clean_id:
            segments[clean_id] = clean_progress_segment(value)
    return {
        "version": 1,
        "paper_id": str(data.get("paper_id") or ""),
        "segments": segments,
        "summary": data.get("summary") if isinstance(data.get("summary"), dict) else {},
        "updated_at": str(data.get("updated_at") or ""),
    }


def load_reading_progress(paper_dir: Path) -> dict[str, Any]:
    progress = clean_reading_progress(read_json(paper_dir / "reading_progress.json", {"version": 1, "segments": {}}))
    return enrich_reading_progress(paper_dir, progress)


def annotation_counts_by_segment(paper_dir: Path) -> dict[str, dict[str, int]]:
    annotations = read_json(paper_dir / "annotations.json", {"annotations": []}).get("annotations", [])
    counts: dict[str, dict[str, int]] = {}
    for annotation in annotations:
        if not isinstance(annotation, dict) or is_teacher_definition(annotation):
            continue
        segment_id = str(annotation.get("segment_id") or "").strip()
        if not segment_id:
            continue
        bucket = counts.setdefault(segment_id, {"highlight_count": 0, "note_count": 0})
        bucket["highlight_count"] += 1
        if str(annotation.get("note") or "").strip():
            bucket["note_count"] += 1
    return counts


def reading_segment_state(visible_ms: int, highlight_count: int, note_count: int) -> str:
    if note_count > 0 or highlight_count >= 2 or visible_ms >= READING_CAREFUL_MS:
        return "careful"
    if highlight_count > 0 or visible_ms >= READING_SKIMMED_MS:
        return "skimmed"
    return "unread"


def reading_segment_depth(visible_ms: int, state: str, highlight_count: int, note_count: int) -> float:
    if state == "unread":
        return 0.0
    time_depth = min(1.0, visible_ms / READING_CAREFUL_MS)
    engagement_depth = min(0.25, note_count * 0.16 + highlight_count * 0.07)
    depth = 0.12 + time_depth * 0.58 + engagement_depth
    if state == "careful":
        depth = max(depth, 0.58)
    return round(min(0.92, max(0.12, depth)), 3)


def readable_segment_ids(paper_dir: Path) -> set[str]:
    segments = load_segments(paper_dir)
    ids = {
        str(segment.get("id") or "").strip()
        for segment in segments
        if str(segment.get("id") or "").strip()
        and segment.get("kind") != "heading"
        and str(segment.get("markdown") or segment.get("translation") or "").strip()
    }
    return ids or {str(segment.get("id") or "").strip() for segment in segments if str(segment.get("id") or "").strip()}


def summarize_reading_progress(paper_dir: Path, progress: dict[str, Any]) -> dict[str, Any]:
    readable_ids = readable_segment_ids(paper_dir)
    total = len(readable_ids) or 0
    counts = {"unread": 0, "skimmed": 0, "careful": 0}
    note_total = 0
    highlight_total = 0
    visible_ms_total = 0
    visit_total = 0
    for segment_id in readable_ids:
        item = progress.get("segments", {}).get(segment_id, {})
        state = item.get("state") or "unread"
        if state not in counts:
            state = "unread"
        counts[state] += 1
        visible_ms_total += int(item.get("visible_ms") or 0)
        visit_total += int(item.get("visits") or 0)
        note_total += int(item.get("note_count") or 0)
        highlight_total += int(item.get("highlight_count") or 0)
    covered = counts["skimmed"] + counts["careful"]
    coverage_ratio = (covered / total) if total else 0.0
    careful_ratio = (counts["careful"] / total) if total else 0.0
    if total and coverage_ratio >= 0.60 and careful_ratio >= 0.35:
        read_status = "read"
    elif note_total >= 8:
        read_status = "read"
    elif careful_ratio >= 0.15 or note_total >= 3:
        read_status = "deep-reading"
    elif coverage_ratio >= 0.35:
        read_status = "skimmed"
    elif covered > 0:
        read_status = "skimming"
    else:
        read_status = "unread"
    return {
        "total_segments": total,
        "unread": counts["unread"],
        "skimmed": counts["skimmed"],
        "careful": counts["careful"],
        "coverage_ratio": round(coverage_ratio, 3),
        "careful_ratio": round(careful_ratio, 3),
        "note_count": note_total,
        "highlight_count": highlight_total,
        "total_visible_ms": visible_ms_total,
        "visit_count": visit_total,
        "read_status": read_status,
        "thresholds": {"skimmed_ms": READING_SKIMMED_MS, "careful_ms": READING_CAREFUL_MS},
    }


def enrich_reading_progress(paper_dir: Path, progress: dict[str, Any]) -> dict[str, Any]:
    counts = annotation_counts_by_segment(paper_dir)
    segments = progress.setdefault("segments", {})
    for segment_id, count in counts.items():
        segments.setdefault(segment_id, clean_progress_segment({}))
    for segment_id, item in list(segments.items()):
        count = counts.get(segment_id, {"highlight_count": 0, "note_count": 0})
        visible_ms = int(item.get("visible_ms") or 0)
        highlight_count = int(count.get("highlight_count") or 0)
        note_count = int(count.get("note_count") or 0)
        segment_state = reading_segment_state(visible_ms, highlight_count, note_count)
        item.update(
            {
                "highlight_count": highlight_count,
                "note_count": note_count,
                "state": segment_state,
                "depth": reading_segment_depth(visible_ms, segment_state, highlight_count, note_count),
            }
        )
    progress["summary"] = summarize_reading_progress(paper_dir, progress)
    return progress


def should_auto_update_read_status(metadata: dict[str, Any], proposed_status: str) -> bool:
    current = str(metadata.get("read_status") or metadata.get("status") or "unread").strip() or "unread"
    proposed = proposed_status if proposed_status in READ_STATUS_RANK else "unread"
    if current == "archived":
        return False
    if current == "read" and proposed != "read":
        return False
    if metadata.get("read_status_source") == "user" and READ_STATUS_RANK.get(proposed, 0) <= READ_STATUS_RANK.get(current, 0):
        return False
    return READ_STATUS_RANK.get(proposed, 0) > READ_STATUS_RANK.get(current, 0) or current not in READ_STATUS_RANK


def update_reading_progress(workspace: Path, paper_id: str, paper_dir: Path, data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    existing = clean_reading_progress(read_json(paper_dir / "reading_progress.json", {"version": 1, "segments": {}}))
    incoming = clean_reading_progress({"segments": data.get("segments", {}) if isinstance(data, dict) else {}})
    for segment_id, incoming_item in incoming.get("segments", {}).items():
        current = existing.setdefault("segments", {}).setdefault(segment_id, clean_progress_segment({}))
        current["visible_ms"] = max(int(current.get("visible_ms") or 0), int(incoming_item.get("visible_ms") or 0))
        current["visits"] = max(int(current.get("visits") or 0), int(incoming_item.get("visits") or 0))
        current["updated_at"] = incoming_item.get("updated_at") or now_iso()
    existing["paper_id"] = paper_id
    existing["updated_at"] = now_iso()
    progress = enrich_reading_progress(paper_dir, existing)
    write_json(paper_dir / "reading_progress.json", progress)
    metadata = read_json(paper_dir / "metadata.json", {})
    summary = progress.get("summary", {})
    proposed_status = str(summary.get("read_status") or "unread")
    if should_auto_update_read_status(metadata, proposed_status):
        metadata["read_status"] = proposed_status
        metadata["status"] = proposed_status
        metadata["read_status_source"] = "auto"
    metadata["reading_progress_summary"] = summary
    metadata["reading_progress_updated_at"] = progress.get("updated_at") or now_iso()
    metadata["updated_at"] = now_iso()
    write_json(paper_dir / "metadata.json", metadata)
    sync_library_from_metadata(workspace, paper_id, paper_dir, metadata, generate_pdf_preview=False)
    return progress, metadata


def ollama_generate(prompt: str, model: str, host: str) -> str:
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    request = urllib.request.Request(
        urllib.parse.urljoin(host.rstrip("/") + "/", "api/generate"),
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "paper-reader-agent/0.1"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310 - local user-configured Ollama endpoint
        data = json.loads(response.read().decode("utf-8"))
    if data.get("error"):
        raise RuntimeError(str(data["error"]))
    return str(data.get("response") or "").strip()


def cloud_llm_enabled() -> bool:
    return bool(kimi_api_key())


def llm_backend_label() -> str:
    if cloud_llm_enabled():
        return f"kimi:{kimi_model()}"
    return env_value("PAPER_READER_TRANSLATION_MODEL", default="qwen2.5:7b-instruct")


def agent_chat(messages: list[dict[str, str]], *, max_tokens: int = 4096, temperature: float = 0.2) -> tuple[str, str]:
    if not kimi_api_key():
        raise RuntimeError("Kimi API key is not configured. Set PAPER_READER_KIMI_API_KEY or MOONSHOT_API_KEY and restart the app.")
    return kimi_chat(messages, max_tokens=max_tokens, temperature=temperature), f"kimi:{kimi_model()}"


def http_error_summary(exc: urllib.error.HTTPError) -> str:
    body = ""
    try:
        body = exc.read().decode("utf-8", errors="replace").strip()
    except Exception:  # noqa: BLE001
        body = ""
    summary = f"HTTP {exc.code} {exc.reason}"
    if body:
        summary += f": {body[:700]}"
    return summary


def kimi_api_key() -> str:
    return env_value("PAPER_READER_KIMI_API_KEY", "MOONSHOT_API_KEY")


def kimi_base_url() -> str:
    return env_value("PAPER_READER_KIMI_BASE_URL", "MOONSHOT_BASE_URL", default="https://api.moonshot.cn/v1")


def kimi_model() -> str:
    return env_value("PAPER_READER_KIMI_MODEL", "MOONSHOT_MODEL", default="kimi-k2.6")


def kimi_request(path: str, *, data: bytes | None = None, headers: dict[str, str] | None = None, method: str | None = None, timeout: int = 240) -> bytes:
    api_key = kimi_api_key()
    if not api_key:
        raise RuntimeError("Kimi API key is not configured. Set PAPER_READER_KIMI_API_KEY or MOONSHOT_API_KEY and restart the app.")
    endpoint = urllib.parse.urljoin(kimi_base_url().rstrip("/") + "/", path.lstrip("/"))
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "paper-reader-agent/0.1",
            **(headers or {}),
        },
        method=method or ("POST" if data is not None else "GET"),
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - user-configured Kimi endpoint
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Kimi API request failed: {exc.code} {exc.reason}: {detail}") from exc


def kimi_upload_file_extract(file_path: Path) -> dict[str, Any]:
    boundary = f"----paper-reader-{uuid.uuid4().hex}"
    filename = file_path.name.encode("utf-8", errors="ignore").decode("utf-8") or "paper.pdf"
    payload = b"".join(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            b'Content-Disposition: form-data; name="purpose"\r\n\r\n',
            b"file-extract\r\n",
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8"),
            b"Content-Type: application/pdf\r\n\r\n",
            file_path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    raw = kimi_request("files", data=payload, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, timeout=300)
    return json.loads(raw.decode("utf-8"))


def kimi_file_content(file_id: str) -> str:
    if not file_id:
        return ""
    raw = kimi_request(f"files/{urllib.parse.quote(file_id, safe='')}/content", method="GET", timeout=300)
    return raw.decode("utf-8", errors="replace")


def kimi_delete_file(file_id: str) -> bool:
    if not file_id:
        return False
    try:
        kimi_request(f"files/{urllib.parse.quote(file_id, safe='')}", method="DELETE", timeout=60)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"Kimi file cleanup failed for {file_id}: {exc}", file=sys.stderr)
        return False


def kimi_chat(messages: list[dict[str, str]], *, max_tokens: int = 4096, temperature: float = 0.2) -> str:
    model = kimi_model()
    request_temperature = 0.6 if model == "kimi-k2.6" else temperature
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "stream": False,
            "max_completion_tokens": max_tokens,
            "temperature": request_temperature,
            "thinking": {"type": "disabled"} if model == "kimi-k2.6" else None,
        },
        ensure_ascii=False,
    ).replace(', "thinking": null', "").encode("utf-8")
    raw = kimi_request("chat/completions", data=payload, headers={"Content-Type": "application/json"}, timeout=300)
    data = json.loads(raw.decode("utf-8"))
    choices = data.get("choices") or []
    content = ((choices[0] or {}).get("message") or {}).get("content") if choices else ""
    if not content:
        raise RuntimeError(f"Kimi returned no content: {data}")
    return str(content).strip()


def translation_prompt(text: str) -> str:
    raw = str(text or "")
    table_hint = ""
    if re.search(r"<table[\s>]", raw, flags=re.I) or "\n|" in raw:
        table_hint = """
表格特别要求：
- 保持原表格结构（HTML table 或 Markdown pipe table）和行列顺序。
- 翻译每个自然语言单元格中的英文内容，不要只翻译标题或部分列。
- 保留引用编号、变量名、公式、缩写、N、ID、p-value、模型名和专有术语。
- 如果单元格中中英文混排，只翻译可翻译的英文短语，保留已有中文。
"""
    return f"""你是 HCI/AI 学术论文翻译助手。请将下面英文论文段落翻译成中文。
要求：
1. 保持学术语气，准确、自然。
2. 保留关键术语英文原词，例如 sensemaking, scaffolding, agency, workflow, LLM, prompt, human-AI collaboration。
3. 不要扩写，不要总结，不要解释。
4. 如果原文是标题、表格、引用或公式，保持结构。
5. 只输出译文。
6. 原图由阅读器单独展示。只翻译正文、图注和表格文字，不要复制或生成图片标记，也不要凭空转写图中文字。
{table_hint}

原文：
{raw}
"""


def translate_text_cloud(text: str) -> str:
    clean = str(text or "").strip()
    if not clean:
        return ""
    return kimi_chat(
        [
            {
                "role": "system",
                "content": "你是 HCI/AI 学术论文翻译助手。请准确、自然地将英文论文内容翻译成中文，保持学术语气，保留关键术语英文原词，不扩写、不总结。",
            },
            {"role": "user", "content": translation_prompt(clean)},
        ],
        max_tokens=4096,
        temperature=0.15,
    )


def translate_text_local(text: str) -> str:
    clean = str(text or "").strip()
    if not clean:
        return ""
    model = os.environ.get("PAPER_READER_TRANSLATION_MODEL", "qwen2.5:7b-instruct")
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    return ollama_generate(translation_prompt(clean), model, host)


def translation_config() -> dict[str, Any]:
    selected = env_value("PAPER_READER_TRANSLATION_PROVIDER", default="legacy").strip().lower() or "legacy"
    if selected == "copilot":
        return {
            "auto_start": True,
            "provider": "copilot",
            "model": env_value("PAPER_READER_COPILOT_MODEL", default="gpt-4.1").strip() or "gpt-4.1",
        }
    provider = ("kimi" if cloud_llm_enabled() else "ollama") if selected == "legacy" else selected
    model = kimi_model() if provider == "kimi" else env_value("PAPER_READER_TRANSLATION_MODEL", default="qwen2.5:7b-instruct")
    return {"auto_start": False, "provider": provider, "model": model}


def translation_concurrency() -> int:
    value = env_value("PAPER_READER_TRANSLATION_CONCURRENCY", default="1")
    try:
        limit = int(value)
    except ValueError:
        raise ValueError("PAPER_READER_TRANSLATION_CONCURRENCY must be an integer from 1 to 4.") from None
    if not 1 <= limit <= 4:
        raise ValueError("PAPER_READER_TRANSLATION_CONCURRENCY must be an integer from 1 to 4.")
    return limit


class RetryableTranslationError(RuntimeError):
    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


def translation_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        try:
            deadline = parsedate_to_datetime(value)
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=dt.timezone.utc)
            seconds = deadline.timestamp() - time.time()
        except (TypeError, ValueError, OverflowError):
            return None
    return max(0.0, seconds) if math.isfinite(seconds) else None


def copilot_translation_endpoint(value: str | None = None) -> str:
    value = value or env_value("PAPER_READER_COPILOT_BASE_URL", default="http://127.0.0.1:4141/v1").strip() or "http://127.0.0.1:4141/v1"
    try:
        parsed = urllib.parse.urlsplit(value)
        host = parsed.hostname or ""
        local = host.lower() == "localhost" or ipaddress.ip_address(host).is_loopback
        port = parsed.port
    except ValueError:
        raise ValueError("Copilot translation requires a loopback HTTP(S) base URL.") from None
    if not local or parsed.scheme not in {"http", "https"} or parsed.username or parsed.password or parsed.query or parsed.fragment or "%" in host:
        raise ValueError("Copilot translation requires a loopback HTTP(S) base URL without credentials, query or fragment.")
    # Avoid system proxies and hostname/DNS remapping for local-only requests.
    hostname = "127.0.0.1" if host.lower() == "localhost" else (f"[{host}]" if ":" in host else host)
    netloc = f"{hostname}:{port}" if port is not None else hostname
    path = parsed.path.rstrip("/")
    if not path.endswith("/chat/completions"):
        path += "/chat/completions"
    return urllib.parse.urlunsplit((parsed.scheme, netloc, path, "", ""))


class NoTranslationRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def translate_text_copilot(text: str, model: str, endpoint: str | None = None) -> str:
    endpoint = copilot_translation_endpoint(endpoint)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Translate source paper paragraphs into Chinese faithfully. Preserve Markdown structure and technical terms. Output only the complete translation, without summaries or commentary."},
            {"role": "user", "content": translation_prompt(text)},
        ],
        "max_tokens": 1400,
        "stream": False,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoTranslationRedirect())
    try:
        with opener.open(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in {429, 503}:
            raise RetryableTranslationError(
                f"Local Copilot translation proxy returned HTTP {exc.code}.",
                translation_retry_after(exc.headers.get("Retry-After") if exc.headers else None),
            ) from None
        raise RuntimeError(f"Local Copilot translation proxy returned HTTP {exc.code}.") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RetryableTranslationError("Could not reach the local Copilot translation proxy, or the request timed out.") from None
    except (ValueError, UnicodeError):
        raise RuntimeError("Local Copilot translation proxy returned invalid JSON.") from None
    choices = data.get("choices") if isinstance(data, dict) else None
    choice = choices[0] if isinstance(choices, list) and choices and isinstance(choices[0], dict) else {}
    message = choice.get("message") if isinstance(choice.get("message"), dict) else {}
    content = message.get("content")
    if choice.get("finish_reason") != "stop" or message.get("refusal"):
        raise RuntimeError("Copilot translation was incomplete or refused; no partial translation was saved.")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Copilot translation was empty; no translation was saved.")
    return content


def translate_text(text: str, config: dict[str, Any] | None = None) -> str:
    config = config or translation_config()
    provider = config["provider"]
    if provider == "copilot":
        return translate_text_copilot(text, config["model"], config.get("endpoint"))
    if provider == "kimi":
        return translate_text_cloud(text)
    if provider == "ollama":
        return translate_text_local(text)
    raise ValueError("Unsupported translation provider; choose copilot, kimi, ollama or legacy.")


def appendix_heading_reached(segment: dict[str, Any]) -> bool:
    if segment.get("kind") != "heading":
        return False
    title = extract_heading_text(str(segment.get("markdown") or ""))
    clean = re.sub(r"\s+", " ", title).strip().casefold()
    return bool(re.match(r"^(appendix|appendices|附录)\b", clean))


def strip_translation_images(markdown: str) -> str:
    text = re.sub(r"!\[(?:\\.|[^\]\\])*\]\((?:\\.|[^\\()]|\([^()]*\))*\)", " ", str(markdown or ""))
    return re.sub(r"<img\b[^>]*>", " ", text, flags=re.I)


_MATH_ENVIRONMENTS = (
    r"equation\*?|align\*?|alignat\*?|aligned|alignedat|gather\*?|gathered|"
    r"multline\*?|multlined|eqnarray\*?|split|array|[pbBvV]?matrix\*?|smallmatrix|cases|displaymath"
)
_MATH_ENV_TOKEN = re.compile(r"\\(begin|end)\{([^{}\n]+)\}")
_MATH_OR_CODE = re.compile(
    r"(?P<fence>^ {0,3}(?:`{3,}|~{3,})[^\n]*)"
    r"|(?P<indent>^(?: {4}|\t)[^\n]+)"
    r"|(?P<html><(?P<html_tag>(?i:pre|code))\b[^>]*>)"
    r"|(?P<comment><!--)"
    r"|(?P<code>`+)"
    rf"|(?P<environment>\\begin\{{(?:{_MATH_ENVIRONMENTS})\}})"
    r"|(?P<delimiter>\$\$|\\\[|\\\(|\$)",
    re.M,
)


def _math_escaped(text: str, position: int) -> bool:
    before = position
    while before and text[before - 1] == "\\":
        before -= 1
    return (position - before) % 2 == 1


def _balanced_math(expression: str) -> bool:
    braces = 0
    fences = 0
    environments: list[str] = []
    for match in re.finditer(r"\\(?:begin|end)\{[^{}\n]+\}|\\[A-Za-z]+|\\[\s\S]|[{}$]", expression):
        token = match.group()
        environment = _MATH_ENV_TOKEN.fullmatch(token)
        if environment:
            action, name = environment.groups()
            if action == "begin":
                environments.append(name)
            elif not environments or environments.pop() != name:
                return False
        elif token == "{":
            braces += 1
        elif token == "}":
            braces -= 1
            if braces < 0:
                return False
        elif token == "\\left":
            fences += 1
        elif token == "\\right":
            fences -= 1
            if fences < 0:
                return False
        elif token in {"$", "\\[", "\\]", "\\(", "\\)"}:
            return False
    return braces == 0 and fences == 0 and not environments


def math_spans(markdown: str) -> list[dict[str, Any]]:
    """Return nonoverlapping start/end (exclusive), mode and latex spans, excluding code.

    Only closed, structurally balanced math is recognized. Dollar inline math uses
    tight delimiters except for standalone expressions, and cannot close before a
    digit (e.g. $5 to $10).
    Environment spans retain their wrappers in latex; other spans omit delimiters.
    """
    text = str(markdown or "")
    spans: list[dict[str, Any]] = []
    position = 0
    while match := _MATH_OR_CODE.search(text, position):
        start, position = match.span()
        token = match.group()
        if _math_escaped(text, start):
            continue
        if match.group("fence"):
            marker = re.match(r" {0,3}(`+|~+)", token).group(1)
            closing = re.compile(rf"^ {{0,3}}{re.escape(marker[0])}{{{len(marker)},}}[ \t]*\r?$", re.M).search(text, position)
            position = closing.end() if closing else len(text)
            continue
        if match.group("indent"):
            continue
        if match.group("html") or match.group("comment") or match.group("code"):
            if match.group("html"):
                pattern = rf"</{match.group('html_tag')}\s*>"
            elif match.group("comment"):
                pattern = "-->"
            else:
                pattern = rf"(?<!`){re.escape(token)}(?!`)"
            closing = re.compile(pattern, re.I).search(text, position)
            position = closing.end() if closing else len(text)
            continue
        if match.group("environment"):
            stack: list[str] = []
            closing_end = None
            for environment in _MATH_ENV_TOKEN.finditer(text, start):
                if _math_escaped(text, environment.start()):
                    continue
                action, name = environment.groups()
                if action == "begin":
                    stack.append(name)
                elif not stack or stack.pop() != name:
                    break
                elif not stack:
                    closing_end = environment.end()
                    body = text[position:environment.start()]
                    break
            if closing_end is None:
                break
            position = closing_end
            expression, mode = text[start:position], "display"
        else:
            mode = "display" if token in {"$$", "\\["} else "inline"
            delimiter = {"$$": "$$", "\\[": "\\]", "\\(": "\\)", "$": "$"}[token]
            if token.startswith("$") and (
                (start and text[start - 1] == "$") or text[position:position + 1] == "$"
            ):
                continue
            closing_start = position
            while True:
                closing_start = text.find(delimiter, closing_start)
                if closing_start < 0:
                    break
                closing_end = closing_start + len(delimiter)
                if not _math_escaped(text, closing_start) and not (
                    delimiter.startswith("$") and (
                        text[closing_start - 1:closing_start] == "$" or text[closing_end:closing_end + 1] == "$"
                    )
                ):
                    break
                closing_start += len(delimiter)
            if closing_start < 0:
                if token != "$":
                    break
                continue
            body = expression = text[position:closing_start]
            if mode == "inline" and "\n" in body:
                continue
            if token == "$" and (
                not body.strip() or text[closing_end:closing_end + 1].isdigit()
                or ((body[0].isspace() or body[-1].isspace()) and (text[:start].strip() or text[closing_end:].strip()))
            ):
                continue
            position = closing_end
        if body.strip() and _balanced_math(expression):
            spans.append({"start": start, "end": position, "mode": mode, "latex": expression})
    return spans


def _without_math_spans(text: str, spans: list[dict[str, Any]]) -> str:
    if not spans:
        return text
    masked_chunks: list[str] = []
    position = 0
    for span in spans:
        masked_chunks.extend((text[position:span["start"]], re.sub(r"[^\r\n]", " ", text[span["start"]:span["end"]])))
        position = span["end"]
    masked = "".join((*masked_chunks, text[position:]))
    chunks: list[str] = []
    position = 0
    for span in spans:
        start, end = span["start"], span["end"]
        line_start = text.rfind("\n", 0, start) + 1
        if not re.search(r"[^\s.,;:，。；：]", masked[line_start:start]):
            # A number on the equation's line (or its immediate next line) is a
            # label, not prose. Do not remove separate paragraph/citation numbers.
            suffix = re.match(
                r"[^\S\r\n]*(?:\r?\n[^\S\r\n]*)?"
                r"(?:\\tag\*?\s*\{[^{}\n]+\}|[（(][^\S\r\n]*[A-Za-z]?(?:\d+(?:[.-]\d+)*[A-Za-z]?|[A-Za-z]\.\d+)[^\S\r\n]*[)）])"
                r"[^\S\r\n]*[.,;:，。；：]?[^\S\r\n]*(?=\r?\n|$)",
                text[end:],
            )
            if suffix:
                end += suffix.end()
        chunks.extend((text[position:start], " "))
        position = end
    chunks.append(text[position:])
    return "".join(chunks)


def _math_only(text: str, spans: list[dict[str, Any]]) -> bool:
    return bool(spans) and not re.search(r"[^\s.,;:，。；：]", _without_math_spans(text, spans))


def _math_group_end(text: str, start: int) -> int | None:
    if text[start:start + 1] != "{":
        return None
    depth = 0
    for position in range(start, len(text)):
        if _math_escaped(text, position):
            continue
        if text[position] == "{":
            depth += 1
        elif text[position] == "}":
            depth -= 1
            if depth == 0:
                return position + 1
    return None


def _math_key(expression: str) -> tuple[str, ...]:
    tokens: list[str] = []
    position = 0
    while position < len(expression):
        if expression[position].isspace():
            position += 1
            continue
        command = re.match(r"\\[A-Za-z]+|\\[\s\S]", expression[position:])
        if not command:
            tokens.append(expression[position])
            position += 1
            continue
        token = command.group()
        environment = _MATH_ENV_TOKEN.match(expression, position)
        if environment:
            action, name = environment.groups()
            name = name.removesuffix("*")
            tokens.append(f"\\{action}{{{name}}}")
            position = environment.end()
            continue
        position += len(token)
        if token in {"\\left", "\\right"}:
            position += len(expression[position:]) - len(expression[position:].lstrip())
            if expression[position:position + 1] == ".":
                position += 1
            continue
        group_start = position
        if token == "\\tag" and expression[group_start:group_start + 1] == "*":
            group_start += 1
        while expression[group_start:group_start + 1].isspace():
            group_start += 1
        group_end = _math_group_end(expression, group_start)
        if token in {"\\tag", "\\label"} and group_end is not None:
            position = group_end
            continue
        if token in {"\\text", "\\textrm", "\\textsf", "\\texttt", "\\textnormal", "\\textit", "\\textbf", "\\mbox", "\\operatorname"} and group_end is not None:
            tokens.append(token + expression[group_start:group_end])
            position = group_end
            continue
        tokens.append(token)
    layout_environments = {"equation", "displaymath", "align", "alignat", "aligned", "alignedat", "gather", "gathered", "multline", "multlined", "eqnarray", "split"}
    while len(tokens) > 1:
        outer = _MATH_ENV_TOKEN.fullmatch(tokens[0])
        if not outer or outer.group(1) != "begin" or outer.group(2) not in layout_environments:
            break
        if tokens[-1] != f"\\end{{{outer.group(2)}}}":
            break
        depth = 0
        for token in tokens[:-1]:
            environment = _MATH_ENV_TOKEN.fullmatch(token)
            if environment:
                depth += 1 if environment.group(1) == "begin" else -1
            if depth == 0:
                break
        if depth == 0:
            break
        tokens = tokens[1:-1]
    return tuple(tokens)


def translation_source_for_segment(segment: dict[str, Any]) -> str:
    """Send prose, inline notation and literal code, omitting display equations."""
    text = strip_translation_images(str(segment.get("markdown") or ""))
    if segment.get("kind") == "code":
        return text.strip()
    spans = math_spans(text)
    if _math_only(text, spans):
        return ""
    return _without_math_spans(text, [span for span in spans if span["mode"] == "display"]).strip()


def translation_text_for_segment(segment: dict[str, Any], translation: str | None = None) -> str:
    """Hide duplicate media/math without mutating saved data.

    Explanatory prose keeps inline notation and unmatched display equations,
    including when the source itself is math-only. Explicit code remains literal.
    """
    text = strip_translation_images(str(segment.get("translation") or "") if translation is None else translation)
    if segment.get("kind") == "code":
        return text.strip()
    source = strip_translation_images(str(segment.get("markdown") or ""))
    source_spans, spans = math_spans(source), math_spans(text)
    source_is_math_only, translation_is_math_only = _math_only(source, source_spans), _math_only(text, spans)
    if source_is_math_only and translation_is_math_only:
        return ""
    source_math = {_math_key(span["latex"]) for span in source_spans if source_is_math_only or span["mode"] == "display"}
    if len(spans) == 1 and translation_is_math_only and _math_key(spans[0]["latex"]) in source_math:
        return ""
    duplicates = [span for span in spans if span["mode"] == "display" and _math_key(span["latex"]) in source_math]
    return _without_math_spans(text, duplicates).strip()


def should_translate_segment(segment: dict[str, Any], appendix_started: bool = False) -> bool:
    """Translate all prose, including appendices; omit image/math-only blocks."""
    return bool(translation_source_for_segment(segment))


def translation_segments(paper_dir: Path) -> list[dict[str, Any]]:
    segments = read_json(paper_dir / "segments.json", [], strict=True)
    if not isinstance(segments, list) or any(not isinstance(item, dict) for item in segments):
        raise ValueError("segments.json must contain a list of source segments.")
    ids = [item.get("id") for item in segments if should_translate_segment(item)]
    if any(not isinstance(value, str) or not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("Source segments must have unique, nonempty string IDs.")
    return segments


def has_translation(segment: dict[str, Any]) -> bool:
    return isinstance(segment.get("translation"), str) and bool(translation_text_for_segment(segment))


def translation_counts(segments: list[dict[str, Any]]) -> tuple[int, int]:
    eligible = [item for item in segments if should_translate_segment(item)]
    return sum(has_translation(item) for item in eligible), len(eligible)


def _eligible_force_pending(pending: list[dict[str, Any]], segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible = {item.get("id"): should_translate_segment(item) for item in segments}
    # Keep missing IDs so the existing stale-source check still fails explicitly.
    return [item for item in pending if eligible.get(item.get("id"), True)]


def translation_fingerprint(segments: list[dict[str, Any]]) -> str:
    values = [(item.get("id"), item.get("markdown"), item.get("translation")) for item in segments]
    return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode("utf-8")).hexdigest()


def translation_snapshot(paper_dir: Path, *, job_id: str = "", after: int = -1, segments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Read durable progress/deltas, never initialize a manager or start work."""
    state = read_json(paper_dir / "translation_state.json", {}, strict=True)
    state = state if isinstance(state, dict) else {}
    segments = translation_segments(paper_dir) if segments is None else segments
    completed, total = translation_counts(segments)
    status = str(state.get("status") or ("ready" if total and completed == total else "not_started"))
    if status == "ready" and completed < total:
        status = "not_started"
    live = TRANSLATION_JOBS is not None and TRANSLATION_JOBS.is_live(paper_dir, str(state.get("job_id") or ""))
    if status in {"queued", "processing", "retrying"} and not live:
        status = "interrupted"
    revision = int(state.get("revision") or 0)
    translation = {
        "status": status,
        "completed": completed,
        "total": total,
        "error": str(state.get("error") or ""),
        "backend": str(state.get("backend") or ""),
        "job_id": str(state.get("job_id") or ""),
        "revision": revision,
        "retry_at": state.get("retry_at"),
        "retry_attempts": int(state.get("retry_attempts") or 0),
    }
    full = not job_id or job_id != translation["job_id"] or after < 0 or after > revision
    full = full or state.get("fingerprint") != translation_fingerprint(segments)
    changes = state.get("segment_revisions") or {}
    updates = []
    for segment in segments:
        if not has_translation(segment):
            continue
        change = changes.get(segment.get("id"), {})
        if full or (int(change.get("revision") or 0) > after and change.get("markdown") == segment.get("markdown")):
            updates.append({key: segment.get(key, "") for key in ("id", "markdown", "translation")})
    return {"translation": translation, "updates": updates}


class TranslationJobManager:
    """Bounded workers share paragraph claims and a global retry cooldown."""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.pending: queue.Queue[tuple[Path, str] | None] = queue.Queue()
        self.jobs: dict[Path, str] = {}
        self.claims: dict[tuple[Path, str], set[str]] = {}
        self.concurrency = translation_concurrency()
        self.threads: list[threading.Thread] = []
        self.thread: threading.Thread | None = None
        self.stopped = False
        self.stop_event = threading.Event()
        self.retry_until = 0.0

    def is_live(self, paper_dir: Path, job_id: str) -> bool:
        with self.lock:
            return not self.stopped and bool(job_id) and self.jobs.get(paper_dir.resolve()) == job_id

    def close(self) -> None:
        with self.lock:
            self.stopped = True
            self.stop_event.set()
            for _ in self.threads:
                self.pending.put(None)
        for thread in self.threads:
            thread.join(timeout=5)

    def queue_snapshot(self, workspace: Path) -> dict[str, Any]:
        with self.lock:
            jobs = []
            for paper_dir in self.jobs:
                if not paper_dir.is_relative_to(workspace.resolve()) or not paper_dir.is_dir():
                    continue
                state = read_json(paper_dir / "translation_state.json", {}, strict=True)
                metadata = read_json(paper_dir / "metadata.json", {}, strict=True)
                jobs.append({
                    **{key: state.get(key) for key in (
                        "paper_id", "status", "completed", "total", "error", "backend",
                        "job_id", "revision", "retry_at", "retry_attempts",
                    )},
                    "paper_id": metadata.get("id") or state.get("paper_id"),
                    "title": metadata.get("title") or state.get("paper_id"),
                    "active_requests": sum(len(ids) for (path, _), ids in self.claims.items() if path == paper_dir),
                })
            return {
                "ok": True, "concurrency": self.concurrency,
                "active_requests": sum(len(ids) for ids in self.claims.values()),
                "retry_at": self.retry_until if self.retry_until > time.time() else None,
                "jobs": jobs,
            }

    def _save(self, paper_dir: Path, state: dict[str, Any], segments: list[dict[str, Any]]) -> None:
        if not paper_dir.is_dir():
            raise FileNotFoundError("Paper was removed while translation was running.")
        state["completed"], state["total"] = translation_counts(segments)
        state["revision"] = int(state.get("revision") or 0) + 1
        state["fingerprint"] = translation_fingerprint(segments)
        state["updated_at"] = now_iso()
        write_json(paper_dir / "translation_state.json", state)

    def submit(self, paper_id: str, paper_dir: Path, data: dict[str, Any]) -> dict[str, Any]:
        action = str(data.get("action") or "start")
        if action not in {"start", "pause", "resume"}:
            raise ValueError("Translation action must be start, pause or resume.")
        automatic = bool(data.get("automatic"))
        config = translation_config()
        paper_dir = paper_dir.resolve()
        with self.lock:
            if self.stopped:
                raise RuntimeError("Translation worker has stopped.")
            state = read_json(paper_dir / "translation_state.json", {}, strict=True)
            if not isinstance(state, dict):
                raise ValueError("translation_state.json must contain an object.")
            segments = translation_segments(paper_dir)
            if action == "pause":
                state.setdefault("version", 1)
                state.setdefault("job_id", uuid.uuid4().hex)
                state.setdefault("paper_id", paper_id)
                state.update({"status": "paused", "error": ""})
                self._save(paper_dir, state, segments)
                self.jobs[paper_dir] = state["job_id"]
                return translation_snapshot(paper_dir)["translation"]
            if automatic and (not config["auto_start"] or state.get("status") in {"paused", "failed"}):
                return translation_snapshot(paper_dir)["translation"]
            if self.is_live(paper_dir, str(state.get("job_id") or "")) and state.get("status") in {"queued", "processing", "retrying"}:
                return translation_snapshot(paper_dir)["translation"]
            completed, total = translation_counts(segments)
            if (
                state.get("status") in {"ready", "waiting_for_source"}
                and state.get("fingerprint") == translation_fingerprint(segments)
                and completed == total
                and (automatic or not data.get("force"))
            ):
                return translation_snapshot(paper_dir)["translation"]
            if config["provider"] == "copilot":
                config["endpoint"] = copilot_translation_endpoint()
            elif config["provider"] not in {"kimi", "ollama"}:
                raise ValueError("Unsupported translation provider; choose copilot, kimi, ollama or legacy.")
            force_pending = []
            if bool(data.get("force")) and not automatic:
                force_pending = [
                    {"id": item["id"], "markdown": item.get("markdown"), "translation": item.get("translation")}
                    for item in segments if should_translate_segment(item)
                ]
            elif action == "resume" and not automatic:
                force_pending = _eligible_force_pending(state.get("force_pending") or [], segments)
            state = {
                "version": 1, "paper_id": paper_id, "job_id": uuid.uuid4().hex,
                "status": "queued" if completed < total or force_pending else ("ready" if segments else "waiting_for_source"),
                "error": "" if segments else "Parse PDF to Markdown before translating.",
                "backend": f"{config['provider']}:{config['model']}", "config": config,
                "automatic": automatic, "revision": 0, "segment_revisions": {}, "force_pending": force_pending,
            }
            self._save(paper_dir, state, segments)
            self.jobs[paper_dir] = state["job_id"]
            if state["status"] == "queued":
                for _ in range(self.concurrency):
                    self.pending.put((paper_dir, state["job_id"]))
                if not self.threads:
                    for index in range(self.concurrency):
                        thread = threading.Thread(target=self._run, name=f"paper-reader-translation-{index + 1}", daemon=True)
                        self.threads.append(thread)
                        thread.start()
                    self.thread = self.threads[0]
            return translation_snapshot(paper_dir)["translation"]

    def _run(self) -> None:
        while True:
            work = self.pending.get()
            if work is None:
                return
            paper_dir, job_id = work
            while not self.stopped:
                with self.lock:
                    delay = self.retry_until - time.time()
                if delay <= 0 or self.stop_event.wait(min(delay, 60.0)):
                    break
            if self.stopped:
                return
            again = False
            try:
                again = self._step(paper_dir, job_id)
            except Exception as exc:  # noqa: BLE001 - fail only this persisted job
                again = self._record_failure(paper_dir, job_id, exc)
            finally:
                with self.lock:
                    if self.jobs.get(paper_dir) == job_id:
                        if not paper_dir.is_dir():
                            self.jobs.pop(paper_dir, None)
                        elif again and not self.stopped:
                            self.pending.put(work)

    def _record_failure(self, paper_dir: Path, job_id: str, exc: Exception) -> bool:
        with self.lock:
            if not paper_dir.is_dir():
                return False
            try:
                state = read_json(paper_dir / "translation_state.json", {}, strict=True)
                if state.get("job_id") != job_id or state.get("status") not in {"queued", "processing", "retrying"}:
                    return False
                again = False
                if isinstance(exc, RetryableTranslationError):
                    attempts = int(state.get("retry_attempts") or 0) + 1
                    delay = exc.retry_after if exc.retry_after is not None else min(30.0, 2.0 ** attempts)
                    self.retry_until = max(self.retry_until, time.time() + delay)
                    again = attempts <= 3
                    state.update({
                        "status": "retrying" if again else "failed",
                        "error": str(exc)[:400] + (f" Retrying ({attempts}/3)." if again else " Automatic retries exhausted; retry manually."),
                        "retry_at": self.retry_until, "retry_attempts": attempts,
                    })
                else:
                    state.update({"status": "failed", "error": str(exc)[:500]})
                self._save(paper_dir, state, translation_segments(paper_dir))
                return again
            except Exception:
                traceback.print_exc(file=sys.stderr)
                return False

    def _step(self, paper_dir: Path, job_id: str) -> bool:
        with self.lock:
            state = read_json(paper_dir / "translation_state.json", {}, strict=True)
            if self.stopped or state.get("job_id") != job_id or state.get("status") not in {"queued", "processing", "retrying"}:
                return False
            if self.retry_until > time.time():
                return True
            segments = translation_segments(paper_dir)
            claimed = self.claims.get((paper_dir, job_id), set())
            force_pending = state.get("force_pending") or []
            eligible_pending = _eligible_force_pending(force_pending, segments)
            if eligible_pending != force_pending:
                state["force_pending"] = force_pending = eligible_pending
                self._save(paper_dir, state, segments)
            if force_pending:
                expected = next((item for item in force_pending if item["id"] not in claimed), None)
                if expected is None:
                    return False
                source = next((item for item in segments if item.get("id") == expected["id"]), None)
                if source is None or any(source.get(key) != expected.get(key) for key in ("markdown", "translation")):
                    raise RuntimeError("Source or translation changed after forced translation was requested; nothing was overwritten.")
            else:
                source = next((item for item in segments if item.get("id") not in claimed and should_translate_segment(item) and not has_translation(item)), None)
            if source is None:
                if claimed:
                    return False
                state.update({"status": "ready", "error": ""})
                self._save(paper_dir, state, segments)
                return False
            source = dict(source)
            if state["status"] != "processing":
                state.update({"status": "processing", "error": "", "retry_at": None})
                self._save(paper_dir, state, segments)
            config = dict(state["config"])
            self.claims.setdefault((paper_dir, job_id), set()).add(source["id"])
        try:
            result = translate_text(translation_source_for_segment(source), config)
            if not isinstance(result, str) or not result.strip():
                raise RuntimeError("Translation was empty; no translation was saved.")
            result = translation_text_for_segment(source, result)
            if not result.strip():
                raise RuntimeError("Translation contained only images or repeated equations, not translated text; no translation was saved.")
            with self.lock:
                state = read_json(paper_dir / "translation_state.json", {}, strict=True)
                if self.stopped or state.get("job_id") != job_id or state.get("status") not in {"queued", "processing", "retrying", "failed"}:
                    return False
                # Merge under the shared file lock, never over a stale segment list.
                with write_lock_for(paper_dir / "segments.json"):
                    latest = translation_segments(paper_dir)
                    target = next((item for item in latest if item.get("id") == source["id"]), None)
                    if target is None or target.get("markdown") != source.get("markdown"):
                        raise RuntimeError("Source changed while translating; the stale result was not saved.")
                    if target.get("translation") != source.get("translation"):
                        raise RuntimeError("Translation was edited while a request was running; the result was not saved.")
                    target["translation"] = result
                    write_json(paper_dir / "segments.json", latest)
                if state.get("force_pending"):
                    state["force_pending"] = [item for item in state["force_pending"] if item["id"] != source["id"]]
                next_revision = int(state.get("revision") or 0) + 1
                state.setdefault("segment_revisions", {})[source["id"]] = {"revision": next_revision, "markdown": source.get("markdown")}
                if state["status"] != "failed" and not state.get("force_pending") and translation_counts(latest)[0] == translation_counts(latest)[1]:
                    state.update({"status": "ready", "error": "", "retry_at": None})
                self._save(paper_dir, state, latest)
                return state["status"] not in {"ready", "failed"}
        except Exception as exc:
            return self._record_failure(paper_dir, job_id, exc)
        finally:
            with self.lock:
                claimed = self.claims.get((paper_dir, job_id), set())
                claimed.discard(source["id"])
                if not claimed:
                    self.claims.pop((paper_dir, job_id), None)


def translation_job_manager() -> TranslationJobManager:
    global TRANSLATION_JOBS
    with TRANSLATION_JOBS_GUARD:
        if TRANSLATION_JOBS is None:
            TRANSLATION_JOBS = TranslationJobManager()
        return TRANSLATION_JOBS


def resume_translation_waiting_for_source(paper_id: str, paper_dir: Path) -> None:
    state = read_json(paper_dir / "translation_state.json", {})
    if isinstance(state, dict) and state.get("status") == "waiting_for_source":
        translation_job_manager().submit(paper_id, paper_dir, {"automatic": bool(state.get("automatic"))})


def translate_paper_full(workspace: Path, paper_id: str, paper_dir: Path, force: bool = False) -> dict[str, Any]:
    """Synchronous compatibility wrapper; HTTP uses the nonblocking job API."""
    status = translation_job_manager().submit(paper_id, paper_dir, {"force": force})
    while status["status"] in {"queued", "processing", "retrying"}:
        time.sleep(0.05)
        status = translation_snapshot(paper_dir)["translation"]
    if status["status"] != "ready":
        raise RuntimeError(status["error"] or f"Translation is {status['status']}.")
    metadata = read_json(paper_dir / "metadata.json", {})
    return {**metadata, "translation_status": status["status"], "translation_error": status["error"], "translation_backend": status["backend"]}


def multipart_boundary(content_type: str) -> bytes:
    match = re.search(r"boundary=(?:\"([^\"]+)\"|([^;]+))", content_type or "", flags=re.I)
    if not match:
        raise ValueError("Missing multipart boundary")
    return (match.group(1) or match.group(2)).strip().encode("utf-8")


def parse_multipart_files(content_type: str, body: bytes, field_name: str = "files") -> list[tuple[str, bytes]]:
    boundary = multipart_boundary(content_type)
    files: list[tuple[str, bytes]] = []
    for raw_part in body.split(b"--" + boundary):
        part = raw_part.strip(b"\r\n")
        if not part or part == b"--" or b"\r\n\r\n" not in part:
            continue
        header_blob, content = part.split(b"\r\n\r\n", 1)
        header_text = header_blob.decode("utf-8", errors="replace")
        disposition = next((line for line in header_text.split("\r\n") if line.lower().startswith("content-disposition:")), "")
        if f'name="{field_name}"' not in disposition:
            continue
        filename_match = re.search(r'filename="([^"]+)"', disposition)
        if not filename_match:
            continue
        filename = Path(filename_match.group(1).replace("\\", "/")).name
        if not filename.lower().endswith(".pdf"):
            continue
        files.append((filename, content.rstrip(b"\r\n")))
    return files


def parse_multipart_form(content_type: str, body: bytes) -> tuple[dict[str, str], list[tuple[str, bytes]]]:
    boundary = multipart_boundary(content_type)
    fields: dict[str, str] = {}
    files: list[tuple[str, bytes]] = []
    for raw_part in body.split(b"--" + boundary):
        part = raw_part.strip(b"\r\n")
        if not part or part == b"--" or b"\r\n\r\n" not in part:
            continue
        header_blob, content = part.split(b"\r\n\r\n", 1)
        header_text = header_blob.decode("utf-8", errors="replace")
        disposition = next((line for line in header_text.split("\r\n") if line.lower().startswith("content-disposition:")), "")
        name_match = re.search(r'name="([^"]+)"', disposition)
        if not name_match:
            continue
        name = name_match.group(1)
        filename_match = re.search(r'filename="([^"]+)"', disposition)
        clean_content = content.rstrip(b"\r\n")
        if filename_match:
            filename = Path(filename_match.group(1).replace("\\", "/")).name or "paper.pdf"
            if filename.lower().endswith(".pdf"):
                files.append((filename, clean_content))
        else:
            fields[name] = clean_content.decode("utf-8", errors="replace")
    return fields, files


def paper_candidates_dir(workspace: Path) -> Path:
    path = workspace / "paper_candidates"
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_candidate_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(value or "")).strip("-")[:120]


def candidate_dir(workspace: Path, candidate_id: str) -> Path:
    safe_id = safe_candidate_id(candidate_id)
    if not safe_id:
        raise ValueError("candidate_id is required")
    path = (paper_candidates_dir(workspace) / safe_id).resolve()
    path.relative_to(paper_candidates_dir(workspace).resolve())
    return path


def default_chrome_paper_brief_prompt() -> str:
    return EXPLANATION_PROMPT.strip()


def chrome_brief_prompt(workspace: Path, override: str = "") -> str:
    if override.strip():
        return override.strip()
    prompt_path = workspace / "prompts" / "chrome_paper_brief_prompt.md"
    if prompt_path.exists():
        text = prompt_path.read_text(encoding="utf-8").strip()
        if text:
            return text
    return default_chrome_paper_brief_prompt()


def clean_paper_brief_title(value: Any) -> str:
    title = html.unescape(str(value or "")).strip()
    title = re.sub(r"^\s{0,3}#{1,6}\s*", "", title).strip()
    title = re.sub(r"^[-*]\s+", "", title).strip()
    title = re.sub(r"^\*\*(.+)\*\*$", r"\1", title).strip()
    title = re.sub(r"^(?:Title|Paper Title|论文标题|题名|标题)\s*[:：\-]\s*", "", title, flags=re.I).strip()
    title = title.strip(" \t\r\n\"'`*_[]()（）【】")
    title = re.sub(r":(?=[A-Z])", ": ", title)
    title = re.sub(r"\s+", " ", title).strip()
    if not title:
        return ""
    lowered = title.casefold()
    if any(marker in lowered for marker in {"原文未明确", "not specified", "not provided", "unknown", "n/a"}):
        return ""
    if re.fullmatch(r"(?:doi\s*[:：]?\s*)?10\.\d{4,9}/\S+", title, flags=re.I):
        return ""
    if re.fullmatch(r"\d{4}\.\d{4,5}(?:v\d+)?", title, flags=re.I):
        return ""
    if re.fullmatch(r"[\d._\-/]+", title):
        return ""
    return title if title_key_is_usable(normalize_title_key(title)) else ""


def extract_title_from_paper_brief(brief: str) -> str:
    for line in str(brief or "").replace("\r\n", "\n").split("\n")[:80]:
        text = line.strip()
        if not text or text.startswith("```"):
            continue
        labelled = re.match(r"^\s{0,3}#{0,6}\s*(?:[-*]\s*)?(?:\*\*)?(?:Title|Paper Title|论文标题|题名|标题)(?:\*\*)?\s*[:：\-]\s*(.+)$", text, flags=re.I)
        if labelled:
            title = clean_paper_brief_title(labelled.group(1))
            if title:
                return title
    return ""


def unwrap_kimi_extract_prefix(text: str) -> str:
    raw_text = str(text or "")
    stripped = raw_text.lstrip()
    if not stripped.startswith("{"):
        return raw_text
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict) and isinstance(parsed.get("content"), str):
            return parsed["content"]
    except json.JSONDecodeError:
        pass
    match = re.search(r'"content"\s*:\s*"', stripped)
    if not match:
        return raw_text
    escaped = stripped[match.end():]
    chars: list[str] = []
    escaping = False
    for char in escaped:
        if escaping:
            chars.append(char)
            escaping = False
            continue
        if char == "\\":
            chars.append(char)
            escaping = True
            continue
        if char == '"':
            break
        chars.append(char)
    chunk = "".join(chars)
    for trim in range(0, min(len(chunk), 32) + 1):
        candidate = chunk[:len(chunk) - trim] if trim else chunk
        try:
            return json.loads(f'"{candidate}"')
        except json.JSONDecodeError:
            continue
    return chunk.replace("\\n", "\n")


def extract_title_from_pdf_extract(text: str) -> str:
    raw_text = unwrap_kimi_extract_prefix(text)
    for line in raw_text.replace("\r\n", "\n").split("\n")[:120]:
        clean_line = re.sub(r"<[^>]+>", "", line).strip()
        if not clean_line:
            continue
        line_key = normalize_title_key(clean_line)
        if re.search(r"\barxiv\b|permission to reproduce|proper attribution", clean_line, flags=re.I):
            continue
        if line_key in {"abstract", "author", "authors", "introduction"}:
            break
        heading = re.match(r"^\s{0,3}#{1,3}\s+(.+)$", clean_line)
        if heading:
            title = clean_paper_brief_title(heading.group(1))
            if title:
                return title
    return ""


def candidate_title_should_update(candidate: dict[str, Any], title: str) -> bool:
    if not title:
        return False
    if str(candidate.get("title_source") or "").strip() == "user":
        return False
    current = str(candidate.get("title") or "").strip()
    if not current:
        return True
    if normalize_title_key(current) == normalize_title_key(title):
        return False
    return str(candidate.get("title_source") or "").strip() in {"", "filename", "candidate", "paper_brief", "pdf_extract"}


def apply_candidate_title(candidate: dict[str, Any], title: str, source: str) -> dict[str, Any]:
    if not title:
        return candidate
    if source == "paper_brief":
        candidate["paper_brief_title"] = title
    if source == "pdf_extract":
        candidate["pdf_extract_title"] = title
    if candidate_title_should_update(candidate, title):
        candidate["title"] = title
        candidate["title_source"] = source
        candidate["title_key"] = normalize_title_key(title)
    return candidate


def metadata_title_should_update(metadata: dict[str, Any], title: str, source: str) -> bool:
    if not title:
        return False
    if metadata.get("title_locked") or str(metadata.get("title_source") or "").strip() in {"user", "feishu"}:
        return False
    current = str(metadata.get("title") or "").strip()
    if not current:
        return True
    if normalize_title_key(current) == normalize_title_key(title):
        return False
    current_source = str(metadata.get("title_source") or "").strip()
    if source == "pdf_extract" and current_source == "paper_brief":
        return False
    replaceable_sources = {"", "filename", "library", "reference", "candidate", "pdf_extract"}
    if source == "paper_brief":
        replaceable_sources.add("paper_brief")
    return current_source in replaceable_sources or should_replace_title(metadata, title)


def apply_paper_brief_title_to_metadata(metadata: dict[str, Any], brief: str, extract_text: str = "") -> dict[str, Any]:
    title = extract_title_from_paper_brief(brief)
    source = "paper_brief" if title else "pdf_extract"
    if not title:
        title = extract_title_from_pdf_extract(extract_text)
    if not title:
        return metadata
    if source == "paper_brief":
        metadata["paper_brief_title"] = title
    else:
        metadata["pdf_extract_title"] = title
    if metadata_title_should_update(metadata, title, source):
        metadata["title"] = title
        metadata["title_source"] = source
        metadata["title_key"] = normalize_title_key(title)
    return metadata


def apply_paper_brief_title_to_candidate(candidate: dict[str, Any], brief: str, extract_text: str = "") -> dict[str, Any]:
    title = extract_title_from_paper_brief(brief)
    if title:
        return apply_candidate_title(candidate, title, "paper_brief")
    return apply_candidate_title(candidate, extract_title_from_pdf_extract(extract_text), "pdf_extract")


def read_text_prefix(path: Path, limit: int = 12000) -> str:
    if not path.exists():
        return ""
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        return handle.read(limit)


def read_candidate(workspace: Path, candidate_id: str) -> dict[str, Any]:
    path = candidate_dir(workspace, candidate_id) / "candidate.json"
    if not path.exists():
        raise FileNotFoundError(candidate_id)
    candidate = read_json(path, {})
    candidate.setdefault("id", safe_candidate_id(candidate_id))
    brief = (candidate_dir(workspace, candidate_id) / "paper_brief.md").read_text(encoding="utf-8") if (candidate_dir(workspace, candidate_id) / "paper_brief.md").exists() else ""
    candidate.setdefault("paper_brief", brief)
    extract_text = read_text_prefix(candidate_dir(workspace, candidate_id) / "kimi_extract.txt")
    apply_paper_brief_title_to_candidate(candidate, brief, extract_text)
    candidate.setdefault("annotations", read_json(candidate_dir(workspace, candidate_id) / "annotations.json", {"annotations": []}).get("annotations", []))
    return candidate


def write_candidate(workspace: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    candidate_id = safe_candidate_id(str(candidate.get("id") or ""))
    if not candidate_id:
        raise ValueError("candidate id is required")
    path = candidate_dir(workspace, candidate_id)
    path.mkdir(parents=True, exist_ok=True)
    candidate["id"] = candidate_id
    candidate["updated_at"] = now_iso()
    write_json(path / "candidate.json", candidate)
    return candidate


def list_candidates(workspace: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for item in paper_candidates_dir(workspace).iterdir():
        if item.is_dir() and (item / "candidate.json").exists():
            try:
                candidates.append(read_candidate(workspace, item.name))
            except Exception:  # noqa: BLE001
                continue
    candidates.sort(key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
    return candidates


def clean_candidate_annotations(value: Any) -> dict[str, list[dict[str, Any]]]:
    now = now_iso()
    raw_items = value.get("annotations", value) if isinstance(value, dict) else value
    items = raw_items if isinstance(raw_items, list) else []
    cleaned: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        quote = str(item.get("quote") or "")
        note = str(item.get("note") or "")
        if not quote.strip() and not note.strip():
            continue
        tags = item.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        cleaned.append(
            {
                "id": str(item.get("id") or f"cand-ann-{hashlib.sha1((quote + note + str(index) + now).encode('utf-8')).hexdigest()[:12]}"),
                "target": "thinking",
                "block_id": PAPER_BRIEF_BLOCK_ID,
                "type": str(item.get("type") or "range"),
                "color": str(item.get("color") or "yellow"),
                "quote": quote,
                "note": note,
                "tags": [str(tag).strip() for tag in tags if str(tag).strip()] if isinstance(tags, list) else [],
                "created_at": str(item.get("created_at") or now),
                "updated_at": str(item.get("updated_at") or now),
            }
        )
    return {"annotations": cleaned}


def normalize_importance_level(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    match = re.search(r"[0-3]", raw)
    if not match:
        return ""
    level = max(0, min(3, int(match.group(0))))
    return str(level) if level else ""


def importance_fields(level: Any) -> dict[str, Any]:
    clean_level = normalize_importance_level(level)
    return {"importance": clean_level, "importance_tags": [clean_level] if clean_level else []}


def pdf_filename_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(str(url or ""))
    name = Path(urllib.parse.unquote(parsed.path or "paper.pdf")).name or "paper.pdf"
    if not name.lower().endswith(".pdf"):
        name = f"{slugify(name, 'paper')}.pdf"
    return name


def pdf_bytes_are_recognizable(content: bytes) -> bool:
    return bool(content) and b"%PDF" in content[:1024]


def download_pdf_bytes(url: str, extra_headers: dict[str, str] | None = None) -> tuple[str, bytes]:
    parsed = urllib.parse.urlparse(str(url or ""))
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("pdf_url must start with http:// or https://")
    headers = {
        "User-Agent": "Mozilla/5.0 paper-reader-agent/0.1",
        "Accept": "application/pdf,*/*",
    }
    for key, value in (extra_headers or {}).items():
        clean_key = str(key or "").strip()
        clean_value = str(value or "").strip()
        if clean_key and clean_value:
            headers[clean_key] = clean_value
    request = urllib.request.Request(
        url,
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - user-triggered PDF URL import
        content = response.read()
        content_type = response.headers.get("Content-Type", "")
    if not content:
        raise ValueError("Downloaded PDF is empty")
    if not pdf_bytes_are_recognizable(content):
        raise ValueError("URL did not return a recognizable PDF; try manual upload from the extension")
    return pdf_filename_from_url(url), content


def browser_pdf_request_headers(data: dict[str, Any], pdf_url: str) -> dict[str, str]:
    headers: dict[str, str] = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8",
        "Accept-Language": str(data.get("browser_accept_language") or "en-US,en;q=0.9"),
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }
    cookie_header = str(data.get("browser_cookie_header") or "").strip()
    if cookie_header:
        headers["Cookie"] = cookie_header
    user_agent = str(data.get("browser_user_agent") or "").strip()
    if user_agent:
        headers["User-Agent"] = user_agent
    referer = str(data.get("source_page_url") or pdf_url or "").strip()
    if referer:
        headers["Referer"] = referer
    return headers


def candidate_summary(candidate: dict[str, Any], workspace: Path) -> dict[str, Any]:
    candidate_id = str(candidate.get("id") or "")
    path = candidate_dir(workspace, candidate_id)
    brief_path = path / "paper_brief.md"
    annotations_path = path / "annotations.json"
    result = {**candidate}
    result["paper_brief"] = brief_path.read_text(encoding="utf-8") if brief_path.exists() else ""
    result["annotations"] = read_json(annotations_path, {"annotations": []}).get("annotations", []) if annotations_path.exists() else []
    return result


def generate_candidate_brief(workspace: Path, *, pdf_bytes: bytes, filename: str, source_url: str = "", source_page_url: str = "", prompt_override: str = "", force: bool = False) -> dict[str, Any]:
    ensure_workspace(workspace)
    if not pdf_bytes:
        raise ValueError("PDF content is required")
    if not pdf_bytes_are_recognizable(pdf_bytes):
        raise ValueError("Uploaded content is not a recognizable PDF. The browser may have captured a PDF viewer HTML shell; use the browser download button or Upload PDF with the saved file.")
    digest = hashlib.sha256(pdf_bytes).hexdigest()
    base_name = Path(filename or pdf_filename_from_url(source_url) or "paper.pdf").stem
    candidate_id = safe_candidate_id(f"candidate-{slugify(base_name, 'paper')}-{digest[:12]}")
    path = candidate_dir(workspace, candidate_id)
    path.mkdir(parents=True, exist_ok=True)
    pdf_path = path / "original.pdf"
    brief_path = path / "paper_brief.md"
    extract_path = path / "kimi_extract.txt"
    annotations_path = path / "annotations.json"
    if not force and (path / "candidate.json").exists() and brief_path.exists():
        return candidate_summary(read_candidate(workspace, candidate_id), workspace)
    pdf_path.write_bytes(pdf_bytes)
    prompt = chrome_brief_prompt(workspace, prompt_override)
    candidate = read_json(path / "candidate.json", {}) if (path / "candidate.json").exists() else {}
    now = now_iso()
    candidate.update(
        {
            "id": candidate_id,
            "title": candidate.get("title") or Path(filename or base_name).stem,
            "source_url": source_url,
            "source_page_url": source_page_url,
            "source_domain": urllib.parse.urlparse(source_url or source_page_url).netloc,
            "source_pdf_name": filename or "paper.pdf",
            "original_pdf": "original.pdf",
            "pdf_sha256": digest,
            "brief_status": "generating",
            "brief_prompt_id": DEFAULT_CHROME_BRIEF_PROMPT_ID,
            "brief_prompt": prompt,
            "brief_model": kimi_model(),
            "decision": candidate.get("decision") or "undecided",
            "tags": candidate.get("tags", []),
            "project": candidate.get("project", ""),
            "read_status": candidate.get("read_status", "unread"),
            **importance_fields(candidate.get("importance", "")),
            "created_at": candidate.get("created_at") or now,
            "updated_at": now,
        }
    )
    write_candidate(workspace, candidate)
    file_id = ""
    try:
        file_object = kimi_upload_file_extract(pdf_path)
        file_id = str(file_object.get("id") or "")
        extracted_text = kimi_file_content(file_id)
        if not extracted_text.strip():
            raise RuntimeError("Kimi returned empty extracted text")
        write_text_atomic(extract_path, extracted_text)
        apply_paper_brief_title_to_candidate(candidate, "", extracted_text)
        messages = [
            {"role": "system", "content": extracted_text[:180000]},
            {"role": "user", "content": prompt},
        ]
        brief = kimi_chat(messages, max_tokens=7000, temperature=0.2).rstrip() + "\n"
        write_text_atomic(brief_path, brief)
        if not annotations_path.exists():
            write_json(annotations_path, {"annotations": []})
        apply_paper_brief_title_to_candidate(candidate, brief)
        candidate.update(
            {
                "brief_status": "ready",
                "kimi_file_id": file_id,
                "kimi_file_deleted": kimi_delete_file(file_id) if env_value("PAPER_READER_KIMI_DELETE_FILES", default="1").strip().lower() not in {"0", "false", "no"} else False,
                "kimi_extract_path": "kimi_extract.txt",
                "paper_brief_path": "paper_brief.md",
                "updated_at": now_iso(),
                "brief_error": "",
            }
        )
        write_candidate(workspace, candidate)
    except Exception as exc:  # noqa: BLE001
        candidate.update({"brief_status": "failed", "brief_error": str(exc), "kimi_file_id": file_id, "updated_at": now_iso()})
        write_candidate(workspace, candidate)
        raise
    return candidate_summary(candidate, workspace)


def save_candidate_annotations(workspace: Path, candidate_id: str, value: Any) -> dict[str, Any]:
    path = candidate_dir(workspace, candidate_id)
    if not (path / "candidate.json").exists():
        raise FileNotFoundError(candidate_id)
    annotations = clean_candidate_annotations(value)
    write_json(path / "annotations.json", annotations)
    candidate = read_json(path / "candidate.json", {})
    candidate["updated_at"] = now_iso()
    write_candidate(workspace, candidate)
    sync_candidate_annotations_to_library(workspace, candidate_id)
    return annotations


def sync_candidate_annotations_to_library(workspace: Path, candidate_id: str) -> int:
    candidate = read_candidate(workspace, candidate_id)
    paper_id = str(candidate.get("saved_paper_id") or "").strip()
    if not paper_id:
        return 0
    record = find_paper_record(workspace, paper_id)
    if not record:
        return 0
    paper_dir = workspace / str(record.get("paper_dir") or "")
    if not paper_dir.exists():
        return 0
    source_annotations = read_json(candidate_dir(workspace, candidate_id) / "annotations.json", {"annotations": []})
    cleaned = clean_candidate_annotations(source_annotations).get("annotations", [])
    thinking = load_thinking(paper_dir)
    thinking["annotations"] = [
        item for item in thinking.get("annotations", []) if not str(item.get("id", "")).startswith(f"{candidate_id}-")
    ]
    for item in cleaned:
        thinking["annotations"].append({**item, "id": f"{candidate_id}-{item['id']}", "block_id": PAPER_BRIEF_BLOCK_ID})
    write_json(paper_dir / "thinking.json", clean_thinking(thinking))
    return len(cleaned)


def sync_candidate_metadata_to_library(workspace: Path, candidate_id: str, data: dict[str, Any]) -> None:
    candidate = read_candidate(workspace, candidate_id)
    paper_id = str(candidate.get("saved_paper_id") or "").strip()
    if not paper_id:
        return
    record = find_paper_record(workspace, paper_id)
    if not record:
        return
    paper_dir = workspace / str(record.get("paper_dir") or "")
    if not paper_dir.exists():
        return
    metadata = read_json(paper_dir / "metadata.json", {})
    if "tags" in data:
        metadata["tags"] = normalize_tag_paths(data.get("tags", candidate.get("tags", [])))
    if "project" in data:
        project = str(data.get("project") or candidate.get("project") or "").strip()
        projects = normalize_project_list([project] if project else metadata_projects(metadata))
        metadata["projects"] = projects
        metadata["project"] = projects[0] if projects else ""
    if "importance" in data:
        metadata.update(importance_fields(data.get("importance", candidate.get("importance", ""))))
    if "read_status" in data:
        metadata["read_status"] = str(data.get("read_status") or candidate.get("read_status") or "unread")
        metadata["status"] = metadata["read_status"]
        metadata["read_status_source"] = "user"
    metadata["updated_at"] = now_iso()
    write_json(paper_dir / "metadata.json", metadata)
    sync_library_from_metadata(workspace, paper_id, paper_dir, metadata)


def update_candidate_metadata(workspace: Path, candidate_id: str, data: dict[str, Any]) -> dict[str, Any]:
    candidate = read_candidate(workspace, candidate_id)
    for key in {"title", "decision", "read_status", "project"}:
        if key in data:
            candidate[key] = str(data.get(key) or "")
            if key == "title":
                candidate["title_source"] = "user"
                candidate["title_key"] = normalize_title_key(candidate[key])
    if "tags" in data:
        candidate["tags"] = normalize_tag_paths(data.get("tags", []))
    if "importance" in data:
        candidate.update(importance_fields(data.get("importance")))
    saved = candidate_summary(write_candidate(workspace, candidate), workspace)
    sync_candidate_metadata_to_library(workspace, candidate_id, data)
    return saved


class PaperProcessingJobManager:
    """One FIFO parser worker; durable requests live with each paper's metadata."""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.pending: queue.Queue[str | None] = queue.Queue()
        self.jobs: dict[str, dict[str, Any]] = {}
        self.thread: threading.Thread | None = None
        self.closed = False
        self.sequence = 0

    def submit(self, workspace: Path, paper_id: str, paper_dir: Path, options: dict[str, Any] | None = None, *,
               mode: str = "deep", refresh_citations: bool = False, refresh_videos: bool = False,
               queued_at: str = "") -> bool:
        if mode not in {"deep", "skim"}:
            raise ValueError("Processing mode must be deep or skim.")
        workspace, paper_dir = workspace.resolve(), paper_dir.resolve()
        key = f"{workspace}::{paper_id}"
        parse_options = {name: value for name, value in (options or {}).items()
                         if name in {"backend", "method", "lang", "start", "end"}}
        if any(value is not None and not isinstance(value, (str, int)) for value in parse_options.values()):
            raise ValueError("Invalid PDF parsing options.")
        with self.lock:
            if self.closed:
                raise RuntimeError("The parsing queue is shutting down. Retry after restarting the reader.")
            existing = self.jobs.get(key)
            if existing and existing["status"] in {"queued", "processing"}:
                if existing["mode"] != mode:
                    raise ValueError("This paper is already processing in another mode. Wait for it to finish.")
                return False
            request = {
                "mode": mode, "options": parse_options,
                "queued_at": queued_at or dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds"),
                "refresh_citations": bool(refresh_citations), "refresh_videos": bool(refresh_videos),
            }
            metadata = save_processing_fields(workspace, paper_id, paper_dir, {
                "processing_mode": mode, "reading_mode": mode, "processing_status": "processing_queued",
                "processing_background": "queued", "processing_error": "", "processing_request": request,
                "processing_started_at": "", "processing_finished_at": "",
            })
            self.sequence += 1
            self.jobs[key] = {
                **request, "workspace": workspace, "paper_dir": paper_dir, "paper_id": paper_id,
                "title": metadata.get("title") or paper_id, "status": "queued", "error": "",
                "started_at": "", "finished_at": "", "sequence": self.sequence,
            }
            self.pending.put(key)
            if self.thread is None:
                self.thread = threading.Thread(target=self._run, name="paper-reader-parser", daemon=True)
                self.thread.start()
        return True

    def restore_finished(self, workspace: Path, paper_id: str, paper_dir: Path, metadata: dict[str, Any]) -> None:
        request = metadata.get("processing_request")
        if not isinstance(request, dict) or metadata.get("processing_status") not in {"ready", "failed"}:
            return
        key = f"{workspace.resolve()}::{paper_id}"
        with self.lock:
            if key in self.jobs:
                return
            self.sequence += 1
            self.jobs[key] = {
                **request, "workspace": workspace.resolve(), "paper_dir": paper_dir.resolve(), "paper_id": paper_id,
                "title": metadata.get("title") or paper_id, "status": metadata["processing_status"],
                "error": metadata.get("processing_error", ""), "started_at": metadata.get("processing_started_at", ""),
                "finished_at": metadata.get("processing_finished_at", ""), "sequence": self.sequence,
            }

    def snapshot(self, workspace: Path) -> dict[str, Any]:
        with self.lock:
            ordered = sorted(self.jobs.values(), key=lambda job: job["sequence"])
            positions = {id(job): index + 1 for index, job in enumerate(job for job in ordered if job["status"] == "queued")}
            jobs = [{
                **{name: job.get(name, "") for name in ("paper_id", "title", "mode", "status", "error", "queued_at", "started_at", "finished_at")},
                "position": positions.get(id(job)),
            } for job in ordered if job["workspace"] == workspace.resolve()]
            return {"ok": True, "concurrency": 1,
                    "active_jobs": sum(job["status"] == "processing" for job in ordered),
                    "queued_count": len(positions), "jobs": jobs}

    def shutdown(self, timeout: float = 5) -> None:
        with self.lock:
            if not self.closed:
                self.closed = True
                self.pending.put(None)
            thread = self.thread
        if thread:
            thread.join(timeout=timeout)
            if thread.is_alive():
                raise RuntimeError("The parsing worker has not finished; queued requests remain saved on disk.")

    def _run(self) -> None:
        while True:
            key = self.pending.get()
            if key is None:
                self.pending.task_done()
                return
            with self.lock:
                job = self.jobs[key]
                job["status"] = "processing"
                job["started_at"] = now_iso()
            workspace, paper_dir, paper_id = job["workspace"], job["paper_dir"], job["paper_id"]
            error = ""
            try:
                save_processing_fields(workspace, paper_id, paper_dir, {
                    "processing_status": "processing", "processing_background": "processing",
                    "processing_started_at": job["started_at"],
                })
                processor = process_paper_skim if job["mode"] == "skim" else process_paper_deep
                metadata = processor(workspace, paper_id, paper_dir, job["options"])
                for requested, enrich, label in (
                    (job["refresh_citations"], refresh_paper_citations, "citation"),
                    (job["refresh_videos"], refresh_paper_videos, "video"),
                ):
                    if requested:
                        try:
                            enrich(workspace, paper_id, paper_dir)
                        except Exception as exc:  # noqa: BLE001
                            print(f"Background {label} lookup failed for {paper_id}: {exc}", file=sys.stderr)
                save_processing_fields(workspace, paper_id, paper_dir, {
                    "processing_background": "done", "processing_finished_at": now_iso(),
                })
                with self.lock:
                    job["title"] = metadata.get("title") or job["title"]
            except Exception as exc:  # noqa: BLE001
                error = str(exc)
                try:
                    save_processing_fields(workspace, paper_id, paper_dir, {
                        "processing_status": "failed", "processing_error": error,
                        "processing_background": "failed", "processing_finished_at": now_iso(),
                    })
                except Exception as save_error:  # noqa: BLE001
                    error += f"; could not persist the failure: {save_error}"
                print(f"Background paper processing failed for {paper_id}: {error}", file=sys.stderr)
            finally:
                with self.lock:
                    job.update(status="failed" if error else "ready", error=error, finished_at=now_iso())
                self.pending.task_done()


def processing_job_manager() -> PaperProcessingJobManager:
    global PROCESSING_JOBS
    with PROCESSING_JOBS_GUARD:
        if PROCESSING_JOBS is None:
            PROCESSING_JOBS = PaperProcessingJobManager()
        return PROCESSING_JOBS


def start_background_paper_processing(workspace: Path, paper_id: str, paper_dir: Path, options: dict[str, Any] | None = None, *, mode: str = "deep", refresh_citations: bool = False, refresh_videos: bool = False) -> bool:
    return processing_job_manager().submit(workspace, paper_id, paper_dir, options, mode=mode,
                                           refresh_citations=refresh_citations, refresh_videos=refresh_videos)


RESUMABLE_PROCESSING_STATUSES = {
    "processing",
    "processing_queued",
    "paper_brief_processing",
    "paper_brief_ready",
}

RESUMABLE_BACKGROUND_STATES = {"queued", "waiting_for_brief"}


def nonempty_segment_count(paper_dir: Path) -> int:
    segments = read_json(paper_dir / "segments.json", []) if (paper_dir / "segments.json").exists() else []
    if not isinstance(segments, list):
        return 0
    return sum(1 for segment in segments if isinstance(segment, dict) and str(segment.get("markdown") or "").strip())


def should_resume_processing(paper_dir: Path, metadata: dict[str, Any]) -> tuple[bool, str]:
    if not (paper_dir / "original.pdf").exists():
        return False, ""
    mode = str(metadata.get("processing_mode") or metadata.get("reading_mode") or "deep").strip().lower()
    status = str(metadata.get("processing_status") or "").strip().lower()
    background = str(metadata.get("processing_background") or "").strip().lower()
    if status in RESUMABLE_PROCESSING_STATUSES:
        return True, mode if mode in {"skim", "deep"} else "deep"
    if status != "ready" and background in RESUMABLE_BACKGROUND_STATES:
        return True, mode if mode in {"skim", "deep"} else "deep"
    if mode == "deep" and status == "ready" and nonempty_segment_count(paper_dir) == 0:
        return True, "deep"
    return False, ""


def resume_interrupted_processing_tasks(workspace: Path) -> list[str]:
    resumed: list[str] = []
    pending = []
    library = load_library_raw(workspace)
    for paper in library.get("papers", []):
        paper_id = str(paper.get("id") or "").strip()
        if not paper_id:
            continue
        paper_dir = workspace / str(paper.get("paper_dir") or f"papers/{paper_id}")
        if not paper_dir.exists():
            continue
        metadata = read_json(paper_dir / "metadata.json", {})
        if not isinstance(metadata, dict):
            metadata = {}
        should_resume, mode = should_resume_processing(paper_dir, metadata)
        if not should_resume:
            if metadata.get("processing_request"):
                processing_job_manager().restore_finished(workspace, paper_id, paper_dir, metadata)
            continue
        request = metadata.get("processing_request") or {}
        pending.append((str(request.get("queued_at") or metadata.get("updated_at") or ""), paper_id, paper_dir, mode, request))
    for queued_at, paper_id, paper_dir, mode, request in sorted(pending, key=lambda item: (item[0], item[1])):
        started = processing_job_manager().submit(
            workspace, paper_id, paper_dir, request.get("options") or {}, mode=mode, queued_at=queued_at,
            refresh_citations=bool(request.get("refresh_citations")), refresh_videos=bool(request.get("refresh_videos")),
        )
        if started:
            resumed.append(paper_id)
    return resumed


def migrate_candidate_to_library(workspace: Path, candidate_id: str, data: dict[str, Any]) -> dict[str, Any]:
    candidate = read_candidate(workspace, candidate_id)
    path = candidate_dir(workspace, candidate_id)
    pdf_path = path / "original.pdf"
    if not pdf_path.exists():
        raise FileNotFoundError("Candidate PDF is missing")
    brief = (path / "paper_brief.md").read_text(encoding="utf-8") if (path / "paper_brief.md").exists() else ""
    extract_text = read_text_prefix(path / "kimi_extract.txt")
    apply_paper_brief_title_to_candidate(candidate, brief, extract_text)
    tags = normalize_tag_paths(data.get("tags", candidate.get("tags", [])))
    duplicate_policy = str(data.get("duplicate_policy") or "ask")
    paper_title = str(data.get("title") or candidate.get("title") or pdf_path.stem)
    result = register_paper_in_library(workspace, pdf_path, title=paper_title, tags=tags, duplicate_policy=duplicate_policy, pdf_digest=str(candidate.get("pdf_sha256") or ""), generate_pdf_preview=False, enrich_citation=False)
    if result.get("duplicate"):
        return {"ok": False, **result}
    paper_id = str(result.get("paper_id") or "")
    record = find_paper_record(workspace, paper_id)
    if not record:
        raise RuntimeError("Saved paper did not appear in Library")
    paper_dir = workspace / str(record.get("paper_dir") or "")
    metadata = read_json(paper_dir / "metadata.json", {})
    project = str(data.get("project") or candidate.get("project") or "").strip()
    projects = normalize_project_list([project] if project else metadata_projects(metadata))
    metadata.update(
        {
            "source_url": candidate.get("source_url", ""),
            "source_page_url": candidate.get("source_page_url", ""),
            "source_candidate_id": candidate_id,
            "title": paper_title,
            "title_key": normalize_title_key(paper_title),
            "title_source": candidate.get("title_source") or "candidate",
            "tags": tags,
            "read_status": str(data.get("read_status") or candidate.get("read_status") or "unread"),
            "status": str(data.get("read_status") or candidate.get("read_status") or "unread"),
            "read_status_source": "user" if data.get("read_status") else metadata.get("read_status_source", ""),
            "projects": projects,
            "project": projects[0] if projects else "",
            **importance_fields(data.get("importance", candidate.get("importance", ""))),
            "agent_analysis_status": "candidate_brief",
            "processing_mode": "deep",
            "reading_mode": "deep",
            "processing_status": "processing",
            "processing_background": "queued",
            "processing_error": "",
            "updated_at": now_iso(),
        }
    )
    write_json(paper_dir / "metadata.json", metadata)
    thinking = load_thinking(paper_dir)
    if brief.strip():
        thinking["explain"] = {
            "content": brief,
            "updated_at": now_iso(),
            "source": "candidate-kimi-brief",
            "prompt": str(candidate.get("brief_prompt") or ""),
        }
    candidate_annotations = read_json(path / "annotations.json", {"annotations": []})
    thinking["annotations"] = [
        item for item in thinking.get("annotations", []) if not str(item.get("id", "")).startswith(f"{candidate_id}-")
    ]
    for item in clean_candidate_annotations(candidate_annotations).get("annotations", []):
        thinking["annotations"].append({**item, "id": f"{candidate_id}-{item['id']}", "block_id": PAPER_BRIEF_BLOCK_ID})
    cleaned_thinking = clean_thinking(thinking)
    write_json(paper_dir / "thinking.json", cleaned_thinking)
    sync_library_from_metadata(workspace, paper_id, paper_dir, metadata, generate_pdf_preview=False)
    background_started = start_background_paper_processing(workspace, paper_id, paper_dir, {}, mode="deep")
    candidate.update({"decision": "saved", "saved_paper_id": paper_id, "updated_at": now_iso()})
    write_candidate(workspace, candidate)
    return {"ok": True, "paper_id": paper_id, "metadata": read_json(paper_dir / "metadata.json", metadata), "processing_background": "started" if background_started else "already_running", "migrated_annotations": len(candidate_annotations.get("annotations", [])), "candidate": candidate_summary(candidate, workspace)}


def read_library_index(workspace: Path) -> dict[str, Any]:
    """Read the web index without initialization, per-paper discovery, or caching.

    Mutation APIs update library.json; external index edits are visible on the
    next request. External per-paper edits do not rescan/update this index;
    paper GET and CLI load_library still read those per-paper files.
    """
    library = read_json(workspace / "library.json", {"version": TOOL_VERSION, "papers": []})
    if not isinstance(library, dict):
        library = {"version": TOOL_VERSION, "papers": []}
    if "papers" not in library or not isinstance(library["papers"], list):
        library["papers"] = []
    return library


def load_library_raw(workspace: Path) -> dict[str, Any]:
    ensure_workspace(workspace)
    return read_library_index(workspace)


def load_library(workspace: Path) -> dict[str, Any]:
    library = load_library_raw(workspace)
    for paper in library["papers"]:
        paper_dir = workspace / paper.get("paper_dir", "")
        metadata = normalized_metadata(paper_dir, read_json(paper_dir / "metadata.json", {})) if paper_dir.exists() else {}
        fields = infer_processing_fields(paper_dir, metadata)
        paper.setdefault("processing_mode", fields["processing_mode"])
        paper.setdefault("reading_mode", fields["reading_mode"])
        paper.setdefault("processing_status", fields["processing_status"])
        projects = metadata_projects({**paper, **metadata})
        if projects:
            paper["projects"] = projects
            paper["project"] = projects[0]
        tags = normalize_tag_paths(metadata.get("tags", paper.get("tags", [])))
        if tags:
            paper["tags"] = tags
        for key in {"authors", "institutions", "venue", "year", "importance", "importance_tags", "preview_image", "preview_image_alt", "source_pdf_name", "source_type", "source_reference", "source_parent_paper_id", "source_parent_paper_title", "source_url", "source_page_url", "pdf_url", "open_access_pdf_url", "semantic_scholar_url", "arxiv_id", "reference_pdf_error", "original_path", "processing_error", "translation_status", "translation_error", "translation_backend", "citation_count", "citation_error", "citation_source", "citation_url", "citation_updated_at", "reading_progress_summary", "reading_progress_updated_at", "read_status_source", "title_key", "video_links", "video_search_status", "video_search_error", "video_search_updated_at", "youtube_quota", "project", "projects", "tag_colors", "project_colors"}:
            value = metadata.get(key)
            existing_value = paper.get(key)
            empty_existing = key not in paper or existing_value is None or existing_value == "" or (isinstance(existing_value, list) and not existing_value) or (isinstance(existing_value, dict) and not existing_value)
            if empty_existing and value is not None and value != "":
                paper[key] = value
    return library


def save_library(workspace: Path, library: dict[str, Any]) -> None:
    library["version"] = TOOL_VERSION
    library["updated_at"] = now_iso()
    write_json(workspace / "library.json", library)


def upsert_paper_record(workspace: Path, record: dict[str, Any]) -> None:
    with write_lock_for(workspace / "library.json"):
        library = load_library_raw(workspace)
        papers = library["papers"]
        for index, existing in enumerate(papers):
            if existing.get("id") == record.get("id"):
                merged = {**existing, **record, "updated_at": now_iso()}
                papers[index] = merged
                save_library(workspace, library)
                return
        record.setdefault("created_at", now_iso())
        record.setdefault("updated_at", now_iso())
        papers.append(record)
        papers.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        save_library(workspace, library)


def find_paper_record(workspace: Path, paper_id: str) -> dict[str, Any] | None:
    library = load_library(workspace)
    for paper in library.get("papers", []):
        if paper.get("id") == paper_id:
            return paper
    return None


def remove_paper_record(workspace: Path, paper_id: str) -> bool:
    with write_lock_for(workspace / "library.json"):
        library = load_library_raw(workspace)
        papers = library.get("papers", [])
        next_papers = [paper for paper in papers if paper.get("id") != paper_id]
        if len(next_papers) == len(papers):
            return False
        library["papers"] = next_papers
        save_library(workspace, library)
        return True


def sync_library_from_metadata(workspace: Path, paper_id: str, paper_dir: Path, metadata: dict[str, Any], *, generate_pdf_preview: bool = True) -> None:
    original_preview_image = metadata.get("preview_image", "")
    metadata = normalized_metadata(paper_dir, metadata, generate_pdf_preview=generate_pdf_preview)
    if metadata.get("preview_image") and metadata.get("preview_image") != original_preview_image and (paper_dir / "metadata.json").exists():
        write_json(paper_dir / "metadata.json", metadata)
    processing_mode = metadata.get("processing_mode") or metadata.get("reading_mode") or "deep"
    processing_status = metadata.get("processing_status") or "ready"
    authors = metadata.get("authors") or metadata.get("author", "")
    institutions = metadata.get("institutions") or metadata.get("institution", "")
    venue = metadata.get("venue") or metadata.get("journal", "")
    year = normalize_year(metadata.get("year") or metadata.get("publication_year", ""))
    projects = metadata_projects(metadata)
    upsert_paper_record(
        workspace,
        {
            "id": paper_id,
            "title": metadata.get("title") or paper_id,
            "title_key": metadata.get("title_key") or normalize_title_key(metadata.get("title") or paper_id),
            "authors": authors,
            "institutions": institutions,
            "paper_dir": str(paper_dir.relative_to(workspace)),
            "metadata": str((paper_dir / "metadata.json").relative_to(workspace)),
            "reader_md": str((paper_dir / "reader.md").relative_to(workspace)),
            "annotated_md": str((paper_dir / "annotated.md").relative_to(workspace)),
            "notes_md": str((paper_dir / "notes.md").relative_to(workspace)),
            "source_pdf": str((paper_dir / "original.pdf").relative_to(workspace)) if (paper_dir / "original.pdf").exists() else "",
            "venue": venue,
            "year": year,
            "importance": metadata.get("importance", ""),
            "importance_tags": metadata.get("importance_tags", []),
            "preview_image": metadata.get("preview_image", ""),
            "preview_image_alt": metadata.get("preview_image_alt", ""),
            "project": projects[0] if projects else "",
            "projects": projects,
            "read_status": metadata.get("read_status", metadata.get("status", "unread")),
            "read_status_source": metadata.get("read_status_source", ""),
            "reading_progress_summary": metadata.get("reading_progress_summary", {}),
            "reading_progress_updated_at": metadata.get("reading_progress_updated_at", ""),
            "processing_mode": processing_mode,
            "reading_mode": metadata.get("reading_mode", processing_mode),
            "processing_status": processing_status,
            "processing_error": metadata.get("processing_error", ""),
            "translation_status": metadata.get("translation_status", "not_started"),
            "translation_error": metadata.get("translation_error", ""),
            "translation_backend": metadata.get("translation_backend", ""),
            "translated_segments": metadata.get("translated_segments"),
            "agent_analysis_status": metadata.get("agent_analysis_status", ""),
            "paper_brief_status": metadata.get("paper_brief_status", ""),
            "paper_brief_error": metadata.get("paper_brief_error", ""),
            "paper_brief_updated_at": metadata.get("paper_brief_updated_at", ""),
            "paper_brief_title": metadata.get("paper_brief_title", ""),
            "title_source": metadata.get("title_source", ""),
            "feishu": metadata.get("feishu", {}),
            "feishu_attachment": metadata.get("feishu_attachment", {}),
            "source_pdf_sha256": metadata.get("source_pdf_sha256", ""),
            "citation_count": metadata.get("citation_count", ""),
            "citation_error": metadata.get("citation_error", ""),
            "citation_source": metadata.get("citation_source", ""),
            "citation_url": metadata.get("citation_url", ""),
            "citation_updated_at": metadata.get("citation_updated_at", ""),
            "pdf_url": metadata.get("pdf_url", ""),
            "open_access_pdf_url": metadata.get("open_access_pdf_url", ""),
            "semantic_scholar_url": metadata.get("semantic_scholar_url", ""),
            "arxiv_id": metadata.get("arxiv_id", ""),
            "reference_pdf_error": metadata.get("reference_pdf_error", ""),
            "video_links": metadata.get("video_links", []),
            "video_search_status": metadata.get("video_search_status", "not_started"),
            "video_search_error": metadata.get("video_search_error", ""),
            "video_search_updated_at": metadata.get("video_search_updated_at", ""),
            "youtube_quota": metadata.get("youtube_quota", {}),
            "tags": normalize_tag_paths(metadata.get("tags", [])),
            "tag_colors": metadata.get("tag_colors", {}),
            "project_colors": metadata.get("project_colors", {}),
            "source_type": metadata.get("source_type", "pdf" if (paper_dir / "original.pdf").exists() else metadata.get("source_type", "manual")),
            "source_reference": metadata.get("source_reference", ""),
            "source_parent_paper_id": metadata.get("source_parent_paper_id", ""),
            "source_parent_paper_title": metadata.get("source_parent_paper_title", ""),
            "source_url": metadata.get("source_url", ""),
            "source_page_url": metadata.get("source_page_url", ""),
            "source_pdf_name": metadata.get("source_pdf_name", ""),
            "original_path": metadata.get("original_path", ""),
            "created_at": metadata.get("created_at", ""),
            "created_or_refreshed_at": metadata.get("created_or_refreshed_at", ""),
        },
    )


def mindmaps_dir(workspace: Path) -> Path:
    path = workspace / "mindmaps"
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_mindmap_project(project: Any) -> str:
    normalized = normalize_project_name(project)
    return normalized if normalized in CANONICAL_PROJECTS else "collaborative"


def mindmap_project_dir(workspace: Path, project: Any) -> Path:
    path = mindmaps_dir(workspace) / re.sub(r"[^a-zA-Z0-9_.-]+", "-", normalize_mindmap_project(project)).strip("-")
    path.mkdir(parents=True, exist_ok=True)
    return path


def mindmap_index_path(workspace: Path) -> Path:
    return mindmaps_dir(workspace) / "index.json"


def safe_mindmap_id(value: Any) -> str:
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(value or "")).strip("-")
    return safe_id[:96]


def mindmap_doc_path(workspace: Path, project: Any, mindmap_id: str) -> Path:
    safe_id = safe_mindmap_id(mindmap_id)
    if not safe_id:
        raise ValueError("mindmap_id is required")
    return mindmap_project_dir(workspace, project) / f"{safe_id}.json"


def canvas_root(workspace: Path) -> Path:
    return workspace / "canvas_boards"


def normalize_canvas_project(project: Any) -> str:
    return normalize_project_name(project) or "collaborative"


def canvas_project_dir(workspace: Path, project: Any) -> Path:
    return canvas_root(workspace) / re.sub(r"[^a-zA-Z0-9_.-]+", "-", normalize_canvas_project(project)).strip("-")


def canvas_board_path(workspace: Path, project: Any, board_id: str) -> Path:
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(board_id or "")).strip("-")
    return canvas_project_dir(workspace, project) / f"{safe_id}.json"


def canvas_index_path(workspace: Path) -> Path:
    return canvas_root(workspace) / "index.json"


def slug_id(prefix: str, value: str = "") -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "-", unicodedata.normalize("NFKC", value or "").lower()).strip("-")[:42]
    suffix = hashlib.sha1(f"{value}-{now_iso()}-{uuid.uuid4().hex}".encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{base}-{suffix}" if base else f"{prefix}-{suffix}"


def clean_canvas_ref(ref: Any) -> dict[str, str]:
    if not isinstance(ref, dict):
        return {}
    return {
        key: str(ref.get(key) or "")
        for key in {"paper_id", "annotation_id", "segment_id", "thinking_block_id", "takeaway_block_id", "media_src", "source"}
        if str(ref.get(key) or "")
    }


def clean_canvas_card(card: Any, index: int = 0) -> dict[str, Any]:
    item = card if isinstance(card, dict) else {}
    kind = str(item.get("kind") or "text").strip().lower()
    if kind not in {"text", "paper", "note", "image", "table"}:
        kind = "text"
    now = now_iso()
    source_refs = [clean_canvas_ref(ref) for ref in item.get("source_refs", [])] if isinstance(item.get("source_refs"), list) else []
    source_refs = [ref for ref in source_refs if ref]
    return {
        "id": str(item.get("id") or slug_id("card", f"{kind}-{index}")),
        "kind": kind,
        "x": float(item.get("x") or 0),
        "y": float(item.get("y") or 0),
        "width": max(80, min(1200, float(item.get("width") or (320 if kind == "table" else 240)))),
        "height": max(48, min(900, float(item.get("height") or (220 if kind == "table" else 120)))),
        "title": str(item.get("title") or ""),
        "text": str(item.get("text") or ""),
        "cluster_id": str(item.get("cluster_id") or ""),
        "paper_id": str(item.get("paper_id") or ""),
        "annotation_id": str(item.get("annotation_id") or ""),
        "local_tags": normalize_string_list(item.get("local_tags", [])),
        "linked_tags": normalize_tag_paths(item.get("linked_tags", [])),
        "source_refs": source_refs,
        "table": item.get("table") if isinstance(item.get("table"), dict) else {},
        "sync_excluded": bool(item.get("sync_excluded")),
        "created_at": str(item.get("created_at") or now),
        "updated_at": str(item.get("updated_at") or now),
    }


def clean_canvas_cluster(cluster: Any, index: int = 0) -> dict[str, Any]:
    item = cluster if isinstance(cluster, dict) else {}
    title = str(item.get("title") or "Cluster").strip() or "Cluster"
    tag_match = re.search(r"#([\w\-./\u4e00-\u9fff]+)", title)
    now = now_iso()
    return {
        "id": str(item.get("id") or slug_id("cluster", f"{title}-{index}")),
        "x": float(item.get("x") or 0),
        "y": float(item.get("y") or 0),
        "width": max(160, min(2400, float(item.get("width") or 520))),
        "height": max(120, min(1800, float(item.get("height") or 340))),
        "title": title,
        "tag_candidate": str(item.get("tag_candidate") or (tag_match.group(1) if tag_match else "")),
        "linked_library_tag": str(item.get("linked_library_tag") or ""),
        "sync_mode": str(item.get("sync_mode") or "local"),
        "created_at": str(item.get("created_at") or now),
        "updated_at": str(item.get("updated_at") or now),
    }


def clean_canvas_board(data: Any, project: Any = "collaborative", board_id: str = "") -> dict[str, Any]:
    raw = data if isinstance(data, dict) else {}
    now = now_iso()
    title = str(raw.get("title") or "Untitled Canvas").strip() or "Untitled Canvas"
    clean_project = normalize_canvas_project(raw.get("project") or project)
    clean_id = str(raw.get("id") or board_id or slug_id("board", title))
    viewport = raw.get("viewport") if isinstance(raw.get("viewport"), dict) else {}
    return {
        "version": 1,
        "id": clean_id,
        "project": clean_project,
        "title": title,
        "description": str(raw.get("description") or ""),
        "viewport": {
            "x": float(viewport.get("x") or 0),
            "y": float(viewport.get("y") or 0),
            "zoom": max(0.2, min(3, float(viewport.get("zoom") or 1))),
        },
        "cards": [clean_canvas_card(card, index) for index, card in enumerate(raw.get("cards", []))] if isinstance(raw.get("cards"), list) else [],
        "clusters": [clean_canvas_cluster(cluster, index) for index, cluster in enumerate(raw.get("clusters", []))] if isinstance(raw.get("clusters"), list) else [],
        "edges": raw.get("edges", []) if isinstance(raw.get("edges"), list) else [],
        "created_at": str(raw.get("created_at") or now),
        "updated_at": str(raw.get("updated_at") or now),
    }


def read_canvas_index(workspace: Path) -> dict[str, Any]:
    root = canvas_root(workspace)
    root.mkdir(parents=True, exist_ok=True)
    index = read_json(canvas_index_path(workspace), {"version": 1, "boards": []})
    if not isinstance(index, dict):
        index = {"version": 1, "boards": []}
    if not isinstance(index.get("boards"), list):
        index["boards"] = []
    return index


def write_canvas_index(workspace: Path, index: dict[str, Any]) -> None:
    index["version"] = 1
    index["updated_at"] = now_iso()
    write_json(canvas_index_path(workspace), index)


def canvas_board_summary(board: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": board.get("id", ""),
        "project": board.get("project", ""),
        "title": board.get("title", "Untitled Canvas"),
        "description": board.get("description", ""),
        "card_count": len(board.get("cards", [])),
        "cluster_count": len(board.get("clusters", [])),
        "updated_at": board.get("updated_at", ""),
        "created_at": board.get("created_at", ""),
    }


def ensure_default_canvas_board(workspace: Path) -> dict[str, Any]:
    index = read_canvas_index(workspace)
    if index.get("boards"):
        return index
    board = clean_canvas_board({"title": "Collaborative Canvas", "project": "collaborative"}, "collaborative")
    write_json(canvas_board_path(workspace, board["project"], board["id"]), board)
    index["boards"] = [canvas_board_summary(board)]
    write_canvas_index(workspace, index)
    return index


def list_canvas_boards(workspace: Path, project: Any = "") -> dict[str, Any]:
    index = ensure_default_canvas_board(workspace)
    clean_project = normalize_canvas_project(project) if project else ""
    boards = index.get("boards", [])
    if clean_project:
        boards = [board for board in boards if board.get("project") == clean_project]
    return {"version": 1, "boards": boards}


def find_canvas_board_summary(workspace: Path, board_id: str) -> dict[str, Any] | None:
    index = ensure_default_canvas_board(workspace)
    for board in index.get("boards", []):
        if board.get("id") == board_id:
            return board
    return None


def read_canvas_board(workspace: Path, board_id: str) -> dict[str, Any]:
    summary = find_canvas_board_summary(workspace, board_id)
    if not summary:
        raise FileNotFoundError(board_id)
    board = read_json(canvas_board_path(workspace, summary.get("project"), board_id), {})
    return clean_canvas_board(board, summary.get("project"), board_id)


def upsert_canvas_board(workspace: Path, board: dict[str, Any]) -> dict[str, Any]:
    clean = clean_canvas_board(board, board.get("project"), board.get("id"))
    clean["updated_at"] = now_iso()
    write_json(canvas_board_path(workspace, clean["project"], clean["id"]), clean)
    index = read_canvas_index(workspace)
    summaries = [item for item in index.get("boards", []) if item.get("id") != clean["id"]]
    summaries.append(canvas_board_summary(clean))
    summaries.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    index["boards"] = summaries
    write_canvas_index(workspace, index)
    return clean


def create_canvas_board(workspace: Path, data: dict[str, Any]) -> dict[str, Any]:
    project = normalize_canvas_project(data.get("project") or "collaborative")
    title = str(data.get("title") or "Untitled Canvas").strip() or "Untitled Canvas"
    board = clean_canvas_board({**data, "id": slug_id("board", title), "project": project, "title": title}, project)
    return upsert_canvas_board(workspace, board)


def delete_canvas_board(workspace: Path, board_id: str) -> bool:
    summary = find_canvas_board_summary(workspace, board_id)
    if not summary:
        return False
    path = canvas_board_path(workspace, summary.get("project"), board_id)
    if path.exists():
        path.unlink()
    index = read_canvas_index(workspace)
    index["boards"] = [item for item in index.get("boards", []) if item.get("id") != board_id]
    write_canvas_index(workspace, index)
    return True


def canvas_sync_proposals(workspace: Path, board: dict[str, Any]) -> list[dict[str, Any]]:
    library = load_library(workspace)
    papers = {paper.get("id"): set(normalize_tag_paths(paper.get("tags", []))) for paper in library.get("papers", [])}
    proposals: list[dict[str, Any]] = []
    for cluster in board.get("clusters", []):
        tag_values = normalize_tag_paths(cluster.get("linked_library_tag") or cluster.get("tag_candidate") or "")
        tag = tag_values[0] if tag_values else ""
        if not tag:
            continue
        cards = [card for card in board.get("cards", []) if card.get("cluster_id") == cluster.get("id") and card.get("kind") == "paper" and card.get("paper_id")]
        for card in cards:
            paper_id = card.get("paper_id")
            if tag in papers.get(paper_id, set()):
                continue
            proposals.append({
                "id": f"sync-{cluster.get('id')}-{paper_id}-{tag}",
                "type": "add-tag-to-paper",
                "board_id": board.get("id", ""),
                "cluster_id": cluster.get("id", ""),
                "cluster_title": cluster.get("title", ""),
                "paper_id": paper_id,
                "paper_title": next((paper.get("title") for paper in library.get("papers", []) if paper.get("id") == paper_id), paper_id),
                "from": "",
                "to": tag,
                "status": "pending",
            })
    return proposals


def mindmap_node_id(prefix: str, *parts: Any) -> str:
    source = "::".join(str(part or "") for part in parts)
    slug = slugify(source, prefix)[:52]
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{slug}-{digest}"


def default_mindmap(project: str, title: str = "", mindmap_id: str = "") -> dict[str, Any]:
    now = now_iso()
    project = normalize_mindmap_project(project)
    clean_title = str(title or "").strip() or f"{project} sensemaking"
    clean_id = safe_mindmap_id(mindmap_id) or slug_id("mindmap", f"{project}-{clean_title}")
    root_id = f"root-{clean_id}"
    return {
        "version": 1,
        "id": clean_id,
        "project": project,
        "title": clean_title,
        "description": "",
        "view": "tree",
        "root_id": root_id,
        "nodes": [
            {
                "id": root_id,
                "type": "root",
                "kind": "root",
                "title": clean_title,
                "parent_id": "",
                "children": [],
                "created_at": now,
                "updated_at": now,
            }
        ],
        "viewport": {"x": 80, "y": 80, "zoom": 1},
        "expanded_node_ids": [root_id],
        "selected_node_id": root_id,
        "layout": {},
        "created_at": now,
        "updated_at": now,
        "source": "",
    }


def clean_mindmap_table(value: Any) -> dict[str, Any]:
    table = value if isinstance(value, dict) else {}
    columns = normalize_string_list(table.get("columns", []))
    if not columns:
        columns = ["Paper / note source", "Problem addressed", "Method / system move", "What it misses", "What we can borrow", "Implication for our paper"]
    rows: list[dict[str, str]] = []
    raw_rows = table.get("rows") if isinstance(table.get("rows"), list) else []
    for row in raw_rows[:120]:
        if not isinstance(row, dict):
            continue
        rows.append({column: str(row.get(column) or "")[:1200] for column in columns})
    if not rows:
        rows = [{column: "" for column in columns}]
    return {
        "template": str(table.get("template") or "Research Gap Comparison")[:160],
        "columns": columns[:16],
        "rows": rows,
    }


def clean_mindmap_node(node: dict[str, Any], project: str) -> dict[str, Any] | None:
    if not isinstance(node, dict):
        return None
    node_type = str(node.get("type") or node.get("kind") or "text").strip().lower()
    if node_type == "category":
        node_type = "text"
    if node_type == "frame":
        node_type = "text"
    if node_type == "writing":
        node_type = "text"
    if node_type not in {"root", "text", "paper-tag", "paper", "note", "table"}:
        node_type = "text"
    node_id = str(node.get("id") or mindmap_node_id(node_type, node.get("title"), node.get("paper_id"))).strip()
    if not node_id:
        return None
    category_path = [normalize_tag_path(part) for part in (node.get("category_path") if isinstance(node.get("category_path"), list) else [])]
    category_path = [part for part in category_path if part]
    title = str(node.get("title") or "").strip() or (project if node_type == "root" else "Untitled")
    tag_match = re.search(r"#([\w\-./\u4e00-\u9fff]+)", title)
    return {
        "id": node_id,
        "type": node_type,
        "kind": node_type,
        "field_type": str(node.get("field_type") or node_type).strip(),
        "canonical_tag": str(node.get("canonical_tag") or "").strip(),
        "title": title,
        "parent_id": str(node.get("parent_id") or ""),
        "paper_id": str(node.get("paper_id") or ""),
        "category_path": category_path,
        "summary": str(node.get("summary") or "").strip(),
        "text": str(node.get("text") or "").strip(),
        "source": str(node.get("source") or ""),
        "source_refs": clean_source_refs(node.get("source_refs")),
        "inline_refs": clean_source_refs(node.get("inline_refs")),
        "note_tags": normalize_string_list(node.get("note_tags", [])),
        "branch_tag_candidate": normalize_tag_path(node.get("branch_tag_candidate", "") or (tag_match.group(1) if tag_match else "")),
        "linked_library_tag": normalize_tag_path(node.get("linked_library_tag", "")),
        "table": clean_mindmap_table(node.get("table")) if node_type == "table" else {},
        "collapsed": bool(node.get("collapsed")),
        "children": [str(child) for child in (node.get("children") if isinstance(node.get("children"), list) else []) if str(child).strip()],
        "created_at": str(node.get("created_at") or now_iso()),
        "updated_at": str(node.get("updated_at") or now_iso()),
    }


def clean_mindmap_doc(data: Any, project: str, mindmap_id: str = "") -> dict[str, Any]:
    project = normalize_mindmap_project(project)
    data = data if isinstance(data, dict) else {}
    title = str(data.get("title") or "").strip() or f"{project} sensemaking"
    clean_id = safe_mindmap_id(data.get("id") or mindmap_id) or slug_id("mindmap", f"{project}-{title}")
    default = default_mindmap(project, title, clean_id)
    raw_nodes = data.get("nodes") if isinstance(data.get("nodes"), list) else []
    nodes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_node in raw_nodes[:MINDMAP_NODE_LIMIT]:
        node = clean_mindmap_node(raw_node, project)
        if not node or node["id"] in seen:
            continue
        seen.add(node["id"])
        nodes.append(node)
    root_id = str(data.get("root_id") or default["root_id"])
    if not any(node.get("id") == root_id for node in nodes):
        nodes.insert(0, default["nodes"][0])
        root_id = default["root_id"]
    valid_ids = {node["id"] for node in nodes}
    for node in nodes:
        if node["type"] != "root" and node.get("parent_id") not in valid_ids:
            node["parent_id"] = root_id
        node["children"] = [child for child in node.get("children", []) if child in valid_ids and child != node["id"]]
    existing_children = {child for node in nodes for child in node.get("children", [])}
    by_id = {node["id"]: node for node in nodes}
    for node in nodes:
        parent_id = node.get("parent_id")
        if node["id"] != root_id and parent_id in by_id and node["id"] not in existing_children:
            by_id[parent_id].setdefault("children", []).append(node["id"])
    viewport = data.get("viewport") if isinstance(data.get("viewport"), dict) else {}
    selected_node_id = str(data.get("selected_node_id") or root_id)
    if selected_node_id not in valid_ids:
        selected_node_id = root_id
    expanded_node_ids = [str(item) for item in (data.get("expanded_node_ids") if isinstance(data.get("expanded_node_ids"), list) else []) if str(item) in valid_ids]
    if root_id not in expanded_node_ids:
        expanded_node_ids.insert(0, root_id)
    return {
        "version": 1,
        "id": clean_id,
        "project": project,
        "title": title,
        "description": str(data.get("description") or ""),
        "view": str(data.get("view") or "tree"),
        "root_id": root_id,
        "nodes": nodes,
        "viewport": {
            "x": float(viewport.get("x") if viewport.get("x") is not None else 80),
            "y": float(viewport.get("y") if viewport.get("y") is not None else 80),
            "zoom": max(0.2, min(3, float(viewport.get("zoom") or 1))),
        },
        "expanded_node_ids": expanded_node_ids,
        "selected_node_id": selected_node_id,
        "layout": data.get("layout") if isinstance(data.get("layout"), dict) else {},
        "source": str(data.get("source") or ""),
        "archived_at": str(data.get("archived_at") or ""),
        "created_at": str(data.get("created_at") or now_iso()),
        "updated_at": now_iso(),
    }


def read_mindmaps_index(workspace: Path) -> dict[str, Any]:
    root = mindmaps_dir(workspace)
    index = read_json(mindmap_index_path(workspace), {"version": 2, "mindmaps": [], "current_by_project": {}})
    if not isinstance(index, dict):
        index = {"version": 2, "mindmaps": [], "current_by_project": {}}
    if not isinstance(index.get("mindmaps"), list):
        index["mindmaps"] = []
    if not isinstance(index.get("current_by_project"), dict):
        index["current_by_project"] = {}
    for project in CANONICAL_PROJECTS:
        legacy_path = root / f"{project}.json"
        if legacy_path.exists() and not any(item.get("project") == project for item in index["mindmaps"]):
            legacy = clean_mindmap_doc(read_json(legacy_path, {}), project, f"legacy-{project}")
            legacy["title"] = legacy.get("title") or f"{project} legacy map"
            write_json(mindmap_doc_path(workspace, project, legacy["id"]), legacy)
            index["mindmaps"].append(mindmap_summary_from_doc(legacy))
            index["current_by_project"][project] = legacy["id"]
    return index


def write_mindmaps_index(workspace: Path, index: dict[str, Any]) -> None:
    index["version"] = 2
    index["updated_at"] = now_iso()
    write_json(mindmap_index_path(workspace), index)


def mindmap_summary_from_doc(doc: dict[str, Any]) -> dict[str, Any]:
    counts: dict[str, int] = {"root": 0, "text": 0, "paper": 0, "note": 0, "table": 0}
    for node in doc.get("nodes", []):
        node_type = node.get("type") or node.get("kind") or "text"
        counts[node_type] = counts.get(node_type, 0) + 1
    return {
        "id": doc.get("id", ""),
        "project": doc.get("project", ""),
        "title": doc.get("title", "Untitled Mindmap"),
        "description": doc.get("description", ""),
        "view": doc.get("view", "tree"),
        "node_count": len(doc.get("nodes", [])),
        "counts": counts,
        "selected_node_id": doc.get("selected_node_id", doc.get("root_id", "")),
        "updated_at": doc.get("updated_at", ""),
        "created_at": doc.get("created_at", ""),
        "archived_at": doc.get("archived_at", ""),
    }


def upsert_mindmap_summary(workspace: Path, doc: dict[str, Any]) -> None:
    index = read_mindmaps_index(workspace)
    summary = mindmap_summary_from_doc(doc)
    index["mindmaps"] = [item for item in index.get("mindmaps", []) if item.get("id") != summary["id"]]
    index["mindmaps"].append(summary)
    index["mindmaps"].sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    if not summary.get("archived_at"):
        index.setdefault("current_by_project", {})[summary["project"]] = summary["id"]
    write_mindmaps_index(workspace, index)


def list_mindmaps(workspace: Path, project: Any = "", include_archived: bool = False) -> dict[str, Any]:
    index = read_mindmaps_index(workspace)
    clean_project = normalize_mindmap_project(project) if project else ""
    items = index.get("mindmaps", [])
    if clean_project:
        items = [item for item in items if item.get("project") == clean_project]
    if not include_archived:
        items = [item for item in items if not item.get("archived_at")]
    return {"version": 2, "mindmaps": items, "current_by_project": index.get("current_by_project", {})}


def current_mindmap_id(workspace: Path, project: Any) -> str:
    project_name = normalize_mindmap_project(project)
    index = read_mindmaps_index(workspace)
    current_id = safe_mindmap_id(index.get("current_by_project", {}).get(project_name, ""))
    if current_id:
        return current_id
    items = list_mindmaps(workspace, project_name).get("mindmaps", [])
    return safe_mindmap_id(items[0].get("id")) if items else ""


def ensure_default_mindmap(workspace: Path, project: Any) -> dict[str, Any]:
    project_name = normalize_mindmap_project(project)
    existing_id = current_mindmap_id(workspace, project_name)
    if existing_id:
        return read_mindmap(workspace, project_name, existing_id)
    doc = default_mindmap(project_name, f"{project_name} sensemaking")
    write_json(mindmap_doc_path(workspace, project_name, doc["id"]), doc)
    upsert_mindmap_summary(workspace, doc)
    return doc


def read_mindmap(workspace: Path, project: Any, mindmap_id: str = "", *, seed: bool = True) -> dict[str, Any]:
    project_name = normalize_mindmap_project(project)
    doc_id = safe_mindmap_id(mindmap_id) or current_mindmap_id(workspace, project_name)
    if not doc_id:
        return ensure_default_mindmap(workspace, project_name)
    path = mindmap_doc_path(workspace, project_name, doc_id)
    if not path.exists():
        raise FileNotFoundError(doc_id)
    doc = clean_mindmap_doc(read_json(path, {}), project_name, doc_id)
    upsert_mindmap_summary(workspace, doc)
    return doc


def write_mindmap(workspace: Path, project: Any, data: Any, mindmap_id: str = "") -> dict[str, Any]:
    project_name = normalize_mindmap_project(project)
    doc = clean_mindmap_doc(data, project_name, mindmap_id or (data.get("id") if isinstance(data, dict) else ""))
    doc["updated_at"] = now_iso()
    write_json(mindmap_doc_path(workspace, project_name, doc["id"]), doc)
    upsert_mindmap_summary(workspace, doc)
    return doc


def create_mindmap(workspace: Path, data: dict[str, Any]) -> dict[str, Any]:
    project = normalize_mindmap_project(data.get("project") or "collaborative")
    title = str(data.get("title") or "New sensemaking view").strip() or "New sensemaking view"
    doc = default_mindmap(project, title)
    if isinstance(data.get("viewport"), dict):
        doc["viewport"] = data["viewport"]
    return write_mindmap(workspace, project, doc, doc["id"])


def duplicate_mindmap(workspace: Path, project: Any, mindmap_id: str, title: str = "") -> dict[str, Any]:
    source = read_mindmap(workspace, project, mindmap_id)
    new_title = str(title or f"{source.get('title', 'Mindmap')} copy").strip()
    duplicate = json.loads(json.dumps(source))
    duplicate["id"] = slug_id("mindmap", f"{source.get('project')}-{new_title}")
    duplicate["title"] = new_title
    duplicate["created_at"] = now_iso()
    duplicate["updated_at"] = now_iso()
    old_root = duplicate.get("root_id", "")
    new_root = f"root-{duplicate['id']}"
    duplicate["root_id"] = new_root
    for node in duplicate.get("nodes", []):
        if node.get("id") == old_root:
            node["id"] = new_root
            node["title"] = new_title
        if node.get("parent_id") == old_root:
            node["parent_id"] = new_root
        if isinstance(node.get("children"), list):
            node["children"] = [new_root if child == old_root else child for child in node["children"]]
    duplicate["selected_node_id"] = new_root if duplicate.get("selected_node_id") == old_root else duplicate.get("selected_node_id", new_root)
    duplicate["expanded_node_ids"] = [new_root if item == old_root else item for item in duplicate.get("expanded_node_ids", [])]
    return write_mindmap(workspace, project, duplicate, duplicate["id"])


def delete_mindmap(workspace: Path, project: Any, mindmap_id: str, archive: bool = False) -> bool:
    project_name = normalize_mindmap_project(project)
    doc_id = safe_mindmap_id(mindmap_id)
    if not doc_id:
        return False
    path = mindmap_doc_path(workspace, project_name, doc_id)
    if archive and path.exists():
        doc = read_mindmap(workspace, project_name, doc_id)
        doc["archived_at"] = now_iso()
        write_mindmap(workspace, project_name, doc, doc_id)
    elif path.exists():
        path.unlink()
    index = read_mindmaps_index(workspace)
    if not archive:
        index["mindmaps"] = [item for item in index.get("mindmaps", []) if item.get("id") != doc_id]
    if index.get("current_by_project", {}).get(project_name) == doc_id:
        remaining = [item for item in index.get("mindmaps", []) if item.get("project") == project_name and not item.get("archived_at") and item.get("id") != doc_id]
        if remaining:
            index["current_by_project"][project_name] = remaining[0].get("id", "")
        else:
            index["current_by_project"].pop(project_name, None)
    write_mindmaps_index(workspace, index)
    return True


def mm_text(node: ET.Element) -> str:
    return html.unescape(node.attrib.get("TEXT", "")).strip()


def mindmap_clean_title(text: str) -> str:
    text = html.unescape(str(text or ""))
    text = re.sub(r"^[\s\-–—•*#✅🎯🗓]+", "", text).strip()
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -–—")


def category_title_from_mm(text: str) -> str:
    text = mindmap_clean_title(text)
    text = re.sub(r"^\[[^\]]+\]\s*", "", text).strip()
    return text[:160] or "Untitled"


def curated_mindmap_note(text: str) -> str:
    text = mindmap_clean_title(text)
    text = re.sub(r"^[-*]\s*", "", text)
    replacements = [
        (r"^【解决问题】", "Problem: "),
        (r"^【解决的问题?】", "Problem: "),
        (r"^【问题】", "Problem: "),
        (r"^【解决方式】", "Design move: "),
        (r"^【解决】", "Design move: "),
        (r"^【insights?】", "Insight: "),
        (r"^【GAP】", "Gap: "),
        (r"^【值得参考的设计方向】", "Borrow: "),
        (r"^【可以参考的解决思路】", "Borrow: "),
        (r"^【值得借的】", "Borrow: "),
        (r"^【已经做掉的】", "Already covered: "),
        (r"^【结果】", "Finding: "),
        (r"^【结论】", "Finding: "),
    ]
    for pattern, label in replacements:
        text = re.sub(pattern, label, text, flags=re.I).strip()
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = text.replace("\\&", "&").replace("\\.", ".")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= 360:
        return text
    cut = max(text.rfind("。", 0, 360), text.rfind("；", 0, 360), text.rfind(";", 0, 360), text.rfind(".", 0, 360))
    return (text[: cut + 1] if cut > 120 else text[:360]).strip()


def valuable_mindmap_note(text: str) -> bool:
    clean = mindmap_clean_title(text)
    if len(clean) < 8:
        return False
    markers = [
        "【问题】",
        "【解决问题】",
        "【解决的问题】",
        "【解决方式】",
        "【解决】",
        "【insight】",
        "【insights】",
        "【GAP】",
        "【值得参考",
        "【值得借",
        "【可以参考",
        "gap",
        "GAP",
        "boundary",
        "deliberation",
        "private",
        "public",
        "reasoning",
        "trace",
        "可借",
        "借鉴",
        "启发",
        "我们的",
        "我们",
        "不同",
        "没有处理",
        "不处理",
        "未处理",
        "未解决",
    ]
    return any(marker in clean for marker in markers)


def compact_mm_note_subtree(node: ET.Element, max_parts: int = 5) -> str:
    parts = [curated_mindmap_note(mm_text(node))]
    for child in node.findall("node"):
        child_text = curated_mindmap_note(mm_text(child))
        if child_text and valuable_mindmap_note(child_text):
            parts.append(child_text)
        if len(parts) >= max_parts:
            break
    parts = [part for part in parts if part]
    return "；".join(parts[:max_parts])


def related_works_mm_path(workspace: Path) -> Path | None:
    candidates = [
        Path.cwd() / "06_references" / "Related works.mm",
        workspace.parent / "06_references" / "Related works.mm",
        Path(r"E:\MSRA_3\collaborative\06_references\Related works.mm"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def library_title_index(workspace: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for paper in load_library(workspace).get("papers", []):
        key = normalize_title_key(paper.get("title") or "")
        if title_key_is_usable(key):
            result[key] = paper
    return result


def match_mm_paper(text: str, title_index: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    key = normalize_title_key(mindmap_clean_title(text))
    if not title_key_is_usable(key):
        return None
    if key in title_index:
        return title_index[key]
    for title_key, paper in title_index.items():
        if len(title_key) >= 18 and len(key) >= 18 and (title_key in key or key in title_key):
            return paper
    return None


def seed_mindmap_from_related_works(workspace: Path, project: str) -> dict[str, Any]:
    doc = default_mindmap(project)
    mm_path = related_works_mm_path(workspace)
    if not mm_path:
        return doc
    try:
        root = ET.parse(mm_path).getroot()
    except Exception:
        return doc
    title_index = library_title_index(workspace)
    nodes = doc["nodes"]
    by_id = {doc["root_id"]: nodes[0]}
    category_by_path: dict[tuple[str, ...], str] = {(): doc["root_id"]}
    seen_paper_instances: set[tuple[str, tuple[str, ...]]] = set()
    paper_descendant_cache: dict[int, bool] = {}

    def has_paper_descendant(node: ET.Element) -> bool:
        cache_key = id(node)
        if cache_key in paper_descendant_cache:
            return paper_descendant_cache[cache_key]
        if match_mm_paper(mm_text(node), title_index):
            paper_descendant_cache[cache_key] = True
            return True
        value = any(has_paper_descendant(child) for child in node.findall("node"))
        paper_descendant_cache[cache_key] = value
        return value

    def add_child(parent_id: str, child: dict[str, Any]) -> None:
        nodes.append(child)
        by_id[child["id"]] = child
        if child["id"] not in by_id[parent_id].setdefault("children", []):
            by_id[parent_id].setdefault("children", []).append(child["id"])

    def ensure_category(path_parts: list[str]) -> str:
        clean_parts = [category_title_from_mm(part) for part in path_parts if category_title_from_mm(part)]
        parent_id = doc["root_id"]
        current: list[str] = []
        for part in clean_parts:
            current.append(part)
            key = tuple(current)
            if key in category_by_path:
                parent_id = category_by_path[key]
                continue
            node_id = mindmap_node_id("cat", project, *current)
            now = now_iso()
            add_child(
                parent_id,
                {
                    "id": node_id,
                    "type": "category",
                    "title": part,
                    "parent_id": parent_id,
                    "paper_id": "",
                    "category_path": current.copy(),
                    "summary": "",
                    "text": "",
                    "source": "related-works-mm",
                    "source_refs": [],
                    "children": [],
                    "created_at": now,
                    "updated_at": now,
                },
            )
            category_by_path[key] = node_id
            parent_id = node_id
        return parent_id

    def add_paper_node(paper: dict[str, Any], category_path: list[str], source_text: str, source_node: ET.Element) -> None:
        paper_id = str(paper.get("id") or "")
        if not paper_id:
            return
        category_tuple = tuple(category_path)
        if (paper_id, category_tuple) in seen_paper_instances:
            return
        seen_paper_instances.add((paper_id, category_tuple))
        parent_id = ensure_category(category_path)
        now = now_iso()
        node_id = mindmap_node_id("paperinst", project, paper_id, "/".join(category_path), source_text)
        child_ids: list[str] = []
        paper_node = {
            "id": node_id,
            "type": "paper",
            "title": paper.get("title") or mindmap_clean_title(source_text),
            "parent_id": parent_id,
            "paper_id": paper_id,
            "category_path": category_path,
            "summary": "",
            "text": "",
            "source": "related-works-mm",
            "source_refs": [],
            "children": child_ids,
            "created_at": now,
            "updated_at": now,
        }
        add_child(parent_id, paper_node)
        note_index = 0
        for child in source_node.findall("node"):
            raw_text = mm_text(child)
            if not valuable_mindmap_note(raw_text):
                continue
            note_text = compact_mm_note_subtree(child)
            if not note_text:
                continue
            note_index += 1
            note_id = mindmap_node_id("note", node_id, note_index, note_text)
            add_child(
                node_id,
                {
                    "id": note_id,
                    "type": "note",
                    "title": note_text.split(":", 1)[0][:64] if ":" in note_text else "Writing note",
                    "parent_id": node_id,
                    "paper_id": paper_id,
                    "category_path": category_path,
                    "summary": "",
                    "text": note_text,
                    "source": "related-works-mm-curated",
                    "source_refs": [],
                    "children": [],
                    "created_at": now,
                    "updated_at": now,
                },
            )
        if note_index:
            first_note = next((by_id[child_id]["text"] for child_id in child_ids if by_id.get(child_id, {}).get("type") == "note"), "")
            paper_node["summary"] = first_note[:260]
        # Mindmap branch labels are local by default. Library tags are changed only through explicit Sync Review.

    def visit(node: ET.Element, category_path: list[str]) -> None:
        text = mm_text(node)
        paper = match_mm_paper(text, title_index)
        if paper:
            add_paper_node(paper, category_path, text, node)
            return
        next_path = category_path
        if text and node is not root and text != "PAI_Related works" and has_paper_descendant(node):
            next_path = [*category_path, category_title_from_mm(text)]
            ensure_category(next_path)
        for child in node.findall("node"):
            visit(child, next_path)

    for child in root.findall("node"):
        visit(child, [])

    def generated_branch_has_paper(node_id: str) -> bool:
        node = by_id.get(node_id)
        if not node:
            return False
        if node.get("type") == "paper":
            return True
        return any(generated_branch_has_paper(child_id) for child_id in node.get("children", []))

    removable = {
        node["id"]
        for node in nodes
        if node.get("type") == "category" and node.get("source") == "related-works-mm" and not generated_branch_has_paper(node["id"])
    }
    if removable:
        nodes[:] = [node for node in nodes if node["id"] not in removable]
        for node in nodes:
            node["children"] = [child_id for child_id in node.get("children", []) if child_id not in removable]
    doc["nodes"] = nodes[:MINDMAP_NODE_LIMIT]
    doc["source"] = str(mm_path)
    doc["updated_at"] = now_iso()
    return clean_mindmap_doc(doc, project)


def sync_paper_tag_path(workspace: Path, paper_id: str, category_path: list[str]) -> None:
    tag = normalize_tag_path("/".join(category_path))
    if not paper_id or not tag:
        return
    record = find_paper_record(workspace, paper_id)
    if not record:
        return
    path = workspace / str(record.get("paper_dir") or "")
    metadata = read_json(path / "metadata.json", {})
    tags = normalize_tag_paths(metadata.get("tags", record.get("tags", [])))
    if tag not in tags:
        tags.append(tag)
        metadata["tags"] = tags
        metadata["updated_at"] = now_iso()
        write_json(path / "metadata.json", metadata)
        sync_library_from_metadata(workspace, paper_id, path, metadata)


def mindmap_summary(workspace: Path, project: str) -> dict[str, Any]:
    doc = ensure_default_mindmap(workspace, project)
    return mindmap_summary_from_doc(doc)


def searchable_takeaway_text(paper_dir: Path, max_chars: int = 5000) -> str:
    doc = load_takeaway_doc(paper_dir)
    parts = []
    for block in doc.get("blocks", [])[:100]:
        parts.extend([block.get("text", ""), block.get("note", ""), block.get("quote", "")])
    return " ".join(str(part or "") for part in parts)[:max_chars]


def mindmap_search_papers(workspace: Path, query: str, project: str = "collaborative", limit: int = 30) -> list[dict[str, Any]]:
    terms = [term for term in re.findall(r"[A-Za-z0-9\-]{2,}|[\u4e00-\u9fff]{2,}", str(query or "").casefold()) if term]
    results = []
    for paper in load_library(workspace).get("papers", []):
        paper_id = str(paper.get("id") or "")
        if not paper_id:
            continue
        paper_dir = workspace / str(paper.get("paper_dir") or "")
        haystack = " ".join(
            [
                paper.get("title", ""),
                paper.get("authors", ""),
                paper.get("venue", ""),
                paper.get("year", ""),
                " ".join(paperProjects := metadata_projects({"project": paper.get("project", ""), "projects": paper.get("projects", [])})),
                " ".join(normalize_tag_paths(paper.get("tags", []))),
                searchable_takeaway_text(paper_dir),
            ]
        ).casefold()
        if terms and not all(term in haystack for term in terms):
            continue
        annotations = read_json(paper_dir / "annotations.json", {"annotations": []}).get("annotations", [])
        takeaway_blocks = load_takeaway_doc(paper_dir).get("blocks", [])
        score = 0
        score += 12 if takeaway_blocks else 0
        score += min(12, len([item for item in annotations if str(item.get("note") or "").strip()]))
        score += {"read": 8, "deep-reading": 6, "skimmed": 4, "skimming": 2}.get(str(paper.get("read_status") or ""), 0)
        score += sum(4 for term in terms if term in " ".join(normalize_tag_paths(paper.get("tags", []))).casefold())
        results.append(
            {
                "paper_id": paper_id,
                "title": paper.get("title", paper_id),
                "authors": paper.get("authors", ""),
                "venue": paper.get("venue", ""),
                "year": paper.get("year", ""),
                "tags": normalize_tag_paths(paper.get("tags", [])),
                "projects": paperProjects,
                "read_status": paper.get("read_status", "unread"),
                "note_count": len([item for item in annotations if str(item.get("note") or "").strip()]),
                "takeaway_count": len(takeaway_blocks),
                "score": score,
            }
        )
    results.sort(key=lambda item: (-item["score"], item["title"]))
    return results[: max(1, min(100, int(limit or 30)))]


def takeaway_nodes_for_paper(workspace: Path, paper_id: str, parent_id: str, category_path: list[str]) -> list[dict[str, Any]]:
    record = find_paper_record(workspace, paper_id)
    if not record:
        return []
    paper_dir = workspace / str(record.get("paper_dir") or "")
    doc = load_takeaway_doc(paper_dir)
    nodes = []
    now = now_iso()
    index = 0
    for block in doc.get("blocks", [])[:80]:
        if block.get("type") == "heading":
            continue
        text = curated_mindmap_note(block.get("text") or block.get("note") or block.get("quote") or "")
        if not text or len(text) < 6:
            continue
        index += 1
        nodes.append(
            {
                "id": mindmap_node_id("note", parent_id, index, text),
                "type": "note",
                "title": text.split(":", 1)[0][:64] if ":" in text else "Takeaway",
                "parent_id": parent_id,
                "paper_id": paper_id,
                "category_path": category_path,
                "summary": "",
                "text": text,
                "source": "takeaway-doc",
                "source_refs": clean_source_refs(block.get("source_refs")),
                "children": [],
                "created_at": now,
                "updated_at": now,
            }
        )
    return nodes[:24]


def add_paper_instance_to_mindmap(workspace: Path, project: Any, data: dict[str, Any]) -> dict[str, Any]:
    project_name = normalize_mindmap_project(project)
    doc = read_mindmap(workspace, project_name, safe_mindmap_id(data.get("mindmap_id") or data.get("id") or ""), seed=True)
    paper_id = str(data.get("paper_id") or "").strip()
    record = find_paper_record(workspace, paper_id)
    if not record:
        raise ValueError(f"Unknown paper: {paper_id}")
    category_path = [normalize_tag_path(part) for part in (data.get("category_path") if isinstance(data.get("category_path"), list) else [])]
    category_path = [part for part in category_path if part]
    if not category_path:
        category_path = [normalize_tag_path(data.get("category") or "Uncategorized") or "Uncategorized"]
    doc = ensure_mindmap_category_path(doc, category_path)
    parent_id = category_id_for_path(doc, category_path) or doc["root_id"]
    now = now_iso()
    node_id = mindmap_node_id("paperinst", project_name, paper_id, "/".join(category_path), now)
    title = str(record.get("title") or paper_id)
    summary = str(data.get("summary") or "").strip()
    node = {
        "id": node_id,
        "type": "paper",
        "title": title,
        "parent_id": parent_id,
        "paper_id": paper_id,
        "category_path": category_path,
        "summary": summary,
        "text": "",
        "source": str(data.get("source") or "manual-add"),
        "source_refs": [],
        "children": [],
        "created_at": now,
        "updated_at": now,
    }
    doc["nodes"].append(node)
    by_id = {item["id"]: item for item in doc["nodes"]}
    by_id[parent_id].setdefault("children", []).append(node_id)
    if data.get("include_takeaway", True):
        note_nodes = takeaway_nodes_for_paper(workspace, paper_id, node_id, category_path)
        doc["nodes"].extend(note_nodes)
        node["children"] = [item["id"] for item in note_nodes]
        if not summary and note_nodes:
            node["summary"] = note_nodes[0].get("text", "")[:260]
    saved = write_mindmap(workspace, project_name, doc, doc.get("id", ""))
    return {"mindmap": saved, "node": node}


def mindmap_descendant_nodes(doc: dict[str, Any], node_id: str) -> list[dict[str, Any]]:
    by_id = {node.get("id"): node for node in doc.get("nodes", [])}
    result: list[dict[str, Any]] = []

    def visit(current_id: str) -> None:
        node = by_id.get(current_id)
        if not node:
            return
        result.append(node)
        child_ids = node.get("children") if isinstance(node.get("children"), list) else []
        implicit = [item.get("id") for item in doc.get("nodes", []) if item.get("parent_id") == current_id and item.get("id") not in child_ids]
        for child_id in [*child_ids, *implicit]:
            visit(str(child_id or ""))

    visit(node_id)
    return result


def mindmap_branch_tag(node: dict[str, Any]) -> str:
    explicit = normalize_tag_path(node.get("linked_library_tag") or node.get("branch_tag_candidate") or "")
    if explicit:
        return explicit
    match = re.search(r"#([\w\-./\u4e00-\u9fff]+)", str(node.get("title") or ""))
    return normalize_tag_path(match.group(1)) if match else ""


def mindmap_sync_proposals(workspace: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    library = load_library(workspace)
    papers = {paper.get("id"): set(normalize_tag_paths(paper.get("tags", []))) for paper in library.get("papers", [])}
    titles = {paper.get("id"): paper.get("title", paper.get("id", "")) for paper in library.get("papers", [])}
    proposals: list[dict[str, Any]] = []
    for branch in doc.get("nodes", []):
        tag = mindmap_branch_tag(branch)
        if not tag:
            continue
        paper_sources: dict[str, set[str]] = {}
        for node in mindmap_descendant_nodes(doc, str(branch.get("id") or "")):
            paper_id = str(node.get("paper_id") or "")
            if not paper_id:
                for ref in node.get("source_refs", []) if isinstance(node.get("source_refs"), list) else []:
                    paper_id = str(ref.get("paper_id") or "")
                    if paper_id:
                        break
            if not paper_id:
                continue
            refs = paper_sources.setdefault(paper_id, set())
            for ref in node.get("source_refs", []) if isinstance(node.get("source_refs"), list) else []:
                if ref.get("annotation_id"):
                    refs.add(str(ref.get("annotation_id")))
        for paper_id, source_note_ids in sorted(paper_sources.items()):
            if tag in papers.get(paper_id, set()):
                continue
            proposals.append(
                {
                    "id": f"sync-{doc.get('id')}-{branch.get('id')}-{paper_id}-{tag}",
                    "type": "add-paper-tag-to-paper",
                    "mindmap_id": doc.get("id", ""),
                    "branch_node_id": branch.get("id", ""),
                    "branch_title": branch.get("title", ""),
                    "paper_id": paper_id,
                    "paper_title": titles.get(paper_id, paper_id),
                    "to": tag,
                    "source_note_ids": sorted(source_note_ids),
                    "status": "pending",
                }
            )
    return proposals


def apply_mindmap_sync_proposals(workspace: Path, proposals: list[dict[str, Any]], selected_ids: set[str]) -> list[dict[str, Any]]:
    applied: list[dict[str, Any]] = []
    for proposal in proposals:
        if selected_ids and proposal.get("id") not in selected_ids:
            continue
        if proposal.get("type") != "add-paper-tag-to-paper":
            continue
        record = find_paper_record(workspace, proposal.get("paper_id", ""))
        if not record:
            continue
        paper_dir = workspace / str(record.get("paper_dir") or "")
        metadata = read_json(paper_dir / "metadata.json", {})
        tags = normalize_tag_paths(metadata.get("tags", record.get("tags", [])))
        tag_values = normalize_tag_paths(proposal.get("to", ""))
        if not tag_values:
            continue
        tag = tag_values[0]
        if tag not in tags:
            metadata["tags"] = tags + [tag]
            metadata["updated_at"] = now_iso()
            write_json(paper_dir / "metadata.json", metadata)
            sync_library_from_metadata(workspace, proposal.get("paper_id", ""), paper_dir, metadata)
            applied.append(proposal)
    return applied


def category_id_for_path(doc: dict[str, Any], category_path: list[str]) -> str:
    normalized = [normalize_tag_path(part) for part in category_path if normalize_tag_path(part)]
    for node in doc.get("nodes", []):
        if node.get("category_path") == normalized and (node.get("type") in {"text", "category", "paper-tag"} or node.get("field_type") in {"frame", "paper-tag", "text"}):
            return str(node.get("id") or "")
    return ""


def ensure_mindmap_category_path(doc: dict[str, Any], category_path: list[str]) -> dict[str, Any]:
    category_path = [normalize_tag_path(part) for part in category_path if normalize_tag_path(part)]
    by_id = {node["id"]: node for node in doc.get("nodes", [])}
    parent_id = doc.get("root_id") or ""
    current: list[str] = []
    for part in category_path:
        current.append(part)
        existing_id = category_id_for_path(doc, current)
        if existing_id:
            parent_id = existing_id
            continue
        now = now_iso()
        node_id = mindmap_node_id("cat", doc.get("project", "collaborative"), *current)
        node = {
            "id": node_id,
            "type": "text",
            "kind": "text",
            "field_type": "frame" if len(current) == 1 else "paper-tag",
            "title": part,
            "parent_id": parent_id,
            "paper_id": "",
            "category_path": current.copy(),
            "summary": "",
            "text": "",
            "source": "manual-category",
            "source_refs": [],
            "children": [],
            "created_at": now,
            "updated_at": now,
        }
        doc.setdefault("nodes", []).append(node)
        if parent_id in by_id:
            by_id[parent_id].setdefault("children", []).append(node_id)
        by_id[node_id] = node
        parent_id = node_id
    return doc


def strip_reference_markup(text: str) -> str:
    text = html.unescape(str(text or ""))
    text = re.sub(r"</?(?:sup|sub)>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"([A-Za-z])-\s+([A-Za-z])", r"\1\2", text)
    return text


REFERENCE_SECTION_TITLES = {"references", "bibliography", "works cited", "literature cited"}


def normalized_reference_section_title(value: Any) -> str:
    text = strip_reference_markup(value)
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"^\d+(?:\.\d+)*\s*[.):-]?\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip(" .:-").lower()
    return text


def is_reference_section_path(section_path: Any) -> bool:
    if isinstance(section_path, str):
        section_items = [section_path]
    elif isinstance(section_path, list):
        section_items = section_path
    else:
        return False
    return any(normalized_reference_section_title(item) in REFERENCE_SECTION_TITLES for item in section_items)


def truncate_reference_body_at_next_marker(body: str, number: str) -> str:
    try:
        next_number = int(str(number).strip()) + 1
    except ValueError:
        return body
    marker_pattern = re.compile(rf"{re.escape(str(next_number))}\.\s+")
    for match in marker_pattern.finditer(body):
        tail = body[match.end() : match.end() + 100]
        if re.match(r"[A-Z][A-Za-z'’.-]+,\s*(?:[A-Z]\.?)+", tail):
            return body[: match.start()].strip(" .;,")
        if re.match(r"[A-Z][A-Za-z'’-]+(?:\s+[A-Z][A-Za-z'’-]+){0,5}\s+\((?:19|20)\d{2}\)", tail):
            return body[: match.start()].strip(" .;,")
    return body


def reference_cache_matches_parsed(parsed: dict[str, Any], cached: dict[str, Any]) -> bool:
    parsed_title = str(parsed.get("title") or "").strip()
    cached_title = str(cached.get("title") or cached.get("matched_title") or "").strip()
    if not parsed_title or not cached_title:
        return True
    if str(cached.get("source") or "") in {"", "parsed_reference"}:
        return True
    return reference_title_match_score(parsed_title, cached_title) >= 0.72


def parse_reference_entry(segment: dict[str, Any]) -> dict[str, Any] | None:
    raw = segment.get("markdown", "")
    clean = strip_reference_markup(raw)
    match = re.match(r"^(?:\[(\d+)\]|(\d+)\s*[.)])\s+(.+)$", clean)
    if not match:
        return None
    number = match.group(1) or match.group(2)
    body = truncate_reference_body_at_next_marker(match.group(3).strip(), number)
    leading_url_match = re.match(r"^(https?://\S+)\s+(.+)$", body)
    leading_url = leading_url_match.group(1).rstrip(".,);]") if leading_url_match else ""
    leading_url_tail = leading_url_match.group(2).strip(" .") if leading_url_match else ""
    year_match = re.search(r"\b(19|20)\d{2}\b", body)
    year = year_match.group(0) if year_match else ""
    authors = body[: year_match.start()].strip(" .") if year_match else ""
    authors = re.sub(r"[\s(]+$", "", authors)
    if leading_url:
        authors = ""
    after_year = body[year_match.end() :].strip(" .") if year_match else body
    after_year = re.sub(r"^[)\].,;:\s]+", "", after_year)
    doi_match = re.search(r"(?:doi:\s*|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/[^\s\"<>]+)", body, flags=re.I)
    doi = doi_match.group(1).rstrip(".,);]") if doi_match else ""
    url_match = re.search(r"https?://\S+", body)
    url = url_match.group(0).rstrip(".,);]") if url_match else (f"https://doi.org/{doi}" if doi else "")

    title = ""
    if after_year:
        split_match = re.split(
            r"\.\s+(?:In\s+|Proc\b|Proceedings\s+|ACM\b|IEEE\b|arXiv\b|Design Science\b|doi:|https?://|Technical Report\b)",
            after_year,
            maxsplit=1,
            flags=re.I,
        )
        title = split_match[0].strip(" .")
    if leading_url_tail and (not title or title.startswith(("http://", "https://"))):
        title = re.sub(r"\b(?:19|20)\d{2}\b.*$", "", leading_url_tail).strip(" .,-") or leading_url_tail
        title = re.sub(r"\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*$", "", title, flags=re.I).strip(" .,-")
    if not title:
        title = body[:180].strip(" .")
    venue = ""
    venue_match = re.search(r"\.\s+([^.]*(?:CHI|IUI|CSCW|UIST|DIS|Design Science|arXiv|IEEE|ACM)[^.]*)", body, flags=re.I)
    if venue_match:
        venue = venue_match.group(1).strip(" .")
    return {
        "id": number,
        "number": number,
        "segment_id": segment.get("id", ""),
        "raw": clean,
        "title": title,
        "authors": authors,
        "year": year,
        "venue": venue,
        "doi": doi,
        "url": url or leading_url,
        "pdf_url": leading_url if leading_url.lower().split("?", 1)[0].endswith(".pdf") else "",
        "open_access_pdf_url": leading_url if leading_url.lower().split("?", 1)[0].endswith(".pdf") else "",
        "abstract": "",
        "abstract_zh": "",
        "source": "parsed_reference",
    }


def load_reference_index(paper_dir: Path) -> dict[str, Any]:
    segments = load_segments(paper_dir)
    references: dict[str, dict[str, Any]] = {}
    for segment in segments:
        if not is_reference_section_path(segment.get("section_path", [])):
            continue
        parsed = parse_reference_entry(segment)
        if parsed:
            references[parsed["number"]] = parsed
    cache = read_json(paper_dir / "reference_cards.json", {"version": 1, "references": {}})
    for number, cached in cache.get("references", {}).items():
        parsed = references.get(str(number), {"id": str(number), "number": str(number)})
        if not reference_cache_matches_parsed(parsed, cached):
            references[str(number)] = parsed
            continue
        references[str(number)] = {**parsed, **cached, "id": str(number), "number": str(number)}
    return {"version": 1, "references": references}


def save_reference_card(paper_dir: Path, card: dict[str, Any]) -> None:
    cache_path = paper_dir / "reference_cards.json"
    cache = read_json(cache_path, {"version": 1, "references": {}})
    refs = cache.setdefault("references", {})
    number = str(card.get("number") or card.get("id") or "").strip()
    if not number:
        return
    refs[number] = {**refs.get(number, {}), **card, "id": number, "number": number, "updated_at": now_iso()}
    write_json(cache_path, cache)


def abstract_from_openalex_index(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        for position in positions:
            words.append((int(position), word))
    return " ".join(word for _, word in sorted(words)).strip()


def clean_abstract(text: str) -> str:
    return re.sub(r"^\s*abstract\s+", "", str(text or "").strip(), flags=re.I)


def http_json(url: str, timeout: int = 10) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "paper-reader-agent/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - user-triggered scholarly metadata lookup
        return json.loads(response.read().decode("utf-8"))


def http_text(url: str, timeout: int = 10) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "paper-reader-agent/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - user-triggered scholarly metadata lookup
        return response.read().decode("utf-8", errors="replace")


REFERENCE_TITLE_STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "in",
    "of",
    "on",
    "the",
    "to",
    "with",
}


def normalize_reference_title_for_match(value: Any) -> str:
    text = unicodedata.normalize("NFKC", html.unescape(str(value or ""))).casefold()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def reference_title_tokens(value: Any) -> set[str]:
    return {token for token in normalize_reference_title_for_match(value).split() if len(token) > 2 and token not in REFERENCE_TITLE_STOPWORDS}


def reference_title_match_score(query_title: Any, candidate_title: Any) -> float:
    query = normalize_reference_title_for_match(query_title)
    candidate = normalize_reference_title_for_match(candidate_title)
    if not query or not candidate:
        return 0.0
    query_key = normalize_title_key(query)
    candidate_key = normalize_title_key(candidate)
    if query_key == candidate_key or normalize_title_key_without_leading_articles(query) == normalize_title_key_without_leading_articles(candidate):
        return 1.0
    if query_key and candidate_key and (query_key in candidate_key or candidate_key in query_key):
        key_balance = min(len(query_key), len(candidate_key)) / max(1, max(len(query_key), len(candidate_key)))
        if key_balance >= 0.72:
            return 0.93
    ratio = difflib.SequenceMatcher(None, query, candidate).ratio()
    query_tokens = reference_title_tokens(query)
    candidate_tokens = reference_title_tokens(candidate)
    if not query_tokens or not candidate_tokens:
        return ratio
    containment = len(query_tokens & candidate_tokens) / max(1, min(len(query_tokens), len(candidate_tokens)))
    overlap = len(query_tokens & candidate_tokens) / max(1, len(query_tokens | candidate_tokens))
    token_balance = min(len(query_tokens), len(candidate_tokens)) / max(1, max(len(query_tokens), len(candidate_tokens)))
    containment_score = containment * 0.92 if token_balance >= 0.55 else 0.0
    return max(ratio, containment_score, overlap)


def best_title_matched_item(items: list[dict[str, Any]], query_title: str, title_key: str) -> dict[str, Any] | None:
    best_item: dict[str, Any] | None = None
    best_score = 0.0
    for item in items:
        candidate_title = item.get(title_key) or ""
        if isinstance(candidate_title, list):
            candidate_title = candidate_title[0] if candidate_title else ""
        score = reference_title_match_score(query_title, candidate_title)
        if score > best_score:
            best_item = item
            best_score = score
    if best_item and best_score >= 0.72:
        best_item = {**best_item, "_title_match_score": best_score}
        return best_item
    return None


def crossref_card(data: dict[str, Any]) -> dict[str, Any]:
    titles = data.get("title") if isinstance(data.get("title"), list) else []
    containers = data.get("container-title") if isinstance(data.get("container-title"), list) else []
    authors = []
    for author in data.get("author") or []:
        name = " ".join(str(author.get(key) or "").strip() for key in ("given", "family")).strip()
        if name:
            authors.append(name)
    date_parts = (data.get("published-print") or data.get("published-online") or data.get("issued") or {}).get("date-parts") or []
    year = str((date_parts[0] or [""])[0] or "") if date_parts else ""
    doi = str(data.get("DOI") or "").strip()
    return {
        "title": titles[0] if titles else "",
        "matched_title": titles[0] if titles else "",
        "title_match_score": data.get("_title_match_score", ""),
        "authors": ", ".join(authors),
        "year": year,
        "venue": containers[0] if containers else "",
        "doi": doi,
        "url": f"https://doi.org/{doi}" if doi else str(data.get("URL") or ""),
        "source": "crossref",
    }


def lookup_crossref_card(title: str) -> dict[str, Any]:
    query = urllib.parse.urlencode({"query.title": title, "rows": "5"})
    data = http_json(f"https://api.crossref.org/works?{query}")
    items = (data.get("message") or {}).get("items") or []
    best = best_title_matched_item(items, title, "title")
    return crossref_card(best) if best else {}


def arxiv_text(entry: ET.Element, name: str) -> str:
    node = entry.find(f"{{http://www.w3.org/2005/Atom}}{name}")
    return re.sub(r"\s+", " ", node.text or "").strip() if node is not None else ""


def arxiv_card(entry: ET.Element) -> dict[str, Any]:
    title = arxiv_text(entry, "title")
    summary = clean_abstract(arxiv_text(entry, "summary"))
    authors = []
    for author in entry.findall("{http://www.w3.org/2005/Atom}author"):
        name = author.find("{http://www.w3.org/2005/Atom}name")
        if name is not None and name.text:
            authors.append(re.sub(r"\s+", " ", name.text).strip())
    entry_id = arxiv_text(entry, "id")
    arxiv_id = entry_id.rstrip("/").rsplit("/", 1)[-1] if entry_id else ""
    pdf_url = ""
    for link in entry.findall("{http://www.w3.org/2005/Atom}link"):
        if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
            pdf_url = link.attrib.get("href", "")
            break
    if arxiv_id and not pdf_url:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    year = ""
    published = arxiv_text(entry, "published") or arxiv_text(entry, "updated")
    if published:
        year = normalize_year(published[:4])
    return {
        "title": title,
        "matched_title": title,
        "authors": ", ".join(authors),
        "year": year,
        "venue": "arXiv",
        "url": entry_id,
        "pdf_url": pdf_url,
        "open_access_pdf_url": pdf_url,
        "arxiv_id": arxiv_id,
        "abstract": summary,
        "source": "arxiv",
    }


def lookup_arxiv_card(title: str) -> dict[str, Any]:
    query_title = str(title or "").strip()
    if not query_title:
        return {}
    query = urllib.parse.urlencode({"search_query": f'ti:"{query_title}"', "start": "0", "max_results": "5"})
    text = http_text(f"https://export.arxiv.org/api/query?{query}", timeout=12)
    root = ET.fromstring(text)
    entries = [arxiv_card(entry) for entry in root.findall("{http://www.w3.org/2005/Atom}entry")]
    best = best_title_matched_item(entries, query_title, "title")
    return best if best else {}


def enrich_reference_online(card: dict[str, Any]) -> dict[str, Any]:
    title = str(card.get("title") or "").strip()
    doi = str(card.get("doi") or "").strip()
    enriched: dict[str, Any] = {}
    try:
        if doi:
            url = "https://api.semanticscholar.org/graph/v1/paper/" + urllib.parse.quote(
                f"DOI:{doi}", safe=""
            ) + "?fields=title,abstract,authors,year,venue,externalIds,url,openAccessPdf"
            data = http_json(url)
            candidate = semantic_scholar_card(data)
            if not title or reference_title_match_score(title, candidate.get("title") or "") >= 0.72:
                enriched = candidate
        elif title:
            query = urllib.parse.urlencode(
                {"query": title, "limit": "5", "fields": "title,abstract,authors,year,venue,externalIds,url,openAccessPdf"}
            )
            data = http_json(f"https://api.semanticscholar.org/graph/v1/paper/search?{query}")
            item = best_title_matched_item(data.get("data") or [], title, "title")
            if item:
                enriched = semantic_scholar_card(item)
    except Exception:  # noqa: BLE001
        enriched = {}
    if not enriched and (doi or title):
        try:
            if doi:
                query = urllib.parse.urlencode({"filter": f"doi:https://doi.org/{doi}", "per-page": "1"})
            else:
                query = urllib.parse.urlencode({"search": title, "per-page": "1"})
            data = http_json(f"https://api.openalex.org/works?{query}")
            item = best_title_matched_item(data.get("results") or [], title, "display_name")
            if item:
                enriched = openalex_card(item)
        except Exception:  # noqa: BLE001
            enriched = {}
    if title and not enriched.get("pdf_url"):
        try:
            arxiv = lookup_arxiv_card(title)
            for key, value in arxiv.items():
                if value and not enriched.get(key):
                    enriched[key] = value
        except Exception:  # noqa: BLE001
            pass
    if title and not enriched.get("doi"):
        try:
            crossref = lookup_crossref_card(title)
            for key, value in crossref.items():
                if value and not enriched.get(key):
                    enriched[key] = value
        except Exception:  # noqa: BLE001
            pass
    merged = {**card}
    for key, value in enriched.items():
        if value and not merged.get(key):
            merged[key] = value
    if enriched:
        merged["source"] = enriched.get("source", "online_metadata")
    return merged


def semantic_scholar_card(data: dict[str, Any]) -> dict[str, Any]:
    external = data.get("externalIds") or {}
    doi = external.get("DOI") or ""
    open_access = data.get("openAccessPdf") if isinstance(data.get("openAccessPdf"), dict) else {}
    arxiv_id = external.get("ArXiv") or ""
    pdf_url = open_access.get("url") or (f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else "")
    return {
        "title": data.get("title") or "",
        "matched_title": data.get("title") or "",
        "title_match_score": data.get("_title_match_score", ""),
        "authors": ", ".join(author.get("name", "") for author in data.get("authors", []) if author.get("name")),
        "year": str(data.get("year") or ""),
        "venue": data.get("venue") or "",
        "doi": doi,
        "url": data.get("url") or (f"https://doi.org/{doi}" if doi else ""),
        "semantic_scholar_url": data.get("url") or "",
        "pdf_url": pdf_url,
        "open_access_pdf_url": open_access.get("url") or "",
        "arxiv_id": arxiv_id,
        "abstract": clean_abstract(data.get("abstract") or ""),
        "source": "semantic_scholar",
    }


def openalex_card(data: dict[str, Any]) -> dict[str, Any]:
    authors = []
    for item in data.get("authorships", []):
        author = item.get("author") or {}
        if author.get("display_name"):
            authors.append(author["display_name"])
    doi_url = data.get("doi") or ""
    doi = doi_url.replace("https://doi.org/", "")
    primary_location = data.get("primary_location") if isinstance(data.get("primary_location"), dict) else {}
    return {
        "title": data.get("display_name") or "",
        "matched_title": data.get("display_name") or "",
        "title_match_score": data.get("_title_match_score", ""),
        "authors": ", ".join(authors),
        "year": str(data.get("publication_year") or ""),
        "venue": (primary_location.get("source") or {}).get("display_name") or "",
        "doi": doi,
        "url": doi_url or data.get("id") or "",
        "pdf_url": primary_location.get("pdf_url") or "",
        "open_access_pdf_url": primary_location.get("pdf_url") or "",
        "abstract": clean_abstract(abstract_from_openalex_index(data.get("abstract_inverted_index"))),
        "source": "openalex",
    }


def fetch_citation_info(metadata: dict[str, Any]) -> dict[str, Any]:
    title = str(metadata.get("title") or "").strip()
    doi = str(metadata.get("doi") or "").strip()
    if not title and not doi:
        return {"citation_count": "", "citation_source": "", "citation_url": "", "citation_error": "Missing title/DOI"}
    try:
        if doi:
            url = "https://api.semanticscholar.org/graph/v1/paper/" + urllib.parse.quote(
                f"DOI:{doi}", safe=""
            ) + "?fields=title,citationCount,influentialCitationCount,url,year,venue"
            data = http_json(url)
        else:
            query = urllib.parse.urlencode({"query": title, "limit": "1", "fields": "title,citationCount,influentialCitationCount,url,year,venue"})
            result = http_json(f"https://api.semanticscholar.org/graph/v1/paper/search?{query}")
            items = result.get("data") or []
            data = items[0] if items else {}
        if data:
            return {
                "citation_count": data.get("citationCount", ""),
                "influential_citation_count": data.get("influentialCitationCount", ""),
                "citation_source": "semantic_scholar",
                "citation_url": data.get("url") or "",
                "citation_error": "",
            }
    except Exception:  # noqa: BLE001
        pass
    try:
        if doi:
            query = urllib.parse.urlencode({"filter": f"doi:https://doi.org/{doi}", "per-page": "1"})
        else:
            query = urllib.parse.urlencode({"search": title, "per-page": "1"})
        result = http_json(f"https://api.openalex.org/works?{query}")
        items = result.get("results") or []
        if items:
            item = items[0]
            return {
                "citation_count": item.get("cited_by_count", ""),
                "influential_citation_count": "",
                "citation_source": "openalex",
                "citation_url": item.get("id") or "",
                "citation_error": "",
            }
    except Exception as exc:  # noqa: BLE001
        return {"citation_count": "", "citation_source": "", "citation_url": "", "citation_error": str(exc)}
    return {"citation_count": "", "citation_source": "", "citation_url": "", "citation_error": "No citation record found"}


def refresh_paper_citations(workspace: Path, paper_id: str, paper_dir: Path) -> dict[str, Any]:
    metadata = read_json(paper_dir / "metadata.json", {})
    citation_info = fetch_citation_info(metadata)
    metadata.update(citation_info)
    metadata["citation_updated_at"] = now_iso()
    metadata["updated_at"] = now_iso()
    write_json(paper_dir / "metadata.json", metadata)
    sync_library_from_metadata(workspace, paper_id, paper_dir, metadata)
    return metadata


YOUTUBE_SEARCH_ENDPOINT = "https://www.googleapis.com/youtube/v3/search"


def youtube_daily_limit() -> int:
    raw = os.environ.get("PAPER_READER_YOUTUBE_DAILY_LIMIT", "90")
    try:
        return max(0, min(100, int(raw)))
    except ValueError:
        return 90


def youtube_api_key() -> str:
    return os.environ.get("PAPER_READER_YOUTUBE_API_KEY") or os.environ.get("YOUTUBE_API_KEY", "")


def youtube_quota_path(workspace: Path) -> Path:
    return workspace / "youtube_quota.json"


def parse_iso_datetime(value: Any) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except Exception:  # noqa: BLE001
        return None


def youtube_quota_state(workspace: Path) -> dict[str, Any]:
    limit = youtube_daily_limit()
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=24)
    raw = read_json(youtube_quota_path(workspace), {"events": []})
    events = []
    for value in raw.get("events", []) if isinstance(raw, dict) else []:
        parsed = parse_iso_datetime(value)
        if parsed and parsed >= cutoff:
            events.append(parsed.isoformat())
    oldest = parse_iso_datetime(events[0]) if events else None
    reset_at = (oldest + dt.timedelta(hours=24)).isoformat() if oldest else ""
    return {"limit": limit, "used": len(events), "remaining": max(0, limit - len(events)), "events": events, "reset_at": reset_at, "window_hours": 24}


def reserve_youtube_search_quota(workspace: Path) -> dict[str, Any]:
    state = youtube_quota_state(workspace)
    if state["limit"] <= 0 or state["remaining"] <= 0:
        write_json(youtube_quota_path(workspace), {"events": state["events"], "updated_at": now_iso(), "limit": state["limit"]})
        raise RuntimeError(f"YouTube daily free quota guard reached ({state['used']}/{state['limit']} searches in the last 24h).")
    events = [*state["events"], dt.datetime.now(dt.timezone.utc).isoformat()]
    write_json(youtube_quota_path(workspace), {"events": events, "updated_at": now_iso(), "limit": state["limit"], "window_hours": 24})
    return youtube_quota_state(workspace)


def youtube_search_query(metadata: dict[str, Any]) -> str:
    title = str(metadata.get("title") or "").strip()
    extras = [metadata.get("venue") or metadata.get("journal") or "", normalize_year(metadata.get("year") or metadata.get("publication_year") or "")]
    return " ".join([title, *[str(item).strip() for item in extras if str(item).strip()], "paper presentation"]).strip()


def youtube_search_queries(metadata: dict[str, Any], max_queries: int = 3) -> list[str]:
    title = str(metadata.get("title") or "").strip()
    if not title:
        return []
    compact_title = re.sub(r"[\u2018\u2019'\"“”]", "", title)
    subtitle = title.split(":", 1)[0].strip() if ":" in title else ""
    candidates = [
        f'"{title}"',
        compact_title,
        f'{subtitle} {metadata.get("venue") or metadata.get("journal") or ""} paper presentation'.strip() if subtitle else "",
        youtube_search_query(metadata),
    ]
    seen: set[str] = set()
    queries = []
    for candidate in candidates:
        clean = re.sub(r"\s+", " ", str(candidate or "").strip())
        if clean and clean not in seen:
            seen.add(clean)
            queries.append(clean)
        if len(queries) >= max(1, max_queries):
            break
    return queries


def video_title_contains_full_paper_title(paper_title: str, video_title: str) -> bool:
    title_key = normalize_title_key(paper_title)
    video_key = normalize_title_key(video_title)
    return title_key_is_usable(title_key) and title_key in video_key


def text_token_set(text: str) -> set[str]:
    stop = {"paper", "presentation", "preview", "video", "talk", "chi", "acm", "sigchi", "the", "and", "with", "for", "from", "that", "this"}
    return {token for token in re.findall(r"[a-z0-9]{3,}|[\u4e00-\u9fff]{2,}", str(text or "").casefold()) if token not in stop}


def video_relevance_score(query_title: str, video_title: str, channel_title: str = "") -> float:
    query_tokens = text_token_set(query_title)
    video_tokens = text_token_set(video_title)
    if not query_tokens or not video_tokens:
        return 0.0
    overlap = len(query_tokens & video_tokens) / max(1, len(query_tokens))
    reverse_overlap = len(query_tokens & video_tokens) / max(1, len(video_tokens))
    title_key = normalize_title_key(query_title)
    video_key = normalize_title_key(video_title)
    exact_bonus = 0.45 if title_key and (title_key in video_key or video_key in title_key) else 0.0
    channel_bonus = 0.12 if re.search(r"\b(chi|acm|uist|cscw|iui|sigchi|conference)\b", channel_title or "", flags=re.I) else 0.0
    return round(min(1.0, overlap * 0.62 + reverse_overlap * 0.2 + exact_bonus + channel_bonus), 3)


def youtube_min_relevance_score() -> float:
    try:
        return max(0.0, min(1.0, float(os.environ.get("PAPER_READER_YOUTUBE_MIN_SCORE", "0.38"))))
    except ValueError:
        return 0.38


def search_youtube_videos(workspace: Path, metadata: dict[str, Any], max_results: int = 5) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    key = youtube_api_key()
    if not key:
        raise RuntimeError("YouTube API key is not configured. Set YOUTUBE_API_KEY or PAPER_READER_YOUTUBE_API_KEY and restart the app.")
    queries = youtube_search_queries(metadata)
    if not queries:
        raise RuntimeError("Missing paper title for YouTube search.")
    videos_by_id: dict[str, dict[str, Any]] = {}
    quota = youtube_quota_state(workspace)
    for query in queries:
        quota = reserve_youtube_search_quota(workspace)
        params = urllib.parse.urlencode(
            {
                "part": "snippet",
                "type": "video",
                "maxResults": str(max(1, min(10, int(max_results or 5)))),
                "order": "relevance",
                "q": query,
                "key": key,
                "fields": "items(id/videoId,snippet/title,snippet/channelTitle,snippet/publishedAt,snippet/thumbnails/default/url),nextPageToken",
            }
        )
        data = http_json(f"{YOUTUBE_SEARCH_ENDPOINT}?{params}", timeout=12)
        for item in data.get("items", []):
            video_id = ((item.get("id") or {}).get("videoId") or "").strip()
            snippet = item.get("snippet") or {}
            if not video_id:
                continue
            title = str(snippet.get("title") or "").strip()
            channel = str(snippet.get("channelTitle") or "").strip()
            paper_title = str(metadata.get("title") or "")
            if not video_title_contains_full_paper_title(paper_title, title):
                continue
            score = video_relevance_score(paper_title, title, channel)
            existing = videos_by_id.get(video_id)
            if existing and existing.get("score", 0) >= score:
                continue
            videos_by_id[video_id] = {
                "source": "youtube",
                "title": title,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "video_id": video_id,
                "channel": channel,
                "published_at": snippet.get("publishedAt") or "",
                "thumbnail": (((snippet.get("thumbnails") or {}).get("default") or {}).get("url") or ""),
                "score": score,
                "query": query,
            }
    min_score = youtube_min_relevance_score()
    videos = [video for video in videos_by_id.values() if video.get("score", 0) >= min_score]
    videos.sort(key=lambda item: item.get("score", 0), reverse=True)
    return videos[:max_results], quota


def refresh_paper_videos(workspace: Path, paper_id: str, paper_dir: Path, force: bool = False) -> dict[str, Any]:
    metadata = read_json(paper_dir / "metadata.json", {})
    if metadata.get("video_search_status") == "ready" and metadata.get("video_links") and not force:
        return metadata
    if not youtube_api_key():
        metadata.update(
            {
                "video_links": metadata.get("video_links", []),
                "video_search_status": "not_configured",
                "video_search_error": "Set YOUTUBE_API_KEY or PAPER_READER_YOUTUBE_API_KEY and restart the app.",
                "video_search_updated_at": now_iso(),
                "youtube_quota": youtube_quota_state(workspace),
                "updated_at": now_iso(),
            }
        )
        write_json(paper_dir / "metadata.json", metadata)
        sync_library_from_metadata(workspace, paper_id, paper_dir, metadata)
        return metadata
    try:
        videos, quota = search_youtube_videos(workspace, metadata)
        existing_links = metadata.get("video_links", []) if isinstance(metadata.get("video_links"), list) else []
        manual_links = [
            link
            for link in existing_links
            if isinstance(link, dict) and ("manual" in str(link.get("query") or "").lower() or str(link.get("source") or "").lower() == "manual")
        ]
        seen_urls = {str(video.get("url") or "") for video in videos}
        merged_videos = [*videos, *[link for link in manual_links if str(link.get("url") or "") not in seen_urls]]
        metadata.update(
            {
                "video_links": merged_videos,
                "video_search_status": "ready" if merged_videos else "no_results",
                "video_search_error": "",
                "video_search_updated_at": now_iso(),
                "youtube_quota": quota,
                "updated_at": now_iso(),
            }
        )
    except Exception as exc:  # noqa: BLE001
        status = "quota_limited" if "quota" in str(exc).lower() else "failed"
        metadata.update(
            {
                "video_links": metadata.get("video_links", []),
                "video_search_status": status,
                "video_search_error": str(exc),
                "video_search_updated_at": now_iso(),
                "youtube_quota": youtube_quota_state(workspace),
                "updated_at": now_iso(),
            }
        )
    write_json(paper_dir / "metadata.json", metadata)
    sync_library_from_metadata(workspace, paper_id, paper_dir, metadata)
    return metadata


METADATA_UPDATE_FIELDS = {
    "title",
    "author",
    "authors",
    "institution",
    "institutions",
    "journal",
    "venue",
    "publication_year",
    "year",
    "abstract",
    "abstract_zh",
    "research_question",
    "method",
    "result",
    "discussion",
    "doi",
    "url",
    "pdf_url",
    "open_access_pdf_url",
    "semantic_scholar_url",
    "arxiv_id",
    "source_url",
    "source_page_url",
    "reference_pdf_error",
    "importance",
    "importance_tags",
    "preview_image",
    "preview_image_alt",
    "project",
    "projects",
    "project_colors",
    "read_status",
    "status",
    "tags",
    "tag_colors",
    "processing_mode",
    "reading_mode",
    "processing_status",
    "processing_error",
    "citation_count",
    "citation_error",
    "influential_citation_count",
    "citation_source",
    "citation_url",
    "citation_updated_at",
    "video_links",
    "video_search_status",
    "video_search_error",
    "video_search_updated_at",
    "youtube_quota",
    "title_key",
    "source_pdf_name",
    "source_type",
    "title_source",
    "title_locked",
    "agent_analysis_status",
}


def apply_paper_metadata_update(workspace: Path, paper_id: str, paper_dir: Path, data: dict[str, Any], *, generate_pdf_preview: bool = False) -> dict[str, Any]:
    with write_lock_for(paper_dir / "metadata.json"):
        return _apply_paper_metadata_update(workspace, paper_id, paper_dir, data, generate_pdf_preview=generate_pdf_preview)


def _apply_paper_metadata_update(workspace: Path, paper_id: str, paper_dir: Path, data: dict[str, Any], *, generate_pdf_preview: bool = False) -> dict[str, Any]:
    metadata = read_json(paper_dir / "metadata.json", {})
    if metadata.get("feishu", {}).get("record_id"):
        overrides = set(metadata.get("feishu_local_overrides") or [])
        overrides.update(key for key in feishu_metadata.FIELD_MAPPING if key in data and data[key] != metadata.get(key))
        metadata["feishu_local_overrides"] = sorted(overrides)
    if "importance" in data:
        metadata.update(importance_fields(data.get("importance")))
    for key, value in data.items():
        if key not in METADATA_UPDATE_FIELDS or key == "importance":
            continue
        if key in {"year", "publication_year"}:
            metadata[key] = normalize_year(value)
        elif key == "tags":
            metadata[key] = normalize_tag_paths(value)
        elif key == "projects":
            metadata[key] = normalize_project_list(value)
        elif key == "importance_tags":
            metadata[key] = normalize_string_list(value)
        else:
            metadata[key] = value
    if "projects" in data:
        projects = normalize_project_list(metadata.get("projects", []))
        metadata["projects"] = projects
        metadata["project"] = projects[0] if projects else ""
    elif "project" in data:
        projects = metadata_projects(metadata)
        metadata["projects"] = projects
    if data.get("title"):
        metadata["title_source"] = data.get("title_source") or "user"
    if "read_status" in data or "status" in data:
        metadata["read_status_source"] = "user"
    metadata["updated_at"] = now_iso()
    write_json(paper_dir / "metadata.json", metadata)
    sync_library_from_metadata(workspace, paper_id, paper_dir, metadata, generate_pdf_preview=generate_pdf_preview)
    return metadata


def feishu_config() -> dict[str, Any]:
    base_token = env_value("PAPER_READER_FEISHU_BASE_TOKEN")
    table_id = env_value("PAPER_READER_FEISHU_TABLE_ID")
    return {
        "enabled": bool(base_token and table_id),
        "auto_sync": env_value("PAPER_READER_FEISHU_AUTO_SYNC", default="0").lower() in {"1", "true", "yes"},
        "base_token": base_token, "table_id": table_id,
        "publication_enabled": bool(base_token and table_id),
        "fields": {key: value[0] for key, value in feishu_metadata.FIELD_MAPPING.items()},
    }


def feishu_settings() -> tuple[str, str, str]:
    config = feishu_config()
    if not config["enabled"]:
        raise ValueError("Configure PAPER_READER_FEISHU_BASE_TOKEN and PAPER_READER_FEISHU_TABLE_ID first.")
    feishu_metadata.validate_ids(config["base_token"], config["table_id"])
    return config["base_token"], config["table_id"], env_value("PAPER_READER_LARK_CLI")


def publication_settings() -> dict[str, Any]:
    from reading_archive import TABLE_COLUMN_NAMES

    base_token, table_id, executable = feishu_settings()
    return {
        "mode": "table",
        "base_token": base_token, "table_id": table_id, "executable": executable,
        "text_fields": {
            key: env_value(variable, default=TABLE_COLUMN_NAMES[key])
            for key, variable in (
                ("my-notes", "PAPER_READER_FEISHU_NOTES_FIELD"),
                ("ai-discussions", "PAPER_READER_FEISHU_DISCUSSIONS_FIELD"),
                ("accepted-definitions", "PAPER_READER_FEISHU_DEFINITIONS_FIELD"),
                ("other-material", "PAPER_READER_FEISHU_MATERIALS_FIELD"),
            )
        },
        "archive_field": env_value("PAPER_READER_FEISHU_ARCHIVE_FIELD", default="阅读档案"),
        "backup_field": env_value("PAPER_READER_FEISHU_BACKUP_FIELD", default="阅读数据备份"),
        "parent_token": env_value("PAPER_READER_FEISHU_ARCHIVE_PARENT"),
    }


def sync_feishu_metadata(workspace: Path, paper_id: str, paper_dir: Path, data: dict[str, Any], *,
                        source_record: dict[str, Any] | None = None) -> dict[str, Any]:
    base_token, table_id, executable = feishu_settings()
    automatic = bool(data.get("automatic"))
    before = read_json(paper_dir / "metadata.json", {}, strict=True)
    link = before.get("feishu") or {}
    record_id = str(data.get("record_id") or link.get("record_id") or "")
    if automatic and data.get("record_id") and data["record_id"] != link.get("record_id"):
        raise ValueError("Automatic synchronization cannot select an arbitrary Feishu record.")
    if link.get("record_id") and (link.get("base_token") != base_token or link.get("table_id") != table_id):
        raise ValueError("This paper is linked to a different Feishu table. Confirm a new association before changing it.")
    if not record_id:
        search = feishu_metadata.search_records(base_token, table_id, before.get("title") or paper_id, executable=executable)
        matches = [record for record in search["records"]
                   if feishu_metadata.title_key(record["title"]) == feishu_metadata.title_key(before.get("title"))]
        if len(matches) != 1 or search["has_more"]:
            return {"ok": True, "status": "needs_match", "candidates": search["records"], "has_more": search["has_more"]}
        record_id = matches[0]["record_id"]
    source = source_record if source_record is not None else feishu_metadata.read_record(base_token, table_id, record_id, executable=executable)
    if source.get("record_id") != record_id:
        raise ValueError("The Feishu snapshot does not belong to the selected record.")
    with write_lock_for(paper_dir / "metadata.json"):
        if not paper_dir.is_dir():
            raise FileNotFoundError("Paper was removed during Feishu synchronization.")
        metadata = read_json(paper_dir / "metadata.json", {}, strict=True)
        current_link = metadata.get("feishu") or {}
        if current_link != link:
            raise ValueError("The Feishu association changed while fetching. Retry using the current association.")
        if automatic and not link and metadata.get("title") != before.get("title"):
            raise ValueError("The local title changed while matching. Retry with the current title.")
        cache = read_json(paper_dir / "feishu_metadata.json", {}, strict=True)
        if cache and cache.get("record_id") != record_id:
            raise ValueError("An existing Feishu snapshot belongs to another record; automatic replacement is disabled.")
        original = cache.get("previous_metadata") or {key: metadata.get(key) for key in feishu_metadata.FIELD_MAPPING}
        overrides = set(metadata.get("feishu_local_overrides") or [])
        if metadata.get("title_locked") or metadata.get("title_source") == "user":
            overrides.add("title")
        changed_during_fetch = {key for key in feishu_metadata.FIELD_MAPPING if metadata.get(key) != before.get(key)}
        overrides.update(changed_during_fetch)
        applied = []
        for key, value in source["metadata"].items():
            if value.strip() and key not in overrides:
                if metadata.get(key) != value:
                    applied.append(key)
                metadata[key] = value
        if source["metadata"]["title"].strip() and "title" not in overrides:
            metadata["title_source"] = "feishu"
            metadata["title_key"] = normalize_title_key(metadata["title"])
        metadata["feishu"] = {
            "base_token": base_token, "table_id": table_id, "record_id": record_id,
            "synced_at": now_iso(), "field_sources": source["field_sources"],
            "url": f"https://feishu.cn/base/{base_token}?table={table_id}&record={record_id}",
        }
        metadata["feishu_local_overrides"] = sorted(overrides)
        snapshot = {**source, "base_token": base_token, "table_id": table_id,
                    "synced_at": metadata["feishu"]["synced_at"], "previous_metadata": original}
        write_json(paper_dir / "feishu_metadata.json", snapshot)
        if applied or not link:
            metadata["updated_at"] = now_iso()
        write_json(paper_dir / "metadata.json", metadata)
        sync_library_from_metadata(workspace, paper_id, paper_dir, metadata, generate_pdf_preview=False)
    return {"ok": True, "status": "synced", "metadata": metadata, "feishu_metadata": snapshot,
            "applied_fields": applied, "local_overrides": sorted(overrides)}


def linked_feishu_paper(workspace: Path, base_token: str, table_id: str, record_id: str) -> dict[str, Any] | None:
    matches = [paper for paper in read_library_index(workspace).get("papers", [])
               if all((paper.get("feishu") or {}).get(key) == value for key, value in {
                   "base_token": base_token, "table_id": table_id, "record_id": record_id,
               }.items())]
    if len(matches) > 1:
        raise ValueError("More than one local paper is linked to this Feishu record. Resolve the duplicate before importing.")
    return matches[0] if matches else None


def preview_feishu_record(workspace: Path, reference: str) -> dict[str, Any]:
    base_token, table_id, executable = feishu_settings()
    record_id = feishu_metadata.resolve_record_reference(base_token, table_id, reference, executable=executable)
    source = feishu_metadata.read_intake_record(base_token, table_id, record_id, executable=executable)
    paper = linked_feishu_paper(workspace, base_token, table_id, record_id)
    return {"ok": True, "record": source, "local_paper": paper}


def feishu_intake_response(workspace: Path, paper_id: str, metadata: dict[str, Any], *,
                           reused: bool, local_source: bool) -> dict[str, Any]:
    paper = next((item for item in read_library_index(workspace).get("papers", []) if item.get("id") == paper_id), None)
    if paper is None:
        raise RuntimeError("The imported paper is missing from the local index. Keep its files and recover the index before retrying.")
    return {"ok": True, "paper_id": paper_id, "metadata": metadata, "reused": reused,
            "used_local_pdf": local_source, "paper": paper,
            "feishu_metadata": read_json(paper_record_dir(workspace, paper) / "feishu_metadata.json", {}, strict=True)}


def register_feishu_pdf(workspace: Path, source: dict[str, Any], attachment: dict[str, Any], pdf_path: Path, *,
                        local_source: bool, linked: dict[str, Any] | None) -> dict[str, Any]:
    base_token, table_id, _executable = feishu_settings()
    with pdf_path.open("rb") as stream:
        if not pdf_bytes_are_recognizable(stream.read(1024)):
            raise ValueError("The selected file is not a PDF. No existing reading data was replaced.")
    digest = file_hash(pdf_path)
    record_id = source["record_id"]
    title = source["metadata"].get("title") or Path(attachment["name"]).stem
    cloud_title_key = feishu_metadata.title_key(source["metadata"].get("title"))
    target_id = f"feishu-{record_id}"
    candidates = [paper for paper in read_library_index(workspace).get("papers", [])
                  if paper.get("source_pdf_sha256") == digest or str(paper.get("id", "")).endswith(f"-{digest[:12]}")
                  or paper.get("id") == target_id or (linked and paper.get("id") == linked["id"])
                  or (cloud_title_key and feishu_metadata.title_key(paper.get("title")) == cloud_title_key)]
    identical = [paper for paper in candidates
                 if (paper_record_dir(workspace, paper) / "original.pdf").is_file()
                 and file_hash(paper_record_dir(workspace, paper) / "original.pdf") == digest]
    if len(identical) > 1:
        raise ValueError("This PDF matches multiple local papers. Resolve the duplicate before linking another record.")
    existing = identical[0] if identical else None
    if linked and (not existing or existing["id"] != linked["id"]):
        linked_dir = paper_record_dir(workspace, linked)
        if (linked_dir / "original.pdf").exists() or nonempty_segment_count(linked_dir):
            raise ValueError("The selected PDF differs from the linked local source. Existing annotations were not replaced.")
        existing = linked
    if not existing:
        duplicate = next((paper for paper in candidates
                          if cloud_title_key and feishu_metadata.title_key(paper.get("title")) == cloud_title_key), None)
        if duplicate:
            raise ValueError("A local paper has the same title, but its PDF identity is not verified. Use its metadata panel to confirm the association first.")
        target_dir = workspace / "papers" / target_id
        if target_dir.exists():
            raise ValueError("An unindexed import directory already exists for this record. Recover it before retrying; no files were replaced.")
        result = register_paper_in_library(
            workspace, pdf_path, paper_id=target_id, title=title, title_source="feishu" if cloud_title_key else "filename",
            pdf_digest=digest, match_title=False, generate_pdf_preview=False, enrich_citation=False,
        )
        if result.get("duplicate") or not result.get("ok"):
            raise ValueError("This PDF conflicts with an existing paper. No replacement was performed.")
        paper_id = result["paper_id"]
        paper_dir = workspace / "papers" / paper_id
    else:
        paper_id = existing["id"]
        paper_dir = paper_record_dir(workspace, existing)
        metadata = read_json(paper_dir / "metadata.json", {}, strict=True)
        link = metadata.get("feishu") or {}
        if link and any(link.get(key) != value for key, value in {
            "base_token": base_token, "table_id": table_id, "record_id": record_id,
        }.items()):
            raise ValueError("This local PDF is linked to another Feishu record. Re-association must be explicit.")
        if not (paper_dir / "original.pdf").exists():
            shutil.copy2(pdf_path, paper_dir / "original.pdf")
    fields = {
        "source_pdf": "original.pdf", "source_pdf_sha256": digest,
        "feishu_attachment": {
            **attachment, "sha256": digest,
            "verification": "user_selected_local_pdf" if local_source else "downloaded_feishu_attachment",
        },
    }
    if not existing:
        fields.update(source_pdf_name=attachment["name"], original_path=str(pdf_path if local_source else paper_dir / "original.pdf"))
    save_processing_fields(workspace, paper_id, paper_dir, fields)
    sync_feishu_metadata(workspace, paper_id, paper_dir, {"record_id": record_id}, source_record=source)
    metadata = prepare_pdf_brief_then_background(workspace, paper_id, paper_dir, {}, mode="deep")
    return feishu_intake_response(workspace, paper_id, metadata, reused=bool(existing), local_source=local_source)


def intake_feishu_paper(workspace: Path, data: dict[str, Any]) -> dict[str, Any]:
    base_token, table_id, executable = feishu_settings()
    record_id = str(data.get("record_id") or "").strip()
    feishu_metadata.validate_ids(base_token, table_id, record_id)
    if not record_id:
        raise ValueError("Select a Feishu record before queuing a paper.")
    source = feishu_metadata.read_intake_record(base_token, table_id, record_id, executable=executable)
    attachment = next((item for item in source["attachments"] if item["file_token"] == data.get("file_token")), None)
    if attachment is None:
        raise ValueError("Select one of this record's current PDF attachments. Refresh the preview if it changed.")
    local_path = str(data.get("local_pdf_path") or "").strip()
    with write_lock_for(workspace / "feishu-intake"):
        linked = linked_feishu_paper(workspace, base_token, table_id, record_id)
        if linked:
            paper_id = linked["id"]
            paper_dir = paper_record_dir(workspace, linked)
            metadata = read_json(paper_dir / "metadata.json", {}, strict=True)
            previous = metadata.get("feishu_attachment") or {}
            if previous and previous.get("file_token") != attachment["file_token"]:
                raise ValueError("Feishu has a different PDF attachment now. The existing local source and notes were kept; do not replace them implicitly.")
            pdf_path = paper_dir / "original.pdf"
            if not local_path and previous and pdf_path.is_file():
                if file_hash(pdf_path) != previous.get("sha256"):
                    raise ValueError("The local PDF changed since import. Verify it before reusing the Feishu association.")
                sync_feishu_metadata(workspace, paper_id, paper_dir, {"record_id": record_id}, source_record=source)
                metadata = prepare_pdf_brief_then_background(workspace, paper_id, paper_dir, {}, mode="deep")
                return feishu_intake_response(workspace, paper_id, metadata, reused=True, local_source=True)
        if local_path:
            pdf_path = Path(local_path).expanduser().resolve(strict=True)
            if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
                raise ValueError("Choose an existing local PDF file, not a folder.")
            if attachment.get("size") and pdf_path.stat().st_size != attachment["size"]:
                raise ValueError("The local PDF size does not match the selected cloud attachment. Download the cloud PDF or choose the correct local file.")
            return register_feishu_pdf(workspace, source, attachment, pdf_path, local_source=True, linked=linked)
        with tempfile.TemporaryDirectory(prefix="paper-reader-feishu-") as temporary:
            pdf_path = feishu_metadata.download_record_attachment(
                base_token, table_id, record_id, attachment["file_token"], Path(temporary) / "attachment.pdf",
                executable=executable,
            )
            if attachment.get("size") and pdf_path.stat().st_size != attachment["size"]:
                raise ValueError("The downloaded PDF size differs from the selected attachment. Refresh the preview and retry.")
            return register_feishu_pdf(workspace, source, attachment, pdf_path, local_source=False, linked=linked)


def aggregate_notes(workspace: Path) -> list[dict[str, Any]]:
    library = load_library(workspace)
    notes: list[dict[str, Any]] = []
    for paper in library.get("papers", []):
        paper_id = str(paper.get("id") or "")
        if not paper_id:
            continue
        paper_dir = workspace / paper.get("paper_dir", "")
        annotations = read_json(paper_dir / "annotations.json", {"annotations": []}).get("annotations", [])
        metadata = read_json(paper_dir / "metadata.json", {})
        title = metadata.get("title") or paper.get("title") or paper_id
        projects = metadata_projects({**paper, **metadata})
        project_colors = metadata.get("project_colors") or paper.get("project_colors") or {}
        for annotation in annotations:
            if not isinstance(annotation, dict):
                continue
            notes.append(
                {
                    **annotation,
                    "paper_id": paper_id,
                    "paper_title": title,
                    "paper_venue": metadata.get("venue") or paper.get("venue", ""),
                    "paper_year": metadata.get("year") or paper.get("year", ""),
                    "paper_project": projects[0] if projects else "",
                    "paper_projects": projects,
                    "paper_project_colors": project_colors,
                    "source_scope": "paper",
                }
            )
        thinking = load_thinking(paper_dir)
        thinking_blocks = {str(block.get("id") or ""): block for block in thinking.get("blocks", []) if isinstance(block, dict)}
        for annotation in thinking.get("annotations", []):
            if not isinstance(annotation, dict):
                continue
            block_id = str(annotation.get("block_id") or "").strip()
            if not block_id:
                continue
            block = thinking_blocks.get(block_id, {})
            block_title = "Paper Brief" if block_id == PAPER_BRIEF_BLOCK_ID else (block.get("title") or block.get("prompt") or "AI output")
            notes.append(
                {
                    **annotation,
                    "paper_id": paper_id,
                    "paper_title": title,
                    "paper_venue": metadata.get("venue") or paper.get("venue", ""),
                    "paper_year": metadata.get("year") or paper.get("year", ""),
                    "paper_project": projects[0] if projects else "",
                    "paper_projects": projects,
                    "paper_project_colors": project_colors,
                    "segment_id": block_id,
                    "source_scope": "thinking",
                    "thinking_block_id": block_id,
                    "thinking_block_title": block_title,
                }
            )
    notes.sort(key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
    return notes


def get_reference_card(paper_dir: Path, number: str, enrich: bool = True) -> dict[str, Any] | None:
    reference_index = load_reference_index(paper_dir).get("references", {})
    card = reference_index.get(str(number))
    if not card:
        return None
    if enrich and not card.get("abstract"):
        enriched = enrich_reference_online(card)
        if enriched != card:
            save_reference_card(paper_dir, enriched)
        card = enriched
    return card


def reference_paper_id(card: dict[str, Any]) -> str:
    basis = card.get("doi") or card.get("title") or card.get("raw") or card.get("number") or "reference"
    digest = hashlib.sha256(str(basis).encode("utf-8")).hexdigest()[:12]
    return f"{slugify(str(card.get('title') or 'reference'), 'reference')}-{digest}"


def reference_pdf_url(card: dict[str, Any]) -> str:
    for key in ("pdf_url", "open_access_pdf_url", "arxiv_pdf_url"):
        value = str(card.get(key) or "").strip()
        if value.startswith(("http://", "https://")):
            return value
    value = str(card.get("url") or "").strip()
    if value.startswith(("http://", "https://")) and value.lower().split("?", 1)[0].endswith(".pdf"):
        return value
    return ""


def merge_reference_metadata(metadata: dict[str, Any], card: dict[str, Any], *, parent_paper_id: str = "", parent_title: str = "") -> dict[str, Any]:
    title = card.get("title") or metadata.get("title") or f"Reference {card.get('number', '')}".strip()
    metadata.setdefault("id", metadata.get("id", ""))
    metadata.update(
        {
            "title": metadata.get("title") or title,
            "title_key": metadata.get("title_key") or normalize_title_key(title),
            "authors": metadata.get("authors") or card.get("authors", ""),
            "venue": metadata.get("venue") or card.get("venue", ""),
            "year": metadata.get("year") or card.get("year", ""),
            "abstract": metadata.get("abstract") or card.get("abstract", ""),
            "abstract_zh": metadata.get("abstract_zh") or card.get("abstract_zh", ""),
            "source_reference": metadata.get("source_reference") or card.get("raw", ""),
            "source_parent_paper_id": metadata.get("source_parent_paper_id") or parent_paper_id,
            "source_parent_paper_title": metadata.get("source_parent_paper_title") or parent_title,
            "doi": metadata.get("doi") or card.get("doi", ""),
            "url": metadata.get("url") or card.get("url", ""),
            "semantic_scholar_url": metadata.get("semantic_scholar_url") or card.get("semantic_scholar_url", ""),
            "pdf_url": metadata.get("pdf_url") or reference_pdf_url(card),
            "open_access_pdf_url": metadata.get("open_access_pdf_url") or card.get("open_access_pdf_url", ""),
            "arxiv_id": metadata.get("arxiv_id") or card.get("arxiv_id", ""),
        }
    )
    return metadata


def attach_reference_pdf_to_paper(workspace: Path, paper_id: str, paper_dir: Path, metadata: dict[str, Any], card: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    pdf_url = reference_pdf_url(card)
    if not pdf_url:
        return metadata, {"pdf_attached": False, "pdf_url": "", "pdf_error": ""}
    if (paper_dir / "original.pdf").exists():
        metadata.update({"pdf_url": metadata.get("pdf_url") or pdf_url, "updated_at": now_iso()})
        return metadata, {"pdf_attached": True, "pdf_url": pdf_url, "pdf_error": "", "pdf_existing": True}
    try:
        filename, content = download_pdf_bytes(pdf_url, {"Referer": str(card.get("url") or card.get("semantic_scholar_url") or pdf_url)})
    except Exception as exc:  # noqa: BLE001
        metadata.update({"pdf_url": pdf_url, "reference_pdf_error": str(exc), "updated_at": now_iso()})
        write_json(paper_dir / "metadata.json", metadata)
        sync_library_from_metadata(workspace, paper_id, paper_dir, metadata, generate_pdf_preview=False)
        return metadata, {"pdf_attached": False, "pdf_url": pdf_url, "pdf_error": str(exc)}
    (paper_dir / "original.pdf").write_bytes(content)
    metadata.update(
        {
            "source_pdf": "original.pdf",
            "source_pdf_name": filename,
            "source_type": "reference_pdf",
            "pdf_url": pdf_url,
            "source_url": pdf_url,
            "source_page_url": card.get("url") or card.get("semantic_scholar_url") or "",
            "reference_pdf_error": "",
            "processing_mode": metadata.get("processing_mode", "library-only"),
            "reading_mode": metadata.get("reading_mode", metadata.get("processing_mode", "library-only")),
            "processing_status": metadata.get("processing_status", "not_processed"),
            "updated_at": now_iso(),
        }
    )
    write_json(paper_dir / "metadata.json", metadata)
    sync_library_from_metadata(workspace, paper_id, paper_dir, metadata, generate_pdf_preview=False)
    return metadata, {"pdf_attached": True, "pdf_url": pdf_url, "pdf_error": ""}


def add_reference_to_library(
    workspace: Path,
    card: dict[str, Any],
    parent_paper_id: str,
    tags: list[str] | None = None,
    projects: list[str] | None = None,
    importance: Any = "",
) -> dict[str, Any]:
    paper_id = reference_paper_id(card)
    title = card.get("title") or f"Reference {card.get('number', '')}".strip()
    duplicate = find_duplicate_paper_by_title(workspace, title, exclude_paper_id=paper_id)
    if duplicate:
        duplicate_id = str(duplicate.get("id") or "")
        duplicate_dir = paper_record_dir(workspace, duplicate)
        if duplicate_id and duplicate_dir.exists() and duplicate_can_accept_pdf(workspace, duplicate) and reference_pdf_url(card):
            metadata = read_json(duplicate_dir / "metadata.json", {})
            parent_record = find_paper_record(workspace, parent_paper_id) or {}
            metadata = merge_reference_metadata(metadata, card, parent_paper_id=parent_paper_id, parent_title=parent_record.get("title") or parent_paper_id)
            if str(importance or "").strip():
                metadata.update(importance_fields(importance))
            if tags:
                metadata["tags"] = normalize_tag_paths([*normalize_tag_paths(metadata.get("tags", [])), *tags])
            clean_projects = normalize_project_list([*metadata_projects(metadata), *(projects or [])])
            metadata["projects"] = clean_projects
            metadata["project"] = clean_projects[0] if clean_projects else ""
            write_json(duplicate_dir / "metadata.json", metadata)
            metadata, pdf_info = attach_reference_pdf_to_paper(workspace, duplicate_id, duplicate_dir, metadata, card)
            if pdf_info.get("pdf_attached"):
                metadata = prepare_pdf_brief_then_background(workspace, duplicate_id, duplicate_dir, {}, mode="deep")
                pdf_info["processing_background"] = "started"
            return {"paper_id": duplicate_id, "metadata": metadata, "attached_to_existing": True, **pdf_info}
        return {**duplicate_paper_response(workspace, title, str(card.get("raw") or "reference"), duplicate), "paper_id": duplicate.get("id", "")}
    paper_dir = workspace / "papers" / paper_id
    paper_dir.mkdir(parents=True, exist_ok=True)
    abstract = card.get("abstract") or ""
    abstract_zh = card.get("abstract_zh") or ""
    clean_projects = normalize_project_list(projects or [])
    parent_record = find_paper_record(workspace, parent_paper_id) or {}
    parent_title = parent_record.get("title") or parent_paper_id
    metadata = merge_reference_metadata(
        {
        "id": paper_id,
        "title": title,
        "title_key": normalize_title_key(title),
        "title_source": "reference",
        "source_type": "reference",
        "status": "unread",
        "read_status": "unread",
        **importance_fields(importance),
        "tags": [str(tag).strip() for tag in (tags or []) if str(tag).strip()],
        "projects": clean_projects,
        "project": clean_projects[0] if clean_projects else "",
        "agent_analysis_status": "reference_card",
        "paper_brief_status": "needs_pdf",
        "updated_at": now_iso(),
        },
        card,
        parent_paper_id=parent_paper_id,
        parent_title=parent_title,
    )
    write_json(paper_dir / "metadata.json", metadata)
    blocks = [f"# {title}"]
    if card.get("authors"):
        blocks.append(str(card["authors"]))
    if abstract:
        blocks.append("## Abstract\n" + abstract)
    if abstract_zh:
        blocks.append("## 中文摘要\n" + abstract_zh)
    if card.get("raw"):
        blocks.append("## Source Reference\n" + card["raw"])
    segments, outline = build_segments("\n\n".join(blocks))
    write_json(paper_dir / "segments.json", segments)
    write_json(paper_dir / "outline.json", {"outline": outline, "core_locations": []})
    if not (paper_dir / "annotations.json").exists():
        write_json(paper_dir / "annotations.json", {"annotations": []})
    write_reader_bundle(paper_dir, metadata, segments, "reference-card")
    export_notes_and_annotated(paper_dir)
    sync_library_from_metadata(workspace, paper_id, paper_dir, metadata)
    metadata, pdf_info = attach_reference_pdf_to_paper(workspace, paper_id, paper_dir, metadata, card)
    if not pdf_info.get("pdf_attached") and not pdf_info.get("pdf_url"):
        lookup_result = find_and_attach_pdf_to_existing_paper(workspace, paper_id, paper_dir, force=True)
        metadata = lookup_result.get("metadata") or metadata
        pdf_info = {
            "pdf_attached": lookup_result.get("pdf_attached", False),
            "pdf_url": lookup_result.get("pdf_url", ""),
            "pdf_error": lookup_result.get("pdf_error", ""),
            "pdf_existing": lookup_result.get("pdf_existing", False),
        }
    if pdf_info.get("pdf_attached"):
        metadata = prepare_pdf_brief_then_background(workspace, paper_id, paper_dir, {}, mode="deep")
        pdf_info["processing_background"] = "started"
    return {"paper_id": paper_id, "metadata": metadata, **pdf_info}


def metadata_card_for_pdf_lookup(metadata: dict[str, Any]) -> dict[str, Any]:
    card = {
        "title": metadata.get("title") or "",
        "authors": metadata.get("authors") or metadata.get("author") or "",
        "year": metadata.get("year") or metadata.get("publication_year") or "",
        "venue": metadata.get("venue") or metadata.get("journal") or "",
        "doi": metadata.get("doi") or "",
        "url": metadata.get("url") or "",
        "pdf_url": metadata.get("pdf_url") or "",
        "open_access_pdf_url": metadata.get("open_access_pdf_url") or "",
        "semantic_scholar_url": metadata.get("semantic_scholar_url") or "",
        "arxiv_id": metadata.get("arxiv_id") or "",
        "abstract": metadata.get("abstract") or "",
        "abstract_zh": metadata.get("abstract_zh") or "",
        "raw": metadata.get("source_reference") or "",
        "source": metadata.get("citation_source") or metadata.get("source_type") or "metadata",
    }
    source_reference = str(metadata.get("source_reference") or "").strip()
    parsed = parse_reference_entry({"id": "source_reference", "markdown": source_reference}) if source_reference else None
    if parsed:
        current_score = reference_title_match_score(parsed.get("title"), card.get("title"))
        if current_score < 0.72 or len(str(parsed.get("title") or "")) < len(str(card.get("title") or "")):
            for key in ("title", "authors", "year", "venue", "doi", "url", "raw"):
                if parsed.get(key):
                    card[key] = parsed[key]
    return card


def merge_enriched_card_into_metadata(metadata: dict[str, Any], card: dict[str, Any]) -> dict[str, Any]:
    current_title = str(metadata.get("title") or "").strip()
    card_title = str(card.get("matched_title") or card.get("title") or "").strip()
    if card_title and (
        not current_title
        or str(metadata.get("title_source") or "") in {"", "reference", "metadata", "library"}
        or reference_title_match_score(current_title, card_title) >= 0.72
    ):
        metadata["title"] = card_title
        metadata["title_key"] = normalize_title_key(card_title)
        metadata["title_source"] = "online_metadata"
    for key in ("authors", "year", "venue", "doi", "url", "semantic_scholar_url", "pdf_url", "open_access_pdf_url", "arxiv_id", "abstract", "abstract_zh"):
        value = card.get(key)
        if value and (key in {"pdf_url", "open_access_pdf_url", "semantic_scholar_url", "arxiv_id"} or not metadata.get(key)):
            metadata[key] = value
    metadata["metadata_lookup_source"] = card.get("source") or metadata.get("metadata_lookup_source") or "online_metadata"
    metadata["metadata_lookup_updated_at"] = now_iso()
    metadata["updated_at"] = now_iso()
    return metadata


def find_and_attach_pdf_to_existing_paper(workspace: Path, paper_id: str, paper_dir: Path, *, force: bool = False) -> dict[str, Any]:
    metadata = read_json(paper_dir / "metadata.json", {})
    card = metadata_card_for_pdf_lookup(metadata)
    if force or not reference_pdf_url(card):
        card = enrich_reference_online(card)
    metadata = merge_enriched_card_into_metadata(metadata, card)
    write_json(paper_dir / "metadata.json", metadata)
    sync_library_from_metadata(workspace, paper_id, paper_dir, metadata, generate_pdf_preview=False)
    if (paper_dir / "original.pdf").exists():
        metadata.update({"reference_pdf_error": "", "updated_at": now_iso()})
        write_json(paper_dir / "metadata.json", metadata)
        sync_library_from_metadata(workspace, paper_id, paper_dir, metadata, generate_pdf_preview=False)
        return {"ok": True, "paper_id": paper_id, "metadata": metadata, "pdf_attached": True, "pdf_existing": True, "pdf_url": reference_pdf_url(card), "pdf_error": "", "card": card}
    metadata, pdf_info = attach_reference_pdf_to_paper(workspace, paper_id, paper_dir, metadata, card)
    if pdf_info.get("pdf_attached"):
        metadata = prepare_pdf_brief_then_background(workspace, paper_id, paper_dir, {}, mode="deep")
        pdf_info["processing_background"] = "started"
    elif not pdf_info.get("pdf_url"):
        metadata.update({"reference_pdf_error": "No open PDF URL found from Semantic Scholar, OpenAlex, Crossref, or arXiv.", "updated_at": now_iso()})
        write_json(paper_dir / "metadata.json", metadata)
        sync_library_from_metadata(workspace, paper_id, paper_dir, metadata, generate_pdf_preview=False)
        pdf_info["pdf_error"] = metadata["reference_pdf_error"]
    return {"ok": True, "paper_id": paper_id, "metadata": metadata, "card": card, **pdf_info}


def find_mineru() -> str | None:
    explicit = os.environ.get("PAPER_READER_MINERU")
    if explicit:
        return explicit
    found = shutil.which("mineru")
    if found:
        return found
    wrapper = Path.home() / ".local" / "bin" / "mineru.bat"
    if wrapper.exists():
        return str(wrapper)
    return None


def run_mineru(pdf_path: Path, output_dir: Path, backend: str, method: str, lang: str, start: int | None, end: int | None) -> Path:
    mineru = find_mineru()
    if not mineru:
        raise RuntimeError("MinerU command not found. Set PAPER_READER_MINERU or put mineru on PATH.")
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [mineru, "-p", str(pdf_path), "-o", str(output_dir), "-b", backend, "-m", method, "-l", lang]
    if start is not None:
        cmd.extend(["-s", str(start)])
    if end is not None:
        cmd.extend(["-e", str(end)])
    subprocess.run(cmd, check=True)
    candidates = sorted(output_dir.rglob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not candidates:
        raise RuntimeError(f"MinerU finished but no Markdown file was found under {output_dir}")
    return candidates[0]


def block_type(block: str) -> tuple[str, int | None]:
    first = block.lstrip().splitlines()[0] if block.strip() else ""
    heading = re.match(r"^(#{1,6})\s+(.+)$", first)
    if heading:
        return "heading", len(heading.group(1))
    if first.startswith("```"):
        return "code", None
    if first.startswith(">"):
        return "quote", None
    if first.startswith("|") or re.search(r"<\s*table[\s>]", block, flags=re.I):
        return "table", None
    if re.match(r"^\s*([-*+]\s+|\d+[.)]\s+)", first):
        return "list", None
    return "paragraph", None


class MarkdownTableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[dict[str, Any]]] = []
        self.current_row: list[dict[str, Any]] | None = None
        self.current_cell: dict[str, Any] | None = None
        self.capture_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        clean_tag = tag.lower()
        if clean_tag == "tr":
            self.current_row = []
        elif clean_tag in {"td", "th"} and self.current_row is not None:
            attr_map = {key.lower(): value for key, value in attrs if key}
            self.current_cell = {"tag": clean_tag, "attrs": attr_map, "parts": []}
            self.capture_cell = True
        elif self.capture_cell and clean_tag in {"br", "p", "div"} and self.current_cell is not None:
            self.current_cell["parts"].append(" ")

    def handle_endtag(self, tag: str) -> None:
        clean_tag = tag.lower()
        if clean_tag in {"td", "th"} and self.current_cell is not None and self.current_row is not None:
            self.current_row.append(self.current_cell)
            self.current_cell = None
            self.capture_cell = False
        elif clean_tag == "tr" and self.current_row is not None:
            self.rows.append(self.current_row)
            self.current_row = None

    def handle_data(self, data: str) -> None:
        if self.capture_cell and self.current_cell is not None:
            self.current_cell["parts"].append(data)


def clean_table_cell_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\b([A-Za-z]{2,})-\s+([A-Za-z]{2,})\b", r"\1\2", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text


def table_cell_text(cell: dict[str, Any]) -> str:
    return clean_table_cell_text("".join(str(part) for part in cell.get("parts", [])))


def raw_table_cell_text(cell: dict[str, Any]) -> str:
    text = html.unescape("".join(str(part) for part in cell.get("parts", [])))
    return re.sub(r"\s+", " ", text).strip()


def repair_two_column_wrapped_rows(rows: list[list[dict[str, Any]]]) -> list[list[dict[str, Any]]]:
    if len(rows) < 2:
        return rows
    header = [table_cell_text(cell).casefold() for cell in rows[0]]
    if len(header) != 2 or "code" not in header[0] or "description" not in header[1]:
        return rows
    repaired: list[list[dict[str, Any]]] = [rows[0]]
    for row in rows[1:]:
        if len(row) == 2:
            first = raw_table_cell_text(row[0])
            second = raw_table_cell_text(row[1])
            if re.fullmatch(r"[a-z]{2,12}", first) and re.match(r"^\d+(?:\.\d+)+\s+", second):
                split = re.match(r"^(?P<prefix>\d+(?:\.\d+)+\s+.*?\s+)(?P<broken>[A-Za-z]+)-\s*(?P<description>[A-Z][a-z].*)$", second)
                if split:
                    label = clean_table_cell_text(split.group("prefix") + split.group("broken") + first)
                    description = clean_table_cell_text(split.group("description"))
                    row[0]["parts"] = [label]
                    row[1]["parts"] = [description]
        repaired.append(row)
    return repaired


def render_html_table(rows: list[list[dict[str, Any]]]) -> str:
    rendered_rows: list[str] = []
    for row in rows:
        cells: list[str] = []
        for cell in row:
            tag = "th" if str(cell.get("tag") or "td").lower() == "th" else "td"
            attrs = cell.get("attrs") if isinstance(cell.get("attrs"), dict) else {}
            attr_text = ""
            for attr_name in ("rowspan", "colspan"):
                attr_value = str(attrs.get(attr_name) or "").strip()
                if attr_value.isdigit() and int(attr_value) > 1:
                    attr_text += f' {attr_name}="{html.escape(attr_value)}"'
            cells.append(f"<{tag}{attr_text}>{inline_markdown_to_html(table_cell_text(cell))}</{tag}>")
        rendered_rows.append("<tr>" + "".join(cells) + "</tr>")
    return "<table>" + "".join(rendered_rows) + "</table>"


def normalize_html_tables(markdown: str) -> str:
    def replace_table(match: re.Match[str]) -> str:
        if re.search(r"<\s*img\b", match.group(0), flags=re.I):
            return match.group(0)
        parser = MarkdownTableHTMLParser()
        parser.feed(match.group(0))
        rows = repair_two_column_wrapped_rows(parser.rows)
        return render_html_table(rows) if rows else match.group(0)

    return re.sub(r"<\s*table[\s\S]*?<\s*/\s*table\s*>", replace_table, str(markdown or ""), flags=re.I)


def normalize_math_fragment(text: str) -> str:
    fragment = str(text or "")
    fragment = re.sub(r"\\\s+([A-Za-z]+)", r"\\\1", fragment)
    fragment = re.sub(r"\{\s*\}", "{}", fragment)
    fragment = re.sub(r"\\(left|right)\s*", r"\\\1", fragment)
    return fragment.strip()


PDF_WORD_SPACE_FIXES = {
    "alter natives": "alternatives",
    "ana lyst": "analyst",
    "ana lysts": "analysts",
    "ana lysis": "analysis",
    "ana lytical": "analytical",
    "articu late": "articulate",
    "articu lating": "articulating",
    "assump tions": "assumptions",
    "behav ior": "behavior",
    "behav iors": "behaviors",
    "cogni tive": "cognitive",
    "cohe r ent": "coherent",
    "commu nication": "communication",
    "commu nications": "communications",
    "computa tional": "computational",
    "contex tual": "contextual",
    "cre ative": "creative",
    "cre ativity": "creativity",
    "docu ment": "document",
    "docu menting": "documenting",
    "exter nalize": "externalize",
    "exter nalizing": "externalizing",
    "fig ure": "figure",
    "im plicit": "implicit",
    "im plicitly": "implicitly",
    "in terpretation": "interpretation",
    "in terpretations": "interpretations",
    "inter pretation": "interpretation",
    "inter pretations": "interpretations",
    "inter pretive": "interpretive",
    "inter face": "interface",
    "inter action": "interaction",
    "inter actions": "interactions",
    "inter vention": "intervention",
    "inter ventions": "interventions",
    "know ledge": "knowledge",
    "meth od": "method",
    "meth ods": "methods",
    "narra tive": "narrative",
    "par ticipant": "participant",
    "par ticipants": "participants",
    "prom ising": "promising",
    "ques tion": "question",
    "ques tions": "questions",
    "ratio nale": "rationale",
    "rea soning": "reasoning",
    "reso lution": "resolution",
    "scaf folding": "scaffolding",
    "seman tic": "semantic",
    "sense making": "sensemaking",
    "struc ture": "structure",
    "struc tures": "structures",
    "sys tem": "system",
    "sys tems": "systems",
    "un examined": "unexamined",
    "accountabil ity": "accountability",
    "evo lution": "evolution",
    "in tervention": "intervention",
    "in terventions": "interventions",
    "visu alization": "visualization",
}


def preserve_word_case(source: str, replacement: str) -> str:
    if source.isupper():
        return replacement.upper()
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def repair_pdf_word_spacing(text: str) -> str:
    repaired = str(text or "")
    for broken, fixed in PDF_WORD_SPACE_FIXES.items():
        pattern = re.compile(rf"\b{re.escape(broken)}\b", re.IGNORECASE)
        repaired = pattern.sub(lambda match: preserve_word_case(match.group(0), fixed), repaired)
    return repaired


def cleanup_markdown_artifacts(markdown: str) -> str:
    text = str(markdown or "")

    def replace_dollar_math(match: re.Match[str]) -> str:
        return "$" + normalize_math_fragment(match.group(1)) + "$"

    text = re.sub(r"\$([^$\n]+)\$", replace_dollar_math, text)
    text = re.sub(r"(?<=\d)\s+(?=\d)", "", text)
    text = re.sub(r"\b([A-Za-z])-\s+([A-Za-z])\b", r"\1\2", text)
    text = repair_pdf_word_spacing(text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text


def split_numbered_heading_line(line: str) -> tuple[str, str] | None:
    stripped = str(line or "").strip()
    match = re.match(r"^(\d{1,2}(?:\.\d{1,2}){1,5})\s+(.+)$", stripped)
    if not match:
        return None
    section_number = match.group(1)
    body = match.group(2).strip()
    if not body:
        return None
    title = body
    tail = ""
    sentence = re.match(r"^(.{4,120}?\.)\s+([A-Z][\s\S]*)$", body)
    if sentence:
        candidate_title = sentence.group(1).strip()
        if not re.search(r"\b(?:e\.g|i\.e|vs|fig|figure|table|et al)\.$", candidate_title, flags=re.I):
            title = candidate_title.rstrip(".").strip()
            tail = sentence.group(2).strip()
    elif len(body) > 150 or re.search(r"[.!?]\s+", body):
        return None
    level = max(2, min(6, 2 + section_number.count(".")))
    heading = f"{'#' * level} {section_number} {title}".strip()
    return heading, tail


def split_markdown_blocks(markdown: str) -> list[str]:
    markdown = normalize_html_tables(cleanup_markdown_artifacts(normalize_pdf_fallback_markdown(markdown)))
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[str] = []
    current: list[str] = []
    in_code = False

    def flush() -> None:
        nonlocal current
        text = "\n".join(current).strip("\n")
        if text.strip():
            blocks.append(text)
        current = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            current.append(line)
            in_code = not in_code
            if not in_code:
                flush()
            continue
        if in_code:
            current.append(line)
            continue
        if not stripped:
            flush()
            continue
        if re.match(r"^#{1,6}\s+", stripped):
            flush()
            current.append(line)
            flush()
            continue
        numbered_heading = split_numbered_heading_line(line)
        if numbered_heading:
            flush()
            heading, tail = numbered_heading
            current.append(heading)
            flush()
            if tail:
                current.append(tail)
            continue
        current.append(line)
    flush()
    return blocks


def is_pdf_fallback_markdown(markdown: str) -> bool:
    if "pypdfium2 fallback" in markdown:
        return True
    page_headings = re.findall(r"(?m)^## Page \d+\s*$", markdown)
    real_headings = re.findall(r"(?m)^#{1,3}\s+(?!Page \d+\s*$).+", markdown)
    return len(page_headings) >= 3 and len(real_headings) <= 2


def clean_pdf_fallback_line(line: str) -> str:
    line = line.replace("\x02", "").replace("\u00ad", "")
    line = re.sub(r"\s+", " ", line).strip()
    line = re.sub(r"([A-Za-z])-\s+([A-Za-z])", r"\1\2", line)
    line = repair_pdf_word_spacing(line)
    return line


def is_pdf_running_header(line: str) -> bool:
    if not line:
        return True
    if re.fullmatch(r"\d+", line):
        return True
    lowered = line.lower()
    if "creative commons" in lowered or "copyright held" in lowered or "acm isbn" in lowered:
        return True
    if lowered.startswith("https://doi.org/"):
        return True
    if " chi " in f" {lowered} " and "barcelona" in lowered and len(line) < 180:
        return True
    if "supporting reflexivity and rigor" in lowered and "chi" in lowered:
        return True
    return False


def pdf_heading_level(line: str) -> int | None:
    if line in {"Abstract", "CCS Concepts", "Keywords", "ACM Reference Format:", "Acknowledgments", "References"}:
        return 2
    if re.fullmatch(r"\d+\s+[A-Z][^.;]{2,120}", line):
        return 2
    if re.fullmatch(r"\d+\.\d+(?:\.\d+)?\s+[A-Z][^.;]{2,140}", line):
        return 3
    if re.fullmatch(r"A\.\d+(?:\.\d+)?\s+[A-Z][^.;]{2,140}", line):
        return 3
    return None


def should_continue_pdf_heading(line: str) -> bool:
    if not line or len(line) > 80:
        return False
    if pdf_heading_level(line) or re.match(r"^(Figure|Table)\s+\d+[:.]", line) or re.match(r"^\[\d+\]", line):
        return False
    if line.endswith(('.', ',', ';', ':')):
        return False
    return True


def should_flush_pdf_paragraph(current: str, next_line: str) -> bool:
    if len(current) > 1400:
        return True
    if len(current) < 260:
        return False
    if not re.search(r"[.!?][\]\)]?$", current):
        return False
    if re.match(r"^(However|Furthermore|Moreover|Instead|Finally|While|This|These|The|Our|We|In|Participants|Results)\b", next_line):
        return True
    return bool(re.match(r"^[A-Z][a-z]", next_line))


def split_pdf_fallback_lines(lines: list[str]) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []

    def flush() -> None:
        nonlocal current
        if current:
            blocks.append(" ".join(current).strip())
            current = []

    index = 0
    while index < len(lines):
        line = lines[index]
        if is_pdf_running_header(line):
            index += 1
            continue

        numbered_heading = split_numbered_heading_line(line)
        if numbered_heading:
            flush()
            heading, tail = numbered_heading
            blocks.append(heading)
            if tail:
                current.append(tail)
            index += 1
            continue

        heading_level = pdf_heading_level(line)
        if heading_level:
            flush()
            heading_lines = [line]
            index += 1
            while index < len(lines) and should_continue_pdf_heading(lines[index]) and len(" ".join(heading_lines)) < 120:
                heading_lines.append(lines[index])
                index += 1
            blocks.append("#" * heading_level + " " + " ".join(heading_lines))
            continue

        if re.match(r"^(Figure|Table)\s+\d+[:.]", line):
            flush()
            caption = [line]
            index += 1
            while index < len(lines) and not pdf_heading_level(lines[index]) and not re.match(r"^(Figure|Table)\s+\d+[:.]", lines[index]) and len(" ".join(caption)) < 1000:
                caption.append(lines[index])
                index += 1
                if re.search(r"[.!?]$", caption[-1]) and len(" ".join(caption)) > 220:
                    break
            blocks.append(" ".join(caption))
            continue

        if re.match(r"^\[\d+\]", line):
            flush()
            reference = [line]
            index += 1
            while index < len(lines) and not re.match(r"^\[\d+\]", lines[index]) and not pdf_heading_level(lines[index]):
                reference.append(lines[index])
                index += 1
            blocks.append(" ".join(reference))
            continue

        if current and should_flush_pdf_paragraph(" ".join(current), line):
            flush()
        current.append(line)
        index += 1
    flush()
    return blocks


def normalize_pdf_fallback_markdown(markdown: str) -> str:
    if not is_pdf_fallback_markdown(markdown):
        return markdown
    markdown = markdown.replace("\r\n", "\n").replace("\r", "\n")
    title_match = re.search(r"(?m)^#\s+(.+)$", markdown)
    title = title_match.group(1).strip() if title_match else "Extracted Paper"
    pages = re.split(r"(?m)^## Page \d+\s*$", markdown)
    normalized = [f"# {title}"]
    for page in pages[1:]:
        lines = [clean_pdf_fallback_line(line) for line in page.splitlines()]
        lines = [line for line in lines if line and not line.startswith("<!--")]
        normalized.extend(split_pdf_fallback_lines(lines))
    return "\n\n".join(block for block in normalized if block.strip()) + "\n"


def inline_markdown_to_html(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href=\"\2\" target=\"_blank\" rel=\"noreferrer\">\1</a>", escaped)
    return autolink_plain_urls_and_dois(escaped)


def autolink_plain_urls_and_dois(html_text: str) -> str:
    def link_token(token: str) -> str:
        trailing = ""
        while token and token[-1] in ".,);]":
            trailing = token[-1] + trailing
            token = token[:-1]
        href = token if re.match(r"https?://", token, flags=re.I) else f"https://doi.org/{token}"
        return f'<a href="{html.escape(href)}" target="_blank" rel="noreferrer">{html.escape(token)}</a>{html.escape(trailing)}'

    def link_plain_part(part: str) -> str:
        return re.sub(r"(?<![\w/])(https?://[^\s<]+|10\.\d{4,9}/[^\s<]+)", lambda match: link_token(match.group(1)), part)

    parts = re.split(r"(<a\b[^>]*>.*?</a>|<[^>]+>)", html_text, flags=re.I)
    return "".join(part if part.startswith("<") else link_plain_part(part) for part in parts)


def markdown_block_to_html(block: str, kind: str, level: int | None) -> str:
    lines = block.splitlines()
    if kind == "heading" and level:
        text = re.sub(r"^#{1,6}\s+", "", lines[0]).strip()
        return f"<h{level}>{inline_markdown_to_html(text)}</h{level}>"
    if kind == "code":
        body = "\n".join(line for line in lines if not line.strip().startswith("```"))
        return f"<pre><code>{html.escape(body)}</code></pre>"
    if kind == "quote":
        body = "\n".join(re.sub(r"^>\s?", "", line) for line in lines)
        return f"<blockquote>{inline_markdown_to_html(body)}</blockquote>"
    if kind == "list":
        items = []
        for line in lines:
            item = re.sub(r"^\s*([-*+]\s+|\d+[.)]\s+)", "", line).strip()
            if item:
                items.append(f"<li>{inline_markdown_to_html(item)}</li>")
        return "<ul>" + "".join(items) + "</ul>"
    if kind == "table":
        html_table = re.search(r"<\s*table[\s\S]*?<\s*/\s*table\s*>", block, flags=re.I)
        if html_table:
            caption = clean_table_cell_text(block[: html_table.start()])
            if re.search(r"<\s*img\b", html_table.group(0), flags=re.I):
                table_html = html_table.group(0)
                if caption:
                    return f"<figure class=\"paper-table\"><figcaption>{inline_markdown_to_html(caption)}</figcaption>{table_html}</figure>"
                return table_html
            parser = MarkdownTableHTMLParser()
            parser.feed(html_table.group(0))
            table_html = render_html_table(repair_two_column_wrapped_rows(parser.rows)) if parser.rows else html_table.group(0)
            if caption:
                return f"<figure class=\"paper-table\"><figcaption>{inline_markdown_to_html(caption)}</figcaption>{table_html}</figure>"
            return table_html
        rows = []
        for line in lines:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
                continue
            rows.append("<tr>" + "".join(f"<td>{inline_markdown_to_html(cell)}</td>" for cell in cells) + "</tr>")
        return "<table>" + "".join(rows) + "</table>"
    text = "\n".join(lines)
    return f"<p>{inline_markdown_to_html(text).replace(chr(10), '<br>')}</p>"


def extract_heading_text(block: str) -> str:
    first = block.splitlines()[0].strip()
    return re.sub(r"^#{1,6}\s+", "", first).strip()


def infer_heading_level(title: str, markdown_level: int | None) -> int:
    try:
        level = int(markdown_level or 1)
    except (TypeError, ValueError):
        level = 1
    level = max(1, min(6, level))
    match = re.match(r"^\s*(\d{1,2}(?:\.\d{1,2}){0,5})(?=\s|[:.)、-]|$)", str(title or ""))
    if not match:
        return level
    section_number = match.group(1)
    try:
        first_number = int(section_number.split(".", 1)[0])
    except ValueError:
        return level
    if first_number < 1 or first_number > 50:
        return level
    if "." not in section_number and level <= 1:
        return level
    return max(1, min(6, 2 + section_number.count(".")))


def build_segments(markdown: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blocks = split_markdown_blocks(markdown)
    segments: list[dict[str, Any]] = []
    outline: list[dict[str, Any]] = []
    section_stack: list[dict[str, Any]] = []
    for index, block in enumerate(blocks, start=1):
        kind, level = block_type(block)
        segment_id = f"p-{index:04d}"
        segment_level = level
        if kind == "heading" and level:
            title = extract_heading_text(block)
            segment_level = infer_heading_level(title, level)
            section_stack = [item for item in section_stack if item["level"] < segment_level]
            section_stack.append({"level": segment_level, "title": title, "segment_id": segment_id})
            outline.append({"id": segment_id, "level": segment_level, "title": title, "kind": "heading"})
        segment = {
            "id": segment_id,
            "kind": kind,
            "level": segment_level,
            "markdown": block,
            "html": markdown_block_to_html(block, kind, segment_level),
            "translation": "",
            "section_path": [item["title"] for item in section_stack],
        }
        segments.append(segment)
    return segments, outline


def make_reader_markdown(segments: list[dict[str, Any]], source_name: str) -> str:
    lines = [
        "<!-- Generated by paper-reader-agent. Edit translations and notes freely; keep anchors stable. -->",
        f"<!-- Source: {source_name} -->",
        "",
    ]
    for segment in segments:
        segment_id = segment["id"]
        lines.append(f'<a id="{segment_id}"></a>')
        lines.append("")
        lines.append(segment["markdown"].rstrip())
        lines.append("")
        translation = translation_text_for_segment(segment)
        if translation.strip() or translation_source_for_segment(segment):
            lines.append(f"<!-- zh:{segment_id} -->")
            if translation.strip():
                lines.append(f"> 中文：{translation}")
            lines.append(f"<!-- /zh:{segment_id} -->")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def source_block_type(segment: dict[str, Any]) -> str:
    kind = str(segment.get("kind") or "paragraph")
    markdown = str(segment.get("markdown") or "")
    plain = markdown_plain_text(markdown)
    if kind == "table" or re.search(r"<\s*table[\s>]", markdown, flags=re.I):
        return "table"
    if re.search(r"!\[[^\]]*\]\([^)]+\)", markdown):
        return "figure"
    if re.match(r"^(?:fig(?:ure)?\.?|table)\s*\d+\b", plain, flags=re.I):
        return "caption"
    if kind in {"heading", "list", "quote", "code"}:
        return kind
    return "paragraph"


def source_block_prefix(block_type: str) -> str:
    if block_type == "figure":
        return "F"
    if block_type == "table":
        return "T"
    if block_type == "caption":
        return "C"
    return "S"


def source_block_page_hint(markdown: str) -> int | None:
    text = str(markdown or "")
    for pattern in (
        r"<!--\s*page\s*[:=]\s*(\d+)\s*-->",
        r"^#{1,6}\s+Page\s+(\d+)\b",
        r"\bp(?:age)?[._ -]?(\d{1,4})\b",
    ):
        match = re.search(pattern, text, flags=re.I | re.M)
        if match:
            try:
                return int(match.group(1))
            except (TypeError, ValueError):
                return None
    return None


def source_refs_from_text(text: str) -> list[str]:
    refs: list[str] = []
    for prefix, pattern in (("F", r"\bfig(?:ure)?\.?\s*(\d+)"), ("T", r"\btable\s*(\d+)")):
        for match in re.finditer(pattern, str(text or ""), flags=re.I):
            ref = f"{prefix}{int(match.group(1)):03d}"
            if ref not in refs:
                refs.append(ref)
    return refs


def image_info_from_markdown(markdown: str) -> dict[str, str]:
    match = re.search(r"!\[([^\]]*)\]\(([^)]+)\)", str(markdown or ""))
    if not match:
        return {}
    return {"alt": match.group(1).strip(), "image_path": match.group(2).strip()}


def caption_number_from_text(text: str, label: str) -> str:
    pattern = r"\bfig(?:ure)?\.?\s*(\d+)" if label == "figure" else r"\btable\s*(\d+)"
    match = re.search(pattern, str(text or ""), flags=re.I)
    return match.group(1) if match else ""


def extract_math_fragments_for_source_map(text: str) -> list[dict[str, str]]:
    raw = str(text or "")
    patterns = [
        (r"\$\$([\s\S]+?)\$\$", "display"),
        (r"\\\[([\s\S]+?)\\\]", "display"),
        (r"\\\(([^\n]+?)\\\)", "inline"),
        (r"(?<!\\)\$([^$\n]+?)(?<!\\)\$", "inline"),
        (r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}([\s\S]+?)\\end\{\1\}", "display"),
    ]
    fragments: list[dict[str, str]] = []
    seen: set[str] = set()
    for pattern, mode in patterns:
        for match in re.finditer(pattern, raw, flags=re.I):
            expression = match.group(2) if match.lastindex and match.lastindex >= 2 else match.group(1)
            expression = str(expression or "").strip()
            if not expression or expression in seen:
                continue
            seen.add(expression)
            fragments.append({"mode": mode, "latex": expression[:1200]})
    return fragments[:24]


def build_source_map(metadata: dict[str, Any], segments: list[dict[str, Any]], source_name: str) -> dict[str, Any]:
    counters = {"S": 0, "C": 0, "F": 0, "T": 0}
    blocks: list[dict[str, Any]] = []
    pages: dict[int, list[str]] = {}
    figures: list[dict[str, Any]] = []
    tables: list[dict[str, Any]] = []
    current_page: int | None = None
    previous_text_id = ""
    for order, segment in enumerate(segments, start=1):
        markdown = str(segment.get("markdown") or "")
        block_type = source_block_type(segment)
        prefix = source_block_prefix(block_type)
        counters[prefix] += 1
        source_id = f"{prefix}{counters[prefix]:03d}"
        page_hint = source_block_page_hint(markdown)
        if page_hint is not None:
            current_page = page_hint
        confidence = "high" if current_page is not None else "medium"
        math_fragments = extract_math_fragments_for_source_map(markdown)
        block: dict[str, Any] = {
            "id": source_id,
            "segment_id": str(segment.get("id") or ""),
            "page": current_page,
            "type": block_type,
            "order": order,
            "section_path": segment.get("section_path", []),
            "original_text": markdown,
            "translation": str(segment.get("translation") or ""),
            "bbox": [],
            "confidence": confidence,
            "refs": source_refs_from_text(markdown),
            "insert_after": previous_text_id if block_type in {"figure", "table", "caption"} else "",
        }
        if math_fragments:
            block["math"] = math_fragments
        blocks.append(block)
        if current_page is not None:
            pages.setdefault(current_page, []).append(source_id)
        if block_type not in {"figure", "table", "caption"}:
            previous_text_id = source_id
        if block_type == "figure":
            info = image_info_from_markdown(markdown)
            figures.append(
                {
                    "id": source_id,
                    "page": current_page,
                    "caption_id": "",
                    "image_path": info.get("image_path", ""),
                    "alt": info.get("alt", ""),
                    "insert_after": block.get("insert_after", ""),
                    "confidence": confidence,
                }
            )
        elif block_type == "table":
            tables.append(
                {
                    "id": source_id,
                    "page": current_page,
                    "caption_id": "",
                    "insert_after": block.get("insert_after", ""),
                    "caption_number": caption_number_from_text(markdown, "table"),
                    "confidence": confidence,
                }
            )
    return {
        "version": 1,
        "generated_at": now_iso(),
        "paper": {
            "title": str(metadata.get("title") or ""),
            "venue": str(metadata.get("venue") or ""),
            "source_type": str(metadata.get("source_type") or ("pdf" if metadata.get("source_pdf") else "raw-md")),
            "language": "en",
            "source_path": source_name,
        },
        "blocks": blocks,
        "pages": [{"page": page, "block_ids": ids} for page, ids in sorted(pages.items())],
        "figures": figures,
        "tables": tables,
    }


TERMINOLOGY_STOPWORDS = {
    "A", "An", "And", "As", "At", "By", "For", "From", "In", "Into", "Is", "It", "Of", "On", "Or", "The", "This", "To", "With",
    "Abstract", "Acknowledgments", "Conclusion", "Discussion", "Figure", "Introduction", "Method", "Methods", "References", "Results", "Table",
}


def candidate_terms_from_text(text: str) -> list[str]:
    clean = re.sub(r"https?://\S+|10\.\d{4,9}/\S+", " ", str(text or ""))
    terms: list[str] = []
    terms.extend(match.group(0) for match in re.finditer(r"\b[A-Z]{2,}(?:-[A-Z0-9]+)?\b", clean))
    for match in re.finditer(r"\b[A-Z][A-Za-z0-9-]+(?:\s+(?:[A-Z][A-Za-z0-9-]+|[a-z][A-Za-z0-9-]+)){1,4}\b", clean):
        term = match.group(0).strip()
        first = term.split()[0]
        if first in TERMINOLOGY_STOPWORDS:
            continue
        if len(term) < 5 or len(term) > 80:
            continue
        terms.append(term)
    result: list[str] = []
    seen: set[str] = set()
    for term in terms:
        key = term.casefold()
        if key in seen or term in TERMINOLOGY_STOPWORDS:
            continue
        seen.add(key)
        result.append(term)
    return result


def build_terminology_ledger(segments: list[dict[str, Any]], limit: int = 80) -> dict[str, Any]:
    ledger: dict[str, dict[str, Any]] = {}
    for segment in segments:
        if segment.get("kind") in {"heading", "table", "code"}:
            continue
        segment_id = str(segment.get("id") or "")
        for term in candidate_terms_from_text(markdown_plain_text(segment.get("markdown", ""))):
            key = term.casefold()
            entry = ledger.setdefault(
                key,
                {
                    "term": term,
                    "canonical_zh": "",
                    "source_terms": [term],
                    "forbidden_aliases": [],
                    "notes": "",
                    "count": 0,
                    "segment_ids": [],
                },
            )
            entry["count"] += 1
            if segment_id and segment_id not in entry["segment_ids"] and len(entry["segment_ids"]) < 10:
                entry["segment_ids"].append(segment_id)
    terms = sorted(ledger.values(), key=lambda item: (-int(item.get("count") or 0), str(item.get("term") or "")))[:limit]
    return {"version": 1, "generated_at": now_iso(), "terms": terms}


def make_translation_notes(source_map: dict[str, Any], terminology: dict[str, Any], source_name: str) -> str:
    blocks = source_map.get("blocks") if isinstance(source_map.get("blocks"), list) else []
    untranslated = [block for block in blocks if block.get("type") not in {"heading", "figure"} and not str(block.get("translation") or "").strip()]
    low_confidence = [block for block in blocks if block.get("confidence") != "high"]
    math_blocks = [block for block in blocks if block.get("math")]
    media_blocks = [block for block in blocks if block.get("type") in {"figure", "table", "caption"}]
    term_count = len(terminology.get("terms") if isinstance(terminology, dict) else [])
    lines = [
        "# Translation / Extraction Notes",
        "",
        f"Generated: {source_map.get('generated_at') or now_iso()}",
        f"Source: {source_name}",
        "",
        "## Current Status",
        "",
        f"- Source blocks: {len(blocks)}",
        f"- Untranslated substantive blocks: {len(untranslated)}",
        f"- Figure/table/caption blocks: {len(media_blocks)}",
        f"- Blocks containing delimited LaTeX/math: {len(math_blocks)}",
        f"- Candidate terminology entries: {term_count}",
        "",
        "## Notes",
        "",
        "- `source_map.json` keeps stable source IDs alongside the existing `p-0001` reader anchors.",
        "- Page numbers and bounding boxes are recorded when the extractor exposes them; otherwise confidence is marked `medium` so the PDF remains the ground truth.",
        "- Browser rendering uses local KaTeX for delimited LaTeX. OCR math that lacks Markdown/LaTeX delimiters may still need manual source checking.",
        "- Keep this file as the audit trail for skipped, uncertain, or manually repaired content.",
    ]
    if low_confidence:
        lines.extend(["", "## Blocks Needing Source Check", ""])
        for block in low_confidence[:40]:
            quote = markdown_plain_text(block.get("original_text", ""))[:140]
            lines.append(f"- {block.get('id')} / {block.get('segment_id')}: {quote}")
        if len(low_confidence) > 40:
            lines.append(f"- ... {len(low_confidence) - 40} more blocks")
    return "\n".join(lines).rstrip() + "\n"


def make_source_grounded_paper_markdown(metadata: dict[str, Any], segments: list[dict[str, Any]], source_map: dict[str, Any], terminology: dict[str, Any], source_name: str) -> str:
    title = str(metadata.get("title") or source_map.get("paper", {}).get("title") or "Untitled Paper")
    blocks = source_map.get("blocks") if isinstance(source_map.get("blocks"), list) else []
    by_segment_id = {str(segment.get("id") or ""): block for segment, block in zip(segments, blocks)}
    lines = [
        "<!-- Generated by paper-reader-agent as a Nature Reader style companion. -->",
        f"# {title}",
        "",
        f"Source: {source_name}",
        "",
        "## Page / Section Index",
        "",
    ]
    headings = [segment for segment in segments if segment.get("kind") == "heading"]
    if headings:
        for segment in headings[:80]:
            block = by_segment_id.get(str(segment.get("id") or ""), {})
            title_text = re.sub(r"^#{1,6}\s+", "", str(segment.get("markdown") or "")).strip()
            lines.append(f"- [{block.get('id') or segment.get('id')}] {title_text}")
    else:
        lines.append("- No stable headings were detected.")
    terms = terminology.get("terms") if isinstance(terminology, dict) else []
    lines.extend(["", "## Terminology Ledger", "", "| Term | 中文 | Source blocks |", "|---|---|---|"])
    if terms:
        for term in terms[:40]:
            source_ids = ", ".join(str(item) for item in term.get("segment_ids", [])[:5])
            lines.append(f"| {str(term.get('term') or '').replace('|', '/')} | {str(term.get('canonical_zh') or '').replace('|', '/')} | {source_ids} |")
    else:
        lines.append("|  |  |  |")
    lines.extend(["", "## Full Text", ""])
    for segment in segments:
        segment_id = str(segment.get("id") or "")
        block = by_segment_id.get(segment_id, {})
        source_id = str(block.get("id") or segment_id)
        page = block.get("page")
        source_label = f"p.{page} {source_id}" if page else source_id
        original = str(segment.get("markdown") or "").rstrip()
        translation = translation_text_for_segment(segment)
        lines.append(f'<a id="{source_id}"></a>')
        lines.append("")
        lines.append(f"**Source:** {source_label} · `{segment_id}`")
        lines.append("")
        lines.append("**Original:**")
        lines.append("")
        lines.append(original or "_[empty source block]_")
        lines.append("")
        if translation or translation_source_for_segment(segment):
            lines.append("**中文:**")
            lines.append("")
            lines.append(translation or "_[Not translated yet]_")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_source_artifacts(paper_dir: Path, metadata: dict[str, Any], segments: list[dict[str, Any]], source_name: str) -> None:
    source_map = build_source_map(metadata, segments, source_name)
    terminology = build_terminology_ledger(segments)
    write_json(paper_dir / "source_map.json", source_map)
    write_json(paper_dir / "terminology_ledger.json", terminology)
    write_text_atomic(paper_dir / "translation_notes.md", make_translation_notes(source_map, terminology, source_name))
    write_text_atomic(paper_dir / "paper.md", make_source_grounded_paper_markdown(metadata, segments, source_map, terminology, source_name))


def write_reader_bundle(paper_dir: Path, metadata: dict[str, Any], segments: list[dict[str, Any]], source_name: str) -> None:
    write_text_atomic(paper_dir / "reader.md", make_reader_markdown(segments, source_name))
    write_source_artifacts(paper_dir, metadata, segments, source_name)


def load_segments(paper_dir: Path) -> list[dict[str, Any]]:
    return read_json(paper_dir / "segments.json", [])


def annotations_by_segment(paper_dir: Path) -> dict[str, list[dict[str, Any]]]:
    annotations = read_json(paper_dir / "annotations.json", {"annotations": []}).get("annotations", [])
    result: dict[str, list[dict[str, Any]]] = {}
    for item in annotations:
        segment_id = item.get("segment_id")
        if segment_id:
            result.setdefault(segment_id, []).append(item)
    return result


def clean_annotation_range(value: Any) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    try:
        start = int(value.get("start", 0))
        end = int(value.get("end", 0))
    except (TypeError, ValueError):
        return None
    if start < 0 or end <= start:
        return None
    return {"start": start, "end": end}


def merge_records_by_id(existing: Any, incoming: list[Any]) -> list[Any]:
    """Replace a submitted collection, retaining extension fields on its IDs."""
    original = {
        str(item["id"]): item for item in existing
        if isinstance(item, dict) and item.get("id")
    } if isinstance(existing, list) else {}
    return [
        {**original.get(str(item.get("id") or ""), {}), **item} if isinstance(item, dict) else item
        for item in incoming
    ]


def default_thinking() -> dict[str, Any]:
    return {
        "version": 1,
        "explain": {"content": "", "updated_at": "", "source": "", "prompt": ""},
        "blocks": [],
        "annotations": [],
        "report_thoughts": [],
    }


def load_thinking(paper_dir: Path) -> dict[str, Any]:
    data = read_json(paper_dir / "thinking.json", default_thinking())
    if not isinstance(data, dict):
        data = default_thinking()
    data.setdefault("version", 1)
    explain = data.get("explain") if isinstance(data.get("explain"), dict) else {}
    data["explain"] = {
        **explain,
        "content": str(explain.get("content") or ""),
        "updated_at": str(explain.get("updated_at") or ""),
        "source": str(explain.get("source") or ""),
        "prompt": str(explain.get("prompt") or ""),
    }
    if not isinstance(data.get("blocks"), list):
        data["blocks"] = []
    if not isinstance(data.get("annotations"), list):
        data["annotations"] = []
    if not isinstance(data.get("report_thoughts"), list):
        data["report_thoughts"] = []
    return data


def clean_thinking(data: dict[str, Any]) -> dict[str, Any]:
    now = now_iso()
    explain = data.get("explain") if isinstance(data.get("explain"), dict) else {}
    cleaned: dict[str, Any] = {
        **data,
        "version": data.get("version", 1),
        "updated_at": now,
        "explain": {
            **explain,
            "content": str(explain.get("content") or ""),
            "updated_at": str(explain.get("updated_at") or now),
            "source": str(explain.get("source") or ""),
            "prompt": str(explain.get("prompt") or ""),
        },
        "blocks": [],
        "annotations": [],
        "report_thoughts": [],
    }
    for index, block in enumerate(data.get("blocks") if isinstance(data.get("blocks"), list) else []):
        if not isinstance(block, dict):
            continue
        content = str(block.get("content") or "")
        prompt = str(block.get("prompt") or "")
        mode = str(block.get("mode") or "").strip().lower()
        model = str(block.get("model") or "").strip()
        is_agent_block = mode in {"source", "free", "reading_narrative"} or bool(model)
        raw_title = str(block.get("title") or "").strip()
        if is_agent_block and raw_title in {"AI output", "Source-grounded answer", "Free reflection answer", "Source-grounded", "Free reflection"}:
            raw_title = ""
        title = raw_title or ("" if is_agent_block else "AI output")
        block_id = str(block.get("id") or f"tb-{index + 1}")
        cleaned_block = {
            **block,
            "id": block_id,
            "type": str(block.get("type") or "ai_output"),
            "title": title,
            "content": content,
            "created_at": str(block.get("created_at") or now),
            "updated_at": str(block.get("updated_at") or now),
        }
        if mode in {"source", "free", "reading_narrative"}:
            cleaned_block["mode"] = mode
        if prompt.strip():
            cleaned_block["prompt"] = prompt
        if model:
            cleaned_block["model"] = model
        context_mode = str(block.get("context_mode") or "").strip()
        if context_mode:
            cleaned_block["context_mode"] = context_mode
        try:
            context_chars = int(block.get("context_chars") or 0)
        except (TypeError, ValueError):
            context_chars = 0
        if context_chars > 0:
            cleaned_block["context_chars"] = context_chars
        context_error = str(block.get("context_error") or "").strip()
        if context_error:
            cleaned_block["context_error"] = context_error[:800]
        project_context = block.get("project_context") if isinstance(block.get("project_context"), dict) else {}
        if project_context:
            cleaned_block["project_context"] = {
                **project_context,
                "project": str(project_context.get("project") or "").strip(),
                "card_count": int(project_context.get("card_count") or 0),
                "source_path": str(project_context.get("source_path") or "").strip(),
            }
        status = str(block.get("status") or "").strip()
        if status:
            cleaned_block["status"] = status
        # Stored references include original selections/ranges. Context
        # truncation helpers are for generation, not persisting reader edits.
        cleaned["blocks"].append(cleaned_block)
    for item in data.get("annotations") if isinstance(data.get("annotations"), list) else []:
        if not isinstance(item, dict):
            continue
        # An external edit or partial save may leave a missing block; keep the
        # human record and its original target instead of silently deleting it.
        block_id = str(item.get("block_id") or item.get("thinking_block_id") or "")
        cleaned_item: dict[str, Any] = {
            **item,
            "id": str(item.get("id") or f"ta-{uuid.uuid4().hex[:12]}"),
            "block_id": block_id,
            "type": str(item.get("type") or "range"),
            "target": str(item.get("target") or "thinking"),
            "color": str(item.get("color") or "yellow"),
            "quote": str(item.get("quote") or ""),
            "note": str(item.get("note") or ""),
            "created_at": str(item.get("created_at") or now),
            "updated_at": str(item.get("updated_at") or now),
        }
        tags = item.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        if isinstance(tags, list):
            cleaned_item["tags"] = list(tags)
        presentation_flow_id = str(item.get("presentation_flow_id") or "").strip()
        if presentation_flow_id:
            cleaned_item["presentation_flow_id"] = presentation_flow_id
        range_value = clean_annotation_range(item.get("range"))
        if range_value:
            cleaned_item["range"] = {**item["range"], **range_value}
        cleaned["annotations"].append(cleaned_item)
    for item in data.get("report_thoughts") if isinstance(data.get("report_thoughts"), list) else []:
        if not isinstance(item, dict):
            continue
        note = str(item.get("note") or "")
        cleaned["report_thoughts"].append(
            {
                **item,
                "id": str(item.get("id") or f"rt-{uuid.uuid4().hex[:12]}"),
                "group": str(item.get("group") or "sensemaking-gap"),
                "note": note,
                "created_at": str(item.get("created_at") or now),
                "updated_at": str(item.get("updated_at") or now),
            }
        )
    return cleaned


def save_thinking_update(paper_dir: Path, data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("thinking must be an object")
    for key in ("annotations", "blocks", "report_thoughts"):
        if key in data and (
            not isinstance(data[key], list) or any(not isinstance(item, dict) for item in data[key])
        ):
            raise ValueError(f"{key} must be a list of objects")
    if "explain" in data and not isinstance(data["explain"], dict):
        raise ValueError("explain must be an object")
    existing = read_json(paper_dir / "thinking.json", default_thinking(), strict=True)
    if not isinstance(existing, dict):
        raise ValueError("thinking.json must contain an object")
    incoming = {**data}
    for key in ("annotations", "blocks", "report_thoughts"):
        if key in incoming:
            incoming[key] = merge_records_by_id(existing.get(key), incoming[key])
    if "explain" in incoming and isinstance(existing.get("explain"), dict):
        incoming["explain"] = {**existing["explain"], **incoming["explain"]}
    cleaned = clean_thinking(incoming)
    saved = {**existing, **incoming, "updated_at": cleaned["updated_at"]}
    saved.setdefault("version", 1)
    # Omitted sections are untouched, particularly original AI blocks when
    # only user annotations change. Explicit empty lists still delete records.
    for key in ("annotations", "blocks", "report_thoughts", "explain"):
        if key in incoming:
            if key == "explain":
                saved[key] = {**cleaned[key], **incoming[key]}
            else:
                saved[key] = [
                    {**defaults, **record, "id": record.get("id") or defaults["id"]}
                    for record, defaults in zip(incoming[key], cleaned[key])
                ]
    write_json(paper_dir / "thinking.json", saved)
    schedule_export_notes_and_annotated(paper_dir)
    return saved


def default_takeaway_doc() -> dict[str, Any]:
    return {"version": 1, "blocks": [], "updated_at": ""}


def takeaway_doc_skeleton_from_outline(outline_data: dict[str, Any] | None) -> dict[str, Any]:
    now = now_iso()
    outline_data = outline_data if isinstance(outline_data, dict) else {}
    flows = outline_data.get("presentation_flow") if isinstance(outline_data.get("presentation_flow"), list) else []
    blocks: list[dict[str, Any]] = []

    def add_block(block_id: str, text: str, indent: int, level: int = 2) -> None:
        blocks.append(
            {
                "id": block_id,
                "type": "heading",
                "text": text,
                "indent": indent,
                "level": level,
                "created_at": now,
                "updated_at": now,
            }
        )

    add_block("td-heading-paper", "Paper Evidence / 原文信息", 0, 1)
    if flows:
        for index, flow in enumerate(flows[:12], start=1):
            title = str(flow.get("title") or flow.get("core") or f"Paper Flow {index}").strip()
            add_block(f"td-heading-flow-{index}", title, 1, 2)
    else:
        add_block("td-heading-paper-flow", "Paper Flow / 原文结构", 1, 2)
    add_block("td-heading-sensemaking", "My Sensemaking / 我的思考", 0, 1)
    for key, label in [
        ("gap", "GAP"),
        ("borrow", "What We Can Borrow"),
        ("angle", "Our Paper Angle"),
        ("question", "Open Questions"),
        ("phrase", "Useful Phrases"),
    ]:
        add_block(f"td-heading-sensemaking-{key}", label, 1, 2)
    return {"version": 1, "blocks": blocks, "updated_at": now}


def ensure_takeaway_doc_skeleton(paper_dir: Path, outline_data: dict[str, Any] | None) -> dict[str, Any]:
    existing = read_json(paper_dir / "takeaway_doc.json", default_takeaway_doc())
    if isinstance(existing, dict) and isinstance(existing.get("blocks"), list) and existing.get("blocks"):
        return clean_takeaway_doc(existing)
    doc = clean_takeaway_doc(takeaway_doc_skeleton_from_outline(outline_data))
    write_json(paper_dir / "takeaway_doc.json", doc)
    return doc


def clean_source_refs(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    refs: list[dict[str, str]] = []
    for item in value[:12]:
        if not isinstance(item, dict):
            continue
        ref = {
            "paper_id": str(item.get("paper_id") or ""),
            "annotation_id": str(item.get("annotation_id") or ""),
            "segment_id": str(item.get("segment_id") or ""),
            "end_segment_id": str(item.get("end_segment_id") or ""),
            "block_id": str(item.get("block_id") or ""),
            "item_id": str(item.get("item_id") or ""),
            "source": str(item.get("source") or ""),
            "label": str(item.get("label") or ""),
            "quote": str(item.get("quote") or "")[:900],
        }
        if any(ref.values()):
            refs.append(ref)
    return refs


def clean_selection_refs(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    refs: list[dict[str, Any]] = []
    for item in value[:24]:
        if not isinstance(item, dict):
            continue
        ref: dict[str, Any] = {
            "paper_id": str(item.get("paper_id") or ""),
            "segment_id": str(item.get("segment_id") or ""),
            "target": str(item.get("target") or "source"),
            "quote": str(item.get("quote") or "")[:1200],
        }
        if isinstance(item.get("range"), dict):
            range_value = clean_annotation_range(item.get("range"))
            if range_value:
                ref["range"] = range_value
        if any(str(ref.get(key) or "").strip() for key in {"paper_id", "segment_id", "quote"}):
            refs.append(ref)
    return refs


def clean_takeaway_doc(data: dict[str, Any]) -> dict[str, Any]:
    now = now_iso()
    cleaned: dict[str, Any] = {"version": 1, "updated_at": now, "blocks": []}
    blocks = data.get("blocks") if isinstance(data, dict) and isinstance(data.get("blocks"), list) else []
    for index, block in enumerate(blocks[:500]):
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "bullet").strip().lower()
        if block_type not in {"heading", "bullet"}:
            block_type = "bullet"
        text = str(block.get("text") or "")
        try:
            indent = int(block.get("indent", 0))
        except (TypeError, ValueError):
            indent = 0
        try:
            level = int(block.get("level", 1))
        except (TypeError, ValueError):
            level = 1
        cleaned_block = {
            "id": str(block.get("id") or f"td-{index + 1}").strip() or f"td-{index + 1}",
            "type": block_type,
            "text": text,
            "indent": max(0, min(6, indent)),
            "level": max(1, min(3, level)),
            "source_item_id": str(block.get("source_item_id") or ""),
            "source": str(block.get("source") or ""),
            "source_label": str(block.get("source_label") or ""),
            "quote": str(block.get("quote") or ""),
            "note": str(block.get("note") or ""),
            "meta": str(block.get("meta") or ""),
            "color": str(block.get("color") or ""),
            "source_refs": clean_source_refs(block.get("source_refs")),
            "locked": bool(block.get("locked")),
            "created_at": str(block.get("created_at") or now),
            "updated_at": str(block.get("updated_at") or now),
        }
        tags = block.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        cleaned_block["tags"] = [str(tag).strip() for tag in tags[:20] if str(tag).strip()] if isinstance(tags, list) else []
        cleaned["blocks"].append(cleaned_block)
    return cleaned


def load_takeaway_doc(paper_dir: Path) -> dict[str, Any]:
    data = read_json(paper_dir / "takeaway_doc.json", default_takeaway_doc())
    if not isinstance(data, dict):
        data = default_takeaway_doc()
    return clean_takeaway_doc(data) if data.get("blocks") else default_takeaway_doc()


def publication_service() -> feishu_publish.PublicationService:
    global PUBLICATION_SERVICE
    with PUBLICATION_SERVICE_GUARD:
        if PUBLICATION_SERVICE is None:
            PUBLICATION_SERVICE = feishu_publish.PublicationService(
                snapshot_reader=load_reading_data, json_reader=read_json,
                json_writer=write_json, text_writer=write_text_atomic,
            )
        return PUBLICATION_SERVICE


def load_reading_data(paper_dir: Path, paper_id: str | None = None, *, include_teacher: bool = True) -> dict[str, Any]:
    """Versioned, lossless JSON-document snapshot; never normalizes or writes.

    Missing files are omitted, not synthesized. Invalid JSON fails the export
    rather than silently losing records. This is reading data, not a PDF backup.
    """
    missing = object()
    files: dict[str, Any] = {}
    names = [
        "metadata.json", "segments.json", "annotations.json", "thinking.json",
        "reading_progress.json", "outline.json", "takeaway_doc.json", "translation_state.json",
    ]
    if include_teacher:
        names.append("reading_teacher.json")
    for name in names:
        value = read_json(paper_dir / name, missing, strict=True)
        if value is not missing:
            files[name] = value
    return {
        "format": "paper-reader-reading-data",
        "version": 1,
        "paper_id": paper_id or paper_dir.name,
        "sources": {
            "segments.json": "Original source segments and stored translations, not user notes.",
            "annotations.json#/annotations": "User highlights and notes on source/translation segments; accepted AI definitions retain explicit origin fields.",
            "thinking.json#/annotations": "User annotations on stored thinking/AI text; quotes are not necessarily user-authored.",
            "thinking.json#/report_thoughts": "Original user notes/questions.",
            "thinking.json#/blocks": "Stored thinking blocks including original AI outputs and prompts; type/mode/model/source are retained.",
            "thinking.json#/chat": "Stored chat records, if present; roles/sources are retained without inferring authorship or classifying prose.",
            "thinking.json#/messages": "Stored message records, if present; roles/sources are retained without inferring authorship or classifying prose.",
            "thinking.json#/explain": "Original AI Paper Brief, separate from user notes.",
            "takeaway_doc.json": "Stored mixed-origin takeaway records; authorship is not reinterpreted.",
            "translation_state.json": "Persisted translation job progress, separate from original metadata and user annotations.",
            "reading_teacher.json": "Local AI teaching suggestions and their source/context snapshots, not user-authored notes.",
        },
        "files": files,
    }


def make_notes_markdown(reading_data: dict[str, Any]) -> str:
    """Render every stored record mechanically, including orphaned highlights."""
    files = reading_data["files"]
    metadata = files.get("metadata.json")
    title = (metadata.get("title") if isinstance(metadata, dict) else "") or reading_data["paper_id"]
    segments = files.get("segments.json")
    segment_lookup = {
        str(segment.get("id")): segment for segment in segments if isinstance(segment, dict)
    } if isinstance(segments, list) else {}
    lines = [
        f"# Reading Notes: {title}", "",
        "Mechanical export: quotations, notes/questions and stored prompts are verbatim. "
        "Original AI content is kept in separate sections; no new interpretation is generated.",
        "JSON files remain authoritative. Record fields preserve IDs, targets, ranges and extensions; "
        "missing source targets do not discard annotations.", "",
    ]

    def fenced(text: str, language: str) -> str:
        longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
        fence = "`" * max(3, longest + 1)
        suffix = "" if text.endswith("\n") else "\n"
        return f"{fence}{language}\n{text}{suffix}{fence}"

    def add_record(record: Any, source: str, label: str) -> None:
        lines.extend([f"### {label}", "", f"- Record source: `{source}`", ""])
        if not isinstance(record, dict):
            lines.extend([fenced(json.dumps(record, ensure_ascii=False, indent=2), "json"), ""])
            return
        segment_id = record.get("segment_id")
        if isinstance(segment_id, str) and segment_id:
            lines.extend([f"- Source link: [reader.md](reader.md#{urllib.parse.quote(segment_id, safe='')})", ""])
        text_fields = {
            "quote": "Original quote", "note": "Original note/question",
            "prompt": "Stored prompt/question", "content": "Stored content", "text": "Stored text",
            "message": "Stored message",
        }
        if is_teacher_definition(record):
            text_fields["note"] = "Accepted AI definition (AI-origin; reader edits retained)"
        prose = {key: value for key, value in record.items() if key in text_fields and isinstance(value, str) and value}
        nested_messages = record.get("messages")
        fields = {
            key: value for key, value in record.items()
            if key not in prose and not (key == "messages" and isinstance(nested_messages, list))
        }
        lines.extend(["Record fields:", "", fenced(json.dumps(fields, ensure_ascii=False, indent=2), "json"), ""])
        for key, value in prose.items():
            lines.extend([f"#### {text_fields[key]} (verbatim)", "", fenced(value, "text"), ""])
        if source.startswith("annotations.json#") and not record.get("quote") and segment_id:
            segment = segment_lookup.get(str(segment_id), {})
            target = record.get("target") or "source"
            context = segment.get("translation" if target == "translation" else "markdown") if target in {"source", "translation"} else None
            if isinstance(context, str) and context:
                lines.extend(["#### Target segment context (not a recorded quote)", "", fenced(context, "text"), ""])
        if isinstance(nested_messages, list):
            add_records("Stored messages (recorded roles/sources; not classified)", nested_messages, f"{source}/messages")

    def add_records(heading: str, records: Any, source: str) -> None:
        lines.extend([f"## {heading}", ""])
        if isinstance(records, list):
            for index, record in enumerate(records):
                add_record(record, f"{source}/{index}", f"Record {index + 1}")
        elif records is not None:
            add_record(records, source, "Stored value")

    annotations = files.get("annotations.json", {})
    add_records(
        "Paper annotations",
        annotations.get("annotations", []) if isinstance(annotations, dict) else annotations,
        "annotations.json#/annotations" if isinstance(annotations, dict) else "annotations.json#",
    )
    thinking = files.get("thinking.json", {})
    if isinstance(thinking, dict):
        add_records("Thinking annotations (user records on stored thinking/AI text)", thinking.get("annotations", []), "thinking.json#/annotations")
        add_records("Report thoughts (original user notes/questions)", thinking.get("report_thoughts", []), "thinking.json#/report_thoughts")
        add_records("Stored thinking blocks (includes original AI outputs; not user annotations)", thinking.get("blocks", []), "thinking.json#/blocks")
        for key in ("chat", "messages"):
            if key in thinking:
                add_records(f"Stored {key} (recorded roles/sources; not classified)", thinking[key], f"thinking.json#/{key}")
        if thinking.get("explain"):
            lines.extend(["## Original AI Paper Brief (not user notes)", ""])
            add_record(thinking["explain"], "thinking.json#/explain", "Stored Paper Brief")
    elif "thinking.json" in files:
        add_records("Stored thinking data", thinking, "thinking.json#")
    takeaway = files.get("takeaway_doc.json", {})
    add_records(
        "Stored takeaway records (mixed origin; not reinterpreted)",
        takeaway.get("blocks", []) if isinstance(takeaway, dict) else takeaway,
        "takeaway_doc.json#/blocks" if isinstance(takeaway, dict) else "takeaway_doc.json#",
    )
    return "\n".join(lines).rstrip() + "\n"


def export_notes_and_annotated(paper_dir: Path) -> None:
    # Serialize snapshot + writes, not just each output file: an older slow
    # export must not overwrite a newer save's derived Markdown.
    with write_lock_for(paper_dir / ".notes-export"):
        write_notes_and_annotated(paper_dir)


def write_notes_and_annotated(paper_dir: Path) -> None:
    reading_data = load_reading_data(paper_dir, include_teacher=False)
    files = reading_data["files"]
    metadata = files.get("metadata.json") or {}
    title = metadata.get("title") or paper_dir.name
    segments = files.get("segments.json") or []
    annotation_data = files.get("annotations.json") or {}
    records = annotation_data.get("annotations", []) if isinstance(annotation_data, dict) else annotation_data
    annotations: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if isinstance(record, dict) and record.get("segment_id"):
            annotations.setdefault(record["segment_id"], []).append(record)

    annotated_lines = [f"# Annotated Reading Copy: {title}", ""]
    for segment in segments:
        segment_id = segment["id"]
        segment_annotations = annotations.get(segment_id, [])
        first_highlight = next((item for item in segment_annotations if item.get("color")), None)
        color = first_highlight.get("color") if first_highlight else None
        if color:
            annotated_lines.append(f"<!-- highlight:{segment_id} color={color} -->")
        annotated_lines.append(f'<a id="{segment_id}"></a>')
        annotated_lines.append(segment["markdown"].rstrip())
        translation = translation_text_for_segment(segment)
        if translation.strip():
            annotated_lines.append("")
            annotated_lines.append(f"> 中文：{translation}")
        for annotation in segment_annotations:
            note = annotation.get("note") or ""
            if not note:
                continue
            annotated_lines.append("")
            annotated_lines.append("> [!NOTE]")
            for line in note.splitlines():
                annotated_lines.append(f"> {line}")
        annotated_lines.append("")
    write_text_atomic(paper_dir / "notes.md", make_notes_markdown(reading_data))
    write_text_atomic(paper_dir / "annotated.md", "\n".join(annotated_lines).rstrip() + "\n")


def schedule_export_notes_and_annotated(paper_dir: Path, delay: float = 0.35) -> None:
    key = paper_dir.resolve()

    def run_export() -> None:
        try:
            export_notes_and_annotated(paper_dir)
        except Exception as exc:  # noqa: BLE001 - background export should not break note saving
            print(f"Background notes export failed for {paper_dir}: {exc}", file=sys.stderr)
        finally:
            with EXPORT_TIMERS_GUARD:
                if EXPORT_TIMERS.get(key) is timer:
                    EXPORT_TIMERS.pop(key, None)

    timer = threading.Timer(delay, run_export)
    timer.daemon = True
    with EXPORT_TIMERS_GUARD:
        previous = EXPORT_TIMERS.get(key)
        if previous:
            previous.cancel()
        EXPORT_TIMERS[key] = timer
    timer.start()


def guess_title_from_segments(segments: list[dict[str, Any]], fallback: str) -> str:
    for segment in segments:
        if segment.get("kind") == "heading" and segment.get("level") == 1:
            title = feishu_metadata.clean_title(extract_heading_text(segment.get("markdown", "")))
            if title:
                return title
    return fallback


def markdown_plain_text(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", str(text or ""))
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"[*_#>`|]+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def section_excerpt(segments: list[dict[str, Any]], keywords: list[str], max_chars: int = 1800) -> str:
    keyword_pattern = re.compile("|".join(re.escape(keyword) for keyword in keywords), flags=re.I)
    chunks: list[str] = []
    for segment in segments:
        section_path = " / ".join(segment.get("section_path", []))
        heading_text = extract_heading_text(segment.get("markdown", "")) if segment.get("kind") == "heading" else ""
        haystack = f"{section_path} {heading_text}"
        if not keyword_pattern.search(haystack):
            continue
        if segment.get("kind") == "heading":
            continue
        text = markdown_plain_text(segment.get("markdown", ""))
        if text:
            chunks.append(text)
        if len("\n".join(chunks)) >= max_chars:
            break
    return "\n".join(chunks).strip()[:max_chars]


def find_research_question(segments: list[dict[str, Any]], abstract: str) -> str:
    candidates = []
    for segment in segments:
        text = markdown_plain_text(segment.get("markdown", ""))
        if re.search(r"\b(research question|RQ\d?|we ask|we investigate|we examine|we explore)\b", text, flags=re.I):
            candidates.append(text)
        if len("\n".join(candidates)) > 900:
            break
    if candidates:
        return "\n".join(candidates)[:1200]
    sentences = re.split(r"(?<=[.!?。！？])\s+", abstract)
    return " ".join(sentences[:2]).strip()


def infer_venue(text: str) -> str:
    lowered = text.lower()
    venue_patterns = [
        ("CHI", r"\bchi\b|conference on human factors in computing systems"),
        ("UIST", r"\buist\b"),
        ("CSCW", r"\bcscw\b"),
        ("DIS", r"\bdis\b|designing interactive systems"),
        ("IUI", r"\biui\b"),
        ("IEEE", r"\bieee\b"),
        ("arXiv", r"arxiv"),
        ("ACM", r"\bacm\b"),
    ]
    for label, pattern in venue_patterns:
        if re.search(pattern, lowered, flags=re.I):
            return label
    return ""


def build_skim_summary(metadata: dict[str, Any], segments: list[dict[str, Any]], source_name: str) -> str:
    cloud_summary = build_cloud_skim_summary(metadata, segments, source_name)
    if cloud_summary:
        return cloud_summary
    title = metadata.get("title") or "Untitled Paper"
    raw_sample = "\n".join(markdown_plain_text(segment.get("markdown", "")) for segment in segments[:20])
    abstract = metadata.get("abstract") or section_excerpt(segments, ["abstract"], max_chars=2200)
    research_question = metadata.get("research_question") or find_research_question(segments, abstract)
    authors = metadata.get("authors", "")
    institutions = metadata.get("institutions", "")
    venue = metadata.get("venue") or infer_venue(raw_sample)
    year = str(metadata.get("year") or "")
    if not year:
        year_match = re.search(r"\b(19|20)\d{2}\b", raw_sample)
        year = year_match.group(0) if year_match else ""
    section_titles = [item.get("title", "") for item in read_json(Path(metadata.get("_paper_dir", "")) / "outline.json", {"outline": []}).get("outline", [])] if metadata.get("_paper_dir") else []
    if not section_titles:
        section_titles = [extract_heading_text(segment.get("markdown", "")) for segment in segments if segment.get("kind") == "heading"]
    section_titles = [title for title in section_titles if title][:12]
    explain_items = [
        f"- 这篇论文的标题是《{title}》。它主要围绕摘要中呈现的问题展开：{abstract[:260] if abstract else '待从原文进一步补充。'}",
        f"- 可以先把它当作一篇回答“{research_question[:220] if research_question else '作者试图解决什么问题'}”的论文来读。略读阶段的目标是判断它是否值得升级为精读。",
        "- 阅读主线建议：先看研究动机和问题定义，再看方法/系统/研究设计，最后看 evaluation、findings 和 limitations。",
    ]
    if section_titles:
        explain_items.append("- 文章结构主干：" + " -> ".join(section_titles[:8]))
    explain_items.extend([
        "- 如果这篇论文要用于写作，可以优先标注它属于 related work、motivation、method、evaluation、theory 中的哪一种证据。",
        "- 如果后续需要原文引用、逐段翻译或图表细读，请在 Library 中点击“精读”升级。",
    ])
    return "\n".join(
        [
            f"# Author: {authors or '待补充'}",
            f"# Institution: {institutions or '待补充'}",
            f"# Journal: {venue or '待补充'}",
            f"# Publication Year: {year or '待补充'}",
            f"# Abstract: {abstract or '待补充'}",
            f"# Research Question: {research_question or '待补充'}",
            "# Explain the paper in a vivid and understandable way, can be fluid structured based on the paper framing.",
            "",
            *explain_items,
            "",
            f"> Source: {source_name}",
            "> Mode: 略读，仅做主干提取；未进行全文逐段翻译。",
        ]
    ).rstrip() + "\n"


def paper_text_for_llm(segments: list[dict[str, Any]], max_chars: int = 52000) -> str:
    chunks = []
    for segment in segments:
        segment_id = str(segment.get("id") or "")
        text = markdown_plain_text(segment.get("markdown", ""))
        if not text:
            continue
        chunks.append(f"[{segment_id}] {text}")
        if len("\n".join(chunks)) >= max_chars:
            break
    return "\n".join(chunks)[:max_chars]


def paper_markdown_for_chat(segments: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for segment in segments:
        segment_id = str(segment.get("id") or "")
        markdown = str(segment.get("markdown") or "").strip()
        if not markdown:
            continue
        if segment_id:
            chunks.append(f'<a id="{segment_id}"></a>\n\n{markdown}')
        else:
            chunks.append(markdown)
    return "\n\n".join(chunks).strip()


def load_paper_markdown_for_chat(paper_dir: Path, segments: list[dict[str, Any]]) -> str:
    for filename in ("raw.md", "reader.md"):
        path = paper_dir / filename
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    return paper_markdown_for_chat(segments)


CHAT_FULL_MARKDOWN_CHAR_LIMIT = 85000
CHAT_COMPRESSED_MARKDOWN_CHAR_LIMIT = 52000


def segment_markdown_with_anchor(segment: dict[str, Any]) -> str:
    segment_id = str(segment.get("id") or "")
    markdown = str(segment.get("markdown") or "").strip()
    if not markdown:
        return ""
    return f'<a id="{segment_id}"></a>\n\n{markdown}' if segment_id else markdown


def append_chat_chunk(lines: list[str], chunk: str, max_chars: int) -> bool:
    chunk = str(chunk or "").strip()
    if not chunk:
        return True
    candidate_len = len("\n\n".join(lines)) + len(chunk) + 2
    if candidate_len > max_chars:
        return False
    lines.append(chunk)
    return True


def compressed_paper_markdown_for_chat(segments: list[dict[str, Any]], source_refs: list[dict[str, str]], message: str, max_chars: int = CHAT_COMPRESSED_MARKDOWN_CHAR_LIMIT) -> str:
    lines = [
        "<!-- Context note: original paper Markdown exceeded the chat model/request limit; this compressed Markdown keeps the paper outline, opening sections, selected/retrieved evidence, query-matched segments, and ending sections. -->"
    ]
    by_id = {str(segment.get("id") or ""): segment for segment in segments}
    used: set[str] = set()

    headings = []
    for segment in segments:
        if segment.get("kind") != "heading":
            continue
        segment_id = str(segment.get("id") or "")
        title = extract_heading_text(segment.get("markdown", ""))
        if title:
            headings.append(f"- [{segment_id}] {title}" if segment_id else f"- {title}")
    if headings:
        append_chat_chunk(lines, "## Paper Outline\n" + "\n".join(headings[:80]), max_chars)

    def add_segment(segment: dict[str, Any]) -> bool:
        segment_id = str(segment.get("id") or "")
        if not segment_id or segment_id in used:
            return True
        chunk = segment_markdown_with_anchor(segment)
        if not append_chat_chunk(lines, chunk, max_chars):
            return False
        used.add(segment_id)
        return True

    append_chat_chunk(lines, "## Opening Markdown", max_chars)
    opening_count = 0
    for segment in segments:
        if not str(segment.get("markdown") or "").strip():
            continue
        if not add_segment(segment):
            break
        opening_count += 1
        if opening_count >= 18:
            break

    ref_ids = [str(ref.get("segment_id") or "") for ref in source_refs if ref.get("segment_id")]
    if ref_ids:
        append_chat_chunk(lines, "## Selected And Retrieved Evidence Markdown", max_chars)
    for ref_id in ref_ids:
        center = segment_number(ref_id)
        for offset in range(-2, 3):
            segment = by_id.get(segment_id_from_number(center + offset))
            if segment and not add_segment(segment):
                return "\n\n".join(lines).strip()

    tokens = chat_query_tokens(message)
    if tokens:
        append_chat_chunk(lines, "## Query Matched Markdown", max_chars)
        scored: list[tuple[float, int, dict[str, Any]]] = []
        for index, segment in enumerate(segments):
            segment_id = str(segment.get("id") or "")
            if not segment_id or segment_id in used or segment.get("kind") == "heading":
                continue
            text = markdown_plain_text(segment.get("markdown", ""))
            if not text:
                continue
            lowered = text.lower()
            score = 0.0
            for token in tokens:
                if token in lowered:
                    score += 2.0 + min(4, lowered.count(token)) * 0.25
            if score > 0:
                scored.append((score, index, segment))
        scored.sort(key=lambda item: (-item[0], item[1]))
        for _score, _index, segment in scored[:28]:
            if not add_segment(segment):
                return "\n\n".join(lines).strip()

    append_chat_chunk(lines, "## Ending Markdown", max_chars)
    tail_segments = [segment for segment in segments if str(segment.get("markdown") or "").strip()][-14:]
    for segment in tail_segments:
        if not add_segment(segment):
            break
    return "\n\n".join(lines).strip()


def should_retry_chat_with_compressed_context(exc: Exception) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    markers = [
        "context length",
        "context_length",
        "maximum context",
        "max context",
        "token limit",
        "too many tokens",
        "request too large",
        "payload too large",
        "entity too large",
        "413",
    ]
    return any(marker in text for marker in markers)


def chat_exception_message(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return http_error_summary(exc)
    return str(exc)


def briefing_messages(metadata: dict[str, Any], segments: list[dict[str, Any]], outline: list[dict[str, Any]] | None, source_name: str) -> list[dict[str, str]]:
    title = str(metadata.get("title") or "Untitled Paper")
    outline_titles = outline_markdown(outline or [], limit=12)
    body = paper_text_for_llm(segments)
    return [
        {
            "role": "system",
            "content": "你是 HCI/AI 学术论文阅读助手。请用中文为研究者生成准确、具体、可编辑的 Paper Brief。不要编造原文没有的信息；重要术语保留英文原词。",
        },
        {
            "role": "user",
            "content": f"""请基于下面解析出的论文文本生成 Paper Brief。

输出要求：
# Author:
# Institution:
# Journal:
# Publication Year:
# Abstract:
# Research Question:
# Explain the paper in a vivid and understandable way, can be fluid structured based on the paper framing.

在 Explain 部分请包括：
- 这篇论文真正关心的问题
- 作者为什么认为这个问题重要
- 方法/系统/研究设计是什么
- evaluation 或 findings 支撑了什么
- 对 HCI / AI 论文写作可借鉴之处

已知元数据：
Title: {title}
Authors: {metadata.get('authors') or 'unknown'}
Venue: {metadata.get('venue') or metadata.get('journal') or 'unknown'}
Year: {metadata.get('year') or metadata.get('publication_year') or 'unknown'}
Source: {source_name}
Outline: {outline_titles or 'unknown'}

论文文本片段：
{body}
""",
        },
    ]


def build_cloud_skim_summary(metadata: dict[str, Any], segments: list[dict[str, Any]], source_name: str) -> str:
    if not cloud_llm_enabled() or not segments:
        return ""
    try:
        outline = read_json(Path(metadata.get("_paper_dir", "")) / "outline.json", {"outline": []}).get("outline", []) if metadata.get("_paper_dir") else []
        return kimi_chat(briefing_messages(metadata, segments, outline, source_name), max_tokens=7000, temperature=0.2).rstrip() + "\n"
    except Exception as exc:  # noqa: BLE001
        print(f"Cloud skim summary failed, falling back to local summary: {exc}", file=sys.stderr)
        return ""


def compact_explanation_text(text: str, max_chars: int = 900) -> str:
    clean = re.sub(r"\s+", " ", markdown_plain_text(text or "")).strip()
    return clean[:max_chars].rstrip() + ("..." if len(clean) > max_chars else "")


def sentence_bullets(text: str, limit: int = 3, max_chars: int = 260) -> list[str]:
    clean = compact_explanation_text(text, max_chars=1800)
    if not clean:
        return []
    pieces = re.split(r"(?<=[。！？.!?])\s+|\n+", clean)
    bullets: list[str] = []
    for piece in pieces:
        item = piece.strip(" -•\t")
        if len(item) < 24:
            continue
        bullets.append(item[:max_chars].rstrip() + ("..." if len(item) > max_chars else ""))
        if len(bullets) >= limit:
            break
    if not bullets and clean:
        bullets.append(clean[:max_chars].rstrip() + ("..." if len(clean) > max_chars else ""))
    return bullets


def explanation_section(segments: list[dict[str, Any]], keywords: list[str], max_chars: int = 1400) -> str:
    return compact_explanation_text(section_excerpt(segments, keywords, max_chars=max_chars), max_chars=max_chars)


def research_question_markdown(question: str, title: str, abstract: str) -> str:
    clean = compact_explanation_text(question, max_chars=900)
    if not clean:
        fallback = compact_explanation_text(abstract, max_chars=420)
        clean = f"这篇论文可以理解为在追问：围绕《{title}》所描述的场景，现有做法为什么不够，以及作者提出的方法如何改善这一问题。{fallback}"
    rq_matches = re.findall(r"(?:RQ\s*\d+|Research Question\s*\d*)[:：.]?\s*([^\n。；;]+(?:[。?？][^\n。；;]*)?)", clean, flags=re.I)
    if rq_matches:
        return "\n".join(f"- RQ{index + 1}：{item.strip()}" for index, item in enumerate(rq_matches[:5]))
    parts = sentence_bullets(clean, limit=3, max_chars=240)
    if len(parts) == 1:
        return f"- RQ1：{parts[0]}"
    return "\n".join(f"- RQ{index + 1}：{item}" for index, item in enumerate(parts))


def outline_markdown(outline: list[dict[str, Any]], limit: int = 8) -> str:
    titles = [str(item.get("title") or "").strip() for item in outline if item.get("title")]
    titles = [title for title in titles if title and not should_skip_presentation_heading(title)][:limit]
    return " → ".join(titles)


def looks_like_auto_explanation(content: str) -> bool:
    clean = str(content or "")
    if not clean.strip():
        return True
    auto_markers = [
        "先说人话：这篇论文到底在关心什么",
        "哪些句子可以直接服务你的 motivation",
        "快速解释已放到右侧 Explain",
    ]
    return any(marker in clean for marker in auto_markers)


def build_paper_explanation(metadata: dict[str, Any], segments: list[dict[str, Any]], outline: list[dict[str, Any]], source_name: str) -> str:
    cloud_explanation = build_cloud_paper_explanation(metadata, segments, outline, source_name)
    if cloud_explanation:
        return cloud_explanation
    title = str(metadata.get("title") or "Untitled Paper")
    abstract = compact_explanation_text(metadata.get("abstract") or section_excerpt(segments, ["abstract"], max_chars=2200), max_chars=1600)
    question = str(metadata.get("research_question") or find_research_question(segments, abstract) or "")
    method = compact_explanation_text(metadata.get("method") or explanation_section(segments, ["method", "system", "design", "framework", "approach", "implementation"], max_chars=1800), max_chars=1200)
    study = explanation_section(segments, ["study", "evaluation", "experiment", "participants", "procedure", "data", "analysis"], max_chars=1600)
    findings = compact_explanation_text(metadata.get("result") or explanation_section(segments, ["finding", "findings", "result", "results"], max_chars=1800), max_chars=1200)
    discussion = compact_explanation_text(metadata.get("discussion") or explanation_section(segments, ["discussion", "implication", "limitation", "future", "conclusion"], max_chars=1600), max_chars=1000)
    structure = outline_markdown(outline)
    method_bullets = sentence_bullets(method, limit=4, max_chars=260)
    study_bullets = sentence_bullets(study, limit=3, max_chars=260)
    finding_bullets = sentence_bullets(findings, limit=4, max_chars=280)
    discussion_bullets = sentence_bullets(discussion, limit=3, max_chars=280)
    abstract_for_output = abstract or "未在解析结果中稳定定位到摘要；建议精读后检查 raw.md 或原 PDF。"
    core_problem = compact_explanation_text(question or abstract or title, max_chars=420)
    lines = [
        "# 摘要：",
        abstract_for_output,
        "",
        "# 研究问题：",
        research_question_markdown(question, title, abstract),
        "",
        "# 解读：",
        "",
        f"## 核心问题：这篇论文真正想解决什么",
        f"这篇论文《{title}》关心的不是一个孤立的技术细节，而是一个具体工作场景里的决策、协作或理解问题。用人话说，它想弄清楚：{core_problem}",
        "",
        "它值得读的地方在于：作者不是只给一个工具或模型，而是在尝试把一个原本容易被粗略带过的问题拆开，让读者看到问题为什么会发生、哪些因素在起作用，以及系统/方法应该怎样介入。",
        "",
    ]
    if structure:
        lines.extend(["## 论文的展开路径", f"可以按这条线读：{structure}", ""])
    lines.extend(["## 作者的做法：他们如何把问题变成可研究的对象"])
    if method_bullets:
        lines.extend(f"- {item}" for item in method_bullets)
    else:
        lines.append("- 解析结果里没有稳定抓到 method/system 段落；建议精读后在原文中补充方法细节。")
    lines.extend(["", "## 他们如何验证或展开分析"])
    if study_bullets:
        lines.extend(f"- {item}" for item in study_bullets)
    else:
        lines.append("- 论文的验证方式需要结合具体章节阅读；当前解析结果没有明显提取到 evaluation/study 片段。")
    lines.extend(["", "## 他们发现了什么"])
    if finding_bullets:
        lines.extend(f"- {item}" for item in finding_bullets)
    else:
        lines.append("- 当前解析结果没有稳定定位 findings/results；可以在精读后用右侧 For Writing 记录可引用发现。")
    lines.extend(["", "## 关键见解和启示"])
    if discussion_bullets:
        lines.extend(f"- {item}" for item in discussion_bullets)
    else:
        lines.extend([
            "- 读这篇论文时，重点看它如何定义问题边界，而不只是看最终系统或实验指标。",
            "- 对 CHI/HCI 写作来说，它可能最有用的部分是 motivation、study framing、design implication 或 discussion 的论证方式。",
        ])
    lines.extend(
        [
            "",
            "## 写作时可以怎么用",
            "- **Motivation**：抽取作者如何把日常现象升级为研究问题。",
            "- **Related Work**：记录它把哪些概念、系统或理论放在同一个问题空间中。",
            "- **Method/System**：看它如何把抽象主张落实成可观察的步骤、界面、流程或研究设计。",
            "- **Discussion**：留意作者如何承认限制，同时把发现推广到更大的 HCI/AI 设计问题。",
            "",
            f"> Source: {source_name}",
            "> Generated after PDF parsing; edit freely if you want a more personal reading voice.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_cloud_paper_explanation(metadata: dict[str, Any], segments: list[dict[str, Any]], outline: list[dict[str, Any]], source_name: str) -> str:
    if not cloud_llm_enabled() or not segments:
        return ""
    title = str(metadata.get("title") or "Untitled Paper")
    try:
        messages = [
            {
                "role": "system",
                "content": "你是 HCI/AI 学术论文阅读助手。请用中文生成清楚、具体、可编辑的论文解读，不能编造原文没有的信息。保留关键英文术语。",
            },
            {
                "role": "user",
                "content": f"""请基于下面论文文本生成 Paper Brief，严格使用这三个一级标题：
# 摘要：
# 研究问题：
# 解读：

要求：
1. 摘要和研究问题要尽量贴近原文。
2. 解读部分要像给研究者讲论文一样，具体说明问题、方法/系统、evaluation/findings、局限和可借鉴写法。
3. 使用中文；关键术语如 sensemaking, provenance, computational notebook, handoff 等保留英文。
4. 不要输出“我无法”等模板话，无法确定的信息请标为“原文未明确说明”。

Title: {title}
Source: {source_name}
Outline: {outline_markdown(outline, limit=12) or 'unknown'}

论文文本片段：
{paper_text_for_llm(segments)}
""",
            },
        ]
        return kimi_chat(messages, max_tokens=7000, temperature=0.2).rstrip() + "\n"
    except Exception as exc:  # noqa: BLE001
        print(f"Cloud paper explanation failed, falling back to local explanation: {exc}", file=sys.stderr)
        return ""


def update_explanation_from_pdf(paper_dir: Path, metadata: dict[str, Any], segments: list[dict[str, Any]], outline: list[dict[str, Any]], source_name: str, force: bool = False) -> dict[str, Any]:
    thinking = load_thinking(paper_dir)
    current = str(thinking.get("explain", {}).get("content") or "")
    if not force and current.strip() and not looks_like_auto_explanation(current):
        return thinking
    thinking["explain"] = {
        "content": build_paper_explanation(metadata, segments, outline, source_name),
        "updated_at": now_iso(),
        "source": "auto-pdf",
        "prompt": EXPLANATION_PROMPT,
    }
    cleaned = clean_thinking(thinking)
    write_json(paper_dir / "thinking.json", cleaned)
    write_text_atomic(paper_dir / "explanation_prompt.md", EXPLANATION_PROMPT.strip() + "\n")
    return cleaned


def update_paper_brief_from_pdf(workspace: Path, paper_dir: Path, metadata: dict[str, Any], source_name: str, force: bool = False) -> dict[str, Any]:
    pdf_path = paper_dir / "original.pdf"
    if not pdf_path.exists():
        raise FileNotFoundError("No original.pdf found for PDF Paper Brief generation.")
    thinking = load_thinking(paper_dir)
    current = str(thinking.get("explain", {}).get("content") or "")
    if not force and current.strip() and not looks_like_auto_explanation(current):
        apply_paper_brief_title_to_metadata(metadata, current, read_text_prefix(paper_dir / "paper_brief_kimi_extract.txt"))
        metadata.update({"paper_brief_status": metadata.get("paper_brief_status") or "ready", "agent_analysis_status": metadata.get("agent_analysis_status") or "paper_brief_ready", "updated_at": now_iso()})
        write_json(paper_dir / "metadata.json", metadata)
        sync_library_from_metadata(workspace, str(metadata.get("id") or paper_dir.name), paper_dir, metadata, generate_pdf_preview=False)
        return thinking
    prompt = chrome_brief_prompt(workspace)
    file_id = ""
    deleted = False
    try:
        file_object = kimi_upload_file_extract(pdf_path)
        file_id = str(file_object.get("id") or "")
        extracted_text = kimi_file_content(file_id)
        if not extracted_text.strip():
            raise RuntimeError("Kimi returned empty extracted text")
        write_text_atomic(paper_dir / "paper_brief_kimi_extract.txt", extracted_text)
        messages = [
            {"role": "system", "content": extracted_text[:180000]},
            {"role": "user", "content": prompt},
        ]
        brief = kimi_chat(messages, max_tokens=7000, temperature=0.2).rstrip() + "\n"
        apply_paper_brief_title_to_metadata(metadata, brief, extracted_text)
        if env_value("PAPER_READER_KIMI_DELETE_FILES", default="1").strip().lower() not in {"0", "false", "no"}:
            deleted = kimi_delete_file(file_id)
        thinking["explain"] = {
            "content": brief,
            "updated_at": now_iso(),
            "source": "kimi-pdf",
            "prompt": prompt,
            "model": kimi_model(),
        }
        cleaned = clean_thinking(thinking)
        write_json(paper_dir / "thinking.json", cleaned)
        write_text_atomic(paper_dir / "explanation_prompt.md", prompt.strip() + "\n")
        metadata.update(
            {
                "paper_brief_status": "ready",
                "paper_brief_source": "kimi-pdf",
                "paper_brief_model": kimi_model(),
                "paper_brief_prompt_id": DEFAULT_CHROME_BRIEF_PROMPT_ID,
                "paper_brief_source_name": source_name,
                "paper_brief_kimi_file_id": file_id,
                "paper_brief_kimi_file_deleted": deleted,
                "paper_brief_error": "",
                "paper_brief_updated_at": now_iso(),
                "agent_analysis_status": "paper_brief_ready",
                "updated_at": now_iso(),
            }
        )
        write_json(paper_dir / "metadata.json", metadata)
        sync_library_from_metadata(workspace, str(metadata.get("id") or paper_dir.name), paper_dir, metadata)
        return cleaned
    except Exception as exc:  # noqa: BLE001
        if file_id and env_value("PAPER_READER_KIMI_DELETE_FILES", default="1").strip().lower() not in {"0", "false", "no"}:
            deleted = kimi_delete_file(file_id)
        segments = load_segments(paper_dir)
        outline_data = read_json(paper_dir / "outline.json", {"outline": []})
        outline = outline_data.get("outline", []) if isinstance(outline_data, dict) else []
        if not segments and (paper_dir / "raw.md").exists():
            raw_md = (paper_dir / "raw.md").read_text(encoding="utf-8")
            segments, outline = build_segments(raw_md)
        brief = build_paper_explanation(metadata, segments, outline, source_name)
        thinking["explain"] = {
            "content": brief,
            "updated_at": now_iso(),
            "source": "local-pdf-fallback",
            "prompt": prompt,
            "fallback_reason": str(exc),
        }
        cleaned = clean_thinking(thinking)
        write_json(paper_dir / "thinking.json", cleaned)
        write_text_atomic(paper_dir / "explanation_prompt.md", prompt.strip() + "\n")
        metadata.update(
            {
                "paper_brief_status": "ready",
                "paper_brief_source": "local-pdf-fallback",
                "paper_brief_model": kimi_model(),
                "paper_brief_prompt_id": DEFAULT_CHROME_BRIEF_PROMPT_ID,
                "paper_brief_source_name": source_name,
                "paper_brief_kimi_file_id": file_id,
                "paper_brief_kimi_file_deleted": deleted,
                "paper_brief_error": f"Kimi PDF brief failed; used local fallback: {exc}",
                "paper_brief_updated_at": now_iso(),
                "agent_analysis_status": "paper_brief_ready",
                "updated_at": now_iso(),
            }
        )
        write_json(paper_dir / "metadata.json", metadata)
        sync_library_from_metadata(workspace, str(metadata.get("id") or paper_dir.name), paper_dir, metadata)
        return cleaned


def segment_number(segment_id: str) -> int:
    match = re.search(r"(\d+)$", str(segment_id or ""))
    return int(match.group(1)) if match else -1


def segment_id_from_number(number: int) -> str:
    return f"p-{max(0, int(number)):04d}"


def segment_text(segment: dict[str, Any], max_chars: int = 360) -> str:
    text = markdown_plain_text(segment.get("markdown", ""))
    if not text:
        text = markdown_plain_text(segment.get("translation", ""))
    return text[:max_chars].strip()


def chat_query_tokens(text: str) -> list[str]:
    raw = str(text or "").lower()
    tokens = re.findall(r"[a-z][a-z\-]{2,}|[\u4e00-\u9fff]{2,}", raw)
    stop = {
        "about",
        "after",
        "article",
        "paper",
        "study",
        "this",
        "that",
        "the",
        "with",
        "what",
        "when",
        "where",
        "which",
        "why",
        "how",
        "define",
        "definition",
        "这篇",
        "文章",
        "论文",
        "如何",
        "什么",
        "定义",
        "作者",
    }
    result: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        token = token.strip("-")
        if len(token) < 2 or token in stop or token in seen:
            continue
        seen.add(token)
        result.append(token)
    return result[:18]


def source_ref_from_segment(paper_id: str, segment: dict[str, Any], label: str = "") -> dict[str, str]:
    segment_id = str(segment.get("id") or "")
    quote = segment_text(segment, max_chars=620)
    return {
        "paper_id": paper_id,
        "segment_id": segment_id,
        "end_segment_id": segment_id,
        "source": "paper-segment",
        "label": label or segment_id,
        "quote": quote,
    }


def normalize_selection_refs_for_chat(paper_id: str, value: Any) -> list[dict[str, Any]]:
    refs = clean_selection_refs(value)
    for ref in refs:
        if not ref.get("paper_id"):
            ref["paper_id"] = paper_id
    return refs


def retrieve_chat_source_refs(paper_id: str, segments: list[dict[str, Any]], message: str, selection_refs: list[dict[str, Any]], limit: int = 5) -> list[dict[str, str]]:
    selected_ids = [str(ref.get("segment_id") or "") for ref in selection_refs if ref.get("segment_id")]
    by_id = {str(segment.get("id") or ""): segment for segment in segments}
    refs: list[dict[str, str]] = []
    seen: set[str] = set()
    for segment_id in selected_ids:
        segment = by_id.get(segment_id)
        if segment and segment_id not in seen:
            refs.append(source_ref_from_segment(paper_id, segment, segment_id))
            seen.add(segment_id)
    tokens = chat_query_tokens(message)
    if not tokens and len(refs) >= limit:
        return refs[:limit]
    scored: list[tuple[float, int, dict[str, Any]]] = []
    for index, segment in enumerate(segments):
        segment_id = str(segment.get("id") or "")
        if segment_id in seen or segment.get("kind") == "heading":
            continue
        text = markdown_plain_text(segment.get("markdown", "") or segment.get("translation", ""))
        if not text.strip():
            continue
        lowered = text.lower()
        score = 0.0
        for token in tokens:
            if token in lowered:
                score += 2.0 + min(3, lowered.count(token)) * 0.25
        for selected_id in selected_ids:
            distance = abs(segment_number(segment_id) - segment_number(selected_id))
            if distance <= 3:
                score += 1.2 / (distance + 1)
        if score > 0:
            scored.append((score, index, segment))
    scored.sort(key=lambda item: (-item[0], item[1]))
    for _score, _index, segment in scored:
        if len(refs) >= limit:
            break
        segment_id = str(segment.get("id") or "")
        if segment_id in seen:
            continue
        refs.append(source_ref_from_segment(paper_id, segment, segment_id))
        seen.add(segment_id)
    if not refs:
        for segment in segments:
            if segment.get("kind") == "heading":
                continue
            if segment_text(segment, max_chars=80):
                refs.append(source_ref_from_segment(paper_id, segment, str(segment.get("id") or "")))
                break
    return refs[:limit]


def chat_context_from_refs(source_refs: list[dict[str, str]]) -> str:
    lines = []
    for ref in source_refs:
        segment_id = ref.get("segment_id") or "source"
        quote = str(ref.get("quote") or "").strip()
        if quote:
            lines.append(f"[{segment_id}] {quote}")
    return "\n".join(lines)


def recent_thinking_context(thinking: dict[str, Any], limit: int = 4) -> str:
    blocks = thinking.get("blocks") if isinstance(thinking.get("blocks"), list) else []
    lines = []
    for block in blocks[:limit]:
        title = str(block.get("title") or "AI output")
        content = str(block.get("content") or "").strip()
        if not content:
            continue
        lines.append(f"## {title}\n{content[:900]}")
    return "\n\n".join(lines)


def generate_chat_reply(metadata: dict[str, Any], segments: list[dict[str, Any]], thinking: dict[str, Any], message: str, mode: str, source_refs: list[dict[str, str]], full_markdown: str = "", project_context: str = "") -> tuple[str, str]:
    title = str(metadata.get("title") or "Untitled Paper")
    paper_markdown = str(full_markdown or "").strip() or paper_markdown_for_chat(segments)
    project_context_block = f"\n\n项目背景 Context Cards（用户长期维护的项目背景摘要；只在和当前问题相关时使用）：\n{project_context.strip()}" if project_context.strip() else ""
    if mode == "source":
        source_context = chat_context_from_refs(source_refs)
        messages = [
            {
                "role": "system",
                "content": "你是 HCI/AI 论文阅读器。请基于提供的完整论文 Markdown 回答，不要只依赖 Paper Brief 或摘要；不要编造论文没有支持的信息。必要的时候可以结合 Markdown 表格、图式、章节结构解释论文。中文为主，关键术语保留英文。回答要像正常研究讨论：先直接回应问题，再解释论文里的机制、含义、与用户研究/系统设计的关系。",
            },
            {
                "role": "user",
                "content": f"""当前论文：{title}

用户问题：{message}
{project_context_block}

完整论文 Markdown（包含稳定段落锚点，例如 <a id="p-0001"></a>）：
{paper_markdown or '暂无论文 Markdown'}

用户选中或检索命中的重点片段（用于优先定位证据，但不要替代完整 Markdown）：
{source_context or '暂无重点片段'}

请回答用户问题。要求：
1. 写成 2-4 个有信息量的自然段，必要时可加少量 bullet；不要只给短关键词。
2. 每个依赖原文证据的重要解释，都尽量在相关句子或段落后面直接加段落引用，例如 [p-0019]；可以根据完整 Markdown 中的锚点推断段落 id。不要把所有引用集中放在最后。
3. 不要输出单独的“引用列表”或“来源如下”。
4. 如果完整 Markdown 仍不足以回答某个部分，请明确说证据不足，并说明还需要哪类原文证据。""",
            },
        ]
        return agent_chat(messages, max_tokens=2600, temperature=0.2)
    free_context = recent_thinking_context(thinking)
    messages = [
        {
            "role": "system",
            "content": "你是 HCI/AI 研究合作者。请基于提供的完整论文 Markdown 帮助用户做发散思考、研究设计启发和理论脉络整理；不要只依赖 Paper Brief 或摘要。中文回答，要像正常研究讨论一样展开：先给判断，再解释理由，再给可操作的下一步。",
        },
        {
            "role": "user",
            "content": f"""当前论文：{title}
{project_context_block}

完整论文 Markdown（包含稳定段落锚点，例如 <a id="p-0001"></a>）：
{paper_markdown or '暂无论文 Markdown'}

已有 AI output 摘要：
{free_context or '暂无'}

用户问题：{message}

请回答用户问题。要求：
1. 写成 2-4 个有信息量的自然段，必要时可加少量 bullet；不要只给短关键词。
2. 明确区分“论文已经支持的启发”和“你基于论文延伸出的设计/研究建议”。
3. 给出可以继续写进笔记、系统设计或 user study 分析里的具体表达。
4. 重要判断尽量引用完整 Markdown 中的段落锚点，例如 [p-0019]。""",
        },
    ]
    return agent_chat(messages, max_tokens=2800, temperature=0.4)


def append_chat_output_block(paper_id: str, paper_dir: Path, data: dict[str, Any]) -> dict[str, Any]:
    message = str(data.get("message") or "")
    if not message.strip():
        raise ValueError("message is required")
    mode = str(data.get("mode") or "source").strip().lower()
    if mode not in {"source", "free"}:
        mode = "source"
    metadata = normalized_metadata(paper_dir, read_json(paper_dir / "metadata.json", {}))
    segments = load_segments(paper_dir)
    thinking = load_thinking(paper_dir)
    project_context = ""
    project_context_info: dict[str, Any] = {}
    if bool(data.get("use_project_context")):
        paper_projects = metadata_projects(metadata)
        project = normalize_project_name(data.get("project") or (paper_projects[0] if paper_projects else "")) or "collaborative"
        context = load_project_context(paper_dir.parent.parent, project)
        project_context = project_context_summary_for_prompt(context)
        project_context_info = {
            "project": project,
            "card_count": len(context.get("cards", [])),
            "source_path": context.get("source_path", ""),
        }
    selection_refs = normalize_selection_refs_for_chat(paper_id, data.get("selection_refs"))
    source_refs = retrieve_chat_source_refs(paper_id, segments, message, selection_refs, limit=7) if mode == "source" else []
    paper_markdown = load_paper_markdown_for_chat(paper_dir, segments)
    context_mode = "full"
    context_error = ""
    context_markdown = paper_markdown
    if len(paper_markdown) > CHAT_FULL_MARKDOWN_CHAR_LIMIT:
        context_mode = "compressed_size_limit"
        context_markdown = compressed_paper_markdown_for_chat(segments, source_refs, message)
    try:
        content, model_label = generate_chat_reply(metadata, segments, thinking, message, mode, source_refs, context_markdown, project_context)
    except Exception as exc:  # noqa: BLE001
        if context_mode.startswith("compressed") or not should_retry_chat_with_compressed_context(exc):
            raise
        context_mode = "compressed_after_error"
        context_error = str(exc)
        context_markdown = compressed_paper_markdown_for_chat(segments, source_refs, message)
        content, model_label = generate_chat_reply(metadata, segments, thinking, message, mode, source_refs, context_markdown, project_context)
    now = now_iso()
    block = {
        "id": f"tb-chat-{hashlib.sha1((paper_id + message + now).encode('utf-8')).hexdigest()[:12]}",
        "type": "ai_output",
        "title": "",
        "content": content,
        "prompt": message,
        "mode": mode,
        "model": model_label,
        "context_mode": context_mode,
        "context_chars": len(paper_markdown),
        "context_error": context_error[:800],
        "project_context": project_context_info,
        "source_refs": source_refs,
        "selection_refs": selection_refs,
        "created_at": now,
        "updated_at": now,
    }
    thinking.setdefault("blocks", [])
    thinking["blocks"].insert(0, block)
    cleaned = clean_thinking(thinking)
    write_json(paper_dir / "thinking.json", cleaned)
    schedule_export_notes_and_annotated(paper_dir)
    return {"thinking": cleaned, "block": next((item for item in cleaned["blocks"] if item["id"] == block["id"]), block)}


def thinking_block_lookup(thinking: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(block.get("id") or ""): block for block in thinking.get("blocks", []) if isinstance(block, dict)}


def annotation_sort_key(item: dict[str, Any]) -> tuple[int, str]:
    segment_id = str(item.get("segment_id") or item.get("block_id") or "")
    return (segment_number(segment_id), str(item.get("updated_at") or item.get("created_at") or ""))


def reading_narrative_evidence_context(paper_id: str, paper_dir: Path, segments: list[dict[str, Any]], thinking: dict[str, Any], max_items: int = 72) -> tuple[str, list[dict[str, str]]]:
    segment_lookup = {str(segment.get("id") or ""): segment for segment in segments if isinstance(segment, dict)}
    paper_annotations = read_json(paper_dir / "annotations.json", {"annotations": []}).get("annotations", [])
    blocks = thinking_block_lookup(thinking)
    evidence: list[dict[str, Any]] = []

    for annotation in paper_annotations if isinstance(paper_annotations, list) else []:
        if not isinstance(annotation, dict):
            continue
        quote = str(annotation.get("quote") or "").strip()
        note = str(annotation.get("note") or "").strip()
        segment_id = str(annotation.get("segment_id") or "").strip()
        if not quote and not note:
            continue
        segment_text = markdown_plain_text(segment_lookup.get(segment_id, {}).get("markdown", ""))[:900]
        evidence.append(
            {
                "source": "paper-highlight",
                "annotation_id": str(annotation.get("id") or ""),
                "segment_id": segment_id,
                "label": segment_id or str(annotation.get("id") or "highlight"),
                "quote": quote[:900],
                "note": note[:1000],
                "tags": annotation.get("tags", []),
                "color": str(annotation.get("color") or ""),
                "context": segment_text,
                "updated_at": str(annotation.get("updated_at") or annotation.get("created_at") or ""),
            }
        )

    for annotation in thinking.get("annotations", []) if isinstance(thinking.get("annotations"), list) else []:
        if not isinstance(annotation, dict):
            continue
        quote = str(annotation.get("quote") or "").strip()
        note = str(annotation.get("note") or "").strip()
        block_id = str(annotation.get("block_id") or "").strip()
        if not quote and not note:
            continue
        block = blocks.get(block_id, {})
        block_title = "Paper Brief" if block_id == PAPER_BRIEF_BLOCK_ID else str(block.get("title") or block.get("prompt") or "AI output")
        evidence.append(
            {
                "source": "thinking-note",
                "annotation_id": str(annotation.get("id") or ""),
                "block_id": block_id,
                "label": block_title,
                "quote": quote[:900],
                "note": note[:1000],
                "tags": annotation.get("tags", []),
                "color": str(annotation.get("color") or ""),
                "context": markdown_plain_text(str(block.get("content") or ""))[:900],
                "updated_at": str(annotation.get("updated_at") or annotation.get("created_at") or ""),
            }
        )

    evidence.sort(key=annotation_sort_key)
    note_items = [item for item in evidence if item.get("note")]
    highlight_items = [item for item in evidence if not item.get("note")]
    selected = (note_items + highlight_items)[:max_items]
    lines: list[str] = []
    source_refs: list[dict[str, str]] = []
    for index, item in enumerate(selected, start=1):
        label = str(item.get("label") or item.get("segment_id") or item.get("block_id") or f"evidence-{index}")
        tags = item.get("tags") if isinstance(item.get("tags"), list) else []
        lines.append(f"### E{index}: {item.get('source')} · {label}")
        if item.get("note"):
            lines.append(f"My note: {item['note']}")
        if item.get("quote"):
            lines.append(f"Highlight: {item['quote']}")
        if tags:
            lines.append("Tags: " + ", ".join(str(tag) for tag in tags if str(tag).strip()))
        if item.get("context"):
            lines.append(f"Nearby paper/context text: {item['context']}")
        lines.append("")
        source_refs.append(
            {
                "paper_id": paper_id,
                "annotation_id": str(item.get("annotation_id") or ""),
                "segment_id": str(item.get("segment_id") or ""),
                "block_id": str(item.get("block_id") or ""),
                "source": str(item.get("source") or ""),
                "label": label,
                "quote": str(item.get("quote") or item.get("note") or "")[:900],
            }
        )
    return "\n".join(lines).strip() or "暂无用户高亮或 note。", source_refs


def takeaway_doc_context(takeaway_doc: dict[str, Any], max_chars: int = 6500) -> str:
    lines: list[str] = []
    for block in takeaway_doc.get("blocks", []) if isinstance(takeaway_doc.get("blocks"), list) else []:
        text = str(block.get("text") or "").strip()
        if not text:
            continue
        indent = max(0, int(block.get("indent") or 0))
        prefix = "#" * max(1, min(3, int(block.get("level") or 2))) if block.get("type") == "heading" else "-"
        lines.append(f"{'  ' * indent}{prefix} {text}")
    result = "\n".join(lines).strip()
    return result[:max_chars].rstrip() + ("\n..." if len(result) > max_chars else "")


def outline_context_for_narrative(outline_data: dict[str, Any], max_items: int = 18) -> str:
    outline = outline_data.get("outline") if isinstance(outline_data.get("outline"), list) else []
    titles = []
    for item in outline:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if title and not should_skip_presentation_heading(title):
            titles.append(title)
        if len(titles) >= max_items:
            break
    return " -> ".join(titles)


def generate_reading_narrative(
    metadata: dict[str, Any],
    segments: list[dict[str, Any]],
    thinking: dict[str, Any],
    takeaway_doc: dict[str, Any],
    outline_data: dict[str, Any],
    evidence_context: str,
    project_context: str,
) -> tuple[str, str, str]:
    title = str(metadata.get("title") or "Untitled Paper")
    project = ", ".join(metadata_projects(metadata)) or "unknown"
    paper_brief = str(thinking.get("explain", {}).get("content") or "").strip()[:9000]
    takeaway = takeaway_doc_context(takeaway_doc)
    outline = outline_context_for_narrative(outline_data)
    if not cloud_llm_enabled():
        raise RuntimeError("Kimi API key is not configured. Set PAPER_READER_KIMI_API_KEY or MOONSHOT_API_KEY and restart the app.")
    messages = [
        {
            "role": "system",
            "content": "你是用户的 HCI/AI 论文阅读合作者。你的任务不是重写摘要，而是把用户的 highlights/notes 整合成一篇可回看、可转发、能服务项目推进的 reading narrative。必须忠于用户留下的 note 和高亮；不要把没有证据的猜测写成确定结论。中文为主，关键术语保留英文。",
        },
        {
            "role": "user",
            "content": f"""请为这篇论文生成一篇 Reading Narrative。

论文：{title}
项目：{project}
作者/年份/ venue：{metadata.get('authors') or 'unknown'} / {metadata.get('year') or metadata.get('publication_year') or 'unknown'} / {metadata.get('venue') or metadata.get('journal') or 'unknown'}

论文结构：
{outline or '暂无稳定 outline'}

Paper Brief（只作为背景，不要照抄）：
{paper_brief or '暂无 Paper Brief'}

用户 highlights / notes（最高优先级；请把它当成“用户真正关心什么”的证据）：
{evidence_context}

当前 Takeaway Report 草稿（可能很硬；只用来理解用户已经归类过哪些点）：
{takeaway or '暂无 Takeaway Report'}

项目背景 Context Cards（如果有，请说明这篇论文对项目哪里有用；没有就不要硬编）：
{project_context or '暂无 project context'}

输出要求：
1. 写成一篇可以直接贴到群里的 narrative，不要是字段表；长度约 900-1500 中文字。
2. 开头先用 2-3 句话讲“我今天读到的核心是什么，以及为什么它和我的项目有关”。
3. 中间要有“我之后回看这篇论文应该重点看哪里”，用 3-6 条 bullet，每条都说明为什么值得回看，并尽量带段落锚点如 [p-0123] 或高亮证据。
4. 要有“它能怎么进入我的项目/论文”：区分 motivation、related work、method/design inspiration、discussion/limitation，不能每类都硬写，只有有证据才写。
5. 必须保留用户自己的宝贵思考：如果 note 里有第一人称、疑问、可借鉴、担心、类比，请优先转述；不要把它磨平成普通摘要。
6. 对证据不足的地方要说“这只是启发，不适合直接作为 claim”。
7. 不要输出“以下是/总之/综上”这种模板话；语气像研究伙伴给组里讲今天读了什么。
8. 每个重要判断后尽量附原文段落锚点或 evidence 编号，例如 [p-0031] / [E4]。""",
        },
    ]
    content, model = agent_chat(messages, max_tokens=3600, temperature=0.35)
    return content.strip() + "\n", model, "llm"


def append_reading_narrative_block(workspace: Path, paper_id: str, paper_dir: Path, data: dict[str, Any]) -> dict[str, Any]:
    metadata = normalized_metadata(paper_dir, read_json(paper_dir / "metadata.json", {}))
    segments = load_segments(paper_dir)
    thinking = load_thinking(paper_dir)
    takeaway_doc = load_takeaway_doc(paper_dir)
    outline_data = read_json(paper_dir / "outline.json", {"outline": [], "presentation_flow": []})
    evidence_context, source_refs = reading_narrative_evidence_context(paper_id, paper_dir, segments, thinking)
    project_context = ""
    project_context_info: dict[str, Any] = {}
    if bool(data.get("use_project_context", True)):
        paper_projects = metadata_projects(metadata)
        project = normalize_project_name(data.get("project") or (paper_projects[0] if paper_projects else "")) or "collaborative"
        context = load_project_context(workspace, project)
        project_context = project_context_summary_for_prompt(context)
        project_context_info = {
            "project": project,
            "card_count": len(context.get("cards", [])),
            "source_path": context.get("source_path", ""),
        }
    content, model_label, context_mode = generate_reading_narrative(metadata, segments, thinking, takeaway_doc, outline_data, evidence_context, project_context)
    now = now_iso()
    prompt = "Generate a source-grounded reading narrative from my highlights, notes, Takeaway Report, Paper Brief, and project context."
    block = {
        "id": f"tb-narrative-{hashlib.sha1((paper_id + now).encode('utf-8')).hexdigest()[:12]}",
        "type": "ai_output",
        "title": "Reading Narrative",
        "content": content,
        "prompt": prompt,
        "mode": "reading_narrative",
        "model": model_label,
        "context_mode": context_mode,
        "context_chars": len(evidence_context) + len(project_context),
        "project_context": project_context_info,
        "source_refs": source_refs[:16],
        "created_at": now,
        "updated_at": now,
    }
    thinking.setdefault("blocks", [])
    thinking["blocks"].insert(0, block)
    cleaned = clean_thinking(thinking)
    write_json(paper_dir / "thinking.json", cleaned)
    return {"thinking": cleaned, "block": next((item for item in cleaned["blocks"] if item["id"] == block["id"]), block)}


def delete_thinking_block(paper_dir: Path, block_id: str) -> dict[str, Any]:
    thinking = load_thinking(paper_dir)
    thinking["blocks"] = [block for block in thinking.get("blocks", []) if str(block.get("id") or "") != block_id]
    thinking["annotations"] = [item for item in thinking.get("annotations", []) if str(item.get("block_id") or "") != block_id]
    cleaned = clean_thinking(thinking)
    write_json(paper_dir / "thinking.json", cleaned)
    schedule_export_notes_and_annotated(paper_dir)
    return cleaned


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"\b[A-Za-z][A-Za-z-]{3,}\b", str(text or ""))
    stop = {
        "about",
        "after",
        "among",
        "based",
        "between",
        "paper",
        "study",
        "system",
        "systems",
        "their",
        "these",
        "those",
        "through",
        "using",
        "which",
        "while",
        "with",
    }
    result: list[str] = []
    seen: set[str] = set()
    for word in words:
        key = word.lower().strip("-")
        if key in stop or key in seen:
            continue
        seen.add(key)
        result.append(word)
        if len(result) >= limit:
            break
    return result


def flow_title_for_heading(title: str) -> str:
    clean = re.sub(r"^\d+(?:\.\d+)*\s+", "", str(title or "")).strip() or "Paper Flow"
    lowered = clean.lower()
    if "abstract" in lowered:
        return "摘要主张：" + clean
    if any(word in lowered for word in ["introduction", "background", "related", "motivation", "problem"]):
        return "问题设定：" + clean
    if any(word in lowered for word in ["method", "system", "design", "framework", "approach", "implementation"]):
        return "方法/系统：" + clean
    if any(word in lowered for word in ["study", "evaluation", "experiment", "result", "finding"]):
        return "研究发现：" + clean
    if any(word in lowered for word in ["discussion", "implication", "limitation", "future", "conclusion"]):
        return "讨论启示：" + clean
    return clean


def chinese_core_summary(title: str, content: str = "") -> str:
    lowered = str(title or "").lower()
    if "abstract" in lowered:
        return "本节概括论文的问题、方法和主要贡献，适合作为汇报开场的总览。"
    if any(word in lowered for word in ["introduction", "background", "motivation", "problem"]):
        return "本节交代研究动机、核心问题和本文要解决的缺口。"
    if "related" in lowered:
        return "本节梳理相关工作，并定位本文相对既有研究的差异。"
    if any(word in lowered for word in ["method", "system", "design", "framework", "approach", "implementation"]):
        return "本节说明方法或系统设计，包括关键组件、流程和设计取舍。"
    if any(word in lowered for word in ["study", "evaluation", "experiment", "participant", "procedure"]):
        return "本节说明研究设计、参与者、任务流程和评价方式。"
    if any(word in lowered for word in ["result", "finding", "analysis"]):
        return "本节总结主要发现，并说明这些证据如何支撑论文主张。"
    if any(word in lowered for word in ["discussion", "implication", "limitation", "future", "conclusion"]):
        return "本节提炼讨论、设计启示、适用边界和未来工作。"
    chinese = re.findall(r"[\u4e00-\u9fff][\u4e00-\u9fff，。；：、（）《》“”\s]{12,}", str(content or ""))
    if chinese:
        snippet = re.sub(r"\s+", "", chinese[0])[:56].rstrip("，。；：、")
        return f"本节围绕“{snippet}”展开，适合作为该部分的汇报节点。"
    return "本节是论文论证链条中的一个主干节点，可用于承接前后文并组织相关笔记。"


def should_skip_presentation_heading(title: str, metadata: dict[str, Any] | None = None) -> bool:
    clean = re.sub(r"\s+", " ", str(title or "")).strip()
    lowered = clean.lower()
    if not lowered:
        return True
    paper_title = re.sub(r"\s+", " ", str((metadata or {}).get("title") or "")).strip().lower()
    if paper_title and (lowered == paper_title or lowered in paper_title or paper_title in lowered):
        return True
    skip_markers = [
        "ccs concepts",
        "keywords",
        "author keywords",
        "acm reference format",
        "reference format",
        "references",
        "acknowledg",
        "appendix",
    ]
    return any(marker in lowered for marker in skip_markers)


def first_content_segment(segments: list[dict[str, Any]], start: int, end: int) -> dict[str, Any] | None:
    for segment in segments:
        number = segment_number(segment.get("id", ""))
        if number < start or number > end:
            continue
        if segment.get("kind") != "heading" and segment_text(segment, max_chars=80):
            return segment
    return None


def build_presentation_flow(metadata: dict[str, Any], segments: list[dict[str, Any]], outline: list[dict[str, Any]], max_nodes: int = 7) -> list[dict[str, Any]]:
    if not segments:
        return []
    headings = [item for item in outline if item.get("id") and item.get("title") and int(item.get("level") or 2) <= 3 and not should_skip_presentation_heading(str(item.get("title") or ""), metadata)]
    if headings and len(headings) > 1 and headings[0].get("title", "").strip().lower() == str(metadata.get("title", "")).strip().lower():
        headings = headings[1:]
    if not headings:
        step = max(1, len(segments) // 5)
        headings = [
            {"id": segment.get("id"), "title": f"Flow {index + 1}", "level": 2}
            for index, segment in enumerate(segments[::step][:5])
            if segment.get("id")
        ]
    headings = headings[:max_nodes]
    all_segment_numbers = [segment_number(segment.get("id", "")) for segment in segments if segment_number(segment.get("id", "")) > 0]
    last_number = max(all_segment_numbers) if all_segment_numbers else 1
    flow: list[dict[str, Any]] = []
    for index, heading in enumerate(headings):
        start = segment_number(str(heading.get("id") or ""))
        if start <= 0:
            continue
        if index + 1 < len(headings):
            next_start = segment_number(str(headings[index + 1].get("id") or ""))
            end = max(start, next_start - 1) if next_start > start else start
        else:
            end = last_number
        content = first_content_segment(segments, start, end)
        anchor_ids = [str(heading.get("id"))]
        if content and content.get("id") not in anchor_ids:
            anchor_ids.append(str(content.get("id")))
        source_text = segment_text(content or next((segment for segment in segments if segment.get("id") == heading.get("id")), {}), max_chars=260)
        title = flow_title_for_heading(str(heading.get("title") or f"Flow {index + 1}"))
        core_text = chinese_core_summary(str(heading.get("title") or title), source_text)
        basis = f"{title} {source_text}"
        flow.append(
            {
                "id": f"flow-{index + 1}",
                "title": title,
                "core": core_text or title,
                "anchors": anchor_ids[:5],
                "anchor_ranges": [[segment_id_from_number(start), segment_id_from_number(end)]],
                "keywords": extract_keywords(basis, limit=8),
            }
        )
    return flow


def build_skim_analysis(metadata: dict[str, Any], segments: list[dict[str, Any]], outline: list[dict[str, Any]], source_name: str) -> dict[str, Any]:
    skim_summary = build_skim_summary(metadata, segments, source_name)
    return {
        "metadata": {
            "authors": metadata.get("authors", ""),
            "institutions": metadata.get("institutions", ""),
            "venue": metadata.get("venue", ""),
            "year": metadata.get("year", ""),
            "abstract": metadata.get("abstract", ""),
            "research_question": metadata.get("research_question", ""),
        },
        "skim_summary": skim_summary,
        "presentation_flow": build_presentation_flow(metadata, segments, outline),
        "source": source_name,
        "generated_at": now_iso(),
    }


def register_paper_in_library(
    workspace: Path,
    pdf_path: Path,
    paper_id: str | None = None,
    title: str | None = None,
    tags: list[str] | None = None,
    projects: list[str] | None = None,
    tag_colors: dict[str, str] | None = None,
    project_colors: dict[str, str] | None = None,
    duplicate_policy: str = "ask",
    replace_paper_id: str | None = None,
    pdf_digest: str | None = None,
    generate_pdf_preview: bool = False,
    enrich_citation: bool = False,
    title_source: str | None = None,
    match_title: bool = True,
) -> dict[str, Any]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    digest = str(pdf_digest or "").strip().lower()[:12] or file_hash(pdf_path, limit=None)[:12]
    candidate_title = title or pdf_path.stem
    duplicate = find_duplicate_paper_by_title(workspace, candidate_title, exclude_paper_id=paper_id) if match_title else None
    auto_attached_to = ""
    if duplicate and duplicate_policy != "replace":
        if duplicate_can_accept_pdf(workspace, duplicate):
            auto_attached_to = str(duplicate.get("id") or "")
            replace_paper_id = auto_attached_to
            duplicate_policy = "replace"
            duplicate_dir = paper_record_dir(workspace, duplicate)
            duplicate_metadata = read_json(duplicate_dir / "metadata.json", {}) if duplicate_dir.exists() else {}
            candidate_title = duplicate_metadata.get("title") or duplicate.get("title") or candidate_title
        else:
            return duplicate_paper_response(workspace, candidate_title, pdf_path.name, duplicate)
    next_paper_id = replace_paper_id or paper_id or f"{slugify(pdf_path.stem)}-{digest}"
    paper_dir = workspace / "papers" / next_paper_id
    backup_dir = backup_paper_before_replace(paper_dir) if duplicate_policy == "replace" and paper_dir.exists() else ""
    paper_dir.mkdir(parents=True, exist_ok=True)
    destination_pdf = paper_dir / "original.pdf"
    if pdf_path.resolve() != destination_pdf.resolve():
        shutil.copy2(pdf_path, destination_pdf)
    metadata = read_json(paper_dir / "metadata.json", {})
    metadata.update(
        {
            "id": next_paper_id,
            "title": candidate_title or metadata.get("title") or pdf_path.stem,
            "title_key": normalize_title_key(candidate_title or metadata.get("title") or pdf_path.stem),
            "title_source": title_source or ("user" if title else metadata.get("title_source", "filename")),
            "source_pdf": "original.pdf",
            "source_pdf_name": pdf_path.name,
            "original_path": str(pdf_path),
            "source_type": "pdf" if auto_attached_to else metadata.get("source_type", "pdf"),
            "created_at": metadata.get("created_at") or now_iso(),
            "created_or_refreshed_at": metadata.get("created_or_refreshed_at") or now_iso(),
            "updated_at": now_iso(),
            "status": metadata.get("status", "unread"),
            "read_status": metadata.get("read_status", "unread"),
            "processing_mode": metadata.get("processing_mode", "library-only"),
            "reading_mode": metadata.get("reading_mode", "library-only"),
            "processing_status": metadata.get("processing_status", "not_processed"),
            "processing_error": "",
            "venue": metadata.get("venue", ""),
            "year": metadata.get("year", ""),
            "authors": metadata.get("authors", ""),
            "institutions": metadata.get("institutions", ""),
            "importance": metadata.get("importance", ""),
            "tags": tags if tags is not None else metadata.get("tags", []),
            "projects": projects if projects is not None else metadata.get("projects", []),
            "project": (projects[0] if projects else "") if projects is not None else metadata.get("project", ""),
            "tag_colors": tag_colors if tag_colors is not None else metadata.get("tag_colors", {}),
            "project_colors": project_colors if project_colors is not None else metadata.get("project_colors", {}),
            "agent_analysis_status": metadata.get("agent_analysis_status", "not_started"),
            "replacement_backup_dir": backup_dir or metadata.get("replacement_backup_dir", ""),
        }
    )
    if enrich_citation:
        metadata = metadata_with_citation(metadata)
    write_json(paper_dir / "metadata.json", metadata)
    if not (paper_dir / "segments.json").exists():
        write_json(paper_dir / "segments.json", [])
    if not (paper_dir / "outline.json").exists():
        write_json(paper_dir / "outline.json", {"outline": [], "core_locations": []})
    if not (paper_dir / "annotations.json").exists():
        write_json(paper_dir / "annotations.json", {"annotations": []})
    if not (paper_dir / "reader.md").exists():
        write_text_atomic(paper_dir / "reader.md", f"# {metadata['title']}\n\nThis paper is in Library only. Choose 略读 or 精读 from the Library page.\n")
    sync_library_from_metadata(workspace, next_paper_id, paper_dir, metadata, generate_pdf_preview=generate_pdf_preview)
    return {"ok": True, "paper_id": next_paper_id, "metadata": metadata, "replaced": bool(backup_dir), "backup_dir": backup_dir, "attached_to_existing": bool(auto_attached_to), "auto_attached_to": auto_attached_to}


def register_uploaded_pdf(
    workspace: Path,
    filename: str,
    content: bytes,
    paper_id: str | None = None,
    title: str | None = None,
    tags: list[str] | None = None,
    projects: list[str] | None = None,
    tag_colors: dict[str, str] | None = None,
    project_colors: dict[str, str] | None = None,
    duplicate_policy: str = "ask",
    replace_paper_id: str | None = None,
    generate_pdf_preview: bool = False,
    enrich_citation: bool = False,
) -> dict[str, Any]:
    if not content:
        raise ValueError(f"Empty PDF upload: {filename}")
    digest = hashlib.sha256(content).hexdigest()[:12]
    stem = Path(filename).stem or "paper"
    candidate_title = title or stem
    duplicate = find_duplicate_paper_by_title(workspace, candidate_title, exclude_paper_id=paper_id)
    auto_attached_to = ""
    if duplicate and duplicate_policy != "replace":
        if duplicate_can_accept_pdf(workspace, duplicate):
            auto_attached_to = str(duplicate.get("id") or "")
            replace_paper_id = auto_attached_to
            duplicate_policy = "replace"
            duplicate_dir = paper_record_dir(workspace, duplicate)
            duplicate_metadata = read_json(duplicate_dir / "metadata.json", {}) if duplicate_dir.exists() else {}
            candidate_title = duplicate_metadata.get("title") or duplicate.get("title") or candidate_title
        else:
            return duplicate_paper_response(workspace, candidate_title, filename, duplicate)
    next_paper_id = replace_paper_id or paper_id or f"{slugify(stem)}-{digest}"
    paper_dir = workspace / "papers" / next_paper_id
    backup_dir = backup_paper_before_replace(paper_dir) if duplicate_policy == "replace" and paper_dir.exists() else ""
    paper_dir.mkdir(parents=True, exist_ok=True)
    destination_pdf = paper_dir / "original.pdf"
    destination_pdf.write_bytes(content)
    metadata = read_json(paper_dir / "metadata.json", {})
    metadata.update(
        {
            "id": next_paper_id,
            "title": candidate_title or metadata.get("title") or stem,
            "title_key": normalize_title_key(candidate_title or metadata.get("title") or stem),
            "title_source": "user" if title else metadata.get("title_source", "filename"),
            "source_pdf": "original.pdf",
            "source_pdf_name": filename,
            "original_path": "",
            "source_type": "pdf" if auto_attached_to else metadata.get("source_type", "pdf"),
            "created_at": metadata.get("created_at") or now_iso(),
            "created_or_refreshed_at": metadata.get("created_or_refreshed_at") or now_iso(),
            "updated_at": now_iso(),
            "status": metadata.get("status", "unread"),
            "read_status": metadata.get("read_status", "unread"),
            "processing_mode": metadata.get("processing_mode", "library-only"),
            "reading_mode": metadata.get("reading_mode", "library-only"),
            "processing_status": metadata.get("processing_status", "not_processed"),
            "processing_error": "",
            "venue": metadata.get("venue", ""),
            "year": normalize_year(metadata.get("year", "")),
            "authors": metadata.get("authors", ""),
            "institutions": metadata.get("institutions", ""),
            "importance": metadata.get("importance", ""),
            "tags": tags if tags is not None else metadata.get("tags", []),
            "projects": projects if projects is not None else metadata.get("projects", []),
            "project": (projects[0] if projects else "") if projects is not None else metadata.get("project", ""),
            "tag_colors": tag_colors if tag_colors is not None else metadata.get("tag_colors", {}),
            "project_colors": project_colors if project_colors is not None else metadata.get("project_colors", {}),
            "agent_analysis_status": metadata.get("agent_analysis_status", "not_started"),
            "replacement_backup_dir": backup_dir or metadata.get("replacement_backup_dir", ""),
        }
    )
    if enrich_citation:
        metadata = metadata_with_citation(metadata)
    write_json(paper_dir / "metadata.json", metadata)
    if not (paper_dir / "segments.json").exists():
        write_json(paper_dir / "segments.json", [])
    if not (paper_dir / "outline.json").exists():
        write_json(paper_dir / "outline.json", {"outline": [], "core_locations": []})
    if not (paper_dir / "annotations.json").exists():
        write_json(paper_dir / "annotations.json", {"annotations": []})
    if not (paper_dir / "reader.md").exists():
        write_text_atomic(paper_dir / "reader.md", f"# {metadata['title']}\n\nThis paper is in Library only. Choose 略读 or 精读 from the Library page.\n")
    sync_library_from_metadata(workspace, next_paper_id, paper_dir, metadata, generate_pdf_preview=generate_pdf_preview)
    return {"ok": True, "paper_id": next_paper_id, "metadata": metadata, "replaced": bool(backup_dir), "backup_dir": backup_dir, "attached_to_existing": bool(auto_attached_to), "auto_attached_to": auto_attached_to}


def register_metadata_only_paper(
    workspace: Path,
    title: str,
    tags: list[str] | None = None,
    projects: list[str] | None = None,
    tag_colors: dict[str, str] | None = None,
    project_colors: dict[str, str] | None = None,
    paper_id: str | None = None,
    metadata_fields: dict[str, Any] | None = None,
    duplicate_policy: str = "ask",
    replace_paper_id: str | None = None,
) -> dict[str, Any]:
    clean_title = str(title or "").strip()
    if not clean_title:
        raise ValueError("title is required when adding a paper without a PDF")
    duplicate = find_duplicate_paper_by_title(workspace, clean_title, exclude_paper_id=paper_id)
    if duplicate and duplicate_policy != "replace":
        return duplicate_paper_response(workspace, clean_title, "metadata-only", duplicate)
    digest = hashlib.sha256(clean_title.encode("utf-8")).hexdigest()[:12]
    next_paper_id = replace_paper_id or paper_id or f"{slugify(clean_title, 'paper')}-{digest}"
    paper_dir = workspace / "papers" / next_paper_id
    backup_dir = backup_paper_before_replace(paper_dir) if duplicate_policy == "replace" and paper_dir.exists() else ""
    paper_dir.mkdir(parents=True, exist_ok=True)
    metadata_fields = metadata_fields if isinstance(metadata_fields, dict) else {}
    metadata = read_json(paper_dir / "metadata.json", {})
    metadata.update(
        {
            "id": next_paper_id,
            "title": clean_title,
            "title_key": normalize_title_key(clean_title),
            "title_source": "user",
            "source_pdf": "",
            "source_pdf_name": "",
            "original_path": "",
            "source_type": "metadata",
            "created_at": metadata.get("created_at") or now_iso(),
            "created_or_refreshed_at": metadata.get("created_or_refreshed_at") or now_iso(),
            "updated_at": now_iso(),
            "status": metadata.get("status", "unread"),
            "read_status": metadata.get("read_status", "unread"),
            "processing_mode": "library-only",
            "reading_mode": "library-only",
            "processing_status": "not_processed",
            "processing_error": "",
            "venue": metadata_fields.get("venue") or metadata_fields.get("journal") or metadata.get("venue", ""),
            "year": normalize_year(metadata_fields.get("year") or metadata_fields.get("publication_year") or metadata.get("year", "")),
            "authors": metadata_fields.get("authors") or metadata_fields.get("author") or metadata.get("authors", ""),
            "institutions": metadata_fields.get("institutions") or metadata_fields.get("institution") or metadata.get("institutions", ""),
            "abstract": metadata_fields.get("abstract") or metadata.get("abstract", ""),
            "doi": metadata_fields.get("doi") or metadata.get("doi", ""),
            "url": metadata_fields.get("url") or metadata.get("url", ""),
            "pdf_url": metadata_fields.get("pdf_url") or metadata_fields.get("open_access_pdf_url") or metadata.get("pdf_url", ""),
            "open_access_pdf_url": metadata_fields.get("open_access_pdf_url") or metadata.get("open_access_pdf_url", ""),
            "semantic_scholar_url": metadata_fields.get("semantic_scholar_url") or metadata.get("semantic_scholar_url", ""),
            "arxiv_id": metadata_fields.get("arxiv_id") or metadata.get("arxiv_id", ""),
            "importance": metadata_fields.get("importance") or metadata.get("importance", ""),
            "tags": tags if tags is not None else metadata.get("tags", []),
            "projects": projects if projects is not None else metadata.get("projects", []),
            "project": (projects[0] if projects else "") if projects is not None else metadata.get("project", ""),
            "tag_colors": tag_colors if tag_colors is not None else metadata.get("tag_colors", {}),
            "project_colors": project_colors if project_colors is not None else metadata.get("project_colors", {}),
            "agent_analysis_status": "metadata_only",
            "replacement_backup_dir": backup_dir or metadata.get("replacement_backup_dir", ""),
        }
    )
    write_json(paper_dir / "metadata.json", metadata)
    if not (paper_dir / "segments.json").exists():
        write_json(paper_dir / "segments.json", [])
    if not (paper_dir / "outline.json").exists():
        write_json(paper_dir / "outline.json", {"outline": [], "core_locations": [], "presentation_flow": []})
    if not (paper_dir / "annotations.json").exists():
        write_json(paper_dir / "annotations.json", {"annotations": []})
    if not (paper_dir / "reader.md").exists():
        write_text_atomic(paper_dir / "reader.md", f"# {clean_title}\n\nNo PDF attached yet. Attach a PDF to parse its source Markdown.\n")
    sync_library_from_metadata(workspace, next_paper_id, paper_dir, metadata, generate_pdf_preview=False)
    return {"ok": True, "paper_id": next_paper_id, "metadata": metadata, "replaced": bool(backup_dir), "backup_dir": backup_dir}


def process_paper_skim(workspace: Path, paper_id: str, paper_dir: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
    options = options or {}
    metadata = read_json(paper_dir / "metadata.json", {})
    metadata.update({"processing_mode": "skim", "reading_mode": "skim", "processing_status": "processing", "processing_error": "", "updated_at": now_iso()})
    write_json(paper_dir / "metadata.json", metadata)
    sync_library_from_metadata(workspace, paper_id, paper_dir, metadata)
    pdf_path = paper_dir / "original.pdf"
    raw_md_path = paper_dir / "raw.md"
    if pdf_path.exists():
        try:
            update_paper_brief_from_pdf(workspace, paper_dir, metadata, pdf_path.name, force=bool(options.get("force_brief")))
            metadata = read_json(paper_dir / "metadata.json", metadata)
        except Exception as exc:  # noqa: BLE001
            print(f"PDF Paper Brief generation failed for {paper_id}: {exc}", file=sys.stderr)
            metadata = read_json(paper_dir / "metadata.json", metadata)
    try:
        if pdf_path.exists():
            mineru_output = paper_dir / "mineru_output"
            generated_md = run_mineru(
                pdf_path,
                mineru_output,
                backend=str(options.get("backend") or "pipeline"),
                method=str(options.get("method") or "auto"),
                lang=str(options.get("lang") or "en"),
                start=options.get("start"),
                end=options.get("end"),
            )
            raw_md = generated_md.read_text(encoding="utf-8")
            copy_markdown_assets(generated_md, paper_dir)
            source_name = pdf_path.name
        elif raw_md_path.exists():
            raw_md = raw_md_path.read_text(encoding="utf-8")
            source_name = raw_md_path.name
        else:
            raise RuntimeError("No original.pdf or raw.md found for skim processing.")
        write_text_atomic(raw_md_path, raw_md)
        segments, outline = build_segments(raw_md)
        title = update_title_from_segments(metadata, segments, paper_id)
        metadata["_paper_dir"] = str(paper_dir)
        metadata.update(
            {
                "title": title,
                "title_key": normalize_title_key(title),
                "abstract": metadata.get("abstract") or section_excerpt(segments, ["abstract"], max_chars=2200),
                "research_question": metadata.get("research_question") or find_research_question(segments, section_excerpt(segments, ["abstract"], max_chars=2200)),
                "venue": metadata.get("venue") or infer_venue(raw_md[:5000]),
                "year": normalize_year(metadata.get("year", "")),
                "processing_status": "ready",
                "processing_background": "done",
                "read_status": "skimmed",
                "agent_analysis_status": "skim_ready",
                "updated_at": now_iso(),
            }
        )
        metadata.pop("_paper_dir", None)
        skim_analysis = build_skim_analysis({**metadata, "_paper_dir": str(paper_dir)}, segments, outline, source_name)
        skim_summary = str(skim_analysis.get("skim_summary") or "")
        presentation_flow = skim_analysis.get("presentation_flow", [])
        write_text_atomic(paper_dir / "skim_prompt.md", SKIM_ANALYSIS_PROMPT.strip() + "\n")
        write_json(paper_dir / "skim_analysis.json", skim_analysis)
        write_text_atomic(paper_dir / "skim_summary.md", skim_summary)
        write_json(paper_dir / "segments.json", [])
        write_json(
            paper_dir / "outline.json",
            {
                "outline": outline,
                "presentation_flow": presentation_flow,
                "core_locations": [
                    {"label": item.get("title", ""), "summary": item.get("core", ""), "anchor": (item.get("anchors") or ["skim-summary"])[0]}
                    for item in presentation_flow
                ],
            },
        )
        ensure_takeaway_doc_skeleton(paper_dir, read_json(paper_dir / "outline.json", {"outline": [], "presentation_flow": []}))
        if not pdf_path.exists():
            update_explanation_from_pdf(paper_dir, metadata, segments, outline, source_name)
        write_text_atomic(paper_dir / "reader.md", skim_summary)
        write_source_artifacts(paper_dir, metadata, [], source_name)
        metadata = metadata_with_citation(metadata)
    except Exception as exc:  # noqa: BLE001
        metadata.update({"processing_status": "failed", "processing_error": str(exc), "updated_at": now_iso()})
        write_json(paper_dir / "metadata.json", metadata)
        sync_library_from_metadata(workspace, paper_id, paper_dir, metadata)
        raise
    write_json(paper_dir / "metadata.json", metadata)
    export_notes_and_annotated(paper_dir)
    sync_library_from_metadata(workspace, paper_id, paper_dir, metadata)
    return metadata


def reusable_parsed_source(paper_dir: Path, metadata: dict[str, Any], segments: list[dict[str, Any]]) -> bool:
    if not any(str(item.get("markdown") or "").strip() for item in segments):
        return False
    if metadata.get("source_type") not in {"reference", "metadata"} or (paper_dir / "raw.md").is_file() or metadata.get("source_parse_complete"):
        return True
    # Reference-card placeholders are not parsed PDF text, but never replace
    # a source already targeted by annotations or saved translations, including
    # equations hidden only in the reading copy.
    annotations = read_json(paper_dir / "annotations.json", {})
    return any(
        isinstance(item.get("translation"), str) and strip_translation_images(item["translation"]).strip()
        for item in segments
    ) or bool(annotations.get("annotations") if isinstance(annotations, dict) else annotations)


def save_processing_fields(workspace: Path, paper_id: str, paper_dir: Path, fields: dict[str, Any]) -> dict[str, Any]:
    with write_lock_for(paper_dir / "metadata.json"):
        if not (paper_dir / "metadata.json").is_file():
            raise FileNotFoundError("Paper metadata is missing; the queued job will not recreate a removed paper.")
        metadata = read_json(paper_dir / "metadata.json", {}, strict=True)
        metadata.update({**fields, "updated_at": now_iso()})
        write_json(paper_dir / "metadata.json", metadata)
    sync_library_from_metadata(workspace, paper_id, paper_dir, metadata, generate_pdf_preview=False)
    return metadata


def process_paper_deep(workspace: Path, paper_id: str, paper_dir: Path, options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Source-only parsing. Briefs, takeaways and translation are separate jobs."""
    options = options or {}
    metadata = read_json(paper_dir / "metadata.json", {})
    existing = translation_segments(paper_dir)
    if reusable_parsed_source(paper_dir, metadata, existing):
        metadata = save_processing_fields(workspace, paper_id, paper_dir, {"processing_mode": "deep", "reading_mode": "deep", "processing_status": "ready", "processing_error": "", "processing_background": "done"})
        resume_translation_waiting_for_source(paper_id, paper_dir)
        return metadata
    save_processing_fields(workspace, paper_id, paper_dir, {"processing_mode": "deep", "reading_mode": "deep", "processing_status": "processing", "processing_error": ""})
    pdf_path = paper_dir / "original.pdf"
    raw_md_path = paper_dir / "raw.md"
    try:
        if raw_md_path.is_file():
            raw_md = raw_md_path.read_text(encoding="utf-8")
            source_name = pdf_path.name if pdf_path.exists() else raw_md_path.name
        elif pdf_path.is_file():
            mineru_output = paper_dir / "mineru_output"
            generated_md = run_mineru(
                pdf_path,
                mineru_output,
                backend=str(options.get("backend") or "pipeline"),
                method=str(options.get("method") or "auto"),
                lang=str(options.get("lang") or "en"),
                start=options.get("start"),
                end=options.get("end"),
            )
            raw_md = generated_md.read_text(encoding="utf-8")
            copy_markdown_assets(generated_md, paper_dir)
            source_name = pdf_path.name
        else:
            raise RuntimeError("No original.pdf or raw.md found for deep processing.")
        segments, outline = build_segments(raw_md)
        if not segments:
            raise RuntimeError("PDF/Markdown parsing produced no source segments.")
        created_source = False
        with write_lock_for(paper_dir / "segments.json"):
            metadata = read_json(paper_dir / "metadata.json", {})
            latest = translation_segments(paper_dir)
            if reusable_parsed_source(paper_dir, metadata, latest):
                segments = latest
            else:
                write_text_atomic(raw_md_path, raw_md)
                write_json(paper_dir / "segments.json", segments)
                existing_outline = read_json(paper_dir / "outline.json", {})
                write_json(paper_dir / "outline.json", {**existing_outline, "outline": outline, "core_locations": existing_outline.get("core_locations", [])})
                if not (paper_dir / "annotations.json").exists():
                    write_json(paper_dir / "annotations.json", {"annotations": []})
                created_source = True
        if created_source:
            write_reader_bundle(paper_dir, metadata, segments, source_name)
            if not (paper_dir / "notes.md").exists() and not (paper_dir / "annotated.md").exists():
                export_notes_and_annotated(paper_dir)
        metadata = read_json(paper_dir / "metadata.json", {})
        title = metadata.get("title") if metadata.get("title_source") == "user" else update_title_from_segments(metadata, segments, paper_id)
        metadata = save_processing_fields(workspace, paper_id, paper_dir, {
            "title": title or paper_id, "title_source": metadata.get("title_source", "paper"), "source_parse_complete": True,
            "source_pdf": "original.pdf" if pdf_path.exists() else metadata.get("source_pdf", ""),
            "processing_status": "ready", "processing_background": "done", "processing_error": "",
            "created_or_refreshed_at": now_iso(),
        })
    except Exception as exc:  # noqa: BLE001
        save_processing_fields(workspace, paper_id, paper_dir, {"processing_status": "failed", "processing_error": str(exc)})
        raise
    resume_translation_waiting_for_source(paper_id, paper_dir)
    return metadata


def prepare_pdf_brief_then_background(workspace: Path, paper_id: str, paper_dir: Path, options: dict[str, Any] | None = None, *, mode: str = "deep", refresh_citations: bool = False, refresh_videos: bool = False) -> dict[str, Any]:
    """Legacy helper name retained for callers; now queues source-first parsing."""
    metadata = read_json(paper_dir / "metadata.json", {})
    if mode == "deep" and reusable_parsed_source(paper_dir, metadata, translation_segments(paper_dir)):
        return process_paper_deep(workspace, paper_id, paper_dir, options)
    start_background_paper_processing(workspace, paper_id, paper_dir, options or {}, mode=mode, refresh_citations=refresh_citations, refresh_videos=refresh_videos)
    return read_json(paper_dir / "metadata.json", {}, strict=True)


def ingest_pdf(args: argparse.Namespace) -> None:
    workspace = resolve_workspace(args.workspace)
    ensure_workspace(workspace)
    pdf_path = Path(args.pdf).expanduser().resolve() if args.pdf else None
    raw_md_path = Path(args.raw_md).expanduser().resolve() if args.raw_md else None
    if not pdf_path and not raw_md_path:
        raise SystemExit("Provide a PDF path or --raw-md.")
    if pdf_path and not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")
    if raw_md_path and not raw_md_path.exists():
        raise SystemExit(f"Raw Markdown not found: {raw_md_path}")

    source_for_hash = pdf_path or raw_md_path
    assert source_for_hash is not None
    digest = file_hash(source_for_hash, limit=None)[:12]
    base_name = pdf_path.stem if pdf_path else raw_md_path.stem
    paper_id = args.paper_id or f"{slugify(base_name)}-{digest}"
    paper_dir = workspace / "papers" / paper_id
    paper_dir.mkdir(parents=True, exist_ok=True)
    existing_metadata = read_json(paper_dir / "metadata.json", {})
    if reusable_parsed_source(paper_dir, existing_metadata, translation_segments(paper_dir)):
        process_paper_deep(workspace, paper_id, paper_dir)
        print(f"Reused parsed paper: {paper_id}")
        return

    if pdf_path:
        destination_pdf = paper_dir / "original.pdf"
        if pdf_path.resolve() != destination_pdf.resolve():
            shutil.copy2(pdf_path, destination_pdf)
    if raw_md_path:
        raw_md = raw_md_path.read_text(encoding="utf-8")
        copy_markdown_assets(raw_md_path, paper_dir)
    else:
        mineru_output = paper_dir / "mineru_output"
        generated_md = run_mineru(
            paper_dir / "original.pdf",
            mineru_output,
            backend=args.backend,
            method=args.method,
            lang=args.lang,
            start=args.start,
            end=args.end,
        )
        raw_md = generated_md.read_text(encoding="utf-8")
        copy_markdown_assets(generated_md, paper_dir)
    write_text_atomic(paper_dir / "raw.md", raw_md)

    segments, outline = build_segments(raw_md)
    title = args.title or guess_title_from_segments(segments, base_name)
    metadata = read_json(paper_dir / "metadata.json", {})
    metadata.update(
        {
            "id": paper_id,
            "title": title,
            "title_source": "user" if args.title else "paper",
            "source_pdf": "original.pdf" if pdf_path else metadata.get("source_pdf", ""),
            "source_pdf_name": pdf_path.name if pdf_path else metadata.get("source_pdf_name", ""),
            "original_path": str(pdf_path) if pdf_path else str(raw_md_path),
            "source_type": "pdf" if pdf_path else metadata.get("source_type", "raw-md"),
            "created_at": metadata.get("created_at") or now_iso(),
            "created_or_refreshed_at": now_iso(),
            "status": metadata.get("status", "new"),
            "venue": metadata.get("venue", ""),
            "year": normalize_year(metadata.get("year", "")),
            "authors": metadata.get("authors", ""),
            "institutions": metadata.get("institutions", ""),
            "abstract": metadata.get("abstract", ""),
            "research_question": metadata.get("research_question", ""),
            "method": metadata.get("method", ""),
            "result": metadata.get("result", ""),
            "discussion": metadata.get("discussion", ""),
            "importance": metadata.get("importance", ""),
            "read_status": metadata.get("read_status", "unread"),
            "processing_mode": metadata.get("processing_mode", "deep"),
            "reading_mode": metadata.get("reading_mode", metadata.get("processing_mode", "deep")),
            "processing_status": metadata.get("processing_status", "ready"),
            "processing_error": metadata.get("processing_error", ""),
            "tags": metadata.get("tags", []),
            "agent_analysis_status": metadata.get("agent_analysis_status", "needs_agent"),
        }
    )
    write_json(paper_dir / "metadata.json", metadata)
    existing_outline = read_json(paper_dir / "outline.json", {"outline": [], "core_locations": []})
    write_json(paper_dir / "segments.json", segments)
    write_json(paper_dir / "outline.json", {**existing_outline, "outline": outline, "core_locations": existing_outline.get("core_locations", [])})
    if not (paper_dir / "annotations.json").exists():
        write_json(paper_dir / "annotations.json", {"annotations": []})
    write_reader_bundle(paper_dir, metadata, segments, source_for_hash.name)
    if not (paper_dir / "notes.md").exists() and not (paper_dir / "annotated.md").exists():
        export_notes_and_annotated(paper_dir)

    sync_library_from_metadata(workspace, paper_id, paper_dir, metadata, generate_pdf_preview=False)

    print(f"Imported paper: {title}")
    print(f"Paper ID: {paper_id}")
    print(f"Workspace: {workspace}")
    print(f"Reader MD: {paper_dir / 'reader.md'}")
    print(f"Serve with: paper-reader-agent --workspace \"{workspace}\" serve --open")


def init_workspace(args: argparse.Namespace) -> None:
    workspace = resolve_workspace(args.workspace)
    ensure_workspace(workspace)
    if not args.no_config:
        config_path = Path.cwd() / CONFIG_FILE
        relative = os.path.relpath(workspace, Path.cwd())
        write_json(config_path, {"workspace": relative, "created_at": now_iso(), "tool": "paper-reader-agent"})
        print(f"Wrote config: {config_path}")
    print(f"Workspace ready: {workspace}")


def doctor(args: argparse.Namespace) -> None:
    print(f"paper-reader-agent {TOOL_VERSION}")
    print(f"Python: {sys.executable}")
    print(f"Script: {Path(__file__).resolve()}")
    mineru = find_mineru()
    print(f"MinerU: {mineru or 'not found'}")
    if mineru:
        try:
            output = subprocess.run([mineru, "--version"], check=True, capture_output=True, text=True, timeout=60)
            print(output.stdout.strip() or output.stderr.strip())
        except Exception as exc:  # noqa: BLE001
            print(f"MinerU version check failed: {exc}")
    workspace = resolve_workspace(args.workspace)
    print(f"Default workspace: {workspace}")


def normalized_query_value(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value or "")).strip().casefold()


def paper_record_dir(workspace: Path, paper: dict[str, Any]) -> Path:
    path = Path(str(paper.get("paper_dir") or ""))
    return path if path.is_absolute() else workspace / path


def paper_record_artifact(workspace: Path, paper: dict[str, Any], field: str, filename: str) -> Path:
    value = str(paper.get(field) or "").strip()
    if value:
        path = Path(value)
        return path if path.is_absolute() else workspace / path
    return paper_record_dir(workspace, paper) / filename


def load_paper_query_brief(paper_dir: Path) -> str:
    thinking = read_json(paper_dir / "thinking.json", {})
    explain = thinking.get("explain") if isinstance(thinking, dict) else None
    if not isinstance(explain, dict):
        return ""
    return str(explain.get("content") or "").strip()


def paper_matches_query(paper: dict[str, Any], project: str, tag: str, search: str) -> bool:
    projects = {normalized_query_value(value) for value in metadata_projects(paper)}
    if project and normalized_query_value(project) not in projects:
        return False

    paper_tags = {normalized_query_value(value) for value in normalize_tag_paths(paper.get("tags", []))}
    requested_tags = {normalized_query_value(value) for value in normalize_tag_paths(tag)} if tag else set()
    if requested_tags and not paper_tags.intersection(requested_tags):
        return False

    needle = normalized_query_value(search)
    if not needle:
        return True
    searchable = json.dumps(
        {
            "id": paper.get("id", ""),
            "title": paper.get("title", ""),
            "authors": paper.get("authors", ""),
            "venue": paper.get("venue", ""),
            "year": paper.get("year", ""),
            "projects": metadata_projects(paper),
            "tags": normalize_tag_paths(paper.get("tags", [])),
        },
        ensure_ascii=False,
    )
    return needle in normalized_query_value(searchable)


def markdown_link_label(value: Any) -> str:
    return str(value or "").replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def markdown_artifact_reference(path_value: str, output_path: Path | None) -> str:
    path = Path(path_value)
    if not path.exists():
        return f"`{path}` (missing)"
    if output_path is None:
        return f"`{path}`"
    relative = os.path.relpath(path, output_path.parent).replace("\\", "/")
    return f"[{markdown_link_label(path.name)}](<{relative}>)"


def render_paper_query_markdown(payload: dict[str, Any], output_path: Path | None = None) -> str:
    summary = payload["summary"]
    filters = payload["filters"]
    papers = payload["papers"]
    lines = [
        "# Paper Query Results",
        "",
        f"- Library papers: {summary['library_papers']}",
        f"- Matched papers: {summary['matched_papers']}",
        f"- Returned papers: {summary['returned_papers']}",
        f"- Briefing available: {summary['briefing_available']}",
        f"- Briefing missing: {summary['briefing_missing']}",
        "",
        "Data source: `library.json` for filtering and each matched paper's `thinking.json` -> `explain.content` for Briefing availability and content.",
        "",
        "## Paper Index",
        "",
    ]
    for index, paper in enumerate(papers, 1):
        lines.append(f"{index}. [{markdown_link_label(paper['title'])}](#paper-{index:03d})")

    for index, paper in enumerate(papers, 1):
        briefing = paper["briefing"]
        lines.extend(
            [
                "",
                "---",
                "",
                f'<a id="paper-{index:03d}"></a>',
                f"## {index:03d}. {paper['title']}",
                "",
                f"- Paper ID: `{paper['id']}`",
                f"- Projects: {', '.join(paper['projects']) or '-'}",
                f"- Tags: {', '.join(paper['tags']) or '-'}",
                f"- Reader: {markdown_artifact_reference(paper['reader_path'], output_path)}",
                f"- Notes: {markdown_artifact_reference(paper['notes_path'], output_path)}",
                f"- Briefing source: {markdown_artifact_reference(briefing['path'], output_path)}",
                f"- Briefing status: {'available' if briefing['available'] else 'missing'}",
            ]
        )
        if filters["include_briefs"]:
            lines.extend(["", "### Briefing", ""])
            lines.append(briefing.get("content") or "> **Briefing unavailable:** `thinking.json` is missing or `explain.content` is empty.")
    return "\n".join(lines).rstrip() + "\n"


def query_papers_cli(args: argparse.Namespace) -> None:
    workspace = resolve_workspace(args.workspace)
    library = load_library_raw(workspace)
    if args.limit < 0:
        raise SystemExit("--limit must be zero or greater")

    matched: list[dict[str, Any]] = []
    for paper in library.get("papers", []):
        if not paper_matches_query(paper, args.project, args.tag, args.search):
            continue
        paper_dir = paper_record_dir(workspace, paper)
        briefing_path = paper_dir / "thinking.json"
        briefing_content = load_paper_query_brief(paper_dir)
        briefing_available = bool(briefing_content)
        if args.brief == "available" and not briefing_available:
            continue
        if args.brief == "missing" and briefing_available:
            continue
        reader_path = paper_record_artifact(workspace, paper, "reader_md", "reader.md").resolve()
        notes_path = paper_record_artifact(workspace, paper, "notes_md", "notes.md").resolve()
        resolved_briefing_path = briefing_path.resolve()
        record = {
            "id": str(paper.get("id") or ""),
            "title": str(paper.get("title") or paper.get("id") or "").strip(),
            "projects": metadata_projects(paper),
            "tags": normalize_tag_paths(paper.get("tags", [])),
            "year": paper.get("year", ""),
            "venue": paper.get("venue", ""),
            "paper_dir": str(paper_dir.resolve()),
            "reader_path": str(reader_path),
            "reader_exists": reader_path.exists(),
            "notes_path": str(notes_path),
            "notes_exists": notes_path.exists(),
            "briefing": {
                "available": briefing_available,
                "chars": len(briefing_content),
                "path": str(resolved_briefing_path),
                "source_exists": resolved_briefing_path.exists(),
            },
        }
        if args.include_briefs:
            record["briefing"]["content"] = briefing_content
        matched.append(record)

    matched.sort(key=lambda paper: (normalized_query_value(paper["title"]), paper["id"]))
    total_matches = len(matched)
    briefing_available = sum(bool(paper["briefing"]["available"]) for paper in matched)
    returned = matched[: args.limit] if args.limit else matched
    payload = {
        "workspace": str(workspace),
        "filters": {
            "project": args.project or "",
            "tag": args.tag or "",
            "search": args.search or "",
            "brief": args.brief,
            "include_briefs": bool(args.include_briefs),
            "limit": args.limit,
        },
        "summary": {
            "library_papers": len(library.get("papers", [])),
            "matched_papers": total_matches,
            "returned_papers": len(returned),
            "briefing_available": briefing_available,
            "briefing_missing": total_matches - briefing_available,
        },
        "papers": returned,
    }

    output_path = None
    if args.output:
        requested_path = Path(args.output).expanduser()
        output_path = requested_path if requested_path.is_absolute() else workspace / requested_path
    content = render_paper_query_markdown(payload, output_path) if args.format == "markdown" else json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if output_path is None:
        print(content, end="")
        return
    write_text_atomic(output_path, content)
    print(f"Wrote query results: {output_path}")
    print(f"Matched papers: {total_matches}")
    print(f"Returned papers: {len(returned)}")
    print(f"Briefing available: {briefing_available}")
    print(f"Briefing missing: {total_matches - briefing_available}")


def list_status(args: argparse.Namespace) -> None:
    workspace = resolve_workspace(args.workspace)
    library = load_library(workspace)
    print(f"Workspace: {workspace}")
    print(f"Papers: {len(library.get('papers', []))}")
    for paper in library.get("papers", []):
        mode = paper.get("processing_mode", "library-only")
        status = paper.get("processing_status", "not_processed")
        citations = paper.get("citation_count", "")
        citation_text = f", citations={citations}" if citations != "" else ""
        print(f"- {paper.get('id')}: {paper.get('title')} [{paper.get('read_status', 'unread')}, {mode}/{status}{citation_text}]")


def register_paper_cli(args: argparse.Namespace) -> None:
    workspace = resolve_workspace(args.workspace)
    ensure_workspace(workspace)
    tags = [tag.strip() for tag in (args.tags or "").split(",") if tag.strip()]
    result = register_paper_in_library(workspace, Path(args.pdf).expanduser().resolve(), paper_id=args.paper_id, title=args.title, tags=tags)
    print(f"Registered paper: {result['metadata'].get('title')}")
    print(f"Paper ID: {result['paper_id']}")


def process_paper_cli(args: argparse.Namespace) -> None:
    workspace = resolve_workspace(args.workspace)
    record = find_paper_record(workspace, args.paper_id)
    if not record:
        raise SystemExit(f"Unknown paper: {args.paper_id}")
    paper_dir = workspace / record.get("paper_dir", "")
    options = {"backend": args.backend, "method": args.method, "lang": args.lang, "start": args.start, "end": args.end}
    metadata = process_paper_skim(workspace, args.paper_id, paper_dir, options) if args.mode == "skim" else process_paper_deep(workspace, args.paper_id, paper_dir, options)
    print(f"Processed paper: {metadata.get('title')}")
    print(f"Mode: {args.mode}")
    print(f"Status: {metadata.get('processing_status')}")


def refresh_citations_cli(args: argparse.Namespace) -> None:
    workspace = resolve_workspace(args.workspace)
    library = load_library(workspace)
    targets = [args.paper_id] if args.paper_id else [paper.get("id") for paper in library.get("papers", [])]
    refreshed = 0
    for paper_id in targets:
        if not paper_id:
            continue
        record = find_paper_record(workspace, paper_id)
        if not record:
            print(f"Skipping unknown paper: {paper_id}")
            continue
        paper_dir = workspace / record.get("paper_dir", "")
        metadata = refresh_paper_citations(workspace, paper_id, paper_dir)
        print(f"{paper_id}: {metadata.get('citation_count', '')} ({metadata.get('citation_source', '')})")
        refreshed += 1
    print(f"Refreshed citations for {refreshed} paper(s).")


def rebuild_outputs(args: argparse.Namespace) -> None:
    workspace = resolve_workspace(args.workspace)
    library = load_library(workspace)
    paper_ids = [args.paper_id] if args.paper_id else [paper.get("id") for paper in library.get("papers", [])]
    rebuilt = 0
    for paper_id in paper_ids:
        if not paper_id:
            continue
        paper_record = next((paper for paper in library.get("papers", []) if paper.get("id") == paper_id), None)
        if not paper_record:
            print(f"Skipping unknown paper: {paper_id}")
            continue
        paper_dir = workspace / paper_record.get("paper_dir", "")
        segments = load_segments(paper_dir)
        if not segments:
            print(f"Skipping paper without segments: {paper_id}")
            continue
        source_name = read_json(paper_dir / "metadata.json", {}).get("source_pdf") or "raw.md"
        write_reader_bundle(paper_dir, read_json(paper_dir / "metadata.json", {}), segments, source_name)
        export_notes_and_annotated(paper_dir)
        rebuilt += 1
        print(f"Rebuilt: {paper_id}")
    print(f"Rebuilt outputs for {rebuilt} paper(s).")


class ReaderHandler(BaseHTTPRequestHandler):
    workspace: Path = Path.cwd()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        timestamp = dt.datetime.now().strftime("%H:%M:%S")
        sys.stderr.write(f"[{timestamp}] {format % args}\n")

    def send_payload(self, payload: bytes, content_type: str, status: int = 200, *, download_name: str | None = None, etag: str | None = None) -> None:
        validators = [value.strip().removeprefix("W/") for value in self.headers.get("If-None-Match", "").split(",")]
        not_modified = bool(etag and (etag in validators or "*" in validators))
        try:
            self.send_response(HTTPStatus.NOT_MODIFIED if not_modified else status)
            self.send_header("Cache-Control", "no-cache" if etag else "no-store")
            if etag:
                self.send_header("ETag", etag)
            if not not_modified:
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(payload)))
                if download_name:
                    ascii_name = re.sub(r"[^a-zA-Z0-9._-]", "_", download_name)
                    encoded_name = urllib.parse.quote(download_name, safe="")
                    self.send_header("Content-Disposition", f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded_name}")
            self.end_headers()
            if not not_modified:
                self.wfile.write(payload)
        except CLIENT_DISCONNECT_ERRORS:
            return

    def send_json(self, data: Any, status: int = 200, *, download_name: str | None = None) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_payload(payload, "application/json; charset=utf-8", status, download_name=download_name)

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:  # noqa: A003
        if self.path.startswith("/api/"):
            self.send_json({"ok": False, "error": str(message or HTTPStatus(code).phrase)}, int(code))
            return
        safe_message = str(message or HTTPStatus(code).phrase).encode("latin-1", "replace").decode("latin-1")
        safe_explain = str(explain).encode("latin-1", "replace").decode("latin-1") if explain else None
        super().send_error(code, safe_message, safe_explain)

    def send_text_file(self, path: Path, content_type: str | None = None, *, cache_static: bool = False) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        payload = path.read_bytes()
        etag = f'"{hashlib.sha256(payload).hexdigest()}"' if cache_static else None
        self.send_payload(payload, content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream", etag=etag)

    def get_paper_dir(self, paper_id: str) -> Path | None:
        library = read_library_index(self.workspace)
        for paper in library.get("papers", []):
            if isinstance(paper, dict) and paper.get("id") == paper_id and paper.get("paper_dir"):
                registered = (self.workspace / paper["paper_dir"]).resolve()
                return registered if registered.is_dir() else None
        papers_root = (self.workspace / "papers").resolve()
        direct = (papers_root / paper_id).resolve()
        if not direct.is_relative_to(papers_root) or direct == papers_root:
            return None
        if direct.is_dir():
            return direct
        return None

    def do_GET(self) -> None:  # noqa: N802
        try:
            self._do_GET()
        except CLIENT_DISCONNECT_ERRORS:
            return
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc(file=sys.stderr)
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def _do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        publication_match = re.fullmatch(r"/api/papers/([^/]+)/feishu-publication", path)
        if publication_match:
            paper_dir = self.get_paper_dir(urllib.parse.unquote(publication_match.group(1)))
            if not paper_dir:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                self.require_publication_origin()
                status = publication_service().status(paper_dir, publication_settings())
                self.send_json({"ok": True, "publication": status})
            except PermissionError as exc:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.FORBIDDEN)
            except (ValueError, RuntimeError, OSError) as exc:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        if path == "/api/feishu/search":
            try:
                base_token, table_id, executable = feishu_settings()
                keyword = urllib.parse.parse_qs(parsed.query).get("keyword", [""])[0]
                result = feishu_metadata.search_records(base_token, table_id, keyword, executable=executable)
            except (ValueError, RuntimeError, OSError) as exc:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            self.send_json({"ok": True, **result})
            return
        if path == "/api/feishu/preview":
            try:
                reference = urllib.parse.parse_qs(parsed.query).get("reference", [""])[0]
                result = preview_feishu_record(self.workspace, reference)
            except (ValueError, RuntimeError, OSError) as exc:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            self.send_json(result)
            return
        if path == "/" or path == "/index.html":
            self.send_text_file(WEB_DIR / "index.html", "text/html; charset=utf-8", cache_static=True)
            return
        if path in {"/app.js", "/styles.css"}:
            self.send_text_file(WEB_DIR / path.lstrip("/"), "application/javascript; charset=utf-8" if path.endswith(".js") else "text/css; charset=utf-8", cache_static=True)
            return
        if path.startswith("/vendor/"):
            web_root = WEB_DIR.resolve()
            target = (web_root / urllib.parse.unquote(path.lstrip("/"))).resolve()
            try:
                target.relative_to(web_root)
            except ValueError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_text_file(target, cache_static=True)
            return
        if path == "/api/library":
            library = read_library_index(self.workspace)
            self.send_json({"workspace": str(self.workspace), "library": library, "tag_dictionary": tag_dictionary(), "project_contexts": read_project_contexts(self.workspace), "translation_config": translation_config(), "feishu_config": feishu_config()})
            return
        if path == "/api/translation-queue":
            try:
                snapshot = TRANSLATION_JOBS.queue_snapshot(self.workspace) if TRANSLATION_JOBS else {
                    "ok": True, "concurrency": translation_concurrency(), "active_requests": 0, "jobs": [], "retry_at": None,
                }
            except (ValueError, OSError) as exc:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            self.send_json(snapshot)
            return
        if path == "/api/processing-queue":
            self.send_json(PROCESSING_JOBS.snapshot(self.workspace) if PROCESSING_JOBS else {
                "ok": True, "concurrency": 1, "active_jobs": 0, "queued_count": 0, "jobs": [],
            })
            return
        if path == "/api/project-contexts":
            self.send_json({"ok": True, "workspace": str(self.workspace), "project_contexts": read_project_contexts(self.workspace)})
            return
        if path == "/api/tag-dictionary":
            self.send_json({"ok": True, "tag_dictionary": tag_dictionary()})
            return
        if path == "/api/papers":
            library = read_library_index(self.workspace)
            self.send_json({"workspace": str(self.workspace), "papers": library.get("papers", []), "tag_dictionary": tag_dictionary()})
            return
        if path == "/api/candidates":
            self.send_json({"ok": True, "workspace": str(self.workspace), "candidates": list_candidates(self.workspace), "library": load_library(self.workspace), "tag_dictionary": tag_dictionary()})
            return
        candidate_match = re.match(r"^/api/candidates/([^/]+)$", path)
        if candidate_match:
            candidate_id = urllib.parse.unquote(candidate_match.group(1))
            try:
                self.send_json({"ok": True, "candidate": read_candidate(self.workspace, candidate_id)})
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
            return
        candidate_annotations_match = re.match(r"^/api/candidates/([^/]+)/annotations$", path)
        if candidate_annotations_match:
            candidate_id = urllib.parse.unquote(candidate_annotations_match.group(1))
            try:
                path = candidate_dir(self.workspace, candidate_id)
                if not (path / "candidate.json").exists():
                    raise FileNotFoundError(candidate_id)
                annotations = read_json(path / "annotations.json", {"annotations": []})
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json({"ok": True, "annotations": annotations.get("annotations", [])})
            return
        if path == "/api/mindmaps":
            query = urllib.parse.parse_qs(parsed.query)
            project = (query.get("project", [""])[0] or "").strip()
            include_archived = (query.get("include_archived", ["0"])[0] or "0").lower() in {"1", "true", "yes"}
            self.send_json({"ok": True, "workspace": str(self.workspace), **list_mindmaps(self.workspace, project, include_archived=include_archived), "projects": [mindmap_summary(self.workspace, project_name) for project_name in CANONICAL_PROJECTS], "library": load_library(self.workspace), "tag_dictionary": tag_dictionary()})
            return
        if path == "/api/canvas/boards":
            query = urllib.parse.parse_qs(parsed.query)
            project = (query.get("project", [""])[0] or "").strip()
            self.send_json({"ok": True, "workspace": str(self.workspace), **list_canvas_boards(self.workspace, project), "library": load_library(self.workspace), "tag_dictionary": tag_dictionary()})
            return
        canvas_board_match = re.match(r"^/api/canvas/boards/([^/]+)$", path)
        if canvas_board_match:
            board_id = urllib.parse.unquote(canvas_board_match.group(1))
            try:
                board = read_canvas_board(self.workspace, board_id)
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json({"ok": True, "board": board, "library": load_library(self.workspace), "notes": aggregate_notes(self.workspace), "tag_dictionary": tag_dictionary(), "sync_proposals": canvas_sync_proposals(self.workspace, board)})
            return
        canvas_sync_match = re.match(r"^/api/canvas/boards/([^/]+)/sync-proposals$", path)
        if canvas_sync_match:
            board_id = urllib.parse.unquote(canvas_sync_match.group(1))
            try:
                board = read_canvas_board(self.workspace, board_id)
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json({"ok": True, "proposals": canvas_sync_proposals(self.workspace, board)})
            return
        mindmap_sync_match = re.match(r"^/api/mindmaps/([^/]+)/([^/]+)/sync-proposals$", path)
        if mindmap_sync_match:
            project = urllib.parse.unquote(mindmap_sync_match.group(1))
            mindmap_id = urllib.parse.unquote(mindmap_sync_match.group(2))
            try:
                doc = read_mindmap(self.workspace, project, mindmap_id, seed=True)
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json({"ok": True, "proposals": mindmap_sync_proposals(self.workspace, doc)})
            return
        mindmap_doc_match = re.match(r"^/api/mindmaps/([^/]+)/([^/]+)$", path)
        if mindmap_doc_match:
            project = urllib.parse.unquote(mindmap_doc_match.group(1))
            mindmap_id = urllib.parse.unquote(mindmap_doc_match.group(2))
            try:
                doc = read_mindmap(self.workspace, project, mindmap_id, seed=True)
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json({"ok": True, "mindmap": doc, **list_mindmaps(self.workspace, project), "library": load_library(self.workspace), "notes": aggregate_notes(self.workspace), "tag_dictionary": tag_dictionary()})
            return
        mindmap_match = re.match(r"^/api/mindmaps/([^/]+)$", path)
        if mindmap_match:
            project = urllib.parse.unquote(mindmap_match.group(1))
            query = urllib.parse.parse_qs(parsed.query)
            mindmap_id = (query.get("id", [""])[0] or "").strip()
            try:
                doc = read_mindmap(self.workspace, project, mindmap_id, seed=True)
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json({"ok": True, "mindmap": doc, **list_mindmaps(self.workspace, project), "library": load_library(self.workspace), "notes": aggregate_notes(self.workspace), "tag_dictionary": tag_dictionary()})
            return
        if path == "/api/notes":
            self.send_json({"workspace": str(self.workspace), "notes": aggregate_notes(self.workspace)})
            return
        takeaway_match = re.match(r"^/api/papers/([^/]+)/takeaway-doc$", path)
        if takeaway_match:
            paper_id = urllib.parse.unquote(takeaway_match.group(1))
            paper_dir = self.get_paper_dir(paper_id)
            if not paper_dir:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json({"ok": True, "takeaway_doc": load_takeaway_doc(paper_dir)})
            return
        references_match = re.match(r"^/api/papers/([^/]+)/references$", path)
        if references_match:
            paper_id = urllib.parse.unquote(references_match.group(1))
            paper_dir = self.get_paper_dir(paper_id)
            if not paper_dir:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json(load_reference_index(paper_dir))
            return
        reference_match = re.match(r"^/api/papers/([^/]+)/references/(\d+)$", path)
        if reference_match:
            paper_id = urllib.parse.unquote(reference_match.group(1))
            number = reference_match.group(2)
            paper_dir = self.get_paper_dir(paper_id)
            if not paper_dir:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            query = urllib.parse.parse_qs(parsed.query)
            enrich = (query.get("enrich", ["1"])[0] or "1").lower() not in {"0", "false", "no"}
            card = get_reference_card(paper_dir, number, enrich=enrich)
            if not card:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json({"reference": card})
            return
        translation_match = re.match(r"^/api/papers/([^/]+)/translation$", path)
        if translation_match:
            paper_id = urllib.parse.unquote(translation_match.group(1))
            paper_dir = self.get_paper_dir(paper_id)
            if not paper_dir:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            query = urllib.parse.parse_qs(parsed.query)
            try:
                after = int(query.get("after", ["-1"])[0])
            except ValueError:
                self.send_error(HTTPStatus.BAD_REQUEST, "after must be a revision number")
                return
            self.send_json({"ok": True, "paper_id": paper_id, **translation_snapshot(paper_dir, job_id=query.get("job_id", [""])[0], after=after)})
            return
        teacher_match = re.fullmatch(r"/api/papers/([^/]+)/reading-teacher", path)
        if teacher_match:
            paper_id = urllib.parse.unquote(teacher_match.group(1))
            paper_dir = self.get_paper_dir(paper_id)
            if not paper_dir:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                missing = object()
                data = read_json(paper_dir / "reading_teacher.json", missing, strict=True)
                teacher = {"available": False, "cards": [], "issues": []} if data is missing else validate_reading_teacher(
                    data, read_json(paper_dir / "segments.json", [], strict=True), paper_id,
                )
            except (ValueError, OSError) as exc:
                self.send_json({"ok": False, "error": f"Reading teacher unavailable: {exc}"}, status=HTTPStatus.CONFLICT)
                return
            self.send_json({"ok": True, "paper_id": paper_id, "teacher": teacher})
            return
        export_match = re.match(r"^/api/papers/([^/]+)/(notes-md|reading-data)$", path)
        if export_match:
            paper_id = urllib.parse.unquote(export_match.group(1))
            paper_dir = self.get_paper_dir(paper_id)
            if not paper_dir:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            # Generate downloads in memory from current source files. GET must
            # neither rewrite JSON nor depend on a potentially stale notes.md.
            snapshot = load_reading_data(paper_dir, paper_id, include_teacher=export_match.group(2) == "reading-data")
            filename = slugify(paper_id)
            if export_match.group(2) == "notes-md":
                self.send_payload(make_notes_markdown(snapshot).encode("utf-8"), "text/markdown; charset=utf-8", download_name=f"{filename}-notes.md")
            else:
                self.send_json(snapshot, download_name=f"{filename}-reading-data.json")
            return
        match = re.match(r"^/api/papers/([^/]+)$", path)
        if match:
            paper_id = urllib.parse.unquote(match.group(1))
            paper_dir = self.get_paper_dir(paper_id)
            if not paper_dir:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            metadata = normalized_metadata(paper_dir, read_json(paper_dir / "metadata.json", {}), discover_preview=False)
            # Advertise the download with a stat only, never PDF parsing.
            metadata["source_pdf"] = (metadata.get("source_pdf") or "original.pdf") if (paper_dir / "original.pdf").is_file() else ""
            segments = read_json(paper_dir / "segments.json", [])
            translation = translation_snapshot(paper_dir, segments=segments)["translation"]
            metadata.update({
                "translation_status": translation["status"], "translation_error": translation["error"],
                "translation_backend": translation["backend"], "translated_segments": translation["completed"],
                "translation_total": translation["total"],
            })
            self.send_json(
                {
                    "metadata": metadata,
                    "feishu_metadata": read_json(paper_dir / "feishu_metadata.json", {}),
                    "outline": read_json(paper_dir / "outline.json", {"outline": [], "core_locations": []}),
                    "segments": segments,
                    "teacher_available": (paper_dir / "reading_teacher.json").is_file(),
                    "translation": translation,
                    "translation_config": translation_config(),
                    # No PDF text extraction or rendering on open. Incomplete
                    # figures use the original PDF endpoint in the reader.
                    "figure_fallbacks": {},
                    "annotations": read_json(paper_dir / "annotations.json", {"annotations": []}),
                    "reading_progress": load_reading_progress(paper_dir),
                    "thinking": load_thinking(paper_dir),
                    "takeaway_doc": load_takeaway_doc(paper_dir),
                    "skim_analysis": read_json(paper_dir / "skim_analysis.json", {}),
                    "skim_summary": (paper_dir / "skim_summary.md").read_text(encoding="utf-8") if (paper_dir / "skim_summary.md").exists() else "",
                    "skim_prompt": (paper_dir / "skim_prompt.md").read_text(encoding="utf-8") if (paper_dir / "skim_prompt.md").exists() else SKIM_ANALYSIS_PROMPT,
                    "mode_labels": PROCESSING_MODE_LABELS,
                    "paths": {
                        "reader_md": str(paper_dir / "reader.md"),
                        "annotated_md": str(paper_dir / "annotated.md"),
                        "notes_md": str(paper_dir / "notes.md"),
                        "annotations_json": str(paper_dir / "annotations.json"),
                        "thinking_json": str(paper_dir / "thinking.json"),
                        "segments_json": str(paper_dir / "segments.json"),
                        "reading_progress_json": str(paper_dir / "reading_progress.json"),
                    },
                }
            )
            return
        asset_match = re.match(r"^/api/papers/([^/]+)/assets/(.+)$", path)
        if asset_match:
            paper_id = urllib.parse.unquote(asset_match.group(1))
            relative_asset = urllib.parse.unquote(asset_match.group(2)).replace("\\", "/")
            paper_dir = self.get_paper_dir(paper_id)
            if not paper_dir or relative_asset.startswith("/") or ".." in Path(relative_asset).parts:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            asset_path = (paper_dir / relative_asset).resolve()
            try:
                asset_path.relative_to(paper_dir.resolve())
            except ValueError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_text_file(asset_path)
            return
        file_match = re.match(r"^/api/papers/([^/]+)/(pdf|reader-md|paper-md|annotated-md|source-map|translation-notes|terminology-ledger)$", path)
        if file_match:
            paper_id = urllib.parse.unquote(file_match.group(1))
            file_kind = file_match.group(2)
            paper_dir = self.get_paper_dir(paper_id)
            if not paper_dir:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            file_map = {
                "pdf": (paper_dir / "original.pdf", "application/pdf"),
                "reader-md": (paper_dir / "reader.md", "text/markdown; charset=utf-8"),
                "paper-md": (paper_dir / "paper.md", "text/markdown; charset=utf-8"),
                "annotated-md": (paper_dir / "annotated.md", "text/markdown; charset=utf-8"),
                "source-map": (paper_dir / "source_map.json", "application/json; charset=utf-8"),
                "translation-notes": (paper_dir / "translation_notes.md", "text/markdown; charset=utf-8"),
                "terminology-ledger": (paper_dir / "terminology_ledger.json", "application/json; charset=utf-8"),
            }
            file_path, content_type = file_map[file_kind]
            self.send_text_file(file_path, content_type)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def require_publication_origin(self) -> None:
        host = urllib.parse.urlsplit("http://" + self.headers.get("Host", ""))
        if host.hostname not in {"localhost", "127.0.0.1", "::1"} or host.username or host.password:
            raise PermissionError("Open the reader on localhost to publish reading records.")
        origin = self.headers.get("Origin")
        if origin:
            source = urllib.parse.urlsplit(origin)
            if source.scheme not in {"http", "https"} or source.netloc != host.netloc or source.username or source.password:
                raise PermissionError("Publication requests must come from this reader's own origin.")

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._do_POST()
        except CLIENT_DISCONNECT_ERRORS:
            return
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc(file=sys.stderr)
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def _do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        publication_match = re.fullmatch(r"/api/papers/([^/]+)/feishu-publication/(preview|publish)", parsed.path)
        if publication_match:
            paper_dir = self.get_paper_dir(urllib.parse.unquote(publication_match.group(1)))
            if not paper_dir:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                self.require_publication_origin()
                if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                    raise ValueError("Publication requires an application/json request.")
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 65536:
                    raise ValueError("Invalid publication request length.")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Publication expects a JSON object.")
                if publication_match.group(2) == "preview":
                    if data:
                        raise ValueError("Preview uses the current saved paper and its configured destination.")
                elif (
                    set(data) != {"preview_id", "confirm"} or data.get("confirm") is not True
                    or not isinstance(data.get("preview_id"), str) or not data["preview_id"]
                ):
                    raise ValueError("Confirm the current preview before publishing; arbitrary destinations are not accepted.")
                service = publication_service()
                settings = publication_settings()
                if publication_match.group(2) == "preview":
                    self.send_json({"ok": True, "preview": service.preview(paper_dir, settings)})
                else:
                    result = service.start(paper_dir, settings, data["preview_id"], True)
                    self.send_json({"ok": True, "publication": result})
            except PermissionError as exc:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.FORBIDDEN)
            except feishu_publish.PublicationConflict as exc:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.CONFLICT)
            except (ValueError, RuntimeError, OSError) as exc:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        if parsed.path in {"/api/feishu/intake", "/api/processing-queue/retry"}:
            try:
                data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
                if not isinstance(data, dict):
                    raise ValueError("This action expects a JSON object.")
                if parsed.path == "/api/feishu/intake":
                    result = intake_feishu_paper(self.workspace, data)
                else:
                    paper_id = str(data.get("paper_id") or "")
                    paper_dir = self.get_paper_dir(paper_id)
                    if not paper_dir:
                        raise ValueError("The queued paper no longer exists in this workspace.")
                    metadata = read_json(paper_dir / "metadata.json", {}, strict=True)
                    if metadata.get("processing_status") != "failed":
                        raise ValueError("Only failed parsing jobs need a retry.")
                    request = metadata.get("processing_request") or {}
                    start_background_paper_processing(
                        self.workspace, paper_id, paper_dir, request.get("options") or {},
                        mode=request.get("mode") or "deep", refresh_citations=bool(request.get("refresh_citations")),
                        refresh_videos=bool(request.get("refresh_videos")),
                    )
                    result = {"ok": True, "paper_id": paper_id, "metadata": read_json(paper_dir / "metadata.json", {}, strict=True)}
                self.send_json(result)
            except (ValueError, RuntimeError, OSError) as exc:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        feishu_match = re.fullmatch(r"/api/papers/([^/]+)/feishu-sync", parsed.path)
        if feishu_match:
            paper_id = urllib.parse.unquote(feishu_match.group(1))
            paper_dir = self.get_paper_dir(paper_id)
            if not paper_dir:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
                if not isinstance(data, dict):
                    raise ValueError("Feishu synchronization expects a JSON object.")
                self.send_json(sync_feishu_metadata(self.workspace, paper_id, paper_dir, data))
            except (ValueError, RuntimeError, OSError) as exc:
                self.send_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        library_add_match = parsed.path == "/api/library/papers"
        library_upload_match = parsed.path == "/api/library/papers/upload"
        library_metadata_match = parsed.path == "/api/library/papers/metadata"
        project_context_match = re.match(r"^/api/project-contexts/([^/]+)$", parsed.path)
        candidate_brief_match = parsed.path == "/api/candidates/brief"
        candidate_annotations_match = re.match(r"^/api/candidates/([^/]+)/annotations$", parsed.path)
        candidate_metadata_match = re.match(r"^/api/candidates/([^/]+)/metadata$", parsed.path)
        candidate_save_match = re.match(r"^/api/candidates/([^/]+)/save-to-library$", parsed.path)
        attach_pdf_match = re.match(r"^/api/papers/([^/]+)/pdf$", parsed.path)
        annotations_match = re.match(r"^/api/papers/([^/]+)/annotations$", parsed.path)
        thinking_match = re.match(r"^/api/papers/([^/]+)/thinking$", parsed.path)
        chat_match = re.match(r"^/api/papers/([^/]+)/chat$", parsed.path)
        reading_narrative_match = re.match(r"^/api/papers/([^/]+)/reading-narrative$", parsed.path)
        takeaway_match = re.match(r"^/api/papers/([^/]+)/takeaway-doc$", parsed.path)
        explain_match = re.match(r"^/api/papers/([^/]+)/thinking/explain$", parsed.path)
        metadata_match = re.match(r"^/api/papers/([^/]+)/metadata$", parsed.path)
        find_pdf_match = re.match(r"^/api/papers/([^/]+)/find-pdf$", parsed.path)
        reading_progress_match = re.match(r"^/api/papers/([^/]+)/reading-progress$", parsed.path)
        process_match = re.match(r"^/api/papers/([^/]+)/process$", parsed.path)
        translate_match = re.match(r"^/api/papers/([^/]+)/translate$", parsed.path)
        citations_match = re.match(r"^/api/papers/([^/]+)/citations$", parsed.path)
        videos_match = re.match(r"^/api/papers/([^/]+)/videos$", parsed.path)
        reference_add_match = re.match(r"^/api/papers/([^/]+)/references/(\d+)/add$", parsed.path)
        canvas_boards_match = parsed.path == "/api/canvas/boards"
        canvas_board_match = re.match(r"^/api/canvas/boards/([^/]+)$", parsed.path)
        canvas_sync_apply_match = re.match(r"^/api/canvas/boards/([^/]+)/sync-apply$", parsed.path)
        mindmap_create_match = parsed.path == "/api/mindmaps"
        mindmap_doc_save_match = re.match(r"^/api/mindmaps/([^/]+)/([^/]+)$", parsed.path)
        mindmap_duplicate_match = re.match(r"^/api/mindmaps/([^/]+)/([^/]+)/duplicate$", parsed.path)
        mindmap_doc_add_paper_match = re.match(r"^/api/mindmaps/([^/]+)/([^/]+)/paper-instances$", parsed.path)
        mindmap_sync_apply_match = re.match(r"^/api/mindmaps/([^/]+)/([^/]+)/sync-apply$", parsed.path)
        mindmap_save_match = re.match(r"^/api/mindmaps/([^/]+)$", parsed.path)
        mindmap_search_match = re.match(r"^/api/mindmaps/([^/]+)/paper-search$", parsed.path)
        mindmap_add_paper_match = re.match(r"^/api/mindmaps/([^/]+)/paper-instances$", parsed.path)
        if not library_add_match and not library_upload_match and not library_metadata_match and not project_context_match and not candidate_brief_match and not candidate_annotations_match and not candidate_metadata_match and not candidate_save_match and not attach_pdf_match and not annotations_match and not thinking_match and not chat_match and not reading_narrative_match and not takeaway_match and not explain_match and not metadata_match and not find_pdf_match and not reading_progress_match and not process_match and not translate_match and not citations_match and not videos_match and not reference_add_match and not canvas_boards_match and not canvas_board_match and not canvas_sync_apply_match and not mindmap_create_match and not mindmap_doc_save_match and not mindmap_duplicate_match and not mindmap_doc_add_paper_match and not mindmap_sync_apply_match and not mindmap_save_match and not mindmap_search_match and not mindmap_add_paper_match:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)

        if candidate_brief_match:
            try:
                content_type = self.headers.get("Content-Type", "")
                if "multipart/form-data" in content_type:
                    fields, files = parse_multipart_form(content_type, raw_body)
                    if not files:
                        raise ValueError("No PDF file uploaded")
                    filename, content = files[0]
                    result = generate_candidate_brief(
                        self.workspace,
                        pdf_bytes=content,
                        filename=filename,
                        source_url=fields.get("source_url", ""),
                        source_page_url=fields.get("source_page_url", ""),
                        prompt_override=fields.get("prompt", ""),
                        force=str(fields.get("force", "")).lower() in {"1", "true", "yes"},
                    )
                else:
                    data = json.loads(raw_body.decode("utf-8") or "{}") if raw_body.strip() else {}
                    pdf_url = str(data.get("pdf_url") or "").strip()
                    local_pdf_path = str(data.get("local_pdf_path") or "").strip()
                    if local_pdf_path:
                        source_path = Path(local_pdf_path).expanduser().resolve()
                        if not source_path.exists() or not source_path.is_file():
                            raise FileNotFoundError(f"Local PDF not found: {source_path}")
                        filename = str(data.get("filename") or source_path.name)
                        content = source_path.read_bytes()
                        if bool(data.get("delete_local_pdf_after_import")) and "paper-reader-agent-temp" in source_path.parts:
                            try:
                                source_path.unlink()
                            except OSError:
                                pass
                    elif pdf_url:
                        filename, content = download_pdf_bytes(pdf_url, browser_pdf_request_headers(data, pdf_url))
                    else:
                        raise ValueError("pdf_url or uploaded PDF file is required")
                    result = generate_candidate_brief(
                        self.workspace,
                        pdf_bytes=content,
                        filename=str(data.get("filename") or filename),
                        source_url=str(data.get("source_url") or pdf_url or local_pdf_path),
                        source_page_url=str(data.get("source_page_url") or ""),
                        prompt_override=str(data.get("prompt") or ""),
                        force=bool(data.get("force")),
                    )
                self.send_json({"ok": True, "candidate": result, "paper_brief": result.get("paper_brief", "")})
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
            return

        if library_upload_match:
            try:
                query = urllib.parse.parse_qs(parsed.query)
                duplicate_policy = (query.get("duplicate_policy", ["ask"])[0] or "ask").lower()
                replace_paper_id = (query.get("replace_paper_id", [""])[0] or "").strip() or None
                upload_tags = normalize_tag_paths(query.get("tags", [""])[0] or "")
                upload_projects = normalize_project_list(query.get("projects", [""])[0] or "")
                files = parse_multipart_files(self.headers.get("Content-Type", ""), raw_body)
                results = []
                for index, (filename, content) in enumerate(files):
                    result = register_uploaded_pdf(
                        self.workspace,
                        filename,
                        content,
                        tags=upload_tags,
                        projects=upload_projects,
                        duplicate_policy=duplicate_policy if len(files) == 1 else "ask",
                        replace_paper_id=replace_paper_id if len(files) == 1 else None,
                        generate_pdf_preview=False,
                        enrich_citation=False,
                    )
                    if result.get("duplicate"):
                        results.append(result)
                        continue
                    paper_id = result["paper_id"]
                    paper_dir = self.get_paper_dir(paper_id)
                    if paper_dir:
                        result["metadata"] = prepare_pdf_brief_then_background(self.workspace, paper_id, paper_dir, {}, mode="deep")
                    results.append(result)
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "count": len([item for item in results if not item.get("duplicate")]), "duplicate_count": len([item for item in results if item.get("duplicate")]), "papers": results})
            return

        if attach_pdf_match:
            paper_id = urllib.parse.unquote(attach_pdf_match.group(1))
            paper_dir = self.get_paper_dir(paper_id)
            if not paper_dir:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                files = parse_multipart_files(self.headers.get("Content-Type", ""), raw_body)
                if not files:
                    raise ValueError("No PDF file uploaded")
                filename, content = files[0]
                (paper_dir / "original.pdf").write_bytes(content)
                metadata = read_json(paper_dir / "metadata.json", {})
                metadata.update(
                    {
                        "source_pdf": "original.pdf",
                        "source_pdf_name": filename,
                        "source_type": metadata.get("source_type", "pdf"),
                        "processing_mode": metadata.get("processing_mode", "library-only"),
                        "reading_mode": metadata.get("reading_mode", metadata.get("processing_mode", "library-only")),
                        "processing_status": metadata.get("processing_status", "not_processed"),
                        "updated_at": now_iso(),
                    }
                )
                write_json(paper_dir / "metadata.json", metadata)
                sync_library_from_metadata(self.workspace, paper_id, paper_dir, metadata, generate_pdf_preview=False)
                metadata = prepare_pdf_brief_then_background(self.workspace, paper_id, paper_dir, {}, mode="deep")
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "paper_id": paper_id, "metadata": metadata})
            return

        body = raw_body.decode("utf-8")
        try:
            data = json.loads(body) if body.strip() else {}
        except json.JSONDecodeError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
            return

        if library_metadata_match:
            payload = data if isinstance(data, dict) else {}
            paper_ids = [str(item or "").strip() for item in payload.get("paper_ids", []) if str(item or "").strip()]
            metadata_data = payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {}
            if not paper_ids:
                self.send_error(HTTPStatus.BAD_REQUEST, "paper_ids must be a non-empty list")
                return
            if not metadata_data:
                self.send_error(HTTPStatus.BAD_REQUEST, "metadata must be a non-empty object")
                return
            updated = []
            missing = []
            for item_id in paper_ids:
                paper_id = urllib.parse.unquote(item_id)
                paper_dir = self.get_paper_dir(paper_id)
                if not paper_dir:
                    missing.append(paper_id)
                    continue
                metadata = apply_paper_metadata_update(self.workspace, paper_id, paper_dir, metadata_data, generate_pdf_preview=False)
                updated.append({"paper_id": paper_id, "metadata": metadata})
            if not updated:
                self.send_error(HTTPStatus.NOT_FOUND, "No matching papers found")
                return
            self.send_json({"ok": True, "updated": updated, "missing": missing})
            return

        if project_context_match:
            project = urllib.parse.unquote(project_context_match.group(1))
            try:
                payload = data if isinstance(data, dict) else {}
                source_path = str(payload.get("source_path") or "").strip()
                if payload.get("refresh", True):
                    context = refresh_project_context_from_source(self.workspace, project, source_path)
                else:
                    context = upsert_project_context(self.workspace, project, {"source_path": source_path})
            except FileNotFoundError as exc:
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "context": context, "project_contexts": read_project_contexts(self.workspace)})
            return

        if candidate_annotations_match:
            candidate_id = urllib.parse.unquote(candidate_annotations_match.group(1))
            try:
                annotations = save_candidate_annotations(self.workspace, candidate_id, data if isinstance(data, dict) else {})
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "annotations": annotations.get("annotations", []), "candidate": read_candidate(self.workspace, candidate_id)})
            return

        if candidate_metadata_match:
            candidate_id = urllib.parse.unquote(candidate_metadata_match.group(1))
            try:
                candidate = update_candidate_metadata(self.workspace, candidate_id, data if isinstance(data, dict) else {})
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "candidate": candidate})
            return

        if candidate_save_match:
            candidate_id = urllib.parse.unquote(candidate_save_match.group(1))
            try:
                result = migrate_candidate_to_library(self.workspace, candidate_id, data if isinstance(data, dict) else {})
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json(result)
            return

        if canvas_boards_match:
            try:
                board = create_canvas_board(self.workspace, data if isinstance(data, dict) else {})
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "board": board, **list_canvas_boards(self.workspace)})
            return

        if canvas_board_match and not canvas_sync_apply_match:
            board_id = urllib.parse.unquote(canvas_board_match.group(1))
            try:
                board = upsert_canvas_board(self.workspace, {**(data if isinstance(data, dict) else {}), "id": board_id})
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "board": board, "sync_proposals": canvas_sync_proposals(self.workspace, board)})
            return

        if canvas_sync_apply_match:
            board_id = urllib.parse.unquote(canvas_sync_apply_match.group(1))
            try:
                board = read_canvas_board(self.workspace, board_id)
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            selected_ids = set(str(item) for item in data.get("proposal_ids", [])) if isinstance(data, dict) else set()
            proposals = canvas_sync_proposals(self.workspace, board)
            applied: list[dict[str, Any]] = []
            for proposal in proposals:
                if selected_ids and proposal["id"] not in selected_ids:
                    continue
                if proposal.get("type") != "add-tag-to-paper":
                    continue
                record = find_paper_record(self.workspace, proposal.get("paper_id", ""))
                if not record:
                    continue
                paper_dir = self.workspace / record.get("paper_dir", "")
                metadata = read_json(paper_dir / "metadata.json", {})
                tags = normalize_tag_paths(metadata.get("tags", record.get("tags", [])))
                tag = normalize_tag_paths(proposal.get("to", ""))
                if tag and tag not in tags:
                    metadata["tags"] = tags + [tag]
                    metadata["updated_at"] = now_iso()
                    write_json(paper_dir / "metadata.json", metadata)
                    sync_library_from_metadata(self.workspace, proposal.get("paper_id", ""), paper_dir, metadata)
                    applied.append(proposal)
            self.send_json({"ok": True, "applied": applied, "library": load_library(self.workspace), "sync_proposals": canvas_sync_proposals(self.workspace, board)})
            return

        if mindmap_create_match:
            try:
                doc = create_mindmap(self.workspace, data if isinstance(data, dict) else {})
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "mindmap": doc, **list_mindmaps(self.workspace, doc.get("project", "")), "library": load_library(self.workspace), "tag_dictionary": tag_dictionary()})
            return

        if mindmap_duplicate_match:
            project = urllib.parse.unquote(mindmap_duplicate_match.group(1))
            mindmap_id = urllib.parse.unquote(mindmap_duplicate_match.group(2))
            try:
                doc = duplicate_mindmap(self.workspace, project, mindmap_id, str(data.get("title") or "") if isinstance(data, dict) else "")
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "mindmap": doc, **list_mindmaps(self.workspace, project), "library": load_library(self.workspace), "tag_dictionary": tag_dictionary()})
            return

        if mindmap_sync_apply_match:
            project = urllib.parse.unquote(mindmap_sync_apply_match.group(1))
            mindmap_id = urllib.parse.unquote(mindmap_sync_apply_match.group(2))
            try:
                doc = read_mindmap(self.workspace, project, mindmap_id, seed=True)
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            selected_ids = set(str(item) for item in data.get("proposal_ids", [])) if isinstance(data, dict) else set()
            proposals = mindmap_sync_proposals(self.workspace, doc)
            applied = apply_mindmap_sync_proposals(self.workspace, proposals, selected_ids)
            self.send_json({"ok": True, "applied": applied, "library": load_library(self.workspace), "proposals": mindmap_sync_proposals(self.workspace, doc)})
            return

        if mindmap_doc_save_match and not mindmap_duplicate_match and not mindmap_doc_add_paper_match and not mindmap_sync_apply_match and not mindmap_search_match and not mindmap_add_paper_match:
            project = urllib.parse.unquote(mindmap_doc_save_match.group(1))
            mindmap_id = urllib.parse.unquote(mindmap_doc_save_match.group(2))
            try:
                doc = write_mindmap(self.workspace, project, data if isinstance(data, dict) else {}, mindmap_id)
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "mindmap": doc, **list_mindmaps(self.workspace, project)})
            return

        if mindmap_save_match and not mindmap_search_match and not mindmap_add_paper_match:
            project = urllib.parse.unquote(mindmap_save_match.group(1))
            try:
                doc = write_mindmap(self.workspace, project, data if isinstance(data, dict) else {}, safe_mindmap_id(data.get("id") if isinstance(data, dict) else ""))
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "mindmap": doc, **list_mindmaps(self.workspace, project)})
            return

        if mindmap_search_match:
            project = urllib.parse.unquote(mindmap_search_match.group(1))
            query = str(data.get("query") or "") if isinstance(data, dict) else ""
            limit = int(data.get("limit") or 30) if isinstance(data, dict) else 30
            self.send_json({"ok": True, "project": normalize_mindmap_project(project), "results": mindmap_search_papers(self.workspace, query, project, limit)})
            return

        if mindmap_doc_add_paper_match or mindmap_add_paper_match:
            project = urllib.parse.unquote((mindmap_doc_add_paper_match or mindmap_add_paper_match).group(1))
            if mindmap_doc_add_paper_match and isinstance(data, dict):
                data["mindmap_id"] = urllib.parse.unquote(mindmap_doc_add_paper_match.group(2))
            try:
                result = add_paper_instance_to_mindmap(self.workspace, project, data if isinstance(data, dict) else {})
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, **result, **list_mindmaps(self.workspace, project), "library": load_library(self.workspace)})
            return

        if library_add_match:
            pdf_value = str(data.get("path") or data.get("pdf") or "").strip().strip('"')
            title_value = str(data.get("title") or "").strip()
            tags = normalize_tag_paths(data.get("tags", []))
            projects = normalize_project_list(data.get("projects", data.get("project", [])))
            tag_colors = data.get("tag_colors") if isinstance(data.get("tag_colors"), dict) else {}
            project_colors = data.get("project_colors") if isinstance(data.get("project_colors"), dict) else {}
            try:
                if pdf_value and pdf_value != DEFAULT_PDF_LIBRARY_PATH:
                    result = register_paper_in_library(
                        self.workspace,
                        Path(pdf_value).expanduser().resolve(),
                        paper_id=str(data.get("paper_id") or "").strip() or None,
                        title=title_value or None,
                        tags=tags,
                        projects=projects,
                        tag_colors=tag_colors,
                        project_colors=project_colors,
                        duplicate_policy=str(data.get("duplicate_policy") or "ask").strip().lower() or "ask",
                        replace_paper_id=str(data.get("replace_paper_id") or "").strip() or None,
                        generate_pdf_preview=False,
                        enrich_citation=False,
                    )
                    should_process_pdf = True
                else:
                    result = register_metadata_only_paper(
                        self.workspace,
                        title_value,
                        paper_id=str(data.get("paper_id") or "").strip() or None,
                        tags=tags,
                        projects=projects,
                        tag_colors=tag_colors,
                        project_colors=project_colors,
                        metadata_fields=data if isinstance(data, dict) else {},
                        duplicate_policy=str(data.get("duplicate_policy") or "ask").strip().lower() or "ask",
                        replace_paper_id=str(data.get("replace_paper_id") or "").strip() or None,
                    )
                    should_process_pdf = False
                if result.get("duplicate"):
                    self.send_json(result)
                    return
                paper_dir = self.get_paper_dir(result["paper_id"])
                if paper_dir:
                    if should_process_pdf:
                        result["metadata"] = prepare_pdf_brief_then_background(self.workspace, result["paper_id"], paper_dir, data if isinstance(data, dict) else {}, mode="deep")
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, **result})
            return

        paper_id = urllib.parse.unquote((annotations_match or thinking_match or chat_match or reading_narrative_match or takeaway_match or explain_match or metadata_match or find_pdf_match or reading_progress_match or process_match or translate_match or citations_match or videos_match or reference_add_match).group(1))
        paper_dir = self.get_paper_dir(paper_id)
        if not paper_dir:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        if explain_match:
            segments = load_segments(paper_dir)
            outline_data = read_json(paper_dir / "outline.json", {"outline": []})
            outline = outline_data.get("outline", []) if isinstance(outline_data, dict) else []
            if not segments and (paper_dir / "raw.md").exists():
                raw_md = (paper_dir / "raw.md").read_text(encoding="utf-8")
                segments, outline = build_segments(raw_md)
            metadata = normalized_metadata(paper_dir, read_json(paper_dir / "metadata.json", {}))
            source_name = metadata.get("source_pdf") or "raw.md"
            if (paper_dir / "original.pdf").exists():
                thinking = update_paper_brief_from_pdf(self.workspace, paper_dir, metadata, source_name, force=True)
            else:
                if str(metadata.get("source_type") or "").lower() in {"reference", "metadata"}:
                    self.send_error(HTTPStatus.BAD_REQUEST, "Attach a PDF before generating a Paper Brief for this Library item.")
                    return
                thinking = update_explanation_from_pdf(paper_dir, metadata, segments, outline, source_name, force=True)
            self.send_json({"ok": True, "thinking": thinking})
            return

        if thinking_match:
            try:
                cleaned = save_thinking_update(paper_dir, data)
            except ValueError as exc:
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            self.send_json({"ok": True, "thinking": cleaned})
            return

        if chat_match:
            try:
                result = append_chat_output_block(paper_id, paper_dir, data if isinstance(data, dict) else {})
            except Exception as exc:  # noqa: BLE001
                self.send_json({"ok": False, "error": chat_exception_message(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            self.send_json({"ok": True, **result})
            return

        if reading_narrative_match:
            try:
                result = append_reading_narrative_block(self.workspace, paper_id, paper_dir, data if isinstance(data, dict) else {})
            except Exception as exc:  # noqa: BLE001
                self.send_json({"ok": False, "error": chat_exception_message(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            self.send_json({"ok": True, **result})
            return

        if takeaway_match:
            cleaned = clean_takeaway_doc(data if isinstance(data, dict) else {})
            write_json(paper_dir / "takeaway_doc.json", cleaned)
            schedule_export_notes_and_annotated(paper_dir)
            self.send_json({"ok": True, "takeaway_doc": cleaned})
            return

        if process_match:
            mode = str(data.get("mode") or "").strip().lower()
            if mode not in {"skim", "deep"}:
                self.send_error(HTTPStatus.BAD_REQUEST, "mode must be skim or deep")
                return
            try:
                metadata = prepare_pdf_brief_then_background(self.workspace, paper_id, paper_dir, data, mode=mode)
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
                return
            self.send_json({"ok": True, "mode": mode, "metadata": metadata})
            return

        if translate_match:
            if not isinstance(data, dict):
                self.send_error(HTTPStatus.BAD_REQUEST, "translation request must be an object")
                return
            try:
                translation = translation_job_manager().submit(paper_id, paper_dir, data)
            except ValueError as exc:
                self.send_error(HTTPStatus.BAD_REQUEST, str(exc))
                return
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
                return
            self.send_json({"ok": True, "translation": translation})
            return

        if citations_match:
            try:
                metadata = refresh_paper_citations(self.workspace, paper_id, paper_dir)
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
                return
            self.send_json({"ok": True, "metadata": metadata})
            return

        if videos_match:
            try:
                metadata = refresh_paper_videos(self.workspace, paper_id, paper_dir, force=bool(data.get("force", True)))
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
                return
            self.send_json({"ok": True, "metadata": metadata, "youtube_quota": metadata.get("youtube_quota", youtube_quota_state(self.workspace))})
            return

        if find_pdf_match:
            try:
                result = find_and_attach_pdf_to_existing_paper(self.workspace, paper_id, paper_dir, force=bool(data.get("force", True)))
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
                return
            self.send_json(result)
            return

        if reading_progress_match:
            try:
                progress, metadata = update_reading_progress(self.workspace, paper_id, paper_dir, data if isinstance(data, dict) else {})
            except Exception as exc:  # noqa: BLE001
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
                return
            self.send_json({"ok": True, "reading_progress": progress, "metadata": metadata})
            return

        if reference_add_match:
            number = reference_add_match.group(2)
            card = get_reference_card(paper_dir, number, enrich=True)
            if not card:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            incoming_title = str(data.get("title") or "").strip()
            incoming_matches_card = not incoming_title or not card.get("title") or reference_title_match_score(card.get("title"), incoming_title) >= 0.72
            for key in {"abstract", "abstract_zh", "title", "authors", "venue", "year", "doi", "url", "pdf_url", "open_access_pdf_url", "semantic_scholar_url", "arxiv_id"}:
                if data.get(key) and (incoming_matches_card or (key == "title" and not card.get("title"))):
                    card[key] = data[key]
            tags = data.get("tags", [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
            if not isinstance(tags, list):
                tags = []
            projects = data.get("projects", [])
            if isinstance(projects, str):
                projects = [project.strip() for project in projects.split(",") if project.strip()]
            if not isinstance(projects, list):
                projects = []
            save_reference_card(paper_dir, card)
            result = add_reference_to_library(
                self.workspace,
                card,
                paper_id,
                tags=[str(tag).strip() for tag in tags if str(tag).strip()],
                projects=[str(project).strip() for project in projects if str(project).strip()],
                importance=data.get("importance", ""),
            )
            self.send_json({"ok": True, "reference": card, **result})
            return

        if metadata_match:
            metadata = apply_paper_metadata_update(self.workspace, paper_id, paper_dir, data if isinstance(data, dict) else {}, generate_pdf_preview=False)
            self.send_json({"ok": True, "metadata": metadata})
            return

        annotations_started = time.perf_counter()
        if not isinstance(data, dict):
            self.send_error(HTTPStatus.BAD_REQUEST, "annotations must be an object")
            return
        annotations = data.get("annotations")
        if not isinstance(annotations, list) or any(not isinstance(item, dict) for item in annotations):
            self.send_error(HTTPStatus.BAD_REQUEST, "annotations must be a list of objects")
            return
        existing_annotations = read_json(paper_dir / "annotations.json", {"annotations": []}, strict=True)
        if not isinstance(existing_annotations, dict):
            self.send_error(HTTPStatus.BAD_REQUEST, "annotations.json must contain an object")
            return
        annotations = merge_records_by_id(existing_annotations.get("annotations"), annotations)
        cleaned = []
        for item in annotations:
            if not isinstance(item, dict):
                continue
            segment_id = str(item.get("segment_id", ""))
            if not segment_id.strip():
                self.send_error(HTTPStatus.BAD_REQUEST, "Each paper annotation must retain its segment_id")
                return
            cleaned_item: dict[str, Any] = {
                **item,
                "id": str(item.get("id") or f"a-{uuid.uuid4().hex[:12]}"),
                "segment_id": segment_id,
                "color": str(item.get("color", "yellow")).strip() or "yellow",
                "quote": str(item.get("quote", "")),
                "note": str(item.get("note", "")),
                "updated_at": item.get("updated_at") or now_iso(),
            }
            tags = item.get("tags", [])
            if isinstance(tags, str):
                tags = [tags]
            if isinstance(tags, list):
                cleaned_item["tags"] = list(tags)
            if item.get("created_at"):
                cleaned_item["created_at"] = item.get("created_at")
            for key in {"type", "target", "presentation_flow_id"}:
                if item.get(key):
                    cleaned_item[key] = str(item.get(key))
            for key in {"annotation_group_id", "group_quote"}:
                if item.get(key):
                    cleaned_item[key] = str(item.get(key))
            for key in {"group_index", "group_count"}:
                if item.get(key) is not None:
                    try:
                        cleaned_item[key] = int(item.get(key))
                    except (TypeError, ValueError):
                        pass
            for key in {"media_src", "media_alt"}:
                if item.get(key):
                    cleaned_item[key] = str(item.get(key))
            range_value = clean_annotation_range(item.get("range"))
            if range_value:
                cleaned_item["range"] = {**item["range"], **range_value}
            paired_range = clean_annotation_range(item.get("paired_range"))
            if paired_range:
                paired = {**item["paired_range"], **paired_range}
                if isinstance(item.get("paired_range"), dict) and item["paired_range"].get("target"):
                    paired["target"] = str(item["paired_range"].get("target"))
                if isinstance(item.get("paired_range"), dict) and item["paired_range"].get("quote"):
                    paired["quote"] = str(item["paired_range"].get("quote"))
                cleaned_item["paired_range"] = paired
            cleaned.append(cleaned_item)
        cleaned_at = time.perf_counter()
        write_json(paper_dir / "annotations.json", {**existing_annotations, "annotations": cleaned, "updated_at": now_iso()})
        written_at = time.perf_counter()
        schedule_export_notes_and_annotated(paper_dir)
        scheduled_at = time.perf_counter()
        self.send_json({"ok": True, "count": len(cleaned)})
        finished_at = time.perf_counter()
        total_ms = (finished_at - annotations_started) * 1000
        if total_ms > 250:
            print(
                "Slow annotation save "
                f"paper_id={paper_id} count={len(cleaned)} "
                f"clean_ms={(cleaned_at - annotations_started) * 1000:.0f} "
                f"write_ms={(written_at - cleaned_at) * 1000:.0f} "
                f"schedule_ms={(scheduled_at - written_at) * 1000:.0f} "
                f"send_ms={(finished_at - scheduled_at) * 1000:.0f} "
                f"total_ms={total_ms:.0f}",
                file=sys.stderr,
            )

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        block_match = re.match(r"^/api/papers/([^/]+)/thinking/blocks/([^/]+)$", parsed.path)
        canvas_board_match = re.match(r"^/api/canvas/boards/([^/]+)$", parsed.path)
        mindmap_doc_match = re.match(r"^/api/mindmaps/([^/]+)/([^/]+)$", parsed.path)
        match = re.match(r"^/api/papers/([^/]+)$", parsed.path)
        if canvas_board_match:
            board_id = urllib.parse.unquote(canvas_board_match.group(1))
            deleted = delete_canvas_board(self.workspace, board_id)
            self.send_json({"ok": True, "deleted": deleted, "board_id": board_id, **list_canvas_boards(self.workspace)})
            return
        if mindmap_doc_match:
            project = urllib.parse.unquote(mindmap_doc_match.group(1))
            mindmap_id = urllib.parse.unquote(mindmap_doc_match.group(2))
            query = urllib.parse.parse_qs(parsed.query)
            archive = (query.get("archive", ["0"])[0] or "0").lower() in {"1", "true", "yes"}
            deleted = delete_mindmap(self.workspace, project, mindmap_id, archive=archive)
            self.send_json({"ok": True, "deleted": deleted, "mindmap_id": mindmap_id, **list_mindmaps(self.workspace, project)})
            return
        if not match and not block_match:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        paper_id = urllib.parse.unquote((block_match or match).group(1))
        paper_dir = self.get_paper_dir(paper_id)
        if not paper_dir:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if block_match:
            block_id = urllib.parse.unquote(block_match.group(2))
            thinking = delete_thinking_block(paper_dir, block_id)
            self.send_json({"ok": True, "paper_id": paper_id, "block_id": block_id, "thinking": thinking})
            return
        try:
            paper_dir.resolve().relative_to((self.workspace / "papers").resolve())
        except ValueError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid paper directory")
            return
        remove_paper_record(self.workspace, paper_id)
        if paper_dir.exists():
            shutil.rmtree(paper_dir)
        self.send_json({"ok": True, "paper_id": paper_id})


def serve(args: argparse.Namespace) -> None:
    workspace = resolve_workspace(args.workspace)
    ensure_workspace(workspace)
    resumed = resume_interrupted_processing_tasks(workspace)
    ReaderHandler.workspace = workspace
    server = ThreadingHTTPServer((args.host, args.port), ReaderHandler)
    url = f"http://{args.host}:{args.port}/"
    print(f"Serving workspace: {workspace}")
    print(f"Reader URL: {url}")
    if resumed:
        print(f"Resumed interrupted processing for {len(resumed)} paper(s): {', '.join(resumed)}")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server...")
    finally:
        server.server_close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="paper-reader-agent", description="Local paper reading workspace helper")
    parser.add_argument("--workspace", help="Reading workspace directory. Defaults to config or ./paper_reading_workspace")
    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init", help="Create a portable reading workspace")
    init_cmd.add_argument("--no-config", action="store_true", help="Do not write .paper-reader-agent.json in the current folder")
    init_cmd.set_defaults(func=init_workspace)

    ingest_cmd = sub.add_parser("ingest", help="Import a PDF or raw Markdown into the reading workspace")
    ingest_cmd.add_argument("pdf", nargs="?", help="PDF path to import")
    ingest_cmd.add_argument("--raw-md", help="Use an existing MinerU/raw Markdown file instead of running MinerU")
    ingest_cmd.add_argument("--paper-id", help="Stable paper id to use")
    ingest_cmd.add_argument("--title", help="Override title")
    ingest_cmd.add_argument("--backend", default="pipeline", help="MinerU backend, default: pipeline")
    ingest_cmd.add_argument("--method", default="auto", help="MinerU parse method, default: auto")
    ingest_cmd.add_argument("--lang", default="en", help="MinerU OCR language, default: en")
    ingest_cmd.add_argument("--start", type=int, help="Start page, zero-based")
    ingest_cmd.add_argument("--end", type=int, help="End page, zero-based")
    ingest_cmd.set_defaults(func=ingest_pdf)

    register_cmd = sub.add_parser("register", help="Add a PDF to Library without parsing or translating it")
    register_cmd.add_argument("pdf", help="PDF path to add to Library")
    register_cmd.add_argument("--paper-id", help="Stable paper id to use")
    register_cmd.add_argument("--title", help="Override title")
    register_cmd.add_argument("--tags", help="Comma-separated paper type tags")
    register_cmd.set_defaults(func=register_paper_cli)

    process_cmd = sub.add_parser("process", help="Process a Library paper as skim or deep reading")
    process_cmd.add_argument("paper_id", help="Paper id to process")
    process_cmd.add_argument("--mode", choices=["skim", "deep"], required=True, help="Processing mode")
    process_cmd.add_argument("--backend", default="pipeline", help="MinerU backend, default: pipeline")
    process_cmd.add_argument("--method", default="auto", help="MinerU parse method, default: auto")
    process_cmd.add_argument("--lang", default="en", help="MinerU OCR language, default: en")
    process_cmd.add_argument("--start", type=int, help="Start page, zero-based")
    process_cmd.add_argument("--end", type=int, help="End page, zero-based")
    process_cmd.set_defaults(func=process_paper_cli)

    serve_cmd = sub.add_parser("serve", help="Start the local web reader")
    serve_cmd.add_argument("--host", default="127.0.0.1")
    serve_cmd.add_argument("--port", type=int, default=8765)
    serve_cmd.add_argument("--open", action="store_true", help="Open the reader in the browser")
    serve_cmd.set_defaults(func=serve)

    doctor_cmd = sub.add_parser("doctor", help="Check tool and MinerU availability")
    doctor_cmd.set_defaults(func=doctor)

    status_cmd = sub.add_parser("status", help="List papers in the workspace")
    status_cmd.set_defaults(func=list_status)

    query_cmd = sub.add_parser("query", help="Find papers from library.json and optionally export their Briefings")
    query_cmd.add_argument("--project", help="Match one project name exactly, case-insensitive")
    query_cmd.add_argument("--tag", help="Match one normalized paper tag")
    query_cmd.add_argument("--search", help="Case-insensitive text search across title, id, authors, venue, year, projects, and tags")
    query_cmd.add_argument("--brief", choices=["any", "available", "missing"], default="any", help="Filter by actual Briefing content availability")
    query_cmd.add_argument("--include-briefs", action="store_true", help="Include full explain.content bodies; omitted by default to keep output compact")
    query_cmd.add_argument("--limit", type=int, default=0, help="Maximum returned papers after filtering; zero returns all matches")
    query_cmd.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format, default: json")
    query_cmd.add_argument("--output", help="Write output to this path; relative paths are resolved inside the workspace")
    query_cmd.set_defaults(func=query_papers_cli)

    citations_cmd = sub.add_parser("citations", help="Refresh online citation counts for one paper or the whole Library")
    citations_cmd.add_argument("paper_id", nargs="?", help="Paper id to refresh. Omit to refresh all papers")
    citations_cmd.set_defaults(func=refresh_citations_cli)

    rebuild_cmd = sub.add_parser("rebuild", help="Regenerate reader.md, annotated.md, and notes.md after agent edits")
    rebuild_cmd.add_argument("paper_id", nargs="?", help="Paper id to rebuild. Omit to rebuild all papers in the workspace")
    rebuild_cmd.set_defaults(func=rebuild_outputs)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"Command failed with exit code {exc.returncode}: {' '.join(map(str, exc.cmd))}", file=sys.stderr)
        return exc.returncode or 1
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
