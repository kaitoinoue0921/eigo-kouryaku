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
  mountBadge();
  refresh(true);
})();
