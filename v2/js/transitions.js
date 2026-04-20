// Premium page transitions — fade-out on internal link click,
// fade-in on page load. Universal fallback (no View Transitions API).
// Add to <head> of every page that should participate.
(function () {
  // Mark <html> immediately so body can hide before first paint
  document.documentElement.classList.add('js-transitions');

  function reveal() {
    if (document.body) document.body.classList.add('page-ready');
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', reveal);
  } else {
    reveal();
  }

  // Intercept internal link clicks for fade-out
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href]');
    if (!a) return;
    var href = a.getAttribute('href');
    if (!href) return;

    // Skip: hash anchors, mailto/tel, new-tab, downloads, modifier clicks, external URLs
    if (href.charAt(0) === '#') return;
    if (href.indexOf('mailto:') === 0 || href.indexOf('tel:') === 0) return;
    if (a.target === '_blank' || a.hasAttribute('download')) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
    if (/^https?:\/\//.test(href) && href.indexOf(location.host) === -1) return;

    e.preventDefault();
    document.body.classList.remove('page-ready');
    document.body.classList.add('page-leaving');
    setTimeout(function () { window.location.href = href; }, 240);
  }, true);

  // Restore on back/forward cache navigation (Safari, Firefox)
  window.addEventListener('pageshow', function (e) {
    if (e.persisted) {
      document.body.classList.remove('page-leaving');
      document.body.classList.add('page-ready');
    }
  });
})();
