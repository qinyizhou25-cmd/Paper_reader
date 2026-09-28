const state = {
  library: null,
  tagDictionary: { paper_tags: [], note_tags: [], aliases: {}, frames: [] },
  libraryUpload: { active: false, total: 0, completed: 0, files: [], message: "", error: "" },
  currentPaperId: null,
  paperTabs: [],
  paperSessions: new Map(),
  paperLoadVersion: 0,
  paperLoadingId: "",
  translationConfig: { auto_start: false },
  translationJobs: new Map(),
  readerBackgroundTimer: null,
  readerBackgroundVersion: 0,
  translationQueue: { open: false, loading: false, data: null, error: "", timer: null },
  processingQueue: { open: false, loading: false, data: null, error: "", timer: null },
  feishuConfig: { enabled: false, auto_sync: false },
  feishuIntake: { records: [], record: null, localPaper: null, fileToken: "", localPath: "", brief: "raw text_中文",
    loading: false, busy: false, error: "", statusError: "", message: "", hasMore: false, version: 0 },
  feishuSyncByPaper: new Map(),
  feishuPanelOpen: false,
  feishuPollTimer: null,
  feishuPublication: { paperId: "", title: "", version: 0, loading: false, sending: false,
    preview: null, publication: null, error: "", timer: null },
  libraryLoaded: false,
  libraryDirty: true,
  allNotesLoaded: false,
  allNotesDirty: true,
  allNotesPromise: null,
  libraryPage: 0,
  libraryFilterTimer: null,
  metadataDrafts: new Map(),
  thinkingDirty: false,
  takeawayDirty: false,
  drawerInitialValue: "",
  payload: null,
  references: {},
  figures: {},
  annotations: [],
  readingTeacher: emptyReadingTeacher(),
  expandedMarginNotes: new Set(),
  collapsedDefinitionNotes: new Set(),
  thinking: null,
  takeawayDoc: { version: 1, blocks: [], updated_at: "" },
  allNotes: [],
  allNotesRefreshTimer: null,
  pendingAnnotation: null,
  pendingThinkingAnnotation: null,
  currentSelection: null,
  referenceLoads: {},
  referenceIntakeDrafts: {},
  selectedNoteFilters: [],
  selectedNoteProjects: [],
  notesPreview: { paperId: "", annotationId: "", segmentId: "", payload: null, loading: false, error: "" },
  notesPreviewCache: new Map(),
  librarySort: "updated_at",
  libraryGroup: "none",
  libraryProject: "all",
  libraryView: "all",
  libraryDensity: "comfortable",
  libraryFilter: "",
  libraryColumnWidths: {},
  libraryViewSettings: {},
  libraryTagMenuPaperId: "",
  libraryProjectMenuPaperId: "",
  libraryPreviewThumbnailsVisible: false,
  libraryPreview: { open: false, paperId: "", payload: null, loading: false, error: "" },
  projectContexts: { version: 1, contexts: {} },
  projectContextPanel: { open: false, project: "collaborative", saving: false, error: "" },
  libraryCustomProjects: [],
  libraryIntakeTags: [],
  libraryIntakeProjects: [],
  libraryIntakeImportance: 0,
  libraryTagPrompt: { open: false, expanded: false, paperIds: [], saving: false },
  workspaceMetadataEditor: { open: false, saving: false, paperId: "", projects: [], tags: [], importance: 0 },
  canvasBoards: [],
  currentCanvasProject: "collaborative",
  currentCanvasBoardId: "",
  canvasBoard: null,
  selectedCanvasId: "",
  selectedCanvasKind: "",
  canvasToolDrag: "",
  canvasPicker: { open: false, kind: "", cardId: "", query: "" },
  canvasSync: { open: false, proposals: [], selectedIds: new Set() },
  canvasSaveTimer: null,
  canvasPanning: null,
  canvasDragging: null,
  canvasResizing: null,
  mindmaps: [],
  currentMindmapProject: "collaborative",
  currentMindmapId: "",
  mindmap: null,
  selectedMindmapNodeId: "",
  selectedMindmapNodeIds: new Set(),
  mindmapSearchResults: [],
  mindmapSearchLoading: false,
  mindmapPinnedRef: null,
  mindmapEditingNodeId: "",
  mindmapEditDraft: "",
  mindmapTypeMenuNodeId: "",
  mindmapSourceProjectFilters: [],
  mindmapSourceNoteFilters: [],
  mindmapSourceQuery: "",
  mindmapDragNodeId: "",
  mindmapSaveTimer: null,
  mindmapPanning: null,
  mindmapSelecting: null,
  mindmapSelectionDrag: null,
  libraryTitlesCollapsed: false,
  libraryTableScroll: { tableTop: 0, tableLeft: 0, rootLeft: 0, windowY: 0 },
  libraryScrollSnapshots: {},
  workspaceScrollByPaper: {},
  workspaceAnchorsByPaper: {},
  stopScrollRestore: null,
  workspaceMode: "split",
  paperMapCollapsed: false,
  paperMapTab: "map",
  collapsedOutlineIds: new Set(),
  currentOutlineId: "",
  presentationReportOpen: false,
  presentationReportItems: [],
  metadataSaveTimers: new Map(),
  thinkingSaveTimer: null,
  takeawaySaveTimer: null,
  takeawayDocVersion: 0,
  takeawaySaveInFlight: false,
  takeawaySaveQueued: false,
  takeawayAutoSaveNeeded: false,
  takeawayUndoStack: [],
  takeawayRedoStack: [],
  takeawayHistoryLimit: 80,
  takeawayHistoryRestoring: false,
  collapsedTakeawayBlockIds: new Set(),
  takeawaySelectedBlockIds: new Set(),
  takeawaySelectionMode: false,
  takeawayLastSelectedBlockId: "",
  takeawayDragBlockId: "",
  takeawayArrangePreview: null,
  thinkingTab: "writing",
  thinkingComposerMode: "chat",
  manualOutputDraft: { prompt: "", content: "" },
  chatMode: "source",
  chatDraft: "",
  chatSelectionDraft: null,
  chatUseProjectContext: false,
  chatScroll: { top: 0, atEnd: true },
  chatError: "",
  chatSending: false,
  readingNarrativeGenerating: false,
  sensemakingWidth: null,
  reportWidth: null,
  reportResizeInitialized: false,
  lastPointerPosition: null,
  presentationCollapsed: new Set(),
  presentationMenu: null,
  readingProgress: { version: 1, segments: {}, summary: {} },
  readingObserver: null,
  readingVisibleSegments: new Set(),
  readingLastTick: 0,
  readingSaveTimer: null,
  readingFlushTimer: null,
  readingProgressDirty: false,
};

const sidebarWidthStorageKey = "paperReader.sidebarWidth";
const sensemakingWidthStorageKey = "paperReader.sensemakingWidth";
const readerWidthStorageKey = "paperReader.readerWidth";
const reportWidthStorageKey = "paperReader.reportWidth";
const paperMapCollapsedStorageKey = "paperReader.paperMapCollapsed";
const libraryDensityStorageKey = "paperReader.libraryDensity";
const libraryProjectStorageKey = "paperReader.libraryProject";
const libraryViewStorageKey = "paperReader.libraryView";
const libraryViewSettingsStorageKey = "paperReader.libraryViewSettings";
const libraryColumnWidthStorageKey = "paperReader.libraryColumnWidths";
const libraryTitleCollapsedStorageKey = "paperReader.libraryTitlesCollapsed";
const libraryPreviewThumbsStorageKey = "paperReader.libraryPreviewThumbs";
const libraryCustomProjectsStorageKey = "paperReader.customProjects";
const libraryScrollStorageKey = "paperReader.libraryScrollSnapshots";
const paperTabsStorageKey = "paperReader.openPapers.v1";
const paperCacheLimit = 8;
const paperCacheMaxAge = 60000;
const libraryPageSize = 40;

const paperSessionFields = [
  "payload", "annotations", "thinking", "takeawayDoc", "references", "figures",
  "readingProgress", "readingProgressDirty", "thinkingDirty", "takeawayDirty",
  "workspaceMode", "paperMapTab", "collapsedOutlineIds", "collapsedTakeawayBlockIds",
  "takeawayUndoStack", "takeawayRedoStack", "takeawayDocVersion",
  "takeawaySelectedBlockIds", "takeawayLastSelectedBlockId", "takeawaySelectionMode",
  "chatDraft", "chatSelectionDraft", "chatMode", "chatUseProjectContext", "chatScroll", "chatError",
  "thinkingComposerMode", "manualOutputDraft",
  "thinkingTab", "presentationReportOpen", "referenceIntakeDrafts",
  "readingTeacher", "expandedMarginNotes", "collapsedDefinitionNotes",
];

function paperSession(paperId) {
  if (!state.paperSessions.has(paperId)) {
    state.paperSessions.set(paperId, { writes: new Map(), loadedAt: 0, lastUsed: Date.now() });
  }
  return state.paperSessions.get(paperId);
}

function capturePaperSession() {
  if (!state.currentPaperId || !state.payload) return;
  const session = paperSession(state.currentPaperId);
  for (const key of paperSessionFields) session[key] = state[key];
  session.payload.annotations = { ...(session.payload.annotations || {}), annotations: state.annotations };
  session.payload.thinking = state.thinking;
  session.payload.takeaway_doc = state.takeawayDoc;
  session.payload.reading_progress = state.readingProgress;
  session.lastUsed = Date.now();
}

function prunePaperCache() {
  const candidates = [...state.paperSessions.entries()]
    .filter(([id, session]) => id !== state.currentPaperId && !session.thinkingDirty && !session.takeawayDirty
      && !hasThinkingComposerDraft(session)
      && !session.readingProgressDirty && ![...session.writes.values()].some(write => write.pending || write.dirty))
    .sort((a, b) => a[1].lastUsed - b[1].lastUsed);
  while (state.paperSessions.size > paperCacheLimit && candidates.length) {
    state.paperSessions.delete(candidates.shift()[0]);
  }
}

function persistPaperTabs() {
  const positions = {};
  const modes = {};
  for (const id of state.paperTabs) {
    positions[id] = state.workspaceScrollByPaper[id] || 0;
    modes[id] = id === state.currentPaperId ? state.workspaceMode : state.paperSessions.get(id)?.workspaceMode || "read";
  }
  try {
    localStorage.setItem(paperTabsStorageKey, JSON.stringify({
      tabs: state.paperTabs, active: state.currentPaperId, positions, modes,
      anchors: Object.fromEntries(state.paperTabs.filter(id => state.workspaceAnchorsByPaper[id])
        .map(id => [id, state.workspaceAnchorsByPaper[id]])),
    }));
  } catch (error) {
    console.error("Could not persist paper tabs", error);
    toast("Tab positions could not be saved. Your saved notes are unaffected.");
  }
}

function restorePaperTabs() {
  const raw = localStorage.getItem(paperTabsStorageKey);
  if (!raw) return;
  try {
    const saved = JSON.parse(raw);
    const known = new Set((state.library?.papers || []).map(paper => paper.id));
    state.paperTabs = [...new Set((Array.isArray(saved.tabs) ? saved.tabs : []).filter(id => known.has(id)))];
    state.currentPaperId = state.paperTabs.includes(saved.active) ? saved.active : state.paperTabs[0] || null;
    for (const id of state.paperTabs) {
      const y = Number(saved.positions?.[id]);
      if (Number.isFinite(y) && y >= 0) state.workspaceScrollByPaper[id] = y;
      const anchor = saved.anchors?.[id];
      if (anchor && typeof anchor.segmentId === "string" && Number.isFinite(anchor.offset)) state.workspaceAnchorsByPaper[id] = anchor;
      if (["read", "split", "think"].includes(saved.modes?.[id])) paperSession(id).workspaceMode = saved.modes[id];
    }
  } catch (error) {
    console.error("Could not restore paper tabs", error);
    toast("Saved tabs could not be restored. Open papers from Library.");
  }
}

function renderPaperTabs() {
  const root = qs("#paperTabs");
  if (!root) return;
  const focusedId = document.activeElement?.dataset?.paperTab;
  root.innerHTML = state.paperTabs.map(id => {
    const paper = state.library?.papers?.find(item => item.id === id) || { id };
    const title = paperTitle(paper);
    const active = id === state.currentPaperId;
    return `<div class="paper-tab ${active ? "active" : ""}" role="presentation">
      <button type="button" role="tab" aria-selected="${active}" aria-controls="readerView"
        data-paper-tab="${escapeHtml(id)}" title="${escapeHtml(title)}">${escapeHtml(title)}</button>
      <button type="button" class="paper-tab-close" data-close-paper-tab="${escapeHtml(id)}"
        aria-label="Close ${escapeHtml(title)}" title="Close tab (keeps all reading data)">×</button>
    </div>`;
  }).join("");
  if (focusedId) root.querySelector(`[data-paper-tab="${cssEscape(focusedId)}"]`)?.focus({ preventScroll: true });
  const status = qs("#paperLoadStatus");
  if (status) status.textContent = state.paperLoadingId ? "Opening paper…" : state.paperTabs.length ? `${state.paperTabs.length} open` : "Open a paper from Library";
}

async function closePaperTab(paperId) {
  try {
    const index = state.paperTabs.indexOf(paperId);
    if (index < 0) return;
    if (state.paperLoadingId === paperId && state.currentPaperId !== paperId) {
      state.paperLoadVersion += 1;
      state.paperLoadingId = "";
      qs("#readerView").inert = false;
    }
    if (state.currentPaperId === paperId) {
      await flushCurrentPaperEdits();
      const next = state.paperTabs[index + 1] || state.paperTabs[index - 1];
      if (next) {
        if (!await loadPaper(next)) return;
      } else {
        state.paperLoadVersion += 1;
        disconnectReadingProgressTracker();
        capturePaperSession();
        state.currentPaperId = null;
        state.payload = null;
        state.annotations = [];
        state.thinking = null;
        state.figures = {};
        state.references = {};
        renderReader();
        renderSidebar();
        activateView("library");
      }
    }
    state.paperTabs = state.paperTabs.filter(id => id !== paperId);
    persistPaperTabs();
    renderPaperTabs();
    renderPaperSelect();
  } catch (error) {
    toast(`Tab kept open: ${error.message}`);
  }
}

function queuePaperWrite(paperId, kind, data) {
  const session = paperSession(paperId);
  let write = session.writes.get(kind);
  if (!write) {
    write = { pending: 0, dirty: false, revision: 0, promise: null, error: null, body: "" };
    session.writes.set(kind, write);
  }
  write.body = JSON.stringify(data);
  const body = write.body;
  const revision = ++write.revision;
  const previous = write.promise;
  write.pending += 1;
  write.dirty = true;
  renderReaderSaveStatus();
  // A later snapshot can retry a failed write, but the failure stays visible
  // and the tab cannot be discarded until its latest snapshot is saved.
  const ready = previous ? previous.catch(() => undefined) : Promise.resolve();
  const promise = ready.then(() => api(`/api/papers/${encodeURIComponent(paperId)}/${kind}`, {
    method: "POST", body,
  }));
  write.promise = promise;
  promise.then(() => {
    write.pending -= 1;
    if (write.revision === revision) {
      write.dirty = false;
      write.error = null;
    }
    renderReaderSaveStatus();
  }, error => {
    write.pending -= 1;
    write.error = error;
    renderReaderSaveStatus();
    console.error(`Could not save ${kind} for ${paperId}`, error);
    if (paperId === state.currentPaperId) {
      setThinkingSaveState("Unsaved — retry before closing", "error");
      toast(`Save failed: ${error.message}. Keep this tab open and retry.`);
    }
  });
  return promise;
}

function renderReaderSaveStatus() {
  const root = qs("#readerSaveStatus");
  if (!root) return;
  const writes = [...(state.paperSessions.get(state.currentPaperId)?.writes?.values() || [])];
  const error = writes.find(write => write.error);
  const saving = writes.some(write => write.pending);
  const dirty = state.thinkingDirty || state.takeawayDirty || state.metadataDrafts.has(state.currentPaperId)
    || writes.some(write => write.dirty) || noteDrawerHasChanges() || hasThinkingComposerDraft();
  const message = !state.currentPaperId ? "" : error ? "Unsaved — retry before closing"
    : saving ? "Saving locally…" : dirty ? "Unsaved changes" : "Saved locally";
  root.dataset.state = error ? "error" : saving ? "saving" : dirty ? "pending" : "saved";
  if (root.textContent !== message) root.textContent = message;
  refreshSavedDefinitionStatuses();
}

function hasThinkingComposerDraft(session = state) {
  return Boolean(session.chatDraft || session.manualOutputDraft?.prompt || session.manualOutputDraft?.content);
}

function hasUnsavedPaperChanges() {
  return state.thinkingDirty || state.takeawayDirty || noteDrawerHasChanges() || hasThinkingComposerDraft()
    || state.metadataDrafts.size > 0
    || [...state.paperSessions.entries()].some(([id, session]) => (id !== state.currentPaperId && hasThinkingComposerDraft(session))
      || [...session.writes.values()].some(write => write.pending || write.dirty));
}

async function flushCurrentPaperEdits() {
  if (state.chatSending || state.readingNarrativeGenerating) throw new Error("Wait for the current AI request to finish before switching papers.");
  if (noteDrawerHasChanges()) await savePendingAnnotation(true);
  const paperId = state.currentPaperId;
  if (!paperId || !state.payload) return;
  tickReadingProgress({ skipSchedule: true });
  if (state.thinkingSaveTimer) clearTimeout(state.thinkingSaveTimer);
  if (state.takeawaySaveTimer) clearTimeout(state.takeawaySaveTimer);
  state.thinkingSaveTimer = null;
  state.takeawaySaveTimer = null;
  if (state.thinkingDirty) await saveThinking({ silent: true });
  if (state.takeawayDirty) await saveTakeawayDoc({ silent: true });
  await flushReadingProgress({ silent: true, strict: true });
  const session = paperSession(paperId);
  for (const [kind, write] of session.writes) {
    if (write.error && !write.pending) await queuePaperWrite(paperId, kind, JSON.parse(write.body));
    else if (write.promise) await write.promise;
  }
  if (noteDrawerHasChanges()) throw new Error("Save the open note before switching papers.");
  capturePaperSession();
}

async function exportReadingData(format) {
  const paperId = state.currentPaperId;
  if (!paperId) return;
  try {
    if (hasThinkingComposerDraft()) throw new Error("Finish or clear the chat/paste draft before exporting. Unsubmitted drafts are not saved reading data.");
    await flushCurrentPaperEdits();
    if (paperId !== state.currentPaperId) return;
    const endpoint = format === "json" ? "reading-data" : "notes-md";
    const response = await fetch(`/api/papers/${encodeURIComponent(paperId)}/${endpoint}`);
    if (!response.ok) throw new Error(`Export failed (${response.status})`);
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement("a");
    link.href = url;
    link.download = `${paperId}-reading.${format === "json" ? "json" : "md"}`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast("Original reading data exported — no AI summary.");
  } catch (error) {
    toast(`Export failed: ${error.message}`);
  }
}

const defaultNoteTags = [];
const paperBriefBlockId = "paper-brief";
const defaultLibraryProjects = ["collaborative", "memories"];
const defaultPdfLibraryPath = "E:\\论文库\\";
const readingSkimmedMs = 2500;
const readingCarefulMs = 20000;
const maxImportanceStars = 3;

const libraryColumns = [
  { key: "title", label: "Title", width: 520 },
  { key: "project", label: "Project", width: 230 },
  { key: "source", label: "来源", width: 250 },
  { key: "authors", label: "Author", width: 180 },
  { key: "institutions", label: "Institution", width: 180 },
  { key: "venue", label: "Journal", width: 150 },
  { key: "year", label: "Publication Year", width: 130 },
  { key: "importance", label: "重要性", width: 180 },
  { key: "tags", label: "Tags", width: 230 },
  { key: "cite", label: "Cite", width: 110 },
  { key: "videos", label: "Videos", width: 310 },
  { key: "read_status", label: "Read Status", width: 190 },
  { key: "processing", label: "Processing", width: 170 },
  { key: "pdf", label: "PDF", width: 110 },
  { key: "actions", label: "Actions", width: 190 },
];

const memoryTagPalette = ["#f7b4ad", "#f08a84", "#e76666", "#c94d58", "#f4a1c2", "#d94f7d"];
const collaborativeTagPalette = ["#79d4c8", "#55b6c8", "#5ec5a8", "#8edbd0", "#72b7e6", "#6fcf97", "#85c3dd", "#9dddc7"];
const sharedTagPalette = ["#d8c3ff", "#ffd27a", "#cdd7e1", "#e6d6a9"];
const tagColorPalette = [...memoryTagPalette, ...collaborativeTagPalette, ...sharedTagPalette];

function annotationTags(annotation) {
  const tags = annotation?.tags;
  if (Array.isArray(tags)) return tags.map(tag => String(tag).trim()).filter(Boolean);
  if (typeof tags === "string" && tags.trim()) return [tags.trim()];
  return [];
}

function allNoteTags(extraTags = []) {
  const seen = new Set([...defaultNoteTags, ...extraTags.map(tag => String(tag).trim()).filter(Boolean)]);
  for (const annotation of state.annotations) {
    for (const tag of annotationTags(annotation)) seen.add(tag);
  }
  for (const annotation of state.thinking?.annotations || []) {
    for (const tag of annotationTags(annotation)) seen.add(tag);
  }
  for (const note of state.allNotes) {
    for (const tag of annotationTags(note)) seen.add(tag);
  }
  return Array.from(seen);
}

function allLibraryTags(extraTags = []) {
  const seen = new Set((state.tagDictionary?.paper_tags || []).map(tag => String(tag.id || tag).trim()).filter(Boolean));
  extraTags.map(tag => String(tag).trim()).filter(Boolean).forEach(tag => seen.add(tag));
  for (const paper of state.library?.papers || []) {
    for (const tag of uniqueTags(paper.tags || [])) seen.add(tag);
  }
  return Array.from(seen).sort((a, b) => a.localeCompare(b));
}

function canonicalTagRecord(tagId) {
  const id = String(tagId || "").trim();
  return (state.tagDictionary?.paper_tags || []).find(item => item.id === id) || null;
}

function libraryTagLabel(tagId) {
  const record = canonicalTagRecord(tagId);
  return record?.label || tagId;
}

function canonicalTagIdsForInput(value) {
  const raw = String(value || "").trim();
  if (!raw) return [];
  const key = raw.normalize("NFKC").toLowerCase().replace("boundry", "boundary").replace("groud", "ground").replace("conctext", "context").replace(/\s+/g, " ").replace(/\s*[\\/]+\s*/g, "/").trim();
  const exact = state.tagDictionary?.aliases?.[key];
  if (Array.isArray(exact) && exact.length) return exact;
  const byId = canonicalTagRecord(raw);
  if (byId) return [byId.id];
  const byLabel = (state.tagDictionary?.paper_tags || []).find(item => String(item.label || "").toLowerCase() === raw.toLowerCase());
  return byLabel ? [byLabel.id] : [raw];
}

function normalizeImportanceTags(value) {
  if (Array.isArray(value)) return uniqueTags(value);
  return uniqueTags(String(value || "").split(/[,;；、]/));
}

function normalizeImportanceLevel(value) {
  if (Array.isArray(value)) return value.reduce((maxLevel, item) => Math.max(maxLevel, normalizeImportanceLevel(item)), 0);
  if (value && typeof value === "object") return Math.max(normalizeImportanceLevel(value.importance), normalizeImportanceLevel(value.importance_tags));
  const raw = String(value ?? "").trim();
  if (!raw) return 0;
  const numeric = Number(raw);
  if (Number.isFinite(numeric)) return Math.max(0, Math.min(maxImportanceStars, Math.round(numeric)));
  const starCount = (raw.match(/[★⭐]/g) || []).length;
  if (starCount) return Math.max(0, Math.min(maxImportanceStars, starCount));
  const text = raw.normalize("NFKC").toLowerCase();
  const fraction = text.match(/([0-3])\s*\/\s*3/);
  if (fraction) return normalizeImportanceLevel(fraction[1]);
  const digit = text.match(/\b([0-3])\b/);
  if (digit) return normalizeImportanceLevel(digit[1]);
  if (/最重要|非常重要|特别重要|critical|top|must[-\s]?read|very\s+important|high/.test(text)) return 3;
  if (/重要|important|medium|mid/.test(text)) return 2;
  if (/低|一般|minor|low|light/.test(text)) return 1;
  return 0;
}

function paperImportanceLevel(paper = {}) {
  return Math.max(normalizeImportanceLevel(paper.importance), normalizeImportanceLevel(paper.importance_tags || []));
}

function paperImportanceTags(paper = {}) {
  const level = paperImportanceLevel(paper);
  if (level) return [String(level)];
  return uniqueTags([...normalizeImportanceTags(paper.importance_tags || []), ...normalizeImportanceTags(paper.importance || "")]);
}

function allImportanceTags(extraTags = []) {
  const seen = new Set(normalizeImportanceTags(extraTags));
  for (const paper of state.library?.papers || []) {
    for (const tag of paperImportanceTags(paper)) seen.add(tag);
  }
  return Array.from(seen).sort((a, b) => a.localeCompare(b));
}

function importanceLabel(tags) {
  const level = normalizeImportanceLevel(tags);
  if (level) return "★".repeat(level);
  return uniqueTags(tags).join("; ");
}

function paperImportanceLabel(paper = {}) {
  const level = paperImportanceLevel(paper);
  return level ? `${"★".repeat(level)} ${level}/${maxImportanceStars}` : "";
}

function importanceFieldsForLevel(level) {
  const cleanLevel = normalizeImportanceLevel(level);
  return {
    importance: cleanLevel ? String(cleanLevel) : "",
    importance_tags: cleanLevel ? [String(cleanLevel)] : [],
  };
}

function importanceStarEditorHtml(paper = {}, options = {}) {
  const paperId = paper.id || state.currentPaperId || "";
  const level = paperImportanceLevel(paper);
  const variant = options.variant ? ` importance-star-editor-${options.variant}` : "";
  const showLabel = options.showLabel !== false;
  const label = level ? `${level}/${maxImportanceStars}` : "No stars";
  return `<div class="importance-star-editor${variant}${level ? "" : " is-empty"}" aria-label="Paper importance">
    <div class="importance-star-buttons">
      ${[1, 2, 3].map(star => `<button class="importance-star-button ${star <= level ? "active" : ""}" data-set-importance-stars="${escapeHtml(paperId)}" data-importance-level="${star}" type="button" aria-label="${star === level ? "Clear importance" : `Set importance to ${star} star${star === 1 ? "" : "s"}`}" aria-pressed="${star <= level ? "true" : "false"}" title="${star === level ? "Click again to clear importance" : `Set importance to ${star}/${maxImportanceStars}`}">${star <= level ? "★" : "☆"}</button>`).join("")}
    </div>
    ${showLabel ? `<span class="importance-star-label">${escapeHtml(label)}</span>` : ""}
  </div>`;
}

function initLibraryPreferences() {
  state.libraryDensity = localStorage.getItem(libraryDensityStorageKey) || "comfortable";
  state.libraryTitlesCollapsed = localStorage.getItem(libraryTitleCollapsedStorageKey) === "1";
  state.libraryPreviewThumbnailsVisible = localStorage.getItem(libraryPreviewThumbsStorageKey) === "1";
  state.libraryView = localStorage.getItem(libraryViewStorageKey) || "all";
  state.libraryProject = localStorage.getItem(libraryProjectStorageKey) || state.libraryView || "all";
  try {
    const widths = JSON.parse(localStorage.getItem(libraryColumnWidthStorageKey) || "{}");
    state.libraryColumnWidths = widths && typeof widths === "object" ? widths : {};
  } catch (error) {
    state.libraryColumnWidths = {};
  }
  try {
    const settings = JSON.parse(localStorage.getItem(libraryViewSettingsStorageKey) || "{}");
    state.libraryViewSettings = settings && typeof settings === "object" ? settings : {};
  } catch (error) {
    state.libraryViewSettings = {};
  }
  try {
    const snapshots = JSON.parse(localStorage.getItem(libraryScrollStorageKey) || "{}");
    state.libraryScrollSnapshots = snapshots && typeof snapshots === "object" ? snapshots : {};
  } catch (error) {
    state.libraryScrollSnapshots = {};
  }
  try {
    state.libraryCustomProjects = normalizeTagsInput(JSON.parse(localStorage.getItem(libraryCustomProjectsStorageKey) || "[]"));
  } catch (error) {
    state.libraryCustomProjects = [];
  }
  applyStoredLibraryViewSettings(state.libraryView || "all");
}

function normalizeProjectName(value) {
  const text = String(value || "").trim();
  const key = text.toLowerCase().replace(/\s+/g, "");
  if (["collaborative", "collective"].includes(key)) return "collaborative";
  if (["memories", "memoies"].includes(key)) return "memories";
  return text;
}

function paperProjects(paper = {}) {
  const values = Array.isArray(paper.projects) ? paper.projects : String(paper.projects || "").split(",");
  const legacy = String(paper.project || "").trim();
  return uniqueTags([...values, legacy].map(normalizeProjectName));
}

function paperProject(paper = {}) {
  return paperProjects(paper)[0] || "";
}

function allLibraryProjects() {
  const projects = new Set([...defaultLibraryProjects, ...state.libraryCustomProjects.map(normalizeProjectName)]);
  for (const paper of state.library?.papers || []) {
    for (const project of paperProjects(paper)) projects.add(project);
  }
  return Array.from(projects).sort((a, b) => a.localeCompare(b));
}

function projectContextFor(project) {
  const clean = normalizeProjectName(project) || "collaborative";
  return state.projectContexts?.contexts?.[clean] || { project: clean, source_path: "", cards: [] };
}

function currentPaperProject() {
  const metadataProjects = paperProjects(state.payload?.metadata || {});
  if (metadataProjects.length) return metadataProjects[0];
  const paper = state.library?.papers?.find(item => item.id === state.currentPaperId);
  return paperProject(paper) || state.projectContextPanel.project || "collaborative";
}

function projectContextCards(project) {
  const cards = projectContextFor(project).cards;
  return Array.isArray(cards) ? cards : [];
}

function hasProjectContextCards(project) {
  return projectContextCards(project).length > 0;
}

function selectedLibraryIntakeTags() {
  return uniqueTags(state.libraryIntakeTags || []);
}

function selectedLibraryIntakeProjects() {
  return uniqueTags((state.libraryIntakeProjects || []).map(normalizeProjectName)).filter(Boolean);
}

function libraryIntakePayload() {
  const tags = selectedLibraryIntakeTags();
  const projects = selectedLibraryIntakeProjects();
  return {
    tags,
    projects,
    ...importanceFieldsForLevel(state.libraryIntakeImportance),
    tag_colors: Object.fromEntries(tags.map(tag => [tag, tagColor(tag)])),
    project_colors: Object.fromEntries(projects.map(project => [project, projectColor(project)])),
  };
}

function clearLibraryIntakeSelection() {
  state.libraryIntakeTags = [];
  state.libraryIntakeProjects = [];
  state.libraryIntakeImportance = 0;
  renderLibraryIntakePickers();
}

function quickImportanceEditorHtml(level = 0, actionAttr = "data-set-intake-importance") {
  const current = normalizeImportanceLevel(level);
  return `<div class="importance-star-editor importance-star-editor-quick${current ? "" : " is-empty"}" aria-label="Paper importance">
    <div class="importance-star-buttons">
      ${[1, 2, 3].map(star => `<button class="importance-star-button ${star <= current ? "active" : ""}" ${actionAttr}="${star}" type="button" aria-label="${star === current ? "Clear importance" : `Set importance to ${star} star${star === 1 ? "" : "s"}`}" aria-pressed="${star <= current ? "true" : "false"}" title="${star === current ? "Click again to clear importance" : `Set to ${star}/${maxImportanceStars}`}">${star <= current ? "★" : "☆"}</button>`).join("")}
    </div>
    <span class="importance-star-label">${current ? `${current}/${maxImportanceStars}` : "No stars"}</span>
  </div>`;
}

function renderLibraryIntakePickers() {
  const projectRoot = qs("#libraryIntakeProjectPicker");
  const tagRoot = qs("#libraryIntakeTagPicker");
  const importanceRoot = qs("#libraryIntakeImportancePicker");
  if (!projectRoot || !tagRoot) return;
  const selectedProjects = selectedLibraryIntakeProjects();
  const selectedTags = selectedLibraryIntakeTags();
  const projectSet = new Set(selectedProjects);
  const tagSet = new Set(selectedTags);
  const projectOptions = allLibraryProjects();
  const tagOptions = allLibraryTags(selectedTags).filter(tag => tagSet.has(tag) || !String(tag).startsWith("__"));
  const projectColors = projectColorMap();
  const tagColors = tagColorMap();
  projectRoot.innerHTML = `
    <div class="library-intake-picker-header">
      <span>Paper project</span>
      <button class="secondary-button mini-button" data-clear-intake-projects type="button">Clear</button>
    </div>
    <div class="library-tags library-intake-selected" aria-label="Selected paper projects">
      ${selectedProjects.map(project => `<button class="library-tag library-project-tag" style="--tag-color: ${escapeHtml(projectColor(project, projectColors))}" data-remove-intake-project="${escapeHtml(project)}" type="button">${escapeHtml(project)} ×</button>`).join("") || '<span class="muted small-text">No project selected</span>'}
    </div>
    <div class="library-intake-option-panel" data-filter-tag-scope>
      ${tagMenuSearchHtml("Search projects")}
      <div class="library-intake-option-list">
        ${projectOptions.map(project => `<button class="library-tag-option ${projectSet.has(project) ? "active" : ""}" style="--tag-color: ${escapeHtml(projectColor(project, projectColors))}" data-toggle-intake-project="${escapeHtml(project)}" ${filterableTagOptionAttrs(project)} type="button"><span></span>${escapeHtml(project)}</button>`).join("") || '<span class="muted small-text">No existing projects</span>'}
        <span class="muted small-text" data-filter-empty hidden>No matching projects</span>
      </div>
    </div>
    <div class="library-intake-custom-row">
      <input id="libraryIntakeProjectCustom" type="text" placeholder="New project" />
      <button class="secondary-button mini-button" data-add-intake-project type="button">Add</button>
    </div>`;
  tagRoot.innerHTML = `
    <div class="library-intake-picker-header">
      <span>Paper tag</span>
      <button class="secondary-button mini-button" data-clear-intake-tags type="button">Clear</button>
    </div>
    <div class="library-tags library-intake-selected" aria-label="Selected paper tags">
      ${selectedTags.map(tag => `<button class="library-tag" style="--tag-color: ${escapeHtml(tagColor(tag, tagColors))}" data-remove-intake-tag="${escapeHtml(tag)}" title="${escapeHtml(tag)}" type="button">${escapeHtml(libraryTagLabel(tag))} ×</button>`).join("") || '<span class="muted small-text">No paper tag selected</span>'}
    </div>
    <div class="library-intake-option-panel" data-filter-tag-scope>
      ${tagMenuSearchHtml("Search paper tags")}
      <div class="library-intake-option-list">
        ${tagOptions.map(tag => `<button class="library-tag-option ${tagSet.has(tag) ? "active" : ""}" style="--tag-color: ${escapeHtml(tagColor(tag, tagColors))}" data-toggle-intake-tag="${escapeHtml(tag)}" ${filterableTagOptionAttrs(`${tag} ${libraryTagLabel(tag)}`)} type="button"><span></span>${escapeHtml(libraryTagLabel(tag))}</button>`).join("") || '<span class="muted small-text">No existing tags</span>'}
        <span class="muted small-text" data-filter-empty hidden>No matching tags</span>
      </div>
    </div>
    <div class="library-intake-custom-row">
      <input id="libraryIntakeTagCustom" type="text" placeholder="New tag or alias" />
      <button class="secondary-button mini-button" data-add-intake-tag type="button">Add</button>
    </div>`;
  if (importanceRoot) {
    importanceRoot.innerHTML = `
      <div class="library-intake-picker-header">
        <span>Importance</span>
        <button class="secondary-button mini-button" data-clear-intake-importance type="button">Clear</button>
      </div>
      ${quickImportanceEditorHtml(state.libraryIntakeImportance, "data-set-intake-importance")}`;
  }
  initTagOptionFilters(projectRoot);
  initTagOptionFilters(tagRoot);
}

function addLibraryIntakeProjectFromInput() {
  const input = qs("#libraryIntakeProjectCustom");
  const value = normalizeProjectName(input?.value || "");
  if (!value) return;
  state.libraryIntakeProjects = uniqueTags([...selectedLibraryIntakeProjects(), value]);
  if (!allLibraryProjects().includes(value)) {
    state.libraryCustomProjects = uniqueTags([...state.libraryCustomProjects, value]);
    saveCustomLibraryProjects();
  }
  if (input) input.value = "";
  renderLibraryIntakePickers();
}

function addLibraryIntakeTagFromInput() {
  const input = qs("#libraryIntakeTagCustom");
  const values = canonicalTagIdsForInput(input?.value || "");
  if (!values.length) return;
  state.libraryIntakeTags = uniqueTags([...selectedLibraryIntakeTags(), ...values]);
  if (input) input.value = "";
  renderLibraryIntakePickers();
}

function handleLibraryIntakeClick(event) {
  if (event.target.closest?.("[data-close-library-tag-prompt], [data-skip-library-tag-prompt]")) {
    event.preventDefault();
    closeLibraryTagPrompt();
    return true;
  }
  if (event.target.closest?.("[data-expand-library-tag-prompt]")) {
    event.preventDefault();
    state.libraryTagPrompt.expanded = !state.libraryTagPrompt.expanded;
    renderLibraryTagPrompt();
    return true;
  }
  if (event.target.closest?.("[data-save-library-tag-prompt]")) {
    event.preventDefault();
    saveLibraryTagPromptSelection().catch(error => toast(`Tag save failed: ${error.message}`));
    return true;
  }
  const intakeImportance = event.target.closest?.("[data-set-intake-importance]");
  if (intakeImportance) {
    event.preventDefault();
    const clickedLevel = normalizeImportanceLevel(intakeImportance.dataset.setIntakeImportance);
    state.libraryIntakeImportance = clickedLevel === normalizeImportanceLevel(state.libraryIntakeImportance) ? 0 : clickedLevel;
    renderLibraryTagPrompt();
    return true;
  }
  const projectToggle = event.target.closest?.("[data-toggle-intake-project]");
  if (projectToggle) {
    event.preventDefault();
    const value = normalizeProjectName(projectToggle.dataset.toggleIntakeProject || "");
    const selected = new Set(selectedLibraryIntakeProjects());
    if (selected.has(value)) selected.delete(value);
    else if (value) selected.add(value);
    state.libraryIntakeProjects = Array.from(selected);
    renderLibraryIntakePickers();
    return true;
  }
  const tagToggle = event.target.closest?.("[data-toggle-intake-tag]");
  if (tagToggle) {
    event.preventDefault();
    const value = tagToggle.dataset.toggleIntakeTag || "";
    const selected = new Set(selectedLibraryIntakeTags());
    if (selected.has(value)) selected.delete(value);
    else if (value) selected.add(value);
    state.libraryIntakeTags = Array.from(selected);
    renderLibraryIntakePickers();
    return true;
  }
  const projectRemove = event.target.closest?.("[data-remove-intake-project]");
  if (projectRemove) {
    event.preventDefault();
    state.libraryIntakeProjects = selectedLibraryIntakeProjects().filter(project => project !== projectRemove.dataset.removeIntakeProject);
    renderLibraryIntakePickers();
    return true;
  }
  const tagRemove = event.target.closest?.("[data-remove-intake-tag]");
  if (tagRemove) {
    event.preventDefault();
    state.libraryIntakeTags = selectedLibraryIntakeTags().filter(tag => tag !== tagRemove.dataset.removeIntakeTag);
    renderLibraryIntakePickers();
    return true;
  }
  if (event.target.closest?.("[data-clear-intake-projects]")) {
    event.preventDefault();
    state.libraryIntakeProjects = [];
    renderLibraryIntakePickers();
    return true;
  }
  if (event.target.closest?.("[data-clear-intake-tags]")) {
    event.preventDefault();
    state.libraryIntakeTags = [];
    renderLibraryIntakePickers();
    return true;
  }
  if (event.target.closest?.("[data-clear-intake-importance]")) {
    event.preventDefault();
    state.libraryIntakeImportance = 0;
    renderLibraryIntakePickers();
    return true;
  }
  if (event.target.closest?.("[data-add-intake-project]")) {
    event.preventDefault();
    addLibraryIntakeProjectFromInput();
    return true;
  }
  if (event.target.closest?.("[data-add-intake-tag]")) {
    event.preventDefault();
    addLibraryIntakeTagFromInput();
    return true;
  }
  return false;
}

function uploadedPaperIdsFromResult(result) {
  const papers = Array.isArray(result?.papers) ? result.papers : [result].filter(Boolean);
  return uniqueTags(papers
    .filter(item => item && !item.duplicate && !item.error)
    .map(item => item.paper_id || item.metadata?.id || item.metadata?.paper_id || ""));
}

function libraryTagPromptPapers() {
  const ids = new Set(state.libraryTagPrompt?.paperIds || []);
  return (state.library?.papers || []).filter(paper => ids.has(paper.id));
}

function openLibraryTagPrompt(paperIds = []) {
  const ids = uniqueTags(paperIds);
  if (!ids.length) return;
  state.libraryTagPrompt = { open: true, expanded: true, paperIds: ids, saving: false };
  clearLibraryIntakeSelection();
  renderLibraryTagPrompt();
}

function closeLibraryTagPrompt(options = {}) {
  state.libraryTagPrompt = { open: false, expanded: false, paperIds: [], saving: false };
  if (options.clearSelection !== false) clearLibraryIntakeSelection();
  renderLibraryTagPrompt();
}

function renderLibraryTagPrompt() {
  const root = qs("#libraryTagPrompt");
  if (!root) return;
  const papers = libraryTagPromptPapers();
  const visible = Boolean(state.libraryTagPrompt.open && papers.length);
  root.hidden = !visible;
  root.classList.toggle("open", visible);
  root.classList.toggle("expanded", Boolean(state.libraryTagPrompt.expanded));
  root.setAttribute("aria-hidden", visible ? "false" : "true");
  if (!visible) {
    root.innerHTML = "";
    return;
  }
  const title = papers.length === 1 ? compactText(paperTitle(papers[0]) || papers[0].id, 74) : `${papers.length} papers`;
  const selectedTags = selectedLibraryIntakeTags();
  const selectedProjects = selectedLibraryIntakeProjects();
  const selectedImportance = normalizeImportanceLevel(state.libraryIntakeImportance);
  const hasSelection = selectedTags.length || selectedProjects.length || selectedImportance;
  root.innerHTML = `
    <div class="library-tag-prompt-header">
      <div>
        <span class="sense-kicker">Library intake</span>
        <strong>Set metadata while the PDF parses</strong>
      </div>
      <button class="icon-button" data-close-library-tag-prompt type="button" title="Close tag prompt" aria-label="Close tag prompt">x</button>
    </div>
    <p class="library-tag-prompt-copy">${escapeHtml(title)} ${papers.length === 1 ? "is" : "are"} parsing in the background. Add importance, project, and paper tags now; they sync to metadata immediately.</p>
    <div class="library-tag-prompt-paper-list" aria-label="Uploaded papers">
      ${papers.slice(0, 3).map(paper => `<span>${escapeHtml(compactText(paperTitle(paper) || paper.id, 64))}</span>`).join("")}
      ${papers.length > 3 ? `<span>+${papers.length - 3} more</span>` : ""}
    </div>
    ${state.libraryTagPrompt.expanded ? `
      <div class="library-tag-prompt-form">
        <section id="libraryIntakeImportancePicker" class="library-intake-picker library-intake-importance" aria-label="Select paper importance"></section>
        <section id="libraryIntakeProjectPicker" class="library-intake-picker" aria-label="Select paper project"></section>
        <section id="libraryIntakeTagPicker" class="library-intake-picker" aria-label="Select paper tags"></section>
        <div class="library-tag-prompt-actions">
          <button class="secondary-button" data-skip-library-tag-prompt type="button">Not now</button>
          <button class="primary-button" data-save-library-tag-prompt type="button" ${hasSelection && !state.libraryTagPrompt.saving ? "" : "disabled"}>${state.libraryTagPrompt.saving ? "Saving..." : "Apply metadata"}</button>
        </div>
      </div>` : `
      <div class="library-tag-prompt-actions">
        <button class="secondary-button" data-skip-library-tag-prompt type="button">Not now</button>
        <button class="primary-button" data-expand-library-tag-prompt type="button">Add metadata</button>
      </div>`}`;
  if (state.libraryTagPrompt.expanded) renderLibraryIntakePickers();
}

async function saveLibraryTagPromptSelection() {
  const prompt = state.libraryTagPrompt;
  if (!prompt.open || prompt.saving) return;
  const tags = selectedLibraryIntakeTags();
  const projects = selectedLibraryIntakeProjects();
  const importance = normalizeImportanceLevel(state.libraryIntakeImportance);
  if (!tags.length && !projects.length && !importance) return;
  prompt.saving = true;
  renderLibraryTagPrompt();
  try {
    const body = {};
    if (tags.length) {
      body.tags = tags;
      body.tag_colors = Object.fromEntries(tags.map(tag => [tag, tagColor(tag)]));
    }
    if (projects.length) {
      body.projects = projects;
      body.project = projects[0] || "";
      body.project_colors = Object.fromEntries(projects.map(project => [project, projectColor(project)]));
    }
    if (importance) Object.assign(body, importanceFieldsForLevel(importance));
    const response = await api("/api/library/papers/metadata", { method: "POST", body: JSON.stringify({ paper_ids: prompt.paperIds || [], metadata: body }) });
    for (const item of response.updated || []) {
      const paperId = item.paper_id;
      const paper = state.library?.papers?.find(entry => entry.id === paperId);
      if (paper) Object.assign(paper, item.metadata || {});
      if (state.currentPaperId === paperId && state.payload?.metadata) Object.assign(state.payload.metadata, item.metadata || {});
    }
    closeLibraryTagPrompt();
    renderLibraryPreservingScroll();
    toast("Upload metadata saved");
  } finally {
    prompt.saving = false;
    if (state.libraryTagPrompt === prompt) renderLibraryTagPrompt();
  }
}

function saveCustomLibraryProjects() {
  state.libraryCustomProjects = uniqueTags(state.libraryCustomProjects);
  localStorage.setItem(libraryCustomProjectsStorageKey, JSON.stringify(state.libraryCustomProjects));
}

function currentLibraryViewKey() {
  return state.libraryView || state.libraryProject || "all";
}

function applyStoredLibraryViewSettings(key = currentLibraryViewKey()) {
  const settings = state.libraryViewSettings[key] || {};
  state.libraryFilter = settings.filter || "";
  state.librarySort = settings.sort || "updated_at";
  state.libraryGroup = settings.group || (key === "all" ? "none" : "project");
  state.libraryDensity = settings.density || state.libraryDensity || "comfortable";
  state.libraryTableScroll = state.libraryScrollSnapshots[key] || settings.scroll || state.libraryTableScroll || { tableTop: 0, tableLeft: 0, rootLeft: 0, windowY: 0 };
}

function saveCurrentLibraryViewSettings() {
  const key = currentLibraryViewKey();
  state.libraryViewSettings[key] = {
    filter: state.libraryFilter,
    sort: state.librarySort,
    group: state.libraryGroup,
    density: state.libraryDensity,
    scroll: state.libraryTableScroll || { tableTop: 0, tableLeft: 0, rootLeft: 0, windowY: 0 },
  };
  localStorage.setItem(libraryViewSettingsStorageKey, JSON.stringify(state.libraryViewSettings));
}

function applyLibraryView(viewKey) {
  saveCurrentLibraryViewSettings();
  const key = viewKey || "all";
  state.libraryView = key;
  state.libraryProject = key;
  applyStoredLibraryViewSettings(key);
  localStorage.setItem(libraryViewStorageKey, state.libraryView);
  localStorage.setItem(libraryProjectStorageKey, state.libraryProject);
  renderLibrary();
  restoreLibraryScroll();
}

function libraryColumnWidth(key) {
  const column = libraryColumns.find(item => item.key === key);
  const value = Number(state.libraryColumnWidths[key] || column?.width || 140);
  return Math.max(84, Math.min(720, value));
}

function saveLibraryColumnWidths() {
  localStorage.setItem(libraryColumnWidthStorageKey, JSON.stringify(state.libraryColumnWidths || {}));
}

function resetLibraryColumnWidths() {
  state.libraryColumnWidths = {};
  saveLibraryColumnWidths();
  renderLibrary();
}

function tagColorMap() {
  const colors = {};
  for (const paper of state.library?.papers || []) {
    const map = paper.tag_colors && typeof paper.tag_colors === "object" ? paper.tag_colors : {};
    for (const [tag, color] of Object.entries(map)) {
      if (tag && color && !colors[tag]) colors[tag] = color;
    }
  }
  return colors;
}

function fallbackTagColor(tag) {
  const text = String(tag || "");
  let hash = 0;
  for (const char of text) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  const canonical = canonicalTagRecord(text);
  if (canonical?.project_scope === "memories" || text.startsWith("M_")) return memoryTagPalette[hash % memoryTagPalette.length];
  if (canonical?.project_scope === "collaborative" || text.startsWith("C_")) return collaborativeTagPalette[hash % collaborativeTagPalette.length];
  if (canonical?.project_scope === "shared" || ["HAI theory", "How AI influence creativity?"].includes(text)) return sharedTagPalette[hash % sharedTagPalette.length];
  return tagColorPalette[hash % tagColorPalette.length];
}

function tagColor(tag, extraColors = {}) {
  const canonicalColor = canonicalTagRecord(tag)?.color || "";
  return extraColors[tag] || tagColorMap()[tag] || canonicalColor || fallbackTagColor(tag);
}

function tagColorsForPaper(paperId) {
  const paper = state.library?.papers?.find(item => item.id === paperId);
  return { ...(paper?.tag_colors && typeof paper.tag_colors === "object" ? paper.tag_colors : {}) };
}

function projectColorMap() {
  const colors = {};
  for (const paper of state.library?.papers || []) {
    const map = paper.project_colors && typeof paper.project_colors === "object" ? paper.project_colors : {};
    for (const [project, color] of Object.entries(map)) {
      if (project && color && !colors[project]) colors[project] = color;
    }
  }
  return colors;
}

function projectColor(project, extraColors = {}) {
  return extraColors[project] || projectColorMap()[project] || fallbackTagColor(project);
}

function projectColorsForPaper(paperId) {
  const paper = state.library?.papers?.find(item => item.id === paperId);
  return { ...(paper?.project_colors && typeof paper.project_colors === "object" ? paper.project_colors : {}) };
}

function qs(selector) { return document.querySelector(selector); }
function qsa(selector) { return Array.from(document.querySelectorAll(selector)); }

function toast(message) {
  const node = qs("#toast");
  node.textContent = message;
  node.classList.add("show");
  setTimeout(() => node.classList.remove("show"), 1800);
}

function applySidebarWidth(width) {
  const viewportLimit = Math.max(240, Math.min(620, Math.floor(window.innerWidth * 0.48)));
  const clamped = Math.max(200, Math.min(viewportLimit, Math.round(Number(width) || 220)));
  document.documentElement.style.setProperty("--sidebar-width", `${clamped}px`);
  return clamped;
}

function applySensemakingWidth(width) {
  const availableWidth = qs(".reader-workspace")?.clientWidth || window.innerWidth;
  const viewportLimit = Math.max(280, Math.floor(availableWidth * 0.42));
  const clamped = Math.max(280, Math.min(viewportLimit, Math.round(Number(width) || 340)));
  state.sensemakingWidth = clamped;
  document.documentElement.style.setProperty("--sensemaking-width", `${clamped}px`);
  return clamped;
}

function applyReaderWidth(width) {
  if (!["comfortable", "wide", "full"].includes(width)) {
    console.warn("Unknown reading text width preference; using Wide.", width);
    width = "wide";
  }
  qs("#documentRoot").dataset.readerWidth = width;
  qs("#readerWidth").value = width;
  return width;
}

function initReaderWidth() {
  let width = "wide";
  try {
    width = localStorage.getItem(readerWidthStorageKey) || width;
  } catch (error) {
    console.warn("Could not load the reading text width preference.", error);
    toast("Text width preference could not be loaded.");
  }
  applyReaderWidth(width);
  qs("#readerWidth").addEventListener("change", event => {
    const nextWidth = applyReaderWidth(event.target.value);
    try {
      localStorage.setItem(readerWidthStorageKey, nextWidth);
    } catch (error) {
      console.warn("Could not save the reading text width preference.", error);
      toast("Text width changed, but could not be saved for next time.");
    }
  });
}

function applyReportWidth(width) {
  const viewportLimit = Math.max(420, Math.min(860, Math.floor(window.innerWidth * 0.72)));
  const clamped = Math.max(360, Math.min(viewportLimit, Math.round(Number(width) || 520)));
  state.reportWidth = clamped;
  document.documentElement.style.setProperty("--report-sidebar-width", `${clamped}px`);
  return clamped;
}

function initReportResize() {
  const handle = qs("#presentationReportResizeHandle");
  const drawer = qs("#presentationReportDrawer");
  if (!handle || !drawer) return;
  const savedWidth = Number(localStorage.getItem(reportWidthStorageKey));
  applyReportWidth(savedWidth || 520);
  if (state.reportResizeInitialized) return;
  state.reportResizeInitialized = true;
  let dragging = false;
  const moveDragging = event => {
    if (!dragging) return;
    const rect = drawer.getBoundingClientRect();
    applyReportWidth(rect.right - event.clientX);
  };
  const stopDragging = event => {
    if (!dragging) return;
    dragging = false;
    document.body.classList.remove("resizing-report");
    if (event?.pointerId !== undefined) {
      try { handle.releasePointerCapture(event.pointerId); } catch (error) { /* pointer may already be released */ }
    }
    if (state.reportWidth) localStorage.setItem(reportWidthStorageKey, String(state.reportWidth));
  };
  const startDragging = event => {
    if (dragging) return;
    dragging = true;
    if (event.pointerId !== undefined) handle.setPointerCapture(event.pointerId);
    document.body.classList.add("resizing-report");
    event.preventDefault();
  };
  handle.addEventListener("pointerdown", startDragging);
  handle.addEventListener("mousedown", startDragging);
  handle.addEventListener("dblclick", () => {
    applyReportWidth(520);
    localStorage.setItem(reportWidthStorageKey, "520");
  });
  document.addEventListener("pointermove", moveDragging);
  document.addEventListener("mousemove", moveDragging);
  document.addEventListener("pointerup", stopDragging);
  document.addEventListener("mouseup", stopDragging);
  document.addEventListener("pointercancel", stopDragging);
  window.addEventListener("resize", () => {
    if (state.reportWidth) applyReportWidth(state.reportWidth);
  });
}

function initSensemakingResize() {
  const handle = qs("#sensemakingResizeHandle");
  const workspace = qs(".reader-workspace");
  if (!handle || !workspace) return;
  const savedWidth = Number(localStorage.getItem(sensemakingWidthStorageKey));
  if (savedWidth) applySensemakingWidth(savedWidth);
  let dragging = false;
  const moveDragging = event => {
    if (!dragging) return;
    const rect = workspace.getBoundingClientRect();
    applySensemakingWidth(rect.right - event.clientX);
  };
  const stopDragging = event => {
    if (!dragging) return;
    dragging = false;
    document.body.classList.remove("resizing-sensemaking");
    if (event?.pointerId !== undefined) {
      try { handle.releasePointerCapture(event.pointerId); } catch (error) { /* pointer may already be released */ }
    }
    if (state.sensemakingWidth) localStorage.setItem(sensemakingWidthStorageKey, String(state.sensemakingWidth));
  };
  const startDragging = event => {
    if (dragging) return;
    dragging = true;
    if (event.pointerId !== undefined) handle.setPointerCapture(event.pointerId);
    document.body.classList.add("resizing-sensemaking");
    event.preventDefault();
  };
  handle.addEventListener("pointerdown", startDragging);
  document.addEventListener("pointermove", moveDragging);
  document.addEventListener("pointerup", stopDragging);
  document.addEventListener("pointercancel", stopDragging);
  window.addEventListener("resize", () => {
    if (state.sensemakingWidth) applySensemakingWidth(state.sensemakingWidth);
  });
}

function initSidebarResize() {
  const handle = qs("#sidebarResizeHandle");
  const sidebar = qs("#sidebar");
  if (!handle || !sidebar) return;
  const savedWidth = Number(localStorage.getItem(sidebarWidthStorageKey));
  if (savedWidth) applySidebarWidth(savedWidth);
  let dragging = false;
  const moveDragging = event => {
    if (!dragging) return;
    const left = sidebar.getBoundingClientRect().left;
    applySidebarWidth(event.clientX - left);
  };
  const stopDragging = event => {
    if (!dragging) return;
    dragging = false;
    document.body.classList.remove("resizing-sidebar");
    if (event?.pointerId !== undefined) {
      try { handle.releasePointerCapture(event.pointerId); } catch (error) { /* pointer may already be released */ }
    }
    const width = Number(getComputedStyle(document.documentElement).getPropertyValue("--sidebar-width").replace("px", ""));
    if (width) localStorage.setItem(sidebarWidthStorageKey, String(width));
  };
  const startDragging = event => {
    if (dragging) return;
    dragging = true;
    if (event.pointerId !== undefined) handle.setPointerCapture(event.pointerId);
    document.body.classList.add("resizing-sidebar");
    event.preventDefault();
  };
  handle.addEventListener("pointerdown", startDragging);
  document.addEventListener("pointermove", moveDragging);
  document.addEventListener("pointerup", stopDragging);
  document.addEventListener("pointercancel", stopDragging);
  window.addEventListener("resize", () => {
    const current = Number(getComputedStyle(document.documentElement).getPropertyValue("--sidebar-width").replace("px", ""));
    if (current) applySidebarWidth(current);
  });
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = "";
    try {
      const contentType = response.headers.get("Content-Type") || "";
      if (contentType.includes("application/json")) {
        const data = await response.json();
        detail = data.error || data.message || JSON.stringify(data);
      } else {
        detail = (await response.text()).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
      }
    } catch (error) {
      detail = "";
    }
    throw new Error(`${response.status} ${response.statusText}${detail ? `: ${detail.slice(0, 500)}` : ""}`);
  }
  return response.json();
}

function escapeHtml(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function cssEscape(value) {
  if (typeof CSS !== "undefined" && CSS.escape) return CSS.escape(String(value));
  return String(value).replace(/[^a-zA-Z0-9_-]/g, "\\$&");
}

function displayText(text, options = {}) {
  const cleaned = String(text ?? "")
    .replace(/<\/?(?:sub|sup)\b[^>]*>/gi, "")
    .replace(/\b([A-Za-z]{2,})-\s+([A-Za-z]{2,})\b/g, "$1$2")
    .replace(/\s+([,.;:!?])/g, "$1")
    .replace(/[ \t]{2,}/g, " ");
  return options.trim === false ? cleaned : cleaned.trim();
}

function isEscapedAt(text, index) {
  let slashes = 0;
  for (let position = index - 1; position >= 0 && text[position] === "\\"; position -= 1) slashes += 1;
  return slashes % 2 === 1;
}

function findUnescapedDelimiter(text, delimiter, start) {
  let index = start;
  while (index < text.length) {
    index = text.indexOf(delimiter, index);
    if (index < 0) return -1;
    if (!isEscapedAt(text, index) && !(delimiter === "$" && text[index + 1] === "$")) return index;
    index += delimiter.length;
  }
  return -1;
}

function latexEnvironmentAt(text, index) {
  const start = String(text || "").slice(index).match(/^\\begin\{([A-Za-z*]+)\}/);
  if (!start) return null;
  const environment = start[1];
  const allowed = new Set(["equation", "equation*", "align", "align*", "aligned", "gather", "gather*", "gathered", "multline", "multline*", "split", "cases", "matrix", "pmatrix", "bmatrix", "vmatrix", "Vmatrix", "array"]);
  if (!allowed.has(environment)) return null;
  const expressionStart = index + start[0].length;
  const endToken = `\\end{${environment}}`;
  const endStart = text.indexOf(endToken, expressionStart);
  if (endStart < 0) return null;
  return { environment, expressionStart, expressionEnd: endStart, end: endStart + endToken.length };
}

function normalizeMathExpression(expression, environment = "") {
  const body = String(expression || "").trim();
  if (!environment) return body;
  if (/^equation\*?$/.test(environment)) return body;
  if (/^align\*?$/.test(environment)) return `\\begin{aligned}${body}\\end{aligned}`;
  if (/^(gather|multline)\*?$/.test(environment)) return `\\begin{gathered}${body}\\end{gathered}`;
  return `\\begin{${environment}}${body}\\end{${environment}}`;
}

function isLikelyDollarMath(expression) {
  const trimmed = String(expression || "").trim();
  if (!trimmed || /\n/.test(trimmed)) return false;
  if (/^\d+(?:[.,]\d+)?$/.test(trimmed)) return false;
  if (/[\\_^{}=<>+\-*/]|[∑∫√∞≈≠≤≥±×÷]/.test(trimmed)) return true;
  if (/\b(?:frac|sum|int|lim|sqrt|alpha|beta|gamma|delta|theta|lambda|mu|sigma|mathbb|mathcal|mathrm|mathbf|left|right)\b/i.test(trimmed)) return true;
  if (/^[A-Za-z][A-Za-z0-9']*$/.test(trimmed)) return true;
  return trimmed.length <= 48 && /[A-Za-z]/.test(trimmed) && /\d/.test(trimmed);
}

function splitMathFragments(text) {
  const raw = String(text ?? "");
  const parts = [];
  let cursor = 0;
  let index = 0;
  const pushText = end => {
    if (end > cursor) parts.push({ type: "text", text: raw.slice(cursor, end) });
  };
  const pushMath = (start, expressionStart, expressionEnd, end, display) => {
    pushText(start);
    parts.push({ type: "math", raw: raw.slice(start, end), expression: raw.slice(expressionStart, expressionEnd), display });
    cursor = end;
    index = end;
  };
  const pushEnvironmentMath = (start, environmentInfo) => {
    pushText(start);
    parts.push({
      type: "math",
      raw: raw.slice(start, environmentInfo.end),
      expression: normalizeMathExpression(raw.slice(environmentInfo.expressionStart, environmentInfo.expressionEnd), environmentInfo.environment),
      display: true,
    });
    cursor = environmentInfo.end;
    index = environmentInfo.end;
  };
  while (index < raw.length) {
    if (raw.startsWith("\\begin{", index) && !isEscapedAt(raw, index)) {
      const environmentInfo = latexEnvironmentAt(raw, index);
      if (environmentInfo) {
        pushEnvironmentMath(index, environmentInfo);
        continue;
      }
    }
    if (raw.startsWith("$$", index) && !isEscapedAt(raw, index)) {
      const close = findUnescapedDelimiter(raw, "$$", index + 2);
      if (close > index + 2) {
        pushMath(index, index + 2, close, close + 2, true);
        continue;
      }
    }
    if (raw.startsWith("\\[", index) && !isEscapedAt(raw, index)) {
      const close = findUnescapedDelimiter(raw, "\\]", index + 2);
      if (close > index + 2) {
        pushMath(index, index + 2, close, close + 2, true);
        continue;
      }
    }
    if (raw.startsWith("\\(", index) && !isEscapedAt(raw, index)) {
      const close = findUnescapedDelimiter(raw, "\\)", index + 2);
      if (close > index + 2) {
        pushMath(index, index + 2, close, close + 2, false);
        continue;
      }
    }
    if (raw[index] === "$" && raw[index + 1] !== "$" && !isEscapedAt(raw, index)) {
      const close = findUnescapedDelimiter(raw, "$", index + 1);
      if (close > index + 1 && isLikelyDollarMath(raw.slice(index + 1, close))) {
        pushMath(index, index + 1, close, close + 1, false);
        continue;
      }
    }
    index += 1;
  }
  pushText(raw.length);
  return parts;
}

function displayTextPreservingMath(text, options = {}) {
  const raw = options.trim === false ? String(text ?? "") : String(text ?? "").trim();
  return splitMathFragments(raw).map(part => part.type === "math" ? part.raw : displayText(part.text, { trim: false })).join("");
}

function renderMathFragment(part) {
  const fallback = `<span class="math-fallback">${escapeHtml(part.raw)}</span>`;
  const renderer = window.katex?.renderToString;
  if (typeof renderer !== "function") return fallback;
  try {
    const html = renderer(String(part.expression || "").trim(), {
      displayMode: Boolean(part.display),
      throwOnError: false,
      strict: "ignore",
      trust: false,
      output: "htmlAndMathml",
    });
    return `<span class="${part.display ? "math-display" : "math-inline"}" data-annotation-source-length="${part.raw.length}">${html}</span>`;
  } catch (error) {
    return fallback;
  }
}

function renderInlineContent(text, options, renderTextPart) {
  const cleaned = displayTextPreservingMath(text, { trim: options?.trim !== false });
  return splitMathFragments(cleaned).map(part => part.type === "math" ? renderMathFragment(part) : renderTextPart(part.text)).join("");
}

function extractReferenceNumbers(label) {
  const numbers = [];
  for (const part of String(label || "").split(",")) {
    const trimmed = part.trim();
    const range = trimmed.match(/^(\d+)\s*[-–]\s*(\d+)$/);
    if (range) {
      const start = Number(range[1]);
      const end = Number(range[2]);
      if (Number.isFinite(start) && Number.isFinite(end) && end >= start && end - start < 30) {
        for (let number = start; number <= end; number += 1) numbers.push(String(number));
      }
      continue;
    }
    if (/^\d+$/.test(trimmed)) numbers.push(trimmed);
  }
  return [...new Set(numbers)].filter(number => state.references[number]);
}

function linkCitations(htmlText) {
  const withParagraphRefs = htmlText.replace(/\[(p-\d{4})(?:\s*[-–]\s*(p-\d{4}))?\]/gi, (match, start, end) => {
    const cleanStart = String(start || "").toLowerCase();
    const cleanEnd = String(end || "").toLowerCase();
    const label = cleanEnd && cleanEnd !== cleanStart ? `${cleanStart}-${cleanEnd}` : cleanStart;
    return `<button class="citation-link paragraph-ref" data-paragraph-ref="${escapeHtml(cleanStart)}" ${cleanEnd ? `data-end-paragraph-ref="${escapeHtml(cleanEnd)}"` : ""} title="Jump to source paragraph ${escapeHtml(label)}">[${escapeHtml(label)}]</button>`;
  });
  return withParagraphRefs.replace(/\[(\d+(?:\s*,\s*\d+|\s*[-–]\s*\d+)*)\]/g, (match, label) => {
    const numbers = extractReferenceNumbers(label);
    if (!numbers.length) return match;
    return `<button class="citation-link" data-ref-list="${escapeHtml(numbers.join(","))}" title="查看参考文献 ${escapeHtml(match)}">${escapeHtml(match)}</button>`;
  });
}

function assetUrl(src) {
  return assetUrlForPaper(state.currentPaperId, src);
}

function assetUrlForPaper(paperId, src) {
  const clean = String(src || "").trim().replace(/^['"]|['"]$/g, "").replace(/^\.\//, "");
  if (!clean) return "";
  if (/^(https?:|data:|blob:|\/)/i.test(clean)) return clean;
  return `/api/papers/${encodeURIComponent(paperId || state.currentPaperId)}/assets/${clean.split("/").map(encodeURIComponent).join("/")}`;
}

function markdownImageInfo(text) {
  const match = String(text || "").match(/!\[([^\]]*)\]\(([^)]+)\)/);
  return match ? { alt: match[1] || "Paper image", src: match[2] || "" } : null;
}

function stripTranslationImages(text) {
  return String(text || "")
    .replace(/!\[(?:\\.|[^\]\\])*\]\((?:\\.|[^\\()]|\([^()]*\))*\)/g, " ")
    .replace(/<img\b[^>]*>/gi, " ");
}

function translationMathParts(text) {
  const raw = String(text || "");
  const protectedRanges = [];
  const fences = /^[ \t]*(`{3,}|~{3,})[^\r\n]*(?:\r?\n|$)/gm;
  let fence;
  while ((fence = fences.exec(raw))) {
    const close = new RegExp(`^[ \\t]*${fence[1][0]}{${fence[1].length},}[ \\t]*$`, "gm");
    close.lastIndex = fences.lastIndex;
    const end = close.exec(raw);
    const endOffset = end ? close.lastIndex : raw.length;
    protectedRanges.push({ start: fence.index, end: endOffset });
    fences.lastIndex = endOffset;
  }
  for (const match of raw.matchAll(/(`+)([\s\S]*?)\1(?!`)/g)) {
    if (!isEscapedAt(raw, match.index)) protectedRanges.push({ start: match.index, end: match.index + match[0].length });
  }
  for (const match of raw.matchAll(/`+/g)) {
    if (!isEscapedAt(raw, match.index) && !protectedRanges.some(range => match.index >= range.start && match.index < range.end)) {
      protectedRanges.push({ start: match.index, end: raw.length });
      break;
    }
  }
  let offset = 0;
  return splitMathFragments(raw).flatMap(part => {
    const start = offset;
    offset += (part.type === "math" ? part.raw : part.text).length;
    if (part.type !== "math" || protectedRanges.some(range => start < range.end && offset > range.start)) return [];
    if (part.raw.startsWith("$") && !part.display && /^\s*\d/.test(part.expression)
      && /^\d/.test(raw.slice(offset))) return [];
    return [{ ...part, start, end: offset }];
  });
}

function omitTextRanges(text, omissions) {
  let result = "";
  let cursor = 0;
  for (const range of omissions) {
    result += text.slice(cursor, range.start);
    cursor = range.end;
  }
  return result + text.slice(cursor);
}

function isMathOnlyText(text, parts = translationMathParts(text)) {
  if (!parts.length) return false;
  const remainder = omitTextRanges(text, parts).replace(/\\(?:tag|label)\*?\s*\{[^{}]*\}/g, "");
  return !remainder.replace(/[\s\d()[\]{}.,;:!?+=\-–—，。；：！？]/gu, "");
}

function comparableMath(expression) {
  return String(expression || "").replace(/\\(?:tag|label)\*?\s*\{[^{}]*\}/g, "")
    .replace(/\\(?:left|right)\b/g, "").replace(/\s+/g, "");
}

function translationPresentation(segment) {
  const raw = displayTextPreservingMath(segment?.translation || "", { trim: false });
  if (segment?.kind === "code" || !/[$\\]/.test(segment?.markdown || "") || !/[$\\]/.test(raw)) return { text: raw, omissions: [] };
  const source = stripTranslationImages(displayTextPreservingMath(segment?.markdown || "", { trim: false }));
  const sourceParts = translationMathParts(source);
  if (!sourceParts.length) return { text: raw, omissions: [] };
  const translatedParts = translationMathParts(raw);
  const mathOnlySource = isMathOnlyText(source, sourceParts);
  const originals = new Set(sourceParts.filter(part => part.display || mathOnlySource).map(part => comparableMath(part.expression)));
  if (isMathOnlyText(stripTranslationImages(raw)) && (mathOnlySource
    || translatedParts.every(part => originals.has(comparableMath(part.expression))))) {
    return { text: "", omissions: [{ start: 0, end: raw.length }] };
  }
  const omissions = translatedParts.filter(part => part.display && originals.has(comparableMath(part.expression)))
    .map(({ start, end }) => {
      const number = raw.slice(end).match(/^[ \t]*(?:\r?\n[ \t]*)?[(（]\d+[a-z]?[)）](?=[ \t]*(?:\r?\n|$))/i);
      return { start, end: end + (number?.[0].length || 0) };
    });
  return { text: omitTextRanges(raw, omissions), omissions };
}

function displayedOffset(originalOffset, omissions) {
  return originalOffset - omissions.reduce((removed, range) =>
    removed + Math.max(0, Math.min(originalOffset, range.end) - range.start), 0);
}

function originalTranslationOffset(segment, offset, edge) {
  const { omissions } = translationPresentation(segment);
  let removed = 0;
  for (const range of omissions) {
    const boundary = range.start - removed;
    if (offset < boundary || (offset === boundary && edge === "end")) break;
    removed += range.end - range.start;
  }
  return offset + removed;
}

function annotationDisplayRanges(raw, annotations, target, omissions = []) {
  // Keep stored ranges in the original text; only project their visible endpoints.
  const ranges = annotations.map(annotation => {
    const range = normalizedAnnotationRange(annotation, raw, target);
    return { annotation, range: range && {
      start: displayedOffset(range.start, omissions), end: displayedOffset(range.end, omissions),
    } };
  }).filter(item => item.range && item.range.end > item.range.start)
    .sort((a, b) => a.range.start - b.range.start || a.range.end - b.range.end);
  return { text: omitTextRanges(raw, omissions), ranges };
}

function annotationMediaSrc(annotation, paperId = state.currentPaperId) {
  if (annotation?.media_src) return assetUrlForPaper(paperId, annotation.media_src);
  const direct = markdownImageInfo(annotation?.quote || "");
  if (direct?.src) return assetUrlForPaper(paperId, direct.src);
  const segment = paperId === state.currentPaperId ? segmentForId(annotation?.segment_id) : null;
  const fromSegment = markdownImageInfo(segment?.markdown || "");
  return fromSegment?.src ? assetUrlForPaper(paperId, fromSegment.src) : "";
}

const figureReferencePattern = /\b(?:fig(?:ure)?\.?)\s*(\d+)(?:\s*\([a-z]\)|[a-z]|[.-][a-z])?/gi;

function linkFigures(htmlText) {
  return String(htmlText || "").split(/(<[^>]+>)/g).map(part => {
    if (part.startsWith("<")) return part;
    return part.replace(figureReferencePattern, (match, number) => {
      if (!state.figures[number]) return match;
      return `<button class="figure-ref" data-figure-number="${escapeHtml(number)}" title="查看 ${escapeHtml(match)}">${escapeHtml(match)}</button>`;
    });
  }).join("");
}

function autolinkPlainUrlsAndDois(htmlText) {
  const linkToken = token => {
    let clean = String(token || "");
    let trailing = "";
    while (clean && /[.,);\]]/.test(clean.at(-1))) {
      trailing = clean.at(-1) + trailing;
      clean = clean.slice(0, -1);
    }
    const href = /^https?:\/\//i.test(clean) ? clean : `https://doi.org/${clean}`;
    return `<a href="${escapeHtml(href)}" target="_blank" rel="noreferrer">${escapeHtml(clean)}</a>${escapeHtml(trailing)}`;
  };
  return String(htmlText || "").split(/(<a\b[^>]*>.*?<\/a>|<[^>]+>)/gi).map(part => {
    if (!part || part.startsWith("<")) return part;
    return part.replace(/(?<![\w/])(https?:\/\/[^\s<]+|10\.\d{4,9}\/[^\s<]+)/gi, match => linkToken(match));
  }).join("");
}

function inlineMarkdown(text, options = {}) {
  return renderInlineContent(text, options, rawPart => {
  let safe = escapeHtml(displayText(options.images === false ? stripTranslationImages(rawPart) : rawPart, { trim: false }));
  safe = safe.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (match, alt, src) => {
    if (options.images === false) return "";
    const url = assetUrl(src);
    if (!url) return match;
    return `<button class="paper-figure-image" data-figure-src="${escapeHtml(url)}" title="${escapeHtml(alt || "Open figure")}"><img src="${escapeHtml(url)}" alt="${escapeHtml(alt || "Paper figure")}" loading="lazy"></button>`;
  });
  safe = safe.replace(/`([^`]+)`/g, "<code>$1</code>");
  safe = safe.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  safe = safe.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  safe = safe.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');
  safe = autolinkPlainUrlsAndDois(safe);
  if (options.citations) safe = linkCitations(safe);
  safe = linkFigures(safe);
  return safe;
  });
}

function getAnnotationsFor(paragraphId) {
  return state.annotations.filter(item => item.segment_id === paragraphId);
}

function mediaAnnotationsFor(paragraphId) {
  return getAnnotationsFor(paragraphId).filter(item => ["media", "table"].includes(item.target));
}

function isTeacherDefinition(annotation) {
  return annotation?.origin?.kind === "reading-teacher" && annotation.origin.content_type === "definition";
}

function annotationKindLabel(annotation) {
  if (annotation?.source_scope === "thinking" || annotation?.target === "thinking") {
    return (annotation?.thinking_block_id || annotation?.block_id) === paperBriefBlockId ? "Paper Brief" : "AI output";
  }
  if (annotation?.target === "media") return "图片";
  if (markdownImageInfo(annotation?.quote || "")) return "图片";
  if (annotation?.target === "table") return "表格";
  return annotation?.target === "translation" ? "中文" : "原文";
}

function annotationNoteCardText(annotation) {
  const note = displayText(annotation?.note || "");
  if (!note) return "";
  const sourceTexts = [annotation?.quote, annotation?.group_quote]
    .map(value => displayText(value || ""))
    .filter(value => value.length >= 24);
  for (const sourceText of sourceTexts) {
    if (note === sourceText) return "";
    if (note.startsWith(sourceText)) {
      return note.slice(sourceText.length).replace(/^[\s:：,，.;。\-—–|]+/, "").trim();
    }
  }
  return note;
}

function annotationGroupId(annotation) {
  if (annotation?.annotation_group_id) return String(annotation.annotation_group_id);
  const match = String(annotation?.id || "").match(/^(ag-[a-z0-9]+)-\d+$/i);
  return match ? match[1] : "";
}

function annotationGroupIndex(annotation) {
  if (annotation?.group_index !== undefined) return Number(annotation.group_index || 0);
  const match = String(annotation?.id || "").match(/^ag-[a-z0-9]+-(\d+)$/i);
  return match ? Number(match[1]) : 0;
}

function annotationsInGroup(groupId, annotations = state.annotations || []) {
  return groupId ? annotations.filter(item => annotationGroupId(item) === groupId) : [];
}

function segmentMediaInfo(segment, target = "media") {
  const markdown = segment?.markdown || "";
  const imageMatch = markdown.match(/!\[([^\]]*)\]\(([^)]+)\)/);
  if (target === "media" && imageMatch) {
    return { target: "media", label: imageMatch[1] || "Paper image", quote: imageMatch[1] || displayText(markdown).slice(0, 160) || "Paper image", src: assetUrl(imageMatch[2]) };
  }
  const plain = displayText(markdown).replace(/\s+/g, " ");
  return { target: target === "table" ? "table" : "media", label: target === "table" ? "Table" : "Media", quote: plain.slice(0, 220) || (target === "table" ? "Table" : "Media"), src: "" };
}

function mediaAnnotationFor(segmentId, target) {
  return getAnnotationsFor(segmentId).find(item => item.target === target) || null;
}

function effectiveAnnotationsFor(paragraphId, target) {
  const segment = state.payload?.segments?.find(item => item.id === paragraphId);
  return getAnnotationsFor(paragraphId).map(annotation => {
    const directTarget = annotation.target || "source";
    if (!segment || directTarget === target || !annotation.range) return annotation;
    const recalculated = pairedRangeForSelection(segment, {
      target: directTarget,
      range: annotation.range,
      quote: annotation.quote || "",
    });
    return recalculated?.target === target ? { ...annotation, paired_range: recalculated } : { ...annotation, paired_range: null };
  });
}

function uniqueTags(tags) {
  const values = Array.isArray(tags) ? tags : String(tags || "").split(",");
  return [...new Set(values.map(tag => String(tag || "").trim()).filter(Boolean))];
}

function rangeForQuote(text, quote) {
  const raw = String(text ?? "");
  const index = quote ? raw.indexOf(quote) : -1;
  return index >= 0 ? { start: index, end: index + quote.length } : null;
}

function normalizedAnnotationRange(annotation, text, target) {
  const raw = String(text ?? "");
  const isDirectTarget = (annotation.target || "source") === target;
  const directRange = isDirectTarget ? annotation.range : annotation.paired_range;
  if (directRange && Number.isFinite(Number(directRange.start)) && Number.isFinite(Number(directRange.end))) {
    const start = Math.max(0, Math.min(raw.length, Number(directRange.start)));
    const end = Math.max(start, Math.min(raw.length, Number(directRange.end)));
    if (end > start) return { start, end };
  }
  if (isDirectTarget && annotation.quote) return rangeForQuote(raw, displayTextPreservingMath(annotation.quote)) || { start: 0, end: raw.length };
  if (isDirectTarget && annotation.color) return { start: 0, end: raw.length };
  return null;
}

function inlineThinkingNoteChip(annotation) {
  const note = displayText(annotation?.note || "");
  if (!note) return "";
  return `<button class="inline-thinking-note-chip" data-inline-thinking-note="${escapeHtml(annotation.id || "")}" title="${escapeHtml(note)}">${escapeHtml(note)}</button>`;
}

function splitInlineHtmlWithHighlights(text, annotations, target, options = {}) {
  const { text: raw, ranges } = annotationDisplayRanges(displayTextPreservingMath(text, { trim: false }),
    annotations, target, options.omissions);
  if (!ranges.length) return inlineMarkdown(raw, options);
  const parts = [];
  let cursor = 0;
  for (const { annotation, range } of ranges) {
    const start = Math.max(cursor, range.start);
    const end = Math.max(start, range.end);
    if (start > cursor) parts.push(inlineMarkdown(raw.slice(cursor, start), options));
    const color = annotation.color || "yellow";
    const title = annotation.note || annotation.quote || "Highlight";
    parts.push(`<mark class="hl-${escapeHtml(color)}" data-annotation-id="${escapeHtml(annotation.id || "")}" title="${escapeHtml(title)}">${inlineMarkdown(raw.slice(start, end), options)}</mark>`);
    if (target === "thinking" && annotation.show_inline_note_chip !== false) parts.push(inlineThinkingNoteChip(annotation));
    cursor = end;
  }
  if (cursor < raw.length) parts.push(inlineMarkdown(raw.slice(cursor), options));
  return parts.join("");
}

function applyHighlights(text, paragraphId, target, options = {}) {
  return splitInlineHtmlWithHighlights(text, effectiveAnnotationsFor(paragraphId, target), target, {
    ...options, citations: target === "source", images: target !== "translation",
  });
}

function isHtmlTable(text) {
  return /<table[\s>]/i.test(String(text || ""));
}

function isTextTableSegment(segment) {
  const text = String(segment.markdown || "");
  return isHtmlTable(text) || text.includes("\n|")
    || (segment.kind === "table" && !markdownImageInfo(text));
}

function renderHtmlTable(text, options = {}) {
  const raw = String(text || "");
  const tableStart = raw.search(/<table[\s>]/i);
  const caption = tableStart > 0 ? displayText(raw.slice(0, tableStart)) : "";
  const parser = new DOMParser();
  const doc = parser.parseFromString(raw, "text/html");
  const table = doc.querySelector("table");
  if (!table) return `<pre class="source-text">${escapeHtml(displayTextPreservingMath(text))}</pre>`;
  const rows = Array.from(table.querySelectorAll("tr")).map(row => {
    const cells = Array.from(row.children).filter(cell => /^(td|th)$/i.test(cell.tagName));
    const html = cells.map(cell => {
      const tag = cell.tagName.toLowerCase() === "th" ? "th" : "td";
      const rowspan = Math.max(1, Math.min(20, Number(cell.getAttribute("rowspan") || 1)));
      const colspan = Math.max(1, Math.min(20, Number(cell.getAttribute("colspan") || 1)));
      const attrs = `${rowspan > 1 ? ` rowspan="${rowspan}"` : ""}${colspan > 1 ? ` colspan="${colspan}"` : ""}`;
      return `<${tag}${attrs}>${inlineMarkdown(cell.textContent, { ...options, citations: true })}</${tag}>`;
    }).join("");
    return html ? `<tr>${html}</tr>` : "";
  }).filter(Boolean).join("");
  if (!rows) return `<pre class="source-text">${escapeHtml(displayTextPreservingMath(text))}</pre>`;
  return `${caption ? `<div class="table-caption source-text">${inlineMarkdown(caption, { ...options, citations: true })}</div>` : ""}<div class="table-wrap"><table class="paper-table">${rows}</table></div>`;
}

const tableTranslationMap = {
  "Table 1: Paul-Elder Critical Thinking Framework [77]: Elements and Standards for Data-Driven Decision-Making": "表 1：Paul-Elder 批判性思维框架 [77]：数据驱动决策中的要素与标准",
  "Table 4: Aggregated Analysis of Likert Scale Questions with Categorization": "表 4：Likert 量表问题的分类汇总分析",
  "Challenge (C)": "挑战（C）",
  "Observed Behavior (B)": "观察到的行为（B）",
  "Design Goal (DG)": "设计目标（DG）",
  "System Feature": "系统功能",
  "C1. Inconsistent Reflection Support": "C1. 反思支持不一致",
  "B1. Manual reflection practices rely on indi- vidual discipline and memory": "B1. 手动反思实践依赖个人自律与记忆",
  "B2. Insight recording happens in separate doc- uments disconnected from codes": "B2. 洞见记录发生在与代码脱节的独立文档中",
  "DG1. Systematic In-the-Moment Reflexivity Support": "DG1. 系统化的即时反思支持",
  "(A) In-situ reflexive exercises": "（A）情境内反思练习",
  "C2. Untracked Code Evolution": "C2. 代码演化缺乏跟踪",
  "B3. Version control documentation is labor- intensive and inconsistent": "B3. 版本控制记录劳动密集且不一致",
  "DG2. Automated Code Evolution Tracking": "DG2. 自动化代码演化跟踪",
  "() Analytical history": "（B）分析历史",
  "B4. Reactive change management relies on re- searcher awareness to trigger documentation": "B4. 反应式变更管理依赖研究者察觉后才触发记录",
  "(C) Code drift alert": "（C）代码漂移提醒",
  "C3. Inaccessible Collaboration Perspectives": "C3. 协作视角不可获得",
  "B5. Information gathering relies on voluntary self-disclosure in meetings": "B5. 信息收集依赖会议中的自愿自我披露",
  "DG3. Collaborative Positionality Integration": "DG3. 协作式位置性整合",
  "(D) Positionality-aware discussion prompts": "（D）具备位置性感知的讨论提示",
  "B6. Structured discussion happens separately from actual coding decisions": "B6. 结构化讨论与实际编码决策分离",
  "E) Discussion focus for disagreements": "（E）面向分歧的讨论焦点",
  "B7. Proactive reflective prompting occurs in- formally and sporadically": "B7. 主动反思提示仅以非正式且零散的方式出现",
  "Group #": "组别",
  "ID": "编号",
  "Current Role": "当前角色",
  "Primary Domain": "主要领域",
  "Experience (Years)": "经验（年）",
  "Full RTA Comfort Level (1-7)": "完整 RTA 熟悉程度（1-7）",
  "Assistant Professor": "助理教授",
  "PhD Student": "博士生",
  "PhD Graduate": "博士毕业生",
  "MSc Student": "硕士生",
  "Data Analyst": "数据分析师",
  "Data Allocation/Engineer": "数据分配/工程",
  "Software Engineering": "软件工程",
  "HCI + Info. Vis.": "HCI + 信息可视化",
  "HCI + Comp. Ed.": "HCI + 计算教育",
  "RTA Experience (simplified)": "RTA 经验（简化）",
  "View on Topic of Analysis (simplified)": "对分析主题的看法（简化）",
  "Grad course; collaborative application": "研究生课程；协作应用",
  "Four projects; varied data types": "四个项目；多种数据类型",
  "Published research": "已发表研究",
  "Coursework familiarity; partial application": "课程中熟悉；部分应用",
  "PhD course; one project": "博士课程；一个项目",
  "Applied to literature & interviews": "应用于文献与访谈",
  "Applied to student perspectives": "应用于学生视角",
  "Coursework & independent training": "课程学习与独立训练",
  "Master's course; five studies": "硕士课程；五项研究",
  "PhD research; multiple methods (interviews, diaries)": "博士研究；多种方法（访谈、日记）",
  "Initial phase reflexive coding": "初始阶段的反思性编码",
  "Applied to dementia transcripts": "应用于痴呆症逐字稿",
  "HCI, User-centered, Fairness": "HCI、以用户为中心、公平性",
  "Immigrant, System-distrust, Cautious": "移民、对系统不信任、谨慎",
  "AI-skeptic, Citizen-focused, Socially-critical": "对 AI 持怀疑态度、关注公民、具社会批判性",
  "Lived experience, Pro-transparency, Balanced": "生活经验、支持透明性、平衡",
  "Urban planning, Nuanced, Anti-luddism": "城市规划、细致审慎、反技术恐慌",
  "Urbanist, Anti-surveillance, Policy-first": "城市主义者、反监控、政策优先",
  "Interpretivist, Critical, Reflexive": "解释主义、批判性、反思性",
  "Black American, Equity-focused, Data-informed": "美国黑人、关注公平、数据知情",
  "Skeptical, Accuracy-focused, Pro-supervision": "怀疑态度、关注准确性、支持监督",
  "International, Socio-cultural, Chatbot researcher": "国际视角、社会文化、聊天机器人研究者",
  "HCI/Healthcare, Immigrant-lens, Fairness-focused": "HCI/医疗健康、移民视角、关注公平性",
  "Dementia-informed, Accessibility-focused, Pro-AI": "痴呆症知情、关注可访问性、支持 AI",
  "Q#": "题号",
  "Question Text": "问题文本",
  "Mean": "均值",
  "Median": "中位数",
  "SD": "标准差",
  "Supporting Reflexive Analysis (RQ1)": "支持反思性分析（RQ1）",
  "Timely in-flow reflection": "及时的流程内反思",
  "Articulate code rationale": "阐明代码理由",
  "Connect positionality to decisions": "将位置性与决策关联",
  "Consider alternative interpretations": "考虑替代解释",
  "Re-read data more carefully": "更仔细地重读数据",
  "Felt immersed in data": "感觉沉浸于数据中",
  "Would keep reflection prompts on": "愿意保留反思提示",
  "Transparent Code Evolution (RQ2)": "透明的代码演化（RQ2）",
  "Analysis History": "分析历史",
  "Easily see code changes over time": "容易看到代码随时间变化",
  "Increased transparency of research process": "提升研究过程透明度",
  "Code Drift Alert": "代码漂移提醒",
  "Surfaced potential meaningful shifts... Improved the quality of our analysis": "呈现潜在有意义的变化……提升了我们的分析质量",
  "Helped me articulate code boundary...": "帮助我阐明代码边界……",
  "Scaffolding Collaborative Interpretation (RQ3)": "支架协作式解释（RQ3）",
  "Positionality-aware Discussion Prompt": "具备位置性感知的讨论提示",
  "Reframe disagreement focus": "重新框定分歧焦点",
  "Element": "要素",
  "Definition": "定义",
  "Standard": "标准",
  "Assessment Criteria": "评估准则",
  "Purpose": "目的",
  "The overarching goal directing the reasoning pro- cess.": "引导推理过程的总体目标。",
  "Question at Issue": "待解决问题",
  "The specific problem and sub-problems requiring resolution.": "需要解决的具体问题与子问题。",
  "Assumptions": "假设",
  "Underlying beliefs and presuppositions supporting the reasoning process.": "支撑推理过程的底层信念与预设。",
  "Point of View": "视角",
  "The perspective from which the reasoning is made.": "进行推理时所采取的视角。",
  "Concepts": "概念",
  "Theoretical constructs, definitions, and principles shaping analytical frameworks.": "塑造分析框架的理论构念、定义与原则。",
  "Data / Evidence": "数据/证据",
  "Factual foundation supporting reasoning pro- cesses.": "支撑推理过程的事实基础。",
  "Inferences": "推论",
  "Logical conclusions derived from available evi- dence.": "从可用证据中得出的逻辑结论。",
  "Implications": "影响",
  "Both intended consequences and potential unin- tended effects of proposed decisions.": "拟议决策的预期后果与潜在非预期影响。",
  "Clarity": "清晰性",
  "Evaluates comprehensibility and precision of reasoning ele- ments.": "评估推理要素的可理解性与表达精确度。",
  "Accuracy": "准确性",
  "Assesses factual correctness and empirical validity of claims.": "评估主张的事实正确性与经验有效性。",
  "Precision": "精确性",
  "Evaluates the specificity and detail of reasoning components.": "评估推理组成部分的具体性与细节程度。",
  "Relevance": "相关性",
  "Assesses the degree to which reasoning elements contribute to addressing the central question.": "评估推理要素对回答核心问题的贡献程度。",
  "Depth": "深度",
  "Evaluates whether reasoning adequately addresses inherent problem complexity.": "评估推理是否充分处理问题本身的复杂性。",
  "Breadth": "广度",
  "Assesses comprehensiveness of perspective and considera- tion of alternative approaches.": "评估视角的全面性以及对替代方案的考虑。",
  "Logic": "逻辑性",
  "Evaluates the internal consistency and validity of inferential processes.": "评估推论过程的内部一致性与有效性。",
  "Significance": "重要性",
  "Assesses whether reasoning focuses on the most consequen- tial aspects.": "评估推理是否聚焦最具后果性的方面。",
  "Fairness": "公平性",
  "Evaluates reasoning for bias, self-interest, and adequate stakeholder consideration.": "评估推理中是否存在偏见、自利，以及是否充分考虑利益相关者。",
};

function normalizeTableText(text) {
  return displayText(text, { trim: true })
    .replace(/\b([A-Za-z]{2,})-\s+([A-Za-z]{2,})\b/g, "$1$2")
    .replace(/\s+/g, " ");
}

const tableTermTranslations = {
  "Participant": "参与者",
  "Participants": "参与者",
  "Condition": "条件",
  "Conditions": "条件",
  "Task": "任务",
  "Tasks": "任务",
  "Theme": "主题",
  "Themes": "主题",
  "Category": "类别",
  "Categories": "类别",
  "Code": "编码",
  "Codes": "编码",
  "Description": "描述",
  "Example": "示例",
  "Examples": "示例",
  "Quote": "引文",
  "Quotes": "引文",
  "Finding": "发现",
  "Findings": "发现",
  "Result": "结果",
  "Results": "结果",
  "Measure": "指标",
  "Measures": "指标",
  "Metric": "指标",
  "Metrics": "指标",
  "Variable": "变量",
  "Variables": "变量",
  "Baseline": "基线",
  "Approach": "方法",
  "Method": "方法",
  "System": "系统",
  "Feature": "功能",
  "Features": "功能",
  "Benefit": "收益",
  "Benefits": "收益",
  "Limitation": "局限",
  "Limitations": "局限",
  "Accuracy": "准确性",
  "Preference": "偏好",
  "Frequency": "频次",
  "Count": "数量",
  "Total": "总计",
  "Average": "平均值",
  "Mean": "均值",
  "Median": "中位数",
  "Standard deviation": "标准差",
  "Significant": "显著",
  "Not significant": "不显著",
  "Strongly agree": "非常同意",
  "Agree": "同意",
  "Neutral": "中立",
  "Disagree": "不同意",
  "Strongly disagree": "非常不同意",
  "Yes": "是",
  "No": "否",
  "Before": "之前",
  "After": "之后",
};

function translateTableText(text) {
  const normalized = normalizeTableText(text);
  if (!normalized) return "";
  if (/^[\d.\-\s]+$/.test(normalized) || /^P\d+$/i.test(normalized) || /^Q\d+[A-Z]?$/i.test(normalized)) return normalized;
  if (tableTranslationMap[normalized]) return tableTranslationMap[normalized];
  const protectedTerms = new Map();
  let translated = normalized.replace(/\b(HCI|NLP|RTA|LLM|AI|CHI|CSCW|UIST|ACM|ReflexiveLens|Callisto)\b/g, match => {
    const key = `__TERM_${protectedTerms.size}__`;
    protectedTerms.set(key, match);
    return key;
  });
  const replacements = [
    ["Postgraduate Researchers", "研究生研究者"], ["postgraduate researchers", "研究生研究者"],
    ["Data Scientist", "数据科学家"], ["Data Scientists", "数据科学家"],
    ["Participant", "参与者"], ["Participants", "参与者"], ["Researcher", "研究者"], ["Researchers", "研究者"],
    ["Condition", "条件"], ["Conditions", "条件"], ["Task", "任务"], ["Tasks", "任务"], ["Dataset", "数据集"],
    ["Measure", "指标"], ["Measures", "指标"], ["Metric", "指标"], ["Metrics", "指标"], ["Variable", "变量"],
    ["Mean", "均值"], ["Median", "中位数"], ["Standard Deviation", "标准差"], ["SD", "标准差"], ["Range", "范围"],
    ["Strongly Agree", "非常同意"], ["Agree", "同意"], ["Neutral", "中立"], ["Disagree", "不同意"], ["Strongly Disagree", "非常不同意"],
    ["Very Helpful", "非常有帮助"], ["Helpful", "有帮助"], ["Not Helpful", "没有帮助"], ["Useful", "有用"],
    ["Question Text", "问题文本"], ["Question", "问题"], ["Response", "回答"], ["Responses", "回答"],
    ["Category", "类别"], ["Categories", "类别"], ["Theme", "主题"], ["Themes", "主题"], ["Subtheme", "子主题"],
    ["Code", "编码"], ["Codes", "编码"], ["Example", "示例"], ["Examples", "示例"], ["Quote", "引文"], ["Quotes", "引文"], ["Description", "描述"],
    ["Design Goal", "设计目标"], ["Design Implication", "设计启示"], ["System Feature", "系统功能"], ["Feature", "功能"], ["Features", "功能"],
    ["Finding", "发现"], ["Findings", "发现"], ["Result", "结果"], ["Results", "结果"], ["Limitation", "局限"], ["Limitations", "局限"],
    ["Current Role", "当前角色"], ["Primary Domain", "主要领域"], ["Experience", "经验"], ["Year", "年份"], ["Years", "年"],
    ["Assistant Professor", "助理教授"], ["Professor", "教授"], ["PhD Student", "博士生"], ["PhD Graduate", "博士毕业生"], ["MSc Student", "硕士生"], ["Student", "学生"],
    ["Data Analyst", "数据分析师"], ["Software Engineering", "软件工程"], ["Healthcare", "医疗健康"], ["Education", "教育"],
    ["Analysis", "分析"], ["Discussion", "讨论"], ["Reflection", "反思"], ["Reflexive", "反思性"], ["Transparent", "透明"],
    ["Evolution", "演化"], ["Collaborative", "协作式"], ["Collaboration", "协作"], ["Interpretation", "解释"],
    ["Support", "支持"], ["Scaffolding", "支架"], ["Decision", "决策"], ["Reasoning", "推理"], ["Evidence", "证据"],
    ["Accuracy", "准确性"], ["Clarity", "清晰性"], ["Fairness", "公平性"], ["Relevance", "相关性"], ["Significance", "重要性"],
    ...Object.entries(tableTermTranslations),
  ];
  for (const [source, target] of replacements.sort((a, b) => b[0].length - a[0].length)) {
    translated = translated.replace(new RegExp(`\\b${regexEscape(source)}\\b`, "g"), target);
  }
  translated = translated.replace(/\bNo\.\b/gi, "编号").replace(/\bID\b/g, "编号").replace(/\bN\b/g, "N");
  for (const [key, value] of protectedTerms.entries()) translated = translated.replaceAll(key, value);
  return translated;
}

function translatedTableFromTranslation(translation) {
  const raw = String(translation || "").trim();
  if (!raw || !/[\u4e00-\u9fff]/.test(raw)) return "";
  if (isHtmlTable(raw)) return renderHtmlTable(raw, { images: false });
  if (raw.includes("\n|")) return renderPipeTable(raw, { images: false });
  return "";
}

function translatedHtmlTable(text) {
  const raw = String(text || "");
  const tableStart = raw.search(/<table[\s>]/i);
  const caption = tableStart > 0 ? translateTableText(raw.slice(0, tableStart)) : "";
  const parser = new DOMParser();
  const doc = parser.parseFromString(raw, "text/html");
  const table = doc.querySelector("table");
  if (!table) return "";
  const rows = Array.from(table.querySelectorAll("tr")).map(row => {
    const cells = Array.from(row.children).filter(cell => /^(td|th)$/i.test(cell.tagName));
    const html = cells.map(cell => {
      const tag = cell.tagName.toLowerCase() === "th" ? "th" : "td";
      const rowspan = Math.max(1, Math.min(20, Number(cell.getAttribute("rowspan") || 1)));
      const colspan = Math.max(1, Math.min(20, Number(cell.getAttribute("colspan") || 1)));
      const attrs = `${rowspan > 1 ? ` rowspan="${rowspan}"` : ""}${colspan > 1 ? ` colspan="${colspan}"` : ""}`;
      return `<${tag}${attrs}>${inlineMarkdown(translateTableText(cell.textContent), { citations: true })}</${tag}>`;
    }).join("");
    return html ? `<tr>${html}</tr>` : "";
  }).filter(Boolean).join("");
  return rows ? `${caption ? `<div class="table-caption source-text">${escapeHtml(caption)}</div>` : ""}<div class="table-wrap translated-table-wrap"><table class="paper-table translated-paper-table">${rows}</table></div>` : "";
}

function tableTranslationNoteHtml(translation) {
  const withoutTables = String(translation || "")
    .replace(/<table[\s\S]*?<\/table>/gi, "")
    .replace(/^\s*参考文献[：:]\s*/i, "")
    .trim();
  if (!withoutTables || !/[\u4e00-\u9fff]/.test(withoutTables)) return "";
  return `<div class="table-translation-note">${inlineMarkdown(withoutTables, { images: false })}</div>`;
}

function renderTableTranslation(paragraph) {
  if (!paragraph.translation) return "";
  const translatedFromModel = translatedTableFromTranslation(paragraph.translation || "");
  const note = tableTranslationNoteHtml(paragraph.translation || "");
  if (!translatedFromModel && !note) return "";
  return `<div class="translation table-translation"><div class="translation-label">中文表格</div>${translatedFromModel || note}</div>`;
}

function renderPipeTable(text, options = {}) {
  const rows = String(text || "").split("\n")
    .map(line => line.trim())
    .filter(line => line.startsWith("|"))
    .map(line => line.replace(/^\||\|$/g, "").split("|").map(cell => displayTextPreservingMath(cell)));
  const filtered = rows.filter(cells => !cells.every(cell => /^:?-{3,}:?$/.test(cell)));
  if (!filtered.length) return `<pre class="source-text">${escapeHtml(displayTextPreservingMath(text))}</pre>`;
  const body = filtered.map((cells, rowIndex) => `<tr>${cells.map(cell => `${rowIndex === 0 ? "<th>" : "<td>"}${inlineMarkdown(cell, { ...options, citations: true })}${rowIndex === 0 ? "</th>" : "</td>"}`).join("")}</tr>`).join("");
  return `<div class="table-wrap"><table class="paper-table">${body}</table></div>`;
}

function mediaAnnotationToolbarHtml(segment, target, innerHtml) {
  const annotation = mediaAnnotationFor(segment.id, target);
  const highlighted = Boolean(annotation);
  const label = target === "table" ? "Table" : "Image";
  return `
    <div class="media-annotatable ${highlighted ? "media-highlighted" : ""}" data-media-target="${escapeHtml(target)}" data-media-segment="${escapeHtml(segment.id)}" data-ignore-selection-offset="true">
      <div class="media-annotation-bar" data-ignore-selection-offset="true">
        <span>${escapeHtml(label)}</span>
        <button class="secondary-button mini-button" data-media-note="${escapeHtml(segment.id)}" data-media-kind="${escapeHtml(target)}">${highlighted ? "Edit note" : "Highlight + note"}</button>
      </div>
      ${innerHtml}
    </div>`;
}

function wrapMediaImageButtons(segment, html) {
  return String(html || "").replace(/<button class="paper-figure-image"[\s\S]*?<\/button>/g, imageHtml => mediaAnnotationToolbarHtml(segment, "media", imageHtml));
}

function paperTitle(entry) {
  return cleanPaperTitle(entry.title || entry.id || "Untitled");
}

function cleanPaperTitle(title) {
  return String(title || "").replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/<img\b[^>]*>/gi, " ").replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/^#{1,6}\s+/, "").replace(/\s+/g, " ").trim();
}

function paperPreviewImage(paper = {}) {
  return String(paper.preview_image || paper.cover_image || paper.thumbnail || "").trim();
}

function libraryPreviewThumbHtml(paper) {
  if (!state.libraryPreviewThumbnailsVisible) return "";
  const src = paperPreviewImage(paper);
  if (!src) return "";
  const url = assetUrlForPaper(paper.id, src);
  if (!url) return "";
  const alt = paper.preview_image_alt || `Preview image for ${paperTitle(paper)}`;
  return `<button class="library-paper-thumb" data-preview-paper="${escapeHtml(paper.id)}" type="button" title="Open paper preview">
    <img src="${escapeHtml(url)}" alt="${escapeHtml(alt)}" loading="lazy">
  </button>`;
}

function processingMode(paperOrMetadata = {}) {
  return paperOrMetadata.processing_mode || paperOrMetadata.reading_mode || "library-only";
}

function processingLabel(paperOrMetadata = {}) {
  const mode = processingMode(paperOrMetadata);
  return ({ "library-only": "Not parsed", skim: "Saved skim", deep: "Full text", "reference-card": "Reference card" })[mode] || mode;
}

function processingStatus(paperOrMetadata = {}) {
  return paperOrMetadata.processing_status || (processingMode(paperOrMetadata) === "deep" ? "ready" : "not_processed");
}

function paperParsingPending(metadata = {}) {
  return ["processing", "processing_queued", "paper_brief_processing", "paper_brief_ready"].includes(processingStatus(metadata));
}

function parseTimeMs(value) {
  const time = Date.parse(String(value || ""));
  return Number.isFinite(time) ? time : 0;
}

function readingActivitySummary(paper = {}) {
  return paper.reading_progress_summary && typeof paper.reading_progress_summary === "object" ? paper.reading_progress_summary : {};
}

function readingProgressLevel(paper = {}) {
  const summary = readingActivitySummary(paper);
  const coverage = Number(summary.coverage_ratio || 0);
  const careful = Number(summary.careful_ratio || 0);
  const briefCount = Number(summary.paper_brief_annotation_count || 0);
  const bodyTouched = coverage > 0 || Number(summary.total_visible_ms || 0) > 0 || Number(summary.visit_count || 0) > 0;
  if (coverage >= 0.8 || summary.read_status === "read") return 5;
  if (coverage >= 0.65 || careful >= 0.35) return 4;
  if (coverage >= 0.5) return 3;
  if (bodyTouched) return 2;
  if (briefCount > 0) return 1;
  return 0;
}

function readingProgressStageLabel(level) {
  return [
    "No reading trace yet",
    "Paper Brief marked",
    "Body reading started",
    "Body 50%+ read",
    "Mostly read / deep coverage",
    "Body 80%+ read",
  ][Math.max(0, Math.min(5, Number(level || 0)))] || "No reading trace yet";
}

function readingActivityScore(paper = {}) {
  const summary = readingActivitySummary(paper);
  const recentMs = parseTimeMs(paper.reading_progress_updated_at || summary.updated_at || "");
  const opened = recentMs > 0 ? 1 : 0;
  const coverage = Number(summary.coverage_ratio || 0);
  const careful = Number(summary.careful_ratio || 0);
  const notes = Number(summary.note_count || 0);
  const highlights = Number(summary.highlight_count || 0);
  const briefCount = Number(summary.paper_brief_annotation_count || 0);
  const visits = Number(summary.visit_count || 0);
  const visibleSeconds = Number(summary.total_visible_ms || 0) / 1000;
  return opened * 1000000 + readingProgressLevel(paper) * 50000 + coverage * 10000 + careful * 8000 + Math.min(visibleSeconds, 6 * 60 * 60) * 0.4 + Math.min(notes, 50) * 180 + Math.min(highlights, 120) * 60 + Math.min(briefCount, 20) * 50 + Math.min(visits, 500);
}

function compareRecentReadingActivity(left, right) {
  const leftRecent = parseTimeMs(left.reading_progress_updated_at || readingActivitySummary(left).updated_at || "");
  const rightRecent = parseTimeMs(right.reading_progress_updated_at || readingActivitySummary(right).updated_at || "");
  if (rightRecent !== leftRecent) return rightRecent - leftRecent;
  const scoreDiff = readingActivityScore(right) - readingActivityScore(left);
  if (scoreDiff) return scoreDiff;
  return paperTitle(left).localeCompare(paperTitle(right));
}

function normalizeTagsInput(value) {
  if (Array.isArray(value)) return value.map(tag => String(tag).trim()).filter(Boolean);
  return String(value || "").split(",").map(tag => tag.trim()).filter(Boolean);
}

function normalizeTitleKey(title) {
  return String(title || "")
    .normalize("NFKC")
    .toLocaleLowerCase()
    .replace(/[^\p{L}\p{N}]/gu, "");
}

function normalizeTitleKeyWithoutLeadingArticles(title) {
  return String(title || "")
    .normalize("NFKC")
    .toLocaleLowerCase()
    .replace(/^\s*(the|a|an)\s+/, "")
    .replace(/[^\p{L}\p{N}]/gu, "");
}

function titleKeyUsable(titleKey) {
  const cjkCount = Array.from(String(titleKey || "")).filter(char => /[\u4e00-\u9fff]/.test(char)).length;
  return String(titleKey || "").length >= 12 || cjkCount >= 6;
}

function libraryDuplicateByTitle(title, excludePaperId = "") {
  const titleKey = normalizeTitleKey(title);
  if (!titleKeyUsable(titleKey)) return null;
  const comparableTitleKey = normalizeTitleKeyWithoutLeadingArticles(title);
  return (state.library?.papers || []).find(paper => {
    if (excludePaperId && paper.id === excludePaperId) return false;
    const paperKey = paper.title_key || normalizeTitleKey(paperTitle(paper));
    const comparablePaperKey = normalizeTitleKeyWithoutLeadingArticles(paperTitle(paper));
    return (paperKey && paperKey === titleKey) || (titleKeyUsable(comparableTitleKey) && comparablePaperKey === comparableTitleKey);
  }) || null;
}

function duplicatePaperSummary(existing = {}) {
  return [paperAuthors(existing), paperJournal(existing), paperYear(existing), existing.read_status].filter(Boolean).join(" · ");
}

function normalizeReadingProgress(progress = {}) {
  const rawSegments = progress?.segments && typeof progress.segments === "object" ? progress.segments : {};
  const segments = {};
  for (const [segmentId, item] of Object.entries(rawSegments)) {
    if (!segmentId) continue;
    segments[segmentId] = {
      visible_ms: Math.max(0, Number(item?.visible_ms || 0)),
      visits: Math.max(0, Number(item?.visits || 0)),
      updated_at: String(item?.updated_at || ""),
      state: String(item?.state || "unread"),
      depth: Math.max(0, Math.min(0.92, Number(item?.depth || 0))),
      highlight_count: Math.max(0, Number(item?.highlight_count || 0)),
      note_count: Math.max(0, Number(item?.note_count || 0)),
    };
  }
  return { version: 1, paper_id: progress?.paper_id || state.currentPaperId || "", segments, summary: progress?.summary || {}, updated_at: progress?.updated_at || "" };
}

function ensureReadingProgressSegment(segmentId) {
  if (!state.readingProgress?.segments) state.readingProgress = normalizeReadingProgress(state.readingProgress || {});
  if (!state.readingProgress.segments[segmentId]) {
    state.readingProgress.segments[segmentId] = { visible_ms: 0, visits: 0, updated_at: "", state: "unread", depth: 0, highlight_count: 0, note_count: 0 };
  }
  return state.readingProgress.segments[segmentId];
}

function readingAnnotationCounts(segmentId) {
  const annotations = (state.annotations || []).filter(annotation => annotation.segment_id === segmentId && !isTeacherDefinition(annotation));
  return {
    highlight_count: annotations.length,
    note_count: annotations.filter(annotation => String(annotation.note || "").trim()).length,
  };
}

function readingStateForValues(visibleMs, highlightCount, noteCount) {
  if (noteCount > 0 || highlightCount >= 2 || visibleMs >= readingCarefulMs) return "careful";
  if (highlightCount > 0 || visibleMs >= readingSkimmedMs) return "skimmed";
  return "unread";
}

function readingDepthForValues(visibleMs, readingState, highlightCount, noteCount) {
  if (readingState === "unread") return 0;
  const timeDepth = Math.min(1, Math.max(0, visibleMs) / readingCarefulMs);
  const engagementDepth = Math.min(0.25, noteCount * 0.16 + highlightCount * 0.07);
  let depth = 0.12 + timeDepth * 0.58 + engagementDepth;
  if (readingState === "careful") depth = Math.max(depth, 0.58);
  return Math.min(0.92, Math.max(0.12, depth));
}

function readingProgressForSegment(segmentId) {
  if (!segmentId) return { state: "unread", depth: 0, visible_ms: 0, visits: 0, highlight_count: 0, note_count: 0 };
  const stats = state.readingProgress?.segments?.[segmentId] || {};
  const counts = readingAnnotationCounts(segmentId);
  const visibleMs = Math.max(0, Number(stats.visible_ms || 0));
  const readingState = readingStateForValues(visibleMs, counts.highlight_count, counts.note_count);
  const depth = readingDepthForValues(visibleMs, readingState, counts.highlight_count, counts.note_count);
  return {
    state: readingState,
    depth,
    visible_ms: visibleMs,
    visits: Math.max(0, Number(stats.visits || 0)),
    highlight_count: counts.highlight_count,
    note_count: counts.note_count,
  };
}

function readingProgressLabel(progress) {
  if (!progress || progress.state === "unread") return "Not read yet";
  const seconds = Math.round((progress.visible_ms || 0) / 1000);
  const label = progress.state === "careful" ? "Careful read" : "Skimmed";
  const noteText = progress.note_count ? ` · ${progress.note_count} note${progress.note_count > 1 ? "s" : ""}` : "";
  return `${label} · ${seconds}s${noteText}`;
}

function readableSegments() {
  return (state.payload?.segments || []).filter(segment => segment.id && segment.kind !== "heading" && displayText(segment.markdown || segment.translation || ""));
}

function readingSummaryFromCurrentState() {
  const segments = readableSegments();
  const total = segments.length;
  const counts = { unread: 0, skimmed: 0, careful: 0 };
  let noteCount = 0;
  let highlightCount = 0;
  let totalVisibleMs = 0;
  let visitCount = 0;
  for (const segment of segments) {
    const progress = readingProgressForSegment(segment.id);
    counts[progress.state] = (counts[progress.state] || 0) + 1;
    noteCount += progress.note_count;
    highlightCount += progress.highlight_count;
    totalVisibleMs += Math.max(0, Number(progress.visible_ms || 0));
    visitCount += Math.max(0, Number(progress.visits || 0));
  }
  const covered = counts.skimmed + counts.careful;
  const coverageRatio = total ? covered / total : 0;
  const carefulRatio = total ? counts.careful / total : 0;
  let readStatus = "unread";
  if ((total && coverageRatio >= 0.60 && carefulRatio >= 0.35) || noteCount >= 8) readStatus = "read";
  else if (carefulRatio >= 0.15 || noteCount >= 3) readStatus = "deep-reading";
  else if (coverageRatio >= 0.35) readStatus = "skimmed";
  else if (covered > 0) readStatus = "skimming";
  return {
    total_segments: total,
    unread: counts.unread,
    skimmed: counts.skimmed,
    careful: counts.careful,
    coverage_ratio: Math.round(coverageRatio * 1000) / 1000,
    careful_ratio: Math.round(carefulRatio * 1000) / 1000,
    note_count: noteCount,
    highlight_count: highlightCount,
    total_visible_ms: Math.round(totalVisibleMs),
    visit_count: Math.round(visitCount),
    read_status: readStatus,
    thresholds: { skimmed_ms: readingSkimmedMs, careful_ms: readingCarefulMs },
  };
}

function readStatusTone(status) {
  if (["read", "deep-reading"].includes(status)) return "dark";
  if (status === "skimmed") return "medium";
  if (status === "skimming") return "light";
  if (status === "archived") return "archived";
  return "none";
}

function readingProgressSummaryHtml(paper) {
  const summary = paper?.reading_progress_summary || {};
  const level = readingProgressLevel(paper);
  const coverage = Math.round(Number(summary.coverage_ratio || 0) * 100);
  const careful = Math.round(Number(summary.careful_ratio || 0) * 100);
  const briefCount = Number(summary.paper_brief_annotation_count || 0);
  const label = readingProgressStageLabel(level);
  const title = [label, briefCount ? `Paper Brief marks: ${briefCount}` : "", summary.total_segments ? `Body touched: ${coverage}%` : "", summary.total_segments ? `Deep: ${careful}%` : ""].filter(Boolean).join(" · ");
  const dots = [1, 2, 3, 4, 5].map(dot => `<span class="reading-progress-dot ${dot <= level ? "active" : ""}" title="${escapeHtml(readingProgressStageLabel(dot))}"></span>`).join("");
  const bodyText = summary.total_segments ? `${coverage}% body · ${careful}% deep` : (briefCount ? `${briefCount} brief mark${briefCount === 1 ? "" : "s"}` : "No reading trace yet");
  return `<div class="reading-progress-visual" data-progress-level="${level}" title="${escapeHtml(title)}" aria-label="${escapeHtml(title)}">
    <div class="reading-progress-dots">${dots}</div>
    <div class="reading-progress-bar" style="--reading-progress: ${Math.max(0, Math.min(100, coverage))}%"><span></span></div>
    <div class="read-status-summary">${escapeHtml(label)} · ${escapeHtml(bodyText)}</div>
  </div>`;
}

function numberedOutlineLevel(title, rawLevel = 1) {
  const text = String(title || "").trim();
  const match = text.match(/^(\d{1,2}(?:\.\d{1,2}){0,5})(?=\s|[:.)、-]|$)/);
  if (!match) return 0;
  const sectionNumber = match[1];
  const firstNumber = Number(sectionNumber.split(".")[0]);
  if (!Number.isFinite(firstNumber) || firstNumber < 1 || firstNumber > 50) return 0;
  if (!sectionNumber.includes(".") && Number(rawLevel || 1) <= 1) return 0;
  return Math.max(1, Math.min(6, 2 + sectionNumber.split(".").length - 1));
}

function outlineDisplayLevel(item = {}) {
  const rawLevel = Math.max(1, Math.min(6, Number(item.level || 1)));
  const inferred = numberedOutlineLevel(item.title || "", rawLevel);
  return Math.max(rawLevel, inferred || rawLevel);
}

function outlineItemHasChildren(outlineItems, index) {
  const item = outlineItems[index];
  if (!item) return false;
  const level = outlineDisplayLevel(item);
  for (let next = index + 1; next < outlineItems.length; next += 1) {
    const nextLevel = outlineDisplayLevel(outlineItems[next]);
    if (nextLevel <= level) return false;
    if (nextLevel > level) return true;
  }
  return false;
}

function outlineCollapsedAncestorId(outlineItems, index) {
  let level = outlineDisplayLevel(outlineItems[index] || {});
  for (let previous = index - 1; previous >= 0; previous -= 1) {
    const candidate = outlineItems[previous];
    const candidateLevel = outlineDisplayLevel(candidate);
    if (candidateLevel >= level) continue;
    if (state.collapsedOutlineIds.has(candidate.id || "")) return candidate.id || "";
    level = candidateLevel;
  }
  return "";
}

function visibleOutlineIdForItem(item, outlineItems = state.payload?.outline?.outline || []) {
  const index = outlineItems.findIndex(candidate => candidate?.id === item?.id);
  if (index < 0) return item?.id || "";
  let visibleId = item?.id || "";
  let level = outlineDisplayLevel(outlineItems[index]);
  for (let previous = index - 1; previous >= 0; previous -= 1) {
    const candidate = outlineItems[previous];
    const candidateLevel = outlineDisplayLevel(candidate);
    if (candidateLevel >= level) continue;
    if (state.collapsedOutlineIds.has(candidate.id || "")) visibleId = candidate.id || visibleId;
    level = candidateLevel;
  }
  return visibleId;
}

function toggleOutlineCollapsed(outlineId) {
  if (!outlineId) return;
  if (state.collapsedOutlineIds.has(outlineId)) state.collapsedOutlineIds.delete(outlineId);
  else state.collapsedOutlineIds.add(outlineId);
  renderSidebar();
}

function outlineSectionSegmentIds(item, outlineItems, index) {
  const start = segmentIdNumber(item?.id || "");
  if (!Number.isFinite(start)) return [];
  const level = outlineDisplayLevel(item);
  const next = outlineItems.slice(index + 1).find(candidate => outlineDisplayLevel(candidate) <= level && Number.isFinite(segmentIdNumber(candidate.id)));
  const end = next ? segmentIdNumber(next.id) : Number.POSITIVE_INFINITY;
  return readableSegments()
    .filter(segment => {
      const number = segmentIdNumber(segment.id);
      return Number.isFinite(number) && number >= start && number < end;
    })
    .map(segment => segment.id);
}

function readingProgressForOutlineItem(item, outlineItems, index) {
  const segmentIds = outlineSectionSegmentIds(item, outlineItems, index);
  if (!segmentIds.length) return readingProgressForSegment(item?.id || "");
  const segmentProgress = segmentIds.map(readingProgressForSegment);
  const depth = Math.max(0, ...segmentProgress.map(progress => progress.depth || 0));
  const carefulCount = segmentProgress.filter(progress => progress.state === "careful").length;
  const skimmedCount = segmentProgress.filter(progress => progress.state === "skimmed").length;
  const readingState = carefulCount ? "careful" : skimmedCount ? "skimmed" : "unread";
  return { state: readingState, depth, visible_ms: segmentProgress.reduce((sum, progress) => sum + (progress.visible_ms || 0), 0), visits: 0, highlight_count: 0, note_count: 0 };
}

function markdownToPlainLines(markdown, limit = 6) {
  return String(markdown || "")
    .split("\n")
    .map(line => displayText(line.replace(/^#+\s*/, "").replace(/^[-*]\s*/, "")))
    .filter(Boolean)
    .slice(0, limit);
}

function defaultThinkingData() {
  return { version: 1, explain: { content: "", updated_at: "" }, blocks: [], annotations: [], report_thoughts: [] };
}

function normalizeSourceRefs(refs = []) {
  return Array.isArray(refs) ? refs.filter(ref => ref && typeof ref === "object").map(ref => ({
    paper_id: String(ref.paper_id || ""),
    segment_id: String(ref.segment_id || ""),
    end_segment_id: String(ref.end_segment_id || ""),
    annotation_id: String(ref.annotation_id || ""),
    block_id: String(ref.block_id || ""),
    item_id: String(ref.item_id || ""),
    source: String(ref.source || ""),
    label: String(ref.label || ""),
    quote: String(ref.quote || ""),
  })).filter(ref => ref.segment_id || ref.annotation_id || ref.block_id || ref.quote) : [];
}

function normalizeSelectionRefs(refs = []) {
  return Array.isArray(refs) ? refs.filter(ref => ref && typeof ref === "object").map(ref => ({
    paper_id: String(ref.paper_id || ""),
    segment_id: String(ref.segment_id || ""),
    target: String(ref.target || "source"),
    quote: String(ref.quote || ""),
    range: ref.range && typeof ref.range === "object" ? { start: Number(ref.range.start || 0), end: Number(ref.range.end || 0) } : null,
  })).filter(ref => ref.segment_id || ref.quote) : [];
}

function normalizeThinkingData(data = {}, options = {}) {
  const thinking = { ...defaultThinkingData(), ...(data || {}) };
  if (!thinking.explain || typeof thinking.explain !== "object") thinking.explain = { content: "", updated_at: "" };
  thinking.explain.content = String(thinking.explain.content || "");
  thinking.explain.updated_at = String(thinking.explain.updated_at || "");
  thinking.blocks = Array.isArray(thinking.blocks) ? thinking.blocks.map((block, index) => {
    const mode = ["source", "free", "reading_narrative"].includes(String(block?.mode || "")) ? String(block.mode) : "";
    const model = String(block?.model || "");
    const isAgentBlock = Boolean(mode || model);
    const rawTitle = String(block?.title || "").trim();
    const defaultAgentTitles = new Set(["AI output", "Source-grounded answer", "Free reflection answer", "Source-grounded", "Free reflection"]);
    const title = isAgentBlock && defaultAgentTitles.has(rawTitle) ? "" : (rawTitle || (isAgentBlock ? "" : "AI output"));
    return {
      ...block,
      id: String(block?.id || `tb-${index + 1}`),
      type: String(block?.type || "ai_output"),
      title,
      content: String(block?.content || ""),
      prompt: String(block?.prompt || ""),
      mode,
      model,
      context_mode: String(block?.context_mode || ""),
      context_chars: Number(block?.context_chars || 0),
      project_context: block?.project_context && typeof block.project_context === "object" ? {
        project: String(block.project_context.project || ""),
        card_count: Number(block.project_context.card_count || 0),
        source_path: String(block.project_context.source_path || ""),
      } : null,
      status: String(block?.status || ""),
      source_refs: normalizeSourceRefs(block?.source_refs || []),
      selection_refs: normalizeSelectionRefs(block?.selection_refs || []),
      created_at: block?.created_at || new Date().toISOString(),
      updated_at: block?.updated_at || new Date().toISOString(),
    };
  }).filter(block => block.title.trim() || block.content.trim() || block.prompt.trim()) : [];
  thinking.annotations = Array.isArray(thinking.annotations) ? thinking.annotations
    .filter(item => item && typeof item === "object")
    .map(item => ({
      ...item,
      id: String(item.id || `ta-${Date.now().toString(36)}`),
      block_id: String(item.block_id || ""),
      type: String(item.type || "range"),
      target: "thinking",
      color: String(item.color || "yellow"),
      quote: String(item.quote || ""),
      note: String(item.note || ""),
      tags: annotationTags(item),
      presentation_flow_id: String(item.presentation_flow_id || ""),
      range: item.range,
      created_at: item.created_at || new Date().toISOString(),
      updated_at: item.updated_at || new Date().toISOString(),
    })) : [];
  thinking.report_thoughts = Array.isArray(thinking.report_thoughts) ? thinking.report_thoughts.map((item, index) => ({
    ...item,
    id: String(item?.id || `rt-${Date.now().toString(36)}-${index}`),
    group: String(item?.group || "sensemaking-gap"),
    note: String(item?.note || ""),
    created_at: item?.created_at || new Date().toISOString(),
    updated_at: item?.updated_at || new Date().toISOString(),
  })).filter(item => item.note.trim()) : [];
  if (!thinking.explain.content.trim() && options.seed === true) thinking.explain.content = buildExplainSeedMarkdown();
  return thinking;
}

function cleanExplainLine(line) {
  return displayText(String(line || "")
    .replace(/^(metadata|skim summary|main argument|research question|method|result|contribution|takeaway)[:：]/i, "")
    .replace(/^#+\s*/, "")
    .replace(/^[-*]\s*/, ""));
}

function buildExplainSeedMarkdown() {
  const metadata = state.payload?.metadata || {};
  const summary = state.payload?.skim_summary || state.payload?.skim_analysis?.skim_summary || "";
  const lines = markdownToPlainLines(summary, 14).map(cleanExplainLine).filter(Boolean);
  const question = metadata.research_question || lines[0] || metadata.abstract_zh || metadata.abstract || metadata.title || "这篇论文想解决一个具体研究场景里的真实卡点。";
  const method = metadata.method || lines.find(line => /方法|系统|设计|模型|method|system|design|framework/i.test(line)) || lines[1] || "作者通过一个方法、系统或研究设计，把问题拆成可观察、可验证的步骤。";
  const result = metadata.result || lines.find(line => /发现|结果|证明|result|finding|shows|suggest/i.test(line)) || lines[2] || "最重要的结果是：它给我们一个新的角度去理解这个工作流为什么会卡、哪里可以被支持。";
  const takeaways = [...new Set(lines.slice(0, 6))].slice(0, 3);
  while (takeaways.length < 3) {
    takeaways.push([
      "先抓住作者眼里的核心矛盾，而不是急着记技术细节。",
      "看它把 AI、工具、用户和任务之间的关系重新摆在了哪里。",
      "读完后问一句：这个观点能不能迁移到我的 collaborative ideation / CHI 写作里？",
    ][takeaways.length]);
  }
  return `# 解释：\n\n## 先说人话：这篇论文到底在关心什么？\n${question}\n\n它值得读的地方，不是“又做了一个系统/实验”这么简单，而是它试图把一个看起来散乱的工作场景，整理成可以讨论、可以设计、也可以被证据支撑的问题。\n\n## 作者大概怎么做？\n${method}\n\n你可以把它理解成：作者先指出现有做法哪里别扭，再搭了一个更清楚的观察框架，最后用研究或系统证据说明这个框架为什么有用。\n\n## 最值得带走的 3 个点\n- ${takeaways[0]}\n- ${takeaways[1]}\n- ${takeaways[2]}\n\n## 结果给了我们什么启发？\n${result}\n\n## 读这篇时可以盯住\n- 它把“人要判断的事”和“AI/系统能辅助的事”分得清不清楚。\n- 它的贡献是一个新工具、一个新机制，还是一个重新命名问题的 lens。\n- 哪些句子可以直接服务你的 motivation、related work、system design 或 discussion。`;
}

function setThinkingSaveState(message, kind = "") {
  renderReaderSaveStatus();
  const node = qs("#thinkingSaveState");
  if (!node) return;
  node.textContent = message;
  node.dataset.state = kind;
}

function scheduleThinkingSave(delay = 500) {
  state.thinkingDirty = true;
  if (state.thinkingSaveTimer) clearTimeout(state.thinkingSaveTimer);
  setThinkingSaveState("Editing...", "pending");
  state.thinkingSaveTimer = setTimeout(() => {
    state.thinkingSaveTimer = null;
    saveThinking({ silent: true }).catch(error => {
      setThinkingSaveState("Save failed", "error");
      toast(`Thinking save failed: ${error.message}`);
    });
  }, delay);
}

async function saveThinking(options = {}) {
  if (!state.currentPaperId || !state.thinking) return;
  const paperId = state.currentPaperId;
  const thinking = state.thinking;
  const snapshot = JSON.stringify(thinking);
  state.thinkingDirty = true;
  setThinkingSaveState("Saving...", "saving");
  const response = await queuePaperWrite(paperId, "thinking", thinking);
  if (paperId === state.currentPaperId && JSON.stringify(state.thinking) === snapshot) {
    state.thinking = normalizeThinkingData(response.thinking || thinking, { seed: false });
    state.thinkingDirty = false;
    if (state.payload) state.payload.thinking = state.thinking;
    setThinkingSaveState("Saved", "saved");
    capturePaperSession();
  }
  state.allNotesDirty = true;
  if (!options.silent) toast("Notes saved");
}

async function loadLibrary() {
  const initial = !state.libraryLoaded;
  const data = await api("/api/library");
  state.library = data.library;
  state.translationConfig = data.translation_config || { auto_start: false };
  state.feishuConfig = data.feishu_config || { enabled: false, auto_sync: false };
  if (qs("#openFeishuIntake")) qs("#openFeishuIntake").hidden = !state.feishuConfig.enabled;
  state.libraryLoaded = true;
  state.libraryDirty = true;
  if (data.tag_dictionary) state.tagDictionary = data.tag_dictionary;
  state.projectContexts = data.project_contexts || { version: 1, contexts: {} };
  qs("#workspaceLabel").textContent = data.workspace || "Local workspace";
  const paperIds = new Set((state.library.papers || []).map(paper => paper.id));
  if (initial) {
    const savedTabs = localStorage.getItem(paperTabsStorageKey);
    restorePaperTabs();
    const firstId = state.currentPaperId || (!savedTabs ? state.library.papers[0]?.id : null);
    state.currentPaperId = null;
    renderPaperTabs();
    renderPaperSelect();
    if (firstId) await loadPaper(firstId);
    else activateView("library");
  } else {
    state.paperTabs = state.paperTabs.filter(id => paperIds.has(id));
    for (const [id, session] of state.paperSessions) {
      const paper = state.library.papers.find(item => item.id === id);
      if (paper && session.payload?.metadata && paper.updated_at !== session.libraryUpdatedAt) session.loadedAt = 0;
    }
    if (state.currentPaperId && !paperIds.has(state.currentPaperId)) {
      disconnectReadingProgressTracker();
      state.currentPaperId = null;
      state.payload = null;
      state.annotations = [];
      state.thinking = null;
      renderReader();
      renderSidebar();
    }
    renderPaperTabs();
    renderPaperSelect();
  }
  state.allNotesDirty = true;
  if (document.body.dataset.activeView === "library") renderLibrary();
  if (document.body.dataset.activeView === "notes") await loadAllNotes();
}

async function loadAllNotes() {
  if (state.allNotesPromise) return state.allNotesPromise;
  if (state.allNotesLoaded && !state.allNotesDirty) return;
  state.allNotesDirty = false;
  state.allNotesPromise = (async () => {
    try {
      const data = await api("/api/notes");
      state.allNotes = data.notes || [];
      state.allNotesLoaded = true;
      if (document.body.dataset.activeView === "notes") {
        renderNotes();
        renderSidebar();
      }
    } catch (error) {
      state.allNotesDirty = true;
      throw error;
    } finally {
      state.allNotesPromise = null;
    }
  })();
  return state.allNotesPromise;
}

function invalidatePaperCache(paperId) {
  const session = state.paperSessions.get(paperId);
  if (session) session.loadedAt = 0;
  state.notesPreviewCache.delete(paperId);
}

function referenceHints(segments) {
  const references = {};
  for (const segment of segments) {
    if (!(segment.section_path || []).some(title => /references|bibliography/i.test(title))) continue;
    const match = String(segment.markdown || "").match(/^\s*\[?(\d+)\]?[.)]?\s+/);
    if (match) references[match[1]] = { number: match[1], raw: segment.markdown };
  }
  return references;
}

function noteSortTimestamp(note) {
  return note?.updated_at || note?.created_at || "";
}

function noteFromCurrentPaperAnnotation(annotation, paperId = state.currentPaperId) {
  const metadata = state.payload?.metadata || {};
  const paper = state.library?.papers?.find(item => item.id === paperId) || {};
  const projects = normalizeTagsInput(metadata.projects || metadata.project || paper.projects || paper.project || []).map(normalizeProjectName).filter(Boolean);
  return {
    ...annotation,
    paper_id: paperId,
    paper_title: metadata.title || paper.title || paperId,
    paper_venue: metadata.venue || metadata.journal || paper.venue || "",
    paper_year: metadata.year || metadata.publication_year || paper.year || "",
    paper_project: projects[0] || "",
    paper_projects: projects,
    paper_project_colors: metadata.project_colors || paper.project_colors || {},
    source_scope: "paper",
  };
}

function syncCurrentPaperNotesLocally(options = {}) {
  if (!state.currentPaperId) return;
  const paperId = state.currentPaperId;
  const paperNotes = (state.annotations || []).map(annotation => noteFromCurrentPaperAnnotation(annotation, paperId));
  const otherNotes = (state.allNotes || []).filter(note => !(note.paper_id === paperId && (note.source_scope || "paper") === "paper"));
  state.allNotes = [...paperNotes, ...otherNotes].sort((a, b) => String(noteSortTimestamp(b)).localeCompare(String(noteSortTimestamp(a))));
  if (options.renderNotes !== false) renderNotes();
  if (options.renderSidebar !== false) renderSidebar();
}

function shouldRenderNotesImmediately() {
  return document.body.dataset.activeView === "notes";
}

function refreshAllNotesInBackground(delay = 250) {
  state.allNotesDirty = true;
  if (document.body.dataset.activeView !== "notes") return;
  if (state.allNotesRefreshTimer) clearTimeout(state.allNotesRefreshTimer);
  state.allNotesRefreshTimer = setTimeout(() => {
    state.allNotesRefreshTimer = null;
    loadAllNotes().catch(error => console.warn("Background notes refresh failed", error));
  }, delay);
}

async function loadMindmap(project = state.currentMindmapProject || "collaborative", mindmapId = state.currentMindmapId || "") {
  state.currentMindmapProject = normalizeProjectName(project) || "collaborative";
  const suffix = mindmapId ? `/${encodeURIComponent(mindmapId)}` : "";
  const data = await api(`/api/mindmaps/${encodeURIComponent(state.currentMindmapProject)}${suffix}`);
  state.mindmap = data.mindmap || null;
  state.currentMindmapId = state.mindmap?.id || "";
  state.mindmaps = data.mindmaps || state.mindmaps || [];
  state.selectedMindmapNodeId = state.mindmap?.selected_node_id || state.mindmap?.root_id || "";
  state.selectedMindmapNodeIds = new Set([state.selectedMindmapNodeId].filter(Boolean));
  if (data.library) state.library = data.library;
  if (data.notes) state.allNotes = data.notes;
  if (data.tag_dictionary) state.tagDictionary = data.tag_dictionary;
  renderMindmap();
  renderLibrary();
}

async function refreshMindmapList(project = state.currentMindmapProject || "collaborative") {
  const data = await api(`/api/mindmaps?project=${encodeURIComponent(normalizeProjectName(project) || "collaborative")}`);
  state.mindmaps = data.mindmaps || [];
  if (data.library) state.library = data.library;
  if (data.tag_dictionary) state.tagDictionary = data.tag_dictionary;
  renderMindmapBoardList();
  renderMindmapProjectSelect();
}

function setMindmapSaveState(message, kind = "") {
  const node = qs("#mindmapSaveState");
  if (!node) return;
  node.textContent = message;
  node.dataset.state = kind;
}

function scheduleMindmapSave(delay = 450) {
  if (!state.mindmap?.id) return;
  if (state.mindmapSaveTimer) clearTimeout(state.mindmapSaveTimer);
  setMindmapSaveState("Editing...", "pending");
  state.mindmapSaveTimer = setTimeout(() => {
    state.mindmapSaveTimer = null;
    saveCurrentMindmap({ silent: true }).catch(error => {
      setMindmapSaveState("Save failed", "error");
      toast(`Mindmap save failed: ${error.message}`);
    });
  }, delay);
}

function mindmapViewport() {
  if (!state.mindmap) return { x: 80, y: 80, zoom: 1 };
  if (!state.mindmap.viewport || typeof state.mindmap.viewport !== "object") state.mindmap.viewport = { x: 80, y: 80, zoom: 1 };
  state.mindmap.viewport.zoom = Math.max(0.2, Math.min(3, Number(state.mindmap.viewport.zoom || 1)));
  state.mindmap.viewport.x = Number(state.mindmap.viewport.x || 0);
  state.mindmap.viewport.y = Number(state.mindmap.viewport.y || 0);
  return state.mindmap.viewport;
}

function mindmapWorldPoint(clientX, clientY) {
  const stage = qs("#mindmapStage");
  const rect = stage?.getBoundingClientRect();
  const viewport = mindmapViewport();
  const zoom = Number(viewport.zoom || 1);
  if (!rect) return { x: 0, y: 0 };
  return {
    x: (clientX - rect.left - Number(viewport.x || 0)) / zoom,
    y: (clientY - rect.top - Number(viewport.y || 0)) / zoom,
  };
}

function renderMindmapWorldTransform() {
  const world = qs("#mindmapWorld");
  if (!world || !state.mindmap) return;
  const viewport = mindmapViewport();
  world.style.transform = `translate(${Number(viewport.x || 0)}px, ${Number(viewport.y || 0)}px) scale(${Number(viewport.zoom || 1)})`;
  qs("#mindmapZoomLabel") && (qs("#mindmapZoomLabel").textContent = `${Math.round(Number(viewport.zoom || 1) * 100)}%`);
}

function mindmapScreenAnchor(nodeId) {
  if (!nodeId || !state.mindmap) return null;
  const row = document.querySelector(`[data-mindmap-node-row="${cssEscape(nodeId)}"]`);
  if (!row) return null;
  const rect = row.getBoundingClientRect();
  return { nodeId, left: rect.left, top: rect.top };
}

function restoreMindmapScreenAnchor(anchor, options = {}) {
  if (!anchor || !state.mindmap) return;
  const row = document.querySelector(`[data-mindmap-node-row="${cssEscape(anchor.nodeId)}"]`);
  if (!row) return;
  const rect = row.getBoundingClientRect();
  const dx = anchor.left - rect.left;
  const dy = anchor.top - rect.top;
  if (Math.abs(dx) < 0.5 && Math.abs(dy) < 0.5) return;
  const viewport = mindmapViewport();
  viewport.x += dx;
  viewport.y += dy;
  renderMindmapWorldTransform();
  if (options.persist !== false) scheduleMindmapSave(300);
}

function setMindmapZoom(nextZoom, anchorClient = null) {
  if (!state.mindmap) return;
  const stage = qs("#mindmapStage");
  const rect = stage?.getBoundingClientRect();
  const viewport = mindmapViewport();
  const oldZoom = Number(viewport.zoom || 1);
  const zoom = Math.max(0.2, Math.min(3, Number(nextZoom || 1)));
  const anchor = anchorClient || (rect ? { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 } : { x: 0, y: 0 });
  const worldPoint = rect ? { x: (anchor.x - rect.left - viewport.x) / oldZoom, y: (anchor.y - rect.top - viewport.y) / oldZoom } : { x: 0, y: 0 };
  viewport.zoom = zoom;
  if (rect) {
    viewport.x = anchor.x - rect.left - worldPoint.x * zoom;
    viewport.y = anchor.y - rect.top - worldPoint.y * zoom;
  }
  renderMindmapWorldTransform();
  scheduleMindmapSave(350);
}

function resetMindmapView() {
  if (!state.mindmap) return;
  state.mindmap.viewport = { x: 80, y: 80, zoom: 1 };
  renderMindmapWorldTransform();
  scheduleMindmapSave(180);
}

function applyMindmapSelectionPreview(ids) {
  const selected = new Set(ids || []);
  qsa("[data-mindmap-node-row]").forEach(row => {
    const isSelected = selected.has(row.dataset.mindmapNodeRow || "");
    row.classList.toggle("multi-selected", isSelected && selected.size > 1);
    row.classList.toggle("active", isSelected);
  });
  qs("#mindmapSelectionLabel") && (qs("#mindmapSelectionLabel").textContent = `${selected.size} selected`);
}

function updateMindmapSelectionBox(event) {
  const selection = state.mindmapSelecting;
  const stage = qs("#mindmapStage");
  const box = qs("#mindmapSelectionBox");
  const rect = stage?.getBoundingClientRect();
  if (!selection || !stage || !box || !rect) return;
  const left = Math.min(selection.startX, event.clientX) - rect.left;
  const top = Math.min(selection.startY, event.clientY) - rect.top;
  const width = Math.abs(event.clientX - selection.startX);
  const height = Math.abs(event.clientY - selection.startY);
  box.hidden = false;
  box.style.left = `${left}px`;
  box.style.top = `${top}px`;
  box.style.width = `${width}px`;
  box.style.height = `${height}px`;
  const boxRect = { left: rect.left + left, top: rect.top + top, right: rect.left + left + width, bottom: rect.top + top + height };
  const ids = qsa("[data-mindmap-node-row]").filter(row => {
    const rowRect = row.getBoundingClientRect();
    return rowRect.right >= boxRect.left && rowRect.left <= boxRect.right && rowRect.bottom >= boxRect.top && rowRect.top <= boxRect.bottom;
  }).map(row => row.dataset.mindmapNodeRow).filter(Boolean);
  state.mindmapSelecting.ids = ids;
  applyMindmapSelectionPreview(ids);
}

function startMindmapStagePointer(event) {
  if (!state.mindmap || !qs("#mindmapStage")?.contains(event.target)) return;
  if (event.target.closest("[data-mindmap-node-row], .mindmap-toolbar, .mindmap-type-menu, .mindmap-typeahead")) return;
  if (event.button === 1 || event.altKey) {
    const viewport = mindmapViewport();
    state.mindmapPanning = { startX: event.clientX, startY: event.clientY, x: viewport.x, y: viewport.y };
    qs("#mindmapStage")?.classList.add("panning");
    event.preventDefault();
    return;
  }
  if (event.button !== 0) return;
  state.mindmapSelecting = { startX: event.clientX, startY: event.clientY, ids: [] };
  qs("#mindmapStage")?.classList.add("selecting");
  updateMindmapSelectionBox(event);
  event.preventDefault();
}

function handleMindmapPointerMove(event) {
  if (state.mindmapPanning && state.mindmap) {
    const viewport = mindmapViewport();
    viewport.x = state.mindmapPanning.x + event.clientX - state.mindmapPanning.startX;
    viewport.y = state.mindmapPanning.y + event.clientY - state.mindmapPanning.startY;
    renderMindmapWorldTransform();
    scheduleMindmapSave(450);
    return;
  }
  if (state.mindmapSelecting) updateMindmapSelectionBox(event);
}

function endMindmapPointerInteraction(event = null) {
  if (state.mindmapSelecting) {
    const ids = state.mindmapSelecting.ids || [];
    const distance = event ? Math.hypot(event.clientX - state.mindmapSelecting.startX, event.clientY - state.mindmapSelecting.startY) : 0;
    if (ids.length && distance > 4) setMindmapSelection(ids, ids[0]);
    else if (distance <= 4) setMindmapSelection([state.mindmap?.root_id || ""], state.mindmap?.root_id || "");
    state.mindmapSelecting = null;
    const box = qs("#mindmapSelectionBox");
    if (box) box.hidden = true;
    qs("#mindmapStage")?.classList.remove("selecting");
    renderMindmap();
  }
  if (state.mindmapPanning) {
    state.mindmapPanning = null;
    qs("#mindmapStage")?.classList.remove("panning");
  }
}

function normalizeCanvasProject(value) {
  return normalizeProjectName(value) || "collaborative";
}

function canvasCards() {
  return Array.isArray(state.canvasBoard?.cards) ? state.canvasBoard.cards : [];
}

function canvasClusters() {
  return Array.isArray(state.canvasBoard?.clusters) ? state.canvasBoard.clusters : [];
}

function canvasCardById(cardId) {
  return canvasCards().find(card => card.id === cardId) || null;
}

function canvasClusterById(clusterId) {
  return canvasClusters().find(cluster => cluster.id === clusterId) || null;
}

function canvasSelectedObject() {
  return state.selectedCanvasKind === "cluster" ? canvasClusterById(state.selectedCanvasId) : canvasCardById(state.selectedCanvasId);
}

function newCanvasId(prefix) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

function defaultCanvasTable(template = "Research Gap") {
  const columns = template === "Related Work Matrix"
    ? ["Paper", "Problem", "Method", "Finding", "Relevance"]
    : template === "Method Comparison"
      ? ["Paper", "Method", "Data", "Evaluation", "Tradeoff"]
      : ["Paper / cluster", "Problem addressed", "Method / system move", "What it misses", "What we can borrow", "Implication for our paper"];
  return { template, columns, rows: [Object.fromEntries(columns.map(column => [column, ""]))] };
}

function canvasPaper(card) {
  return (state.library?.papers || []).find(paper => paper.id === card?.paper_id) || null;
}

function canvasNote(card) {
  const annotationId = card?.annotation_id || card?.source_refs?.[0]?.annotation_id || "";
  return (state.allNotes || []).find(note => note.id === annotationId) || null;
}

function canvasWorldPoint(clientX, clientY) {
  const stage = qs("#canvasStage");
  const rect = stage?.getBoundingClientRect();
  const viewport = state.canvasBoard?.viewport || { x: 0, y: 0, zoom: 1 };
  const zoom = Number(viewport.zoom || 1);
  if (!rect) return { x: 80, y: 80 };
  return {
    x: (clientX - rect.left - Number(viewport.x || 0)) / zoom,
    y: (clientY - rect.top - Number(viewport.y || 0)) / zoom,
  };
}

function canvasViewportCenter() {
  const stage = qs("#canvasStage");
  const rect = stage?.getBoundingClientRect();
  if (!rect) return { x: 120, y: 120 };
  return canvasWorldPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
}

function canvasClusterAtPoint(point) {
  return [...canvasClusters()].reverse().find(cluster => point.x >= Number(cluster.x || 0) && point.x <= Number(cluster.x || 0) + Number(cluster.width || 0) && point.y >= Number(cluster.y || 0) && point.y <= Number(cluster.y || 0) + Number(cluster.height || 0)) || null;
}

async function loadCanvasBoards(project = state.currentCanvasProject || "collaborative") {
  state.currentCanvasProject = normalizeCanvasProject(project);
  const data = await api(`/api/canvas/boards?project=${encodeURIComponent(state.currentCanvasProject)}`);
  if (data.library) state.library = data.library;
  if (data.tag_dictionary) state.tagDictionary = data.tag_dictionary;
  state.canvasBoards = data.boards || [];
  const selected = state.canvasBoards.find(board => board.id === state.currentCanvasBoardId) || state.canvasBoards[0];
  if (selected) await loadCanvasBoard(selected.id);
  else renderCanvas();
  renderLibrary();
}

async function loadCanvasBoard(boardId) {
  if (!boardId) return;
  const data = await api(`/api/canvas/boards/${encodeURIComponent(boardId)}`);
  state.canvasBoard = data.board || null;
  state.currentCanvasBoardId = state.canvasBoard?.id || "";
  state.currentCanvasProject = state.canvasBoard?.project || state.currentCanvasProject || "collaborative";
  state.canvasBoards = (data.library ? state.canvasBoards : state.canvasBoards).length ? state.canvasBoards : [{ id: state.currentCanvasBoardId, title: state.canvasBoard?.title || "Canvas", project: state.currentCanvasProject }];
  if (data.library) state.library = data.library;
  if (data.notes) state.allNotes = data.notes;
  if (data.tag_dictionary) state.tagDictionary = data.tag_dictionary;
  state.canvasSync.proposals = data.sync_proposals || [];
  renderCanvas();
}

async function createCanvasBoard() {
  const title = window.prompt("Board title:", "New Canvas")?.trim();
  if (!title) return;
  const response = await api("/api/canvas/boards", { method: "POST", body: JSON.stringify({ title, project: state.currentCanvasProject || "collaborative" }) });
  state.canvasBoards = response.boards || [];
  await loadCanvasBoard(response.board?.id || state.canvasBoards[0]?.id || "");
  toast("Canvas board created");
}

async function deleteCurrentCanvasBoard() {
  if (!state.currentCanvasBoardId) return;
  if (state.canvasSaveTimer) clearTimeout(state.canvasSaveTimer);
  state.canvasSaveTimer = null;
  await fetch(`/api/canvas/boards/${encodeURIComponent(state.currentCanvasBoardId)}`, { method: "DELETE" }).then(response => {
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  });
  state.currentCanvasBoardId = "";
  state.canvasBoard = null;
  await loadCanvasBoards(state.currentCanvasProject || "collaborative");
  toast("Canvas board deleted");
}

function setCanvasSaveState(message, kind = "") {
  const node = qs("#canvasSaveState");
  if (!node) return;
  node.textContent = message;
  node.dataset.state = kind;
}

function scheduleCanvasSave(delay = 500) {
  if (!state.canvasBoard?.id) return;
  if (state.canvasSaveTimer) clearTimeout(state.canvasSaveTimer);
  setCanvasSaveState("Editing...", "pending");
  state.canvasSaveTimer = setTimeout(() => {
    state.canvasSaveTimer = null;
    saveCanvasBoard({ silent: true }).catch(error => {
      setCanvasSaveState("Save failed", "error");
      toast(`Canvas save failed: ${error.message}`);
    });
  }, delay);
}

async function saveCanvasBoard(options = {}) {
  if (!state.canvasBoard?.id) return;
  state.canvasBoard.updated_at = new Date().toISOString();
  setCanvasSaveState("Saving...", "saving");
  const response = await api(`/api/canvas/boards/${encodeURIComponent(state.canvasBoard.id)}`, { method: "POST", body: JSON.stringify(state.canvasBoard) });
  state.canvasBoard = response.board || state.canvasBoard;
  state.canvasSync.proposals = response.sync_proposals || [];
  setCanvasSaveState("Saved", "saved");
  if (!options.silent) toast("Canvas saved");
  renderCanvasBoardList();
}

function createCanvasObject(kind, point = canvasViewportCenter()) {
  if (!state.canvasBoard) return;
  const cluster = canvasClusterAtPoint(point);
  const base = { x: Math.round(point.x), y: Math.round(point.y), created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
  if (kind === "cluster") {
    const clusterItem = { id: newCanvasId("cluster"), title: "Cluster", width: 520, height: 340, ...base, sync_mode: "local", tag_candidate: "", linked_library_tag: "" };
    state.canvasBoard.clusters.push(clusterItem);
    state.selectedCanvasId = clusterItem.id;
    state.selectedCanvasKind = "cluster";
  } else {
    const sizes = { table: [560, 260], paper: [280, 150], note: [280, 150], text: [240, 110], image: [280, 180] };
    const [width, height] = sizes[kind] || sizes.text;
    const selectedClusterId = state.selectedCanvasKind === "cluster" && canvasClusterById(state.selectedCanvasId) ? state.selectedCanvasId : "";
    const card = { id: newCanvasId("card"), kind, title: kind === "text" ? "Text" : kind === "table" ? "Research Gap Table" : `Choose ${kind}`, text: kind === "text" ? "Double-click to write" : "", width, height, ...base, cluster_id: cluster?.id || selectedClusterId, source_refs: [], local_tags: [], linked_tags: [], table: kind === "table" ? defaultCanvasTable() : {} };
    if (card.cluster_id && !canvasClusterById(card.cluster_id)) card.cluster_id = "";
    state.canvasBoard.cards.push(card);
    state.selectedCanvasId = card.id;
    state.selectedCanvasKind = "card";
  }
  renderCanvas();
  scheduleCanvasSave(150);
}

function canvasClusterTag(cluster) {
  const tag = cluster?.linked_library_tag || cluster?.tag_candidate || "";
  return tag ? libraryTagLabel(tag) : "Local cluster";
}

function canvasCardTitle(card) {
  if (card.kind === "paper") return paperTitle(canvasPaper(card) || { title: card.title || "Choose paper" });
  if (card.kind === "note") return compactText(canvasNote(card)?.note || canvasNote(card)?.quote || card.title || "Choose note", 80);
  return card.title || card.text || card.kind;
}

function canvasCardHtml(card) {
  const paper = canvasPaper(card);
  const note = canvasNote(card);
  const style = `left:${Number(card.x || 0)}px;top:${Number(card.y || 0)}px;width:${Number(card.width || 240)}px;height:${Number(card.height || 120)}px`;
  const selected = state.selectedCanvasKind === "card" && state.selectedCanvasId === card.id ? " selected" : "";
  const body = card.kind === "paper"
    ? `<strong>${escapeHtml(canvasCardTitle(card))}</strong><span>${escapeHtml([paper?.venue, paper?.year, paper?.read_status].filter(Boolean).join(" · "))}</span><div class="canvas-card-tags">${normalizeTagsInput(paper?.tags || []).slice(0, 4).map(tag => `<span style="--tag-color:${escapeHtml(tagColor(tag))}">${escapeHtml(libraryTagLabel(tag))}</span>`).join("")}</div>`
    : card.kind === "note"
      ? `<strong>${escapeHtml(canvasCardTitle(card))}</strong><blockquote>${escapeHtml(compactText(note?.quote || card.text || "", 120))}</blockquote><span>${escapeHtml(note?.paper_title || "")}</span>`
      : card.kind === "table"
        ? `<strong>${escapeHtml(card.title || "Table")}</strong><span>${escapeHtml(card.table?.template || "Editable table")}</span><div class="canvas-mini-table">${(card.table?.columns || []).slice(0, 4).map(column => `<span>${escapeHtml(column)}</span>`).join("")}</div>`
        : `<strong>${escapeHtml(card.title || "Text")}</strong><p>${escapeHtml(card.text || "Double-click to write")}</p>`;
  return `<div class="canvas-card canvas-card-${escapeHtml(card.kind)}${selected}" style="${style}" data-canvas-card="${escapeHtml(card.id)}" tabindex="0">${body}<button class="canvas-resize-handle" data-canvas-resize="${escapeHtml(card.id)}" type="button" aria-label="Resize card"></button></div>`;
}

function canvasClusterHtml(cluster) {
  const style = `left:${Number(cluster.x || 0)}px;top:${Number(cluster.y || 0)}px;width:${Number(cluster.width || 520)}px;height:${Number(cluster.height || 340)}px`;
  const selected = state.selectedCanvasKind === "cluster" && state.selectedCanvasId === cluster.id ? " selected" : "";
  const tag = cluster.linked_library_tag || cluster.tag_candidate || "";
  return `<section class="canvas-cluster${selected}" style="${style};--tag-color:${escapeHtml(tag ? tagColor(tag) : "#d5dce3")}" data-canvas-cluster="${escapeHtml(cluster.id)}" tabindex="0"><div class="canvas-cluster-title"><strong>${escapeHtml(cluster.title || "Cluster")}</strong><span>${escapeHtml(canvasClusterTag(cluster))}</span></div><button class="canvas-resize-handle" data-canvas-resize-cluster="${escapeHtml(cluster.id)}" type="button" aria-label="Resize cluster"></button></section>`;
}

function renderCanvasProjectSelect() {
  const select = qs("#canvasProject");
  if (!select) return;
  const projects = allLibraryProjects();
  select.innerHTML = projects.map(project => `<option value="${escapeHtml(project)}" ${state.currentCanvasProject === project ? "selected" : ""}>${escapeHtml(project)}</option>`).join("");
}

function renderCanvasBoardList() {
  const root = qs("#canvasBoardList");
  if (!root) return;
  root.innerHTML = (state.canvasBoards || []).map(board => `<button class="canvas-board-item ${state.currentCanvasBoardId === board.id ? "active" : ""}" data-canvas-board="${escapeHtml(board.id)}" type="button"><strong>${escapeHtml(board.title || "Untitled Canvas")}</strong><span>${escapeHtml(`${board.card_count || 0} cards · ${board.cluster_count || 0} clusters`)}</span></button>`).join("") || '<p class="muted small-text">No boards yet.</p>';
  qsa("[data-canvas-board]").forEach(button => button.addEventListener("click", () => loadCanvasBoard(button.dataset.canvasBoard).catch(error => toast(`Canvas load failed: ${error.message}`))));
}

function renderCanvasInspector() {
  const root = qs("#canvasInspector");
  if (!root) return;
  const object = canvasSelectedObject();
  if (!object) {
    root.className = "canvas-inspector-empty";
    root.innerHTML = '<h2>Selection</h2><p>Select a card or cluster to inspect source links and sync state.</p>';
    return;
  }
  root.className = "canvas-inspector-section";
  if (state.selectedCanvasKind === "cluster") {
    const tagOptions = allLibraryTags(object.linked_library_tag ? [object.linked_library_tag] : []);
    root.innerHTML = `<h2>Cluster</h2><label>Title</label><input class="canvas-inspector-input" data-canvas-cluster-title="${escapeHtml(object.id)}" value="${escapeHtml(object.title || "")}" /><label>Link Library tag</label><select class="canvas-inspector-input" data-canvas-cluster-link="${escapeHtml(object.id)}"><option value="">Local only</option>${tagOptions.map(tag => `<option value="${escapeHtml(tag)}" ${object.linked_library_tag === tag ? "selected" : ""}>${escapeHtml(libraryTagLabel(tag))}</option>`).join("")}</select><p class="muted small-text">Use #tag in the title to create a draft tag candidate. Library is updated only through Sync Review.</p>`;
  } else {
    const card = object;
    const sourceButton = card.kind === "paper" && card.paper_id ? `<button class="primary-button mini-button" data-open-canvas-paper="${escapeHtml(card.paper_id)}" type="button">Open Paper</button>` : card.kind === "note" && card.annotation_id ? `<button class="primary-button mini-button" data-open-canvas-note="${escapeHtml(card.annotation_id)}" data-paper-id="${escapeHtml(canvasNote(card)?.paper_id || "")}" type="button">Open Source</button>` : "";
    root.innerHTML = `<h2>${escapeHtml(card.kind)}</h2><label>Title</label><input class="canvas-inspector-input" data-canvas-card-title="${escapeHtml(card.id)}" value="${escapeHtml(card.title || "")}" /><label>Text</label><textarea class="canvas-inspector-input" data-canvas-card-text="${escapeHtml(card.id)}" rows="5">${escapeHtml(card.text || "")}</textarea>${sourceButton}`;
  }
  bindCanvasInspectorEvents(root);
}

function bindCanvasInspectorEvents(root) {
  root.querySelector("[data-canvas-cluster-title]")?.addEventListener("input", event => {
    const cluster = canvasClusterById(event.target.dataset.canvasClusterTitle);
    if (!cluster) return;
    cluster.title = event.target.value;
    const match = cluster.title.match(/#([\w\-./\u4e00-\u9fff]+)/);
    cluster.tag_candidate = match ? match[1] : cluster.tag_candidate || "";
    cluster.updated_at = new Date().toISOString();
    renderCanvasWorld();
    scheduleCanvasSave();
  });
  root.querySelector("[data-canvas-cluster-link]")?.addEventListener("change", event => {
    const cluster = canvasClusterById(event.target.dataset.canvasClusterLink);
    if (!cluster) return;
    cluster.linked_library_tag = event.target.value;
    cluster.sync_mode = cluster.linked_library_tag ? "linked" : "local";
    cluster.updated_at = new Date().toISOString();
    renderCanvasWorld();
    scheduleCanvasSave();
  });
  root.querySelector("[data-canvas-card-title]")?.addEventListener("input", event => {
    const card = canvasCardById(event.target.dataset.canvasCardTitle);
    if (!card) return;
    card.title = event.target.value;
    card.updated_at = new Date().toISOString();
    renderCanvasWorld();
    scheduleCanvasSave();
  });
  root.querySelector("[data-canvas-card-text]")?.addEventListener("input", event => {
    const card = canvasCardById(event.target.dataset.canvasCardText);
    if (!card) return;
    card.text = event.target.value;
    card.updated_at = new Date().toISOString();
    renderCanvasWorld();
    scheduleCanvasSave();
  });
  root.querySelector("[data-open-canvas-paper]")?.addEventListener("click", event => openCanvasPaper(event.target.dataset.openCanvasPaper));
  root.querySelector("[data-open-canvas-note]")?.addEventListener("click", event => {
    openNoteSourcePreview(event.target.dataset.paperId, event.target.dataset.openCanvasNote, "");
    activateView("notes");
  });
}

function renderCanvasWorld() {
  const world = qs("#canvasWorld");
  if (!world || !state.canvasBoard) return;
  const viewport = state.canvasBoard.viewport || { x: 0, y: 0, zoom: 1 };
  world.style.transform = `translate(${Number(viewport.x || 0)}px, ${Number(viewport.y || 0)}px) scale(${Number(viewport.zoom || 1)})`;
  world.innerHTML = `${canvasClusters().map(canvasClusterHtml).join("")}${canvasCards().map(canvasCardHtml).join("")}`;
  bindCanvasObjectEvents(world);
}

function renderCanvas() {
  renderCanvasProjectSelect();
  renderCanvasBoardList();
  const title = qs("#canvasBoardTitle");
  if (title) title.value = state.canvasBoard?.title || "";
  const zoom = Number(state.canvasBoard?.viewport?.zoom || 1);
  qs("#canvasZoomLabel") && (qs("#canvasZoomLabel").textContent = `${Math.round(zoom * 100)}%`);
  const stage = qs("#canvasStage");
  if (!state.canvasBoard) {
    qs("#canvasWorld") && (qs("#canvasWorld").innerHTML = '<p class="muted canvas-empty">Create a board to start.</p>');
    renderCanvasInspector();
    return;
  }
  if (stage) stage.dataset.hasBoard = "true";
  renderCanvasWorld();
  renderCanvasInspector();
  renderCanvasPicker();
  renderCanvasSyncModal();
}

function bindCanvasObjectEvents(root) {
  root.querySelectorAll("[data-canvas-cluster]").forEach(node => {
    node.addEventListener("pointerdown", event => startCanvasObjectDrag(event, "cluster", node.dataset.canvasCluster));
    node.addEventListener("click", event => selectCanvasObject("cluster", node.dataset.canvasCluster, event));
    node.addEventListener("dblclick", event => {
      event.stopPropagation();
      state.selectedCanvasKind = "cluster";
      state.selectedCanvasId = node.dataset.canvasCluster;
      renderCanvasInspector();
      qs(`[data-canvas-cluster-title="${cssEscape(state.selectedCanvasId)}"]`)?.focus();
    });
  });
  root.querySelectorAll("[data-canvas-card]").forEach(node => {
    node.addEventListener("pointerdown", event => startCanvasObjectDrag(event, "card", node.dataset.canvasCard));
    node.addEventListener("click", event => selectCanvasObject("card", node.dataset.canvasCard, event));
    node.addEventListener("dblclick", event => {
      event.stopPropagation();
      openCanvasCardDefaultAction(node.dataset.canvasCard);
    });
  });
  root.querySelectorAll("[data-canvas-resize]").forEach(handle => handle.addEventListener("pointerdown", event => startCanvasResize(event, "card", handle.dataset.canvasResize)));
  root.querySelectorAll("[data-canvas-resize-cluster]").forEach(handle => handle.addEventListener("pointerdown", event => startCanvasResize(event, "cluster", handle.dataset.canvasResizeCluster)));
}

function selectCanvasObject(kind, id, event = null) {
  event?.stopPropagation?.();
  state.selectedCanvasKind = kind;
  state.selectedCanvasId = id;
  renderCanvasWorld();
  renderCanvasInspector();
}

function startCanvasObjectDrag(event, kind, id) {
  if (event.button !== 0 || event.target.closest(".canvas-resize-handle")) return;
  const object = kind === "cluster" ? canvasClusterById(id) : canvasCardById(id);
  if (!object) return;
  selectCanvasObject(kind, id, event);
  const point = canvasWorldPoint(event.clientX, event.clientY);
  state.canvasDragging = { kind, id, offsetX: point.x - Number(object.x || 0), offsetY: point.y - Number(object.y || 0) };
  event.currentTarget.setPointerCapture?.(event.pointerId);
  event.preventDefault();
}

function startCanvasResize(event, kind, id) {
  event.stopPropagation();
  const object = kind === "cluster" ? canvasClusterById(id) : canvasCardById(id);
  if (!object) return;
  state.canvasResizing = { kind, id, startX: event.clientX, startY: event.clientY, width: Number(object.width || 240), height: Number(object.height || 120) };
  event.currentTarget.setPointerCapture?.(event.pointerId);
  event.preventDefault();
}

function handleCanvasPointerMove(event) {
  if (!state.canvasBoard) return;
  if (state.canvasDragging) {
    const { kind, id, offsetX, offsetY } = state.canvasDragging;
    const object = kind === "cluster" ? canvasClusterById(id) : canvasCardById(id);
    if (!object) return;
    const point = canvasWorldPoint(event.clientX, event.clientY);
    const oldX = Number(object.x || 0);
    const oldY = Number(object.y || 0);
    object.x = Math.round(point.x - offsetX);
    object.y = Math.round(point.y - offsetY);
    object.updated_at = new Date().toISOString();
    if (kind === "cluster") {
      const dx = Number(object.x || 0) - oldX;
      const dy = Number(object.y || 0) - oldY;
      canvasCards().filter(card => card.cluster_id === id).forEach(card => {
        card.x = Math.round(Number(card.x || 0) + dx);
        card.y = Math.round(Number(card.y || 0) + dy);
      });
    } else {
      const cluster = canvasClusterAtPoint({ x: object.x + 16, y: object.y + 16 });
      object.cluster_id = cluster?.id || "";
    }
    renderCanvasWorld();
    scheduleCanvasSave(250);
    return;
  }
  if (state.canvasResizing) {
    const { kind, id, startX, startY, width, height } = state.canvasResizing;
    const object = kind === "cluster" ? canvasClusterById(id) : canvasCardById(id);
    if (!object) return;
    const zoom = Number(state.canvasBoard.viewport?.zoom || 1);
    object.width = Math.max(kind === "cluster" ? 160 : 100, Math.round(width + (event.clientX - startX) / zoom));
    object.height = Math.max(kind === "cluster" ? 120 : 60, Math.round(height + (event.clientY - startY) / zoom));
    object.updated_at = new Date().toISOString();
    renderCanvasWorld();
    scheduleCanvasSave(250);
    return;
  }
  if (state.canvasPanning) {
    state.canvasBoard.viewport.x = state.canvasPanning.x + event.clientX - state.canvasPanning.clientX;
    state.canvasBoard.viewport.y = state.canvasPanning.y + event.clientY - state.canvasPanning.clientY;
    renderCanvasWorld();
    scheduleCanvasSave(350);
  }
}

function endCanvasPointerInteraction() {
  state.canvasDragging = null;
  state.canvasResizing = null;
  state.canvasPanning = null;
}

function openCanvasCardDefaultAction(cardId) {
  const card = canvasCardById(cardId);
  if (!card) return;
  state.selectedCanvasKind = "card";
  state.selectedCanvasId = cardId;
  if (card.kind === "paper" || card.kind === "note") {
    state.canvasPicker = { open: true, kind: card.kind, cardId, query: "" };
    renderCanvasPicker();
  } else {
    renderCanvasInspector();
    const selector = card.kind === "table" ? `[data-canvas-card-title="${cssEscape(cardId)}"]` : `[data-canvas-card-text="${cssEscape(cardId)}"]`;
    requestAnimationFrame(() => qs(selector)?.focus());
  }
}

async function openCanvasPaper(paperId) {
  if (!paperId) return;
  await loadPaper(paperId);
  activateView("reader");
}

function canvasPickerOptions() {
  const query = String(state.canvasPicker.query || "").trim().toLowerCase();
  if (state.canvasPicker.kind === "paper") {
    return (state.library?.papers || []).filter(paper => {
      const text = [paperTitle(paper), paperAuthors(paper), paperJournal(paper), paperYear(paper), paper.read_status, ...paperProjects(paper), ...normalizeTagsInput(paper.tags || []).map(libraryTagLabel)].join(" ").toLowerCase();
      return !query || text.includes(query);
    }).slice(0, 50);
  }
  if (state.canvasPicker.kind === "note") {
    return (state.allNotes || []).filter(note => {
      const text = [note.note, note.quote, note.paper_title, note.source_scope, ...projectsForNote(note), ...annotationTags(note)].join(" ").toLowerCase();
      return !query || text.includes(query);
    }).slice(0, 50);
  }
  return [];
}

function renderCanvasPicker() {
  const modal = qs("#canvasPickerModal");
  const title = qs("#canvasPickerTitle");
  const search = qs("#canvasPickerSearch");
  const root = qs("#canvasPickerResults");
  if (!modal || !root) return;
  modal.classList.toggle("open", Boolean(state.canvasPicker.open));
  modal.setAttribute("aria-hidden", state.canvasPicker.open ? "false" : "true");
  if (!state.canvasPicker.open) return;
  if (title) title.textContent = state.canvasPicker.kind === "paper" ? "Choose paper" : "Choose note / highlight";
  if (search && search.value !== state.canvasPicker.query) search.value = state.canvasPicker.query || "";
  const options = canvasPickerOptions();
  root.innerHTML = options.length ? options.map(item => {
    if (state.canvasPicker.kind === "paper") {
      return `<button class="canvas-picker-option" data-canvas-pick-paper="${escapeHtml(item.id)}" type="button"><strong>${escapeHtml(paperTitle(item))}</strong><span>${escapeHtml([item.venue, item.year, item.read_status].filter(Boolean).join(" · "))}</span><span>${paperProjects(item).map(project => escapeHtml(project)).join(" / ")}</span></button>`;
    }
    return `<button class="canvas-picker-option" data-canvas-pick-note="${escapeHtml(item.id)}" type="button"><strong>${escapeHtml(compactText(item.note || item.quote || "Highlight", 90))}</strong><span>${escapeHtml(item.paper_title || item.paper_id || "")}</span><span>${escapeHtml(annotationTags(item).join(" / "))}</span></button>`;
  }).join("") : '<p class="muted">No matches.</p>';
  qsa("[data-canvas-pick-paper]").forEach(button => button.addEventListener("click", () => applyCanvasPickerPaper(button.dataset.canvasPickPaper)));
  qsa("[data-canvas-pick-note]").forEach(button => button.addEventListener("click", () => applyCanvasPickerNote(button.dataset.canvasPickNote)));
  requestAnimationFrame(() => search?.focus());
}

function closeCanvasPicker() {
  state.canvasPicker = { open: false, kind: "", cardId: "", query: "" };
  renderCanvasPicker();
}

async function applyCanvasPickerPaper(paperId) {
  const card = canvasCardById(state.canvasPicker.cardId);
  const paper = (state.library?.papers || []).find(item => item.id === paperId);
  if (!card || !paper) return;
  card.kind = "paper";
  card.paper_id = paper.id;
  card.title = paperTitle(paper);
  card.text = "";
  card.source_refs = [{ paper_id: paper.id, source: "library-paper" }];
  card.updated_at = new Date().toISOString();
  closeCanvasPicker();
  renderCanvas();
  await saveCanvasBoard({ silent: true });
}

async function applyCanvasPickerNote(annotationId) {
  const card = canvasCardById(state.canvasPicker.cardId);
  const note = (state.allNotes || []).find(item => item.id === annotationId);
  if (!card || !note) return;
  card.kind = "note";
  card.annotation_id = note.id;
  card.paper_id = note.paper_id || "";
  card.title = compactText(note.note || note.quote || "Highlight", 90);
  card.text = note.quote || "";
  card.source_refs = [{ paper_id: note.paper_id || "", annotation_id: note.id, segment_id: note.segment_id || "", source: note.source_scope || "note" }];
  card.updated_at = new Date().toISOString();
  closeCanvasPicker();
  renderCanvas();
  await saveCanvasBoard({ silent: true });
}

async function openCanvasSyncReview() {
  if (!state.canvasBoard?.id) return;
  await saveCanvasBoard({ silent: true });
  const response = await api(`/api/canvas/boards/${encodeURIComponent(state.canvasBoard.id)}/sync-proposals`);
  state.canvasSync = { open: true, proposals: response.proposals || [], selectedIds: new Set((response.proposals || []).map(item => item.id)) };
  renderCanvasSyncModal();
}

function renderCanvasSyncModal() {
  const modal = qs("#canvasSyncModal");
  const root = qs("#canvasSyncResults");
  if (!modal || !root) return;
  modal.classList.toggle("open", Boolean(state.canvasSync.open));
  modal.setAttribute("aria-hidden", state.canvasSync.open ? "false" : "true");
  if (!state.canvasSync.open) return;
  const proposals = state.canvasSync.proposals || [];
  root.innerHTML = proposals.length ? proposals.map(item => `<label class="canvas-sync-row"><input type="checkbox" data-canvas-sync-id="${escapeHtml(item.id)}" ${state.canvasSync.selectedIds.has(item.id) ? "checked" : ""}><span><strong>${escapeHtml(item.paper_title || item.paper_id)}</strong><small>${escapeHtml(item.cluster_title || "Cluster")} → ${escapeHtml(libraryTagLabel(item.to || ""))}</small></span></label>`).join("") : '<p class="muted">No Library tag changes are pending.</p>';
  qsa("[data-canvas-sync-id]").forEach(input => input.addEventListener("change", () => {
    if (input.checked) state.canvasSync.selectedIds.add(input.dataset.canvasSyncId);
    else state.canvasSync.selectedIds.delete(input.dataset.canvasSyncId);
  }));
}

function closeCanvasSyncReview() {
  state.canvasSync.open = false;
  renderCanvasSyncModal();
}

async function applyCanvasSyncReview() {
  if (!state.canvasBoard?.id) return;
  const response = await api(`/api/canvas/boards/${encodeURIComponent(state.canvasBoard.id)}/sync-apply`, { method: "POST", body: JSON.stringify({ proposal_ids: Array.from(state.canvasSync.selectedIds || []) }) });
  if (response.library) state.library = response.library;
  state.canvasSync = { open: false, proposals: response.sync_proposals || [], selectedIds: new Set() };
  renderCanvas();
  renderLibrary();
  toast(`${response.applied?.length || 0} Library tag change(s) applied`);
}

function mindmapNodes() {
  return Array.isArray(state.mindmap?.nodes) ? state.mindmap.nodes : [];
}

function mindmapNodeById(nodeId) {
  return mindmapNodes().find(node => node.id === nodeId) || null;
}

function mindmapChildren(parentId) {
  const nodes = mindmapNodes();
  const explicit = mindmapNodeById(parentId)?.children || [];
  const byId = new Map(nodes.map(node => [node.id, node]));
  const children = explicit.map(id => byId.get(id)).filter(Boolean);
  const implicit = nodes.filter(node => node.parent_id === parentId && !explicit.includes(node.id));
  return [...children, ...implicit];
}

function renderMindmapProjectSelect() {
  const select = qs("#mindmapProject");
  if (!select) return;
  const projects = allLibraryProjects();
  select.innerHTML = projects.map(project => `<option value="${escapeHtml(project)}" ${state.currentMindmapProject === project ? "selected" : ""}>${escapeHtml(project)}</option>`).join("");
}

function renderMindmapBoardList() {
  const root = qs("#mindmapList");
  if (!root) return;
  const items = (state.mindmaps || []).filter(item => item.project === state.currentMindmapProject);
  root.innerHTML = items.length ? items.map(item => `<button class="mindmap-board-item ${state.currentMindmapId === item.id ? "active" : ""}" data-mindmap-board="${escapeHtml(item.id)}" type="button"><strong>${escapeHtml(item.title || "Untitled Mindmap")}</strong><span>${escapeHtml(`${item.node_count || 0} nodes · ${item.updated_at ? new Date(item.updated_at).toLocaleDateString() : "new"}`)}</span></button>`).join("") : '<p class="muted small-text">No views yet.</p>';
  qsa("[data-mindmap-board]").forEach(button => button.addEventListener("click", () => loadMindmap(state.currentMindmapProject, button.dataset.mindmapBoard).catch(error => toast(`Mindmap load failed: ${error.message}`))));
}

async function createMindmapView() {
  const title = window.prompt("Mindmap view title:", "New sensemaking view")?.trim();
  if (!title) return;
  const response = await api("/api/mindmaps", { method: "POST", body: JSON.stringify({ title, project: state.currentMindmapProject || "collaborative" }) });
  state.mindmaps = response.mindmaps || [];
  state.mindmap = response.mindmap || null;
  state.currentMindmapId = state.mindmap?.id || "";
  state.selectedMindmapNodeId = state.mindmap?.root_id || "";
  state.selectedMindmapNodeIds = new Set([state.selectedMindmapNodeId].filter(Boolean));
  renderMindmap();
  toast("Mindmap view created");
}

async function duplicateCurrentMindmapView() {
  if (!state.currentMindmapId) return;
  const title = window.prompt("Duplicate view title:", `${state.mindmap?.title || "Mindmap"} copy`)?.trim();
  if (!title) return;
  const response = await api(`/api/mindmaps/${encodeURIComponent(state.currentMindmapProject || "collaborative")}/${encodeURIComponent(state.currentMindmapId)}/duplicate`, { method: "POST", body: JSON.stringify({ title }) });
  state.mindmaps = response.mindmaps || [];
  state.mindmap = response.mindmap || null;
  state.currentMindmapId = state.mindmap?.id || "";
  state.selectedMindmapNodeId = state.mindmap?.root_id || "";
  state.selectedMindmapNodeIds = new Set([state.selectedMindmapNodeId].filter(Boolean));
  renderMindmap();
  toast("Mindmap view duplicated");
}

async function deleteCurrentMindmapView() {
  if (!state.currentMindmapId) return;
  const title = state.mindmap?.title || "this view";
  if (!window.confirm(`Delete ${title}?`)) return;
  if (state.mindmapSaveTimer) clearTimeout(state.mindmapSaveTimer);
  state.mindmapSaveTimer = null;
  const response = await fetch(`/api/mindmaps/${encodeURIComponent(state.currentMindmapProject || "collaborative")}/${encodeURIComponent(state.currentMindmapId)}`, { method: "DELETE" }).then(apiResponse => {
    if (!apiResponse.ok) throw new Error(`${apiResponse.status} ${apiResponse.statusText}`);
    return apiResponse.json();
  });
  state.mindmaps = response.mindmaps || [];
  const next = state.mindmaps.find(item => item.project === state.currentMindmapProject);
  state.currentMindmapId = next?.id || "";
  state.mindmap = null;
  if (state.currentMindmapId) await loadMindmap(state.currentMindmapProject, state.currentMindmapId);
  else {
    const created = await api("/api/mindmaps", { method: "POST", body: JSON.stringify({ title: `${state.currentMindmapProject || "collaborative"} sensemaking`, project: state.currentMindmapProject || "collaborative" }) });
    state.mindmaps = created.mindmaps || [];
    state.mindmap = created.mindmap || null;
    state.currentMindmapId = state.mindmap?.id || "";
    state.selectedMindmapNodeId = state.mindmap?.root_id || "";
    state.selectedMindmapNodeIds = new Set([state.selectedMindmapNodeId].filter(Boolean));
    renderMindmap();
  }
  toast("Mindmap view deleted");
}

function mindmapVisibleSourceNotes() {
  const query = String(state.mindmapSourceQuery || "").trim().toLowerCase();
  const selectedProjects = state.mindmapSourceProjectFilters || [];
  const selectedTags = state.mindmapSourceNoteFilters || [];
  return (state.allNotes || []).filter(note => {
    if (!noteMatchesProjectFilters(note, selectedProjects)) return false;
    if (!noteMatchesTagFilters(note, selectedTags)) return false;
    if (!query) return true;
    const text = [note.note, note.quote, note.paper_title, note.paper_id, note.segment_id, ...annotationTags(note), ...projectsForNote(note)].filter(Boolean).join(" ").toLowerCase();
    return text.includes(query);
  });
}

function mindmapSourceNoteHtml(note) {
  return `<article class="mindmap-source-note" draggable="true" data-mindmap-source-note="${escapeHtml(note.id || "")}" data-paper-id="${escapeHtml(note.paper_id || "")}">
    <strong>${escapeHtml(compactText(note.note || "Highlight only", 96))}</strong>
    ${note.quote ? `<blockquote>${escapeHtml(compactText(note.quote || "", 130))}</blockquote>` : ""}
    <div class="mindmap-source-note-meta">
      <span>${escapeHtml(compactText(note.paper_title || note.paper_id || "Untitled paper", 72))}</span>
      ${annotationTags(note).slice(0, 3).map(tag => `<span class="note-tag mini-note-tag">${escapeHtml(tag)}</span>`).join("")}
    </div>
  </article>`;
}

function renderMindmapSourcePool() {
  const search = qs("#mindmapSourceSearch");
  if (search && search.value !== state.mindmapSourceQuery) search.value = state.mindmapSourceQuery || "";
  renderMindmapSourceProjectFilters();
  renderMindmapSourceTagFilters();
  const root = qs("#mindmapSourceNotes");
  if (!root) return;
  const notes = mindmapVisibleSourceNotes();
  root.innerHTML = notes.length ? notes.map(mindmapSourceNoteHtml).join("") : '<p class="muted small-text">No notes match the current filters.</p>';
  qsa("[data-mindmap-source-note]").forEach(card => {
    card.addEventListener("dragstart", event => {
      event.dataTransfer.effectAllowed = "copy";
      event.dataTransfer.setData("application/x-paper-reader-note", JSON.stringify({ noteId: card.dataset.mindmapSourceNote }));
      event.dataTransfer.setData("text/plain", card.dataset.mindmapSourceNote || "");
    });
    card.addEventListener("dblclick", () => openNoteSourcePreview(card.dataset.paperId, card.dataset.mindmapSourceNote, ""));
  });
}

function renderMindmapSourceProjectFilters() {
  const root = qs("#mindmapSourceProjectFilters");
  if (!root) return;
  const selected = new Set(state.mindmapSourceProjectFilters || []);
  const projects = allNoteProjects();
  root.innerHTML = `<span class="filter-bar-label">Project</span><button class="tag-filter ${selected.size === 0 ? "active" : ""}" data-mindmap-source-project-clear="true">All</button>${projects.map(project => `<button class="tag-filter project-filter ${selected.has(project) ? "active" : ""}" style="--tag-color:${escapeHtml(project === "Unassigned" ? "#d5dce3" : projectColor(project))}" data-mindmap-source-project="${escapeHtml(project)}" type="button">${escapeHtml(project)}</button>`).join("")}`;
  qsa("[data-mindmap-source-project]").forEach(button => button.addEventListener("click", () => {
    const filters = new Set(state.mindmapSourceProjectFilters || []);
    if (filters.has(button.dataset.mindmapSourceProject)) filters.delete(button.dataset.mindmapSourceProject);
    else filters.add(button.dataset.mindmapSourceProject);
    state.mindmapSourceProjectFilters = Array.from(filters);
    renderMindmapSourcePool();
  }));
  qsa("[data-mindmap-source-project-clear]").forEach(button => button.addEventListener("click", () => {
    state.mindmapSourceProjectFilters = [];
    renderMindmapSourcePool();
  }));
}

function renderMindmapSourceTagFilters() {
  const root = qs("#mindmapSourceTagFilters");
  if (!root) return;
  const selected = new Set(state.mindmapSourceNoteFilters || []);
  const projectScopedNotes = (state.allNotes || []).filter(note => noteMatchesProjectFilters(note, state.mindmapSourceProjectFilters || []));
  const counts = new Map();
  for (const note of projectScopedNotes) for (const tag of annotationTags(note)) counts.set(tag, (counts.get(tag) || 0) + 1);
  const tags = allNoteTags().filter(tag => counts.has(tag) || selected.has(tag));
  root.innerHTML = `<span class="filter-bar-label">Note tag</span><button class="tag-filter ${selected.size === 0 ? "active" : ""}" data-mindmap-source-tag-clear="true">All</button>${tags.slice(0, 36).map(tag => `<button class="tag-filter ${selected.has(tag) ? "active" : ""}" data-mindmap-source-tag="${escapeHtml(tag)}" type="button">${escapeHtml(tag)} <span>${counts.get(tag) || 0}</span></button>`).join("")}`;
  qsa("[data-mindmap-source-tag]").forEach(button => button.addEventListener("click", () => {
    const filters = new Set(state.mindmapSourceNoteFilters || []);
    if (filters.has(button.dataset.mindmapSourceTag)) filters.delete(button.dataset.mindmapSourceTag);
    else filters.add(button.dataset.mindmapSourceTag);
    state.mindmapSourceNoteFilters = Array.from(filters);
    renderMindmapSourcePool();
  }));
  qsa("[data-mindmap-source-tag-clear]").forEach(button => button.addEventListener("click", () => {
    state.mindmapSourceNoteFilters = [];
    renderMindmapSourcePool();
  }));
}

function mindmapNodeText(node) {
  return node?.text || node?.summary || node?.title || "Untitled";
}

function mindmapPathText(node) {
  return Array.isArray(node?.category_path) ? node.category_path.filter(Boolean).join(" / ") : "";
}

function mindmapPaper(node) {
  return (state.library?.papers || []).find(paper => paper.id === node?.paper_id) || null;
}

const mindmapFieldTypes = [
  { id: "text", label: "Text" },
  { id: "paper-tag", label: "Paper Tag" },
  { id: "paper", label: "Paper" },
  { id: "note", label: "Note" },
  { id: "table", label: "Table" },
];

function mindmapFieldType(node) {
  if (!node) return "text";
  const explicit = String(node.field_type || node.type || "").trim();
  if (["frame", "writing", "category"].includes(explicit)) return "text";
  if (mindmapFieldTypes.some(item => item.id === explicit)) return explicit;
  if (node.type === "root") return "root";
  if (node.type === "text") return "text";
  if (node.type === "paper") return "paper";
  if (node.type === "note") return "note";
  if (node.type === "table") return "table";
  const parent = mindmapNodeById(node.parent_id);
  if (parent?.type === "root" || parent?.field_type === "root") return "text";
  return "paper-tag";
}

function mindmapFieldTypeLabel(fieldType) {
  if (fieldType === "root") return "Root";
  return mindmapFieldTypes.find(item => item.id === fieldType)?.label || fieldType;
}

function mindmapNodeLabel(node) {
  const fieldType = mindmapFieldType(node);
  if (fieldType === "paper-tag" && node?.canonical_tag) return libraryTagLabel(node.canonical_tag);
  if (node?.type === "paper") return node.title || mindmapPaper(node)?.title || "Untitled paper";
  if (fieldType === "table") return node?.title || node?.table?.template || "Table";
  return node?.title || mindmapNodeText(node);
}

function mindmapNodeStyle(node, fieldType, depth) {
  const styles = [`--mindmap-depth: ${depth}`];
  if (fieldType === "paper-tag") {
    const tag = node?.canonical_tag || node?.title || node?.text || "paper-tag";
    styles.push(`--tag-color: ${tagColor(tag)}`);
  }
  return styles.join("; ");
}

function mindmapNodeTitleHtml(node, fieldType, title) {
  if (fieldType === "paper-tag") {
    return `<span class="mindmap-node-title mindmap-node-tag-pill">${escapeHtml(title)}</span>`;
  }
  return `<span class="mindmap-node-title">${escapeHtml(title)}</span>`;
}

function mindmapEditableValue(node) {
  const fieldType = mindmapFieldType(node);
  if (fieldType === "table") return node?.title || node?.table?.template || "Table";
  if (fieldType === "paper-tag") return node?.canonical_tag ? libraryTagLabel(node.canonical_tag) : mindmapNodeLabel(node);
  return mindmapNodeLabel(node);
}

function mindmapFieldTypeCss(fieldType) {
  return String(fieldType || "field").replace(/[^a-z0-9-]/gi, "-");
}

function mindmapTypeMenuHtml(node, fieldType) {
  return `<div class="mindmap-type-menu" data-mindmap-type-menu="${escapeHtml(node.id)}">
    ${mindmapFieldTypes.map(item => `<button class="mindmap-type-option ${item.id === fieldType ? "active" : ""}" data-mindmap-type-option="${escapeHtml(node.id)}" data-mindmap-type-value="${escapeHtml(item.id)}" type="button">
      <span class="mindmap-type-swatch mindmap-type-swatch-${escapeHtml(mindmapFieldTypeCss(item.id))}" aria-hidden="true"></span>
      <span>${escapeHtml(item.label)}</span>
    </button>`).join("")}
  </div>`;
}

function mindmapPaperOptions(query) {
  const raw = String(query || "").trim().toLowerCase();
  const papers = state.library?.papers || [];
  const scored = papers.map(paper => {
    const title = paperTitle(paper);
    const haystack = [title, paper.venue, paper.year, ...(paper.tags || []).map(tag => libraryTagLabel(tag))].filter(Boolean).join(" ").toLowerCase();
    if (!raw) return { paper, score: 1 };
    if (title.toLowerCase().includes(raw)) return { paper, score: 3 };
    if (haystack.includes(raw)) return { paper, score: 2 };
    return null;
  }).filter(Boolean);
  return scored.sort((left, right) => right.score - left.score || paperTitle(left.paper).localeCompare(paperTitle(right.paper))).slice(0, 8).map(item => item.paper);
}

function mindmapTagOptions(query) {
  const raw = String(query || "").trim().toLowerCase();
  return allLibraryTags().filter(tag => {
    const label = libraryTagLabel(tag);
    return !raw || tag.toLowerCase().includes(raw) || label.toLowerCase().includes(raw);
  }).slice(0, 10);
}

function mindmapNoteOptions(query) {
  const raw = String(query || "").trim().toLowerCase();
  return (state.allNotes || []).filter(note => {
    const haystack = [note.note, note.quote, note.paper_title, note.paper_id, ...(annotationTags(note) || [])].filter(Boolean).join(" ").toLowerCase();
    return !raw || haystack.includes(raw);
  }).slice(0, 8);
}

function mindmapTypeaheadOptionsHtml(fieldType, query) {
  if (fieldType === "paper") {
    const papers = mindmapPaperOptions(query);
    return papers.length ? papers.map(paper => `<button class="mindmap-typeahead-option" data-mindmap-typeahead-kind="paper" data-mindmap-typeahead-value="${escapeHtml(paper.id)}" type="button">
      <strong>${escapeHtml(paperTitle(paper))}</strong>
      <span>${escapeHtml([paper.venue, paper.year].filter(Boolean).join(" · "))}</span>
    </button>`).join("") : `<p class="mindmap-typeahead-empty">No matching paper</p>`;
  }
  if (fieldType === "paper-tag") {
    const tags = mindmapTagOptions(query);
    const canonical = canonicalTagIdsForInput(query)[0] || query.trim();
    const createOption = canonical && !tags.includes(canonical) ? `<button class="mindmap-typeahead-option" data-mindmap-typeahead-kind="tag" data-mindmap-typeahead-value="${escapeHtml(canonical)}" type="button"><strong>Create tag</strong><span>${escapeHtml(libraryTagLabel(canonical))}</span></button>` : "";
    return tags.length || createOption ? `${tags.map(tag => `<button class="mindmap-typeahead-option" data-mindmap-typeahead-kind="tag" data-mindmap-typeahead-value="${escapeHtml(tag)}" type="button"><strong>${escapeHtml(libraryTagLabel(tag))}</strong><span>${escapeHtml(tag)}</span></button>`).join("")}${createOption}` : `<p class="mindmap-typeahead-empty">No matching tag</p>`;
  }
  if (fieldType === "note") {
    const notes = mindmapNoteOptions(query);
    if (!state.allNotes?.length) return `<p class="mindmap-typeahead-empty">Notes are loading...</p>`;
    return notes.length ? notes.map(note => `<button class="mindmap-typeahead-option" data-mindmap-typeahead-kind="note" data-mindmap-typeahead-value="${escapeHtml(note.id)}" type="button">
      <strong>${escapeHtml(compactText(note.note || note.quote || "Highlight", 72))}</strong>
      <span>${escapeHtml(note.paper_title || note.paper_id || "")}</span>
    </button>`).join("") : `<p class="mindmap-typeahead-empty">No matching note</p>`;
  }
  return "";
}

function mindmapTypeaheadHtml(node, fieldType, value) {
  if (!["paper", "paper-tag", "note"].includes(fieldType)) return "";
  return `<div class="mindmap-typeahead" data-mindmap-typeahead="${escapeHtml(node.id)}">${mindmapTypeaheadOptionsHtml(fieldType, value)}</div>`;
}

function mindmapEditHtml(node, fieldType) {
  const value = state.mindmapEditingNodeId === node.id ? state.mindmapEditDraft : mindmapEditableValue(node);
  const commonAttrs = `data-mindmap-edit-input="${escapeHtml(node.id)}" aria-label="Edit ${escapeHtml(mindmapFieldTypeLabel(fieldType))}"`;
  const input = fieldType === "writing"
    ? `<textarea class="mindmap-edit-input mindmap-edit-textarea" rows="3" ${commonAttrs}>${escapeHtml(value)}</textarea>`
    : `<input class="mindmap-edit-input" value="${escapeHtml(value)}" ${commonAttrs} />`;
  return `<div class="mindmap-edit-wrap">${input}${mindmapTypeaheadHtml(node, fieldType, value)}</div>`;
}

function resolveMindmapPaperRef(value) {
  const raw = String(value || "").trim();
  if (!raw) return null;
  const key = normalizeTitleKey(raw);
  return (state.library?.papers || []).find(paper => paper.id === raw || normalizeTitleKey(paperTitle(paper)) === key)
    || (state.library?.papers || []).find(paper => paperTitle(paper).toLowerCase().includes(raw.toLowerCase()))
    || null;
}

function resolveMindmapNoteRef(value) {
  const raw = String(value || "").trim();
  if (!raw) return null;
  return (state.allNotes || []).find(note => note.id === raw)
    || (state.allNotes || []).find(note => String(note.note || note.quote || "").toLowerCase().includes(raw.toLowerCase()))
    || null;
}

function mindmapRefChipHtml(kind, value) {
  const label = kind === "paper"
    ? (paperTitle(resolveMindmapPaperRef(value) || { id: value }) || value)
    : compactText(resolveMindmapNoteRef(value)?.note || resolveMindmapNoteRef(value)?.quote || value, 46);
  return `<button class="mindmap-ref-chip mindmap-ref-${escapeHtml(kind)}" data-mindmap-ref-kind="${escapeHtml(kind)}" data-mindmap-ref-value="${escapeHtml(value)}" type="button" title="Open ${escapeHtml(kind)} reference">${kind === "paper" ? "P" : "H"}</button><span class="mindmap-ref-label">${escapeHtml(label)}</span>`;
}

function renderWritingWithMindmapRefs(text) {
  const raw = String(text || "");
  if (!raw) return '<span class="muted">Empty writing field</span>';
  const pattern = /@(paper|note|highlight)\(([^)]+)\)/gi;
  let cursor = 0;
  const parts = [];
  raw.replace(pattern, (match, kind, value, offset) => {
    if (offset > cursor) parts.push(escapeHtml(raw.slice(cursor, offset)));
    parts.push(`<span class="mindmap-inline-ref">${mindmapRefChipHtml(kind.toLowerCase(), value.trim())}</span>`);
    cursor = offset + match.length;
    return match;
  });
  if (cursor < raw.length) parts.push(escapeHtml(raw.slice(cursor)));
  return parts.join("").replace(/\n/g, "<br>");
}

function mindmapRefCardHtml(ref) {
  if (!ref) return "";
  if (ref.kind === "paper") {
    const paper = resolveMindmapPaperRef(ref.value) || { id: ref.value, title: ref.value };
    return `<section class="mindmap-ref-card">
      <div class="mindmap-ref-card-header"><strong>${escapeHtml(paperTitle(paper))}</strong><button class="icon-button" data-close-mindmap-ref type="button" title="Close reference">x</button></div>
      <p>${escapeHtml([paper.venue, paper.year, paper.read_status].filter(Boolean).join(" · "))}</p>
      <div class="library-tags">${normalizeTagsInput(paper.tags || []).map(tag => `<span class="library-tag">${escapeHtml(libraryTagLabel(tag))}</span>`).join("")}</div>
      <button class="primary-button mini-button" data-open-mindmap-ref-paper="${escapeHtml(paper.id || "")}" type="button">Open Workspace</button>
    </section>`;
  }
  const note = resolveMindmapNoteRef(ref.value);
  return `<section class="mindmap-ref-card">
    <div class="mindmap-ref-card-header"><strong>${escapeHtml(ref.kind === "note" ? "Note" : "Highlight")}</strong><button class="icon-button" data-close-mindmap-ref type="button" title="Close reference">x</button></div>
    ${note ? `<p>${escapeHtml(note.note || "Highlight only")}</p><blockquote>${escapeHtml(note.quote || "")}</blockquote><p class="muted small-text">${escapeHtml(note.paper_title || note.paper_id || "")}</p><button class="primary-button mini-button" data-open-mindmap-ref-note="${escapeHtml(note.id || "")}" data-paper-id="${escapeHtml(note.paper_id || "")}" type="button">Open Source</button>` : `<p class="muted">Reference not found: ${escapeHtml(ref.value)}</p>`}
  </section>`;
}

function openMindmapRef(kind, value) {
  state.mindmapPinnedRef = { kind, value };
  renderMindmapInspector();
}

function noteNodeFromAllNotes(note, parentId) {
  const now = new Date().toISOString();
  return {
    id: `note-node-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
    type: "note",
    field_type: "note",
    title: compactText(note.note || note.quote || "Highlight", 160),
    text: note.quote || "",
    summary: "",
    parent_id: parentId || state.mindmap?.root_id || "",
    paper_id: note.paper_id || "",
    source: note.paper_title || note.paper_id || "note",
    source_refs: [{ paper_id: note.paper_id || "", annotation_id: note.id || "", segment_id: note.segment_id || "", source: note.source_scope || "paper-note" }],
    note_tags: annotationTags(note),
    category_path: [],
    children: [],
    created_at: now,
    updated_at: now,
  };
}

function ensureMindmapChildren(node) {
  if (!node) return [];
  if (!Array.isArray(node.children)) node.children = [];
  return node.children;
}

function detachMindmapNode(nodeId) {
  for (const node of mindmapNodes()) {
    if (Array.isArray(node.children)) node.children = node.children.filter(id => id !== nodeId);
  }
}

function insertMindmapNodeLocal(node, targetId, position = "child") {
  const target = mindmapNodeById(targetId) || mindmapNodeById(state.mindmap?.root_id) || mindmapNodes()[0];
  if (!target || !node) return;
  detachMindmapNode(node.id);
  if (!mindmapNodeById(node.id)) state.mindmap.nodes.push(node);
  if (position === "before" || position === "after") {
    const parent = mindmapNodeById(target.parent_id) || mindmapNodeById(state.mindmap.root_id);
    node.parent_id = parent?.id || state.mindmap.root_id;
    const siblings = ensureMindmapChildren(parent);
    const targetIndex = siblings.indexOf(target.id);
    const insertAt = targetIndex < 0 ? siblings.length : targetIndex + (position === "after" ? 1 : 0);
    siblings.splice(insertAt, 0, node.id);
  } else {
    node.parent_id = target.id;
    ensureMindmapChildren(target).push(node.id);
  }
  node.updated_at = new Date().toISOString();
}

function mindmapNodeDescendantIds(nodeId) {
  const ids = new Set();
  const visit = id => {
    for (const child of mindmapChildren(id)) {
      if (ids.has(child.id)) continue;
      ids.add(child.id);
      visit(child.id);
    }
  };
  visit(nodeId);
  return ids;
}

function moveMindmapNodeLocal(nodeId, targetId, position = "child") {
  if (!nodeId || nodeId === state.mindmap?.root_id || nodeId === targetId) return false;
  if (mindmapNodeDescendantIds(nodeId).has(targetId)) return false;
  const node = mindmapNodeById(nodeId);
  if (!node) return false;
  insertMindmapNodeLocal(node, targetId, position);
  return true;
}

function mindmapDropPosition(event, row) {
  const rect = row.getBoundingClientRect();
  const ratio = rect.height ? (event.clientY - rect.top) / rect.height : 0.5;
  if (ratio < 0.25) return "before";
  if (ratio > 0.75) return "after";
  return "child";
}

function setMindmapSelection(nodeIds, primaryId = "") {
  const clean = Array.from(new Set((nodeIds || []).filter(id => mindmapNodeById(id))));
  const primary = primaryId && clean.includes(primaryId) ? primaryId : clean[0] || state.mindmap?.root_id || "";
  state.selectedMindmapNodeId = primary;
  state.selectedMindmapNodeIds = new Set(clean.length ? clean : [primary].filter(Boolean));
  if (state.mindmap) {
    state.mindmap.selected_node_id = state.selectedMindmapNodeId;
  }
}

function selectedMindmapNodeIds() {
  if (!(state.selectedMindmapNodeIds instanceof Set)) state.selectedMindmapNodeIds = new Set([state.selectedMindmapNodeId].filter(Boolean));
  if (!state.selectedMindmapNodeIds.size && state.selectedMindmapNodeId) state.selectedMindmapNodeIds.add(state.selectedMindmapNodeId);
  return state.selectedMindmapNodeIds;
}

function topLevelMindmapSelection(ids = Array.from(selectedMindmapNodeIds())) {
  const selected = new Set(ids.filter(id => id && id !== state.mindmap?.root_id));
  return Array.from(selected).filter(id => {
    let parentId = mindmapNodeById(id)?.parent_id || "";
    while (parentId) {
      if (selected.has(parentId)) return false;
      parentId = mindmapNodeById(parentId)?.parent_id || "";
    }
    return true;
  });
}

function mindmapTablePreviewHtml(table = {}) {
  const columns = Array.isArray(table.columns) && table.columns.length ? table.columns : defaultCanvasTable().columns;
  const previewCols = columns.slice(0, 4);
  return `<div class="mindmap-table-preview" style="--mindmap-table-cols:${previewCols.length || 1}">${previewCols.map(column => `<span>${escapeHtml(column)}</span>`).join("")}</div>`;
}

function toggleMindmapCollapsed(nodeId) {
  const node = mindmapNodeById(nodeId);
  if (!node || !mindmapChildren(nodeId).length) return;
  node.collapsed = !node.collapsed;
  node.updated_at = new Date().toISOString();
  renderMindmap();
  scheduleMindmapSave(180);
}

function dataTransferHas(event, type) {
  return Array.from(event.dataTransfer?.types || []).includes(type);
}

async function handleMindmapDrop(event, targetId) {
  event.preventDefault();
  const row = event.currentTarget;
  const position = mindmapDropPosition(event, row);
  const anchor = mindmapScreenAnchor(targetId);
  row.classList.remove("drop-before", "drop-after", "drop-child");
  const notePayload = event.dataTransfer.getData("application/x-paper-reader-note");
  const nodePayload = event.dataTransfer.getData("application/x-paper-reader-mindmap-node");
  if (notePayload) {
    const { noteId } = JSON.parse(notePayload);
    const note = (state.allNotes || []).find(item => item.id === noteId);
    if (!note) return;
    const node = noteNodeFromAllNotes(note, targetId);
    insertMindmapNodeLocal(node, targetId, position);
    state.selectedMindmapNodeId = node.id;
    await saveCurrentMindmap();
    renderMindmap();
    restoreMindmapScreenAnchor(anchor);
    toast("Note copied to Mindmap");
    return;
  }
  if (nodePayload) {
    const { nodeId, nodeIds } = JSON.parse(nodePayload);
    const moveIds = topLevelMindmapSelection(Array.isArray(nodeIds) && nodeIds.length ? nodeIds : [nodeId]);
    let moved = false;
    if (position === "before") {
      for (const id of [...moveIds].reverse()) {
        if (moveMindmapNodeLocal(id, targetId, position)) moved = true;
      }
    } else if (position === "after") {
      let insertTargetId = targetId;
      for (const id of moveIds) {
        if (moveMindmapNodeLocal(id, insertTargetId, position)) {
          moved = true;
          insertTargetId = id;
        }
      }
    } else {
      for (const id of moveIds) {
        if (moveMindmapNodeLocal(id, targetId, position)) moved = true;
      }
    }
    if (moved) {
      setMindmapSelection(moveIds, nodeId || moveIds[0]);
      await saveCurrentMindmap();
      renderMindmap();
      restoreMindmapScreenAnchor(anchor);
      toast(moveIds.length > 1 ? "Nodes moved" : "Node moved");
    }
  }
}

function mindmapNodeHtml(node, depth = 0) {
  const children = mindmapChildren(node.id);
  const selected = selectedMindmapNodeIds().has(node.id);
  const active = selected ? " active" : "";
  const multiSelected = selected && selectedMindmapNodeIds().size > 1 ? " multi-selected" : "";
  const type = node.type || "category";
  const fieldType = mindmapFieldType(node);
  const editing = state.mindmapEditingNodeId === node.id;
  const title = mindmapNodeLabel(node);
  const titleHtml = mindmapNodeTitleHtml(node, fieldType, title);
  const summary = fieldType === "table" ? mindmapTablePreviewHtml(node.table || {}) : fieldType === "text" ? (node.text && node.text !== node.title ? node.text : "") : type === "paper" ? (node.summary || "") : fieldType === "note" ? (node.text || node.summary || "") : "";
  const meta = type === "paper" ? [mindmapPaper(node)?.venue, mindmapPaper(node)?.year].filter(Boolean).join(" · ") : fieldType === "note" ? node.source || "" : "";
  const hasChildren = children.length > 0;
  const collapsed = Boolean(node.collapsed);
  return `
    <div class="mindmap-branch" data-mindmap-branch="${escapeHtml(node.id)}">
      <div class="mindmap-node-row mindmap-node-${escapeHtml(fieldType)}${editing ? " editing" : ""}${active}${multiSelected}" draggable="${fieldType === "root" ? "false" : "true"}" style="${escapeHtml(mindmapNodeStyle(node, fieldType, depth))}" data-mindmap-node-row="${escapeHtml(node.id)}">
        <div class="mindmap-node-type-wrap">
          ${fieldType === "root" ? `<span class="mindmap-node-type-static"><span class="mindmap-node-marker" aria-hidden="true"></span></span>` : `<button class="mindmap-node-type-button" data-mindmap-type-button="${escapeHtml(node.id)}" type="button" aria-label="Change field type: ${escapeHtml(mindmapFieldTypeLabel(fieldType))}" title="Change field type"><span class="mindmap-node-marker" aria-hidden="true"></span></button>`}
          ${state.mindmapTypeMenuNodeId === node.id ? mindmapTypeMenuHtml(node, fieldType) : ""}
        </div>
        <div class="mindmap-node-main" data-select-mindmap-node="${escapeHtml(node.id)}" role="button" tabindex="0">
          ${editing ? mindmapEditHtml(node, fieldType) : `${titleHtml}${summary ? (fieldType === "table" ? summary : `<span class="mindmap-node-summary">${fieldType === "text" ? escapeHtml(compactText(summary, 320)) : escapeHtml(compactText(summary, fieldType === "note" ? 260 : 320))}</span>`) : ""}${meta ? `<span class="mindmap-node-meta">${fieldType === "note" && node.paper_id ? `<button class="mindmap-source-link" data-open-mindmap-paper="${escapeHtml(node.paper_id)}" type="button">${escapeHtml(compactText(meta, 130))}</button>` : escapeHtml(meta)}</span>` : ""}`}
        </div>
        ${hasChildren ? `<button class="mindmap-collapse-button" data-toggle-mindmap-collapse="${escapeHtml(node.id)}" type="button" title="${collapsed ? "Expand" : "Collapse"}">${collapsed ? "+" : "-"}</button>` : ""}
      </div>
      ${hasChildren && !collapsed ? `<div class="mindmap-children">${children.map(child => mindmapNodeHtml(child, depth + 1)).join("")}</div>` : ""}
    </div>`;
}

function renderMindmap() {
  renderMindmapProjectSelect();
  renderMindmapBoardList();
  const projectSelect = qs("#mindmapProject");
  if (projectSelect) projectSelect.value = state.currentMindmapProject || "collaborative";
  const titleInput = qs("#mindmapTitle");
  if (titleInput && titleInput.value !== (state.mindmap?.title || "")) titleInput.value = state.mindmap?.title || "";
  const selectionCount = Math.max(0, selectedMindmapNodeIds().size || (state.selectedMindmapNodeId ? 1 : 0));
  qs("#mindmapSelectionLabel") && (qs("#mindmapSelectionLabel").textContent = `${selectionCount || 0} selected`);
  renderMindmapSourcePool();
  const root = qs("#mindmapRoot");
  if (!root) return;
  if (!state.mindmap) {
    root.className = "mindmap-root muted";
    root.textContent = "Open the Mindmap tab to load the writing graph.";
    renderMindmapInspector();
    return;
  }
  const rootNode = mindmapNodeById(state.mindmap.root_id) || mindmapNodes()[0];
  if (!rootNode) {
    root.className = "mindmap-root muted";
    root.textContent = "No mindmap nodes yet.";
    renderMindmapInspector();
    return;
  }
  root.className = "mindmap-root";
  root.innerHTML = `<div class="mindmap-tree">${mindmapNodeHtml(rootNode, 0)}</div>`;
  renderMindmapWorldTransform();
  qsa("[data-mindmap-node-row]").forEach(row => {
    row.addEventListener("dragstart", event => {
      const nodeId = row.dataset.mindmapNodeRow || "";
      if (!nodeId || nodeId === state.mindmap?.root_id) return;
      if (!selectedMindmapNodeIds().has(nodeId)) setMindmapSelection([nodeId], nodeId);
      const nodeIds = topLevelMindmapSelection();
      state.mindmapDragNodeId = nodeId;
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("application/x-paper-reader-mindmap-node", JSON.stringify({ nodeId, nodeIds }));
      row.classList.add("dragging");
    });
    row.addEventListener("dragover", event => {
      if (!dataTransferHas(event, "application/x-paper-reader-note") && !dataTransferHas(event, "application/x-paper-reader-mindmap-node")) return;
      event.preventDefault();
      const position = mindmapDropPosition(event, row);
      row.classList.toggle("drop-before", position === "before");
      row.classList.toggle("drop-after", position === "after");
      row.classList.toggle("drop-child", position === "child");
    });
    row.addEventListener("dragleave", () => row.classList.remove("drop-before", "drop-after", "drop-child"));
    row.addEventListener("drop", event => handleMindmapDrop(event, row.dataset.mindmapNodeRow || ""));
    row.addEventListener("dragend", () => {
      state.mindmapDragNodeId = "";
      qsa(".drop-before, .drop-after, .drop-child").forEach(node => node.classList.remove("drop-before", "drop-after", "drop-child"));
      qsa(".mindmap-node-row.dragging").forEach(node => node.classList.remove("dragging"));
    });
  });
  root.ondragover = event => {
    if (!dataTransferHas(event, "application/x-paper-reader-note")) return;
    event.preventDefault();
  };
  root.ondrop = async event => {
    if (event.target.closest("[data-mindmap-node-row]")) return;
    const payload = event.dataTransfer.getData("application/x-paper-reader-note");
    if (!payload) return;
    event.preventDefault();
    const anchor = mindmapScreenAnchor(rootNode.id);
    const { noteId } = JSON.parse(payload);
    const note = (state.allNotes || []).find(item => item.id === noteId);
    if (!note) return;
    const node = noteNodeFromAllNotes(note, rootNode.id);
    insertMindmapNodeLocal(node, rootNode.id, "child");
    state.selectedMindmapNodeId = node.id;
    await saveCurrentMindmap();
    renderMindmap();
    restoreMindmapScreenAnchor(anchor);
    toast("Note copied to Mindmap");
  };
  qsa("[data-select-mindmap-node]").forEach(button => {
    const selectNode = event => {
      if (event.target.closest("[data-mindmap-ref-kind]")) return;
      if (event.target.closest("[data-mindmap-edit-input], [data-mindmap-typeahead], [data-mindmap-type-button], [data-mindmap-type-menu]")) return;
      const nodeId = button.dataset.selectMindmapNode || "";
      if (event.shiftKey || event.ctrlKey || event.metaKey) {
        const ids = new Set(selectedMindmapNodeIds());
        if (ids.has(nodeId) && nodeId !== state.mindmap?.root_id) ids.delete(nodeId);
        else ids.add(nodeId);
        setMindmapSelection(Array.from(ids), nodeId);
      } else {
        setMindmapSelection([nodeId], nodeId);
      }
      state.mindmapTypeMenuNodeId = "";
      renderMindmap();
      requestAnimationFrame(() => document.querySelector(`[data-select-mindmap-node="${cssEscape(state.selectedMindmapNodeId)}"]`)?.focus({ preventScroll: true }));
    };
    button.addEventListener("click", selectNode);
    button.addEventListener("dblclick", event => {
      event.preventDefault();
      startMindmapEdit(button.dataset.selectMindmapNode || "");
    });
    button.addEventListener("keydown", event => {
      if (event.key === "Enter") {
        event.preventDefault();
        addMindmapNodeBelow(button.dataset.selectMindmapNode || "");
      } else if (event.key === " ") {
        event.preventDefault();
        selectNode(event);
      } else if (event.key === "F2") {
        event.preventDefault();
        startMindmapEdit(button.dataset.selectMindmapNode || "");
      } else if (event.key === "Tab") {
        event.preventDefault();
        if (event.shiftKey) outdentMindmapNode(button.dataset.selectMindmapNode || "");
        else indentMindmapNode(button.dataset.selectMindmapNode || "");
      } else if (event.key === "Backspace") {
        event.preventDefault();
        backspaceMindmapNode(button.dataset.selectMindmapNode || "");
      } else if (event.key === "Delete") {
        event.preventDefault();
        deleteMindmapNode(button.dataset.selectMindmapNode || "");
      }
    });
  });
  bindMindmapInlineEditing();
  qsa("[data-mindmap-ref-kind]").forEach(button => button.addEventListener("click", event => {
    event.stopPropagation();
    openMindmapRef(button.dataset.mindmapRefKind, button.dataset.mindmapRefValue);
  }));
  qsa("[data-open-mindmap-paper]").forEach(button => button.addEventListener("click", event => {
    event.stopPropagation();
    openMindmapPaper(button.dataset.openMindmapPaper);
  }));
  qsa("[data-toggle-mindmap-collapse]").forEach(button => button.addEventListener("click", event => {
    event.stopPropagation();
    toggleMindmapCollapsed(button.dataset.toggleMindmapCollapse || "");
  }));
  renderMindmapInspector();
}

function mindmapTableEditorHtml(node) {
  const table = node?.table && Array.isArray(node.table.columns) ? node.table : defaultCanvasTable("Research Gap");
  const columns = table.columns || [];
  const rows = table.rows?.length ? table.rows : [Object.fromEntries(columns.map(column => [column, ""]))];
  return `<section class="mindmap-table-editor" data-mindmap-table-editor="${escapeHtml(node.id)}">
    <div class="mindmap-table-editor-header">
      <h3>Table</h3>
      <div>
        <button class="secondary-button mini-button" data-add-mindmap-table-row="${escapeHtml(node.id)}" type="button">+ Row</button>
        <button class="secondary-button mini-button" data-add-mindmap-table-column="${escapeHtml(node.id)}" type="button">+ Column</button>
      </div>
    </div>
    <div class="mindmap-table-grid" style="--mindmap-table-editor-cols:${columns.length || 1}">
      ${columns.map((column, columnIndex) => `<input class="mindmap-table-header-input" data-mindmap-table-column="${escapeHtml(node.id)}" data-column-index="${columnIndex}" value="${escapeHtml(column)}" />`).join("")}
      ${rows.map((row, rowIndex) => columns.map((column, columnIndex) => `<textarea class="mindmap-table-cell-input" data-mindmap-table-cell="${escapeHtml(node.id)}" data-row-index="${rowIndex}" data-column-index="${columnIndex}" rows="2">${escapeHtml(row?.[column] || "")}</textarea>`).join("")).join("")}
    </div>
  </section>`;
}

function renderMindmapInspector() {
  const root = qs("#mindmapInspector");
  if (!root) return;
  const node = mindmapNodeById(state.selectedMindmapNodeId);
  const pinnedRefHtml = state.mindmapPinnedRef ? mindmapRefCardHtml(state.mindmapPinnedRef) : "";
  if (!node) {
    root.className = "mindmap-inspector-empty";
    root.innerHTML = `${pinnedRefHtml}<h2>Node Details</h2><p>Select a field in the mindmap. Press Enter on a field to create the next block.</p>`;
    bindMindmapInspectorEvents(root);
    return;
  }
  const paper = mindmapPaper(node);
  const fieldType = mindmapFieldType(node);
  const title = mindmapNodeLabel(node);
  const sourceRef = Array.isArray(node.source_refs) ? node.source_refs.find(ref => ref.annotation_id || ref.paper_id || ref.segment_id) : null;
  root.className = "mindmap-inspector-section";
  root.innerHTML = `
    ${pinnedRefHtml}
    <h2>${escapeHtml(title)}</h2>
    ${node.type === "paper" && paper ? `<button class="primary-button" data-open-mindmap-paper="${escapeHtml(node.paper_id)}" type="button">Open Paper</button>` : ""}
    ${fieldType === "note" && sourceRef?.annotation_id ? `<button class="primary-button" data-open-mindmap-source-note="${escapeHtml(sourceRef.annotation_id)}" data-paper-id="${escapeHtml(sourceRef.paper_id || node.paper_id || "")}" type="button">Open Source</button>` : ""}
    ${fieldType === "note" && (sourceRef?.paper_id || node.paper_id) ? `<button class="secondary-button" data-open-mindmap-paper="${escapeHtml(sourceRef?.paper_id || node.paper_id || "")}" type="button">Open Paper</button>` : ""}
    <dl class="mindmap-inspector-kv">
      <dt>Kind</dt><dd>${escapeHtml(fieldType === "writing" || fieldType === "frame" ? "Text" : mindmapFieldTypeLabel(fieldType))}</dd>
      ${node.canonical_tag ? `<dt>Tag</dt><dd>${escapeHtml(libraryTagLabel(node.canonical_tag))}</dd>` : ""}
      ${paper ? `<dt>Paper</dt><dd>${escapeHtml(paperTitle(paper))}</dd>` : ""}
      ${mindmapPathText(node) ? `<dt>Path</dt><dd><span class="mindmap-tag-path">${escapeHtml(mindmapPathText(node))}</span></dd>` : ""}
      ${node.source ? `<dt>Source</dt><dd>${escapeHtml(node.source)}</dd>` : ""}
    </dl>
    ${node.summary && fieldType === "paper" ? `<p>${escapeHtml(node.summary)}</p>` : ""}
    ${fieldType === "table" ? mindmapTableEditorHtml(node) : fieldType === "text" && node.text && node.text !== node.title ? `<p>${escapeHtml(node.text)}</p>` : node.text && fieldType === "note" ? `<p>${escapeHtml(node.text)}</p>` : ""}
    ${mindmapAddFieldHtml(node.id)}`;
  bindMindmapInspectorEvents(root);
}

function mindmapAddFieldHtml(parentId) {
  if (!parentId) return "";
  return `<section class="mindmap-field-editor" data-mindmap-field-editor="${escapeHtml(parentId)}">
    <h3>Add Field</h3>
    <label>Type</label>
    <select data-mindmap-new-field-type>
      ${mindmapFieldTypes.filter(item => item.id !== "note").map(item => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.label)}</option>`).join("")}
    </select>
    <label>Value</label>
    <textarea data-mindmap-new-field-text rows="4" placeholder="Paper title, canonical tag, or writing with @paper(...) / @note(...) / @highlight(...)"></textarea>
    <button class="primary-button" data-create-mindmap-field type="button">Create Field</button>
  </section>`;
}

function bindMindmapInspectorEvents(root) {
  root.querySelector("[data-open-mindmap-paper]")?.addEventListener("click", event => openMindmapPaper(event.currentTarget.dataset.openMindmapPaper));
  root.querySelector("[data-open-mindmap-source-note]")?.addEventListener("click", event => {
    const button = event.currentTarget;
    openNoteSourcePreview(button.dataset.paperId, button.dataset.openMindmapSourceNote, "");
    activateView("notes");
  });
  root.querySelector("[data-close-mindmap-ref]")?.addEventListener("click", () => {
    state.mindmapPinnedRef = null;
    renderMindmapInspector();
  });
  root.querySelector("[data-open-mindmap-ref-paper]")?.addEventListener("click", event => openMindmapPaper(event.currentTarget.dataset.openMindmapRefPaper));
  root.querySelector("[data-open-mindmap-ref-note]")?.addEventListener("click", event => {
    const button = event.currentTarget;
    openNoteSourcePreview(button.dataset.paperId, button.dataset.openMindmapRefNote, "");
    activateView("notes");
  });
  root.querySelector("[data-create-mindmap-field]")?.addEventListener("click", () => createMindmapFieldFromInspector(root));
  root.querySelectorAll("[data-mindmap-table-column]").forEach(input => input.addEventListener("input", event => {
    const node = mindmapNodeById(input.dataset.mindmapTableColumn || "");
    if (!node) return;
    if (!node.table || !Array.isArray(node.table.columns)) node.table = defaultCanvasTable("Research Gap");
    const index = Number(input.dataset.columnIndex || 0);
    const oldColumn = node.table.columns[index] || `Column ${index + 1}`;
    const nextColumn = event.target.value.trim() || `Column ${index + 1}`;
    node.table.columns[index] = nextColumn;
    for (const row of node.table.rows || []) {
      if (oldColumn !== nextColumn) {
        row[nextColumn] = row[oldColumn] || row[nextColumn] || "";
        delete row[oldColumn];
      }
    }
    node.updated_at = new Date().toISOString();
    scheduleMindmapSave();
  }));
  root.querySelectorAll("[data-mindmap-table-cell]").forEach(input => input.addEventListener("input", event => {
    const node = mindmapNodeById(input.dataset.mindmapTableCell || "");
    if (!node) return;
    if (!node.table || !Array.isArray(node.table.columns)) node.table = defaultCanvasTable("Research Gap");
    const rowIndex = Number(input.dataset.rowIndex || 0);
    const columnIndex = Number(input.dataset.columnIndex || 0);
    const column = node.table.columns[columnIndex];
    if (!column) return;
    if (!Array.isArray(node.table.rows)) node.table.rows = [];
    if (!node.table.rows[rowIndex]) node.table.rows[rowIndex] = {};
    node.table.rows[rowIndex][column] = event.target.value;
    node.updated_at = new Date().toISOString();
    scheduleMindmapSave();
  }));
  root.querySelector("[data-add-mindmap-table-row]")?.addEventListener("click", event => {
    const node = mindmapNodeById(event.currentTarget.dataset.addMindmapTableRow || "");
    if (!node) return;
    if (!node.table || !Array.isArray(node.table.columns)) node.table = defaultCanvasTable("Research Gap");
    node.table.rows = Array.isArray(node.table.rows) ? node.table.rows : [];
    node.table.rows.push(Object.fromEntries(node.table.columns.map(column => [column, ""])));
    node.updated_at = new Date().toISOString();
    renderMindmapInspector();
    renderMindmap();
    scheduleMindmapSave(120);
  });
  root.querySelector("[data-add-mindmap-table-column]")?.addEventListener("click", event => {
    const node = mindmapNodeById(event.currentTarget.dataset.addMindmapTableColumn || "");
    if (!node) return;
    if (!node.table || !Array.isArray(node.table.columns)) node.table = defaultCanvasTable("Research Gap");
    const column = `Column ${node.table.columns.length + 1}`;
    node.table.columns.push(column);
    node.table.rows = Array.isArray(node.table.rows) ? node.table.rows : [];
    for (const row of node.table.rows) row[column] = "";
    node.updated_at = new Date().toISOString();
    renderMindmapInspector();
    renderMindmap();
    scheduleMindmapSave(120);
  });
  root.querySelectorAll("[data-mindmap-ref-kind]").forEach(button => button.addEventListener("click", event => {
    event.stopPropagation();
    openMindmapRef(button.dataset.mindmapRefKind, button.dataset.mindmapRefValue);
  }));
}

function bindMindmapInlineEditing() {
  qsa("[data-mindmap-type-button]").forEach(button => button.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    const nodeId = button.dataset.mindmapTypeButton || "";
    state.selectedMindmapNodeId = nodeId;
    state.mindmapTypeMenuNodeId = state.mindmapTypeMenuNodeId === nodeId ? "" : nodeId;
    renderMindmap();
  }));
  qsa("[data-mindmap-type-option]").forEach(button => button.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    setMindmapNodeType(button.dataset.mindmapTypeOption || "", button.dataset.mindmapTypeValue || "writing");
  }));
  qsa("[data-mindmap-edit-input]").forEach(input => {
    input.addEventListener("input", () => {
      state.mindmapEditDraft = input.value;
      renderMindmapTypeaheadForInput(input);
    });
    input.addEventListener("keydown", event => {
      if (event.key === "Enter" && !(event.shiftKey && input.tagName === "TEXTAREA")) {
        event.preventDefault();
        commitMindmapEdit(input.dataset.mindmapEditInput || "", input.value, { render: false }).then(() => addMindmapNodeBelow(input.dataset.mindmapEditInput || ""));
      } else if (event.key === "Backspace" && !input.value) {
        event.preventDefault();
        removeMindmapNodeLocal(input.dataset.mindmapEditInput || "");
        state.mindmapEditingNodeId = "";
        state.mindmapEditDraft = "";
        saveCurrentMindmap().then(() => renderMindmap());
      } else if (event.key === "Escape") {
        event.preventDefault();
        cancelMindmapEdit(input.dataset.mindmapEditInput || "");
      }
    });
    input.addEventListener("blur", () => {
      setTimeout(() => {
        if (state.mindmapEditingNodeId === input.dataset.mindmapEditInput) {
          commitMindmapEdit(input.dataset.mindmapEditInput || "", input.value);
        }
      }, 120);
    });
  });
  bindMindmapTypeaheadOptions(document);
}

function bindMindmapTypeaheadOptions(root) {
  root.querySelectorAll?.("[data-mindmap-typeahead-kind]").forEach(button => {
    button.addEventListener("mousedown", event => event.preventDefault());
    button.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      const row = button.closest("[data-mindmap-node-row]");
      applyMindmapTypeaheadSelection(row?.dataset.mindmapNodeRow || "", button.dataset.mindmapTypeaheadKind || "", button.dataset.mindmapTypeaheadValue || "");
    });
  });
}

function renderMindmapTypeaheadForInput(input) {
  const nodeId = input?.dataset?.mindmapEditInput || "";
  const node = mindmapNodeById(nodeId);
  const container = document.querySelector(`[data-mindmap-typeahead="${cssEscape(nodeId)}"]`);
  if (!node || !container) return;
  container.innerHTML = mindmapTypeaheadOptionsHtml(mindmapFieldType(node), input.value || "");
  bindMindmapTypeaheadOptions(container);
}

async function startMindmapEdit(nodeId, options = {}) {
  const node = mindmapNodeById(nodeId);
  if (!node) return;
  const fieldType = mindmapFieldType(node);
  if (fieldType === "root") return;
  state.selectedMindmapNodeId = nodeId;
  state.mindmapEditingNodeId = nodeId;
  state.mindmapEditDraft = Object.prototype.hasOwnProperty.call(options, "draft") ? String(options.draft || "") : mindmapEditableValue(node);
  state.mindmapTypeMenuNodeId = "";
  if (fieldType === "note" && !state.allNotes?.length) {
    loadAllNotes().then(() => {
      if (state.mindmapEditingNodeId === nodeId) renderMindmap();
    }).catch(error => toast(`Load notes failed: ${error.message}`));
  }
  renderMindmap();
  requestAnimationFrame(() => {
    const input = document.querySelector(`[data-mindmap-edit-input="${cssEscape(nodeId)}"]`);
    input?.focus();
    if (options.selectAll === false) {
      const end = input?.value?.length || 0;
      input?.setSelectionRange?.(end, end);
    } else {
      input?.select?.();
    }
    renderMindmapTypeaheadForInput(input);
  });
}

function backspaceMindmapNode(nodeId) {
  const node = mindmapNodeById(nodeId);
  if (!node || node.id === state.mindmap?.root_id) return;
  const value = mindmapEditableValue(node);
  if (!value) {
    deleteMindmapNode(nodeId);
    return;
  }
  startMindmapEdit(nodeId, { draft: value.slice(0, -1), selectAll: false });
}

function cancelMindmapEdit(nodeId) {
  const node = mindmapNodeById(nodeId);
  const value = String(state.mindmapEditDraft || "").trim();
  if (node?.source === "ui-field" && !value && !mindmapChildren(nodeId).length) removeMindmapNodeLocal(nodeId);
  state.mindmapEditingNodeId = "";
  state.mindmapEditDraft = "";
  saveCurrentMindmap().then(() => renderMindmap());
}

function removeMindmapNodeLocal(nodeId) {
  if (!nodeId || nodeId === state.mindmap?.root_id) return;
  const ids = new Set([nodeId]);
  let changed = true;
  while (changed) {
    changed = false;
    for (const node of mindmapNodes()) {
      if (ids.has(node.parent_id) && !ids.has(node.id)) {
        ids.add(node.id);
        changed = true;
      }
    }
  }
  for (const node of mindmapNodes()) {
    if (Array.isArray(node.children)) node.children = node.children.filter(id => !ids.has(id));
  }
  state.mindmap.nodes = mindmapNodes().filter(node => !ids.has(node.id));
  if (ids.has(state.selectedMindmapNodeId)) state.selectedMindmapNodeId = state.mindmap?.root_id || "";
  if (ids.has(state.mindmapEditingNodeId)) state.mindmapEditingNodeId = "";
}

async function commitMindmapEdit(nodeId, value, options = {}) {
  const node = mindmapNodeById(nodeId);
  if (!node) return;
  const fieldType = mindmapFieldType(node);
  const raw = String(value || "");
  const trimmed = raw.trim();
  if (fieldType === "writing") {
    node.title = "Writing";
    node.text = raw;
  } else if (fieldType === "text") {
    node.title = trimmed || "Untitled";
    node.text = node.title;
    const parent = mindmapNodeById(node.parent_id);
    node.category_path = parent?.category_path ? [...parent.category_path, node.title].filter(Boolean) : [node.title].filter(Boolean);
    const tagMatch = node.title.match(/#([\w\-./\u4e00-\u9fff]+)/);
    node.branch_tag_candidate = tagMatch ? tagMatch[1] : node.branch_tag_candidate || "";
  } else if (fieldType === "paper-tag") {
    const canonical = trimmed ? (canonicalTagIdsForInput(trimmed)[0] || trimmed) : "";
    node.canonical_tag = canonical;
    node.title = canonical ? libraryTagLabel(canonical) : "";
    const parent = mindmapNodeById(node.parent_id);
    node.category_path = [...(parent?.category_path || []), node.title].filter(Boolean);
  } else if (fieldType === "paper") {
    const paper = resolveMindmapPaperRef(trimmed);
    if (paper) {
      node.paper_id = paper.id;
      node.title = paperTitle(paper);
      node.summary = node.summary || "";
    } else if (trimmed) {
      node.title = trimmed;
      node.paper_id = "";
    } else {
      node.title = "";
      node.paper_id = "";
      node.summary = "";
    }
  } else if (fieldType === "frame" || fieldType === "category") {
    node.title = trimmed;
    node.text = node.title;
    node.category_path = node.title ? [node.title] : [];
  } else if (fieldType === "note") {
    node.title = trimmed;
  } else if (fieldType === "table") {
    node.title = trimmed || node.table?.template || "Research Gap Table";
    if (!node.table || !Array.isArray(node.table.columns)) node.table = defaultCanvasTable("Research Gap");
  }
  node.updated_at = new Date().toISOString();
  state.mindmapEditingNodeId = "";
  state.mindmapEditDraft = "";
  await saveCurrentMindmap();
  if (options.render !== false) renderMindmap();
}

async function deleteMindmapNode(nodeId) {
  const node = mindmapNodeById(nodeId);
  if (!node || node.id === state.mindmap?.root_id) return;
  const ids = selectedMindmapNodeIds().has(nodeId) ? topLevelMindmapSelection() : [nodeId];
  for (const id of ids) removeMindmapNodeLocal(id);
  await saveCurrentMindmap();
  renderMindmap();
  toast(ids.length > 1 ? "Fields deleted" : "Field deleted");
}

async function indentMindmapNode(nodeId) {
  const node = mindmapNodeById(nodeId);
  const parent = mindmapNodeById(node?.parent_id);
  if (!node || !parent || node.id === state.mindmap?.root_id) return;
  const siblings = ensureMindmapChildren(parent);
  const index = siblings.indexOf(node.id);
  if (index <= 0) return;
  const previousSibling = mindmapNodeById(siblings[index - 1]);
  if (!previousSibling) return;
  insertMindmapNodeLocal(node, previousSibling.id, "child");
  setMindmapSelection([node.id], node.id);
  await saveCurrentMindmap();
  renderMindmap();
}

async function outdentMindmapNode(nodeId) {
  const node = mindmapNodeById(nodeId);
  const parent = mindmapNodeById(node?.parent_id);
  if (!node || !parent || parent.id === state.mindmap?.root_id || node.id === state.mindmap?.root_id) return;
  insertMindmapNodeLocal(node, parent.id, "after");
  setMindmapSelection([node.id], node.id);
  await saveCurrentMindmap();
  renderMindmap();
}

async function setMindmapNodeType(nodeId, fieldType) {
  const node = mindmapNodeById(nodeId);
  if (!node || fieldType === "root") return;
  const value = mindmapEditableValue(node);
  node.type = fieldType;
  node.field_type = fieldType;
  if (fieldType === "text") {
    node.title = value || "Text";
    node.text = node.text || node.title;
  } else if (fieldType === "paper-tag") {
    const canonical = canonicalTagIdsForInput(value)[0] || value;
    node.canonical_tag = canonical;
    node.title = libraryTagLabel(canonical);
  } else if (fieldType === "paper") {
    const paper = resolveMindmapPaperRef(value);
    node.paper_id = paper?.id || node.paper_id || "";
    node.title = paper ? paperTitle(paper) : value;
  } else if (fieldType === "frame") {
    node.title = value || "Frame";
    node.text = node.title;
    node.category_path = [node.title];
  } else if (fieldType === "note") {
    node.title = value || "Note";
    node.source = node.source || "ui-field";
  } else if (fieldType === "table") {
    node.title = value || "Research Gap Table";
    node.table = node.table && Array.isArray(node.table.columns) ? node.table : defaultCanvasTable("Research Gap");
  }
  node.updated_at = new Date().toISOString();
  state.mindmapTypeMenuNodeId = "";
  await saveCurrentMindmap();
  startMindmapEdit(nodeId);
}

async function applyMindmapTypeaheadSelection(nodeId, kind, value) {
  const node = mindmapNodeById(nodeId);
  if (!node) return;
  if (kind === "paper") {
    const paper = (state.library?.papers || []).find(item => item.id === value);
    if (!paper) return;
    node.type = "paper";
    node.field_type = "paper";
    node.paper_id = paper.id;
    node.title = paperTitle(paper);
    node.summary = node.summary || "";
  } else if (kind === "tag") {
    const canonical = canonicalTagIdsForInput(value)[0] || value;
    node.type = "paper-tag";
    node.field_type = "paper-tag";
    node.canonical_tag = canonical;
    node.title = libraryTagLabel(canonical);
    const parent = mindmapNodeById(node.parent_id);
    node.category_path = [...(parent?.category_path || []), node.title].filter(Boolean);
  } else if (kind === "note") {
    const note = (state.allNotes || []).find(item => item.id === value);
    if (!note) return;
    node.type = "note";
    node.field_type = "note";
    node.title = compactText(note.note || note.quote || "Highlight", 90);
    node.text = note.quote || "";
    node.source = note.paper_title || note.paper_id || "note";
    node.source_refs = [{ annotation_id: note.id, paper_id: note.paper_id || "" }];
  }
  node.updated_at = new Date().toISOString();
  state.mindmapEditingNodeId = "";
  state.mindmapEditDraft = "";
  await saveCurrentMindmap();
  renderMindmap();
}

async function saveCurrentMindmap(options = {}) {
  if (!state.mindmap) return null;
  state.mindmap.selected_node_id = state.selectedMindmapNodeId || state.mindmap.selected_node_id || state.mindmap.root_id || "";
  state.mindmap.viewport = mindmapViewport();
  state.mindmap.updated_at = new Date().toISOString();
  setMindmapSaveState("Saving...", "saving");
  const project = state.currentMindmapProject || state.mindmap.project || "collaborative";
  const mindmapId = state.currentMindmapId || state.mindmap.id || "";
  const path = mindmapId ? `/api/mindmaps/${encodeURIComponent(project)}/${encodeURIComponent(mindmapId)}` : `/api/mindmaps/${encodeURIComponent(project)}`;
  const response = await api(path, {
    method: "POST",
    body: JSON.stringify(state.mindmap),
  });
  state.mindmap = response.mindmap || state.mindmap;
  state.currentMindmapId = state.mindmap?.id || state.currentMindmapId;
  state.mindmaps = response.mindmaps || state.mindmaps || [];
  setMindmapSaveState("Saved", "saved");
  renderMindmapBoardList();
  if (!options.silent) toast("Mindmap saved");
  return state.mindmap;
}

async function createMindmapFieldFromInspector(root) {
  const editor = root.querySelector("[data-mindmap-field-editor]");
  const parentId = editor?.dataset.mindmapFieldEditor || state.mindmap?.root_id || "";
  const fieldType = editor?.querySelector("[data-mindmap-new-field-type]")?.value || "writing";
  const value = editor?.querySelector("[data-mindmap-new-field-text]")?.value?.trim() || "";
  await createMindmapField(parentId, fieldType, value);
}

async function createMindmapField(parentId, fieldType, value, options = {}) {
  if (!state.mindmap || !parentId) return;
  const parent = mindmapNodeById(parentId) || mindmapNodeById(state.mindmap.root_id);
  const now = new Date().toISOString();
  let node = {
    id: `field-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
    type: fieldType,
    field_type: fieldType,
    title: value || mindmapFieldTypeLabel(fieldType),
    parent_id: parent?.id || state.mindmap.root_id,
    paper_id: "",
    category_path: parent?.category_path ? [...parent.category_path] : [],
    summary: "",
    text: "",
    source: "ui-field",
    source_refs: [],
    inline_refs: [],
    children: [],
    created_at: now,
    updated_at: now,
  };
  if (fieldType === "paper") {
    const paper = resolveMindmapPaperRef(value) || (state.currentPaperId ? state.library?.papers?.find(item => item.id === state.currentPaperId) : null);
    if (!paper && !options.allowBlank) {
      toast("Search or open a paper first");
      return;
    }
    node.paper_id = paper?.id || "";
    node.title = paper ? paperTitle(paper) : value;
    node.category_path = parent?.category_path ? [...parent.category_path] : [];
  } else if (fieldType === "paper-tag") {
    const canonical = canonicalTagIdsForInput(value)[0] || value;
    node.canonical_tag = canonical;
    node.title = libraryTagLabel(canonical);
    node.category_path = [...(parent?.category_path || []), node.title];
  } else if (fieldType === "text") {
    node.title = value || "Text";
    node.text = node.title;
    node.category_path = [...(parent?.category_path || []), node.title].filter(Boolean);
  } else if (fieldType === "writing") {
    node.type = "text";
    node.field_type = "text";
    node.title = value || "Text";
    node.text = value;
  } else if (fieldType === "frame") {
    node.type = "text";
    node.field_type = "text";
    node.category_path = [value || node.title];
  } else if (fieldType === "table") {
    node.title = value || "Research Gap Table";
    node.table = defaultCanvasTable("Research Gap");
  }
  state.mindmap.nodes.push(node);
  if (parent) {
    const children = [...(parent.children || [])].filter(Boolean);
    const insertIndex = options.afterNodeId ? children.indexOf(options.afterNodeId) : -1;
    if (insertIndex >= 0) children.splice(insertIndex + 1, 0, node.id);
    else children.push(node.id);
    parent.children = [...new Set(children)];
  }
  state.selectedMindmapNodeId = node.id;
  await saveCurrentMindmap();
  if (options.edit) startMindmapEdit(node.id);
  else renderMindmap();
  if (!options.silent) toast("Field created");
  return node;
}

async function addMindmapNodeBelow(nodeId) {
  const node = mindmapNodeById(nodeId);
  if (!node || mindmapFieldType(node) === "root") return;
  const fieldType = mindmapFieldType(node);
  await createMindmapField(node.parent_id || state.mindmap?.root_id || "", fieldType, "", { allowBlank: true, afterNodeId: node.id, edit: true, silent: true });
}

async function openMindmapPaper(paperId) {
  if (!paperId) return;
  await loadPaper(paperId);
  activateView("reader");
}

function categoryPathForMindmapNode(nodeId) {
  const node = mindmapNodeById(nodeId);
  if (!node) return normalizeTagsInput(qs("#mindmapCategoryInput")?.value || "Uncategorized");
  const fieldType = mindmapFieldType(node);
  if (["text", "category", "frame", "paper-tag"].includes(fieldType) || node.type === "category") return Array.isArray(node.category_path) && node.category_path.length ? node.category_path : [mindmapNodeLabel(node) || "Uncategorized"];
  return Array.isArray(node.category_path) && node.category_path.length ? node.category_path : ["Uncategorized"];
}

function categoryPathFromInput() {
  const input = qs("#mindmapCategoryInput");
  const value = input?.value?.trim() || "Uncategorized";
  return value.split(/[\\/]+/).map(item => item.trim()).filter(Boolean);
}

async function addPaperToMindmap(paperId, options = {}) {
  if (!paperId) return;
  const categoryPath = options.categoryPath || categoryPathFromInput();
  const project = state.currentMindmapProject || "collaborative";
  const mindmapId = state.currentMindmapId || state.mindmap?.id || "";
  const path = mindmapId ? `/api/mindmaps/${encodeURIComponent(project)}/${encodeURIComponent(mindmapId)}/paper-instances` : `/api/mindmaps/${encodeURIComponent(project)}/paper-instances`;
  const response = await api(path, {
    method: "POST",
    body: JSON.stringify({ paper_id: paperId, mindmap_id: mindmapId, category_path: categoryPath, include_takeaway: options.includeTakeaway !== false, source: options.source || "ui-add" }),
  });
  state.mindmap = response.mindmap || state.mindmap;
  state.currentMindmapId = state.mindmap?.id || state.currentMindmapId;
  state.mindmaps = response.mindmaps || state.mindmaps || [];
  if (response.library) state.library = response.library;
  state.selectedMindmapNodeId = response.node?.id || state.selectedMindmapNodeId;
  state.selectedMindmapNodeIds = new Set([state.selectedMindmapNodeId].filter(Boolean));
  renderMindmap();
  renderLibrary();
  toast("Paper added to Mindmap");
}

async function addCurrentPaperToMindmapNode(nodeId = "") {
  if (!state.currentPaperId) {
    toast("Open a paper first");
    return;
  }
  await addPaperToMindmap(state.currentPaperId, { categoryPath: categoryPathForMindmapNode(nodeId), source: "current-paper" });
}

async function searchMindmapPapers() {
  const query = qs("#mindmapSearchInput")?.value?.trim() || "";
  state.mindmapSearchLoading = true;
  renderMindmapSearchResults();
  try {
    const response = await api(`/api/mindmaps/${encodeURIComponent(state.currentMindmapProject || "collaborative")}/paper-search`, {
      method: "POST",
      body: JSON.stringify({ query, limit: 20 }),
    });
    state.mindmapSearchResults = response.results || [];
  } catch (error) {
    toast(`Mindmap search failed: ${error.message}`);
    state.mindmapSearchResults = [];
  } finally {
    state.mindmapSearchLoading = false;
    renderMindmapSearchResults();
  }
}

function renderMindmapSearchResults() {
  const root = qs("#mindmapSearchResults");
  if (!root) return;
  if (state.mindmapSearchLoading) {
    root.innerHTML = '<p class="muted small-text">Searching...</p>';
    return;
  }
  const items = state.mindmapSearchResults || [];
  if (!items.length) {
    root.innerHTML = '<p class="muted small-text">Search Library to add selected papers.</p>';
    return;
  }
  root.innerHTML = items.map(item => `
    <section class="mindmap-search-row">
      <strong>${escapeHtml(item.title || item.paper_id)}</strong>
      <span>${escapeHtml([item.venue, item.year, item.read_status].filter(Boolean).join(" · "))}</span>
      <span>${escapeHtml((item.tags || []).slice(0, 3).join(" / "))}</span>
      <button class="secondary-button mini-button" data-add-search-paper-to-mindmap="${escapeHtml(item.paper_id)}" type="button">Add to category</button>
    </section>`).join("");
  qsa("[data-add-search-paper-to-mindmap]").forEach(button => button.addEventListener("click", () => addPaperToMindmap(button.dataset.addSearchPaperToMindmap, { source: "mindmap-search" })));
}

function renderPaperSelect() {
  const select = qs("#paperSelect");
  if (!select) return;
  select.innerHTML = "";
  if (!state.library?.papers?.length) {
    select.innerHTML = '<option>No papers imported</option>';
    return;
  }
  select.innerHTML = '<option value="">Open from Library…</option>';
  for (const id of state.paperTabs) {
    const paper = state.library.papers.find(item => item.id === id);
    if (!paper) continue;
    const option = document.createElement("option");
    option.value = paper.id;
    option.textContent = paperTitle(paper);
    if (paper.id === state.currentPaperId) option.selected = true;
    select.appendChild(option);
  }
}

async function loadPaper(paperId, options = {}) {
  if (!paperId) return false;
  const version = ++state.paperLoadVersion;
  state.paperLoadingId = paperId;
  renderPaperTabs();
  qs("#readerView").inert = true;
  try {
    await flushCurrentPaperEdits();
    if (version !== state.paperLoadVersion) return false;
    saveWorkspaceScrollPosition();
    capturePaperSession();
    const session = paperSession(paperId);
    const fresh = !options.force && session.payload && Date.now() - session.loadedAt < paperCacheMaxAge;
    if (paperId === state.currentPaperId && fresh) return true;
    if (!fresh) {
      const payload = await api(`/api/papers/${encodeURIComponent(paperId)}`);
      if (version !== state.paperLoadVersion) return false;
      Object.assign(session, {
        payload,
        annotations: payload.annotations?.annotations || [],
        thinking: normalizeThinkingData(payload.thinking || {}, { seed: false }),
        takeawayDoc: normalizeTakeawayDoc(payload.takeaway_doc || {}),
        readingProgress: normalizeReadingProgress(payload.reading_progress || {}),
        references: referenceHints(payload.segments || []),
        readingProgressDirty: false, thinkingDirty: false, takeawayDirty: false,
        loadedAt: Date.now(),
        readingTeacher: emptyReadingTeacher(session.readingTeacher?.enabled !== false),
        libraryUpdatedAt: state.library?.papers?.find(item => item.id === paperId)?.updated_at,
      });
      // Reference enrichment is independent of displaying the paper body.
      session.referencePromise = api(`/api/papers/${encodeURIComponent(paperId)}/references`).then(index => {
        session.references = { ...session.references, ...(index.references || {}) };
        if (state.currentPaperId === paperId && state.paperSessions.get(paperId) === session) state.references = session.references;
      }).catch(error => {
        console.error(`Reference index failed for ${paperId}`, error);
        if (state.currentPaperId === paperId) toast(`References unavailable: ${error.message}`);
      });
    }
    if (version !== state.paperLoadVersion) return false;
    disconnectReadingProgressTracker();
    closeDrawer({ saved: true });
    closeFigureModal();
    closeReferenceModal();
    state.currentSelection = null;
    state.currentPaperId = paperId;
    const defaults = {
      workspaceMode: "read", paperMapTab: "map", collapsedOutlineIds: new Set(),
      collapsedTakeawayBlockIds: new Set(), takeawayUndoStack: [], takeawayRedoStack: [],
      takeawayDocVersion: 0, takeawaySelectedBlockIds: new Set(), takeawayLastSelectedBlockId: "",
      takeawaySelectionMode: false, chatDraft: "", chatSelectionDraft: null, chatMode: "source",
      chatUseProjectContext: false, thinkingTab: "writing", presentationReportOpen: false,
      chatScroll: { top: 0, atEnd: true }, chatError: "",
      thinkingComposerMode: "chat", manualOutputDraft: { prompt: "", content: "" },
      referenceIntakeDrafts: {},
      expandedMarginNotes: new Set(),
      collapsedDefinitionNotes: new Set(),
    };
    for (const key of paperSessionFields) {
      if (Object.prototype.hasOwnProperty.call(session, key)) state[key] = session[key];
      else if (Object.prototype.hasOwnProperty.call(defaults, key)) state[key] = defaults[key];
    }
    state.figures = mergeFigureFallbacks(buildFigureIndex(state.payload.segments || []), state.payload.figure_fallbacks || {});
    state.referenceLoads = {};
    state.takeawayHistoryRestoring = false;
    state.takeawayDragBlockId = "";
    state.takeawayArrangePreview = null;
    state.workspaceMetadataEditor = { open: false, saving: false, paperId: "", projects: [], tags: [], importance: 0 };
    const savedTakeawayTab = qs('[data-reader-side-pane="takeaway"]');
    if (savedTakeawayTab) savedTakeawayTab.hidden = !state.takeawayDoc.blocks.length;
    if (!state.takeawayDoc.blocks.length) state.presentationReportOpen = false;
    session.lastUsed = Date.now();
    if (!state.paperTabs.includes(paperId)) state.paperTabs.push(paperId);
    renderPaperSelect();
    renderSidebar();
    renderReader();
    setWorkspaceMode(state.workspaceMode);
    setReaderSidePane(state.presentationReportOpen ? "takeaway" : "sensemaking");
    if (state.presentationReportOpen) renderPresentationPanel(state.payload?.outline || {});
    restoreWorkspaceScrollPosition();
    capturePaperSession();
    persistPaperTabs();
    prunePaperCache();
    return true;
  } catch (error) {
    console.error("Paper switch failed", error);
    toast(`Could not open paper: ${error.message}. Your current paper is kept open.`);
    return false;
  } finally {
    if (version === state.paperLoadVersion) {
      state.paperLoadingId = "";
      qs("#readerView").inert = false;
      renderPaperTabs();
      watchReaderBackground();
      watchFeishuMetadata();
      if (state.payload && state.readingTeacher.needsRefresh) refreshReadingTeacher();
      if (state.currentPaperId) scheduleReadingTeacher(state.currentPaperId);
    }
  }
}

function disconnectReadingProgressTracker() {
  if (state.readingObserver) state.readingObserver.disconnect();
  state.readingObserver = null;
  state.readingVisibleSegments.clear();
  state.currentOutlineId = "";
  state.readingLastTick = 0;
  if (state.readingFlushTimer) clearInterval(state.readingFlushTimer);
  state.readingFlushTimer = null;
  updateCurrentOutlineHint([], "");
}

function canTrackReadingProgress() {
  return Boolean(state.currentPaperId && state.payload && !state.paperLoadingId && document.body.dataset.activeView === "reader" && state.workspaceMode !== "think" && !document.hidden);
}

function tickReadingProgress(options = {}) {
  const now = performance.now();
  if (!state.readingLastTick) state.readingLastTick = now;
  const delta = Math.min(1500, Math.max(0, now - state.readingLastTick));
  state.readingLastTick = now;
  if (!canTrackReadingProgress() || !state.readingVisibleSegments.size || delta < 100) return;
  for (const segmentId of state.readingVisibleSegments) {
    const item = ensureReadingProgressSegment(segmentId);
    item.visible_ms = Math.max(0, Number(item.visible_ms || 0)) + delta;
    item.updated_at = new Date().toISOString();
  }
  state.readingProgress.summary = readingSummaryFromCurrentState();
  state.readingProgressDirty = true;
  applyReadingProgressDecorations();
  if (!options.skipSchedule) scheduleReadingProgressSave();
}

function initReadingProgressTracker() {
  disconnectReadingProgressTracker();
  const paragraphs = qsa("#documentRoot .paragraph[data-pid]");
  if (!paragraphs.length || !state.currentPaperId) return;
  state.readingObserver = new IntersectionObserver(entries => {
    tickReadingProgress({ skipSchedule: true });
    for (const entry of entries) {
      const segmentId = entry.target.dataset.pid;
      if (!segmentId) continue;
      const visible = entry.isIntersecting && entry.intersectionRatio >= 0.6;
      if (visible && !state.readingVisibleSegments.has(segmentId)) {
        state.readingVisibleSegments.add(segmentId);
        const item = ensureReadingProgressSegment(segmentId);
        item.visits = Math.max(0, Number(item.visits || 0)) + 1;
        item.updated_at = new Date().toISOString();
        state.readingProgressDirty = true;
      } else if (!visible) {
        state.readingVisibleSegments.delete(segmentId);
      }
    }
    applyReadingProgressDecorations();
    scheduleReadingProgressSave();
  }, { threshold: [0, 0.25, 0.6, 0.9] });
  paragraphs.forEach(paragraph => state.readingObserver.observe(paragraph));
  state.readingLastTick = performance.now();
  state.readingFlushTimer = setInterval(() => tickReadingProgress(), 1000);
  applyReadingProgressDecorations();
}

function scheduleReadingProgressSave(delay = 4500) {
  if (!state.currentPaperId || !state.readingProgressDirty) return;
  if (state.readingSaveTimer) clearTimeout(state.readingSaveTimer);
  state.readingSaveTimer = setTimeout(() => {
    flushReadingProgress({ silent: true }).catch(error => console.error("Reading progress save failed", error));
  }, delay);
}

async function flushReadingProgress(options = {}) {
  if (!state.currentPaperId || !state.readingProgressDirty) return;
  tickReadingProgress({ skipSchedule: true });
  if (state.readingSaveTimer) clearTimeout(state.readingSaveTimer);
  state.readingSaveTimer = null;
  const paperId = state.currentPaperId;
  const payload = { segments: state.readingProgress?.segments || {} };
  state.readingProgressDirty = false;
  try {
    const response = await queuePaperWrite(paperId, "reading-progress", payload);
    if (paperId !== state.currentPaperId) return;
    if (!state.readingProgressDirty) state.readingProgress = normalizeReadingProgress(response.reading_progress || state.readingProgress);
    if (response.metadata && state.payload?.metadata) Object.assign(state.payload.metadata, response.metadata);
    const paper = state.library?.papers?.find(item => item.id === paperId);
    if (paper && response.metadata) Object.assign(paper, response.metadata);
    renderPaperMeta();
    applyReadingProgressDecorations();
    if (!options.silent) toast("Reading progress saved");
  } catch (error) {
    if (paperId === state.currentPaperId) state.readingProgressDirty = true;
    paperSession(paperId).readingProgressDirty = true;
    if (options.strict) throw error;
    toast(`Reading progress save failed: ${error.message}`);
  }
}

function markReadingProgressDirtyFromAnnotations() {
  if (!state.currentPaperId || !state.readingProgress) return;
  for (const annotation of state.annotations || []) {
    if (annotation.segment_id) ensureReadingProgressSegment(annotation.segment_id);
  }
  state.readingProgress.summary = readingSummaryFromCurrentState();
  state.readingProgressDirty = true;
  applyReadingProgressDecorations();
  scheduleReadingProgressSave(900);
}

function applyReadingProgressDecorations() {
  qsa("#documentRoot .paragraph[data-pid]").forEach(paragraph => {
    const progress = readingProgressForSegment(paragraph.dataset.pid);
    paragraph.dataset.readingState = progress.state;
    paragraph.style.setProperty("--reading-depth", String(progress.depth || 0));
    paragraph.removeAttribute("title");
  });
  const outline = state.payload?.outline?.outline || [];
  qsa("#outlineList [data-outline-pid]").forEach(button => {
    const index = Number(button.dataset.outlineIndex || 0);
    const progress = readingProgressForOutlineItem(outline[index] || { id: button.dataset.outlinePid }, outline, index);
    button.dataset.readingState = progress.state;
    button.style.setProperty("--reading-depth", String(progress.depth || 0));
    button.removeAttribute("title");
  });
  updateCurrentOutlineHint(outline);
}

function currentVisibleSegmentId() {
  const paragraphs = qsa("#documentRoot .paragraph[data-pid]");
  const viewportTop = 88;
  let best = null;
  for (const paragraph of paragraphs) {
    const rect = paragraph.getBoundingClientRect();
    if (rect.bottom < viewportTop || rect.top > window.innerHeight) continue;
    const distance = Math.abs(Math.max(rect.top, viewportTop) - viewportTop);
    if (!best || distance < best.distance) best = { segmentId: paragraph.dataset.pid || "", distance };
  }
  return best?.segmentId || "";
}

function outlineItemForSegment(segmentId, outlineItems = state.payload?.outline?.outline || []) {
  const number = segmentIdNumber(segmentId);
  if (!Number.isFinite(number)) return null;
  let current = null;
  for (const item of outlineItems) {
    const start = segmentIdNumber(item?.id || "");
    if (!Number.isFinite(start) || start > number) continue;
    current = item;
  }
  return current;
}

function updateCurrentOutlineHint(outlineItems = state.payload?.outline?.outline || [], segmentId = currentVisibleSegmentId()) {
  const current = outlineItemForSegment(segmentId, outlineItems);
  const currentId = visibleOutlineIdForItem(current, outlineItems);
  const changed = state.currentOutlineId !== currentId;
  state.currentOutlineId = currentId;
  qsa("#outlineList [data-outline-pid]").forEach(button => {
    const active = Boolean(currentId && button.dataset.outlinePid === currentId);
    if (active) {
      button.dataset.currentSection = "true";
      button.setAttribute("aria-current", "location");
      if (changed) button.scrollIntoView({ block: "nearest" });
    } else {
      delete button.dataset.currentSection;
      button.removeAttribute("aria-current");
    }
  });
}

function buildFigureIndex(segments) {
  const figures = {};
  let pendingImages = [];
  for (const segment of segments) {
    const markdown = segment.markdown || "";
    const images = [...markdown.matchAll(/!\[[^\]]*\]\(([^)]+)\)/g)]
      .map(match => ({ src: assetUrl(match[1]), segment_id: segment.id }));
    pendingImages.push(...images);
    const captionMatch = displayText(markdown).match(/(?:^|\n)\s*(?:fig(?:ure)?\.?)\s*(\d+)(?:\s*(?:[.\-]\s*)?\(?[a-z]\)?)?\s*[:.]\s*(.+)/is);
    if (captionMatch) {
      const number = captionMatch[1];
      const previous = figures[number];
      const parts = [...new Map([...(previous?.images || []), ...pendingImages].map(image => [image.src, image])).values()];
      figures[number] = {
        number,
        src: parts[0]?.src || "",
        images: parts,
        image_segment_id: parts[0]?.segment_id || "",
        image_segment_ids: [...new Set(parts.map(image => image.segment_id))],
        caption_segment_id: previous?.caption_segment_id || segment.id,
        caption_segment_ids: [...(previous?.caption_segment_ids || []), segment.id],
        caption: previous?.caption && previous.caption !== markdown ? `${previous.caption}\n${markdown}` : markdown,
        page: segment.page || previous?.page || null,
      };
      pendingImages = [];
    } else if (!images.length && String(markdown).trim()) {
      pendingImages = [];
    }
  }
  return figures;
}

function mergeFigureFallbacks(figures, fallbacks) {
  const result = { ...(figures || {}) };
  for (const [number, fallback] of Object.entries(fallbacks || {})) {
    if (!fallback?.src) continue;
    const existing = result[number] || { number };
    if (existing.src && !fallback.replace_existing) continue;
    result[number] = {
      ...existing,
      number: existing.number || fallback.number || number,
      src: assetUrlForPaper(state.currentPaperId, fallback.src),
      images: [{ src: assetUrlForPaper(state.currentPaperId, fallback.src), segment_id: existing.image_segment_id || "" }],
      image_segment_id: existing.image_segment_id || "",
      caption_segment_id: existing.caption_segment_id || fallback.caption_segment_id || "",
      caption: existing.caption || fallback.caption || "",
      fallback: fallback.fallback || "pdf-page",
      page: fallback.page || "",
    };
  }
  return result;
}

function segmentIsTable(segment = {}) {
  const text = segment.markdown || "";
  return isHtmlTable(text) || segment.kind === "table" || text.includes("\n|");
}

function segmentIsImage(segment = {}) {
  return Boolean(markdownImageInfo(segment.markdown || ""));
}

function figureEntryFromIndexedFigure(figure) {
  const segmentId = figure.image_segment_id || figure.caption_segment_id || "";
  if (!segmentId) return null;
  return {
    kind: "figure",
    key: `figure-${figure.number}-${segmentId}`,
    segment_id: segmentId,
    image_segment_id: figure.image_segment_id || "",
    caption_segment_id: figure.caption_segment_id || "",
    title: `Figure ${figure.number}`,
    caption: figure.caption || "",
    src: figure.src || "",
    image_segment_ids: figure.image_segment_ids || [],
    caption_segment_ids: figure.caption_segment_ids || [],
    part_count: figure.images?.length || 0,
  };
}

function paperMapTableTitle(segment, fallbackIndex) {
  const text = displayText(segment?.markdown || "").replace(/\s+/g, " ").trim();
  const match = text.match(/\btable\s*([0-9]+[a-z]?)/i);
  return match ? `Table ${match[1]}` : `Table ${fallbackIndex}`;
}

function paperMapMediaEntries() {
  const entries = [];
  const seenSegments = new Set();
  const figures = Object.values(state.figures || {}).map(figureEntryFromIndexedFigure).filter(Boolean);
  figures.sort((left, right) => segmentIdNumber(left.segment_id) - segmentIdNumber(right.segment_id));
  for (const figure of figures) {
    entries.push(figure);
    if (figure.image_segment_id) seenSegments.add(figure.image_segment_id);
    if (figure.caption_segment_id) seenSegments.add(figure.caption_segment_id);
    for (const id of figure.image_segment_ids) seenSegments.add(id);
    for (const id of figure.caption_segment_ids) seenSegments.add(id);
  }
  let tableIndex = 1;
  for (const segment of state.payload?.segments || []) {
    if (!segment?.id) continue;
    if (segmentIsTable(segment)) {
      entries.push({
        kind: "table",
        key: `table-${segment.id}`,
        segment_id: segment.id,
        title: paperMapTableTitle(segment, tableIndex),
        caption: segment.markdown || "",
      });
      tableIndex += 1;
      continue;
    }
    if (segmentIsImage(segment) && !seenSegments.has(segment.id)) {
      const image = markdownImageInfo(segment.markdown || "");
      entries.push({
        kind: "figure",
        key: `image-${segment.id}`,
        segment_id: segment.id,
        title: "Figure",
        caption: segment.markdown || "",
        src: assetUrlForPaper(state.currentPaperId, image?.src || ""),
      });
    }
  }
  return entries.sort((left, right) => segmentIdNumber(left.segment_id) - segmentIdNumber(right.segment_id));
}

const presentationPaperGroups = [
  { key: "paper-motivation", label: "Motivation", hint: "论文为什么提出这个问题", keywords: ["motivation", "problem", "challenge", "background", "introduction", "need", "问题", "动机", "背景", "挑战", "为什么"] },
  { key: "paper-related", label: "Related Works", hint: "论文如何定位相关工作", keywords: ["related", "prior", "literature", "previous", "baseline", "相关", "前人", "既有", "文献"] },
  { key: "paper-method", label: "Method / System", hint: "方法、系统、框架和设计细节", keywords: ["method", "system", "design", "framework", "feature", "interface", "implementation", "approach", "workflow", "方法", "系统", "设计", "框架", "流程"] },
  { key: "paper-evaluation", label: "Evaluation / Findings", hint: "研究设计、实验结果和发现", keywords: ["evaluation", "study", "participant", "result", "finding", "analysis", "experiment", "user study", "用户研究", "实验", "结果", "发现", "分析"] },
  { key: "paper-discussion", label: "Discussion / Limitations", hint: "讨论、启示、局限和未来工作", keywords: ["discussion", "implication", "limitation", "future", "conclusion", "takeaway", "讨论", "启示", "局限", "未来", "结论"] },
  { key: "paper-other", label: "Other Evidence", hint: "其他值得汇报的论文信息", keywords: [] },
];

const presentationSensemakingGroups = [
  { key: "sensemaking-gap", label: "GAP", hint: "研究空白、批评、局限、风险和机会", keywords: ["gap", "missing", "lack", "underexplored", "opportunity", "future work", "critique", "weak", "concern", "problematic", "limitation", "threat", "缺口", "空白", "没有处理", "未解决", "机会", "批评", "不足", "问题", "质疑", "风险", "局限"] },
  { key: "sensemaking-borrow", label: "What We Can Borrow", hint: "可以借鉴的方法、概念、设计或论证", keywords: ["borrow", "adapt", "use", "inspire", "reference", "lesson", "借鉴", "可以借", "可借", "参考", "迁移", "启发"] },
  { key: "sensemaking-angle", label: "Our Paper Angle", hint: "可以转化到我们论文里的叙事角度", keywords: ["our paper", "our work", "angle", "framing", "claim", "motivation", "related work", "我们", "我们的", "叙事", "主张", "角度", "写作"] },
  { key: "sensemaking-question", label: "Open Questions", hint: "后续要问自己或组会讨论的问题", keywords: ["question", "why", "how", "whether", "what if", "疑问", "问题", "为什么", "如何", "是否", "？", "?"] },
  { key: "sensemaking-phrase", label: "Useful Phrases", hint: "可以复用的表达、句子和关键词", keywords: ["phrase", "wording", "sentence", "quote", "term", "language", "表达", "句子", "说法", "术语", "金句", "quote摘录"] },
];

const presentationGroups = presentationPaperGroups;

function segmentForId(segmentId) {
  return state.payload?.segments?.find(segment => segment.id === segmentId) || null;
}

function presentationTextForCore(item) {
  return [item.label, item.summary, item.anchor, item.segment_id, item.id].filter(Boolean).join(" ");
}

function presentationTextForNote(note) {
  const segment = segmentForId(note.segment_id);
  return [note.note, note.quote, ...(note.tags || []), ...(segment?.section_path || [])].filter(Boolean).join(" ");
}

function hasChineseText(text) {
  return /[\u4e00-\u9fff]/.test(String(text || ""));
}

function compactText(text, maxLength = 90) {
  const clean = displayText(text).replace(/\s+/g, " ");
  return clean.length > maxLength ? `${clean.slice(0, maxLength).trim()}...` : clean;
}

function chineseCoreSummary(title, rawText = "") {
  const titleText = displayText(title);
  const raw = displayText(rawText);
  const lowered = `${titleText} ${raw}`.toLowerCase();
  if (hasChineseText(raw) && raw.length <= 180 && /^(本节|摘要|论文|这篇|核心|相关|方法|结果|讨论|贡献|RQ|研究问题)/.test(raw)) return raw;
  if (lowered.includes("abstract")) return "本节概括论文的问题、方法和主要贡献，适合作为汇报开场的总览。";
  if (/introduction|background|motivation|problem/.test(lowered)) return "本节交代研究动机、核心问题和本文要解决的缺口。";
  if (lowered.includes("related")) return "本节梳理相关工作，并定位本文相对既有研究的差异。";
  if (/method|system|design|framework|approach|implementation|prototype|interface/.test(lowered)) return "本节说明方法或系统设计，包括关键组件、流程和设计取舍。";
  if (/study|evaluation|experiment|participant|procedure/.test(lowered)) return "本节说明研究设计、参与者、任务流程和评价方式。";
  if (/result|finding|analysis/.test(lowered)) return "本节总结主要发现，并说明这些证据如何支撑论文主张。";
  if (/discussion|implication|limitation|future|conclusion/.test(lowered)) return "本节提炼讨论、设计启示、适用边界和未来工作。";
  if (hasChineseText(raw)) return `本节围绕“${compactText(raw.replace(/\s+/g, ""), 54)}”展开，可作为该部分的汇报节点。`;
  return "本节是论文论证链条中的一个主干节点，可用于承接前后文并组织相关笔记。";
}

function presentationGroupFor(text) {
  const lowered = String(text || "").toLowerCase();
  return presentationGroups.find(group => group.key !== "other" && group.keywords.some(keyword => lowered.includes(keyword.toLowerCase()))) || presentationGroups[presentationGroups.length - 1];
}

function normalizePresentationFlowItem(item, index) {
  const id = String(item?.id || `flow-${index + 1}`).trim() || `flow-${index + 1}`;
  const anchors = Array.isArray(item?.anchors) ? item.anchors.map(anchor => String(anchor).trim()).filter(Boolean) : [];
  const anchorRanges = Array.isArray(item?.anchor_ranges) ? item.anchor_ranges
    .filter(range => Array.isArray(range) && range.length >= 2)
    .map(range => [String(range[0]).trim(), String(range[1]).trim()])
    .filter(range => range[0] && range[1]) : [];
  const keywords = Array.isArray(item?.keywords) ? item.keywords.map(keyword => String(keyword).trim()).filter(Boolean) : [];
  const rawCore = String(item?.core || item?.summary || item?.label || "").trim();
  const title = String(item?.title || `Flow ${index + 1}`).trim() || `Flow ${index + 1}`;
  return {
    id,
    title,
    core: chineseCoreSummary(title, rawCore),
    raw_core: rawCore,
    anchors,
    anchor_ranges: anchorRanges,
    keywords,
  };
}

function fallbackPresentationFlow(outline) {
  const generated = [];
  const headings = (outline.outline || []).filter(item => item.id && item.title && Number(item.level || 2) <= 3 && !shouldSkipPresentationHeading(item.title)).slice(0, 7);
  for (let index = 0; index < headings.length; index += 1) {
    const heading = headings[index];
    const start = segmentIdNumber(heading.id);
    const nextStart = segmentIdNumber(headings[index + 1]?.id || "");
    const end = Number.isFinite(nextStart) && nextStart > start ? nextStart - 1 : start + 8;
    const content = (state.payload?.segments || []).find(segment => {
      const number = segmentIdNumber(segment.id);
      return number > start && number <= end && segment.kind !== "heading" && displayText(segment.markdown || segment.translation || "");
    });
    const rawCore = displayText(content?.translation || content?.markdown || heading.title).slice(0, 260);
    generated.push({
      id: `flow-${index + 1}`,
      title: heading.title,
      core: chineseCoreSummary(heading.title, rawCore),
      raw_core: rawCore,
      anchors: [heading.id, content?.id].filter(Boolean),
      anchor_ranges: [[heading.id, `p-${String(Math.max(start, end)).padStart(4, "0")}`]],
      keywords: textTokens(`${heading.title} ${content?.markdown || ""}`).slice(0, 8),
    });
  }
  if (generated.length) return generated;
  for (const item of outline.core_locations || []) {
    const group = presentationGroupFor(presentationTextForCore(item));
    if (generated.some(flow => flow.id === group.key)) continue;
    generated.push({ id: group.key, title: group.label, core: item.summary || item.label || group.hint, anchors: [item.anchor || item.segment_id || item.id].filter(Boolean), anchor_ranges: [], keywords: group.keywords });
  }
  const skimLines = markdownToPlainLines(state.payload?.skim_summary || state.payload?.skim_analysis?.skim_summary || "", 8);
  for (const line of skimLines) {
    const group = presentationGroupFor(line);
    const existing = generated.find(flow => flow.id === group.key);
    if (existing) {
      if (!existing.core) existing.core = line;
      continue;
    }
    generated.push({ id: group.key, title: group.label, core: line, anchors: ["skim-summary"], anchor_ranges: [], keywords: group.keywords });
  }
  if (!generated.length) {
    return presentationGroups.map(group => ({ id: group.key, title: group.label, core: group.hint, anchors: [], anchor_ranges: [], keywords: group.keywords }));
  }
  return generated;
}

function shouldSkipPresentationHeading(title) {
  const clean = String(title || "").replace(/\s+/g, " ").trim().toLowerCase();
  const paperTitle = String(state.payload?.metadata?.title || "").replace(/\s+/g, " ").trim().toLowerCase();
  if (!clean) return true;
  if (paperTitle && (clean === paperTitle || clean.includes(paperTitle) || paperTitle.includes(clean))) return true;
  return ["ccs concepts", "keywords", "author keywords", "acm reference format", "reference format", "references", "acknowledg", "appendix"].some(marker => clean.includes(marker));
}

function presentationFlow(outline) {
  const explicit = outline.presentation_flow?.length
    ? outline.presentation_flow
    : state.payload?.skim_analysis?.presentation_flow || [];
  const source = explicit.length ? explicit : fallbackPresentationFlow(outline);
  return source.map(normalizePresentationFlowItem);
}

function segmentIdNumber(segmentId) {
  const match = String(segmentId || "").match(/(\d+)$/);
  return match ? Number(match[1]) : Number.NaN;
}

function segmentIdInRange(segmentId, startId, endId) {
  const number = segmentIdNumber(segmentId);
  const start = segmentIdNumber(startId);
  const end = segmentIdNumber(endId);
  if (!Number.isFinite(number) || !Number.isFinite(start) || !Number.isFinite(end)) return false;
  return number >= Math.min(start, end) && number <= Math.max(start, end);
}

function itemAnchorId(item) {
  return item.anchor || item.segment_id || item.id || "";
}

function textTokens(text) {
  const raw = String(text || "").toLowerCase();
  const tokens = raw.match(/[a-z][a-z-]{3,}|[\u4e00-\u9fff]{2,}/g) || [];
  const stop = new Set(["paper", "study", "system", "systems", "method", "results", "using", "with", "this", "that", "from", "论文", "研究", "系统", "方法"]);
  return [...new Set(tokens.filter(token => !stop.has(token)))];
}

function keywordScore(text, flow) {
  const noteTokens = new Set(textTokens(text));
  const flowTokens = textTokens([flow.title, flow.core, ...(flow.keywords || [])].join(" "));
  return flowTokens.reduce((score, token) => score + (noteTokens.has(token) ? 1 : 0), 0);
}

function flowForAnchor(flows, segmentId) {
  if (!segmentId) return null;
  return flows.find(flow => flow.anchors?.includes(segmentId))
    || flows.find(flow => (flow.anchor_ranges || []).some(([start, end]) => segmentIdInRange(segmentId, start, end)))
    || null;
}

function flowForNote(flows, note) {
  if (note.presentation_flow_id) {
    const manual = flows.find(flow => flow.id === note.presentation_flow_id);
    if (manual) return manual;
  }
  const anchored = flowForAnchor(flows, note.segment_id);
  if (anchored) return anchored;
  const text = presentationTextForNote(note);
  const scored = flows.map(flow => ({ flow, score: keywordScore(text, flow) })).sort((a, b) => b.score - a.score);
  return scored[0]?.score > 0 ? scored[0].flow : flows[flows.length - 1] || null;
}

function flowForCore(flows, item) {
  const anchored = flowForAnchor(flows, itemAnchorId(item));
  if (anchored) return anchored;
  const text = presentationTextForCore(item);
  const scored = flows.map(flow => ({ flow, score: keywordScore(text, flow) })).sort((a, b) => b.score - a.score);
  return scored[0]?.score > 0 ? scored[0].flow : null;
}

const legacyPresentationGroupMap = {
  motivation: "paper-motivation",
  method: "paper-method",
  evaluation: "paper-evaluation",
  discussion: "paper-discussion",
  other: "paper-other",
};

function allPresentationReportGroups() {
  return [...presentationPaperGroups, ...presentationSensemakingGroups];
}

function presentationReportGroupByKey(key) {
  const groups = allPresentationReportGroups();
  return groups.find(group => group.key === key) || groups.find(group => group.key === legacyPresentationGroupMap[key]) || null;
}

function reportCategoryForGroupKey(groupKey) {
  return String(groupKey || "").startsWith("sensemaking-") ? "sensemaking" : "paper";
}

function reportGroupForText(text, groups) {
  const lowered = String(text || "").toLowerCase();
  return groups.find(group => !group.key.endsWith("-other") && group.keywords.some(keyword => lowered.includes(keyword.toLowerCase())))
    || groups.find(group => group.key.endsWith("-other"))
    || groups[0];
}

function manualReportGroupKey(item, groups = allPresentationReportGroups()) {
  const value = String(item?.presentation_flow_id || "").trim();
  if (!value) return "";
  if (groups.some(group => group.key === value)) return value;
  const mapped = legacyPresentationGroupMap[value];
  return mapped && groups.some(group => group.key === mapped) ? mapped : "";
}

function reportItemText(item) {
  return [item.title, item.quote, item.note, item.meta, ...(item.tags || [])].filter(Boolean).join(" ");
}

function paperAnnotationReportTarget(annotation) {
  const manual = manualReportGroupKey(annotation, presentationPaperGroups);
  if (manual) return { category: reportCategoryForGroupKey(manual), group: manual };
  const evidenceGroup = reportGroupForText(presentationTextForNote(annotation), presentationPaperGroups);
  return { category: "paper", group: evidenceGroup.key };
}

function reportMoveGroupsForItem(item) {
  return item?.source === "paper-note" ? presentationPaperGroups : allPresentationReportGroups();
}

function thinkingAnnotationReportTarget(annotation, block) {
  const manual = manualReportGroupKey(annotation);
  if (manual) return { category: reportCategoryForGroupKey(manual), group: manual };
  const group = reportGroupForText([annotation.note, annotation.quote, block?.title, ...(annotationTags(annotation) || [])].filter(Boolean).join(" "), presentationSensemakingGroups);
  return { category: "sensemaking", group: group.key };
}

function thinkingBlockDisplayTitle(blockId, block = null) {
  if (blockId === paperBriefBlockId) return "Paper Brief";
  return block?.title || block?.prompt || "AI output";
}

function buildPresentationReportItems(outline) {
  const items = [];
  if (!state.payload || !state.currentPaperId) return items;
  for (const annotation of state.annotations || []) {
    if (annotationGroupId(annotation) && annotationGroupIndex(annotation) > 0) continue;
    const target = paperAnnotationReportTarget(annotation);
    items.push({
      id: `report-paper-note-${annotation.id}`,
      category: target.category,
      group: target.group,
      source: "paper-note",
      sourceLabel: annotation.note ? "Original Note" : "Original Highlight",
      title: `${annotationKindLabel(annotation)}批注`,
      quote: annotation.quote || "",
      note: annotation.note || "",
      tags: annotationTags(annotation),
      meta: [annotationKindLabel(annotation), annotation.segment_id].filter(Boolean).join(" · "),
      mediaSrc: annotationMediaSrc(annotation, state.currentPaperId),
      annotationId: annotation.id,
      paperId: state.currentPaperId,
      color: annotation.color || "yellow",
      raw: annotation,
    });
  }
  for (const block of state.thinking?.blocks || []) {
    const blockAnnotations = (state.thinking.annotations || []).filter(annotation => annotation.block_id === block.id);
    for (const annotation of blockAnnotations) {
      const target = thinkingAnnotationReportTarget(annotation, block);
      items.push({
        id: `report-thinking-note-${annotation.id}`,
        category: target.category,
        group: target.group,
        source: "thinking-note",
        sourceLabel: annotation.note ? "AI Output Note" : "AI Output Highlight",
        title: block.title || "AI output",
        quote: annotation.quote || "",
        note: annotation.note || "",
        tags: annotationTags(annotation),
        meta: block.created_at ? `Sensemaking · ${new Date(block.created_at).toLocaleString()}` : "Sensemaking",
        annotationId: annotation.id,
        blockId: block.id,
        color: annotation.color || "yellow",
        raw: annotation,
      });
    }
  }
  const paperBriefAnnotations = (state.thinking?.annotations || []).filter(annotation => annotation.block_id === paperBriefBlockId);
  const paperBriefBlock = thinkingBlockById(paperBriefBlockId);
  for (const annotation of paperBriefAnnotations) {
    const target = thinkingAnnotationReportTarget(annotation, paperBriefBlock);
    items.push({
      id: `report-thinking-note-${annotation.id}`,
      category: target.category,
      group: target.group,
      source: "thinking-note",
      sourceLabel: annotation.note ? "Paper Brief Note" : "Paper Brief Highlight",
      title: "Paper Brief",
      quote: annotation.quote || "",
      note: annotation.note || "",
      tags: annotationTags(annotation),
      meta: "Paper Brief",
      annotationId: annotation.id,
      blockId: paperBriefBlockId,
      color: annotation.color || "yellow",
      raw: annotation,
    });
  }
  for (const thought of state.thinking?.report_thoughts || []) {
    items.push({
      id: `report-free-thought-${thought.id}`,
      category: "sensemaking",
      group: presentationSensemakingGroups.some(group => group.key === thought.group) ? thought.group : "sensemaking-gap",
      source: "free-thought",
      note: thought.note,
      tags: [],
      meta: thought.updated_at ? `Added · ${new Date(thought.updated_at).toLocaleString()}` : "Added thought",
      thoughtId: thought.id,
      color: "green",
    });
  }
  return items;
}

function buildPresentationReport(outline) {
  const categories = [
    { key: "paper", label: "Paper Evidence / 原文信息", hint: "来自原文、翻译、图片和表格的高亮与笔记", groups: presentationPaperGroups },
    { key: "sensemaking", label: "My Sensemaking / 我的思考", hint: "AI output、高亮、你的 note 和读完后的研究想法", groups: presentationSensemakingGroups },
  ];
  const items = buildPresentationReportItems(outline);
  state.presentationReportItems = items;
  const buckets = Object.fromEntries(allPresentationReportGroups().map(group => [group.key, []]));
  for (const item of items) {
    const group = presentationReportGroupByKey(item.group) || presentationPaperGroups[presentationPaperGroups.length - 1];
    buckets[group.key].push(item);
  }
  return { categories, buckets, items };
}

function ensurePresentationMoveMenu() {
  let menu = qs("#presentationMoveMenu");
  if (menu) return menu;
  menu = document.createElement("div");
  menu.id = "presentationMoveMenu";
  menu.className = "presentation-move-menu";
  menu.setAttribute("role", "menu");
  menu.setAttribute("aria-hidden", "true");
  document.body.appendChild(menu);
  return menu;
}

function closePresentationMoveMenu() {
  const menu = qs("#presentationMoveMenu");
  if (!menu) return;
  menu.classList.remove("open");
  menu.setAttribute("aria-hidden", "true");
  menu.innerHTML = "";
  state.presentationMenu = null;
}

function openPresentationMoveMenu(item, groups, x, y) {
  if (!item?.raw || !item.annotationId) return;
  const menu = ensurePresentationMoveMenu();
  const selected = manualReportGroupKey(item.raw);
  menu.innerHTML = `
    <div class="presentation-move-menu-title">Move card to</div>
    <button class="presentation-move-option ${selected ? "" : "active"}" data-move-report-group="" role="menuitem">Auto</button>
    ${groups.map(group => `<button class="presentation-move-option ${group.key === selected ? "active" : ""}" data-move-report-group="${escapeHtml(group.key)}" role="menuitem"><span>${escapeHtml(group.label)}</span><small>${escapeHtml(group.hint || "")}</small></button>`).join("")}`;
  menu.classList.add("open");
  menu.setAttribute("aria-hidden", "false");
  state.presentationMenu = { source: item.source, annotationId: item.annotationId, paperId: item.paperId || state.currentPaperId };
  const rect = menu.getBoundingClientRect();
  const left = Math.max(8, Math.min(x, window.innerWidth - rect.width - 8));
  const top = Math.max(8, Math.min(y, window.innerHeight - rect.height - 8));
  menu.style.left = `${left}px`;
  menu.style.top = `${top}px`;
  qsa("#presentationMoveMenu [data-move-report-group]").forEach(button => button.addEventListener("click", async event => {
    event.stopPropagation();
    const context = state.presentationMenu;
    const groupKey = button.dataset.moveReportGroup || "";
    closePresentationMoveMenu();
    if (!context) return;
    await updatePresentationGroupOverride(context, groupKey);
  }));
}

function presentationReportItemHtml(item) {
  const color = item.color || "yellow";
  const quote = displayText(item.quote || "");
  const noteText = displayText(item.note || "");
  const tags = item.tags || [];
  const movable = Boolean(item.raw && item.annotationId);
  const freeThought = item.source === "free-thought";
  const sourceLabel = item.source === "thinking-note"
    ? item.blockId === paperBriefBlockId ? "Open Paper Brief" : "Open AI output"
    : item.source === "paper-note"
      ? `Source ${item.raw?.segment_id || item.raw?.segmentId || "passage"}`
      : "";
  return `
    <div class="presentation-note-item presentation-report-card" data-presentation-report-row="${escapeHtml(item.id || "")}">
      <div class="presentation-note-main">
        <span class="presentation-note-color hl-${escapeHtml(color)}"></span>
        <span class="presentation-note-body">
          ${noteText ? `<span class="presentation-note-text presentation-note-primary">${escapeHtml(noteText)}</span>` : freeThought ? "" : '<span class="muted small-text">Highlight only</span>'}
          ${item.mediaSrc ? `<span class="presentation-media-thumb"><img src="${escapeHtml(item.mediaSrc)}" alt="${escapeHtml(quote || "Media note")}"></span>` : ""}
          ${quote ? `<span class="presentation-note-quote">${escapeHtml(quote)}</span>` : ""}
          ${tags.length ? `<span class="presentation-report-tags">${tags.map(tag => `<span>${escapeHtml(tag)}</span>`).join("")}</span>` : ""}
          ${item.meta && !freeThought ? `<span class="presentation-note-meta">${escapeHtml(item.meta)}</span>` : ""}
          ${sourceLabel ? `<button class="presentation-source-link" data-presentation-report-source="${escapeHtml(item.id || "")}" type="button">${escapeHtml(sourceLabel)}</button>` : ""}
        </span>
      </div>
      ${movable ? `<button class="presentation-note-menu-button" data-presentation-report-menu="${escapeHtml(item.id || "")}" aria-label="Move card">...</button>` : ""}
      ${freeThought ? `<button class="presentation-note-menu-button" data-delete-report-thought="${escapeHtml(item.thoughtId || "")}" aria-label="Delete thought">x</button>` : ""}
    </div>`;
}

function defaultTakeawayDoc() {
  return { version: 1, blocks: [], updated_at: "" };
}

function normalizeTakeawayBlock(block = {}, index = 0) {
  const type = ["heading", "bullet"].includes(block.type) ? block.type : "bullet";
  const indent = Math.max(0, Math.min(6, Number.parseInt(block.indent ?? 0, 10) || 0));
  const level = Math.max(1, Math.min(3, Number.parseInt(block.level ?? (type === "heading" ? 1 : 2), 10) || 1));
  const tags = Array.isArray(block.tags) ? block.tags.map(tag => String(tag).trim()).filter(Boolean) : [];
  const sourceRefs = Array.isArray(block.source_refs) ? block.source_refs.filter(item => item && typeof item === "object").map(item => ({
    paper_id: String(item.paper_id || ""),
    annotation_id: String(item.annotation_id || ""),
    segment_id: String(item.segment_id || ""),
    block_id: String(item.block_id || ""),
    item_id: String(item.item_id || ""),
    source: String(item.source || ""),
  })) : [];
  return {
    id: String(block.id || `td-${Date.now().toString(36)}-${index}`),
    type,
    text: String(block.text || ""),
    indent,
    level,
    source_item_id: String(block.source_item_id || ""),
    source: String(block.source || ""),
    source_label: String(block.source_label || ""),
    quote: String(block.quote || ""),
    note: String(block.note || ""),
    meta: String(block.meta || ""),
    color: String(block.color || ""),
    tags,
    source_refs: sourceRefs,
    locked: Boolean(block.locked),
    created_at: block.created_at || new Date().toISOString(),
    updated_at: block.updated_at || new Date().toISOString(),
  };
}

function normalizeTakeawayDoc(doc = {}) {
  const blocks = Array.isArray(doc.blocks) ? doc.blocks.map(normalizeTakeawayBlock) : [];
  return { version: 1, blocks, updated_at: String(doc.updated_at || "") };
}

function reportItemSourceLabel(item) {
  if (item.source === "thinking-note") return item.blockId === paperBriefBlockId ? "Paper Brief" : "AI output";
  if (item.source === "paper-note") return `Source ${item.raw?.segment_id || item.raw?.segmentId || "passage"}`;
  return item.sourceLabel || "Source";
}

function sourceRefsForReportItem(item) {
  if (!item) return [];
  return [{
    paper_id: item.paperId || state.currentPaperId || "",
    annotation_id: item.annotationId || "",
    segment_id: item.raw?.segment_id || item.raw?.segmentId || "",
    block_id: item.blockId || "",
    item_id: item.id || "",
    source: item.source || "",
  }];
}

function takeawayBlockFromReportItem(item, index, indent = 1) {
  const noteText = displayText(item.note || "");
  const quote = displayText(item.quote || "");
  const text = noteText || quote || item.title || `Insight ${index + 1}`;
  return normalizeTakeawayBlock({
    id: `td-src-${String(item.id || index).replace(/[^a-z0-9_-]/gi, "-")}`,
    type: "bullet",
    text,
    indent,
    source_item_id: item.id || "",
    source: item.source || "",
    source_label: reportItemSourceLabel(item),
    quote: noteText && quote ? quote : "",
    note: noteText,
    meta: item.meta || "",
    color: item.color || "yellow",
    tags: item.tags || [],
    source_refs: sourceRefsForReportItem(item),
  }, index);
}

function seedTakeawayDocFromReport(report) {
  const now = new Date().toISOString();
  const blocks = [];
  for (const category of report.categories || []) {
    const categoryGroups = category.groups || [];
    const hasCategoryItems = categoryGroups.some(group => (report.buckets[group.key] || []).length);
    if (!hasCategoryItems && category.key !== "sensemaking") continue;
    blocks.push(normalizeTakeawayBlock({ id: `td-heading-${category.key}`, type: "heading", text: category.label, indent: 0, level: 1, created_at: now, updated_at: now }, blocks.length));
    for (const group of categoryGroups) {
      const groupItems = report.buckets[group.key] || [];
      if (!groupItems.length && category.key !== "sensemaking") continue;
      blocks.push(normalizeTakeawayBlock({ id: `td-heading-${group.key}`, type: "heading", text: group.label, indent: 1, level: 2, created_at: now, updated_at: now }, blocks.length));
      groupItems.forEach(item => blocks.push(takeawayBlockFromReportItem(item, blocks.length, 2)));
    }
  }
  if (!blocks.length) {
    blocks.push(normalizeTakeawayBlock({ id: "td-heading-notes", type: "heading", text: "Takeaway Report", indent: 0, level: 1 }, 0));
    blocks.push(normalizeTakeawayBlock({ id: "td-empty-bullet", type: "bullet", text: "", indent: 1 }, 1));
  }
  return { version: 1, blocks, updated_at: now };
}

function markTakeawayAutoChanged() {
  state.takeawayDocVersion = Number(state.takeawayDocVersion || 0) + 1;
  state.takeawayAutoSaveNeeded = true;
  if (state.takeawayDoc) state.takeawayDoc.updated_at = new Date().toISOString();
}

function takeawayBlockSourceIds(block) {
  const ids = new Set();
  const direct = String(block?.source_item_id || "").trim();
  if (direct) ids.add(direct);
  for (const ref of block?.source_refs || []) {
    const itemId = String(ref?.item_id || "").trim();
    if (itemId) ids.add(itemId);
  }
  return ids;
}

function takeawayExistingSourceIds(blocks) {
  const ids = new Set();
  for (const block of blocks || []) {
    for (const id of takeawayBlockSourceIds(block)) ids.add(id);
  }
  return ids;
}

function findTakeawayHeadingIndex(blocks, id, text) {
  const normalizedText = String(text || "").replace(/\s+/g, " ").trim().toLowerCase();
  let index = blocks.findIndex(block => block.type === "heading" && block.id === id);
  if (index >= 0) return index;
  return blocks.findIndex(block => block.type === "heading" && String(block.text || "").replace(/\s+/g, " ").trim().toLowerCase() === normalizedText);
}

function insertTakeawayHeading(blocks, id, text, indent, level, afterIndex = -1) {
  const existing = findTakeawayHeadingIndex(blocks, id, text);
  if (existing >= 0) return existing;
  const block = normalizeTakeawayBlock({ id, type: "heading", text, indent, level, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }, blocks.length);
  const index = afterIndex >= 0 ? Math.min(blocks.length, afterIndex + 1) : blocks.length;
  blocks.splice(index, 0, block);
  return index;
}

function takeawayGroupEndIndex(blocks, headingIndex) {
  if (headingIndex < 0) return blocks.length;
  const baseIndent = Number(blocks[headingIndex]?.indent || 0);
  let index = headingIndex + 1;
  while (index < blocks.length) {
    const block = blocks[index];
    if (block.type === "heading" && Number(block.indent || 0) <= baseIndent) break;
    index += 1;
  }
  return index;
}

function syncTakeawayDocFromReport(report) {
  state.takeawayDoc = normalizeTakeawayDoc(state.takeawayDoc || {});
  const blocks = state.takeawayDoc.blocks;
  const existingSourceIds = takeawayExistingSourceIds(blocks);
  let added = 0;
  for (const category of report.categories || []) {
    const groups = category.groups || [];
    if (!groups.length) continue;
    const hasItems = groups.some(group => (report.buckets[group.key] || []).some(item => item?.id && !existingSourceIds.has(item.id)));
    if (!hasItems) continue;
    const categoryIndex = insertTakeawayHeading(blocks, `td-heading-${category.key}`, category.label, 0, 1);
    let lastHeadingIndex = categoryIndex;
    for (const group of groups) {
      const missingItems = (report.buckets[group.key] || []).filter(item => item?.id && !existingSourceIds.has(item.id));
      if (!missingItems.length) continue;
      const groupIndex = insertTakeawayHeading(blocks, `td-heading-${group.key}`, group.label, 1, 2, lastHeadingIndex);
      lastHeadingIndex = groupIndex;
      let insertIndex = takeawayGroupEndIndex(blocks, groupIndex);
      const newBlocks = missingItems.map(item => {
        existingSourceIds.add(item.id);
        added += 1;
        return takeawayBlockFromReportItem(item, blocks.length + added, 2);
      });
      blocks.splice(insertIndex, 0, ...newBlocks);
      lastHeadingIndex = insertIndex + newBlocks.length - 1;
    }
  }
  if (added) markTakeawayAutoChanged();
  return added;
}

function ensureTakeawayDoc(report) {
  state.takeawayDoc = normalizeTakeawayDoc(state.takeawayDoc || {});
  if (!state.takeawayDoc.blocks.length) {
    state.takeawayDoc = seedTakeawayDocFromReport(report);
    markTakeawayAutoChanged();
  } else if (!state.takeawayHistoryRestoring) {
    syncTakeawayDocFromReport(report);
  }
  return state.takeawayDoc;
}

function generatedTakeawayHeadingTexts() {
  return new Set([
    "Paper Evidence / 原文信息",
    "My Sensemaking / 我的思考",
    "Takeaway Report",
    ...allPresentationReportGroups().map(group => group.label),
  ].map(text => String(text || "").replace(/\s+/g, " ").trim().toLowerCase()));
}

function isGeneratedTakeawayHeading(block) {
  if (block?.type !== "heading") return false;
  const id = String(block.id || "");
  const text = String(block.text || "").replace(/\s+/g, " ").trim().toLowerCase();
  return id === "td-heading-paper"
    || id === "td-heading-sensemaking"
    || id.startsWith("td-heading-paper-")
    || id.startsWith("td-heading-sensemaking-")
    || generatedTakeawayHeadingTexts().has(text);
}

function takeawayBlockTextForArrange(block) {
  return [block?.text, block?.note, block?.quote, block?.meta, ...(block?.tags || [])].filter(Boolean).join(" ");
}

function takeawayBlockSegmentId(block) {
  const ref = (block?.source_refs || []).find(item => item.segment_id);
  if (ref?.segment_id) return ref.segment_id;
  const text = [block?.source_label, block?.meta].filter(Boolean).join(" ");
  const match = text.match(/\bp-\d+\b/i);
  return match ? match[0] : "";
}

function takeawayBlockSourceKind(block) {
  const sourceValues = new Set([block?.source, ...(block?.source_refs || []).map(ref => ref.source)].map(value => String(value || "").trim()).filter(Boolean));
  if (sourceValues.has("thinking-note") || (block?.source_refs || []).some(ref => ref.block_id)) return "sensemaking";
  if (sourceValues.has("paper-note") || takeawayBlockSegmentId(block)) return "paper";
  return "";
}

function phraseScore(text, patterns) {
  const lowered = String(text || "").toLowerCase();
  return patterns.reduce((score, pattern) => score + (pattern.test(lowered) ? 1 : 0), 0);
}

function classifyTakeawayBlock(block) {
  const text = takeawayBlockTextForArrange(block);
  const sourceKind = takeawayBlockSourceKind(block);
  const reflectionScore = phraseScore(text, [
    /我的|我觉得|我认为|我们|我们的|咱们/,
    /参考|借鉴|启发|反思|差异|不同|对比/,
    /可以|应该|需要|能不能|是否|如何|尝试/,
    /调整|设计|改成|用于|落到|迁移|扩展/,
    /\b(i|my|our|we)\b|\bwe can\b|\bcould\b|\bshould\b|\bmaybe\b|\bidea\b|\bdifference\b|\btakeaway\b|\bimplication\b/,
  ]);
  const evidenceScore = phraseScore(text, [
    /\b(dg|rq|h)\s*\d+[a-z]?\b/i,
    /理论依据|定义|概念|机制|方法|模型|系统|实验|结果|发现|数据|样本|参与者|基线|指标|设计目标|设计原则/,
    /\bdesign\s+(goal|guideline|principle)\b|\bmethod\b|\bresult\b|\bfinding\b|\bexperiment\b|\bparticipant\b|\bbaseline\b|\bmetric\b/,
  ]);
  const compact = String(text || "").replace(/\s+/g, "").length <= 16;
  if (reflectionScore >= 2 && reflectionScore >= evidenceScore) return "sensemaking";
  if (sourceKind === "sensemaking") return reflectionScore || !evidenceScore ? "sensemaking" : "paper";
  if (sourceKind === "paper") return reflectionScore >= 2 && !evidenceScore ? "sensemaking" : "paper";
  if (evidenceScore > 0 || (compact && /^(dg|rq|h)\s*\d+/i.test(String(text || "").trim()))) return "paper";
  return "sensemaking";
}

function flowForTakeawayBlock(block, flows) {
  const segmentId = takeawayBlockSegmentId(block);
  return flowForAnchor(flows, segmentId)
    || flowForNote(flows, { segment_id: segmentId, note: block.text || block.note || "", quote: block.quote || "", tags: block.tags || [] })
    || null;
}

function cloneArrangedTakeawayBlock(block, patch, index) {
  return normalizeTakeawayBlock({ ...block, ...patch, updated_at: new Date().toISOString() }, index);
}

function normalizedTakeawayHeadingText(text) {
  return String(text || "").replace(/[#*_`]/g, "").replace(/\s+/g, " ").trim().toLowerCase();
}

function takeawayBlockIsLocked(block) {
  return Boolean(block?.locked);
}

function takeawayBlockSourceNumber(block) {
  const number = segmentIdNumber(takeawayBlockSegmentId(block));
  return Number.isFinite(number) ? number : Number.POSITIVE_INFINITY;
}

function takeawayBlockIsSourceLinked(block) {
  return Number.isFinite(segmentIdNumber(takeawayBlockSegmentId(block)));
}

function takeawayFlowHeadingIdCandidates(flow) {
  const id = String(flow?.id || "").trim();
  return id ? [`td-heading-${id}`, `td-arranged-flow-${id}`, `td-flow-${id}`] : [];
}

function findTakeawayHeadingForFlow(blocks, flow) {
  const candidates = new Set(takeawayFlowHeadingIdCandidates(flow));
  const title = normalizedTakeawayHeadingText(flow?.title || "");
  return blocks.findIndex(block => block?.type === "heading" && (candidates.has(block.id) || (title && normalizedTakeawayHeadingText(block.text) === title)));
}

function findTakeawayHeadingByText(blocks, text) {
  const target = normalizedTakeawayHeadingText(text);
  return blocks.findIndex(block => block?.type === "heading" && normalizedTakeawayHeadingText(block.text) === target);
}

function findTakeawayPaperRootIndex(blocks) {
  const byId = blocks.findIndex(block => block?.type === "heading" && block.id === "td-heading-paper");
  if (byId >= 0) return byId;
  return findTakeawayHeadingByText(blocks, "Paper Evidence / 原文信息");
}

function findTakeawaySensemakingRootIndex(blocks) {
  const byId = blocks.findIndex(block => block?.type === "heading" && block.id === "td-heading-sensemaking");
  if (byId >= 0) return byId;
  return findTakeawayHeadingByText(blocks, "My Sensemaking / 我的思考");
}

function insertIndexBeforeSensemakingOrEnd(blocks) {
  const sensemakingIndex = findTakeawaySensemakingRootIndex(blocks);
  return sensemakingIndex >= 0 ? sensemakingIndex : blocks.length;
}

function ensureTakeawaySourceHeading(blocks, flow, previousIndex = -1, summary = null) {
  let index = findTakeawayHeadingForFlow(blocks, flow);
  if (index >= 0) {
    if (summary) summary.reusedHeadings += 1;
    return index;
  }
  const paperRootIndex = findTakeawayPaperRootIndex(blocks);
  const parentIndent = paperRootIndex >= 0 ? Number(blocks[paperRootIndex]?.indent || 0) : -1;
  const heading = normalizeTakeawayBlock({
    id: `td-flow-${String(flow?.id || Date.now().toString(36)).replace(/[^a-z0-9_-]/gi, "-")}`,
    type: "heading",
    text: flow?.title || "Other Evidence / 其他原文信息",
    indent: Math.max(0, parentIndent + 1),
    level: Math.min(3, Math.max(1, parentIndent + 2)),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }, blocks.length);
  let insertIndex = insertIndexBeforeSensemakingOrEnd(blocks);
  if (previousIndex >= 0) insertIndex = takeawayGroupEndIndex(blocks, previousIndex);
  else if (paperRootIndex >= 0) insertIndex = takeawayGroupEndIndex(blocks, paperRootIndex);
  insertIndex = Math.max(0, Math.min(blocks.length, insertIndex));
  blocks.splice(insertIndex, 0, heading);
  if (summary) summary.createdHeadings += 1;
  return insertIndex;
}

function buildSourceOrderTakeawayDoc(outline = state.payload?.outline || {}) {
  const currentBlocks = normalizeTakeawayDoc(state.takeawayDoc || {}).blocks;
  const flows = presentationFlow(outline);
  const flowOrder = new Map(flows.map((flow, index) => [flow.id, index]));
  const summary = {
    movedCount: 0,
    untouchedCount: 0,
    lockedCount: 0,
    sourceOrderedCount: 0,
    reusedHeadings: 0,
    createdHeadings: 0,
    flowCount: 0,
  };
  const movableItems = [];
  const preservedBlocks = [];
  for (const [index, block] of currentBlocks.entries()) {
    if (takeawayBlockIsLocked(block)) {
      preservedBlocks.push(block);
      summary.lockedCount += 1;
      continue;
    }
    if (block.type !== "heading" && takeawayBlockIsSourceLinked(block)) {
      const flow = flowForTakeawayBlock(block, flows) || { id: "paper-other", title: "Other Evidence / 其他原文信息" };
      movableItems.push({ block, index, flow, segmentNumber: takeawayBlockSourceNumber(block) });
      continue;
    }
    preservedBlocks.push(block);
    summary.untouchedCount += 1;
  }
  movableItems.sort((left, right) => {
    const leftFlow = left.flow ? flowOrder.get(left.flow.id) ?? Number.POSITIVE_INFINITY : Number.POSITIVE_INFINITY;
    const rightFlow = right.flow ? flowOrder.get(right.flow.id) ?? Number.POSITIVE_INFINITY : Number.POSITIVE_INFINITY;
    return leftFlow - rightFlow || left.segmentNumber - right.segmentNumber || left.index - right.index;
  });
  const blocks = [...preservedBlocks];
  const groups = new Map();
  for (const item of movableItems) {
    const groupId = item.flow?.id || "paper-other";
    if (!groups.has(groupId)) groups.set(groupId, { flow: item.flow, items: [] });
    groups.get(groupId).items.push(item);
  }
  let previousHeadingIndex = -1;
  for (const group of groups.values()) {
    const headingIndex = ensureTakeawaySourceHeading(blocks, group.flow, previousHeadingIndex, summary);
    previousHeadingIndex = headingIndex;
    const heading = blocks[headingIndex];
    const childIndent = Math.min(6, Number(heading?.indent || 0) + 1);
    let insertIndex = takeawayGroupEndIndex(blocks, headingIndex);
    for (const item of group.items) {
      blocks.splice(insertIndex, 0, cloneArrangedTakeawayBlock(item.block, { indent: childIndent, level: 2 }, insertIndex));
      insertIndex += 1;
      summary.movedCount += 1;
      if (Number.isFinite(item.segmentNumber)) summary.sourceOrderedCount += 1;
    }
  }
  summary.flowCount = groups.size;
  return {
    doc: { version: 1, blocks, updated_at: new Date().toISOString() },
    summary,
  };
}

function previewTakeawayTreeArrangement() {
  state.takeawayArrangePreview = buildSourceOrderTakeawayDoc(state.payload?.outline || {});
  renderPresentationPanel(state.payload?.outline || {});
}

async function acceptTakeawayTreeArrangement() {
  if (!state.takeawayArrangePreview?.doc) return;
  pushTakeawayHistory("arrange");
  state.takeawayDoc = normalizeTakeawayDoc(state.takeawayArrangePreview.doc);
  state.takeawayArrangePreview = null;
  touchTakeawayDoc();
  renderPresentationPanel(state.payload?.outline || {});
  await saveTakeawayDoc();
}

function dismissTakeawayTreeArrangement() {
  state.takeawayArrangePreview = null;
  renderPresentationPanel(state.payload?.outline || {});
}

function takeawayArrangePreviewBlockHtml(block) {
  const indent = Math.max(0, Math.min(6, Number(block.indent || 0)));
  const marker = block.type === "heading" ? "#" : "•";
  const text = displayText(block.text || block.note || block.quote || "Untitled");
  return `<div class="takeaway-preview-row takeaway-preview-${escapeHtml(block.type)}" style="--takeaway-indent: ${indent}"><span>${marker}</span><strong>${escapeHtml(text)}</strong></div>`;
}

function takeawayArrangePreviewHtml(preview) {
  const summary = preview?.summary || {};
  const blocks = preview?.doc?.blocks || [];
  return `
    <div class="takeaway-arrange-preview" role="region" aria-label="Source Order Arrange Preview">
      <div class="takeaway-arrange-preview-header">
        <div>
          <strong>Source Order Preview</strong>
          <span>Moved ${summary.movedCount || 0} · Source-ordered ${summary.sourceOrderedCount || 0} · Reused headings ${summary.reusedHeadings || 0} · Created headings ${summary.createdHeadings || 0}${summary.lockedCount ? ` · Locked ${summary.lockedCount}` : ""}</span>
        </div>
        <div class="takeaway-arrange-actions">
          <button class="primary-button mini-button" id="acceptTakeawayArrange" type="button">Accept</button>
          <button class="secondary-button mini-button" id="dismissTakeawayArrange" type="button">Dismiss</button>
        </div>
      </div>
      <div class="takeaway-arrange-preview-tree">
        ${blocks.map(takeawayArrangePreviewBlockHtml).join("")}
      </div>
    </div>`;
}

function setTakeawaySaveState(message, kind = "") {
  renderReaderSaveStatus();
  const node = qs("#takeawaySaveState");
  if (!node) return;
  node.textContent = message;
  node.dataset.state = kind;
}

function cloneTakeawayDoc(doc = state.takeawayDoc) {
  return normalizeTakeawayDoc(JSON.parse(JSON.stringify(doc || defaultTakeawayDoc())));
}

function takeawayDocSignature(doc = state.takeawayDoc) {
  return JSON.stringify((doc?.blocks || []).map(block => ({ ...block, updated_at: "" })));
}

function pushTakeawayHistory(label = "edit") {
  if (!state.takeawayDoc || state.takeawayHistoryRestoring) return;
  const doc = cloneTakeawayDoc(state.takeawayDoc);
  const signature = takeawayDocSignature(doc);
  const latest = state.takeawayUndoStack[state.takeawayUndoStack.length - 1];
  if (latest?.signature === signature) return;
  state.takeawayUndoStack.push({ doc, signature, label });
  if (state.takeawayUndoStack.length > state.takeawayHistoryLimit) state.takeawayUndoStack.shift();
  state.takeawayRedoStack = [];
}

function restoreTakeawayHistoryItem(item, targetStack, label) {
  if (!item?.doc || !state.takeawayDoc) return;
  targetStack.push({ doc: cloneTakeawayDoc(state.takeawayDoc), signature: takeawayDocSignature(state.takeawayDoc), label });
  if (targetStack.length > state.takeawayHistoryLimit) targetStack.shift();
  state.takeawayHistoryRestoring = true;
  state.takeawayDoc = cloneTakeawayDoc(item.doc);
  state.takeawayDoc.updated_at = new Date().toISOString();
  state.takeawayArrangePreview = null;
  state.takeawayDocVersion = Number(state.takeawayDocVersion || 0) + 1;
  if (state.payload) state.payload.takeaway_doc = state.takeawayDoc;
  renderPresentationPanel(state.payload?.outline || {});
  state.takeawayHistoryRestoring = false;
  scheduleTakeawaySave(120);
}

function undoTakeawayChange() {
  const item = state.takeawayUndoStack.pop();
  if (!item) {
    toast("Nothing to undo");
    return;
  }
  restoreTakeawayHistoryItem(item, state.takeawayRedoStack, "redo");
  toast("Undone");
}

function redoTakeawayChange() {
  const item = state.takeawayRedoStack.pop();
  if (!item) {
    toast("Nothing to redo");
    return;
  }
  restoreTakeawayHistoryItem(item, state.takeawayUndoStack, "undo");
  toast("Redone");
}

function touchTakeawayDoc() {
  state.takeawayDocVersion = Number(state.takeawayDocVersion || 0) + 1;
  state.takeawayArrangePreview = null;
  if (state.takeawayDoc) state.takeawayDoc.updated_at = new Date().toISOString();
}

function scheduleTakeawaySave(delay = 650) {
  if (!state.currentPaperId || !state.takeawayDoc) return;
  state.takeawayDirty = true;
  if (state.takeawaySaveTimer) clearTimeout(state.takeawaySaveTimer);
  setTakeawaySaveState("Editing...", "pending");
  state.takeawaySaveTimer = setTimeout(() => {
    state.takeawaySaveTimer = null;
    saveTakeawayDoc({ silent: true }).catch(error => {
      setTakeawaySaveState("Save failed", "error");
      toast(`Takeaway save failed: ${error.message}`);
    });
  }, delay);
}

async function saveTakeawayDoc(options = {}) {
  if (!state.currentPaperId || !state.takeawayDoc) return;
  state.takeawayDoc = normalizeTakeawayDoc(state.takeawayDoc);
  const savingPaperId = state.currentPaperId;
  const savingVersion = Number(state.takeawayDocVersion || 0);
  state.takeawayDirty = true;
  setTakeawaySaveState("Saving...", "saving");
  const response = await queuePaperWrite(savingPaperId, "takeaway-doc", state.takeawayDoc);
  if (state.currentPaperId !== savingPaperId) return;
  if (Number(state.takeawayDocVersion || 0) === savingVersion) {
    state.takeawayDoc = normalizeTakeawayDoc(response.takeaway_doc || state.takeawayDoc);
    state.takeawayDirty = false;
    if (state.payload) state.payload.takeaway_doc = state.takeawayDoc;
    setTakeawaySaveState("Saved", "saved");
    if (!options.silent) toast("Takeaway saved");
    capturePaperSession();
  } else {
    setTakeawaySaveState("Editing...", "pending");
  }
}

function takeawayBlockById(blockId) {
  return state.takeawayDoc?.blocks?.find(block => block.id === blockId) || null;
}

function focusTakeawayBlock(blockId) {
  requestAnimationFrame(() => {
    const node = document.querySelector(`[data-takeaway-text="${cssEscape(blockId)}"]`);
    if (!node) return;
    node.focus();
    const range = document.createRange();
    range.selectNodeContents(node);
    range.collapse(false);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  });
}

function insertTakeawayBlock(afterBlockId = "", type = "bullet") {
  const blocks = state.takeawayDoc.blocks;
  const index = blocks.findIndex(block => block.id === afterBlockId);
  const previous = index >= 0 ? blocks[index] : blocks[blocks.length - 1];
  pushTakeawayHistory("insert");
  const block = normalizeTakeawayBlock({
    id: `td-${Date.now().toString(36)}`,
    type,
    text: "",
    indent: type === "heading" ? Math.max(0, previous?.indent || 0) : Math.max(0, previous?.indent ?? 1),
    level: type === "heading" ? Math.min(3, Math.max(1, previous?.level || 2)) : 2,
  }, blocks.length);
  blocks.splice(index >= 0 ? index + 1 : blocks.length, 0, block);
  touchTakeawayDoc();
  renderPresentationPanel(state.payload?.outline || {});
  focusTakeawayBlock(block.id);
  scheduleTakeawaySave(150);
}

function updateTakeawayBlockText(blockId, text) {
  const block = takeawayBlockById(blockId);
  if (!block) return;
  block.text = String(text || "").replace(/\u00a0/g, " ").trimEnd();
  block.updated_at = new Date().toISOString();
  touchTakeawayDoc();
  scheduleTakeawaySave();
}

function indentTakeawayBlock(blockId, delta) {
  const block = takeawayBlockById(blockId);
  if (!block) return;
  pushTakeawayHistory(delta > 0 ? "indent" : "outdent");
  block.indent = Math.max(0, Math.min(6, Number(block.indent || 0) + delta));
  block.updated_at = new Date().toISOString();
  touchTakeawayDoc();
  renderPresentationPanel(state.payload?.outline || {});
  focusTakeawayBlock(blockId);
  scheduleTakeawaySave(150);
}

function toggleTakeawayBlockType(blockId) {
  const block = takeawayBlockById(blockId);
  if (!block) return;
  pushTakeawayHistory("toggle-type");
  block.type = block.type === "heading" ? "bullet" : "heading";
  block.level = block.type === "heading" ? Math.max(1, Math.min(3, block.level || 2)) : 2;
  block.updated_at = new Date().toISOString();
  touchTakeawayDoc();
  renderPresentationPanel(state.payload?.outline || {});
  focusTakeawayBlock(blockId);
  scheduleTakeawaySave(150);
}

function removeTakeawayBlock(blockId) {
  const blocks = state.takeawayDoc.blocks;
  if (blocks.length <= 1) return;
  const index = blocks.findIndex(block => block.id === blockId);
  if (index < 0) return;
  pushTakeawayHistory("delete");
  blocks.splice(index, 1);
  touchTakeawayDoc();
  renderPresentationPanel(state.payload?.outline || {});
  focusTakeawayBlock(blocks[Math.max(0, index - 1)]?.id || blocks[0]?.id || "");
  scheduleTakeawaySave(150);
}

function takeawaySubtreeRange(blocks, index) {
  if (index < 0 || index >= blocks.length) return { start: index, end: index + 1 };
  const root = blocks[index];
  const rootIndent = Number(root?.indent || 0);
  let end = index + 1;
  while (end < blocks.length) {
    const block = blocks[end];
    const indent = Number(block?.indent || 0);
    if (root?.type === "heading") {
      if (block?.type === "heading" && indent <= rootIndent) break;
    } else if (indent <= rootIndent) {
      break;
    }
    end += 1;
  }
  return { start: index, end };
}

function takeawayBlockHasChildren(blocks, index) {
  const block = blocks[index];
  if (!block || block.type !== "heading") return false;
  const range = takeawaySubtreeRange(blocks, index);
  return range.end > index + 1;
}

function takeawayCollapsedAncestorId(blocks, index) {
  let indent = Number(blocks[index]?.indent || 0);
  for (let previous = index - 1; previous >= 0; previous -= 1) {
    const candidate = blocks[previous];
    const candidateIndent = Number(candidate?.indent || 0);
    if (candidate?.type !== "heading" || candidateIndent >= indent) continue;
    if (state.collapsedTakeawayBlockIds.has(candidate.id || "")) return candidate.id || "";
    indent = candidateIndent;
  }
  return "";
}

function toggleTakeawayCollapsed(blockId) {
  if (!blockId) return;
  if (state.collapsedTakeawayBlockIds.has(blockId)) state.collapsedTakeawayBlockIds.delete(blockId);
  else state.collapsedTakeawayBlockIds.add(blockId);
  renderPresentationPanel(state.payload?.outline || {});
}

function visibleTakeawayBlockEntries(blocks = state.takeawayDoc?.blocks || []) {
  return blocks.map((block, index) => ({ block, index })).filter(item => !takeawayCollapsedAncestorId(blocks, item.index));
}

function selectedTakeawayIdsForDrag(dragId) {
  if (!dragId) return [];
  if (!state.takeawaySelectedBlockIds.size || !state.takeawaySelectedBlockIds.has(dragId)) return [dragId];
  return Array.from(state.takeawaySelectedBlockIds);
}

function takeawayMoveRanges(blocks, ids) {
  const ranges = ids
    .map(id => blocks.findIndex(block => block.id === id))
    .filter(index => index >= 0)
    .map(index => blocks[index]?.type === "heading" ? takeawaySubtreeRange(blocks, index) : { start: index, end: index + 1 })
    .sort((left, right) => left.start - right.start);
  const merged = [];
  for (const range of ranges) {
    const latest = merged[merged.length - 1];
    if (latest && range.start <= latest.end) latest.end = Math.max(latest.end, range.end);
    else merged.push({ ...range });
  }
  return merged;
}

function canDropTakeawaySelection(dragId, targetId) {
  if (!dragId || !targetId) return false;
  const blocks = state.takeawayDoc?.blocks || [];
  const targetIndex = blocks.findIndex(block => block.id === targetId);
  if (targetIndex < 0) return false;
  return !takeawayMoveRanges(blocks, selectedTakeawayIdsForDrag(dragId)).some(range => targetIndex >= range.start && targetIndex < range.end);
}

function takeawayTargetInsertIndex(blocks, targetIndex, after) {
  if (targetIndex < 0) return blocks.length;
  if (!after) return targetIndex;
  return takeawaySubtreeRange(blocks, targetIndex).end;
}

function canDropTakeawayBlock(dragId, targetId) {
  return canDropTakeawaySelection(dragId, targetId);
}

function moveTakeawayBlock(dragId, targetId, after = false) {
  if (!dragId || !targetId) return;
  const blocks = state.takeawayDoc.blocks;
  let targetIndex = blocks.findIndex(item => item.id === targetId);
  if (targetIndex < 0) return;
  const selectedIds = selectedTakeawayIdsForDrag(dragId);
  const movingRanges = takeawayMoveRanges(blocks, selectedIds);
  if (!movingRanges.length || movingRanges.some(range => targetIndex >= range.start && targetIndex < range.end)) return;
  const insertBeforeRemoval = takeawayTargetInsertIndex(blocks, targetIndex, after);
  const movingBlocks = movingRanges.flatMap(range => blocks.slice(range.start, range.end));
  const movingIds = new Set(movingBlocks.map(block => block.id));
  pushTakeawayHistory(movingRanges.length > 1 || selectedIds.length > 1 ? "multi-move" : "move");
  for (const range of [...movingRanges].reverse()) blocks.splice(range.start, range.end - range.start);
  let insertIndex = insertBeforeRemoval;
  insertIndex -= movingRanges.filter(range => range.start < insertBeforeRemoval).reduce((sum, range) => sum + (range.end - range.start), 0);
  if (targetIndex < 0) targetIndex = blocks.length;
  blocks.splice(Math.max(0, Math.min(blocks.length, insertIndex)), 0, ...movingBlocks);
  state.takeawaySelectedBlockIds = new Set([...state.takeawaySelectedBlockIds].filter(id => movingIds.has(id)));
  touchTakeawayDoc();
  renderPresentationPanel(state.payload?.outline || {});
  focusTakeawayBlock(dragId);
  scheduleTakeawaySave(150);
}

function updateTakeawaySelection(blockId, event, checked) {
  if (!blockId) return;
  state.takeawaySelectionMode = true;
  const blocks = state.takeawayDoc?.blocks || [];
  const visibleIds = visibleTakeawayBlockEntries(blocks).map(item => item.block.id);
  if (event?.shiftKey && state.takeawayLastSelectedBlockId) {
    const start = visibleIds.indexOf(state.takeawayLastSelectedBlockId);
    const end = visibleIds.indexOf(blockId);
    if (start >= 0 && end >= 0) {
      const [from, to] = start < end ? [start, end] : [end, start];
      for (const id of visibleIds.slice(from, to + 1)) state.takeawaySelectedBlockIds.add(id);
    }
  } else if (checked) {
    state.takeawaySelectedBlockIds.add(blockId);
  } else {
    state.takeawaySelectedBlockIds.delete(blockId);
  }
  state.takeawayLastSelectedBlockId = blockId;
  if (!state.takeawaySelectedBlockIds.size) state.takeawaySelectionMode = false;
  renderPresentationPanel(state.payload?.outline || {});
}

function enableTakeawaySelectionMode(blockId, event = null) {
  if (!blockId) return;
  event?.preventDefault?.();
  state.takeawaySelectionMode = true;
  if (!state.takeawaySelectedBlockIds.has(blockId)) {
    state.takeawaySelectedBlockIds.add(blockId);
    state.takeawayLastSelectedBlockId = blockId;
  }
  renderPresentationPanel(state.payload?.outline || {});
}

function clearTakeawaySelection() {
  state.takeawaySelectedBlockIds.clear();
  state.takeawaySelectionMode = false;
  state.takeawayLastSelectedBlockId = "";
  renderPresentationPanel(state.payload?.outline || {});
}

function focusTakeawayBlockSource(blockId) {
  const block = takeawayBlockById(blockId);
  if (!block) return;
  const itemId = block.source_item_id || block.source_refs?.[0]?.item_id || "";
  if (itemId && state.presentationReportItems.some(item => item.id === itemId)) {
    focusPresentationReportItem(itemId);
    return;
  }
  const ref = block.source_refs?.[0] || {};
  if (ref.annotation_id && ref.source === "paper-note") focusAnnotation(ref.annotation_id);
  else if (ref.annotation_id && ref.source === "thinking-note") focusThinkingAnnotation(ref.annotation_id);
}

function takeawayBlockSourceAnnotation(block) {
  const ref = (block?.source_refs || []).find(item => item.annotation_id) || null;
  if (!ref) return null;
  if (ref.source === "thinking-note" || ref.block_id) {
    return (state.thinking?.annotations || []).find(item => item.id === ref.annotation_id) || null;
  }
  return (state.annotations || []).find(item => item.id === ref.annotation_id) || null;
}

function nearbySegmentImageSrc(segmentId, paperId = state.currentPaperId, radius = 3) {
  if (!segmentId || paperId !== state.currentPaperId) return "";
  const segments = state.payload?.segments || [];
  const index = segments.findIndex(segment => segment.id === segmentId);
  if (index < 0) return "";
  for (let distance = 0; distance <= radius; distance += 1) {
    for (const candidateIndex of distance ? [index - distance, index + distance] : [index]) {
      const segment = segments[candidateIndex];
      if (!segment) continue;
      const image = markdownImageInfo(segment.markdown || "");
      if (image?.src) return assetUrlForPaper(paperId, image.src);
    }
  }
  return "";
}

function takeawayBlockMediaSrc(block) {
  const ref = (block?.source_refs || []).find(item => item.paper_id || item.segment_id || item.annotation_id) || {};
  const paperId = ref.paper_id || state.currentPaperId;
  const annotation = takeawayBlockSourceAnnotation(block);
  const fromAnnotation = annotationMediaSrc(annotation, paperId);
  if (fromAnnotation) return fromAnnotation;
  const direct = markdownImageInfo(block?.quote || block?.text || "");
  if (direct?.src) return assetUrlForPaper(paperId, direct.src);
  if (paperId !== state.currentPaperId) return "";
  const segmentId = ref.segment_id || takeawayBlockSegmentId(block);
  const segment = segmentForId(segmentId);
  const fromSegment = markdownImageInfo(segment?.markdown || "");
  if (fromSegment?.src) return assetUrlForPaper(paperId, fromSegment.src);
  const hasImagePlaceholder = /!\s*Image|!Image|\bImage\s*\|/i.test([block?.text, block?.quote].filter(Boolean).join(" "));
  return hasImagePlaceholder ? nearbySegmentImageSrc(segmentId, paperId) : "";
}

function takeawayBlockHtml(block, index, blocks) {
  const indent = Math.max(0, Math.min(6, Number(block.indent || 0)));
  const quote = displayText(block.quote || "");
  const tags = block.tags || [];
  const sourceLabel = block.source_label || (block.source_refs?.length ? "Source" : "");
  const placeholder = block.type === "heading" ? "New heading" : "New bullet";
  const collapsible = takeawayBlockHasChildren(blocks, index);
  const collapsed = collapsible && state.collapsedTakeawayBlockIds.has(block.id);
  const selected = state.takeawaySelectedBlockIds.has(block.id);
  const hasUserNote = Boolean(displayText(block.note || ""));
  const sourceKind = takeawayBlockSourceKind(block);
  const mediaSrc = takeawayBlockMediaSrc(block);
  const dragTitle = selected ? "Drag selected blocks to reorder" : "Drag this block to reorder";
  return `
    <div class="takeaway-block takeaway-${escapeHtml(block.type)}${selected ? " selected" : ""}${hasUserNote ? " takeaway-user-note" : sourceKind ? " takeaway-highlight-only" : ""}" data-takeaway-block="${escapeHtml(block.id)}" data-takeaway-collapsible="${collapsible ? "true" : "false"}" data-takeaway-collapsed="${collapsed ? "true" : "false"}" data-takeaway-selected="${selected ? "true" : "false"}" data-takeaway-source-kind="${escapeHtml(sourceKind)}" style="--takeaway-indent: ${indent}">
      <input class="takeaway-select" data-takeaway-select="${escapeHtml(block.id)}" type="checkbox" title="Select block" aria-label="Select report block" ${selected ? "checked" : ""}>
      <button class="takeaway-collapse-toggle" data-takeaway-collapse="${escapeHtml(block.id)}" type="button" title="${collapsed ? "Expand section" : "Collapse section"}" ${collapsible ? "" : "disabled aria-hidden=\"true\""}>${collapsible ? (collapsed ? "⌃" : "⌄") : ""}</button>
      <button class="takeaway-drag-handle" data-takeaway-drag="${escapeHtml(block.id)}" draggable="true" type="button" title="${escapeHtml(dragTitle)}" aria-label="${escapeHtml(dragTitle)}"><span aria-hidden="true"></span></button>
      <div class="takeaway-block-main">
        <div class="takeaway-block-text" data-takeaway-text="${escapeHtml(block.id)}" contenteditable="true" spellcheck="true" data-placeholder="${escapeHtml(placeholder)}">${escapeHtml(block.text || "").replace(/\n/g, "<br>")}</div>
        ${mediaSrc ? `<img class="takeaway-block-media" src="${escapeHtml(mediaSrc)}" alt="${escapeHtml(quote || block.text || "Original source image")}">` : ""}
        ${quote ? `<div class="takeaway-block-quote">${escapeHtml(quote)}</div>` : ""}
        ${(block.meta || sourceLabel || tags.length) ? `<div class="takeaway-block-meta">
          ${sourceLabel ? `<button class="presentation-source-link takeaway-source-link" data-takeaway-source="${escapeHtml(block.id)}" type="button">${escapeHtml(sourceLabel)}</button>` : ""}
          ${block.meta ? `<span>${escapeHtml(block.meta)}</span>` : ""}
          ${tags.map(tag => `<span class="takeaway-tag">${escapeHtml(tag)}</span>`).join("")}
        </div>` : ""}
      </div>
      <div class="takeaway-block-actions">
        <button class="icon-button" data-takeaway-add="bullet" data-after-block="${escapeHtml(block.id)}" type="button" title="Add bullet below">+</button>
        <button class="icon-button" data-takeaway-add="heading" data-after-block="${escapeHtml(block.id)}" type="button" title="Add heading below">H</button>
        <button class="takeaway-type-button" data-takeaway-toggle-type="${escapeHtml(block.id)}" type="button" title="Toggle heading/bullet">${block.type === "heading" ? "H" : "B"}</button>
        <button class="icon-button" data-takeaway-outdent="${escapeHtml(block.id)}" type="button" title="Outdent">&lt;</button>
        <button class="icon-button" data-takeaway-indent="${escapeHtml(block.id)}" type="button" title="Indent">&gt;</button>
        <button class="icon-button" data-takeaway-delete="${escapeHtml(block.id)}" type="button" title="Delete block">x</button>
      </div>
    </div>`;
}

function bindTakeawayEditorEvents() {
  qs(".takeaway-doc-editor")?.addEventListener("dblclick", event => {
    if (event.target.closest(".takeaway-block")) return;
    insertTakeawayBlock(state.takeawayDoc.blocks[state.takeawayDoc.blocks.length - 1]?.id || "", "bullet");
  });
  qsa("[data-takeaway-text]").forEach(node => {
    node.addEventListener("input", () => updateTakeawayBlockText(node.dataset.takeawayText, node.innerText));
    node.addEventListener("keydown", event => {
      const blockId = node.dataset.takeawayText;
      const block = takeawayBlockById(blockId);
      if (!block) return;
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        insertTakeawayBlock(blockId, block.type === "heading" ? "bullet" : "bullet");
      } else if (event.key === "Tab") {
        event.preventDefault();
        indentTakeawayBlock(blockId, event.shiftKey ? -1 : 1);
      } else if (event.key === "Backspace" && !node.innerText.trim()) {
        event.preventDefault();
        removeTakeawayBlock(blockId);
      }
    });
  });
  qsa("[data-takeaway-add]").forEach(button => button.addEventListener("click", () => insertTakeawayBlock(button.dataset.afterBlock, button.dataset.takeawayAdd)));
  qsa("[data-takeaway-indent]").forEach(button => button.addEventListener("click", () => indentTakeawayBlock(button.dataset.takeawayIndent, 1)));
  qsa("[data-takeaway-outdent]").forEach(button => button.addEventListener("click", () => indentTakeawayBlock(button.dataset.takeawayOutdent, -1)));
  qsa("[data-takeaway-toggle-type]").forEach(button => button.addEventListener("click", () => toggleTakeawayBlockType(button.dataset.takeawayToggleType)));
  qsa("[data-takeaway-delete]").forEach(button => button.addEventListener("click", () => removeTakeawayBlock(button.dataset.takeawayDelete)));
  qsa("[data-takeaway-source]").forEach(button => button.addEventListener("click", () => focusTakeawayBlockSource(button.dataset.takeawaySource)));
  qsa("[data-takeaway-collapse]").forEach(button => button.addEventListener("click", event => {
    event.stopPropagation();
    if (!button.disabled) toggleTakeawayCollapsed(button.dataset.takeawayCollapse);
  }));
  qsa("[data-takeaway-select]").forEach(input => input.addEventListener("change", event => updateTakeawaySelection(input.dataset.takeawaySelect, event, input.checked)));
  qsa("[data-takeaway-drag]").forEach(handle => {
    handle.addEventListener("dragstart", event => {
      state.takeawayDragBlockId = handle.dataset.takeawayDrag;
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", state.takeawayDragBlockId || "");
      handle.closest("[data-takeaway-block]")?.classList.add("takeaway-dragging");
    });
    handle.addEventListener("dragend", () => {
      state.takeawayDragBlockId = "";
      qsa(".takeaway-dragging, .takeaway-drop-before, .takeaway-drop-after").forEach(node => node.classList.remove("takeaway-dragging", "takeaway-drop-before", "takeaway-drop-after"));
    });
  });
  qsa("[data-takeaway-block]").forEach(row => {
    row.addEventListener("contextmenu", event => {
      if (event.target.closest(".takeaway-block-actions, button, input, select, a")) return;
      enableTakeawaySelectionMode(row.dataset.takeawayBlock, event);
    });
    row.addEventListener("dragover", event => {
      if (!canDropTakeawayBlock(state.takeawayDragBlockId, row.dataset.takeawayBlock)) return;
      event.preventDefault();
      const rect = row.getBoundingClientRect();
      const after = event.clientY > rect.top + rect.height / 2;
      qsa(".takeaway-drop-before, .takeaway-drop-after").forEach(node => node.classList.remove("takeaway-drop-before", "takeaway-drop-after"));
      row.classList.add(after ? "takeaway-drop-after" : "takeaway-drop-before");
    });
    row.addEventListener("drop", event => {
      if (!canDropTakeawayBlock(state.takeawayDragBlockId, row.dataset.takeawayBlock)) return;
      event.preventDefault();
      const rect = row.getBoundingClientRect();
      moveTakeawayBlock(state.takeawayDragBlockId, row.dataset.takeawayBlock, event.clientY > rect.top + rect.height / 2);
    });
  });
}

function renderPresentationPanel(outline = state.payload?.outline || {}) {
  const root = qs("#presentationReportRoot");
  if (!root) return;
  const doc = normalizeTakeawayDoc(state.takeawayDoc || {});
  if (!doc.blocks.length && !state.payload) {
    root.className = "presentation-root muted";
    root.textContent = "Waiting for agent analysis or notes.";
    return;
  }
  root.className = "presentation-root takeaway-doc-root";
  const visibleBlocks = visibleTakeawayBlockEntries(doc.blocks);
  const selectedCount = state.takeawaySelectedBlockIds.size;
  root.innerHTML = `
    <div class="takeaway-toolbar">
      <div class="takeaway-toolbar-main">
        <button class="primary-button mini-button" data-takeaway-add="bullet" data-after-block="${escapeHtml(doc.blocks[doc.blocks.length - 1]?.id || "")}" type="button">Write</button>
        <button class="secondary-button mini-button" data-takeaway-add="heading" data-after-block="${escapeHtml(doc.blocks[doc.blocks.length - 1]?.id || "")}" type="button">Heading</button>
        <button class="secondary-button mini-button" id="arrangeTakeawayTree" type="button">Source order</button>
      </div>
      ${selectedCount ? `<span class="takeaway-selection-count">${selectedCount} selected</span><button class="secondary-button mini-button" id="clearTakeawaySelection" type="button">Clear</button>` : ""}
      <button class="secondary-button mini-button" id="saveTakeawayNow" type="button">Save</button>
      <span id="takeawaySaveState" class="thinking-save-state">${doc.updated_at ? "Saved" : "Draft"}</span>
    </div>
    <div class="takeaway-doc-guidance">Edit your saved notes directly. Drag to reorder; Tab / Shift+Tab changes depth. Source order groups evidence by its place in the paper.</div>
    ${state.takeawayArrangePreview ? takeawayArrangePreviewHtml(state.takeawayArrangePreview) : ""}
    <div class="takeaway-doc-editor${state.takeawaySelectionMode ? " takeaway-selection-mode" : ""}" aria-label="Editable takeaway report">
      ${visibleBlocks.map(item => takeawayBlockHtml(item.block, item.index, doc.blocks)).join("")}
    </div>`;
  bindTakeawayEditorEvents();
  qs("#clearTakeawaySelection")?.addEventListener("click", clearTakeawaySelection);
  qs("#arrangeTakeawayTree")?.addEventListener("click", previewTakeawayTreeArrangement);
  qs("#addTakeawayToMindmap")?.addEventListener("click", async () => {
    const category = window.prompt("Mindmap category path (use / for nested categories):", normalizeTagsInput(state.payload?.metadata?.tags || [])[0] || "Uncategorized");
    const categoryPath = String(category || "").split(/[\\/]+/).map(item => item.trim()).filter(Boolean);
    if (!categoryPath.length) return;
    if (!state.mindmap) await loadMindmap(state.currentMindmapProject || "collaborative");
    await addPaperToMindmap(state.currentPaperId, { categoryPath, source: "takeaway-report", includeTakeaway: true });
  });
  qs("#acceptTakeawayArrange")?.addEventListener("click", () => acceptTakeawayTreeArrangement().catch(error => {
    setTakeawaySaveState("Save failed", "error");
    toast(`Accept failed: ${error.message}`);
  }));
  qs("#dismissTakeawayArrange")?.addEventListener("click", dismissTakeawayTreeArrangement);
  qs("#saveTakeawayNow")?.addEventListener("click", () => saveTakeawayDoc());
  if (state.takeawayAutoSaveNeeded) {
    state.takeawayAutoSaveNeeded = false;
    scheduleTakeawaySave(250);
  }
}

async function addReportThought(groupKey) {
  if (!state.thinking) return;
  const text = window.prompt("Add your thought to this report group:");
  const note = String(text || "");
  if (!note.trim()) return;
  const now = new Date().toISOString();
  state.thinking.report_thoughts = [...(state.thinking.report_thoughts || []), {
    id: `rt-${Date.now().toString(36)}`,
    group: groupKey || "sensemaking-gap",
    note,
    created_at: now,
    updated_at: now,
  }];
  await saveThinking({ silent: true });
  renderPresentationPanel(state.payload?.outline || {});
  toast("Thought added");
}

async function deleteReportThought(thoughtId) {
  if (!state.thinking || !thoughtId) return;
  state.thinking.report_thoughts = (state.thinking.report_thoughts || []).filter(item => item.id !== thoughtId);
  await saveThinking({ silent: true });
  renderPresentationPanel(state.payload?.outline || {});
  toast("Thought deleted");
}

function focusPresentationReportItem(itemId) {
  const item = state.presentationReportItems.find(candidate => candidate.id === itemId);
  if (!item) return;
  if (item.source === "free-thought") return;
  activateView("reader");
  if (item.source === "paper-note" && item.annotationId) {
    setWorkspaceMode("split");
    focusAnnotation(item.annotationId);
    return;
  }
  if (item.source === "thinking-note" && item.annotationId) {
    if (item.blockId === paperBriefBlockId) {
      setWorkspaceMode("split");
      focusThinkingAnnotation(item.annotationId);
      return;
    }
    setWorkspaceMode("think");
    focusThinkingAnnotation(item.annotationId);
    return;
  }
  if (item.source === "thinking-block" && item.blockId) {
    setWorkspaceMode("think");
    const block = document.querySelector(`[data-thinking-block-card="${cssEscape(item.blockId)}"]`);
    block?.scrollIntoView({ behavior: "smooth", block: "center" });
    block?.classList.add("focus-flash");
    setTimeout(() => block?.classList.remove("focus-flash"), 1200);
    return;
  }
  setWorkspaceMode("split");
  scrollToParagraph(item.anchor || "paper-brief");
}

async function updatePresentationGroupOverride(context, groupKey) {
  if (!context?.annotationId) return;
  const applyOverride = annotation => {
    if (groupKey) annotation.presentation_flow_id = groupKey;
    else delete annotation.presentation_flow_id;
    annotation.updated_at = new Date().toISOString();
  };
  if (context.source === "thinking-note") {
    const annotation = state.thinking?.annotations?.find(item => item.id === context.annotationId);
    if (!annotation) return;
    applyOverride(annotation);
    await saveThinking({ silent: true });
    renderSensemakingPanel();
  } else {
    await mutateAnnotationTags(context.paperId || state.currentPaperId, context.annotationId, applyOverride);
  }
  renderPresentationPanel(state.payload?.outline || {});
  toast(groupKey ? "Card moved" : "Auto placement restored");
}

function renderSidebar() {
  const outline = state.payload?.outline || {};
  const list = qs("#outlineList");
  if (!list) return;
  const mediaList = qs("#paperMapMediaList");
  const activeTab = state.paperMapTab === "media" ? "media" : "map";
  qsa("[data-paper-map-tab]").forEach(button => {
    const active = button.dataset.paperMapTab === activeTab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
  list.hidden = activeTab !== "map";
  if (mediaList) {
    mediaList.hidden = activeTab !== "media";
    if (activeTab !== "media") mediaList.innerHTML = "";
  }
  list.innerHTML = "";
  const outlineItems = outline.outline || [];
  for (const [index, item] of outlineItems.entries()) {
    if (outlineCollapsedAncestorId(outlineItems, index)) continue;
    const level = outlineDisplayLevel(item);
    const collapsible = outlineItemHasChildren(outlineItems, index);
    const collapsed = collapsible && state.collapsedOutlineIds.has(item.id || "");
    const progress = readingProgressForOutlineItem(item, outlineItems, index);
    const button = document.createElement("button");
    button.className = `outline-item outline-l${level}`;
    button.dataset.outlinePid = item.id || "";
    button.dataset.outlineIndex = String(index);
    button.dataset.outlineLevel = String(level);
    button.dataset.outlineCollapsible = collapsible ? "true" : "false";
    button.dataset.outlineCollapsed = collapsed ? "true" : "false";
    if (collapsible) button.setAttribute("aria-expanded", collapsed ? "false" : "true");
    button.dataset.readingState = progress.state;
    button.style.setProperty("--outline-indent", `${16 + Math.max(0, level - 1) * 14}px`);
    button.style.setProperty("--reading-depth", String(progress.depth || 0));
    const title = index === 0 && Number(item.level) === 1 && state.payload?.metadata?.title_source === "feishu"
      ? paperTitle(state.payload.metadata) : cleanPaperTitle(item.title || item.id);
    button.innerHTML = `<span class="outline-collapse-toggle" aria-hidden="true">${collapsible ? (collapsed ? "⌃" : "⌄") : ""}</span><span class="outline-item-title">${escapeHtml(title)}</span>`;
    button.addEventListener("click", event => {
      if (event.target.closest(".outline-collapse-toggle") && collapsible) {
        event.preventDefault();
        event.stopPropagation();
        toggleOutlineCollapsed(item.id || "");
        return;
      }
      scrollToParagraph(item.id);
    });
    list.appendChild(button);
  }
  if (!list.children.length) list.textContent = "No outline yet.";
  if (activeTab === "media" && mediaList) renderPaperMapMediaList(mediaList);
  updateCurrentOutlineHint(outlineItems);
  if (state.presentationReportOpen) renderPresentationPanel(outline);
}

function paperMapMediaCaption(text) {
  return compactText(displayText(String(text || "").replace(/!\[[^\]]*\]\([^)]+\)/g, "")).replace(/\s+/g, " "), 150);
}

function paperMapTableCellsFromHtml(text) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(String(text || ""), "text/html");
  return Array.from(doc.querySelectorAll("tr")).slice(0, 4).map(row => Array.from(row.children)
    .filter(cell => /^(td|th)$/i.test(cell.tagName))
    .slice(0, 3)
    .map(cell => displayText(cell.textContent))
  ).filter(row => row.length);
}

function paperMapTableCellsFromPipe(text) {
  return String(text || "").split("\n")
    .filter(line => line.includes("|"))
    .map(line => line.replace(/^\||\|$/g, "").split("|").map(cell => displayText(cell)))
    .filter(cells => !cells.every(cell => /^:?-{3,}:?$/.test(cell)))
    .slice(0, 4)
    .map(cells => cells.slice(0, 3));
}

function paperMapTablePreviewHtml(entry) {
  const segment = segmentForId(entry.segment_id) || {};
  const text = segment.markdown || entry.caption || "";
  const rows = isHtmlTable(text) ? paperMapTableCellsFromHtml(text) : paperMapTableCellsFromPipe(text);
  if (!rows.length) return `<div class="paper-map-media-placeholder">Table</div>`;
  const columnCount = Math.max(1, Math.min(3, ...rows.map(row => row.length)));
  const cells = rows.flatMap(row => {
    const padded = [...row];
    while (padded.length < columnCount) padded.push("");
    return padded.slice(0, columnCount);
  });
  return `<div class="paper-map-mini-table" style="--paper-map-table-cols: ${columnCount}">${cells.map(cell => `<span>${escapeHtml(compactText(cell, 42))}</span>`).join("")}</div>`;
}

function paperMapFigurePreviewHtml(entry) {
  if (!entry.src) return `<div class="paper-map-media-placeholder">Figure</div>`;
  return `<div class="paper-map-media-thumb"><img src="${escapeHtml(entry.src)}" alt="${escapeHtml(entry.title)} preview" loading="lazy"></div>`;
}

function paperMapMediaEntryHtml(entry) {
  const preview = entry.kind === "table" ? paperMapTablePreviewHtml(entry) : paperMapFigurePreviewHtml(entry);
  const badge = entry.kind === "table" ? "Table" : entry.part_count > 1 ? `${entry.part_count} parts` : "Figure";
  const caption = paperMapMediaCaption(entry.caption || entry.title);
  return `<button class="paper-map-media-card" data-paper-map-jump="${escapeHtml(entry.segment_id)}" type="button">
    <span class="paper-map-media-head"><strong>${escapeHtml(entry.title)}</strong><small>${escapeHtml(badge)}</small></span>
    ${preview}
    ${caption ? `<span class="paper-map-media-caption">${escapeHtml(caption)}</span>` : ""}
  </button>`;
}

function renderPaperMapMediaList(root) {
  const entries = paperMapMediaEntries();
  if (!entries.length) {
    root.innerHTML = `<div class="paper-map-empty">No figures or tables found in this parsed paper.</div>`;
    return;
  }
  root.innerHTML = `<div class="paper-map-media-summary">${entries.length} visual checkpoints</div>${entries.map(paperMapMediaEntryHtml).join("")}`;
  root.querySelectorAll("[data-paper-map-jump]").forEach(button => {
    button.addEventListener("click", () => scrollToParagraph(button.dataset.paperMapJump));
  });
}

function setPaperMapTab(tab) {
  state.paperMapTab = tab === "media" ? "media" : "map";
  renderSidebar();
}

function setWorkspaceMode(mode) {
  tickReadingProgress({ skipSchedule: true });
  const previousMode = state.workspaceMode;
  const nextMode = ["read", "split", "think"].includes(mode) ? mode : "split";
  state.workspaceMode = nextMode;
  state.readingLastTick = performance.now();
  const workspace = qs(".reader-workspace");
  if (workspace) workspace.dataset.workspaceMode = nextMode;
  qsa(".workspace-mode").forEach(button => {
    button.classList.toggle("active", button.dataset.workspaceMode === nextMode);
    button.setAttribute("aria-pressed", String(button.dataset.workspaceMode === nextMode));
  });
  qs("#readerWidth")?.toggleAttribute("disabled", nextMode === "think");
  qs("#toggleReadingTeacher")?.toggleAttribute("disabled", nextMode === "think");
  renderReadingTeacherStatus();
  if (qs("#readerView")) qs("#readerView").dataset.workspaceMode = nextMode;
  if (nextMode === "read" && state.presentationReportOpen) setReaderSidePane("sensemaking");
  if (previousMode === "read" && nextMode !== "read") renderSensemakingPanel();
  if (nextMode !== "read") restoreThinkingChatScroll();
  updateAnnotationToolbarVisibility();
  if (state.currentPaperId) persistPaperTabs();
}

function setPaperMapCollapsed(collapsed) {
  state.paperMapCollapsed = Boolean(collapsed);
  document.body.classList.toggle("paper-map-collapsed", state.paperMapCollapsed);
  localStorage.setItem(paperMapCollapsedStorageKey, state.paperMapCollapsed ? "1" : "0");
  const mainButton = qs("#togglePaperMapMain");
  if (mainButton) {
    mainButton.textContent = "Outline";
    mainButton.setAttribute("aria-expanded", String(!state.paperMapCollapsed));
  }
  const sideButton = qs("#togglePaperMap");
  if (sideButton) {
    sideButton.textContent = "×";
    sideButton.title = "Collapse outline";
    sideButton.setAttribute("aria-label", "Collapse outline");
  }
  const railButton = qs("#paperMapRail");
  if (railButton) railButton.setAttribute("aria-hidden", state.paperMapCollapsed ? "false" : "true");
}

function initPaperMapCollapse() {
  setPaperMapCollapsed(localStorage.getItem(paperMapCollapsedStorageKey) === "1");
}

function isEditableTarget(target) {
  return Boolean(target?.closest?.('input, textarea, select, [contenteditable="true"]'));
}

function isTakeawayShortcutScope(target) {
  return Boolean(state.presentationReportOpen || target?.closest?.("#takeawayPane, .takeaway-doc-root"));
}

function handleTakeawayKeyboardShortcut(event) {
  const key = String(event.key || "").toLowerCase();
  const mod = event.ctrlKey || event.metaKey;
  if (!mod || !isTakeawayShortcutScope(event.target)) return false;
  if (key === "s") {
    event.preventDefault();
    saveTakeawayDoc().catch(error => toast(`Takeaway save failed: ${error.message}`));
    return true;
  }
  if (isEditableTarget(event.target)) return false;
  if (key === "z") {
    event.preventDefault();
    if (event.shiftKey) redoTakeawayChange();
    else undoTakeawayChange();
    return true;
  }
  if (key === "y") {
    event.preventDefault();
    redoTakeawayChange();
    return true;
  }
  return false;
}

function setReaderSidePane(pane) {
  const nextPane = pane === "takeaway" ? "takeaway" : "sensemaking";
  const reportOpen = nextPane === "takeaway";
  state.presentationReportOpen = reportOpen;
  document.body.classList.toggle("presentation-report-open", reportOpen);
  const panel = qs("#sensemakingPanel");
  if (panel) panel.dataset.sidePane = nextPane;
  const sensemakingPane = qs("#sensemakingPane");
  const takeawayPane = qs("#takeawayPane");
  if (sensemakingPane) {
    sensemakingPane.hidden = reportOpen;
    sensemakingPane.classList.toggle("reader-side-pane-active", !reportOpen);
  }
  if (takeawayPane) {
    takeawayPane.hidden = !reportOpen;
    takeawayPane.classList.toggle("reader-side-pane-active", reportOpen);
  }
  qsa("[data-reader-side-pane]").forEach(button => {
    button.classList.toggle("active", button.dataset.readerSidePane === nextPane);
    button.setAttribute("aria-pressed", button.dataset.readerSidePane === nextPane ? "true" : "false");
  });
  const title = qs("#readerSidePanelTitle");
  if (title) title.textContent = reportOpen ? "Saved Takeaway" : "AI chat";
  const openButton = qs("#openPresentationReport");
  if (openButton) openButton.textContent = reportOpen ? "Show chat" : "Saved Takeaway";
  if (!reportOpen) restoreThinkingChatScroll();
}

function openPresentationReport() {
  if (state.workspaceMode === "read") setWorkspaceMode("split");
  renderPresentationPanel(state.payload?.outline || {});
  setReaderSidePane("takeaway");
}

function closePresentationReport() {
  setReaderSidePane("sensemaking");
}

function togglePresentationReport() {
  if (state.presentationReportOpen) closePresentationReport();
  else openPresentationReport();
}

function renderPaperMeta() {
  const metadata = state.payload?.metadata || {};
  const root = qs("#paperMeta");
  const bits = [];
  for (const key of ["authors", "venue", "year", "read_status"]) {
    if (metadata[key]) bits.push(`<span>${escapeHtml(Array.isArray(metadata[key]) ? metadata[key].join(", ") : metadata[key])}</span>`);
  }
  root.innerHTML = `<div class="meta-title-row"><h1 class="meta-title">${escapeHtml(paperTitle(metadata))}</h1></div>
    <div class="paper-bibliography">${bits.join('<span class="bibliography-separator" aria-hidden="true">·</span>')}</div>`;
  const links = qs("#readerFileLinks");
  if (links) {
    const path = `/api/papers/${encodeURIComponent(state.currentPaperId)}`;
    links.innerHTML = `${metadata.source_pdf ? `<a href="${path}/pdf" target="_blank" rel="noreferrer">Open original PDF</a>` : ""}
      <a href="${path}/reader-md" target="_blank" rel="noreferrer">Reader Markdown</a>
      <a href="${path}/paper-md" target="_blank" rel="noreferrer">Paper Markdown</a>
      <a href="${path}/translation-notes" target="_blank" rel="noreferrer">Extraction notes</a>
      <span class="muted small-text">${escapeHtml(processingLabel(metadata))} · ${escapeHtml(processingStatus(metadata))}${metadata.citation_count !== undefined && metadata.citation_count !== "" ? ` · Cited ${escapeHtml(metadata.citation_count)}` : ""}</span>`;
  }
  const importance = qs("#readerImportance");
  if (importance) {
    importance.innerHTML = importanceStarEditorHtml(metadata, { variant: "workspace" });
    bindImportanceStarEditors(importance);
  }
  renderReaderSaveStatus();
  renderWorkspaceMetadataPanel();
  renderFeishuMetadata();
}

function firstMetadataValue(paper, keys = []) {
  for (const key of keys) {
    const value = paper?.[key];
    if (Array.isArray(value) && value.length) return value;
    if (value && typeof value === "object" && Object.keys(value).length) return value;
    if (String(value ?? "").trim()) return value;
  }
  return "";
}

function metadataValueList(value) {
  if (Array.isArray(value)) return value.map(item => String(item || "").trim()).filter(Boolean);
  if (value && typeof value === "object") return Object.values(value).map(item => String(item || "").trim()).filter(Boolean);
  return String(value || "").split(/[;；\n]+/).map(item => item.trim()).filter(Boolean);
}

function metadataUrlCards(paper) {
  const cards = [];
  const addUrl = (label, value) => {
    const url = String(value || "").trim();
    if (!url) return;
    cards.push(`<a class="metadata-info-card metadata-info-link" href="${escapeHtml(url)}" target="_blank" rel="noreferrer"><span>${escapeHtml(label)}</span><strong>${escapeHtml(compactText(url, 96))}</strong></a>`);
  };
  addUrl("PDF / source", firstMetadataValue(paper, ["source_url", "pdf_url", "url", "original_url"]));
  addUrl("Web page", firstMetadataValue(paper, ["source_page_url", "page_url", "html_url"]));
  addUrl("Citation profile", firstMetadataValue(paper, ["citation_url", "semantic_scholar_url", "openalex_url"]));
  const videos = firstMetadataValue(paper, ["videos", "related_videos", "youtube_videos", "video_results"]);
  if (Array.isArray(videos)) {
    videos.slice(0, 3).forEach((video, index) => {
      const url = typeof video === "string" ? video : video?.url;
      const title = typeof video === "string" ? `YouTube ${index + 1}` : video?.title || `YouTube ${index + 1}`;
      addUrl(title, url);
    });
  } else {
    metadataValueList(firstMetadataValue(paper, ["youtube_url", "video_url"])).slice(0, 3).forEach((url, index) => addUrl(`YouTube ${index + 1}`, url));
  }
  return cards.join("");
}

function workspaceMetadataInfoHtml(paper) {
  const rows = [];
  const addRow = (label, value) => {
    const text = Array.isArray(value) ? value.filter(Boolean).join(", ") : String(value ?? "").trim();
    if (!text) return;
    rows.push(`<div class="metadata-info-row"><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(text)}</dd></div>`);
  };
  addRow("Authors", firstMetadataValue(paper, ["authors", "author"]));
  addRow("Institutions", firstMetadataValue(paper, ["institutions", "institution"]));
  addRow("Venue", firstMetadataValue(paper, ["venue", "journal"]));
  addRow("Year", firstMetadataValue(paper, ["year", "publication_year"]));
  addRow("DOI", firstMetadataValue(paper, ["doi"]));
  addRow("Citations", firstMetadataValue(paper, ["citation_count", "cited_by_count"]));
  addRow("Influential", firstMetadataValue(paper, ["influential_citation_count"]));
  addRow("Citation source", firstMetadataValue(paper, ["citation_source"]));
  const quota = paper?.youtube_quota;
  if (quota && typeof quota === "object") addRow("YouTube quota", `${quota.used ?? 0}/${quota.limit ?? "?"}`);
  const citationText = firstMetadataValue(paper, ["bibtex", "citation", "apa", "mla"]);
  const citationBlock = String(citationText || "").trim()
    ? `<details class="metadata-citation-details"><summary>Citation text</summary><pre>${escapeHtml(String(citationText).trim())}</pre></details>`
    : "";
  const links = metadataUrlCards(paper);
  if (!rows.length && !links && !citationBlock) return "";
  return `
    <section class="metadata-info-section" aria-label="Reading metadata">
      <div class="metadata-info-heading">
        <span>Reading references</span>
        <small>${paper.feishu?.record_id ? "Bibliographic fields copied from the linked Feishu record" : "Links and citation details used while reading"}</small>
      </div>
      ${links ? `<div class="metadata-info-cards">${links}</div>` : ""}
      ${rows.length ? `<dl class="metadata-info-list">${rows.join("")}</dl>` : ""}
      ${citationBlock}
    </section>`;
}

function workspaceMetadataPaper() {
  const libraryPaper = state.library?.papers?.find(item => item.id === state.currentPaperId) || {};
  return { ...libraryPaper, ...(state.payload?.metadata || {}) };
}

function feishuPaperState(paperId) {
  if (!state.feishuSyncByPaper.has(paperId)) state.feishuSyncByPaper.set(paperId, { status: "", error: "", candidates: [], lastAttempt: 0 });
  return state.feishuSyncByPaper.get(paperId);
}

function applyFeishuMetadataResult(paperId, response) {
  if (!response.metadata) return;
  const session = state.paperSessions.get(paperId);
  const payload = paperId === state.currentPaperId ? state.payload : session?.payload;
  const keys = [...Object.keys(state.feishuConfig.fields || {}), "title_source", "title_key", "feishu", "feishu_local_overrides"];
  const fields = Object.fromEntries(keys.filter(key => key in response.metadata).map(key => [key, response.metadata[key]]));
  if (payload) {
    Object.assign(payload.metadata, fields);
    if (response.feishu_metadata) payload.feishu_metadata = response.feishu_metadata;
  }
  const paper = state.library?.papers?.find(item => item.id === paperId);
  if (paper) Object.assign(paper, fields);
  state.libraryDirty = true;
  if (paperId === state.currentPaperId) {
    renderPaperMeta();
    renderPaperTabs();
    renderPaperSelect();
    renderSidebar();
  }
}

function feishuIntakePhase() {
  const paper = state.feishuIntake.localPaper;
  if (!paper) return "unparsed";
  if (processingStatus(paper) === "ready" && processingMode(paper) === "deep") return "ready";
  if (paperParsingPending(paper)) return processingStatus(paper) === "processing_queued" ? "queued" : "processing";
  return processingStatus(paper) === "failed" ? "failed" : "unparsed";
}

function feishuIntakeNeedsPolling() {
  return Boolean(qs("#feishuIntakeDialog")?.open && !state.feishuIntake.loading && !state.feishuIntake.busy
    && ["queued", "processing"].includes(feishuIntakePhase()));
}

function watchFeishuIntakeProcessing() {
  if (feishuIntakeNeedsPolling()) refreshProcessingQueue();
  else if (!state.processingQueue.open) clearTimeout(state.processingQueue.timer);
}

function renderFeishuIntakeStatus() {
  const intake = state.feishuIntake;
  const phase = feishuIntakePhase();
  const messages = {
    ready: "Full text is ready. No need to queue this paper again.",
    queued: "Queued for parsing. The full-text button will appear here when it is ready.",
    processing: "Parsing in the background. The full-text button will appear here when it is ready.",
    failed: `Parsing failed${intake.localPaper?.processing_error ? `: ${intake.localPaper.processing_error}` : "."}`,
  };
  const status = qs("#feishuIntakeStatus");
  status.textContent = intake.error || intake.statusError || (intake.busy ? "Preparing the requested paper…"
    : intake.loading ? "Reading Feishu…" : messages[phase] || intake.message);
  status.classList.toggle("error-text", Boolean(intake.error || intake.statusError || phase === "failed"));
  qs("#searchFeishuIntake").disabled = intake.busy || intake.loading;
  qs("#feishuIntakeQuery").disabled = intake.busy;
  qsa("[data-preview-feishu-record]").forEach(button => { button.disabled = intake.busy; });
}

function renderFeishuIntakeActions() {
  renderFeishuIntakeStatus();
  const intake = state.feishuIntake;
  const root = qs("#feishuIntakeActions");
  if (!root) return;
  const phase = feishuIntakePhase();
  const hadFocus = root.contains(document.activeElement);
  const focusedId = document.activeElement?.id;
  const queueLink = '<button id="viewFeishuParsingQueue" class="secondary-button" data-view-feishu-queue type="button">View parsing queue</button>';
  if (intake.busy) root.innerHTML = '<button class="secondary-button" type="button" disabled>Preparing…</button>';
  else if (phase === "ready") {
    root.innerHTML = `<button id="readFeishuFullText" class="primary-button" data-open-feishu-paper="${escapeHtml(intake.localPaper.id)}" type="button">Read full text</button>`;
  } else if (phase === "queued" || phase === "processing") {
    root.innerHTML = `<button class="secondary-button" type="button" disabled>${phase === "queued" ? "Queued for parsing" : "Parsing…"}</button>${queueLink}`;
  } else if (phase === "failed") {
    root.innerHTML = `<button id="retryFeishuParsing" class="primary-button" data-retry-feishu-parse type="button">Retry parsing</button>${queueLink}`;
  } else {
    root.innerHTML = `<button id="queueFeishuPaper" class="primary-button" type="button" ${intake.loading || !intake.fileToken ? "disabled" : ""}>Queue for reading</button>`;
  }
  qs("#feishuPdfInputs").hidden = intake.busy || phase !== "unparsed";
  qs("#feishuIntakeActionHelp").textContent = ({
    ready: "Read the original Markdown now; translation can continue in the background. Metadata refresh is separate, under More → Feishu metadata.",
    queued: "Already queued. You can preview another paper while waiting; there is no need to submit this one again.",
    processing: "Already parsing. You can preview another paper while this one finishes.",
    failed: "Retry uses the existing local PDF. Your saved notes and highlights are kept.",
    unparsed: "Queue for reading imports the selected PDF and requests parsing. Preview alone does neither. No cloud fields are written.",
  })[phase];
  if (hadFocus) {
    const previous = focusedId ? document.getElementById(focusedId) : null;
    (previous && root.contains(previous) ? previous : root.querySelector("button:not(:disabled)"))?.focus({ preventScroll: true });
  }
}

function renderFeishuIntake() {
  const intake = state.feishuIntake;
  renderFeishuIntakeStatus();
  qs("#feishuIntakeResults").innerHTML = intake.records.map(record => `
    <button class="secondary-button" data-preview-feishu-record="${escapeHtml(record.record_id)}"
      aria-pressed="${intake.record?.record_id === record.record_id}" type="button" ${intake.busy ? "disabled" : ""}>
      ${escapeHtml(record.title || record.record_id)}
    </button>`).join("") + (intake.hasMore ? '<p class="muted small-text">More matches exist. Refine the title to narrow the search.</p>' : "");
  const preview = qs("#feishuIntakePreview");
  if (!intake.record) {
    preview.innerHTML = '<p class="muted">Search your Feishu collection, then select a paper to preview its existing briefing.</p>';
    return;
  }
  const record = intake.record;
  const metadata = record.metadata || {};
  const attachments = record.attachments || [];
  const briefings = record.briefings || {};
  const brief = briefings[intake.brief] || "";
  preview.innerHTML = `
    <h3 id="feishuPreviewTitle" tabindex="-1">${escapeHtml(metadata.title || attachments[0]?.name || record.record_id)}</h3>
    <p class="muted small-text">${escapeHtml([metadata.authors, metadata.venue, metadata.year].filter(Boolean).join(" · "))}</p>
    <div class="reader-data-actions" role="group" aria-label="Feishu briefing language">
      ${["raw text_中文", "raw text"].map(field => `<button class="reader-side-tab ${intake.brief === field ? "active" : ""}" data-feishu-brief="${escapeHtml(field)}" type="button" aria-pressed="${intake.brief === field}">${escapeHtml(field)}</button>`).join("")}
    </div>
    ${brief ? `<pre class="feishu-intake-brief">${escapeHtml(brief)}</pre>` : '<p class="muted">This briefing is not available yet. It is not required to parse the PDF.</p>'}
    <div id="feishuPdfInputs">
    <label class="sense-label" for="feishuAttachmentSelect">PDF attachment</label>
    <select id="feishuAttachmentSelect" ${intake.busy ? "disabled" : ""}>
      ${attachments.length !== 1 ? `<option value="">${attachments.length ? "Select the PDF to read" : "No PDF attachment available"}</option>` : ""}
      ${attachments.map(file => `<option value="${escapeHtml(file.file_token)}" ${file.file_token === intake.fileToken ? "selected" : ""}>${escapeHtml(file.name)}${file.size ? ` · ${Math.ceil(file.size / 1024)} KB` : ""}</option>`).join("")}
    </select>
    <details ${intake.localPath ? "open" : ""}>
      <summary>Use a local PDF instead of downloading</summary>
      <label class="sense-label" for="feishuLocalPdfPath">PDF path on this computer (optional)</label>
      <input id="feishuLocalPdfPath" type="text" value="${escapeHtml(intake.localPath)}" placeholder="Full local path to the PDF" ${intake.busy ? "disabled" : ""} />
      <p class="muted small-text">Only use a file you know belongs to this record. Its size is checked, but the cloud PDF is not downloaded for byte comparison.</p>
    </details>
    </div>
    <div id="feishuIntakeActions" class="reader-data-actions"></div>
    <p id="feishuIntakeActionHelp" class="muted small-text"></p>`;
  renderFeishuIntakeActions();
}

function openFeishuIntake() {
  if (!state.feishuConfig.enabled) { toast("Configure the Feishu Base and table before opening a cloud paper."); return; }
  renderFeishuIntake();
  qs("#feishuIntakeDialog").showModal();
  qs("#feishuIntakeQuery").focus();
  watchFeishuIntakeProcessing();
}

async function previewFeishuIntake(reference) {
  const intake = state.feishuIntake;
  const version = ++intake.version;
  Object.assign(intake, { loading: true, error: "", statusError: "", message: "", record: null, localPaper: null, localPath: "", fileToken: "" });
  watchFeishuIntakeProcessing();
  renderFeishuIntake();
  try {
    const data = await api(`/api/feishu/preview?${new URLSearchParams({ reference })}`);
    if (version !== intake.version) return;
    Object.assign(intake, {
      record: data.record, localPaper: data.local_paper || null,
      fileToken: data.record.attachments?.length === 1 ? data.record.attachments[0].file_token : "",
      brief: data.record.briefings?.["raw text_中文"] ? "raw text_中文" : "raw text",
    });
  } catch (error) {
    if (version === intake.version) intake.error = `Preview unavailable: ${error.message}`;
  } finally {
    if (version === intake.version) {
      intake.loading = false;
      renderFeishuIntake();
      if (qs("#feishuIntakeDialog").open) qs("#feishuPreviewTitle")?.focus({ preventScroll: true });
      watchFeishuIntakeProcessing();
    }
  }
}

async function searchFeishuIntake(event) {
  event?.preventDefault();
  const intake = state.feishuIntake;
  if (intake.busy) return;
  const query = qs("#feishuIntakeQuery").value.trim();
  if (!query) { toast("Enter a paper title or a Feishu record reference."); return; }
  if (/^https?:\/\//i.test(query) || /^rec[A-Za-z0-9]+$/.test(query)) {
    await previewFeishuIntake(query);
    return;
  }
  const version = ++intake.version;
  Object.assign(intake, { loading: true, error: "", statusError: "", message: "", records: [], record: null, localPaper: null, hasMore: false });
  watchFeishuIntakeProcessing();
  renderFeishuIntake();
  try {
    const data = await api(`/api/feishu/search?${new URLSearchParams({ keyword: query })}`);
    if (version !== intake.version) return;
    Object.assign(intake, { records: data.records || [], hasMore: Boolean(data.has_more),
      message: data.records?.length ? "Select a record to preview; nothing has been imported." : "No title match. Try a shorter title or paste the record link." });
  } catch (error) {
    if (version === intake.version) intake.error = `Search unavailable: ${error.message}`;
  } finally {
    if (version === intake.version) { intake.loading = false; renderFeishuIntake(); }
  }
}

async function queueFeishuIntake() {
  const intake = state.feishuIntake;
  if (intake.busy || intake.loading || !intake.record || !intake.fileToken) return;
  if (feishuIntakePhase() !== "unparsed") {
    toast(feishuIntakePhase() === "ready" ? "Full text is already ready. Choose Read full text." : "This paper already has a parsing job. Check its status instead of queuing it again.");
    return;
  }
  const data = { record_id: intake.record.record_id, file_token: intake.fileToken, local_pdf_path: intake.localPath };
  intake.version += 1;
  Object.assign(intake, { busy: true, error: "", statusError: "", message: "" });
  renderFeishuIntakeActions();
  try {
    if (intake.localPaper?.id === state.currentPaperId) await flushCurrentPaperEdits();
    const result = await api("/api/feishu/intake", { method: "POST", body: JSON.stringify(data) });
    const paper = result.paper || { ...result.metadata, id: result.paper_id };
    const existing = state.library?.papers?.find(item => item.id === paper.id);
    if (existing) Object.assign(existing, paper);
    else state.library?.papers?.unshift(paper);
    applyFeishuMetadataResult(paper.id, result);
    const cached = state.paperSessions.get(paper.id);
    if (cached) cached.loadedAt = 0;
    intake.localPaper = paper;
    intake.message = result.metadata.processing_status === "ready" ? "Markdown is already ready. The local source was reused."
      : "Added to the parsing queue. You can select another paper while this one is prepared.";
    state.libraryDirty = true;
    renderPaperTabs();
    renderPaperSelect();
    if (document.body.dataset.activeView === "library") renderLibrary();
    toast(intake.message);
    if (state.processingQueue.open) refreshProcessingQueue();
  } catch (error) {
    console.error("Feishu intake failed", error);
    intake.error = `Could not prepare the paper: ${error.message}. Existing reading data is kept.`;
  } finally {
    intake.busy = false;
    renderFeishuIntakeActions();
    watchFeishuIntakeProcessing();
  }
}

async function retryFeishuIntakeParsing() {
  const intake = state.feishuIntake;
  if (intake.busy || intake.loading || feishuIntakePhase() !== "failed") return;
  intake.version += 1;
  Object.assign(intake, { busy: true, error: "", statusError: "" });
  renderFeishuIntakeActions();
  try {
    const result = await api("/api/processing-queue/retry", {
      method: "POST", body: JSON.stringify({ paper_id: intake.localPaper.id }),
    });
    Object.assign(intake.localPaper, result.metadata);
    const cached = state.paperSessions.get(intake.localPaper.id);
    if (cached) cached.loadedAt = 0;
  } catch (error) {
    console.error("Feishu parsing retry failed", error);
    intake.error = `Could not retry parsing: ${error.message}`;
  } finally {
    intake.busy = false;
    renderFeishuIntakeActions();
    watchFeishuIntakeProcessing();
  }
}

async function updateFeishuIntakeProcessing(snapshot, watched) {
  const intake = state.feishuIntake;
  const current = () => watched && watched.version === intake.version && watched.paperId === intake.localPaper?.id
    && feishuIntakeNeedsPolling();
  if (!current()) return;
  const job = snapshot.jobs?.find(item => item.paper_id === watched.paperId);
  let metadata;
  if (job) {
    const status = { queued: "processing_queued", processing: "processing", ready: "ready", failed: "failed" }[job.status];
    if (!status) throw new Error("The parsing queue returned an unknown status.");
    metadata = { processing_status: status, processing_mode: job.mode, processing_error: job.error || "" };
  } else {
    // Older or externally started jobs may be absent from this server's queue.
    const index = await api("/api/papers");
    metadata = index.papers?.find(paper => paper.id === watched.paperId);
    if (!metadata) throw new Error("The local paper is no longer indexed. Refresh its preview to check the association.");
  }
  if (!current()) return;
  const fields = Object.fromEntries(["processing_status", "processing_mode", "processing_error"]
    .filter(key => metadata[key] !== undefined).map(key => [key, metadata[key]]));
  const changed = Object.entries(fields).some(([key, value]) => intake.localPaper[key] !== value);
  Object.assign(intake.localPaper, fields);
  const paper = state.library?.papers?.find(item => item.id === watched.paperId);
  if (paper) Object.assign(paper, fields);
  if (changed) {
    state.libraryDirty = true;
    const cached = state.paperSessions.get(watched.paperId);
    if (cached) cached.loadedAt = 0;
  }
  if (changed || intake.statusError) {
    intake.statusError = "";
    renderFeishuIntakeActions();
  }
}

function renderFeishuMetadata() {
  const button = qs("#toggleFeishuMetadata");
  const root = qs("#feishuMetadataPanel");
  const indicator = qs("#feishuSyncStatus");
  const publishButton = qs("#publishReadingToFeishu");
  if (publishButton) publishButton.hidden = !state.feishuConfig.publication_enabled || !state.currentPaperId;
  if (!button || !root || !indicator) return;
  button.hidden = !state.feishuConfig.enabled || !state.currentPaperId;
  root.hidden = button.hidden || !state.feishuPanelOpen;
  if (button.hidden) { indicator.textContent = ""; return; }
  const sync = feishuPaperState(state.currentPaperId);
  const link = state.payload?.metadata?.feishu;
  indicator.textContent = sync.error ? `Feishu: ${sync.error}` : ({
    syncing: "Reading Feishu fields…", synced: "Metadata from Feishu",
    needs_match: "Feishu association needs confirmation",
  })[sync.status] || (link?.record_id ? "Using cached Feishu metadata" : "Not yet associated with Feishu");
  if (root.hidden) return;
  const cached = state.payload?.feishu_metadata || {};
  const sources = cached.field_sources || state.feishuConfig.fields || {};
  const values = cached.metadata || {};
  const query = sync.query ?? cleanPaperTitle(state.payload?.metadata?.title || "");
  root.innerHTML = `
    <div class="queue-heading"><strong>Feishu → local metadata</strong><button class="icon-button" data-close-feishu type="button" aria-label="Close Feishu metadata">×</button></div>
    <p class="muted small-text">Copy existing column values only. No re-analysis, no cloud writes, and no changes to source text or notes.</p>
    ${link?.record_id ? `<p><a href="${escapeHtml(link.url)}" target="_blank" rel="noreferrer">Open linked Feishu record</a><span class="muted small-text"> · ${escapeHtml(link.synced_at || "")}</span></p>` : ""}
    <div class="reader-data-actions">
      <button class="secondary-button mini-button" data-refresh-feishu type="button" ${sync.status === "syncing" ? "disabled" : ""}>${link?.record_id ? "Refresh mapped fields" : "Match exact title"}</button>
      ${!link?.record_id ? `<input id="feishuSearchKeyword" type="search" value="${escapeHtml(query)}" aria-label="Search Feishu paper title" placeholder="Feishu paper title" /><button class="secondary-button mini-button" data-search-feishu type="button">Search</button>` : ""}
    </div>
    ${sync.error ? `<p class="error-text" role="alert">${escapeHtml(sync.error)}</p>` : ""}
    ${sync.candidates.length && !link?.record_id ? `<ul class="feishu-candidates">${sync.candidates.map(item => `<li><span>${escapeHtml(item.title)}</span><button class="secondary-button mini-button" data-link-feishu="${escapeHtml(item.record_id)}" type="button">Use this record</button></li>`).join("")}</ul>` : ""}
    ${sync.status === "needs_match" && !sync.candidates.length ? '<p class="muted">No unique exact title match yet. Search manually or retry after Feishu finishes its fields.</p>' : ""}
    ${sync.local_overrides?.length ? `<p class="muted small-text">Local edits retained: ${escapeHtml(sync.local_overrides.join(", "))}</p>` : ""}
    ${link?.record_id ? `<dl class="metadata-info-list">${Object.entries(sources).map(([key, field]) => `<div class="metadata-info-row"><dt>${escapeHtml(field)} → ${escapeHtml(key)}</dt><dd>${escapeHtml(values[key] || "(empty — existing local value retained)")}</dd></div>`).join("")}</dl>` : ""}
    ${Object.entries(cached.briefings || {}).filter(([, text]) => text).map(([field, text]) => `<details class="feishu-brief"><summary>Feishu ${escapeHtml(field)} (read-only copy)</summary><pre>${escapeHtml(text)}</pre></details>`).join("")}`;
}

function publicationLink(url, label) {
  if (!url) return "";
  const safe = externalHttpUrl(url);
  return safe ? `<a href="${escapeHtml(safe)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>` : "";
}

function renderFeishuPublication() {
  const view = state.feishuPublication;
  const result = view.publication;
  const preview = view.preview;
  const tableMode = (preview?.mode || result?.mode) === "table";
  const active = view.sending || result?.status === "publishing";
  const messages = {
    idle: "Review the records and destination before publishing.",
    publishing: `Publishing${result?.phase ? ` · ${result.phase}` : ""}… You can close this window; publishing continues.`,
    synced: `${tableMode ? "Saved to the Feishu table" : "Published"}${result?.published_at ? ` · ${result.published_at}` : ""}`,
    pending: "The snapshot is published. Newer local edits still need another update.",
    failed: "Publication failed. Existing local records are safe.",
    conflict: "Publication stopped because the local or cloud version changed.",
    interrupted: "Publication was interrupted. Refresh the preview before resuming.",
    recovery_required: "The previous write needs verification before another publication.",
  };
  qs("#feishuPublishPaper").textContent = view.title;
  qs("#feishuPublishStatus").textContent = view.loading ? "Preparing a read-only preview…"
    : messages[result?.status] || (preview ? "Review the records and destination before publishing." : "");
  const error = view.error || result?.error || "";
  qs("#feishuPublishError").textContent = error;
  qs("#feishuPublishError").hidden = !error;
  const destination = preview?.destination;
  qs("#feishuPublishDestination").innerHTML = tableMode ? `
    <p>${publicationLink(result?.record_url || destination?.record_url, "Open paper in Feishu")}</p>
    ${destination ? `<p class="muted small-text">Columns: ${(destination.text_fields || []).map(field => escapeHtml(field.name)).join(" · ")}</p>
      <p class="muted small-text">Edit these records in the reader. Cloud copies are checked before each update.</p>` : ""}` : `
    ${destination ? `<p>${publicationLink(destination.record_url, "Feishu paper record")}</p>
      <p class="muted small-text">Writes only ${escapeHtml(destination.archive_field?.name || "")} and ${escapeHtml(destination.backup_field?.name || "")}. Your existing analysis and manual fields stay unchanged.</p>` : ""}
    ${publicationLink(result?.document_url || destination?.document_url, "Open reading archive")}`;
  const root = qs("#feishuPublishPreview");
  const previewId = preview?.preview_id || "";
  if (root.dataset.previewId !== previewId) {
    root.dataset.previewId = previewId;
    root.innerHTML = preview ? `
      <p class="muted small-text">Original notes, recorded discussions and accepted definitions. No new AI summary.</p>
      ${(preview.warnings || []).map(warning => `<p class="error-text">${escapeHtml(warning)}</p>`).join("")}
      ${tableMode ? (preview.columns || []).map(column => `<details class="feishu-publish-section" data-publication-column="${escapeHtml(column.id)}">
        <summary>${escapeHtml(column.name)} <span class="muted">${escapeHtml(column.characters)} / ${escapeHtml(column.limit)} characters</span></summary>
        ${column.text ? '<pre class="feishu-publish-cell"></pre>' : '<p class="muted small-text">Empty — clears this reader-managed column.</p>'}
      </details>`).join("") : (preview.sections || []).map(section => `<details class="feishu-publish-section">
        <summary>${escapeHtml(section.title)} <span class="muted">${section.entries.length}</span></summary>
        ${section.entries.map(entry => `<article class="feishu-publish-entry">
          <h3>${escapeHtml(entry.label || entry.id)}</h3>
          ${entry.source ? `<p class="muted small-text">${escapeHtml(entry.source)}</p>` : ""}
          ${entry.quote ? `<blockquote>${escapeHtml(entry.quote)}</blockquote>` : ""}
          ${entry.text ? `<pre>${escapeHtml(entry.text)}</pre>` : ""}
        </article>`).join("")}
      </details>`).join("")}
      <p class="muted small-text">JSON backup${tableMode && destination?.backup_field?.name ? ` · ${escapeHtml(destination.backup_field.name)}` : ""} · ${Math.ceil((preview.snapshot_bytes || 0) / 1024)} KB. Includes stored reading data; excludes PDF/image files, credentials and unrelated project files. Existing backup versions are kept.</p>` : "";
    if (tableMode && preview) {
      root.querySelectorAll("[data-publication-column]").forEach((section, index) => {
        const cell = section.querySelector(".feishu-publish-cell");
        if (cell) cell.textContent = preview.columns[index].text;
      });
    }
  }
  const alreadyPublished = ["synced", "pending"].includes(result?.status) && result.preview_id === preview?.preview_id;
  const confirm = qs("#confirmFeishuPublish");
  const retry = ["failed", "conflict", "interrupted", "recovery_required"].includes(result?.status);
  const needsFreshPreview = retry && result.preview_id === preview?.preview_id;
  confirm.disabled = view.loading || active || needsFreshPreview || !preview || Boolean(view.error) || alreadyPublished || preview.changed === false;
  confirm.textContent = active ? "Publishing…" : alreadyPublished && result?.status === "pending" ? "Refresh preview for newer edits"
    : alreadyPublished || preview?.changed === false ? "No changes to publish"
    : needsFreshPreview ? "Refresh preview before retrying"
    : retry ? "Retry this publication" : "Confirm & publish";
  qs("#refreshFeishuPublish").disabled = view.loading || (active && !view.error);
}

function cancelPublicationPolling() {
  const view = state.feishuPublication;
  if (view.timer) clearTimeout(view.timer);
  view.timer = null;
}

function publicationViewIsCurrent(version, paperId) {
  return qs("#feishuPublishDialog")?.open && state.feishuPublication.version === version
    && state.feishuPublication.paperId === paperId;
}

async function refreshFeishuPublicationStatus(version, paperId) {
  if (!publicationViewIsCurrent(version, paperId)) return;
  cancelPublicationPolling();
  try {
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/feishu-publication`);
    if (!publicationViewIsCurrent(version, paperId)) return;
    state.feishuPublication.publication = response.publication;
    state.feishuPublication.error = "";
    renderFeishuPublication();
    if (response.publication.status === "publishing") {
      state.feishuPublication.timer = setTimeout(() => refreshFeishuPublicationStatus(version, paperId), 1200);
    }
  } catch (error) {
    if (!publicationViewIsCurrent(version, paperId)) return;
    state.feishuPublication.error = `Status unavailable: ${error.message}. Publishing may still be running; close and reopen to check.`;
    renderFeishuPublication();
  }
}

async function openFeishuPublication() {
  const paperId = state.currentPaperId;
  if (!paperId || !state.feishuConfig.publication_enabled) {
    toast("Configure the Feishu paper library before publishing.");
    return;
  }
  cancelPublicationPolling();
  const view = state.feishuPublication;
  const version = ++view.version;
  Object.assign(view, { paperId, title: state.payload?.metadata?.title || paperId, loading: true, sending: false,
    preview: null, publication: null, error: "" });
  qs("#readerMoreActions").open = false;
  if (!qs("#feishuPublishDialog").open) qs("#feishuPublishDialog").showModal();
  renderFeishuPublication();
  try {
    if (state.currentPaperId !== paperId) throw new Error("The active paper changed. Reopen publication for the intended paper.");
    const status = await api(`/api/papers/${encodeURIComponent(paperId)}/feishu-publication`);
    if (!publicationViewIsCurrent(version, paperId)) return;
    view.publication = status.publication;
    if (status.publication.status === "publishing") {
      view.timer = setTimeout(() => refreshFeishuPublicationStatus(version, paperId), 1200);
      return;
    }
    if (hasThinkingComposerDraft()) throw new Error("Finish or copy and clear the unsubmitted chat/paste draft first. Drafts are not saved reading records.");
    await flushCurrentPaperEdits();
    if (!publicationViewIsCurrent(version, paperId)) return;
    if (state.currentPaperId !== paperId) throw new Error("The active paper changed. Reopen the preview.");
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/feishu-publication/preview`, {
      method: "POST", body: "{}",
    });
    if (!publicationViewIsCurrent(version, paperId)) return;
    view.preview = response.preview;
  } catch (error) {
    if (publicationViewIsCurrent(version, paperId)) view.error = error.message;
  } finally {
    if (publicationViewIsCurrent(version, paperId)) {
      view.loading = false;
      renderFeishuPublication();
    }
  }
}

async function confirmFeishuPublication() {
  const view = state.feishuPublication;
  if (!view.preview || view.loading || view.sending || view.publication?.status === "publishing") return;
  const { version, paperId, preview } = view;
  view.sending = true;
  view.error = "";
  renderFeishuPublication();
  try {
    if (paperId !== state.currentPaperId) throw new Error("The active paper changed. Reopen the preview.");
    if (hasThinkingComposerDraft()) throw new Error("Finish or copy and clear the unsubmitted draft before publishing.");
    await flushCurrentPaperEdits();
    if (!publicationViewIsCurrent(version, paperId)) return;
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/feishu-publication/publish`, {
      method: "POST", body: JSON.stringify({ preview_id: preview.preview_id, confirm: true }),
    });
    if (!publicationViewIsCurrent(version, paperId)) return;
    view.publication = response.publication;
    if (response.publication.status === "publishing") {
      view.timer = setTimeout(() => refreshFeishuPublicationStatus(version, paperId), 1200);
    }
  } catch (error) {
    if (publicationViewIsCurrent(version, paperId)) view.error = `${error.message} Refresh the preview before retrying.`;
  } finally {
    if (publicationViewIsCurrent(version, paperId)) {
      view.sending = false;
      renderFeishuPublication();
    }
  }
}

async function syncFeishuPaper(paperId = state.currentPaperId, options = {}) {
  if (!paperId || !state.feishuConfig.enabled) return;
  const sync = feishuPaperState(paperId);
  if (sync.status === "syncing") return;
  if (options.automatic && (state.metadataDrafts.has(paperId)
    || state.workspaceMetadataEditor.open && state.workspaceMetadataEditor.paperId === paperId)) return;
  Object.assign(sync, { status: "syncing", error: "", lastAttempt: Date.now() });
  renderFeishuMetadata();
  try {
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/feishu-sync`, {
      method: "POST", body: JSON.stringify(options),
    });
    Object.assign(sync, { status: response.status, candidates: response.candidates || [], local_overrides: response.local_overrides || [] });
    applyFeishuMetadataResult(paperId, response);
  } catch (error) {
    console.error(`Feishu metadata sync failed for ${paperId}`, error);
    Object.assign(sync, { status: "failed", error: error.message });
    if (!options.automatic) toast(`Feishu metadata unchanged: ${error.message}`);
  } finally {
    if (paperId === state.currentPaperId) renderFeishuMetadata();
  }
}

function watchFeishuMetadata() {
  clearTimeout(state.feishuPollTimer);
  renderFeishuMetadata();
  if (!state.feishuConfig.enabled || !state.feishuConfig.auto_sync
    || !state.currentPaperId || document.body.dataset.activeView !== "reader") return;
  const paperId = state.currentPaperId;
  const poll = async () => {
    if (state.currentPaperId !== paperId || document.body.dataset.activeView !== "reader") return;
    const sync = feishuPaperState(paperId);
    if (Date.now() - sync.lastAttempt >= 60000) await syncFeishuPaper(paperId, { automatic: true });
    if (state.currentPaperId === paperId && document.body.dataset.activeView === "reader") state.feishuPollTimer = setTimeout(poll, 60000);
  };
  state.feishuPollTimer = setTimeout(poll, 0);
}

async function searchFeishuPapers() {
  if (!state.currentPaperId) return;
  const paperId = state.currentPaperId;
  const sync = feishuPaperState(paperId);
  const keyword = qs("#feishuSearchKeyword")?.value || "";
  sync.query = keyword;
  try {
    const response = await api(`/api/feishu/search?${new URLSearchParams({ keyword })}`);
    Object.assign(sync, { candidates: response.records || [], status: "needs_match", error: response.has_more ? "More matches exist. Use a more specific title." : "" });
  } catch (error) {
    console.error("Feishu search failed", error);
    Object.assign(sync, { status: "failed", error: error.message });
  }
  if (state.currentPaperId === paperId) renderFeishuMetadata();
}

function openWorkspaceMetadataEditor() {
  if (!state.currentPaperId) return;
  const paper = workspaceMetadataPaper();
  state.workspaceMetadataEditor = {
    open: true,
    saving: false,
    paperId: state.currentPaperId,
    projects: paperProjects(paper),
    tags: normalizeTagsInput(paper.tags || []),
    importance: paperImportanceLevel(paper),
  };
  renderWorkspaceMetadataPanel();
}

function closeWorkspaceMetadataEditor() {
  state.workspaceMetadataEditor = { open: false, saving: false, paperId: "", projects: [], tags: [], importance: 0 };
  renderWorkspaceMetadataPanel();
}

function toggleWorkspaceMetadataEditor() {
  if (state.workspaceMetadataEditor.open) closeWorkspaceMetadataEditor();
  else openWorkspaceMetadataEditor();
}

function renderWorkspaceMetadataPanel() {
  const root = qs("#workspaceMetadataPanel");
  if (!root) return;
  const editor = state.workspaceMetadataEditor;
  const visible = Boolean(editor.open && state.currentPaperId && editor.paperId === state.currentPaperId);
  root.hidden = !visible;
  root.classList.toggle("open", visible);
  root.setAttribute("aria-hidden", visible ? "false" : "true");
  if (!visible) {
    root.innerHTML = "";
    return;
  }
  const selectedProjects = uniqueTags((editor.projects || []).map(normalizeProjectName)).filter(Boolean);
  const selectedTags = uniqueTags(editor.tags || []);
  const projectSet = new Set(selectedProjects);
  const tagSet = new Set(selectedTags);
  const projectColors = projectColorMap();
  const tagColors = tagColorMap();
  const projectOptions = allLibraryProjects();
  const tagOptions = allLibraryTags(selectedTags).filter(tag => tagSet.has(tag) || !String(tag).startsWith("__"));
  root.innerHTML = `
    <div class="metadata-panel-header">
      <div>
        <span class="sense-kicker">Paper metadata</span>
        <strong>${escapeHtml(compactText(paperTitle(workspaceMetadataPaper()) || "Current paper", 78))}</strong>
      </div>
      <button class="icon-button" data-close-workspace-metadata type="button" title="Close metadata editor" aria-label="Close metadata editor">x</button>
    </div>
    ${workspaceMetadataInfoHtml(workspaceMetadataPaper())}
    <section class="metadata-picker metadata-importance-picker" aria-label="Paper importance">
      <div class="library-intake-picker-header"><span>Importance</span><button class="secondary-button mini-button" data-clear-workspace-importance type="button">Clear</button></div>
      ${quickImportanceEditorHtml(editor.importance, "data-set-workspace-importance")}
    </section>
    <section class="metadata-picker" aria-label="Paper project">
      <div class="library-intake-picker-header"><span>Project tag</span><button class="secondary-button mini-button" data-clear-workspace-projects type="button">Clear</button></div>
      <div class="library-tags library-intake-selected" aria-label="Selected paper projects">
        ${selectedProjects.map(project => `<button class="library-tag library-project-tag" style="--tag-color: ${escapeHtml(projectColor(project, projectColors))}" data-remove-workspace-project="${escapeHtml(project)}" type="button">${escapeHtml(project)} ×</button>`).join("") || '<span class="muted small-text">No project selected</span>'}
      </div>
      <div class="library-intake-option-panel" data-filter-tag-scope>
        ${tagMenuSearchHtml("Search projects")}
        <div class="library-intake-option-list">
          ${projectOptions.map(project => `<button class="library-tag-option ${projectSet.has(project) ? "active" : ""}" style="--tag-color: ${escapeHtml(projectColor(project, projectColors))}" data-toggle-workspace-project="${escapeHtml(project)}" ${filterableTagOptionAttrs(project)} type="button"><span></span>${escapeHtml(project)}</button>`).join("") || '<span class="muted small-text">No existing projects</span>'}
          <span class="muted small-text" data-filter-empty hidden>No matching projects</span>
        </div>
      </div>
      <div class="library-intake-custom-row">
        <input id="workspaceMetadataProjectCustom" type="text" placeholder="New project" />
        <button class="secondary-button mini-button" data-add-workspace-project type="button">Add</button>
      </div>
    </section>
    <section class="metadata-picker" aria-label="Paper tags">
      <div class="library-intake-picker-header"><span>Paper tag</span><button class="secondary-button mini-button" data-clear-workspace-tags type="button">Clear</button></div>
      <div class="library-tags library-intake-selected" aria-label="Selected paper tags">
        ${selectedTags.map(tag => `<button class="library-tag" style="--tag-color: ${escapeHtml(tagColor(tag, tagColors))}" data-remove-workspace-tag="${escapeHtml(tag)}" title="${escapeHtml(tag)}" type="button">${escapeHtml(libraryTagLabel(tag))} ×</button>`).join("") || '<span class="muted small-text">No paper tag selected</span>'}
      </div>
      <div class="library-intake-option-panel" data-filter-tag-scope>
        ${tagMenuSearchHtml("Search paper tags")}
        <div class="library-intake-option-list">
          ${tagOptions.map(tag => `<button class="library-tag-option ${tagSet.has(tag) ? "active" : ""}" style="--tag-color: ${escapeHtml(tagColor(tag, tagColors))}" data-toggle-workspace-tag="${escapeHtml(tag)}" ${filterableTagOptionAttrs(`${tag} ${libraryTagLabel(tag)}`)} type="button"><span></span>${escapeHtml(libraryTagLabel(tag))}</button>`).join("") || '<span class="muted small-text">No existing tags</span>'}
          <span class="muted small-text" data-filter-empty hidden>No matching tags</span>
        </div>
      </div>
      <div class="library-intake-custom-row">
        <input id="workspaceMetadataTagCustom" type="text" placeholder="New tag or alias" />
        <button class="secondary-button mini-button" data-add-workspace-tag type="button">Add</button>
      </div>
    </section>
    <div class="metadata-panel-actions">
      <button class="secondary-button" data-close-workspace-metadata type="button">Cancel</button>
      <button class="primary-button" data-save-workspace-metadata type="button" ${editor.saving ? "disabled" : ""}>${editor.saving ? "Saving..." : "Save metadata"}</button>
    </div>`;
  initTagOptionFilters(root);
}

function addWorkspaceProjectFromInput() {
  const input = qs("#workspaceMetadataProjectCustom");
  const value = normalizeProjectName(input?.value || "");
  if (!value) return;
  state.workspaceMetadataEditor.projects = uniqueTags([...(state.workspaceMetadataEditor.projects || []), value]);
  if (!allLibraryProjects().includes(value)) {
    state.libraryCustomProjects = uniqueTags([...state.libraryCustomProjects, value]);
    saveCustomLibraryProjects();
  }
  if (input) input.value = "";
  renderWorkspaceMetadataPanel();
}

function addWorkspaceTagFromInput() {
  const input = qs("#workspaceMetadataTagCustom");
  const values = canonicalTagIdsForInput(input?.value || "");
  if (!values.length) return;
  state.workspaceMetadataEditor.tags = uniqueTags([...(state.workspaceMetadataEditor.tags || []), ...values]);
  if (input) input.value = "";
  renderWorkspaceMetadataPanel();
}

function handleWorkspaceMetadataClick(event) {
  const target = event.target;
  if (!target?.closest?.("#workspaceMetadataPanel")) return;
  if (target.closest("[data-close-workspace-metadata]")) {
    event.preventDefault();
    closeWorkspaceMetadataEditor();
    return;
  }
  const importanceButton = target.closest("[data-set-workspace-importance]");
  if (importanceButton) {
    event.preventDefault();
    const clickedLevel = normalizeImportanceLevel(importanceButton.dataset.setWorkspaceImportance);
    const currentLevel = normalizeImportanceLevel(state.workspaceMetadataEditor.importance);
    state.workspaceMetadataEditor.importance = clickedLevel === currentLevel ? 0 : clickedLevel;
    renderWorkspaceMetadataPanel();
    return;
  }
  const projectToggle = target.closest("[data-toggle-workspace-project]");
  if (projectToggle) {
    event.preventDefault();
    const value = normalizeProjectName(projectToggle.dataset.toggleWorkspaceProject || "");
    const selected = new Set(state.workspaceMetadataEditor.projects || []);
    if (selected.has(value)) selected.delete(value);
    else if (value) selected.add(value);
    state.workspaceMetadataEditor.projects = Array.from(selected);
    renderWorkspaceMetadataPanel();
    return;
  }
  const tagToggle = target.closest("[data-toggle-workspace-tag]");
  if (tagToggle) {
    event.preventDefault();
    const value = tagToggle.dataset.toggleWorkspaceTag || "";
    const selected = new Set(state.workspaceMetadataEditor.tags || []);
    if (selected.has(value)) selected.delete(value);
    else if (value) selected.add(value);
    state.workspaceMetadataEditor.tags = Array.from(selected);
    renderWorkspaceMetadataPanel();
    return;
  }
  const removeProject = target.closest("[data-remove-workspace-project]");
  if (removeProject) {
    event.preventDefault();
    state.workspaceMetadataEditor.projects = (state.workspaceMetadataEditor.projects || []).filter(project => project !== removeProject.dataset.removeWorkspaceProject);
    renderWorkspaceMetadataPanel();
    return;
  }
  const removeTag = target.closest("[data-remove-workspace-tag]");
  if (removeTag) {
    event.preventDefault();
    state.workspaceMetadataEditor.tags = (state.workspaceMetadataEditor.tags || []).filter(tag => tag !== removeTag.dataset.removeWorkspaceTag);
    renderWorkspaceMetadataPanel();
    return;
  }
  if (target.closest("[data-clear-workspace-projects]")) {
    event.preventDefault();
    state.workspaceMetadataEditor.projects = [];
    renderWorkspaceMetadataPanel();
    return;
  }
  if (target.closest("[data-clear-workspace-tags]")) {
    event.preventDefault();
    state.workspaceMetadataEditor.tags = [];
    renderWorkspaceMetadataPanel();
    return;
  }
  if (target.closest("[data-clear-workspace-importance]")) {
    event.preventDefault();
    state.workspaceMetadataEditor.importance = 0;
    renderWorkspaceMetadataPanel();
    return;
  }
  if (target.closest("[data-add-workspace-project]")) {
    event.preventDefault();
    addWorkspaceProjectFromInput();
    return;
  }
  if (target.closest("[data-add-workspace-tag]")) {
    event.preventDefault();
    addWorkspaceTagFromInput();
    return;
  }
  if (target.closest("[data-save-workspace-metadata]")) {
    event.preventDefault();
    saveWorkspaceMetadataSelection().catch(error => toast(`Metadata save failed: ${error.message}`));
  }
}

async function saveWorkspaceMetadataSelection() {
  const editor = state.workspaceMetadataEditor;
  const paperId = editor.paperId || state.currentPaperId;
  if (!paperId || editor.saving) return;
  const projects = uniqueTags((editor.projects || []).map(normalizeProjectName)).filter(Boolean);
  const tags = uniqueTags(editor.tags || []);
  const tagColors = tagColorsForPaper(paperId);
  tags.forEach(tag => { if (!tagColors[tag]) tagColors[tag] = tagColor(tag, tagColors); });
  const projectColors = projectColorsForPaper(paperId);
  projects.forEach(project => { if (!projectColors[project]) projectColors[project] = projectColor(project, projectColors); });
  const body = {
    tags,
    tag_colors: tagColors,
    projects,
    project: projects[0] || "",
    project_colors: projectColors,
    ...importanceFieldsForLevel(editor.importance),
  };
  editor.saving = true;
  renderWorkspaceMetadataPanel();
  try {
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/metadata`, { method: "POST", body: JSON.stringify(body) });
    const metadata = response.metadata || body;
    const paper = state.library?.papers?.find(item => item.id === paperId);
    if (paper) Object.assign(paper, metadata);
    if (state.currentPaperId === paperId && state.payload?.metadata) Object.assign(state.payload.metadata, metadata);
    toast("Metadata saved");
    closeWorkspaceMetadataEditor();
    renderPaperMeta();
  } finally {
    editor.saving = false;
    if (state.workspaceMetadataEditor === editor) renderWorkspaceMetadataPanel();
  }
}

function updateAnnotationToolbarVisibility() {
  const toolbar = qs("#annotationToolbar");
  if (!toolbar) return;
  const paragraphs = state.payload?.segments || [];
  const mode = processingMode(state.payload?.metadata || {});
  const showForPaper = mode === "deep" && paragraphs.length && state.workspaceMode !== "think";
  const showForWriting = Boolean(state.payload && state.workspaceMode !== "read");
  if (!showForPaper && !showForWriting) toolbar.style.display = "none";
}

function selectedRangeRect() {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0 || !selection.toString().trim()) return null;
  const rects = Array.from(selection.getRangeAt(0).getClientRects()).filter(rect => rect.width || rect.height);
  return rects[0] || selection.getRangeAt(0).getBoundingClientRect();
}

function positionAnnotationToolbar() {
  const toolbar = qs("#annotationToolbar");
  if (!toolbar || !state.currentSelection) {
    if (toolbar) toolbar.style.display = "none";
    return;
  }
  const rect = selectedRangeRect();
  if (!rect) {
    toolbar.style.display = "none";
    return;
  }
  toolbar.style.display = "flex";
  const width = toolbar.offsetWidth || 420;
  const left = Math.max(12, Math.min(window.innerWidth - width - 12, rect.left + rect.width / 2 - width / 2));
  const top = Math.max(12, rect.top - toolbar.offsetHeight - 10);
  toolbar.style.left = `${left}px`;
  toolbar.style.top = `${top}px`;
}

function preferredDrawerPoint() {
  if (state.lastPointerPosition) return state.lastPointerPosition;
  const rect = selectedRangeRect();
  if (rect) return { x: rect.right + 12, y: rect.top };
  return { x: window.innerWidth - 450, y: 82 };
}

function positionNoteDrawer(point = preferredDrawerPoint()) {
  const drawer = qs("#noteDrawer");
  if (!drawer) return;
  const minTop = Math.min(readerViewportTop() + 8, Math.max(12, window.innerHeight - 180));
  drawer.style.maxHeight = `calc(100vh - ${minTop + 12}px)`;
  const width = drawer.offsetWidth || 420;
  const height = Math.min(drawer.offsetHeight || 520, window.innerHeight - 24);
  let left = Number(point?.x ?? window.innerWidth - width - 18) + 12;
  let top = Number(point?.y ?? 82) + 12;
  if (left + width > window.innerWidth - 12) left = Math.max(12, Number(point?.x ?? 0) - width - 12);
  if (top + height > window.innerHeight - 12) top = Math.max(12, window.innerHeight - height - 12);
  drawer.style.left = `${Math.max(12, left)}px`;
  drawer.style.top = `${Math.max(minTop, top)}px`;
}

function refreshDrawerMode() {
  const isEditingPaperNote = Boolean(state.pendingAnnotation?.editing_id);
  const isEditingThinkingNote = Boolean(state.pendingThinkingAnnotation?.editing_id);
  const isEditing = isEditingPaperNote || isEditingThinkingNote;
  const title = qs("#noteDrawer .drawer-header strong");
  if (title) title.textContent = isEditing ? "Edit Note" : "Add Note";
  const deleteButton = qs("#deleteDrawerNote");
  if (!deleteButton) return;
  deleteButton.hidden = !isEditing;
  deleteButton.dataset.noteScope = isEditingThinkingNote ? "thinking" : "paper";
  deleteButton.dataset.annotationId = isEditingThinkingNote ? state.pendingThinkingAnnotation.editing_id : (state.pendingAnnotation?.editing_id || "");
}

function openNoteDrawerAtPointer() {
  const drawer = qs("#noteDrawer");
  if (!drawer) return;
  state.drawerInitialValue = noteDrawerSnapshot();
  refreshDrawerMode();
  drawer.classList.add("open");
  drawer.setAttribute("aria-hidden", "false");
  positionNoteDrawer();
  qs("#noteText")?.focus();
}

function paragraphHtml(paragraph) {
  const pid = paragraph.id;
  const type = paragraph.kind || "paragraph";
  const text = paragraph.markdown || "";
  const readingProgress = readingProgressForSegment(pid);
  const visibleText = displayTextPreservingMath(text, { trim: false });
  const isTableSegment = isTextTableSegment(paragraph);
  let body = "";
  if (type === "heading") {
    const level = Math.min(Math.max(Number(paragraph.level || 2), 1), 3);
    const headingText = cleanPaperTitle(visibleText.replace(/^#{1,6}\s+/, ""));
    body = `<h${level}>${inlineMarkdown(headingText)}</h${level}>`;
  } else if (type === "code") {
    body = `<pre><code>${escapeHtml(text)}</code></pre>`;
  } else if (isHtmlTable(text)) {
    body = mediaAnnotationToolbarHtml(paragraph, "table", renderHtmlTable(text));
  } else if (isTableSegment) {
    body = mediaAnnotationToolbarHtml(paragraph, "table", renderPipeTable(text));
  } else if (/!\[[^\]]*\]\([^)]+\)/.test(text)) {
    body = `<div class="source-text annotation-text" data-pid="${pid}" data-target="source">${wrapMediaImageButtons(paragraph, applyHighlights(visibleText, pid, "source"))}</div>`;
  } else {
    body = `<div class="source-text annotation-text" data-pid="${pid}" data-target="source">${applyHighlights(visibleText, pid, "source")}</div>`;
  }
  const translated = isTableSegment ? null : translationPresentation(paragraph);
  const translation = isTableSegment
    ? renderTableTranslation(paragraph)
    : stripTranslationImages(translated.text).trim()
      ? `<div class="translation annotation-text" data-pid="${pid}" data-target="translation">${applyHighlights(displayTextPreservingMath(paragraph.translation, { trim: false }), pid, "translation", { omissions: translated.omissions })}</div>`
      : "";
  const notes = marginCardsHtml(pid);
  const repeatsTitle = type === "heading" && state.payload?.segments?.[0]?.id === pid
    && !getAnnotationsFor(pid).length
    && cleanPaperTitle(visibleText.replace(/^#{1,6}\s+/, "")).toLocaleLowerCase() === paperTitle(state.payload?.metadata || {}).toLocaleLowerCase();
  return `<article class="paragraph${notes ? " has-comments" : ""}${repeatsTitle ? " paper-title-repeat" : ""}" id="${pid}" data-pid="${pid}" data-reading-state="${escapeHtml(readingProgress.state)}" style="--reading-depth: ${readingProgress.depth || 0}">${body}${translation}${notes}</article>`;
}

function annotationCardsHtml(paragraphId) {
  const items = getAnnotationsFor(paragraphId)
    .map(item => ({ item, noteText: annotationNoteCardText(item) }))
    .filter(entry => entry.noteText || isTeacherDefinition(entry.item));
  if (!items.length) return "";
  return items.map(({ item, noteText }) => {
    if (isTeacherDefinition(item)) return savedDefinitionCardHtml(item);
    const long = noteText.length > 320 || noteText.split("\n").length > 6;
    const expanded = state.expandedMarginNotes.has(item.id);
    const aiDefinition = isTeacherDefinition(item);
    return `<section class="comment-card${long && !expanded ? " is-collapsed" : ""}" data-note-origin="${aiDefinition ? "reading-teacher" : "user"}" aria-label="${aiDefinition ? "Saved AI definition" : "My note"}">
      <header class="margin-card-header">
        <button class="comment-jump" type="button" data-jump-annotation="${escapeHtml(item.id || "")}" title="${aiDefinition ? "Saved AI definition" : "My note"} · ${escapeHtml(annotationKindLabel(item))}" aria-label="Jump to highlighted text">
          <span class="comment-color swatch-${escapeHtml(item.color || "yellow")}" aria-hidden="true"></span>
        </button>
        <button class="comment-edit" type="button" data-edit-annotation="${escapeHtml(item.id || "")}" title="Edit note">Edit</button>
        <button class="comment-delete" type="button" data-delete-annotation="${escapeHtml(item.id || "")}" data-paper-id="${escapeHtml(state.currentPaperId || "")}" title="Delete note" aria-label="Delete note">×</button>
      </header>
      <div class="comment-text" id="margin-note-${escapeHtml(item.id)}">${escapeHtml(noteText)}</div>
      ${long ? `<button class="margin-note-expand" type="button" data-expand-annotation="${escapeHtml(item.id)}" aria-expanded="${expanded}" aria-controls="margin-note-${escapeHtml(item.id)}">${expanded ? "Show less" : "Read full note"}</button>` : ""}
      ${annotationTags(item).length ? `<div class="comment-tags">${annotationTags(item).map(tag => `<span>${escapeHtml(tag)}</span>`).join("")}</div>` : ""}
    </section>`;
  }).join("");
}

function savedDefinitionView(annotation) {
  const origin = annotation.origin;
  const sources = Array.isArray(origin.sources) ? origin.sources : [];
  const title = (typeof origin.title === "string" && origin.title) || String(annotation.note || "").split(/\r?\n/)[0] || "Definition";
  const card = { id: origin.card_id, title, definition: origin.definition,
    anchor: origin.anchor || { segment_id: annotation.segment_id, quote: annotation.quote } };
  const complete = typeof card.definition?.paper === "string" && Array.isArray(card.definition.external)
    && card.definition.external.length > 0 && card.definition.external.every(item =>
      typeof item?.summary === "string" && (item.kind === "ai-summary"
        || sources.some(source => source?.id === item.source_id && typeof source.title === "string"
          && typeof source.url === "string" && typeof source.accessed_at === "string")));
  if (!complete) console.warn("Saved definition has incomplete provenance; showing its saved text.", annotation.id);
  const initial = complete ? (origin.initial_note ?? teacherDefinitionNote(card, { sources })) : null;
  return { card, sources, pristine: complete && annotation.note === initial };
}

function savedDefinitionSaveState(annotation) {
  const write = state.paperSessions.get(state.currentPaperId)?.writes.get("annotations");
  if (state.readingTeacher.saving.has(annotation.origin.card_id) || write?.pending) return "saving";
  return write?.dirty ? "retry" : "saved";
}

function savedDefinitionActionsHtml(annotation) {
  const status = savedDefinitionSaveState(annotation);
  const saving = status === "saving";
  return `<span class="definition-save-state" role="status">${saving ? "Saving…" : status === "retry" ? "Not saved" : "✓ Saved"}</span>
    ${status === "retry"
      ? `<button class="secondary-button mini-button" type="button" data-retry-definition-save="${escapeHtml(annotation.id)}">Retry save</button>`
      : `<button class="secondary-button mini-button" type="button" data-edit-annotation="${escapeHtml(annotation.id)}"${saving ? " disabled" : ""}>Edit</button>`}`;
}

function refreshSavedDefinitionStatuses() {
  qsa("#documentRoot [data-definition-actions]").forEach(footer => {
    const annotation = state.annotations.find(item => item.id === footer.dataset.definitionActions);
    if (!annotation) return;
    const status = savedDefinitionSaveState(annotation);
    if (footer.dataset.saveState === status) return;
    footer.dataset.saveState = status;
    footer.innerHTML = savedDefinitionActionsHtml(annotation);
    bindReaderDynamicEvents(footer);
  });
  qsa("#documentRoot [data-definition-status]").forEach(mark => {
    const annotation = state.annotations.find(item => item.id === mark.dataset.definitionStatus);
    if (!annotation) return;
    const status = savedDefinitionSaveState(annotation);
    mark.textContent = status === "saving" ? "…" : status === "retry" ? "!" : "✓";
    mark.title = status === "saving" ? "Saving" : status === "retry" ? "Not saved" : "Saved";
  });
}

function savedDefinitionCardHtml(annotation) {
  const { card, sources, pristine } = savedDefinitionView(annotation);
  const id = escapeHtml(annotation.id);
  const status = savedDefinitionSaveState(annotation);
  if (state.collapsedDefinitionNotes.has(annotation.id)) {
    return `<button class="teacher-marker saved-definition-marker" type="button" data-open-definition-note="${id}" aria-expanded="false" aria-label="Open saved definition: ${escapeHtml(card.title)}">
      <span data-definition-status="${id}" aria-hidden="true">${status === "saving" ? "…" : status === "retry" ? "!" : "✓"}</span> ${escapeHtml(card.title)}</button>`;
  }
  const note = String(annotation.note || "");
  const long = !pristine && (note.length > 320 || note.split("\n").length > 6);
  const expanded = state.expandedMarginNotes.has(annotation.id);
  return `<section class="comment-card saved-definition-card${long && !expanded ? " is-collapsed" : ""}" id="saved-definition-${id}" data-saved-definition="${id}" data-note-origin="reading-teacher" tabindex="-1" aria-label="Saved AI definition: ${escapeHtml(card.title)}">
    <header class="margin-card-header">${pristine ? `<h3>${escapeHtml(card.title)}</h3>` : '<span class="comment-color swatch-blue" aria-hidden="true"></span>'}
      <button class="teacher-close" type="button" data-close-definition-note="${id}" title="Collapse definition" aria-label="Collapse saved definition">×</button></header>
    ${pristine ? teacherDefinitionHtml(card, { sources, annotationId: annotation.id })
      : `<div class="comment-text" id="margin-note-${id}">${escapeHtml(note)}</div>`}
    ${long ? `<button class="margin-note-expand" type="button" data-expand-annotation="${id}" aria-expanded="${expanded}" aria-controls="margin-note-${id}">${expanded ? "Show less" : "Read full note"}</button>` : ""}
    <footer class="teacher-actions" data-definition-actions="${id}" data-save-state="${status}">${savedDefinitionActionsHtml(annotation)}</footer>
  </section>`;
}

function toggleSavedDefinitionNote(annotationId, open) {
  const annotation = state.annotations.find(item => item.id === annotationId && isTeacherDefinition(item));
  if (!annotation) { toast("This saved definition is no longer available."); return; }
  if (open) state.collapsedDefinitionNotes.delete(annotationId);
  else state.collapsedDefinitionNotes.add(annotationId);
  refreshTeacherMargins([annotation.segment_id]);
  const target = open ? document.getElementById(`saved-definition-${annotationId}`)
    : document.querySelector(`[data-open-definition-note="${cssEscape(annotationId)}"]`);
  target?.focus({ preventScroll: true });
}

async function retrySavedDefinitionNote(annotationId) {
  const annotation = state.annotations.find(item => item.id === annotationId && isTeacherDefinition(item));
  if (!annotation) { toast("This saved definition is no longer available."); return; }
  const paperId = state.currentPaperId;
  const teacher = state.readingTeacher;
  const cardId = annotation.origin.card_id;
  if (teacher.saving.has(cardId)) return;
  teacher.saving.add(cardId);
  try {
    await persistCurrentPaperAnnotations("", { segmentIds: [annotation.segment_id] });
  } catch (error) {
    console.error("Could not save the accepted definition", error);
    if (state.currentPaperId === paperId) toast(`Definition not saved: ${error.message}. Use Retry save.`);
  } finally {
    teacher.saving.delete(cardId);
    if (state.currentPaperId === paperId) refreshTeacherMargins([annotation.segment_id]);
  }
}

function emptyReadingTeacher(enabled = true) {
  return { enabled, data: null, loading: false, error: "", cardsBySegment: new Map(),
    issues: [], openDetails: new Set(), saving: new Set(), ranges: new Map(), activeCardId: "",
    openCardId: "", showDeep: false, needsRefresh: false, scheduled: false };
}

function isDeepTeacherCard(card) {
  return ["focus", "question", "transfer"].includes(card.kind);
}

function marginCardsHtml(paragraphId) {
  const cards = state.readingTeacher.enabled ? state.readingTeacher.cardsBySegment.get(paragraphId) || [] : [];
  const content = annotationCardsHtml(paragraphId) + cards.filter(card =>
    card.kind !== "definition" || adoptedTeacherDefinition(card.id)?.segment_id !== paragraphId).map(card =>
    state.readingTeacher.openCardId === card.id ? readingTeacherCardHtml(card)
      : `<button class="teacher-marker" type="button" data-teacher-open="${escapeHtml(card.id)}" aria-expanded="false" aria-label="Open AI annotation: ${escapeHtml(card.title)}" title="AI teacher · ${escapeHtml(card.title)}">${escapeHtml(card.title)}</button>`
  ).join("");
  return content ? `<aside class="comment-stack" aria-label="Margin annotations">${content}</aside>` : "";
}

function updateMarginLayout() {
  qs("#documentRoot")?.classList.toggle("has-margin-notes",
    Boolean(state.payload?.teacher_available && state.readingTeacher.enabled)
    || state.annotations.some(annotation => isTeacherDefinition(annotation) || annotationNoteCardText(annotation)));
}

function externalHttpUrl(value) {
  try {
    const url = new URL(value);
    if (!["http:", "https:"].includes(url.protocol) || url.username || url.password) throw new Error("Unsupported external URL.");
    return url.href;
  } catch (error) {
    console.warn("Invalid external link", error);
    return "";
  }
}

function readingTeacherSourceUrl(value) {
  return externalHttpUrl(value);
}

function teacherDisclosure(card, key, label, content) {
  const id = `${card.id}:${key}`;
  return `<details data-teacher-disclosure="${escapeHtml(id)}"${state.readingTeacher.openDetails.has(id) ? " open" : ""}><summary>${label}</summary>${content}</details>`;
}

function teacherPaperMeaning(card) {
  return {
    quoted: card.definition.paper_kind === "quote" || (!card.definition.paper_kind && card.definition.paper === card.anchor.quote),
    label: card.definition.paper_kind === "usage" ? "本文用法" : "本文定义",
  };
}

function teacherDefinitionHtml(card, { sources = state.readingTeacher.data?.sources || [], annotationId = "" } = {}) {
  if (!card.definition) return "";
  const { quoted, label } = teacherPaperMeaning(card);
  const aiOnly = card.definition.external.every(item => item.kind === "ai-summary");
  const external = card.definition.external.map((item, index) => {
    if (item.kind === "ai-summary") return `<p>${escapeHtml(item.summary)}${aiOnly ? "" : ' <span class="teacher-context-label">AI 概括</span>'}</p>`;
    const source = sources.find(entry => entry.id === item.source_id);
    const url = readingTeacherSourceUrl(source?.url);
    const provenance = source ? `${source.title} · ${source.accessed_at}${source.reading_scope ? ` · ${source.reading_scope}` : ""}` : item.source_id;
    return `<p>${escapeHtml(item.summary)} ${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(provenance)}" aria-label="${escapeHtml(provenance)}">[${index + 1}]</a>` : "<span class=\"error-text\">来源地址无效。</span>"}</p>`;
  }).join("");
  const sourceAction = annotationId ? `data-jump-annotation="${escapeHtml(annotationId)}"`
    : `data-teacher-source="${escapeHtml(card.id)}" data-evidence-index="-1"`;
  return `<div class="teacher-definition">
    <div><button class="teacher-source-link" type="button" ${sourceAction} title="${quoted ? "Quoted from the paper" : "AI paraphrase of the paper"}">${label}</button>
      <p${quoted ? ' class="teacher-definition-quote"' : ""}>${quoted ? "“" : ""}${escapeHtml(card.definition.paper)}${quoted ? "”" : ""}</p></div>
    <div><strong>${aiOnly ? "一般含义 · AI 概括" : "外部定义"}</strong>${external}</div>
  </div>`;
}

function readingTeacherCardHtml(card) {
  const teacher = state.readingTeacher;
  const definitionOnly = card.kind === "definition";
  const cue = card.kind === "cue";
  const compact = definitionOnly || cue;
  const context = teacher.data.project_context;
  const refs = (card.context_ids || []).map(id => context?.cards.find(item => item.id === id)).filter(Boolean);
  const evidence = [{ ...card.anchor, label: "批注所在原文" }, ...(card.evidence || [])];
  const sourcesHtml = evidence.map((item, index) => `<div>
    <button class="teacher-source-link" type="button" data-teacher-source="${escapeHtml(card.id)}" data-evidence-index="${index - 1}">${escapeHtml(item.label)} · ${escapeHtml(item.segment_id)}</button>
    <blockquote>${escapeHtml(item.quote)}</blockquote></div>`).join("");
  const contextHtml = refs.length ? `<p class="teacher-context-label">${escapeHtml(context.project)} · 项目假设 · 快照 ${escapeHtml(context.snapshot_at)}</p>
    ${refs.map(item => `<p><strong>${escapeHtml(item.title)}</strong><br>${escapeHtml(item.summary)}</p>`).join("")}
    <p class="teacher-context-label">来源：${escapeHtml(context.source_path)}${context.source_status === "missing" ? "（路径不可用，仅保留历史快照）" : ""}</p>` : "";
  const adopted = adoptedTeacherDefinition(card.id);
  const write = state.paperSessions.get(state.currentPaperId)?.writes.get("annotations");
  const saving = teacher.saving.has(card.id);
  const retry = adopted && write?.dirty;
  return `<section class="teacher-card" id="teacher-card-${escapeHtml(card.id)}" data-teacher-card="${escapeHtml(card.id)}" tabindex="-1" aria-label="AI teacher: ${escapeHtml(card.title)}">
    <header class="margin-card-header"><h3 title="AI teacher">${escapeHtml(card.title)}</h3>
      <button class="teacher-close" type="button" data-teacher-close="${escapeHtml(card.id)}" aria-label="Close AI annotation" title="Close">×</button></header>
    ${cue ? `<p class="teacher-cue">${escapeHtml(card.text)}</p>` : definitionOnly ? "" : `<p class="teacher-question">${escapeHtml(card.question)}</p>`}
    ${teacherDefinitionHtml(card)}
    ${compact ? "" : teacherDisclosure(card, "hint", "线索", `<p>${escapeHtml(card.hint)}</p>`)}
    ${compact ? "" : teacherDisclosure(card, "explanation", "解读与依据", `<p>${escapeHtml(card.why)}</p><p>${escapeHtml(card.explanation)}</p>${sourcesHtml}`)}
    ${!compact && contextHtml ? teacherDisclosure(card, "context", `项目依据 · ${escapeHtml(context.project)}`, contextHtml) : ""}
    ${cue ? "" : `<div class="teacher-actions">
      ${definitionOnly ? "" : `<button class="secondary-button mini-button" type="button" data-teacher-reflect="${escapeHtml(card.id)}">记下想法</button>`}
      ${card.definition ? `<button class="secondary-button mini-button" type="button" data-teacher-adopt="${escapeHtml(card.id)}"${saving ? " disabled" : ""} title="Save this AI definition with its sources">${saving ? "Saving…" : retry ? "Retry save" : adopted ? "Saved · edit" : "Save to Notes"}</button>` : ""}
    </div>`}
  </section>`;
}

function exactTeacherRange(anchor) {
  const segment = state.payload?.segments?.find(item => item.id === anchor.segment_id);
  if (!segment || segment.markdown !== anchor.source_markdown) return null;
  const article = document.getElementById(anchor.segment_id);
  const root = article?.querySelector('.source-text[data-target="source"]');
  if (!root || !qs("#documentRoot")?.contains(root)) return null;
  const quote = displayTextPreservingMath(anchor.quote, { trim: false });
  const text = root.textContent;
  const start = text.indexOf(quote);
  if (!quote || start < 0 || text.indexOf(quote, start + 1) >= 0) return null;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const range = document.createRange();
  let offset = 0;
  let started = false;
  while (walker.nextNode()) {
    const node = walker.currentNode;
    const end = offset + node.textContent.length;
    if (!started && start < end) {
      range.setStart(node, start - offset);
      started = true;
    }
    if (started && start + quote.length <= end) {
      range.setEnd(node, start + quote.length - offset);
      return range;
    }
    offset = end;
  }
  return null;
}

function refreshReadingTeacher() {
  const teacher = state.readingTeacher;
  const affected = new Set(teacher.cardsBySegment.keys());
  teacher.cardsBySegment = new Map();
  teacher.ranges = new Map();
  teacher.issues = [...(teacher.data?.issues || [])];
  const segmentOrder = new Map((state.payload?.segments || []).map((segment, index) => [segment.id, index]));
  const cards = teacher.enabled ? (teacher.data?.cards || []).filter(card => isDeepTeacherCard(card) === teacher.showDeep).sort((a, b) =>
    (segmentOrder.get(a.anchor.segment_id) ?? Infinity) - (segmentOrder.get(b.anchor.segment_id) ?? Infinity)) : [];
  for (const card of cards) {
    const anchors = [card.anchor, ...(card.evidence || [])];
    const sourceMatches = anchors.every(anchor => state.payload?.segments?.some(segment =>
      segment.id === anchor.segment_id && segment.markdown === anchor.source_markdown));
    const range = sourceMatches ? exactTeacherRange(card.anchor) : null;
    if (!range) {
      teacher.issues.push({ id: card.id, reason: "原文已变化，或引文无法唯一定位；未划线，请重新核对。" });
      continue;
    }
    const segmentId = card.anchor.segment_id;
    if (!teacher.cardsBySegment.has(segmentId)) teacher.cardsBySegment.set(segmentId, []);
    teacher.cardsBySegment.get(segmentId).push(card);
    teacher.ranges.set(card.id, range);
    affected.add(segmentId);
  }
  if (window.CSS?.highlights && window.Highlight) {
    window.CSS.highlights.delete("reading-teacher");
    window.CSS.highlights.delete("reading-teacher-cues");
    window.CSS.highlights.delete("reading-teacher-focus");
    if (teacher.ranges.size) window.CSS.highlights.set("reading-teacher", new window.Highlight(...teacher.ranges.values()));
    const cueRanges = cards.filter(card => card.kind !== "definition" && teacher.ranges.has(card.id)).map(card => teacher.ranges.get(card.id));
    if (cueRanges.length) window.CSS.highlights.set("reading-teacher-cues", new window.Highlight(...cueRanges));
  }
  if (teacher.enabled && !teacher.ranges.has(teacher.openCardId)) teacher.openCardId = "";
  updateMarginLayout();
  refreshTeacherMargins(affected);
  renderReadingTeacherStatus();
  teacher.needsRefresh = false;
}

function refreshTeacherMargins(segmentIds) {
  for (const segmentId of new Set(segmentIds)) {
    const article = document.getElementById(segmentId);
    if (!article || !qs("#documentRoot")?.contains(article)) continue;
    const previous = article.querySelector(":scope > .comment-stack");
    const html = marginCardsHtml(segmentId);
    const wrapper = document.createElement("div");
    wrapper.innerHTML = html;
    const next = wrapper.firstElementChild;
    if (next) {
      if (previous) previous.replaceWith(next);
      else article.appendChild(next);
      bindReaderDynamicEvents(next);
    } else previous?.remove();
    article.classList.toggle("has-comments", Boolean(next));
  }
}

function renderReadingTeacherStatus() {
  const teacher = state.readingTeacher;
  const toggle = qs("#toggleReadingTeacher");
  const status = qs("#readingTeacherStatus");
  if (!toggle || !status) return;
  toggle.hidden = !state.payload?.teacher_available;
  toggle.disabled = state.workspaceMode === "think";
  toggle.setAttribute("aria-pressed", String(teacher.enabled));
  toggle.textContent = "AI teacher";
  toggle.title = teacher.enabled ? "Hide AI annotations" : "Show AI annotations";
  const depth = qs("#toggleTeacherDepth");
  if (depth) {
    depth.hidden = toggle.hidden || !teacher.enabled || state.workspaceMode === "think"
      || (!teacher.showDeep && !teacher.data?.cards.some(isDeepTeacherCard));
    depth.setAttribute("aria-pressed", String(teacher.showDeep));
    depth.textContent = teacher.showDeep ? "返回导读" : "深入思考";
    depth.title = teacher.showDeep ? "Return to reading cues and definitions" : "Open saved deeper questions; no generation";
  }
  renderReadingTeacherNavigation();
  status.hidden = toggle.hidden || !teacher.enabled || state.workspaceMode === "think";
  if (status.hidden) return;
  if (teacher.error) {
    status.textContent = `AI teacher 未加载：${teacher.error}。原文和笔记仍可正常使用。`;
    const retry = document.createElement("button");
    retry.type = "button";
    retry.className = "secondary-button mini-button";
    retry.textContent = "Retry teacher";
    retry.addEventListener("click", () => loadReadingTeacher(state.currentPaperId, { force: true }));
    status.appendChild(retry);
    return;
  }
  if (!teacher.data) {
    status.textContent = "AI 批注加载中…";
    return;
  }
  const count = teacher.ranges.size;
  const unsupported = !(window.CSS?.highlights && window.Highlight);
  status.hidden = Boolean(count && !teacher.issues.length && !unsupported);
  status.textContent = `${count ? "" : "暂无 AI 批注。"}${teacher.issues.length ? `${teacher.issues.length} 处引用失效，已隐藏。` : ""}${unsupported ? "当前浏览器不支持原文标记；可用右侧标签或顶部位置菜单。" : ""}`;
  if (teacher.issues.length) {
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = "查看未显示的批注";
    const body = document.createElement("div");
    body.textContent = teacher.issues.map(item => `${item.id}: ${item.reason}`).join("\n");
    details.append(summary, body);
    status.appendChild(details);
  }
}

function renderReadingTeacherNavigation() {
  const nav = qs("#readingTeacherNav");
  const select = qs("#readingTeacherLocation");
  if (!nav || !select) return;
  const teacher = state.readingTeacher;
  const cards = [...teacher.cardsBySegment.values()].flat();
  nav.hidden = !state.payload?.teacher_available || !teacher.enabled || !cards.length || state.workspaceMode === "think";
  if (nav.hidden) return;
  const options = JSON.stringify(cards.map(card => [card.id, card.title]));
  if (select.dataset.cards !== options) {
    select.innerHTML = `<option value="" disabled>${cards.length} 处批注</option>` + cards.map((card, index) =>
      `<option value="${escapeHtml(card.id)}">${index + 1}/${cards.length} · ${escapeHtml(card.title)}</option>`).join("");
    select.dataset.cards = options;
  }
  const index = cards.findIndex(card => card.id === teacher.activeCardId);
  select.value = index < 0 ? "" : teacher.activeCardId;
  select.title = index < 0 ? "Go to AI annotation" : cards[index].title;
  select.onchange = () => { if (select.value) focusTeacherSource(select.value); };
  const previous = qs("#previousTeacherCard");
  const next = qs("#nextTeacherCard");
  previous.disabled = index <= 0;
  next.disabled = index === cards.length - 1;
  previous.onclick = () => { if (index > 0) focusTeacherSource(cards[index - 1].id); };
  next.onclick = () => { if (index < cards.length - 1) focusTeacherSource(cards[index + 1].id); };
}

function scheduleReadingTeacher(paperId) {
  const session = state.paperSessions.get(paperId);
  const teacher = session?.readingTeacher;
  if (!session?.payload?.teacher_available || !teacher || teacher.data || teacher.loading || teacher.scheduled || teacher.error) return;
  teacher.scheduled = true;
  const load = () => {
    teacher.scheduled = false;
    if (state.currentPaperId === paperId && !state.paperLoadingId
      && state.paperSessions.get(paperId) === session && session.readingTeacher === teacher) loadReadingTeacher(paperId);
  };
  // Leave a source-only paint before optional file loading and margin layout.
  requestAnimationFrame(() => requestAnimationFrame(() => {
    if (typeof window.requestIdleCallback === "function") window.requestIdleCallback(load, { timeout: 1000 });
    else setTimeout(load, 0);
  }));
}

async function loadReadingTeacher(paperId, { force = false } = {}) {
  const session = state.paperSessions.get(paperId);
  const teacher = session?.readingTeacher;
  if (!session?.payload?.teacher_available || !teacher || teacher.loading || (teacher.data && !force)) return;
  teacher.loading = true;
  teacher.error = "";
  if (paperId === state.currentPaperId) renderReadingTeacherStatus();
  try {
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/reading-teacher`);
    if (response.paper_id !== paperId || !response.teacher || !Array.isArray(response.teacher.cards)) {
      throw new Error("Invalid or mismatched teacher response.");
    }
    if (session.readingTeacher !== teacher || state.paperSessions.get(paperId) !== session) return;
    teacher.data = response.teacher;
    teacher.needsRefresh = true;
    if (response.teacher.available === false) session.payload.teacher_available = false;
  } catch (error) {
    teacher.error = error.message;
    teacher.needsRefresh = true;
    console.error(`Reading teacher failed for ${paperId}`, error);
  } finally {
    teacher.loading = false;
    if (paperId === state.currentPaperId && state.readingTeacher === teacher && !state.paperLoadingId) {
      const top = readerViewportTop();
      const anchor = qsa("#documentRoot .paragraph").find(node => node.getBoundingClientRect().bottom > top);
      const before = anchor?.getBoundingClientRect().top;
      refreshReadingTeacher();
      if (anchor && before !== undefined) {
        const shift = anchor.getBoundingClientRect().top - before;
        if (Math.abs(shift) > 0.5) window.scrollTo({ top: window.scrollY + shift, behavior: "instant" });
      }
    }
  }
}

function readingTeacherCard(cardId) {
  return [...state.readingTeacher.cardsBySegment.values()].flat().find(card => card.id === cardId);
}

function focusTeacherSource(cardId, evidenceIndex = -1, { scroll = true, moveFocus = false } = {}) {
  const card = readingTeacherCard(cardId);
  const anchor = evidenceIndex < 0 ? card?.anchor : card?.evidence?.[evidenceIndex];
  const range = anchor ? exactTeacherRange(anchor) : null;
  if (!range) { toast("无法唯一定位原文；请重新核对该批注。"); return; }
  const teacher = state.readingTeacher;
  const article = document.getElementById(anchor.segment_id);
  const before = article.getBoundingClientRect().top;
  const previous = readingTeacherCard(teacher.openCardId);
  const saved = card.kind === "definition" ? adoptedTeacherDefinition(cardId) : null;
  const savedHere = saved?.segment_id === card.anchor.segment_id ? saved : null;
  const wasCollapsed = savedHere && state.collapsedDefinitionNotes.delete(savedHere.id);
  teacher.activeCardId = cardId;
  if (teacher.openCardId !== cardId || wasCollapsed) {
    teacher.openCardId = cardId;
    refreshTeacherMargins([previous?.anchor.segment_id, card.anchor.segment_id].filter(Boolean));
  }
  renderReadingTeacherNavigation();
  if (scroll) article.scrollIntoView({ behavior: "smooth", block: "center" });
  else {
    const shift = article.getBoundingClientRect().top - before;
    if (Math.abs(shift) > 0.5) window.scrollTo({ top: window.scrollY + shift, behavior: "instant" });
  }
  if (moveFocus) document.getElementById(savedHere ? `saved-definition-${savedHere.id}` : `teacher-card-${cardId}`)?.focus({ preventScroll: true });
  if (window.CSS?.highlights && window.Highlight) {
    const highlight = new window.Highlight(range);
    window.CSS.highlights.set("reading-teacher-focus", highlight);
    setTimeout(() => {
      if (window.CSS.highlights.get("reading-teacher-focus") === highlight) window.CSS.highlights.delete("reading-teacher-focus");
    }, 2200);
  }
}

function closeReadingTeacherCard() {
  const teacher = state.readingTeacher;
  const card = readingTeacherCard(teacher.openCardId);
  teacher.openCardId = "";
  if (!card) return;
  refreshTeacherMargins([card.anchor.segment_id]);
  document.querySelector(`[data-teacher-open="${card.id}"]`)?.focus({ preventScroll: true });
}

function handleReadingTeacherSourceClick(event) {
  if (!state.readingTeacher.enabled || state.workspaceMode === "think" || event.defaultPrevented
    || event.button !== 0 || event.detail > 1 || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey
    || window.getSelection()?.toString() || event.target.closest("button, a, mark[data-annotation-id], img, svg")) return;
  const source = event.target.closest('.source-text[data-target="source"]');
  if (!source) return;
  const cards = [...(state.readingTeacher.cardsBySegment.get(source.dataset.pid) || [])]
    .sort((a, b) => Number(b.kind === "definition") - Number(a.kind === "definition"));
  for (const card of cards) {
    const range = state.readingTeacher.ranges.get(card.id);
    if (range && [...range.getClientRects()].some(rect => event.clientX >= rect.left && event.clientX <= rect.right
      && event.clientY >= rect.top && event.clientY <= rect.bottom)) {
      focusTeacherSource(card.id, -1, { scroll: false });
      return;
    }
  }
}

function teacherNoteSelection(card) {
  const segment = state.payload?.segments?.find(item => item.id === card.anchor.segment_id);
  if (!segment || segment.markdown !== card.anchor.source_markdown) throw new Error("Source changed; reload and verify the teaching card.");
  const text = displayTextPreservingMath(segment.markdown, { trim: false });
  const quote = displayTextPreservingMath(card.anchor.quote, { trim: false });
  const range = rangeForQuote(text, quote);
  if (!range || text.indexOf(quote, range.start + 1) >= 0) throw new Error("Teaching quote is not a unique source match.");
  return { segment_id: segment.id, target: "source", quote, range };
}

function adoptedTeacherDefinition(cardId) {
  return state.annotations.find(item => item.origin?.kind === "reading-teacher"
    && item.origin.document_id === state.readingTeacher.data?.id && item.origin.card_id === cardId
    && item.origin.content_type === "definition");
}

function teacherDefinitionNote(card, data = state.readingTeacher.data) {
  const definition = card.definition;
  const external = definition.external.map(item => {
    if (item.kind === "ai-summary") return `AI 概括（未外部检索）\n${item.summary}`;
    const source = data.sources.find(entry => entry.id === item.source_id);
    if (!source) throw new Error("The definition's external source is no longer available.");
    return `${source.title}\n${item.summary}\n${source.url}\nRetrieved: ${source.accessed_at}`;
  });
  const { quoted, label } = teacherPaperMeaning(card);
  const externalLabel = definition.external.every(item => item.kind === "ai-summary") ? "一般含义" : "外部定义";
  return `${card.title}\n\n来源：AI teacher 定义，用户主动采纳；不是用户原创。\n\n${label}（${quoted ? "原文" : "AI 概括"}）\n${definition.paper}\n原文位置：reader.md#${card.anchor.segment_id}\n\n${externalLabel}\n${external.join("\n\n")}${definition.comparison ? `\n\nAI 对照（不是作者原话）\n${definition.comparison}` : ""}`;
}

async function adoptTeacherDefinition(cardId) {
  const teacher = state.readingTeacher;
  const card = readingTeacherCard(cardId);
  if (teacher.saving.has(cardId)) return;
  if (!card?.definition) { toast("This definition is no longer available; reload and verify the teaching card."); return; }
  const paperId = state.currentPaperId;
  const existing = adoptedTeacherDefinition(cardId);
  const write = state.paperSessions.get(paperId)?.writes.get("annotations");
  if (existing && !write?.dirty) { openExistingAnnotationDrawer(existing.id); return; }
  teacher.saving.add(cardId);
  try {
    if (!existing) {
      const selection = teacherNoteSelection(card);
      const now = new Date().toISOString();
      const note = teacherDefinitionNote(card);
      state.collapsedDefinitionNotes.delete(`ai-def-${teacher.data.id}-${card.id}`);
      state.annotations.push({
        id: `ai-def-${teacher.data.id}-${card.id}`, type: "range", ...selection, color: "blue",
        note, tags: ["definition"], created_at: now, updated_at: now,
        origin: JSON.parse(JSON.stringify({ kind: "reading-teacher", content_type: "definition", document_id: teacher.data.id,
          card_id: card.id, title: card.title, initial_note: note, created_by: teacher.data.created_by, anchor: card.anchor,
          definition: card.definition, sources: teacher.data.sources.filter(source =>
            card.definition.external.some(item => item.source_id === source.id)) })),
      });
    }
    await persistCurrentPaperAnnotations("", { segmentIds: [card.anchor.segment_id] });
    if (state.currentPaperId === paperId) toast("Definition saved to Notes.");
  } catch (error) {
    console.error("Could not adopt teacher definition", error);
    if (state.currentPaperId === paperId) toast(`Definition not saved: ${error.message}. Use Retry save.`);
  } finally {
    teacher.saving.delete(cardId);
    if (state.currentPaperId === paperId && state.readingTeacher === teacher) refreshReadingTeacher();
  }
}

function reflectOnTeacherCard(cardId) {
  const card = readingTeacherCard(cardId);
  if (!card) { toast("This teaching card is no longer available."); return; }
  if (!isDeepTeacherCard(card)) { toast("Use the normal highlight or note controls for your own response."); return; }
  try {
    openAnnotationDrawer(card.anchor.segment_id, "yellow", {
      ...teacherNoteSelection(card),
      teacher_prompt: { document_id: state.readingTeacher.data.id, card_id: card.id, question: card.question },
    });
  } catch (error) {
    toast(`Could not attach a reflection: ${error.message}`);
  }
}

function skimSummaryHtml(markdown) {
  const lines = String(markdown || "").split("\n");
  const parts = [];
  let listItems = [];
  let tableLines = [];
  const flushList = () => {
    if (listItems.length) {
      parts.push(`<ul>${listItems.map(item => `<li>${inlineMarkdown(item)}</li>`).join("")}</ul>`);
      listItems = [];
    }
  };
  const flushTable = () => {
    if (!tableLines.length) return;
    flushList();
    parts.push(renderPipeTable(tableLines.join("\n")));
    tableLines = [];
  };
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      flushList();
      tableLines.push(line);
      continue;
    }
    flushTable();
    if (!trimmed) {
      flushList();
      continue;
    }
    const heading = trimmed.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      flushList();
      const level = Math.min(3, Math.max(2, heading[1].length));
      parts.push(`<h${level}>${inlineMarkdown(heading[2])}</h${level}>`);
      continue;
    }
    const bullet = trimmed.match(/^[-*]\s+(.+)$/);
    if (bullet) {
      listItems.push(bullet[1]);
      continue;
    }
    flushList();
    parts.push(`<p>${inlineMarkdown(trimmed)}</p>`);
  }
  flushTable();
  flushList();
  return parts.join("");
}

function isPipeTableLine(line) {
  const trimmed = String(line || "").trim();
  return trimmed.startsWith("|") && trimmed.endsWith("|") && trimmed.split("|").length >= 4;
}

function renderPipeTableWithHighlights(lines, startOffset, annotations, target = "thinking", options = {}) {
  const rowData = [];
  let cursor = startOffset;
  for (const line of lines) {
    const trimmedStart = line.search(/\S|$/);
    const cells = [];
    const rawCells = line.trim().replace(/^\||\|$/g, "").split("|");
    let localCursor = cursor + trimmedStart + (line.trim().startsWith("|") ? 1 : 0);
    for (const rawCell of rawCells) {
      const leading = rawCell.match(/^\s*/)?.[0]?.length || 0;
      const cellText = rawCell.trim();
      cells.push({ text: cellText, start: localCursor + leading });
      localCursor += rawCell.length + 1;
    }
    rowData.push(cells);
    cursor += line.length + 1;
  }
  const filtered = rowData.filter(cells => !cells.every(cell => /^:?-{3,}:?$/.test(cell.text)));
  if (!filtered.length) return `<pre class="thinking-code"><code>${escapeHtml(lines.join("\n"))}</code></pre>`;
  const body = filtered.map((cells, rowIndex) => `<tr>${cells.map(cell => {
    const tag = rowIndex === 0 ? "th" : "td";
    return `<${tag}>${renderThinkingSpan(cell.text, cell.start, annotations, target, options)}</${tag}>`;
  }).join("")}</tr>`).join("");
  return `<div class="table-wrap"><table class="paper-table">${body}</table></div>`;
}

function renderThinkingSpan(text, startOffset, annotations, target = "thinking", options = {}) {
  const raw = options.rawText || "";
  const sourceText = raw || String(text || "");
  const localAnnotations = annotations.map(annotation => {
    let range = normalizedAnnotationRange(annotation, sourceText, target);
    if (annotation.quote) {
      const quoted = displayTextPreservingMath(annotation.quote);
      const currentSlice = range ? displayTextPreservingMath(sourceText.slice(range.start, range.end)) : "";
      if (!range || (quoted && currentSlice !== quoted && !currentSlice.includes(quoted))) {
        range = rangeForQuote(sourceText, quoted) || range;
      }
    }
    if (!range) return null;
    const start = Math.max(range.start, startOffset);
    const end = Math.min(range.end, startOffset + text.length);
    if (end <= start) return null;
    return { ...annotation, range: { start: start - startOffset, end: end - startOffset }, show_inline_note_chip: range.end <= startOffset + text.length };
  }).filter(Boolean);
  return `<span data-raw-start="${escapeHtml(startOffset)}">${splitInlineHtmlWithHighlights(text, localAnnotations, target, options)}</span>`;
}

function blockMarkdownWithHighlights(markdown, annotations, target = "thinking", options = {}) {
  const raw = String(markdown || "").replace(/\r\n?/g, "\n");
  const lines = raw.split("\n");
  const parts = [];
  let listItems = [];
  let tableLines = [];
  let tableStartOffset = 0;
  let inCode = false;
  let codeLines = [];
  let offset = 0;
  const flushList = () => {
    if (!listItems.length) return;
    parts.push(`<ul>${listItems.map(item => `<li>${item}</li>`).join("")}</ul>`);
    listItems = [];
  };
  const renderSpan = (text, startOffset) => renderThinkingSpan(text, startOffset, annotations, target, { ...options, rawText: raw });
  const flushTable = () => {
    if (!tableLines.length) return;
    flushList();
    parts.push(renderPipeTableWithHighlights(tableLines, tableStartOffset, annotations, target, { ...options, rawText: raw }));
    tableLines = [];
  };
  for (const line of lines) {
    const lineStart = offset;
    const lineLength = line.length;
    offset += lineLength + 1;
    const trimmed = line.trim();
    if (/^```/.test(trimmed)) {
      flushTable();
      flushList();
      if (inCode) {
        parts.push(`<pre class="thinking-code"><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
        codeLines = [];
        inCode = false;
      } else {
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      codeLines.push(line);
      continue;
    }
    if (!trimmed) {
      flushTable();
      flushList();
      continue;
    }
    if (isPipeTableLine(line)) {
      flushList();
      if (!tableLines.length) tableStartOffset = lineStart;
      tableLines.push(line);
      continue;
    }
    flushTable();
    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      flushList();
      const level = Math.min(4, Math.max(2, heading[1].length + 1));
      const headingStart = lineStart + heading[1].length + 1;
      parts.push(`<h${level}>${renderSpan(heading[2], headingStart)}</h${level}>`);
      continue;
    }
    const bullet = line.match(/^\s*[-*+]\s+(.+)$/);
    if (bullet) {
      const bulletStart = lineStart + line.indexOf(bullet[1]);
      listItems.push(renderSpan(bullet[1], bulletStart));
      continue;
    }
    const quote = line.match(/^>\s?(.+)$/);
    if (quote) {
      flushList();
      const quoteStart = lineStart + line.indexOf(quote[1]);
      parts.push(`<blockquote>${renderSpan(quote[1], quoteStart)}</blockquote>`);
      continue;
    }
    flushList();
    parts.push(`<p>${renderSpan(line, lineStart)}</p>`);
  }
  if (inCode) parts.push(`<pre class="thinking-code"><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
  flushTable();
  flushList();
  return parts.join("");
}

function thinkingBlockById(blockId) {
  if (blockId === paperBriefBlockId) {
    return { id: paperBriefBlockId, type: "paper_brief", title: "Paper Brief", content: state.thinking?.explain?.content || "", mode: "brief" };
  }
  return state.thinking?.blocks?.find(block => block.id === blockId) || null;
}

function thinkingAnnotationsFor(blockId) {
  return (state.thinking?.annotations || []).filter(item => item.block_id === blockId);
}

function applyThinkingHighlights(text, blockId) {
  return blockMarkdownWithHighlights(text, thinkingAnnotationsFor(blockId), "thinking", { citations: true });
}

function renderExplainPane() {
  const root = qs("#explainPane");
  if (!root || !state.thinking) return;
  const content = state.thinking.explain.content || "";
  if (!content) {
    root.innerHTML = '<p class="muted">No saved explanation. Original notes are kept without generating a summary.</p>';
    return;
  }
  root.innerHTML = `
    <div class="sense-section sense-explain">
      <div class="sense-section-heading">
        <span class="sense-kicker">Explain</span>
        <h3>像博客一样讲清楚这篇论文</h3>
      </div>
      <div class="sense-actions">
        <button id="regenerateExplain" class="secondary-button" type="button">Regenerate from PDF</button>
      </div>
      <div id="explainPreview" class="sense-explain-preview">${skimSummaryHtml(content)}</div>
      <label class="sense-label" for="explainEditor">Edit explanation</label>
      <textarea id="explainEditor" class="sense-textarea" rows="12" spellcheck="false">${escapeHtml(content)}</textarea>
    </div>`;
  const editor = qs("#explainEditor");
  const preview = qs("#explainPreview");
  qs("#regenerateExplain")?.addEventListener("click", regenerateExplanationFromPdf);
  editor?.addEventListener("input", () => {
    state.thinking.explain.content = editor.value;
    state.thinking.explain.updated_at = new Date().toISOString();
    if (preview) preview.innerHTML = skimSummaryHtml(editor.value);
    scheduleThinkingSave();
  });
}

function paperBriefCardHtml() {
  const content = state.thinking?.explain?.content || "";
  if (!content.trim()) return "";
  return `
    <details class="paper-brief-card" id="paper-brief">
      <summary class="paper-brief-summary">Saved Paper Brief</summary>
      <div class="paper-brief-header">
        <div>
          <span class="sense-kicker">Paper Brief</span>
          <h2>已保存的解读</h2>
        </div>
        <button class="secondary-button" id="regeneratePaperBrief" type="button">Regenerate from PDF</button>
      </div>
      <div id="paperBriefPreview" class="sense-explain-preview thinking-text paper-brief-thinking-text" data-thinking-block="${paperBriefBlockId}" tabindex="0">${applyThinkingHighlights(content, paperBriefBlockId)}</div>
      <details class="paper-brief-edit">
        <summary>Edit paper brief</summary>
        <textarea id="paperBriefEditor" class="sense-textarea" rows="10" spellcheck="false">${escapeHtml(content)}</textarea>
      </details>
    </details>`;
}

function bindPaperBriefCard() {
  const editor = qs("#paperBriefEditor");
  const preview = qs("#paperBriefPreview");
  qs("#regeneratePaperBrief")?.addEventListener("click", regenerateExplanationFromPdf);
  bindThinkingAnnotationControls(qs("#paper-brief") || document);
  editor?.addEventListener("input", () => {
    if (!state.thinking) state.thinking = normalizeThinkingData(state.payload?.thinking || {});
    state.thinking.explain.content = editor.value;
    state.thinking.explain.updated_at = new Date().toISOString();
    if (preview) preview.innerHTML = applyThinkingHighlights(editor.value, paperBriefBlockId);
    scheduleThinkingSave();
  });
}

function refreshPaperBriefCard() {
  const card = qs("#paper-brief");
  if (!card) return false;
  const wrapper = document.createElement("div");
  wrapper.innerHTML = paperBriefCardHtml().trim();
  const next = wrapper.firstElementChild;
  if (!next) return false;
  next.open = card.open;
  card.replaceWith(next);
  bindPaperBriefCard();
  updateToolbarStatus();
  return true;
}

function refreshThinkingAnnotationSurfaces(blockId = "") {
  if (!blockId || blockId === paperBriefBlockId) refreshPaperBriefCard();
  renderSensemakingPanel();
  if (shouldRenderNotesImmediately()) renderNotes();
  refreshAllNotesInBackground();
}

async function regenerateExplanationFromPdf() {
  if (!state.currentPaperId) return;
  const confirmed = window.confirm("Regenerate Paper Brief from the PDF? This will replace the current Paper Brief.");
  if (!confirmed) return;
  const paperId = state.currentPaperId;
  const buttons = qsa("#regeneratePaperBrief, #regenerateExplain");
  buttons.forEach(button => {
    button.disabled = true;
    button.dataset.previousLabel = button.textContent || "";
    button.textContent = "Regenerating...";
  });
  setThinkingSaveState("Regenerating Paper Brief...", "saving");
  try {
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/thinking/explain`, {
      method: "POST",
      body: JSON.stringify({ force: true, target: "paper_brief" }),
    });
    state.thinking = normalizeThinkingData(response.thinking || state.thinking, { seed: false });
    if (state.payload) state.payload.thinking = state.thinking;
    invalidatePaperCache(paperId);
    if (state.currentPaperId === paperId) await loadPaper(paperId, { force: true });
    setThinkingSaveState("Paper Brief regenerated", "saved");
    toast("Paper Brief regenerated");
  } catch (error) {
    buttons.forEach(button => {
      button.disabled = false;
      button.textContent = button.dataset.previousLabel || "Regenerate from PDF";
      delete button.dataset.previousLabel;
    });
    setThinkingSaveState("Paper Brief regenerate failed", "error");
    toast(`Regenerate failed: ${error.message}`);
  }
}

function thinkingAnnotationCardsHtml(blockId) {
  const items = thinkingAnnotationsFor(blockId);
  if (!items.length) return "";
  return `<div class="thinking-note-stack">${items.map(item => `
    <section class="thinking-note-card" data-thinking-note-card="${escapeHtml(item.id || "")}">
      <button class="thinking-note-main" data-focus-thinking-annotation="${escapeHtml(item.id || "")}">
        <span class="thinking-note-color hl-${escapeHtml(item.color || "yellow")}"></span>
        <span class="thinking-note-body">
          <span class="thinking-note-quote">${escapeHtml(compactText(item.quote || "Highlight", 105))}</span>
          ${item.note ? `<span class="thinking-note-text">${escapeHtml(item.note)}</span>` : '<span class="muted small-text">Highlight only</span>'}
        </span>
      </button>
      <div class="note-tags" aria-label="Thinking note tags">
        ${annotationTags(item).map(tag => `<button class="note-tag" data-remove-thinking-tag="${escapeHtml(tag)}" data-thinking-annotation-id="${escapeHtml(item.id || "")}" title="Remove tag">${escapeHtml(tag)} ×</button>`).join("") || '<span class="muted small-text">No tags</span>'}
      </div>
      <div class="thinking-note-actions">
        <button class="secondary-button" data-edit-thinking-annotation="${escapeHtml(item.id || "")}">Edit</button>
        <button class="comment-delete" data-delete-thinking-annotation="${escapeHtml(item.id || "")}" title="Delete note">x</button>
      </div>
      <details class="thinking-tag-details">
        <summary>Tags</summary>
        <div class="note-tag-editor thinking-tag-editor">
          <select data-thinking-tag-select="${escapeHtml(item.id || "")}">
            <option value="">Add existing tag...</option>
            ${allNoteTags().map(tag => `<option value="${escapeHtml(tag)}">${escapeHtml(tag)}</option>`).join("")}
          </select>
          <input data-thinking-tag-input="${escapeHtml(item.id || "")}" placeholder="Custom tag" />
          <button class="secondary-button" data-add-thinking-tag="${escapeHtml(item.id || "")}">Add</button>
        </div>
      </details>
    </section>`).join("")}</div>`;
}

function sourceRefLabel(ref) {
  const start = ref.segment_id || ref.annotation_id || ref.block_id || "source";
  const end = ref.end_segment_id && ref.end_segment_id !== ref.segment_id ? `-${ref.end_segment_id}` : "";
  return ref.label || `${start}${end}`;
}

function sourceRefsHtml(refs = [], attrName = "data-thinking-source-ref") {
  const clean = normalizeSourceRefs(refs);
  if (!clean.length) return "";
  return `<div class="thinking-source-links">${clean.map((ref, index) => `
    <button class="presentation-source-link thinking-source-chip" ${attrName}="${index}" type="button" title="${escapeHtml(compactText(ref.quote || sourceRefLabel(ref), 180))}">${escapeHtml(sourceRefLabel(ref))}</button>
  `).join("")}</div>`;
}

function hasInlineParagraphRefs(text) {
  return /\[(p-\d{4})(?:\s*[-–]\s*(p-\d{4}))?\]/i.test(String(text || ""));
}

function selectionRefsHtml(refs = []) {
  const clean = normalizeSelectionRefs(refs);
  if (!clean.length) return "";
  return `<div class="thinking-prompt-sources">${clean.map((ref, index) => `
    <button class="presentation-source-link thinking-source-chip" data-thinking-selection-ref="${index}" type="button" title="${escapeHtml(compactText(ref.quote || ref.segment_id, 180))}">${escapeHtml(ref.segment_id || `Selection ${index + 1}`)}</button>
  `).join("")}</div>`;
}

function modeLabel(mode) {
  return mode === "source" ? "Source-grounded" : mode === "free" ? "Free reflection" : mode === "reading_narrative" ? "Reading Narrative" : "Manual output";
}

function chatModeHint(mode = state.chatMode) {
  return mode === "source"
    ? "Uses selected passages and paragraph anchors."
    : "No source constraint; useful for riffs, comparisons, and design ideas.";
}

function isAgentThinkingBlock(block) {
  return ["source", "free", "reading_narrative"].includes(String(block?.mode || "")) || Boolean(block?.model);
}

function thinkingBlockHeaderHtml(block) {
  const label = block.mode === "reading_narrative" ? "Generated narrative" : isAgentThinkingBlock(block) ? "" : "Pasted response";
  return `<div class="thinking-message-heading">
    <span class="thinking-message-role">AI</span>
    ${label ? `<span class="thinking-message-origin">${label}</span>` : ""}
  </div>`;
}

function chatSelectionRefs() {
  const draft = state.chatSelectionDraft;
  if (!draft) return [];
  const parts = Array.isArray(draft.parts) && draft.parts.length ? draft.parts : [draft];
  return parts.map(part => ({
    paper_id: state.currentPaperId || "",
    segment_id: part.segment_id || "",
    target: part.target || "source",
    quote: part.quote || "",
    range: part.range || null,
  })).filter(ref => ref.segment_id || ref.quote);
}

function chatComposerHtml() {
  const selectionRefs = chatSelectionRefs();
  const project = currentPaperProject();
  const projectCardCount = projectContextCards(project).length;
  return `
    <section id="thinkingChatComposer" class="sense-section thinking-agent-compose" aria-label="Chat with AI">
      <div class="thinking-chat-controls">
        <div class="thinking-chat-mode" role="group" aria-label="Agent mode">
          <button class="thinking-chat-mode-button ${state.chatMode === "source" ? "active" : ""}" data-chat-mode="source" aria-pressed="${state.chatMode === "source" ? "true" : "false"}" title="${escapeHtml(chatModeHint("source"))}" type="button" ${state.chatSending ? "disabled" : ""}>Source-grounded</button>
          <button class="thinking-chat-mode-button ${state.chatMode === "free" ? "active" : ""}" data-chat-mode="free" aria-pressed="${state.chatMode === "free" ? "true" : "false"}" title="${escapeHtml(chatModeHint("free"))}" type="button" ${state.chatSending ? "disabled" : ""}>Free reflection</button>
        </div>
        <label class="thinking-project-context-toggle ${projectCardCount ? "" : "disabled"}" title="${escapeHtml(project)} · ${escapeHtml(projectCardCount)} context cards">
          <input id="useProjectContext" type="checkbox" ${state.chatUseProjectContext && projectCardCount ? "checked" : ""} ${projectCardCount && !state.chatSending ? "" : "disabled"} />
          <span>Project context</span>
        </label>
      </div>
      ${selectionRefs.length ? `<div class="thinking-chat-selection"><span>Quoted from paper</span>${selectionRefsHtml(selectionRefs)}<button class="icon-button" id="clearChatSelection" type="button" title="Clear quoted source">x</button></div>` : ""}
      <p id="thinkingChatError" class="thinking-chat-error" role="alert"${state.chatError ? "" : " hidden"}>${state.chatError ? `Reply failed: ${escapeHtml(state.chatError)}. Your question is kept below; send it again to retry.` : ""}</p>
      <div class="thinking-chat-input-shell">
        <textarea id="thinkingChatInput" class="sense-textarea" rows="2" aria-label="Message AI" title="Enter to send; Shift+Enter for a new line" placeholder="Message AI..." ${state.chatSending ? "disabled" : ""}>${escapeHtml(state.chatSending ? "" : state.chatDraft || "")}</textarea>
        <div class="thinking-chat-actions">
          <button id="sendThinkingChat" class="primary-button" type="button" ${state.chatSending ? "disabled" : ""}>Send</button>
        </div>
      </div>
    </section>`;
}

function manualOutputComposerHtml() {
  const draft = state.manualOutputDraft;
  return `<section id="manualOutputComposer" class="manual-ai-output-fields" aria-label="Paste AI output">
    <label class="sense-label" for="thinkingBlockPrompt">Original question (optional)</label>
    <input id="thinkingBlockPrompt" class="sense-input" value="${escapeHtml(draft.prompt)}" placeholder="What did you ask the AI?" />
    <label class="sense-label" for="thinkingBlockContent">AI response</label>
    <textarea id="thinkingBlockContent" class="sense-textarea" rows="12" placeholder="Paste the full AI response here...">${escapeHtml(draft.content)}</textarea>
    <div class="thinking-chat-actions">
      <button id="addThinkingBlock" class="secondary-button" type="button">Save AI output</button>
      <span class="manual-draft-status muted small-text" role="status"${draft.content || draft.prompt ? "" : " hidden"}>Unsaved draft</span>
    </div>
  </section>`;
}

function navigateThinkingSourceRef(ref) {
  if (!ref) return;
  if (ref.segment_id) {
    activateView("reader");
    setWorkspaceMode("split");
    scrollToParagraph(ref.segment_id);
  } else if (ref.annotation_id) {
    focusAnnotation(ref.annotation_id);
  }
}

function bindParagraphRefLinks(root = document) {
  root.querySelectorAll?.("[data-paragraph-ref]").forEach(button => button.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    const paragraphId = button.dataset.paragraphRef || "";
    if (!paragraphId) return;
    activateView("reader");
    setWorkspaceMode("split");
    scrollToParagraph(paragraphId);
  }));
}

function bindThinkingSourceLinks() {
  qsa("[data-thinking-source-ref]").forEach(button => button.addEventListener("click", () => {
    const block = button.closest("[data-thinking-block-card]");
    const blockId = block?.dataset.thinkingBlockCard || "";
    const ref = thinkingBlockById(blockId)?.source_refs?.[Number(button.dataset.thinkingSourceRef)] || null;
    navigateThinkingSourceRef(ref);
  }));
  qsa("[data-thinking-selection-ref]").forEach(button => button.addEventListener("click", () => {
    const block = button.closest("[data-thinking-block-card]");
    const blockId = block?.dataset.thinkingBlockCard || "";
    const blockRef = thinkingBlockById(blockId)?.selection_refs?.[Number(button.dataset.thinkingSelectionRef)] || null;
    const draftRef = chatSelectionRefs()[Number(button.dataset.thinkingSelectionRef)] || null;
    navigateThinkingSourceRef(blockRef || draftRef);
  }));
  bindParagraphRefLinks(document);
}

async function sendThinkingChat() {
  if (!state.currentPaperId || !state.thinking || state.chatSending) return;
  const input = qs("#thinkingChatInput");
  const message = input?.value ?? state.chatDraft ?? "";
  if (!message.trim()) {
    toast("Write a message first");
    return;
  }
  state.chatDraft = message;
  state.chatError = "";
  state.chatScroll = { top: 0, atEnd: true };
  state.chatSending = true;
  renderWritingPane();
  setThinkingSaveState("Thinking...", "saving");
  let newBlockId = "";
  try {
    const response = await api(`/api/papers/${encodeURIComponent(state.currentPaperId)}/chat`, {
      method: "POST",
      body: JSON.stringify({ message, mode: state.chatMode, selection_refs: chatSelectionRefs(), use_project_context: state.chatUseProjectContext, project: currentPaperProject() }),
    });
    state.thinking = normalizeThinkingData(response.thinking || state.thinking, { seed: false });
    if (state.payload) state.payload.thinking = state.thinking;
    newBlockId = response.block?.id || state.thinking.blocks?.[0]?.id || "";
    state.chatDraft = "";
    state.chatSelectionDraft = null;
  } catch (error) {
    state.chatError = error.message;
    setThinkingSaveState("Generate failed", "error");
    toast(`Reply failed: ${error.message}`);
  } finally {
    const followReply = state.chatScroll.atEnd;
    const focus = document.activeElement;
    const keepComposing = !focus || focus === document.body || Boolean(focus.closest?.("#thinkingChatComposer"));
    state.chatSending = false;
    renderSensemakingPanel();
    if (newBlockId && followReply) requestAnimationFrame(() => focusThinkingBlockCard(newBlockId));
    else if (newBlockId) toast("New AI reply");
    if (followReply && keepComposing) qs("#thinkingChatInput")?.focus({ preventScroll: true });
  }
}

async function generateReadingNarrative() {
  if (!state.currentPaperId || !state.thinking || state.readingNarrativeGenerating) return;
  state.readingNarrativeGenerating = true;
  renderWritingPane();
  setThinkingSaveState("Generating narrative...", "saving");
  let newBlockId = "";
  try {
    const response = await api(`/api/papers/${encodeURIComponent(state.currentPaperId)}/reading-narrative`, {
      method: "POST",
      body: JSON.stringify({ use_project_context: state.chatUseProjectContext, project: currentPaperProject() }),
    });
    state.thinking = normalizeThinkingData(response.thinking || state.thinking, { seed: false });
    if (state.payload) state.payload.thinking = state.thinking;
    newBlockId = response.block?.id || state.thinking.blocks?.[0]?.id || "";
    toast("Reading narrative added");
  } catch (error) {
    setThinkingSaveState("Narrative failed", "error");
    toast(`Narrative failed: ${error.message}`);
  } finally {
    state.readingNarrativeGenerating = false;
    renderSensemakingPanel();
    if (newBlockId) requestAnimationFrame(() => focusThinkingBlockCard(newBlockId));
  }
}

function askAiFromCurrentSelection() {
  const selection = getReaderSelection() || (state.currentSelection?.segment_id ? state.currentSelection : null);
  if (!selection) {
    toast("Select text inside the paper first");
    return;
  }
  const y = window.scrollY || document.documentElement.scrollTop || 0;
  state.chatMode = "source";
  state.thinkingComposerMode = "chat";
  state.chatSelectionDraft = selection;
  state.chatDraft = "请解释这段原文在论文中的含义，并说明它回答了什么问题。";
  activateView("reader");
  setWorkspaceMode("split");
  setReaderSidePane("sensemaking");
  state.thinkingTab = "writing";
  renderSensemakingPanel();
  requestAnimationFrame(() => {
    window.scrollTo({ top: y, behavior: "auto" });
    qs("#thinkingChatInput")?.focus({ preventScroll: true });
  });
}

function thinkingBlockHtml(block) {
  const projectContext = block.project_context && block.project_context.card_count ? `<span>Project context: ${escapeHtml(block.project_context.project || "project")} · ${escapeHtml(block.project_context.card_count)} cards</span>` : "";
  const promptHtml = block.prompt ? `<div class="thinking-message thinking-message-user"><span class="thinking-message-role">${block.mode === "reading_narrative" ? "Request" : "You"}</span><div class="thinking-block-prompt"><p>${escapeHtml(block.prompt)}</p>${selectionRefsHtml(block.selection_refs)}</div></div>` : "";
  const sourceLinks = hasInlineParagraphRefs(block.content) ? "" : sourceRefsHtml(block.source_refs);
  return `
    <section class="thinking-block" data-thinking-block-card="${escapeHtml(block.id)}">
      ${promptHtml}
      <div class="thinking-message thinking-message-ai">
        ${thinkingBlockHeaderHtml(block)}
        <div class="thinking-block-body">
          <div class="thinking-text" data-thinking-block="${escapeHtml(block.id)}" tabindex="0" aria-label="AI response">${applyThinkingHighlights(block.content || "", block.id)}</div>
        </div>
        ${thinkingAnnotationCardsHtml(block.id)}
        ${sourceLinks}
        <details class="thinking-edit-details">
          <summary>Message options</summary>
          <div class="thinking-message-details">
            <span>${escapeHtml(modeLabel(block.mode))}${block.model ? ` · ${escapeHtml(block.model)}` : ""}</span>
            ${projectContext}
          </div>
          ${!isAgentThinkingBlock(block) ? `<label class="sense-label">Original question<input class="sense-input" data-thinking-prompt="${escapeHtml(block.id)}" value="${escapeHtml(block.prompt || block.title || "")}" /></label>` : ""}
          <label class="sense-label">Edit reply<textarea class="sense-textarea" data-thinking-content="${escapeHtml(block.id)}" rows="8" spellcheck="false">${escapeHtml(block.content || "")}</textarea></label>
          <button class="secondary-button thinking-delete-message" data-delete-thinking-block="${escapeHtml(block.id)}" type="button">Delete conversation turn</button>
        </details>
      </div>
    </section>`;
}

function rememberThinkingChatScroll(history) {
  if (!history?.isConnected || !history.clientHeight || history.dataset.paperId !== state.currentPaperId) return;
  state.chatScroll = {
    top: history.scrollTop,
    atEnd: history.scrollHeight - history.clientHeight - history.scrollTop < 24,
  };
}

function restoreThinkingChatScroll() {
  const history = qs("#thinkingChatHistory");
  const position = state.chatScroll;
  if (!history || history.dataset.paperId !== state.currentPaperId) return;
  requestAnimationFrame(() => {
    if (!history.isConnected || !history.clientHeight || history.dataset.paperId !== state.currentPaperId) return;
    history.scrollTop = position.atEnd ? history.scrollHeight : position.top;
  });
}

function resizeThinkingChatInput() {
  const input = qs("#thinkingChatInput");
  if (!input?.clientHeight) return;
  input.style.height = "auto";
  input.style.height = `${Math.min(160, input.scrollHeight)}px`;
  if (state.chatScroll.atEnd) restoreThinkingChatScroll();
}

function scrollThinkingContentIntoView(node, align = "start") {
  const history = node.closest("#thinkingChatHistory");
  if (!history) {
    node.scrollIntoView({ behavior: "smooth", block: align });
    return;
  }
  const inset = align === "center" ? Math.max(12, (history.clientHeight - node.offsetHeight) / 2) : 12;
  history.scrollTop += node.getBoundingClientRect().top - history.getBoundingClientRect().top - inset;
  rememberThinkingChatScroll(history);
}

function focusThinkingBlockCard(blockId) {
  const card = document.querySelector(`[data-thinking-block-card="${cssEscape(blockId)}"]`);
  if (!card) return;
  scrollThinkingContentIntoView(card);
  card.classList.add("focus-flash");
  setTimeout(() => card.classList.remove("focus-flash"), 1200);
}

function bindThinkingAnnotationControls(root = document) {
  const scoped = selector => Array.from((root || document).querySelectorAll?.(selector) || []);
  scoped("[data-focus-thinking-annotation]").forEach(button => button.addEventListener("click", () => focusThinkingAnnotation(button.dataset.focusThinkingAnnotation)));
  scoped("[data-inline-thinking-note]").forEach(button => button.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    openExistingThinkingAnnotationDrawer(button.dataset.inlineThinkingNote);
  }));
  scoped("[data-edit-thinking-annotation]").forEach(button => button.addEventListener("click", () => openExistingThinkingAnnotationDrawer(button.dataset.editThinkingAnnotation)));
  scoped("[data-delete-thinking-annotation]").forEach(button => button.addEventListener("click", () => deleteThinkingAnnotation(button.dataset.deleteThinkingAnnotation)));
  scoped("[data-thinking-tag-select]").forEach(select => select.addEventListener("change", async () => {
    const annotationId = select.dataset.thinkingTagSelect;
    const selectedValue = select.value;
    select.value = "";
    if (!annotationId || !selectedValue) return;
    await mutateThinkingAnnotationTags(annotationId, annotation => {
      annotation.tags = [...new Set([...annotationTags(annotation), selectedValue])];
    });
    toast("Tag added");
  }));
  scoped("[data-add-thinking-tag]").forEach(button => button.addEventListener("click", () => addTagToThinkingAnnotation(button.dataset.addThinkingTag)));
  scoped("[data-thinking-tag-input]").forEach(input => input.addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault();
      addTagToThinkingAnnotation(input.dataset.thinkingTagInput);
    }
  }));
  scoped("[data-remove-thinking-tag]").forEach(button => button.addEventListener("click", () => removeTagFromThinkingAnnotation(button.dataset.thinkingAnnotationId, button.dataset.removeThinkingTag)));
}

function renderWritingPane() {
  const root = qs("#writingPane");
  if (!root || !state.thinking) return;
  const blocks = [...(state.thinking.blocks || [])].reverse();
  const manual = state.thinkingComposerMode === "paste";
  root.innerHTML = `
    <div id="thinkingChatHistory" class="thinking-block-list" role="log" aria-label="Conversation" aria-live="off" data-paper-id="${escapeHtml(state.currentPaperId)}">
      ${blocks.map(thinkingBlockHtml).join("")}
      ${state.chatSending ? `<section class="thinking-block thinking-pending-turn" data-chat-pending>
        <div class="thinking-message thinking-message-user"><span class="thinking-message-role">You</span><div class="thinking-block-prompt"><p>${escapeHtml(state.chatDraft)}</p></div></div>
        <div class="thinking-message thinking-message-ai"><span class="thinking-message-role">AI</span><p class="thinking-chat-pending" role="status">Thinking...</p></div>
      </section>` : ""}
    </div>
    <div class="thinking-compose-dock">
      <div class="thinking-compose-modes" role="group" aria-label="Message input">
        <button class="reader-side-tab ${manual ? "" : "active"}" data-thinking-composer="chat" aria-pressed="${!manual}" type="button" ${state.chatSending ? "disabled" : ""}>Chat</button>
        <button class="reader-side-tab ${manual ? "active" : ""}" data-thinking-composer="paste" aria-pressed="${manual}" type="button" ${state.chatSending ? "disabled" : ""}>Paste AI output</button>
      </div>
      ${manual ? manualOutputComposerHtml() : chatComposerHtml()}
    </div>`;
  const history = qs("#thinkingChatHistory");
  history.addEventListener("scroll", () => rememberThinkingChatScroll(history), { passive: true });
  resizeThinkingChatInput();
  restoreThinkingChatScroll();
  qsa("[data-thinking-composer]").forEach(button => button.addEventListener("click", () => {
    state.thinkingComposerMode = button.dataset.thinkingComposer;
    renderWritingPane();
    qs(state.thinkingComposerMode === "paste" ? "#thinkingBlockContent" : "#thinkingChatInput")?.focus({ preventScroll: true });
  }));
  qsa("[data-chat-mode]").forEach(button => button.addEventListener("click", () => {
    state.chatMode = button.dataset.chatMode || "source";
    renderWritingPane();
  }));
  qs("#thinkingChatInput")?.addEventListener("input", event => {
    state.chatDraft = event.target.value;
    state.chatError = "";
    qs("#thinkingChatError").hidden = true;
    resizeThinkingChatInput();
  });
  const updateManualDraftStatus = () => {
    const status = qs(".manual-draft-status");
    if (status) status.hidden = !state.manualOutputDraft.prompt && !state.manualOutputDraft.content;
  };
  qs("#thinkingBlockPrompt")?.addEventListener("input", event => {
    state.manualOutputDraft.prompt = event.target.value;
    updateManualDraftStatus();
  });
  qs("#thinkingBlockContent")?.addEventListener("input", event => {
    state.manualOutputDraft.content = event.target.value;
    updateManualDraftStatus();
  });
  qs("#useProjectContext")?.addEventListener("change", event => { state.chatUseProjectContext = event.target.checked; });
  qs("#thinkingChatInput")?.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing && event.keyCode !== 229) {
      event.preventDefault();
      sendThinkingChat();
    }
  });
  qs("#sendThinkingChat")?.addEventListener("click", sendThinkingChat);
  qs("#generateReadingNarrative")?.addEventListener("click", generateReadingNarrative);
  qs("#clearChatSelection")?.addEventListener("click", () => {
    state.chatSelectionDraft = null;
    renderWritingPane();
  });
  qs("#addThinkingBlock")?.addEventListener("click", addThinkingBlockFromForm);
  qsa("[data-thinking-title]").forEach(input => input.addEventListener("input", () => updateThinkingBlockField(input.dataset.thinkingTitle, "title", input.value)));
  qsa("[data-thinking-prompt]").forEach(input => input.addEventListener("input", () => updateThinkingBlockField(input.dataset.thinkingPrompt, "prompt", input.value)));
  qsa("[data-thinking-content]").forEach(textarea => {
    textarea.addEventListener("input", () => updateThinkingBlockField(textarea.dataset.thinkingContent, "content", textarea.value));
    textarea.addEventListener("blur", renderSensemakingPanel);
  });
  qsa("[data-delete-thinking-block]").forEach(button => button.addEventListener("click", () => deleteThinkingBlock(button.dataset.deleteThinkingBlock)));
  qsa("[data-thinking-color]").forEach(button => button.addEventListener("click", () => addThinkingHighlightFromSelection(button.dataset.thinkingBlock, button.dataset.thinkingColor, false)));
  qsa("[data-thinking-note]").forEach(button => button.addEventListener("click", () => addThinkingHighlightFromSelection(button.dataset.thinkingNote, "yellow", true)));
  bindThinkingSourceLinks();
  bindThinkingAnnotationControls(root);
}

function renderSensemakingPanel() {
  const panel = qs("#sensemakingPanel");
  if (!panel) return;
  qsa("[data-thinking-tab]").forEach(button => button.classList.toggle("active", button.dataset.thinkingTab === state.thinkingTab));
  qs("#explainPane")?.classList.toggle("thinking-pane-hidden", state.thinkingTab !== "explain");
  qs("#writingPane")?.classList.toggle("thinking-pane-hidden", state.thinkingTab !== "writing");
  if (!state.payload) {
    qs("#explainPane").innerHTML = '<p class="muted">Select a paper to start sensemaking.</p>';
    qs("#writingPane").innerHTML = "";
    setThinkingSaveState("Ready", "");
    updateAnnotationToolbarVisibility();
    return;
  }
  if (state.workspaceMode === "read") return;
  if (!state.thinking) state.thinking = normalizeThinkingData(state.payload.thinking || {});
  renderExplainPane();
  renderWritingPane();
  setThinkingSaveState("Ready", "");
  updateAnnotationToolbarVisibility();
}

async function addThinkingBlockFromForm() {
  if (!state.thinking) return;
  const promptInput = qs("#thinkingBlockPrompt");
  const contentInput = qs("#thinkingBlockContent");
  const content = contentInput?.value || "";
  if (!content.trim()) {
    toast("Paste an AI output first");
    return;
  }
  const now = new Date().toISOString();
  state.thinking.blocks.unshift({
    id: `tb-${Date.now().toString(36)}`,
    type: "ai_output",
    title: "AI output",
    prompt: promptInput?.value || "",
    content,
    created_at: now,
    updated_at: now,
  });
  if (promptInput) promptInput.value = "";
  if (contentInput) contentInput.value = "";
  state.manualOutputDraft = { prompt: "", content: "" };
  renderSensemakingPanel();
  requestAnimationFrame(() => focusThinkingBlockCard(state.thinking.blocks[0]?.id || ""));
  try {
    await saveThinking({ silent: true });
    toast("AI output saved");
  } catch (error) {
    setThinkingSaveState("Save failed", "error");
    toast(`AI output is not saved: ${error.message}. Keep this tab open and retry.`);
  }
}

function updateThinkingBlockField(blockId, field, value) {
  const block = thinkingBlockById(blockId);
  if (!block || !["title", "content", "prompt"].includes(field)) return;
  block[field] = value;
  block.updated_at = new Date().toISOString();
  scheduleThinkingSave();
}

async function deleteThinkingBlock(blockId) {
  if (!state.thinking || !blockId) return;
  const block = thinkingBlockById(blockId);
  const confirmed = window.confirm(`Delete this conversation turn and its highlights/notes?\n\n${block?.prompt || block?.title || blockId}`);
  if (!confirmed) return;
  try {
    const response = await api(`/api/papers/${encodeURIComponent(state.currentPaperId)}/thinking/blocks/${encodeURIComponent(blockId)}`, { method: "DELETE" });
    state.thinking = normalizeThinkingData(response.thinking || state.thinking, { seed: false });
    if (state.payload) state.payload.thinking = state.thinking;
    renderSensemakingPanel();
    toast("Conversation turn deleted");
  } catch (error) {
    toast(`Delete failed: ${error.message}`);
  }
}

function rawOffsetWithinRenderedMarkdown(container, node, offset) {
  const element = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
  const anchor = element?.closest?.("[data-raw-start]");
  if (!anchor) return textOffsetWithin(container, node, offset);
  const rawStart = Number(anchor.dataset.rawStart || 0);
  return rawStart + textOffsetWithin(anchor, node, offset);
}

function getThinkingSelection(blockId = "") {
  const selection = window.getSelection();
  const text = selection ? selection.toString().trim() : "";
  if (!selection || selection.rangeCount === 0 || !text) return null;
  const range = selection.getRangeAt(0);
  const startContainer = range.startContainer.nodeType === Node.TEXT_NODE ? range.startContainer.parentElement : range.startContainer;
  const endContainer = range.endContainer.nodeType === Node.TEXT_NODE ? range.endContainer.parentElement : range.endContainer;
  const startText = startContainer?.closest?.(".thinking-text");
  const endText = endContainer?.closest?.(".thinking-text");
  if (!startText || !endText || startText !== endText) return null;
  const selectedBlockId = startText.dataset.thinkingBlock || "";
  if (blockId && selectedBlockId !== blockId) return null;
  const start = rawOffsetWithinRenderedMarkdown(startText, range.startContainer, range.startOffset);
  const end = rawOffsetWithinRenderedMarkdown(startText, range.endContainer, range.endOffset);
  if (end <= start) return null;
  return { block_id: selectedBlockId, target: "thinking", quote: text, range: { start, end } };
}

function openThinkingAnnotationDrawer(blockId, color, selectionInfo = null) {
  if (noteDrawerHasChanges() && !closeDrawer()) return;
  const selection = selectionInfo || getThinkingSelection(blockId);
  if (!selection) {
    toast("Select text inside this AI output first");
    return;
  }
  const block = thinkingBlockById(selection.block_id);
  state.pendingAnnotation = null;
  state.pendingThinkingAnnotation = { ...selection, color };
  qs("#drawerAnchor").textContent = `AI output · ${block?.title || selection.block_id}`;
  qs("#drawerQuote").textContent = selection.quote;
  qs("#noteText").value = "";
  qs("#customTagText").value = "";
  renderNoteTagOptions();
  openNoteDrawerAtPointer();
}

function openExistingThinkingAnnotationDrawer(annotationId) {
  if (noteDrawerHasChanges() && !closeDrawer()) return;
  const annotation = state.thinking?.annotations?.find(item => item.id === annotationId);
  if (!annotation) return;
  const block = thinkingBlockById(annotation.block_id);
  state.pendingAnnotation = null;
  state.pendingThinkingAnnotation = { ...annotation, editing_id: annotation.id };
  qs("#drawerAnchor").textContent = `AI output · ${block?.title || annotation.block_id}`;
  qs("#drawerQuote").textContent = annotation.quote || "";
  qs("#noteText").value = annotation.note || "";
  qs("#customTagText").value = "";
  renderNoteTagOptions(annotationTags(annotation));
  openNoteDrawerAtPointer();
}

function addThinkingHighlightFromSelection(blockId, color, includeNote) {
  const selection = getThinkingSelection(blockId);
  if (!selection) {
    toast("Select text inside this AI output first");
    return;
  }
  if (includeNote) {
    openThinkingAnnotationDrawer(blockId, color, selection);
    return;
  }
  state.pendingThinkingAnnotation = { ...selection, color };
  savePendingThinkingAnnotation(false);
}

async function savePendingThinkingAnnotation(includeNote) {
  if (!state.pendingThinkingAnnotation || !state.thinking) return;
  if (state.pendingThinkingAnnotation.editing_id) {
    const annotation = state.thinking.annotations.find(item => item.id === state.pendingThinkingAnnotation.editing_id);
    if (!annotation) return;
    const blockId = annotation.block_id;
    annotation.note = includeNote ? qs("#noteText").value : annotation.note || "";
    annotation.tags = selectedDrawerTags();
    annotation.updated_at = new Date().toISOString();
    closeDrawer({ saved: true });
    await saveThinking({ silent: true });
    refreshThinkingAnnotationSurfaces(blockId);
    toast("Note updated");
    return;
  }
  const item = {
    id: `ta-${Date.now().toString(36)}`,
    type: "range",
    target: "thinking",
    ...state.pendingThinkingAnnotation,
    note: includeNote ? qs("#noteText").value : "",
    tags: selectedDrawerTags(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  state.thinking.annotations.push(item);
  closeDrawer({ saved: true });
  await saveThinking({ silent: true });
  refreshThinkingAnnotationSurfaces(item.block_id);
  toast("Saved locally");
}

function focusThinkingAnnotation(annotationId) {
  const mark = document.querySelector(`.thinking-text [data-annotation-id="${cssEscape(annotationId)}"]`);
  if (!mark) {
    const annotation = state.thinking?.annotations?.find(item => item.id === annotationId);
    if (annotation?.block_id === paperBriefBlockId) {
      setWorkspaceMode("split");
      scrollToParagraph("paper-brief");
      return;
    }
    if (annotation?.block_id) setWorkspaceMode("think");
    return;
  }
  scrollThinkingContentIntoView(mark, "center");
  mark.classList.add("focus-flash");
  setTimeout(() => mark.classList.remove("focus-flash"), 1200);
}

async function deleteThinkingAnnotation(annotationId) {
  if (!state.thinking || !annotationId) return;
  const annotation = state.thinking.annotations.find(item => item.id === annotationId);
  state.thinking.annotations = state.thinking.annotations.filter(item => item.id !== annotationId);
  refreshThinkingAnnotationSurfaces(annotation?.block_id || "");
  await saveThinking({ silent: true });
  toast("Note deleted");
}

async function deleteThinkingAnnotationFromPaper(paperId, annotationId) {
  if (!paperId || !annotationId) return;
  if (paperId === state.currentPaperId) {
    await deleteThinkingAnnotation(annotationId);
    refreshAllNotesInBackground();
    return;
  }
  const payload = paperId === state.currentPaperId ? state.payload : await api(`/api/papers/${encodeURIComponent(paperId)}`);
  const thinking = normalizeThinkingData(payload?.thinking || {}, { seed: false });
  thinking.annotations = (thinking.annotations || []).filter(item => item.id !== annotationId);
  const response = await queuePaperWrite(paperId, "thinking", thinking);
  invalidatePaperCache(paperId);
  state.notesPreviewCache.delete(paperId);
  if (paperId === state.currentPaperId) {
    state.thinking = normalizeThinkingData(response.thinking || thinking, { seed: false });
    if (state.payload) state.payload.thinking = state.thinking;
    renderReader();
  }
  if (state.notesPreview.paperId === paperId && state.notesPreview.annotationId === annotationId) {
    state.notesPreview = { paperId: "", annotationId: "", segmentId: "", note: null, payload: null, loading: false, error: "" };
  }
  state.allNotes = (state.allNotes || []).filter(note => !(note.paper_id === paperId && note.id === annotationId));
  renderNotes();
  renderSidebar();
  refreshAllNotesInBackground();
  toast("Note deleted");
}

async function mutateThinkingAnnotationTags(annotationId, updater) {
  const annotation = state.thinking?.annotations?.find(item => item.id === annotationId);
  if (!annotation) return;
  const blockId = annotation.block_id;
  updater(annotation);
  annotation.updated_at = new Date().toISOString();
  refreshThinkingAnnotationSurfaces(blockId);
  await saveThinking({ silent: true });
}

async function addTagToThinkingAnnotation(annotationId) {
  const input = document.querySelector(`[data-thinking-tag-input="${cssEscape(annotationId)}"]`);
  const tag = input?.value?.trim();
  if (!tag) return;
  input.value = "";
  await mutateThinkingAnnotationTags(annotationId, annotation => {
    annotation.tags = [...new Set([...annotationTags(annotation), tag])];
  });
  toast("Tag added");
}

async function removeTagFromThinkingAnnotation(annotationId, tag) {
  await mutateThinkingAnnotationTags(annotationId, annotation => {
    annotation.tags = annotationTags(annotation).filter(item => item !== tag);
  });
  toast("Tag removed");
}

function bindReaderProcessButtons() {
  qsa("[data-process-paper]").forEach(button => {
    button.addEventListener("click", () => processPaper(button.dataset.processPaper, button.dataset.mode));
  });
}

function renderReader() {
  renderTranslationStatus();
  updateMarginLayout();
  renderReadingTeacherStatus();
  if (!state.payload) {
    disconnectReadingProgressTracker();
    const toolbar = qs("#annotationToolbar");
    if (toolbar) toolbar.style.display = "none";
    qs("#paperMeta").innerHTML = '<div class="meta-title">No paper selected</div>';
    qs("#documentRoot").innerHTML = '<p class="muted">Add a PDF in Library to begin.</p>';
    window.CSS?.highlights?.delete("reading-teacher");
    window.CSS?.highlights?.delete("reading-teacher-focus");
    renderSensemakingPanel();
    return;
  }
  renderPaperMeta();
  const root = qs("#documentRoot");
  const paragraphs = state.payload?.segments || [];
  const metadata = state.payload?.metadata || {};
  const mode = processingMode(metadata);
  const status = processingStatus(metadata);
  updateAnnotationToolbarVisibility();
  if (!paragraphs.length && paperParsingPending(metadata)) {
    disconnectReadingProgressTracker();
    root.innerHTML = '<section class="process-card"><h2>正在准备 Markdown 原文</h2></section>';
    renderSensemakingPanel();
    return;
  }
  if (!paragraphs.length && status === "failed") {
    disconnectReadingProgressTracker();
    root.innerHTML = `<section class="process-card"><h2>PDF 解析失败</h2><p class="error-text">${escapeHtml(metadata.processing_error || "请检查 PDF 和本地解析器。")}</p><button class="secondary-button" data-process-paper="${escapeHtml(state.currentPaperId)}" data-mode="deep">重试解析原文</button></section>`;
    bindReaderProcessButtons();
    renderSensemakingPanel();
    return;
  }
  if (mode === "library-only" || status === "not_processed") {
    disconnectReadingProgressTracker();
    root.innerHTML = `
      <section class="process-card" id="skim-summary">
        <h2>准备阅读全文</h2>
        <div class="process-actions">
          <button class="primary-button" data-process-paper="${escapeHtml(state.currentPaperId)}" data-mode="deep">解析原文并阅读</button>
        </div>
      </section>`;
    bindReaderProcessButtons();
    renderSensemakingPanel();
    return;
  }
  if (mode === "skim") {
    disconnectReadingProgressTracker();
    const skimMarkdown = state.payload?.skim_summary || state.payload?.skim_analysis?.skim_summary || "";
    root.innerHTML = `
      ${paperBriefCardHtml()}
      <article class="process-card skim-markdown-card" id="skim-markdown-breakdown">
        <div class="skim-card-header">
          <span class="pill">Markdown breakdown</span>
          <a class="secondary-button mini-button" href="/api/papers/${escapeHtml(state.currentPaperId)}/reader-md" target="_blank">Open MD</a>
        </div>
        ${skimMarkdown ? skimSummaryHtml(skimMarkdown) : '<p class="muted">No skim markdown is available yet.</p>'}
      </article>
      <article class="process-card skim-card" id="skim-summary">
        <div class="skim-card-header">
          <span class="pill">略读模式</span>
          <button class="secondary-button" data-process-paper="${escapeHtml(state.currentPaperId)}" data-mode="deep">解析 PDF 全文</button>
        </div>
        <h2>略读模式</h2>
        <p>这里保持轻量：先抓论文主线、贡献和可写作的切入点。右侧 Sensemaking 可以粘贴 AI output，并按时间继续批注你的想法。</p>
      </article>`;
    bindReaderProcessButtons();
    bindPaperBriefCard();
    renderSensemakingPanel();
    return;
  }
  root.innerHTML = `${paperBriefCardHtml()}${paragraphs.map(paragraphHtml).join("")}`;
  bindPaperBriefCard();
  bindReaderDynamicEvents(root);
  refreshReadingTeacher();
  updateToolbarStatus();
  initReadingProgressTracker();
  renderSensemakingPanel();
}

function readerScoped(root, selector) {
  return Array.from((root || document).querySelectorAll?.(selector) || []);
}

function bindReaderDynamicEvents(root = document) {
  readerScoped(root, ".citation-link").forEach(button => {
    if (!button.dataset.refList) return;
    button.addEventListener("click", () => openReferenceModal(button.dataset.refList.split(",").filter(Boolean)));
  });
  bindParagraphRefLinks(root);
  readerScoped(root, ".figure-ref").forEach(button => {
    button.addEventListener("click", () => openFigureModal(button.dataset.figureNumber));
  });
  readerScoped(root, ".paper-figure-image").forEach(button => {
    button.addEventListener("click", () => openFigureModalBySrc(button.dataset.figureSrc));
  });
  readerScoped(root, "[data-jump-annotation]").forEach(button => {
    button.addEventListener("click", event => {
      if (event.target.closest("[data-delete-annotation], [data-edit-annotation]")) return;
      focusAnnotation(button.dataset.jumpAnnotation);
    });
  });
  readerScoped(root, "[data-expand-annotation]").forEach(button => {
    button.addEventListener("click", () => {
      const id = button.dataset.expandAnnotation;
      const expanded = !state.expandedMarginNotes.has(id);
      if (expanded) state.expandedMarginNotes.add(id);
      else state.expandedMarginNotes.delete(id);
      button.closest(".comment-card").classList.toggle("is-collapsed", !expanded);
      button.setAttribute("aria-expanded", String(expanded));
      button.textContent = expanded ? "Show less" : "Read full note";
    });
  });
  readerScoped(root, "[data-teacher-source]").forEach(button => {
    button.addEventListener("click", () => focusTeacherSource(button.dataset.teacherSource, Number(button.dataset.evidenceIndex)));
  });
  readerScoped(root, "[data-teacher-open]").forEach(button => {
    button.addEventListener("click", () => focusTeacherSource(button.dataset.teacherOpen, -1, { scroll: false, moveFocus: true }));
  });
  readerScoped(root, "[data-teacher-close]").forEach(button => {
    button.addEventListener("click", closeReadingTeacherCard);
  });
  readerScoped(root, "[data-teacher-card]").forEach(card => {
    card.addEventListener("keydown", event => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      event.stopPropagation();
      closeReadingTeacherCard();
    });
  });
  readerScoped(root, "[data-teacher-reflect]").forEach(button => {
    button.addEventListener("click", () => reflectOnTeacherCard(button.dataset.teacherReflect));
  });
  readerScoped(root, "[data-teacher-adopt]").forEach(button => {
    button.addEventListener("click", () => adoptTeacherDefinition(button.dataset.teacherAdopt));
  });
  readerScoped(root, "[data-open-definition-note]").forEach(button => {
    button.addEventListener("click", () => toggleSavedDefinitionNote(button.dataset.openDefinitionNote, true));
  });
  readerScoped(root, "[data-close-definition-note]").forEach(button => {
    button.addEventListener("click", () => toggleSavedDefinitionNote(button.dataset.closeDefinitionNote, false));
  });
  readerScoped(root, "[data-retry-definition-save]").forEach(button => {
    button.addEventListener("click", () => retrySavedDefinitionNote(button.dataset.retryDefinitionSave));
  });
  readerScoped(root, "[data-saved-definition]").forEach(card => {
    card.addEventListener("keydown", event => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      event.stopPropagation();
      toggleSavedDefinitionNote(card.dataset.savedDefinition, false);
    });
  });
  readerScoped(root, "[data-teacher-disclosure]").forEach(details => {
    details.addEventListener("toggle", () => {
      if (!details.isConnected) return;
      if (details.open) state.readingTeacher.openDetails.add(details.dataset.teacherDisclosure);
      else state.readingTeacher.openDetails.delete(details.dataset.teacherDisclosure);
    });
  });
  readerScoped(root, "[data-delete-annotation]").forEach(button => {
    button.addEventListener("click", event => {
      event.stopPropagation();
      deleteAnnotation(button.dataset.deleteAnnotation, button.dataset.paperId || state.currentPaperId);
    });
  });
  readerScoped(root, "[data-edit-annotation]").forEach(button => {
    button.addEventListener("click", event => {
      event.stopPropagation();
      openExistingAnnotationDrawer(button.dataset.editAnnotation);
    });
  });
  readerScoped(root, "[data-media-note]").forEach(button => {
    button.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      openMediaAnnotationDrawer(button.dataset.mediaNote, button.dataset.mediaKind);
    });
  });
}

function refreshReaderSegments(segmentIds = []) {
  if (!state.payload || processingMode(state.payload.metadata || {}) !== "deep") return false;
  const ids = [...new Set(segmentIds.filter(Boolean))];
  if (!ids.length) return false;
  let refreshed = false;
  for (const segmentId of ids) {
    const segment = (state.payload.segments || []).find(item => item.id === segmentId);
    const existing = document.getElementById(segmentId);
    if (!segment || !existing) return false;
    const wrapper = document.createElement("div");
    wrapper.innerHTML = paragraphHtml(segment).trim();
    const next = wrapper.firstElementChild;
    if (!next) return false;
    existing.replaceWith(next);
    bindReaderDynamicEvents(next);
    if (state.readingObserver) state.readingObserver.observe(next);
    refreshed = true;
  }
  if (refreshed) {
    refreshReadingTeacher();
    updateToolbarStatus();
    applyReadingProgressDecorations();
  }
  return refreshed;
}

function refreshReaderSegmentsOrRender(segmentIds = []) {
  if (!refreshReaderSegments(segmentIds)) renderReader();
}

function ensureFigureModal() {
  let modal = qs("#figureModal");
  if (modal) return modal;
  modal = document.createElement("aside");
  modal.id = "figureModal";
  modal.className = "figure-modal";
  modal.setAttribute("aria-hidden", "true");
  modal.innerHTML = `
    <div class="figure-panel" role="dialog" aria-modal="true" aria-labelledby="figureModalTitle">
      <div class="figure-header">
        <h2 id="figureModalTitle">Figure</h2>
        <button id="closeFigureModal" class="icon-button" title="Close">x</button>
      </div>
      <div id="figureModalBody" class="figure-body"></div>
    </div>`;
  document.body.appendChild(modal);
  qs("#closeFigureModal").addEventListener("click", closeFigureModal);
  modal.addEventListener("click", event => {
    if (event.target === modal) closeFigureModal();
  });
  return modal;
}

function closeFigureModal() {
  const modal = qs("#figureModal");
  if (!modal) return;
  modal.classList.remove("open");
  modal.setAttribute("aria-hidden", "true");
}

function openFigureModal(number) {
  const figure = state.figures[number];
  if (!figure) return;
  renderFigureModal(figure);
}

function openFigureModalBySrc(src) {
  const figure = Object.values(state.figures).find(item => item.src === src || item.images?.some(image => image.src === src)) || { number: "", src, caption: "" };
  renderFigureModal(figure);
}

function renderFigureModal(figure) {
  const modal = ensureFigureModal();
  const body = qs("#figureModalBody");
  const images = figure.images?.length ? figure.images : figure.src ? [{ src: figure.src }] : [];
  const page = Number(figure.page);
  const pdfUrl = `/api/papers/${encodeURIComponent(state.currentPaperId)}/pdf${Number.isInteger(page) && page > 0 ? `#page=${page}` : ""}`;
  qs("#figureModalTitle").textContent = figure.number ? `Figure ${figure.number}` : "Figure";
  body.innerHTML = `
    <div class="figure-source-actions">
      ${images.length > 1 ? `<p>Showing ${images.length} extracted parts together. For the original layout, open the PDF.</p>` : ""}
      ${state.payload?.metadata?.source_pdf ? `<a class="secondary-button mini-button" href="${escapeHtml(pdfUrl)}" target="_blank" rel="noopener">Open original PDF${Number.isInteger(page) && page > 0 ? ` · page ${page}` : ""}</a>` : ""}
    </div>
    ${images.length ? images.map((image, index) => `<figure class="figure-part">
      <img class="figure-modal-image" src="${escapeHtml(image.src)}" alt="${escapeHtml(figure.number ? `Figure ${figure.number}, part ${index + 1}` : "Paper figure")}" decoding="async">
      ${images.length > 1 ? `<figcaption>Part ${index + 1} / ${images.length}</figcaption>` : ""}
    </figure>`).join("") : '<p class="muted">No complete figure image was found. Please use the original PDF.</p>'}
    ${figure.caption ? `<p class="figure-caption-text">${escapeHtml(figure.caption)}</p>` : ""}`;
  body.querySelectorAll("img").forEach(image => image.addEventListener("error", () => {
    const message = document.createElement("p");
    message.className = "figure-image-error";
    message.textContent = "This extracted image is unavailable. Check the original PDF.";
    image.replaceWith(message);
  }, { once: true }));
  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
}

function ensureReferenceModal() {
  let modal = qs("#referenceModal");
  if (modal) return modal;
  modal = document.createElement("aside");
  modal.id = "referenceModal";
  modal.className = "reference-modal";
  modal.setAttribute("aria-hidden", "true");
  modal.innerHTML = `
    <div class="reference-panel" role="dialog" aria-modal="true" aria-labelledby="referenceModalTitle">
      <div class="reference-header">
        <h2 id="referenceModalTitle">参考文献</h2>
        <button id="closeReferenceModal" class="icon-button" title="Close">x</button>
      </div>
      <div id="referenceModalBody" class="reference-body"></div>
    </div>`;
  document.body.appendChild(modal);
  qs("#closeReferenceModal").addEventListener("click", closeReferenceModal);
  modal.addEventListener("click", event => {
    if (event.target === modal) closeReferenceModal();
  });
  return modal;
}

function closeReferenceModal() {
  const modal = qs("#referenceModal");
  if (!modal) return;
  modal.classList.remove("open");
  modal.setAttribute("aria-hidden", "true");
}

async function openReferenceModal(numbers) {
  const modal = ensureReferenceModal();
  const body = qs("#referenceModalBody");
  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
  body.innerHTML = numbers.map(number => referenceCardHtml({ ...(state.references[number] || { number, raw: `[${number}]` }), loadingOnline: true })).join("");
  bindReferenceAddButtons();
  numbers.forEach(number => {
    if (!state.references[number]?.abstract) loadReferenceCard(number);
  });
}

async function loadReferenceCard(number) {
  if (state.referenceLoads[number]) return state.referenceLoads[number];
  const loads = state.referenceLoads;
  loads[number] = loadReferenceCardOnce(number).finally(() => {
    delete loads[number];
  });
  return loads[number];
}

async function loadReferenceCardOnce(number) {
  const paperId = state.currentPaperId;
  const selector = `[data-reference-card="${cssEscape(number)}"]`;
  const cardNode = document.querySelector(selector);
  captureReferenceIntakeDraft(number);
  try {
    const data = await api(`/api/papers/${encodeURIComponent(paperId)}/references/${encodeURIComponent(number)}`);
    if (paperId !== state.currentPaperId) return;
    state.references[number] = data.reference;
    const latestNode = document.querySelector(selector) || cardNode;
    if (latestNode) latestNode.outerHTML = referenceCardHtml(data.reference);
  } catch (error) {
    if (paperId !== state.currentPaperId) return;
    if (cardNode) cardNode.outerHTML = referenceCardHtml({ number, raw: `Reference [${number}] not found`, error: error.message });
  }
  bindReferenceAddButtons();
}

function referenceLoadingHtml(number) {
  return `
    <section class="reference-card" data-reference-card="${escapeHtml(number)}">
      <div class="reference-raw">[${escapeHtml(number)}]</div>
      <p class="muted">Loading reference card...</p>
    </section>`;
}

function bindReferenceAddButtons() {
  qsa("[data-add-reference]").forEach(button => {
    if (button.dataset.bound === "true") return;
    button.dataset.bound = "true";
    button.addEventListener("click", () => addReferenceToLibrary(button.dataset.addReference));
  });
  qsa("[data-open-existing-reference]").forEach(button => {
    if (button.dataset.bound === "true") return;
    button.dataset.bound = "true";
    button.addEventListener("click", () => openExistingReferencePaper(button.dataset.openExistingReference));
  });
  qsa("[data-reference-importance]").forEach(button => {
    if (button.dataset.bound === "true") return;
    button.dataset.bound = "true";
    button.addEventListener("click", () => setReferenceImportance(button.dataset.referenceImportance, button.dataset.importanceLevel));
  });
  bindReferenceDraftInputs();
}

function emptyReferenceIntakeDraft() {
  return { selectedTag: "", customTag: "", selectedProject: "", customProject: "", importance: 0 };
}

function referenceIntakeDraft(number) {
  const key = String(number || "");
  if (!state.referenceIntakeDrafts[key]) state.referenceIntakeDrafts[key] = emptyReferenceIntakeDraft();
  return state.referenceIntakeDrafts[key];
}

function patchReferenceIntakeDraft(number, patch = {}) {
  const key = String(number || "");
  if (!key) return emptyReferenceIntakeDraft();
  state.referenceIntakeDrafts[key] = { ...referenceIntakeDraft(key), ...patch };
  return state.referenceIntakeDrafts[key];
}

function captureReferenceIntakeDraft(number) {
  const key = String(number || "");
  if (!key) return emptyReferenceIntakeDraft();
  const node = document.querySelector(`[data-reference-card="${cssEscape(key)}"]`);
  if (!node) return referenceIntakeDraft(key);
  return patchReferenceIntakeDraft(key, {
    selectedTag: node.querySelector(`[data-reference-tag-select="${cssEscape(key)}"]`)?.value?.trim() || "",
    customTag: node.querySelector(`[data-reference-tag-input="${cssEscape(key)}"]`)?.value?.trim() || "",
    selectedProject: normalizeProjectName(node.querySelector(`[data-reference-project-select="${cssEscape(key)}"]`)?.value || ""),
    customProject: normalizeProjectName(node.querySelector(`[data-reference-project-input="${cssEscape(key)}"]`)?.value || ""),
    importance: selectedReferenceImportance(key),
  });
}

function bindReferenceDraftInputs() {
  qsa("[data-reference-tag-select], [data-reference-tag-input], [data-reference-project-select], [data-reference-project-input]").forEach(input => {
    if (input.dataset.draftBound === "true") return;
    input.dataset.draftBound = "true";
    const number = input.dataset.referenceTagSelect || input.dataset.referenceTagInput || input.dataset.referenceProjectSelect || input.dataset.referenceProjectInput || "";
    const eventName = input.tagName === "SELECT" ? "change" : "input";
    input.addEventListener(eventName, () => captureReferenceIntakeDraft(number));
  });
}

function referenceImportanceEditorHtml(number, level = 0) {
  const current = normalizeImportanceLevel(level);
  return `<div class="importance-star-editor importance-star-editor-quick${current ? "" : " is-empty"}" aria-label="Reference paper importance">
    <div class="importance-star-buttons">
      ${[1, 2, 3].map(star => `<button class="importance-star-button ${star <= current ? "active" : ""}" data-reference-importance="${escapeHtml(number)}" data-importance-level="${star}" type="button" aria-label="${star === current ? "Clear importance" : `Set importance to ${star} star${star === 1 ? "" : "s"}`}" aria-pressed="${star <= current ? "true" : "false"}" title="${star === current ? "Click again to clear importance" : `Set to ${star}/${maxImportanceStars}`}">${star <= current ? "★" : "☆"}</button>`).join("")}
    </div>
    <span class="importance-star-label" data-reference-importance-label="${escapeHtml(number)}">${current ? `${current}/${maxImportanceStars}` : "No stars"}</span>
  </div>`;
}

function selectedReferenceImportance(number) {
  const buttons = qsa(`[data-reference-importance="${cssEscape(number)}"].active`);
  return buttons.reduce((level, button) => Math.max(level, normalizeImportanceLevel(button.dataset.importanceLevel)), 0);
}

function setReferenceImportance(number, level) {
  const clicked = normalizeImportanceLevel(level);
  const current = selectedReferenceImportance(number);
  const next = clicked === current ? 0 : clicked;
  qsa(`[data-reference-importance="${cssEscape(number)}"]`).forEach(button => {
    const star = normalizeImportanceLevel(button.dataset.importanceLevel);
    const active = star <= next;
    button.classList.toggle("active", active);
    button.textContent = active ? "★" : "☆";
    button.setAttribute("aria-pressed", active ? "true" : "false");
    button.setAttribute("aria-label", star === next ? "Clear importance" : `Set importance to ${star} star${star === 1 ? "" : "s"}`);
    button.title = star === next ? "Click again to clear importance" : `Set to ${star}/${maxImportanceStars}`;
  });
  const label = document.querySelector(`[data-reference-importance-label="${cssEscape(number)}"]`);
  if (label) label.textContent = next ? `${next}/${maxImportanceStars}` : "No stars";
  const editor = document.querySelector(`[data-reference-card="${cssEscape(number)}"] .importance-star-editor`);
  editor?.classList.toggle("is-empty", !next);
  patchReferenceIntakeDraft(number, { importance: next });
}

async function openExistingReferencePaper(paperId) {
  if (!paperId) return;
  closeReferenceModal();
  await loadPaper(paperId);
  activateView("reader");
}

function referenceCardHtml(card) {
  const number = card.number || card.id || "";
  const abstract = card.abstract || "";
  const abstractZh = card.abstract_zh || "";
  const pdfUrl = card.pdf_url || card.open_access_pdf_url || card.arxiv_pdf_url || "";
  const tagOptions = allLibraryTags();
  const projectOptions = allLibraryProjects();
  const existingPaper = libraryDuplicateByTitle(card.title || "");
  const draft = referenceIntakeDraft(number);
  return `
    <section class="reference-card" data-reference-card="${escapeHtml(number)}">
      <div class="reference-raw">${escapeHtml(card.raw || "")}</div>
      ${card.error ? `<p class="muted">${escapeHtml(card.error)}</p>` : `<div class="reference-actions">
        ${existingPaper
          ? `<button class="secondary-button reference-add-button" disabled type="button">已在 Library</button><button class="secondary-button" data-open-existing-reference="${escapeHtml(existingPaper.id)}" type="button">Open existing</button>`
          : `<button class="primary-button reference-add-button" data-add-reference="${escapeHtml(number)}">+ 添加</button>`}
        <span class="reference-help">${existingPaper ? `Already in Library · ${escapeHtml(duplicatePaperSummary(existingPaper) || paperTitle(existingPaper))}` : card.loadingOnline && !abstract ? "已显示本地解析，正在后台补在线摘要..." : pdfUrl ? "添加后会尝试自动下载开放 PDF" : "添加该文章以便稍后阅读，status: unread"}</span>
        ${existingPaper ? "" : `<div class="reference-intake-grid">
          <label class="reference-field">
            <span>Paper tag</span>
            <select data-reference-tag-select="${escapeHtml(number)}">
              <option value="">Add existing tag...</option>
              ${tagOptions.map(tag => `<option value="${escapeHtml(tag)}" ${tag === draft.selectedTag ? "selected" : ""}>${escapeHtml(libraryTagLabel(tag))}</option>`).join("")}
            </select>
          </label>
          <label class="reference-field">
            <span>Custom tag</span>
            <input data-reference-tag-input="${escapeHtml(number)}" placeholder="Custom tag" value="${escapeHtml(draft.customTag)}" />
          </label>
          <label class="reference-field">
            <span>Project</span>
            <select data-reference-project-select="${escapeHtml(number)}">
              <option value="">Add project...</option>
              ${projectOptions.map(project => `<option value="${escapeHtml(project)}" ${project === draft.selectedProject ? "selected" : ""}>${escapeHtml(project)}</option>`).join("")}
            </select>
          </label>
          <label class="reference-field">
            <span>New project</span>
            <input data-reference-project-input="${escapeHtml(number)}" placeholder="New project" value="${escapeHtml(draft.customProject)}" />
          </label>
          <div class="reference-field reference-importance-field">
            <span>Importance</span>
            ${referenceImportanceEditorHtml(number, draft.importance)}
          </div>
        </div>`}
      </div>`}
      <dl class="reference-meta">
        <dt>标题</dt>
        <dd>${escapeHtml(card.title || "Unknown title")}</dd>
        <dt>作者</dt>
        <dd>${escapeHtml(card.authors || "Unknown authors")}</dd>
        ${card.venue || card.year ? `<dt>来源</dt><dd>${escapeHtml([card.venue, card.year].filter(Boolean).join(" · "))}</dd>` : ""}
        ${card.url ? `<dt>链接</dt><dd><a href="${escapeHtml(card.url)}" target="_blank" rel="noreferrer">${escapeHtml(card.url)}</a></dd>` : ""}
        ${pdfUrl ? `<dt>PDF</dt><dd><a href="${escapeHtml(pdfUrl)}" target="_blank" rel="noreferrer">${escapeHtml(pdfUrl)}</a></dd>` : ""}
        <dt>摘要</dt>
        <dd>${abstract ? escapeHtml(abstract) : '<span class="muted">未从在线元数据中找到摘要。</span>'}</dd>
        <dt>中文摘要</dt>
        <dd>${abstractZh ? escapeHtml(abstractZh) : '<span class="muted">暂无中文摘要。</span>'}</dd>
      </dl>
    </section>`;
}

async function addReferenceToLibrary(number) {
  const card = state.references[number] || {};
  const cardNode = document.querySelector(`[data-reference-card="${cssEscape(number)}"]`);
  const button = document.querySelector(`[data-add-reference="${cssEscape(number)}"]`);
  const draft = captureReferenceIntakeDraft(number);
  const selectedTag = draft.selectedTag;
  const customTag = draft.customTag;
  const selectedProject = draft.selectedProject;
  const customProject = draft.customProject;
  const projects = uniqueTags([selectedProject, customProject].filter(Boolean));
  if (customProject && !allLibraryProjects().includes(customProject)) {
    state.libraryCustomProjects = uniqueTags([...state.libraryCustomProjects, customProject]);
    saveCustomLibraryProjects();
  }
  const body = {
    title: cardNode?.querySelector(".reference-meta dd")?.textContent?.trim() || card.title,
    doi: card.doi || "",
    url: card.url || "",
    pdf_url: card.pdf_url || card.open_access_pdf_url || card.arxiv_pdf_url || "",
    open_access_pdf_url: card.open_access_pdf_url || "",
    semantic_scholar_url: card.semantic_scholar_url || "",
    arxiv_id: card.arxiv_id || "",
    tags: [...new Set([selectedTag, customTag].filter(Boolean))],
    projects,
    importance: draft.importance || "",
  };
  if (button) {
    button.disabled = true;
    button.textContent = "添加中...";
  }
  const response = await api(`/api/papers/${encodeURIComponent(state.currentPaperId)}/references/${encodeURIComponent(number)}/add`, {
    method: "POST",
    body: JSON.stringify(body),
  });
  if (response.duplicate) {
    toast("Already in Library");
    delete state.referenceIntakeDrafts[String(number || "")];
    await loadLibrary();
    const latestNode = document.querySelector(`[data-reference-card="${cssEscape(number)}"]`);
    if (latestNode) latestNode.outerHTML = referenceCardHtml({ ...card, title: response.existing?.title || body.title || card.title });
    bindReferenceAddButtons();
    return;
  }
  if (response.pdf_attached) toast("已添加到 Library，并开始后台解析 PDF");
  else if (response.pdf_error) toast(`已添加到 Library；PDF 自动下载失败：${response.pdf_error}`);
  else toast("已添加到 Library，status: unread");
  delete state.referenceIntakeDrafts[String(number || "")];
  if (button) button.textContent = "已添加";
  await loadLibrary();
}

function textOffsetWithin(container, node, offset) {
  const ignoredSelector = "[data-ignore-selection-offset]";
  const isIgnored = candidate => candidate?.nodeType === Node.ELEMENT_NODE && candidate.matches?.(ignoredSelector);
  let length = 0;
  let found = false;
  const visit = current => {
    if (!current || found) return;
    if (isIgnored(current)) {
      if (current === node || current.contains?.(node)) found = true;
      return;
    }
    if (current.nodeType === Node.ELEMENT_NODE && current.hasAttribute("data-annotation-source-length")
      && current !== node && !current.contains(node)) {
      length += Number(current.dataset.annotationSourceLength);
      return;
    }
    if (current === node) {
      if (current.nodeType === Node.TEXT_NODE) {
        length += Math.max(0, Math.min(offset, current.textContent.length));
      } else {
        Array.from(current.childNodes || []).slice(0, Math.max(0, offset)).forEach(visit);
      }
      found = true;
      return;
    }
    if (current.nodeType === Node.TEXT_NODE) {
      length += current.textContent.length;
      return;
    }
    Array.from(current.childNodes || []).forEach(visit);
  };
  visit(container);
  return length;
}

const alignmentStopwords = new Set([
  "about", "after", "again", "also", "among", "because", "between", "could", "these", "those", "their", "there", "which", "while",
  "would", "should", "through", "within", "without", "using", "based", "paper", "study", "result", "results", "system", "systems",
  "users", "model", "models", "process", "support", "supports", "supporting", "decision", "making", "reasoning", "traces",
]);

function meaningfulAlignmentTokens(text) {
  const raw = displayText(text, { trim: false });
  const citationTokens = Array.from(raw.matchAll(/\[(\d+(?:\s*,\s*\d+|\s*[-–]\s*\d+)*)\]/g))
    .flatMap(match => match[1].split(/\s*,\s*|\s*[-–]\s*/));
  const wordTokens = raw.match(/\b[A-Za-z][A-Za-z-]{3,}\b|\b\d{2,4}\b/g) || [];
  const tokens = [...citationTokens, ...wordTokens]
    .map(token => token.replace(/[()[\].,;:!?]/g, "").trim())
    .filter(token => token.length >= 2)
    .filter(token => !alignmentStopwords.has(token.toLowerCase()));
  return [...new Set(tokens)].sort((a, b) => b.length - a.length).slice(0, 18);
}

function regexEscape(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function findTokenHits(text, tokens) {
  const hits = [];
  const raw = String(text || "");
  for (const token of tokens) {
    if (!token) continue;
    const pattern = /^\d+$/.test(token)
      ? new RegExp(`(?<!\\d)${regexEscape(token)}(?!\\d)`, "gi")
      : new RegExp(regexEscape(token), "gi");
    for (const match of raw.matchAll(pattern)) {
      hits.push({ start: match.index || 0, end: (match.index || 0) + match[0].length, token });
    }
  }
  return hits.sort((a, b) => a.start - b.start || b.token.length - a.token.length);
}

function rangeContainingOffset(ranges, offset) {
  if (!ranges.length) return null;
  return ranges.find(range => offset >= range.start && offset <= range.end)
    || ranges.reduce((best, range) => Math.abs((range.start + range.end) / 2 - offset) < Math.abs((best.start + best.end) / 2 - offset) ? range : best, ranges[0]);
}

function clampRangeToText(range, text) {
  const length = String(text || "").length;
  const start = Math.max(0, Math.min(length, Number(range?.start || 0)));
  const end = Math.max(start, Math.min(length, Number(range?.end || start)));
  return end > start ? { start, end } : null;
}

function trimRangeToText(range, text) {
  const raw = String(text || "");
  const clamped = clampRangeToText(range, raw);
  if (!clamped) return null;
  let { start, end } = clamped;
  while (start < end && /\s/.test(raw[start])) start += 1;
  while (end > start && /\s/.test(raw[end - 1])) end -= 1;
  return end > start ? { start, end } : null;
}

function tokenHitEvidence(hits) {
  const uniqueTokens = new Set(hits.map(hit => String(hit.token || "").toLowerCase()));
  const strongHits = hits.filter(hit => /^\d+$/.test(hit.token) || String(hit.token || "").length >= 6);
  return { uniqueCount: uniqueTokens.size, strongCount: strongHits.length };
}

function pairedCandidateRange(range, text) {
  const trimmed = trimRangeToText(range, text);
  if (!trimmed) return null;
  const candidate = String(text || "").slice(trimmed.start, trimmed.end);
  const mediaIndex = candidate.search(/!\[[^\]]*\]\(/);
  if (mediaIndex > 0) return trimRangeToText({ start: trimmed.start, end: trimmed.start + mediaIndex }, text);
  return trimmed;
}

function rangeFromSharedTokens(toText, target, tokens, ratioHint) {
  const hits = findTokenHits(toText, tokens);
  if (!hits.length) return null;
  const sentences = sentenceRanges(toText, target);
  const sentenceScores = sentences.map(sentence => {
    const sentenceHits = hits.filter(hit => hit.start >= sentence.start && hit.end <= sentence.end);
    const evidence = tokenHitEvidence(sentenceHits);
    const score = sentenceHits.reduce((sum, hit) => sum + Math.max(1, hit.token.length / 4), 0);
    const center = (sentence.start + sentence.end) / 2;
    const distance = Math.abs(center / Math.max(1, toText.length) - ratioHint);
    const distancePenalty = distance * 2;
    return { sentence, sentenceHits, evidence, distance, score: score - distancePenalty };
  }).filter(item => item.sentenceHits.length);
  if (!sentenceScores.length) return null;
  sentenceScores.sort((a, b) => b.score - a.score);
  const best = sentenceScores[0];
  if (best.evidence.uniqueCount < 2 && !(best.evidence.strongCount >= 1 && best.distance <= 0.22)) return null;
  const minHit = Math.min(...best.sentenceHits.map(hit => hit.start));
  const maxHit = Math.max(...best.sentenceHits.map(hit => hit.end));
  const sentenceLength = best.sentence.end - best.sentence.start;
  if (sentenceLength > 260 && maxHit > minHit) {
    const windowStart = Math.max(best.sentence.start, minHit - 56);
    const windowEnd = Math.min(best.sentence.end, maxHit + 88);
    return pairedCandidateRange({ start: windowStart, end: windowEnd }, toText);
  }
  return pairedCandidateRange(best.sentence, toText);
}

function selectionSentenceSpan(sentences, range) {
  const start = Number(range?.start || 0);
  const end = Number(range?.end || start);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return null;
  const overlaps = sentences.map((sentence, index) => ({
    index,
    sentence,
    overlap: Math.max(0, Math.min(sentence.end, end) - Math.max(sentence.start, start)),
  })).filter(item => item.overlap > 0);
  if (!overlaps.length) return null;
  return {
    startIndex: overlaps[0].index,
    endIndex: overlaps[overlaps.length - 1].index,
    overlap: overlaps.reduce((sum, item) => sum + item.overlap, 0),
  };
}

function mappedSentenceIndex(index, fromCount, toCount) {
  if (fromCount <= 1 || toCount <= 1) return 0;
  return Math.max(0, Math.min(toCount - 1, Math.round((index / (fromCount - 1)) * (toCount - 1))));
}

function sentenceAlignedPairedRange(fromText, toText, selectionInfo, target) {
  const fromSentences = sentenceRanges(fromText, selectionInfo.target);
  const toSentences = sentenceRanges(toText, target);
  if (!fromSentences.length || !toSentences.length) return null;
  const span = selectionSentenceSpan(fromSentences, selectionInfo.range);
  if (!span) return null;
  const fromCount = fromSentences.length;
  const toCount = toSentences.length;
  const countDelta = Math.abs(fromCount - toCount);
  if (fromCount > 1 && toCount > 1 && countDelta > Math.max(1, Math.floor(Math.max(fromCount, toCount) * 0.25))) return null;
  const sourceSentenceStart = fromSentences[span.startIndex].start;
  const sourceSentenceEnd = fromSentences[span.endIndex].end;
  const sourceSentenceLength = Math.max(1, sourceSentenceEnd - sourceSentenceStart);
  const selectionLength = Math.max(0, Number(selectionInfo.range?.end || 0) - Number(selectionInfo.range?.start || 0));
  const coversEnoughSentence = span.overlap / sourceSentenceLength >= 0.45 || selectionLength >= 90 || span.endIndex > span.startIndex;
  if (!coversEnoughSentence) return null;
  const startIndex = mappedSentenceIndex(span.startIndex, fromCount, toCount);
  const endIndex = Math.max(startIndex, mappedSentenceIndex(span.endIndex, fromCount, toCount));
  return pairedCandidateRange({ start: toSentences[startIndex].start, end: toSentences[endIndex].end }, toText);
}

function pairedRangeForSelection(segment, selectionInfo) {
  const target = selectionInfo.target === "source" ? "translation" : "source";
  const fromText = selectionInfo.target === "source" ? displayTextPreservingMath(segment.markdown, { trim: false }) : displayTextPreservingMath(segment.translation, { trim: false });
  const toText = target === "source" ? displayTextPreservingMath(segment.markdown, { trim: false }) : displayTextPreservingMath(segment.translation, { trim: false });
  if (!fromText || !toText) return null;
  const midpoint = (selectionInfo.range.start + selectionInfo.range.end) / 2;
  const ratioHint = midpoint / Math.max(1, fromText.length);
  const quote = selectionInfo.quote || fromText.slice(selectionInfo.range.start, selectionInfo.range.end);
  const localContext = fromText.slice(Math.max(0, selectionInfo.range.start - 90), Math.min(fromText.length, selectionInfo.range.end + 90));
  const selectedSpan = selectionSentenceSpan(sentenceRanges(fromText, selectionInfo.target), selectionInfo.range);
  const spansMultipleSentences = selectedSpan && selectedSpan.endIndex > selectedSpan.startIndex;
  const tokenRange = spansMultipleSentences ? null : (
    rangeFromSharedTokens(toText, target, meaningfulAlignmentTokens(quote), ratioHint)
      || rangeFromSharedTokens(toText, target, meaningfulAlignmentTokens(`${quote} ${localContext}`), ratioHint)
  );
  const range = tokenRange || sentenceAlignedPairedRange(fromText, toText, selectionInfo, target);
  if (!range) return null;
  const pairedQuote = toText.slice(range.start, range.end);
  if (target === "translation" && /[\u4e00-\u9fff]/.test(toText) && !/[\u4e00-\u9fff]/.test(pairedQuote)) return null;
  if (target === "source" && /[A-Za-z]{3,}/.test(toText) && !/[A-Za-z]{3,}/.test(pairedQuote)) return null;
  return { ...range, target, quote: pairedQuote };
}

function sentenceRanges(text, target) {
  const raw = String(text || "");
  if (!raw.trim()) return [];
  if (typeof Intl !== "undefined" && Intl.Segmenter) {
    try {
      const locale = target === "translation" ? "zh" : "en";
      const ranges = Array.from(new Intl.Segmenter(locale, { granularity: "sentence" }).segment(raw))
        .map(segment => trimRangeToText({ start: segment.index, end: segment.index + segment.segment.length }, raw))
        .filter(Boolean);
      if (ranges.length) return ranges;
    } catch (error) {
      // Fall back to punctuation splitting below when Intl.Segmenter is unavailable or rejects a locale.
    }
  }
  const ranges = [];
  let start = 0;
  const punctuation = target === "translation" ? /[。！？；.!?;]/ : /[.!?;]/;
  for (let index = 0; index < raw.length; index += 1) {
    const char = raw[index];
    const next = raw[index + 1] || "";
    if (!punctuation.test(char)) continue;
    if (target === "source" && next && !/\s/.test(next)) continue;
    let end = index + 1;
    while (start < end && /\s/.test(raw[start])) start += 1;
    while (end > start && /\s/.test(raw[end - 1])) end -= 1;
    if (end > start) ranges.push({ start, end });
    start = index + 1;
  }
  let end = raw.length;
  while (start < end && /\s/.test(raw[start])) start += 1;
  while (end > start && /\s/.test(raw[end - 1])) end -= 1;
  if (end > start) ranges.push({ start, end });
  return ranges.length ? ranges : [{ start: 0, end: raw.length }];
}

function getReaderSelection() {
  const selection = window.getSelection();
  const text = selection ? selection.toString().trim() : "";
  if (!selection || selection.rangeCount === 0 || !text) return null;
  const range = selection.getRangeAt(0);
  const startContainer = range.startContainer.nodeType === Node.TEXT_NODE ? range.startContainer.parentElement : range.startContainer;
  const endContainer = range.endContainer.nodeType === Node.TEXT_NODE ? range.endContainer.parentElement : range.endContainer;
  const startText = startContainer?.closest?.(".annotation-text");
  const endText = endContainer?.closest?.(".annotation-text");
  if (!startText || !endText) return null;
  const target = startText.dataset.target || "source";
  if ((endText.dataset.target || "source") !== target) return null;
  if (startText !== endText) return getMultiSegmentReaderSelection(range, startText, endText, target, text);
  let start = textOffsetWithin(startText, range.startContainer, range.startOffset);
  let end = textOffsetWithin(startText, range.endContainer, range.endOffset);
  if (end <= start) return null;
  const segment = state.payload?.segments?.find(item => item.id === startText.dataset.pid);
  if (!segment) return null;
  if (target === "translation") {
    start = originalTranslationOffset(segment, start, "start");
    end = originalTranslationOffset(segment, end, "end");
  }
  const info = {
    segment_id: startText.dataset.pid,
    target: startText.dataset.target || "source",
    quote: text,
    range: { start, end },
  };
  info.paired_range = pairedRangeForSelection(segment, info);
  return info;
}

function annotationTextValue(segment, target) {
  return target === "translation"
    ? displayTextPreservingMath(segment?.translation || "", { trim: false })
    : displayTextPreservingMath(segment?.markdown || "", { trim: false });
}

function selectedAnnotationTextNodes(range, target) {
  return qsa("#documentRoot .annotation-text")
    .filter(node => (node.dataset.target || "source") === target && range.intersectsNode(node))
    .sort((left, right) => left.compareDocumentPosition(right) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1);
}

function selectionPartForNode(node, range, startText, endText, target) {
  const segment = state.payload?.segments?.find(item => item.id === node.dataset.pid);
  if (!segment) return null;
  const text = target === "translation" ? translationPresentation(segment).text : annotationTextValue(segment, target);
  let start = 0;
  let end = text.length;
  if (node === startText) start = textOffsetWithin(node, range.startContainer, range.startOffset);
  if (node === endText) end = textOffsetWithin(node, range.endContainer, range.endOffset);
  start = Math.max(0, Math.min(text.length, start));
  end = Math.max(start, Math.min(text.length, end));
  const quote = text.slice(start, end).trim();
  if (!quote || end <= start) return null;
  if (target === "translation") {
    start = originalTranslationOffset(segment, start, "start");
    end = originalTranslationOffset(segment, end, "end");
  }
  const info = { segment_id: node.dataset.pid, target, quote, range: { start, end } };
  info.paired_range = pairedRangeForSelection(segment, info);
  return info;
}

function getMultiSegmentReaderSelection(range, startText, endText, target, selectedText) {
  const parts = selectedAnnotationTextNodes(range, target)
    .map(node => selectionPartForNode(node, range, startText, endText, target))
    .filter(Boolean);
  if (!parts.length) return null;
  if (parts.length === 1) return parts[0];
  return {
    multi: true,
    segment_id: parts[0].segment_id,
    target,
    quote: selectedText,
    parts,
    range: parts[0].range,
  };
}

function updateToolbarStatus() {
  const status = qs("#toolbarStatus");
  if (!status) return;
  const selection = getReaderSelection();
  const thinkingSelection = selection ? null : getThinkingSelection();
  state.currentSelection = selection || thinkingSelection;
  status.textContent = selection
    ? `${selection.target === "translation" ? "中文" : "原文"} · ${selection.multi ? `${selection.parts.length} segments · ` : ""}${selection.quote.length} chars selected`
    : thinkingSelection
      ? `AI output · ${thinkingSelection.quote.length} chars selected`
    : "";
  positionAnnotationToolbar();
}

function selectedTextForParagraph(paragraphId) {
  const selection = getReaderSelection();
  if (!selection || selection.segment_id !== paragraphId) return "";
  return selection.quote;
}

function fallbackSegmentSelection(paragraphId, color) {
  const paragraph = state.payload.segments.find(item => item.id === paragraphId);
  if (!paragraph) return null;
  const selected = getReaderSelection();
  if (selected && selected.segment_id === paragraphId) return selected;
  const quote = displayText(paragraph.markdown, { trim: false });
  return { segment_id: paragraphId, target: "source", quote, range: { start: 0, end: quote.length }, paired_range: pairedRangeForSelection(paragraph, { target: "source", range: { start: 0, end: quote.length } }) };
}

function openAnnotationDrawer(paragraphId, color, selectionInfo = null) {
  if (noteDrawerHasChanges() && !closeDrawer()) return;
  const selection = selectionInfo || fallbackSegmentSelection(paragraphId, color);
  if (!selection) return;
  state.pendingAnnotation = { ...selection, color };
  state.pendingThinkingAnnotation = null;
  qs("#drawerAnchor").textContent = selection.multi ? `${selection.parts.length} segments` : paragraphId;
  qs("#drawerQuote").textContent = selection.quote;
  qs("#noteText").value = "";
  qs("#customTagText").value = "";
  renderNoteTagOptions();
  openNoteDrawerAtPointer();
}

function openExistingAnnotationDrawer(annotationId) {
  if (noteDrawerHasChanges() && !closeDrawer()) return;
  let annotation = state.annotations.find(item => item.id === annotationId);
  if (!annotation) return;
  const groupId = annotationGroupId(annotation);
  if (groupId) {
    annotation = state.annotations.find(item => annotationGroupId(item) === groupId && (item.note || annotationGroupIndex(item) === 0)) || annotation;
  }
  state.pendingThinkingAnnotation = null;
  state.pendingAnnotation = { ...annotation, editing_id: annotation.id };
  const groupCount = groupId ? annotationsInGroup(groupId).length : Number(annotation.group_count || 0);
  qs("#drawerAnchor").textContent = groupCount > 1 ? `${groupCount} segments` : annotation.segment_id || "Highlight";
  qs("#drawerQuote").textContent = annotation.quote || "";
  qs("#noteText").value = annotation.note || "";
  qs("#customTagText").value = "";
  renderNoteTagOptions(annotationTags(annotation));
  openNoteDrawerAtPointer();
}

function openMediaAnnotationDrawer(segmentId, target) {
  if (noteDrawerHasChanges() && !closeDrawer()) return;
  const existing = mediaAnnotationFor(segmentId, target);
  if (existing) {
    openExistingAnnotationDrawer(existing.id);
    return;
  }
  const segment = state.payload?.segments?.find(item => item.id === segmentId);
  if (!segment) return;
  const info = segmentMediaInfo(segment, target);
  state.pendingThinkingAnnotation = null;
  state.pendingAnnotation = {
    segment_id: segmentId,
    target,
    type: target,
    color: "blue",
    quote: info.quote,
    media_src: info.src || "",
    range: { start: 0, end: Math.max(1, info.quote.length) },
  };
  qs("#drawerAnchor").textContent = `${segmentId} · ${target === "table" ? "Table" : "Image"}`;
  qs("#drawerQuote").textContent = info.quote;
  qs("#noteText").value = "";
  qs("#customTagText").value = "";
  renderNoteTagOptions();
  openNoteDrawerAtPointer();
}

function renderNoteTagOptions(selectedTags = []) {
  const root = qs("#noteTagOptions");
  if (!root) return;
  const selected = new Set(selectedTags);
  root.setAttribute("data-filter-tag-scope", "");
  root.classList.add("tag-options-with-search");
  root.innerHTML = `
    <input class="tag-options-search" data-filter-tag-options type="search" placeholder="Search note tags" aria-label="Search note tags" />
    <div class="tag-options-list">
      ${allNoteTags(selectedTags).map(tag => `
        <label class="tag-option" ${filterableTagOptionAttrs(tag)}>
          <input type="checkbox" value="${escapeHtml(tag)}" ${selected.has(tag) ? "checked" : ""}>
          <span>${escapeHtml(tag)}</span>
        </label>`).join("")}
    </div>
    <div class="muted small-text" data-filter-empty hidden>No matching note tags</div>`;
  initTagOptionFilters(root);
}

function selectedDrawerTags() {
  return qsa("#noteTagOptions input:checked").map(input => input.value.trim()).filter(Boolean);
}

function addCustomDrawerTag() {
  const input = qs("#customTagText");
  const value = input.value.trim();
  if (!value) return;
  const selected = [...selectedDrawerTags(), value];
  input.value = "";
  renderNoteTagOptions(selected);
}

function addHighlightFromSelection(color, includeNote) {
  const thinkingSelection = getThinkingSelection() || (state.currentSelection?.target === "thinking" ? state.currentSelection : null);
  if (thinkingSelection) {
    if (includeNote) {
      openThinkingAnnotationDrawer(thinkingSelection.block_id, color, thinkingSelection);
      return;
    }
    state.pendingThinkingAnnotation = { ...thinkingSelection, color };
    savePendingThinkingAnnotation(false);
    return;
  }
  const selection = getReaderSelection() || (state.currentSelection?.segment_id ? state.currentSelection : null);
  if (!selection) {
    toast("Select text inside the paper first");
    return;
  }
  state.pendingThinkingAnnotation = null;
  if (includeNote) {
    openAnnotationDrawer(selection.segment_id, color, selection);
    return;
  }
  state.pendingAnnotation = { ...selection, color };
  savePendingAnnotation(false);
}

function noteDrawerSnapshot() {
  return JSON.stringify({ note: qs("#noteText")?.value || "", tags: selectedDrawerTags() });
}

function noteDrawerHasChanges() {
  return Boolean((state.pendingAnnotation || state.pendingThinkingAnnotation)
    && qs("#noteDrawer")?.classList.contains("open") && noteDrawerSnapshot() !== state.drawerInitialValue);
}

function closeDrawer(options = {}) {
  if (!options.saved && noteDrawerHasChanges() && !window.confirm("Discard the unsaved note? Use Save to keep your original words.")) return false;
  if (qs("#noteDrawer")?.contains(document.activeElement)) document.activeElement?.blur();
  qs("#noteDrawer").classList.remove("open");
  qs("#noteDrawer").setAttribute("aria-hidden", "true");
  state.pendingAnnotation = null;
  state.pendingThinkingAnnotation = null;
  state.drawerInitialValue = "";
  refreshDrawerMode();
  renderReaderSaveStatus();
  return true;
}

function waitForNextFrame() {
  return new Promise(resolve => requestAnimationFrame(resolve));
}

function setNoteDrawerSaving(isSaving) {
  const saveNote = qs("#saveNote");
  const saveHighlight = qs("#saveHighlightOnly");
  if (saveNote) {
    saveNote.disabled = Boolean(isSaving);
    saveNote.textContent = isSaving ? "Saving..." : "Save Note";
  }
  if (saveHighlight) {
    saveHighlight.disabled = Boolean(isSaving);
  }
}

async function persistCurrentPaperAnnotations(toastMessage = "", options = {}) {
  const paperId = state.currentPaperId;
  if (!paperId) return;
  const optimistic = options.optimistic !== false;
  if (optimistic) {
    if (state.payload?.annotations) state.payload.annotations.annotations = state.annotations;
    state.notesPreviewCache.delete(state.currentPaperId);
    syncCurrentPaperNotesLocally({ renderNotes: shouldRenderNotesImmediately(), renderSidebar: false });
    refreshReaderSegmentsOrRender(options.segmentIds || []);
    markReadingProgressDirtyFromAnnotations();
  }
  await queuePaperWrite(paperId, "annotations", { version: 1, paper_id: paperId, annotations: state.annotations });
  if (!optimistic && paperId === state.currentPaperId) {
    if (state.payload?.annotations) state.payload.annotations.annotations = state.annotations;
    state.notesPreviewCache.delete(state.currentPaperId);
    syncCurrentPaperNotesLocally({ renderNotes: shouldRenderNotesImmediately(), renderSidebar: false });
    refreshReaderSegmentsOrRender(options.segmentIds || []);
    markReadingProgressDirtyFromAnnotations();
  }
  if (toastMessage) toast(toastMessage);
  if (paperId === state.currentPaperId) capturePaperSession();
  refreshAllNotesInBackground();
}

async function deleteDrawerNote() {
  const button = qs("#deleteDrawerNote");
  const annotationId = button?.dataset.annotationId || "";
  if (!annotationId) return;
  if (button.dataset.noteScope === "thinking") await deleteThinkingAnnotation(annotationId);
  else await deleteAnnotation(annotationId, state.currentPaperId);
  closeDrawer();
}

async function savePendingAnnotation(includeNote) {
  if (state.pendingThinkingAnnotation) {
    await savePendingThinkingAnnotation(includeNote);
    return;
  }
  if (!state.pendingAnnotation) return;
  setNoteDrawerSaving(true);
  try {
  if (state.pendingAnnotation.editing_id) {
    const annotation = state.annotations.find(item => item.id === state.pendingAnnotation.editing_id);
    if (!annotation) return;
    annotation.note = includeNote ? qs("#noteText").value : annotation.note || "";
    annotation.tags = selectedDrawerTags();
    annotation.updated_at = new Date().toISOString();
    const segmentIds = [annotation.segment_id].filter(Boolean);
    closeDrawer({ saved: true });
    await persistCurrentPaperAnnotations("Note updated", { segmentIds });
    return;
  }
  const now = new Date().toISOString();
  if (state.pendingAnnotation.multi && Array.isArray(state.pendingAnnotation.parts)) {
    const groupId = `ag-${Date.now().toString(36)}`;
    const noteText = includeNote ? qs("#noteText").value : "";
    const tags = selectedDrawerTags();
    const groupItems = state.pendingAnnotation.parts.map((part, index) => ({
      id: `${groupId}-${index}`,
      type: "range",
      ...part,
      color: state.pendingAnnotation.color || "yellow",
      note: index === 0 ? noteText : "",
      tags: index === 0 ? tags : [],
      annotation_group_id: groupId,
      group_index: index,
      group_count: state.pendingAnnotation.parts.length,
      group_quote: state.pendingAnnotation.quote || "",
      created_at: now,
      updated_at: now,
    }));
    state.annotations.push(...groupItems);
    const segmentIds = groupItems.map(item => item.segment_id).filter(Boolean);
    closeDrawer({ saved: true });
    await persistCurrentPaperAnnotations("Saved multi-segment note", { segmentIds });
    return;
  }
  const item = {
    id: `a-${Date.now().toString(36)}`,
    type: "range",
    ...state.pendingAnnotation,
    note: includeNote ? qs("#noteText").value : "",
    tags: selectedDrawerTags(),
    created_at: now,
    updated_at: now,
  };
  state.annotations.push(item);
  closeDrawer({ saved: true });
  await persistCurrentPaperAnnotations("Saved locally", { segmentIds: [item.segment_id].filter(Boolean) });
  } catch (error) {
    toast(`Save failed: ${error.message}`);
  } finally {
    setNoteDrawerSaving(false);
  }
}

async function saveAnnotations() {
  await persistCurrentPaperAnnotations();
}

async function deleteAnnotation(annotationId, paperId = state.currentPaperId) {
  if (!annotationId || !paperId) return;
  const payload = paperId === state.currentPaperId ? state.payload : await api(`/api/papers/${encodeURIComponent(paperId)}`);
  const annotations = payload?.annotations?.annotations || [];
  const target = annotations.find(item => item.id === annotationId);
  const groupId = annotationGroupId(target);
  const changedSegmentIds = annotations.filter(item => groupId ? annotationGroupId(item) === groupId : item.id === annotationId).map(item => item.segment_id).filter(Boolean);
  const nextAnnotations = annotations.filter(item => groupId ? annotationGroupId(item) !== groupId : item.id !== annotationId);
  if (paperId === state.currentPaperId) {
    state.annotations = nextAnnotations;
    await persistCurrentPaperAnnotations("Note deleted", { segmentIds: changedSegmentIds });
    return;
  }
  await queuePaperWrite(paperId, "annotations", { version: 1, paper_id: paperId, annotations: nextAnnotations });
  invalidatePaperCache(paperId);
  state.notesPreviewCache.delete(paperId);
  if (state.notesPreview.paperId === paperId && (state.notesPreview.annotationId === annotationId || (groupId && annotationGroupId(state.notesPreview.note) === groupId))) {
    state.notesPreview = { paperId: "", annotationId: "", segmentId: "", note: null, payload: null, loading: false, error: "" };
  }
  if (paperId === state.currentPaperId) {
    state.annotations = nextAnnotations;
    if (state.payload?.annotations) state.payload.annotations.annotations = nextAnnotations;
    refreshReaderSegmentsOrRender(changedSegmentIds);
    markReadingProgressDirtyFromAnnotations();
    syncCurrentPaperNotesLocally({ renderNotes: shouldRenderNotesImmediately(), renderSidebar: false });
  } else {
    refreshAllNotesInBackground();
  }
  toast("Note deleted");
}

async function mutateAnnotationTags(paperId, annotationId, updater) {
  const payload = paperId === state.currentPaperId ? state.payload : await api(`/api/papers/${encodeURIComponent(paperId)}`);
  const annotations = payload?.annotations?.annotations || [];
  const annotation = annotations.find(item => item.id === annotationId);
  if (!annotation) return;
  updater(annotation);
  annotation.updated_at = new Date().toISOString();
  if (paperId === state.currentPaperId) {
    state.annotations = annotations;
    await persistCurrentPaperAnnotations("", { segmentIds: [annotation.segment_id].filter(Boolean) });
    return;
  }
  await queuePaperWrite(paperId, "annotations", { version: 1, paper_id: paperId, annotations });
  invalidatePaperCache(paperId);
  state.notesPreviewCache.delete(paperId);
  if (paperId === state.currentPaperId) {
    state.annotations = annotations;
    if (state.payload?.annotations) state.payload.annotations.annotations = annotations;
    refreshReaderSegmentsOrRender([annotation.segment_id].filter(Boolean));
    syncCurrentPaperNotesLocally({ renderNotes: shouldRenderNotesImmediately(), renderSidebar: false });
  } else {
    refreshAllNotesInBackground();
  }
}

async function addTagToAnnotation(annotationId, paperId = state.currentPaperId) {
  const input = document.querySelector(`[data-tag-input="${cssEscape(annotationId)}"]`);
  const tag = input?.value?.trim();
  if (!tag) return;
  input.value = "";
  await mutateAnnotationTags(paperId, annotationId, annotation => {
    annotation.tags = [...new Set([...annotationTags(annotation), tag])];
  });
  toast("Tag added");
}

async function removeTagFromAnnotation(annotationId, tag, paperId = state.currentPaperId) {
  await mutateAnnotationTags(paperId, annotationId, annotation => {
    annotation.tags = annotationTags(annotation).filter(item => item !== tag);
  });
  toast("Tag removed");
}

async function updateAnnotationFlowOverride(paperId, annotationId, flowId) {
  if (!paperId || !annotationId) return;
  await mutateAnnotationTags(paperId, annotationId, annotation => {
    if (flowId) {
      annotation.presentation_flow_id = flowId;
    } else {
      delete annotation.presentation_flow_id;
    }
  });
  toast(flowId ? "Note moved" : "Auto placement restored");
  renderSidebar();
}

function focusAnnotation(annotationId) {
  if (!annotationId) return;
  activateView("reader");
  const mark = document.querySelector(`[data-annotation-id="${cssEscape(annotationId)}"]`);
  if (!mark) {
    const annotation = state.annotations.find(item => item.id === annotationId);
    if (annotation?.segment_id) scrollToParagraph(annotation.segment_id);
    return;
  }
  mark.scrollIntoView({ behavior: "smooth", block: "center" });
  mark.classList.add("focus-flash");
  setTimeout(() => mark.classList.remove("focus-flash"), 1200);
}

function previewInlineMarkdown(text, paperId, options = {}) {
  return renderInlineContent(text, options, rawPart => {
  let safe = escapeHtml(displayText(options.images === false ? stripTranslationImages(rawPart) : rawPart, { trim: false }));
  safe = safe.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (match, alt, src) => {
    if (options.images === false) return "";
    const url = assetUrlForPaper(paperId, src);
    if (!url) return match;
    return `<img class="notes-source-image" src="${escapeHtml(url)}" alt="${escapeHtml(alt || "Paper image")}" loading="lazy">`;
  });
  safe = safe.replace(/`([^`]+)`/g, "<code>$1</code>");
  safe = safe.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  safe = safe.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  safe = safe.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');
  safe = autolinkPlainUrlsAndDois(safe);
  return safe;
  });
}

function splitPreviewInlineHtmlWithHighlights(text, annotations, target, paperId, options = {}) {
  const { text: raw, ranges } = annotationDisplayRanges(displayTextPreservingMath(text, { trim: false }),
    annotations, target, options.omissions);
  if (!ranges.length) return previewInlineMarkdown(raw, paperId, options);
  const parts = [];
  let cursor = 0;
  for (const { annotation, range } of ranges) {
    const start = Math.max(cursor, range.start);
    const end = Math.max(start, range.end);
    if (start > cursor) parts.push(previewInlineMarkdown(raw.slice(cursor, start), paperId, options));
    const color = annotation.color || "yellow";
    const active = annotation.id === state.notesPreview.annotationId ? " active" : "";
    const title = annotation.note || annotation.quote || "Highlight";
    parts.push(`<mark class="hl-${escapeHtml(color)} notes-source-mark${active}" data-preview-annotation-id="${escapeHtml(annotation.id || "")}" title="${escapeHtml(title)}">${previewInlineMarkdown(raw.slice(start, end), paperId, options)}</mark>`);
    cursor = end;
  }
  if (cursor < raw.length) parts.push(previewInlineMarkdown(raw.slice(cursor), paperId, options));
  return parts.join("");
}

function previewEffectiveAnnotationsFor(segment, payload, target) {
  const annotations = (payload?.annotations?.annotations || []).filter(annotation => annotation.segment_id === segment?.id);
  return annotations.map(annotation => {
    const directTarget = annotation.target || "source";
    if (!segment || directTarget === target || !annotation.range) return annotation;
    const recalculated = pairedRangeForSelection(segment, {
      target: directTarget,
      range: annotation.range,
      quote: annotation.quote || "",
    });
    return recalculated?.target === target ? { ...annotation, paired_range: recalculated } : { ...annotation, paired_range: null };
  });
}

function previewApplyHighlights(text, segment, target, payload, paperId, options = {}) {
  return splitPreviewInlineHtmlWithHighlights(text, previewEffectiveAnnotationsFor(segment, payload, target), target, paperId, {
    ...options, citations: false, images: target !== "translation",
  });
}

function previewHtmlTable(text) {
  const raw = String(text || "");
  const tableStart = raw.search(/<table[\s>]/i);
  const caption = tableStart > 0 ? displayText(raw.slice(0, tableStart)) : "";
  const parser = new DOMParser();
  const doc = parser.parseFromString(raw, "text/html");
  const table = doc.querySelector("table");
  if (!table) return `<pre class="source-text">${escapeHtml(displayTextPreservingMath(text))}</pre>`;
  const rows = Array.from(table.querySelectorAll("tr")).map(row => {
    const cells = Array.from(row.children).filter(cell => /^(td|th)$/i.test(cell.tagName));
    const html = cells.map(cell => {
      const tag = cell.tagName.toLowerCase() === "th" ? "th" : "td";
      const rowspan = Math.max(1, Math.min(20, Number(cell.getAttribute("rowspan") || 1)));
      const colspan = Math.max(1, Math.min(20, Number(cell.getAttribute("colspan") || 1)));
      const attrs = `${rowspan > 1 ? ` rowspan="${rowspan}"` : ""}${colspan > 1 ? ` colspan="${colspan}"` : ""}`;
      return `<${tag}${attrs}>${previewInlineMarkdown(cell.textContent, state.notesPreview.paperId)}</${tag}>`;
    }).join("");
    return html ? `<tr>${html}</tr>` : "";
  }).filter(Boolean).join("");
  if (!rows) return `<pre class="source-text">${escapeHtml(displayTextPreservingMath(text))}</pre>`;
  return `${caption ? `<div class="table-caption source-text">${previewInlineMarkdown(caption, state.notesPreview.paperId)}</div>` : ""}<div class="table-wrap"><table class="paper-table">${rows}</table></div>`;
}

function previewParagraphHtml(segment, payload, annotation) {
  const paperId = state.notesPreview.paperId;
  const pid = segment.id;
  const type = segment.kind || "paragraph";
  const text = segment.markdown || "";
  const isTableSegment = isTextTableSegment(segment);
  const active = pid === annotation?.segment_id ? " is-target" : "";
  let body = "";
  if (type === "heading") {
    const level = Math.min(Math.max(Number(segment.level || 2), 1), 3);
    const headingText = displayTextPreservingMath(text, { trim: false }).replace(/^#{1,6}\s+/, "");
    body = `<h${level}>${previewInlineMarkdown(headingText, paperId)}</h${level}>`;
  } else if (type === "code") {
    body = `<pre><code>${escapeHtml(text)}</code></pre>`;
  } else if (isHtmlTable(text)) {
    body = previewHtmlTable(text);
  } else if (isTableSegment) {
    body = renderPipeTable(text);
  } else {
    body = `<div class="source-text">${previewApplyHighlights(displayTextPreservingMath(text, { trim: false }), segment, "source", payload, paperId)}</div>`;
  }
  const translated = isTableSegment ? null : translationPresentation(segment);
  const translation = isTableSegment
    ? renderTableTranslation(segment)
    : stripTranslationImages(translated.text).trim()
      ? `<div class="translation">${previewApplyHighlights(displayTextPreservingMath(segment.translation, { trim: false }), segment, "translation", payload, paperId, { omissions: translated.omissions })}</div>`
      : "";
  return `<article class="notes-source-paragraph${active}" data-preview-pid="${escapeHtml(pid)}"><div class="notes-source-segment-id">${escapeHtml(pid)}</div>${body}${translation}</article>`;
}

function notesPreviewContextSegments(payload, segmentId) {
  const segments = payload?.segments || [];
  const index = segments.findIndex(segment => segment.id === segmentId);
  if (index < 0) return [];
  const indexes = new Set([index - 1, index, index + 1].filter(value => value >= 0 && value < segments.length));
  return Array.from(indexes).sort((a, b) => a - b).map(value => segments[value]);
}

function currentNotesPreviewAnnotation() {
  const payload = state.notesPreview.payload;
  const annotations = payload?.annotations?.annotations || [];
  return annotations.find(annotation => annotation.id === state.notesPreview.annotationId)
    || state.notesPreview.note
    || annotations.find(annotation => annotation.segment_id === state.notesPreview.segmentId)
    || null;
}

function isThinkingNoteItem(item) {
  return item?.source_scope === "thinking" || item?.target === "thinking" || Boolean(item?.thinking_block_id || item?.block_id);
}

function thinkingNoteBlockLabel(item) {
  const blockId = item?.thinking_block_id || item?.block_id || "";
  if (blockId === paperBriefBlockId) return "Paper Brief";
  return item?.thinking_block_title || "AI output";
}

function notesSourcePanelEmptyHtml() {
  return `
    <div class="notes-source-empty">
      <h2>Source Context</h2>
      <p>Select a note.</p>
    </div>`;
}

function renderNotesSourcePanel() {
  const root = qs("#notesSourcePanel");
  if (!root) return;
  if (state.notesPreview.loading) {
    root.innerHTML = '<div class="notes-source-empty"><h2>Source Context</h2><p>Loading original passage...</p></div>';
    return;
  }
  if (state.notesPreview.error) {
    root.innerHTML = `<div class="notes-source-empty"><h2>Source Context</h2><p class="error-text">${escapeHtml(state.notesPreview.error)}</p></div>`;
    return;
  }
  if (!state.notesPreview.payload) {
    root.innerHTML = notesSourcePanelEmptyHtml();
    return;
  }
  const payload = state.notesPreview.payload;
  const metadata = payload.metadata || {};
  const annotation = currentNotesPreviewAnnotation();
  if (annotation && isThinkingNoteItem(annotation)) {
    const blockLabel = thinkingNoteBlockLabel(annotation);
    root.innerHTML = `
      <div class="notes-source-header">
        <div>
          <span class="sense-kicker">Source Context</span>
          <h2>${escapeHtml(metadata.title || annotation.paper_title || state.notesPreview.paperId || "Untitled paper")}</h2>
          <p>${escapeHtml(blockLabel)}</p>
        </div>
        <button class="icon-button" data-close-notes-source title="Close source context" aria-label="Close source context">x</button>
      </div>
      <section class="notes-source-note" aria-label="Selected note">
        <div class="notes-source-note-header">
          <span>${escapeHtml(blockLabel)}</span>
          <button class="note-delete-button" data-delete-thinking-source-note="${escapeHtml(annotation.id || "")}" data-paper-id="${escapeHtml(state.notesPreview.paperId || "")}" title="Delete note" aria-label="Delete note">x</button>
        </div>
        ${annotation.note ? `<p>${escapeHtml(annotation.note)}</p>` : '<p class="muted">Highlight only</p>'}
        ${annotation.quote ? `<blockquote>${escapeHtml(annotation.quote)}</blockquote>` : ""}
        <div class="note-context-row"><span>${escapeHtml(annotationKindLabel(annotation))}</span><span>${escapeHtml(annotation.thinking_block_id || annotation.block_id || "")}</span></div>
      </section>
      <div class="notes-source-actions">
        <button class="primary-button" data-open-source-workspace="${escapeHtml(state.notesPreview.paperId)}" data-annotation-id="${escapeHtml(state.notesPreview.annotationId || "")}" data-block-id="${escapeHtml(annotation.thinking_block_id || annotation.block_id || "")}">Open in Workspace</button>
      </div>`;
    qs("#notesSourcePanel [data-close-notes-source]")?.addEventListener("click", closeNotesSourcePreview);
    qs("#notesSourcePanel [data-open-source-workspace]")?.addEventListener("click", () => openNotesSourceInWorkspace());
    qs("#notesSourcePanel [data-delete-thinking-source-note]")?.addEventListener("click", event => {
      const button = event.currentTarget;
      deleteThinkingAnnotationFromPaper(button.dataset.paperId || state.notesPreview.paperId, button.dataset.deleteThinkingSourceNote);
    });
    return;
  }
  const targetSegment = (payload.segments || []).find(segment => segment.id === (annotation?.segment_id || state.notesPreview.segmentId));
  const contextSegments = notesPreviewContextSegments(payload, targetSegment?.id || state.notesPreview.segmentId);
  const sectionPath = targetSegment?.section_path?.length ? targetSegment.section_path.join(" / ") : "Source passage";
  root.innerHTML = `
    <div class="notes-source-header">
      <div>
        <span class="sense-kicker">Source Context</span>
        <h2>${escapeHtml(metadata.title || annotation?.paper_title || state.notesPreview.paperId || "Untitled paper")}</h2>
        <p>${escapeHtml(sectionPath)}</p>
      </div>
      <button class="icon-button" data-close-notes-source title="Close source context" aria-label="Close source context">x</button>
    </div>
    ${annotation ? `<section class="notes-source-note" aria-label="Selected note">
      <div class="notes-source-note-header">
        ${isTeacherDefinition(annotation) ? '<span class="note-block-label">Saved AI definition</span>' : ""}
        <span>${escapeHtml(annotation.segment_id || state.notesPreview.segmentId || "Selected note")}</span>
        <button class="note-delete-button" data-delete-source-note="${escapeHtml(annotation.id || "")}" data-paper-id="${escapeHtml(state.notesPreview.paperId || "")}" title="Delete note" aria-label="Delete note">x</button>
      </div>
      ${annotation.note ? `<p>${escapeHtml(annotation.note)}</p>` : '<p class="muted">Highlight only</p>'}
      ${annotation.quote ? `<blockquote>${escapeHtml(annotation.quote)}</blockquote>` : ""}
      <div class="note-context-row"><span>${escapeHtml(annotationKindLabel(annotation))}</span><span>${escapeHtml(annotation.segment_id || state.notesPreview.segmentId || "")}</span></div>
    </section>` : ""}
    <div class="notes-source-context">
      ${contextSegments.length ? contextSegments.map(segment => previewParagraphHtml(segment, payload, annotation)).join("") : '<p class="muted">Original segment was not found in the parsed paper.</p>'}
    </div>
    <div class="notes-source-actions">
      <button class="primary-button" data-open-source-workspace="${escapeHtml(state.notesPreview.paperId)}" data-annotation-id="${escapeHtml(state.notesPreview.annotationId || "")}" data-segment-id="${escapeHtml(annotation?.segment_id || state.notesPreview.segmentId || "")}">Open in Workspace</button>
    </div>`;
  qs("#notesSourcePanel [data-close-notes-source]")?.addEventListener("click", closeNotesSourcePreview);
  qs("#notesSourcePanel [data-open-source-workspace]")?.addEventListener("click", () => openNotesSourceInWorkspace());
  qs("#notesSourcePanel [data-delete-source-note]")?.addEventListener("click", event => {
    const button = event.currentTarget;
    deleteAnnotation(button.dataset.deleteSourceNote, button.dataset.paperId || state.notesPreview.paperId);
  });
}

async function loadPaperPreviewPayload(paperId) {
  if (state.notesPreviewCache.has(paperId)) return state.notesPreviewCache.get(paperId);
  const payload = await api(`/api/papers/${encodeURIComponent(paperId)}`);
  state.notesPreviewCache.set(paperId, payload);
  return payload;
}

async function openNoteSourcePreview(paperId, annotationId, segmentId) {
  if (!paperId) return;
  const note = state.allNotes.find(item => item.id === annotationId && item.paper_id === paperId) || null;
  state.notesPreview = { paperId, annotationId: annotationId || "", segmentId: segmentId || note?.segment_id || "", note, payload: null, loading: true, error: "" };
  renderNotes();
  try {
    const payload = await loadPaperPreviewPayload(paperId);
    if (state.notesPreview.paperId !== paperId || state.notesPreview.annotationId !== (annotationId || "")) return;
    state.notesPreview = { ...state.notesPreview, payload, loading: false, error: "" };
  } catch (error) {
    state.notesPreview = { ...state.notesPreview, loading: false, error: `Could not load source: ${error.message}` };
  }
  renderNotes();
  requestAnimationFrame(() => {
    const target = qs('#notesSourcePanel .notes-source-paragraph.is-target');
    target?.scrollIntoView({ behavior: "smooth", block: "center" });
    target?.classList.add("focus-flash");
    setTimeout(() => target?.classList.remove("focus-flash"), 1200);
  });
}

function closeNotesSourcePreview() {
  state.notesPreview = { paperId: "", annotationId: "", segmentId: "", note: null, payload: null, loading: false, error: "" };
  renderNotes();
}

function clearNotesPreviewIfStale(notes = state.allNotes || []) {
  if (!state.notesPreview.paperId || !state.notesPreview.annotationId) return;
  const exists = notes.some(note => note.id === state.notesPreview.annotationId && note.paper_id === state.notesPreview.paperId);
  if (!exists) {
    state.notesPreview = { paperId: "", annotationId: "", segmentId: "", note: null, payload: null, loading: false, error: "" };
  }
}

async function openNotesSourceInWorkspace() {
  const { paperId, annotationId, segmentId } = state.notesPreview;
  if (!paperId) return;
  if (paperId !== state.currentPaperId) await loadPaper(paperId);
  activateView("reader");
  const annotation = currentNotesPreviewAnnotation();
  if (annotation && isThinkingNoteItem(annotation)) {
    const blockId = annotation.thinking_block_id || annotation.block_id || "";
    if (blockId === paperBriefBlockId) setWorkspaceMode("split");
    else setWorkspaceMode("think");
    focusThinkingAnnotation(annotationId);
    return;
  }
  if (annotationId) focusAnnotation(annotationId);
  else if (segmentId) scrollToParagraph(segmentId);
}

function renderNotes() {
  const root = qs("#notesRoot");
  if (document.body.dataset.activeView !== "notes") return;
  renderNoteProjectFilters();
  renderNoteTagFilters();
  const notes = state.allNotes || [];
  clearNotesPreviewIfStale(notes);
  const selectedFilters = state.selectedNoteFilters || [];
  const selectedProjects = state.selectedNoteProjects || [];
  const visibleAnnotations = notes.filter(item => noteMatchesProjectFilters(item, selectedProjects) && noteMatchesTagFilters(item, selectedFilters));
  if (!visibleAnnotations.length) {
    root.innerHTML = '<p class="muted">No notes yet. Highlight a passage in any paper to start.</p>';
    renderNotesSourcePanel();
    return;
  }
  root.innerHTML = visibleAnnotations.map(item => `
    <section class="note-row ${state.notesPreview.annotationId === item.id && state.notesPreview.paperId === item.paper_id ? "active" : ""}" data-note-row="${escapeHtml(item.id || "")}" data-paper-id="${escapeHtml(item.paper_id || "")}">
      <div class="note-row-header">
        <div class="note-main-content">
          ${item.note ? `<div class="note-user-block">
            <span class="note-block-label">${isTeacherDefinition(item) ? "Saved AI definition" : "Your note"}</span>
            <p class="note-text note-text-primary">${escapeHtml(item.note)}</p>
          </div>` : '<span class="note-row-kind">Highlight only</span>'}
          ${annotationMediaSrc(item, item.paper_id) ? `<img class="note-media-thumb" src="${escapeHtml(annotationMediaSrc(item, item.paper_id))}" alt="${escapeHtml(item.quote || "Media note")}" loading="lazy" decoding="async">` : ""}
          <div class="note-quote-block">
            <span class="note-block-label">Source passage</span>
            <div class="quote note-primary-quote"><mark class="hl-${escapeHtml(item.color || "yellow")}">${escapeHtml(item.quote || "")}</mark></div>
          </div>
        </div>
        <button class="note-delete-button" data-delete-annotation="${escapeHtml(item.id || "")}" data-paper-id="${escapeHtml(item.paper_id || "")}" title="Delete note">x</button>
      </div>
      <div class="note-context-row">
        <button class="note-context-link" data-jump="${escapeHtml(item.segment_id)}" data-paper-id="${escapeHtml(item.paper_id || "")}" data-annotation-id="${escapeHtml(item.id || "")}" aria-label="Preview original source for ${escapeHtml(item.paper_title || item.paper_id || "this note")}">${escapeHtml(item.paper_title || item.paper_id || "Untitled paper")}</button>
        ${projectsForNote(item).map(project => `<span class="note-project-pill" style="--tag-color: ${escapeHtml(projectColor(project, item.paper_project_colors || {}))}">${escapeHtml(project)}</span>`).join("")}
        <span>${escapeHtml(item.segment_id || "")}</span>
        <span>${escapeHtml(annotationKindLabel(item))}</span>
      ${item.paper_venue || item.paper_year ? `<span class="note-target-pill">${escapeHtml([item.paper_venue, item.paper_year].filter(Boolean).join(" · "))}</span>` : ""}
      </div>
      <div class="note-tags" aria-label="Note tags">
        ${annotationTags(item).map(tag => `<button class="note-tag" data-remove-tag="${escapeHtml(tag)}" data-paper-id="${escapeHtml(item.paper_id || "")}" data-annotation-id="${escapeHtml(item.id || "")}" title="Remove tag">${escapeHtml(tag)} ×</button>`).join("") || '<span class="muted">No tags</span>'}
      </div>
      <details class="note-tag-details">
        <summary>Tags</summary>
        <div class="note-tag-editor" data-filter-tag-scope>
          <div class="note-tag-picker">
            <input class="note-tag-search" data-filter-tag-options type="search" placeholder="Search existing tag" aria-label="Search existing note tag" />
            <div class="note-tag-picker-options">
              ${allNoteTags().map(tag => `<button class="tag-filter note-tag-add-option" data-add-existing-note-tag="${escapeHtml(tag)}" data-annotation-id="${escapeHtml(item.id || "")}" data-paper-id="${escapeHtml(item.paper_id || "")}" ${filterableTagOptionAttrs(tag)} type="button">${escapeHtml(tag)}</button>`).join("") || '<span class="muted small-text">No existing tags</span>'}
              <span class="muted small-text" data-filter-empty hidden>No matching tags</span>
            </div>
          </div>
          <input data-tag-input="${escapeHtml(item.id || "")}" data-paper-id="${escapeHtml(item.paper_id || "")}" placeholder="Custom tag" />
          <button class="secondary-button" data-add-tag="${escapeHtml(item.id || "")}" data-paper-id="${escapeHtml(item.paper_id || "")}">Add</button>
        </div>
      </details>
    </section>
  `).join("");
  qsa("[data-jump]").forEach(button => button.addEventListener("click", async () => {
    await openNoteSourcePreview(button.dataset.paperId, button.dataset.annotationId, button.dataset.jump);
  }));
  qsa("[data-add-existing-note-tag]").forEach(button => button.addEventListener("click", async event => {
    event.preventDefault();
    const annotationId = button.dataset.annotationId;
    const paperId = button.dataset.paperId || state.currentPaperId;
    const selectedValue = button.dataset.addExistingNoteTag;
    if (!annotationId || !selectedValue) return;
    await mutateAnnotationTags(paperId, annotationId, annotation => {
      annotation.tags = [...new Set([...annotationTags(annotation), selectedValue])];
    });
    toast("Tag added");
  }));
  qsa("[data-add-tag]").forEach(button => button.addEventListener("click", () => addTagToAnnotation(button.dataset.addTag, button.dataset.paperId)));
  qsa("[data-tag-input]").forEach(input => input.addEventListener("keydown", event => {
    if (event.key === "Enter") addTagToAnnotation(input.dataset.tagInput, input.dataset.paperId);
  }));
  qsa("[data-remove-tag]").forEach(button => button.addEventListener("click", () => removeTagFromAnnotation(button.dataset.annotationId, button.dataset.removeTag, button.dataset.paperId)));
  qsa("#notesRoot [data-delete-annotation]").forEach(button => button.addEventListener("click", () => deleteAnnotation(button.dataset.deleteAnnotation, button.dataset.paperId)));
  initTagOptionFilters(root);
  renderNotesSourcePanel();
}

function renderNoteProjectFilters() {
  const root = qs("#notesProjectFilters");
  if (!root) return;
  const notes = state.allNotes || [];
  const selected = new Set(state.selectedNoteProjects || []);
  const counts = new Map();
  for (const note of notes) {
    const projects = projectsForNote(note);
    if (!projects.length) counts.set("Unassigned", (counts.get("Unassigned") || 0) + 1);
    for (const project of projects) counts.set(project, (counts.get(project) || 0) + 1);
  }
  const projects = allNoteProjects();
  root.innerHTML = `
    <span class="filter-bar-label">Project</span>
    <button class="tag-filter ${selected.size === 0 ? "active" : ""}" data-note-project-clear="true">All <span>${notes.length}</span></button>
    ${projects.map(project => `<button class="tag-filter project-filter ${selected.has(project) ? "active" : ""}" style="--tag-color: ${escapeHtml(project === "Unassigned" ? "#d5dce3" : projectColor(project))}" data-note-project-filter="${escapeHtml(project)}" aria-pressed="${selected.has(project) ? "true" : "false"}">${escapeHtml(project)} <span>${counts.get(project) || 0}</span></button>`).join("")}
    ${selected.size ? `<button class="tag-filter note-filter-clear" data-note-project-clear="true">Clear ${selected.size}</button>` : ""}`;
  qsa("[data-note-project-filter]").forEach(button => button.addEventListener("click", () => {
    const project = button.dataset.noteProjectFilter;
    const filters = new Set(state.selectedNoteProjects || []);
    if (filters.has(project)) filters.delete(project);
    else filters.add(project);
    state.selectedNoteProjects = Array.from(filters);
    renderNotes();
  }));
  qsa("[data-note-project-clear]").forEach(button => button.addEventListener("click", () => {
    state.selectedNoteProjects = [];
    renderNotes();
  }));
}

function renderNoteTagFilters() {
  const root = qs("#notesTagFilters");
  if (!root) return;
  const counts = new Map();
  const notes = state.allNotes || [];
  const projectScopedNotes = notes.filter(note => noteMatchesProjectFilters(note, state.selectedNoteProjects || []));
  for (const annotation of projectScopedNotes) {
    for (const tag of annotationTags(annotation)) counts.set(tag, (counts.get(tag) || 0) + 1);
  }
  const selected = new Set(state.selectedNoteFilters || []);
  const tags = allNoteTags().filter(tag => counts.has(tag) || selected.has(tag));
  root.innerHTML = `
    <span class="filter-bar-label">Note tag</span>
    <button class="tag-filter ${selected.size === 0 ? "active" : ""}" data-note-filter-clear="true">All <span>${projectScopedNotes.length}</span></button>
    ${tags.map(tag => `<button class="tag-filter ${selected.has(tag) ? "active" : ""}" data-note-filter="${escapeHtml(tag)}" aria-pressed="${selected.has(tag) ? "true" : "false"}">${escapeHtml(tag)} <span>${counts.get(tag) || 0}</span></button>`).join("")}
    ${selected.size ? `<button class="tag-filter note-filter-clear" data-note-filter-clear="true">Clear ${selected.size}</button>` : ""}`;
  qsa("[data-note-filter]").forEach(button => button.addEventListener("click", () => {
    const tag = button.dataset.noteFilter;
    const filters = new Set(state.selectedNoteFilters || []);
    if (filters.has(tag)) filters.delete(tag);
    else filters.add(tag);
    state.selectedNoteFilters = Array.from(filters);
    renderNotes();
  }));
  qsa("[data-note-filter-clear]").forEach(button => button.addEventListener("click", () => {
    state.selectedNoteFilters = [];
    renderNotes();
  }));
}

async function uploadPdfFilesRaw(files, paperId = "", duplicateOptions = {}) {
  const formData = new FormData();
  for (const file of files) formData.append("files", file, file.name);
  let endpoint = paperId ? `/api/papers/${encodeURIComponent(paperId)}/pdf` : "/api/library/papers/upload";
  if (!paperId) {
    const query = new URLSearchParams();
    if (duplicateOptions.duplicate_policy) {
      query.set("duplicate_policy", duplicateOptions.duplicate_policy);
      query.set("replace_paper_id", duplicateOptions.replace_paper_id || "");
    }
    if (Array.from(query.keys()).length) endpoint += `?${query.toString()}`;
  }
  const response = await fetch(endpoint, { method: "POST", body: formData });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

function uploadStatusLabel(status) {
  if (status === "done") return "完成";
  if (status === "duplicate") return "重复";
  if (status === "error") return "失败";
  if (status === "waiting") return "待确认";
  if (status === "cancelled") return "已取消";
  return "解析中";
}

function renderLibraryUploadStatus() {
  const root = qs("#libraryUploadStatus");
  if (!root) return;
  const upload = state.libraryUpload || {};
  const hasItems = Array.isArray(upload.files) && upload.files.length;
  root.hidden = !hasItems && !upload.message && !upload.error;
  root.dataset.state = upload.error ? "error" : upload.active ? "active" : "done";
  const total = Number(upload.total || upload.files?.length || 0);
  const completed = Number(upload.completed || 0);
  const progress = total ? Math.max(0, Math.min(100, Math.round((completed / total) * 100))) : 0;
  const items = (upload.files || []).map(item => `
    <li data-state="${escapeHtml(item.status || "active")}">
      <span class="upload-file-name">${escapeHtml(item.name || "PDF")}</span>
      <span class="upload-file-state">${escapeHtml(uploadStatusLabel(item.status || "active"))}</span>
      ${item.detail ? `<small>${escapeHtml(item.detail)}</small>` : ""}
      ${item.paperId && item.status === "done" ? `<div class="upload-file-actions"><button class="secondary-button mini-button" data-open-upload-paper="${escapeHtml(item.paperId)}" type="button">Workspace</button><button class="secondary-button mini-button" data-preview-upload-paper="${escapeHtml(item.paperId)}" type="button">Preview</button></div>` : ""}
    </li>`).join("");
  root.innerHTML = `
    <div class="library-upload-summary">
      <div>
        <strong>${escapeHtml(upload.message || "Upload status")}</strong>
        ${total ? `<span>${escapeHtml(String(completed))}/${escapeHtml(String(total))}</span>` : ""}
      </div>
      <div class="library-upload-progress" aria-hidden="true"><span style="width: ${upload.active ? Math.max(progress, 8) : progress}%"></span></div>
    </div>
    ${items ? `<ul class="library-upload-files">${items}</ul>` : ""}
    ${upload.error ? `<div class="library-upload-error">${escapeHtml(upload.error)}</div>` : ""}`;
  root.querySelectorAll("[data-open-upload-paper]").forEach(button => button.addEventListener("click", () => openPaperInWorkspace(button.dataset.openUploadPaper)));
  root.querySelectorAll("[data-preview-upload-paper]").forEach(button => button.addEventListener("click", () => openLibraryPreview(button.dataset.previewUploadPaper)));
  qs("#choosePdfFiles")?.toggleAttribute("disabled", Boolean(upload.active));
  qs("#libraryDropZone")?.classList.toggle("is-uploading", Boolean(upload.active));
}

async function openPaperInWorkspace(paperId) {
  if (!paperId) return;
  if (await loadPaper(paperId)) activateView("reader");
}

function beginLibraryUpload(files, paperId = "") {
  const items = files.map(file => ({ name: file.name || "PDF", status: "active", detail: paperId ? "正在上传并重新解析" : "正在上传并解析" }));
  state.libraryUpload = {
    active: true,
    total: files.length,
    completed: 0,
    files: items,
    message: paperId ? "正在附加 PDF 并解析" : `正在上传并解析 ${files.length} 篇 PDF`,
    error: "",
  };
  renderLibraryUploadStatus();
}

function markLibraryUploadWaiting(message) {
  state.libraryUpload.active = false;
  state.libraryUpload.message = message;
  state.libraryUpload.files = (state.libraryUpload.files || []).map(item => ({ ...item, status: "waiting", detail: "检测到重复论文，等待选择处理方式" }));
  renderLibraryUploadStatus();
}

function finishLibraryUpload(result, files, paperId = "") {
  const papers = Array.isArray(result?.papers) ? result.papers : [];
  const items = files.map((file, index) => {
    const paper = papers[index] || result || {};
    if (paper.duplicate) return { name: file.name || paper.filename || "PDF", status: "duplicate", detail: paper.existing?.title ? `已存在：${paper.existing.title}` : "已跳过重复论文" };
    if (paper.processing_error) return { name: file.name || paper.filename || "PDF", status: "error", detail: paper.processing_error, paperId: paper.paper_id || paper.metadata?.id || "" };
    if (paper.error) return { name: file.name || paper.filename || "PDF", status: "error", detail: paper.error };
    const title = paper.metadata?.title || paper.title || paper.paper_id || "已加入 Library";
    const detail = paperParsingPending(paper.metadata) ? `已入库，后台解析中：${title}` : `已入库：${title}`;
    return { name: file.name || paper.filename || "PDF", status: "done", detail, paperId: paper.paper_id || paper.metadata?.id || "" };
  });
  const doneCount = items.filter(item => item.status === "done").length;
  const duplicateCount = items.filter(item => item.status === "duplicate").length;
  const errorCount = items.filter(item => item.status === "error").length;
  const parts = [];
  if (doneCount) parts.push(`${doneCount} 篇已入库`);
  if (duplicateCount) parts.push(`${duplicateCount} 篇重复`);
  if (errorCount) parts.push(`${errorCount} 篇失败`);
  state.libraryUpload = {
    active: false,
    total: files.length,
    completed: doneCount + duplicateCount + errorCount,
    files: items,
    message: paperId ? "PDF 已附加，解析状态见阅读页" : `批量上传完成：${parts.join("，") || "无变化"}`,
    error: "",
  };
  if (!paperId) clearLibraryIntakeSelection();
  renderLibraryUploadStatus();
}

function failLibraryUpload(files, error) {
  state.libraryUpload = {
    active: false,
    total: files.length,
    completed: 0,
    files: files.map(file => ({ name: file.name || "PDF", status: "error", detail: error.message || "Upload failed" })),
    message: "上传或解析失败",
    error: error.message || String(error),
  };
  renderLibraryUploadStatus();
}

async function uploadPdfFiles(fileList, paperId = "") {
  const files = Array.from(fileList || []).filter(file => file && /\.pdf$/i.test(file.name || ""));
  if (!files.length) {
    toast("Drop or choose PDF files first");
    return;
  }
  beginLibraryUpload(files, paperId);
  try {
    let result = await uploadPdfFilesRaw(files, paperId);
    const duplicateItems = (result.papers || []).filter(item => item.duplicate);
    if (!paperId && files.length === 1 && duplicateItems.length) {
      markLibraryUploadWaiting("检测到重复论文");
      const choice = await openDuplicatePaperDialog(duplicateItems[0]);
      if (choice !== "replace") {
        state.libraryUpload = { active: false, total: files.length, completed: 1, files: files.map(file => ({ name: file.name || "PDF", status: "cancelled", detail: "用户取消替换" })), message: "上传已取消", error: "" };
        renderLibraryUploadStatus();
        toast("Upload cancelled");
        await loadLibrary();
        return;
      }
      beginLibraryUpload(files, paperId);
      state.libraryUpload.message = "正在替换重复论文并重新解析";
      renderLibraryUploadStatus();
      result = await uploadPdfFilesRaw(files, paperId, { duplicate_policy: "replace", replace_paper_id: duplicateItems[0].existing?.id || "" });
    }
    const promptPaperIds = paperId ? [] : uploadedPaperIdsFromResult(result);
    finishLibraryUpload(result, files, paperId);
    const duplicateCount = Number(result.duplicate_count || 0);
    toast(paperId
      ? "PDF attached and parsed"
      : duplicateCount
        ? `${result.count || 0} PDF(s) added, ${duplicateCount} duplicate(s) skipped`
        : `${result.count || files.length} PDF(s) added and parsed`);
    await loadLibrary();
    if (promptPaperIds.length) openLibraryTagPrompt(promptPaperIds);
    if (paperId) invalidatePaperCache(paperId);
    if (paperId && paperId === state.currentPaperId) await loadPaper(paperId, { force: true });
  } catch (error) {
    failLibraryUpload(files, error);
    throw error;
  }
}

function ensureDuplicateModal() {
  let modal = qs("#duplicatePaperModal");
  if (modal) return modal;
  modal = document.createElement("aside");
  modal.id = "duplicatePaperModal";
  modal.className = "duplicate-modal";
  modal.setAttribute("aria-hidden", "true");
  modal.innerHTML = `
    <div class="duplicate-panel" role="dialog" aria-modal="true" aria-labelledby="duplicatePaperTitle">
      <div class="duplicate-header">
        <div>
          <span class="sense-kicker">Duplicate Paper</span>
          <h2 id="duplicatePaperTitle">This paper is already in Library</h2>
        </div>
        <button class="icon-button" data-duplicate-action="cancel" title="Cancel">x</button>
      </div>
      <div id="duplicatePaperBody" class="duplicate-body"></div>
      <div class="duplicate-actions">
        <button class="secondary-button" data-duplicate-action="cancel">Cancel</button>
        <button class="danger-button" data-duplicate-action="replace">Replace Existing</button>
      </div>
    </div>`;
  document.body.appendChild(modal);
  modal.addEventListener("click", event => {
    if (event.target === modal) modal.dispatchEvent(new CustomEvent("duplicate-choice", { detail: "cancel" }));
  });
  return modal;
}

function duplicateDialogHtml(info) {
  const existing = info?.existing || {};
  const candidate = info?.candidate || {};
  const summary = [existing.authors, existing.venue, existing.year, existing.read_status].filter(Boolean).join(" · ");
  return `
    <section class="duplicate-card duplicate-existing">
      <h3>Existing</h3>
      <p class="duplicate-title">${escapeHtml(existing.title || "Untitled paper")}</p>
      ${summary ? `<p class="muted">${escapeHtml(summary)}</p>` : ""}
      <p class="muted small-text">${escapeHtml(existing.note_count || 0)} notes${existing.source_pdf_name ? ` · ${escapeHtml(existing.source_pdf_name)}` : ""}</p>
    </section>
    <section class="duplicate-card">
      <h3>New</h3>
      <p class="duplicate-title">${escapeHtml(candidate.title || "Untitled paper")}</p>
      ${candidate.source_name ? `<p class="muted small-text">${escapeHtml(candidate.source_name)}</p>` : ""}
    </section>
    <p class="duplicate-warning">Replacing keeps the existing Library row and backs up the previous metadata, notes, thinking, reading progress, and parsed files before refreshing this paper.</p>`;
}

function openDuplicatePaperDialog(info) {
  const modal = ensureDuplicateModal();
  qs("#duplicatePaperBody").innerHTML = duplicateDialogHtml(info);
  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
  return new Promise(resolve => {
    const cleanup = choice => {
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
      modal.removeEventListener("duplicate-choice", onChoice);
      qsa("#duplicatePaperModal [data-duplicate-action]").forEach(button => button.removeEventListener("click", onButton));
      resolve(choice);
    };
    const onChoice = event => cleanup(event.detail || "cancel");
    const onButton = event => cleanup(event.currentTarget.dataset.duplicateAction || "cancel");
    modal.addEventListener("duplicate-choice", onChoice);
    qsa("#duplicatePaperModal [data-duplicate-action]").forEach(button => button.addEventListener("click", onButton));
    qs('#duplicatePaperModal [data-duplicate-action="cancel"]')?.focus();
  });
}

async function submitAddPaperRequest(body) {
  return api("/api/library/papers", { method: "POST", body: JSON.stringify(body) });
}

async function completeAddPaperResult(result, pathInput, titleInput, options = {}) {
  toast(result.processing_error ? "Added, but Markdown parsing failed"
    : paperParsingPending(result.metadata) ? "Added; Markdown parsing runs in the background" : "Added to Library");
  if (pathInput) pathInput.value = defaultPdfLibraryPath;
  if (titleInput) titleInput.value = "";
  clearLibraryIntakeSelection();
  await loadLibrary();
  if (result.paper_id) invalidatePaperCache(result.paper_id);
  if (options.promptTags && result.paper_id) openLibraryTagPrompt([result.paper_id]);
  activateView("library");
}

async function addPaperFromForm() {
  const pathInput = qs("#addPdfPath");
  const titleInput = qs("#addPaperTitle");
  const path = pathInput?.value?.trim();
  const title = titleInput?.value?.trim() || "";
  const hasPdfPath = Boolean(path && path !== defaultPdfLibraryPath);
  if (!hasPdfPath && !title) {
    toast("Add a PDF filename, or enter a title to create a metadata-only paper");
    return;
  }
  const button = qs("#addPaperButton");
  if (button) {
    button.disabled = true;
    button.textContent = hasPdfPath ? "Adding + parsing..." : "Adding metadata...";
  }
  try {
    const body = { path: hasPdfPath ? path : "", title };
    let result = await submitAddPaperRequest(body);
    if (result.duplicate) {
      const choice = await openDuplicatePaperDialog(result);
      if (choice !== "replace") {
        toast("Add cancelled");
        return;
      }
      result = await submitAddPaperRequest({ ...body, duplicate_policy: "replace", replace_paper_id: result.existing?.id || "" });
    }
    if (result.duplicate) {
      toast("Duplicate paper was not replaced");
      return;
    }
    await completeAddPaperResult(result, pathInput, titleInput, { promptTags: hasPdfPath });
  } catch (error) {
    toast(`Add failed: ${error.message}`);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = "Add + Parse";
    }
  }
}

async function processPaper(paperId, mode) {
  if (!paperId || !mode) return;
  const label = "Markdown";
  toast(`${label}处理中...`);
  qsa(`[data-process-paper="${cssEscape(paperId)}"]`).forEach(button => { button.disabled = true; });
  try {
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/process`, {
      method: "POST",
      body: JSON.stringify({ mode }),
    });
    toast(response.metadata?.processing_status === "ready" ? "Markdown ready" : "Markdown parsing queued");
    invalidatePaperCache(paperId);
    await loadLibrary();
    if (await loadPaper(paperId, { force: true })) activateView("reader");
  } catch (error) {
    toast(`${label}失败: ${error.message}`);
    await loadLibrary();
  }
}

function translationJob(paperId) {
  if (!state.translationJobs.has(paperId)) state.translationJobs.set(paperId, { cursor: 0, cursorJobId: "" });
  return state.translationJobs.get(paperId);
}

function renderTranslationStatus() {
  const root = qs("#readerTranslationStatus");
  if (!root) return;
  root.hidden = !state.currentPaperId || !state.payload?.segments?.length;
  if (root.hidden) return;
  const job = translationJob(state.currentPaperId);
  const status = job.status || state.payload.translation?.status || "not_started";
  const active = ["queued", "processing", "pausing", "retrying"].includes(status);
  const labels = {
    not_started: state.translationConfig.auto_start ? "Preparing background translation" : "Translation",
    queued: "Translation queued", processing: "Translating in background",
    pausing: "Pausing after the current paragraph", paused: "Translation paused",
    retrying: "Translation waiting before retry",
    waiting_for_source: "Waiting for Markdown source",
    ready: "Translation complete", failed: "Translation stopped", interrupted: "Translation interrupted",
    source_changed: "Source changed — reload before continuing",
  };
  root.dataset.status = status;
  qs("#translationStatusLabel").textContent = labels[status] || status;
  qs("#translationStatusDetail").textContent = job.error || [
    job.total ? `${job.completed || 0} / ${job.total} paragraphs` : "",
    job.backend || state.translationConfig.model || "",
  ].filter(Boolean).join(" · ");
  const progress = qs("#translationProgress");
  progress.max = Math.max(1, job.total || 1);
  progress.value = job.completed || 0;
  progress.hidden = !job.total;
  const button = qs("#translateCurrentPaper");
  button.textContent = active ? "Pause" : status === "source_changed" ? "Reload from disk"
    : ["failed", "interrupted"].includes(status) ? "Retry" : status === "paused" ? "Resume" : "Translate";
  button.disabled = Boolean(job.requesting) || status === "pausing";
  button.hidden = status === "ready" || (status === "not_started" && state.translationConfig.auto_start && !job.error);
}

function applyTranslationResponse(paperId, response) {
  if (response.paper_id && response.paper_id !== paperId) throw new Error("Translation response belongs to another paper.");
  const session = state.paperSessions.get(paperId);
  const payload = paperId === state.currentPaperId ? state.payload : session?.payload;
  if (!payload) return;
  const job = translationJob(paperId);
  if (response.translation) Object.assign(job, response.translation);
  const active = paperId === state.currentPaperId && !state.paperLoadingId;
  const viewportTop = readerViewportTop();
  const anchor = active ? qsa("#documentRoot .paragraph").find(node => node.getBoundingClientRect().bottom > viewportTop) : null;
  const anchorTop = anchor?.getBoundingClientRect().top;
  let changedSource = false;
  for (const update of response.updates || []) {
    if (typeof update.translation !== "string" || !update.translation.trim()) throw new Error("Received an empty translation update.");
    const paragraph = payload.segments.find(item => item.id === update.id);
    if (!paragraph || paragraph.markdown !== update.markdown) {
      changedSource = true;
      continue;
    }
    if (paragraph.translation === update.translation) continue;
    paragraph.translation = update.translation;
    if (!active) continue;
    const article = document.getElementById(paragraph.id);
    if (!article) continue;
    const wrapper = document.createElement("div");
    wrapper.innerHTML = paragraphHtml(paragraph);
    const translated = wrapper.querySelector(".paragraph > .translation");
    const previous = article.querySelector(":scope > .translation");
    if (!translated) {
      previous?.remove();
      continue;
    }
    if (previous) previous.replaceWith(translated);
    else article.insertBefore(translated, article.querySelector(":scope > .comment-stack"));
    bindReaderDynamicEvents(translated);
  }
  if (anchor && anchorTop !== undefined) {
    const shift = anchor.getBoundingClientRect().top - anchorTop;
    if (Math.abs(shift) > 0.5) window.scrollTo({ top: window.scrollY + shift, behavior: "instant" });
  }
  if (changedSource) {
    job.status = "source_changed";
    job.error = "The source was changed on disk. Saved notes are kept; use Reload from disk.";
  } else if (response.translation) {
    job.cursor = response.translation.revision || 0;
    job.cursorJobId = response.translation.job_id || "";
  }
  payload.translation = response.translation || payload.translation;
  Object.assign(payload.metadata || {}, { translation_status: job.status, translation_error: job.error || "" });
  const paper = state.library?.papers?.find(item => item.id === paperId);
  if (paper) {
    Object.assign(paper, { translation_status: job.status, translation_error: job.error || "" });
    state.libraryDirty = true;
  }
  state.notesPreviewCache.delete(paperId);
  if (active) renderTranslationStatus();
}

function stopReaderBackground() {
  clearTimeout(state.readerBackgroundTimer);
  state.readerBackgroundTimer = null;
  state.readerBackgroundVersion += 1;
}

function watchReaderBackground({ automatic = true, start = true } = {}) {
  stopReaderBackground();
  renderTranslationStatus();
  const parsing = paperParsingPending(state.payload?.metadata || {});
  if (!state.currentPaperId || !state.payload || state.paperLoadingId
    || document.body.dataset.activeView !== "reader"
    || (automatic && !state.translationConfig.auto_start && !parsing)) return;
  const paperId = state.currentPaperId;
  const version = state.readerBackgroundVersion;
  const stillCurrent = () => version === state.readerBackgroundVersion && paperId === state.currentPaperId
    && document.body.dataset.activeView === "reader" && !state.paperLoadingId;
  let shouldStart = start;
  const poll = async () => {
    if (!stillCurrent()) return;
    try {
      if (!state.payload.segments?.length) {
        const metadata = state.payload.metadata || {};
        const pending = paperParsingPending(metadata);
        if (!pending && (!metadata.source_pdf || processingStatus(metadata) === "failed"
          || processingMode(metadata) === "reference-card")) return;
        if (!pending) {
          const result = await api(`/api/papers/${encodeURIComponent(paperId)}/process`, {
            method: "POST", body: JSON.stringify({ mode: "deep" }),
          });
          if (!stillCurrent()) return;
          Object.assign(state.payload.metadata, result.metadata || {});
          renderReader();
        } else {
          const payload = await api(`/api/papers/${encodeURIComponent(paperId)}`);
          if (!stillCurrent()) return;
          if (payload.segments?.length || payload.metadata?.processing_status === "failed") {
            await loadPaper(paperId, { force: true });
            return;
          }
        }
      } else {
        const job = translationJob(paperId);
        if (shouldStart) {
          const result = await api(`/api/papers/${encodeURIComponent(paperId)}/translate`, {
            method: "POST", body: JSON.stringify({ action: "start", automatic }),
          });
          if (!stillCurrent()) return;
          if (result.translation) Object.assign(job, result.translation);
          shouldStart = false;
        }
        const query = new URLSearchParams({ job_id: job.cursorJobId || "", after: String(job.cursor || 0) });
        const response = await api(`/api/papers/${encodeURIComponent(paperId)}/translation?${query}`);
        if (!stillCurrent()) return;
        applyTranslationResponse(paperId, response);
        if (!["queued", "processing", "pausing", "retrying"].includes(job.status)) return;
      }
      if (stillCurrent()) state.readerBackgroundTimer = setTimeout(poll, 1200);
    } catch (error) {
      console.error(`Background reading failed for ${paperId}`, error);
      if (!stillCurrent()) return;
      Object.assign(translationJob(paperId), { status: "failed", error: error.message });
      renderTranslationStatus();
      toast(`Background reading stopped: ${error.message}. Original text and notes are kept.`);
    }
  };
  state.readerBackgroundTimer = setTimeout(poll, 0);
}

async function translatePaper(paperId = state.currentPaperId) {
  if (!paperId) return;
  const job = translationJob(paperId);
  if (job.requesting) return;
  if (job.status === "source_changed") {
    await loadPaper(paperId, { force: true });
    return;
  }
  const action = ["queued", "processing", "retrying"].includes(job.status) ? "pause" : "resume";
  if (paperId === state.currentPaperId) stopReaderBackground();
  job.requesting = true;
  renderTranslationStatus();
  try {
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/translate`, {
      method: "POST", body: JSON.stringify({ action, automatic: false }),
    });
    if (response.translation) Object.assign(job, response.translation);
    if (paperId === state.currentPaperId) watchReaderBackground({ automatic: false, start: false });
  } catch (error) {
    console.error(`Translation ${action} failed for ${paperId}`, error);
    Object.assign(job, { status: "failed", error: error.message });
    toast(`Translation stopped: ${error.message}`);
  } finally {
    job.requesting = false;
    renderTranslationStatus();
  }
}

function renderTranslationQueue() {
  const queue = state.translationQueue;
  const panel = qs("#translationQueuePanel");
  if (!panel) return;
  panel.hidden = !queue.open;
  qs("#toggleTranslationQueue")?.setAttribute("aria-expanded", String(queue.open));
  if (!queue.open) return;
  const data = queue.data || { jobs: [] };
  qs("#translationQueueSummary").textContent = queue.error || (queue.data
    ? `${data.active_requests || 0} active / ${data.concurrency || 1} maximum · Only papers requested for translation`
    : "Loading queue…");
  qs("#translationQueueItems").innerHTML = (data.jobs || []).map(job => {
    const active = ["queued", "processing", "retrying", "waiting_for_source"].includes(job.status);
    const title = state.library?.papers?.find(paper => paper.id === job.paper_id);
    return `<article class="translation-queue-item">
      <button class="queue-paper-title" data-queue-open="${escapeHtml(job.paper_id)}" type="button">${escapeHtml(title ? paperTitle(title) : cleanPaperTitle(job.title || job.paper_id))}</button>
      <span class="muted small-text">${escapeHtml(job.status)} · ${job.completed || 0}/${job.total || 0}${job.active_requests ? ` · ${job.active_requests} active` : ""}</span>
      ${job.error ? `<span class="error-text small-text">${escapeHtml(job.error)}</span>` : ""}
      ${job.status !== "ready" ? `<button class="secondary-button mini-button" data-queue-action="${active ? "pause" : "resume"}" data-queue-paper="${escapeHtml(job.paper_id)}" type="button">${active ? "Pause" : job.status === "failed" ? "Retry" : "Resume"}</button>` : ""}
    </article>`;
  }).join("") || '<p class="muted">Open a paper to add missing translations to the queue.</p>';
}

async function refreshTranslationQueue() {
  const queue = state.translationQueue;
  clearTimeout(queue.timer);
  if (!queue.open || queue.loading) return;
  queue.loading = true;
  try {
    queue.data = await api("/api/translation-queue");
    queue.error = "";
  } catch (error) {
    console.error("Translation queue refresh failed", error);
    queue.error = `Queue unavailable: ${error.message}`;
  } finally {
    queue.loading = false;
    renderTranslationQueue();
    if (queue.open) queue.timer = setTimeout(refreshTranslationQueue, 2500);
  }
}

function toggleTranslationQueue(open = !state.translationQueue.open) {
  if (open) toggleProcessingQueue(false);
  state.translationQueue.open = open;
  renderTranslationQueue();
  if (open) refreshTranslationQueue();
  else clearTimeout(state.translationQueue.timer);
}

function renderProcessingQueue() {
  const queue = state.processingQueue;
  qs("#processingQueuePanel").hidden = !queue.open;
  qs("#toggleProcessingQueue").setAttribute("aria-expanded", String(queue.open));
  if (!queue.open) return;
  qs("#processingQueueSummary").textContent = queue.error || (queue.data
    ? `${queue.data.active_jobs} parsing · ${queue.data.queued_count} waiting · one parser maximum`
    : "Loading queue…");
  qs("#processingQueueItems").innerHTML = (queue.data?.jobs || []).map(job => `
    <article class="translation-queue-item">
      <button class="queue-paper-title" data-parse-open="${escapeHtml(job.paper_id)}" type="button">${escapeHtml(job.title || job.paper_id)}</button>
      <span class="muted small-text">${escapeHtml(job.status)}${job.position ? ` · queue position ${job.position}` : ""}</span>
      ${job.error ? `<span class="error-text small-text" role="alert">${escapeHtml(job.error)}</span>` : ""}
      ${job.status === "failed" ? `<button class="secondary-button mini-button" data-parse-retry="${escapeHtml(job.paper_id)}" type="button">Retry parsing</button>` : ""}
    </article>`).join("") || '<p class="muted">No parsing jobs requested. Queue a paper from Feishu or add a local PDF.</p>';
}

async function refreshProcessingQueue() {
  const queue = state.processingQueue;
  clearTimeout(queue.timer);
  if ((!queue.open && !feishuIntakeNeedsPolling()) || queue.loading) return;
  const watched = feishuIntakeNeedsPolling()
    ? { paperId: state.feishuIntake.localPaper.id, version: state.feishuIntake.version } : null;
  queue.loading = true;
  try {
    queue.data = await api("/api/processing-queue");
    await updateFeishuIntakeProcessing(queue.data, watched);
    queue.error = "";
  } catch (error) {
    console.error("Parsing queue refresh failed", error);
    queue.error = `Queue unavailable: ${error.message}`;
    if (watched && watched.version === state.feishuIntake.version && watched.paperId === state.feishuIntake.localPaper?.id
      && feishuIntakeNeedsPolling()) {
      state.feishuIntake.statusError = `Parsing status unavailable: ${error.message}. The paper has not been queued again.`;
      renderFeishuIntakeActions();
    }
  } finally {
    queue.loading = false;
    renderProcessingQueue();
    if (queue.open || feishuIntakeNeedsPolling()) queue.timer = setTimeout(refreshProcessingQueue, 2500);
  }
}

function toggleProcessingQueue(open = !state.processingQueue.open) {
  if (open) toggleTranslationQueue(false);
  state.processingQueue.open = open;
  renderProcessingQueue();
  if (open || feishuIntakeNeedsPolling()) refreshProcessingQueue();
  else clearTimeout(state.processingQueue.timer);
}

async function retryQueuedParsing(paperId, button) {
  button.disabled = true;
  try {
    await api("/api/processing-queue/retry", { method: "POST", body: JSON.stringify({ paper_id: paperId }) });
    if (paperId === state.currentPaperId) watchReaderBackground({ start: false });
  } catch (error) {
    console.error("Parsing retry failed", error);
    toast(`Could not retry parsing: ${error.message}`);
  } finally {
    await refreshProcessingQueue();
  }
}

async function controlQueuedTranslation(paperId, action) {
  try {
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/translate`, {
      method: "POST", body: JSON.stringify({ action, automatic: false }),
    });
    if (response.translation) Object.assign(translationJob(paperId), response.translation);
    if (paperId === state.currentPaperId) watchReaderBackground({ automatic: false, start: false });
  } catch (error) {
    console.error(`Queue action failed for ${paperId}`, error);
    toast(`Queue action failed: ${error.message}`);
  }
  await refreshTranslationQueue();
}

async function refreshCitation(paperId) {
  const button = document.querySelector(`[data-refresh-citation="${cssEscape(paperId)}"]`);
  if (button) {
    button.disabled = true;
    button.textContent = "Searching...";
  }
  try {
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/citations`, { method: "POST", body: JSON.stringify({}) });
    const paper = state.library?.papers?.find(item => item.id === paperId);
    if (paper && response.metadata) Object.assign(paper, response.metadata);
    refreshLibraryRowOrRender(paperId);
    toast("Citation info updated");
  } catch (error) {
    toast(`Citation lookup failed: ${error.message}`);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = "Refresh";
    }
  }
}

async function refreshVideos(paperId) {
  const button = document.querySelector(`[data-refresh-videos="${cssEscape(paperId)}"]`);
  if (button) {
    button.disabled = true;
    button.textContent = "Searching...";
  }
  try {
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/videos`, { method: "POST", body: JSON.stringify({ force: true }) });
    const paper = state.library?.papers?.find(item => item.id === paperId);
    if (paper && response.metadata) Object.assign(paper, response.metadata);
    refreshLibraryRowOrRender(paperId);
    toast("Video links updated");
  } catch (error) {
    toast(`Video lookup failed: ${error.message}`);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = "Refresh Videos";
    }
  }
}

async function findPdfForPaper(paperId) {
  const button = document.querySelector(`[data-find-pdf="${cssEscape(paperId)}"]`);
  if (button) {
    button.disabled = true;
    button.textContent = "Finding...";
  }
  try {
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/find-pdf`, { method: "POST", body: JSON.stringify({ force: true }) });
    const paper = state.library?.papers?.find(item => item.id === paperId);
    if (paper && response.metadata) Object.assign(paper, response.metadata);
    refreshLibraryRowOrRender(paperId);
    if (response.pdf_attached) toast(response.pdf_existing ? "PDF already attached" : "PDF found, attached, and parsing started");
    else if (response.pdf_error) toast(`PDF search finished: ${response.pdf_error}`);
    else toast("PDF search finished; no open PDF found");
    await loadLibrary();
  } catch (error) {
    toast(`Find PDF failed: ${error.message}`);
    await loadLibrary();
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = "Find PDF";
    }
  }
}

function youtubeVideoIdFromUrl(url) {
  const raw = String(url || "").trim();
  if (!raw) return "";
  try {
    const parsed = new URL(raw);
    if (parsed.hostname.includes("youtu.be")) return parsed.pathname.replace(/^\//, "").split("/")[0] || "";
    if (parsed.hostname.includes("youtube.com")) return parsed.searchParams.get("v") || "";
  } catch (error) {
    return "";
  }
  return "";
}

function cleanVideoUrl(url) {
  const raw = String(url || "").trim();
  const videoId = youtubeVideoIdFromUrl(raw);
  return videoId ? `https://www.youtube.com/watch?v=${videoId}` : raw;
}

function paperVideoLinks(paper = {}) {
  return Array.isArray(paper.video_links) ? paper.video_links.filter(link => link && String(link.url || "").trim()) : [];
}

async function savePaperVideos(paperId, links) {
  const nextLinks = paperVideoLinks({ video_links: links });
  const response = await api(`/api/papers/${encodeURIComponent(paperId)}/metadata`, {
    method: "POST",
    body: JSON.stringify({ video_links: nextLinks, video_search_status: nextLinks.length ? "ready" : "no_results", video_search_error: "" }),
  });
  const paper = state.library?.papers?.find(item => item.id === paperId);
  if (paper) Object.assign(paper, { video_links: nextLinks, video_search_status: nextLinks.length ? "ready" : "no_results", video_search_error: "" }, response.metadata || {});
  refreshLibraryRowOrRender(paperId);
}

async function addVideoLink(paperId) {
  const input = document.querySelector(`[data-video-input="${cssEscape(paperId)}"]`);
  const url = cleanVideoUrl(input?.value || "");
  if (!url) return;
  const paper = state.library?.papers?.find(item => item.id === paperId) || {};
  const links = paperVideoLinks(paper);
  if (links.some(link => cleanVideoUrl(link.url) === url)) {
    toast("Video already exists");
    return;
  }
  if (input) input.value = "";
  const videoId = youtubeVideoIdFromUrl(url);
  await savePaperVideos(paperId, [...links, {
    source: videoId ? "youtube" : "manual",
    title: videoId ? `YouTube video ${videoId}` : url,
    url,
    video_id: videoId,
    channel: "",
    published_at: "",
    thumbnail: "",
    score: 1,
    query: "manual",
  }]);
  toast("Video added");
}

async function deleteVideoLink(paperId, index) {
  const paper = state.library?.papers?.find(item => item.id === paperId) || {};
  const links = paperVideoLinks(paper);
  const nextLinks = links.filter((_, linkIndex) => linkIndex !== Number(index));
  await savePaperVideos(paperId, nextLinks);
  toast("Video deleted");
}

async function deletePaper(paperId) {
  const paper = state.library?.papers?.find(item => item.id === paperId);
  const confirmed = window.confirm(`Delete this paper from Library and local storage?\n\n${paperTitle(paper || { id: paperId })}`);
  if (!confirmed) return;
  if (state.currentPaperId === paperId) await flushCurrentPaperEdits();
  await fetch(`/api/papers/${encodeURIComponent(paperId)}`, { method: "DELETE" }).then(response => {
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json();
  });
  toast("Paper deleted");
  if (state.currentPaperId === paperId) state.currentPaperId = null;
  state.paperTabs = state.paperTabs.filter(id => id !== paperId);
  state.paperSessions.delete(paperId);
  if (!state.currentPaperId) {
    disconnectReadingProgressTracker();
    state.payload = null;
    state.annotations = [];
    state.thinking = null;
    renderReader();
    renderSidebar();
  }
  persistPaperTabs();
  if (state.notesPreview.paperId === paperId) state.notesPreview = { paperId: "", annotationId: "", segmentId: "", note: null, payload: null, loading: false, error: "" };
  state.notesPreviewCache.delete(paperId);
  await loadLibrary();
}

function tagMenuSearchHtml(placeholder = "Search tags") {
  return `<input class="library-tag-menu-search" data-filter-tag-options type="search" placeholder="${escapeHtml(placeholder)}" aria-label="${escapeHtml(placeholder)}" />`;
}

function filterableTagOptionAttrs(text) {
  return `data-filterable-tag-option data-filter-text="${escapeHtml(String(text || "").toLowerCase())}"`;
}

function applyTagOptionFilter(input) {
  const scope = input.closest("[data-filter-tag-scope]");
  if (!scope) return;
  const query = input.value.trim().toLowerCase();
  const options = Array.from(scope.querySelectorAll("[data-filterable-tag-option]"));
  let visible = 0;
  for (const option of options) {
    const text = option.dataset.filterText || option.textContent.toLowerCase();
    const show = !query || text.includes(query);
    option.hidden = !show;
    if (show) visible += 1;
  }
  const empty = scope.querySelector("[data-filter-empty]");
  if (empty) empty.hidden = !query || visible > 0 || !options.length;
}

function initTagOptionFilters(root = document) {
  root.querySelectorAll("[data-filter-tag-options]").forEach(input => {
    input.addEventListener("input", () => applyTagOptionFilter(input));
    applyTagOptionFilter(input);
  });
}

function libraryTagEditorHtml(paper) {
  const tags = normalizeTagsInput(paper.tags || []);
  const options = allLibraryTags(tags).filter(tag => !tags.includes(tag));
  const colors = { ...tagColorMap(), ...(paper.tag_colors || {}) };
  const menuOpen = state.libraryTagMenuPaperId === paper.id;
  return `
    <div class="library-tags" aria-label="Paper tags">
      ${tags.map(tag => `<button class="library-tag" style="--tag-color: ${escapeHtml(tagColor(tag, colors))}" data-remove-paper-tag="${escapeHtml(tag)}" data-paper-id="${escapeHtml(paper.id)}" title="${escapeHtml(tag)}">${escapeHtml(libraryTagLabel(tag))} ×</button>`).join("") || '<span class="muted small-text">No tags</span>'}
    </div>
    <div class="library-tag-menu-wrap">
      <button class="secondary-button mini-button library-add-tag-button" data-open-tag-menu="${escapeHtml(paper.id)}" type="button">+ Add tag</button>
      ${menuOpen ? `<div class="library-tag-menu" data-tag-menu="${escapeHtml(paper.id)}" data-filter-tag-scope>
        ${tagMenuSearchHtml("Search paper tags")}
        <div class="library-tag-menu-section">
          <div class="library-tag-menu-label">Existing tags</div>
          ${options.length ? options.map(tag => `<button class="library-tag-option" style="--tag-color: ${escapeHtml(tagColor(tag, colors))}" data-add-existing-tag="${escapeHtml(tag)}" data-paper-id="${escapeHtml(paper.id)}" ${filterableTagOptionAttrs(`${tag} ${libraryTagLabel(tag)}`)} type="button"><span></span>${escapeHtml(libraryTagLabel(tag))}</button>`).join("") : '<div class="muted small-text">No existing tags</div>'}
          <div class="muted small-text" data-filter-empty hidden>No matching tags</div>
        </div>
        <div class="library-tag-menu-section">
          <div class="library-tag-menu-label">Add custom tag</div>
          <input class="library-custom-tag-input" data-paper-tag-input="${escapeHtml(paper.id)}" placeholder="New tag" />
          <div class="tag-color-palette" aria-label="Choose tag color">
            ${tagColorPalette.map((color, index) => `<label class="tag-color-swatch" style="--tag-color: ${escapeHtml(color)}" title="Tag color"><input type="radio" name="tag-color-${escapeHtml(paper.id)}" value="${escapeHtml(color)}" ${index === 0 ? "checked" : ""}><span></span></label>`).join("")}
          </div>
          <button class="primary-button mini-button" data-add-custom-tag="${escapeHtml(paper.id)}" type="button">Add custom tag</button>
        </div>
      </div>` : ""}
    </div>`;
}

function libraryProjectEditorHtml(paper) {
  const projects = paperProjects(paper);
  const options = allLibraryProjects().filter(project => !projects.includes(project));
  const colors = { ...projectColorMap(), ...(paper.project_colors || {}) };
  const menuOpen = state.libraryProjectMenuPaperId === paper.id;
  return `
    <div class="library-tags library-project-tags" aria-label="Paper projects">
      ${projects.map(project => `<button class="library-tag library-project-tag" style="--tag-color: ${escapeHtml(projectColor(project, colors))}" data-remove-paper-project="${escapeHtml(project)}" data-paper-id="${escapeHtml(paper.id)}" title="Remove project">${escapeHtml(project)} ×</button>`).join("") || '<span class="muted small-text">No project</span>'}
    </div>
    <div class="library-tag-menu-wrap">
      <button class="secondary-button mini-button library-add-tag-button" data-open-project-menu="${escapeHtml(paper.id)}" type="button">+ Add project</button>
      ${menuOpen ? `<div class="library-tag-menu" data-project-menu="${escapeHtml(paper.id)}" data-filter-tag-scope>
        ${tagMenuSearchHtml("Search projects")}
        <div class="library-tag-menu-section">
          <div class="library-tag-menu-label">Existing projects</div>
          ${options.length ? options.map(project => `<button class="library-tag-option" style="--tag-color: ${escapeHtml(projectColor(project, colors))}" data-add-existing-project="${escapeHtml(project)}" data-paper-id="${escapeHtml(paper.id)}" ${filterableTagOptionAttrs(project)} type="button"><span></span>${escapeHtml(project)}</button>`).join("") : '<div class="muted small-text">No existing projects</div>'}
          <div class="muted small-text" data-filter-empty hidden>No matching projects</div>
        </div>
        <div class="library-tag-menu-section">
          <div class="library-tag-menu-label">Create project</div>
          <input class="library-custom-tag-input" data-paper-project-input="${escapeHtml(paper.id)}" placeholder="New project" />
          <button class="primary-button mini-button" data-add-custom-project="${escapeHtml(paper.id)}" type="button">Create + add</button>
        </div>
      </div>` : ""}
    </div>`;
}

function libraryImportanceEditorHtml(paper) {
  return importanceStarEditorHtml(paper, { variant: "library-cell" });
}

async function savePaperTags(paperId, tags, tagColors = null) {
  const nextTags = uniqueTags(tags);
  captureLibraryScroll();
  const body = { tags: nextTags };
  if (tagColors) body.tag_colors = tagColors;
  const paper = state.library?.papers?.find(item => item.id === paperId);
  const previous = paperSnapshot(paper);
  if (paper) Object.assign(paper, { tags: nextTags, ...(tagColors ? { tag_colors: tagColors } : {}) });
  refreshLibraryRowOrRender(paperId);
  restoreLibraryScroll();
  setMetadataSaveState(paperId, "Saving...", "saving");
  try {
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/metadata`, { method: "POST", body: JSON.stringify(body) });
    const savedTags = normalizeTagsInput(response.metadata?.tags || nextTags);
    if (paper) Object.assign(paper, { tags: savedTags, ...(tagColors ? { tag_colors: tagColors } : {}) }, response.metadata || {});
    refreshLibraryRow(paperId);
    setMetadataSaveState(paperId, "Saved", "saved");
  } catch (error) {
    restorePaperSnapshot(paper, previous);
    refreshLibraryRowOrRender(paperId);
    setMetadataSaveState(paperId, "Save failed", "error");
    throw error;
  }
}

async function savePaperImportance(paperId, tags) {
  await savePaperImportanceLevel(paperId, normalizeImportanceLevel(tags));
}

async function savePaperImportanceLevel(paperId, level, options = {}) {
  if (!paperId) return;
  const body = importanceFieldsForLevel(level);
  const fromLibrary = document.body.dataset.activeView === "library";
  if (fromLibrary) captureLibraryScroll();
  const paper = state.library?.papers?.find(item => item.id === paperId);
  const previous = paperSnapshot(paper);
  const previousMetadata = state.currentPaperId === paperId && state.payload?.metadata ? paperSnapshot(state.payload.metadata) : null;
  if (paper) Object.assign(paper, body);
  if (state.currentPaperId === paperId && state.payload?.metadata) {
    Object.assign(state.payload.metadata, body);
    renderPaperMeta();
  }
  if (fromLibrary && options.renderLibrary !== false) {
    refreshLibraryRowOrRender(paperId);
    restoreLibraryScroll();
  }
  setMetadataSaveState(paperId, "Saving...", "saving");
  try {
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/metadata`, { method: "POST", body: JSON.stringify(body) });
    const metadata = response.metadata || body;
    if (paper) Object.assign(paper, body, metadata);
    if (state.currentPaperId === paperId && state.payload?.metadata) {
      Object.assign(state.payload.metadata, body, metadata);
      renderPaperMeta();
    }
    if (fromLibrary && options.renderLibrary !== false) refreshLibraryRow(paperId);
    setMetadataSaveState(paperId, "Saved", "saved");
    if (!options.silent) toast(body.importance ? `Importance set to ${body.importance}/${maxImportanceStars}` : "Importance cleared");
  } catch (error) {
    restorePaperSnapshot(paper, previous);
    if (previousMetadata && state.currentPaperId === paperId && state.payload?.metadata) {
      restorePaperSnapshot(state.payload.metadata, previousMetadata);
      renderPaperMeta();
    }
    if (fromLibrary && options.renderLibrary !== false) refreshLibraryRowOrRender(paperId);
    setMetadataSaveState(paperId, "Save failed", "error");
    throw error;
  }
}

function bindImportanceStarEditors(root = document) {
  Array.from(root.querySelectorAll?.("[data-set-importance-stars]") || []).forEach(button => {
    if (button.dataset.importanceBound === "1") return;
    button.dataset.importanceBound = "1";
    button.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      const paperId = button.dataset.setImportanceStars || state.currentPaperId || "";
      const currentLevel = button.closest(".importance-star-editor")?.querySelectorAll(".importance-star-button.active").length || 0;
      const clickedLevel = normalizeImportanceLevel(button.dataset.importanceLevel);
      const nextLevel = clickedLevel === currentLevel ? 0 : clickedLevel;
      savePaperImportanceLevel(paperId, nextLevel, { silent: true }).catch(error => toast(`Importance save failed: ${error.message}`));
    });
  });
}

async function savePaperProjects(paperId, projects, projectColors = null) {
  const nextProjects = uniqueTags(projects);
  captureLibraryScroll();
  const body = { projects: nextProjects, project: nextProjects[0] || "" };
  if (projectColors) body.project_colors = projectColors;
  const paper = state.library?.papers?.find(item => item.id === paperId);
  const previous = paperSnapshot(paper);
  if (paper) Object.assign(paper, { projects: nextProjects, project: nextProjects[0] || "", ...(projectColors ? { project_colors: projectColors } : {}) });
  refreshLibraryRowOrRender(paperId);
  restoreLibraryScroll();
  setMetadataSaveState(paperId, "Saving...", "saving");
  try {
    const response = await api(`/api/papers/${encodeURIComponent(paperId)}/metadata`, { method: "POST", body: JSON.stringify(body) });
    if (paper) Object.assign(paper, { projects: nextProjects, project: nextProjects[0] || "", ...(projectColors ? { project_colors: projectColors } : {}) }, response.metadata || {});
    refreshLibraryRow(paperId);
    setMetadataSaveState(paperId, "Saved", "saved");
  } catch (error) {
    restorePaperSnapshot(paper, previous);
    refreshLibraryRowOrRender(paperId);
    setMetadataSaveState(paperId, "Save failed", "error");
    throw error;
  }
}

async function addPaperProject(paperId, project, color = "") {
  const value = String(project || "").trim();
  if (!paperId || !value) return;
  const colors = projectColorsForPaper(paperId);
  if (color) colors[value] = color;
  else if (!colors[value]) colors[value] = projectColor(value);
  const paper = state.library?.papers?.find(item => item.id === paperId);
  state.libraryProjectMenuPaperId = "";
  await savePaperProjects(paperId, [...paperProjects(paper), value], colors);
  toast("Project added");
}

async function addPaperProjectFromInput(paperId) {
  const input = document.querySelector(`[data-paper-project-input="${cssEscape(paperId)}"]`);
  const value = input?.value?.trim();
  if (input) input.value = "";
  await addPaperProject(paperId, value, projectColor(value));
}

async function removePaperProject(paperId, project) {
  if (!paperId || !project) return;
  const paper = state.library?.papers?.find(item => item.id === paperId);
  await savePaperProjects(paperId, paperProjects(paper).filter(item => item !== project));
  toast("Project removed");
}

function tagsForPaper(paperId) {
  const paper = state.library?.papers?.find(item => item.id === paperId);
  return normalizeTagsInput(paper?.tags || []);
}

function projectsForNote(note = {}) {
  const direct = normalizeTagsInput(note.paper_projects || note.paper_project || []);
  if (direct.length) return direct.map(normalizeProjectName).filter(Boolean);
  const paper = state.library?.papers?.find(item => item.id === note.paper_id);
  return paper ? paperProjects(paper) : [];
}

function allNoteProjects() {
  const projects = new Set(allLibraryProjects().map(normalizeProjectName));
  let hasUnassigned = false;
  for (const note of state.allNotes || []) {
    const values = projectsForNote(note);
    if (!values.length) hasUnassigned = true;
    values.forEach(project => projects.add(project));
  }
  const sorted = Array.from(projects).filter(Boolean).sort((a, b) => a.localeCompare(b));
  return hasUnassigned ? [...sorted, "Unassigned"] : sorted;
}

function noteMatchesProjectFilters(note, selectedProjects = state.selectedNoteProjects || []) {
  if (!selectedProjects.length) return true;
  const projects = projectsForNote(note);
  return selectedProjects.some(project => project === "Unassigned" ? !projects.length : projects.includes(project));
}

function noteMatchesTagFilters(note, selectedFilters = state.selectedNoteFilters || []) {
  return !selectedFilters.length || annotationTags(note).some(tag => selectedFilters.includes(tag));
}

async function addPaperTag(paperId, tag, color = "") {
  const values = canonicalTagIdsForInput(tag);
  if (!paperId || !values.length) return;
  const colors = tagColorsForPaper(paperId);
  for (const value of values) {
    if (color) colors[value] = color;
    else if (!colors[value]) colors[value] = tagColor(value);
  }
  state.libraryTagMenuPaperId = "";
  await savePaperTags(paperId, [...tagsForPaper(paperId), ...values], colors);
  toast("Tag added");
}

async function addPaperTagFromInput(paperId) {
  const input = document.querySelector(`[data-paper-tag-input="${cssEscape(paperId)}"]`);
  const value = input?.value?.trim();
  if (input) input.value = "";
  const selectedColor = document.querySelector(`[name="tag-color-${cssEscape(paperId)}"]:checked`)?.value || tagColorPalette[0];
  await addPaperTag(paperId, value, selectedColor);
}

async function removePaperTag(paperId, tag) {
  if (!paperId || !tag) return;
  await savePaperTags(paperId, tagsForPaper(paperId).filter(item => item !== tag));
  toast("Tag removed");
}

function captureLibraryScroll() {
  const tableWrap = qs(".library-table-wrap");
  const root = qs("#libraryRoot");
  state.libraryTableScroll = {
    tableTop: tableWrap?.scrollTop || 0,
    tableLeft: tableWrap?.scrollLeft || 0,
    rootLeft: root?.scrollLeft || 0,
    windowY: window.scrollY || document.documentElement.scrollTop || 0,
  };
  const key = currentLibraryViewKey();
  state.libraryScrollSnapshots[key] = state.libraryTableScroll;
  localStorage.setItem(libraryScrollStorageKey, JSON.stringify(state.libraryScrollSnapshots));
  saveCurrentLibraryViewSettings();
}

function restoreLibraryScroll() {
  const key = currentLibraryViewKey();
  const snapshot = state.libraryScrollSnapshots[key] || state.libraryViewSettings[key]?.scroll || state.libraryTableScroll || {};
  state.libraryTableScroll = snapshot;
  const apply = () => {
    const tableWrap = qs(".library-table-wrap");
    const root = qs("#libraryRoot");
    if (tableWrap) {
      tableWrap.scrollTop = Number(snapshot.tableTop || 0);
      tableWrap.scrollLeft = Number(snapshot.tableLeft || 0);
    }
    if (root) root.scrollLeft = Number(snapshot.rootLeft || 0);
    if (document.body.dataset.activeView === "library") window.scrollTo({ top: Number(snapshot.windowY || 0), behavior: "auto" });
  };
  apply();
  requestAnimationFrame(() => {
    apply();
    setTimeout(apply, 0);
    setTimeout(apply, 80);
  });
}

function renderLibraryPreservingScroll() {
  captureLibraryScroll();
  renderLibrary();
  restoreLibraryScroll();
}

function libraryScoped(root, selector) {
  return Array.from((root || document).querySelectorAll?.(selector) || []);
}

function bindLibraryRowEvents(root = document) {
  libraryScoped(root, "[data-open-paper]").forEach(button => button.addEventListener("click", async () => {
    if (await loadPaper(button.dataset.openPaper)) activateView("reader");
  }));
  libraryScoped(root, "[data-preview-paper]").forEach(button => button.addEventListener("click", () => openLibraryPreview(button.dataset.previewPaper)));
  bindImportanceStarEditors(root);
  libraryScoped(root, "[data-field]").forEach(field => {
    const row = field.closest("[data-paper-row]");
    const paperId = row?.dataset.paperRow;
    if (!paperId) return;
    const eventName = field.tagName === "SELECT" ? "change" : "input";
    if (field.dataset.field === "read_status") {
      field.addEventListener("change", () => {
        field.className = `read-status-select read-status-${readStatusTone(field.value)}`;
      });
    }
    field.addEventListener(eventName, () => scheduleMetadataSave(paperId));
    field.addEventListener("blur", () => scheduleMetadataSave(paperId, 40));
  });
  libraryScoped(root, "[data-process-paper]").forEach(button => button.addEventListener("click", () => processPaper(button.dataset.processPaper, button.dataset.mode)));
  libraryScoped(root, "[data-add-library-paper-to-mindmap]").forEach(button => button.addEventListener("click", async () => {
    if (!state.mindmap) await loadMindmap(state.currentMindmapProject || "collaborative");
    const category = window.prompt("Mindmap category path (use / for nested categories):", normalizeTagsInput(state.library?.papers?.find(item => item.id === button.dataset.addLibraryPaperToMindmap)?.tags || [])[0] || "Uncategorized");
    const categoryPath = String(category || "").split(/[\\/]+/).map(item => item.trim()).filter(Boolean);
    if (!categoryPath.length) return;
    await addPaperToMindmap(button.dataset.addLibraryPaperToMindmap, { categoryPath, source: "library" });
  }));
  libraryScoped(root, "[data-translate-paper]").forEach(button => button.addEventListener("click", () => translatePaper(button.dataset.translatePaper)));
  libraryScoped(root, "[data-refresh-citation]").forEach(button => button.addEventListener("click", () => refreshCitation(button.dataset.refreshCitation)));
  libraryScoped(root, "[data-find-pdf]").forEach(button => button.addEventListener("click", () => findPdfForPaper(button.dataset.findPdf)));
  libraryScoped(root, "[data-refresh-videos]").forEach(button => button.addEventListener("click", () => refreshVideos(button.dataset.refreshVideos)));
  libraryScoped(root, "[data-add-video]").forEach(button => button.addEventListener("click", () => addVideoLink(button.dataset.addVideo)));
  libraryScoped(root, "[data-video-input]").forEach(input => input.addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault();
      addVideoLink(input.dataset.videoInput);
    }
  }));
  libraryScoped(root, "[data-delete-video]").forEach(button => button.addEventListener("click", () => deleteVideoLink(button.dataset.deleteVideo, button.dataset.videoIndex)));
  libraryScoped(root, "[data-delete-paper]").forEach(button => button.addEventListener("click", () => deletePaper(button.dataset.deletePaper)));
  libraryScoped(root, "[data-attach-pdf]").forEach(button => button.addEventListener("click", () => {
    document.querySelector(`[data-attach-pdf-input="${cssEscape(button.dataset.attachPdf)}"]`)?.click();
  }));
  libraryScoped(root, "[data-attach-pdf-input]").forEach(input => input.addEventListener("change", async () => {
    const paperId = input.dataset.attachPdfInput;
    try {
      await uploadPdfFiles(input.files, paperId);
    } catch (error) {
      toast(`Attach failed: ${error.message}`);
    } finally {
      input.value = "";
    }
  }));
  libraryScoped(root, "[data-open-tag-menu]").forEach(button => button.addEventListener("click", event => {
    event.stopPropagation();
    const paperId = button.dataset.openTagMenu;
    const previousPaperId = state.libraryTagMenuPaperId;
    state.libraryTagMenuPaperId = previousPaperId === paperId ? "" : paperId;
    state.libraryProjectMenuPaperId = "";
    if (previousPaperId && previousPaperId !== paperId) refreshLibraryRow(previousPaperId);
    refreshLibraryRowOrRender(paperId);
  }));
  libraryScoped(root, "[data-open-project-menu]").forEach(button => button.addEventListener("click", event => {
    event.stopPropagation();
    const paperId = button.dataset.openProjectMenu;
    const previousPaperId = state.libraryProjectMenuPaperId;
    state.libraryProjectMenuPaperId = previousPaperId === paperId ? "" : paperId;
    state.libraryTagMenuPaperId = "";
    if (previousPaperId && previousPaperId !== paperId) refreshLibraryRow(previousPaperId);
    refreshLibraryRowOrRender(paperId);
  }));
  libraryScoped(root, "[data-add-existing-tag]").forEach(button => button.addEventListener("click", event => {
    event.stopPropagation();
    addPaperTag(button.dataset.paperId, button.dataset.addExistingTag, tagColor(button.dataset.addExistingTag));
  }));
  libraryScoped(root, "[data-add-custom-tag]").forEach(button => button.addEventListener("click", event => {
    event.stopPropagation();
    addPaperTagFromInput(button.dataset.addCustomTag);
  }));
  libraryScoped(root, "[data-paper-tag-input]").forEach(input => input.addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault();
      addPaperTagFromInput(input.dataset.paperTagInput);
    }
  }));
  libraryScoped(root, "[data-remove-paper-tag]").forEach(button => button.addEventListener("click", () => removePaperTag(button.dataset.paperId, button.dataset.removePaperTag)));
  libraryScoped(root, "[data-add-existing-project]").forEach(button => button.addEventListener("click", event => {
    event.stopPropagation();
    addPaperProject(button.dataset.paperId, button.dataset.addExistingProject, projectColor(button.dataset.addExistingProject));
  }));
  libraryScoped(root, "[data-add-custom-project]").forEach(button => button.addEventListener("click", event => {
    event.stopPropagation();
    addPaperProjectFromInput(button.dataset.addCustomProject);
  }));
  libraryScoped(root, "[data-paper-project-input]").forEach(input => input.addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault();
      addPaperProjectFromInput(input.dataset.paperProjectInput);
    }
  }));
  libraryScoped(root, "[data-remove-paper-project]").forEach(button => button.addEventListener("click", () => removePaperProject(button.dataset.paperId, button.dataset.removePaperProject)));
  initTagOptionFilters(root);
}

function refreshLibraryRow(paperId) {
  const row = document.querySelector(`[data-paper-row="${cssEscape(paperId)}"]`);
  const paper = state.library?.papers?.find(item => item.id === paperId);
  if (!row || !paper) return false;
  const wrapper = document.createElement("tbody");
  wrapper.innerHTML = libraryRowHtml(paper).trim();
  const nextRow = wrapper.querySelector("[data-paper-row]");
  if (!nextRow) return false;
  row.replaceWith(nextRow);
  bindLibraryRowEvents(nextRow);
  return true;
}

function refreshLibraryRowOrRender(paperId) {
  if (!refreshLibraryRow(paperId)) renderLibraryPreservingScroll();
}

function paperSnapshot(paper) {
  return paper ? JSON.parse(JSON.stringify(paper)) : null;
}

function restorePaperSnapshot(paper, snapshot) {
  if (!paper || !snapshot) return;
  for (const key of Object.keys(paper)) delete paper[key];
  Object.assign(paper, snapshot);
}

function closeLibraryTagMenus(options = {}) {
  if (!state.libraryTagMenuPaperId && !state.libraryProjectMenuPaperId) return;
  state.libraryTagMenuPaperId = "";
  state.libraryProjectMenuPaperId = "";
  if (options.render !== false) renderLibraryPreservingScroll();
}

function sourceParentPaper(paper) {
  const parentId = String(paper?.source_parent_paper_id || "").trim();
  if (!parentId) return null;
  return (state.library?.papers || []).find(item => item.id === parentId) || { id: parentId, title: paper?.source_parent_paper_title || parentId };
}

function sourceHtml(paper) {
  if (paper?.source_type === "reference") {
    const parent = sourceParentPaper(paper);
    if (parent?.id) {
      return `<button class="library-source-link" data-open-paper="${escapeHtml(parent.id)}" type="button" title="${escapeHtml(`Citation from ${paperTitle(parent)}`)}"><span>Citation from</span><strong>${escapeHtml(compactText(paperTitle(parent), 82))}</strong></button>`;
    }
    return '<span class="source-pill">Reference</span>';
  }
  if (paper?.source_type === "pdf") return '<span class="muted small-text">PDF</span>';
  return '<span class="muted small-text">-</span>';
}

function paperAuthors(paper) { return paper.authors || paper.author || ""; }
function paperInstitutions(paper) { return paper.institutions || paper.institution || ""; }
function paperJournal(paper) { return paper.venue || paper.journal || ""; }
function paperYear(paper) { return paper.year || paper.publication_year || ""; }
function paperAddedTime(paper) { return paper.created_at || paper.created_or_refreshed_at || paper.updated_at || ""; }

function libraryCellInput(field, value, label, extraClass = "") {
  const text = String(value || "");
  return `<input class="library-cell-input ${extraClass}" data-field="${escapeHtml(field)}" value="${escapeHtml(text)}" aria-label="${escapeHtml(label)}" title="${escapeHtml(text)}">`;
}

function libraryTitleCellHtml(paper) {
  const title = paperTitle(paper);
  return `<div class="library-title-cell-layout ${state.libraryPreviewThumbnailsVisible && paperPreviewImage(paper) ? "has-preview" : ""}">
    ${libraryPreviewThumbHtml(paper)}
    <div class="library-title-stack ${state.libraryTitlesCollapsed ? "collapsed" : "expanded"}">
      <textarea class="library-cell-input library-title-input" data-field="title" aria-label="Title" rows="${state.libraryTitlesCollapsed ? 1 : 4}">${escapeHtml(title)}</textarea>
      ${importanceStarEditorHtml(paper, { variant: "library-title", showLabel: false })}
      <div class="library-title-actions">
        <button class="secondary-button library-open-button" data-open-paper="${escapeHtml(paper.id)}">Open</button>
        <button class="secondary-button library-preview-button" data-preview-paper="${escapeHtml(paper.id)}" type="button">Preview</button>
      </div>
    </div>
  </div>`;
}

function citationHtml(paper) {
  if (paper.citation_count !== undefined && paper.citation_count !== "") {
    return `<strong>${escapeHtml(paper.citation_count)}</strong>${paper.citation_source ? `<br><span class="muted small-text">${escapeHtml(paper.citation_source)}</span>` : ""}`;
  }
  if (paper.citation_error) return `<span class="error-text">${escapeHtml(paper.citation_error)}</span>`;
  return '<span class="muted">-</span>';
}

function videoLinksHtml(paper) {
  const status = paper.video_search_status || "not_started";
  const links = paperVideoLinks(paper);
  const quota = paper.youtube_quota || {};
  const quotaText = quota.limit !== undefined ? `<div class="muted small-text">YouTube quota: ${escapeHtml(quota.remaining ?? "?")}/${escapeHtml(quota.limit ?? "?")} left</div>` : "";
  const statusText = {
    not_configured: "Set YOUTUBE_API_KEY and restart",
    quota_limited: "Daily free limit reached",
    no_results: "No video found",
    failed: paper.video_search_error || "Search failed",
    not_started: "Not searched yet",
    ready: "Ready",
  }[status] || status;
  const linkHtml = links.map((link, index) => `
    <div class="video-link-row">
      <a class="video-link" href="${escapeHtml(link.url || "")}" target="_blank" rel="noreferrer">
        <span>${escapeHtml(compactText(link.title || link.url || "YouTube video", 72))}</span>
        ${link.channel ? `<small>${escapeHtml(link.channel)}</small>` : ""}
      </a>
      <button class="icon-button video-delete-button" data-delete-video="${escapeHtml(paper.id)}" data-video-index="${escapeHtml(index)}" type="button" aria-label="Delete video">x</button>
    </div>`).join("");
  const emphasizedStatus = ["failed", "quota_limited", "not_configured"].includes(status);
  return `<div class="video-links-cell">
    ${linkHtml || (emphasizedStatus ? "" : `<span class="muted small-text">${escapeHtml(statusText)}</span>`)}
    ${emphasizedStatus ? `<div class="error-text">${escapeHtml(statusText)}</div>` : ""}
    ${quotaText}
    <div class="video-manual-row">
      <input class="video-url-input" data-video-input="${escapeHtml(paper.id)}" placeholder="Paste YouTube URL" />
      <button class="secondary-button mini-button" data-add-video="${escapeHtml(paper.id)}" type="button">Add</button>
    </div>
    <button class="secondary-button mini-button" data-refresh-videos="${escapeHtml(paper.id)}">Refresh Videos</button>
  </div>`;
}

function libraryPreviewMetadataHtml(metadata = {}) {
  const rows = [
    ["Title", metadata.title],
    ["Authors", metadata.authors || metadata.author],
    ["Institution", metadata.institutions || metadata.institution],
    ["Venue", metadata.venue || metadata.journal],
    ["Year", metadata.year || metadata.publication_year],
    ["重要性", paperImportanceLabel(metadata)],
    ["Read Status", metadata.read_status || metadata.status],
    ["Processing", `${processingLabel(metadata)} / ${processingStatus(metadata)}`],
    ["Citations", metadata.citation_count !== undefined && metadata.citation_count !== "" ? `${metadata.citation_count}${metadata.citation_source ? ` · ${metadata.citation_source}` : ""}` : "-"],
    ["Videos", Array.isArray(metadata.video_links) && metadata.video_links.length ? `${metadata.video_links.length} link(s)` : (metadata.video_search_status || "-")],
    ["Tags", normalizeTagsInput(metadata.tags || []).map(libraryTagLabel).join(", ")],
    ["Projects", normalizeTagsInput(metadata.projects || metadata.project || []).join(", ")],
  ].filter(([, value]) => String(value ?? "").trim());
  return `<section class="library-preview-section">
    <h3>Metadata</h3>
    <dl class="library-preview-meta">
      ${rows.map(([label, value]) => `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd>`).join("")}
    </dl>
  </section>`;
}

function libraryPreviewBriefHtml(payload) {
  const brief = payload?.thinking?.explain?.content || payload?.skim_summary || payload?.skim_analysis?.skim_summary || "";
  return `<section class="library-preview-section">
    <h3>Paper Brief</h3>
    ${brief.trim() ? `<div class="sense-explain-preview">${skimSummaryHtml(brief)}</div>` : '<p class="muted">No Paper Brief yet. Attach a PDF to generate one.</p>'}
  </section>`;
}

function libraryPreviewTakeawayHtml(payload) {
  const doc = normalizeTakeawayDoc(payload?.takeaway_doc || {});
  const outline = payload?.outline || {};
  const report = { categories: [
    { key: "paper", label: "Paper Evidence / 原文信息", groups: presentationPaperGroups },
    { key: "sensemaking", label: "My Sensemaking / 我的思考", groups: presentationSensemakingGroups },
  ] };
  const blocks = doc.blocks.length ? doc.blocks : seedTakeawayDocFromReport({ ...report, buckets: {}, items: [] }).blocks;
  const outlineCount = Array.isArray(outline.outline) ? outline.outline.length : 0;
  return `<section class="library-preview-section library-preview-takeaway">
    <h3>Takeaway Report</h3>
    ${outlineCount ? `<p class="muted small-text">Paper Map: ${escapeHtml(outlineCount)} node(s)</p>` : '<p class="muted small-text">Paper Map will be generated after PDF parsing.</p>'}
    <div class="library-preview-takeaway-tree">
      ${blocks.slice(0, 60).map(block => `<div class="takeaway-preview-row takeaway-preview-${escapeHtml(block.type)}" style="--takeaway-indent: ${Math.max(0, Math.min(6, Number(block.indent || 0)))}"><span>${block.type === "heading" ? "#" : "•"}</span><strong>${escapeHtml(displayText(block.text || block.note || block.quote || "Untitled"))}</strong></div>`).join("")}
    </div>
  </section>`;
}

function renderLibraryPreview() {
  const drawer = qs("#libraryPreviewDrawer");
  const root = qs("#libraryPreviewRoot");
  if (!drawer || !root) return;
  drawer.classList.toggle("open", Boolean(state.libraryPreview.open));
  drawer.setAttribute("aria-hidden", state.libraryPreview.open ? "false" : "true");
  if (!state.libraryPreview.open) return;
  if (state.libraryPreview.loading) {
    root.className = "library-preview-root muted";
    root.textContent = "Loading preview...";
    return;
  }
  if (state.libraryPreview.error) {
    root.className = "library-preview-root error-text";
    root.textContent = state.libraryPreview.error;
    return;
  }
  const payload = state.libraryPreview.payload;
  const metadata = payload?.metadata || state.library?.papers?.find(item => item.id === state.libraryPreview.paperId) || {};
  qs("#libraryPreviewTitle").textContent = paperTitle(metadata) || "Library Preview";
  root.className = "library-preview-root";
  root.innerHTML = `${libraryPreviewMetadataHtml(metadata)}${libraryPreviewBriefHtml(payload)}${libraryPreviewTakeawayHtml(payload)}`;
}

async function openLibraryPreview(paperId) {
  if (!paperId) return;
  state.libraryPreview = { open: true, paperId, payload: null, loading: true, error: "" };
  renderLibraryPreview();
  try {
    const payload = await api(`/api/papers/${encodeURIComponent(paperId)}`);
    if (state.libraryPreview.paperId !== paperId) return;
    state.libraryPreview = { open: true, paperId, payload, loading: false, error: "" };
  } catch (error) {
    state.libraryPreview = { open: true, paperId, payload: null, loading: false, error: `Preview failed: ${error.message}` };
  }
  renderLibraryPreview();
}

function closeLibraryPreview() {
  state.libraryPreview = { open: false, paperId: "", payload: null, loading: false, error: "" };
  renderLibraryPreview();
}

function paperHasParsedBrief(paper) {
  return processingMode(paper) !== "library-only" && processingStatus(paper) === "ready";
}

function libraryPrimaryActionHtml(paper) {
  return paperHasParsedBrief(paper)
    ? `<button class="secondary-button" data-open-paper="${escapeHtml(paper.id)}">Read</button>`
    : `<button class="secondary-button" data-process-paper="${escapeHtml(paper.id)}" data-mode="deep">Parse Markdown</button>`;
}

function sortedLibraryPapers(papers) {
  const filter = state.libraryFilter.trim().toLowerCase();
  const project = state.libraryProject || "all";
  const byProject = project === "all"
    ? [...papers]
    : papers.filter(paper => project === "Unassigned" ? !paperProjects(paper).length : paperProjects(paper).includes(project));
  const visible = filter
    ? byProject.filter(paper => [paperTitle(paper), ...paperProjects(paper), ...paperImportanceTags(paper), sourceParentPaper(paper)?.title || "", paperAuthors(paper), paperInstitutions(paper), paperJournal(paper), paperYear(paper), ...(normalizeTagsInput(paper.tags || []))].join(" ").toLowerCase().includes(filter))
    : [...byProject];
  const sort = state.librarySort;
  return visible.sort((left, right) => {
    if (sort === "title") return paperTitle(left).localeCompare(paperTitle(right));
    if (sort === "project") return (paperProject(left) || "Unassigned").localeCompare(paperProject(right) || "Unassigned") || paperTitle(left).localeCompare(paperTitle(right));
    if (sort === "importance") return paperImportanceLevel(right) - paperImportanceLevel(left) || paperTitle(left).localeCompare(paperTitle(right));
    if (sort === "journal") return paperJournal(left).localeCompare(paperJournal(right)) || paperTitle(left).localeCompare(paperTitle(right));
    if (sort === "year") return String(paperYear(right)).localeCompare(String(paperYear(left))) || paperTitle(left).localeCompare(paperTitle(right));
    if (sort === "cite") return Number(right.citation_count || -1) - Number(left.citation_count || -1);
    if (sort === "recent") return compareRecentReadingActivity(left, right);
    return String(paperAddedTime(right)).localeCompare(String(paperAddedTime(left)));
  });
}

function libraryGroupLabel(paper) {
  if (state.libraryGroup === "project") return paperProjects(paper).join(" / ") || "Unassigned";
  if (state.libraryGroup === "importance") return paperImportanceLabel(paper) || "No Importance";
  if (state.libraryGroup === "tags") return normalizeTagsInput(paper.tags || [])[0] || "No Tags";
  if (state.libraryGroup === "journal") return paperJournal(paper) || "No Journal";
  if (state.libraryGroup === "year") return paperYear(paper) || "No Year";
  if (state.libraryGroup === "read_status") return paper.read_status || "unread";
  return "";
}

function libraryColGroupHtml() {
  return `<colgroup>${libraryColumns.map(column => `<col style="width: ${libraryColumnWidth(column.key)}px">`).join("")}</colgroup>`;
}

function libraryHeaderHtml() {
  return `<thead><tr>${libraryColumns.map(column => `
    <th data-library-column="${escapeHtml(column.key)}">
      <span>${escapeHtml(column.label)}</span>
      <button class="library-column-resizer" data-resize-column="${escapeHtml(column.key)}" aria-label="Resize ${escapeHtml(column.label)} column" type="button"></button>
    </th>`).join("")}</tr></thead>`;
}

function initLibraryColumnResize() {
  qsa("[data-resize-column]").forEach(handle => {
    let startX = 0;
    let startWidth = 0;
    const key = handle.dataset.resizeColumn;
    const move = event => {
      if (!startWidth) return;
      state.libraryColumnWidths[key] = Math.max(84, Math.min(720, startWidth + event.clientX - startX));
      document.querySelectorAll(`col:nth-child(${libraryColumns.findIndex(column => column.key === key) + 1})`).forEach(col => {
        col.style.width = `${state.libraryColumnWidths[key]}px`;
      });
    };
    const stop = event => {
      if (!startWidth) return;
      startWidth = 0;
      document.body.classList.remove("resizing-library-column");
      saveLibraryColumnWidths();
      try { handle.releasePointerCapture(event.pointerId); } catch (error) { /* pointer may be gone */ }
    };
    handle.addEventListener("pointerdown", event => {
      startX = event.clientX;
      startWidth = libraryColumnWidth(key);
      document.body.classList.add("resizing-library-column");
      handle.setPointerCapture(event.pointerId);
      event.preventDefault();
      event.stopPropagation();
    });
    handle.addEventListener("pointermove", move);
    handle.addEventListener("pointerup", stop);
    handle.addEventListener("pointercancel", stop);
  });
}

function libraryRowsHtml(papers) {
  const rows = [];
  let currentGroup = null;
  for (const paper of papers) {
    const group = libraryGroupLabel(paper);
    if (state.libraryGroup !== "none" && group !== currentGroup) {
      currentGroup = group;
      rows.push(`<tr class="library-group-row"><td colspan="${libraryColumns.length}">${escapeHtml(group)}</td></tr>`);
    }
    rows.push(libraryRowHtml(paper));
  }
  return rows.join("");
}

function projectContextPanelHtml() {
  if (!state.projectContextPanel.open) return "";
  const projects = allLibraryProjects();
  const fallbackProject = state.libraryProject !== "all" && state.libraryProject !== "Unassigned" ? state.libraryProject : "collaborative";
  const project = projects.includes(state.projectContextPanel.project) ? state.projectContextPanel.project : fallbackProject;
  state.projectContextPanel.project = project;
  const context = projectContextFor(project);
  const cards = projectContextCards(project);
  const sourcePath = context.source_path || "";
  return `
    <section class="project-context-panel" aria-label="Project Context">
      <div class="project-context-header">
        <div>
          <span class="sense-kicker">Project Context</span>
          <h2>${escapeHtml(project)}</h2>
        </div>
        <button class="icon-button" id="closeProjectContextPanel" type="button" title="Close Project Context">x</button>
      </div>
      <div class="project-context-controls">
        <label>Project <select id="projectContextProject">
          ${projects.map(item => `<option value="${escapeHtml(item)}" ${item === project ? "selected" : ""}>${escapeHtml(item)}</option>`).join("")}
        </select></label>
        <label class="project-context-source-field">Source file <input id="projectContextSourcePath" type="text" value="${escapeHtml(sourcePath)}" placeholder="E:\\path\\to\\outline.html" /></label>
        <button class="primary-button mini-button" id="refreshProjectContext" type="button" ${state.projectContextPanel.saving ? "disabled" : ""}>${state.projectContextPanel.saving ? "Refreshing..." : "Save + Refresh"}</button>
      </div>
      <div class="project-context-status ${state.projectContextPanel.error ? "error" : ""}">
        ${state.projectContextPanel.error ? escapeHtml(state.projectContextPanel.error) : `${escapeHtml(cards.length)} context cards${context.source_chars ? ` · ${escapeHtml(context.source_chars)} source chars` : ""}${context.refreshed_at ? ` · refreshed ${escapeHtml(context.refreshed_at.slice(0, 16).replace("T", " "))}` : ""}`}
      </div>
      <div class="project-context-card-list">
        ${cards.length ? cards.slice(0, 8).map(card => `
          <article class="project-context-card">
            <div class="project-context-card-top"><span>${escapeHtml(card.type || "background")}</span><strong>${escapeHtml(card.title || "Context")}</strong></div>
            <p>${escapeHtml(card.summary || "")}</p>
          </article>
        `).join("") : '<p class="muted small-text">Connect a local outline file, then refresh to create compact cards for AI chat and future Mindmap use.</p>'}
      </div>
    </section>`;
}

function libraryRowHtml(paper) {
  const readStatus = paper.read_status || "unread";
  return `
      <tr data-paper-row="${escapeHtml(paper.id)}">
        <td class="library-title-cell">${libraryTitleCellHtml(paper)}</td>
        <td class="library-project-cell">${libraryProjectEditorHtml(paper)}</td>
        <td class="library-source-cell">${sourceHtml(paper)}</td>
        <td>${libraryCellInput("authors", paperAuthors(paper), "Author")}</td>
        <td>${libraryCellInput("institutions", paperInstitutions(paper), "Institution")}</td>
        <td>${libraryCellInput("venue", paperJournal(paper), "Journal")}</td>
        <td>${libraryCellInput("year", paperYear(paper), "Publication Year")}</td>
        <td class="library-importance-cell">${libraryImportanceEditorHtml(paper)}</td>
        <td class="library-tag-cell">${libraryTagEditorHtml(paper)}</td>
        <td>${citationHtml(paper)}<br><button class="secondary-button mini-button" data-refresh-citation="${escapeHtml(paper.id)}">Refresh</button></td>
        <td class="library-video-cell">${videoLinksHtml(paper)}</td>
        <td class="read-status-cell"><select class="read-status-select read-status-${escapeHtml(readStatusTone(readStatus))}" data-field="read_status">
          ${["unread", "skimming", "skimmed", "deep-reading", "read", "archived"].map(v => `<option value="${v}" ${readStatus === v ? "selected" : ""}>${v}</option>`).join("")}
        </select>${readingProgressSummaryHtml(paper)}</td>
        <td><span class="mode-pill">${escapeHtml(processingLabel(paper))}</span><br><span class="muted small-text">${escapeHtml(processingStatus(paper))}</span>${paper.processing_error ? `<br><span class="error-text">${escapeHtml(paper.processing_error)}</span>` : ""}${paper.translation_status ? `<br><span class="muted small-text">Translation: ${escapeHtml(paper.translation_status)}</span>` : ""}${paper.translation_error ? `<br><span class="error-text">${escapeHtml(paper.translation_error)}</span>` : ""}</td>
        <td class="library-pdf-cell">
          ${paper.source_pdf ? `<a class="secondary-button mini-button" href="/api/papers/${encodeURIComponent(paper.id)}/pdf" target="_blank">PDF</a>` : `<span class="muted small-text">No PDF</span>`}
          <input type="file" accept="application/pdf,.pdf" hidden data-attach-pdf-input="${escapeHtml(paper.id)}">
          <div class="library-pdf-actions">
            ${paper.source_pdf ? "" : `<button class="secondary-button mini-button" data-find-pdf="${escapeHtml(paper.id)}" type="button">Find PDF</button>`}
            <button class="secondary-button mini-button" data-attach-pdf="${escapeHtml(paper.id)}" type="button">Attach</button>
          </div>
          ${paper.reference_pdf_error ? `<span class="error-text small-text">${escapeHtml(paper.reference_pdf_error)}</span>` : ""}
        </td>
        <td class="library-actions">
          <div class="library-action-buttons">
            ${libraryPrimaryActionHtml(paper)}
            <button class="danger-button" data-delete-paper="${escapeHtml(paper.id)}">Delete</button>
          </div>
        </td>
      </tr>`;
}

function renderLibrary() {
  const root = qs("#libraryRoot");
  state.libraryDirty = false;
  const papers = state.library?.papers || [];
  renderLibraryTagPrompt();
  const projects = allLibraryProjects();
  if (state.libraryProject !== "all" && !projects.includes(state.libraryProject) && state.libraryProject !== "Unassigned") {
    state.libraryProject = "all";
  }
  const visiblePapers = sortedLibraryPapers(papers);
  const pagingKey = JSON.stringify([state.libraryFilter, state.libraryProject, state.librarySort, state.libraryGroup]);
  if (state.libraryPagingKey !== pagingKey) state.libraryPage = 0;
  state.libraryPagingKey = pagingKey;
  const pageCount = Math.max(1, Math.ceil(visiblePapers.length / libraryPageSize));
  state.libraryPage = Math.min(Math.max(0, state.libraryPage), pageCount - 1);
  const pageStart = state.libraryPage * libraryPageSize;
  const pagePapers = visiblePapers.slice(pageStart, pageStart + libraryPageSize);
  const viewChips = uniqueTags(["all", "Unassigned", ...projects]);
  root.innerHTML = `
    <div class="library-view-tabs" aria-label="Project views">
      ${viewChips.map(view => `<button class="library-view-tab ${state.libraryView === view ? "active" : ""}" data-library-view="${escapeHtml(view)}" type="button">${view === "all" ? "All papers" : escapeHtml(view)}</button>`).join("")}
      <button class="library-view-tab library-new-project-view" id="createLibraryProjectView" type="button">+ Project view</button>
      <button class="library-view-tab project-context-entry ${state.projectContextPanel.open ? "active" : ""}" id="openProjectContextPanel" type="button">Project Context</button>
    </div>
    ${projectContextPanelHtml()}
    <div class="library-controls library-grid-controls">
      <input id="libraryFilter" type="search" value="${escapeHtml(state.libraryFilter)}" placeholder="Search title, author, project, importance, journal, year, tags" />
      <label>Project <select id="libraryProject">
        <option value="all" ${state.libraryProject === "all" ? "selected" : ""}>All projects</option>
        <option value="Unassigned" ${state.libraryProject === "Unassigned" ? "selected" : ""}>Unassigned</option>
        ${projects.map(project => `<option value="${escapeHtml(project)}" ${state.libraryProject === project ? "selected" : ""}>${escapeHtml(project)}</option>`).join("")}
      </select></label>
      <label>Sort <select id="librarySort">
        ${[["updated_at", "Added Time"], ["recent", "Recent Reading"], ["title", "Title"], ["project", "Project"], ["importance", "重要性"], ["journal", "Journal"], ["year", "Publication Year"], ["cite", "Cite"]].map(([value, label]) => `<option value="${value}" ${state.librarySort === value ? "selected" : ""}>${label}</option>`).join("")}
      </select></label>
      <label>Group <select id="libraryGroup">
        ${[["none", "None"], ["project", "Project"], ["importance", "重要性"], ["tags", "Tags"], ["journal", "Journal"], ["year", "Publication Year"], ["read_status", "Read Status"]].map(([value, label]) => `<option value="${value}" ${state.libraryGroup === value ? "selected" : ""}>${label}</option>`).join("")}
      </select></label>
      <label>Rows <select id="libraryDensity">
        ${[["compact", "Compact"], ["comfortable", "Comfortable"], ["expanded", "Expanded"]].map(([value, label]) => `<option value="${value}" ${state.libraryDensity === value ? "selected" : ""}>${label}</option>`).join("")}
      </select></label>
      <button class="secondary-button mini-button icon-text-button" id="resetLibraryColumns" type="button" title="Reset library columns" aria-label="Reset library columns"><span class="button-icon" aria-hidden="true">Col</span><span>Reset</span></button>
      <button class="secondary-button mini-button icon-text-button" id="toggleLibraryTitles" type="button" title="${state.libraryTitlesCollapsed ? "Show full titles" : "Collapse titles"}" aria-label="${state.libraryTitlesCollapsed ? "Show full titles" : "Collapse titles"}"><span class="button-icon" aria-hidden="true">Aa</span><span>${state.libraryTitlesCollapsed ? "Full" : "Collapse"}</span></button>
      <button class="secondary-button mini-button icon-text-button library-preview-toggle ${state.libraryPreviewThumbnailsVisible ? "active" : ""}" id="toggleLibraryPreviewThumbs" type="button" aria-pressed="${state.libraryPreviewThumbnailsVisible ? "true" : "false"}" title="${state.libraryPreviewThumbnailsVisible ? "Hide previews" : "Show previews"}" aria-label="${state.libraryPreviewThumbnailsVisible ? "Hide previews" : "Show previews"}"><span class="button-icon" aria-hidden="true">Img</span><span>${state.libraryPreviewThumbnailsVisible ? "Hide" : "Preview"}</span></button>
    </div>
    <div class="library-view-summary">${escapeHtml(visiblePapers.length)} of ${escapeHtml(papers.length)} papers${state.libraryProject !== "all" ? ` · ${escapeHtml(state.libraryProject)}` : ""}
      <nav class="library-pagination" aria-label="Library pages">
        <button type="button" class="secondary-button mini-button" id="libraryPreviousPage" ${state.libraryPage === 0 ? "disabled" : ""}>Previous</button>
        <span aria-live="polite">${visiblePapers.length ? pageStart + 1 : 0}–${Math.min(pageStart + libraryPageSize, visiblePapers.length)} · Page ${state.libraryPage + 1} / ${pageCount}</span>
        <button type="button" class="secondary-button mini-button" id="libraryNextPage" ${state.libraryPage + 1 >= pageCount ? "disabled" : ""}>Next</button>
      </nav>
    </div>
    ${visiblePapers.length ? `
    <div class="library-table-wrap" data-density="${escapeHtml(state.libraryDensity)}">
    <table class="library-table">
      ${libraryColGroupHtml()}
      ${libraryHeaderHtml()}
      <tbody>
        ${libraryRowsHtml(pagePapers)}
      </tbody>
    </table>
    </div>` : '<p class="muted">No papers match the current Library view.</p>'}`;
  qs("#libraryFilter")?.addEventListener("input", event => {
    state.libraryFilter = event.target.value;
    saveCurrentLibraryViewSettings();
    const selection = event.target.selectionStart;
    if (state.libraryFilterTimer) clearTimeout(state.libraryFilterTimer);
    state.libraryFilterTimer = setTimeout(() => {
      renderLibrary();
      const input = qs("#libraryFilter");
      input?.focus({ preventScroll: true });
      if (input && selection !== null) input.setSelectionRange(selection, selection);
    }, 120);
  });
  qs("#libraryPreviousPage")?.addEventListener("click", () => { state.libraryPage -= 1; renderLibraryPreservingScroll(); });
  qs("#libraryNextPage")?.addEventListener("click", () => { state.libraryPage += 1; renderLibraryPreservingScroll(); });
  qs("#librarySort")?.addEventListener("change", event => {
    state.librarySort = event.target.value;
    saveCurrentLibraryViewSettings();
    renderLibrary();
  });
  qs("#libraryProject")?.addEventListener("change", event => {
    applyLibraryView(event.target.value || "all");
  });
  qs("#libraryGroup")?.addEventListener("change", event => {
    state.libraryGroup = event.target.value;
    saveCurrentLibraryViewSettings();
    renderLibrary();
  });
  qs("#libraryDensity")?.addEventListener("change", event => {
    state.libraryDensity = event.target.value || "comfortable";
    localStorage.setItem(libraryDensityStorageKey, state.libraryDensity);
    saveCurrentLibraryViewSettings();
    renderLibrary();
  });
  qsa("[data-library-view]").forEach(button => button.addEventListener("click", () => applyLibraryView(button.dataset.libraryView || "all")));
  qs("#createLibraryProjectView")?.addEventListener("click", createLibraryProjectView);
  qs("#openProjectContextPanel")?.addEventListener("click", () => {
    state.projectContextPanel.open = !state.projectContextPanel.open;
    if (state.libraryProject !== "all" && state.libraryProject !== "Unassigned") state.projectContextPanel.project = state.libraryProject;
    renderLibrary();
  });
  qs("#closeProjectContextPanel")?.addEventListener("click", () => {
    state.projectContextPanel.open = false;
    renderLibrary();
  });
  qs("#projectContextProject")?.addEventListener("change", event => {
    state.projectContextPanel.project = event.target.value || "collaborative";
    state.projectContextPanel.error = "";
    renderLibrary();
  });
  qs("#refreshProjectContext")?.addEventListener("click", refreshProjectContextFromPanel);
  qs("#resetLibraryColumns")?.addEventListener("click", resetLibraryColumnWidths);
  qs("#toggleLibraryTitles")?.addEventListener("click", () => {
    state.libraryTitlesCollapsed = !state.libraryTitlesCollapsed;
    localStorage.setItem(libraryTitleCollapsedStorageKey, state.libraryTitlesCollapsed ? "1" : "0");
    renderLibrary();
  });
  qs("#toggleLibraryPreviewThumbs")?.addEventListener("click", () => {
    state.libraryPreviewThumbnailsVisible = !state.libraryPreviewThumbnailsVisible;
    localStorage.setItem(libraryPreviewThumbsStorageKey, state.libraryPreviewThumbnailsVisible ? "1" : "0");
    renderLibraryPreservingScroll();
  });
  initLibraryColumnResize();
  bindLibraryRowEvents(root);
  for (const [paperId, draft] of state.metadataDrafts) {
    const row = root.querySelector(`[data-paper-row="${cssEscape(paperId)}"]`);
    row?.querySelectorAll("[data-field]").forEach(field => {
      if (Object.prototype.hasOwnProperty.call(draft, field.dataset.field)) {
        const value = draft[field.dataset.field];
        field.value = Array.isArray(value) ? value.join(", ") : value;
      }
    });
  }
}

function createLibraryProjectView() {
  const value = window.prompt("New project view name:");
  const project = String(value || "").trim();
  if (!project) return;
  if (!allLibraryProjects().includes(project)) {
    state.libraryCustomProjects.push(project);
    saveCustomLibraryProjects();
  }
  applyLibraryView(project);
}

async function refreshProjectContextFromPanel() {
  const project = normalizeProjectName(qs("#projectContextProject")?.value || state.projectContextPanel.project || "collaborative");
  const sourcePath = qs("#projectContextSourcePath")?.value?.trim() || "";
  if (!project) return;
  state.projectContextPanel = { ...state.projectContextPanel, open: true, project, saving: true, error: "" };
  renderLibrary();
  try {
    const response = await api(`/api/project-contexts/${encodeURIComponent(project)}`, {
      method: "POST",
      body: JSON.stringify({ source_path: sourcePath, refresh: true }),
    });
    state.projectContexts = response.project_contexts || state.projectContexts;
    state.projectContextPanel = { ...state.projectContextPanel, open: true, project, saving: false, error: "" };
    toast("Project context refreshed");
  } catch (error) {
    state.projectContextPanel = { ...state.projectContextPanel, open: true, project, saving: false, error: error.message };
    toast(`Project context failed: ${error.message}`);
  }
  renderLibrary();
}

function setMetadataSaveState(paperId, message, kind = "") {
  renderReaderSaveStatus();
  const node = document.querySelector(`[data-save-state="${cssEscape(paperId)}"]`);
  if (!node) return;
  node.textContent = message;
  node.dataset.state = kind;
}

function scheduleMetadataSave(paperId, delay = 650) {
  const row = document.querySelector(`[data-paper-row="${cssEscape(paperId)}"]`);
  if (row) {
    const draft = {};
    row.querySelectorAll("[data-field]").forEach(field => {
      draft[field.dataset.field] = field.dataset.field === "tags" ? normalizeTagsInput(field.value) : field.value;
    });
    state.metadataDrafts.set(paperId, draft);
  }
  if (!state.metadataDrafts.has(paperId)) return;
  if (state.metadataSaveTimers.has(paperId)) clearTimeout(state.metadataSaveTimers.get(paperId));
  setMetadataSaveState(paperId, "Editing...", "pending");
  const timer = setTimeout(() => {
    state.metadataSaveTimers.delete(paperId);
    saveMetadataRow(paperId, { silent: true }).catch(error => {
      setMetadataSaveState(paperId, "Save failed", "error");
      toast(`Metadata save failed: ${error.message}`);
    });
  }, delay);
  state.metadataSaveTimers.set(paperId, timer);
}

async function saveMetadataRow(paperId, options = {}) {
  const data = state.metadataDrafts.get(paperId);
  if (!data) return;
  setMetadataSaveState(paperId, "Saving...", "saving");
  const response = await queuePaperWrite(paperId, "metadata", data);
  if (state.metadataDrafts.get(paperId) === data) state.metadataDrafts.delete(paperId);
  const paper = state.library?.papers?.find(item => item.id === paperId);
  if (paper) Object.assign(paper, data, response.metadata || {});
  if (state.currentPaperId === paperId && state.payload?.metadata) Object.assign(state.payload.metadata, data, response.metadata || {});
  invalidatePaperCache(paperId);
  setMetadataSaveState(paperId, "Saved", "saved");
  if (!options.silent) toast("Metadata saved");
}

function scrollToParagraph(paragraphId) {
  const target = document.getElementById(paragraphId);
  if (!target) return;
  state.stopScrollRestore?.();
  if (target.tagName === "DETAILS") target.open = true;
  history.replaceState(null, "", `#${paragraphId}`);
  updateCurrentOutlineHint(state.payload?.outline?.outline || [], paragraphId);
  target.scrollIntoView({ behavior: "smooth", block: "start" });
  target.classList.remove("source-flash");
  window.requestAnimationFrame(() => {
    target.classList.add("source-flash");
    window.setTimeout(() => target.classList.remove("source-flash"), 1500);
  });
}

function saveWorkspaceScrollPosition() {
  if (document.body.dataset.activeView !== "reader" || !state.currentPaperId) return;
  state.workspaceScrollByPaper[state.currentPaperId] = window.scrollY || document.documentElement.scrollTop || 0;
  const viewportTop = readerViewportTop();
  const paragraph = qsa("#documentRoot .paragraph").find(node => node.getBoundingClientRect().bottom > viewportTop);
  if (paragraph) state.workspaceAnchorsByPaper[state.currentPaperId] = { segmentId: paragraph.id, offset: paragraph.getBoundingClientRect().top };
  persistPaperTabs();
}

function readerViewportTop() {
  return Math.max(108, qs("#workspaceToolbar")?.getBoundingClientRect().bottom || 0) + 16;
}

function restoreWorkspaceScrollPosition() {
  if (!state.currentPaperId) return;
  const paperId = state.currentPaperId;
  const y = Number(state.workspaceScrollByPaper[paperId] || 0);
  if (!Number.isFinite(y)) return;
  state.stopScrollRestore?.();
  const saved = state.workspaceAnchorsByPaper[paperId];
  const anchor = saved ? document.getElementById(saved.segmentId) : null;
  let stopped = false;
  const apply = () => {
    if (stopped || state.currentPaperId !== paperId || document.body.dataset.activeView !== "reader") return;
    const top = anchor ? window.scrollY + anchor.getBoundingClientRect().top - saved.offset : y;
    window.scrollTo({ top: Math.max(0, top), behavior: "instant" });
  };
  const images = anchor ? qsa("#documentRoot img").filter(image => !image.complete
    && (anchor.contains(image) || (image.compareDocumentPosition(anchor) & Node.DOCUMENT_POSITION_FOLLOWING))) : [];
  const pending = new Set(images);
  // Keep the same paragraph in view while preceding figure parts finish loading.
  const onImage = event => {
    pending.delete(event.currentTarget);
    requestAnimationFrame(() => {
      apply();
      if (!pending.size) stop();
    });
  };
  const stop = () => {
    stopped = true;
    images.forEach(image => { image.removeEventListener("load", onImage); image.removeEventListener("error", onImage); });
    window.removeEventListener("wheel", stop);
    window.removeEventListener("pointerdown", stop);
    window.removeEventListener("keydown", stop);
    if (state.stopScrollRestore === stop) state.stopScrollRestore = null;
  };
  state.stopScrollRestore = stop;
  images.forEach(image => { image.addEventListener("load", onImage, { once: true }); image.addEventListener("error", onImage, { once: true }); });
  window.addEventListener("wheel", stop, { once: true, passive: true });
  window.addEventListener("pointerdown", stop, { once: true, passive: true });
  window.addEventListener("keydown", stop, { once: true });
  requestAnimationFrame(() => {
    apply();
    if (!pending.size) stop();
  });
}

function activateView(view) {
  const previousView = document.body.dataset.activeView;
  if (previousView === "reader" && view !== "reader") {
    saveWorkspaceScrollPosition();
    state.stopScrollRestore?.();
    stopReaderBackground();
    clearTimeout(state.feishuPollTimer);
  }
  if (previousView === "library" && view !== "library") captureLibraryScroll();
  tickReadingProgress({ skipSchedule: true });
  document.body.dataset.activeView = view;
  qsa(".tab").forEach(tab => tab.classList.toggle("active", tab.dataset.view === view));
  qsa(".view").forEach(node => node.classList.remove("active"));
  qs(`#${view}View`).classList.add("active");
  state.readingLastTick = performance.now();
  if (previousView === "reader" && view !== "reader") scheduleReadingProgressSave(200);
  if (previousView !== "reader" && view === "reader") {
    restoreWorkspaceScrollPosition();
    watchReaderBackground();
    watchFeishuMetadata();
  }
  if (view === "library") {
    if (state.libraryDirty || !qs("#libraryRoot")?.children.length) renderLibrary();
    restoreLibraryScroll();
  }
  if (view === "notes") {
    if (!state.allNotesLoaded) qs("#notesRoot").innerHTML = '<p class="muted">Loading original highlights and notes…</p>';
    loadAllNotes().catch(error => {
      toast(`Notes load failed: ${error.message}`);
      const root = qs("#notesRoot");
      if (!state.allNotesLoaded) root.textContent = `Notes could not be loaded: ${error.message}. Reopen All Notes to retry.`;
    });
  }
  if (view === "canvas" && !state.canvasBoard) loadCanvasBoards().catch(error => toast(`Canvas load failed: ${error.message}`));
  if (view === "mindmap" && !state.mindmap) loadMindmap().catch(error => toast(`Mindmap load failed: ${error.message}`));
  updateAnnotationToolbarVisibility();
}

function bindEvents() {
  qs("#toggleProcessingQueue")?.addEventListener("click", () => toggleProcessingQueue());
  qs("#closeProcessingQueue")?.addEventListener("click", () => toggleProcessingQueue(false));
  qs("#processingQueueItems")?.addEventListener("click", async event => {
    const open = event.target.closest("[data-parse-open]");
    if (open) {
      await openPaperInWorkspace(open.dataset.parseOpen);
      if (state.currentPaperId === open.dataset.parseOpen) toggleProcessingQueue(false);
    }
    const retry = event.target.closest("[data-parse-retry]");
    if (retry) retryQueuedParsing(retry.dataset.parseRetry, retry);
  });
  qs("#openFeishuIntake")?.addEventListener("click", openFeishuIntake);
  qs("#publishReadingToFeishu")?.addEventListener("click", openFeishuPublication);
  qs("#refreshFeishuPublish")?.addEventListener("click", openFeishuPublication);
  qs("#confirmFeishuPublish")?.addEventListener("click", confirmFeishuPublication);
  qs("#closeFeishuPublish")?.addEventListener("click", () => qs("#feishuPublishDialog").close());
  qs("#feishuPublishDialog")?.addEventListener("close", () => {
    cancelPublicationPolling();
    state.feishuPublication.version += 1;
  });
  qs("#feishuPublishDialog")?.addEventListener("keydown", event => {
    if (event.key === "Escape") event.stopPropagation();
  });
  qs("#closeFeishuIntake")?.addEventListener("click", () => qs("#feishuIntakeDialog").close());
  qs("#feishuIntakeDialog")?.addEventListener("close", watchFeishuIntakeProcessing);
  qs("#feishuIntakeDialog")?.addEventListener("keydown", event => {
    if (event.key === "Escape") event.stopPropagation();
  });
  qs("#feishuIntakeSearchForm")?.addEventListener("submit", searchFeishuIntake);
  qs("#feishuIntakeResults")?.addEventListener("click", event => {
    const button = event.target.closest("[data-preview-feishu-record]");
    if (button && !state.feishuIntake.busy) previewFeishuIntake(button.dataset.previewFeishuRecord);
  });
  qs("#feishuIntakePreview")?.addEventListener("input", event => {
    if (event.target.id === "feishuLocalPdfPath") state.feishuIntake.localPath = event.target.value;
  });
  qs("#feishuIntakePreview")?.addEventListener("change", event => {
    if (event.target.id === "feishuAttachmentSelect") {
      state.feishuIntake.fileToken = event.target.value;
      renderFeishuIntake();
    }
  });
  qs("#feishuIntakePreview")?.addEventListener("click", async event => {
    const brief = event.target.closest("[data-feishu-brief]");
    if (brief) { state.feishuIntake.brief = brief.dataset.feishuBrief; renderFeishuIntake(); }
    if (event.target.closest("#queueFeishuPaper")) queueFeishuIntake();
    if (event.target.closest("[data-retry-feishu-parse]")) retryFeishuIntakeParsing();
    if (event.target.closest("[data-view-feishu-queue]")) {
      qs("#feishuIntakeDialog").close();
      toggleProcessingQueue(true);
    }
    const open = event.target.closest("[data-open-feishu-paper]");
    if (open && feishuIntakePhase() === "ready" && open.dataset.openFeishuPaper === state.feishuIntake.localPaper?.id) {
      const cached = state.paperSessions.get(open.dataset.openFeishuPaper);
      if (cached?.payload && (!cached.payload.segments?.length || processingStatus(cached.payload.metadata) !== "ready")) {
        cached.loadedAt = 0;
      }
      await openPaperInWorkspace(open.dataset.openFeishuPaper);
      if (state.currentPaperId === open.dataset.openFeishuPaper) qs("#feishuIntakeDialog").close();
    }
  });
  qs("#toggleTranslationQueue")?.addEventListener("click", () => toggleTranslationQueue());
  qs("#closeTranslationQueue")?.addEventListener("click", () => toggleTranslationQueue(false));
  qs("#translationQueueItems")?.addEventListener("click", event => {
    const open = event.target.closest("[data-queue-open]");
    if (open) openPaperInWorkspace(open.dataset.queueOpen);
    const control = event.target.closest("[data-queue-action]");
    if (control) controlQueuedTranslation(control.dataset.queuePaper, control.dataset.queueAction);
  });
  qs("#toggleFeishuMetadata")?.addEventListener("click", () => {
    state.feishuPanelOpen = !state.feishuPanelOpen;
    renderFeishuMetadata();
  });
  qs("#feishuMetadataPanel")?.addEventListener("input", event => {
    if (event.target.id === "feishuSearchKeyword") feishuPaperState(state.currentPaperId).query = event.target.value;
  });
  qs("#feishuMetadataPanel")?.addEventListener("click", event => {
    if (event.target.closest("[data-close-feishu]")) { state.feishuPanelOpen = false; renderFeishuMetadata(); }
    if (event.target.closest("[data-search-feishu]")) searchFeishuPapers();
    if (event.target.closest("[data-refresh-feishu]")) syncFeishuPaper();
    const match = event.target.closest("[data-link-feishu]");
    if (match) syncFeishuPaper(state.currentPaperId, { record_id: match.dataset.linkFeishu });
  });
  document.addEventListener("pointerdown", event => {
    state.lastPointerPosition = { x: event.clientX, y: event.clientY };
    if (event.target.closest("#noteDrawer, #annotationToolbar, .paper-tab-strip, [data-media-note], [data-edit-annotation], [data-inline-thinking-note], mark[data-annotation-id]")) return;
    if (qs("#noteDrawer")?.classList.contains("open") && !noteDrawerHasChanges()) closeDrawer();
  });
  document.addEventListener("pointerup", event => {
    state.lastPointerPosition = { x: event.clientX, y: event.clientY };
  });
  document.addEventListener("click", event => {
    if (document.body.dataset.activeView !== "library") return;
    if (event.target.closest(".library-tag-menu-wrap")) return;
    closeLibraryTagMenus();
  });
  qs("#paperSelect").addEventListener("change", event => {
    if (event.target.value) openPaperInWorkspace(event.target.value);
    else activateView("library");
  });
  qs("#paperTabs")?.addEventListener("click", event => {
    const close = event.target.closest("[data-close-paper-tab]");
    if (close) { closePaperTab(close.dataset.closePaperTab); return; }
    const tab = event.target.closest("[data-paper-tab]");
    if (tab) openPaperInWorkspace(tab.dataset.paperTab);
  });
  qs("#paperTabs")?.addEventListener("keydown", event => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    const tabs = qsa("#paperTabs [data-paper-tab]");
    if (!tabs.length) return;
    const index = tabs.indexOf(document.activeElement);
    const next = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1
      : (index + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
    event.preventDefault();
    tabs[next].focus();
    openPaperInWorkspace(tabs[next].dataset.paperTab);
  });
  qs("#openPaperLibrary")?.addEventListener("click", () => activateView("library"));
  qs("#exportNotesMarkdown")?.addEventListener("click", () => exportReadingData("md"));
  qs("#exportReadingJson")?.addEventListener("click", () => exportReadingData("json"));
  qs("#reloadCurrentPaper")?.addEventListener("click", () => {
    if (state.currentPaperId) loadPaper(state.currentPaperId, { force: true });
  });
  qs("#toggleReadingTeacher")?.addEventListener("click", () => {
    state.readingTeacher.enabled = !state.readingTeacher.enabled;
    refreshReadingTeacher();
    capturePaperSession();
  });
  qs("#toggleTeacherDepth")?.addEventListener("click", () => {
    state.readingTeacher.showDeep = !state.readingTeacher.showDeep;
    state.readingTeacher.openCardId = "";
    state.readingTeacher.activeCardId = "";
    refreshReadingTeacher();
    capturePaperSession();
  });
  qs("#documentRoot")?.addEventListener("click", handleReadingTeacherSourceClick);
  qsa(".tab").forEach(tab => tab.addEventListener("click", () => activateView(tab.dataset.view)));
  qs("#canvasProject")?.addEventListener("change", event => loadCanvasBoards(event.target.value).catch(error => toast(`Canvas load failed: ${error.message}`)));
  qs("#createCanvasBoard")?.addEventListener("click", () => createCanvasBoard().catch(error => toast(`Create board failed: ${error.message}`)));
  qs("#deleteCanvasBoard")?.addEventListener("click", () => deleteCurrentCanvasBoard().catch(error => toast(`Delete board failed: ${error.message}`)));
  qs("#canvasBoardTitle")?.addEventListener("input", event => {
    if (!state.canvasBoard) return;
    state.canvasBoard.title = event.target.value;
    scheduleCanvasSave();
    renderCanvasBoardList();
  });
  qs("#canvasZoomIn")?.addEventListener("click", () => {
    if (!state.canvasBoard) return;
    state.canvasBoard.viewport.zoom = Math.min(3, Number(state.canvasBoard.viewport.zoom || 1) + 0.1);
    renderCanvas();
    scheduleCanvasSave();
  });
  qs("#canvasZoomOut")?.addEventListener("click", () => {
    if (!state.canvasBoard) return;
    state.canvasBoard.viewport.zoom = Math.max(0.2, Number(state.canvasBoard.viewport.zoom || 1) - 0.1);
    renderCanvas();
    scheduleCanvasSave();
  });
  qs("#canvasResetView")?.addEventListener("click", () => {
    if (!state.canvasBoard) return;
    state.canvasBoard.viewport = { x: 0, y: 0, zoom: 1 };
    renderCanvas();
    scheduleCanvasSave();
  });
  qsa("[data-canvas-tool]").forEach(tool => {
    tool.addEventListener("dragstart", event => {
      state.canvasToolDrag = tool.dataset.canvasTool || "text";
      event.dataTransfer.effectAllowed = "copy";
      event.dataTransfer.setData("text/plain", state.canvasToolDrag);
    });
    tool.addEventListener("click", () => createCanvasObject(tool.dataset.canvasTool || "text"));
  });
  qs("#canvasStage")?.addEventListener("dragover", event => {
    if (!state.canvasToolDrag) return;
    event.preventDefault();
  });
  qs("#canvasStage")?.addEventListener("drop", event => {
    const kind = state.canvasToolDrag || event.dataTransfer.getData("text/plain") || "text";
    if (!kind) return;
    event.preventDefault();
    createCanvasObject(kind, canvasWorldPoint(event.clientX, event.clientY));
    state.canvasToolDrag = "";
  });
  qs("#canvasStage")?.addEventListener("pointerdown", event => {
    if (event.button !== 0 || event.target.closest("[data-canvas-card], [data-canvas-cluster], .canvas-tool")) return;
    if (!state.canvasBoard) return;
    state.selectedCanvasId = "";
    state.selectedCanvasKind = "";
    state.canvasPanning = { clientX: event.clientX, clientY: event.clientY, x: Number(state.canvasBoard.viewport?.x || 0), y: Number(state.canvasBoard.viewport?.y || 0) };
    renderCanvasInspector();
  });
  document.addEventListener("pointermove", event => {
    handleCanvasPointerMove(event);
    handleMindmapPointerMove(event);
  });
  document.addEventListener("pointerup", event => {
    endCanvasPointerInteraction();
    endMindmapPointerInteraction(event);
  });
  qs("#closeCanvasPicker")?.addEventListener("click", closeCanvasPicker);
  qs("#canvasPickerSearch")?.addEventListener("input", event => {
    state.canvasPicker.query = event.target.value;
    renderCanvasPicker();
  });
  qs("#canvasPickerModal")?.addEventListener("click", event => {
    if (event.target.id === "canvasPickerModal") closeCanvasPicker();
  });
  qs("#canvasSyncReview")?.addEventListener("click", () => openCanvasSyncReview().catch(error => toast(`Sync review failed: ${error.message}`)));
  qs("#closeCanvasSync")?.addEventListener("click", closeCanvasSyncReview);
  qs("#canvasSyncModal")?.addEventListener("click", event => {
    if (event.target.id === "canvasSyncModal") closeCanvasSyncReview();
  });
  qs("#applyCanvasSync")?.addEventListener("click", () => applyCanvasSyncReview().catch(error => toast(`Apply sync failed: ${error.message}`)));
  qs("#mindmapProject")?.addEventListener("change", event => {
    state.currentMindmapId = "";
    loadMindmap(event.target.value, "").catch(error => toast(`Mindmap load failed: ${error.message}`));
  });
  qs("#createMindmap")?.addEventListener("click", () => createMindmapView().catch(error => toast(`Create view failed: ${error.message}`)));
  qs("#duplicateMindmap")?.addEventListener("click", () => duplicateCurrentMindmapView().catch(error => toast(`Duplicate view failed: ${error.message}`)));
  qs("#deleteMindmap")?.addEventListener("click", () => deleteCurrentMindmapView().catch(error => toast(`Delete view failed: ${error.message}`)));
  qs("#mindmapTitle")?.addEventListener("input", event => {
    if (!state.mindmap) return;
    state.mindmap.title = event.target.value;
    const rootNode = mindmapNodeById(state.mindmap.root_id);
    if (rootNode) rootNode.title = event.target.value || state.currentMindmapProject || "Mindmap";
    renderMindmapBoardList();
    scheduleMindmapSave();
  });
  qs("#mindmapZoomIn")?.addEventListener("click", () => setMindmapZoom(Number(mindmapViewport().zoom || 1) + 0.1));
  qs("#mindmapZoomOut")?.addEventListener("click", () => setMindmapZoom(Number(mindmapViewport().zoom || 1) - 0.1));
  qs("#mindmapResetView")?.addEventListener("click", resetMindmapView);
  qs("#mindmapAddText")?.addEventListener("click", () => createMindmapField(state.selectedMindmapNodeId || state.mindmap?.root_id || "", "text", "", { allowBlank: true, edit: true, silent: true }).catch(error => toast(`Add text failed: ${error.message}`)));
  qs("#mindmapAddTable")?.addEventListener("click", () => createMindmapField(state.selectedMindmapNodeId || state.mindmap?.root_id || "", "table", "Research Gap Table", { allowBlank: true, silent: true }).catch(error => toast(`Add table failed: ${error.message}`)));
  qs("#mindmapStage")?.addEventListener("pointerdown", startMindmapStagePointer);
  qs("#mindmapStage")?.addEventListener("wheel", event => {
    if (!state.mindmap) return;
    event.preventDefault();
    if (event.ctrlKey || event.metaKey) {
      const delta = event.deltaY > 0 ? -0.08 : 0.08;
      setMindmapZoom(Number(mindmapViewport().zoom || 1) + delta, { x: event.clientX, y: event.clientY });
    } else {
      const viewport = mindmapViewport();
      viewport.x -= event.deltaX;
      viewport.y -= event.deltaY;
      renderMindmapWorldTransform();
      scheduleMindmapSave(450);
    }
  }, { passive: false });
  qs("#mindmapSourceSearch")?.addEventListener("input", event => {
    state.mindmapSourceQuery = event.target.value;
    renderMindmapSourcePool();
  });
  qs("#mindmapSearchButton")?.addEventListener("click", searchMindmapPapers);
  qs("#mindmapSearchInput")?.addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault();
      searchMindmapPapers();
    }
  });
  qsa(".workspace-mode").forEach(button => button.addEventListener("click", () => setWorkspaceMode(button.dataset.workspaceMode)));
  const moreActions = qs("#readerMoreActions");
  moreActions?.addEventListener("click", event => {
    if (!event.target.closest("button, a")) return;
    const restoreFocus = moreActions.contains(document.activeElement);
    moreActions.open = false;
    if (restoreFocus) moreActions.querySelector("summary")?.focus({ preventScroll: true });
  });
  moreActions?.addEventListener("change", event => {
    if (event.target.id === "paperSelect") moreActions.open = false;
  });
  document.addEventListener("click", event => {
    if (moreActions?.open && !moreActions.contains(event.target)) moreActions.open = false;
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && moreActions?.open) {
      event.preventDefault();
      event.stopImmediatePropagation();
      moreActions.open = false;
      moreActions.querySelector("summary")?.focus();
    }
  });
  document.addEventListener("input", event => {
    if (event.target.closest("#noteDrawer, #sensemakingPanel")) renderReaderSaveStatus();
  });
  qs("#toggleWorkspaceMetadata")?.addEventListener("click", toggleWorkspaceMetadataEditor);
  qs("#workspaceMetadataPanel")?.addEventListener("click", handleWorkspaceMetadataClick);
  qsa("[data-reader-side-pane]").forEach(button => button.addEventListener("click", () => {
    if (button.dataset.readerSidePane === "takeaway") openPresentationReport();
    else closePresentationReport();
  }));
  qs("#translateCurrentPaper")?.addEventListener("click", () => translatePaper(state.currentPaperId));
  qs("#openPresentationReport")?.addEventListener("click", togglePresentationReport);
  qs("#closePresentationReport")?.addEventListener("click", closePresentationReport);
  qs("#closeLibraryPreview")?.addEventListener("click", closeLibraryPreview);
  qs("#togglePaperMap")?.addEventListener("click", () => setPaperMapCollapsed(true));
  qs("#togglePaperMapMain")?.addEventListener("click", () => setPaperMapCollapsed(!state.paperMapCollapsed));
  qs("#paperMapRail")?.addEventListener("click", () => setPaperMapCollapsed(false));
  qsa("[data-paper-map-tab]").forEach(button => button.addEventListener("click", () => setPaperMapTab(button.dataset.paperMapTab)));
  qsa("[data-thinking-tab]").forEach(button => button.addEventListener("click", () => {
    state.thinkingTab = button.dataset.thinkingTab || "explain";
    renderSensemakingPanel();
  }));
  qs("#addPaperButton")?.addEventListener("click", addPaperFromForm);
  document.addEventListener("click", event => {
    handleLibraryIntakeClick(event);
  });
  document.addEventListener("keydown", event => {
    if (event.key !== "Enter") return;
    if (event.target?.id === "libraryIntakeProjectCustom") {
      event.preventDefault();
      addLibraryIntakeProjectFromInput();
    }
    if (event.target?.id === "libraryIntakeTagCustom") {
      event.preventDefault();
      addLibraryIntakeTagFromInput();
    }
    if (event.target?.id === "workspaceMetadataProjectCustom") {
      event.preventDefault();
      addWorkspaceProjectFromInput();
    }
    if (event.target?.id === "workspaceMetadataTagCustom") {
      event.preventDefault();
      addWorkspaceTagFromInput();
    }
  });
  qs("#choosePdfFiles")?.addEventListener("click", () => qs("#pdfFilePicker")?.click());
  qs("#pdfFilePicker")?.addEventListener("change", async event => {
    try {
      await uploadPdfFiles(event.target.files);
    } catch (error) {
      toast(`Upload failed: ${error.message}`);
    } finally {
      event.target.value = "";
    }
  });
  const dropZone = qs("#libraryDropZone");
  dropZone?.addEventListener("dragover", event => {
    event.preventDefault();
    dropZone.classList.add("drag-over");
  });
  dropZone?.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
  dropZone?.addEventListener("drop", async event => {
    event.preventDefault();
    dropZone.classList.remove("drag-over");
    try {
      await uploadPdfFiles(event.dataTransfer?.files);
    } catch (error) {
      toast(`Upload failed: ${error.message}`);
    }
  });
  qs("#addPdfPath")?.addEventListener("keydown", event => {
    if (event.key === "Enter") addPaperFromForm();
  });
  document.addEventListener("selectionchange", () => {
    if (qs("#readerView")?.classList.contains("active")) updateToolbarStatus();
  });
  document.addEventListener("visibilitychange", () => {
    tickReadingProgress({ skipSchedule: true });
    if (document.hidden) {
      saveWorkspaceScrollPosition();
      flushReadingProgress({ silent: true });
    }
    else state.readingLastTick = performance.now();
  });
  window.addEventListener("beforeunload", event => {
    saveWorkspaceScrollPosition();
    if (hasUnsavedPaperChanges()) {
      event.preventDefault();
      event.returnValue = "";
    }
    tickReadingProgress({ skipSchedule: true });
    if (!state.currentPaperId || !state.readingProgressDirty || !navigator.sendBeacon) return;
    const blob = new Blob([JSON.stringify({ segments: state.readingProgress?.segments || {} })], { type: "application/json" });
    navigator.sendBeacon(`/api/papers/${encodeURIComponent(state.currentPaperId)}/reading-progress`, blob);
  });
  qs("#annotationToolbar")?.addEventListener("mousedown", event => event.preventDefault());
  document.addEventListener("click", event => {
    const mark = event.target.closest?.('mark[data-annotation-id]');
    if (!mark || window.getSelection()?.toString()) return;
    const annotationId = mark.dataset.annotationId;
    if (!annotationId) return;
    event.noteDrawerOpened = true;
    if (mark.closest(".thinking-text")) openExistingThinkingAnnotationDrawer(annotationId);
    else openExistingAnnotationDrawer(annotationId);
  });
  qsa("[data-toolbar-color]").forEach(button => {
    button.addEventListener("click", () => addHighlightFromSelection(button.dataset.toolbarColor, false));
  });
  qs("#toolbarNote").addEventListener("click", () => addHighlightFromSelection("yellow", true));
  qs("#toolbarQuestion")?.addEventListener("click", () => {
    addHighlightFromSelection("blue", true);
    if (state.pendingAnnotation || state.pendingThinkingAnnotation) {
      renderNoteTagOptions(["question"]);
      state.drawerInitialValue = noteDrawerSnapshot();
    }
  });
  qs("#toolbarAskAi")?.addEventListener("click", askAiFromCurrentSelection);
  qs("#closeDrawer").addEventListener("click", closeDrawer);
  qs("#addCustomTag").addEventListener("click", addCustomDrawerTag);
  qs("#customTagText").addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault();
      addCustomDrawerTag();
    }
  });
  qs("#saveNote").addEventListener("click", () => savePendingAnnotation(true));
  qs("#saveHighlightOnly").addEventListener("click", () => savePendingAnnotation(false));
  qs("#deleteDrawerNote")?.addEventListener("click", deleteDrawerNote);
  document.addEventListener("click", event => {
    if (event.target.closest("#presentationMoveMenu") || event.target.closest("[data-presentation-note-menu]")) return;
    closePresentationMoveMenu();
  });
  document.addEventListener("click", event => {
    if (event.target.closest(".library-tag-menu, .library-add-tag-button")) return;
    if (state.libraryTagMenuPaperId || state.libraryProjectMenuPaperId) {
      state.libraryTagMenuPaperId = "";
      state.libraryProjectMenuPaperId = "";
      if (document.body.dataset.activeView === "library") renderLibrary();
    }
  });
  document.addEventListener("keydown", event => {
    if (handleTakeawayKeyboardShortcut(event)) return;
    if (event.key === "Escape") {
      closeDrawer();
      closeLibraryPreview();
      closePresentationMoveMenu();
      closePresentationReport();
      closeCanvasPicker();
      closeCanvasSyncReview();
    }
  });
}

document.body.dataset.activeView = "reader";
initLibraryPreferences();
initPaperMapCollapse();
initSidebarResize();
initSensemakingResize();
initReaderWidth();
initReportResize();
bindEvents();
loadLibrary().catch(error => {
  console.error(error);
  toast(`Error: ${error.message}`);
});