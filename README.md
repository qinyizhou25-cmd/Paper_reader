# Paper Reader Agent

Local-first paper reading and sensemaking workspace for academic PDFs and Markdown.

Paper Reader Agent imports papers into a local file-backed workspace, serves an anchored web reader, stores highlights and notes as JSON/Markdown, and provides optional AI-assisted paper briefs, translation, skim summaries, source-grounded chat, citation/video helpers, and browser-side paper brief capture. It is intended for small-group trial use: users keep papers and notes on their own machine, and each user supplies their own API keys.

## What It Does

- Local Library for metadata, projects, tags, reading status, citations, PDF links, and video links.
- PDF or Markdown ingestion into stable reader files such as `raw.md`, `segments.json`, `outline.json`, and `reader.md`.
- Web reader with paragraph IDs, outline navigation, highlights, notes, figures, and tables.
- Sensemaking panel for editable Paper Brief / AI outputs and source-linked notes.
- All Notes, Takeaway Report, Mindmap, and Canvas workspaces for organizing reading traces.
- Optional Kimi / Moonshot cloud AI for paper briefs, Kimi file extraction, translation, skim summaries, and source-grounded chat.
- Optional local Ollama translation fallback when no Kimi key is configured.

Core reading, Library, notes, Takeaway, Mindmap, and Canvas features are local files. AI features are optional and require user-provided keys.

## Repository Layout

```text
paper-reader-agent/
  paper_reader_agent.py        # CLI, local HTTP server, API, persistence
  web/                         # Static web UI
    index.html
    app.js
    styles.css
  chrome_extension/            # Optional browser side panel helper
  paper-reader-app.ps1         # Optional Windows launcher
  .env.example                 # API-key/environment reference
```

The app creates and uses a separate workspace directory. Do not commit that workspace.

```text
paper_reading_workspace/
  library.json
  assets/
  paper_candidates/
  prompts/
  papers/<paper_id>/
    original.pdf
    raw.md
    segments.json
    outline.json
    metadata.json
    annotations.json
    thinking.json
    takeaway_doc.json
  mindmaps/
  canvas_boards/
```

## Requirements

- Python 3.10+.
- Windows PowerShell is the most tested environment, but the backend is plain Python standard library.
- Optional PDF conversion backend such as MinerU. Raw Markdown import works without MinerU.
- Optional Kimi / Moonshot API key for Paper Brief generation, Kimi PDF text extraction, source-grounded chat, cloud translation, and the Chrome side-panel brief workflow.
- Optional Ollama for local translation when no Kimi key is configured.
- Optional YouTube API key for related-video search.

No Python package install is required for the core server. External tools such as MinerU must be installed separately if you want PDF parsing.

## Quick Start

From this repository directory:

```powershell
py .\paper_reader_agent.py doctor
py .\paper_reader_agent.py --workspace .\paper_reading_workspace init
py .\paper_reader_agent.py --workspace .\paper_reading_workspace serve --port 8765 --open
```

For AI features, copy the environment template before starting the server:

```powershell
Copy-Item .env.example .env
notepad .env
```

Then open:

```text
http://127.0.0.1:8765/
```

Import a raw Markdown file:

```powershell
py .\paper_reader_agent.py --workspace .\paper_reading_workspace ingest --raw-md path\to\paper.md
```

Import or process a PDF, if your PDF converter is configured:

```powershell
py .\paper_reader_agent.py --workspace .\paper_reading_workspace ingest path\to\paper.pdf
py .\paper_reader_agent.py --workspace .\paper_reading_workspace process <paper_id> --mode deep
```

You can also launch the local server on Windows with:

```powershell
.\paper-reader-app.ps1 -Workspace .\paper_reading_workspace
```

## API Keys And Environment

Copy `.env.example` to `.env` in this repository folder, then replace the blank values with your own keys. Real `.env` files are ignored by git. You can also set the same variables in your shell or user environment; explicit process environment variables take precedence over `.env` values.

Current cloud AI support is Kimi / Moonshot-compatible. Older SiliconFlow and direct DeepSeek environment variables are no longer used by the current code path.

Kimi / Moonshot setup:

```env
PAPER_READER_KIMI_API_KEY=your_key_here
PAPER_READER_KIMI_BASE_URL=https://api.moonshot.cn/v1
PAPER_READER_KIMI_MODEL=kimi-k2.6
```

The legacy Moonshot aliases also work:

```env
MOONSHOT_API_KEY=your_key_here
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
MOONSHOT_MODEL=kimi-k2.6
```

Paper Reader uploads PDFs to Kimi for the browser Paper Brief workflow and deletes the uploaded Kimi file after extraction by default. To keep uploaded files in your Kimi account, set:

```env
PAPER_READER_KIMI_DELETE_FILES=0
```

If no Kimi key is configured, local Library, reading, notes, Takeaway, Mindmap, and Canvas features still work. AI-dependent cloud actions will show configuration errors instead of silently using someone else's key. Full-text translation can still use a local Ollama server when configured:

```env
PAPER_READER_TRANSLATION_MODEL=qwen2.5:7b-instruct
OLLAMA_HOST=http://127.0.0.1:11434
```

Optional video search uses either variable name:

```env
PAPER_READER_YOUTUBE_API_KEY=your_key_here
YOUTUBE_API_KEY=your_key_here
PAPER_READER_YOUTUBE_DAILY_LIMIT=90
PAPER_READER_YOUTUBE_MIN_SCORE=0.38
```

Optional workspace and PDF converter overrides:

```env
PAPER_READER_WORKSPACE=C:\path\to\paper_reading_workspace
PAPER_READER_MINERU=C:\path\to\mineru.bat
```

## Useful Commands

```powershell
py .\paper_reader_agent.py --workspace .\paper_reading_workspace status
py .\paper_reader_agent.py --workspace .\paper_reading_workspace register path\to\paper.pdf
py .\paper_reader_agent.py --workspace .\paper_reading_workspace rebuild <paper_id>
py .\paper_reader_agent.py --workspace .\paper_reading_workspace citations
py .\paper_reader_agent.py --workspace .\paper_reading_workspace serve --port 8765
```

## Chrome Extension

The `chrome_extension/` folder contains an optional local side-panel helper for collecting paper brief candidates from the browser. Load it unpacked from Chrome's extension page and point it to the local server, usually `http://127.0.0.1:8765`.

The side panel sends the selected PDF to the local backend, which uses the configured Kimi / Moonshot key for PDF text extraction and Paper Brief generation.

The extension requests broad host permissions so it can inspect web pages and PDFs selected by the user. Review the manifest before sharing it with testers.

## Privacy And Sharing Notes

- Do not commit your workspace directory, PDFs, generated paper files, `.env`, or logs.
- Do not commit API keys or browser cookies.
- Keep example paths generic.
- The app is local-first; users should choose their own workspace folder.
- For small-group trials, ask testers to report OS, Python version, PDF converter setup, browser, and the exact command they ran.

## Development Checks

```powershell
py -m py_compile .\paper_reader_agent.py
node --check .\web\app.js
Get-ChildItem .\chrome_extension -Filter *.js | ForEach-Object { node --check $_.FullName }
```

## Status

This is an early local research tool. It is suitable for source-based small-group testing, but it is not packaged as a polished installer yet.