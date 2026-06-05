const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

window.addEventListener('load', () => {
  setTimeout(() => document.body.classList.add('loaded'), prefersReducedMotion ? 50 : 1350);
});

const progressBar = document.querySelector('.progress-bar');
const progressDot = document.querySelector('.progress-dot');
const horizontalWrap = document.querySelector('.horizontal-wrap');
const horizontalTrack = document.querySelector('.horizontal-track');
const hero = document.querySelector('.hero');
const stage = document.querySelector('.stage');

function updateScrollEffects() {
  const max = document.documentElement.scrollHeight - innerHeight;
  const percent = max ? window.scrollY / max : 0;
  progressBar.style.width = `${percent * 100}%`;
  progressDot.style.left = `${percent * 100}%`;

  if (horizontalWrap && horizontalTrack) {
    const rect = horizontalWrap.getBoundingClientRect();
    const travel = Math.max(0, horizontalTrack.scrollWidth - innerWidth + innerWidth * 0.16);
    const total = Math.max(1, horizontalWrap.offsetHeight - innerHeight);
    if (rect.top <= 0 && Math.abs(rect.top) <= total) {
      const local = Math.min(1, Math.max(0, Math.abs(rect.top) / total));
      horizontalTrack.style.transform = `translateX(${-travel * local}px)`;
    }
  }

  if (hero && stage) {
    const heroProgress = Math.min(1, Math.max(0, window.scrollY / Math.max(1, hero.offsetHeight)));
    stage.style.transform = `rotateX(${heroProgress * 5}deg) rotateY(${-heroProgress * 8}deg) translateY(${heroProgress * 26}px)`;
    hero.style.setProperty('--hero-progress', heroProgress.toFixed(3));
  }
}
window.addEventListener('scroll', updateScrollEffects, { passive: true });
window.addEventListener('resize', updateScrollEffects);
updateScrollEffects();

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) entry.target.classList.add('in-view');
  });
}, { threshold: 0.16 });
document.querySelectorAll('.reveal, .doodle-panel').forEach(el => observer.observe(el));

const cursorGlow = document.querySelector('.cursor-glow');
window.addEventListener('pointermove', event => {
  if (!cursorGlow || prefersReducedMotion) return;
  cursorGlow.animate({ left: `${event.clientX}px`, top: `${event.clientY}px` }, { duration: 650, fill: 'forwards' });
});

document.querySelectorAll('.magnetic').forEach(button => {
  button.addEventListener('pointermove', event => {
    if (prefersReducedMotion) return;
    const rect = button.getBoundingClientRect();
    button.style.transform = `translate(${(event.clientX - rect.left - rect.width / 2) * .18}px, ${(event.clientY - rect.top - rect.height / 2) * .18}px)`;
  });
  button.addEventListener('pointerleave', () => button.style.transform = 'translate(0, 0)');
});

document.querySelectorAll('.tilt, .story-beat').forEach(card => {
  card.addEventListener('pointermove', event => {
    const rect = card.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width - .5;
    const y = (event.clientY - rect.top) / rect.height - .5;
    card.style.setProperty('--mx', `${(x + .5) * 100}%`);
    card.style.setProperty('--my', `${(y + .5) * 100}%`);
    if (card.classList.contains('tilt') && !prefersReducedMotion) {
      card.style.transform = `rotateX(${-y * 10}deg) rotateY(${x * 12}deg) translateY(-6px)`;
    }
  });
  card.addEventListener('pointerleave', () => {
    if (card.classList.contains('tilt')) card.style.transform = 'rotateX(0) rotateY(0) translateY(0)';
  });
});

function burst(x = innerWidth / 2, y = innerHeight / 2, count = 28) {
  for (let i = 0; i < count; i++) {
    const heart = document.createElement('span');
    heart.className = 'heart-burst';
    heart.style.left = `${x}px`;
    heart.style.top = `${y}px`;
    heart.style.background = i % 4 === 0 ? '#64f4ff' : i % 3 === 0 ? '#ff9d43' : i % 2 ? '#a979ff' : '#ff68b5';
    heart.style.setProperty('--x', `${Math.cos(i * 1.7) * (90 + Math.random() * 180)}px`);
    heart.style.setProperty('--y', `${Math.sin(i * 1.31) * (90 + Math.random() * 180)}px`);
    document.body.appendChild(heart);
    setTimeout(() => heart.remove(), 950);
  }
}

document.getElementById('syncMoment')?.addEventListener('click', event => burst(event.clientX, event.clientY, 38));
document.querySelector('.confetti-btn')?.addEventListener('click', event => burst(event.clientX, event.clientY, 64));

const liveLabels = ['@123 watching quietly', '@125 collecting details', '@126 bringing bike', '@124 noticed one effort', 'story growth progressing'];
const liveCollab = document.querySelector('.live-collab');
let liveIndex = 0;
if (liveCollab && !prefersReducedMotion) {
  setInterval(() => {
    const tags = liveCollab.querySelectorAll('em');
    if (!tags.length) return;
    tags[liveIndex % tags.length].textContent = liveLabels[liveIndex % liveLabels.length];
    liveIndex += 1;
  }, 1600);
}

const canvas = document.getElementById('constellation');
const ctx = canvas.getContext('2d');
let stars = [];
function resizeCanvas() {
  canvas.width = innerWidth * devicePixelRatio;
  canvas.height = innerHeight * devicePixelRatio;
  ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
  stars = Array.from({ length: Math.min(120, Math.floor(innerWidth / 12)) }, () => ({
    x: Math.random() * innerWidth,
    y: Math.random() * innerHeight,
    vx: (Math.random() - .5) * .35,
    vy: (Math.random() - .5) * .35,
    r: Math.random() * 1.8 + .5
  }));
}
function animateStars() {
  ctx.clearRect(0, 0, innerWidth, innerHeight);
  stars.forEach((star, i) => {
    star.x = (star.x + star.vx + innerWidth) % innerWidth;
    star.y = (star.y + star.vy + innerHeight) % innerHeight;
    ctx.beginPath();
    ctx.arc(star.x, star.y, star.r, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,.72)';
    ctx.fill();
    for (let j = i + 1; j < stars.length; j++) {
      const other = stars[j];
      const distance = Math.hypot(star.x - other.x, star.y - other.y);
      if (distance < 105) {
        ctx.strokeStyle = `rgba(255,104,181,${(1 - distance / 105) * .16})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(star.x, star.y);
        ctx.lineTo(other.x, other.y);
        ctx.stroke();
      }
    }
  });
  if (!prefersReducedMotion) requestAnimationFrame(animateStars);
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);
animateStars();
