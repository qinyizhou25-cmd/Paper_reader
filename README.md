# Paper Reader Agent

Local-first paper reading and original-note workspace for academic PDFs and Markdown.

## Focused Reader (Windows-first)

The current refocus keeps Feishu as the main collection and the local app as a
fast reader. The agreed scope and later integration/migration stages are in
[the local refocus plan](READER_REFOCUS_PLAN.md).

- Open several papers in persistent tabs, including in Read mode. Closing a tab
  never deletes its paper or notes. Arrow keys/Home/End navigate the tab strip.
  Each paper restores its reading mode and visible paragraph; delayed figure
  loading does not discard the saved paragraph position.
- Recent paper data is cached (up to eight clean sessions; cached files are
  refreshed on a later open after 60 seconds). **More -> Reload from disk** explicitly
  reads changes made by an agent after saving current edits.
- A paper displays without waiting for its reference index or all-library
  notes. All Notes loads only when opened. Library displays at most 40 paper
  rows per page and preserves edits when paging or filtering.
- **Question** saves a normal annotation tagged `question`; it does not call a
  model. Notes retain original text instead of an AI paraphrase.
- **Notes Markdown** and **Raw JSON** first flush current edits, then download
  mechanical exports. Raw reading data is the lossless source; Markdown is a
  readable view, not a format for automatically importing edits back.
- **More -> Publish to Feishu** previews the current saved reading records
  as four text columns in the existing paper row before explicit confirmation.
  It keeps a JSON backup and does not create a document or generate a summary.
- Figure captions can retain multiple adjacent extracted parts. The viewer
  shows each part and links to the original PDF. This does not claim to repair
  upstream bounding boxes or reconstruct an exact composite crop.
- Pending writes are serialized per paper. A failed save is visible; switching
  or closing that paper retries the latest snapshot and stays on it if saving
  still fails. Closing the browser with unsaved edits requests confirmation.
- Mindmap/Canvas entry points and automatic takeaway generation are removed
  from the core reading flow. Existing data is retained. Existing AI tools are
  optional. No new AI reporting is added. Feishu metadata intake is read-only;
  reading-record publication is a separate, explicitly confirmed action.
- Papers without a saved brief do not display an invented placeholder
  explanation. Existing briefs remain available in a collapsed disclosure.
- Web Library reads the existing `library.json` index without reopening every
  paper. Use the app's metadata operations to keep that index updated; an
  external edit to an individual metadata file alone does not refresh the
  Library index.

### Paper-like reading interface

- Warm off-white surfaces, dark text, and restrained blue-gray controls replace
  the green gradients and frosted panels. Reading uses locally installed
  Georgia/Songti/SimSun fallbacks; no web fonts or frontend dependencies are
  added. Existing local KaTeX assets are unchanged.
- Source text is 18px, with aligned, similarly sized translations. Personal
  notes appear in a warm-tinted right margin when the document area
  is at least 760px wide. Every paragraph shares the same text column, so one
  annotated paragraph does not become narrower than its neighbors. Long notes
  have an explicit **Read full note** control; editing/deletion remain visible.
  Narrow columns (including narrow Split panes) place the same colored cards
  below the passage instead of squeezing the text or covering later paragraphs.
  Repeated note/target labels are available through hover and accessible names,
  rather than printed on every card.
- **Width** in the top reading toolbar adjusts both source text and translations:
  **Comfortable** is up to 800px, **Wide** is up to 1280px (the default), and
  **Full width** fills the available reading area. All choices shrink to fit
  smaller screens. The browser remembers the choice across papers and reloads;
  changing it only updates CSS, without rebuilding or reloading the paper.
  It is disabled in **Notes only** mode and does not resize the notes side pane.
  These limits apply to the document area: when margin notes are present, a
  272px annotation column and 24px gap are reserved inside it on wide layouts.
- Figure **Highlight + note** / **Edit note** controls sit in a separate row
  above the image instead of covering its contents. Image previews, translated
  captions, table annotations, and existing saved notes are unchanged.
- The reading toolbar stays at the top. **Read**, **Split**, and **Notes only**
  are explicit layout choices. Opening **Saved Takeaway** changes only the
  side pane in Split; it never hides the paper or collapses its outline.
  Closing it also preserves the chosen layout. Saved writing remains editable,
  and opening a pane never generates a report.
- **More** contains paper details, Feishu metadata, original-file links, rating,
  exports, and reload. Escape closes just that menu and returns keyboard focus,
  without discarding an open note draft. Save failures remain visible in the
  reading toolbar; moving controls does not hide error/retry states.
- Repeated tutorial paragraphs are removed from the reader, Library, Notes,
  parsing queue and chat/paste composers. Input labels, source/mode tooltips,
  real progress/errors and unsaved-draft status remain.
- These are presentation changes, not a data migration. Existing source text,
  translations, annotation ranges, original notes, and per-paper reading modes
  remain intact. After saving any open draft, refresh an existing browser tab
  to load the new interface; restarting translation is unnecessary.

### Equations without duplicate translations

- Standalone equations appear once, in the original text. Equation-only blocks
  are not translation jobs; displayed equations are omitted from mixed-prose
  translation input, while inline variables remain with their surrounding text.
- The reader and source preview hide old repeated translated equations without
  rewriting the saved source or translation. Newly generated reading copies
  follow the same rule; existing on-disk copies are updated on rebuild/export.
  Within translated prose, matching ignores whitespace and nonsemantic equation
  tags; unmatched formulas and inline notation remain. For standalone mathematical
  blocks the original is authoritative, so a math-only translated copy is hidden.
  Explanatory prose, code and prices are not silently discarded.
- Old highlight positions stay relative to the saved translation. Display-only
  omissions project those ranges, and new text selections map back to the
  original positions. A note made on an older translated equation remains in
  Notes and its paragraph's margin even when that second equation is hidden.
  Raw JSON exports remain lossless.

### In-place AI teacher: a brief-aware local example

- The example is for **Towards Human-AI Deliberation: Design and
  Evaluation of LLM-Empowered Deliberative AI for AI-Assisted Decision-Making**.
  The second revision assumes the reader has read the saved Brief but not the
  source closely: **seven reading cues and three term definitions** cover the
  contribution, discussion unit, opinion update, study cases, accuracy, reliance
  and experience. Four cues are statements and three are light questions, each
  24-49 characters long; this is not a fixed question quota. The saved Brief
  informs selection, but claims are checked against the paper rather than
  treating the Brief's interpretations as facts.
- By default, only source marks and small right-margin labels appear. Clicking
  marked words, a margin label, or the location picker opens **one** short card;
  closing it returns to its label. Cues do not ask for a written answer.
  Existing complex questions and project-transfer prompts are retained behind
  **深入思考**; **返回导读** returns to the reading cues and definitions.
- Expanded teacher cards share the margin with personal notes, but have a blue-gray
  surface; identity remains in hover text and accessible names, without a
  repeated header on every card. Reading cues use a pale source highlight,
  and terms a dotted underline; neither is inserted into `annotations.json`.
  Text selections, personal highlights and citation/image controls take
  precedence over teacher hit testing. Margin labels support Enter/Space;
  Escape in an open card closes it and restores focus to its label.
  **AI teacher** toggles the suggestions without hiding or deleting human notes.
- A compact location picker beside **AI teacher** lists all valid cards in
  the selected layer in source order, with previous/next controls. It does not reload the paper or
  create notes; disabled/invalid cards are not navigable. It hides in Notes only.
- Definition cards contain the term, **本文定义** or **本文用法**, and a short
  external/general meaning, without a question, hints or a reflection action.
  The example retains the paper's deliberation definition and Cambridge gloss,
  and adds **Weight of Evidence (WoE)** and **appropriate reliance**. Unretrieved
  general explanations say **AI 概括**, with no invented citation or retrieval date.
  The paper label locates the source; numbered external links retain source
  titles, retrieval dates and scope in their hover/accessibility text.
- Deeper cards show questions before optional hints and explanations. **记下想法**
  opens a blank normal note attached to the passage;
  its prompting question is retained separately, not prefilled as the answer.
- **Save to Notes** explicitly adopts a definition with separate
  paper meaning, the retrieved/AI-summary distinction, available source URLs,
  retrieval dates and provenance. Repeat clicks/retries reuse the same record.
  The original card becomes a **single saved-definition card**, with **Saved**
  as a status and **Edit** as the action; it does not add a second copy underneath.
  Saving/failure states are explicit, and retry still works with Teacher hidden.
  Close collapses the saved card to a checked term label, rather than deleting it;
  deletion is available inside Edit.
  Accepted definitions display their own saved snapshot, independently of the
  current teacher file. Reader edits show the actual saved text, not the old AI
  definition. Turning Teacher off, switching to deeper questions or losing its
  optional file does not hide the saved note. Existing saved definitions need
  no migration. Full provenance remains in the saved data and exports instead
  of repeating an attribution paragraph inside the compact margin card.
  All Notes and Markdown exports label it as a saved AI definition; margin
  cards retain that identity in hover/accessibility text and a distinct color.
  It uses existing Notes and the `definition`
  tag; there is no new cross-paper glossary database.
  Editing retains that provenance and the reader's exact edits. Adoption alone
  does not count as a personal reflection or automatically mark a passage as
  carefully read; use a separate reflection note for your own response.
- Project-based questions cite a dated, local context snapshot and its source
  document. Project goals/hypotheses are not paper findings. The example does
  not continuously scan a project, upload memory, or refresh external definitions
  when a paper opens. External links open only when chosen.
- Cards live in the paper's optional `reading_teacher.json`, outside application
  code. Ordinary opening only checks that file's existence; the separate local
  `/api/papers/{id}/reading-teacher` request loads and validates it after the
  source has had its first paint, using the browser's idle period when available.
  There is no new model call, parser, font or dependency. A deferred load is
  cancelled if the reader switches papers; it resumes on returning, including
  after a failed tab switch. Delayed responses cannot replace another paper's
  teacher or newer source.
- Version 1 files identify the paper, document ID, creation time/author, sources
  and cards. Every primary/evidence anchor contains `segment_id`, an exact
  unique `quote` and `source_sha256` (SHA-256 of that segment's UTF-8 `markdown`,
  excluding translation). A `cue` has a short `text` (one paragraph, at most 180
  characters) and `form` (`statement` or `question`), without a mandatory
  question/hint/explanation chain. Project transfer and definitions are separate
  cards. Definition cards require `paper` and `external` meanings, but no
  `why`, `question`, `hint`, `explanation` or
  `comparison`. Older values for those fields remain valid and are retained
  in raw data/adoption provenance; legacy comparisons are not printed in the
  compact definition card. Optional `paper_kind: "quote"` checks the definition
  excerpt against the anchored paragraph, even when only the term is underlined;
  `"usage"` labels an account of how the paper uses a term. External meanings
  either reference a retrieved `source_id` or explicitly use `kind: "ai-summary"`,
  which cannot carry retrieval metadata. Other card kinds still require their
  thinking prompts and belong to the deeper layer.
  Transfer cards refer to explicit context IDs. The server rejects malformed
  files and hides source-stale cards with a
  visible explanation, never a whole-paragraph fallback.
- Modern Chromium/Safari/Firefox use the native CSS Highlight API, which does
  not replace source text nodes or destroy selections. Other browsers keep the
  cards and source-location buttons with an explicit underline-support notice.
  Raw JSON exports preserve the optional teacher file separately; Notes Markdown
  includes only the definitions/reflections the reader actually saved.
  A malformed teacher file does not block note saving or Notes Markdown;
  lossless Raw JSON still reports malformed JSON rather than silently omitting it.
- This is a curated, interactive teaching example, not an automatic teacher.
  The reader explicitly chose to validate this paper's content and interactions
  before building general manual/automatic generation. Model/provider
  orchestration, Brief/source bidirectional links, live project-memory
  synchronization and an independent terminology library remain deferred.
  The prior learning research
  and evidence boundaries are in [the research note](AI_READING_TEACHER_RESEARCH.md).

### Chat and pasted AI responses

- **AI chat** shows older conversations above newer ones, with the reader's
  question followed by the AI reply. History scrolls independently above the
  bottom message composer in both Split and Notes only. Rendering does not
  reorder the stored records or move the source paper.
- The question box is visible immediately. Opening it does not send a request;
  **Send** or Enter is explicit. Shift+Enter adds a newline, and confirming an
  IME candidate does not send. A pending question appears in the conversation;
  a failed request leaves an explicit error and keeps the draft for retry.
- AI replies remain selectable for highlights and original personal notes.
  **Message options** contains source/mode details, reply editing and explicit
  deletion of a conversation turn. Pasted replies and generated narratives
  retain their distinct labels; none are presented as original human notes.
- **Paste AI output** is a separate, full-width editor with a taller, resizable
  response box and an optional original question. **Save AI output** stores the
  pasted text verbatim as AI-origin content, not as a human note. It does not
  call a model. You can then highlight the saved response and attach your own
  thoughts.
- Switching composers or paper tabs keeps unsubmitted drafts within the current
  browser session, along with each paper's chat scroll position. Scrolling back
  to older messages is not undone by changing chat mode or saving a highlight.
  Draft sessions are protected from cache eviction, and closing
  the page warns about unsaved content. Drafts are not saved records: finish or
  clear them before exporting. Save errors preserve the added block and remain
  visible until a successful retry.

### Publishing reading records to Feishu

Publishing is a mechanical reading-data handoff, not a request to generate an
AI narrative. Four dedicated text columns in the existing paper row separate
original personal notes/highlights, recorded AI conversations, and accepted AI definitions. Notes
on an AI reply remain the reader's words while the quoted reply remains AI-origin.
Existing mixed-origin Takeaway records and previously generated material remain
separate; publication never calls the narrative, chat, briefing or translation
generators.
Generated speaker labels use `我:` and `AI:` without repeated "original"
disclaimers or per-message numbering. Quotation origins and uncertain authorship
remain explicit; these presentation changes never rewrite stored prose.

1. Associate the paper with its existing Feishu record using **More -> Feishu
   metadata** if needed. Publication never creates another paper record.
2. Choose **More -> Publish to Feishu** from the local reader. Saved edits are
   flushed before the preview. Unsubmitted chat/paste drafts are not records:
   finish them, or copy and clear them, before preparing a new preview.
3. Inspect the destination and expand each column to review its exact text and
   length. Preview does not write cloud content. Empty columns are shown
   explicitly; publishing can clear an empty category's previously managed cell.
4. Choose **Confirm & publish**. You can close the dialog and continue reading;
   the local server finishes the job. Reopen it to check progress and open the
   paper row in Feishu. Closing a browser is not a cloud rollback.
5. After later edits, prepare a fresh preview and update the same row.
   Unchanged saved content does not rewrite the cells or create another backup.
   New local edits made during an upload remain pending for a later publication.

Publication writes only these dedicated columns in the configured paper table:

| Default field | Required type | Content |
|---|---|---|
| `阅读笔记` | Plain text | Personal notes first, with original quotations and provenance |
| `AI 讨论` | Plain text | Recorded original questions and answers, with explicit roles |
| `已采纳定义` | Plain text | Accepted definitions, sources and saved reader edits |
| `其他阅读材料` | Plain text | Existing mixed-origin material, without a new summary |
| `阅读数据备份` | Attachment | Content-versioned JSON reading snapshots |

The columns must exist; the reader does not silently create/repurpose fields.
The optional `PAPER_READER_FEISHU_NOTES_FIELD`,
`PAPER_READER_FEISHU_DISCUSSIONS_FIELD`, `PAPER_READER_FEISHU_DEFINITIONS_FIELD`,
`PAPER_READER_FEISHU_MATERIALS_FIELD` and `PAPER_READER_FEISHU_BACKUP_FIELD`
settings select approved exact field names. Configure the resolved Base/table
and authenticated native `lark-cli` as for metadata intake. All cloud operations
use the user identity.

The four text cells are sent in one record update. Each includes its labels,
quotes and source locations in a conservative 100,000 UTF-16-unit limit; an
over-limit column stops the preview rather than truncating original content.
Large requests use a guarded local UTF-8 JSON file and the CLI's cwd-relative
`@file` input, not Windows command-line interpolation or an online agent.

These are **one-way reader-managed columns**, not bidirectional cloud editors.
A changed destination, observed cloud edit or stale local preview stops the
publication instead of blindly replacing another version. Preflight/readback
checks are not an atomic cloud compare-and-swap: avoid simultaneous edits to
these columns from another client. Existing manual-note columns remain separate.
Failures remain visible. Choose **Refresh preview** before retrying; a verified new
preview enables confirmation and reuses the recorded cell/backup receipts.
After a PATCH, bounded read-only retries tolerate delayed visibility of the
expected cell values. They never resend the PATCH; an unresolved result retains
its receipt for explicit recovery.
Ambiguous write outcomes require verification, not blind duplicate creation.
Existing backup versions and unrelated Base fields are never removed. Read
status, Raw Text and existing human/AI analysis columns are not written.

Previously published Docx archives and the `阅读档案` URL column are retained
unchanged, not refreshed by table publication. Their verified matching JSON
backups can be reused when moving to table publication. The App does not need
to fetch or update those documents. Legacy document publishing remains available
to existing service callers, but is not the App's default publication path.

The JSON backup retains stored source/translation segments, annotations,
thinking records and the optional teacher file. It is not a complete PDF/image
or machine backup: source binaries, credentials, logs, caches and unrelated
project files are excluded. Passive dwell/view changes do not continuously
create cloud revisions. **Notes Markdown / Raw JSON** remain available as
independent local downloads.

Publication is lazy and localhost-only (`localhost`, `127.0.0.1` or `::1`).
Opening a paper never contacts the publication service; status polling happens
only while its dialog is open. See
[the publishing design](READER_REFOCUS_PLAN.md#table-first-publication-2026-09-27).

### Source-first, progressive translation

Normal PDF intake now queues PDF-to-Markdown conversion without generating a
local Paper Brief, takeaway, citation search, or video search first. Existing
saved briefs remain available; they are not a reading prerequisite and are
not regenerated during ordinary reading.

To opt in to automatic translation through an already-running local Copilot
proxy, set these non-secret values in the ignored `.env` file and restart the
reader server:

```dotenv
PAPER_READER_TRANSLATION_PROVIDER=copilot
PAPER_READER_COPILOT_BASE_URL=http://127.0.0.1:4141/v1
PAPER_READER_COPILOT_MODEL=gpt-4.1
PAPER_READER_TRANSLATION_CONCURRENCY=2
```

- Open a paper to read the original Markdown immediately after parsing.
  Missing translations start automatically; existing translations are kept.
- A progress strip offers pause/resume/retry. Translation errors do not block
  original-text reading or note saving.
- Completed paragraphs are saved before the browser receives them. The reader
  polls for incremental updates, inserts only translation content, and keeps
  source highlights, unfinished note drafts, focus, and the visible paragraph.
- **Images appear only in the original content.** Translate surrounding prose
  and captions, not an unchanged second copy of the image. This also applies
  to screenshot-style tables; no image OCR/repainting is implied. Actual
  Markdown/HTML text tables retain translated cells, structure, and numbers.
  Inline/standalone image markup is excluded from new translation requests
  and replies. Existing translated image copies are suppressed in the reader,
  note previews, and generated reading Markdown without rewriting old source,
  translations, or annotation ranges. Raw JSON remains lossless.
- **Translation queue** shows requested papers and offers open/pause/resume/retry
  without switching away from the current paper. Its two-slot setting is a
  **global** request limit across papers, not two requests per tab. A single
  paper can use both slots for distinct paragraphs. The default remains one
  slot; supported settings are 1-4.
- Workers rotate between papers. Out-of-order replies are merged by paragraph
  ID after rechecking the source and existing translation. A failed request
  does not discard its successful peer's result.
- Copilot HTTP 429/503, timeouts, and connection errors trigger a shared
  cooldown, respecting `Retry-After` or using increasing backoff. At most three
  automatic retries are allowed per job; further failure requires manual retry.
  Pausing or a server restart retains already saved translations. Only requested
  papers join the current server session's queue; it never scans the Library
  to start translations.
- Only the paper's source paragraphs are sent. Highlights, questions, and notes
  are not sent to the translation model. **A local proxy is not an offline
  model:** it forwards text to its upstream service, whose availability and
  usage limits still apply.
- Without the explicit `copilot` setting, existing manual Kimi/Ollama translation
  remains available. Copilot errors never silently select another provider.

The Feishu `raw text` / `raw text_中文` briefing workflow is unchanged. Neither
full-text translation nor local note export repurposes or overwrites those
fields.

### Feishu metadata: copy existing columns, do not re-extract

Feishu already extracts bibliographic fields from its briefing workflow. The
reader **copies those columns directly**; it does not parse the briefing text,
generate a replacement brief, or call a model to derive metadata.

The current adapter targets the verified columns of the user's existing paper
table:

| Feishu column | Local metadata |
| --- | --- |
| 资料名称 | `title` |
| 作者AI | `authors` |
| 发表机构 | `institutions` |
| 发表期刊/会议 | `venue` |
| 时间 | `year` |
| Abstract | `abstract` |
| Research Question | `research_question` |
| Method / Result / Discussion | `method` / `result` / `discussion` |

Configure an authenticated `lark-cli` user identity and the non-secret settings
in `.env.example`: `PAPER_READER_FEISHU_BASE_TOKEN`,
`PAPER_READER_FEISHU_TABLE_ID`, and optionally a native executable path in
`PAPER_READER_LARK_CLI`. Resolve a Wiki URL using `lark-cli base +url-resolve`;
do not use the Wiki token as the Base token. Field IDs in `feishu_metadata.py`
belong to that specific table, not to arbitrary tables with similar labels.

- Enable `PAPER_READER_FEISHU_AUTO_SYNC=1` to refresh the current reader paper
  in the background about once per minute. Reading never waits for Feishu.
- An existing local paper is associated automatically only when its normalized
  full title has one exact match and the search is complete. Otherwise use
  **More → Feishu metadata → Search → Use this record** to select the association.
  This is a convenience for existing papers, not a universal paper identifier.
- After association, refresh uses the stable Feishu record ID. The metadata
  header, tabs, and Library index receive the mapped fields. Source Markdown,
  paragraph IDs, translations, and notes are not regenerated.
- Empty cloud values retain existing local values. Local corrections to mapped
  fields are retained as overrides. Network/auth/schema errors are visible;
  previously cached data remains readable offline.
- A deleted/inaccessible linked record is an error, not a successful refresh
  with empty columns. The reader keeps its cached metadata; reconnecting a
  replacement record must be explicit.
- `feishu_metadata.json` stores the field sources, the first pre-sync metadata
  values, and read-only copies of `raw text` / `raw text_中文`. Those copies are
  separate from the old local brief and its annotations.

This metadata mapping is **read-only**. Local PDF import remains available;
papers need not exist in Feishu first. The separate publication action above
uses only dedicated archive/backup columns. Two-computer conflict merging and
bidirectional mobile note editing remain later work.

### On-demand Feishu intake and the parsing queue

1. Open **Library → From Feishu**. Search a paper title or paste a record ID /
   record-specific Base link. A generic table/view link does not identify a
   paper. The configured Base/table must match the link.
2. Select a result to read the existing **raw text_中文 / raw text**. This is
   screening only: no PDF download, local import, MinerU, or AI generation.
   Missing titles/briefings do not prevent a subsequent explicit PDF import.
3. For an unparsed paper, select the PDF attachment and choose **Queue for reading**. PDFs in
   **原文 pdf** and **附件** are available; multiple attachments require a
   selection. The selected file is downloaded only now and copied into the
   local workspace. Feishu columns and record identity are retained.
4. If the PDF is already on this computer, expand **Use a local PDF instead
   of downloading** and enter its full path before queuing. You must know it
   belongs to that record: its PDF header and size are checked, but matching
   size is not a cloud/local byte-identity proof.
5. Keep queuing other papers while conversion runs. Once the source is ready,
   choose **Read full text**. Queuing does not unexpectedly switch the current
   paper. **Parse queue**, beside the paper tabs, shows jobs and explicit retry.

The preview actions are mutually exclusive:

| Local state | Available action |
| --- | --- |
| Not parsed (including a saved skim only) | **Queue for reading** |
| Queued / parsing | Disabled state indicator and **View parsing queue**; no repeat submission |
| Full source ready | **Read full text** only; no queue or PDF-import controls |
| Parsing failed | **Retry parsing** using the existing local PDF |

Full text means parsed source Markdown, not a completed Chinese translation.
The button updates automatically when parsing finishes, without replacing the
briefing DOM, scroll position or text selection. The open preview checks local
queue state, falling back to the compact local index for untracked jobs; it
does not repeatedly query Feishu or reload the full paper. Metadata refresh
remains a separate action under **More → Feishu metadata**.

The app now uses **one FIFO parsing worker**, separate from the configured
translation request slots. All app intake paths share it, including local
uploads, reference intake, and legacy skim requests. A completed paper becomes
readable without waiting for the rest of the queue; source Markdown remains
the prerequisite, not a newly generated local brief. Unrequested cloud papers
are never automatically parsed. Status polling runs only while a queue panel
is open or an open intake preview is waiting for parsing, and stops when that
preview is closed or finishes.

Existing linked imports are reused without another download, and already
parsed source is retained. PDF hashes allow verified existing local copies to
keep their paper IDs and annotations. Feishu imports do not use fuzzy title
similarity as identity. Ambiguous exact-title matches, links to a different
record, changed attachments, or externally replaced local PDFs stop rather
than silently overwrite reading data.

Each requested parse stores its options/order in local metadata. On restart,
unfinished requested work resumes serially, and finished/failed requests
remain visible; failures do not block later papers. A retry is explicit. The
single worker prevents resource contention but is not a promise of faster
MinerU model startup or conversion for any particular PDF.

This step downloads only on request and **never writes Feishu fields**. It
does not publish notes automatically; use the separate confirmed publication
flow after reading.

### Original data for agents

For a known paper ID, the local server exposes:

- `GET /api/papers/<paper_id>/notes-md` for a fresh Markdown export of original
  reading notes/highlights.
- `GET /api/papers/<paper_id>/reading-data` for a versioned raw-data snapshot.

When working directly on disk, use the CLI `query` first, then read the selected
paper's `segments.json`, `annotations.json`, `thinking.json`, and (where used)
`takeaway_doc.json`. Treat `notes.md` as a generated view. Do not overwrite
annotations or user-authored thoughts when generating translations or analysis.
Keep human questions/notes separate from quoted paper text and existing AI
responses. Exports do not infer which sentences are questions.

Tab lists and view positions live in browser preferences; paper content,
translations, and saved notes remain server-side local files. Tab preferences
are not a backup. Cross-computer session handoff and Mac migration are deferred.

Paper Reader Agent imports papers into a local file-backed workspace, serves an anchored web reader, stores highlights and notes as JSON/Markdown, and provides optional AI-assisted paper briefs, translation, skim summaries, source-grounded chat, citation/video helpers, and browser-side paper brief capture. It is intended for small-group trial use: users keep papers and notes on their own machine, and each user supplies their own API keys.

## What It Does

- Local Library for metadata, projects, tags, reading status, citations, PDF links, and video links.
- PDF or Markdown ingestion into stable reader files such as `raw.md`, `segments.json`, `outline.json`, and `reader.md`.
- Web reader with paragraph IDs, outline navigation, highlights, notes, figures, and tables.
- Sensemaking panel for editable Paper Brief / AI outputs and source-linked notes.
- All Notes and original-data exports; previously saved Takeaway data remains accessible.
- Optional Kimi / Moonshot cloud AI for paper briefs, Kimi file extraction, translation, skim summaries, and source-grounded chat.
- Optional local Ollama translation fallback when no Kimi key is configured.

Core reading, Library, notes, Takeaway, Mindmap, and Canvas features are local files. AI features are optional and require user-provided keys.

## Repository Layout

```text
paper-reader-agent/
  paper_reader_agent.py        # CLI, local HTTP server, API, persistence
  feishu_metadata.py           # Read-only existing Feishu column mapping
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

KaTeX 0.17.0 is bundled locally for equation rendering, including its CSS and
fonts. Its [MIT license](web/vendor/katex/LICENSE) is included with the assets.

### Windows and Mac status

Windows is the verified platform for this version. The reader uses a shared
Python backend and browser UI; separate long-lived Windows and Mac codebases
are not needed. Platform-specific launchers and configuration can use the
same application code.

Mac migration is not implemented or verified yet. Existing Windows-written
library paths need separator normalization, and the launcher, PDF tools,
AI services and Feishu CLI need setup on the destination machine. Pulling the
repository updates code only: separately transfer the complete reading workspace,
including hidden publication receipts, and configure local paths and credentials.
Browser tab/view preferences are not included in that workspace. Concurrent
two-computer editing and automatic conflict merging are not supported.

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
py .\paper_reader_agent.py --workspace .\paper_reading_workspace query --project collaborative --limit 20
py .\paper_reader_agent.py --workspace .\paper_reading_workspace query --project collaborative --search "sensemaking"
py .\paper_reader_agent.py --workspace .\paper_reading_workspace query --project collaborative --include-briefs --format markdown --output collaborative_briefings.md
py .\paper_reader_agent.py --workspace .\paper_reading_workspace register path\to\paper.pdf
py .\paper_reader_agent.py --workspace .\paper_reading_workspace rebuild <paper_id>
py .\paper_reader_agent.py --workspace .\paper_reading_workspace citations
py .\paper_reader_agent.py --workspace .\paper_reading_workspace serve --port 8765
```

## Fast Retrieval For Agents

Use `query` before opening paper folders. It reads `library.json` once, filters by project, tag, or search text, and returns structured JSON with direct paths to `reader.md`, `notes.md`, and `thinking.json`.

1. Start with compact metadata only. Do not pass `--include-briefs` during discovery.
2. Narrow with `--project`, `--tag`, `--search`, `--brief`, and `--limit`.
3. Read only the returned `reader_path`, `notes_path`, or `briefing.path` needed for the task.
4. Add `--include-briefs` only for a narrow result set or when exporting a complete project catalog.

Default JSON output is intended for agents:

```powershell
paper-reader-agent query --project collaborative --search "group decision" --limit 10 --output agent_query.json
```

This installation loads the default library from `PAPER_READER_WORKSPACE` in `.env`, so agents should omit `--workspace` unless they intentionally need another library. On Windows, file output is preferable to piping JSON through the shell: the command prints the resolved output path, and the agent can read that one compact file next.

To regenerate a readable project catalog inside the workspace:

```powershell
paper-reader-agent query --project collaborative --include-briefs --format markdown --output collaborative_briefings.md
```

The command checks actual `thinking.json` -> `explain.content` values. It does not use `paper_brief_status` to decide whether a Briefing exists. Relative `--output` paths are resolved inside the selected workspace.

## Chrome Extension

The `chrome_extension/` folder contains an optional local side-panel helper for collecting paper brief candidates from the browser. Load it unpacked from Chrome's extension page and point it to the local server, usually `http://127.0.0.1:8765`.

The side panel sends the selected PDF to the local backend, which uses the configured Kimi / Moonshot key for PDF text extraction and Paper Brief generation.

This is still a **PDF-first** helper, not an HTML/full-text webpage reader or a
Feishu connector. An ACM article or PDF-viewer URL may return HTML rather than
PDF bytes. The current fallback chain retries browser/backend/download/tab
capture paths; it does not guarantee access to publisher PDFs. No webpage-first
briefing or access-control bypass is implemented. The reader's Copilot
translation setting does not switch this older Kimi briefing workflow.

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
node --test .\tests\reader_state.test.cjs
py -B -m unittest discover -s .\tests -p "test_*.py" -v
Get-ChildItem .\chrome_extension -Filter *.js | ForEach-Object { node --check $_.FullName }
```

The browser regressions in `tests/reader_ui.test.cjs` require Playwright and an
installed Edge browser (override `READER_BROWSER_CHANNEL` for another supported
channel). They run a temporary loopback fixture server with synthetic papers,
block non-fixture browser requests, and do not open the real reading workspace.
Run them with `node --test .\tests\reader_ui.test.cjs` once Playwright is
resolvable through the normal Node module path or a tooling-only `NODE_PATH`.

For browser-to-real-backend verification, set `READER_TEST_PYTHON` to a verified
Python executable and run `node --test .\tests\reader_http.test.cjs`. This starts
the actual HTTP handler directly on a disposable workspace, never the normal
startup path that resumes processing jobs. It blocks external model/converter
calls and cleans up its temporary workspace. Without that environment variable
this additional integration test is explicitly skipped.

The same integration file includes an opt-in live Copilot test. With an already
running loopback proxy, set `READER_TEST_LIVE_COPILOT=1` and run
`node --test --test-name-pattern="optional live Copilot" .\tests\reader_http.test.cjs`.
Only two disposable, self-authored source paragraphs are sent; it never opens
the real library. This test may consume provider quota. Normal browser/backend
tests stub the translator and reject outgoing network traffic.

## Status

This is an early local research tool. It is suitable for source-based small-group testing, but it is not packaged as a polished installer yet.