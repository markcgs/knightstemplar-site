// Light/dark toggle, mobile menu, State News filter and calendar filter.
(function () {
  var root = document.documentElement;
  var mq = matchMedia("(prefers-color-scheme: dark)");
  var isDark = function () { return (root.dataset.theme || (mq.matches ? "dark" : "light")) === "dark"; };
  var btn = document.querySelector(".theme-btn");
  if (btn) {
    var sync = function () {
      btn.setAttribute("aria-pressed", String(isDark()));
      btn.setAttribute("aria-label", isDark() ? "Light mode" : "Dark mode");
    };
    btn.hidden = false;
    sync();
    btn.addEventListener("click", function () {
      root.dataset.theme = isDark() ? "light" : "dark";
      try { localStorage.setItem("theme", root.dataset.theme); } catch (e) {}
      sync();
    });
    mq.addEventListener && mq.addEventListener("change", sync);
  }

  var menu = document.querySelector(".menu-btn");
  var nav = document.getElementById("site-nav");
  if (menu && nav) {
    menu.hidden = false;
    menu.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      menu.setAttribute("aria-expanded", String(open));
    });
  }

  document.querySelectorAll("input[data-filter]").forEach(function (input) {
    var table = document.querySelector(input.dataset.filter);
    if (!table) return;
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase();
      table.querySelectorAll("tbody tr").forEach(function (tr) {
        tr.hidden = q && tr.querySelector("th").textContent.toLowerCase().indexOf(q) === -1;
      });
    });
  });

  var filt = document.querySelector(".ev-filter");
  if (filt) {
    filt.addEventListener("click", function (ev) {
      var b = ev.target.closest("button");
      if (!b) return;
      filt.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      var cat = b.dataset.cat;
      document.querySelectorAll("#upcoming .ev").forEach(function (card) {
        var c = card.querySelector(".ev-cat");
        card.hidden = cat && (!c || c.textContent !== cat);
      });
      document.querySelectorAll("#upcoming .ev-list").forEach(function (list) {
        var any = list.querySelector(".ev:not([hidden])");
        list.hidden = !any;
        list.previousElementSibling.hidden = !any;
      });
    });
  }
})();
