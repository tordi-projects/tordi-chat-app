(function () {
  const conversationId = window.TORDI_CONVERSATION_ID;
  const myUserId = window.TORDI_USER_ID;
  const uploadUrl = window.TORDI_UPLOAD_URL;
  const pollUrl = window.TORDI_POLL_URL;
  const sendUrl = window.TORDI_SEND_URL;
  const typingUrl = window.TORDI_TYPING_URL;
  if (!conversationId) return;

  const messageList = document.getElementById('message-list');
  const form = document.getElementById('message-form');
  const input = document.getElementById('message-input');
  const typingIndicator = document.getElementById('typing-indicator');
  const peerStatus = document.getElementById('peer-status');
  const emojiBtn = document.getElementById('emoji-btn');
  const emojiPanel = document.getElementById('emoji-panel');
  const attachBtn = document.getElementById('attach-btn');
  const attachmentInput = document.getElementById('attachment-input');
  const sendBtn = document.getElementById('send-btn');

  let lastMessageId = parseInt(window.TORDI_LAST_MESSAGE_ID || '0', 10) || 0;

  function csrfToken() {
    return form.querySelector('[name=csrfmiddlewaretoken]').value;
  }

  function showTransientNotice(text) {
    typingIndicator.textContent = text;
    setTimeout(() => {
      if (typingIndicator.textContent === text) typingIndicator.textContent = '';
    }, 3000);
  }

  // ---------- Rendering ----------
  function appendMessage(data) {
    const emptyState = messageList.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    const row = document.createElement('div');
    const mine = String(data.sender_id) === String(myUserId);
    row.className = `bubble-row ${mine ? 'mine' : 'theirs'}`;

    const bubble = document.createElement('div');
    bubble.className = 'bubble' + (data.attachment_url && !data.text ? ' media-only' : '');

    if (data.attachment_url) {
      const mediaWrap = document.createElement('div');
      mediaWrap.className = 'bubble-media';
      if (data.attachment_kind === 'image') {
        const img = document.createElement('img');
        img.src = data.attachment_url;
        mediaWrap.appendChild(img);
      } else if (data.attachment_kind === 'video') {
        const video = document.createElement('video');
        video.src = data.attachment_url;
        video.controls = true;
        mediaWrap.appendChild(video);
      } else {
        const link = document.createElement('a');
        link.href = data.attachment_url;
        link.target = '_blank';
        link.textContent = 'Download attachment';
        mediaWrap.appendChild(link);
      }
      bubble.appendChild(mediaWrap);
    }

    if (data.text) {
      const text = document.createElement('span');
      text.className = 'bubble-text';
      text.textContent = data.text;
      bubble.appendChild(text);
    }

    const time = document.createElement('span');
    time.className = 'bubble-time';
    time.textContent = data.timestamp;
    bubble.appendChild(time);

    row.appendChild(bubble);
    messageList.appendChild(row);
    messageList.scrollTop = messageList.scrollHeight;

    if (data.id > lastMessageId) lastMessageId = data.id;
  }

  // ---------- Polling loop ----------
  let pollInFlight = false;
  let typingDisplayTimeout = null;

  async function poll() {
    if (pollInFlight) return;
    pollInFlight = true;
    try {
      const res = await fetch(`${pollUrl}?after=${lastMessageId}`, { credentials: 'same-origin' });
      if (!res.ok) return;
      const data = await res.json();

      (data.messages || []).forEach(appendMessage);

      if (data.other_typing) {
        clearTimeout(typingDisplayTimeout);
        typingIndicator.textContent = 'typing...';
        typingDisplayTimeout = setTimeout(() => { typingIndicator.textContent = ''; }, 2500);
      }

      if (peerStatus && data.other_status) {
        peerStatus.textContent = data.other_status;
      }
    } catch (err) {
      // Silent — next poll cycle will retry. Avoid spamming the UI over a
      // single dropped request (e.g. brief network blip).
    } finally {
      pollInFlight = false;
    }
  }

  poll();
  setInterval(poll, 2500);

  // ---------- Sending text ----------
  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    closeEmojiPanel();

    try {
      const res = await fetch(sendUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken() },
        body: new URLSearchParams({ text }),
      });
      const data = await res.json();
      if (data.error) {
        showTransientNotice(data.error);
        return;
      }
      appendMessage(data.message);
    } catch (err) {
      showTransientNotice('Message failed to send. Please try again.');
    }
  });

  let lastTypingSent = 0;
  input.addEventListener('input', function () {
    const now = Date.now();
    if (now - lastTypingSent > 1500) {
      fetch(typingUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken() },
      }).catch(() => {});
      lastTypingSent = now;
    }
  });

  // ---------- Attachments ----------
  attachBtn.addEventListener('click', function () {
    attachmentInput.click();
  });

  attachmentInput.addEventListener('change', function () {
    const file = attachmentInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('attachment', file);
    formData.append('caption', input.value.trim());

    sendBtn.disabled = true;
    attachBtn.disabled = true;

    fetch(uploadUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken() },
      body: formData,
    })
      .then((res) => res.json())
      .then((res) => {
        if (res.error) {
          showTransientNotice(res.error);
        } else {
          input.value = '';
          appendMessage(res.message);
        }
      })
      .catch(() => {
        showTransientNotice('Upload failed. Please try again.');
      })
      .finally(() => {
        sendBtn.disabled = false;
        attachBtn.disabled = false;
        attachmentInput.value = '';
      });
  });

  // ---------- Emoji picker ----------
  const EMOJIS = [
    '😀','😁','😂','🤣','😊','😍','😘','😜','🤔','😎',
    '😢','😭','😡','😴','🤗','🙌','👏','👍','👎','🙏',
    '💪','🔥','✨','🎉','❤️','💔','💯','😱','😇','🤩',
    '🥳','😅','😆','🙃','🤨','😐','😬','🤯','🥺','😤',
    '👋','🤝','✌️','🤞','👌','🤙','💃','🕺','🍕','☕',
    '🎂','🎁','⚽','🏆','🚗','✈️','🌍','☀️','🌙','⭐'
  ];

  EMOJIS.forEach((emoji) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = emoji;
    btn.addEventListener('click', () => {
      input.value += emoji;
      input.focus();
    });
    emojiPanel.appendChild(btn);
  });

  function closeEmojiPanel() { emojiPanel.classList.remove('open'); }

  emojiBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    emojiPanel.classList.toggle('open');
  });

  document.addEventListener('click', function (e) {
    if (!emojiPanel.contains(e.target) && e.target !== emojiBtn) {
      closeEmojiPanel();
    }
  });

  // Scroll to bottom on load
  messageList.scrollTop = messageList.scrollHeight;
})();
