const state = {
  token: null,
  apiBase: "http://localhost:8000",
  pollTimer: null,
  currentTaskId: null,
};

const qs = (id) => document.getElementById(id);

const loginForm = qs("loginForm");
const processForm = qs("processForm");
const vocabForm = qs("vocabForm");
const refreshHistoryBtn = qs("refreshHistory");

const loginStatus = qs("loginStatus");
const progressPanel = qs("progressPanel");
const progressBar = qs("progressBar");
const progressText = qs("progressText");
const taskIdLabel = qs("taskIdLabel");
const resultArea = qs("resultArea");
const historyList = qs("historyList");
const vocabList = qs("vocabList");
const toastEl = qs("toast");

function showToast(message, duration = 2500) {
  toastEl.textContent = message;
  toastEl.classList.remove("hidden");
  toastEl.classList.add("show");
  setTimeout(() => {
    toastEl.classList.remove("show");
    toastEl.classList.add("hidden");
  }, duration);
}

function setLoading(el, loading) {
  if (loading) {
    el.setAttribute("disabled", "disabled");
  } else {
    el.removeAttribute("disabled");
  }
}

async function login(event) {
  event.preventDefault();

  const apiBase = qs("apiBase").value.trim().replace(/\/+$/, "");
  const username = qs("username").value.trim();
  const password = qs("password").value;

  if (!apiBase) {
    showToast("請輸入 API 位址");
    return;
  }

  state.apiBase = apiBase;
  loginStatus.textContent = "登入中...";
  setLoading(loginForm.querySelector("button"), true);

  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);

  try {
    const resp = await fetch(`${state.apiBase}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });

    if (!resp.ok) {
      throw new Error(`登入失敗：${resp.status}`);
    }
    const data = await resp.json();
    state.token = data.access_token;
    loginStatus.textContent = "登入成功，Token 已取得。";
    showToast("登入成功");
    await Promise.all([loadHistory(), loadVocabulary()]);
  } catch (err) {
    console.error(err);
    loginStatus.textContent = "登入失敗，請檢查帳密與 API 位址。";
    showToast("登入失敗");
  } finally {
    setLoading(loginForm.querySelector("button"), false);
  }
}

function requireToken() {
  if (!state.token) {
    throw new Error("請先登入取得 Token");
  }
}

async function authedFetch(path, options = {}) {
  requireToken();
  const url = `${state.apiBase}${path.startsWith("/") ? path : `/${path}`}`;
  const headers = options.headers ? { ...options.headers } : {};

  if (!options.skipAuth) {
    headers["Authorization"] = `Bearer ${state.token}`;
  }

  const fetchOptions = {
    ...options,
    headers,
  };
  const resp = await fetch(url, fetchOptions);
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `API error: ${resp.status}`);
  }
  return resp;
}

async function startProcess(event) {
  event.preventDefault();
  try {
    requireToken();
  } catch (err) {
    showToast(err.message);
    return;
  }

  const fileInput = qs("audioFile");
  const template = qs("templateSelect").value;

  if (!fileInput.files || !fileInput.files.length) {
    showToast("請選擇音訊檔");
    return;
  }

  const file = fileInput.files[0];

  try {
    setLoading(processForm.querySelector("button"), true);
    progressPanel.classList.remove("hidden");
    progressText.textContent = "上傳中...";
    progressBar.style.width = "10%";

    const formData = new FormData();
    formData.append("file", file, file.name);

    const uploadResp = await authedFetch("/transcription/upload", {
      method: "POST",
      body: formData,
    });
    const uploadData = await uploadResp.json();
    progressText.textContent = "檔案上傳完成，建立任務...";

    const processResp = await authedFetch("/transcription/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_path: uploadData.file_path,
        template_id: template,
      }),
    });
    const processData = await processResp.json();
    const taskId = processData.task_id;
    state.currentTaskId = taskId;
    taskIdLabel.textContent = taskId;
    progressText.textContent = "任務已建立，開始處理...";
    pollTask(taskId);
  } catch (err) {
    console.error(err);
    showToast("任務建立失敗");
    progressText.textContent = "處理失敗，請查看主控台。";
  } finally {
    setLoading(processForm.querySelector("button"), false);
  }
}

function updateProgress(status, progress) {
  progressBar.style.width = `${progress}%`;
  progressText.textContent = `狀態：${status}（${progress}%）`;
}

async function pollTask(taskId) {
  clearTimeout(state.pollTimer);

  try {
    const resp = await authedFetch(`/transcription/tasks/${taskId}`);
    const data = await resp.json();
    updateProgress(data.status, data.progress ?? 0);

    if (data.status === "completed") {
      showToast("處理完成");
      await renderResult(taskId, data);
      await loadHistory();
      return;
    }

    if (data.status === "failed") {
      showToast("處理失敗");
      renderErrorResult(data.error_message || "未知錯誤");
      return;
    }

    state.pollTimer = setTimeout(() => pollTask(taskId), 3000);
  } catch (err) {
    console.error(err);
    showToast("輪詢任務失敗");
    state.pollTimer = setTimeout(() => pollTask(taskId), 4000);
  }
}

function renderErrorResult(message) {
  resultArea.innerHTML = `
    <div class="result-block">
      <h3>錯誤</h3>
      <p>${message}</p>
    </div>
  `;
}

async function renderResult(taskId, taskData) {
  try {
    const artifactsResp = await authedFetch(`/transcription/tasks/${taskId}/artifacts`);
    const artifacts = await artifactsResp.json();
    const summary = taskData.result?.summary || "無摘要";
    const highlights = taskData.result?.highlights || [];

    const highlightsHtml =
      highlights.length > 0
        ? `<ul>${highlights
            .map(
              (item) =>
                `<li>${item.start} ~ ${item.end} <strong>${item.speaker}</strong>：${item.text}</li>`
            )
            .join("")}</ul>`
        : "<p>尚無重點。</p>";

    resultArea.innerHTML = `
      <div class="result-block">
        <h3>摘要</h3>
        <p>${summary}</p>
      </div>
      <div class="result-block">
        <h3>精華重點</h3>
        ${highlightsHtml}
      </div>
      <div class="result-block">
        <h3>Markdown 報告</h3>
        <textarea readonly>${artifacts.report_markdown || "無報告資料"}</textarea>
      </div>
      <div class="result-block">
        <h3>逐字稿</h3>
        <textarea readonly>${artifacts.transcript_text || "無逐字稿資料"}</textarea>
      </div>
      <div class="downloads">
        <button data-kind="report-md">下載 Markdown</button>
        <button data-kind="report-pdf">下載 PDF</button>
        <button data-kind="transcript">下載逐字稿</button>
      </div>
    `;

    resultArea.querySelectorAll(".downloads button").forEach((btn) => {
      btn.addEventListener("click", () => downloadArtifact(taskId, btn.dataset.kind));
    });
  } catch (err) {
    console.error(err);
    renderErrorResult("無法載入結果");
  }
}

async function downloadArtifact(taskId, kind) {
  try {
    const resp = await authedFetch(`/transcription/tasks/${taskId}/download/${kind}`);
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const ext = kind === "report-pdf" ? "pdf" : kind === "report-md" ? "md" : "txt";
    const a = document.createElement("a");
    a.href = url;
    a.download = `${taskId}-${kind}.${ext}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error(err);
    showToast("下載失敗");
  }
}

async function loadHistory() {
  try {
    const resp = await authedFetch("/transcription/history?limit=15");
    const items = await resp.json();
    if (!items.length) {
      historyList.innerHTML = "<p class='placeholder'>尚無歷史記錄。</p>";
      return;
    }
    historyList.innerHTML = items
      .map(
        (item) => `
        <div class="history-item">
          <header>
            <strong>${item.template_id}</strong>
            <small>${item.created_at}</small>
          </header>
          <p>狀態：${item.status} · 進度：${item.progress}%</p>
          ${
            item.result
              ? `<button data-history="${item.id}">查看結果</button>`
              : "<small>尚無結果</small>"
          }
        </div>
      `
      )
      .join("");

    historyList.querySelectorAll("button[data-history]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        try {
          const taskId = btn.dataset.history;
          const taskResp = await authedFetch(`/transcription/tasks/${taskId}`);
          const taskData = await taskResp.json();
          await renderResult(taskId, taskData);
          progressPanel.classList.remove("hidden");
          taskIdLabel.textContent = taskId;
          updateProgress(taskData.status, taskData.progress ?? 100);
        } catch (err) {
          console.error(err);
          showToast("載入歷史結果失敗");
        }
      });
    });
  } catch (err) {
    console.error(err);
    historyList.innerHTML = "<p class='placeholder'>無法載入歷史記錄。</p>";
  }
}

async function loadVocabulary() {
  try {
    const resp = await authedFetch("/vocabulary/");
    const words = await resp.json();
    if (!words.length) {
      vocabList.innerHTML = "<span class='placeholder'>尚未新增詞彙</span>";
      return;
    }
    vocabList.innerHTML = "";
    words.forEach((word) => {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = word;
      tag.title = "點擊刪除";
      tag.addEventListener("click", () => deleteVocabulary(word));
      vocabList.appendChild(tag);
    });
  } catch (err) {
    console.error(err);
    vocabList.innerHTML = "<span class='placeholder'>讀取詞彙失敗</span>";
  }
}

async function addVocabulary(event) {
  event.preventDefault();
  const value = qs("vocabInput").value.trim();
  if (!value) {
    showToast("請輸入詞彙");
    return;
  }
  try {
    await authedFetch("/vocabulary/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ word: value }),
    });
    qs("vocabInput").value = "";
    showToast("新增成功");
    await loadVocabulary();
  } catch (err) {
    console.error(err);
    showToast("新增失敗");
  }
}

async function deleteVocabulary(word) {
  if (!confirm(`確定刪除「${word}」？`)) {
    return;
  }
  try {
    await authedFetch(`/vocabulary/${encodeURIComponent(word)}`, {
      method: "DELETE",
    });
    showToast("已刪除");
    await loadVocabulary();
  } catch (err) {
    console.error(err);
    showToast("刪除失敗");
  }
}

loginForm.addEventListener("submit", login);
processForm.addEventListener("submit", startProcess);
vocabForm.addEventListener("submit", addVocabulary);
refreshHistoryBtn.addEventListener("click", loadHistory);
