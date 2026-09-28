const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const http = require("node:http");
const path = require("node:path");
const { test } = require("node:test");
const { chromium } = require("playwright");

const webRoot = path.resolve(__dirname, "..", "web");

function fixturePaper(id) {
  const segments = Array.from({ length: 240 }, (_, index) => ({
    id: `p-${String(index + 1).padStart(4, "0")}`,
    kind: index === 0 ? "heading" : "paragraph",
    level: index === 0 ? 1 : null,
    section_path: ["Introduction"],
    markdown: index === 0 ? `# Paper ${id}` : `This is original paragraph ${index + 1} of paper ${id}. The evidence should remain linked to the exact words selected by the reader. [1]`,
    translation: index === 0 ? "" : `Translation of paragraph ${index + 1} of paper ${id}.`,
  }));
  segments[2].markdown = "![](part-one.svg)";
  segments[3].markdown = "![](part-two.svg)";
  segments[4].markdown = "Figure 1: Two parts of the same figure.";
  segments[239] = { id: "p-0240", markdown: "[1] Example reference.", section_path: ["References"] };
  return {
    metadata: {
      id, title: `Paper ${id}`, source_pdf: "original.pdf",
      processing_mode: "deep", processing_status: "ready", translation_status: "done",
      projects: ["collaborative"], read_status: "unread", year: "2026",
    },
    segments,
    outline: { outline: [{ id: "p-0001", title: "Introduction", level: 1 }], core_locations: [] },
    annotations: { version: 1, annotations: [] },
    thinking: { version: 1, explain: { content: "" }, blocks: [], annotations: [], report_thoughts: [] },
    takeaway_doc: { version: 1, blocks: [] },
    reading_progress: { version: 1, segments: {}, summary: {} },
    figure_fallbacks: {},
  };
}

function fixtureTeacher(paper) {
  const anchor = (index, quote) => ({
    segment_id: paper.segments[index].id, quote, source_markdown: paper.segments[index].markdown,
    source_sha256: require("node:crypto").createHash("sha256").update(paper.segments[index].markdown).digest("hex"),
  });
  return {
    version: 1, id: "teacher-fixture-v1", paper_id: paper.metadata.id, created_by: "agent-curated-example", created_at: "2026-09-27",
    available: true, issues: [],
    sources: [{ id: "dictionary", title: "Verified dictionary", url: "https://example.org/definition", accessed_at: "2026-09-27" }],
    project_context: { project: "collaborative", source_path: "local-project-context.html", snapshot_at: "2026-07-04",
      cards: [{ id: "ctx-goal", title: "Project goal", summary: "Evaluate the process, not just agreement. This is a hypothesis." }] },
    cards: [
      { id: "definition", kind: "definition", title: "Deliberation", anchor: anchor(1, "exact words"),
        why: "Keep the meaning attached to its evidence.", question: "Could people still disagree after a useful discussion?",
        hint: "Separate the process from consensus.", explanation: "This is AI interpretation, not the author's quote.",
        evidence: [{ ...anchor(6, "original paragraph 7"), label: "Related evidence" }],
        definition: { paper: "exact words", external: [{ source_id: "dictionary", summary: "Retrieved dictionary meaning." }],
          comparison: "The paper has a narrower scope than ordinary usage." } },
      { id: "transfer", kind: "transfer", title: "Apply the mechanism, not the interface", anchor: anchor(6, "original paragraph 7"),
        why: "Transfer requires checking assumptions.", question: "What observable change would support your project goal?",
        hint: "Check what the receiving person can do next.", explanation: "A project hypothesis, not a finding of this paper.",
        context_ids: ["ctx-goal"], evidence: [] },
    ],
  };
}

async function fixtureServer() {
  const papers = new Map(["A", "B", "C", ...Array.from({ length: 120 }, (_, i) => `N${i}`)].map(id => [id, fixturePaper(id)]));
  const calls = [];
  const control = { failAnnotations: false, failThinking: false, slowPaper: "", slowMs: 0, assetDelay: 0, autoTranslate: false,
    feishu: false, feishuDelay: 0, feishuNeedsMatch: false, feishuError: false, feishuAutoSync: true, feishuIntake: false,
    processingQueueDelay: 0, processingQueueError: false, teacherDelay: 0, teacherError: false,
    chatDelay: 0, failChat: false, publication: false, publicationPreviewDelay: 0,
    publicationConflict: false, publicationStatusError: false, publicationForceChange: false };
  const teachers = new Map();
  const intakeRequests = [];
  const chatRequests = [];
  const publications = new Map();
  const publicationPreviews = new Map();
  const publicationRequests = [];
  let publicationVersion = 0;
  const publicationFingerprint = paper => require("node:crypto").createHash("sha256")
    .update(JSON.stringify({ annotations: paper.annotations, thinking: paper.thinking })).digest("hex");
  const processingJobs = new Map();
  const cloudRecords = new Map(["recIntakeOne", "recIntakeTwo"].map((record_id, index) => [record_id, {
    record_id, metadata: { title: `Synthetic cloud paper ${index + 1}`, authors: "Example Author", year: "2026" },
    field_sources: { title: "资料名称" },
    briefings: { "raw text": "# Title: Synthetic briefing\n<script>globalThis.fixtureInjection=true</script>", "raw text_中文": "已有的筛选摘要；不需要再次生成。" },
    attachments: [{ field_id: "fldPdf", file_token: `file${index + 1}`, name: `example-${index + 1}.pdf`, size: 100 }],
  }]));
  const translationJobs = new Map();
  const translationJob = id => {
    if (!translationJobs.has(id)) translationJobs.set(id, {
      status: "not_started", completed: papers.get(id).segments.filter(item => item.translation).length,
      total: papers.get(id).segments.length, error: "", backend: "copilot:gpt-4.1",
      job_id: `fixture-${id}`, revision: 0, updates: [],
    });
    return translationJobs.get(id);
  };
  const server = http.createServer(async (request, response) => {
    try {
      const url = new URL(request.url, "http://localhost");
      calls.push({ method: request.method, pathname: url.pathname });
      const json = data => {
        response.writeHead(200, { "Content-Type": "application/json" });
        response.end(JSON.stringify(data));
      };
      if (url.pathname === "/api/library") {
        return json({
          workspace: "Disposable reader test fixture",
          translation_config: { auto_start: control.autoTranslate, provider: "copilot", model: "gpt-4.1" },
          feishu_config: { enabled: control.feishu, auto_sync: control.feishu && control.feishuAutoSync, publication_enabled: control.publication, fields: {
            title: "资料名称", authors: "作者AI", institutions: "发表机构", venue: "发表期刊/会议", year: "时间",
          } },
          library: { papers: [...papers.values()].map((paper, i) => ({
            ...paper.metadata,
            created_at: new Date(Date.UTC(2026, 8, 25) - i * 1000).toISOString(),
            updated_at: "2026-09-25T00:00:00Z",
          })) },
          tag_dictionary: { paper_tags: [], note_tags: [], aliases: {}, frames: [] },
          project_contexts: { contexts: {} },
        });
      }
      if (url.pathname === "/api/translation-queue") {
        const jobs = [...translationJobs].map(([paper_id, job]) => ({
          ...job, updates: undefined, paper_id, title: papers.get(paper_id).metadata.title,
          active_requests: job.status === "processing" ? 1 : 0,
        }));
        return json({ ok: true, concurrency: 2, active_requests: jobs.reduce((count, job) => count + job.active_requests, 0), jobs });
      }
      if (url.pathname === "/api/processing-queue") {
        let position = 0;
        const jobs = [...processingJobs.values()].map(job => ({ ...job, position: job.status === "queued" ? ++position : null }));
        if (control.processingQueueDelay) await new Promise(resolve => setTimeout(resolve, control.processingQueueDelay));
        if (control.processingQueueError) {
          response.writeHead(503, { "Content-Type": "application/json" });
          response.end(JSON.stringify({ error: "Synthetic queue status failure" }));
          return;
        }
        return json({ ok: true, concurrency: 1, active_jobs: jobs.filter(job => job.status === "processing").length, queued_count: position, jobs });
      }
      if (url.pathname === "/api/papers") return json({ papers: [...papers.values()].map(paper => paper.metadata) });
      if (url.pathname === "/api/feishu/search") return json({ ok: true, records: control.feishuIntake
        ? [...cloudRecords.values()].map(record => ({ record_id: record.record_id, title: record.metadata.title }))
        : [{ record_id: "recFixture", title: "Mapped title from Feishu" }], has_more: false });
      if (url.pathname === "/api/feishu/preview") {
        const record = cloudRecords.get(url.searchParams.get("reference"));
        if (!record) throw new Error("Unknown synthetic Feishu record");
        return json({ ok: true, record, local_paper: papers.get(`cloud-${record.record_id}`)?.metadata || null });
      }
      if (url.pathname === "/api/feishu/intake" || url.pathname === "/api/processing-queue/retry") {
        let raw = "";
        for await (const chunk of request) raw += chunk;
        const data = JSON.parse(raw);
        if (control.feishuError) {
          response.writeHead(503, { "Content-Type": "application/json" });
          response.end(JSON.stringify({ error: "Synthetic download failure" }));
          return;
        }
        if (url.pathname.endsWith("/retry")) {
          processingJobs.get(data.paper_id).status = "queued";
          processingJobs.get(data.paper_id).error = "";
          papers.get(data.paper_id).metadata.processing_status = "processing_queued";
          return json({ ok: true, metadata: papers.get(data.paper_id).metadata });
        }
        intakeRequests.push(data);
        const record = cloudRecords.get(data.record_id);
        const id = `cloud-${data.record_id}`;
        const reused = papers.has(id);
        if (!reused) {
          const paper = fixturePaper(id);
          Object.assign(paper.metadata, record.metadata, { id, processing_status: "processing_queued", feishu: { record_id: data.record_id } });
          papers.set(id, paper);
          processingJobs.set(id, { paper_id: id, title: record.metadata.title, mode: "deep", status: processingJobs.size ? "queued" : "processing", error: "" });
        }
        Object.assign(papers.get(id).metadata, record.metadata);
        return json({ ok: true, paper_id: id, paper: papers.get(id).metadata, metadata: papers.get(id).metadata, reused });
      }
      if (url.pathname === "/api/notes") return json({
        notes: [...papers].flatMap(([id, paper]) => paper.annotations.annotations.map(note => ({
          ...note, paper_id: id, paper_title: paper.metadata.title, paper_projects: ["collaborative"], source_scope: "paper",
        }))),
      });
      const match = url.pathname.match(/^\/api\/papers\/([^/]+)(?:\/(.+))?$/);
      if (match) {
        const paper = papers.get(match[1]);
        if (!paper) { response.writeHead(404); response.end("Missing fixture paper"); return; }
        const route = match[2];
        if (request.method === "POST") {
          let raw = "";
          for await (const chunk of request) raw += chunk;
          const data = JSON.parse(raw);
          if (route === "feishu-publication/preview") {
            const fingerprint = publicationFingerprint(paper);
            const preview = {
              mode: "table",
              preview_id: `preview-${++publicationVersion}`, fingerprint,
              changed: control.publicationForceChange || !["synced", "pending"].includes(publications.get(match[1])?.status)
                || publications.get(match[1])?.fingerprint !== fingerprint,
              snapshot_bytes: 4096, counts: { paper_annotations: paper.annotations.annotations.length },
              warnings: [],
              destination: { mode: "table", title: paper.metadata.title, record_id: `rec${match[1]}`,
                record_url: `https://feishu.cn/base/Fixture?record=rec${match[1]}`,
                backup_field: { id: "fldBackup", name: "阅读数据备份" },
                legacy_document_url: publications.get(match[1])?.legacy_document_url || "" },
              sections: [
                { id: "my-notes", title: "阅读笔记", entries: paper.annotations.annotations.map(note => ({
                  id: note.id, label: note.segment_id, quote: note.quote, text: note.note, source: "Original personal note",
                })) },
                { id: "ai-discussions", title: "AI 讨论", entries: paper.thinking.blocks.map(block => ({
                  id: block.id, label: "You / AI", quote: block.prompt, text: block.content, source: "AI discussion",
                })) },
                { id: "accepted-definitions", title: "已采纳定义", entries: [] },
                { id: "other-material", title: "其他阅读材料", entries: [] },
              ],
            };
            preview.columns = preview.sections.map(section => {
              const text = section.entries.map(entry => [entry.label, entry.text, entry.quote, entry.source].filter(Boolean).join("\n\n")).join("\n\n");
              return { id: section.id, name: section.title, text, characters: text.length, limit: 100000 };
            });
            preview.destination.text_fields = preview.columns.map((column, index) => ({
              section_id: column.id, id: `fldText${index}`, name: column.name, characters: column.characters, limit: column.limit,
            }));
            publicationPreviews.set(match[1], preview);
            if (control.publicationPreviewDelay) await new Promise(resolve => setTimeout(resolve, control.publicationPreviewDelay));
            return json({ ok: true, preview });
          }
          if (route === "feishu-publication/publish") {
            const preview = publicationPreviews.get(match[1]);
            const previous = publications.get(match[1]);
            if (data.confirm && previous?.preview_id === data.preview_id) return json({ ok: true, publication: previous });
            if (!data.confirm || data.preview_id !== preview?.preview_id || publicationFingerprint(paper) !== preview.fingerprint || control.publicationConflict) {
              response.writeHead(409, { "Content-Type": "application/json" });
              response.end(JSON.stringify({ ok: false, error: "Local or cloud version changed; refresh the preview." }));
              return;
            }
            publicationRequests.push({ paperId: match[1], ...data });
            const publication = { mode: "table", status: "publishing", phase: "writing_cells", error: "", fingerprint: preview.fingerprint,
              preview_id: preview.preview_id, job_id: `job-${publicationRequests.length}`,
              record_url: preview.destination.record_url, legacy_document_url: previous?.legacy_document_url || "" };
            publications.set(match[1], publication);
            return json({ ok: true, publication });
          }
          if (route === "feishu-sync") {
            if (control.feishuDelay) await new Promise(resolve => setTimeout(resolve, control.feishuDelay));
            if (control.feishuError) {
              response.writeHead(503, { "Content-Type": "application/json" });
              response.end(JSON.stringify({ error: "Synthetic Feishu permission error" }));
              return;
            }
            if (control.feishuNeedsMatch && !data.record_id && !paper.metadata.feishu) return json({ ok: true, status: "needs_match", candidates: [], has_more: false });
            Object.assign(paper.metadata, {
              title: "Mapped title from Feishu", authors: "Mapped author", institutions: "Mapped institution",
              venue: "CHI", year: "2026", title_source: "feishu",
              feishu: { record_id: "recFixture", url: "https://feishu.cn/base/example", synced_at: "2026-09-25T10:00:00Z" },
            });
            paper.feishu_metadata = { metadata: { title: "Mapped title from Feishu", authors: "Mapped author" },
              field_sources: { title: "资料名称", authors: "作者AI" },
              briefings: { "raw text": "# Exact existing briefing", "raw text_中文": "Exact existing Chinese briefing" } };
            return json({ ok: true, status: "synced", metadata: paper.metadata, feishu_metadata: paper.feishu_metadata, applied_fields: ["title", "authors"] });
          }
          if (route === "process") {
            paper.metadata.processing_mode = "deep";
            paper.metadata.processing_status = "processing_queued";
            return json({ ok: true, metadata: paper.metadata });
          }
          if (route === "translate") {
            const job = translationJob(match[1]);
            if (data.action === "pause") job.status = "paused";
            else if (!data.automatic || !["paused", "failed", "ready"].includes(job.status)) {
              job.status = "processing";
              job.error = "";
            }
            return json({ ok: true, translation: { ...job, updates: undefined } });
          }
          if (route === "chat") {
            chatRequests.push(data);
            if (control.chatDelay) await new Promise(resolve => setTimeout(resolve, control.chatDelay));
            if (control.failChat) {
              response.writeHead(503, { "Content-Type": "application/json" });
              response.end(JSON.stringify({ error: "Synthetic chat service unavailable" }));
              return;
            }
            const block = {
              id: `chat-reply-${chatRequests.length}`, type: "ai_output", mode: data.mode,
              prompt: data.message, content: `A synthetic reply to: ${data.message}\n\nRead the evidence [p-0002].`,
              model: "local-test-fixture", selection_refs: data.selection_refs,
              created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
            };
            paper.thinking.blocks.unshift(block);
            return json({ ok: true, thinking: paper.thinking, block });
          }
          if ((route === "annotations" && control.failAnnotations) || (route === "thinking" && control.failThinking)) {
            response.writeHead(503, { "Content-Type": "application/json" });
            response.end(JSON.stringify({ error: "Simulated disk failure" }));
            return;
          }
          const keys = { annotations: "annotations", thinking: "thinking", "takeaway-doc": "takeaway_doc", "reading-progress": "reading_progress", metadata: "metadata" };
          const key = keys[route];
          if (!key) throw new Error(`Unexpected fixture write: ${route}`);
          paper[key] = { ...paper[key], ...data };
          return json({ ok: true, [key]: paper[key], metadata: paper.metadata });
        }
        if (!route) {
          if (match[1] === control.slowPaper) await new Promise(resolve => setTimeout(resolve, control.slowMs));
          return json(paper);
        }
        if (route === "references") return json({ references: { 1: { number: "1", raw: "Example reference", abstract: "Fixture reference" } } });
        if (route === "feishu-publication") {
          if (control.publicationStatusError) {
            response.writeHead(503, { "Content-Type": "application/json" });
            response.end(JSON.stringify({ ok: false, error: "Synthetic publication status failure" }));
            return;
          }
          return json({ ok: true, publication: publications.get(match[1]) || { mode: "table", status: "idle", error: "", fingerprint: "" } });
        }
        if (route === "reading-teacher") {
          if (control.teacherDelay) await new Promise(resolve => setTimeout(resolve, control.teacherDelay));
          if (control.teacherError) {
            response.writeHead(409, { "Content-Type": "application/json" });
            response.end(JSON.stringify({ error: "Synthetic invalid teacher file" }));
            return;
          }
          return json({ paper_id: match[1], teacher: teachers.get(match[1]) || { available: false, cards: [], issues: [] } });
        }
        if (route === "translation") {
          const job = translationJob(match[1]);
          const updates = url.searchParams.get("job_id") !== job.job_id
            ? paper.segments.filter(item => item.translation).map(({ id, markdown, translation }) => ({ id, markdown, translation }))
            : job.updates.filter(item => item.revision > Number(url.searchParams.get("after") || 0));
          return json({ ok: true, paper_id: match[1], translation: { ...job, updates: undefined }, updates });
        }
        if (route.startsWith("assets/")) {
          if (control.assetDelay) await new Promise(resolve => setTimeout(resolve, control.assetDelay));
          response.writeHead(200, { "Content-Type": "image/svg+xml" });
          response.end('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="200"><rect width="640" height="200" fill="#cfe5ff"/><text x="30" y="70">Figure part</text></svg>');
          return;
        }
        if (route === "notes-md") {
          response.writeHead(200, { "Content-Type": "text/markdown", "Content-Disposition": 'attachment; filename="notes.md"' });
          response.end(paper.annotations.annotations.map(note => `${note.quote}\n${note.note}`).join("\n\n"));
          return;
        }
        if (route === "reading-data") return json(paper);
        if (route === "pdf") {
          response.writeHead(200, { "Content-Type": "application/pdf" });
          response.end("%PDF-1.4\n");
          return;
        }
        response.writeHead(404); response.end(`Missing fixture route ${route}`); return;
      }
      const file = path.resolve(webRoot, "." + (url.pathname === "/" ? "/index.html" : decodeURIComponent(url.pathname)));
      if (!file.startsWith(webRoot + path.sep)) throw new Error("Fixture path escaped web root");
      const body = await fs.readFile(file);
      const types = { ".html": "text/html", ".js": "application/javascript", ".css": "text/css", ".woff2": "font/woff2" };
      response.writeHead(200, { "Content-Type": types[path.extname(file)] || "application/octet-stream" });
      response.end(body);
    } catch (error) {
      response.writeHead(error.code === "ENOENT" ? 404 : 500, { "Content-Type": "text/plain" });
      response.end(String(error));
    }
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const publishTranslation = (paperId, segmentId, translation) => {
    const segment = papers.get(paperId).segments.find(item => item.id === segmentId);
    segment.translation = translation;
    const job = translationJob(paperId);
    job.revision += 1;
    job.completed = papers.get(paperId).segments.filter(item => item.translation).length;
    job.updates.push({ id: segmentId, markdown: segment.markdown, translation, revision: job.revision });
    if (job.completed === job.total) job.status = "ready";
  };
  return { server, papers, calls, control, translationJob, publishTranslation, cloudRecords, intakeRequests, processingJobs, teachers, chatRequests,
    publications, publicationPreviews, publicationRequests,
    url: `http://127.0.0.1:${server.address().port}` };
}

test("focused reader browser regressions on disposable data", { timeout: 120000 }, async t => {
  const fixture = await fixtureServer();
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, acceptDownloads: true });
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => {
    if (route.request().url().startsWith(fixture.url)) route.continue();
    else route.abort();
  });
  const open = async id => {
    const result = await page.evaluate(id => openPaperInWorkspace(id), id);
    await page.waitForFunction(id => state.currentPaperId === id && !state.paperLoadingId, id);
    return result;
  };
  const selectPassage = async () => {
    await page.locator("#p-0002 .source-text").scrollIntoViewIfNeeded();
    await page.locator("#p-0002 .source-text").evaluate(node => {
      const range = document.createRange();
      range.selectNodeContents(node);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      document.dispatchEvent(new Event("selectionchange"));
    });
  };

  await t.test("startup is lazy and reading no longer creates a report", async () => {
    await page.goto(fixture.url);
    await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
    assert.equal(await page.locator("#documentRoot .paragraph").count(), 240);
    assert.equal(await page.locator("#paper-brief").count(), 0, "Do not fabricate an explanation for papers without a saved brief");
    assert.equal(fixture.calls.filter(call => call.pathname === "/api/notes").length, 0);
    assert.equal(fixture.calls.filter(call => call.pathname.endsWith("/takeaway-doc")).length, 0);
    assert.equal(await page.locator('.tab[data-view="mindmap"]').count(), 0);
    assert.equal(await page.locator('[data-reader-side-pane="takeaway"]').isVisible(), false);
    const toolbarFits = await page.locator("#workspaceToolbar").evaluate(node => {
      const rect = node.getBoundingClientRect();
      return rect.left >= 0 && rect.right <= window.innerWidth;
    });
    assert.equal(toolbarFits, true, "Export actions must not push the fixed reading toolbar off screen");
  });

  await t.test("questions retain exact text, survive a tab switch, and use no AI endpoint", async () => {
    await open("B");
    await open("A");
    await selectPassage();
    await page.locator("#toolbarQuestion").click();
    await page.locator("#noteText").fill("  Why does this work?\nKeep my exact wording.  ");
    await page.locator('[data-paper-tab="B"]').click();
    await page.waitForFunction(() => state.currentPaperId === "B" && !state.paperLoadingId);
    const note = fixture.papers.get("A").annotations.annotations[0];
    assert.equal(note.note, "  Why does this work?\nKeep my exact wording.  ");
    assert.ok(note.tags.includes("question"));
    assert.equal(fixture.papers.get("B").annotations.annotations.length, 0);
    assert.ok(!fixture.calls.some(call => /\/(chat|reading-narrative|thinking\/explain)$/.test(call.pathname)));
    await page.locator('[data-paper-tab="A"]').click();
    await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
    assert.equal(await page.locator("#p-0002 .comment-card").count(), 1);
  });

  await t.test("warm switches avoid paper GETs and restore scroll positions", async () => {
    await page.evaluate(() => window.scrollTo({ top: 1100, behavior: "instant" }));
    const before = fixture.calls.filter(call => call.method === "GET" && call.pathname === "/api/papers/A").length;
    await open("B");
    const saved = await page.evaluate(() => state.workspaceAnchorsByPaper.A);
    fixture.control.assetDelay = 350;
    const started = performance.now();
    await open("A");
    const elapsed = performance.now() - started;
    const after = fixture.calls.filter(call => call.method === "GET" && call.pathname === "/api/papers/A").length;
    assert.equal(after, before);
    await page.waitForFunction(saved => {
      const images = [...document.querySelectorAll("#documentRoot img")];
      return images.every(image => image.complete)
        && Math.abs(document.getElementById(saved.segmentId).getBoundingClientRect().top - saved.offset) < 10;
    }, saved, { timeout: 5000 });
    fixture.control.assetDelay = 0;
    assert.ok(elapsed < 1500, `Warm switch took ${elapsed.toFixed(0)}ms for a 240-segment fixture`);
    t.diagnostic(`Warm switch (240 segments, test fixture): ${elapsed.toFixed(0)}ms; 0 paper GETs.`);
  });

  await t.test("figure viewer groups fragments and exposes the original PDF", async () => {
    await page.evaluate(() => openFigureModal("1"));
    assert.equal(await page.locator("#figureModalBody img").count(), 2);
    assert.equal(await page.locator('#figureModalBody a[href="/api/papers/A/pdf"]').count(), 1);
    await page.locator("#closeFigureModal").click();
  });

  await t.test("library pagination bounds rows, keeps typing focus, and saves edits across pages", async () => {
    await page.locator('.tab[data-view="library"]').click();
    assert.equal(await page.locator("[data-paper-row]").count(), 40);
    const row = page.locator('[data-paper-row="A"]');
    await row.locator('[data-field="authors"]').fill("Exact author edit");
    await page.locator("#libraryNextPage").click();
    assert.equal(await page.locator("[data-paper-row]").count(), 40);
    await page.waitForFunction(() => !state.metadataDrafts.has("A"));
    assert.equal(fixture.papers.get("A").metadata.authors, "Exact author edit");
    await page.locator("#libraryFilter").fill("Paper B");
    await page.waitForFunction(() => document.querySelectorAll("[data-paper-row]").length === 1);
    assert.equal(await page.locator("[data-paper-row]").getAttribute("data-paper-row"), "B");
    assert.equal(await page.locator("#libraryFilter").evaluate(node => node === document.activeElement), true);
  });

  await t.test("failed note writes block switching and explicit retry recovers", async () => {
    await open("A");
    await page.locator('.workspace-mode[data-workspace-mode="read"]').click();
    fixture.control.failAnnotations = true;
    await selectPassage();
    await page.locator("#toolbarNote").click();
    await page.locator("#noteText").fill("Keep this note when the disk fails.");
    await page.locator("#saveNote").click();
    await page.waitForFunction(() => paperSession("A").writes.get("annotations")?.error);
    assert.equal(await page.locator("#readerSaveStatus").getAttribute("data-state"), "error");
    assert.match(await page.locator("#readerSaveStatus").innerText(), /retry before closing/);
    const errorBounds = await page.locator("#readerSaveStatus").boundingBox();
    assert.ok(errorBounds.y >= 108 && errorBounds.y + errorBounds.height < 200, "Save failures stay visible in the reading toolbar");
    await page.locator('[data-paper-tab="B"]').click();
    await page.waitForFunction(() => !state.paperLoadingId);
    assert.equal(await page.evaluate(() => state.currentPaperId), "A");
    assert.ok(await page.evaluate(() => state.annotations.some(note => note.note === "Keep this note when the disk fails.")));
    fixture.control.failAnnotations = false;
    await open("B");
    assert.ok(fixture.papers.get("A").annotations.annotations.some(note => note.note === "Keep this note when the disk fails."));
    assert.equal(await page.locator("#readerSaveStatus").getAttribute("data-state"), "saved");
  });

  await t.test("reload restores open tabs and saved notes; Markdown and JSON exports are downloads", async () => {
    await open("A");
    await page.reload();
    await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
    assert.equal(await page.locator("#paperTabs [role=tab]").count(), 2);
    assert.equal(await page.evaluate(() => state.annotations.length), 2);
    for (const selector of ["#exportNotesMarkdown", "#exportReadingJson"]) {
      await page.locator("#readerMoreActions > summary").click();
      const downloadPromise = page.waitForEvent("download");
      await page.locator(selector).click();
      const download = await downloadPromise;
      assert.match(download.suggestedFilename(), /^A-reading\.(md|json)$/);
      await download.delete();
    }
    await page.locator('.tab[data-view="notes"]').click();
    await page.waitForFunction(() => state.allNotesLoaded);
    assert.equal(fixture.calls.filter(call => call.pathname === "/api/notes").length, 1);
  });

  assert.deepEqual(errors, [], "No uncaught browser errors are allowed.");
});

test("automatic translation updates preserve source DOM, drafts, scroll and tab identity", { timeout: 60000 }, async t => {
  const fixture = await fixtureServer();
  fixture.control.autoTranslate = true;
  for (const segment of fixture.papers.get("A").segments) {
    segment.translation = ["p-0002", "p-0011", "p-0012"].includes(segment.id) ? "" : "Previously saved translation.";
  }
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId && translationJob("A").status === "processing");
  assert.equal(await page.locator("#p-0002 > .translation").count(), 0, "Source is readable before its translation exists");
  assert.equal(await page.locator("#paper-brief").count(), 0);
  await page.evaluate(() => {
    window.originalSource = document.querySelector("#p-0002 .source-text");
    openAnnotationDrawer("p-0002", "blue");
  });
  await page.locator("#noteText").fill("  Preserve this unfinished thought.\nDo not summarize it.  ");
  const position = await page.evaluate(() => {
    window.scrollTo({ top: 1800, behavior: "instant" });
    const node = [...document.querySelectorAll("#documentRoot .paragraph")].find(item => item.getBoundingClientRect().bottom > 124);
    return { id: node.id, top: node.getBoundingClientRect().top };
  });
  fixture.publishTranslation("A", "p-0002", "The newly translated paragraph. ".repeat(30));
  await page.waitForFunction(() => document.querySelector("#p-0002 > .translation")?.textContent.includes("newly translated"));
  assert.equal(await page.evaluate(() => window.originalSource === document.querySelector("#p-0002 .source-text")), true);
  assert.equal(await page.locator("#noteText").inputValue(), "  Preserve this unfinished thought.\nDo not summarize it.  ");
  assert.equal(await page.locator("#noteText").evaluate(node => node === document.activeElement), true);
  assert.ok(await page.evaluate(saved => Math.abs(document.getElementById(saved.id).getBoundingClientRect().top - saved.top) < 10, position));
  assert.equal(await page.evaluate(() => state.payload.segments[0].translation), "Previously saved translation.");
  await page.evaluate(() => openPaperInWorkspace("B"));
  await page.waitForFunction(() => state.currentPaperId === "B" && !state.paperLoadingId);
  fixture.publishTranslation("A", "p-0011", "Translation belonging only to A.");
  assert.ok(!await page.locator("#documentRoot").innerText().then(text => text.includes("Translation belonging only to A.")));
  await page.evaluate(() => openPaperInWorkspace("A"));
  await page.waitForFunction(() => document.querySelector("#p-0011 > .translation")?.textContent.includes("belonging only to A"));
  assert.equal(fixture.papers.get("A").annotations.annotations[0].note, "  Preserve this unfinished thought.\nDo not summarize it.  ");
  await page.locator("#translateCurrentPaper").click();
  await page.waitForFunction(() => translationJob("A").status === "paused");
  await page.reload();
  await page.waitForFunction(() => !state.paperLoadingId && translationJob("A").status === "paused");
  assert.equal(await page.locator("#translateCurrentPaper").innerText(), "Resume");
  await page.locator("#translateCurrentPaper").click();
  await page.waitForFunction(() => translationJob("A").status === "processing");
  Object.assign(fixture.translationJob("A"), { status: "failed", error: "Synthetic proxy quota error" });
  await page.waitForFunction(() => document.querySelector("#translationStatusDetail").textContent.includes("Synthetic proxy quota error"));
  await page.locator("#translateCurrentPaper").click();
  await page.waitForFunction(() => translationJob("A").status === "processing");
  fixture.publishTranslation("A", "p-0012", "The last newly translated paragraph.");
  await page.waitForFunction(() => translationJob("A").status === "ready");
  assert.equal(await page.locator("#p-0012 > .translation").innerText(), "The last newly translated paragraph.");
  assert.equal(await page.locator("#translateCurrentPaper").isVisible(), false);
  assert.ok(!fixture.calls.some(call => /\/(chat|reading-narrative|thinking\/explain)$/.test(call.pathname)));
  assert.deepEqual(errors, []);
});

test("an unparsed PDF opens into background parsing and then the original Markdown", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  fixture.control.autoTranslate = true;
  const paper = fixture.papers.get("A");
  const segments = paper.segments;
  paper.segments = [];
  Object.assign(paper.metadata, { processing_mode: "library-only", processing_status: "not_processed" });
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.payload?.metadata.processing_status === "processing_queued");
  assert.equal(await page.locator("#documentRoot .paragraph").count(), 0);
  assert.equal(fixture.calls.filter(call => call.method === "POST" && call.pathname === "/api/papers/A/process").length, 1);
  assert.equal(fixture.calls.filter(call => call.pathname === "/api/papers/A/translate").length, 0);
  paper.segments = segments;
  paper.metadata.processing_status = "ready";
  await page.waitForFunction(() => document.querySelectorAll("#documentRoot .paragraph").length === 240
    && translationJob("A").status === "processing");
  assert.equal(await page.locator("#paper-brief").count(), 0);
  assert.ok(!fixture.calls.some(call => /\/(chat|reading-narrative|thinking\/explain)$/.test(call.pathname)));
  assert.deepEqual(errors, []);
});

test("Feishu columns refresh metadata without replacing source, note drafts, or local briefs", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  fixture.control.feishu = true;
  fixture.control.feishuDelay = 1300;
  const paper = fixture.papers.get("A");
  paper.metadata.title = "Paper A![](images/header.jpg)";
  paper.segments[0].markdown = "# Paper A![](images/header.jpg)";
  paper.outline.outline[0].title = paper.metadata.title;
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  assert.equal(await page.locator("#documentRoot .paragraph").count(), 240);
  assert.ok(!(await page.locator("#paperMeta").innerText()).includes("images/header"));
  await page.evaluate(() => {
    window.originalSourceNode = document.querySelector("#p-0002 .source-text");
    openAnnotationDrawer("p-0002", "blue");
  });
  await page.locator("#noteText").fill("Do not overwrite my in-progress thought.");
  await page.waitForFunction(() => state.payload?.metadata.title_source === "feishu");
  assert.equal(await page.locator("#paperMeta .meta-title").innerText(), "Mapped title from Feishu");
  assert.equal(await page.locator("#outlineList .outline-item-title").first().innerText(), "Mapped title from Feishu");
  assert.equal(await page.locator("#noteText").inputValue(), "Do not overwrite my in-progress thought.");
  assert.equal(await page.evaluate(() => document.querySelector("#p-0002 .source-text") === window.originalSourceNode), true);
  assert.equal(await page.evaluate(() => state.thinking.explain.content), "");
  assert.equal(await page.evaluate(() => state.payload.segments[0].markdown), "# Paper A![](images/header.jpg)");
  await page.locator("#readerMoreActions > summary").click();
  await page.keyboard.press("Escape");
  assert.equal(await page.locator("#noteText").inputValue(), "Do not overwrite my in-progress thought.");
  assert.equal(await page.locator("#noteDrawer").getAttribute("aria-hidden"), "false");
  await page.locator("#readerMoreActions > summary").click();
  await page.locator("#toggleFeishuMetadata").click();
  assert.match(await page.locator("#feishuMetadataPanel").innerText(), /资料名称 → title/);
  assert.match(await page.locator("#feishuMetadataPanel").innerText(), /作者AI → authors/);
  assert.equal(await page.locator("#feishuMetadataPanel .feishu-brief").count(), 2);
  fixture.control.feishuError = true;
  await page.locator("[data-refresh-feishu]").click();
  await page.waitForFunction(() => feishuPaperState("A").status === "failed");
  assert.equal(await page.evaluate(() => state.payload.metadata.title), "Mapped title from Feishu");
  assert.equal(await page.locator("#noteText").inputValue(), "Do not overwrite my in-progress thought.");
  assert.match(await page.locator("#feishuMetadataPanel .error-text").innerText(), /permission error/);
  assert.deepEqual(errors, []);
});

test("ambiguous Feishu association can be explicitly selected and translation queue controls other papers", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  fixture.control.feishu = true;
  fixture.control.feishuNeedsMatch = true;
  fixture.translationJob("A").status = "processing";
  fixture.translationJob("B").status = "queued";
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => feishuPaperState("A").status === "needs_match");
  assert.equal(await page.evaluate(() => state.payload.metadata.title), "Paper A");
  await page.locator("#readerMoreActions > summary").click();
  await page.locator("#toggleFeishuMetadata").click();
  await page.locator("#feishuSearchKeyword").fill("Mapped");
  await page.locator("[data-search-feishu]").click();
  await page.locator("[data-link-feishu]").click();
  await page.waitForFunction(() => state.payload.metadata.feishu?.record_id === "recFixture");
  await page.locator("#toggleTranslationQueue").click();
  await page.waitForFunction(() => document.querySelectorAll(".translation-queue-item").length === 2);
  assert.match(await page.locator("#translationQueueSummary").innerText(), /1 active \/ 2 maximum/);
  await page.locator('[data-queue-paper="B"]').click();
  await page.waitForFunction(() => translationJob("B").status === "paused");
  assert.equal(await page.evaluate(() => state.currentPaperId), "A");
  assert.equal(await page.locator('[data-queue-paper="B"]').innerText(), "Resume");
  await page.locator('[data-queue-paper="B"]').click();
  await page.waitForFunction(() => translationJob("B").status === "processing");
  assert.equal(fixture.translationJob("B").status, "processing");
  for (const width of [900, 1100, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    const bounds = await page.locator("#translationQueuePanel").boundingBox();
    assert.ok(bounds.x >= 0 && bounds.x + bounds.width <= width);
  }
  await page.locator("#closeTranslationQueue").click();
  assert.equal(await page.locator("#translationQueuePanel").isVisible(), false);
  assert.deepEqual(errors, []);
});

test("equations appear once in the reader and note preview while old and new highlights keep their offsets", { timeout: 45000 }, async t => {
  const fixture = await fixtureServer();
  const paper = fixture.papers.get("A");
  const equation = String.raw`$$\hat{O}_{AI}=\frac{1-U}{1-U+S}\cdot O_{AI}+\frac{S}{1-U+S}\cdot O_{Human}\tag{1}$$`;
  const translated = "关系如下：\n$$x_{score}=y$$\n其中 $x_{score}$ 表示得分。保留原有解释。新批注位置。";
  const oldQuote = "保留原有解释。";
  const newQuote = "新批注位置。";
  paper.segments = [
    paper.segments[0],
    { id: "p-0002", kind: "paragraph", markdown: equation, translation: equation },
    { id: "p-0003", kind: "paragraph",
      markdown: "The relation is:\n$$x_{score}=y$$\nHere $x_{score}$ is a score. We keep the explanation.",
      translation: translated },
    { id: "p-0004", kind: "paragraph", markdown: "The following paragraph.", translation: "下一段。" },
  ];
  paper.annotations.annotations = [
    { id: "equation-note", segment_id: "p-0002", target: "translation", quote: equation,
      range: { start: 0, end: equation.length }, note: "My note on the older translated equation.", color: "yellow", tags: [] },
    { id: "old-after-equation", segment_id: "p-0003", target: "translation", quote: oldQuote,
      range: { start: translated.indexOf(oldQuote), end: translated.indexOf(oldQuote) + oldQuote.length },
      note: "Keep my existing explanation note.", color: "blue", tags: [] },
  ];
  const originals = JSON.stringify(paper.segments);
  const originalNotes = JSON.stringify(paper.annotations.annotations);
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => { await browser.close(); await new Promise(resolve => fixture.server.close(resolve)); });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  assert.equal(await page.locator("#p-0002 .math-display").count(), 1);
  assert.equal(await page.locator("#p-0002 > .translation").count(), 0);
  assert.equal(await page.locator("#margin-note-equation-note").innerText(), "My note on the older translated equation.");
  assert.equal(await page.locator("#p-0003 > .source-text .math-display").count(), 1);
  assert.equal(await page.locator("#p-0003 > .translation .math-display").count(), 0);
  assert.equal(await page.locator("#p-0003 > .translation .math-inline").count(), 1);
  assert.equal(await page.locator('#p-0003 > .translation [data-annotation-id="old-after-equation"]').innerText(), oldQuote);
  assert.equal(JSON.stringify(paper.segments), originals, "Showing one equation does not rewrite old translations");
  assert.equal(JSON.stringify(paper.annotations.annotations), originalNotes);

  await page.locator("#p-0003 > .translation").scrollIntoViewIfNeeded();
  const selection = await page.evaluate(quote => {
    const root = document.querySelector("#p-0003 > .translation");
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      const start = node.textContent.indexOf(quote);
      if (start < 0) continue;
      const range = document.createRange();
      range.setStart(node, start);
      range.setEnd(node, start + quote.length);
      getSelection().removeAllRanges();
      getSelection().addRange(range);
      return getReaderSelection();
    }
    throw new Error("The translated prose was not rendered.");
  }, newQuote);
  assert.equal(selection.quote, newQuote);
  assert.deepEqual(selection.range, { start: translated.indexOf(newQuote), end: translated.indexOf(newQuote) + newQuote.length });
  await page.locator("#toolbarNote").click();
  await page.locator("#noteText").fill("New note after the omitted equation and inline variable.");
  await page.locator("#saveNote").click();
  await page.waitForFunction(() => !state.paperSessions.get("A").writes.get("annotations")?.dirty);
  const added = paper.annotations.annotations.find(item => !["equation-note", "old-after-equation"].includes(item.id));
  assert.equal(added.quote, newQuote);
  assert.deepEqual(added.range, selection.range);
  assert.equal(await page.locator(`#p-0003 > .translation [data-annotation-id="${added.id}"]`).innerText(), newQuote);
  assert.equal(JSON.stringify(paper.segments), originals);
  await page.reload();
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  assert.equal(await page.locator("#p-0002 .math-display").count(), 1);
  assert.equal(await page.locator(`#p-0003 > .translation [data-annotation-id="${added.id}"]`).innerText(), newQuote);

  await page.locator('.tab[data-view="notes"]').click();
  await page.evaluate(() => openNoteSourcePreview("A", "old-after-equation", "p-0003"));
  const preview = page.locator('#notesSourcePanel [data-preview-pid="p-0003"]');
  assert.equal(await page.locator('#notesSourcePanel [data-preview-pid="p-0002"] .math-display').count(), 1);
  assert.equal(await preview.locator(".translation .math-display").count(), 0);
  assert.equal(await preview.locator(".translation .math-inline").count(), 1);
  assert.equal(await preview.locator('[data-preview-annotation-id="old-after-equation"]').last().innerText(), oldQuote);
  await page.locator('.tab[data-view="reader"]').click();
  await page.evaluate(() => {
    window.equationSourceNode = document.querySelector("#p-0002 > .source-text");
    const segment = state.payload.segments[1];
    applyTranslationResponse("A", { translation: { status: "processing", job_id: "equation-fixture", revision: 1 },
      updates: [{ id: segment.id, markdown: segment.markdown, translation: segment.markdown }] });
  });
  assert.equal(await page.locator("#p-0002 .math-display").count(), 1);
  assert.equal(await page.evaluate(() => document.querySelector("#p-0002 > .source-text") === window.equationSourceNode), true);
  for (const mode of ["read", "split"]) {
    await page.locator(`.workspace-mode[data-workspace-mode="${mode}"]`).click();
    await page.setViewportSize({ width: 390, height: 1000 });
    assert.equal(await page.locator("#p-0002 .math-display").count(), 1);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
    await page.setViewportSize({ width: 1440, height: 1100 });
  }
  assert.deepEqual(errors, []);
});

test("figures appear once, captions stay translated, and real text tables retain translated cells", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  const paper = fixture.papers.get("A");
  paper.segments = [
    paper.segments[0],
    { id: "p-0002", kind: "paragraph", markdown: "Original prose. ![](part-one.svg) Figure 2: Original caption.",
      translation: "中文段落。 ![](part-one.svg) 图2：原始中文图注。" },
    { id: "p-0003", kind: "paragraph", markdown: "![](part-two.svg)", translation: "![](part-two.svg)" },
    { id: "p-0004", kind: "table", markdown: "![](part-two.svg) Table 1: Scanned table.",
      translation: "![](part-two.svg) 表1：表格截图。" },
    { id: "p-0005", kind: "table", markdown: "| Method | Score |\n|---|---|\n| Workflow ![](part-one.svg) | 0.87 |",
      translation: "| 方法 | 分数 |\n|---|---|\n| 工作流程 ![](part-one.svg) | 0.87 |" },
    { id: "p-0006", kind: "table", markdown: "<table><tr><th>Method</th><th>Score</th></tr><tr><td rowspan=\"2\">Workflow</td><td>0.87</td></tr><tr><td>0.92</td></tr></table>",
      translation: "<table><tr><th>方法</th><th>分数</th></tr><tr><td rowspan=\"2\">工作流程</td><td>0.87</td></tr><tr><td>0.92</td></tr></table>" },
  ];
  const savedNote = { id: "caption-note", segment_id: "p-0002", target: "translation", quote: "图2：原始中文图注。",
    note: "Keep my original question about this figure.", color: "yellow", tags: ["question"] };
  paper.annotations.annotations = [savedNote];
  const before = JSON.stringify({ segments: paper.segments, annotations: paper.annotations, thinking: paper.thinking });
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  assert.equal(await page.locator("#p-0002 img").count(), 1);
  assert.equal(await page.locator("#p-0002 > .translation img").count(), 0);
  assert.match(await page.locator("#p-0002 > .translation").innerText(), /原始中文图注/);
  assert.equal(await page.locator('#p-0002 > .translation [data-annotation-id="caption-note"]').innerText(), savedNote.quote);
  assert.equal(await page.locator("#p-0003 img").count(), 1);
  assert.equal(await page.locator("#p-0003 > .translation").count(), 0);
  assert.equal(await page.locator("#p-0004 img").count(), 1);
  assert.match(await page.locator("#p-0004 > .translation").innerText(), /表格截图/);
  assert.equal(await page.locator("#p-0004 table").count(), 0);
  assert.equal(await page.locator("#p-0005 table").count(), 2);
  assert.equal(await page.locator("#p-0005 > .translation img").count(), 0);
  assert.equal(await page.locator("#p-0005 > .translation tr").count(), 2);
  assert.deepEqual((await page.locator("#p-0005 > .translation th, #p-0005 > .translation td").allTextContents()).map(text => text.trim()), ["方法", "分数", "工作流程", "0.87"]);
  assert.equal(await page.locator('#p-0006 > .translation td[rowspan="2"]').innerText(), "工作流程");
  assert.match(await page.locator("#p-0006 > .translation").innerText(), /0\.92/);
  const preview = await page.evaluate(() => {
    state.notesPreview.paperId = "A";
    const root = document.createElement("div");
    root.innerHTML = previewParagraphHtml(state.payload.segments[1], state.payload, state.annotations[0]);
    return { images: root.querySelectorAll("img").length, translatedImages: root.querySelectorAll(".translation img").length,
      caption: root.querySelector(".translation").textContent };
  });
  assert.equal(preview.images, 1);
  assert.equal(preview.translatedImages, 0);
  assert.match(preview.caption, /原始中文图注/);
  assert.equal(JSON.stringify({ segments: paper.segments, annotations: paper.annotations, thinking: paper.thinking }), before, "Opening old translations must not rewrite the saved raw data");
  await page.evaluate(() => {
    window.mediaSourceNode = document.querySelector("#p-0002 > .source-text");
    openAnnotationDrawer("p-0002", "blue");
  });
  await page.locator("#noteText").fill("Unfinished draft must remain untouched.");
  await page.evaluate(() => {
    const segment = state.payload.segments[1];
    applyTranslationResponse("A", { translation: { status: "processing", job_id: "media-fixture", revision: 1 },
      updates: [{ id: segment.id, markdown: segment.markdown, translation: "新增译文。 ![](part-one.svg) 图2：更新的中文图注。" }] });
  });
  assert.equal(await page.locator("#p-0002 img").count(), 1);
  assert.match(await page.locator("#p-0002 > .translation").innerText(), /更新的中文图注/);
  assert.equal(await page.evaluate(() => document.querySelector("#p-0002 > .source-text") === window.mediaSourceNode), true);
  assert.equal(await page.locator("#noteText").inputValue(), "Unfinished draft must remain untouched.");
  await page.evaluate(() => {
    const segment = state.payload.segments[1];
    applyTranslationResponse("A", { translation: { status: "processing", job_id: "media-fixture", revision: 2 },
      updates: [{ id: segment.id, markdown: segment.markdown, translation: "![](part-one.svg)" }] });
  });
  assert.equal(await page.locator("#p-0002 > .translation").count(), 0);
  assert.equal(await page.locator("#p-0002 img").count(), 1);
  assert.equal(await page.locator("#noteText").inputValue(), "Unfinished draft must remain untouched.");
  assert.equal(fixture.calls.filter(call => call.method === "POST" && call.pathname.endsWith("/translate")).length, 0);
  assert.deepEqual(errors, []);
});

test("Saved Takeaway switches only the side pane and preserves the chosen workspace mode", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  fixture.papers.get("A").takeaway_doc.blocks = [
    { id: "saved-heading", type: "heading", text: "Saved reading notes", indent: 0 },
    { id: "saved-thought", type: "bullet", text: "My exact original thought.", indent: 1 },
  ];
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.locator('.workspace-mode[data-workspace-mode="split"]').click();
  const before = await page.evaluate(() => {
    window.sourceBeforeTakeaway = document.querySelector("#p-0002");
    return { collapsed: state.paperMapCollapsed, sourceWidth: document.querySelector("#documentRoot").getBoundingClientRect().width };
  });
  await page.locator('[data-reader-side-pane="takeaway"]').click();
  assert.equal(await page.evaluate(() => state.workspaceMode), "split");
  assert.equal(await page.evaluate(() => state.paperMapCollapsed), before.collapsed);
  assert.equal(await page.locator("#documentRoot").isVisible(), true);
  assert.equal(await page.locator("#takeawayPane").isVisible(), true);
  assert.ok(Math.abs(await page.locator("#documentRoot").evaluate(node => node.getBoundingClientRect().width) - before.sourceWidth) < 2);
  await page.locator('[data-takeaway-text="saved-thought"]').fill("My edited thought, not an AI summary.");
  await page.locator('[data-reader-side-pane="sensemaking"]').click();
  assert.equal(await page.evaluate(() => state.workspaceMode), "split");
  await page.locator('[data-reader-side-pane="takeaway"]').click();
  assert.equal(await page.locator('[data-takeaway-text="saved-thought"]').innerText(), "My edited thought, not an AI summary.");
  assert.equal(await page.evaluate(() => document.querySelector("#p-0002") === window.sourceBeforeTakeaway), true);
  await page.locator('.workspace-mode[data-workspace-mode="think"]').click();
  assert.equal(await page.locator("#documentRoot").isVisible(), false);
  await page.locator("#closePresentationReport").click();
  assert.equal(await page.evaluate(() => state.workspaceMode), "think", "Closing a pane must not undo the explicitly selected mode");
  await page.locator('.workspace-mode[data-workspace-mode="split"]').click();
  await page.locator('[data-reader-side-pane="takeaway"]').click();
  await page.evaluate(() => openPaperInWorkspace("B"));
  await page.locator('[data-paper-tab="A"]').click();
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  assert.equal(await page.evaluate(() => state.workspaceMode), "split");
  assert.equal(await page.locator("#takeawayPane").isVisible(), true);
  assert.equal(await page.locator('[data-takeaway-text="saved-thought"]').innerText(), "My edited thought, not an AI summary.");
  assert.equal(await page.locator("#readerSaveStatus").getAttribute("data-state"), "saved");
  assert.equal(fixture.papers.get("A").takeaway_doc.blocks.find(block => block.id === "saved-thought").text, "My edited thought, not an AI summary.");
  assert.deepEqual(errors, []);
});

test("Feishu screening is lazy and read-only until explicit intake, with multiple papers visible in the parse queue", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  Object.assign(fixture.control, { feishu: true, feishuIntake: true, feishuAutoSync: false });
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  assert.equal(fixture.calls.filter(call => /\/api\/(feishu|processing-queue)/.test(call.pathname)).length, 0);
  await page.locator('.tab[data-view="library"]').click();
  await page.locator("#openFeishuIntake").click();
  assert.equal(fixture.calls.filter(call => call.pathname.startsWith("/api/feishu/")).length, 0);
  await page.locator("#feishuIntakeQuery").fill("Synthetic");
  await page.locator("#searchFeishuIntake").click();
  await page.locator('[data-preview-feishu-record="recIntakeOne"]').click();
  await page.waitForFunction(() => state.feishuIntake.record?.record_id === "recIntakeOne" && !state.feishuIntake.loading);
  assert.match(await page.locator(".feishu-intake-brief").innerText(), /已有的筛选摘要/);
  await page.locator('[data-feishu-brief="raw text"]').click();
  assert.match(await page.locator(".feishu-intake-brief").innerText(), /<script>/);
  assert.equal(await page.evaluate(() => globalThis.fixtureInjection), undefined);
  assert.equal(fixture.calls.filter(call => call.method === "POST" && /intake|process|translate|chat/.test(call.pathname)).length, 0);
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    const dialog = await page.locator("#feishuIntakeDialog").boundingBox();
    assert.ok(dialog.x >= 0 && dialog.x + dialog.width <= width + 1);
    assert.equal(await page.locator("#feishuIntakeDialog").evaluate(node => node.scrollWidth <= node.clientWidth + 1), true);
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  if (process.env.READER_TEST_INTAKE_SCREENSHOT) await page.screenshot({ path: process.env.READER_TEST_INTAKE_SCREENSHOT });
  await page.locator("#feishuIntakePreview details summary").click();
  await page.locator("#feishuLocalPdfPath").fill("C:\\synthetic\\example-1.pdf");
  await page.locator("#queueFeishuPaper").click();
  await page.waitForFunction(() => !state.feishuIntake.busy && state.feishuIntake.localPaper?.id === "cloud-recIntakeOne");
  assert.equal(fixture.intakeRequests[0].local_pdf_path, "C:\\synthetic\\example-1.pdf");
  assert.equal(await page.evaluate(() => state.currentPaperId), "A", "Queueing must not switch away from the currently read paper");
  await page.locator('[data-preview-feishu-record="recIntakeTwo"]').click();
  await page.waitForFunction(() => state.feishuIntake.record?.record_id === "recIntakeTwo" && !state.feishuIntake.loading);
  assert.equal(await page.evaluate(() => state.feishuIntake.localPath), "");
  await page.locator("#queueFeishuPaper").click();
  await page.waitForFunction(() => !state.feishuIntake.busy && state.feishuIntake.localPaper?.id === "cloud-recIntakeTwo");
  assert.equal(fixture.processingJobs.size, 2);
  await page.keyboard.press("Escape");
  assert.equal(await page.locator("#feishuIntakeDialog").isVisible(), false);
  await page.locator("#toggleProcessingQueue").click();
  await page.waitForFunction(() => state.processingQueue.data?.jobs.length === 2);
  assert.match(await page.locator("#processingQueueSummary").innerText(), /1 parsing · 1 waiting/);
  assert.match(await page.locator("#processingQueueItems").innerText(), /queue position 1/);
  fixture.processingJobs.get("cloud-recIntakeOne").status = "ready";
  fixture.papers.get("cloud-recIntakeOne").metadata.processing_status = "ready";
  Object.assign(fixture.processingJobs.get("cloud-recIntakeTwo"), { status: "failed", error: "Synthetic parse error" });
  fixture.papers.get("cloud-recIntakeTwo").metadata.processing_status = "failed";
  await page.evaluate(() => refreshProcessingQueue());
  await page.locator('[data-parse-retry="cloud-recIntakeTwo"]').click();
  await page.waitForFunction(() => state.processingQueue.data?.jobs.find(job => job.paper_id === "cloud-recIntakeTwo")?.status === "queued");
  assert.equal(fixture.calls.filter(call => call.pathname === "/api/processing-queue/retry").length, 1);
  await page.locator('[data-parse-open="cloud-recIntakeOne"]').click();
  await page.waitForFunction(() => state.currentPaperId === "cloud-recIntakeOne" && !state.paperLoadingId);
  assert.equal(await page.locator("#processingQueuePanel").isVisible(), false);
  await page.evaluate(() => {
    globalThis.intakeSourceBeforeRefresh = document.querySelector("#p-0002");
    state.chatDraft = "Keep this original unsent question.";
  });
  fixture.cloudRecords.get("recIntakeOne").metadata.title = "An updated cloud column title";
  await page.locator('.tab[data-view="library"]').click();
  await page.locator("#openFeishuIntake").click();
  await page.locator('[data-preview-feishu-record="recIntakeOne"]').click();
  await page.waitForFunction(() => state.feishuIntake.record?.record_id === "recIntakeOne" && !state.feishuIntake.loading);
  assert.equal(await page.locator("#queueFeishuPaper").count(), 0);
  assert.equal(await page.locator("#readFeishuFullText").innerText(), "Read full text");
  assert.equal(await page.locator("#feishuPdfInputs").isVisible(), false);
  assert.equal(await page.locator("#feishuPreviewTitle").innerText(), "An updated cloud column title");
  const requests = fixture.intakeRequests.length;
  await page.evaluate(() => queueFeishuIntake());
  assert.equal(fixture.intakeRequests.length, requests, "A ready paper cannot be requeued through the intake action");
  assert.equal(await page.evaluate(() => state.payload.metadata.title), "Synthetic cloud paper 1", "Previewing is not an implicit metadata refresh");
  assert.equal(await page.evaluate(() => state.chatDraft), "Keep this original unsent question.");
  assert.equal(await page.evaluate(() => document.querySelector("#p-0002") === globalThis.intakeSourceBeforeRefresh), true);
  await page.locator("#readFeishuFullText").click();
  await page.locator("#feishuIntakeDialog").waitFor({ state: "hidden" });
  assert.equal(await page.locator("#feishuIntakeDialog").isVisible(), false);
  assert.equal(fixture.processingJobs.size, 2, "Reusing an import does not duplicate its parsing job");
  assert.equal(fixture.calls.filter(call => /\/chat$|\/translate$|\/candidates\/brief$/.test(call.pathname)).length, 0);
  assert.deepEqual(errors, []);
});

test("Feishu intake failures stay visible without adding a local paper or a parsing job", { timeout: 20000 }, async t => {
  const fixture = await fixtureServer();
  Object.assign(fixture.control, { feishu: true, feishuIntake: true, feishuAutoSync: false, feishuError: true });
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage();
  page.setDefaultTimeout(5000);
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.locator('.tab[data-view="library"]').click();
  await page.locator("#openFeishuIntake").click();
  await page.locator("#feishuIntakeQuery").fill("recIntakeOne");
  await page.locator("#searchFeishuIntake").click();
  await page.waitForFunction(() => state.feishuIntake.record?.record_id === "recIntakeOne" && !state.feishuIntake.loading);
  await page.locator("#queueFeishuPaper").click();
  await page.waitForFunction(() => !state.feishuIntake.busy && state.feishuIntake.error);
  assert.match(await page.locator("#feishuIntakeStatus").innerText(), /Synthetic download failure/);
  assert.equal(fixture.papers.size, 123);
  assert.equal(fixture.processingJobs.size, 0);
  assert.equal(await page.evaluate(() => state.feishuIntake.localPaper), null);
});

test("Feishu parsing completion replaces the disabled queue state with full text without disturbing the briefing", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  Object.assign(fixture.control, { feishu: true, feishuIntake: true, feishuAutoSync: false });
  fixture.cloudRecords.get("recIntakeOne").briefings["raw text_中文"] = Array.from({ length: 60 }, (_, index) => `Original screening paragraph ${index + 1}.`).join("\n\n");
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.locator('.tab[data-view="library"]').click();
  await page.locator("#openFeishuIntake").click();
  await page.locator("#feishuIntakeQuery").fill("recIntakeOne");
  await page.locator("#searchFeishuIntake").click();
  await page.waitForFunction(() => state.feishuIntake.record && !state.feishuIntake.loading);
  assert.equal(await page.locator("#readFeishuFullText").count(), 0);
  await page.locator("#queueFeishuPaper").click();
  await page.waitForFunction(() => feishuIntakePhase() === "processing");
  assert.equal(await page.locator("#queueFeishuPaper").count(), 0);
  assert.equal(await page.locator("#readFeishuFullText").count(), 0);
  assert.equal(await page.locator("#feishuIntakeActions button:disabled").innerText(), "Parsing…");
  await page.evaluate(() => queueFeishuIntake());
  assert.equal(fixture.intakeRequests.length, 1);
  await page.locator(".feishu-intake-brief").evaluate(node => {
    globalThis.briefBeforeCompletion = node;
    node.scrollTop = 230;
    const range = document.createRange();
    range.setStart(node.firstChild, 0);
    range.setEnd(node.firstChild, 8);
    getSelection().removeAllRanges();
    getSelection().addRange(range);
  });
  fixture.processingJobs.get("cloud-recIntakeOne").status = "ready";
  Object.assign(fixture.papers.get("cloud-recIntakeOne").metadata, { processing_status: "ready", translation_status: "processing" });
  await page.waitForFunction(() => feishuIntakePhase() === "ready");
  assert.equal(await page.locator("#queueFeishuPaper").count(), 0);
  assert.equal(await page.locator("#readFeishuFullText").innerText(), "Read full text");
  assert.match(await page.locator("#feishuIntakeStatus").innerText(), /Full text is ready/);
  assert.equal(await page.evaluate(() => document.querySelector(".feishu-intake-brief") === globalThis.briefBeforeCompletion), true);
  assert.equal(await page.locator(".feishu-intake-brief").evaluate(node => node.scrollTop), 230);
  assert.equal(await page.evaluate(() => getSelection().toString()), "Original");
  const count = fixture.calls.filter(call => call.pathname === "/api/processing-queue").length;
  await page.waitForTimeout(2800);
  assert.equal(fixture.calls.filter(call => call.pathname === "/api/processing-queue").length, count, "Ready previews stop polling");
  assert.equal(fixture.calls.filter(call => call.pathname === "/api/feishu/preview").length, 1);
  assert.equal(fixture.calls.filter(call => call.pathname === "/api/papers/cloud-recIntakeOne").length, 0, "Status updates do not reload the full paper");
  assert.equal(fixture.intakeRequests.length, 1);
  assert.deepEqual(errors, []);
});

test("Feishu status polling survives errors, falls back to the local index and exposes an explicit failed-job retry", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  Object.assign(fixture.control, { feishu: true, feishuIntake: true, feishuAutoSync: false, processingQueueError: true });
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage();
  page.setDefaultTimeout(5000);
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.locator('.tab[data-view="library"]').click();
  await page.locator("#openFeishuIntake").click();
  await page.locator("#feishuIntakeQuery").fill("recIntakeOne");
  await page.locator("#searchFeishuIntake").click();
  await page.waitForFunction(() => state.feishuIntake.record && !state.feishuIntake.loading);
  await page.locator("#queueFeishuPaper").click();
  await page.waitForFunction(() => state.feishuIntake.statusError);
  assert.match(await page.locator("#feishuIntakeStatus").innerText(), /Parsing status unavailable/);
  assert.equal(await page.locator("#queueFeishuPaper").count(), 0);
  assert.equal(await page.locator("#readFeishuFullText").count(), 0);
  fixture.control.processingQueueError = false;
  Object.assign(fixture.processingJobs.get("cloud-recIntakeOne"), { status: "failed", error: "Synthetic parsing failure" });
  fixture.papers.get("cloud-recIntakeOne").metadata.processing_status = "failed";
  await page.waitForFunction(() => feishuIntakePhase() === "failed" && !state.feishuIntake.statusError);
  assert.equal(await page.locator("#retryFeishuParsing").innerText(), "Retry parsing");
  assert.equal(await page.locator("#queueFeishuPaper").count(), 0);
  await page.locator("#retryFeishuParsing").click();
  await page.waitForFunction(() => !state.feishuIntake.busy && feishuIntakePhase() === "queued");
  assert.equal(fixture.calls.filter(call => call.pathname === "/api/processing-queue/retry").length, 1);
  assert.equal(fixture.intakeRequests.length, 1, "Retry must not re-import or redownload the PDF");
  fixture.processingJobs.clear();
  fixture.papers.get("cloud-recIntakeOne").metadata.processing_status = "ready";
  await page.waitForFunction(() => feishuIntakePhase() === "ready");
  assert.equal(await page.locator("#readFeishuFullText").isVisible(), true);
  assert.equal(fixture.calls.filter(call => call.pathname === "/api/papers").length, 1);
  assert.equal(fixture.calls.filter(call => call.pathname === "/api/feishu/preview").length, 1);
  await page.evaluate(() => {
    const cached = paperSession("cloud-recIntakeOne");
    cached.payload = { metadata: { id: "cloud-recIntakeOne", processing_mode: "deep", processing_status: "processing" }, segments: [] };
    cached.loadedAt = Date.now();
    watchReaderBackground = () => {};
  });
  await page.locator("#readFeishuFullText").click();
  await page.waitForFunction(() => state.currentPaperId === "cloud-recIntakeOne" && !state.paperLoadingId);
  assert.ok(await page.evaluate(() => state.payload.segments.length > 0), "Read full text must not reuse an empty pre-parse cache");
  assert.equal(fixture.calls.filter(call => call.pathname === "/api/papers/cloud-recIntakeOne").length, 1);
});

test("switching or closing a Feishu preview prevents stale parsing responses and stops hidden polling", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  Object.assign(fixture.control, { feishu: true, feishuIntake: true, feishuAutoSync: false, processingQueueDelay: 350 });
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage();
  page.setDefaultTimeout(5000);
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.locator('.tab[data-view="library"]').click();
  await page.locator("#openFeishuIntake").click();
  await page.locator("#feishuIntakeQuery").fill("Synthetic");
  await page.locator("#searchFeishuIntake").click();
  await page.locator('[data-preview-feishu-record="recIntakeOne"]').click();
  await page.waitForFunction(() => state.feishuIntake.record && !state.feishuIntake.loading);
  await page.locator("#queueFeishuPaper").click();
  await page.waitForFunction(() => !state.feishuIntake.busy && state.processingQueue.loading);
  await page.locator('[data-preview-feishu-record="recIntakeTwo"]').click();
  await page.waitForFunction(() => state.feishuIntake.record?.record_id === "recIntakeTwo" && !state.feishuIntake.loading && !state.processingQueue.loading);
  assert.equal(await page.evaluate(() => state.feishuIntake.localPaper), null);
  assert.equal(await page.locator("#queueFeishuPaper").isEnabled(), true);
  assert.equal(await page.locator("#readFeishuFullText").count(), 0);
  let count = fixture.calls.filter(call => call.pathname === "/api/processing-queue").length;
  await page.waitForTimeout(2800);
  assert.equal(fixture.calls.filter(call => call.pathname === "/api/processing-queue").length, count);
  await page.locator('[data-preview-feishu-record="recIntakeOne"]').click();
  await page.waitForFunction(() => state.feishuIntake.record?.record_id === "recIntakeOne" && state.processingQueue.loading);
  await page.keyboard.press("Escape");
  await page.waitForFunction(() => !state.processingQueue.loading);
  count = fixture.calls.filter(call => call.pathname === "/api/processing-queue").length;
  await page.waitForTimeout(2800);
  assert.equal(fixture.calls.filter(call => call.pathname === "/api/processing-queue").length, count);
});

test("publication preview is explicit, flushes saved records, escapes originals and blocks unsubmitted drafts", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  fixture.control.publication = true;
  const original = "  My original <script>globalThis.publishInjection = true</script> note.\r\n  Keep tabs\tand trailing spaces.  \n";
  fixture.papers.get("A").annotations.annotations = [{
    id: "publish-note", segment_id: "p-0002", target: "source", type: "range", color: "yellow",
    quote: "original paragraph", note: original, range: { start: 8, end: 26 },
  }];
  fixture.papers.get("A").thinking.blocks = [{ id: "discussion", type: "ai_output", mode: "source",
    prompt: "My exact question", content: "An existing AI answer, not a new summary." }];
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  assert.equal(fixture.calls.filter(call => call.pathname.includes("feishu-publication")).length, 0, "Opening a paper must not contact the publishing service");
  await page.evaluate(() => {
    globalThis.publicationSourceNode = document.querySelector("#documentRoot");
    state.thinking.report_thoughts.push({ id: "pending-thought", note: "An exact thought awaiting its scheduled save." });
    scheduleThinkingSave(60000);
  });
  await page.locator("#readerMoreActions summary").click();
  await page.locator("#publishReadingToFeishu").click();
  await page.waitForFunction(() => !state.feishuPublication.loading);
  assert.equal(await page.evaluate(() => state.feishuPublication.error), "");
  assert.ok(await page.evaluate(() => Boolean(state.feishuPublication.preview)));
  const calls = fixture.calls.map(call => `${call.method} ${call.pathname}`);
  assert.ok(calls.indexOf("POST /api/papers/A/thinking") < calls.indexOf("POST /api/papers/A/feishu-publication/preview"));
  assert.equal(fixture.papers.get("A").thinking.report_thoughts[0].note, "An exact thought awaiting its scheduled save.");
  assert.equal(fixture.publicationRequests.length, 0);
  assert.equal(await page.locator("[data-publication-column]").count(), 4);
  assert.equal(await page.getByRole("link", { name: "Open paper in Feishu" }).getAttribute("href"), "https://feishu.cn/base/Fixture?record=recA");
  await page.locator(".feishu-publish-section summary").first().click();
  assert.equal(await page.locator(".feishu-publish-cell").first().textContent(), fixture.publicationPreviews.get("A").columns[0].text);
  assert.match(await page.locator(".feishu-publish-cell").first().textContent(), /My original <script>/);
  assert.equal(await page.locator("#feishuPublishPreview script").count(), 0);
  assert.equal(await page.evaluate(() => globalThis.publishInjection), undefined);
  for (const width of [1440, 900, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    const box = await page.locator("#feishuPublishDialog").boundingBox();
    assert.ok(box.x >= 0 && box.x + box.width <= width + 1);
    assert.ok(box.y >= 0 && box.y + box.height <= 1001);
    assert.equal(await page.locator("#feishuPublishDialog").evaluate(node => node.scrollWidth <= node.clientWidth + 1), true);
  }
  await page.locator("#closeFeishuPublish").click();
  assert.equal(fixture.publicationRequests.length, 0, "Cancel after preview is cloud read-only");
  const previewsBefore = fixture.calls.filter(call => call.pathname.endsWith("feishu-publication/preview")).length;
  await page.evaluate(() => {
    state.chatDraft = "Do not upload an unsubmitted question.";
    return openFeishuPublication();
  });
  assert.match(await page.locator("#feishuPublishError").innerText(), /unsubmitted/);
  assert.equal(await page.evaluate(() => state.chatDraft), "Do not upload an unsubmitted question.");
  assert.equal(fixture.calls.filter(call => call.pathname.endsWith("feishu-publication/preview")).length, previewsBefore);
  assert.equal(await page.evaluate(() => document.querySelector("#documentRoot") === globalThis.publicationSourceNode), true);
  assert.ok(!fixture.calls.some(call => /\/(chat|reading-narrative|translate|thinking\/explain)$/.test(call.pathname)));
  assert.deepEqual(errors, []);
});

test("publication requires confirmation, stops polling when closed, and shows no-op and conflict states", { timeout: 35000 }, async t => {
  const fixture = await fixtureServer();
  fixture.control.publication = true;
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.evaluate(() => openFeishuPublication());
  assert.equal(await page.evaluate(() => state.feishuPublication.error), "");
  assert.equal(fixture.publicationRequests.length, 0);
  await page.locator("#confirmFeishuPublish").click();
  await page.waitForFunction(() => state.feishuPublication.publication?.status === "publishing" && !state.feishuPublication.sending);
  assert.equal(fixture.publicationRequests.length, 1);
  assert.equal(fixture.publicationRequests[0].confirm, true);
  assert.equal(await page.locator("#confirmFeishuPublish").isDisabled(), true);
  await page.locator("#closeFeishuPublish").click();
  await page.waitForTimeout(150);
  const statusReads = fixture.calls.filter(call => call.pathname.endsWith("/feishu-publication")).length;
  await page.waitForTimeout(1450);
  assert.equal(fixture.calls.filter(call => call.pathname.endsWith("/feishu-publication")).length, statusReads);
  fixture.publications.set("A", { ...fixture.publications.get("A"), status: "synced",
    legacy_document_url: "https://feishu.cn/docx/readerArchive", published_at: "2026-09-27T10:00:00Z" });
  await page.evaluate(() => openFeishuPublication());
  assert.equal(await page.locator("#confirmFeishuPublish").isDisabled(), true);
  assert.equal(await page.locator("#confirmFeishuPublish").innerText(), "No changes to publish");
  assert.equal(await page.getByRole("link", { name: "Open paper in Feishu" }).getAttribute("href"), "https://feishu.cn/base/Fixture?record=recA");
  assert.equal(await page.getByRole("link", { name: "Open reading archive" }).count(), 0);
  assert.match(await page.locator("#feishuPublishStatus").innerText(), /Saved to the Feishu table/);
  assert.equal(fixture.publicationRequests.length, 1);
  fixture.control.publicationForceChange = true;
  await page.locator("#refreshFeishuPublish").click();
  await page.waitForFunction(() => !state.feishuPublication.loading && state.feishuPublication.preview?.changed);
  assert.equal(await page.locator("#confirmFeishuPublish").isDisabled(), false, "A changed column projection can be published even with the same raw fingerprint");
  fixture.control.publicationForceChange = false;
  fixture.papers.get("A").thinking.report_thoughts.push({ id: "new", note: "A newly saved local thought." });
  await page.locator("#refreshFeishuPublish").click();
  await page.waitForFunction(() => !state.feishuPublication.loading && state.feishuPublication.preview?.changed);
  fixture.control.publicationConflict = true;
  await page.locator("#confirmFeishuPublish").click();
  await page.waitForFunction(() => Boolean(state.feishuPublication.error));
  assert.match(await page.locator("#feishuPublishError").innerText(), /version changed/);
  assert.equal(await page.locator("#confirmFeishuPublish").isDisabled(), true);
  assert.equal(fixture.publicationRequests.length, 1);
  fixture.control.publicationConflict = false;
  await page.locator("#refreshFeishuPublish").click();
  await page.waitForFunction(() => !state.feishuPublication.loading && !state.feishuPublication.error);
  await page.locator("#confirmFeishuPublish").click();
  await page.waitForFunction(() => state.feishuPublication.publication?.status === "publishing" && !state.feishuPublication.sending);
  fixture.publications.set("A", { ...fixture.publications.get("A"), status: "pending", error: "",
    legacy_document_url: "https://feishu.cn/docx/readerArchive" });
  await page.waitForFunction(() => state.feishuPublication.publication?.status === "pending");
  assert.match(await page.locator("#feishuPublishStatus").innerText(), /Newer local edits/);
  assert.equal(await page.locator("#confirmFeishuPublish").isDisabled(), true);
  assert.equal(fixture.publicationRequests.length, 2);
  assert.ok(!fixture.calls.some(call => /\/(chat|reading-narrative|translate)$/.test(call.pathname)));
});

test("a delayed publication preview cannot replace another paper's dialog", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  fixture.control.publication = true;
  fixture.control.publicationPreviewDelay = 800;
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.evaluate(() => { openFeishuPublication(); });
  await page.waitForFunction(() => state.feishuPublication.loading && Boolean(state.feishuPublication.publication));
  await page.locator("#closeFeishuPublish").click();
  await page.evaluate(() => openPaperInWorkspace("B"));
  fixture.control.publicationPreviewDelay = 0;
  await page.evaluate(() => openFeishuPublication());
  await page.waitForTimeout(1000);
  assert.equal(await page.locator("#feishuPublishPaper").innerText(), "Paper B");
  assert.equal(await page.evaluate(() => state.feishuPublication.preview.destination.record_id), "recB");
  assert.equal(fixture.publicationRequests.length, 0);
});

test("publication recovery requires a fresh preview and permits a verified retry", { timeout: 35000 }, async t => {
  const fixture = await fixtureServer();
  fixture.control.publication = true;
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.evaluate(() => openFeishuPublication());
  await page.locator("#confirmFeishuPublish").click();
  await page.waitForFunction(() => state.feishuPublication.publication?.status === "publishing" && !state.feishuPublication.sending);
  for (const status of ["failed", "interrupted", "conflict", "recovery_required"]) {
    const previous = fixture.publications.get("A");
    const attempts = fixture.publicationRequests.length;
    fixture.publications.set("A", { ...previous, status, error: "The previous attempt stopped.",
      legacy_document_url: "https://feishu.cn/docx/readerArchive" });
    await page.waitForFunction(expected => state.feishuPublication.publication?.status === expected, status);
    assert.equal(await page.locator("#confirmFeishuPublish").isDisabled(), true, status);
    assert.equal(await page.locator("#confirmFeishuPublish").innerText(), "Refresh preview before retrying");
    assert.equal(fixture.publicationRequests.length, attempts);
    await page.locator("#refreshFeishuPublish").click();
    await page.waitForFunction(() => !state.feishuPublication.loading && !state.feishuPublication.error);
    assert.notEqual(await page.evaluate(() => state.feishuPublication.preview.preview_id), previous.preview_id);
    assert.equal(await page.locator("#confirmFeishuPublish").isDisabled(), false, status);
    assert.equal(await page.locator("#confirmFeishuPublish").innerText(), "Retry this publication");
    await page.locator("#confirmFeishuPublish").click();
    await page.waitForFunction(() => state.feishuPublication.publication?.status === "publishing" && !state.feishuPublication.sending);
    assert.equal(fixture.publicationRequests.length, attempts + 1);
    assert.equal(fixture.publications.get("A").record_url, "https://feishu.cn/base/Fixture?record=recA");
    assert.equal(fixture.publications.get("A").legacy_document_url, "https://feishu.cn/docx/readerArchive");
  }
  assert.ok(!fixture.calls.some(call => /\/(chat|reading-narrative|translate)$/.test(call.pathname)));
});

test("AI conversation keeps chronological messages above a fixed composer and preserves highlighted replies", { timeout: 45000 }, async t => {
  const fixture = await fixtureServer();
  const paper = fixture.papers.get("A");
  paper.thinking.blocks = Array.from({ length: 10 }, (_, index) => ({
    id: `chat-${10 - index}`, type: "ai_output", mode: index % 2 ? "source" : "free",
    prompt: `Question ${10 - index}: what supports this conclusion?`,
    content: `Reply ${10 - index} explains the **mechanism** with evidence [p-0002].\n\n${"A useful discussion distinguishes evidence from a suggestion. ".repeat(12)}`,
    created_at: new Date(Date.UTC(2026, 8, 27, 8, 10 - index)).toISOString(),
  }));
  const storedIds = paper.thinking.blocks.map(block => block.id);
  const latest = paper.thinking.blocks[0];
  const start = latest.content.indexOf("mechanism");
  paper.thinking.annotations = [{
    id: "chat-note", block_id: latest.id, target: "thinking", type: "range", color: "yellow",
    quote: "mechanism", note: "My own interpretation, not the AI reply.", range: { start, end: start + 9 },
  }];
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.locator('.workspace-mode[data-workspace-mode="split"]').click();
  await page.waitForFunction(() => document.querySelector("#thinkingChatHistory").scrollTop > 0);
  assert.deepEqual(await page.locator("[data-thinking-block-card]").evaluateAll(nodes => nodes.map(node => node.dataset.thinkingBlockCard)), [...storedIds].reverse());
  assert.deepEqual(await page.evaluate(() => state.thinking.blocks.map(block => block.id)), storedIds, "Rendering must not reorder stored records");
  assert.equal(await page.locator(".thinking-block-delete-row").count(), 0);
  assert.equal(await page.locator('[data-thinking-block-card="chat-10"] .thinking-delete-message').isVisible(), false);
  assert.equal(await page.locator('[data-thinking-block-card="chat-10"] .thinking-message-user .thinking-message-role').innerText(), "You");
  assert.equal(await page.locator('[data-thinking-block-card="chat-10"] .thinking-message-ai .thinking-message-role').innerText(), "AI");
  assert.equal(await page.locator('[data-thinking-block="chat-10"] [data-annotation-id="chat-note"]').innerText(), "mechanism");
  await page.locator('[data-chat-mode="source"]').scrollIntoViewIfNeeded();
  await page.evaluate(() => {
    globalThis.originalChatSourceNode = document.querySelector("#documentRoot");
    const history = document.querySelector("#thinkingChatHistory");
    history.scrollTop = 200;
    history.dispatchEvent(new Event("scroll"));
  });
  const composerBefore = await page.locator("#thinkingChatComposer").boundingBox();
  const originalScroll = await page.evaluate(() => window.scrollY);
  await page.locator('[data-chat-mode="source"]').click();
  await page.waitForFunction(() => Math.abs(document.querySelector("#thinkingChatHistory").scrollTop - 200) < 2);
  const composerAfter = await page.locator("#thinkingChatComposer").boundingBox();
  assert.ok(Math.abs(composerAfter.y - composerBefore.y) < 2, `Reading history does not move the composer: ${JSON.stringify({ composerBefore, composerAfter })}`);
  assert.equal(await page.evaluate(() => window.scrollY), originalScroll, "Chat-only controls must not move the paper");
  assert.equal(await page.evaluate(() => document.querySelector("#documentRoot") === globalThis.originalChatSourceNode), true);
  await page.evaluate(() => focusThinkingBlockCard("chat-10"));
  await page.locator('[data-inline-thinking-note="chat-note"]').click();
  assert.equal(await page.locator("#noteText").inputValue(), "My own interpretation, not the AI reply.");
  await page.locator("#noteText").fill("My revised interpretation remains a personal note.");
  await page.locator("#saveNote").click();
  await page.waitForFunction(() => !state.thinkingDirty && !paperSession("A").writes.get("thinking")?.pending);
  assert.equal(paper.thinking.annotations[0].note, "My revised interpretation remains a personal note.");
  assert.equal(paper.thinking.blocks[0].content, latest.content);
  await page.locator('[data-thinking-block="chat-10"]').evaluate(node => {
    const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    let text;
    while ((text = walker.nextNode())) {
      const start = text.textContent.indexOf("useful discussion");
      if (start < 0) continue;
      const range = document.createRange();
      range.setStart(text, start);
      range.setEnd(text, start + "useful discussion".length);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      document.dispatchEvent(new Event("selectionchange"));
      return;
    }
    throw new Error("Fixture selection was not found");
  });
  await page.locator("#toolbarNote").click();
  await page.locator("#noteText").fill("A second original note on the AI discussion.");
  await page.locator("#saveNote").click();
  await page.waitForFunction(() => state.thinking.annotations.length === 2 && !state.thinkingDirty && !paperSession("A").writes.get("thinking")?.pending);
  assert.equal(paper.thinking.annotations[1].quote, "useful discussion");
  assert.equal(paper.thinking.annotations[1].note, "A second original note on the AI discussion.");
  for (const width of [1440, 900, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const mode of ["split", "think"]) {
      await page.locator(`.workspace-mode[data-workspace-mode="${mode}"]`).click();
      const layout = await page.evaluate(() => {
        const bounds = selector => {
          const node = document.querySelector(selector);
          const rect = node.getBoundingClientRect();
          return { x: rect.x, y: rect.y, width: rect.width, bottom: rect.bottom, height: rect.height,
            clientWidth: node.clientWidth, scrollWidth: node.scrollWidth };
        };
        return { panel: bounds("#sensemakingPanel"), history: bounds("#thinkingChatHistory"), input: bounds("#thinkingChatComposer") };
      });
      assert.ok(layout.history.height >= 100, `History is usable at ${width}/${mode}`);
      assert.ok(layout.history.bottom <= layout.input.y + 1, `Messages must be above the composer at ${width}/${mode}`);
      assert.ok(layout.input.bottom <= layout.panel.bottom + 1, `Composer stays inside the panel at ${width}/${mode}`);
      assert.ok(layout.panel.x >= 0 && layout.panel.x + layout.panel.width <= width + 1);
      assert.ok(layout.history.scrollWidth <= layout.history.clientWidth + 1, `No horizontal chat overflow at ${width}/${mode}`);
    }
  }
  assert.equal(fixture.chatRequests.length, 0);
  assert.deepEqual(errors, []);
});

test("AI conversation shows pending messages, preserves failed drafts and sends only on explicit non-IME input", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  fixture.control.chatDelay = 600;
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.locator('.workspace-mode[data-workspace-mode="split"]').click();
  const question = "What does the paper actually show?";
  await page.locator("#thinkingChatInput").fill(question);
  await page.locator("#thinkingChatInput").evaluate(node => node.dispatchEvent(new KeyboardEvent("keydown", {
    key: "Enter", isComposing: true, bubbles: true, cancelable: true,
  })));
  assert.equal(fixture.chatRequests.length, 0, "Confirming an IME candidate must not send a message");
  await page.locator("#thinkingChatInput").press("Shift+Enter");
  assert.equal(fixture.chatRequests.length, 0, "Shift+Enter only adds a newline");
  await page.locator("#thinkingChatInput").fill(question);
  await page.locator("#sendThinkingChat").click();
  await page.waitForFunction(() => state.chatSending);
  assert.equal(await page.locator("[data-chat-pending] .thinking-block-prompt").innerText(), question);
  assert.equal(await page.locator("#thinkingChatInput").inputValue(), "", "The pending question appears once, not also in the input");
  assert.equal(await page.locator("#sendThinkingChat").isDisabled(), true);
  assert.equal(await page.locator('[data-chat-mode="free"]').isDisabled(), true);
  assert.equal(await page.evaluate(() => state.thinking.blocks.length), 0, "Pending turns are not falsely marked as saved");
  await page.waitForFunction(() => !state.chatSending && state.thinking.blocks.length === 1);
  assert.equal(await page.locator("[data-chat-pending]").count(), 0);
  assert.equal(await page.locator("#thinkingChatInput").evaluate(node => node === document.activeElement), true);
  assert.equal(fixture.papers.get("A").thinking.blocks[0].prompt, question);
  assert.equal(fixture.chatRequests.length, 1);
  fixture.control.failChat = true;
  await page.locator("#thinkingChatInput").fill("Keep this question after a service failure.");
  await page.locator("#sendThinkingChat").click();
  await page.waitForFunction(() => !state.chatSending && state.chatError);
  assert.equal(await page.locator("#thinkingChatError").isVisible(), true);
  assert.match(await page.locator("#thinkingChatError").innerText(), /Synthetic chat service unavailable/);
  assert.equal(await page.locator("#thinkingChatInput").inputValue(), "Keep this question after a service failure.");
  assert.equal(fixture.papers.get("A").thinking.blocks.length, 1);
  fixture.control.failChat = false;
  await page.locator("#sendThinkingChat").click();
  await page.waitForFunction(() => !state.chatSending && state.thinking.blocks.length === 2);
  assert.equal(await page.locator("#thinkingChatError").isVisible(), false);
  assert.equal(fixture.chatRequests.length, 3);
  assert.deepEqual(await page.locator(".thinking-message-user .thinking-block-prompt").allTextContents(), [
    question, "Keep this question after a service failure.",
  ]);
  assert.equal(fixture.papers.get("A").thinking.blocks.length, 2, "Retry adds exactly one completed turn");
  assert.ok(!fixture.calls.some(call => /reading-narrative|feishu|translate$/.test(call.pathname)), "Chat does not trigger a narrative, publishing or translation");
  assert.deepEqual(errors, []);
});

test("AI conversation reply arrival does not displace older history or an active personal-note draft", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  fixture.control.chatDelay = 1200;
  const paper = fixture.papers.get("A");
  paper.thinking.blocks = ["newer", "older"].map(id => ({
    id, type: "ai_output", mode: "source", prompt: `An ${id} question`,
    content: "Original evidence. " + "Read this reply without losing your place. ".repeat(100),
  }));
  paper.thinking.annotations = [{
    id: "existing-chat-note", block_id: "older", target: "thinking", type: "range", color: "yellow",
    quote: "Original evidence", note: "An original saved note.", range: { start: 0, end: 17 },
  }];
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.locator('.workspace-mode[data-workspace-mode="split"]').click();
  await page.locator("#thinkingChatInput").fill("A new follow-up");
  await page.locator("#sendThinkingChat").click();
  await page.waitForFunction(() => state.chatSending);
  await page.evaluate(() => {
    const history = document.querySelector("#thinkingChatHistory");
    history.scrollTop = 0;
    history.dispatchEvent(new Event("scroll"));
    openExistingThinkingAnnotationDrawer("existing-chat-note");
  });
  await page.locator("#noteText").fill("Do not interrupt this unsaved personal thought.");
  await page.waitForFunction(() => !state.chatSending && state.thinking.blocks.length === 3);
  await page.waitForFunction(() => document.querySelector("#thinkingChatHistory").scrollTop === 0);
  assert.equal(await page.locator("#noteText").inputValue(), "Do not interrupt this unsaved personal thought.");
  assert.equal(await page.locator("#noteText").evaluate(node => node === document.activeElement), true);
  assert.equal(paper.thinking.annotations[0].note, "An original saved note.", "Reply arrival does not silently submit a note draft");
  assert.equal(fixture.chatRequests.length, 1);
});

test("AI chat opens directly and manual output uses a full-width editor without losing drafts", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  fixture.papers.get("A").takeaway_doc.blocks = [{ id: "saved-note", type: "bullet", text: "Existing saved thought.", indent: 0 }];
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.locator('.workspace-mode[data-workspace-mode="split"]').click();
  assert.equal(await page.locator("#thinkingChatInput").isVisible(), true);
  assert.equal(await page.locator("#thinkingChatInput").evaluate(node => node.closest("details")), null);
  assert.ok(!(await page.locator("#writingPane").innerText()).includes("Paste AI outputs here"));
  assert.doesNotMatch(await page.locator("#writingPane").innerText(), /Responses are saved below|Conversation mode|Enter to send/);
  assert.equal(await page.locator("#readerSidePanelDescription").count(), 0);
  assert.match(await page.locator('[data-chat-mode="source"]').getAttribute("title"), /passages/);
  await page.locator("#thinkingChatInput").fill("Keep this unsent question.");
  await page.locator('[data-thinking-composer="paste"]').click();
  assert.equal(await page.locator("#manualOutputHelp").count(), 0);
  assert.equal(await page.locator(".manual-draft-status").isVisible(), false);
  const prompt = "  My original prompt.  ";
  const content = "  External AI response, not my personal note.\n\nKeep **these exact words** and line breaks.  ";
  await page.locator("#thinkingBlockPrompt").fill(prompt);
  await page.locator("#thinkingBlockContent").fill(content);
  assert.equal(await page.locator(".manual-draft-status").innerText(), "Unsaved draft");
  assert.equal(await page.locator("#readerSaveStatus").getAttribute("data-state"), "pending");
  await page.evaluate(() => exportReadingData("json"));
  assert.equal(fixture.calls.filter(call => call.pathname.endsWith("/reading-data")).length, 0, "Export must not silently omit an unsubmitted draft");
  assert.match(await page.locator("#toast").innerText(), /Unsubmitted drafts/);
  for (const width of [1440, 900, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    const area = await page.locator("#thinkingBlockContent").boundingBox();
    const pane = await page.locator("#writingPane").boundingBox();
    assert.ok(area.width >= pane.width - 32, `Paste editor is not full-width at ${width}px`);
    assert.ok(area.height >= 280, `Paste editor is too short at ${width}px`);
    assert.ok(area.x >= 0 && area.x + area.width <= width + 1);
  }
  if (process.env.READER_TEST_PASTE_SCREENSHOT) {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.locator("#thinkingBlockContent").scrollIntoViewIfNeeded();
    await page.screenshot({ path: process.env.READER_TEST_PASTE_SCREENSHOT });
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.locator('[data-thinking-composer="chat"]').click();
  assert.equal(await page.locator("#thinkingChatInput").inputValue(), "Keep this unsent question.");
  await page.locator('[data-chat-mode="free"]').click();
  assert.equal(await page.locator("#thinkingChatInput").isVisible(), true);
  await page.locator('[data-thinking-composer="paste"]').click();
  assert.equal(await page.locator("#thinkingBlockContent").inputValue(), content);
  await page.evaluate(() => openPaperInWorkspace("B"));
  await page.locator('.workspace-mode[data-workspace-mode="split"]').click();
  await page.locator('[data-thinking-composer="paste"]').click();
  assert.equal(await page.locator("#thinkingBlockContent").inputValue(), "");
  assert.equal(await page.locator(".manual-draft-status").isVisible(), false);
  await page.locator('[data-paper-tab="A"]').click();
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  assert.equal(await page.locator("#thinkingBlockPrompt").inputValue(), prompt);
  assert.equal(await page.locator("#thinkingBlockContent").inputValue(), content);
  await page.locator("#addThinkingBlock").click();
  await page.waitForFunction(() => !state.thinkingDirty && state.thinking.blocks.length === 1);
  assert.equal(fixture.papers.get("A").thinking.blocks[0].content, content);
  assert.equal(fixture.papers.get("A").thinking.blocks[0].prompt, prompt);
  assert.equal(fixture.papers.get("A").thinking.blocks[0].type, "ai_output");
  assert.equal(await page.locator("#thinkingBlockContent").inputValue(), "");
  await page.locator('[data-reader-side-pane="takeaway"]').click();
  await page.evaluate(() => {
    state.currentSelection = { segment_id: "p-0002", target: "source", quote: "Original evidence", range: { start: 0, end: 17 } };
    askAiFromCurrentSelection();
  });
  assert.equal(await page.locator("#thinkingChatInput").isVisible(), true, "Selection-to-chat opens the correct visible composer, even from Saved Takeaway");
  assert.equal(await page.evaluate(() => state.workspaceMode), "split");
  assert.equal(fixture.calls.filter(call => call.pathname.endsWith("/chat")).length, 0, "Opening chat and saving pasted content never send an AI request");
  assert.deepEqual(errors, []);
});

test("a pasted AI output survives a disk failure without an unhandled error or duplicate on retry", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  fixture.control.failThinking = true;
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.locator('.workspace-mode[data-workspace-mode="split"]').click();
  await page.locator('[data-thinking-composer="paste"]').click();
  const content = "Keep this pasted AI response through a failed save.";
  await page.locator("#thinkingBlockContent").fill(content);
  await page.locator("#addThinkingBlock").click();
  await page.waitForFunction(() => paperSession("A").writes.get("thinking")?.error);
  assert.equal(await page.locator("#readerSaveStatus").getAttribute("data-state"), "error");
  assert.equal(await page.evaluate(() => state.thinking.blocks[0].content), content);
  await page.evaluate(() => openPaperInWorkspace("B"));
  assert.equal(await page.evaluate(() => state.currentPaperId), "A");
  fixture.control.failThinking = false;
  await page.evaluate(() => openPaperInWorkspace("B"));
  await page.waitForFunction(() => state.currentPaperId === "B" && !state.paperLoadingId);
  assert.equal(fixture.papers.get("A").thinking.blocks.length, 1);
  assert.equal(fixture.papers.get("A").thinking.blocks[0].content, content);
  assert.deepEqual(errors, []);
});

test("margin notes and local teacher preserve source, drafts, provenance and responsive reading", { timeout: 90000 }, async t => {
  const fixture = await fixtureServer();
  const paper = fixture.papers.get("A");
  paper.teacher_available = true;
  fixture.teachers.set("A", fixtureTeacher(paper));
  fixture.control.teacherDelay = 900;
  const originalNote = "My raw personal interpretation.\nKeep the uncertainty.\n\n".repeat(12);
  const start = paper.segments[1].markdown.indexOf("exact words");
  paper.annotations.annotations.push({ id: "my-margin-note", segment_id: "p-0002", target: "source",
    range: { start, end: start + 11 }, quote: "exact words", color: "yellow", note: originalNote, tags: [] });
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => { await browser.close(); await new Promise(resolve => fixture.server.close(resolve)); });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  assert.equal(await page.locator("#p-0002 .source-text").isVisible(), true);
  assert.equal(await page.locator(".teacher-card").count(), 0, "The source must appear before the deliberately slow teacher response");
  await page.evaluate(() => {
    window.teacherSourceBefore = document.querySelector("#p-0002 .source-text");
    const range = document.createRange();
    range.setStart(window.teacherSourceBefore.firstChild, 0);
    range.setEnd(window.teacherSourceBefore.firstChild, 4);
    getSelection().removeAllRanges();
    getSelection().addRange(range);
  });
  await page.waitForFunction(() => state.readingTeacher.ranges.size === 1);
  assert.equal(await page.evaluate(() => document.querySelector("#p-0002 .source-text") === window.teacherSourceBefore), true);
  assert.equal(await page.evaluate(() => getSelection().toString()), "This", "Loading teacher must not destroy a source selection");
  assert.deepEqual(await page.evaluate(() => [...CSS.highlights.get("reading-teacher")].map(range => range.toString())), ["exact words"]);
  assert.equal(await page.locator(".teacher-card").count(), 0, "Teacher cards are closed until a reading location is chosen");
  assert.equal(await page.locator('[data-teacher-open="transfer"]').count(), 0, "Project transfer must not appear in the initial reading layer");
  await page.evaluate(() => getSelection().removeAllRanges());
  await page.locator('[data-teacher-open="definition"]').click();
  assert.equal(await page.locator('#p-0002 mark[data-annotation-id="my-margin-note"]').innerText(), "exact words");
  assert.equal(paper.annotations.annotations.length, 1, "Teacher suggestions must not become user annotations automatically");
  assert.equal(paper.annotations.annotations[0].note, originalNote);
  const layout = await page.evaluate(() => {
    const rect = selector => document.querySelector(selector).getBoundingClientRect().toJSON();
    return { source: rect("#p-0002 .source-text"), unannotated: rect("#p-0008 .source-text"),
      notes: rect("#p-0002 .comment-stack"), paragraph: rect("#p-0002"), next: rect("#p-0003"),
      noteBackground: getComputedStyle(document.querySelector(".comment-card")).backgroundColor,
      teacherBackground: getComputedStyle(document.querySelector(".teacher-card")).backgroundColor };
  });
  assert.ok(layout.notes.x >= layout.source.x + layout.source.width + 23, "Notes belong to the right margin at desktop width");
  assert.ok(Math.abs(layout.source.width - layout.unannotated.width) < 1, "All paragraphs share the same source column");
  assert.ok(layout.next.y >= layout.paragraph.y + layout.paragraph.height, "Long and multiple margin cards must not overlap the next paragraph");
  assert.notEqual(layout.noteBackground, layout.teacherBackground);
  assert.notEqual(layout.noteBackground, "rgba(0, 0, 0, 0)");
  await page.locator('[data-expand-annotation="my-margin-note"]').click();
  assert.equal(await page.locator('[data-expand-annotation="my-margin-note"]').getAttribute("aria-expanded"), "true");
  assert.equal(await page.locator("#margin-note-my-margin-note").textContent(), originalNote.trim());
  await page.locator('[data-expand-annotation="my-margin-note"]').click();
  await page.setViewportSize({ width: 390, height: 1000 });
  const mobile = await page.evaluate(() => {
    const article = document.querySelector("#p-0002");
    return { noteTop: article.querySelector(".comment-stack").getBoundingClientRect().top,
      translationBottom: article.querySelector(".translation").getBoundingClientRect().bottom,
      overflow: document.documentElement.scrollWidth > innerWidth + 1 };
  });
  assert.ok(mobile.noteTop >= mobile.translationBottom, "Narrow columns use clearly separated inline cards");
  assert.equal(mobile.overflow, false);
  await page.setViewportSize({ width: 1440, height: 1000 });
  const definition = page.locator('[data-teacher-card="definition"]');
  assert.match(await definition.innerText(), /本文定义.*exact words.*外部定义/s);
  assert.doesNotMatch(await definition.innerText(), /AI teacher|概念辨析|Could people still disagree|AI 对照|线索|记下想法/);
  assert.equal(await definition.locator("details, .teacher-question, [data-teacher-reflect]").count(), 0);
  assert.equal(await definition.getAttribute("aria-label"), "AI teacher: Deliberation");
  assert.equal(await page.locator('#p-0002 .comment-card').getAttribute("aria-label"), "My note");
  assert.doesNotMatch(await page.locator('#p-0002 .comment-card').innerText(), /My note|原文/);
  await definition.locator('[data-teacher-source]').click();
  assert.equal(await page.locator("#readingTeacherLocation").inputValue(), "definition");
  assert.equal(await definition.locator(".teacher-definition-quote").innerText(), "“exact words”");
  assert.equal(await definition.locator(".teacher-definition > div").last().locator("p").innerText(), "Retrieved dictionary meaning. [1]");
  assert.equal(await page.locator('[data-teacher-card="definition"] a').getAttribute("href"), "https://example.org/definition");
  await page.locator("#toggleTeacherDepth").click();
  await page.locator('[data-teacher-open="transfer"]').click();
  await page.locator('[data-teacher-disclosure="transfer:context"] > summary').click();
  assert.match(await page.locator('[data-teacher-disclosure="transfer:context"]').innerText(), /collaborative.*2026-07-04/s);
  assert.match(await page.locator('[data-teacher-disclosure="transfer:context"]').innerText(), /hypothesis/);
  await page.locator("#toggleTeacherDepth").click();
  await page.locator('[data-teacher-open="definition"]').click();
  if (process.env.READER_TEST_UI_SCREENSHOT_PREFIX) {
    await page.locator("#p-0002").scrollIntoViewIfNeeded();
    await page.screenshot({ path: `${process.env.READER_TEST_UI_SCREENSHOT_PREFIX}-teacher.png` });
  }
  fixture.control.failAnnotations = true;
  await page.evaluate(() => {
    const button = document.querySelector('[data-teacher-adopt="definition"]');
    button.click();
    button.click();
  });
  await page.waitForFunction(() => !state.readingTeacher.saving.size && state.paperSessions.get("A").writes.get("annotations")?.error);
  assert.equal(await page.evaluate(() => state.annotations.length), 2, "Double clicks and failed saves must not duplicate definitions");
  assert.equal(await page.locator('[data-retry-definition-save]').innerText(), "Retry save");
  assert.equal(await page.locator('[data-teacher-card="definition"], [data-teacher-open="definition"]').count(), 0);
  assert.equal(await page.locator(".saved-definition-card").count(), 1, "Saving changes the original card into one saved-note view");
  assert.match(await page.locator(".definition-save-state").innerText(), /Not saved/);
  assert.equal(paper.annotations.annotations.length, 1, "A failed disk write is not a saved definition");
  await page.evaluate(() => openPaperInWorkspace("B"));
  assert.equal(await page.evaluate(() => state.currentPaperId), "A", "Unsaved definition protects the tab just like an original note");
  await page.locator("#toggleReadingTeacher").click();
  assert.equal(await page.locator("[data-retry-definition-save]").count(), 1, "A save failure can be retried even with the teacher hidden");
  fixture.control.failAnnotations = false;
  await page.locator("[data-retry-definition-save]").click();
  await page.waitForFunction(() => !state.readingTeacher.saving.size && !state.paperSessions.get("A").writes.get("annotations").dirty);
  assert.equal(paper.annotations.annotations.length, 2);
  const saved = paper.annotations.annotations.find(note => note.origin?.kind === "reading-teacher");
  assert.equal(saved.origin.content_type, "definition");
  assert.equal(saved.origin.card_id, "definition");
  assert.equal(saved.origin.sources[0].url, "https://example.org/definition");
  assert.equal(saved.origin.definition.comparison, fixture.teachers.get("A").cards[0].definition.comparison, "Compact display must not discard legacy provenance");
  assert.match(saved.note, /不是用户原创/);
  assert.match(saved.note, /reader.md#p-0002/);
  assert.equal(saved.origin.initial_note, saved.note);
  assert.equal(paper.annotations.annotations[0].note, originalNote);
  assert.equal(await page.locator(".saved-definition-card .definition-save-state").innerText(), "✓ Saved");
  assert.doesNotMatch(await page.locator(".saved-definition-card").innerText(), /不是用户原创|Retrieved:/);
  await page.locator(`.saved-definition-card [data-edit-annotation="${saved.id}"]`).click();
  assert.equal(await page.locator("#noteText").inputValue(), saved.note);
  assert.equal(paper.annotations.annotations.length, 2);
  await page.evaluate(() => closeDrawer());
  await page.locator("#toggleReadingTeacher").click();
  await page.locator("#toggleTeacherDepth").click();
  await page.locator('[data-teacher-open="transfer"]').click();
  await page.locator('[data-teacher-reflect="transfer"]').click();
  assert.equal(await page.locator("#noteText").inputValue(), "", "The teacher must not pre-fill a user's answer");
  await page.locator("#noteText").fill("  My own response.\nI still have a question.\n");
  await page.locator("#saveNote").click();
  await page.waitForFunction(() => !state.paperSessions.get("A").writes.get("annotations").dirty);
  const reflection = paper.annotations.annotations.find(note => note.teacher_prompt);
  assert.equal(reflection.note, "  My own response.\nI still have a question.\n");
  assert.equal(reflection.teacher_prompt.card_id, "transfer");
  assert.equal(reflection.origin, undefined, "A user's response is not AI-authored");
  await page.locator('.tab[data-view="notes"]').click();
  await page.waitForSelector(`[data-note-row="${saved.id}"]`);
  assert.equal(await page.locator(`[data-note-row="${saved.id}"] .note-user-block .note-block-label`).innerText(), "SAVED AI DEFINITION");
  await page.locator('.tab[data-view="reader"]').click();
  await page.evaluate(() => { window.sourceBeforeTeacherToggle = document.querySelector("#p-0002 .source-text"); });
  await page.locator("#toggleReadingTeacher").click();
  assert.equal(await page.locator(".teacher-card").count(), 0);
  assert.equal(await page.evaluate(() => CSS.highlights.has("reading-teacher")), false);
  assert.equal(await page.evaluate(() => document.querySelector("#p-0002 .source-text") === window.sourceBeforeTeacherToggle), true);
  assert.equal(await page.locator("#p-0002 .comment-card").count(), 2, "Hiding the teacher must retain personal and explicitly accepted notes");
  assert.equal(await page.locator("#p-0007 .comment-card").count(), 1, "The human response remains on the question's source");
  await page.evaluate(() => openPaperInWorkspace("B"));
  assert.equal(await page.locator("#toggleReadingTeacher").isVisible(), false);
  await page.evaluate(() => openPaperInWorkspace("A"));
  assert.equal(await page.locator("#toggleReadingTeacher").getAttribute("aria-pressed"), "false");
  assert.equal(fixture.calls.filter(call => call.pathname === "/api/papers/A/reading-teacher").length, 1, "Warm tabs reuse the local teaching data");
  await page.locator("#toggleReadingTeacher").click();
  fixture.control.teacherError = true;
  fixture.control.teacherDelay = 0;
  await page.evaluate(() => loadPaper("A", { force: true }));
  await page.waitForFunction(() => state.readingTeacher.error);
  assert.equal(await page.locator("#p-0002 .source-text").isVisible(), true);
  assert.match(await page.locator("#readingTeacherStatus").innerText(), /原文和笔记仍可正常使用/);
  fixture.control.teacherError = false;
  fixture.teachers.get("A").cards[0].anchor.source_markdown += " Changed on disk.";
  await page.getByRole("button", { name: "Retry teacher", exact: true }).click();
  await page.waitForFunction(() => state.readingTeacher.issues.length === 1 && !state.readingTeacher.loading);
  assert.equal(await page.locator('[data-teacher-card="definition"]').count(), 0, "Changed source may not receive a plausible-looking fallback highlight");
  assert.match(await page.locator("#readingTeacherStatus").innerText(), /引用失效/);
  await page.locator("#toggleTeacherDepth").click();
  await page.locator('[data-teacher-open="transfer"]').click();
  assert.equal(await page.locator('[data-teacher-card="transfer"]').count(), 1);
  assert.equal(fixture.calls.filter(call => /\/(chat|translate|process)$/.test(call.pathname)).length, 0);
  assert.deepEqual(errors, []);
});

test("teacher cues open from exact source hits or keyboard without taking over notes", { timeout: 45000 }, async t => {
  const fixture = await fixtureServer();
  const paper = fixture.papers.get("A");
  paper.teacher_available = true;
  const teacher = fixtureTeacher(paper);
  const anchor = (index, quote) => ({
    segment_id: paper.segments[index].id, quote, source_markdown: paper.segments[index].markdown,
    source_sha256: require("node:crypto").createHash("sha256").update(paper.segments[index].markdown).digest("hex"),
  });
  teacher.cards.push(
    { id: "cue", kind: "cue", title: "Read the mechanism", form: "question",
      text: "What does the evidence change here?",
      anchor: anchor(8, "The evidence should remain linked to the exact words selected by the reader.") },
    { id: "usage", kind: "definition", title: "Reliance", anchor: anchor(9, "evidence"),
      definition: { paper_kind: "usage", paper: "How this paper uses the term.",
        external: [{ kind: "ai-summary", summary: "A short general meaning, not a retrieved quotation." }] } },
  );
  fixture.teachers.set("A", teacher);
  const start = paper.segments[1].markdown.indexOf("exact words");
  paper.annotations.annotations.push({ id: "personal", segment_id: "p-0002", target: "source",
    range: { start, end: start + 11 }, quote: "exact words", color: "yellow", note: "My unedited thought.", tags: [] });
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => { await browser.close(); await new Promise(resolve => fixture.server.close(resolve)); });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.readingTeacher.ranges.size === 3);
  assert.equal(await page.locator(".teacher-card").count(), 0);
  assert.equal(await page.locator(".teacher-marker").count(), 3);
  assert.equal(await page.evaluate(() => CSS.highlights.get("reading-teacher-cues").size), 1);
  assert.equal(await page.locator(".teacher-question, [data-teacher-disclosure]").count(), 0);

  await page.locator("#p-0009").scrollIntoViewIfNeeded();
  const hit = await page.evaluate(() => {
    window.cueSource = document.querySelector("#p-0009 .source-text");
    const rect = [...state.readingTeacher.ranges.get("cue").getClientRects()].filter(rect => rect.width > 1).at(-1);
    return { x: rect.x + Math.min(8, rect.width / 2), y: rect.y + rect.height / 2 };
  });
  await page.evaluate(({ x, y }) => {
    const selection = document.createRange();
    selection.setStart(window.cueSource.firstChild, 0);
    selection.setEnd(window.cueSource.firstChild, 4);
    getSelection().removeAllRanges();
    getSelection().addRange(selection);
    window.cueSource.dispatchEvent(new MouseEvent("click", { bubbles: true, clientX: x, clientY: y, button: 0, detail: 1 }));
  }, hit);
  assert.equal(await page.locator(".teacher-card").count(), 0, "A reading selection takes precedence over opening a cue");
  assert.equal(await page.evaluate(() => getSelection().toString()), "This");
  await page.evaluate(() => getSelection().removeAllRanges());
  await page.mouse.click(hit.x, hit.y);
  assert.equal(await page.locator('[data-teacher-card="cue"] .teacher-cue').innerText(), "What does the evidence change here?");
  assert.equal(await page.locator('[data-teacher-card="cue"] details, [data-teacher-card="cue"] .teacher-actions').count(), 0);
  assert.equal(await page.locator("#noteDrawer").evaluate(node => node.classList.contains("open")), false);
  assert.equal(await page.evaluate(() => document.querySelector("#p-0009 .source-text") === window.cueSource), true);
  assert.equal(paper.annotations.annotations.length, 1);
  await page.locator('[data-teacher-close="cue"]').click();

  await page.locator("#p-0009").scrollIntoViewIfNeeded();
  const outside = await page.evaluate(() => {
    const range = document.createRange();
    range.setStart(window.cueSource.firstChild, 0);
    range.setEnd(window.cueSource.firstChild, 4);
    const rect = range.getBoundingClientRect();
    return { x: rect.x + 2, y: rect.y + rect.height / 2 };
  });
  await page.mouse.click(outside.x, outside.y);
  assert.equal(await page.locator(".teacher-card").count(), 0, "A paragraph click outside the marked words is not a teacher action");
  await page.locator('[data-teacher-open="cue"]').focus();
  await page.keyboard.press("Enter");
  assert.equal(await page.locator(".teacher-card").count(), 1);
  assert.equal(await page.evaluate(() => document.activeElement.id), "teacher-card-cue");
  await page.keyboard.press("Escape");
  assert.equal(await page.locator(".teacher-card").count(), 0);
  assert.equal(await page.evaluate(() => document.activeElement.dataset.teacherOpen), "cue");

  await page.locator('mark[data-annotation-id="personal"]').click();
  assert.equal(await page.locator("#noteText").inputValue(), "My unedited thought.");
  assert.equal(await page.locator(".teacher-card").count(), 0, "A personal highlight opens its own note, not the overlapping AI definition");
  await page.locator("#closeDrawer").click();
  await page.locator("#readingTeacherLocation").selectOption("usage");
  const usage = page.locator('[data-teacher-card="usage"]');
  assert.match(await usage.innerText(), /本文用法.*一般含义 · AI 概括/s);
  assert.equal(await usage.locator("a, .teacher-question, details, [data-teacher-reflect]").count(), 0);
  await usage.locator("[data-teacher-adopt]").click();
  await page.waitForFunction(() => !state.readingTeacher.saving.size && !state.paperSessions.get("A").writes.get("annotations")?.dirty);
  const saved = paper.annotations.annotations.find(note => note.origin?.card_id === "usage");
  assert.ok(saved);
  assert.deepEqual(saved.origin.sources, []);
  assert.equal(saved.origin.definition.paper_kind, "usage");
  assert.equal(saved.origin.definition.external[0].kind, "ai-summary");
  assert.match(saved.note, /本文用法（AI 概括）/);
  assert.match(saved.note, /AI 概括（未外部检索）/);
  assert.doesNotMatch(saved.note, /Retrieved:|https:|undefined/);
  assert.equal(paper.annotations.annotations[0].note, "My unedited thought.");
  await page.evaluate(() => {
    const card = state.readingTeacher.data.cards.find(item => item.id === "usage");
    card.definition.paper = "A later teacher suggestion.";
    card.definition.external[0].summary = "A later general explanation.";
    refreshReadingTeacher();
  });
  assert.equal(await page.locator(".saved-definition-card .teacher-definition > div").first().locator("p").innerText(),
    "How this paper uses the term.", "Accepted provenance must not alias the mutable teacher suggestion");
  assert.doesNotMatch(await page.locator(".saved-definition-card").innerText(), /A later/);

  await page.evaluate(() => openPaperInWorkspace("B"));
  await page.evaluate(() => openPaperInWorkspace("A"));
  assert.equal(await page.locator(`[data-saved-definition="${saved.id}"]`).count(), 1, "Warm tabs retain one saved definition, not a second teacher copy");
  assert.equal(await page.locator('[data-teacher-card="usage"], [data-teacher-open="usage"]').count(), 0);
  assert.equal(fixture.calls.filter(call => call.pathname === "/api/papers/A/reading-teacher").length, 1);
  await page.locator("#toggleTeacherDepth").click();
  assert.equal(await page.locator(".teacher-card").count(), 0);
  assert.equal(await page.locator(".teacher-marker").count(), 1);
  await page.locator('[data-teacher-open="transfer"]').click();
  assert.equal(await page.locator(".teacher-question").count(), 1, "Only an explicit deeper-layer choice exposes project questions");
  await page.locator("#toggleTeacherDepth").click();
  assert.equal(await page.locator(".teacher-marker").count(), 2, "The saved term does not get a duplicate teacher marker");
  for (const mode of ["read", "split"]) {
    await page.locator(`[data-workspace-mode="${mode}"].workspace-mode`).click();
    await page.setViewportSize({ width: 390, height: 1000 });
    await page.locator("#readingTeacherLocation").selectOption("cue");
    assert.equal(await page.locator(".teacher-card").count(), 1);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
    await page.setViewportSize({ width: 1440, height: 1000 });
  }
  await page.evaluate(() => {
    CSS.highlights.clear();
    Object.defineProperty(CSS, "highlights", { configurable: true, value: undefined });
    refreshReadingTeacher();
  });
  assert.match(await page.locator("#readingTeacherStatus").innerText(), /不支持原文标记/);
  await page.locator("#readingTeacherLocation").selectOption("definition");
  assert.equal(await page.locator('[data-teacher-card="definition"]').count(), 1, "The location picker still works without native highlights");
  assert.equal(fixture.calls.filter(call => /\/(chat|translate|process)$/.test(call.pathname)).length, 0);
  assert.deepEqual(errors, []);
});

test("teacher navigation reaches all eight locations in source order without reloading", { timeout: 30000 }, async t => {
  const fixture = await fixtureServer();
  const paper = fixture.papers.get("A");
  paper.teacher_available = true;
  const teacher = fixtureTeacher(paper);
  teacher.cards[1] = {
    id: "mechanism", kind: "cue", title: "Mechanism", anchor: teacher.cards[1].anchor,
    text: "Notice what this method changes.", form: "statement",
  };
  const extraIndices = [8, 30, 80, 140, 180, 220];
  teacher.cards.push(...extraIndices.map(index => ({
    ...teacher.cards[1], id: `cue-${index}`, title: `Reading cue at paragraph ${index + 1}`,
    anchor: { segment_id: paper.segments[index].id, quote: `original paragraph ${index + 1}`,
      source_markdown: paper.segments[index].markdown,
      source_sha256: require("node:crypto").createHash("sha256").update(paper.segments[index].markdown).digest("hex") },
  })));
  teacher.cards.reverse();
  fixture.teachers.set("A", teacher);
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => { await browser.close(); await new Promise(resolve => fixture.server.close(resolve)); });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.readingTeacher.ranges.size === 8);
  const ids = ["definition", "mechanism", ...extraIndices.map(index => `cue-${index}`)];
  assert.deepEqual(await page.locator("#readingTeacherLocation option").evaluateAll(options =>
    options.map(option => option.value).filter(Boolean)), ids);
  assert.equal(await page.locator("#readingTeacherLocation").inputValue(), "");
  assert.equal(await page.locator("#readingTeacherStatus").isVisible(), false, "Ready state has no tutorial paragraph");
  assert.equal(await page.locator("#previousTeacherCard").isEnabled(), false);
  assert.equal(await page.locator(".teacher-card").count(), 0);
  await page.evaluate(() => { window.navigationSource = document.querySelector("#p-0002 .source-text"); });
  for (const id of ids) {
    await page.locator("#nextTeacherCard").click();
    assert.equal(await page.locator("#readingTeacherLocation").inputValue(), id);
    const rangeText = await page.evaluate(() => [...CSS.highlights.get("reading-teacher-focus")][0].toString());
    assert.equal(rangeText, teacher.cards.find(card => card.id === id).anchor.quote);
    assert.equal(await page.locator(".teacher-card").count(), 1, "Navigation only opens the selected reading prompt");
    assert.equal(await page.locator(`[data-teacher-card="${id}"]`).count(), 1);
  }
  assert.equal(await page.locator("#nextTeacherCard").isEnabled(), false);
  await page.locator("#previousTeacherCard").click();
  assert.equal(await page.locator("#readingTeacherLocation").inputValue(), ids.at(-2));
  await page.locator("#readingTeacherLocation").selectOption("definition");
  assert.equal(await page.locator("#previousTeacherCard").isEnabled(), false);
  assert.equal(await page.evaluate(() => document.querySelector("#p-0002 .source-text") === window.navigationSource), true);
  assert.equal(fixture.calls.filter(call => call.pathname === "/api/papers/A").length, 1);
  assert.equal(fixture.calls.filter(call => call.pathname.endsWith("/reading-teacher")).length, 1);
  assert.equal(paper.annotations.annotations.length, 0, "Navigation is not a note write");
  for (const mode of ["think", "split", "read"]) {
    await page.locator(`[data-workspace-mode="${mode}"].workspace-mode`).click();
    assert.equal(await page.locator("#readingTeacherNav").isVisible(), mode !== "think");
  }
  await page.setViewportSize({ width: 390, height: 1000 });
  assert.equal(await page.locator("#readingTeacherNav").isVisible(), true);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1), false);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.locator("#toggleReadingTeacher").click();
  assert.equal(await page.locator("#readingTeacherNav").isVisible(), false);
  await page.locator("#toggleReadingTeacher").click();
  assert.equal(await page.locator("#readingTeacherLocation").inputValue(), "definition");
  await page.locator("#readingTeacherLocation").selectOption("cue-220");
  await page.evaluate(() => {
    state.readingTeacher.data.cards.find(card => card.id === "cue-220").anchor.source_markdown += " Changed.";
    refreshReadingTeacher();
  });
  assert.equal(await page.locator("#readingTeacherLocation option").count(), 8, "Invalid source is removed, not navigable");
  assert.equal(await page.locator("#readingTeacherLocation").inputValue(), "");
  assert.match(await page.locator("#readingTeacherStatus").innerText(), /引用失效/);
  assert.deepEqual(errors, []);
});

test("scholarly reader keeps readable text, stable note widths, and accessible controls across viewport sizes", { timeout: 45000 }, async t => {
  const fixture = await fixtureServer();
  const paper = fixture.papers.get("A");
  paper.metadata.title = "Reading Together: Evidence, Interpretation, and Annotations";
  paper.metadata.authors = "Alex Reader and Lin Chen";
  paper.metadata.venue = "Reading Systems";
  paper.takeaway_doc.blocks = [
    { id: "design-heading", type: "heading", text: "My reading notes", indent: 0 },
    { id: "design-thought", type: "bullet", text: "Keep the evidence separate from my interpretation.", indent: 0 },
  ];
  paper.segments[0].markdown = `# ${paper.metadata.title}`;
  paper.segments[1].translation = "阅读时，证据应该始终与读者选择的原文相对应。保留原始笔记，而不是用生成的总结替代读者的思考。";
  const quote = "exact words";
  const start = paper.segments[1].markdown.indexOf(quote);
  paper.annotations.annotations.push({
    id: "visual-note", segment_id: "p-0002", target: "source", color: "yellow",
    start, end: start + quote.length, quote, note: "Keep the evidence separate from my interpretation.", tags: [],
  });
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  const theme = await page.evaluate(() => {
    const style = selector => getComputedStyle(document.querySelector(selector));
    const bounds = selector => document.querySelector(selector).getBoundingClientRect();
    return {
      background: style("body").backgroundImage, toolbarBackground: style(".workspace-toolbar").backgroundImage,
      blur: style(".topbar").backdropFilter, shadow: style(".sensemaking-panel").boxShadow,
      sourceColor: style("#p-0002 .source-text").color, translationColor: style("#p-0002 .translation").color,
      paperColor: style(".content").backgroundColor, font: style("#p-0002 .source-text").fontFamily,
      sourceSize: parseFloat(style("#p-0002 .source-text").fontSize),
      translationSize: parseFloat(style("#p-0002 .translation").fontSize),
      translationBorder: style("#p-0002 .translation").borderLeftWidth,
      leftDifference: bounds("#p-0002 .translation").left - bounds("#p-0002 .source-text").left,
      widthDifference: bounds("#p-0002 .source-text").width - bounds("#p-0007 .source-text").width,
      documentWidth: bounds("#documentRoot").width,
    };
  });
  assert.equal(theme.background, "none");
  assert.equal(theme.toolbarBackground, "none");
  assert.equal(theme.blur, "none");
  assert.equal(theme.shadow, "none");
  assert.match(theme.font, /Georgia/);
  assert.ok(theme.sourceSize >= 18 && theme.translationSize >= 17.5);
  assert.equal(theme.translationBorder, "0px");
  assert.ok(Math.abs(theme.leftDifference) < 1, "Source and translation start on the same left edge");
  assert.ok(Math.abs(theme.widthDifference) < 1, "An attached note must not narrow its paragraph");
  assert.equal(await page.locator("#readerWidth").inputValue(), "wide");
  assert.ok(theme.documentWidth <= 1280);
  const luminance = color => {
    const [r, g, b] = color.match(/\d+/g).slice(0, 3).map(Number).map(value => {
      const srgb = value / 255;
      return srgb <= 0.04045 ? srgb / 12.92 : ((srgb + 0.055) / 1.055) ** 2.4;
    });
    return r * 0.2126 + g * 0.7152 + b * 0.0722;
  };
  for (const color of [theme.sourceColor, theme.translationColor]) {
    const ratio = (luminance(theme.paperColor) + 0.05) / (luminance(color) + 0.05);
    assert.ok(ratio >= 4.5, `Reading contrast ratio ${ratio.toFixed(2)} must meet WCAG AA`);
  }
  assert.equal(await page.locator("#paperMeta h1").innerText(), paper.metadata.title);
  assert.equal(await page.locator("#p-0001 h1").isVisible(), false, "Only the identical first source heading is visually deduplicated");
  assert.equal(await page.locator("#p-0002 .comment-edit").isVisible(), true);
  await page.locator("#p-0002 .comment-edit").focus();
  assert.equal(await page.locator("#p-0002 .comment-edit").evaluate(node => getComputedStyle(node).opacity), "1");
  if (process.env.READER_TEST_UI_SCREENSHOT_PREFIX) {
    await page.screenshot({ path: `${process.env.READER_TEST_UI_SCREENSHOT_PREFIX}-read.png` });
  }
  for (const width of [1440, 1100, 900, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.locator("#readerMoreActions > summary").focus();
    await page.keyboard.press("Enter");
    assert.equal(await page.locator("#paperSelect").isVisible(), true);
    for (const selector of ["#workspaceToolbar", "#readerMoreActions .reader-data-actions", "#toggleTranslationQueue"]) {
      const bounds = await page.locator(selector).boundingBox();
      assert.ok(bounds.x >= 0 && bounds.x + bounds.width <= width + 1, `${selector} overflows the ${width}px viewport`);
    }
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    await page.keyboard.press("Escape");
    assert.equal(await page.locator("#readerMoreActions").getAttribute("open"), null);
    assert.equal(await page.locator("#readerMoreActions > summary").evaluate(node => node === document.activeElement), true);
    await page.locator("#readerMoreActions > summary").click();
    await page.locator(".brand-mark").click();
    assert.equal(await page.locator("#readerMoreActions").getAttribute("open"), null);
    await page.locator('.workspace-mode[data-workspace-mode="split"]').click();
    await page.locator('[data-reader-side-pane="takeaway"]').click();
    assert.equal(await page.evaluate(() => state.workspaceMode), "split");
    assert.equal(await page.locator("#documentRoot").isVisible(), true);
    assert.equal(await page.locator("#takeawayPane").isVisible(), true);
    if (width >= 900) {
      const source = await page.locator("#documentRoot").boundingBox();
      const notes = await page.locator("#sensemakingPanel").boundingBox();
      assert.ok(notes.x >= source.x + source.width, `Split must remain side by side at ${width}px`);
    }
    if (process.env.READER_TEST_UI_SCREENSHOT_PREFIX) {
      await page.locator("#workspaceToolbar").scrollIntoViewIfNeeded();
      await page.screenshot({ path: `${process.env.READER_TEST_UI_SCREENSHOT_PREFIX}-split-${width}.png` });
    }
    await page.locator('.workspace-mode[data-workspace-mode="read"]').click();
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.evaluate(() => scrollToParagraph("p-0010"));
  await page.waitForFunction(() => {
    const top = document.getElementById("p-0010").getBoundingClientRect().top;
    return top >= document.getElementById("workspaceToolbar").getBoundingClientRect().bottom && top < 200;
  });
  assert.deepEqual(errors, []);
});

test("reading width preferences keep media controls outside figures without reloading papers", { timeout: 60000 }, async t => {
  const fixture = await fixtureServer();
  const paper = fixture.papers.get("A");
  paper.segments[5] = {
    id: "p-0006", kind: "table", markdown: "| Layout | Width |\n| --- | --- |\n| Wide | 1280px |", translation: "",
  };
  paper.annotations.annotations.push({
    id: "existing-image-note", segment_id: "p-0004", target: "media", type: "media",
    color: "blue", quote: "Figure part", note: "Keep this original image note.", tags: [],
  });
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(5000);
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
  await page.goto(fixture.url);
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  assert.equal(await page.locator("#readerWidth").inputValue(), "wide");
  assert.equal(await page.locator("#p-0003 [data-media-note]").innerText(), "Highlight + note");
  assert.equal(await page.locator("#p-0004 [data-media-note]").innerText(), "Edit note");
  await page.locator("#p-0003 img").scrollIntoViewIfNeeded();
  await page.locator("#p-0003 img").evaluate(image => image.decode());

  let layoutCases = 0;
  for (const collapsed of [false, true]) {
    if (await page.evaluate(() => state.paperMapCollapsed) !== collapsed) await page.locator("#togglePaperMapMain").click();
    for (const viewport of [390, 900, 1100, 1440, 2560]) {
      await page.setViewportSize({ width: viewport, height: 1000 });
      for (const mode of ["read", "split"]) {
        await page.locator(`.workspace-mode[data-workspace-mode="${mode}"]`).click();
        let notesWidth;
        for (const preference of ["comfortable", "wide", "full"]) {
          await page.locator("#readerWidth").selectOption(preference);
          const layout = await page.evaluate(() => {
            const root = document.querySelector("#documentRoot");
            const width = node => node.getBoundingClientRect().width;
            const media = [...root.querySelectorAll(".media-annotatable")].map(wrapper => {
              const bar = wrapper.querySelector(".media-annotation-bar");
              const button = bar.querySelector("button");
              const visual = wrapper.querySelector(".paper-figure-image, .table-wrap");
              return {
                normalFlow: getComputedStyle(bar).position === "static",
                separate: bar.getBoundingClientRect().bottom + 1 <= visual.getBoundingClientRect().top,
                contained: button.getBoundingClientRect().left >= wrapper.getBoundingClientRect().left - 1
                  && button.getBoundingClientRect().right <= wrapper.getBoundingClientRect().right + 1,
              };
            });
            return {
              available: parseFloat(getComputedStyle(document.querySelector(".reader-workspace")).gridTemplateColumns),
              document: width(root), source: width(document.querySelector("#p-0002 .source-text")),
              translation: width(document.querySelector("#p-0002 .translation")),
              notes: width(document.querySelector("#sensemakingPanel")),
              overflow: document.documentElement.scrollWidth > innerWidth + 1,
              media,
            };
          });
          const limit = { comfortable: 800, wide: 1280, full: Infinity }[preference];
          const expected = Math.min(layout.available, limit);
          const description = `${viewport}px ${mode} ${preference}, outline collapsed=${collapsed}: ${JSON.stringify(layout)}`;
          assert.ok(Math.abs(layout.document - expected) < 1, `Document width: ${description}`);
          const textWidth = expected >= 760 ? expected - 296 : expected;
          for (const key of ["source", "translation"]) assert.ok(Math.abs(layout[key] - textWidth) < 1, `${key} shares the aligned margin column: ${description}`);
          assert.equal(layout.overflow, false, description);
          assert.equal(layout.media.length, 3);
          assert.ok(layout.media.every(item => item.normalFlow && item.separate && item.contained), description);
          if (notesWidth !== undefined) assert.ok(Math.abs(layout.notes - notesWidth) < 1, `Notes width changed: ${description}`);
          notesWidth = layout.notes;
          layoutCases += 1;
        }
      }
    }
  }

  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.locator('.workspace-mode[data-workspace-mode="read"]').click();
  const source = await page.locator("#p-0002 .source-text").elementHandle();
  const paperGets = () => fixture.calls.filter(call => call.method === "GET" && call.pathname === "/api/papers/A").length;
  const getsBefore = paperGets();
  for (const preference of ["comfortable", "wide", "full"]) await page.locator("#readerWidth").selectOption(preference);
  assert.equal(await source.evaluate(node => node.isConnected), true, "Changing width preserves the source DOM and highlights");
  assert.equal(paperGets(), getsBefore, "Changing width never reloads the paper");
  await page.evaluate(() => openPaperInWorkspace("B"));
  await page.waitForFunction(() => state.currentPaperId === "B" && !state.paperLoadingId);
  assert.equal(await page.locator("#readerWidth").inputValue(), "full");
  await page.locator('[data-paper-tab="A"]').click();
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  await page.reload();
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  assert.equal(await page.locator("#readerWidth").inputValue(), "full");
  await page.locator('.workspace-mode[data-workspace-mode="think"]').click();
  assert.equal(await page.locator("#readerWidth").isDisabled(), true);
  await page.locator('.workspace-mode[data-workspace-mode="read"]').click();
  assert.equal(await page.locator("#readerWidth").isEnabled(), true);
  await page.locator("#readerWidth").focus();
  await page.keyboard.press("Home");
  assert.equal(await page.locator("#readerWidth").inputValue(), "comfortable");
  await page.locator("#readerWidth").selectOption("wide");
  await page.locator("#p-0003 [data-media-note]").click();
  await page.locator("#noteText").fill("New note without obscuring the image.");
  const saved = page.waitForResponse(response => response.url().endsWith("/api/papers/A/annotations") && response.request().method() === "POST");
  await page.locator("#saveNote").click();
  assert.equal((await saved).ok(), true);
  await page.waitForFunction(() => document.querySelector("#p-0003 [data-media-note]").textContent === "Edit note");
  assert.ok(paper.annotations.annotations.some(note => note.note === "Keep this original image note."));
  assert.ok(paper.annotations.annotations.some(note => note.note === "New note without obscuring the image."));
  const separation = await page.locator("#p-0003 .media-annotatable").evaluate(wrapper => (
    wrapper.querySelector(".media-annotation-bar").getBoundingClientRect().bottom
      < wrapper.querySelector(".paper-figure-image").getBoundingClientRect().top
  ));
  assert.equal(separation, true, "The saved-note action remains outside the image");
  if (process.env.READER_TEST_UI_SCREENSHOT_PREFIX) {
    await page.locator("#p-0003").scrollIntoViewIfNeeded();
    await page.screenshot({ path: `${process.env.READER_TEST_UI_SCREENSHOT_PREFIX}-width.png` });
  }
  await page.evaluate(() => localStorage.setItem("paperReader.readerWidth", "invalid"));
  await page.reload();
  await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
  assert.equal(await page.locator("#readerWidth").inputValue(), "wide");
  await page.evaluate(() => {
    const original = Storage.prototype.setItem;
    Storage.prototype.setItem = function (key, value) {
      if (key === "paperReader.readerWidth") throw new DOMException("Synthetic storage failure", "QuotaExceededError");
      return original.call(this, key, value);
    };
  });
  await page.locator("#readerWidth").selectOption("comfortable");
  assert.equal(await page.locator("#documentRoot").getAttribute("data-reader-width"), "comfortable");
  assert.match(await page.locator("#toast").innerText(), /could not be saved/);
  assert.deepEqual(errors, []);
  t.diagnostic(`${layoutCases} viewport/mode/width/outline combinations; original and translated text share the exact available width after the annotation margin.`);
});

test("reader opening and warm switching remain bounded without additional font or library requests", { timeout: 45000 }, async t => {
  const fixture = await fixtureServer();
  const browser = await chromium.launch({ channel: process.env.READER_BROWSER_CHANNEL || "msedge", headless: true });
  t.after(async () => {
    await browser.close();
    await new Promise(resolve => fixture.server.close(resolve));
  });
  const cold = [], warm = [], requests = [];
  for (let run = 0; run < 3; run += 1) {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    page.on("request", request => requests.push({ url: request.url(), type: request.resourceType() }));
    await page.route("**/*", route => route.request().url().startsWith(fixture.url) ? route.continue() : route.abort());
    const start = performance.now();
    await page.goto(fixture.url);
    await page.waitForFunction(() => state.currentPaperId === "A" && !state.paperLoadingId);
    cold.push(performance.now() - start);
    await page.evaluate(() => openPaperInWorkspace("B"));
    const bodyGets = () => fixture.calls.filter(call => call.method === "GET" && /^\/api\/papers\/[AB]$/.test(call.pathname)).length;
    const before = bodyGets();
    for (const id of ["A", "B", "A"]) {
      const switchStart = performance.now();
      await page.evaluate(id => openPaperInWorkspace(id), id);
      await page.waitForFunction(id => state.currentPaperId === id && !state.paperLoadingId, id);
      warm.push(performance.now() - switchStart);
    }
    assert.equal(bodyGets(), before, "Warm switches must not fetch paper bodies again");
    await page.close();
  }
  const median = values => [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)];
  assert.ok(median(cold) < 4000, `Cold opening median ${median(cold).toFixed(0)}ms exceeds 4s`);
  assert.ok(median(warm) < 1500, `Warm switch median ${median(warm).toFixed(0)}ms exceeds 1.5s`);
  assert.deepEqual(requests.filter(request => request.type === "font" || !request.url.startsWith(fixture.url)), []);
  const scripts = [...new Set(requests.filter(request => request.type === "script").map(request => new URL(request.url).pathname))];
  assert.deepEqual(scripts.sort(), ["/app.js", "/vendor/katex/katex.min.js"]);
  t.diagnostic(`240-segment fixture: cold median ${median(cold).toFixed(0)}ms (3 samples); warm median ${median(warm).toFixed(0)}ms (9 samples); no added font requests, scripts, or warm body GETs.`);
});
