(function () {
  function csrfToken() {
    const el = document.querySelector('input[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  document.querySelectorAll('.add-contact-btn').forEach((btn) => {
    btn.addEventListener('click', function () {
      btn.disabled = true;
      fetch(btn.dataset.url, { method: 'POST', headers: { 'X-CSRFToken': csrfToken() } })
        .then((res) => res.json())
        .then((res) => {
          if (res.status === 'ok') {
            const badge = document.createElement('span');
            badge.className = 'added-badge';
            badge.textContent = '✓ Added';
            btn.replaceWith(badge);
          } else {
            btn.disabled = false;
            alert(res.error || 'Failed to add contact.');
          }
        })
        .catch(() => {
          btn.disabled = false;
          alert('Failed to add contact. Please try again.');
        });
    });
  });
})();
