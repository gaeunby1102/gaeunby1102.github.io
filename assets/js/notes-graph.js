/* Obsidian-style force-directed graph of the Notes page.
   Reads the categorized note list from the DOM, so it stays in sync
   with the list automatically. No external libraries. */
(function () {
  var canvas = document.getElementById('notes-graph');
  if (!canvas || !canvas.getContext) return;
  var ctx = canvas.getContext('2d');

  // ---- palette (assigned per category, in order) ----
  var PALETTE = ['#e07a5f', '#3d9970', '#6a8cff', '#b56cd6', '#e0a800', '#ef6f9c',
                 '#00a3a3', '#d1495b'];

  // ---- theme colors ----
  function themeColors() {
    var cs = getComputedStyle(document.body);
    return {
      text: cs.color || '#333',
      link: getComputedStyle(document.documentElement).getPropertyValue('--border') || '#ccc',
      bg: cs.backgroundColor || '#fff'
    };
  }

  // ---- build graph from DOM ----
  var nodes = [], links = [], byId = {};
  function addNode(n) { nodes.push(n); byId[n.id] = n; return n; }

  function build() {
    nodes = []; links = []; byId = {};
    // Preferred: embedded data (used on the home page)
    if (window.NOTES_DATA && window.NOTES_DATA.length) {
      window.NOTES_DATA.forEach(function (cat, ci) {
        var color = PALETTE[ci % PALETTE.length];
        var catId = 'cat:' + ci;
        addNode({ id: catId, label: cat.category, url: cat.url || null,
                  color: color, isCat: true, r: 13,
                  x: cx() + rnd(120), y: cy() + rnd(120), vx: 0, vy: 0 });
        (cat.notes || []).forEach(function (n, k) {
          var nid = catId + ':' + k;
          addNode({ id: nid, label: n.label, url: n.url, color: color, isCat: false, r: 6.5,
                    x: cx() + rnd(160), y: cy() + rnd(160), vx: 0, vy: 0 });
          links.push({ s: catId, t: nid });
        });
      });
      return;
    }
    // Fallback: read the categorized list from the DOM (Notes page)
    var cats = document.querySelectorAll('.note-cat');
    var ci = 0;
    cats.forEach(function (h) {
      var color = PALETTE[ci % PALETTE.length];
      var catId = 'cat:' + ci;
      addNode({ id: catId, label: h.textContent.trim(), url: null,
                color: color, isCat: true, r: 13,
                x: cx() + rnd(120), y: cy() + rnd(120), vx: 0, vy: 0 });
      // notes belong to the ul immediately after the header
      var ul = h.nextElementSibling;
      while (ul && ul.tagName !== 'UL') ul = ul.nextElementSibling;
      if (ul) {
        ul.querySelectorAll('li > a').forEach(function (a, k) {
          var nid = catId + ':' + k;
          addNode({ id: nid, label: a.textContent.trim(), url: a.getAttribute('href'),
                    color: color, isCat: false, r: 6.5,
                    x: cx() + rnd(160), y: cy() + rnd(160), vx: 0, vy: 0 });
          links.push({ s: catId, t: nid });
        });
      }
      ci++;
    });
  }

  function rnd(m) { return (Math.random() - 0.5) * m; }
  function cx() { return canvas._w ? canvas._w / 2 : 300; }
  function cy() { return canvas._h ? canvas._h / 2 : 220; }

  // ---- sizing (devicePixelRatio aware) ----
  function resize() {
    var rect = canvas.getBoundingClientRect();
    var dpr = window.devicePixelRatio || 1;
    canvas._w = rect.width; canvas._h = rect.height;
    canvas.width = Math.round(rect.width * dpr);
    canvas.height = Math.round(rect.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  // ---- force simulation ----
  var alpha = 1;
  function tick() {
    var W = canvas._w, H = canvas._h;
    var kRep = 2600, kSpring = 0.02, rest = 74, center = 0.015;
    // repulsion
    for (var i = 0; i < nodes.length; i++) {
      var a = nodes[i];
      for (var j = i + 1; j < nodes.length; j++) {
        var b = nodes[j];
        var dx = a.x - b.x, dy = a.y - b.y;
        var d2 = dx * dx + dy * dy || 0.01;
        var d = Math.sqrt(d2);
        var f = (kRep * alpha) / d2;
        var fx = (dx / d) * f, fy = (dy / d) * f;
        a.vx += fx; a.vy += fy; b.vx -= fx; b.vy -= fy;
      }
    }
    // springs
    links.forEach(function (l) {
      var a = byId[l.s], b = byId[l.t];
      var dx = b.x - a.x, dy = b.y - a.y;
      var d = Math.sqrt(dx * dx + dy * dy) || 0.01;
      var f = kSpring * (d - rest) * alpha;
      var fx = (dx / d) * f, fy = (dy / d) * f;
      a.vx += fx; a.vy += fy; b.vx -= fx; b.vy -= fy;
    });
    // centering + integrate
    nodes.forEach(function (n) {
      if (n === dragging) return;
      n.vx += (W / 2 - n.x) * center * alpha;
      n.vy += (H / 2 - n.y) * center * alpha;
      n.vx *= 0.86; n.vy *= 0.86;
      n.x += n.vx; n.y += n.vy;
      var pad = n.r + 4;
      n.x = Math.max(pad, Math.min(W - pad, n.x));
      n.y = Math.max(pad, Math.min(H - pad, n.y));
    });
    if (alpha > 0.05) alpha *= 0.992;
  }

  // ---- draw ----
  var hover = null;
  function draw() {
    var C = themeColors();
    ctx.clearRect(0, 0, canvas._w, canvas._h);
    // links
    ctx.lineWidth = 1;
    links.forEach(function (l) {
      var a = byId[l.s], b = byId[l.t];
      var hot = hover && (hover === a || hover === b);
      ctx.strokeStyle = hot ? a.color : 'rgba(140,140,140,0.28)';
      ctx.globalAlpha = hot ? 0.8 : 1;
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    });
    ctx.globalAlpha = 1;
    // nodes
    nodes.forEach(function (n) {
      var hot = hover === n;
      ctx.beginPath();
      ctx.arc(n.x, n.y, hot ? n.r + 2 : n.r, 0, Math.PI * 2);
      ctx.fillStyle = n.color;
      ctx.fill();
      if (n.isCat) { ctx.lineWidth = 2; ctx.strokeStyle = C.bg; ctx.stroke(); }
    });
    // labels
    ctx.fillStyle = C.text;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    nodes.forEach(function (n) {
      var show = n.isCat || hover === n ||
                 (hover && links.some(function (l) {
                   return (l.s === hover.id && l.t === n.id) || (l.t === hover.id && l.s === n.id);
                 }));
      if (!show) return;
      ctx.font = (n.isCat ? '600 12px' : '11px') +
        ' -apple-system, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif';
      var t = n.label.length > 28 ? n.label.slice(0, 27) + '…' : n.label;
      ctx.fillText(t, n.x, n.y + n.r + 3);
    });
  }

  function loop() { tick(); draw(); requestAnimationFrame(loop); }

  // ---- interaction ----
  var dragging = null, downNode = null, downXY = null, moved = false;
  function pos(e) {
    var r = canvas.getBoundingClientRect();
    var t = e.touches ? e.touches[0] : e;
    return { x: t.clientX - r.left, y: t.clientY - r.top };
  }
  function pick(p) {
    for (var i = nodes.length - 1; i >= 0; i--) {
      var n = nodes[i], dx = p.x - n.x, dy = p.y - n.y;
      if (dx * dx + dy * dy <= (n.r + 5) * (n.r + 5)) return n;
    }
    return null;
  }
  function onMove(e) {
    var p = pos(e);
    if (dragging) {
      dragging.x = p.x; dragging.y = p.y; dragging.vx = 0; dragging.vy = 0;
      alpha = Math.max(alpha, 0.4); moved = true;
      e.preventDefault(); return;
    }
    hover = pick(p);
    canvas.style.cursor = hover ? 'pointer' : 'default';
  }
  function onDown(e) {
    var p = pos(e); downNode = pick(p); downXY = p; moved = false;
    if (downNode) { dragging = downNode; alpha = Math.max(alpha, 0.5); }
  }
  function onUp(e) {
    if (downNode && !moved && downNode.url) window.location.href = downNode.url;
    dragging = null; downNode = null;
  }
  canvas.addEventListener('mousemove', onMove);
  canvas.addEventListener('mousedown', onDown);
  window.addEventListener('mouseup', onUp);
  canvas.addEventListener('touchstart', onDown, { passive: true });
  canvas.addEventListener('touchmove', onMove, { passive: false });
  window.addEventListener('touchend', onUp);
  window.addEventListener('resize', function () { resize(); alpha = Math.max(alpha, 0.3); });

  // ---- go ----
  resize(); build();
  // spread initial positions in a circle for a nicer start
  nodes.forEach(function (n, i) {
    var ang = (i / nodes.length) * Math.PI * 2;
    n.x = cx() + Math.cos(ang) * 120 + rnd(20);
    n.y = cy() + Math.sin(ang) * 100 + rnd(20);
  });
  loop();
})();
