// ===== NAV DARK/LIGHT TRANSITION =====

(function () {
  const nav = document.getElementById('main-nav');
  const hero = document.getElementById('hero');

  window.addEventListener('scroll', () => {
    if (!hero || !nav) return;
    const heroBottom = hero.offsetTop + hero.offsetHeight;
    if (window.scrollY > heroBottom - 80) {
      nav.classList.add('nav-light');
    } else {
      nav.classList.remove('nav-light');
    }
  });
})();

// ===== HERO ENTRANCE ANIMATION =====

document.addEventListener('DOMContentLoaded', () => {
  const heroLeft = document.querySelector('.hero-left');
  const heroRight = document.querySelector('.hero-right');

  if (heroLeft) {
    heroLeft.style.opacity = '0';
    heroLeft.style.transform = 'translateX(-40px)';
  }
  if (heroRight) {
    heroRight.style.opacity = '0';
    heroRight.style.transform = 'translateX(40px)';
  }

  setTimeout(() => {
    if (heroLeft) {
      heroLeft.style.transition = 'opacity 0.9s cubic-bezier(0.16,1,0.3,1), transform 0.9s cubic-bezier(0.16,1,0.3,1)';
      heroLeft.style.opacity = '1';
      heroLeft.style.transform = 'translateX(0)';
    }
    if (heroRight) {
      setTimeout(() => {
        heroRight.style.transition = 'opacity 0.9s cubic-bezier(0.16,1,0.3,1), transform 0.9s cubic-bezier(0.16,1,0.3,1)';
        heroRight.style.opacity = '1';
        heroRight.style.transform = 'translateX(0)';
      }, 200);
    }
  }, 100);
});

// ===== MAGNETIC BUTTON EFFECT =====

(function () {
  const magnetics = document.querySelectorAll('.magnetic');

  magnetics.forEach((btn) => {
    btn.addEventListener('mousemove', (e) => {
      const rect = btn.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = e.clientX - cx;
      const dy = e.clientY - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const maxDist = 80;

      if (dist < maxDist) {
        const pull = (1 - dist / maxDist) * 8;
        const mx = (dx / dist) * pull;
        const my = (dy / dist) * pull;
        btn.style.transform = `translate(${mx}px, ${my}px)`;
      }
    });

    btn.addEventListener('mouseleave', () => {
      btn.style.transition = 'transform 0.4s cubic-bezier(0.16,1,0.3,1)';
      btn.style.transform = 'translate(0, 0)';
      setTimeout(() => {
        btn.style.transition = '';
      }, 400);
    });
  });
})();

// ===== ACTIVE NAV LINK ON SCROLL =====

(function () {
  const navLinks = document.querySelectorAll('.nav-links a');
  const sections = [];

  navLinks.forEach((link) => {
    const id = link.getAttribute('href').slice(1);
    const section = document.getElementById(id);
    if (section) sections.push({ id, el: section, link });
  });

  function updateActive() {
    let current = sections[0];

    for (const s of sections) {
      const rect = s.el.getBoundingClientRect();
      if (rect.top <= 120) current = s;
    }

    navLinks.forEach((l) => l.classList.remove('active'));
    if (current) current.link.classList.add('active');
  }

  window.addEventListener('scroll', updateActive, { passive: true });
  updateActive();
})();

// ===== PROJECTS GRID =====
// (Previously horizontal scroll with drag - now a static grid, no JS needed)

// ===== RESEARCH COUNTER ANIMATION =====

(function () {
  const statNums = document.querySelectorAll('.research-stat-num[data-count]');
  if (!statNums.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      const target = parseInt(el.dataset.count);
      let current = 0;
      const duration = 1200;
      const step = Math.ceil(target / (duration / 16));
      const counter = setInterval(() => {
        current += step;
        if (current >= target) {
          current = target;
          clearInterval(counter);
        }
        el.textContent = current;
      }, 16);
      observer.unobserve(el);
    });
  }, { threshold: 0.5 });

  statNums.forEach(el => observer.observe(el));
})();

// ===== SCROLL REVEAL OBSERVER =====

(function () {
  const reveals = document.querySelectorAll(
    '.reveal, .reveal-left, .reveal-right, .reveal-scale'
  );

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;

        const el = entry.target;

        // If this element is a reveal-group, stagger its children
        if (el.classList.contains('reveal-group')) {
          const children = el.querySelectorAll(
            '.reveal, .reveal-left, .reveal-right, .reveal-scale'
          );
          children.forEach((child, i) => {
            setTimeout(() => {
              child.classList.add('visible');
            }, i * 100);
          });
        }

        el.classList.add('visible');
        observer.unobserve(el);
      });
    },
    { threshold: 0.05 }
  );

  reveals.forEach((el) => observer.observe(el));
})();

// ===== Poster lightbox =====
(function () {
  const cards = Array.from(document.querySelectorAll('.research-poster-card[data-poster]'));
  if (!cards.length) return;

  const lb = document.getElementById('poster-lightbox');
  const img = document.getElementById('lb-image');
  const typeEl = document.getElementById('lb-type');
  const titleEl = document.getElementById('lb-title');
  const subEl = document.getElementById('lb-subtitle');
  const venueEl = document.getElementById('lb-venue');
  const dl = document.getElementById('lb-download');
  const closeBtn = document.getElementById('lb-close');
  const prevBtn = document.getElementById('lb-prev');
  const nextBtn = document.getElementById('lb-next');

  let currentIndex = 0;

  function render(i) {
    const card = cards[i];
    if (!card) return;
    currentIndex = i;
    img.src = card.dataset.full;
    img.alt = card.dataset.title;
    typeEl.textContent = card.dataset.type;
    typeEl.style.color = card.dataset.typecolor || '#A5B4FC';
    titleEl.textContent = card.dataset.title;
    subEl.textContent = card.dataset.subtitle || '';
    venueEl.textContent = card.dataset.venue || '';
    dl.href = card.dataset.pdf;
    dl.setAttribute('download', '');
    prevBtn.style.visibility = cards.length > 1 ? 'visible' : 'hidden';
    nextBtn.style.visibility = cards.length > 1 ? 'visible' : 'hidden';
  }

  function open(i) {
    render(i);
    lb.classList.add('is-open');
    lb.setAttribute('aria-hidden', 'false');
    document.body.classList.add('lb-open');
  }
  function close() {
    lb.classList.remove('is-open');
    lb.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('lb-open');
  }
  function next() { render((currentIndex + 1) % cards.length); }
  function prev() { render((currentIndex - 1 + cards.length) % cards.length); }

  cards.forEach((card, i) => {
    card.addEventListener('click', (e) => {
      e.preventDefault();
      open(i);
    });
  });

  closeBtn.addEventListener('click', close);
  nextBtn.addEventListener('click', next);
  prevBtn.addEventListener('click', prev);

  // Click on backdrop closes
  lb.addEventListener('click', (e) => {
    if (e.target === lb) close();
  });

  // Keyboard nav
  document.addEventListener('keydown', (e) => {
    if (!lb.classList.contains('is-open')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowRight') next();
    if (e.key === 'ArrowLeft') prev();
  });
})();
