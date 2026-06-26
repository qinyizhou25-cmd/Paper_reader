const DEFAULT_BACKEND = "http://127.0.0.1:8765";

const state = {
  backendUrl: DEFAULT_BACKEND,
  candidate: null,
  annotations: [],
  importance: "",
  selectedQuote: "",
  selectedTags: [],
  library: { papers: [] },
  tagDictionary: { paper_tags: [] },
  candidates: [],
};

function qs(selector) { return document.querySelector(selector); }

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function setStatus(message, kind = "") {
  const node = qs("#statusText");
  node.textContent = message || "";
  node.classList.toggle("error", kind === "error");
}

function normalizeBackendUrl(value) {
  return String(value || DEFAULT_BACKEND).trim().replace(/\/$/, "") || DEFAULT_BACKEND;
}

async function loadSettings() {
  const settings = await chrome.storage.local.get(["backendUrl", "promptOverride"]);
  state.backendUrl = normalizeBackendUrl(settings.backendUrl);
  qs("#promptOverride").value = settings.promptOverride || "";
}

async function savePromptOverride() {
  await chrome.storage.local.set({ promptOverride: qs("#promptOverride").value || "" });
}

async function api(path, options = {}) {
  const response = await fetch(`${state.backendUrl}${path}`, options);
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const data = await response.json();
      message = data.error || message;
    } catch (_error) {
      // ignore non-json errors
    }
    throw new Error(message);
  }
  return response.json();
}

function applyWorkspaceData(data) {
  if (data?.library) state.library = data.library;
  if (data?.tag_dictionary) state.tagDictionary = data.tag_dictionary;
  if (Array.isArray(data?.candidates)) state.candidates = data.candidates;
}

async function checkBackend() {
  try {
    const data = await api("/api/candidates");
    applyWorkspaceData(data);
    qs("#connectionState").textContent = `Connected: ${data.workspace || state.backendUrl}`;
    renderTagPicker();
    renderProjectSelect();
  } catch (error) {
    qs("#connectionState").textContent = "Local server not connected";
    setStatus(`Start Paper Reader Agent at ${state.backendUrl}`, "error");
  }
}

function normalizeTagList(value) {
  const raw = Array.isArray(value) ? value : String(value || "").split(/[,;；、]/);
  return raw.map(item => String(item || "").trim()).filter(Boolean);
}

function uniqueValues(values) {
  const seen = new Set();
  const result = [];
  for (const value of values.map(item => String(item || "").trim()).filter(Boolean)) {
    const key = value.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(value);
  }
  return result;
}

function normalizeProjectName(value) {
  const text = String(value || "").trim();
  const key = text.toLowerCase().replace(/\s+/g, "");
  if (["collaborative", "collective"].includes(key)) return "collaborative";
  if (["memories", "memoies"].includes(key)) return "memories";
  return text;
}

function paperProjects(paper = {}) {
  return uniqueValues([...normalizeTagList(paper.projects), normalizeProjectName(paper.project || "")].map(normalizeProjectName));
}

function allPaperTagOptions() {
  const canonical = (state.tagDictionary?.paper_tags || []).map(tag => String(tag.id || tag.label || tag || "").trim());
  const libraryTags = (state.library?.papers || []).flatMap(paper => normalizeTagList(paper.tags));
  const candidateTags = (state.candidates || []).flatMap(candidate => normalizeTagList(candidate.tags));
  return uniqueValues([...canonical, ...libraryTags, ...candidateTags, ...state.selectedTags]).sort((left, right) => left.localeCompare(right));
}

function allProjectOptions() {
  const libraryProjects = (state.library?.papers || []).flatMap(paperProjects);
  const candidateProjects = (state.candidates || []).map(candidate => normalizeProjectName(candidate.project || ""));
  const currentProject = normalizeProjectName(qs("#projectName")?.value || state.candidate?.project || "");
  return uniqueValues(["collaborative", "memories", ...libraryProjects, ...candidateProjects, currentProject]).sort((left, right) => left.localeCompare(right));
}

async function currentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab || {};
}

function looksLikePdfUrl(url) {
  const clean = String(url || "").split("#", 1)[0].split("?", 1)[0].toLowerCase();
  return clean.endsWith(".pdf") || String(url || "").toLowerCase().includes(".pdf");
}

function filenameFromUrl(url) {
  try {
    const parsed = new URL(url);
    const parts = parsed.pathname.split("/").map(part => decodeURIComponent(part)).filter(Boolean);
    const name = parts.at(-1) || "paper";
    return name.toLowerCase().endsWith(".pdf") ? name : `${name.replace(/[^a-z0-9._-]+/gi, "-") || "paper"}.pdf`;
  } catch (_error) {
    return "paper.pdf";
  }
}

async function blobLooksLikePdf(blob, contentType) {
  if (String(contentType || "").toLowerCase().includes("pdf")) return true;
  const header = await blob.slice(0, Math.min(blob.size, 16)).text().catch(() => "");
  return header.startsWith("%PDF");
}

async function fetchPdfWithChromeSession(pdfUrl) {
  const response = await fetch(pdfUrl, {
    method: "GET",
    credentials: "include",
    cache: "no-store",
    headers: { Accept: "application/pdf,*/*" },
  });
  if (!response.ok) {
    throw new Error(`Chrome download failed: HTTP ${response.status} ${response.statusText}`);
  }
  const blob = await response.blob();
  if (!blob.size) throw new Error("Chrome downloaded an empty PDF response.");
  if (!(await blobLooksLikePdf(blob, response.headers.get("Content-Type") || ""))) {
    throw new Error("Chrome did not receive a recognizable PDF. Try the Upload PDF button.");
  }
  return new File([blob], filenameFromUrl(response.url || pdfUrl), { type: "application/pdf" });
}

async function cookieHeaderForUrl(url) {
  if (!chrome.cookies?.getAll) return "";
  const cookies = await chrome.cookies.getAll({ url });
  return cookies.map(cookie => `${cookie.name}=${cookie.value}`).join("; ");
}

function runtimeCall(label, invoke) {
  return new Promise((resolve, reject) => {
    invoke(result => {
      const error = chrome.runtime.lastError;
      if (error) reject(new Error(`${label}: ${error.message}`));
      else resolve(result);
    });
  });
}

function debuggerAttach(target) {
  return runtimeCall("debugger.attach", done => chrome.debugger.attach(target, "1.3", done));
}

function debuggerDetach(target) {
  return runtimeCall("debugger.detach", done => chrome.debugger.detach(target, done)).catch(() => {});
}

function debuggerCommand(target, method, params = {}) {
  return runtimeCall(method, done => chrome.debugger.sendCommand(target, method, params, done));
}

function tabReload(tabId) {
  return runtimeCall("tabs.reload", done => chrome.tabs.reload(tabId, { bypassCache: true }, done));
}

function downloadsDownload(options) {
  return runtimeCall("downloads.download", done => chrome.downloads.download(options, done));
}

function downloadsSearch(query) {
  return runtimeCall("downloads.search", done => chrome.downloads.search(query, done));
}

function waitForDownloadComplete(downloadId, timeoutMs = 120000) {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      cleanup();
      reject(new Error("Timed out waiting for Chrome download to finish."));
    }, timeoutMs);
    const cleanup = () => {
      clearTimeout(timeout);
      chrome.downloads.onChanged.removeListener(listener);
    };
    const listener = delta => {
      if (delta.id !== downloadId) return;
      if (delta.error?.current) {
        cleanup();
        reject(new Error(`Chrome download failed: ${delta.error.current}`));
      } else if (delta.state?.current === "complete") {
        cleanup();
        resolve();
      }
    };
    chrome.downloads.onChanged.addListener(listener);
  });
}

async function generateBriefFromChromeDownload(pdfUrl, tab) {
  if (!chrome.downloads?.download) throw new Error("chrome.downloads API is unavailable.");
  const relativeName = `paper-reader-agent-temp/${Date.now()}-${filenameFromUrl(pdfUrl)}`;
  const downloadId = await downloadsDownload({
    url: pdfUrl,
    filename: relativeName,
    conflictAction: "uniquify",
    saveAs: false,
  });
  await waitForDownloadComplete(downloadId);
  const items = await downloadsSearch({ id: downloadId });
  const item = items?.[0] || {};
  if (!item.filename) throw new Error("Chrome download finished but did not expose a local filename.");
  return api("/api/candidates/brief", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      local_pdf_path: item.filename,
      filename: filenameFromUrl(pdfUrl),
      source_url: pdfUrl,
      source_page_url: tab.url || pdfUrl,
      prompt: qs("#promptOverride").value || "",
      delete_local_pdf_after_import: true,
    }),
  });
}

function responseHeader(headers, name) {
  const cleanName = String(name || "").toLowerCase();
  const found = (headers || []).find(header => String(header.name || "").toLowerCase() === cleanName);
  return found?.value || "";
}

function isPdfNetworkResponse(response) {
  const status = Number(response?.status || 0);
  const mime = String(response?.mimeType || responseHeader(response?.headers, "content-type") || "").toLowerCase();
  return status >= 200 && status < 300 && mime.includes("pdf");
}

function bytesFromDebuggerBody(body, base64Encoded) {
  if (!base64Encoded) return new TextEncoder().encode(body || "");
  const binary = atob(body || "");
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  return bytes;
}

function bytesLookLikePdf(bytes) {
  if (!bytes?.length) return false;
  const limit = Math.min(bytes.length, 1024);
  for (let index = 0; index <= limit - 4; index += 1) {
    if (bytes[index] === 0x25 && bytes[index + 1] === 0x50 && bytes[index + 2] === 0x44 && bytes[index + 3] === 0x46) return true;
  }
  return false;
}

async function capturePdfFromCurrentTab(tab, pdfUrl) {
  if (!tab.id) throw new Error("No active tab id is available for PDF capture.");
  const target = { tabId: tab.id };
  let cleanup = () => {};
  try {
    await debuggerAttach(target);
    await debuggerCommand(target, "Network.enable");
    const request = await new Promise((resolve, reject) => {
      let pdfRequestId = "";
      let pdfResponseUrl = "";
      const timeout = setTimeout(() => {
        cleanup();
        reject(new Error("Timed out waiting for Chrome to load the PDF response."));
      }, 90000);
      const listener = (source, method, params) => {
        if (source.tabId !== tab.id) return;
        if (method === "Network.responseReceived" && isPdfNetworkResponse(params.response)) {
          pdfRequestId = params.requestId;
          pdfResponseUrl = params.response.url || pdfUrl;
        }
        if (method === "Network.loadingFinished" && params.requestId === pdfRequestId) {
          clearTimeout(timeout);
          cleanup();
          resolve({ requestId: pdfRequestId, responseUrl: pdfResponseUrl || pdfUrl });
        }
        if (method === "Network.loadingFailed" && params.requestId === pdfRequestId) {
          clearTimeout(timeout);
          cleanup();
          reject(new Error(params.errorText || "Chrome failed to load the PDF response."));
        }
      };
      cleanup = () => chrome.debugger.onEvent.removeListener(listener);
      chrome.debugger.onEvent.addListener(listener);
      tabReload(tab.id).catch(error => {
        clearTimeout(timeout);
        cleanup();
        reject(error);
      });
    });
    const body = await debuggerCommand(target, "Network.getResponseBody", { requestId: request.requestId });
    const bytes = bytesFromDebuggerBody(body?.body || "", Boolean(body?.base64Encoded));
    if (!bytes.length) throw new Error("Chrome captured an empty PDF body.");
    if (!bytesLookLikePdf(bytes)) throw new Error("Chrome captured a PDF viewer shell instead of the original PDF bytes.");
    return new File([bytes], filenameFromUrl(request.responseUrl || pdfUrl), { type: "application/pdf" });
  } finally {
    cleanup();
    await debuggerDetach(target);
  }
}

async function generateBriefFromBackendUrl(pdfUrl, tab) {
  const cookieHeader = await cookieHeaderForUrl(pdfUrl).catch(() => "");
  return api("/api/candidates/brief", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      pdf_url: pdfUrl,
      source_page_url: tab.url || pdfUrl,
      prompt: qs("#promptOverride").value || "",
      browser_cookie_header: cookieHeader,
      browser_user_agent: navigator.userAgent,
      browser_accept_language: navigator.language || "",
    }),
  });
}

async function useCurrentTab() {
  const tab = await currentTab();
  qs("#pdfUrl").value = tab.url || "";
  if (!looksLikePdfUrl(tab.url || "")) {
    setStatus("Current tab does not look like a direct PDF URL. Paste a PDF URL or upload a PDF file.", "error");
  } else {
    setStatus("PDF URL loaded from current tab.");
  }
}

function markdownToHtml(markdown) {
  const lines = String(markdown || "").replace(/\r\n/g, "\n").split("\n");
  const html = [];
  let inList = false;
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      if (inList) {
        html.push("</ul>");
        inList = false;
      }
      continue;
    }
    const heading = trimmed.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      if (inList) {
        html.push("</ul>");
        inList = false;
      }
      const level = Math.min(3, heading[1].length);
      html.push(`<h${level}>${escapeHtml(heading[2])}</h${level}>`);
      continue;
    }
    const bullet = trimmed.match(/^[-*]\s+(.+)$/);
    if (bullet) {
      if (!inList) {
        html.push("<ul>");
        inList = true;
      }
      html.push(`<li>${escapeHtml(bullet[1])}</li>`);
      continue;
    }
    if (inList) {
      html.push("</ul>");
      inList = false;
    }
    html.push(`<p>${escapeHtml(trimmed)}</p>`);
  }
  if (inList) html.push("</ul>");
  return html.join("\n");
}

function applyBriefHighlights(html, annotations) {
  let result = html;
  for (const annotation of annotations || []) {
    const quote = String(annotation.quote || "").trim();
    if (!quote) continue;
    const escapedQuote = escapeHtml(quote);
    if (!escapedQuote || !result.includes(escapedQuote)) continue;
    const className = annotation.note ? "brief-mark brief-mark-note" : "brief-mark";
    result = result.replace(escapedQuote, `<mark class="${className}" title="${escapeHtml(annotation.note || "Highlight")}">${escapedQuote}</mark>`);
  }
  return result;
}

function renderSelectedTags() {
  const root = qs("#selectedPaperTags");
  if (!root) return;
  if (!state.selectedTags.length) {
    root.innerHTML = '<span class="muted">No paper type selected</span>';
    return;
  }
  root.innerHTML = state.selectedTags.map(tag => `<button class="tag-chip" data-remove-tag="${escapeHtml(tag)}" type="button" title="Remove tag">${escapeHtml(tag)} <span>×</span></button>`).join("");
  root.querySelectorAll("[data-remove-tag]").forEach(button => {
    button.addEventListener("click", async () => {
      state.selectedTags = state.selectedTags.filter(tag => tag !== button.dataset.removeTag);
      renderTagPicker();
      await saveCandidateMetadata({ silent: true });
    });
  });
}

function renderTagOptions() {
  const menu = qs("#paperTagOptions");
  const input = qs("#paperTags");
  if (!menu || !input) return;
  const query = input.value.trim().toLowerCase();
  const options = allPaperTagOptions().filter(tag => !state.selectedTags.includes(tag) && (!query || tag.toLowerCase().includes(query))).slice(0, 18);
  const canCreate = input.value.trim() && !state.selectedTags.some(tag => tag.toLowerCase() === input.value.trim().toLowerCase()) && !options.some(tag => tag.toLowerCase() === input.value.trim().toLowerCase());
  menu.hidden = !input.matches(":focus") && !query;
  menu.innerHTML = [
    ...options.map(tag => `<button class="tag-option" data-add-tag="${escapeHtml(tag)}" type="button">${escapeHtml(tag)}</button>`),
    canCreate ? `<button class="tag-option tag-create" data-create-tag="${escapeHtml(input.value.trim())}" type="button">Create "${escapeHtml(input.value.trim())}"</button>` : "",
    !options.length && !canCreate ? '<span class="muted small">No matching paper types</span>' : "",
  ].join("");
  menu.querySelectorAll("[data-add-tag], [data-create-tag]").forEach(button => {
    button.addEventListener("mousedown", event => event.preventDefault());
    button.addEventListener("click", async () => {
      await addSelectedTag(button.dataset.addTag || button.dataset.createTag || "");
    });
  });
}

function renderTagPicker() {
  renderSelectedTags();
  renderTagOptions();
}

async function addSelectedTag(value) {
  const tag = String(value || "").trim();
  if (!tag) return;
  state.selectedTags = uniqueValues([...state.selectedTags, tag]);
  qs("#paperTags").value = "";
  renderTagPicker();
  await saveCandidateMetadata({ silent: true });
}

function renderProjectSelect() {
  const select = qs("#projectName");
  if (!select) return;
  const current = normalizeProjectName(state.candidate?.project || select.value || "collaborative") || "collaborative";
  const options = allProjectOptions();
  select.innerHTML = options.map(project => `<option value="${escapeHtml(project)}" ${project === current ? "selected" : ""}>${escapeHtml(project)}</option>`).join("");
  select.value = options.includes(current) ? current : options[0] || "collaborative";
}

async function addProjectFromInput() {
  const input = qs("#customProjectName");
  const value = normalizeProjectName(input?.value || "");
  if (!value) return;
  const select = qs("#projectName");
  if (input) input.value = "";
  if (select && !Array.from(select.options).some(option => option.value === value)) {
    select.appendChild(new Option(value, value));
  }
  if (select) select.value = value;
  await saveCandidateMetadata({ silent: true });
  renderProjectSelect();
}

function renderStars() {
  const root = qs("#importanceStars");
  const level = Number(state.importance || 0);
  root.innerHTML = [1, 2, 3].map(star => `<button class="star-button ${star <= level ? "active" : ""}" data-star="${star}" type="button" aria-label="${star === level ? "Clear importance" : `Set ${star} stars`}">${star <= level ? "★" : "☆"}</button>`).join("");
  root.querySelectorAll("[data-star]").forEach(button => {
    button.addEventListener("click", async () => {
      const clicked = button.dataset.star || "";
      state.importance = clicked === state.importance ? "" : clicked;
      renderStars();
      await saveCandidateMetadata({ silent: true });
    });
  });
}

function renderCandidate(candidate) {
  state.candidate = candidate;
  state.annotations = Array.isArray(candidate.annotations) ? candidate.annotations : [];
  state.importance = String(candidate.importance || "");
  state.selectedTags = normalizeTagList(candidate.tags || []);
  qs("#briefSection").hidden = false;
  qs("#saveSection").hidden = false;
  qs("#refreshCandidate").disabled = false;
  qs("#candidateTitle").textContent = candidate.title || "Untitled paper";
  qs("#candidateStatus").textContent = candidate.brief_status || "ready";
  qs("#briefContent").innerHTML = applyBriefHighlights(markdownToHtml(candidate.paper_brief || ""), state.annotations);
  qs("#paperTags").value = "";
  renderProjectSelect();
  if (candidate.project && qs("#projectName")) qs("#projectName").value = candidate.project;
  renderTagPicker();
  renderStars();
  renderNotes();
}

function renderNotes() {
  const root = qs("#notesList");
  if (!state.annotations.length) {
    root.classList.add("muted");
    root.textContent = "No notes yet.";
    return;
  }
  root.classList.remove("muted");
  const template = qs("#noteTemplate");
  root.innerHTML = "";
  for (const note of state.annotations) {
    const node = template.content.cloneNode(true);
    node.querySelector("blockquote").textContent = note.quote || "";
    node.querySelector("p").textContent = note.note || "Highlight";
    if (!note.note) node.querySelector("p").classList.add("muted");
    root.appendChild(node);
  }
}

function selectedBriefText() {
  const selection = window.getSelection();
  if (!selection || !selection.toString().trim()) return "";
  const brief = qs("#briefContent");
  if (!brief.contains(selection.anchorNode) || !brief.contains(selection.focusNode)) return "";
  return selection.toString().trim().replace(/\s+/g, " ").slice(0, 1200);
}

function updateSelectionHint() {
  state.selectedQuote = selectedBriefText();
  qs("#selectionHint").textContent = state.selectedQuote ? `${state.selectedQuote.slice(0, 80)}${state.selectedQuote.length > 80 ? "..." : ""}` : "No text selected";
}

async function saveCandidateAnnotations() {
  if (!state.candidate?.id) return;
  const data = await api(`/api/candidates/${encodeURIComponent(state.candidate.id)}/annotations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ annotations: state.annotations }),
  });
  state.annotations = data.annotations || [];
  if (data.candidate) state.candidate = data.candidate;
  qs("#briefContent").innerHTML = applyBriefHighlights(markdownToHtml(state.candidate?.paper_brief || ""), state.annotations);
  renderNotes();
}

async function addHighlight() {
  updateSelectionHint();
  if (!state.candidate?.id) {
    setStatus("Generate a Paper Brief first.", "error");
    return;
  }
  if (!state.selectedQuote) {
    setStatus("Select text in the Paper Brief first.", "error");
    return;
  }
  state.annotations.push({
    id: `cand-ann-${Date.now().toString(36)}`,
    block_id: "paper-brief",
    target: "thinking",
    quote: state.selectedQuote,
    note: "",
    color: "yellow",
    tags: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  });
  await saveCandidateAnnotations();
  setStatus("Highlight saved to candidate brief.");
}

async function addNote() {
  updateSelectionHint();
  const note = qs("#noteText").value.trim();
  if (!state.candidate?.id) {
    setStatus("Generate a Paper Brief first.", "error");
    return;
  }
  if (!state.selectedQuote && !note) {
    setStatus("Select brief text or write a note first.", "error");
    return;
  }
  state.annotations.push({
    id: `cand-ann-${Date.now().toString(36)}`,
    block_id: "paper-brief",
    target: "thinking",
    quote: state.selectedQuote,
    note,
    color: "yellow",
    tags: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  });
  qs("#noteText").value = "";
  await saveCandidateAnnotations();
  setStatus("Note saved to candidate brief.");
}

function metadataPayload() {
  return {
    tags: state.selectedTags,
    project: normalizeProjectName(qs("#projectName").value),
    importance: state.importance,
    read_status: "unread",
  };
}

async function saveCandidateMetadata(options = {}) {
  if (!state.candidate?.id) return;
  const data = await api(`/api/candidates/${encodeURIComponent(state.candidate.id)}/metadata`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(metadataPayload()),
  });
  state.candidate = data.candidate;
  state.selectedTags = normalizeTagList(state.candidate.tags || state.selectedTags);
  renderTagPicker();
  renderProjectSelect();
  if (!options.silent) setStatus("Candidate metadata saved.");
}

async function generateBriefFromUrl() {
  const pdfUrl = qs("#pdfUrl").value.trim();
  if (!pdfUrl) throw new Error("Paste a PDF URL or upload a PDF file.");
  const tab = await currentTab();
  try {
    const file = await fetchPdfWithChromeSession(pdfUrl);
    return generateBriefFromFile(file, { sourceUrl: pdfUrl, sourcePageUrl: tab.url || pdfUrl });
  } catch (browserError) {
    try {
      return await generateBriefFromBackendUrl(pdfUrl, tab);
    } catch (backendError) {
      try {
        setStatus("ACM blocked direct download; trying Chrome's download manager...");
        return await generateBriefFromChromeDownload(pdfUrl, tab);
      } catch (downloadError) {
        try {
          setStatus("ACM blocked direct download; capturing the PDF from the active browser tab...");
          const capturedFile = await capturePdfFromCurrentTab(tab, pdfUrl);
          return generateBriefFromFile(capturedFile, { sourceUrl: pdfUrl, sourcePageUrl: tab.url || pdfUrl });
        } catch (captureError) {
          throw new Error(`Could not download this PDF. Chrome session: ${browserError.message || browserError}. Backend: ${backendError.message || backendError}. Chrome download: ${downloadError.message || downloadError}. Tab capture: ${captureError.message || captureError}. Reload the extension, allow Downloads/Debugger/site access if prompted, then retry from the visible PDF tab.`);
        }
      }
    }
  }
}

async function generateBriefFromFile(file, options = {}) {
  const tab = await currentTab();
  const form = new FormData();
  form.append("file", file, file.name || "paper.pdf");
  form.append("source_url", options.sourceUrl || qs("#pdfUrl").value.trim() || tab.url || "");
  form.append("source_page_url", options.sourcePageUrl || tab.url || "");
  form.append("prompt", qs("#promptOverride").value || "");
  return api("/api/candidates/brief", { method: "POST", body: form });
}

async function generateBrief() {
  await savePromptOverride();
  setStatus("Generating Paper Brief with local backend + Kimi...");
  qs("#generateBrief").disabled = true;
  try {
    const file = qs("#pdfFile").files?.[0];
    const data = file ? await generateBriefFromFile(file) : await generateBriefFromUrl();
    renderCandidate(data.candidate);
    setStatus("Paper Brief ready.");
  } catch (error) {
    setStatus(error.message || String(error), "error");
  } finally {
    qs("#generateBrief").disabled = false;
  }
}

async function reloadCandidate() {
  if (!state.candidate?.id) return;
  const data = await api(`/api/candidates/${encodeURIComponent(state.candidate.id)}`);
  renderCandidate(data.candidate);
  setStatus("Candidate reloaded.");
}

async function saveToLibrary() {
  if (!state.candidate?.id) return;
  await saveCandidateMetadata({ silent: true });
  setStatus("Saving candidate to Library...");
  qs("#saveToLibrary").disabled = true;
  try {
    const data = await api(`/api/candidates/${encodeURIComponent(state.candidate.id)}/save-to-library`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...metadataPayload(), duplicate_policy: "ask" }),
    });
    if (data.duplicate) {
      setStatus("This paper may already exist in Library. Open Paper Reader Agent to resolve duplicate.", "error");
      return;
    }
    setStatus(`Saved to Library: ${data.paper_id}`);
  } catch (error) {
    setStatus(error.message || String(error), "error");
  } finally {
    qs("#saveToLibrary").disabled = false;
  }
}

async function init() {
  await loadSettings();
  await checkBackend();
  await useCurrentTab().catch(() => {});
  renderStars();
  qs("#openOptions").addEventListener("click", () => chrome.runtime.openOptionsPage());
  qs("#useCurrentTab").addEventListener("click", useCurrentTab);
  qs("#generateBrief").addEventListener("click", generateBrief);
  qs("#refreshCandidate").addEventListener("click", reloadCandidate);
  qs("#briefContent").addEventListener("mouseup", updateSelectionHint);
  qs("#briefContent").addEventListener("keyup", updateSelectionHint);
  qs("#highlightSelection").addEventListener("click", addHighlight);
  qs("#addNote").addEventListener("click", addNote);
  qs("#paperTags").addEventListener("input", renderTagOptions);
  qs("#paperTags").addEventListener("focus", renderTagOptions);
  qs("#paperTags").addEventListener("blur", () => setTimeout(() => { qs("#paperTagOptions").hidden = true; }, 160));
  qs("#paperTags").addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault();
      addSelectedTag(qs("#paperTags").value).catch(error => setStatus(error.message, "error"));
    }
  });
  qs("#projectName").addEventListener("change", () => saveCandidateMetadata().catch(error => setStatus(error.message, "error")));
  qs("#addProject").addEventListener("click", () => addProjectFromInput().catch(error => setStatus(error.message, "error")));
  qs("#customProjectName").addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault();
      addProjectFromInput().catch(error => setStatus(error.message, "error"));
    }
  });
  qs("#saveToLibrary").addEventListener("click", saveToLibrary);
}

init().catch(error => setStatus(error.message || String(error), "error"));
