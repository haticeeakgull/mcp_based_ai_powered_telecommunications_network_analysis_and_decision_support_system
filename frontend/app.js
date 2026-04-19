const API_BASE = "http://127.0.0.1:8000";

const chatBox = document.getElementById("chatBox");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const limitInput = document.getElementById("limitInput");

function addMessage(text, type) {
  const div = document.createElement("div");
  div.className = `msg ${type}`;
  div.textContent = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = messageInput.value.trim();
  const limit = Number(limitInput.value || 20);
  if (!message) return;

  addMessage(`Sen: ${message}`, "user");
  messageInput.value = "";

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, limit }),
    });

    const data = await res.json();
    if (!res.ok) {
      addMessage(`Hata: ${data.detail || "Bilinmeyen hata"}`, "bot");
      return;
    }

    addMessage(`Asistan: ${data.answer}`, "bot");
    addMessage(JSON.stringify(data.data, null, 2), "bot");
  } catch (err) {
    addMessage(`Baglanti hatasi: ${err.message}`, "bot");
  }
});
