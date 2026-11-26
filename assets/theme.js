// Light/dark toggle (follows the system setting until the visitor chooses)
// and the phone menu.
(function () {
  var root = document.documentElement;
  var saved = localStorage.getItem('theme');
  if (saved) root.setAttribute('data-theme', saved);

  function current() {
    var set = root.getAttribute('data-theme');
    if (set) return set;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  document.addEventListener('DOMContentLoaded', function () {
    var theme = document.querySelector('.theme-toggle');
    if (theme) {
      var label = function () {
        var dark = current() === 'dark';
        theme.textContent = dark ? '☀' : '☾';   // sun / moon
        theme.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
        theme.title = theme.getAttribute('aria-label');
      };
      label();
      theme.addEventListener('click', function () {
        var next = current() === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        label();
      });
    }

    var menu = document.querySelector('.menu-toggle');
    var nav = document.getElementById('site-nav');
    if (menu && nav) {
      menu.addEventListener('click', function () {
        var open = nav.classList.toggle('open');
        menu.setAttribute('aria-expanded', open ? 'true' : 'false');
        menu.innerHTML = open ? '&times;' : '&#9776;';
      });
    }
  });
})();
