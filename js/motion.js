// Motion enhancements: 3D card tilt + scroll progress bar.
// Both respect prefers-reduced-motion.
(function () {
  var reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ===== Scroll progress bar =====
  // Thin gradient line at the very top of the viewport. Width tracks scroll
  // position. Lives on every page that includes this script.
  function initScrollProgress() {
    var bar = document.createElement('div');
    bar.className = 'scroll-progress';
    bar.setAttribute('aria-hidden', 'true');
    document.body.appendChild(bar);

    var ticking = false;
    function update() {
      var doc = document.documentElement;
      var max = (doc.scrollHeight || document.body.scrollHeight) - window.innerHeight;
      var pct = max > 0 ? (window.scrollY / max) * 100 : 0;
      bar.style.transform = 'scaleX(' + (pct / 100) + ')';
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) {
        window.requestAnimationFrame(update);
        ticking = true;
      }
    }, { passive: true });
    update();
  }

  // ===== 3D card tilt =====
  // Subtle rotateX/rotateY following the cursor, capped at small angles for
  // taste. CSS reads the values from custom properties so existing transforms
  // (the case-card hover translateY, the tile box-shadow) keep working.
  function init3DTilt() {
    if (reducedMotion) return;
    // Don't enable on touch-only devices (no real hover).
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;

    var cards = document.querySelectorAll('.case-card');
    if (!cards.length) return;

    var MAX_TILT_X = 5;  // degrees
    var MAX_TILT_Y = 7;

    cards.forEach(function (card) {
      var rafId = null;
      var pending = null;

      function apply() {
        if (!pending) return;
        card.style.setProperty('--tilt-x', pending.x + 'deg');
        card.style.setProperty('--tilt-y', pending.y + 'deg');
        pending = null;
        rafId = null;
      }

      card.addEventListener('mouseenter', function () {
        card.classList.add('tilting');
      });

      card.addEventListener('mousemove', function (e) {
        var rect = card.getBoundingClientRect();
        var cx = (e.clientX - rect.left) / rect.width - 0.5;   // -0.5 to 0.5
        var cy = (e.clientY - rect.top) / rect.height - 0.5;
        pending = {
          x: (-cy * MAX_TILT_X * 2).toFixed(2),
          y: (cx * MAX_TILT_Y * 2).toFixed(2),
        };
        if (rafId == null) rafId = window.requestAnimationFrame(apply);
      });

      card.addEventListener('mouseleave', function () {
        card.classList.remove('tilting');
        card.style.setProperty('--tilt-x', '0deg');
        card.style.setProperty('--tilt-y', '0deg');
      });
    });
  }

  function init() {
    initScrollProgress();
    init3DTilt();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
