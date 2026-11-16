// chat.js

import { $, escapeHtml } from './dom.js';
import { getInactiveIds } from './state.js';
import { renderSearchResultsBlock } from './render.js';

/**
 * Get the user ID from local storage or create a new one.
 * @returns {string} userId
 */
function getUserId() {
  let userId = localStorage.getItem("user_id");
  if (!userId) {
    userId = "guest-" + Math.random().toString(36).substring(2, 10);
    localStorage.setItem("user_id", userId);
  }
  return userId;
}

/**
 * Render markdown if marked is available, otherwise show escaped text.
 * @param {string} text
 * @returns {string}
 */
function renderMarkdown(text) {
  if (window.marked && typeof window.marked.parse === "function") {
    return window.marked.parse(text);
  }
  return `<pre>${escapeHtml(text)}</pre>`;
}


/**
 * Initialize the chat functionality.
 * Sets up event listeners for the chat form, input, and buttons.
 */
export function initChat() {
  const chatForm = $("chat-form");
  const chatInput = $("user-input");
  const chatBox = $("chat-box");
  const docLimitInput = $("top-k-select");
  const submitButton = $("submit-button");
  const clearButton = $("clear-history");
  const resetLLMButton = $("reset-llm");

  if (!chatForm || !chatInput || !chatBox || !submitButton) return;

  const userId = getUserId();

  function setBusy(busy) {
    chatInput.disabled = busy;
    submitButton.disabled = busy;
    if (resetLLMButton) resetLLMButton.disabled = busy;
    if (clearButton) clearButton.disabled = busy;
    submitButton.textContent = busy ? "Loading..." : "Send";
  }

  // These used to be registered inside the submit handler, which stacked a
  // new copy of each listener every time a message was sent.
  clearButton?.addEventListener("click", function () {
    chatBox.innerHTML = "";
    chatInput.focus();
  });

  resetLLMButton?.addEventListener("click", async function () {
    setBusy(true);
    chatBox.innerHTML = `<div><strong>Assistant:</strong> Memory cleared. How can I help?</div>`;

    const searchResults = $("search-results");
    if (searchResults) {
      searchResults.innerHTML = "";
    }

    try {
      await fetch(`/debug/memory?user_id=${encodeURIComponent(userId)}`, {
        method: "DELETE"
      });
    } catch (err) {
      console.error("Failed to reset LLM memory:", err);
      chatBox.innerHTML += `<em>Error resetting memory: ${escapeHtml(err.message)}</em>`;
    }

    setBusy(false);
    chatInput.focus();
  });

  chatForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const msg = chatInput.value.trim();
    if (!msg) return;

    setBusy(true);
    chatInput.value = '';

    chatBox.insertAdjacentHTML("beforeend", `<br><div><strong>You:</strong> ${escapeHtml(msg)}</div>`);
    const botMsg = document.createElement("div");
    chatBox.appendChild(botMsg);
    chatBox.scrollTop = chatBox.scrollHeight;

    const inactive = JSON.stringify(getInactiveIds());

    // === Show the retrieved context in the search panel ===
    try {
      const searchLimit = docLimitInput?.value || 5;
      const contextResponse = await fetch(`/search?q=${encodeURIComponent(msg)}&top_k=${searchLimit}`);
      const contextData = await contextResponse.json();

      if (contextData?.results?.length) {
        const searchResults = $("search-results");
        searchResults.innerHTML = `
          <h3>RAG Context Used:</h3>
          ${renderSearchResultsBlock(contextData.results)}
        `;
      }
    } catch (err) {
      console.error("Context search failed", err);
    }

    const persona = $("persona-text")?.value || "";

    try {
      const response = await fetch("/chat-stream", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          message: msg,
          persona,
          user_id: userId,
          inactive
        })
      });

      if (!response.ok || !response.body) {
        botMsg.innerHTML = `<strong>Assistant:</strong> <em>Server error (${response.status}).</em>`;
      } else if ((response.headers.get("content-type") || "").includes("application/json")) {
        // The server reports setup errors (e.g. no documents/model) as JSON
        const data = await response.json();
        botMsg.innerHTML = `<strong>Assistant:</strong> <em>${escapeHtml(data.response || "Unknown error")}</em>`;
      } else {
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          botMsg.innerHTML = `<br>${renderMarkdown(buffer)}`;
          chatBox.scrollTop = chatBox.scrollHeight;
        }
      }
    } catch (err) {
      botMsg.innerHTML = `<strong>Assistant:</strong> <em>Error: ${escapeHtml(err.message || String(err))}</em>`;
    }

    setBusy(false);
    chatInput.focus();
  });
}
