(function () {
  'use strict';

  /* ---------- 顶部进度条 ---------- */
  var prog = document.querySelector('.nav-progress');
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    var p = max > 0 ? (h.scrollTop / max) * 100 : 0;
    if (prog) prog.style.width = p + '%';
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- 导航高亮 ---------- */
  var links = [].slice.call(document.querySelectorAll('.nav-links a'));
  var secs = links.map(function (a) {
    return document.querySelector(a.getAttribute('href'));
  }).filter(Boolean);

  function markActive() {
    var y = window.scrollY + 120;
    var idx = 0;
    secs.forEach(function (s, i) { if (s.offsetTop <= y) idx = i; });
    links.forEach(function (a, i) { a.classList.toggle('on', i === idx); });
  }
  window.addEventListener('scroll', markActive, { passive: true });
  markActive();

  /* ---------- 问题点展开 ---------- */
  document.querySelectorAll('.pcard-h').forEach(function (h) {
    h.addEventListener('click', function () {
      var card = h.parentNode;
      card.classList.toggle('open');
    });
  });

  var toggleAll = document.getElementById('toggleAll');
  if (toggleAll) {
    toggleAll.addEventListener('click', function () {
      var cards = [].slice.call(document.querySelectorAll('.pcard'));
      var allOpen = cards.every(function (c) { return c.classList.contains('open'); });
      cards.forEach(function (c) { c.classList.toggle('open', !allOpen); });
      toggleAll.textContent = allOpen ? '全部展开' : '全部收起';
    });
  }

  /* ---------- 明细表筛选 ---------- */
  var fbtns = [].slice.call(document.querySelectorAll('.fbtn'));
  var rows = [].slice.call(document.querySelectorAll('#stageTable tbody tr'));
  var search = document.getElementById('tblSearch');
  var empty = document.getElementById('tblEmpty');
  var cur = 'all';

  function applyFilter() {
    var q = (search && search.value || '').trim().toLowerCase();
    var shown = 0;
    rows.forEach(function (tr) {
      var okStage = cur === 'all' || tr.getAttribute('data-top') === cur;
      var okText = !q || tr.textContent.toLowerCase().indexOf(q) >= 0;
      var ok = okStage && okText;
      tr.style.display = ok ? '' : 'none';
      if (ok) shown++;
    });
    if (empty) empty.style.display = shown ? 'none' : 'block';
  }

  fbtns.forEach(function (b) {
    b.addEventListener('click', function () {
      fbtns.forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      cur = b.getAttribute('data-f');
      applyFilter();
    });
  });
  if (search) search.addEventListener('input', applyFilter);

  /* ---------- 灯箱：原尺寸显示 + 滚轮缩放 + 拖动平移 ---------- */
  var lb = document.getElementById('lb');
  var lbImg = document.getElementById('lbImg');
  var lbCap = document.getElementById('lbCap');

  var ZMIN = 0.4, ZMAX = 6;
  var zs = 1, tx = 0, ty = 0, t0 = 0, bW = 0, bH = 0;
  var zhint = null, zval = null, drag = null, dragged = false;

  function clampNum(v, a, b) { return v < a ? a : (v > b ? b : v); }

  function paint() {
    lbImg.style.transform =
      'translate3d(' + tx.toFixed(2) + 'px,' + ty.toFixed(2) + 'px,0) scale(' + zs.toFixed(4) + ')';
    if (zval) zval.textContent = Math.round(zs * 100) + '%';
  }

  /* 图片按原始像素显示（1:1），超出视口的部分靠拖动查看 */
  function fit() {
    if (!lbImg.naturalWidth) return;
    lbImg.style.maxWidth = 'none';
    lbImg.style.maxHeight = 'none';
    lbImg.style.height = 'auto';
    var availW = Math.max(120, lb.clientWidth - 68);
    var availH = Math.max(120, lb.clientHeight - 68);
    var w = Math.min(lbImg.naturalWidth, availW);
    bW = w;
    bH = w * lbImg.naturalHeight / lbImg.naturalWidth;
    lbImg.style.width = w + 'px';
    /* 长图默认从顶部开始看，而不是居中裁掉一半 */
    t0 = bH > availH ? (bH - availH) / 2 : 0;
    resetView();
  }

  function resetView() {
    zs = 1; tx = 0; ty = t0;
    paint();
  }

  /* 以 (mx,my) 为锚点缩放：鼠标下的那一点保持不动 */
  function zoomAt(s2, mx, my) {
    s2 = clampNum(s2, ZMIN, ZMAX);
    if (Math.abs(s2 - zs) < 1e-6) return;
    var r = lbImg.getBoundingClientRect();
    var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    var k = s2 / zs;
    var lx = cx - tx, ly = cy - ty;          /* 布局中心（不含 transform） */
    tx = mx - (mx - cx) * k - lx;
    ty = my - (my - cy) * k - ly;
    zs = s2;
    paint();
  }

  function openLb(src, cap) {
    lbImg.src = src;
    if (lbCap) lbCap.textContent = cap || '';
    lb.classList.add('on');
    document.body.style.overflow = 'hidden';
    if (lbImg.complete && lbImg.naturalWidth) fit();
    else lbImg.onload = fit;
  }

  function closeLb() {
    lb.classList.remove('on');
    document.body.style.overflow = '';
  }

  if (lb && lbImg) {
    zhint = document.createElement('div');
    zhint.style.cssText = 'position:absolute;top:20px;left:22px;z-index:6;' +
      'color:rgba(255,255,255,.72);font-size:12.5px;line-height:1.4;pointer-events:none;' +
      'letter-spacing:.2px;background:rgba(12,18,26,.62);padding:7px 14px;border-radius:999px;' +
      'backdrop-filter:blur(4px);';
    zhint.innerHTML = '滚轮缩放 · 拖动平移 · 双击复位 · 点背景或 Esc 关闭' +
      '　<b style="color:#fff;font-variant-numeric:tabular-nums;">100%</b>';
    lb.appendChild(zhint);
    zval = zhint.querySelector('b');
    lbImg.style.cursor = 'grab';

    /* 图注浮在图片之上，加胶囊底避免压在浅色气泡上看不清 */
    if (lbCap) {
      lbCap.style.zIndex = '5';
      lbCap.style.left = '50%';
      lbCap.style.right = 'auto';
      lbCap.style.transform = 'translateX(-50%)';
      lbCap.style.maxWidth = 'min(78vw, 900px)';
      lbCap.style.background = 'rgba(12,18,26,.72)';
      lbCap.style.color = 'rgba(255,255,255,.9)';
      lbCap.style.padding = '8px 18px';
      lbCap.style.borderRadius = '999px';
      lbCap.style.lineHeight = '1.55';
      lbCap.style.backdropFilter = 'blur(4px)';
    }

    document.addEventListener('click', function (e) {
      var t = e.target.closest ? e.target.closest('[data-zoom]') : null;
      if (!t) return;
      var img = t.querySelector('img');
      if (!img) return;
      openLb(img.src, t.getAttribute('data-zoom'));
    });

    lb.addEventListener('wheel', function (e) {
      if (!lb.classList.contains('on')) return;
      e.preventDefault();
      var d = e.deltaY;
      if (e.deltaMode === 1) d *= 16; else if (e.deltaMode === 2) d *= 100;
      zoomAt(zs * Math.exp(-d * 0.0016), e.clientX, e.clientY);
    }, { passive: false });

    lbImg.addEventListener('pointerdown', function (e) {
      if (e.pointerType === 'mouse' && e.button !== 0) return;
      drag = { x: e.clientX, y: e.clientY, tx: tx, ty: ty };
      dragged = false;
      lbImg.style.cursor = 'grabbing';
      /* 触摸端不拦默认行为，保留浏览器原生双指缩放 */
      if (e.pointerType === 'mouse') e.preventDefault();
    });
    window.addEventListener('pointermove', function (e) {
      if (!drag) return;
      var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (Math.abs(dx) + Math.abs(dy) > 4) dragged = true;
      tx = drag.tx + dx;
      ty = drag.ty + dy;
      paint();
    });
    window.addEventListener('pointerup', function () {
      if (!drag) return;
      drag = null;
      lbImg.style.cursor = 'grab';
    });

    lbImg.addEventListener('dblclick', function (e) {
      e.stopPropagation();
      if (zs > 1.02) resetView();
      else zoomAt(2, e.clientX, e.clientY);
    });

    lb.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('.lb-close')) { closeLb(); return; }
      if (dragged) { dragged = false; return; }   /* 拖完松手不算点击 */
      if (e.target === lb) closeLb();             /* 只点背景才关 */
    });

    document.addEventListener('keydown', function (e) {
      if (!lb.classList.contains('on')) return;
      var k = e.key;
      if (k === 'Escape') { closeLb(); return; }
      var mx = window.innerWidth / 2, my = window.innerHeight / 2;
      if (k === '+' || k === '=') { e.preventDefault(); zoomAt(zs * 1.25, mx, my); }
      else if (k === '-' || k === '_') { e.preventDefault(); zoomAt(zs / 1.25, mx, my); }
      else if (k === '0') { e.preventDefault(); resetView(); }
    });
  }

  /* ---------- 表格内阶段筛选联动 ---------- */
  document.querySelectorAll('[data-jump]').forEach(function (el) {
    el.addEventListener('click', function () {
      var f = el.getAttribute('data-jump');
      var btn = document.querySelector('.fbtn[data-f="' + f + '"]');
      if (btn) btn.click();
      document.getElementById('stageTable').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
})();
