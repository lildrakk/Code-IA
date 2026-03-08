const chat = document.getElementById("chat");
const input = document.getElementById("mensaje");
const btnEnviar = document.getElementById("btn-enviar");
const btnStop = document.getElementById("btn-stop");
const typing = document.getElementById("typing");

let controller = null;

function agregarMensaje(tipo, texto) {
    const div = document.createElement("div");
    div.classList.add("message", tipo);

    const avatar = document.createElement("img");
    avatar.classList.add("avatar");
    avatar.src = tipo === "usuario" ? "https://i.imgur.com/0y0y0y0.png" : "https://i.imgur.com/1X1X1X1.png";

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");

    if (texto.includes("```")) {
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
    } else {
        bubble.textContent = texto;
    }

    div.appendChild(avatar);
    div.appendChild(bubble);

    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

async function enviar() {
    const texto = input.value.trim();
    if (!texto) return;

    agregarMensaje("usuario", texto);
    input.value = "";

    typing.classList.remove("hidden");
    btnStop.classList.remove("hidden");

    controller = new AbortController();

    try {
        const res = await fetch("https://code-ia-3uq5.onrender.com/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mensaje: texto }),
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
