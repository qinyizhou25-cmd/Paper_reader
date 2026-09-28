const assert = require("node:assert/strict");
const { spawn } = require("node:child_process");
const path = require("node:path");
const { test } = require("node:test");
const { chromium } = require("playwright");

const serverScript = String.raw`
import hashlib
import json
import os
import sys
import tempfile
import threading
from pathlib import Path
import paper_reader_agent as reader

reader.ENV_FILES_LOADED = True
automatic = os.environ.get("READER_TEST_AUTO_TRANSLATE") == "1"
live_proxy = os.environ.get("READER_TEST_LIVE_PROXY") == "1"
feishu_intake = os.environ.get("READER_TEST_FEISHU_INTAKE") == "1"
teacher_enabled = os.environ.get("READER_TEST_TEACHER") == "1"
os.environ["PAPER_READER_TRANSLATION_PROVIDER"] = "copilot" if automatic else "legacy"
os.environ["PAPER_READER_COPILOT_BASE_URL"] = "http://127.0.0.1:4141/v1"
os.environ["PAPER_READER_COPILOT_MODEL"] = "gpt-4.1"
os.environ["PAPER_READER_TRANSLATION_CONCURRENCY"] = os.environ.get("READER_TEST_CONCURRENCY", "1")
os.environ["PAPER_READER_FEISHU_AUTO_SYNC"] = "0"
os.environ["PAPER_READER_FEISHU_BASE_TOKEN"] = ""
os.environ["PAPER_READER_FEISHU_TABLE_ID"] = ""
translation_gate = threading.Semaphore(0)
translation_calls = []
parse_gate = threading.Semaphore(0)
parse_calls = []
download_calls = []
def translate_fixture(text, provider=None):
    translation_calls.append(text)
    if not translation_gate.acquire(timeout=15):
        raise RuntimeError("The browser test did not release the fixture translation")
    return "Translated synthetic content: " + text
if automatic and not live_proxy:
    reader.translate_text = translate_fixture
def forbidden(*args, **kwargs):
    raise AssertionError("Integration fixtures must not run AI, converters, or outgoing HTTP")
original_urlopen = reader.urllib.request.urlopen
def fixture_urlopen(request, *args, **kwargs):
    url = request.full_url if hasattr(request, "full_url") else str(request)
    if live_proxy and url.startswith("http://127.0.0.1:4141/v1/"):
        if getattr(request, "data", None) and b"PRIVATE_FIXTURE_NOTE" in request.data:
            raise AssertionError("Notes must not be sent to the translator")
        return original_urlopen(request, *args, **kwargs)
    return forbidden()
reader.urllib.request.urlopen = fixture_urlopen
reader.subprocess.run = forbidden
reader.resume_interrupted_processing_tasks = forbidden

with tempfile.TemporaryDirectory(prefix="paper-reader-http-test-") as temporary:
    workspace = Path(temporary)
    records = []
    for paper_id in ("A", "B"):
        paper_dir = workspace / "papers" / paper_id
        paper_dir.mkdir(parents=True)
        metadata = {"id": paper_id, "title": "Fixture " + paper_id, "processing_mode": "deep", "processing_status": "ready"}
        records.append({**metadata, "paper_dir": "papers/" + paper_id, "source_pdf": "papers/" + paper_id + "/original.pdf"})
        files = {
            "metadata.json": metadata,
            "segments.json": [
                {"id": "p-0001", "kind": "heading", "level": 1, "markdown": "# Fixture " + paper_id, "translation": "Saved heading translation." if automatic else "", "section_path": []},
                {"id": "p-0002", "kind": "paragraph", "markdown": "The original evidence must remain unchanged.", "translation": "" if automatic and paper_id == "A" else "The paired translation.", "section_path": ["Introduction"]}
            ],
            "annotations.json": {"version": 1, "paper_id": paper_id, "annotations": [], "fixture_extension": {"preserve": True}},
            "outline.json": {"outline": [{"id": "p-0001", "title": "Introduction", "level": 1}], "core_locations": []},
            "thinking.json": {"explain": {"content": "A previously saved explanation." if paper_id == "B" else ""}, "blocks": [], "annotations": [], "report_thoughts": []}
        }
        if automatic and paper_id == "A":
            files["segments.json"].append({"id": "p-0003", "kind": "paragraph", "markdown": "A second synthetic paragraph.", "translation": "", "fixture_extension": {"preserve": True}})
        if live_proxy and paper_id == "A":
            files["annotations.json"]["annotations"] = [{"id": "private-fixture", "paragraph_id": "p-0002", "target": "source", "quote": "The original evidence", "note": "PRIVATE_FIXTURE_NOTE", "color": "yellow", "tags": []}]
        if teacher_enabled and paper_id == "A":
            source = files["segments.json"][1]["markdown"]
            files["reading_teacher.json"] = {
                "version": 1, "id": "http-example", "paper_id": paper_id,
                "created_at": "2026-09-27", "created_by": "agent-curated-example",
                "sources": [{"id": "dictionary", "title": "Synthetic dictionary", "url": "https://example.org/definition", "accessed_at": "2026-09-27"}],
                "cards": [{"id": "definition", "kind": "definition", "title": "Evidence",
                    "anchor": {"segment_id": "p-0002", "quote": "original evidence", "source_sha256": hashlib.sha256(source.encode()).hexdigest()},
                    "definition": {"paper": "original evidence", "external": [{"source_id": "dictionary", "summary": "External meaning."}]}}]
            }
        for name, value in files.items():
            (paper_dir / name).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        (paper_dir / "original.pdf").write_bytes(b"%PDF-1.4\n")
    (workspace / "library.json").write_text(json.dumps({"version": 1, "papers": records}), encoding="utf-8")
    if feishu_intake:
        os.environ["PAPER_READER_FEISHU_BASE_TOKEN"] = "FixtureBase"
        os.environ["PAPER_READER_FEISHU_TABLE_ID"] = "tblFixture"
        pdfs = {record_id: ("%PDF-1.4\nSynthetic " + record_id + "\n%%EOF").encode() for record_id in ("recHttpOne", "recHttpTwo")}
        cloud = {record_id: {
            "record_id": record_id,
            "metadata": {**{key: "" for key in reader.feishu_metadata.FIELD_MAPPING}, "title": "Cloud title " + record_id, "authors": "Example Author"},
            "field_sources": {key: value[0] for key, value in reader.feishu_metadata.FIELD_MAPPING.items()},
            "briefings": {"raw text": "# Title: Existing screening only", "raw text_中文": ""},
            "attachments": [{"field_id": "fldPdf", "file_token": "file" + record_id, "name": "synthetic.pdf", "size": len(content)}],
        } for record_id, content in pdfs.items()}
        reader.feishu_metadata.search_records = lambda *args, **kwargs: {
            "records": [{"record_id": item["record_id"], "title": item["metadata"]["title"]} for item in cloud.values()], "has_more": False,
        }
        reader.feishu_metadata.read_intake_record = lambda base, table, record_id, **kwargs: json.loads(json.dumps(cloud[record_id]))
        def download_fixture(base, table, record_id, file_token, destination, **kwargs):
            download_calls.append(record_id)
            destination.write_bytes(pdfs[record_id])
            return destination
        reader.feishu_metadata.download_record_attachment = download_fixture
        def parse_fixture(pdf_path, output_dir, **kwargs):
            parse_calls.append(pdf_path.parent.name)
            if not parse_gate.acquire(timeout=30):
                raise RuntimeError("The browser did not release the synthetic parser")
            output_dir.mkdir(parents=True, exist_ok=True)
            generated = output_dir / "source.md"
            generated.write_text("# Original synthetic source\n\nIndependent source for " + pdf_path.parent.name + ".", encoding="utf-8")
            return generated
        reader.run_mineru = parse_fixture
    class Handler(reader.ReaderHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            if self.path == "/fixture/parse-next":
                parse_gate.release()
                self.send_json({"ok": True})
                return
            if self.path == "/fixture/translation-next":
                translation_gate.release()
                self.send_json({"ok": True})
                return
            super().do_POST()
        def do_GET(self):
            if self.path == "/fixture/intake-state":
                self.send_json({"parse_calls": parse_calls, "download_calls": download_calls})
                return
            if self.path == "/fixture/translation-calls":
                self.send_json({"calls": translation_calls})
                return
            super().do_GET()
    Handler.workspace = workspace
    server = reader.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    def stop_when_requested():
        sys.stdin.readline()
        for _ in range(10):
            translation_gate.release()
            parse_gate.release()
        server.shutdown()
    threading.Thread(target=stop_when_requested, daemon=True).start()
    print(json.dumps({"url": "http://127.0.0.1:" + str(server.server_address[1])}), flush=True)
    try:
        server.serve_forever(poll_interval=0.05)
    finally:
        server.server_close()
        if reader.TRANSLATION_JOBS:
            reader.TRANSLATION_JOBS.close()
        if reader.PROCESSING_JOBS:
            reader.PROCESSING_JOBS.shutdown()
        with reader.EXPORT_TIMERS_GUARD:
            timers = list(reader.EXPORT_TIMERS.values())
        for timer in timers:
            timer.join(5)
`;

async function readerFixture(t, automatic = false, liveProxy = false, concurrency = 1, feishuIntake = false, teacher = false) {
  const child = spawn(process.env.READER_TEST_PYTHON, ["-B", "-c", serverScript], {
    cwd: path.resolve(__dirname, ".."),
    stdio: ["pipe", "pipe", "pipe"],
    env: { ...process.env, PYTHONIOENCODING: "utf-8", READER_TEST_AUTO_TRANSLATE: automatic ? "1" : "0",
      READER_TEST_LIVE_PROXY: liveProxy ? "1" : "0", READER_TEST_CONCURRENCY: String(concurrency), READER_TEST_FEISHU_INTAKE: feishuIntake ? "1" : "0",
      READER_TEST_TEACHER: teacher ? "1" : "0" },
  });
  let stderr = "";
  child.stderr.on("data", data => { stderr += data; });
  const exit = new Promise(resolve => child.once("exit", (code, signal) => resolve({ code, signal })));
  t.after(async () => {
    if (child.exitCode === null) child.stdin.end("stop\n");
    const timer = setTimeout(() => child.kill(), 10000);
    const result = await exit;
    clearTimeout(timer);
    assert.equal(result.code, 0, stderr || "Fixture Python server must exit cleanly");
  });
  const url = await new Promise((resolve, reject) => {
    let output = "";
    const timer = setTimeout(() => reject(new Error(`Fixture startup timed out: ${stderr}`)), 10000);
    child.once("error", error => { clearTimeout(timer); reject(error); });
    child.stdout.on("data", data => {
      output += data;
      if (output.includes("\n")) {
        clearTimeout(timer);
        try { resolve(JSON.parse(output.split("\n")[0]).url); } catch (error) { reject(error); }
      }
    });
    child.once("exit", code => { clearTimeout(timer); reject(new Error(`Fixture exited ${code}: ${stderr}`)); });
  });
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(() => browser.close());
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(url) ? route.continue() : route.abort());
  return { url, page, errors, stderr: () => stderr };
}

test("actual HTTP teacher adoption persists distinct provenance in original reading exports", {
  skip: !process.env.READER_TEST_PYTHON, timeout: 30000,
}, async t => {
  const { url, page, errors } = await readerFixture(t, false, false, 1, false, true);
  await page.goto(url);
  await page.waitForFunction(() => state.currentPaperId === "A" && state.readingTeacher.ranges.size === 1);
  const before = await (await page.request.get(url + "/api/papers/A/reading-data")).json();
  assert.equal(await page.locator(".teacher-card").count(), 0);
  await page.locator('[data-teacher-open="definition"]').click();
  await page.locator('[data-teacher-adopt="definition"]').click();
  await page.waitForFunction(() => !state.readingTeacher.saving.size && !state.paperSessions.get("A").writes.get("annotations")?.dirty);
  const after = await (await page.request.get(url + "/api/papers/A/reading-data")).json();
  const saved = after.files["annotations.json"];
  assert.equal(saved.annotations.length, 1);
  assert.equal(saved.annotations[0].origin.kind, "reading-teacher");
  assert.equal(saved.annotations[0].origin.content_type, "definition");
  assert.equal(saved.annotations[0].origin.sources[0].url, "https://example.org/definition");
  assert.equal(saved.annotations[0].quote, "original evidence");
  assert.match(saved.annotations[0].note, /本文定义（原文）/);
  assert.doesNotMatch(saved.annotations[0].note, /undefined|AI 对照/);
  assert.equal(await page.locator('[data-teacher-card="definition"], [data-teacher-open="definition"]').count(), 0);
  assert.equal(await page.locator(".saved-definition-card").count(), 1);
  assert.equal(await page.locator(".saved-definition-card .teacher-question").count(), 0);
  assert.deepEqual(saved.fixture_extension, { preserve: true });
  assert.deepEqual(after.files["segments.json"], before.files["segments.json"]);
  assert.deepEqual(after.files["reading_teacher.json"], before.files["reading_teacher.json"]);
  const markdown = await (await page.request.get(url + "/api/papers/A/notes-md")).text();
  assert.match(markdown, /Accepted AI definition \(AI-origin; reader edits retained\)/);
  assert.match(markdown, /https:\/\/example.org\/definition/);
  await page.reload();
  await page.waitForFunction(() => state.currentPaperId === "A" && state.readingTeacher.ranges.size === 1);
  await page.locator("#readingTeacherLocation").selectOption("definition");
  assert.equal(await page.locator(".definition-save-state").innerText(), "✓ Saved");
  assert.equal(await page.locator('.comment-card[data-note-origin="reading-teacher"]').count(), 1);
  assert.equal(await page.locator('[data-teacher-card="definition"], [data-teacher-open="definition"]').count(), 0);
  const noteId = saved.annotations[0].id;
  await page.locator(`[data-close-definition-note="${noteId}"]`).click();
  assert.equal(await page.locator(".saved-definition-card").count(), 0);
  await page.locator(`[data-open-definition-note="${noteId}"]`).focus();
  await page.keyboard.press("Enter");
  assert.equal(await page.locator(".saved-definition-card").count(), 1);
  assert.equal(await page.evaluate(() => document.activeElement.id), `saved-definition-${noteId}`);
  await page.locator(`.saved-definition-card [data-edit-annotation="${noteId}"]`).click();
  const edited = "My own definition wording.\nKeep this uncertainty and my exact edits.";
  await page.locator("#noteText").fill(edited);
  await page.locator("#saveNote").click();
  await page.waitForFunction(() => !state.paperSessions.get("A").writes.get("annotations")?.dirty);
  assert.equal(await page.locator(".saved-definition-card .comment-text").textContent(), edited);
  assert.equal(await page.locator(".saved-definition-card .teacher-definition").count(), 0, "Do not show the original AI text instead of the reader's edits");
  await page.locator("#toggleReadingTeacher").click();
  assert.equal(await page.locator(".saved-definition-card .comment-text").textContent(), edited);
  await page.locator("#toggleReadingTeacher").click();
  const editedData = await (await page.request.get(url + "/api/papers/A/reading-data")).json();
  assert.equal(editedData.files["annotations.json"].annotations.length, 1);
  assert.equal(editedData.files["annotations.json"].annotations[0].note, edited);
  assert.equal(editedData.files["annotations.json"].annotations[0].origin.initial_note, saved.annotations[0].note);
  await page.locator(`.saved-definition-card [data-edit-annotation="${noteId}"]`).click();
  page.once("dialog", dialog => dialog.accept());
  await page.locator("#deleteDrawerNote").click();
  await page.waitForFunction(() => !state.annotations.length && !state.paperSessions.get("A").writes.get("annotations")?.dirty);
  assert.equal(await page.locator(".saved-definition-card").count(), 0);
  assert.equal(await page.locator('[data-teacher-adopt="definition"]').innerText(), "Save to Notes");
  assert.deepEqual(errors, []);
});

test("actual Feishu intake exposes the first parsed source while the second paper waits and notes remain writable", {
  skip: !process.env.READER_TEST_PYTHON,
  timeout: 60000,
}, async t => {
  const { url, page, errors, stderr } = await readerFixture(t, false, false, 1, true);
  await page.goto(url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.locator('.tab[data-view="library"]').click();
  await page.locator("#openFeishuIntake").click();
  await page.locator("#feishuIntakeQuery").fill("Cloud title");
  await page.locator("#searchFeishuIntake").click();
  await page.locator('[data-preview-feishu-record="recHttpOne"]').click();
  await page.waitForFunction(() => state.feishuIntake.record?.record_id === "recHttpOne" && !state.feishuIntake.loading);
  const before = await (await page.request.get(url + "/fixture/intake-state")).json();
  assert.deepEqual(before, { parse_calls: [], download_calls: [] });
  await page.locator("#queueFeishuPaper").click();
  await page.waitForFunction(() => !state.feishuIntake.busy && (state.feishuIntake.localPaper?.id === "feishu-recHttpOne" || state.feishuIntake.error));
  assert.equal(await page.evaluate(() => state.feishuIntake.error), "", stderr());
  await page.locator('[data-preview-feishu-record="recHttpTwo"]').click();
  await page.waitForFunction(() => state.feishuIntake.record?.record_id === "recHttpTwo" && !state.feishuIntake.loading);
  await page.locator("#queueFeishuPaper").click();
  await page.waitForFunction(() => !state.feishuIntake.busy && (state.feishuIntake.localPaper?.id === "feishu-recHttpTwo" || state.feishuIntake.error));
  assert.equal(await page.evaluate(() => state.feishuIntake.error), "", stderr());
  await page.keyboard.press("Escape");
  const waiting = await (await page.request.get(url + "/api/processing-queue")).json();
  assert.equal(waiting.active_jobs, 1);
  assert.equal(waiting.queued_count, 1);
  assert.deepEqual((await (await page.request.get(url + "/fixture/intake-state")).json()).parse_calls, ["feishu-recHttpOne"]);
  await page.locator('.tab[data-view="reader"]').click();
  await page.evaluate(() => openAnnotationDrawer("p-0002", "blue"));
  const originalNote = "  Keep this thought while the parser is busy.\nNo AI rewrite.  ";
  await page.locator("#noteText").fill(originalNote);
  await page.evaluate(() => savePendingAnnotation(true));
  await page.request.post(url + "/fixture/parse-next");
  await page.waitForFunction(async () => {
    const queue = await (await fetch("/api/processing-queue")).json();
    return queue.jobs.find(job => job.paper_id === "feishu-recHttpOne")?.status === "ready"
      && queue.jobs.find(job => job.paper_id === "feishu-recHttpTwo")?.status === "processing";
  });
  await page.locator("#toggleProcessingQueue").click();
  await page.locator('[data-parse-open="feishu-recHttpOne"]').click();
  await page.waitForFunction(() => state.currentPaperId === "feishu-recHttpOne" && !state.paperLoadingId);
  assert.equal(await page.evaluate(() => state.payload.metadata.title), "Cloud title recHttpOne");
  assert.match(await page.locator("#documentRoot").innerText(), /Independent source for feishu-recHttpOne/);
  const whileReading = await (await page.request.get(url + "/api/processing-queue")).json();
  assert.equal(whileReading.active_jobs, 1, "The second paper can still be parsing while the first is readable");
  await page.request.post(url + "/fixture/parse-next");
  await page.waitForFunction(async () => (await (await fetch("/api/processing-queue")).json()).jobs.every(job => job.status === "ready"));
  const saved = await (await page.request.get(url + "/api/papers/A/reading-data")).json();
  assert.equal(saved.files["annotations.json"].annotations[0].note, originalNote);
  const completed = await (await page.request.get(url + "/fixture/intake-state")).json();
  assert.deepEqual(completed.parse_calls, ["feishu-recHttpOne", "feishu-recHttpTwo"]);
  assert.deepEqual(completed.download_calls, ["recHttpOne", "recHttpTwo"]);
  assert.equal(await page.evaluate(() => state.currentPaperId), "feishu-recHttpOne");
  assert.deepEqual(errors, [], stderr());
});

test("browser and actual Python handler preserve and export the same original note", {
  skip: !process.env.READER_TEST_PYTHON,
  timeout: 60000,
}, async t => {
  const { url, page, errors, stderr } = await readerFixture(t);
  await page.goto(url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId, null, { timeout: 10000 }).catch(async error => {
    const status = await page.evaluate(() => ({
      paper: typeof state === "undefined" ? null : state.currentPaperId,
      toast: document.querySelector("#toast")?.textContent,
    }));
    throw new Error(`${error.message}\n${JSON.stringify({ status, errors, stderr: stderr() })}`);
  });
  assert.equal(await page.locator("#paper-brief").count(), 0);
  await page.evaluate(() => openPaperInWorkspace("B"));
  assert.equal(await page.locator("#paper-brief").getAttribute("open"), null);
  await page.locator("#paper-brief > summary").click();
  assert.match(await page.locator("#paperBriefPreview").innerText(), /A previously saved explanation/);
  await page.evaluate(() => refreshPaperBriefCard());
  assert.equal(await page.locator("#paper-brief").evaluate(node => node.open), true, "Refreshing highlights must not collapse a saved brief");
  await page.evaluate(async () => {
    await openPaperInWorkspace("A");
    openAnnotationDrawer("p-0002", "blue");
    renderNoteTagOptions(["question"]);
  });
  const original = "  Is this supported?\nI am not convinced.  ";
  await page.locator("#noteText").fill(original);
  await page.locator('[data-paper-tab="B"]').click();
  await page.waitForFunction(() => state.currentPaperId === "B" && !state.paperLoadingId);
  await page.locator('[data-paper-tab="A"]').click();
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  assert.equal(await page.evaluate(() => state.annotations[0].note), original);
  assert.deepEqual(await page.evaluate(() => state.annotations[0].tags), ["question"]);
  const notesResponse = await page.request.get(url + "/api/papers/A/notes-md");
  assert.equal(notesResponse.status(), 200);
  assert.equal(notesResponse.headers()["cache-control"], "no-store");
  const markdown = await notesResponse.text();
  assert.ok(markdown.includes(original), "Markdown must contain the original note verbatim");
  assert.ok(markdown.includes("The original evidence must remain unchanged."));
  const rawResponse = await page.request.get(url + "/api/papers/A/reading-data");
  assert.equal(rawResponse.status(), 200);
  const raw = await rawResponse.json();
  assert.ok(JSON.stringify(raw).includes(JSON.stringify(original).slice(1, -1)));
  assert.ok(JSON.stringify(raw).includes('"fixture_extension":{"preserve":true}'));
  await page.reload();
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  assert.equal(await page.evaluate(() => state.annotations[0].note), original);
  assert.equal(await page.locator("#paperTabs [role=tab]").count(), 2);
  assert.equal(await page.locator('a[href="/api/papers/A/pdf"]').count(), 1);
  assert.equal(await page.locator("#paper-brief").count(), 0);
  for (const width of [900, 1100, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    const overflow = await page.locator("#workspaceToolbar, .reader-data-actions, #readerTranslationStatus").evaluateAll(nodes => nodes
      .flatMap(node => [node, ...node.querySelectorAll("button")])
      .filter(node => {
        const bounds = node.getBoundingClientRect();
        return bounds.left < 0 || bounds.right > window.innerWidth;
      }).map(node => node.id || node.className));
    assert.deepEqual(overflow, [], `Reading controls must fit a ${width}px viewport`);
  }
  if (process.env.READER_TEST_SCREENSHOT) {
    await page.screenshot({ path: process.env.READER_TEST_SCREENSHOT, fullPage: false });
  }
  assert.deepEqual(errors, []);
  assert.equal(stderr(), "", "The actual backend must not log unexpected exceptions");
});

test("actual backend publishes saved translation paragraphs while original notes remain editable", {
  skip: !process.env.READER_TEST_PYTHON,
  timeout: 60000,
}, async t => {
  const { url, page, errors, stderr } = await readerFixture(t, true);
  await page.goto(url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId && translationJob("A").status === "processing");
  assert.equal(await page.locator("#p-0002 > .translation").count(), 0);
  assert.match(await page.locator("#p-0002 .source-text").innerText(), /original evidence/);
  await page.evaluate(() => openAnnotationDrawer("p-0002", "blue"));
  const original = "  Keep my original question.\nDo not send this note to the translator.  ";
  await page.locator("#noteText").fill(original);
  await page.locator("#saveNote").click();
  await page.evaluate(() => flushCurrentPaperEdits());
  await page.request.post(url + "/fixture/translation-next");
  await page.waitForFunction(() => document.querySelector("#p-0002 > .translation")?.textContent.includes("Translated synthetic content"), null, { timeout: 10000 }).catch(async error => {
    const progress = await (await page.request.get(url + "/api/papers/A/translation")).json();
    const calls = await (await page.request.get(url + "/fixture/translation-calls")).json();
    const local = await page.evaluate(() => ({ status: translationJob("A"), translation: state.payload.segments[1].translation }));
    throw new Error(`${error.message}\n${JSON.stringify({ progress, calls, local, errors, stderr: stderr() })}`);
  });
  assert.equal(await page.locator("#p-0003 > .translation").count(), 0);
  const intermediate = await (await page.request.get(url + "/api/papers/A")).json();
  assert.match(intermediate.segments[1].translation, /Translated synthetic content/);
  assert.equal(intermediate.segments[2].translation, "");
  assert.equal(intermediate.annotations.annotations[0].note, original);
  await page.request.post(url + "/fixture/translation-next");
  await page.waitForFunction(() => translationJob("A").status === "ready");
  const final = await (await page.request.get(url + "/api/papers/A")).json();
  assert.equal(final.segments[0].translation, "Saved heading translation.");
  assert.deepEqual(final.segments[2].fixture_extension, { preserve: true });
  assert.equal(final.annotations.annotations[0].note, original);
  const calls = await (await page.request.get(url + "/fixture/translation-calls")).json();
  assert.deepEqual(calls.calls, ["The original evidence must remain unchanged.", "A second synthetic paragraph."]);
  await page.reload();
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId && translationJob("A").status === "ready");
  assert.equal(await page.locator("#p-0003 > .translation").innerText(), "Translated synthetic content: A second synthetic paragraph.");
  assert.equal((await (await page.request.get(url + "/fixture/translation-calls")).json()).calls.length, 2);
  assert.deepEqual(errors, []);
  assert.equal(stderr(), "");
});

test("optional live Copilot proxy translates only disposable synthetic source", {
  skip: !process.env.READER_TEST_PYTHON || process.env.READER_TEST_LIVE_COPILOT !== "1",
  timeout: 120000,
}, async t => {
  const { url, page, errors, stderr } = await readerFixture(t, true, true, 2);
  const started = performance.now();
  await page.goto(url);
  await page.waitForFunction(() => ["ready", "failed"].includes(translationJob("A").status), null, { timeout: 90000 });
  const progress = await page.evaluate(() => translationJob("A"));
  assert.equal(progress.status, "ready", progress.error || "Live fixture translation should complete");
  const payload = await (await page.request.get(url + "/api/papers/A")).json();
  assert.equal(payload.segments[0].translation, "Saved heading translation.");
  assert.equal(payload.segments[1].markdown, "The original evidence must remain unchanged.");
  assert.match(payload.segments[1].translation, /[\u4e00-\u9fff]/);
  assert.match(await page.locator("#p-0003 > .translation").innerText(), /[\u4e00-\u9fff]/);
  assert.equal(payload.annotations.annotations[0].note, "PRIVATE_FIXTURE_NOTE");
  assert.deepEqual(payload.segments[2].fixture_extension, { preserve: true });
  assert.deepEqual(errors, []);
  assert.equal(stderr(), "");
  t.diagnostic(`Two synthetic paragraphs through the real proxy with two request slots: ${((performance.now() - started) / 1000).toFixed(1)}s; no user library data involved.`);
});

test("actual two-slot queue runs two distinct paragraphs before either finishes", {
  skip: !process.env.READER_TEST_PYTHON,
  timeout: 45000,
}, async t => {
  const { url, page, errors, stderr } = await readerFixture(t, true, false, 2);
  await page.goto(url);
  await page.waitForFunction(() => translationJob("A").status === "processing");
  await page.locator("#toggleTranslationQueue").click();
  await page.waitForFunction(() => state.translationQueue.data?.active_requests === 2);
  const calls = await (await page.request.get(url + "/fixture/translation-calls")).json();
  assert.deepEqual(new Set(calls.calls), new Set(["The original evidence must remain unchanged.", "A second synthetic paragraph."]));
  assert.match(await page.locator("#translationQueueSummary").innerText(), /2 active \/ 2 maximum/);
  await page.request.post(url + "/fixture/translation-next");
  await page.request.post(url + "/fixture/translation-next");
  await page.waitForFunction(() => translationJob("A").status === "ready");
  const payload = await (await page.request.get(url + "/api/papers/A")).json();
  assert.equal(payload.segments[0].translation, "Saved heading translation.");
  assert.match(payload.segments[1].translation, /Translated synthetic content/);
  assert.match(payload.segments[2].translation, /Translated synthetic content/);
  assert.deepEqual(payload.segments[2].fixture_extension, { preserve: true });
  assert.deepEqual(errors, []);
  assert.equal(stderr(), "");
});
