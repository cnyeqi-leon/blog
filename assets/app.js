(function () {
  'use strict';
  var doc = document.documentElement;
  function $(s) { return document.querySelector(s); }
  function $$(s) { return Array.prototype.slice.call(document.querySelectorAll(s)); }

  /* ---------- 深浅色 ---------- */
  var themeBtn = $('#themeBtn');
  var themeColor = $('#themeColor');
  function currentTheme() { return doc.getAttribute('data-theme') === 'dark' ? 'dark' : 'light'; }
  function applyTheme(t, persist) {
    doc.setAttribute('data-theme', t);
    if (themeColor) themeColor.setAttribute('content', t === 'dark' ? '#000000' : '#ffffff');
    if (themeBtn) {
      var label = t === 'dark' ? '切换到浅色模式' : '切换到深色模式';
      themeBtn.setAttribute('aria-label', label);
      themeBtn.setAttribute('title', label);
      themeBtn.setAttribute('aria-pressed', t === 'dark' ? 'true' : 'false');
    }
    if (persist) { try { localStorage.setItem('theme', t); } catch (e) {} }
  }
  if (themeBtn) {
    applyTheme(currentTheme(), false);
    themeBtn.addEventListener('click', function () {
      applyTheme(currentTheme() === 'dark' ? 'light' : 'dark', true);
    });
    if (window.matchMedia) {
      var mq = window.matchMedia('(prefers-color-scheme: dark)');
      var onChange = function (e) {
        var saved = null;
        try { saved = localStorage.getItem('theme'); } catch (err) {}
        if (!saved) applyTheme(e.matches ? 'dark' : 'light', false);
      };
      if (mq.addEventListener) mq.addEventListener('change', onChange);
      else if (mq.addListener) mq.addListener(onChange);
    }
  }

  /* ---------- 轻提示 ---------- */
  var toastEl = $('#toast');
  var toastTimer = null;
  function toast(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add('on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('on'); }, 2200);
  }

  /* ---------- 互动按钮（纯前端，不接真实数据） ---------- */
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t || !t.closest) return;
    var like = t.closest('.act-like');
    if (like) {
      var liked = like.getAttribute('aria-pressed') === 'true';
      like.setAttribute('aria-pressed', liked ? 'false' : 'true');
      like.classList.toggle('liked', !liked);
      return;
    }
    var share = t.closest('.act-share');
    if (share) {
      var href = share.getAttribute('data-href') || '';
      var url = location.href;
      if (href) { try { url = new URL(href, location.href).href; } catch (err) {} }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(
          function () { toast('链接已复制'); },
          function () { toast(url); }
        );
      } else {
        toast(url);
      }
      return;
    }
    if (t.closest('.act-reply') || t.closest('.act-repost')) {
      toast('这里只做展示，没有接入互动数据');
    }
  });

  /* ---------- 时间线搜索 / 筛选 ---------- */
  var feed = $('#feed');
  if (!feed) return;
  var cards = $$('.post-card');
  var total = cards.length;
  var input = $('#q');
  var clearSearch = $('#qclear');
  var countEl = $('#count');
  var emptyEl = $('#empty');
  var emptyText = $('#emptyText');
  var filterBar = $('#filterBar');
  var filterText = $('#filterText');
  var clearFilter = $('#clearFilter');
  var month = '';

  function norm(s) { return (s || '').toLowerCase(); }
  function apply() {
    var q = norm(input ? input.value.trim() : '');
    var shown = 0;
    cards.forEach(function (card) {
      var okQ = !q || norm(card.getAttribute('data-search')).indexOf(q) !== -1;
      var okM = !month || (card.getAttribute('data-date') || '').indexOf(month) === 0;
      var show = okQ && okM;
      card.hidden = !show;
      if (show) shown++;
    });
    if (countEl) countEl.textContent = '共 ' + total + ' 条';
    if (emptyEl) emptyEl.hidden = shown > 0;
    if (emptyText && shown === 0) {
      emptyText.textContent = total ? '没有找到匹配的帖子，换个关键词试试。' : '这里还没有帖子。';
    }
    if (filterBar) filterBar.hidden = !(q || month);
    if (filterText && (q || month)) {
      var parts = [];
      if (q) parts.push('关键词「' + input.value.trim() + '」');
      if (month) parts.push('归档 ' + month.replace('-', ' 年 ') + ' 月');
      filterText.textContent = '筛选：' + parts.join(' · ') + ' → ' + shown + ' 条';
    }
    if (clearSearch) clearSearch.hidden = !q;
  }

  if (input) input.addEventListener('input', apply);
  if (clearSearch) clearSearch.addEventListener('click', function () {
    if (input) { input.value = ''; input.focus(); }
    apply();
  });
  if (clearFilter) clearFilter.addEventListener('click', function () {
    month = '';
    if (input) input.value = '';
    apply();
  });

  feed.addEventListener('click', function (e) {
    var tag = e.target && e.target.closest ? e.target.closest('[data-tag]') : null;
    if (!tag) return;
    if (input) input.value = tag.getAttribute('data-tag') || '';
    month = '';
    apply();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  $$('[data-side-tag]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (input) input.value = btn.getAttribute('data-side-tag') || '';
      month = '';
      apply();
    });
  });
  $$('[data-side-month]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      month = btn.getAttribute('data-side-month') || '';
      apply();
    });
  });

  var params = new URLSearchParams(location.search);
  var tagParam = params.get('tag');
  var monthParam = params.get('month');
  if (tagParam && input) input.value = tagParam;
  if (monthParam) month = monthParam;
  apply();
})();
