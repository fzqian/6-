/* 聊天记录文字版 · 复制
   长图里的字是像素，选不中；这一块是真 DOM，所以两件事要做：
     1. 拖选 —— 不用写代码，别拦着就行（不设 user-select:none，不绑 data-zoom 灯箱）
     2. 一键带走 —— 拼成「说话人：正文　〔①②〕」的纯文本进剪贴板

   报告是双击本地打开（file://），非安全上下文拿不到 navigator.clipboard，
   必须留 textarea + execCommand 兜底，再失败就自动选中提示 Ctrl+C。
   不引第三方库，不改 assets/app.js（多页共用、check.py 逐字节比对）。 */
(function () {
  'use strict';

  var CIRC = ['①', '②', '③', '④'];

  function execCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.cssText = 'position:fixed;top:0;left:-9999px;opacity:0;';
    document.body.appendChild(ta);
    ta.select();
    ta.setSelectionRange(0, text.length);
    var okk = false;
    try { okk = document.execCommand('copy'); } catch (e) { okk = false; }
    document.body.removeChild(ta);
    return okk;
  }

  function flash(btn, txt, cls) {
    var orig = btn.getAttribute('data-orig') || btn.textContent;
    btn.setAttribute('data-orig', orig);
    btn.textContent = txt;
    if (cls) btn.classList.add(cls);
    clearTimeout(btn._t);
    btn._t = setTimeout(function () {
      btn.textContent = orig;
      if (cls) btn.classList.remove(cls);
    }, 2000);
  }

  function crisp(k) {
    var out = '';
    for (var i = 0; i < k.length; i++) {
      var n = parseInt(k.charAt(i), 10);
      out += (n >= 1 && n <= 4) ? CIRC[n - 1] : k.charAt(i);
    }
    return out;
  }

  /* 拼纯文本：只取原文与说话人，标注带（解释性文字）不混进来，
     否则粘出去会插在两句对话中间，读起来像另一个人说的话。
     要点版（data-cc-plain="1"）连条尾的〔②〕也不加 —— 那一版是给销售
     照着念的，正文里多一个括号反而碍事，标号只在网页上看。 */
  function build(box) {
    var out = [];
    var plain = box.getAttribute('data-cc-plain') === '1';
    var head = box.getAttribute('data-cc-head');
    if (head) out.push(head.replace(/&amp;/g, '&').replace(/&quot;/g, '"'));

    var rows = box.querySelectorAll('.cl-body > *');
    [].forEach.call(rows, function (el) {
      if (el.classList.contains('cl-time')) {
        var t = el.textContent.trim();
        var sep = '—— ' + t + ' ——';
        /* 同一天连着出现两次时间条（说明带把一个上午切成几段）时只留一条 */
        if (t && out[out.length - 1] !== sep) { out.push(''); out.push(sep); }
      } else if (el.classList.contains('cl-msg')) {
        var x = el.querySelector('.cl-txt');
        if (!x) return;
        var ks = crisp(el.getAttribute('data-k') || '');
        out.push((el.getAttribute('data-who') || '') + '：' + x.textContent +
                 (!plain && ks ? '　〔' + ks + '〕' : ''));
      } else if (el.classList.contains('cl-note')) {
        out.push('');
        out.push(el.textContent.trim());
      } else if (el.classList.contains('cl-gap')) {
        out.push('');
        out.push('（' + el.textContent.trim() + '）');
      }
    });
    return out.join('\n');
  }

  /* 自检脚本用它验证「点复制拿到的 == 页面上印的原文」 */
  window.clBuildText = function (el) { return build(el); };

  function selectBody(box) {
    var body = box.querySelector('.cl-body');
    if (!body) return false;
    try {
      var r = document.createRange();
      r.selectNodeContents(body);
      var s = window.getSelection();
      s.removeAllRanges();
      s.addRange(r);
      return true;
    } catch (e) { return false; }
  }

  /* 一页两版时按钮没有固定目标：点「复制要点」要拿当前露出来的那一版。
     data-lcgrp 记着这一组，谁没 hidden 就是谁；没有 lcgrp 的（接通建联那块）照旧按 id 找。 */
  function boxOf(btn, attr) {
    var g = btn.getAttribute('data-lcgrp');
    if (g) {
      var panes = document.querySelectorAll('[data-clgrp="' + g + '"].cl-pane');
      for (var i = 0; i < panes.length; i++) {
        if (!panes[i].hidden) return panes[i];
      }
    }
    return document.getElementById(btn.getAttribute(attr));
  }

  [].forEach.call(document.querySelectorAll('[data-lc]'), function (btn) {
    btn.addEventListener('click', function () {
      var box = boxOf(btn, 'data-lc');
      if (!box) return;
      var text = build(box);
      if (!text) return;
      var n = 0, lines = text.split('\n');
      for (var i = 0; i < lines.length; i++) if (lines[i] && lines[i].indexOf('：') > 0) n++;
      function fail() {
        if (selectBody(box)) flash(btn, '已选中 · 按 Ctrl+C');
        else flash(btn, '复制失败，请拖选');
      }
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function () {
          flash(btn, '已复制 ' + n + ' 条 ✓', 'ok');
        }, function () {
          if (execCopy(text)) flash(btn, '已复制 ' + n + ' 条 ✓', 'ok');
          else fail();
        });
      } else if (execCopy(text)) {
        flash(btn, '已复制 ' + n + ' 条 ✓', 'ok');
      } else {
        fail();
      }
    });
  });

  [].forEach.call(document.querySelectorAll('[data-lcsel]'), function (btn) {
    btn.addEventListener('click', function () {
      var box = boxOf(btn, 'data-lcsel');
      if (!box) return;
      if (selectBody(box)) flash(btn, '已选中 · 按 Ctrl+C', 'ok');
      else flash(btn, '选中失败');
    });
  });

  /* 要点版 / 完整版切换：一组两个 pane，同时只露一个。
     切完要滚回顶部、重算底边渐隐 —— 否则从 40 条的完整版切到 8 条的要点版，
     滚动位置还停在半路，看起来像一片空白。工具栏那个复制按钮的文字也跟着换：
     在要点版上写着「复制全文」，粘出来却只有 8 条，会让人以为漏了。 */
  [].forEach.call(document.querySelectorAll('.cl-tabs'), function (tabs) {
    var btns = [].slice.call(tabs.querySelectorAll('.cl-tab'));
    var win = tabs.parentNode;
    if (!win) return;
    var wrap = win.parentNode;
    var tools = wrap && wrap.parentNode
      ? wrap.parentNode.querySelector('.cl-tools') : null;
    var cp = tools ? tools.querySelector('[data-lcgrp]') : null;

    function show(btn) {
      var id = btn.getAttribute('data-pane');
      var grp = btn.getAttribute('data-clgrp');
      var slim = /k$/.test(id);
      [].forEach.call(document.querySelectorAll('[data-clgrp="' + grp + '"].cl-pane'),
        function (p) { p.hidden = (p.id !== id); });
      btns.forEach(function (b) { b.classList.toggle('on', b === btn); });
      win.scrollTop = 0;
      if (cp) {
        var lbl = cp.getAttribute(slim ? 'data-lbl-slim' : 'data-lbl-full');
        if (lbl) {
          clearTimeout(cp._t);
          cp.classList.remove('ok');
          cp.textContent = lbl;
          cp.removeAttribute('data-orig');
        }
      }
      if (typeof win._clUpd === 'function') setTimeout(win._clUpd, 20);
    }

    btns.forEach(function (b) {
      b.addEventListener('click', function () { if (!b.classList.contains('on')) show(b); });
    });
  });

  /* 底边渐隐：收起时窗口能滚，最后一个气泡会被硬切，用一条渐变压住；
     滚到底（含「展开全部」后不再有滚动）就把渐变撤掉，否则最后一行永远看不清。 */
  [].forEach.call(document.querySelectorAll('.cclive .shotwin'), function (win) {
    var wrap = win.parentNode;
    if (!wrap || !/cl-wrap/.test(wrap.className)) return;
    function upd() {
      var atEnd = win.scrollTop + win.clientHeight >= win.scrollHeight - 6;
      wrap.classList.toggle('at-end', atEnd);
    }
    /* 切版之后内容高度变了，得让切换那一段能把它叫起来重算一次 */
    win._clUpd = upd;
    win.addEventListener('scroll', upd, { passive: true });
    window.addEventListener('resize', upd);
    var cb = wrap.parentNode.querySelector('.swchk');
    if (cb) cb.addEventListener('change', function () { setTimeout(upd, 30); });
    upd();
  });
})();
