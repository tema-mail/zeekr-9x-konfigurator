/* Конфигуратор Zeekr 9X: места, версия, батарея, помощь водителю, цвет, декор, диски, салон, экран.
 * Картинки – официальные рендеры Zeekr конкретной сборки. Цен нет намеренно. Без зависимостей.
 * Для встраивания: событие "zeekr9x:change" на блоке [data-z9] (detail: text, config, url)
 * и window.Zeekr9X.get() – текущая сборка, чтобы подставить её в форму заявки сайта. */
(function () {
  "use strict";

  var D = window.ZEEKR_9X;
  var root = document.querySelector("[data-z9]");
  if (!D || !root) return;

  var $ = function (sel) { return root.querySelector(sel); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); };
  var O = D.options;
  var opt = function (id) { return O[id] || { name: id, note: "", mutex: [], cascade: [] }; };
  var ids = function (list) { return list.map(function (x) { return x.id; }); };
  var defOf = function (list) { for (var i = 0; i < list.length; i++) if (list[i].def) return list[i].id; return list.length ? list[0].id : null; };
  var EXT = {}; D.ext.forEach(function (c) { EXT[c] = true; });
  var INT = {}; D.int.forEach(function (c) { INT[c] = true; });
  var SHORT = function (pc) { return pc.replace(/^Z011PC/, ""); };
  var LONG = function (s) { return "Z011PC" + s; };

  function conflict(a, b) {
    return opt(a).mutex.indexOf(b) !== -1 || opt(b).mutex.indexOf(a) !== -1;
  }
  function versionById(id) { for (var i = 0; i < D.versions.length; i++) if (D.versions[i].id === id) return D.versions[i]; return null; }
  function versionsOf(seats) { return D.versions.filter(function (v) { return v.seats === seats; }); }

  // ---------- состояние ----------
  var first = versionById("55") || D.versions[0];
  var state = { seats: first.seats, version: first.id, battery: null, adas: null, paint: null, kit: null, wheel: null, interior: null, screen: null, extras: [], shot: "hero" };

  function resetToDefaults(V, keepLook) {
    state.battery = defOf(V.batteries);
    state.adas = defOf(V.adas);
    ["paint", "kit", "wheel", "interior", "screen"].forEach(function (k) {
      var list = ids(V[k + "s"]);
      if (!keepLook || list.indexOf(state[k]) === -1) state[k] = defOf(V[k + "s"]);
    });
    state.extras = V.extras.filter(function (e) { return e.def; }).map(function (e) { return e.id; });
  }
  resetToDefaults(first, false);

  // Ссылка на сборку: #v=55&b=001&a=012&p=002&k=021&w=026&i=008&s=033&x=017
  (function readHash() {
    var h = location.hash.replace(/^#/, "");
    if (!h) return;
    var q = {};
    h.split("&").forEach(function (kv) { var p = kv.split("="); q[p[0]] = decodeURIComponent(p[1] || ""); });
    var V = versionById(q.v);
    if (!V) return;
    state.version = V.id; state.seats = V.seats;
    resetToDefaults(V, false);
    var map = { b: "battery", a: "adas", p: "paint", k: "kit", w: "wheel", i: "interior", s: "screen" };
    Object.keys(map).forEach(function (key) { if (q[key]) state[map[key]] = LONG(q[key]); });
    if (q.x !== undefined) state.extras = q.x ? q.x.split(".").map(LONG) : [];
  })();

  var version = function () { return versionById(state.version); };

  // Привести сборку в порядок: недоступное в версии – на значение по умолчанию,
  // несовместимое (цвет / декор / диски) – подобрать, начиная с того, что человек выбрал последним.
  function normalize(priority) {
    var V = version();
    if (ids(V.batteries).indexOf(state.battery) === -1) state.battery = defOf(V.batteries);
    if (ids(V.adas).indexOf(state.adas) === -1) state.adas = defOf(V.adas);
    ["interior", "screen"].forEach(function (k) { if (ids(V[k + "s"]).indexOf(state[k]) === -1) state[k] = defOf(V[k + "s"]); });

    var order = ["paint", "kit", "wheel"];
    if (priority && order.indexOf(priority) !== -1) order = [priority].concat(order.filter(function (k) { return k !== priority; }));
    var fixed = {};
    order.forEach(function (k, n) {
      var list = V[k + "s"];
      var valid = function (x) {
        if (ids(list).indexOf(x) === -1) return false;
        for (var f in fixed) if (conflict(x, fixed[f])) return false;
        if (k === "wheel" && fixed.kit && opt(fixed.kit).cascade.length && opt(fixed.kit).cascade.indexOf(x) === -1) return false;
        if (k === "kit" && fixed.wheel && opt(x).cascade.length && opt(x).cascade.indexOf(fixed.wheel) === -1) return false;
        return true;
      };
      if (n > 0 || ids(list).indexOf(state[k]) === -1) {
        if (!valid(state[k])) {
          var pick = null, d = defOf(list);
          if (valid(d)) pick = d;
          else for (var i = 0; i < list.length; i++) if (valid(list[i].id)) { pick = list[i].id; break; }
          state[k] = pick || d;
        }
      }
      fixed[k] = state[k];
    });
    var allowedExtras = ids(V.extras);
    state.extras = state.extras.filter(function (x) { return allowedExtras.indexOf(x) !== -1; });
    V.extras.forEach(function (e) { if (e.def && state.extras.indexOf(e.id) === -1) state.extras.push(e.id); });
  }

  // ---------- картинки ----------
  function extCode() {
    var c = [state.adas, state.paint, state.kit, state.wheel].join("_");
    if (EXT[c]) return c;
    var tail = "_" + [state.paint, state.kit, state.wheel].join("_");
    for (var k in EXT) if (k.slice(-tail.length) === tail) return k;
    return D.ext[0];
  }
  function intCode() {
    var c = [state.interior, state.adas, state.screen].join("_");
    if (INT[c]) return c;
    for (var k in INT) if (k.indexOf(state.interior + "_") === 0) return k;
    return D.int[0];
  }
  // Виды, которые есть у текущей сборки: у части сборок Zeekr не делал ракурсы спереди и сбоку.
  function shotsNow() {
    var have = (D.have && D.have[extCode()]) || ["hero"];
    return D.shots.filter(function (s) { return s.id === "int" || have.indexOf(s.id) !== -1; });
  }
  function fixShot() {
    if (!shotsNow().some(function (s) { return s.id === state.shot; })) state.shot = "hero";
  }
  function srcFor(shot) {
    if (shot === "int") return D.paths.int.replace("{code}", intCode());
    return D.paths.ext.replace("{code}", extCode()).replace("{shot}", shot);
  }

  var cache = {};
  function preload(src) {
    if (cache[src]) return cache[src];
    var img = new Image(); img.decoding = "async";
    cache[src] = new Promise(function (res) { img.onload = img.onerror = function () { res(src); }; });
    img.src = src;
    return cache[src];
  }
  function warm() { shotsNow().forEach(function (s) { preload(srcFor(s.id)); }); }

  var stage = $(".z9__stage");
  var front = $(".z9__shot--a"), back = $(".z9__shot--b");
  var token = 0;
  function show() {
    var my = ++token, src = srcFor(state.shot), hero = state.shot === "hero";
    stage.classList.add("is-loading");
    preload(src).then(function () {
      if (my !== token) return;
      var img = back.querySelector("img");
      img.src = src; img.alt = altText();
      back.classList.toggle("is-hero", hero);
      back.classList.add("is-front"); front.classList.remove("is-front");
      var t = front; front = back; back = t;
      stage.classList.remove("is-loading");
      warm();
    });
  }
  function altText() {
    if (state.shot === "int") return "Салон Zeekr 9X, " + opt(state.interior).name;
    var sh = D.shots.filter(function (s) { return s.id === state.shot; })[0];
    return "Zeekr 9X " + version().name + ", " + opt(state.paint).name + ", " + opt(state.wheel).name + ", " + sh.label.toLowerCase();
  }

  // ---------- отрисовка ----------
  function seg(attr, id, title, sub, active, single) {
    return '<button type="button" class="z9__seg' + (active ? " is-active" : "") + (single ? " is-single" : "") + '" data-' + attr + '="' + id + '" aria-pressed="' + active + '"><b>' + esc(title) + "</b>" + (sub ? "<span>" + esc(sub) + "</span>" : "") + "</button>";
  }
  function option(attr, id, active, single) {
    var o = opt(id);
    return '<button type="button" class="z9__option' + (active ? " is-active" : "") + (single ? " is-single" : "") + '" data-' + attr + '="' + id + '" aria-pressed="' + active + '">' +
      (o.icon ? '<img src="' + o.icon + '" alt="" width="56" height="56" loading="lazy">' : "<span></span>") +
      '<span class="z9__option-text"><span class="z9__option-name">' + esc(o.name) + '</span><span class="z9__option-note">' + esc(o.note) + "</span></span></button>";
  }
  function swatches(attr, list, cur) {
    return list.map(function (x) {
      var o = opt(x.id), on = x.id === cur;
      return '<button type="button" class="z9__swatch' + (on ? " is-active" : "") + '" data-' + attr + '="' + x.id + '" title="' + esc(o.name) + '" aria-label="' + esc(o.name) + '" aria-pressed="' + on + '">' +
        '<img src="' + o.icon + '" alt="" width="44" height="44"></button>';
    }).join("");
  }

  function render() {
    var V = version();
    var seatsList = [];
    D.versions.forEach(function (v) { if (seatsList.indexOf(v.seats) === -1) seatsList.push(v.seats); });
    $("[data-slot=seats]").innerHTML = seatsList.sort().reverse().map(function (s) {
      return seg("seats", s, s + " мест", s === 6 ? "второй ряд – два кресла" : "второй ряд – диван", s === state.seats);
    }).join("");

    $("[data-slot=versions]").innerHTML = versionsOf(state.seats).map(function (v) {
      var on = v.id === state.version;
      return '<button type="button" class="z9__trim' + (on ? " is-active" : "") + '" data-version="' + v.id + '" aria-pressed="' + on + '">' +
        '<span class="z9__trim-name">9X ' + esc(v.name) + '</span><span class="z9__trim-tag">' + esc(v.tag) + "</span></button>";
    }).join("");

    $("[data-slot=battery]").innerHTML = V.batteries.map(function (b) {
      var r = V.ranges[b.id];
      return seg("battery", b.id, b.name, r ? r.ev + " км на электричестве · " + r.total + " км всего" : "", b.id === state.battery, V.batteries.length === 1);
    }).join("");
    $("[data-slot=adas]").innerHTML = V.adas.map(function (a) {
      return seg("adas", a.id, "Пакет " + a.name, a.note, a.id === state.adas, V.adas.length === 1);
    }).join("");

    $("[data-slot=paint-picked]").textContent = opt(state.paint).name;
    $("[data-slot=paints]").innerHTML = swatches("paint", V.paints, state.paint);

    $("[data-slot=kit-picked]").textContent = "";
    $("[data-slot=kits]").innerHTML = V.kits.map(function (k) { return option("kit", k.id, k.id === state.kit, V.kits.length === 1); }).join("");
    var kitNote = "";
    V.kits.forEach(function (k) { if (conflict(k.id, state.paint)) kitNote = "Глянцевый хром – только с белым кузовом, чёрный декор и пакет «Яохэй» – только с чёрным. При выборе цвет подстроится."; });
    $("[data-slot=kit-note]").textContent = kitNote;

    $("[data-slot=wheel-picked]").textContent = "";
    $("[data-slot=wheels]").innerHTML = V.wheels.map(function (w) { return option("wheel", w.id, w.id === state.wheel, V.wheels.length === 1); }).join("");
    var wn = "";
    if (opt(state.kit).cascade.length) wn = "С пакетом «Яохэй» – только чёрные кованые диски.";
    else if (V.wheels.some(function (w) { return opt(w.id).cascade.length === 0 && conflict(w.id, state.kit); })) wn = "Чёрные диски «Яохэй» идут только в пакете «Яохэй».";
    $("[data-slot=wheel-note]").textContent = wn;

    $("[data-slot=interior-picked]").textContent = opt(state.interior).name;
    $("[data-slot=interiors]").innerHTML = swatches("interior", V.interiors, state.interior);

    $("[data-slot=screens]").innerHTML = V.screens.map(function (s) {
      return seg("screen", s.id, opt(s.id).name, opt(s.id).note, s.id === state.screen, V.screens.length === 1);
    }).join("");

    $("[data-block=extras]").hidden = !V.extras.length;
    $("[data-slot=extras]").innerHTML = V.extras.map(function (e) {
      var on = state.extras.indexOf(e.id) !== -1;
      return '<label class="z9__check"><input type="checkbox" data-extra="' + e.id + '"' + (on ? " checked" : "") + (e.def ? " disabled" : "") + "> " +
        esc(opt(e.id).name) + (e.def ? " <small>в комплектации</small>" : "") + "</label>";
    }).join("");

    renderThumbs();
    renderSummary();
  }

  function renderThumbs() {
    $("[data-slot=thumbs]").innerHTML = shotsNow().map(function (s) {
      var on = s.id === state.shot;
      return '<button type="button" class="z9__thumb' + (s.id === "hero" ? " is-hero" : "") + (on ? " is-active" : "") + '" data-shot="' + s.id + '" aria-pressed="' + on + '">' +
        '<img src="' + srcFor(s.id) + '" alt="" loading="lazy" width="160" height="100"><span>' + esc(s.label) + "</span></button>";
    }).join("");
  }

  function config() {
    var V = version(), r = V.ranges[state.battery] || {};
    var adas = V.adas.filter(function (a) { return a.id === state.adas; })[0] || {};
    var lines = [
      ["Версия", "9X " + V.name + ", " + V.seats + " мест"],
      ["Привод", V.drive],
      ["Батарея", opt(state.battery).name],
      ["Запас хода (CLTC)", r.ev ? r.ev + " км на электричестве, " + r.total + " км всего" : ""],
      ["Помощь водителю", "Пакет " + opt(state.adas).name + (adas.note ? " (" + adas.note + ")" : "")],
      ["Цвет кузова", opt(state.paint).name],
      ["Декор кузова", opt(state.kit).name],
      ["Диски", opt(state.wheel).name + ", " + opt(state.wheel).note],
      ["Салон", opt(state.interior).name],
      ["Экран спереди", opt(state.screen).name]
    ];
    if (state.extras.length) lines.push(["Дополнительно", state.extras.map(function (x) { return opt(x).name; }).join(", ")]);
    var text = "Zeekr 9X " + V.name + ", " + V.seats + " мест, " + opt(state.battery).name + ", " + opt(state.adas).name + ": " +
      "кузов " + opt(state.paint).name + ", декор: " + opt(state.kit).name + ", диски " + opt(state.wheel).name + ", салон " + opt(state.interior).name;
    var hash = "#v=" + V.id + "&b=" + SHORT(state.battery) + "&a=" + SHORT(state.adas) + "&p=" + SHORT(state.paint) + "&k=" + SHORT(state.kit) +
      "&w=" + SHORT(state.wheel) + "&i=" + SHORT(state.interior) + "&s=" + SHORT(state.screen) + "&x=" + state.extras.map(SHORT).join(".");
    return { text: text, lines: lines, hash: hash, codes: { version: V.id, battery: state.battery, adas: state.adas, paint: state.paint, kit: state.kit, wheel: state.wheel, interior: state.interior, screen: state.screen, extras: state.extras.slice() } };
  }

  function renderSummary() {
    var c = config(), V = version();
    $("[data-slot=summary-config]").textContent = c.text;
    $("[data-slot=summary-lines]").innerHTML = c.lines.filter(function (l) { return l[1]; }).map(function (l) {
      return '<div class="z9__row"><dt>' + esc(l[0]) + "</dt><dd>" + esc(l[1]) + "</dd></div>";
    }).join("");
    $("[data-slot=stage-name]").textContent = "Zeekr 9X " + V.name;
    $("[data-slot=stage-note]").textContent = opt(state.paint).name + " · " + opt(state.wheel).name + " · салон " + opt(state.interior).name;
    if (history.replaceState) history.replaceState(null, "", c.hash);
    var detail = { text: c.text, lines: c.lines, config: c.codes, url: location.href.split("#")[0] + c.hash };
    window.Zeekr9X = { get: function () { return detail; } };
    root.dispatchEvent(new CustomEvent("zeekr9x:change", { bubbles: true, detail: detail }));
  }

  function update(priority, imageChanged) {
    normalize(priority);
    fixShot();
    render();
    if (imageChanged !== false) show();
  }

  // ---------- события ----------
  root.addEventListener("click", function (e) {
    var b = e.target.closest("button");
    if (!b || !root.contains(b)) return;
    var d = b.dataset;
    if (d.seats) {
      var s = +d.seats; if (s === state.seats) return;
      var name = version().name, list = versionsOf(s);
      var V = list.filter(function (v) { return v.name === name; })[0] || list[0];
      state.seats = s; state.version = V.id; resetToDefaults(V, true); update(null);
    } else if (d.version) {
      if (d.version === state.version) return;
      var V2 = versionById(d.version); state.version = V2.id; resetToDefaults(V2, true); update(null);
    } else if (d.battery) { state.battery = d.battery; update(null, false);
    } else if (d.adas) { state.adas = d.adas; if (state.shot === "int") state.shot = "hero"; update(null);
    } else if (d.paint) { state.paint = d.paint; if (state.shot === "int") state.shot = "hero"; update("paint");
    } else if (d.kit) { state.kit = d.kit; if (state.shot === "int") state.shot = "front34"; update("kit");
    } else if (d.wheel) { state.wheel = d.wheel; if (state.shot === "int" || state.shot === "rear34") state.shot = "side"; update("wheel");
    } else if (d.interior) { state.interior = d.interior; state.shot = "int"; update(null);
    } else if (d.screen) { state.screen = d.screen; state.shot = "int"; update(null);
    } else if (d.shot) { state.shot = d.shot; renderThumbs(); show();
    } else if (d.nav) {
      var list2 = shotsNow().map(function (x) { return x.id; }), idx = list2.indexOf(state.shot);
      state.shot = list2[(idx + (d.nav === "next" ? 1 : -1) + list2.length) % list2.length];
      renderThumbs(); show();
    } else if (b.hasAttribute("data-copy")) {
      var url = window.Zeekr9X.get().url, st = $("[data-slot=copy-status]");
      var ok = function () { st.textContent = "Ссылка скопирована"; };
      if (navigator.clipboard) navigator.clipboard.writeText(url).then(ok, function () { st.textContent = url; });
      else st.textContent = url;
    }
  });
  root.addEventListener("change", function (e) {
    var x = e.target.getAttribute("data-extra");
    if (!x) return;
    var i = state.extras.indexOf(x);
    if (e.target.checked && i === -1) state.extras.push(x);
    if (!e.target.checked && i !== -1) state.extras.splice(i, 1);
    update(null, false);
  });
  stage.addEventListener("keydown", function (e) {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    e.preventDefault();
    var list = shotsNow().map(function (x) { return x.id; }), idx = list.indexOf(state.shot);
    state.shot = list[(idx + (e.key === "ArrowRight" ? 1 : -1) + list.length) % list.length];
    renderThumbs(); show();
  });
  (function swipe() {
    var x0 = null;
    stage.addEventListener("pointerdown", function (e) { x0 = e.clientX; });
    stage.addEventListener("pointerup", function (e) {
      if (x0 === null) return;
      var dx = e.clientX - x0; x0 = null;
      if (Math.abs(dx) < 40) return;
      var list = shotsNow().map(function (x) { return x.id; }), idx = list.indexOf(state.shot);
      state.shot = list[(idx + (dx < 0 ? 1 : -1) + list.length) % list.length];
      renderThumbs(); show();
    });
  })();

  // ---------- тема ----------
  var tb = document.querySelector("[data-theme-toggle]");
  if (tb) {
    var upd = function () { var dk = document.documentElement.getAttribute("data-theme") === "dark"; tb.textContent = dk ? "☀" : "☾"; tb.title = dk ? "Светлая тема" : "Тёмная тема"; };
    tb.addEventListener("click", function () {
      var n = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", n);
      try { localStorage.setItem("tema", n); } catch (er) {}
      upd();
    });
    upd();
  }

  normalize(null);
  fixShot();
  render();
  var img0 = front.querySelector("img");
  img0.src = srcFor(state.shot); img0.alt = altText();
  front.classList.add("is-front"); front.classList.toggle("is-hero", state.shot === "hero");
  window.addEventListener("load", function () { setTimeout(warm, 600); });
})();
