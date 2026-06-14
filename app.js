const BACKEND = "https://TU_DOMINIO/generate";

function agregarMensaje(texto) {
  const div = document.createElement("div");
  div.className = "mensaje";
  div.textContent = texto;
  document.getElementById("mensajes").appendChild(div);
}

async function enviar() {
  const prompt = document.getElementById("prompt").value;
  const mode = document.getElementById("mode").value;
  const language = document.getElementById("language").value;

  agregarMensaje("Tú: " + prompt);

  const res = await fetch(BACKEND, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ prompt, mode, language })
  });

  const data = await res.json();

  agregarMensaje("Xtreme AI: " + data.content);

  if (data.type === "file") {
    agregarMensaje("Archivo listo: " + data.file_url);
  }
}
