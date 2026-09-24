(function () {
  var LOGIN_KEY = 'amoraLoggedIn';

  function apply() {
    var loggedIn = false;
    try { loggedIn = localStorage.getItem(LOGIN_KEY) === '1'; } catch (e) {}

    document.querySelectorAll('.js-account-label').forEach(function (el) {
      el.textContent = loggedIn ? 'Profil' : 'Login';
    });
    document.querySelectorAll('.js-account-link').forEach(function (a) {
      a.setAttribute('href', loggedIn ? 'profil.html' : 'login.html');
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', apply);
  } else {
    apply();
  }
})();