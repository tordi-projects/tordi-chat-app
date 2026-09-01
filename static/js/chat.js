(function () {
  const conversationId = window.TORDI_CONVERSATION_ID;
  const myUserId = window.TORDI_USER_ID;
  const uploadUrl = window.TORDI_UPLOAD_URL;
  if (!conversationId) return;

  const messageList = document.getElementById('message-list');
  const form = document.getElementById('message-form');
  const input = document.getElementById('message-input');
  const typingIndicator = document.getElementById('typing-indicator');
  const emojiBtn = document.getElementById('emoji-btn');
  const emojiPanel = document.getElementById('emoji-panel');
  const attachBtn = document.getElementById('attach-btn');
  const attachmentInput = document.getElementById('attachment-input');
  const sendBtn = document.getElementById('send-btn');

  const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
  const socket = new WebSocket(`${protocol}${window.location.host}/ws/chat/${conversationId}/`);

  let typingTimeout = null;

  // ---------- Incoming messages ----------
  socket.onmessage = function (event) {
    const data = JSON.parse(event.data);

    if (data.type === 'typing') {
      if (String(data.sender_id) === String(myUserId)) return;
      typingIndicator.textContent = `${data.sender_name} is typing...`;
      clearTimeout(typingTimeout);
      typingTimeout = setTimeout(() => { typingIndicator.textContent = ''; }, 2000);
      return;
    }

    appendMessage(data);
  };

  socket.onclose = function () {
    typingIndicator.textContent = 'Disconnected — refresh to reconnect.';
  };

  function appendMessage(data) {
    const emptyState = messageList.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    const row = document.createElement('div');
    const mine = String(data.sender_id) === String(myUserId);
    row.className = `bubble-row ${mine ? 'mine' : 'theirs'}`;

    const bubble = document.createElement('div');
    bubble.className = 'bubble' + (data.attachment_url && !data.message ? ' media-only' : '');

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

    if (data.message) {
      const text = document.createElement('span');
      text.className = 'bubble-text';
      text.textContent = data.message;
      bubble.appendChild(text);
    }

    const time = document.createElement('span');
    time.className = 'bubble-time';
    time.textContent = data.timestamp;
    bubble.appendChild(time);

    row.appendChild(bubble);
    messageList.appendChild(row);
    messageList.scrollTop = messageList.scrollHeight;
  }

  // ---------- Sending text ----------
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    socket.send(JSON.stringify({ type: 'message', message: text }));
    input.value = '';
    closeEmojiPanel();
  });

  let lastTypingSent = 0;
  input.addEventListener('input', function () {
    const now = Date.now();
    if (now - lastTypingSent > 1500) {
      socket.send(JSON.stringify({ type: 'typing' }));
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

    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;
    const formData = new FormData();
    formData.append('attachment', file);
    formData.append('caption', input.value.trim());

    sendBtn.disabled = true;
    attachBtn.disabled = true;

    fetch(uploadUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
      body: formData,
    })
      .then((res) => res.json())
      .then((res) => {
        if (res.error) {
          typingIndicator.textContent = res.error;
          setTimeout(() => { typingIndicator.textContent = ''; }, 3000);
        } else {
          input.value = '';
        }
      })
      .catch(() => {
        typingIndicator.textContent = 'Upload failed. Please try again.';
        setTimeout(() => { typingIndicator.textContent = ''; }, 3000);
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
