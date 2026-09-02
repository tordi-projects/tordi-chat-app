(function () {
  const stage = document.getElementById('story-stage');
  if (!stage) return;

  const slides = Array.from(stage.querySelectorAll('.story-slide'));
  const bars = Array.from(document.querySelectorAll('.story-progress-fill'));
  const timeLabel = document.getElementById('story-time');
  const prevZone = document.getElementById('story-prev');
  const nextZone = document.getElementById('story-next');

  const TEXT_DURATION = 5000;
  const FALLBACK_VIDEO_DURATION = 8000;

  let current = 0;
  let timer = null;

  function csrfToken() {
    const el = document.querySelector('input[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  function markViewed(slide) {
    const url = slide.dataset.markUrl;
    if (!url) return;
    fetch(url, { method: 'POST', headers: { 'X-CSRFToken': csrfToken() } }).catch(() => {});
  }

  function goToInbox() {
    window.location.href = '/';
  }

  function showSlide(index) {
    if (index < 0) { goToInbox(); return; }
    if (index >= slides.length) { goToInbox(); return; }

    clearTimeout(timer);

    slides.forEach((s, i) => { s.style.display = i === index ? 'flex' : 'none'; });
    bars.forEach((b, i) => {
      b.style.transition = 'none';
      b.style.width = i < index ? '100%' : '0%';
    });

    current = index;
    const slide = slides[current];
    timeLabel.textContent = slide.dataset.time || '';
    markViewed(slide);

    const video = slide.querySelector('video');

    if (video) {
      video.currentTime = 0;
      video.muted = false;
      video.play().catch(() => {});
      video.onloadedmetadata = () => {
        const durationMs = (video.duration && isFinite(video.duration)) ? video.duration * 1000 : FALLBACK_VIDEO_DURATION;
        animateBar(durationMs);
      };
      video.onended = () => showSlide(current + 1);
    } else {
      animateBar(TEXT_DURATION);
      timer = setTimeout(() => showSlide(current + 1), TEXT_DURATION);
    }
  }

  function animateBar(durationMs) {
    const bar = bars[current];
    if (!bar) return;
    requestAnimationFrame(() => {
      bar.style.transition = `width ${durationMs}ms linear`;
      bar.style.width = '100%';
    });
  }

  prevZone.addEventListener('click', () => showSlide(current - 1));
  nextZone.addEventListener('click', () => showSlide(current + 1));

  showSlide(0);
})();
