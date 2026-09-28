# Paper Reader: focused reading plan

Updated: 2026-09-27

## Product boundary

- Feishu remains the primary place for collecting, searching, classifying, and
  prioritizing papers.
- The local reader focuses on fast PDF/Markdown reading, paragraph-aligned
  translations, multiple open papers, and faithful highlights and notes.
- Preserve the user's words. Export and synchronization are mechanical data
  transfer, not AI interpretation or report generation.
- VS Code agents can read the original structured data and a readable Markdown
  export. Human notes, questions, source quotations, and AI outputs must remain
  distinguishable.
- Keep existing papers, translations, annotations, thinking records, mindmaps,
  and canvas data. Removing an interface entry does not delete stored data.
- Windows is the current implementation target. Mac migration is a later,
  explicit task, not a reason to rebuild or reparse the existing library now.

## Stage 1 - dependable, focused local reading (current)

### Scope

- Preserve direct PDF import and existing paragraph translations.
- Remove unnecessary work from initial load and paper switching. Load the
  library and all-paper notes only when needed; reuse recent paper payloads.
- Add persistent paper tabs available in reading mode. Preserve each paper's
  position and editing state; prevent stale requests or delayed saves from
  affecting another paper.
- Keep the local library as a lightweight search/import/recent-reading entry.
  Bound the number of rendered rows instead of rebuilding an unbounded table.
- Remove Mindmap/Canvas entry points from the core interface without deleting
  their files or repurposing their data.
- Preserve multiple image parts belonging to one figure and provide original
  PDF access when extraction is incomplete. Do not claim that grouping image
  parts reconstructs an accurate PDF crop.
- Keep PDF extraction and preview generation out of the normal paper-open
  request.
- Save annotations in their original structured format and export readable
  Markdown including highlight-only entries and verbatim notes/questions.
  Exports must not silently replace human notes with AI summaries.
- Document agent-facing file locations and preserve stable annotation/paragraph
  identifiers. No cloud sync or AI generation is added in this stage.

### Verification

- Opening the app must not wait for full-library notes before the active view.
- Switching A -> B -> A preserves notes, position, and paper identity; rapidly
  switching papers cannot display a stale response as the current paper.
- Save errors are visible and block discarding unsaved changes.
- Reopening a processed paper reuses its existing data, not PDF parsing or
  translation.
- Library rows are bounded and navigation/search remains usable.
- Multiple figure parts remain accessible; original PDF fallback is explicit.
- Markdown exports contain original quotes and notes, including highlights
  without a written note; raw JSON remains the authoritative editable record.
- Regression tests use disposable fixtures, not the real paper library.
- Existing unrelated worktree edits and all real reading data remain intact.

### Completion record

Implemented and verified on Windows with disposable test libraries.

- Persistent multi-paper tabs restore paper-specific editing state, reading
  mode, and paragraph position. Late image loads keep the restored paragraph
  anchored. Clean payloads are cached for up to 60 seconds, with a manual
  **Reload from disk** action for external edits.
- Paper opening no longer extracts PDFs or generates image previews. Full
  library notes and reference enrichment do not block the first paper view.
  The web Library reads the existing index and renders at most 40 rows.
- Saves are serialized per paper and resource. Tests cover rapid switching,
  exact question text, failed writes, retry, and edits surviving pagination.
- **Notes Markdown** and **Raw JSON** export original reading data after
  pending edits are saved. Unknown JSON fields and orphan annotations are
  retained. No report is generated or substituted for the user's words.
- Mindmap entry points and automatic report/placeholder-brief generation are
  removed from the main flow. Existing saved briefs and outputs are retained.
- Figure parts are grouped for viewing with explicit original-PDF access.
  Accurate PDF recropping remains unresolved; this is not a claim that every
  extraction error has been repaired.

Verification commands (from the repository root):

```powershell
py -B -m unittest discover -s .\tests -p test_reader_backend.py -v

$env:NODE_PATH = 'C:\path\to\validation\node_modules'
$env:READER_TEST_PYTHON = (py -3 -c "import sys; print(sys.executable)").Trim()
node --test .\tests\reader_state.test.cjs .\tests\reader_ui.test.cjs .\tests\reader_http.test.cjs

node --check .\web\app.js
git --no-pager diff --check
```

The suite covers 29 backend cases, 10 frontend-state cases, seven synthetic
browser scenarios, and a real Python-handler/browser integration. Browser
checks include 900px, 1100px, and 1440px controls, original-note save/export/
reload, no unsolicited AI requests, and saved-brief preservation. Python 3.12.3
and Edge were used; Playwright is installed only in isolated validation tooling.

A representative warm switch of a 240-segment synthetic paper took about
0.3 seconds with no repeated paper-body GET. This is not a benchmark or speed
guarantee for the real library. Large documents and cold disk reads still
need normal use testing.

Remaining boundaries:

- Feishu synchronization, generated reports, Mac migration, and multi-computer
  merging have not been implemented.
- External edits to an individual metadata file do not rebuild the lightweight
  Library index. Normal app metadata writes keep it updated; reloading one
  paper is not a library-wide reindex operation.
- Tabs/view positions are browser preferences, not a portable backup. Original
  saved notes and reading data remain in the existing local workspace.
- All tests used temporary data and blocked external AI/converter activity.
  The real reading library was not modified, reparsed, or migrated, and its
  normal background-processing startup was not invoked for validation.

## Stage 1B - source-first background translation (approved)

The user's updated workflow keeps the existing Feishu `raw text` and
`raw text_中文` overview/briefing process. These fields are not repurposed as
full source text or full-paper translation destinations.

- Normal local intake is PDF -> Markdown, without a local briefing prerequisite.
  Existing local briefs remain available; do not delete them or regenerate them
  automatically. Keep already parsed papers and stable paragraph IDs.
- Entering the reader shows original text first, then starts missing translations
  in the background through the configured local Copilot proxy.
- Start with GPT-4.1 and bounded requests. Translation must be idempotent, saved
  incrementally, and pausable/retryable without replacing existing translations.
  Include textual appendices rather than silently stopping at the appendix.
- Update only translated paragraph content in the browser, not the whole reading
  page. Preserve the reader's position, current text selection, note editor,
  original highlights, and each tab's paper identity.
- The proxy's unavailability or an exhausted quota must show an error while
  leaving original text and local notes usable. Never silently fall back to a
  different provider.
- Send source paragraphs only, never reading notes/questions/highlights. The
  loopback proxy forwards requests upstream; this is not offline inference.
- Do not start bulk translation of the entire Library. Opening a paper is the
  trigger; multiple open papers share bounded background capacity.

The user-running loopback proxy at `http://127.0.0.1:4141/v1` passed a synthetic
translation smoke test. The same short sample took about 2.7 seconds on GPT-4.1
and 20.2 seconds on GPT-5-mini. These single-request observations do not establish
full-paper speed, translation quality across papers, or future usage costs.
No real papers or notes were sent for those tests.

The automatic source-first workflow is implemented. Browser tests cover
incremental translation insertion, unchanged source DOM, note drafts/focus,
scroll anchoring, pause/resume/retry, tab identity, and queued PDF parsing.
The actual Python handler has also been verified with a controlled translator:
each paragraph reaches disk and the reader before the next completes, while
original notes and extension fields remain unchanged.

An additional opt-in end-to-end test exercised the actual new backend and the
user-running Copilot proxy with two self-authored synthetic paragraphs. Both
became visible Chinese translations; existing translation and original-note
fixtures stayed unchanged. Source-read-to-complete time for that small run was
about 14.5 seconds including requests and browser polling, illustrating why
individual request timings are not a whole-paper speed guarantee.

The local ignored `.env` opts in to Copilot/GPT-4.1; other installations retain
legacy manual translation unless explicitly configured.

Final verification passed: 60 Python regressions (29 existing plus 31 new),
11 frontend-state cases, nine browser scenarios, and two real-handler/browser
integrations. The separate live-proxy test also passed; it is intentionally
skipped in ordinary offline regression runs.

The local server was restarted at `http://127.0.0.1:8765/`. Its live configuration
reports automatic Copilot translation enabled with GPT-4.1, and the original
327-paper workspace is still selected. No entire-library translation was
started, and existing browser pages were not forcibly reloaded. Save any current
draft and refresh the reader to use the new client.

## Stage 1C - bounded parallel translation

- The user selected two simultaneous requests, shared globally across papers.
  A single paper can translate two different paragraphs in parallel.
- The queue lists only requested jobs and exposes pause/resume/retry. Each
  completed paragraph is merged by ID, including out-of-order results.
- HTTP 429/503 and temporary connection failures share a cooldown and honor
  `Retry-After`. Stop after three automatic retries per job instead of flooding
  the proxy or switching providers/accounts.
- Keep all existing text, translations, highlights, and unfinished note drafts.
  More concurrency is not a promise of a fixed speedup or additional quota.

### Reading-media follow-up

- Show each original image once. The translated paragraph contains Chinese
  prose/captions, not another unchanged bitmap. Image-only segments require
  no translation, including scanned tables; this does not claim image OCR.
- Keep actual Markdown/HTML table translation, preserving cells, numbers, and
  row/column structure. An image labeled as a table remains an original image,
  with a translated caption rather than a second screenshot.
- Remove image markup from new model inputs and outputs, including images
  embedded inside a paragraph. Treat image-only replies as an explicit failure.
- Suppress old image copies at rendering/export time instead of editing old
  paragraph text or stored annotation offsets. Apply the same behavior to
  progressive updates, note previews, and derived reading Markdown.

## Stage 1D - lightweight academic reading interface

Approved scope: improve the paper-like appearance without adding startup work,
font downloads, frontend dependencies, or new AI behavior.

- Use warm paper surfaces, dark text, neutral borders, and restrained blue-gray
  actions. Remove gradients, backdrop blur, and permanent card shadows from
  the core reading, notes, and Library surfaces.
- Use installed system serif fallbacks for paper text, with bounded line
  lengths. Keep original and translated paragraphs aligned and legible.
  An attached note must not narrow its paragraph; keyboard and touch access to
  note-edit controls must remain available.
- Move workspace controls to the reading toolbar. Put secondary actions in
  **More**, while keeping save failures visible without opening a menu.
- Keep **Saved Takeaway** in the side pane. Opening or closing it in Split
  preserves the document, outline, current mode, original writing, and source
  DOM. **Notes only** hides the paper only after an explicit mode selection.
- Preserve source files, translations, annotation offsets, notes, cached paper
  switching, and user reading preferences. No parser, data migration, generated
  summary, or cloud write belongs to this interface change.

Validation covers disposable libraries only: 390/900/1100/1440px layouts,
keyboard/menu/draft behavior, contrast, outline anchors below the toolbar,
save/retry/export, multi-paper switching, incremental translation, and the
existing Feishu metadata workflow. Measure cold opening and warm switching
against the same 240-segment fixture; verify no extra fonts, scripts, or warm
paper-body requests rather than relying only on a generous time threshold.

Completion record (Windows / Edge):

- 31 frontend-state, browser, and actual-handler checks passed. The optional
  live Copilot test was skipped; this visual change was validated without
  sending real papers to an external model.
- The same synthetic 240-segment fixture measured 378ms median cold opening
  (three samples) and 175ms median cached switching (nine samples), compared
  with the pre-change 522ms and 208ms measurements. No added font/script
  requests or repeated warm paper-body GETs were observed. This small local
  comparison is not a speed guarantee for every real paper.
- Read/Split screenshots, including narrow layouts, were inspected. Tests
  also cover an open note draft while using More/Feishu, Escape focus, and
  save failures remaining visible in Read mode.
- The existing local server returned HTTP 200 and served the new client
  assets. It was not restarted; existing translation jobs and the real
  reading workspace were not rewritten. Save open drafts before refreshing.

## Stage 2 - minimal Feishu data transfer (metadata slice implemented)

The user's clarified requirement is direct **column-to-metadata copying**.
Feishu already generates `raw text` / `raw text_中文` and extracts the named
columns. Do not repeat that extraction locally.

Implemented slice:

- Copy 资料名称 -> title, 作者AI -> authors, 发表机构 -> institutions,
  发表期刊/会议 -> venue, 时间 -> year, and the existing Abstract /
  Research Question / Method / Result / Discussion columns.
- Reuse the configured user-identity `lark-cli` in a small read-only adapter;
  no pre-existing application integration code was found to duplicate.
- Existing local papers can obtain an initial association through one unique,
  complete, exact-title match or explicit manual selection. Afterwards refresh
  by record ID, never repeated fuzzy matching.
- Refresh only the current reader paper in the background about once per
  minute; allow manual refresh. Neither opening nor offline reading waits for
  the cloud. A cloud failure does not erase cached local metadata.
- Preserve local corrections, original source segments, paragraph/annotation
  IDs, and all human reading data. Keep the cloud brief in a separate read-only
  cache instead of replacing an annotated local brief.
- Remove image Markdown artifacts from displayed headings and newly extracted
  title candidates, without rewriting the original source text.

Verification and deployment:

- Passed 89 Python cases, 11 frontend-state cases, 11 synthetic-browser
  scenarios, and three actual-handler/browser integrations.
- A separate opt-in test completed both self-authored paragraphs through the
  real Copilot proxy with two request slots. That small run took about
  17.3 seconds including browser polling; it is not evidence of a fixed
  speedup, since upstream latency varies.
- Live Feishu validation exposed its 50-character search-keyword limit. The
  adapter now queries a bounded prefix but still compares the complete
  normalized title before automatic association. Structured CLI errors on
  stderr remain explicit rather than being mistaken for invalid JSON.
- The live reader at `http://127.0.0.1:8765/` keeps the existing 327-paper
  workspace. Two global translation slots and background Feishu metadata
  refresh are enabled in ignored local configuration.
- The existing Vidmento paper was uniquely associated with its Feishu record
  and all ten mapped fields were copied to local metadata. Before/after hashes
  confirmed that source segments/translations, annotations, thinking records,
  and outline were unchanged by this metadata-only operation.
- The already-running Vidmento translation was paused for deployment and
  resumed from 190 saved paragraphs, not restarted from scratch. Live status
  subsequently showed two active requests and 214/341 saved paragraphs with
  no error. No other Library papers were bulk-started; browser pages were not
  forcibly refreshed.

Remaining:

- Pull paper metadata/PDFs on demand. Uploading a paper to Feishu does not
  automatically trigger local download, parsing, or translation.
- Keep direct local import; optionally associate it with an existing Feishu
  record or explicitly create a new one.
- Map a stable local paper ID to the Feishu record ID. Use PDF fingerprints and
  scholarly identifiers to detect duplicates and document versions, never a
  Windows absolute path or title as the sole durable identity. The current
  exact-title convenience is only an initial association for existing papers.
- Publish original reading notes/highlights as Markdown or a corresponding
  Feishu document, with raw structured data where needed for lossless transfer.
- Update only agreed reading-status/link fields. Do not overwrite the existing
  abstract, classification, human notes, or AI fields implicitly.
- Make retries idempotent and show pending/failed/synced state. Offline reading
  and local saving must not depend on Feishu availability.
- Exclude mobile note editing, AI report generation, and universal bidirectional
  field synchronization.

### Handoff and repeat publishing (2026-09-26)

On-demand intake and the serial parsing queue are implemented below.
Cloud note publishing, repeat-update conflict handling, and citation write-back
remain proposed rather than implemented.

Keep a single canonical Feishu record per paper. The inspected Base has one
paper table and multiple category views, not a separate paper identity for
each category.

1. **Open on demand.** Add a small "Open from Feishu" action accepting a record
   link or a narrowly scoped search. Do not clone the full cloud database into
   the reader or download/parse every uploaded paper. A later Feishu reading
   queue can be pulled by the running local app; a cloud workflow cannot call
   the user's localhost server directly.
2. **Bind before enrichment.** Persist the Base/table/record association during
   import. Reuse a selected local PDF when it matches the cloud attachment;
   otherwise download that attachment. Use PDF hashes to distinguish file
   versions. Do not match by filename alone, require a generated title before
   reading, or overwrite annotations when an attachment version changes.
3. **Read first.** Parse locally, show source Markdown, and use the existing
   bounded translation queue. Copy Feishu metadata when available, without
   generating another local brief or changing paper identity.
4. **Publish explicitly first.** Start with "Sync reading notes to Feishu":
   flush local edits, capture a versioned snapshot, then update a stable notes
   document linked from the same Feishu record. Keep verbatim human notes,
   highlights, questions, IDs, anchors, and provenance. Keep Markdown locally
   and provide a structured reading snapshot for agents; do not silently
   upload unrelated local files or repurpose AI brief/question input fields.
5. **Update, do not append copies.** Reuse the same record and notes document.
   Refresh only the reader-managed note content; new, edited, and removed
   annotations should all be reflected. Serialize publishing per paper, skip
   unchanged snapshots, and retain failed jobs for explicit retry. If local
   edits continue during upload, leave the newer revision marked unsynced.
6. **Keep ownership clear.** The local reader owns its published note mirror.
   Preserve existing Feishu manual annotations, takeaway fields, and AI outputs.
   Detect unexpected cloud edits to the managed content and stop rather than
   silently overwriting them. Reading-status mapping and any new destination
   columns need agreement before writes. Check existing workflow triggers so
   publishing notes does not inadvertently restart PDF analysis.
7. **Retain citation enrichment.** Keep the existing citation-count lookup.
   Prefer DOI/provider IDs, then validated bibliographic matching. Publish
   successful results to the existing Feishu citation field together with
   source and checked-at information; failed lookups must not clear a known
   count. Start with explicit refresh and cached results, not an online query
   on every paper open. A list of all citing papers is a separate feature.

Read-only Orca probe:

- The local PDF is 19 pages, 6,818,289 bytes, DOI
  `10.1145/3772318.3790335`. Its title is "Orca: Browsing at Scale Through
  User-Driven and AI-Facilitated Orchestration Across Malleable Webpages".
- Feishu attachment search found one record. A temporary attachment download
  had the same SHA-256 as the user's local PDF and was removed after checking.
- At inspection time, both raw-text briefing fields and all ten mapped
  metadata fields were empty. Title-only search found nothing, whereas the
  existing adapter could read the record directly. This is an uploaded paper,
  not evidence that its cloud analysis has completed or failed.
- The 327-entry local library index had no match by title/filename, PDF hash
  prefix, DOI, or Feishu record ID. No local import or parsing was started.
- The existing citation lookup returned 1 from OpenAlex for this DOI, with
  source `https://openalex.org/W4416603329`. This is a dated index result, not
  an authoritative real-time total.
- No Feishu records, fields, workflows, or real reading data were written.
  Note publishing and repeat-update behavior remain proposed, not tested
  end-to-end against the user's cloud library.

### Intake clarification and UX follow-up (2026-09-26)

- Implemented the direct **Chat with AI** / **Paste AI output** controls in
  Notes. The paste editor uses the full pane width with a 280px minimum height.
  Mode/tab switches retain drafts; saved AI text stays separate from original
  human notes. No new AI calls, font downloads, or frontend dependencies.
- Orca now has a different Feishu record, `recvwifJ0ZnWgS`; the earlier
  `recvwi9hBqjPzh` is reported missing. The new record contains its title,
  authors, venue/year and both briefings. Protect reads against the CLI's
  `record_not_found` marker even when it also returns a null-filled row.
  The replacement attachment's name/size match the earlier PDF, but it was
  not downloaded again for a second byte-level comparison. Orca was not
  imported, parsed, or translated during this follow-up.
- Direct mapped columns remain authoritative. Where the existing briefing
  title reader is used, recognize the Title label with or without Markdown
  heading markers, rather than requiring `#`. Regression cases also cover
  bold/lowercase labels and reject unlabelled prose.

Validation passed for the reader state/browser/actual-handler suites and all
23 Feishu/title-label tests. Checks include full-width paste at 390/900/1440px,
verbatim saved text, save failure/retry without duplicate blocks, drafts after
tab closure/cache expiry, and unchanged files after missing-record errors.
The optional live-proxy test was skipped; all new interaction checks use
disposable content and block external requests. The synthetic 240-segment
performance check reported 435ms median cold opening and 179ms warm switching,
with no added fonts/scripts or warm paper-body fetches; these are not timings
for Orca or the real library.

Deployment: restarted only the idle reader after confirming zero translations
in flight and zero parsing tasks eligible for startup recovery. The new server
returns HTTP 200 at `http://127.0.0.1:8765/` and still uses the existing 327-paper
workspace. The Copilot proxy was not stopped, and open browser pages were not
forcibly refreshed. Save any draft before refreshing to load the new controls.

### Approved follow-up: Feishu intake and one parser

The user selected Feishu on-demand opening / parsing ahead of browser-extension
work, and explicitly chose one active parser for responsiveness.

- **Library → From Feishu** searches titles or previews an explicit record
  reference. Existing raw-text briefings are read-only screening material.
  Preview does not download a PDF, import a paper, start translation, or run
  a converter. Missing generated titles/briefings do not block explicit intake.
- **Queue for reading** is the commit point. Select one PDF from the verified
  attachment fields; either download it then, or explicitly choose a known
  local PDF. Local-file size/header validation is not misrepresented as a
  byte comparison with a cloud file that was never downloaded.
- Persist Base/table/record identity, the selected attachment and local SHA-256.
  Reuse linked imports and verified matching local PDFs without replacing
  existing paper IDs, source text, or annotations. Reject changed attachment
  versions and ambiguous associations; do not use the legacy fuzzy-title
  duplicate matcher for distinct Feishu records.
- **Parse queue** exposes waiting position, active parsing, completion and
  explicit retry. All app parsing paths now share one FIFO worker instead of
  one Timer per paper. This is separate from the two translation request slots.
  A ready paper can be read while the next one is parsing.
- Requests/options are persisted in paper metadata with a high-resolution UTC
  ordering timestamp. Interrupted work resumes serially; failed requests do
  not auto-retry, and removed metadata is not silently recreated by a queued
  worker. Cold-start parsing performance still needs separate benchmarking.
- Intake reads the compact Library index, not the legacy whole-library
  metadata/preview enrichment path. Index read-modify-write operations are
  serialized so a parser finishing and a new import/reading update cannot
  overwrite one another's index entries.
- No full-cloud mirroring, cloud-field writes or raw-text regeneration. Note
  publishing remains the next integration milestone. The extension was neither
  removed nor modified.

Verification: all 150 backend tests and 39 frontend/state/actual-handler checks
passed; the optional real-proxy test was explicitly skipped. The actual Python
handler test queues two synthetic Feishu PDFs, allows an original note to be
saved while parsing is blocked, exposes the first source before the second
finishes, and verifies the original note in the raw-data export. Tests also
cover repeated/concurrent intake, changed PDFs, similar-but-distinct titles,
restart ordering, failed-job continuation, and metadata refresh without losing
the current source DOM or chat draft. No new fonts, scripts, or cold-start cloud
requests were introduced.

The new read-only preview path also verified the current Orca record, its title,
authors, two existing briefings and PDF attachment. It passed local-write guards;
Orca is still not imported and the real Library still has 327 entries. No real
PDF was downloaded, converted or sent to a model for this verification.

Deployment of this follow-up is also verified: the persistent localhost server
serves the new intake controls, its parsing queue reports one slot with no
unrequested jobs, and the real Orca preview succeeds through the HTTP handler.
The existing browser was not forcibly refreshed. A separate synthetic
240-segment performance run measured 532ms median cold opening and 192ms warm
switching; these are browser-fixture timings, not real-paper/MinerU guarantees.

### Intake button-state follow-up

- A local record is not itself proof that parsing has completed. The intake
  preview now distinguishes unparsed, queued, processing, failed, and ready
  full-source states. Saved skims are not labeled full text.
- Ready papers expose only **Read full text**, without another queue/import
  action. Queued/processing jobs cannot be submitted again. Failed jobs offer
  **Retry parsing** against the existing local PDF.
- Pending previews share the existing local parsing-status poller. Completion
  changes only status/action controls, preserving the briefing DOM, selection
  and scroll. Closing/switching the preview prevents stale responses and stops
  unnecessary polling. Feishu and full-paper content are not re-fetched for
  these updates; untracked jobs can be checked against the compact local index.
- Reading does not wait for translation. An empty cached pre-parse payload is
  invalidated before opening a paper now known to have full text. Metadata
  refresh remains separate from the reading/queueing action.
- Focused state/browser tests cover every action state, errors and retry,
  automatic completion, no duplicate intake, stopped polling, stale responses,
  and source-cache refresh. The actual Python-handler intake integration also
  remains covered, using synthetic PDFs rather than the user's papers.

Deferred browser screening work:

1. Keep the extension optional. Prefer a webpage-first screening connector: capture
   title/DOI/abstract or full text actually available to the user, mark whether
   a preview is abstract-only or full-text, then collect to Feishu on demand.
   Partial evidence must not masquerade as a full-paper analysis or overwrite
   a complete raw-text briefing.
2. Do not add more automatic retries to the old extension download chain.
   It currently expects PDF bytes, then calls Kimi for extraction and briefing;
   it does not read ACM article DOM content or inherit Copilot translation
   configuration. Download, extraction and generation errors need distinct
   handling. Any publisher login/challenge stays user-mediated; no paywall or
   access-control circumvention. Real ACM-page acceptance testing requires an
   accessible user-selected page; code inspection is not an end-to-end pass.

## Stage 3 - local teacher example; general automation deferred

- Provide small, queryable bundles of source text, translations, exact
  highlights, and original notes/questions to agents.
- Keep every agent output separate from human-authored records.
- Any future summary/report generation is explicit and reviewable. It can live
  in the existing Feishu intelligent table rather than the local reader.
- Do not add Zotero or Obsidian unless a concrete unmet workflow justifies it.

### In-situ reading teacher: primary-source research

The goal is deeper understanding and independent thinking, not faster completion
or more highlighted text. The teacher should work beside the original passage
in Read mode, rather than requiring another chat window.

The three user-selected videos were accessed as public video streams and read
through their embedded Chinese captions and lecture frames:

- [Li Mu: How to read papers](https://www.bilibili.com/video/BV1H44y1t75x/),
  published runtime 6:39. Around 1:23, 2:31 and 4:25, the three passes progress
  from screening to understanding the structure/figures and mentally
  reconstructing the work. Around 4:48, consider how the reader would solve the
  problem or design the experiment; around 5:29, close the paper and recall it.
- [Yin Zhinan: Reading literature](https://www.bilibili.com/video/BV1kR4y177tj/),
  published runtime 7:22. Distinguish reviews, research articles and methods
  papers. The main lesson uses reviews to locate a problem within a field and
  its subproblems (roughly 2:47-5:24), recommends more than one review to avoid
  a narrow account (5:51), and annotating unfamiliar technical terms (6:31).
  The closing card defers detailed research-article techniques to a later video;
  do not attribute that absent lesson to this recording.
- [Awake: Literature reading and notes](https://www.bilibili.com/video/BV17W4y167SM/),
  published runtime 21:16. Reading goals determine which sections deserve close
  attention (13:36-17:02). Notes are not merely highlighting, copying, or
  producing an exhaustive review (18:10-19:16). The final template asks what is
  good about the work and what the reader can reuse; its "125" example refers to
  one idea, two figures and five sentence patterns, not a mandatory product quota.

Evidence boundary: local OCR sampled the visual timelines every 0.5 seconds;
important claims were checked against source frames. There was no audio
transcription, account-cookie extraction, cloud upload or private-paper model
request. OCR can include misspellings, slide text and obscured captions; it is
not a certified, word-perfect transcript. These videos provide practitioner
strategies, not experimental proof that AI annotations improve learning.

Design implications to validate before implementation:

1. Make important passages relative to the reader's purpose and the paper type.
   Explain why a passage deserves attention; do not highlight every paragraph.
2. Attach questions to precise source evidence: reconstruct the argument,
   interpret a figure, propose an alternative design, test an assumption, or
   consider transfer to the reader's own work. Offer hints before an optional
   answer, and do not force a response or quiz.
3. Explain only consequential unfamiliar terms in context. Distinguish the
   author's definition, an AI explanation and any externally sourced definition.
   A dictionary translation alone is not a theory explanation.
4. Keep teacher marks separate from human highlights and thoughts. Adopting a
   definition into Notes must preserve its AI/source attribution and original
   passage; it must not be counted as the reader's independent reflection.
5. Test a small in-place teaching sample on a familiar paper before building the
   UI. Judge whether the reader can explain the argument/evidence and form an
   original response, not how many annotations or notes the model produces.
6. Preserve original-first rendering and responsiveness. Teaching is an optional,
   cached background activity, never a prerequisite for opening the paper.

At the video-research stage, generation, provider wiring, source-range validation,
annotation display and adoption were unimplemented. That research alone changed
no runtime or reading data. The subsequent local prototype below implements
display, validation and adoption, not general generation/provider orchestration.

### YouTube tutorial follow-up: research completed, implementation unchanged

The requested synthesis is in
[AI reading teacher research](AI_READING_TEACHER_RESEARCH.md).

- Read the complete retrieved English caption tracks for Stanford CS230
  [Lecture 8](https://www.youtube.com/watch?v=733m6qBH-jI) (64:47) and Bitesize
  Bio's [critical-analysis tutorial](https://www.youtube.com/watch?v=SwNydUyb0Ns)
  (38:41), including the latter's Q&A. The Stanford reading lesson is mainly
  before 29:30; its later career advice is not relabeled reading instruction.
- Verify Stanford's four reading questions against the actual board, including
  the fourth question that is not fully spoken in the subtitle track. Check
  Bitesize Bio's method, conclusion, checklist and note-table slides directly.
  Original English ASR captions for Bitesize Bio retain transcription uncertainty.
- Distinguish initial comprehension from evidence-level scrutiny. Skipping a
  derivation on a first pass does not justify skipping method/result checks when
  a paper becomes a foundation for one's own work.
- Prioritize source-linked questions connecting claims, definitions, methods,
  figures and conclusions. Ask for a learner-generated explanation before
  optionally revealing hints or an AI answer.
- Do not equate critical reading with fault-finding, invent author intentions,
  or apply experimental-biology controls indiscriminately to qualitative,
  theoretical or design-oriented HCI work. Missing evidence in the currently
  read passage is not proof that the entire paper omitted it.
- Prototype a small in-place teaching sample before implementing UI. Keep
  optionality, precise source anchoring, human/AI note provenance, original-first
  opening, and the current Feishu/library boundary. No runtime changes were made
  during that video-research step.

### Local teaching example and margin-note restoration (2026-09-27)

The user selected a bounded interactive example with definition adoption into
existing Notes, rather than an automatic teacher for every paper or a separate
glossary database.

- [x] Restore personal notes to a warm-colored right margin with accessible
  identity labels.
  Source and translation columns remain aligned across annotated/unannotated
  paragraphs. Long notes expand explicitly; narrow documents use colored,
  distinct inline cards. Split, note editing, drafts and figure controls remain.
- [x] Add a distinct, optional blue-gray teacher layer without converting its
  suggestions into human highlights. Native source underlines leave original
  text nodes/selections alone. No new font, framework or model request.
- [x] Defer optional teacher loading until after a source-only paint, then use
  browser idle time when available. Cancel stale scheduled loads and recover
  after returning to a paper or failing to open another tab.
- [x] Create eight real-source cards for *Towards Human-AI Deliberation*
  (CHI 2025, DOI `10.1145/3706598.3713423`). The compact revision has eight primary
  anchors and seven cross-passage evidence anchors.
  Verify the source hash and unique quote at both ends of cross-paragraph claims.
- [x] Distinguish the paper's deliberation account from the independently
  retrieved Cambridge dictionary entry and Gracia's original abstract
  (MEDLINE/Europe PMC, PMID `14620459`). Do not claim to have read Gracia's full
  paywalled article or treat all meanings of deliberation as interchangeable.
- [x] Locate the moved collaborative context document rather than assume its
  old cache is current. Its updated framing is *narrative handoff artifact*,
  with sender-owned narrative, continuation questions and sending preview.
  Use a dated local snapshot; do not overwrite the shared Project Context cache.
  Transfer prompts respect its explicit choice not to force every question
  back into AI and not to promise improved final decision quality.
- [x] Offer hints/explanations on demand and a blank normal-note entry for the
  reader's response. Adopt definitions only on click, with durable AI/source
  provenance and idempotent failure/retry behavior.
- [x] Keep optional teacher JSON separate in raw exports. Label accepted AI
  definitions in margin cards, All Notes and mechanical Markdown exports.
  Do not count adopted AI definitions as independent reflection or automatically
  promote reading progress to "Careful read"; retain the origin after editing.
  A broken optional teacher file must not break personal-note Markdown exports.

Initial prototype validation passed 22 Python checks and 30 Node/browser/HTTP checks,
including first-paint scheduling, delayed/stale responses, exact anchors,
missing/malformed files, human highlights, selections/drafts, save failure,
repeat adoption, tabs, 60 layout combinations and lossless exports. These
automated persistence tests use disposable data, not the real parser or a model.
A separate read-only browser check against the running reader verified the
379-segment example: eight cards and eight source underlines, no invalid
anchors, all sixteen original annotations, and no overflow at 390px.
Source/translation, annotation, thinking and Notes Markdown file hashes stayed
unchanged. The only new reading artifact is the separate local teacher file.

### Compact reading follow-up (2026-09-27)

- Remove repeated visible "My note / original" and "AI teacher / card kind"
  headers; keep color, hover/accessibility identity and all save/error signals.
- Remove generic tutorial paragraphs in the active reader/Library/Notes,
  queue and AI composers. Preserve actual unsaved drafts rather than a permanent
  instruction explaining the Save button.
- Replace the long teacher status paragraph and first-only jump with a compact
  source-ordered picker and previous/next controls for all eight locations.
- Treat definitions separately from thinking prompts. The Deliberation card
  now contains the paper's exact phrase, a short external gloss and a save action;
  it has no question, hint, interpretation disclosure or reflection button.
  The other seven cards keep their questions and optional project/evidence detail.
- Accept compact definition data while preserving legacy fields and previously
  adopted notes. Original source, translations and human annotations are not
  rewritten.
- List video-research cleanup candidates without deleting them; retain the
  current reader testing dependencies and compact evidence for the research.

This refinement passed 14 Python and 15 Node/browser/HTTP checks. A separate
read-only check on the real 379-segment paper reached every location in source
order, verified one question-free definition and seven thinking prompts, and
kept the sixteen original annotations and original reading-file hashes intact.
The ready UI has no teacher tutorial paragraph, and all three reading modes
remain overflow-free at 390px. No font, dependency or model call was added.

### Brief-aware reading guide, second example (2026-09-27)

The reader found the first questions cognitively demanding and too early in
their reading process. They have normally read the saved Brief before opening
the source. They explicitly chose to refine this paper's content and interaction
before implementing general manual/automatic generation.

- [x] Curate seven source-anchored cues: contribution, discussion unit, opinion
  update, case selection, accuracy, reliance and experience. Use four statements
  and three locally answerable questions, not a fixed 6:4 quota. Each cue is
  24-49 characters, with no hint/answer stack or required written response.
- [x] Add concise WoE and appropriate-reliance cards alongside deliberation.
  Distinguish verbatim paper excerpts, accounts of paper usage, retrieved
  definitions and explicitly labelled AI general explanations. Do not invent
  retrieval metadata for AI-only glosses.
- [x] Show source marks and small margin labels first; open only one selected
  card through the source, label or location picker. Preserve personal-note
  selection/editing, source nodes, keyboard access and narrow-screen fallback.
- [x] Preserve the seven older complex/project questions behind an explicit
  deeper-layer switch, rather than expose them during the first close reading.
  Existing adopted definitions retain their document/card identity.
- [x] Keep the source-first idle loading and per-paper cache. No generation
  hook, parser/translation change, font, dependency or new external request.
  Original annotations, source/translation, Brief and Notes files are untouched.

The local saved Brief was used for selection, not reread from Feishu or treated
as a ground-truth summary. In particular, the reading cues distinguish current
case opinion updates from training, decreased over-reliance from all reliance
being improved, and lower satisfaction from measured increases in mental demand.
Brief/source bidirectional linking, automatic/manual generation, live project
memory and a separate glossary remain deferred. The next decision depends on
actual reading feedback; passing UI/source/persistence checks is not evidence
that learning has improved.

Validation: 19 Python and 16 Node/browser/HTTP checks passed, including 60
layout combinations, source-click/keyboard access, one-card disclosure,
selection and personal-highlight priority, AI-gloss provenance, save retries
and source-first loading. A separate read-only check of the real paper reached
all ten reading locations with exact ranges and no invalid anchors, checked
nine viewport/mode combinations, and verified the seven saved deeper prompts
remain opt-in. All sixteen original annotations and the source/translation,
thinking and Notes file hashes remained unchanged. The local reader was
restarted with empty parsing/translation queues and its HTTP endpoint verified.

### Single-content display follow-up (2026-09-27)

- Keep standalone equations in the original only, and skip them in future
  translation work. Hide legacy equation duplicates in the reader and source
  preview without rewriting old translations. Preserve surrounding explanations
  and inline notation, including annotations after a hidden display equation.
- Replace the teacher-to-note duplication with one saved-definition view.
  Saving changes its status/actions in place; errors and retries remain visible.
  Close collapses, Edit opens the existing record, and deletion remains explicit.
  Persist the original accepted content in provenance for new definitions, while
  rendering already-saved definitions without a migration.
- Treat the accepted snapshot and the reader's subsequent edits as authoritative
  for the saved card, not the current teacher suggestion. Keep saved definitions
  available with Teacher disabled or unavailable. Ordinary personal notes and
  the distinction between AI definitions and independent reflection remain.
- Do not touch the user's screenshots or rewrite the real paper's annotations,
  translations, Brief or Notes files to achieve a presentation fix.

Validation passed 65 translation, 19 teacher and 8 processing Python checks;
28 state/cross-runtime checks, 18 browser checks (including nested fixtures)
and 4 actual HTTP checks. A Python/browser parity test also caught and fixed
literal `kind: code` being mistaken for an equation. The opening/switching
fixture stayed within its existing bounds with no new fonts or warm body GETs.
The final deployed-paper check found exactly one rendered equation and one
saved definition, retained all 17 current annotations and the current file
hashes, and passed six real viewport/mode combinations. Saved definitions are
already visible before the optional teacher file loads. The reader was safely
restarted with no active queue work or HTTP requests and returned HTTP 200.

### Conversation-first AI panel (2026-09-27)

- Render persisted turns oldest-to-newest without mutating their stored order,
  IDs, original questions, replies or annotation ranges.
- Separate the reader's message from the AI reply visually; remove the nested
  sticky-note borders and always-visible delete controls. Keep mode/context
  details and reply editing under Message options.
- Place a compact, directly accessible composer below independently scrolling
  history. Keep the position per paper and preserve it during annotation saves,
  composer switches and mode changes. Source navigation stays independent.
- Retain pasted-output editing and original AI-response highlights/notes.
  Pending questions and reply failures are explicit; a failed request keeps
  the unsent text. IME confirmation is not Enter-to-send.
- No new model provider, narrative request, cloud call, font or dependency.

Validation passed 29 state checks, 18 browser checks (including nested fixtures)
and one actual Python HTTP note/export check. Coverage includes chronological
rendering, fixed composer geometry, AI-response highlights and note edits,
pending/failed requests, retry without duplicate turns, IME input and arrival of
a reply while the reader is reviewing older messages or writing a personal note.
The 240-segment opening fixture stayed within its existing bounds: cold median
582 ms and warm median 169 ms, with no added fonts, scripts or warm body GETs.
Read-only validation of the Deliberation paper preserved its six conversation
turns, original reading files and definition/equation single-copy behavior;
six real viewport/mode combinations passed. No Feishu writes or real model
requests were made. The running reader serves the updated static UI.

### Categorized cloud handoff (2026-09-27)

The initial document-based design and validation below are retained as history.
The current App default is [table-first publication](#table-first-publication-2026-09-27).

The user approved implementation of the preview/confirm publishing workflow
after the conversation-first UI. A schema inspection found 50 existing fields;
the user explicitly chose two new dedicated columns rather than repurposing
`你的批注`, `take away`, `提问流` or an AI-triggering input. Created `阅读档案`
(text/URL) and `阅读数据备份` (attachment) in the
already configured Base/table. The enabled-workflow listing returned zero
items; existing field extensions and unrelated columns remain untouched.

Keep one existing Base paper record as the index and one stable reader-managed
document as its readable archive. Do not put a long generated narrative into a
briefing/analysis field or create another paper record for each update.

The document separates these content categories, with other saved mixed-origin
material in its own section:

1. **My reading notes.** Preserve original source/translation quotations,
   highlights, questions, tags and the reader's own words. Include personal
   comments on AI replies with an explicit AI-quote reference, not by assigning
   the AI's quoted prose to the reader.
2. **AI discussions.** Preserve completed questions and replies in chronological
   order, inline references, message IDs, recorded mode/model/context provenance
   and the reader's highlights. An absent context snapshot is not reconstructed
   or claimed to have been saved. Pasted output remains distinguishable.
3. **Accepted definitions and other saved AI material.** Keep accepted Teacher
   definitions, their paper/external sources and reader edits separate from
   independent human reflection. Link to the existing Brief instead of
   regenerating it. Preserve existing mixed-origin Takeaway records with their
   known origins; never guess authorship. Unaccepted teaching suggestions need
   not clutter the readable archive.

A separate versioned structured snapshot supports agents and lossless recovery
of the stored reading records. Reuse the current raw JSON data boundary
(including source/translation segments and the optional teacher document), and
record the PDF fingerprint, schema version and content hashes in a publishing
manifest. Raw JSON is not a complete PDF/image backup. Reuse an existing matching
cloud PDF and explicitly include missing source/image assets only when a complete
paper package is requested. Never silently add unrelated project memory, machine
configuration, credentials, logs or cache files.

The publishing interaction is **preview categories and destination
-> confirm -> update the same archive**. Flush local edits first, reject or
resolve unsubmitted drafts, capture an immutable version, skip unchanged content
and serialize retries per paper. Keep local edits made during upload marked
pending for the next update. An unexpected cloud edit to reader-managed content
must stop publication for a user decision, not be silently overwritten.

Each preview/write validates the actual schema and bound record again. Only
the two approved destination columns may be written; no reading-status or
sync-time column was added. Preserve existing manual/AI fields and do not
invoke the PDF briefing workflow. The local reader remains the editor and the
cloud document a mirror; bidirectional mobile editing is not implied.

The reader's entry is **More -> Publish to Feishu**. Publication endpoints are
local-only, require same-origin JSON and an explicit preview confirmation, and
do not accept client-supplied document destinations or arbitrary content. The
preview dialog does not call the model or cloud mutation endpoints. It stops
polling when closed and ignores stale responses for other papers; server-side
publication continues independently of the open dialog.

Generating a concise shareable narrative, if later requested, is a separate
opt-in AI action with explicit provenance and review. It must not be called by
export or publication, nor replace the full record.

### Publishing validation

- The Deliberation example was published through the real App confirmation
  flow using the authenticated local CLI, without a model request. The archive
  contains 21 personal annotations, five recorded question/answer pairs, one
  accepted definition, and separately labelled existing saved material.
- Independent download verification compared the 719,323-byte JSON attachment
  with the immutable local backup and checked its hashes. All 108 nonempty
  original text/quote entries were found in the cloud document. The seven
  original reading files remained byte-for-byte unchanged.
- All 48 comparable pre-existing Base fields matched their baseline. Two other
  baseline fields could no longer be compared: `rawtext2.附件` disappeared from
  the schema, and `文本 35` became an unsupported `metadata` field. `rawtext2`
  was already unsupported before publication. These schema changes were not
  reverted or treated as verified values. The recent record history shows the
  publication updates only to the two approved destination columns; this is
  not a table-wide schema audit.
- A fresh read-only preview correctly displayed **No changes to publish**.
  The cloud document stayed at revision 9 with the same single backup token.
  No real user note was edited to manufacture a second version.
- Recovery now requires a fresh verified preview after a stopped attempt,
  rather than replaying its consumed confirmation. Five publication/intake
  browser checks passed, including failed, interrupted, conflict and
  verification-required retries. Cloud-failure recovery itself remains covered
  by deterministic backend tests, not by deliberately damaging the live archive.
- The backend tests include real HTTP-to-publication integration with a fake
  CLI. A Windows newline regression preserves exact backup bytes without
  weakening integrity checks. Source opening remains independent of publication.

### Table-first publication (2026-09-27)

The user chose direct table cells for cross-paper browsing rather than requiring
an extra document. Keep one paper per row; do not add a separate notes table or
infer thematic tags/summaries in this iteration.

Four new plain-text columns are dedicated to reader-managed original records:

| Column | Stored content |
|---|---|
| 阅读笔记 | Personal words, quotations and source positions |
| AI 讨论 | Original questions and answers with recorded roles |
| 已采纳定义 | Accepted definitions and their saved provenance |
| 其他阅读材料 | Existing saved mixed-origin material |

Keep `阅读数据备份` as the existing attachment column. Preserve the old Docx
archive, URL column and receipts, and reuse a matching verified backup instead
of uploading another copy just because the presentation changed.

The preview shows the exact cell text, column name, and length. Quotes remain
distinguishable from the reader's notes, and no model is called. Plain-text
rendering shares the existing category/provenance logic without constructing
Docx XML. Each column is bounded at 100,000 UTF-16 units including labels and
quotes; excess content is rejected, never silently shortened.

The App explicitly selects table mode. Update the four cells in one record
patch through the local native CLI, with a guarded UTF-8 `@relative-file` payload
because CLI 1.0.58 does not support stdin for this Base command. The approved
four new field names were repaired after PowerShell's default input encoding
replaced Chinese literals; their types remained plain text and all 53 older
field schemas were verified unchanged. Maintenance scripts should load names
from UTF-8 files or set PowerShell `$OutputEncoding` before piping source code;
`PYTHONIOENCODING` alone does not fix incoming PowerShell bytes.

Use immutable previews, explicit confirmation, durable receipts, preflight and
readback checks. Nonempty unmanaged cells or observed cloud edits must conflict.
These are one-way reader-managed cells: Base upsert is not atomic compare-and-
swap, so simultaneous cloud editing is not supported. Existing human-edited
columns are not reused. Keep no-op detection, safe retry and background progress
without adding requests to normal paper opening.

Validation of the table-first flow:

- The App published the real Deliberation reading records into all four columns:
  21 personal entries, five question/answer pairs, one accepted definition and
  35 existing saved-material entries. Independent reads matched every complete
  cell string, including quotations and provenance.
- The first PATCH was acknowledged before its values were visible in the first
  query. Its durable receipt prevented a duplicate write. Bounded read-only
  verification retries now handle old or mixed expected values, stop on
  unexpected edits, and retain unresolved receipts. The existing live attempt
  was finalized through a fresh App preview/confirmation without another PATCH.
- Record history remained at revision 15159 after recovery and a no-change
  preview: exactly one update containing the four new fields. The previous
  719,323-byte JSON backup was downloaded, hash-checked and reused; there is
  still one backup attachment.
- All 51 readable pre-existing field values and seven original reading files
  matched their baseline. The old Docx remained at its baseline revision 10.
  The two unsupported extension fields, `metadata` and `rawtext2`, were not
  claimed to be value-verified or modified.
- Related regressions cover 37 formatter, 35 core HTTP/persistence, 64 legacy
  publisher and 45 table-publisher cases. Five publication/intake browser checks
  passed, including literal CRLF/tab preservation. The 240-segment opening check
  passed with no extra requests (cold median 472 ms, warm median 196 ms in this
  shared environment; not a performance guarantee).

## Cross-platform foundation (2026-09-28)

Implementation lives on the temporary `feature/cross-platform` branch. Keep
the verified Windows baseline on `main` until Mac acceptance; this is one shared
application, not a long-lived Windows/Mac fork.

- Read legacy workspace-relative Windows paths through a shared resolver and
  write portable relative paths for new index entries. Reading does not migrate
  or rewrite the original files, paragraph IDs, annotations, or cloud receipts.
- Keep source/translation, notes, queues, CLI queries, and Feishu intake on the
  same resolver. Explicitly reject foreign absolute drive paths and paths that
  escape the workspace instead of guessing a different paper.
- Require an initialized workspace before normal server startup or read-only
  CLI operations. `init` and `serve --create-workspace` are deliberate first-use
  actions. Bind the server port before resuming processing jobs.
- Add a foreground macOS launcher, native tool discovery, optional PDF-preview
  dependencies and machine-specific setup guidance. Do not copy Windows virtual
  environments, API keys or CLI login caches.
- Regression fixtures include relocated saved notes and publication receipts,
  plus separate Windows/macOS CI. Native MinerU conversion, Finder startup,
  Feishu authorization and the user's AI proxy still require Mac acceptance.

No real paper workspace is modified or uploaded by this compatibility work.
Selected-paper packaging/import is a separate task; GitHub carries app code,
while selected reading data will be transferred privately by USB or cloud drive.

## Later - selected-paper transfer and Mac acceptance

- Inventory and back up the complete reading workspace before migration.
- Transfer original PDFs, parsed text, translations, figures, annotations,
  thinking records, and reading positions without regenerating identifiers.
- Normalize persisted paths and configure launchers/converters per machine.
  Secrets and device-specific configuration are not part of a reading package.
- Start with a one-time main-machine migration. If needed later, implement
  versioned per-paper handoff packages with one editor at a time.
- Do not silently overwrite concurrent edits; keep conflicting versions.
- Two-computer real-time collaboration is outside the current plan.
