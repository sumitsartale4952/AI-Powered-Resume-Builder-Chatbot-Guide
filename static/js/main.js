document.addEventListener("DOMContentLoaded", () => {
  // DOM elements
  const chatMessages = document.getElementById("chatMessages");
  const userInput = document.getElementById("userInput");
  const sendButton = document.getElementById("sendButton");
  const optionsContainer = document.getElementById("optionsContainer");
  const progressBar = document.getElementById("progressBar");

  // State management
  let sessionId = localStorage.getItem("sessionId") || Date.now().toString();
  let userData = JSON.parse(localStorage.getItem("userData")) || {};
  let isTyping = false;

  // Store session ID
  localStorage.setItem("sessionId", sessionId);

  async function sendMessage(message) {
    if (!message.trim() || isTyping) return;

    try {
      // Show user message
      appendMessage(message, "user");
      userInput.value = "";
      isTyping = true;

      // Show typing indicator
      showTypingIndicator();

      // Send to backend
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-ID": sessionId,
        },
        body: JSON.stringify({
          message,
          session_id: sessionId,
          user_data: userData,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Update state
      if (data.user_data) {
        userData = { ...userData, ...data.user_data };
        localStorage.setItem("userData", JSON.stringify(userData));
      }

      // Update progress if provided
      if (data.progress) {
        updateProgress(data.progress);
      }

      // Remove typing indicator and show response
      hideTypingIndicator();
      appendMessage(data.response, "bot", data.options);

      // Handle completion
      if (data.completed) {
        handleCompletion(data);
      }
    } catch (error) {
      console.error("Chat error:", error);
      hideTypingIndicator();
      appendMessage("Sorry, something went wrong. Please try again.", "bot");
    } finally {
      isTyping = false;
    }
  }

  function appendMessage(text, sender, options = []) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}-message`;

    // Sanitize HTML content
    const sanitizedText = DOMPurify.sanitize(text);
    messageDiv.innerHTML = marked(sanitizedText); // Convert markdown to HTML

    chatMessages.appendChild(messageDiv);
    messageDiv.scrollIntoView({ behavior: "smooth" });

    if (options.length > 0) {
      showOptions(options);
    }
  }

  function showOptions(options) {
    optionsContainer.innerHTML = "";

    options.forEach((opt) => {
      const button = document.createElement("button");
      button.className = "option-btn";
      button.textContent = opt;
      button.addEventListener("click", () => {
        sendMessage(opt);
        optionsContainer.innerHTML = "";
      });
      optionsContainer.appendChild(button);
    });
  }

  function updateProgress(progress) {
    if (progressBar) {
      progressBar.style.width = `${progress}%`;
      progressBar.setAttribute("aria-valuenow", progress);
    }
  }

  function showTypingIndicator() {
    const typingDiv = document.createElement("div");
    typingDiv.className = "typing-indicator";
    typingDiv.innerHTML = "<span></span><span></span><span></span>";
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function hideTypingIndicator() {
    const typingIndicator = chatMessages.querySelector(".typing-indicator");
    if (typingIndicator) {
      typingIndicator.remove();
    }
  }

  function handleCompletion(data) {
    if (data.resume_url) {
      const downloadDiv = document.createElement("div");
      downloadDiv.className = "download-section";
      downloadDiv.innerHTML = `
              <a href="${data.resume_url}" class="download-btn" download>
                  Download Resume
                  <svg viewBox="0 0 24 24">
                      <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/>
                  </svg>
              </a>
          `;
      chatMessages.appendChild(downloadDiv);
    }
  }

  // Event Listeners
  sendButton.addEventListener("click", () => {
    const message = userInput.value.trim();
    if (message) {
      sendMessage(message);
    }
  });

  userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendButton.click();
    }
  });

  // Handle file uploads
  const fileInput = document.getElementById("fileInput");
  if (fileInput) {
    fileInput.addEventListener("change", async (e) => {
      const file = e.target.files[0];
      if (file) {
        const formData = new FormData();
        formData.append("photo", file);

        try {
          const response = await fetch("/upload-photo", {
            method: "POST",
            headers: {
              "X-Session-ID": sessionId,
            },
            body: formData,
          });

          const data = await response.json();
          if (data.photo_url) {
            userData.photo_url = data.photo_url;
            localStorage.setItem("userData", JSON.stringify(userData));
            appendMessage("Photo uploaded successfully!", "bot");
          }
        } catch (error) {
          console.error("Upload error:", error);
          appendMessage("Failed to upload photo. Please try again.", "bot");
        }
      }
    });
  }

  // Initialize conversation
  sendMessage("Hi");
});
