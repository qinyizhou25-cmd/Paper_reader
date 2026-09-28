const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");
const { spawnSync } = require("node:child_process");

const source = fs.readFileSync(path.join(__dirname, "..", "web", "app.js"), "utf8");
const bootstrap = source.lastIndexOf('document.body.dataset.activeView = "reader";');
assert.ok(bootstrap > 0, "The test must exclude application bootstrap, not application functions.");

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

function payload(id) {
  return {
    metadata: { id, title: id, processing_mode: "deep", processing_status: "ready" },
    segments: [{ id: "p-0001", markdown: "Original source", translation: "Original translation" }],
    annotations: { annotations: [] },
    thinking: { blocks: [], annotations: [], explain: { content: "" } },
    takeaway_doc: { blocks: [] },
    reading_progress: { segments: {}, summary: {} },
  };
}

function app(api = async () => ({}), { deferTeacher = false } = {}) {
  const storage = new Map();
  const messages = [];
  const animationFrames = [];
  const idleCallbacks = [];
  const context = vm.createContext({
    console: { error: (...args) => messages.push(args), warn: (...args) => messages.push(args) },
    setTimeout, clearTimeout, setInterval, clearInterval, performance, URL, Blob,
    localStorage: { getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value) },
    document: {
      body: { dataset: { activeView: "reader" } },
      activeElement: null,
      querySelector: () => null,
      querySelectorAll: () => [],
    },
    window: { scrollY: 0, confirm: () => false, requestIdleCallback: callback => idleCallbacks.push(callback) },
    requestAnimationFrame: callback => deferTeacher ? animationFrames.push(callback) : callback(),
    testApi: api,
  });
  vm.runInContext(source.slice(0, bootstrap), context);
  vm.runInContext(`
    api = testApi;
    const readerNode = { inert: false };
    qs = selector => selector === "#readerView" ? readerNode : null;
    toast = () => {};
    renderPaperTabs = renderPaperSelect = renderSidebar = renderReader = () => {};
    refreshReadingTeacher = () => {};
    ${deferTeacher ? "" : "scheduleReadingTeacher = paperId => loadReadingTeacher(paperId);"}
    setWorkspaceMode = mode => { state.workspaceMode = mode; };
    setReaderSidePane = () => {};
    renderPresentationPanel = () => {};
    saveWorkspaceScrollPosition = restoreWorkspaceScrollPosition = () => {};
    disconnectReadingProgressTracker = tickReadingProgress = () => {};
    flushReadingProgress = async () => {};
    closeDrawer = closeFigureModal = closeReferenceModal = () => {};
    noteDrawerHasChanges = () => false;
    state.library = { papers: ["A", "B", "C"].map(id => ({ id, title: id, updated_at: "1" })) };
  `, context);
  return {
    run: code => vm.runInContext(code, context),
    json: code => JSON.parse(vm.runInContext(`JSON.stringify(${code})`, context)),
    advanceFrame: () => animationFrames.splice(0).forEach(callback => callback()),
    runIdle: () => idleCallbacks.splice(0).forEach(callback => callback()),
    storage,
    messages,
  };
}

test("Feishu intake separates full-text readiness, queued parsing, failure and saved skim", () => {
  const reader = app();
  const cases = [
    [null, "unparsed"],
    [{ processing_mode: "library-only", processing_status: "not_processed" }, "unparsed"],
    [{ processing_mode: "deep", processing_status: "processing_queued" }, "queued"],
    [{ processing_mode: "deep", processing_status: "processing" }, "processing"],
    [{ processing_mode: "deep", processing_status: "failed" }, "failed"],
    [{ processing_mode: "skim", processing_status: "ready" }, "unparsed"],
    [{ processing_mode: "deep", processing_status: "ready", translation_status: "processing" }, "ready"],
    [{ processing_mode: "deep", processing_status: "ready", translation_status: "failed" }, "ready"],
  ];
  for (const [paper, expected] of cases) {
    reader.run(`state.feishuIntake.localPaper = ${JSON.stringify(paper)};`);
    assert.equal(reader.run("feishuIntakePhase()"), expected, JSON.stringify(paper));
  }
});

function equationDisplayCases() {
  return [
    ["$$x=y\\tag{1}$$", "$$x=y\\tag{1}$$", ""],
    ["\\[x=y\\]", "$x = y$", ""],
    ["$x=y$", "\\(x=y\\)", ""],
    ["$$x=y$$ (1)", "$$x=y$$ (1)", ""],
    ["$$x=y$$", "$$x=y$$\nwhere $x$ is a score.", "\nwhere $x$ is a score."],
    ["Text. $$x=y$$ More text.", "Translated. \\[ x = y \\] More translated text.", "Translated.  More translated text."],
    ["Text. $$x=y$$ More text.", "$x=y$", ""],
    ["$$x=y$$", "$$x=y$$\n(1)\nExplanation.", "\nExplanation."],
    ["Text. $$x=y$$", "Text. $$x=z$$", "Text. $$x=z$$"],
    ["Use $x$ in the method.", "Use $x$ in the translation.", "Use $x$ in the translation."],
    ["The price is $5 or $10.", "The price is $5 or $10.", "The price is $5 or $10."],
    ["$5 - $10", "$5 - $10", "$5 - $10"],
    ["Literal \\$5 and \\$10", "Literal \\$5 and \\$10", "Literal \\$5 and \\$10"],
    ["Unclosed $$x=y", "Unclosed $$x=y", "Unclosed $$x=y"],
    ["Code `$$x=y$$`", "Code `$$x=y$$`", "Code `$$x=y$$`"],
    ["```tex\n$$x=y$$\n```", "```tex\n$$x=y$$\n```", "```tex\n$$x=y$$\n```"],
    ["```tex\n$$x=y$$", "```tex\n$$x=y$$", "```tex\n$$x=y$$"],
    ["Unclosed code ` $$x=y$$", "Unclosed code ` $$x=y$$", "Unclosed code ` $$x=y$$"],
    ["\\begin{align}x&=y\\end{align}", "\\begin{align}x&=y\\end{align}", ""],
    ["$$x=y$$", "$$x=y$$", "$$x=y$$", "code"],
  ];
}

test("translated equations are hidden without removing prose, inline notation, code or prices", () => {
  const reader = app();
  for (const [markdown, translation, expected, kind] of equationDisplayCases()) {
    assert.equal(reader.run(`translationPresentation(${JSON.stringify({ markdown, translation, kind })}).text`), expected, markdown);
  }
});

test("browser and Python reading exports agree on which equations to omit", { skip: !process.env.READER_TEST_PYTHON }, () => {
  const cases = equationDisplayCases();
  const result = spawnSync(process.env.READER_TEST_PYTHON, ["-X", "utf8", "-B", "-c",
    "import json,sys; import paper_reader_agent as r; cases=json.load(sys.stdin); json.dump([r.translation_text_for_segment({'markdown':c[0],'translation':c[1],'kind':c[3] if len(c)>3 else 'paragraph'}) for c in cases],sys.stdout)"],
  { cwd: path.resolve(__dirname, ".."), input: JSON.stringify(cases), encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr || result.error?.message);
  const outputs = JSON.parse(result.stdout);
  const normalize = text => text.replace(/\s+/g, " ").trim();
  cases.forEach(([source, , expected], index) => assert.equal(normalize(outputs[index]), normalize(expected), source));
});

test("equation display maps old and new highlight offsets without changing stored translations", () => {
  const reader = app();
  const translation = "Before. $$x=y$$ After. $x$ remains inline.";
  const segment = { id: "equation", markdown: "Before. $$x=y$$ After.", translation };
  reader.run(`const equationSegment = ${JSON.stringify(segment)};`);
  const presentation = reader.json("translationPresentation(equationSegment)");
  const originalStart = translation.indexOf("After.");
  const displayedStart = presentation.text.indexOf("After.");
  assert.equal(reader.run(`originalTranslationOffset(equationSegment, ${displayedStart}, "start")`), originalStart);
  assert.equal(reader.run(`originalTranslationOffset(equationSegment, ${displayedStart + 6}, "end")`), originalStart + 6);
  const projected = reader.json(`annotationDisplayRanges(equationSegment.translation, [
    { id: "old-note", target: "translation", range: { start: ${originalStart}, end: ${originalStart + 6} } },
    { id: "formula-note", target: "translation", range: { start: 8, end: 15 } }
  ], "translation", translationPresentation(equationSegment).omissions)`);
  assert.equal(projected.ranges.length, 1);
  assert.equal(projected.text.slice(projected.ranges[0].range.start, projected.ranges[0].range.end), "After.");
  assert.equal(reader.run("equationSegment.translation"), translation);
});

test("saved definitions render from their own snapshots and preserve legacy or edited notes", () => {
  const reader = app();
  reader.run(`
    const savedCard = { id: "term", title: "Reliance", anchor: { segment_id: "p-1", quote: "reliance" },
      definition: { paper_kind: "usage", paper: "Paper usage.", external: [{ kind: "ai-summary", summary: "General meaning." }] } };
    const initialNote = teacherDefinitionNote(savedCard, { sources: [] });
    const savedAnnotation = { id: "saved-term", segment_id: "p-1", note: initialNote,
      origin: { kind: "reading-teacher", content_type: "definition", card_id: "term",
        anchor: savedCard.anchor, definition: savedCard.definition, sources: [] } };
  `);
  assert.equal(reader.run("savedDefinitionView(savedAnnotation).pristine"), true, "Existing notes need no migration");
  reader.run('savedAnnotation.origin.initial_note = initialNote; savedAnnotation.origin.title = "Reliance"; state.readingTeacher.data = { cards: [{ ...savedCard, definition: { paper: "New AI wording" } }] };');
  assert.equal(reader.run("savedDefinitionView(savedAnnotation).card.definition.paper"), "Paper usage.");
  assert.equal(reader.run("savedDefinitionView(savedAnnotation).pristine"), true, "New teacher wording cannot replace the accepted snapshot");
  reader.run('savedAnnotation.note = "  My edited meaning.\\nKeep this exactly.\\n";');
  assert.equal(reader.run("savedDefinitionView(savedAnnotation).pristine"), false);
  assert.equal(reader.run("savedAnnotation.note"), "  My edited meaning.\nKeep this exactly.\n");
  reader.run('savedAnnotation.note = "";');
  assert.equal(reader.run("savedDefinitionView(savedAnnotation).pristine"), false, "An empty edit must not resurrect the AI text");
});

test("a slow teacher never blocks source or leaks across paper tabs", async () => {
  const teacherResponse = deferred();
  const calls = [];
  const reader = app(async url => {
    calls.push(url);
    if (url.endsWith("/reading-teacher")) return teacherResponse.promise;
    if (url.endsWith("/references")) return { references: {} };
    const id = url.split("/").pop();
    return { ...payload(id), teacher_available: id === "A" };
  });
  await reader.run('loadPaper("A")');
  assert.equal(reader.run("state.currentPaperId"), "A");
  assert.equal(reader.run("state.readingTeacher.loading"), true);
  await reader.run('loadPaper("B")');
  teacherResponse.resolve({ paper_id: "A", teacher: { id: "A-teacher", cards: [], issues: [] } });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(reader.run("state.currentPaperId"), "B");
  assert.equal(reader.run("state.readingTeacher.data"), null);
  assert.equal(reader.run('state.paperSessions.get("A").readingTeacher.data.id'), "A-teacher");
  assert.equal(calls.filter(url => url.endsWith("/reading-teacher")).length, 1);
});

test("teacher loading waits for a source paint and idle time without duplicate requests", async () => {
  let teacherCalls = 0;
  const reader = app(async url => {
    if (url.endsWith("/reading-teacher")) {
      teacherCalls += 1;
      return { paper_id: "A", teacher: { id: "A-teacher", cards: [], issues: [] } };
    }
    if (url.endsWith("/references")) return { references: {} };
    return { ...payload("A"), teacher_available: true };
  }, { deferTeacher: true });
  await reader.run('loadPaper("A")');
  assert.equal(reader.run("state.currentPaperId"), "A");
  assert.equal(reader.run("state.readingTeacher.scheduled"), true);
  assert.equal(teacherCalls, 0);
  reader.run('scheduleReadingTeacher("A")');
  reader.advanceFrame();
  reader.runIdle();
  assert.equal(teacherCalls, 0, "Leave the first frame available for source rendering.");
  reader.advanceFrame();
  assert.equal(teacherCalls, 0, "Do not load until the deferred idle callback.");
  reader.runIdle();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(teacherCalls, 1);
  assert.equal(reader.run("state.readingTeacher.data.id"), "A-teacher");
  reader.run('scheduleReadingTeacher("A")');
  reader.advanceFrame();
  reader.advanceFrame();
  reader.runIdle();
  assert.equal(teacherCalls, 1, "Cached teacher data does not schedule another request.");
});

test("a scheduled teacher is cancelled on tab switch and retried when returning", async () => {
  let teacherCalls = 0;
  const reader = app(async url => {
    if (url.endsWith("/reading-teacher")) {
      teacherCalls += 1;
      return { paper_id: "A", teacher: { id: "A-teacher", cards: [], issues: [] } };
    }
    if (url.endsWith("/references")) return { references: {} };
    const id = url.split("/").pop();
    return { ...payload(id), teacher_available: id === "A" };
  }, { deferTeacher: true });
  await reader.run('loadPaper("A")');
  await reader.run('loadPaper("B")');
  reader.advanceFrame();
  reader.advanceFrame();
  reader.runIdle();
  assert.equal(teacherCalls, 0);
  assert.equal(reader.run("state.readingTeacher.data"), null);
  assert.equal(reader.run('state.paperSessions.get("A").readingTeacher.scheduled'), false);
  await reader.run('loadPaper("A")');
  reader.advanceFrame();
  reader.advanceFrame();
  reader.runIdle();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(teacherCalls, 1);
  assert.equal(reader.run("state.readingTeacher.data.id"), "A-teacher");
});

test("forced reload cancels a teacher scheduled for the older source", async () => {
  let teacherCalls = 0;
  const reader = app(async url => {
    if (url.endsWith("/reading-teacher")) {
      teacherCalls += 1;
      return { paper_id: "A", teacher: { id: "current-teacher", cards: [], issues: [] } };
    }
    if (url.endsWith("/references")) return { references: {} };
    return { ...payload("A"), teacher_available: true };
  }, { deferTeacher: true });
  await reader.run('loadPaper("A")');
  reader.run("window.oldTeacher = state.readingTeacher;");
  await reader.run('loadPaper("A", { force: true })');
  reader.advanceFrame();
  reader.advanceFrame();
  reader.runIdle();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(teacherCalls, 1);
  assert.equal(reader.run("window.oldTeacher.data"), null);
  assert.equal(reader.run("window.oldTeacher.scheduled"), false);
  assert.equal(reader.run("state.readingTeacher.data.id"), "current-teacher");
});

test("a scheduled teacher resumes after the attempted next paper fails to open", async () => {
  const otherPaper = deferred();
  const otherStarted = deferred();
  let teacherCalls = 0;
  const reader = app(async url => {
    if (url.endsWith("/reading-teacher")) {
      teacherCalls += 1;
      return { paper_id: "A", teacher: { id: "kept-teacher", cards: [], issues: [] } };
    }
    if (url.endsWith("/references")) return { references: {} };
    if (url.endsWith("/B")) { otherStarted.resolve(); return otherPaper.promise; }
    return { ...payload("A"), teacher_available: true };
  }, { deferTeacher: true });
  await reader.run('loadPaper("A")');
  const switching = reader.run('loadPaper("B")');
  await otherStarted.promise;
  reader.advanceFrame();
  reader.advanceFrame();
  reader.runIdle();
  assert.equal(teacherCalls, 0);
  otherPaper.reject(new Error("Cannot open B"));
  await switching;
  assert.equal(reader.run("state.currentPaperId"), "A");
  reader.advanceFrame();
  reader.advanceFrame();
  reader.runIdle();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(teacherCalls, 1);
  assert.equal(reader.run("state.readingTeacher.data.id"), "kept-teacher");
});

test("accepted teacher definitions do not masquerade as independent human reflection", () => {
  const reader = app();
  reader.run(`state.annotations = ["definition-one", "definition-two"].map(id => ({
    id, segment_id: "p-0001", note: "AI definition",
    origin: { kind: "reading-teacher", content_type: "definition" },
  }));`);
  assert.deepEqual(reader.json('readingAnnotationCounts("p-0001")'), { highlight_count: 0, note_count: 0 });
  assert.equal(reader.run('readingProgressForSegment("p-0001").state'), "unread");
  reader.run(`state.annotations.push({ id: "my-response", segment_id: "p-0001", note: "My own thought",
    teacher_prompt: { card_id: "definition" } });`);
  assert.deepEqual(reader.json('readingAnnotationCounts("p-0001")'), { highlight_count: 1, note_count: 1 });
});

test("forced reload rejects a teacher response for an older source session", async () => {
  const oldResponse = deferred();
  let teacherCalls = 0;
  const reader = app(async url => {
    if (url.endsWith("/reading-teacher")) {
      teacherCalls += 1;
      return teacherCalls === 1 ? oldResponse.promise : { paper_id: "A", teacher: { id: "new-teacher", cards: [], issues: [] } };
    }
    if (url.endsWith("/references")) return { references: {} };
    return { ...payload("A"), teacher_available: true };
  });
  await reader.run('loadPaper("A")');
  await reader.run('loadPaper("A", { force: true })');
  oldResponse.resolve({ paper_id: "A", teacher: { id: "old-teacher", cards: [], issues: [] } });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(reader.run("state.readingTeacher.data.id"), "new-teacher");
});

test("a teacher completed during a failed tab switch is displayed on the kept paper", async () => {
  const teacherResponse = deferred();
  const otherPaper = deferred();
  const otherStarted = deferred();
  const reader = app(async url => {
    if (url.endsWith("/reading-teacher")) return teacherResponse.promise;
    if (url.endsWith("/references")) return { references: {} };
    if (url.endsWith("/B")) { otherStarted.resolve(); return otherPaper.promise; }
    return { ...payload("A"), teacher_available: true };
  });
  reader.run('refreshReadingTeacher = () => { window.renderedTeacher = state.readingTeacher.data?.id; state.readingTeacher.needsRefresh = false; };');
  await reader.run('loadPaper("A")');
  const switching = reader.run('loadPaper("B")');
  await otherStarted.promise;
  teacherResponse.resolve({ paper_id: "A", teacher: { id: "kept-teacher", cards: [], issues: [] } });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(reader.run("window.renderedTeacher"), undefined);
  otherPaper.reject(new Error("Cannot open B"));
  await switching;
  assert.equal(reader.run("state.currentPaperId"), "A");
  assert.equal(reader.run("window.renderedTeacher"), "kept-teacher");
});

test("unsubmitted AI composer drafts survive cache pressure and trigger the unsaved warning", () => {
  const reader = app();
  reader.run(`
    state.currentPaperId = "B";
    paperSession("A").manualOutputDraft = { prompt: "", content: "Keep the pasted draft exactly." };
    for (let index = 0; index < 10; index += 1) paperSession("clean-" + index);
    prunePaperCache();
  `);
  assert.equal(reader.run("state.paperSessions.size"), 8);
  assert.equal(reader.run('state.paperSessions.get("A").manualOutputDraft.content'), "Keep the pasted draft exactly.");
  assert.equal(reader.run("hasUnsavedPaperChanges()"), true);
  reader.run('state.paperSessions.get("A").manualOutputDraft.content = "";');
  assert.equal(reader.run("hasUnsavedPaperChanges()"), false);
  reader.run('state.chatDraft = "My unsent question";');
  assert.equal(reader.run("hasUnsavedPaperChanges()"), true);
});

test("figure indexing retains every adjacent part and does not bridge unrelated prose", () => {
  const reader = app();
  reader.run('state.currentPaperId = "A";');
  const figures = reader.json(`buildFigureIndex([
    { id: "p-0001", markdown: "![](one.png)\\n![](two.png)" },
    { id: "p-0002", markdown: "![](three.png)" },
    { id: "p-0003", markdown: "Figure 1: Three panels." },
    { id: "p-0004", markdown: "![](unrelated.png)" },
    { id: "p-0005", markdown: "An unrelated paragraph." },
    { id: "p-0006", markdown: "Figure 2: Missing image." }
  ])`);
  assert.equal(figures["1"].images.length, 3);
  assert.deepEqual(figures["1"].image_segment_ids, ["p-0001", "p-0002"]);
  assert.equal(figures["2"].images.length, 0);
});

test("translation rendering suppresses image copies while preserving raw caption highlight offsets", () => {
  const reader = app();
  reader.run(`
    state.currentPaperId = "A";
    const mixed = {
      id: "p-0001", kind: "paragraph",
      markdown: "Original prose. ![](figure.png) Figure 2: Workflow.",
      translation: "前文说明。 ![](figure.png) 图2：工作流程。"
    };
    state.payload = { metadata: { id: "A" }, segments: [mixed] };
  `);
  const rendered = reader.run("paragraphHtml(mixed)");
  assert.equal((rendered.match(/<img /g) || []).length, 1);
  reader.run(`
    const quote = "图2：工作流程。";
    const start = displayTextPreservingMath(mixed.translation, { trim: false }).indexOf(quote);
    state.annotations = [{ id: "caption-note", segment_id: mixed.id, target: "translation", quote,
      note: "My original question", color: "yellow", range: { start, end: start + quote.length } }];
  `);
  const caption = reader.run(`applyHighlights(displayTextPreservingMath(mixed.translation, { trim: false }), mixed.id, "translation")`);
  assert.match(caption, /data-annotation-id="caption-note"[^>]*>图2：工作流程。<\/mark>/);
  assert.ok(!caption.includes("<img"));
  assert.equal(reader.run("mixed.translation"), "前文说明。 ![](figure.png) 图2：工作流程。");
  const imageOnly = reader.run(`paragraphHtml({ id: "p-0002", markdown: "![](scan.jpg)", translation: "![](scan.jpg)" })`);
  assert.equal((imageOnly.match(/<img /g) || []).length, 1);
  assert.ok(!imageOnly.includes('class="translation'));
  const scannedTable = reader.run(`paragraphHtml({ id: "p-0003", kind: "table",
    markdown: "![](scan.jpg) Table 1: Source caption.",
    translation: "![](scan.jpg) 表1：中文图注。" })`);
  assert.equal((scannedTable.match(/<img /g) || []).length, 1);
  assert.ok(!scannedTable.includes("中文表格"));
  assert.ok(scannedTable.includes("表1：中文图注。"));
});

test("opening a paper does not wait for references or request all-library notes", async () => {
  const references = deferred();
  const calls = [];
  const reader = app(async url => {
    calls.push(url);
    return url.endsWith("/references") ? references.promise : payload("A");
  });
  assert.equal(await reader.run('loadPaper("A")'), true);
  assert.equal(reader.run("state.currentPaperId"), "A");
  assert.ok(!calls.includes("/api/notes"));
  assert.deepEqual(calls, ["/api/papers/A", "/api/papers/A/references"]);
  references.resolve({ references: { 1: { number: "1" } } });
});

test("warm paper switches reuse data and restore per-paper mode and state", async () => {
  const calls = [];
  const reader = app(async url => {
    calls.push(url);
    return url.endsWith("/references") ? { references: {} } : payload(url.split("/").pop());
  });
  await reader.run('loadPaper("A")');
  reader.run('state.workspaceMode = "split"; state.chatDraft = "My unsubmitted question";');
  await reader.run('loadPaper("B")');
  assert.equal(reader.run("state.chatDraft"), "");
  await reader.run('loadPaper("A")');
  assert.equal(reader.run("state.workspaceMode"), "split");
  assert.equal(reader.run("state.chatDraft"), "My unsubmitted question");
  assert.equal(calls.filter(url => url === "/api/papers/A").length, 1);
  assert.deepEqual(reader.json("state.paperTabs"), ["A", "B"]);
});

test("composer drafts survive closing a paper tab and an expired source cache", async () => {
  const calls = [];
  const reader = app(async url => {
    calls.push(url);
    return url.endsWith("/references") ? { references: {} } : payload(url.split("/").pop());
  });
  await reader.run('loadPaper("A")');
  reader.run(`
    state.chatDraft = "My unsent question";
    state.thinkingComposerMode = "paste";
    state.manualOutputDraft = { prompt: "  Original question  ", content: "  Original output\\n" };
  `);
  await reader.run('loadPaper("B")');
  await reader.run('closePaperTab("A")');
  assert.deepEqual(reader.json("state.paperTabs"), ["B"]);
  assert.equal(reader.run("hasUnsavedPaperChanges()"), true);
  reader.run('paperSession("A").loadedAt = 0;');
  await reader.run('loadPaper("A")');
  assert.equal(calls.filter(url => url === "/api/papers/A").length, 2);
  assert.equal(reader.run("state.chatDraft"), "My unsent question");
  assert.equal(reader.run("state.thinkingComposerMode"), "paste");
  assert.deepEqual(reader.json("state.manualOutputDraft"), { prompt: "  Original question  ", content: "  Original output\n" });
});

test("chat history position and reply failures are isolated per paper without changing reading records", async () => {
  const reader = app(async url => url.endsWith("/references") ? { references: {} } : payload(url.split("/").pop()));
  await reader.run('loadPaper("A")');
  reader.run(`
    state.chatScroll = { top: 240, atEnd: false };
    state.chatError = "Reply unavailable";
    state.chatDraft = "An unsent follow-up";
  `);
  await reader.run('loadPaper("B")');
  assert.deepEqual(reader.json("state.chatScroll"), { top: 0, atEnd: true });
  assert.equal(reader.run("state.chatError"), "");
  reader.run('state.chatScroll = { top: 560, atEnd: false };');
  await reader.run('loadPaper("A")');
  assert.deepEqual(reader.json("state.chatScroll"), { top: 240, atEnd: false });
  assert.equal(reader.run("state.chatError"), "Reply unavailable");
  assert.equal(reader.run("state.chatDraft"), "An unsent follow-up");
  assert.equal(reader.run('"chatScroll" in state.thinking || "chatError" in state.thinking'), false);
  assert.equal(reader.run('"chatScroll" in state.payload || "chatError" in state.payload'), false);
});

test("the unsaved warning uses current composer state rather than its stale cached copy", async () => {
  const reader = app(async url => url.endsWith("/references") ? { references: {} } : payload("A"));
  await reader.run('loadPaper("A")');
  reader.run(`
    state.chatDraft = "An old unsent question";
    state.manualOutputDraft = { prompt: "", content: "A response to save" };
    capturePaperSession();
    state.chatDraft = "";
    state.manualOutputDraft = { prompt: "", content: "" };
  `);
  assert.equal(reader.run("hasUnsavedPaperChanges()"), false);
});

test("an older slow response cannot replace the paper most recently requested", async () => {
  const slow = deferred();
  const started = deferred();
  const reader = app(async url => {
    if (url.endsWith("/references")) return { references: {} };
    if (url === "/api/papers/B") { started.resolve(); return slow.promise; }
    return payload(url.split("/").pop());
  });
  await reader.run('loadPaper("A")');
  const oldRequest = reader.run('loadPaper("B")');
  await started.promise;
  assert.equal(await reader.run('loadPaper("C")'), true);
  slow.resolve(payload("B"));
  assert.equal(await oldRequest, false);
  assert.equal(reader.run("state.currentPaperId"), "C");
  assert.equal(reader.run("state.payload.metadata.id"), "C");
});

test("writes are serialized per paper and snapshot data before the next edit", async () => {
  const first = deferred();
  const calls = [];
  const reader = app(async (url, options) => {
    calls.push({ url, body: JSON.parse(options.body) });
    if (calls.length === 1) return first.promise;
    return { ok: true };
  });
  const one = reader.run('queuePaperWrite("A", "annotations", { annotations: [{ note: "first" }] })');
  const two = reader.run('queuePaperWrite("A", "annotations", { annotations: [{ note: "second" }] })');
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(calls.length, 1);
  first.resolve({ ok: true });
  await Promise.all([one, two]);
  assert.deepEqual(calls.map(call => call.body.annotations[0].note), ["first", "second"]);
  assert.equal(reader.run('paperSession("A").writes.get("annotations").dirty'), false);
});

test("failed saves keep the current paper and can be explicitly retried", async () => {
  let fail = true;
  const reader = app(async (url, options) => {
    if (url.endsWith("/thinking")) {
      if (fail) throw new Error("disk is unavailable");
      return { thinking: JSON.parse(options.body) };
    }
    return url.endsWith("/references") ? { references: {} } : payload(url.split("/").pop());
  });
  await reader.run('loadPaper("A")');
  reader.run('state.thinking.annotations.push({ id: "note", note: "Do not lose this", block_id: "paper-brief" }); state.thinkingDirty = true;');
  assert.equal(await reader.run('loadPaper("B")'), false);
  assert.equal(reader.run("state.currentPaperId"), "A");
  assert.equal(reader.run("state.thinking.annotations[0].note"), "Do not lose this");
  assert.equal(reader.run('paperSession("A").writes.get("thinking").dirty'), true);
  fail = false;
  assert.equal(await reader.run('loadPaper("B")'), true);
  assert.equal(reader.run('paperSession("A").thinking.annotations[0].note'), "Do not lose this");
});

test("forced reload reads external edits rather than restoring the old payload", async () => {
  let version = 1;
  const reader = app(async url => {
    if (url.endsWith("/references")) return { references: {} };
    const data = payload("A");
    data.segments[0].translation = `version ${version}`;
    return data;
  });
  await reader.run('loadPaper("A")');
  version = 2;
  await reader.run('loadPaper("A", { force: true })');
  assert.equal(reader.run("state.payload.segments[0].translation"), "version 2");
});

test("thinking normalization preserves verbatim notes, unknown provenance, and orphan annotations", () => {
  const reader = app();
  const result = reader.json(`normalizeThinkingData({
    explain: { content: "" }, blocks: [],
    annotations: [{ id: "original", block_id: "old-block", note: "  My words\\nexactly  ", source_author: "human" }]
  })`);
  assert.equal(result.explain.content, "");
  assert.equal(result.annotations[0].note, "  My words\nexactly  ");
  assert.equal(result.annotations[0].source_author, "human");
  assert.equal(result.annotations[0].block_id, "old-block");
});

test("reading never fabricates a brief when none was saved", () => {
  const reader = app();
  reader.run('state.thinking = { explain: { content: "" }, annotations: [] };');
  assert.equal(reader.run("paperBriefCardHtml()"), "");
  reader.run('state.thinking.explain.content = "An existing saved explanation.";');
  assert.match(reader.run("paperBriefCardHtml()"), /An existing saved explanation/);
  assert.match(reader.run("paperBriefCardHtml()"), /<details class="paper-brief-card"/);
});

test("only the open tab list and view positions are restored; notes are not stored in tab preferences", async () => {
  const reader = app(async url => url.endsWith("/references") ? {} : payload("A"));
  await reader.run('loadPaper("A")');
  reader.run('state.workspaceScrollByPaper.A = 750; persistPaperTabs(); state.paperTabs = []; state.currentPaperId = null; restorePaperTabs();');
  assert.deepEqual(reader.json("state.paperTabs"), ["A"]);
  assert.equal(reader.run("state.currentPaperId"), "A");
  assert.equal(reader.run("state.workspaceScrollByPaper.A"), 750);
  const saved = JSON.parse(reader.storage.get("paperReader.openPapers.v1"));
  assert.deepEqual(Object.keys(saved).sort(), ["active", "anchors", "modes", "positions", "tabs"]);
});

test("translation updates never leak into another tab or overwrite changed source", () => {
  const reader = app();
  reader.run(`
    state.currentPaperId = "B";
    state.payload = { segments: [{ id: "p-1", markdown: "B source", translation: "" }] };
    paperSession("A").payload = {
      segments: [{ id: "p-1", markdown: "A source", translation: "", custom: true }],
      annotations: { annotations: [{ note: "Keep my words." }] }
    };
    applyTranslationResponse("A", { paper_id: "A", translation: { status: "processing", revision: 1, job_id: "a" },
      updates: [{ id: "p-1", markdown: "A source", translation: "A translation" }] });
  `);
  assert.equal(reader.run('state.payload.segments[0].translation'), "");
  assert.equal(reader.run('paperSession("A").payload.segments[0].translation'), "A translation");
  assert.equal(reader.run('paperSession("A").payload.segments[0].custom'), true);
  assert.equal(reader.run('paperSession("A").payload.annotations.annotations[0].note'), "Keep my words.");
  reader.run(`applyTranslationResponse("A", { translation: { status: "ready", revision: 2, job_id: "a" },
    updates: [{ id: "p-1", markdown: "Different source", translation: "Do not apply" }] });`);
  assert.equal(reader.run('paperSession("A").payload.segments[0].translation'), "A translation");
  assert.equal(reader.run('translationJob("A").status'), "source_changed");
  assert.equal(reader.run('translationJob("A").cursor'), 1);
});
