/* auth.js — status login diambil dari server Django (/api/me/).
   Mengubah tombol "Login" jadi "Profil" (pengguna) atau "Dashboard" (admin). */
(function () {
  function apply(me) {
    var loggedIn = !!(me && me.loggedIn);
    var admin = loggedIn && me.role === 'admin';
    document.querySelectorAll('.js-account-label').forEach(function (el) {
      el.textContent = loggedIn ? (admin ? 'Dashboard' : 'Profil') : 'Login';
    });
    document.querySelectorAll('.js-account-link').forEach(function (a) {
      a.setAttribute('href', loggedIn ? (admin ? '/dashboard-admin/' : '/profil.html') : '/login.html');
    });
  }
  function run() {
    fetch('/api/me/', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(apply)
      .catch(function () { apply(null); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
  else run();
})();
