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

// ===== PROJECTS DRAG SCROLL =====

(function () {
  const grid = document.querySelector('.projects-grid');
  if (!grid) return;

  let isDown = false;
  let startX;
  let scrollLeft;

  grid.addEventListener('mousedown', (e) => {
    isDown = true;
    startX = e.pageX - grid.offsetLeft;
    scrollLeft = grid.scrollLeft;
  });

  grid.addEventListener('mouseleave', () => { isDown = false; });
  grid.addEventListener('mouseup', () => { isDown = false; });

  grid.addEventListener('mousemove', (e) => {
    if (!isDown) return;
    e.preventDefault();
    const x = e.pageX - grid.offsetLeft;
    const walk = (x - startX) * 2;
    grid.scrollLeft = scrollLeft - walk;
  });

  // Hide scroll hint when scrolled to end
  const hint = document.querySelector('.projects-scroll-hint');
  if (hint) {
    const updateHint = () => {
      const atEnd = grid.scrollLeft + grid.clientWidth >= grid.scrollWidth - 10;
      hint.classList.toggle('hidden', atEnd);
    };
    grid.addEventListener('scroll', updateHint);
    window.addEventListener('resize', updateHint);
    updateHint();
  }
})();

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
