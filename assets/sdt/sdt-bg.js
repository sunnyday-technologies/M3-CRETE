/* Sunnyday background layer for bom.m3-crete.com (copied from the m3-crete.com release, 2026-11-04).
   Reads <html data-sdt-bg="gantry|plain"> and draws a decorative, aria-hidden canvas behind the page:
   the M3-2 seen from above, drawn faint and slow. One animation loop, paused in hidden tabs,
   device pixel ratio capped at 2, a still frame under prefers-reduced-motion, and fainter under 720 px. */
(function () {
  "use strict";
  var root = document.documentElement;
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  var layer = null;
  var stop = function () {};
  var STEEL = "169, 203, 239";
  var LIME = "151, 215, 0";

  function rgba(c, a) { return "rgba(" + c + ", " + Math.max(0, a).toFixed(3) + ")"; }
  function ease(x) { x = x < 0 ? 0 : x > 1 ? 1 : x; return x * x * (3 - 2 * x); }
  function superellipse(a, n) {
    return Math.pow(Math.pow(Math.abs(Math.cos(a)), n) + Math.pow(Math.abs(Math.sin(a)), n), -1 / n);
  }

  function canvasLoop(host, frame) {
    var canvas = document.createElement("canvas");
    var ctx = canvas.getContext("2d");
    var w = 0, h = 0, id = 0, last = 0, t = 0;
    host.appendChild(canvas);

    function resize() {
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function tick(now) {
      var dt = last ? Math.min((now - last) / 1000, 0.1) : 0;
      last = now;
      t += dt;
      ctx.clearRect(0, 0, w, h);
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      frame(ctx, w, h, reduced.matches ? -1 : t);
      if (!reduced.matches && !document.hidden) id = requestAnimationFrame(tick);
    }
    function start() {
      cancelAnimationFrame(id);
      last = 0;
      resize();
      tick(performance.now());
    }
    function onVisible() { if (!document.hidden) start(); }

    window.addEventListener("resize", start);
    document.addEventListener("visibilitychange", onVisible);
    reduced.addEventListener("change", start);
    start();
    return function () {
      cancelAnimationFrame(id);
      window.removeEventListener("resize", start);
      document.removeEventListener("visibilitychange", onVisible);
      reduced.removeEventListener("change", start);
    };
  }

  function nozzle(ctx, x, y, k) {
    ctx.fillStyle = rgba(LIME, 0.13);
    ctx.beginPath();
    ctx.arc(x, y, 6.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = rgba(LIME, k < 1 ? 0.7 : 0.88);
    ctx.beginPath();
    ctx.arc(x, y, 2.2, 0, Math.PI * 2);
    ctx.fill();
  }

  /* Gantry: the M3-CRETE frame seen from above, its rails at their M3-2 positions and proportions
     (millimetres, from the reference assembly). The X beam spans the long axis and moves front to back;
     the carriage rides it, tracing a double wall with a zig-zag truss, the usual printed-wall toolpath.
     Then the print fades and the carriage moves to the next plan shape. */
  function gantry(host) {
    var BUILD = 80, HOLD = 4, FADE = 5, CYCLE = BUILD + HOLD + FADE;
    // Plan extent: posts' outer faces.
    var FX0 = -40, FX1 = 2120, FY0 = -26, FY1 = 1066;
    // Fixed top frame: front and back rails, the two end beams and the center cross-bar.
    var RAILS = [[40, -26, 2040, 14], [40, 1026, 2040, 1066], [-40, 20, 40, 1020], [2040, 20, 2120, 1020],
      [1000, 20, 1080, 1020]];
    var POSTS = [[-40, -26], [2040, -26], [-40, 1026], [2040, 1026]];   // 80 x 40 each
    var GANTRY_X = [13, 2069];   // the X beam's carriages ride the end Y beams here
    var CX = 1040, CY = 520, WALL = 120, PITCH = 170, M = 220;
    var shapes = [{ n: 3, rx: 700, ry: 330 }, { n: 2, rx: 640, ry: 340 }, { n: 2.5, rx: 480, ry: 345 }];
    var cache = {};

    // Outer wall centreline, resampled to even spacing, with inward normals.
    function outline(sh) {
      var raw = [], len = [0], i, K = 720;
      for (i = 0; i <= K; i++) {
        var ang = (i / K) * Math.PI * 2 - Math.PI * 0.75;
        var r = superellipse(ang, sh.n);
        raw.push([CX + Math.cos(ang) * r * sh.rx, CY + Math.sin(ang) * r * sh.ry]);
        if (i) len.push(len[i - 1] + Math.hypot(raw[i][0] - raw[i - 1][0], raw[i][1] - raw[i - 1][1]));
      }
      var total = len[K], out = [], j = 1;
      for (i = 0; i <= M; i++) {
        var want = (i / M) * total;
        while (j < K && len[j] < want) j++;
        var f = (want - len[j - 1]) / (len[j] - len[j - 1] || 1);
        out.push([raw[j - 1][0] + (raw[j][0] - raw[j - 1][0]) * f, raw[j - 1][1] + (raw[j][1] - raw[j - 1][1]) * f]);
      }
      return out.map(function (p, i) {
        var a = out[i === 0 ? M - 1 : i - 1], b = out[i === M ? 1 : i + 1];
        var tx = b[0] - a[0], ty = b[1] - a[1], l = Math.hypot(tx, ty) || 1;
        var nx = -ty / l, ny = tx / l;
        if (nx * (CX - p[0]) + ny * (CY - p[1]) < 0) { nx = -nx; ny = -ny; }
        return [p[0], p[1], nx, ny, (i / M) * total];
      });
    }
    function toolpath(index) {
      if (cache[index]) return cache[index];
      var outer = outline(shapes[index]), pts = [], i;
      var teeth = Math.round(outer[M][4] / PITCH);
      function at(q, off) {
        var x = q * M, a = Math.min(Math.floor(x), M - 1), f = x - a, p = outer[a], b = outer[a + 1];
        return [p[0] + (b[0] - p[0]) * f + p[2] * off, p[1] + (b[1] - p[1]) * f + p[3] * off];
      }
      for (i = 0; i <= M; i++) pts.push([outer[i][0], outer[i][1]]);
      for (i = 0; i <= M; i++) pts.push([outer[i][0] + outer[i][2] * WALL, outer[i][1] + outer[i][3] * WALL]);
      for (i = 0; i <= teeth * 2; i++) pts.push(at(i / (teeth * 2), i % 2 ? WALL : 0));
      var len = [0];
      for (i = 1; i < pts.length; i++) {
        len.push(len[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
      }
      cache[index] = { pts: pts, len: len, total: len[len.length - 1] };
      return cache[index];
    }

    return canvasLoop(host, function (ctx, w, h, t) {
      if (t < 0) t = BUILD * 0.6;
      var small = w < 720, k = small ? 0.62 : 1;
      var index = Math.floor(t / CYCLE) % shapes.length;
      var path = toolpath(index);
      var next = toolpath((index + 1) % shapes.length);
      var phase = t % CYCLE;
      var FW = small ? w * 0.92 : Math.min(w * 0.5, h * 1.15);
      var S = FW / (FX1 - FX0), FH = (FY1 - FY0) * S;
      var X0 = (small ? w * 0.5 : w * 0.7) - FW / 2;
      var Y0 = (small ? h * 0.62 : h * 0.55) - FH / 2;
      function X(x) { return X0 + (x - FX0) * S; }
      function Y(y) { return Y0 + (y - FY0) * S; }
      function box(x0, y0, x1, y1, fill, line) {
        ctx.fillStyle = rgba(STEEL, fill * k);
        ctx.fillRect(X(x0), Y(y0), (x1 - x0) * S, (y1 - y0) * S);
        ctx.strokeStyle = rgba(STEEL, line * k);
        ctx.strokeRect(X(x0), Y(y0), (x1 - x0) * S, (y1 - y0) * S);
      }
      var fade = phase < BUILD + HOLD ? ease(phase / 2) : 1 - ease((phase - BUILD - HOLD) / FADE);

      // Floor: a sparse dot grid under the open-bottom frame.
      ctx.lineWidth = 1;
      ctx.fillStyle = rgba(STEEL, 0.1 * k);
      ctx.beginPath();
      for (var gx = 240; gx <= 1840; gx += 200) {
        for (var gy = 120; gy <= 920; gy += 200) {
          ctx.moveTo(X(gx) + 0.9, Y(gy));
          ctx.arc(X(gx), Y(gy), 0.9, 0, Math.PI * 2);
        }
      }
      ctx.fill();

      // Toolpath laid so far.
      var s = Math.min(phase / BUILD, 1) * path.total;
      var pts = path.pts, i = 1, head;
      var trail = new Path2D();
      trail.moveTo(X(pts[0][0]), Y(pts[0][1]));
      while (i < pts.length && path.len[i] <= s) { trail.lineTo(X(pts[i][0]), Y(pts[i][1])); i++; }
      if (i < pts.length) {
        var f = (s - path.len[i - 1]) / (path.len[i] - path.len[i - 1]);
        head = [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f];
        trail.lineTo(X(head[0]), Y(head[1]));
      } else {
        // Done: the carriage travels to the next start point while the print fades.
        var end = pts[pts.length - 1], start = next.pts[0];
        var m = ease((phase - BUILD) / (HOLD + FADE));
        head = [end[0] + (start[0] - end[0]) * m, end[1] + (start[1] - end[1]) * m];
      }
      ctx.lineWidth = 40 * S;
      ctx.strokeStyle = rgba(STEEL, 0.06 * k * fade);
      ctx.stroke(trail);
      ctx.lineWidth = 1;
      ctx.strokeStyle = rgba(STEEL, 0.22 * k * fade);
      ctx.stroke(trail);

      // X beam at the carriage, its two end carriages, then the fixed top frame over it.
      box(40, head[1] - 20, 2040, head[1] + 20, 0.03, 0.17);
      GANTRY_X.forEach(function (x) { box(x - 22, head[1] - 60, x + 22, head[1] + 60, 0.03, 0.22); });
      RAILS.forEach(function (r) { box(r[0], r[1], r[2], r[3], 0.022, 0.14); });
      POSTS.forEach(function (p) { box(p[0], p[1], p[0] + 80, p[1] + 40, 0.05, 0.22); });

      // Carriage and nozzle.
      var hx = X(head[0]), hy = Y(head[1]), c = 35 * S;
      ctx.strokeStyle = rgba(STEEL, 0.3 * k);
      ctx.strokeRect(hx - c, hy - c, c * 2, c * 2);
      nozzle(ctx, hx, hy, k);
    });
  }

  function mount(mode) {
    stop();
    stop = function () {};
    if (layer) layer.remove();
    layer = null;
    if (root.getAttribute("data-sdt-theme") !== "dark" || mode !== "gantry") return;
    layer = document.createElement("div");
    layer.className = "sdt-bg sdt-bg--gantry";
    layer.setAttribute("aria-hidden", "true");
    document.body.insertBefore(layer, document.body.firstChild);
    stop = gantry(layer);
  }

  window.sdtBg = { set: function (mode) { root.setAttribute("data-sdt-bg", mode); mount(mode); } };
  mount(root.getAttribute("data-sdt-bg"));
})();
