(function () {
  function csrfToken() {
    const el = document.querySelector('input[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  document.querySelectorAll('.remove-contact-btn').forEach((btn) => {
    btn.addEventListener('click', function () {
      if (!confirm('Remove this contact? They will no longer see your status.')) return;
      fetch(btn.dataset.url, { method: 'POST', headers: { 'X-CSRFToken': csrfToken() } })
        .then(() => window.location.reload())
        .catch(() => alert('Failed to remove contact. Please try again.'));
    });
  });
})();
