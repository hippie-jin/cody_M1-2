const API_BASE_URL = window.API_BASE_URL || "http://127.0.0.1:8000";

let currentConversationId = null;

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `요청 실패 (${res.status})`);
  }
  if (res.status === 204) return null;
  return res.json();
}

function setupTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      buttons.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
    });
  });
}

function switchToTab(name) {
  document.querySelector(`.tab-btn[data-tab="${name}"]`).click();
}

async function warmUpBackend() {
  const banner = document.getElementById("cold-start-banner");
  const start = Date.now();
  try {
    await fetch(`${API_BASE_URL}/`);
  } catch (err) {
    // 첫 요청 실패는 서버가 아직 깨어나는 중일 수 있으므로 무시한다
  }
  if (Date.now() - start > 2000) {
    banner.hidden = false;
    setTimeout(() => (banner.hidden = true), 4000);
  }
}

async function refreshSummary() {
  const bar = document.getElementById("summary-bar");
  try {
    const s = await apiFetch("/api/data/summary");
    if (s.count === 0) {
      bar.textContent = "아직 등록된 데이터가 없습니다. '데이터 관리' 탭에서 추가해보세요.";
      return;
    }
    bar.textContent =
      `기간: ${s.period} · 데이터 ${s.count}개 · ` +
      `평균 ${s.metrics.average} · 최대 ${s.metrics.max} · 최소 ${s.metrics.min} · 트렌드: ${s.trend}`;
  } catch (err) {
    bar.textContent = `요약 정보를 불러오지 못했습니다: ${err.message}`;
  }
}

function appendMessage(role, content) {
  const wrap = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = content;
  wrap.appendChild(div);
  wrap.scrollTop = wrap.scrollHeight;
}

function clearChat() {
  document.getElementById("chat-messages").innerHTML = "";
}

async function sendChatMessage(message) {
  appendMessage("user", message);
  const loading = document.getElementById("chat-loading");
  loading.hidden = false;
  try {
    const res = await apiFetch("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: currentConversationId }),
    });
    currentConversationId = res.conversation_id;
    appendMessage("assistant", res.reply);
    refreshHistory();
  } catch (err) {
    appendMessage("assistant", `오류가 발생했습니다: ${err.message}`);
  } finally {
    loading.hidden = true;
  }
}

function setupChat() {
  document.getElementById("chat-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const input = document.getElementById("chat-input");
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    sendChatMessage(message);
  });

  document.getElementById("new-chat-btn").addEventListener("click", () => {
    currentConversationId = null;
    clearChat();
  });
}

function renderDataRow(point) {
  const tr = document.createElement("tr");
  tr.dataset.id = point.id;
  tr.innerHTML = `
    <td><input type="date" value="${point.date}" class="edit-date" /></td>
    <td><input type="number" step="any" value="${point.value}" class="edit-value" /></td>
    <td class="memo-cell"><input type="text" value="${point.memo ?? ""}" class="edit-memo" /></td>
    <td class="row-actions">
      <button class="save-btn">저장</button>
      <button class="danger-btn delete-btn">삭제</button>
    </td>
  `;

  tr.querySelector(".save-btn").addEventListener("click", async () => {
    const date = tr.querySelector(".edit-date").value;
    const value = parseFloat(tr.querySelector(".edit-value").value);
    const memo = tr.querySelector(".edit-memo").value;
    try {
      await apiFetch(`/api/data/${point.id}`, {
        method: "PUT",
        body: JSON.stringify({ date, value, memo }),
      });
      await Promise.all([loadDataList(), refreshSummary()]);
    } catch (err) {
      alert(`수정 실패: ${err.message}`);
    }
  });

  tr.querySelector(".delete-btn").addEventListener("click", async () => {
    if (!confirm("이 데이터를 삭제할까요?")) return;
    try {
      await apiFetch(`/api/data/${point.id}`, { method: "DELETE" });
      await Promise.all([loadDataList(), refreshSummary()]);
    } catch (err) {
      alert(`삭제 실패: ${err.message}`);
    }
  });

  return tr;
}

async function loadDataList() {
  const status = document.getElementById("data-list-status");
  const tbody = document.getElementById("data-table-body");
  status.textContent = "불러오는 중...";
  try {
    const points = await apiFetch("/api/data");
    tbody.innerHTML = "";
    points.forEach((p) => tbody.appendChild(renderDataRow(p)));
    status.textContent = `총 ${points.length}개`;
  } catch (err) {
    status.textContent = `불러오기 실패: ${err.message}`;
  }
}

function setupDataForm() {
  document.getElementById("data-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const date = document.getElementById("data-date").value;
    const value = parseFloat(document.getElementById("data-value").value);
    const memo = document.getElementById("data-memo").value || null;
    try {
      await apiFetch("/api/data", {
        method: "POST",
        body: JSON.stringify({ date, value, memo }),
      });
      e.target.reset();
      await Promise.all([loadDataList(), refreshSummary()]);
    } catch (err) {
      alert(`추가 실패: ${err.message}`);
    }
  });
}

async function loadConversationIntoChat(id) {
  try {
    const conv = await apiFetch(`/api/conversations/${id}`);
    currentConversationId = conv.id;
    clearChat();
    conv.messages.forEach((m) => appendMessage(m.role, m.content));
    switchToTab("chat");
  } catch (err) {
    alert(`대화 불러오기 실패: ${err.message}`);
  }
}

function renderHistoryItem(conv) {
  const div = document.createElement("div");
  div.className = "history-item";
  const date = new Date(conv.created_at).toLocaleString("ko-KR");
  div.innerHTML = `
    <div class="info">
      <div class="title">${conv.title}</div>
      <div class="meta">${date} · 메시지 ${conv.message_count}개</div>
    </div>
    <div class="history-actions">
      <button class="load-btn">불러오기</button>
      <button class="danger-btn del-btn">삭제</button>
    </div>
  `;
  div.querySelector(".load-btn").addEventListener("click", () => loadConversationIntoChat(conv.id));
  div.querySelector(".del-btn").addEventListener("click", async () => {
    if (!confirm("이 대화를 삭제할까요?")) return;
    try {
      await apiFetch(`/api/conversations/${conv.id}`, { method: "DELETE" });
      refreshHistory();
    } catch (err) {
      alert(`삭제 실패: ${err.message}`);
    }
  });
  return div;
}

async function refreshHistory() {
  const list = document.getElementById("history-list");
  try {
    const conversations = await apiFetch("/api/conversations");
    list.innerHTML = "";
    if (conversations.length === 0) {
      list.textContent = "아직 저장된 대화가 없습니다.";
      return;
    }
    conversations.forEach((c) => list.appendChild(renderHistoryItem(c)));
  } catch (err) {
    list.textContent = `대화 목록을 불러오지 못했습니다: ${err.message}`;
  }
}

async function init() {
  setupTabs();
  setupChat();
  setupDataForm();
  await warmUpBackend();
  refreshSummary();
  loadDataList();
  refreshHistory();
}

init();
