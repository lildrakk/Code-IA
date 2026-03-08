// ---------------------------------------------------------
// ELEMENTOS DEL CHAT
// ---------------------------------------------------------
const chat = document.getElementById("chat");
const input = document.getElementById("mensaje");
const btnEnviar = document.getElementById("btn-enviar");
const btnStop = document.getElementById("btn-stop");
const typing = document.getElementById("typing");

// ---------------------------------------------------------
// ELEMENTOS DE ARCHIVOS
// ---------------------------------------------------------
const btnFile = document.getElementById("btn-file");
const fileInput = document.getElementById("file-input");
const attachedFilesDiv = document.getElementById("attached-files");

let archivosAdjuntos = [];

// ---------------------------------------------------------
// ELEMENTOS DEL PANEL DE PREVIEW
// ---------------------------------------------------------
const previewPanel = document.getElementById("preview-panel");
const previewFrame = document.getElementById("preview-frame");
const btnPC = document.getElementById("preview-pc");
const btnMobile = document.getElementById("preview-mobile");
const btnRefresh = document.getElementById("preview-refresh");
const btnFullscreen = document.getElementById("preview-fullscreen");
const btnClose = document.getElementById("preview-close");

// ARCHIVOS GENERADOS POR LA IA
let lastHTML = "";
let lastCSS = "";
let lastJS = "";

let controller = null;

// ---------------------------------------------------------
// SISTEMA DE MENSAJES
// ---------------------------------------------------------

function agregarMensaje(tipo, texto) {
    const div = document.createElement("div");
    div.classList.add("message", tipo);

    const avatar = document.createElement("img");
    avatar.classList.add("avatar");
    avatar.src = tipo === "usuario"
        ? "https://i.imgur.com/0y0y0y0.png"
        : "https://i.imgur.com/1X1X1X1.png";

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");

    // Detectar si la IA devolvió una web completa
    if (tipo === "ia" && texto.includes("<html")) {
        procesarWebGenerada(texto);

        bubble.innerHTML = `
            <div class="preview-card">
                <strong>📄 Página web generada</strong><br>
                Haz clic en PREVIEW para verla.
                <br><br>
                <button class="preview-btn">PREVIEW</button>
            </div>
        `;

        setTimeout(() => {
            const btn = bubble.querySelector(".preview-btn");
            if (btn) btn.onclick = () => abrirPreview(bubble);
        }, 50);

        div.appendChild(avatar);
        div.appendChild(bubble);
        chat.appendChild(div);
        chat.scrollTop = chat.scrollHeight;
        return;
    }

    // Detectar bloques de código
    else if (texto.includes("```")) {
        const partes = texto.split("```");

        bubble.innerHTML = partes[0];

        const code = document.createElement("pre");
        code.classList.add("code-block");
        code.textContent = partes[1];

        const copyBtn = document.createElement("button");
        copyBtn.textContent = "Copiar";
        copyBtn.classList.add("copy-btn");
        copyBtn.onclick = () => navigator.clipboard.writeText(partes[1]);

        code.appendChild(copyBtn);
        bubble.appendChild(code);
    }

    else {
        bubble.textContent = texto;
    }

    div.appendChild(avatar);
    div.appendChild(bubble);

    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

// ---------------------------------------------------------
// SISTEMA DE ARCHIVOS ADJUNTOS
// ---------------------------------------------------------

btnFile.onclick = () => fileInput.click();

fileInput.onchange = () => {
    archivosAdjuntos = Array.from(fileInput.files);
    mostrarArchivosAdjuntos();
};

function mostrarArchivosAdjuntos() {
    attachedFilesDiv.innerHTML = "";

    archivosAdjuntos.forEach(file => {
        const tag = document.createElement("div");
        tag.classList.add("file-tag");
        tag.textContent = "📎 " + file.name;
        attachedFilesDiv.appendChild(tag);
    });
}

// ---------------------------------------------------------
// ENVÍO DE MENSAJES + ARCHIVOS
// ---------------------------------------------------------

async function enviar() {
    const texto = input.value.trim();
    if (!texto && archivosAdjuntos.length === 0) return;

    agregarMensaje("usuario", texto || "📎 Archivo enviado");

    typing.classList.remove("hidden");
    btnStop.classList.remove("hidden");

    controller = new AbortController();

    const formData = new FormData();
    formData.append("mensaje", texto);

    archivosAdjuntos.forEach(file => {
        formData.append("archivos", file);
    });

    input.value = "";
    archivosAdjuntos = [];
    attachedFilesDiv.innerHTML = "";

    try {
        const res = await fetch("https://code-ia-3uq5.onrender.com/api/chat", {
            method: "POST",
            body: formData,
            signal: controller.signal
        });

        const data = await res.json();

        typing.classList.add("hidden");
        btnStop.classList.add("hidden");

        agregarMensaje("ia", data.respuesta);

    } catch (e) {
        typing.classList.add("hidden");
        btnStop.classList.add("hidden");
        agregarMensaje("ia", "⚠️ Respuesta detenida o error de conexión.");
    }
}

btnEnviar.onclick = enviar;
btnStop.onclick = () => controller?.abort();
input.addEventListener("keypress", e => {
    if (e.key === "Enter") enviar();
});

// ---------------------------------------------------------
// SISTEMA DE PREVIEW LOCAL PROFESIONAL
// ---------------------------------------------------------

function procesarWebGenerada(texto) {
    lastHTML = extraerBloque(texto, "html");
    lastCSS = extraerBloque(texto, "css");
    lastJS = extraerBloque(texto, "javascript");
}

function extraerBloque(texto, tipo) {
    const regex = new RegExp("```" + tipo + "[\\s\\S]*?```", "g");
    const match = texto.match(regex);

    if (!match) return "";

    return match[0]
        .replace("```" + tipo, "")
        .replace("```", "")
        .trim();
}

function abrirPreview(bubble) {
    previewPanel.classList.remove("hidden");

    // Posicionar debajo del mensaje
    const rect = bubble.getBoundingClientRect();
    previewPanel.style.top = rect.bottom + 10 + "px";
    previewPanel.style.left = rect.left + "px";

    actualizarPreview();
}

function actualizarPreview() {
    const doc = previewFrame.contentDocument;

    doc.open();
    doc.write(`
        <html>
        <head>
            <style>${lastCSS}</style>
        </head>
        <body>
            ${lastHTML}
            <script>${lastJS}</script>
        </body>
        </html>
    `);
    doc.close();
}

// ---------------------------------------------------------
// BOTONES DEL PANEL DE PREVIEW
// ---------------------------------------------------------

btnPC.onclick = () => {
    previewFrame.style.width = "100%";
    previewFrame.style.height = "500px";
};

btnMobile.onclick = () => {
    previewFrame.style.width = "375px";
    previewFrame.style.height = "667px";
};

btnRefresh.onclick = actualizarPreview;

btnFullscreen.onclick = () => {
    previewPanel.requestFullscreen();
};

btnClose.onclick = () => {
    previewPanel.classList.add("hidden");
};
