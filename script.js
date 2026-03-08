// ---------------------------------------------------------
// ELEMENTOS DEL CHAT
// ---------------------------------------------------------
const chat = document.getElementById("chat");
const input = document.getElementById("mensaje");
const btnEnviar = document.getElementById("btn-enviar");
const btnStop = document.getElementById("btn-stop");
const typing = document.getElementById("typing");

// ---------------------------------------------------------
// ARCHIVOS (ACTIVADOS)
// ---------------------------------------------------------
const btnFile = document.getElementById("btn-file");
const fileInput = document.getElementById("file-input");
const attachedFilesDiv = document.getElementById("attached-files");

let archivosAdjuntos = [];

btnFile.onclick = () => fileInput.click();

fileInput.onchange = () => {
    archivosAdjuntos = [...fileInput.files];
    attachedFilesDiv.innerHTML = "";

    archivosAdjuntos.forEach((file, index) => {
        const url = URL.createObjectURL(file);

        const mini = document.createElement("div");
        mini.classList.add("miniatura");

        mini.innerHTML = `
            <img src="${url}" class="mini-img">
            <span class="mini-close" data-i="${index}">✖</span>
        `;

        attachedFilesDiv.appendChild(mini);
    });

    // Eliminar miniatura
    attachedFilesDiv.onclick = e => {
        if (e.target.classList.contains("mini-close")) {
            const i = e.target.dataset.i;
            archivosAdjuntos.splice(i, 1);
            fileInput.value = "";
            fileInput.onchange();
        }
    };
};

// ---------------------------------------------------------
// PREVIEW
// ---------------------------------------------------------
const previewPanel = document.getElementById("preview-panel");
const previewFrame = document.getElementById("preview-frame");
const btnPC = document.getElementById("preview-pc");
const btnMobile = document.getElementById("preview-mobile");
const btnRefresh = document.getElementById("preview-refresh");
const btnFullscreen = document.getElementById("preview-fullscreen");
const btnClose = document.getElementById("preview-close");

let lastHTML = "";
let lastCSS = "";
let lastJS = "";

let controller = null;

// ---------------------------------------------------------
// FUNCIÓN PARA AGREGAR MENSAJES
// ---------------------------------------------------------
function agregarMensaje(tipo, contenido) {
    const div = document.createElement("div");
    div.classList.add("message", tipo);

    const avatar = document.createElement("img");
    avatar.classList.add("avatar");
    avatar.src = tipo === "usuario"
        ? "https://i.imgur.com/0y0y0y0.png"
        : "https://i.imgur.com/1X1X1X1.png";

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");

    // Si la IA generó una web completa
    if (tipo === "ia" && contenido.includes("<html")) {
        procesarWebGenerada(contenido);

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

    // Múltiples bloques de código
    if (contenido.includes("```")) {
        const partes = contenido.split("```");

        partes.forEach((parte, i) => {
            if (i % 2 === 0) {
                if (parte.trim() !== "") {
                    const p = document.createElement("div");
                    p.textContent = parte;
                    bubble.appendChild(p);
                }
            } else {
                const code = document.createElement("pre");
                code.classList.add("code-block");
                code.textContent = parte;

                const copyBtn = document.createElement("button");
                copyBtn.textContent = "Copiar";
                copyBtn.classList.add("copy-btn");
                copyBtn.onclick = () => navigator.clipboard.writeText(parte);

                code.appendChild(copyBtn);
                bubble.appendChild(code);
            }
        });
    } else {
        bubble.textContent = contenido;
    }

    div.appendChild(avatar);
    div.appendChild(bubble);

    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

// ---------------------------------------------------------
// ENVÍO DE MENSAJES (MULTIMODAL)
// ---------------------------------------------------------
async function enviar() {
    const texto = input.value.trim();
    const hayImagenes = archivosAdjuntos.length > 0;

    if (!texto && !hayImagenes) return;

    agregarMensaje("usuario", texto || "[Imagen]");

    typing.classList.remove("hidden");
    btnStop.classList.remove("hidden");

    controller = new AbortController();

    input.value = "";

    try {
        let res;

        if (hayImagenes) {
            // Enviar como multipart/form-data
            const form = new FormData();
            form.append("mensaje", texto);

            archivosAdjuntos.forEach(img => form.append("imagenes", img));

            res = await fetch("https://code-ia-3uq5.onrender.com/api/chat", {
                method: "POST",
                body: form,
                signal: controller.signal
            });

        } else {
            // Enviar solo texto
            res = await fetch("https://code-ia-3uq5.onrender.com/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mensaje: texto }),
                signal: controller.signal
            });
        }

        const respuestaTexto = await res.text();

        typing.classList.add("hidden");
        btnStop.classList.add("hidden");

        agregarMensaje("ia", respuestaTexto);

        archivosAdjuntos = [];
        attachedFilesDiv.innerHTML = "";
        fileInput.value = "";

    } catch (e) {
        typing.classList.add("hidden");
        btnStop.classList.add("hidden");
        agregarMensaje("ia", "⚠️ Respuesta detenida o error de conexión.");
    }
}

btnEnviar.onclick = enviar;
btnStop.onclick = () => controller?.abort();

// ---------------------------------------------------------
// ENTER = SALTO DE LÍNEA
// CTRL + ENTER = ENVIAR
// ---------------------------------------------------------
input.addEventListener("keydown", e => {
    if (e.key === "Enter") {
        if (e.ctrlKey) {
            enviar();
        } else {
            e.preventDefault();
            input.value += "\n";
        }
    }
});

// ---------------------------------------------------------
// PREVIEW
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
