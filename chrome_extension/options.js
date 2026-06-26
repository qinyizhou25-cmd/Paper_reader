const DEFAULT_BACKEND = "http://127.0.0.1:8765";

function qs(selector) { return document.querySelector(selector); }
function normalizeBackendUrl(value) { return String(value || DEFAULT_BACKEND).trim().replace(/\/$/, "") || DEFAULT_BACKEND; }
function setStatus(message, kind = "") {
  const node = qs("#statusText");
  node.textContent = message || "";
  node.classList.toggle("error", kind === "error");
}

async function loadOptions() {
  const settings = await chrome.storage.local.get(["backendUrl", "promptOverride"]);
  qs("#backendUrl").value = normalizeBackendUrl(settings.backendUrl);
  qs("#promptOverride").value = settings.promptOverride || "";
}

async function saveOptions() {
  await chrome.storage.local.set({
    backendUrl: normalizeBackendUrl(qs("#backendUrl").value),
    promptOverride: qs("#promptOverride").value || "",
  });
  setStatus("Options saved.");
}

async function testBackend() {
  const backend = normalizeBackendUrl(qs("#backendUrl").value);
  try {
    const response = await fetch(`${backend}/api/candidates`);
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    const data = await response.json();
    setStatus(`Connected: ${data.workspace || backend}`);
  } catch (error) {
    setStatus(`Backend test failed: ${error.message || error}`, "error");
  }
}

qs("#saveOptions").addEventListener("click", saveOptions);
qs("#testBackend").addEventListener("click", testBackend);
loadOptions().catch(error => setStatus(error.message || String(error), "error"));
