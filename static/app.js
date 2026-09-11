const chatWindow = document.getElementById("chatWindow");
const chatForm = document.getElementById("chatForm");
const questionInput = document.getElementById("questionInput");
const uploadBtn = document.getElementById("uploadBtn");
const pdfInput = document.getElementById("pdfInput");
const uploadStatus = document.getElementById("uploadStatus");

function addBubble(text, sender, sources) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${sender}`;
  bubble.textContent = text;

  if (sources && sources.length) {
    const src = document.createElement("div");
    src.className = "sources";
    src.textContent = "Sources: " + sources.map(s => `${s.file} (p.${s.page})`).join(", ");
    bubble.appendChild(src);
  }

  chatWindow.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  addBubble(question, "user");
  questionInput.value = "";

  const thinking = document.createElement("div");
  thinking.className = "bubble bot";
  thinking.textContent = "Thinking...";
  chatWindow.appendChild(thinking);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    thinking.remove();

    if (!res.ok) {
      addBubble(`Error: ${data.error}`, "bot");
    } else {
      addBubble(data.answer, "bot", data.sources);
    }
  } catch (err) {
    thinking.remove();
    addBubble(`Network error: ${err.message}`, "bot");
  }
});

uploadBtn.addEventListener("click", async () => {
  if (!pdfInput.files.length) {
    uploadStatus.textContent = "Choose a PDF first.";
    return;
  }

  const formData = new FormData();
  formData.append("file", pdfInput.files[0]);

  uploadStatus.textContent = "Ingesting...";
  try {
    const res = await fetch("/api/upload", { method: "POST", body: formData });
    const data = await res.json();
    uploadStatus.textContent = res.ok ? data.message : `Error: ${data.error}`;
  } catch (err) {
    uploadStatus.textContent = `Network error: ${err.message}`;
  }
});
