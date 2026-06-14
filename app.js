const BACKEND = "https://TU_DOMINIO/generate";

// Estado simple en memoria
let chats = [];
let currentChatId = null;
let currentMode = "chat";
let attachedFiles = [];
let attachedImages = [];

// Utilidades
function createId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function getCurrentChat() {
  return chats.find((c) => c.id === currentChatId) || null;
}

function ensureChat() {
  if (!currentChatId) {
    const id = createId();
    const chat = {
      id,
      title: "Nuevo chat",
      messages: [],
      createdAt: new Date().toISOString(),
    };
    chats.unshift(chat);
    currentChatId = id;
    renderChatList();
  }
}

// Render de lista de chats
function renderChatList() {
  const list = document.getElementById("chat-list");
  list.innerHTML = "";

  if (chats.length === 0) {
    const empty = document.createElement("div");
    empty.className = "panel-item";
    empty.textContent = "No hay chats todavía.";
    list.appendChild(empty);
    return;
  }

  chats.forEach((chat) => {
    const item = document.createElement("div");
    item.className = "chat-list-item" + (chat.id === currentChatId ? " active" : "");
    item.textContent = chat.title || "Chat sin título";
    item.onclick = () => {
      currentChatId = chat.id;
      renderChatList();
      renderMessages();
    };
    list.appendChild(item);
  });
}

// Render de mensajes
function renderMessages() {
  const chat = getCurrentChat();
  const cont = document.getElementById("messages");
  const welcome = document.getElementById("welcome");

  cont.innerHTML = "";

  if (!chat || chat.messages.length === 0) {
    welcome.style.display = "block";
    return;
  }

  welcome.style.display = "none";

  chat.messages.forEach((msg) => {
    const row = document.createElement("div");
    row.className = "message-row " + (msg.role === "user" ? "user" : "ai");

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = msg.role === "user" ? "Tú" : "XA";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = msg.content;

    row.appendChild(avatar);
    row.appendChild(bubble);
    cont.appendChild(row);
  });

  cont.scrollTop = cont.scrollHeight;
}

// Añadir mensaje al chat actual
function addMessage(role, content) {
  ensureChat();
  const chat = getCurrentChat();
  chat.messages.push({ role, content, id: createId(), createdAt: new Date().toISOString() });

  // Actualizar título del chat con el primer mensaje del usuario
  if (role === "user" && chat.messages.length === 1) {
    chat.title = content.slice(0, 40) + (content.length > 40 ? "..." : "");
  }

  renderChatList();
  renderMessages();
}

// Modo (chat / file)
function setMode(mode) {
  currentMode = mode;
  document.getElementById("mode-chat").classList.toggle("active", mode === "chat");
  document.getElementById("mode-file").classList.toggle("active", mode === "file");
}

// Adjuntos
function renderAttached() {
  const cont = document.getElementById("attached-files");
  cont.innerHTML = "";

  const all = [
    ...attachedFiles.map((f) => ({ type: "file", name: f.name })),
    ...attachedImages.map((f) => ({ type: "img", name: f.name })),
  ];

  all.forEach((item) => {
    const pill = document.createElement("div");
    pill.className = "file-pill";
    pill.textContent = (item.type === "img" ? "🖼 " : "📎 ") + item.name;
    cont.appendChild(pill);
  });
}

// Enviar mensaje
async function sendMessage() {
  const promptEl = document.getElementById("prompt");
  const langEl = document.getElementById("language");
  const prompt = promptEl.value.trim();
  const language = langEl.value.trim();

  if (!prompt) return;

  addMessage("user", prompt);
  promptEl.value = "";
  autoResizeTextarea();

  // Nota: de momento no enviamos archivos al backend, solo los mostramos en UI.
  try {
    const res = await fetch(BACKEND, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        mode: currentMode,
        language: language || null,
      }),
    });

    const data = await res.json();
    const content = data.content || "Sin respuesta de Xtreme AI.";
    addMessage("ai", content);

    if (data.type === "file" && data.file_url) {
      addMessage("ai", "Archivo generado: " + data.file_url);
    }
  } catch (err) {
    addMessage("ai", "Error al conectar con Xtreme AI.");
  }
}

// Auto-resize textarea
function autoResizeTextarea() {
  const ta = document.getElementById("prompt");
  ta.style.height = "auto";
  ta.style.height = ta.scrollHeight + "px";
}

// Nuevo chat
function newChat() {
  const id = createId();
  const chat = {
    id,
    title: "Nuevo chat",
    messages: [],
    createdAt: new Date().toISOString(),
  };
  chats.unshift(chat);
  currentChatId = id;
  renderChatList();
  renderMessages();
}

// Sidebar / menú
function openSidebar() {
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("overlay");
  sidebar.classList.add("open");
  overlay.classList.add("visible");
}

function closeSidebar() {
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("overlay");
  sidebar.classList.remove("open");
  overlay.classList.remove("visible");
}

// Sidepanel (perfil / ajustes / about)
function openSidepanel(title, contentHtml) {
  const panel = document.getElementById("sidepanel");
  document.getElementById("sidepanel-title").textContent = title;
  document.getElementById("sidepanel-content").innerHTML = contentHtml;
  panel.classList.add("open");
}

function closeSidepanel() {
  const panel = document.getElementById("sidepanel");
  panel.classList.remove("open");
}

// Contenidos de panel
function showProfilePanel() {
  openSidepanel(
    "Perfil",
    `
    <div class="panel-section">
      <div class="panel-section-title">Usuario</div>
      <div class="panel-item">Nombre: Invitado</div>
      <div class="panel-item">Rol: Desarrollador</div>
    </div>
    <div class="panel-section">
      <div class="panel-section-title">Xtreme Cloud</div>
      <div class="panel-item">Integración futura con tu hosting XtremeCloud.</div>
    </div>
  `
  );
}

function showSettingsPanel() {
  openSidepanel(
    "Ajustes",
    `
    <div class="panel-section">
      <div class="panel-section-title">Preferencias</div>
      <div class="panel-item">Tema: Oscuro (por defecto)</div>
      <div class="panel-item">Idioma: Español</div>
      <div class="panel-item">Modo por defecto: Chat</div>
    </div>
    <div class="panel-section">
      <div class="panel-section-title">Próximamente</div>
      <div class="panel-item">Historial persistente, login con Google, perfiles avanzados...</div>
    </div>
  `
  );
}

function showAboutPanel() {
  openSidepanel(
    "Acerca de Xtreme AI",
    `
    <div class="panel-section">
      <div class="panel-section-title">Descripción</div>
      <div class="panel-item">
        Xtreme AI es un asistente especializado en código, diseñado para integrarse con tu hosting XtremeCloud.
      </div>
    </div>
    <div class="panel-section">
      <div class="panel-section-title">Tecnología</div>
      <div class="panel-item">Backend: FastAPI + Groq (Llama 3).</div>
      <div class="panel-item">Frontend: HTML, CSS, JS puro, estilo tipo OpenAI.</div>
    </div>
  `
  );
}

// Adjuntar archivos
function handleAttachFile() {
  document.getElementById("file-input").click();
}

function handleAttachImage() {
  document.getElementById("image-input").click();
}

function onFilesSelected(e, type) {
  const files = Array.from(e.target.files || []);
  if (type === "file") {
    attachedFiles = attachedFiles.concat(files);
  } else {
    attachedImages = attachedImages.concat(files);
  }
  renderAttached();
}

// Tema (placeholder)
function toggleTheme() {
  // Aquí podrías alternar clases para tema claro/oscuro en el futuro.
  // De momento solo mostramos un mensaje en consola.
  console.log("Tema alternado (placeholder).");
}

// Inicialización
function init() {
  // Botones de modo
  document.getElementById("mode-chat").addEventListener("click", () => setMode("chat"));
  document.getElementById("mode-file").addEventListener("click", () => setMode("file"));

  // Enviar
  document.getElementById("send-button").addEventListener("click", sendMessage);

  const ta = document.getElementById("prompt");
  ta.addEventListener("input", autoResizeTextarea);
  ta.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Nuevo chat
  document.getElementById("new-chat-btn").addEventListener("click", () => {
    newChat();
    closeSidebar();
  });

  // Sidebar
  document.getElementById("menu-toggle").addEventListener("click", openSidebar);
  document.getElementById("sidebar-close").addEventListener("click", closeSidebar);
  document.getElementById("overlay").addEventListener("click", closeSidebar);

  // Sidepanel
  document.getElementById("avatar-button").addEventListener("click", showProfilePanel);
  document.getElementById("profile-btn").addEventListener("click", () => {
    showProfilePanel();
    closeSidebar();
  });
  document.getElementById("settings-btn").addEventListener("click", () => {
    showSettingsPanel();
    closeSidebar();
  });
  document.getElementById("about-btn").addEventListener("click", () => {
    showAboutPanel();
    closeSidebar();
  });
  document.getElementById("sidepanel-close").addEventListener("click", closeSidepanel);

  // Adjuntos
  document.getElementById("attach-file-btn").addEventListener("click", handleAttachFile);
  document.getElementById("attach-image-btn").addEventListener("click", handleAttachImage);
  document.getElementById("file-input").addEventListener("change", (e) =>
    onFilesSelected(e, "file")
  );
  document.getElementById("image-input").addEventListener("change", (e) =>
    onFilesSelected(e, "img")
  );

  // Tema
  document.getElementById("theme-toggle").addEventListener("click", toggleTheme);

  // Estado inicial
  setMode("chat");
  renderChatList();
  renderMessages();
}

document.addEventListener("DOMContentLoaded", init); 
