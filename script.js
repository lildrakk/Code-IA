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

let controller = null;

// ---------------------------------------------------------
// FUNCIÓN PARA AGREGAR MENSAJES (SIN PREVIEW WEB)
// ---------------------------------------------------------
function agregarMensaje(tipo, contenido) {
    const div = document.createElement("div");
    div.classList.add("message", tipo);

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");

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
            const form = new FormData();
            form.append("mensaje", texto);

            archivosAdjuntos.forEach(img => form.append("imagenes", img));

            res = await fetch("https://code-ia-3uq5.onrender.com/api/chat", {
                method: "POST",
                body: form,
                signal: controller.signal
            });

        } else {
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
