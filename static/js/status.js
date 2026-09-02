(function () {
  const form = document.getElementById('status-form');
  if (!form) return;

  const textArea = document.getElementById('status-text');
  const mediaBtn = document.getElementById('status-media-btn');
  const mediaInput = document.getElementById('status-media-input');
  const preview = document.getElementById('status-preview');
  const createUrl = window.TORDI_CREATE_STATUS_URL;

  function csrfToken() {
    return form.querySelector('[name=csrfmiddlewaretoken]').value;
  }

  mediaBtn.addEventListener('click', () => mediaInput.click());

  mediaInput.addEventListener('change', function () {
    preview.innerHTML = '';
    const file = mediaInput.files[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    if (file.type.startsWith('video')) {
      const v = document.createElement('video');
      v.src = url; v.controls = true; v.style.maxWidth = '100%'; v.style.borderRadius = '12px'; v.style.marginTop = '10px';
      preview.appendChild(v);
    } else {
      const img = document.createElement('img');
      img.src = url; img.style.maxWidth = '100%'; img.style.borderRadius = '12px'; img.style.marginTop = '10px';
      preview.appendChild(img);
    }
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    const text = textArea.value.trim();
    const file = mediaInput.files[0];
    if (!text && !file) return;

    const submitBtn = form.querySelector('button[type=submit]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Posting...';

    const formData = new FormData();
    formData.append('text', text);
    if (file) formData.append('media', file);

    fetch(createUrl, { method: 'POST', headers: { 'X-CSRFToken': csrfToken() }, body: formData })
      .then((res) => res.json())
      .then((res) => {
        if (res.error) {
          alert(res.error);
          submitBtn.disabled = false;
          submitBtn.textContent = 'Post status';
        } else {
          window.location.reload();
        }
      })
      .catch(() => {
        alert('Failed to post status. Please try again.');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Post status';
      });
  });

  document.querySelectorAll('.delete-status-btn').forEach((btn) => {
    btn.addEventListener('click', function () {
      if (!confirm('Delete this status?')) return;
      fetch(btn.dataset.url, { method: 'POST', headers: { 'X-CSRFToken': csrfToken() } })
        .then(() => window.location.reload())
        .catch(() => alert('Failed to delete. Please try again.'));
    });
  });
})();
