// 受験英語 完全攻略ノート — 共通スクリプト
// ・表示範囲フィルタ（必須／必須＋差がつく／すべて）
// ・「理解した」チェック（チェックした項目は隠す。元に戻せる）
// ・経験値・レベル・トロフィー・連続日数（記録ページに表示）
// 状態はこの端末のブラウザ(localStorage)にだけ保存する。保存できない環境でも表示は壊れない。
(function () {
  'use strict';

  /* ---------- 保存 ---------- */
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
    remove: function (k) { try { localStorage.removeItem(k); } catch (e) {} }
  };
  function jget(k, fb) { try { var v = store.get(k); return v ? JSON.parse(v) : fb; } catch (e) { return fb; } }
  function jset(k, v) { store.set(k, JSON.stringify(v)); }

  /* ---------- 定義 ---------- */
  var ITEMS = window.EIKO_ITEMS || [];
  var PAGES = window.EIKO_PAGES || {};
  var XP = { must: 10, core: 20, skip: 5 };
  var QUIZ_XP = 5;
  var LEVEL_NAMES = ['はじめの一歩', '記号ウォッチャー', '骨組みハンター', '節の探検家', '論理ナビゲーター', '構文コレクター', '長文ランナー', '得点アップの達人', '読解の職人', '受験英語マスター'];
  // 必要経験値は「必須＋差がつく＋確認問題」の合計に対する割合で決める（項目が増えても、レベルの難しさが変わらない）
  var LEVEL_FRACS = [0, 0.01, 0.035, 0.08, 0.15, 0.25, 0.38, 0.53, 0.70, 0.90];
  function buildLevels() {
    var quizTotal = 0, maxXp = 0;
    Object.keys(PAGES).forEach(function (p) { quizTotal += PAGES[p].quizzes || 0; });
    ITEMS.forEach(function (it) { if (it.tier !== 'skip') maxXp += XP[it.tier]; });
    maxXp += quizTotal * QUIZ_XP;
    if (maxXp < 100) maxXp = 1000;
    return LEVEL_NAMES.map(function (n, i) { return { xp: Math.round(maxXp * LEVEL_FRACS[i] / 5) * 5, name: n }; });
  }
  var LEVELS = buildLevels();

  function mustDone(page) {
    return function (s) { var p = s.byPage[page]; return !!p && p.must.t > 0 && p.must.d === p.must.t; };
  }
  function mustDoneGroup(match) {
    return function (s) {
      var d = 0, t = 0;
      Object.keys(s.byPage).forEach(function (p) { if (match(p)) { d += s.byPage[p].must.d; t += s.byPage[p].must.t; } });
      return t > 0 && d === t;
    };
  }
  var TROPHIES = [
    { id: 'first', icon: '🌱', name: '最初の一歩', desc: 'はじめて項目を「理解した」にする', test: function (s) { return s.done >= 1; } },
    { id: 'n5', icon: '⭐', name: '5項目クリア', desc: '5項目を理解した', test: function (s) { return s.done >= 5; } },
    { id: 'n10', icon: '🌟', name: '10項目クリア', desc: '10項目を理解した', test: function (s) { return s.done >= 10; } },
    { id: 'n25', icon: '💫', name: '25項目クリア', desc: '25項目を理解した', test: function (s) { return s.done >= 25; } },
    { id: 'n50', icon: '✨', name: '50項目クリア', desc: '50項目を理解した', test: function (s) { return s.done >= 50; } },
    { id: 'n100', icon: '🎖️', name: '100項目クリア', desc: '100項目を理解した', test: function (s) { return s.done >= 100; } },
    { id: 'n150', icon: '🥇', name: '150項目クリア', desc: '150項目を理解した', test: function (s) { return s.done >= 150; } },
    { id: 'must-symbols', icon: '✍️', name: '記号マスター', desc: '「記号」の必須をすべて理解した', test: mustDone('symbols.html') },
    { id: 'must-grammar', icon: '📘', name: '文法マスター', desc: '「文法」の必須をすべて理解した', test: mustDone('grammar.html') },
    { id: 'must-order', icon: '🔀', name: '語順の達人', desc: '「語順・特殊な構造」の必須をすべて理解した', test: mustDone('p-order.html') },
    { id: 'must-modifier', icon: '🔗', name: '修飾ハンター', desc: '「修飾」の必須をすべて理解した', test: mustDone('p-modifier.html') },
    { id: 'must-clause', icon: '🧱', name: '節の建築士', desc: '「節・接続表現」の必須をすべて理解した', test: mustDone('p-clause.html') },
    { id: 'must-verbal', icon: '🔧', name: '準動詞マスター', desc: '「準動詞」の必須をすべて理解した', test: mustDone('p-verbal.html') },
    { id: 'must-compare', icon: '⚖️', name: '比較の名人', desc: '「比較」の必須をすべて理解した', test: mustDone('p-compare.html') },
    { id: 'must-negation', icon: '🚫', name: '否定の見張り番', desc: '「否定」の必須をすべて理解した', test: mustDone('p-negation.html') },
    { id: 'must-subj', icon: '💭', name: '仮定法の魔術師', desc: '「仮定法・助動詞」の必須をすべて理解した', test: mustDone('p-subjunctive.html') },
    { id: 'must-verbs', icon: '🧭', name: '語法の職人', desc: '「動詞の型・語法」の必須をすべて理解した', test: mustDone('p-verbs.html') },
    { id: 'must-patterns', icon: '🧩', name: '構文コンプリート', desc: '構文ライブラリの必須をすべて理解した', test: mustDoneGroup(function (p) { return p.indexOf('p-') === 0; }) },
    { id: 'must-before', icon: '🧭', name: '長文準備完了', desc: '「長文の前に」の必須をすべて理解した', test: mustDone('before-reading.html') },
    { id: 'must-score', icon: '🎯', name: '得点のコツ習得', desc: '「得点のコツ」の必須をすべて理解した', test: mustDone('score-tips.html') },
    { id: 'all-must', icon: '🏅', name: '必須コンプリート', desc: 'すべてのページの必須を理解した', test: function (s) { return s.byTier.must.t > 0 && s.byTier.must.d === s.byTier.must.t; } },
    { id: 'all-core', icon: '🏆', name: '差がつく制覇', desc: '必須と「差がつく」をすべて理解した', test: function (s) { return s.byTier.must.t > 0 && s.byTier.must.d === s.byTier.must.t && s.byTier.core.d === s.byTier.core.t; } },
    { id: 'quiz1', icon: '📝', name: '確認問題デビュー', desc: '確認問題を1問開いた', test: function (s) { return s.quizDone >= 1; } },
    { id: 'quiz10', icon: '🧠', name: '10問チャレンジ', desc: '確認問題を10問開いた', test: function (s) { return s.quizDone >= 10; } },
    { id: 'quizall', icon: '💯', name: '確認問題コンプリート', desc: 'すべての確認問題を開いた', test: function (s) { return s.quizTotal > 0 && s.quizDone >= s.quizTotal; } },
    { id: 'streak3', icon: '🔥', name: '3日連続', desc: '3日連続で学習した', test: function (s) { return s.streak.best >= 3; } },
    { id: 'streak7', icon: '☄️', name: '7日連続', desc: '7日連続で学習した', test: function (s) { return s.streak.best >= 7; } },
    { id: 'skip', icon: '✂️', name: '線引きを知る', desc: '「不要リスト」を見た', test: function (s) { return s.visitedSkip; } },
    { id: 'lv5', icon: '🚀', name: 'レベル5到達', desc: 'レベル5に到達した', test: function (s) { return s.level >= 5; } },
    { id: 'lv10', icon: '👑', name: 'レベル10到達', desc: 'レベル10に到達した', test: function (s) { return s.level >= 10; } }
  ];

  function pageFile() { var p = location.pathname.split('/').pop(); return p || 'index.html'; }

  /* ---------- 日付・連続日数 ---------- */
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function fmt(d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); }
  function dayNum(s) { var a = s.split('-'); return Math.round(Date.UTC(+a[0], +a[1] - 1, +a[2]) / 86400000); }
  function daysList() { return jget('eiko:days', []); }
  function recordDay() {
    var d = daysList(), t = fmt(new Date());
    if (d.indexOf(t) < 0) { d.push(t); jset('eiko:days', d); }
  }
  function streaks() {
    var d = daysList().slice().sort(), set = {}, best = 0, run = 0, prev = null;
    d.forEach(function (x) { set[x] = 1; });
    d.forEach(function (x) {
      run = (prev && dayNum(x) - dayNum(prev) === 1) ? run + 1 : 1;
      if (run > best) best = run;
      prev = x;
    });
    var cur = 0, cursor = new Date();
    if (!set[fmt(cursor)]) cursor.setDate(cursor.getDate() - 1);
    while (set[fmt(cursor)]) { cur++; cursor.setDate(cursor.getDate() - 1); }
    return { current: cur, best: best };
  }

  /* ---------- 状態の計算 ---------- */
  function isDone(id) { return store.get('eiko:done:' + id) === '1'; }
  function compute() {
    var s = { done: 0, total: ITEMS.length, xp: 0, byPage: {}, byTier: { must: { d: 0, t: 0 }, core: { d: 0, t: 0 }, skip: { d: 0, t: 0 } } };
    Object.keys(PAGES).forEach(function (p) {
      s.byPage[p] = { must: { d: 0, t: 0 }, core: { d: 0, t: 0 }, skip: { d: 0, t: 0 } };
    });
    ITEMS.forEach(function (it) {
      var bp = s.byPage[it.page];
      if (!bp) return;
      bp[it.tier].t++; s.byTier[it.tier].t++;
      if (isDone(it.id)) { bp[it.tier].d++; s.byTier[it.tier].d++; s.done++; s.xp += XP[it.tier]; }
    });
    s.quizTotal = 0;
    Object.keys(PAGES).forEach(function (p) { s.quizTotal += PAGES[p].quizzes || 0; });
    s.quizDone = Math.min(Object.keys(jget('eiko:quiz', {})).length, s.quizTotal);
    s.xp += s.quizDone * QUIZ_XP;
    var lv = 0;
    for (var i = 0; i < LEVELS.length; i++) if (s.xp >= LEVELS[i].xp) lv = i;
    s.level = lv + 1;
    s.levelName = LEVELS[lv].name;
    s.curXp = LEVELS[lv].xp;
    s.nextXp = lv + 1 < LEVELS.length ? LEVELS[lv + 1].xp : null;
    s.streak = streaks();
    s.visitedSkip = store.get('eiko:visit:skip') === '1';
    return s;
  }

  /* ---------- トースト・紙吹雪 ---------- */
  var toastBox = null;
  function toast(o) {
    if (!toastBox) {
      toastBox = document.createElement('div');
      toastBox.className = 'toasts';
      toastBox.setAttribute('role', 'status');
      toastBox.setAttribute('aria-live', 'polite');
      document.body.appendChild(toastBox);
    }
    var el = document.createElement('div');
    el.className = 'toast ' + (o.cls || '');
    var msg = document.createElement('span');
    msg.className = 'msg';
    msg.textContent = o.text;
    el.appendChild(msg);
    function remove() { if (el.parentNode) el.parentNode.removeChild(el); }
    if (o.action) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = o.action;
      b.addEventListener('click', function () { if (o.onAction) o.onAction(); remove(); });
      el.appendChild(b);
    }
    toastBox.appendChild(el);
    setTimeout(remove, o.ms || 4500);
  }
  function celebrate() {
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var box = document.createElement('div');
    box.className = 'confetti';
    box.setAttribute('aria-hidden', 'true');
    var colors = ['#a6392a', '#a17a2e', '#3a7a4e', '#4a6fa5', '#c07a2b'];
    for (var i = 0; i < 28; i++) {
      var p = document.createElement('i');
      p.style.left = (Math.random() * 100) + '%';
      p.style.background = colors[i % colors.length];
      p.style.animationDelay = (Math.random() * 0.4) + 's';
      p.style.animationDuration = (1.4 + Math.random() * 1.2) + 's';
      box.appendChild(p);
    }
    document.body.appendChild(box);
    setTimeout(function () { if (box.parentNode) box.parentNode.removeChild(box); }, 3300);
  }

  /* ---------- レベル・トロフィー ---------- */
  function checkAwards(s, announce) {
    var got = jget('eiko:trophies', {}), fresh = [];
    TROPHIES.forEach(function (t) {
      if (!got[t.id] && t.test(s)) { got[t.id] = Date.now(); fresh.push(t); }
    });
    if (fresh.length) {
      jset('eiko:trophies', got);
      if (announce) {
        if (fresh.length <= 2) {
          fresh.forEach(function (t) { toast({ text: t.icon + ' トロフィー獲得：' + t.name, cls: 'award', ms: 5500 }); });
        } else {
          toast({ text: '🏆 トロフィーを' + fresh.length + '個獲得しました（記録ページで確認）', cls: 'award', ms: 5500 });
        }
        celebrate();
      }
    }
    return got;
  }
  function checkLevel(s, announce) {
    var last = store.get('eiko:lastLevel');
    if (last === null) { store.set('eiko:lastLevel', String(s.level)); return; }
    if (s.level > parseInt(last, 10)) {
      store.set('eiko:lastLevel', String(s.level));
      if (announce) {
        toast({ text: '🎉 レベルアップ！ Lv.' + s.level + '「' + s.levelName + '」', cls: 'levelup', ms: 6000 });
        celebrate();
      }
    }
  }

  /* ---------- ヘッダーのバッジ ---------- */
  var badge = null;
  function mountBadge() {
    var wrap = document.querySelector('.site-head .wrap');
    if (!wrap) return;
    badge = document.createElement('a');
    badge.className = 'lv-badge';
    badge.href = 'progress.html';
    badge.innerHTML = '<span class="lv-n"></span><span class="lv-bar"><i></i></span>';
    var nav = wrap.querySelector('.nav');
    wrap.insertBefore(badge, nav);
  }
  function paintBadge(s) {
    if (!badge) return;
    badge.querySelector('.lv-n').textContent = 'Lv.' + s.level + '　' + s.xp + ' XP';
    var pct = s.nextXp ? (s.xp - s.curXp) / (s.nextXp - s.curXp) * 100 : 100;
    badge.querySelector('i').style.width = Math.min(100, Math.max(0, pct)) + '%';
    badge.title = s.levelName + (s.nextXp ? '（次のレベルまで ' + (s.nextXp - s.xp) + ' XP）' : '（最高レベル）');
  }

  /* ---------- ページ内の表示 ---------- */
  var body = document.body;
  var mode = store.get('eiko:mode');
  if (mode !== 'must' && mode !== 'core' && mode !== 'all') mode = 'core';
  body.setAttribute('data-mode', mode);
  var hideDone = store.get('eiko:hideDone') !== '0';
  body.setAttribute('data-hide-done', hideDone ? '1' : '0');

  var filter = document.querySelector('.filter');
  var progEl = document.getElementById('prog');
  var buttons = document.querySelectorAll('.filter button[data-mode]');
  var hdBtn = null, emptyMsg = null;
  var hasItems = !!document.querySelector('.item');

  if (filter && hasItems) {
    hdBtn = document.createElement('button');
    hdBtn.type = 'button';
    hdBtn.className = 'hd';
    hdBtn.addEventListener('click', function () {
      hideDone = !hideDone;
      store.set('eiko:hideDone', hideDone ? '1' : '0');
      body.setAttribute('data-hide-done', hideDone ? '1' : '0');
      paintPage();
    });
    filter.insertBefore(hdBtn, progEl);

    emptyMsg = document.createElement('div');
    emptyMsg.className = 'empty-msg';
    emptyMsg.hidden = true;
    emptyMsg.innerHTML = '<b>この範囲の項目は、すべて完了しました。</b><br><span>ボタンで範囲を広げるか、完了した項目を表示して見直せます。</span>';
    var tb = document.querySelector('.toolbar');
    tb.parentNode.insertBefore(emptyMsg, tb.nextSibling);
  }

  document.querySelectorAll('.item h3').forEach(function (h, i) {
    h.setAttribute('data-no', (i + 1 < 10 ? '0' : '') + (i + 1));
  });

  function inMode(tier) {
    var m = body.getAttribute('data-mode');
    if (m === 'must') return tier === 'must';
    if (m === 'core') return tier !== 'skip';
    return true;
  }
  function paintPage() {
    buttons.forEach(function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-mode') === body.getAttribute('data-mode') ? 'true' : 'false');
    });
    if (!hasItems) return;
    var total = 0, done = 0, shown = 0;
    document.querySelectorAll('.item').forEach(function (it) {
      var t = it.getAttribute('data-tier');
      if (!inMode(t)) return;
      total++;
      var isD = it.classList.contains('is-done');
      if (isD) done++;
      if (!(hideDone && isD)) shown++;
    });
    if (progEl) progEl.textContent = '理解した ' + done + ' / ' + total;
    if (hdBtn) {
      hdBtn.textContent = '完了を隠す' + (done ? '（' + done + '）' : '');
      hdBtn.setAttribute('aria-pressed', hideDone ? 'true' : 'false');
    }
    if (emptyMsg) emptyMsg.hidden = !(total > 0 && shown === 0);
  }

  buttons.forEach(function (b) {
    b.addEventListener('click', function () {
      body.setAttribute('data-mode', b.getAttribute('data-mode'));
      store.set('eiko:mode', b.getAttribute('data-mode'));
      paintPage();
    });
  });

  function paintMap(s) {
    document.querySelectorAll('.mchip[data-id]').forEach(function (c) {
      c.classList.toggle('done', isDone(c.getAttribute('data-id')));
    });
    document.querySelectorAll('.mcat[data-page]').forEach(function (c) {
      var b = s.byPage[c.getAttribute('data-page')], el = c.querySelector('.mprog');
      if (!b || !el) return;
      var d = b.must.d + b.core.d + b.skip.d, tt = b.must.t + b.core.t + b.skip.t;
      el.textContent = '必須 ' + b.must.d + '/' + b.must.t + '　全体 ' + d + '/' + tt;
    });
  }

  function paintCards(s) {
    document.querySelectorAll('.pcard[data-page]').forEach(function (c) {
      var b = s.byPage[c.getAttribute('data-page')];
      var el = c.querySelector('.pcard-prog');
      if (!b || !el) return;
      var d = b.must.d + b.core.d, t = b.must.t + b.core.t;
      var pct = t ? Math.round(d / t * 100) : 0;
      el.innerHTML = '<span class="pbar"><i style="width:' + pct + '%"></i></span><span class="pnum">必須 ' + b.must.d + '/' + b.must.t + '　差がつく ' + b.core.d + '/' + b.core.t + '</span>';
    });
  }

  function refresh(announce) {
    var s = compute();
    paintBadge(s);
    paintCards(s);
    paintPage();
    paintToc();
    paintTocPage();
    paintMap(s);
    checkLevel(s, announce);
    checkAwards(s, announce);
    if (progressRoot) renderProgress(s);
  }

  /* チェックボックス */
  document.querySelectorAll('input[data-id]').forEach(function (box) {
    var key = 'eiko:done:' + box.getAttribute('data-id');
    var item = box.closest('.item');
    if (store.get(key) === '1') { box.checked = true; item.classList.add('is-done'); }
    box.addEventListener('change', function () {
      var checked = box.checked;
      store.set(key, checked ? '1' : '0');
      item.classList.toggle('is-done', checked);
      if (checked) {
        recordDay();
        if (hideDone) {
          var h = item.querySelector('h3');
          toast({
            text: '「' + (h ? h.textContent : '項目') + '」を完了にしました',
            action: '元に戻す',
            onAction: function () { box.checked = false; box.dispatchEvent(new Event('change')); },
            ms: 6000
          });
        }
      }
      refresh(true);
    });
  });

  /* 確認問題（開いた数を数える） */
  document.querySelectorAll('details.q').forEach(function (d, i) {
    var key = pageFile() + ':' + i;
    d.addEventListener('toggle', function () {
      if (!d.open) return;
      var m = jget('eiko:quiz', {});
      if (m[key]) return;
      m[key] = 1;
      jset('eiko:quiz', m);
      recordDay();
      refresh(true);
    });
  });

  if (pageFile() === 'skip-list.html') store.set('eiko:visit:skip', '1');


  /* ---------- 目次（ページ内）・全体目次ページ ---------- */
  var TIER_SHORT = { must: '必須', core: '差がつく', skip: '不要' };
  var tocEl = null;
  function esc(t) { var d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
  function buildToc() {
    var main = document.querySelector('main');
    if (!main || !hasItems) return;
    var anchorNode = main.querySelector('.toolbar') || main.querySelector('.lead');
    if (!anchorNode) return;
    var quiz = main.querySelector('.quiz');
    if (quiz && !quiz.id) quiz.id = 'quiz';
    var html = '', n = 0, open = false;
    main.querySelectorAll('h2, .item').forEach(function (el) {
      if (el.closest('.quiz')) return;
      if (el.tagName === 'H2') {
        if (open) html += '</ol>';
        html += '<p class="toc-h">' + esc(el.textContent) + '</p><ol>';
        open = true;
      } else {
        if (!open) { html += '<ol>'; open = true; }
        var h3 = el.querySelector('h3'), t = el.getAttribute('data-tier');
        html += '<li data-tier="' + t + '" data-id="' + el.id + '"><a href="#' + el.id + '"><span class="tier tier-' + t + '">' + TIER_SHORT[t] +
          '</span><span class="no">No.' + (h3.getAttribute('data-no') || '') + '</span> ' + esc(h3.textContent) + '</a></li>';
        n++;
      }
    });
    if (open) html += '</ol>';
    if (quiz) html += '<p class="toc-h"><a href="#quiz">確認問題（' + quiz.querySelectorAll('details.q').length + '問）</a></p>';
    tocEl = document.createElement('details');
    tocEl.className = 'toc';
    tocEl.innerHTML = '<summary>目次（' + n + '項目）</summary><div class="toc-body">' + html + '</div>';
    anchorNode.parentNode.insertBefore(tocEl, anchorNode);
  }
  function paintToc() {
    if (!tocEl) return;
    tocEl.querySelectorAll('li').forEach(function (li) {
      var it = document.getElementById(li.getAttribute('data-id'));
      li.classList.toggle('done', !!(it && it.classList.contains('is-done')));
      li.hidden = !inMode(li.getAttribute('data-tier'));
    });
    tocEl.querySelectorAll('p.toc-h').forEach(function (h) {
      var ol = h.nextElementSibling;
      if (ol && ol.tagName === 'OL') h.hidden = !ol.querySelector('li:not([hidden])');
    });
  }
  function paintTocPage() {
    var secs = document.querySelectorAll('.tocp[data-page]');
    if (!secs.length) return;
    secs.forEach(function (sec) {
      var total = 0, done = 0;
      sec.querySelectorAll('li[data-id]').forEach(function (li) {
        total++;
        var d = isDone(li.getAttribute('data-id'));
        li.classList.toggle('done', d);
        if (d) done++;
      });
      var c = sec.querySelector('.count');
      if (c) c.textContent = done + ' / ' + total;
    });
  }

  /* ---------- 項目へ移動（隠れていても表示する） ---------- */
  function revealHash() {
    var id = '';
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (e) { return; }
    if (!id) return;
    var t = document.getElementById(id);
    if (!t) return;
    if (t.classList.contains('item') && t.offsetParent === null) t.classList.add('force-show');
    t.classList.remove('flash');
    void t.offsetWidth;
    t.classList.add('flash');
    setTimeout(function () { t.classList.remove('flash'); }, 2400);
    t.scrollIntoView({ block: 'start' });
  }

  /* ---------- 検索 ---------- */
  var searchDocs = null, searchLoading = false;
  var modal = null, inputEl = null, listEl = null, searchBtn = null;
  var results = [], activeIdx = -1;
  function norm(t) { return String(t).normalize('NFKC').toLowerCase(); }
  function loadIndex(cb) {
    if (searchDocs) return cb();
    var ready = function () {
      searchDocs = window.EIKO_SEARCH || [];
      searchDocs.forEach(function (d) { d._t = norm(d.ti); d._x = norm(d.x); });
      cb();
    };
    if (window.EIKO_SEARCH) return ready();
    if (searchLoading) return;
    searchLoading = true;
    var sc = document.createElement('script');
    sc.src = 'assets/search-index.js';
    sc.onload = ready;
    sc.onerror = function () { searchLoading = false; listEl.innerHTML = '<p class="s-empty">検索データを読み込めませんでした。</p>'; };
    document.head.appendChild(sc);
  }
  function mountSearch() {
    var wrap = document.querySelector('.site-head .wrap');
    if (!wrap) return;
    searchBtn = document.createElement('button');
    searchBtn.type = 'button';
    searchBtn.className = 'search-btn';
    searchBtn.setAttribute('aria-label', '検索を開く');
    searchBtn.innerHTML = '<span aria-hidden="true">🔍</span> 検索';
    searchBtn.addEventListener('click', openSearch);
    var anchor = wrap.querySelector('.nav');
    wrap.insertBefore(searchBtn, anchor);

    modal = document.createElement('div');
    modal.className = 'search-modal';
    modal.hidden = true;
    modal.innerHTML = '<div class="search-box" role="dialog" aria-modal="true" aria-label="サイト内検索">' +
      '<div class="search-head"><input type="search" class="search-input" placeholder="キーワードで検索（例：倒置　whereas　no more than　セミコロン）" autocomplete="off" aria-label="検索キーワード">' +
      '<button type="button" class="search-close" aria-label="閉じる">×</button></div>' +
      '<div class="search-list" role="listbox"></div>' +
      '<p class="search-foot">スペースで区切ると、すべての語を含む項目に絞り込みます。　<kbd>↑</kbd><kbd>↓</kbd>で選択、<kbd>Enter</kbd>で移動、<kbd>Esc</kbd>で閉じる</p></div>';
    document.body.appendChild(modal);
    inputEl = modal.querySelector('.search-input');
    listEl = modal.querySelector('.search-list');
    modal.addEventListener('click', function (e) { if (e.target === modal) closeSearch(); });
    modal.querySelector('.search-close').addEventListener('click', closeSearch);
    inputEl.addEventListener('input', function () { runSearch(inputEl.value); });
    inputEl.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); moveActive(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); moveActive(-1); }
      else if (e.key === 'Enter') {
        var a = listEl.querySelectorAll('a')[Math.max(activeIdx, 0)];
        if (a) { e.preventDefault(); a.click(); }
      }
    });
    listEl.addEventListener('click', function (e) { if (e.target.closest('a')) closeSearch(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !modal.hidden) { closeSearch(); return; }
      var tag = (e.target && e.target.tagName) || '';
      if (e.key === '/' && !e.ctrlKey && !e.metaKey && tag !== 'INPUT' && tag !== 'TEXTAREA' && modal.hidden) { e.preventDefault(); openSearch(); }
    });
  }
  function openSearch() {
    modal.hidden = false;
    document.body.classList.add('search-open');
    inputEl.focus();
    inputEl.select();
    listEl.innerHTML = '<p class="s-empty">読み込み中…</p>';
    loadIndex(function () { runSearch(inputEl.value); });
  }
  function closeSearch() {
    modal.hidden = true;
    document.body.classList.remove('search-open');
    if (searchBtn) searchBtn.focus();
  }
  function moveActive(dir) {
    var links = listEl.querySelectorAll('a');
    if (!links.length) return;
    activeIdx = (activeIdx + dir + links.length) % links.length;
    links.forEach(function (a, i) { a.parentNode.classList.toggle('active', i === activeIdx); });
    links[activeIdx].scrollIntoView({ block: 'nearest' });
  }
  function runSearch(q) {
    var terms = norm(q).split(/[\s　]+/).filter(Boolean);
    activeIdx = -1;
    if (!terms.length) {
      listEl.innerHTML = '<p class="s-empty">キーワードを入力してください。<br><span>例：倒置、whereas、no more than、セミコロン、仮定法、要約</span></p>';
      return;
    }
    var out = [];
    searchDocs.forEach(function (d) {
      var score = 0;
      for (var i = 0; i < terms.length; i++) {
        var inT = d._t.indexOf(terms[i]) >= 0, inX = d._x.indexOf(terms[i]) >= 0;
        if (!inT && !inX) return;
        score += (inT ? 10 : 0) + (inX ? 2 : 0);
      }
      if (d.t === 'must') score += 1;
      out.push({ d: d, score: score });
    });
    out.sort(function (a, b) { return b.score - a.score; });
    results = out.slice(0, 40);
    renderResults(terms, out.length);
  }
  function renderResults(terms, total) {
    listEl.innerHTML = '';
    if (!results.length) {
      listEl.innerHTML = '<p class="s-empty">見つかりませんでした。<br><span>別の言い方や、英語の表現そのもので試してください。</span></p>';
      return;
    }
    var head = document.createElement('p');
    head.className = 's-count';
    head.textContent = total + '件' + (total > results.length ? '（上位' + results.length + '件を表示）' : '');
    listEl.appendChild(head);
    var ul = document.createElement('ul');
    results.forEach(function (r, i) {
      var d = r.d, li = document.createElement('li');
      var a = document.createElement('a');
      a.href = d.p + (d.id ? '#' + d.id : '');
      var top = document.createElement('span');
      top.className = 's-top';
      if (d.t) { var chip = document.createElement('span'); chip.className = 'tier tier-' + d.t; chip.textContent = TIER_SHORT[d.t]; top.appendChild(chip); }
      var ti = document.createElement('b'); ti.textContent = d.ti; top.appendChild(ti);
      var pn = document.createElement('span'); pn.className = 's-page'; pn.textContent = d.pn; top.appendChild(pn);
      if (d.id && isDone(d.id)) { var dn = document.createElement('span'); dn.className = 's-done'; dn.textContent = '完了'; top.appendChild(dn); }
      a.appendChild(top);
      var sn = snippet(d, terms);
      if (sn) a.appendChild(sn);
      li.appendChild(a);
      ul.appendChild(li);
    });
    listEl.appendChild(ul);
  }
  function snippet(d, terms) {
    var x = d.x, nx = d._x, pos = -1, len = 0;
    for (var i = 0; i < terms.length; i++) { var k = nx.indexOf(terms[i]); if (k >= 0 && (pos < 0 || k < pos)) { pos = k; len = terms[i].length; } }
    var span = document.createElement('span');
    span.className = 's-snip';
    if (pos < 0) { span.textContent = x.slice(0, 90); return span; }
    var start = Math.max(0, pos - 30), end = Math.min(x.length, pos + len + 60);
    if (start > 0) span.appendChild(document.createTextNode('…'));
    span.appendChild(document.createTextNode(x.slice(start, pos)));
    var m = document.createElement('mark'); m.textContent = x.slice(pos, pos + len); span.appendChild(m);
    span.appendChild(document.createTextNode(x.slice(pos + len, end)));
    if (end < x.length) span.appendChild(document.createTextNode('…'));
    return span;
  }

  /* ---------- 記録ページ ---------- */
  var progressRoot = document.getElementById('progress-root');
  function bar(d, t) {
    var pct = t ? Math.round(d / t * 100) : 0;
    return '<span class="pbar"><i style="width:' + pct + '%"></i></span><span class="pnum">' + d + ' / ' + t + '</span>';
  }
  function renderProgress(s) {
    var got = jget('eiko:trophies', {});
    var need = s.nextXp ? (s.nextXp - s.xp) : 0;
    var pct = s.nextXp ? Math.round((s.xp - s.curXp) / (s.nextXp - s.curXp) * 100) : 100;
    var html = '';
    html += '<section class="lvcard"><div class="lvbig">Lv.' + s.level + '</div><div class="lvbody">' +
      '<h2 class="lvname">' + s.levelName + '</h2>' +
      '<div class="xpbar"><i style="width:' + pct + '%"></i></div>' +
      '<p class="note">' + s.xp + ' XP' + (s.nextXp ? '　／　次のレベルまで あと ' + need + ' XP' : '　／　最高レベルに到達しました') + '</p></div></section>';
    html += '<div class="stats">' +
      '<div class="stat"><b>' + s.done + ' / ' + s.total + '</b><span>理解した項目</span></div>' +
      '<div class="stat"><b>' + s.quizDone + ' / ' + s.quizTotal + '</b><span>開いた確認問題</span></div>' +
      '<div class="stat"><b>' + s.streak.current + ' 日</b><span>連続学習（最長 ' + s.streak.best + ' 日）</span></div>' +
      '<div class="stat"><b>' + Object.keys(got).length + ' / ' + TROPHIES.length + '</b><span>トロフィー</span></div></div>';
    html += '<h2>ページ別の進み具合</h2><div class="tablewrap"><table class="ptable"><tr><th>ページ</th><th>必須</th><th>差がつく</th></tr>';
    Object.keys(PAGES).forEach(function (p) {
      var b = s.byPage[p];
      html += '<tr><td><a href="' + p + '">' + PAGES[p].name + '</a></td><td>' + bar(b.must.d, b.must.t) + '</td><td>' + bar(b.core.d, b.core.t) + '</td></tr>';
    });
    html += '</table></div>';
    html += '<h2>トロフィー</h2><div class="trophies">';
    TROPHIES.forEach(function (t) {
      var on = !!got[t.id];
      html += '<div class="trophy' + (on ? '' : ' locked') + '"><span class="ticon">' + (on ? t.icon : '🔒') + '</span><b>' + t.name + '</b><span>' + t.desc + '</span></div>';
    });
    html += '</div>';
    html += '<h2>経験値のルール</h2><ul><li>項目を「理解した」にする：必須 ' + XP.must + ' XP／差がつく ' + XP.core + ' XP／不要 ' + XP.skip + ' XP</li><li>確認問題をはじめて開く：' + QUIZ_XP + ' XP（1問ごと）</li><li>チェックを外すと、その分の経験値も戻ります（トロフィーは残ります）</li></ul>';
    html += '<p class="note" style="margin-top:24px"><button type="button" id="reset-btn" class="danger">記録をすべて消す</button>　この端末に保存された記録だけが消えます。</p>';
    progressRoot.innerHTML = html;
    var rb = document.getElementById('reset-btn');
    if (rb) rb.addEventListener('click', function () {
      if (!window.confirm('チェック・経験値・トロフィーの記録をすべて消します。よろしいですか？')) return;
      try {
        var keys = [];
        for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); if (k && k.indexOf('eiko:') === 0) keys.push(k); }
        keys.forEach(function (k) { localStorage.removeItem(k); });
      } catch (e) {}
      location.reload();
    });
  }

  /* ---------- 起動 ---------- */
  // ヘッダーが固定表示のときだけ、その高さぶん下に切替バーを置く
  function setHeadH() {
    var h = document.querySelector('.site-head');
    var fixed = h && getComputedStyle(h).position === 'sticky';
    document.documentElement.style.setProperty('--head-h', fixed ? h.offsetHeight + 'px' : '0px');
  }
  mountBadge();
  mountSearch();
  buildToc();
  setHeadH();
  window.addEventListener('resize', setHeadH);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(setHeadH);
  refresh(true);
  revealHash();
  window.addEventListener('hashchange', revealHash);
})();
