#!/usr/bin/env python3
"""サイト全体のビルド（項目を追加・変更したら実行する）。
  1. tools/content/*.py から 構文ページ(p-*.html) と 入口ページ(patterns.html) を生成
  2. 全ページのナビを統一
  3. skip-list.html の「構文の不要一覧」を自動集計
  4. assets/manifest.js（レベル・トロフィー用の項目一覧）を生成
使い方: python3 tools/build_all.py
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from content import order, modifier, clause, verbal, compare, negation, subj, verbs  # noqa: E402

PATTERN_PAGES = [order, modifier, clause, verbal, compare, negation, subj, verbs]
TIER_LABEL = {"must": "必須", "core": "差がつく", "skip": "ここまで不要"}

NAV = [("index.html", "トップ"), ("toc.html", "目次"), ("symbols.html", "記号"), ("grammar.html", "文法"),
       ("patterns.html", "構文"), ("before-reading.html", "長文の前に"),
       ("score-tips.html", "得点のコツ"), ("skip-list.html", "不要リスト"), ("progress.html", "記録")]

HEAD = """<!doctype html>
<html lang="ja">
<head>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1744436882685241"
     crossorigin="anonymous"></script>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | 受験英語 完全攻略ノート</title>
<meta name="description" content="{desc}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>%F0%9F%93%96</text></svg>">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600;800&family=Zen+Kaku+Gothic+New:wght@400;500;700;900&display=swap">
<link rel="stylesheet" href="assets/style.css">
</head>
<body data-mode="core">
<header class="site-head"><div class="wrap">
  <a class="brand" href="index.html">受験英語 完全攻略ノート</a>
  <nav class="nav">
  </nav>
</div></header>

<main class="wrap">
"""
FOOT = """</main>
<script src="assets/manifest.js"></script>
<script src="assets/app.js"></script>
</body>
</html>
"""
TOOLBAR = """  <div class="toolbar"><div class="wrap"><div class="filter" role="group" aria-label="表示する範囲">
    <button type="button" data-mode="must">必須だけ</button>
    <button type="button" data-mode="core">必須＋差がつく</button>
    <button type="button" data-mode="all">不要ゾーンも見る</button>
    <span class="prog" id="prog"></span>
  </div></div></div>
"""


def esc_attr(s):
    return s.replace('"', "&quot;")


def render_item(it):
    h = ['  <article class="item" data-tier="%s" id="%s">' % (it["tier"], it["id"]),
         '    <header><span class="tier tier-%s">%s</span><h3>%s</h3></header>' % (it["tier"], TIER_LABEL[it["tier"]], it["title"])]
    if it["focus"]:
        h.append('    <div class="focus"><b>着眼点</b><span>%s</span></div>' % it["focus"])
    if it["body"]:
        h.append("    <p>%s</p>" % it["body"])
    if it["table"]:
        head, rows = it["table"]
        t = ['    <div class="tablewrap"><table>', "      <tr>" + "".join("<th>%s</th>" % c for c in head) + "</tr>"]
        for r in rows:
            t.append("      <tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
        t.append("    </table></div>")
        h.extend(t)
    for en, ja in it["ex"]:
        h.append('    <div class="ex"><p class="en">%s</p><p class="ja">%s</p></div>' % (en, ja))
    if it["tip"]:
        h.append('    <p class="tip"><b>ポイント</b>：%s</p>' % it["tip"])
    if it["warn"]:
        h.append('    <p class="warn"><b>注意</b>：%s</p>' % it["warn"])
    if it["line"]:
        h.append('    <p class="line"><b>線引き</b>：%s</p>' % it["line"])
    h.append('    <label class="done"><input type="checkbox" data-id="%s"> 理解した</label>' % it["id"])
    h.append("  </article>\n")
    return "\n".join(h)


def render_quiz(quiz):
    if not quiz:
        return ""
    out = ['  <section class="quiz" id="quiz">', "    <h2>確認問題</h2>",
           '    <p class="note">クリックすると答えが開く。答えを見る前に、頭の中で答えを決めてから開く。</p>']
    for q, a in quiz:
        out.append('\n    <details class="q"><summary>%s</summary>\n      <div class="ans">%s</div></details>' % (q, a))
    out.append("  </section>\n")
    return "\n".join(out)


def build_category(idx):
    m = PATTERN_PAGES[idx]
    P = m.PAGE
    prev = PATTERN_PAGES[idx - 1].PAGE if idx > 0 else None
    nxt = PATTERN_PAGES[idx + 1].PAGE if idx + 1 < len(PATTERN_PAGES) else None
    n = sum(len(s[1]) for s in P["sections"])
    parts = [HEAD.format(title=P["name"] + "（構文ライブラリ）", desc=P["lead"]),
             '  <p class="note"><a href="patterns.html">← 構文ライブラリ</a>　／　%d項目</p>' % n,
             "  <h1>%s</h1>" % P["name"],
             '  <p class="lead">%s</p>' % P["lead"],
             TOOLBAR]
    for h2, items in P["sections"]:
        parts.append("  <h2>%s</h2>\n" % h2)
        for it in items:
            parts.append(render_item(it))
    parts.append(render_quiz(P.get("quiz")))
    links = []
    if prev:
        links.append('<a href="%s">← %s</a>' % (prev["file"], prev["name"]))
    if nxt:
        links.append('<a href="%s">%s →</a>' % (nxt["file"], nxt["name"]))
    else:
        links.append('<a href="before-reading.html">次は「長文の前に」へ →</a>')
    parts.append("  <footer>\n    <p>%s</p>\n  </footer>\n" % "　／　".join(links))
    parts.append(FOOT)
    (ROOT / P["file"]).write_text("\n".join(parts), encoding="utf-8")
    return n


def build_hub():
    cards, total, tiers = [], 0, {"must": 0, "core": 0, "skip": 0}
    for m in PATTERN_PAGES:
        P = m.PAGE
        c = {"must": 0, "core": 0, "skip": 0}
        for _, items in P["sections"]:
            for it in items:
                c[it["tier"]] += 1
        n = sum(c.values())
        total += n
        for k in c:
            tiers[k] += c[k]
        cards.append(
            '    <a class="card pcard" href="%s" data-page="%s"><b>%s　%s</b><span>%s</span>'
            '<span class="pcard-meta">%d項目（必須 %d ／ 差がつく %d ／ 不要 %d）</span>'
            '<span class="pcard-prog"></span></a>' % (P["file"], P["file"], P["icon"], P["name"], P["summary"], n, c["must"], c["core"], c["skip"]))
    parts = [HEAD.format(title="構文ライブラリ", desc="受験英語の頻出構文を8分野・約%d項目に整理。着眼点・図解・訳、必須・差がつく・不要の3段階、確認問題つき。" % total),
             "  <h1>構文ライブラリ</h1>",
             '  <p class="lead">受験で出る構文を、<b>8分野・%d項目</b>に整理した。1項目は「着眼点 → 例文と訳 → ポイント」の順。</p>' % total,
             '  <p class="note">全体像は、<a href="toc.html#map">英語構文マップ</a>（文の設計図・分野別の全構文）で見わたせます。</p>',
             "  <h2>分野を選ぶ</h2>",
             '  <div class="cards">', "\n".join(cards), "  </div>",
             "  <h2>網羅の範囲について</h2>",
             '  <ul>',
             "    <li>対象は共通テスト〜MARCH・地方国公立で問われる、<b>標準的な構文</b>。難関大の細かい構文は、「不要」または「差がつく」に分けてある。</li>",
             "    <li>出題される英文は無数にあり、<b>1つ残らず載せることはできない</b>。載せているのは、「出会う頻度が高く、読み方の型として使える」ものを選んだ一覧。</li>",
             "    <li>過去問で見つけた構文がこの一覧にないときは、<b>近い型の項目に当てはめて読める</b>か確認する。当てはまらなければ、追加の候補にする。</li>",
             "  </ul>",
             "  <h2>図解の読み方</h2>",
             '  <div class="legend"><span class="S">主語（S）</span><span class="V">動詞（V）</span><span class="O">目的語・補語（O・C）</span><span>[ ] 節</span><span>( ) 修飾</span></div>',
             '  <p class="note">本文では、下線で構造を示す。ノートに書くときも、同じ記法で統一すると、あとで見直しやすい。</p>',
             "  <footer>\n    <p>まず「必須」だけを表示して、各分野を一通り読み、そのあと「差がつく」に進むのがおすすめ。</p>\n  </footer>",
             FOOT]
    (ROOT / "patterns.html").write_text("\n".join(parts), encoding="utf-8")
    return total, tiers


def sync_nav():
    def nav(cur, cat=False):
        lines = ['  <nav class="nav">']
        for f, n in NAV:
            a = ' aria-current="page"' if f == cur else ""
            lines.append('    <a href="%s"%s>%s</a>' % (f, a, n))
        lines.append("  </nav>")
        return "\n".join(lines)
    targets = [f for f, _ in NAV] + [m.PAGE["file"] for m in PATTERN_PAGES] + ["before-reading.html"]
    for f in dict.fromkeys(targets):
        p = ROOT / f
        t = p.read_text(encoding="utf-8")
        cur = "patterns.html" if f.startswith("p-") else f
        t = re.sub(r'  <nav class="nav">.*?  </nav>', nav(cur), t, count=1, flags=re.S)
        for s in ("manifest.js", "app.js"):
            pass
        if "assets/manifest.js" not in t:
            t = t.replace("</body>", '<script src="assets/manifest.js"></script>\n<script src="assets/app.js"></script>\n</body>')
        if 'href="privacy.html"' not in t and "</footer>" in t:
            t = t.replace("</footer>", '  <p class="note"><a href="privacy.html">プライバシーポリシー</a></p>\n  </footer>', 1)
        p.write_text(t, encoding="utf-8")


def inject_ads():
    """全ページの <head> に AdSense スクリプトを入れる（既存サイトと同じ方式）。"""
    snippet = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1744436882685241"\n'
               '     crossorigin="anonymous"></script>\n')
    n = 0
    for p in sorted(ROOT.glob("*.html")):
        t = p.read_text(encoding="utf-8")
        if "adsbygoogle" in t:
            continue
        t = t.replace("<head>\n", "<head>\n" + snippet, 1)
        p.write_text(t, encoding="utf-8")
        n += 1
    return n


def build_skip_section():
    p = ROOT / "skip-list.html"
    t = p.read_text(encoding="utf-8")
    rows = []
    for m in PATTERN_PAGES:
        P = m.PAGE
        for _, items in P["sections"]:
            for it in items:
                if it["tier"] == "skip":
                    rows.append('    <tr><td><a href="%s#%s">%s</a></td><td>%s</td><td>%s</td></tr>' % (P["file"], it["id"], it["title"], P["name"], it["line"]))
    block = ('<!-- AUTO-SKIP-START -->\n  <h3 style="margin-top:24px">構文（自動集計）</h3>\n'
             '  <div class="tablewrap"><table>\n    <tr><th>不要なこと</th><th>分野</th><th>線引き</th></tr>\n' + "\n".join(rows) +
             '\n  </table></div>\n  <!-- AUTO-SKIP-END -->')
    if "<!-- AUTO-SKIP-START -->" in t:
        t = re.sub(r"<!-- AUTO-SKIP-START -->.*?<!-- AUTO-SKIP-END -->", block, t, flags=re.S)
    else:
        t = t.replace('  <h2>「不要」を「必要」に格上げする基準</h2>', "  " + block + '\n\n  <h2>「不要」を「必要」に格上げする基準</h2>', 1)
    p.write_text(t, encoding="utf-8")
    return len(rows)


def build_manifest():
    pages = [("symbols.html", "記号"), ("grammar.html", "文法")] + \
            [(m.PAGE["file"], m.PAGE["name"]) for m in PATTERN_PAGES] + \
            [("before-reading.html", "長文の前に"), ("score-tips.html", "得点のコツ")]
    items, info, ids = [], {}, set()
    for fname, label in pages:
        html = (ROOT / fname).read_text(encoding="utf-8")
        info[fname] = {"name": label, "quizzes": len(re.findall(r'<details class="q"', html))}
        for m in re.finditer(r'<article class="item" data-tier="(must|core|skip)" id="([^"]+)">(.*?)</article>', html, re.S):
            tier, _id, body = m.groups()
            d = re.search(r'data-id="([^"]+)"', body)
            if not d:
                raise SystemExit("%s: #%s にチェックボックス(data-id)がありません" % (fname, _id))
            if d.group(1) in ids:
                raise SystemExit("data-id が重複しています: %s" % d.group(1))
            ids.add(d.group(1))
            title = re.sub(r"<[^>]+>", "", re.search(r"<h3>(.*?)</h3>", body, re.S).group(1)).strip()
            items.append({"id": d.group(1), "tier": tier, "page": fname, "title": title})
    out = "window.EIKO_ITEMS=" + json.dumps(items, ensure_ascii=False) + ";\nwindow.EIKO_PAGES=" + json.dumps(info, ensure_ascii=False) + ";\n"
    (ROOT / "assets" / "manifest.js").write_text(out, encoding="utf-8")
    by = {}
    for i in items:
        by[i["tier"]] = by.get(i["tier"], 0) + 1
    return len(items), by, sum(p["quizzes"] for p in info.values())


import html as _html


def _plain(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = _html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def item_pages():
    """項目を持つページ（順序つき）: (ファイル名, 表示名)"""
    return [("symbols.html", "記号"), ("grammar.html", "文法")] + \
           [(m.PAGE["file"], m.PAGE["name"]) for m in PATTERN_PAGES] + \
           [("before-reading.html", "長文の前に"), ("score-tips.html", "得点のコツ")]


ITEM_RE = re.compile(r'<article class="item" data-tier="(must|core|skip)" id="([^"]+)">(.*?)</article>', re.S)


def build_search():
    docs = []
    for fname, label in item_pages():
        html = (ROOT / fname).read_text(encoding="utf-8")
        for m in ITEM_RE.finditer(html):
            tier, _id, body = m.groups()
            title = _plain(re.search(r"<h3>(.*?)</h3>", body, re.S).group(1))
            text = _plain(body.replace("理解した", ""))
            docs.append({"id": _id, "p": fname, "pn": label, "t": tier, "ti": title, "x": text})
    # 分野・ページ単位の検索対象
    for m in PATTERN_PAGES:
        P = m.PAGE
        docs.append({"id": "", "p": P["file"], "pn": "構文ライブラリ", "t": "", "ti": P["name"] + "（分野）", "x": P["summary"] + " " + P["lead"]})
    skip = (ROOT / "skip-list.html").read_text(encoding="utf-8")
    main = re.search(r"<main.*?</main>", skip, re.S)
    docs.append({"id": "", "p": "skip-list.html", "pn": "不要リスト", "t": "", "ti": "ここまでは不要（一覧）", "x": _plain(main.group(0))[:6000] if main else ""})
    out = "window.EIKO_SEARCH=" + json.dumps(docs, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (ROOT / "assets" / "search-index.js").write_text(out, encoding="utf-8")
    return len(docs), len(out.encode("utf-8"))


# ---------------- 英語構文マップ ----------------
import math

# マインドマップの枝。並びは時計回り（上から）。hue は色相。leaves は (項目id, 短いラベル)。
# 枝ごとの「くわしい一覧」用に ids を持つ。存在しないidはビルドエラー。
MINDMAP = [
    dict(key="s", name="主語 S", sub="何が・だれが", hue=0, group="part", desc="名詞・名詞節・不定詞・動名詞。長い主語の見つけ方。",
         leaves=[("od-long-subject", "長い主語"), ("dummy-it", "形式主語 it"), ("cl-noun-that", "名詞節 that"), ("cl-whether-if", "whether / if"),
                 ("md-what", "what 節"), ("vb-gerund-subj", "動名詞の主語"), ("vs-inanimate", "無生物主語"), ("od-insertion", "挿入")],
         more=["cl-indirect-question", "md-noun-construction", "vb-sub-inf"]),
    dict(key="v", name="動詞 V", sub="時制・態・助動詞", hue=36, group="part", desc="動詞の形が、いつのこと・どんな意味かを決める。",
         leaves=[("present-perfect", "現在完了"), ("passive", "受動態"), ("vs-tense", "時制の一致"), ("sj-modal-basic", "助動詞の推量"),
                 ("modal-perfect", "助動詞+have p.p."), ("sj-used-to", "used to"), ("vs-there", "There 構文"), ("vs-phrasal", "群動詞")],
         more=["vs-passive-note", "sj-may-well", "sj-should-emotion"]),
    dict(key="o", name="目的語・補語", sub="V のあとの形", hue=72, group="part", desc="動詞ごとに、後ろに来る形が決まっている。",
         leaves=[("vs-svoc", "SVOC"), ("vs-causative", "使役 make/let/have"), ("vs-perception", "知覚動詞"), ("vs-svo-to", "SVO to do"),
                 ("vs-from-ing", "prevent A from -ing"), ("vs-as", "regard A as B"), ("od-dummy-object", "形式目的語 it"), ("vb-gerund-idioms", "動名詞の慣用表現"), ("to-infinitive", "to 不定詞の3用法")],
         more=["vs-of", "vs-with", "gerund-inf", "vb-sub-inf"]),
    dict(key="m", name="修飾 M", sub="情報を足す", hue=108, group="part", desc="関係詞・分詞・不定詞・前置詞句・同格。どこにかかるかを決める。",
         leaves=[("md-rel-basic", "関係代名詞"), ("md-prep-rel", "前置詞+関係詞"), ("md-rel-adverb", "関係副詞"), ("md-rel-omit", "関係詞の省略"),
                 ("md-nonrestrictive", "非制限用法"), ("md-participle-post", "分詞の後置修飾"), ("md-to-adj", "to 不定詞の修飾"), ("od-appositive", "同格"), ("md-prep-phrase", "前置詞句の係り先")],
         more=["md-that-what", "md-compound-rel", "md-chain-rel", "md-adj-post", "vb-too-enough", "vb-purpose-result"]),
    dict(key="adv", name="副詞節・接続", sub="時・理由・条件…", hue=144, group="part", desc="時・理由・条件・譲歩・目的などを、主節の前後に足す。",
         leaves=[("cl-time-cond-present", "時・条件は現在形"), ("cl-not-until", "not until"), ("cl-concession", "譲歩"), ("cl-condition", "条件 unless"),
                 ("cl-purpose", "目的 so that"), ("cl-result", "結果 so…that"), ("vb-participle-basic", "分詞構文"), ("vb-with-oc", "with + O + C")],
         more=["cl-time-conj", "cl-reason", "cl-manner", "cl-range", "cl-contrast", "vb-participle-perf-pass", "od-concessive-inv"]),
    dict(key="cmp", name="比較", sub="", hue=180, group="change", desc="何と何を比べているかを決める。型で覚える。",
         leaves=[("cp-as-as", "as … as"), ("cp-comparative", "比較級 than"), ("cp-the-more", "the + 比較級 …"), ("cp-superlative", "最上級"),
                 ("cp-superlative-equivalent", "最上級相当"), ("cp-no-more-than", "no more than"), ("cp-not-so-much", "not so much A as B"), ("cp-than-omitted", "that of / those of")],
         more=["cp-idioms", "cp-as-possible", "cp-latin", "cp-of-the-two"]),
    dict(key="neg", name="否定", sub="", hue=216, group="change", desc="どこまでが否定されているか、隠れた否定はないか。",
         leaves=[("ng-partial", "部分否定"), ("ng-not-a-but-b", "not A but B"), ("ng-semi", "準否定 hardly"), ("ng-no-noun", "no + 名詞"),
                 ("ng-double", "二重否定"), ("ng-idioms", "否定の慣用表現"), ("ng-hidden", "隠れた否定"), ("ng-transfer", "否定の転移")],
         more=["ng-no-longer", "ng-strong", "ng-scope", "ng-emphatic"]),
    dict(key="sub", name="仮定・願望", sub="", hue=252, group="change", desc="動詞の形が、実際の時間とずれていたら、現実と違う話。",
         leaves=[("sj-past", "仮定法過去"), ("sj-past-perf", "仮定法過去完了"), ("sj-inversion", "if の省略"), ("sj-wish", "I wish"),
                 ("sj-as-if", "as if"), ("sj-without", "without / but for"), ("sj-hidden-cond", "隠れた条件")],
         more=["sj-were-to-should", "sj-high-time", "sj-would-rather", "sj-otherwise", "sj-mixed"]),
    dict(key="ord", name="語順・強調", sub="", hue=288, group="change", desc="語順が普通と違うとき、何が起きているかを見抜く。",
         leaves=[("od-neg-inversion", "否定語の倒置"), ("od-only", "Only の倒置"), ("od-so-neither", "So do I"), ("od-c-inversion", "補語・場所の倒置"),
                 ("od-cleft", "強調構文"), ("od-emphasis", "強調 do"), ("od-common-ellipsis", "省略")],
         more=["od-rhetorical", "od-wh-to", "od-what-idioms"]),
    dict(key="con", name="つなぐ・論理", sub="", hue=324, group="change", desc="接続の範囲と、論理の向きをつかむ。",
         leaves=[("cl-coordination", "and の範囲"), ("cl-correlative", "相関接続詞"), ("cl-prep-conj", "前置詞と接続詞"), ("cl-as-usage", "as の意味"),
                 ("discourse", "論理を示す語"), ("reference", "指示語"), ("that-usage", "that の見分け")],
         more=["cl-so-for-yet", "three-clauses", "wh-clauses", "paragraph-types"]),
]
STEPS = [
    ("① 動詞 → 主語", ["skeleton"]),
    ("② 修飾を外す", ["od-insertion", "md-prep-phrase", "md-participle-post"]),
    ("③ 節を見抜く", ["three-clauses", "that-usage", "wh-clauses"]),
    ("④ 論理でつなぐ", ["discourse", "reference", "paragraph-types"]),
]
CAT_HUE = {"od": 5, "md": 210, "cl": 30, "vb": 175, "cp": 275, "ng": 340, "sj": 250, "vs": 140}


def _short(title):
    t = title.split("（")[0].strip()
    return t if len(t) >= 2 else title


def _tw(s, fs=11.5):
    return sum(fs if ord(c) >= 0x2E80 else fs * 0.56 for c in s)


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_mindmap_svg(idx):
    n_br = len(MINDMAP)
    fs = 11.5
    R_LEAF = 238
    maxw = max(_tw(lb, fs + 0.6) for br in MINDMAP for _, lb in br["leaves"])
    label_end = R_LEAF + 12 + maxw
    R_ARC = label_end + 24
    S = int(R_ARC + 40)
    C = S
    W = 2 * S
    R_BR = 168
    step_deg = 360.0 / n_br
    spread = 33.0

    def pt(r, deg):
        a = math.radians(deg)
        return C + r * math.cos(a), C + r * math.sin(a)

    missing = []
    o = ['<svg class="mm-svg" viewBox="0 0 %d %d" role="group" aria-label="英語構文マップ。中心から10本の枝が広がる" xmlns="http://www.w3.org/2000/svg">' % (W, W)]
    # 外側の弧とラベル
    def arc(id_, a0, a1, label, rev=False):
        if rev:
            x0, y0 = pt(R_ARC, a1); x1, y1 = pt(R_ARC, a0); sweep = 0
        else:
            x0, y0 = pt(R_ARC, a0); x1, y1 = pt(R_ARC, a1); sweep = 1
        o.append('<path id="%s" class="mm-arc" d="M %.1f %.1f A %.1f %.1f 0 0 %d %.1f %.1f" fill="none"/>' % (id_, x0, y0, R_ARC, R_ARC, sweep, x1, y1))
        o.append('<text class="mm-arc-label"><textPath href="#%s" startOffset="50%%" text-anchor="middle">%s</textPath></text>' % (id_, label))
    a_first = -90 - step_deg / 2 + 2
    a_mid = -90 + step_deg * 5 - step_deg / 2
    arc("mm-arc-a", a_first, a_mid - 2, "文をつくる 5つの部品")
    arc("mm-arc-b", a_mid + 2, -90 + step_deg * 10 - step_deg / 2 - 2, "文全体にかかる 5つの変化", rev=True)
    # 中心
    for i, br in enumerate(MINDMAP):
        deg = -90 + step_deg * i
        bx, by = pt(R_BR, deg)
        o.append('<g class="mm-group" data-branch="%s" style="--h:%d">' % (br["key"], br["hue"]))
        cx0, cy0 = pt(58, deg)
        o.append('<line class="mm-spoke" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (cx0, cy0, bx, by))
        leaves = br["leaves"]
        n = len(leaves)
        step = min(spread / (n - 1), 5.4) if n > 1 else 0
        for k, (iid, label) in enumerate(leaves):
            if iid not in idx:
                missing.append(iid)
                continue
            d = idx[iid]
            a = deg + (k - (n - 1) / 2.0) * step
            lx, ly = pt(R_LEAF, a)
            right = math.cos(math.radians(a)) >= 0
            rot = a if right else a + 180
            o.append('<line class="mm-twig" x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (bx, by, lx, ly))
            tx = 9 if right else -9
            anchor = "start" if right else "end"
            o.append('<a class="mm-leaf t-%s" data-id="%s" href="%s#%s" aria-label="%s"><title>%s（%s）</title>'
                     '<g transform="translate(%.1f %.1f) rotate(%.1f)"><circle r="3.6"/><text x="%d" dy=".35em" text-anchor="%s">%s</text></g></a>'
                     % (d["t"], iid, d["p"], iid, _esc(d["ti"]), _esc(d["ti"]), _esc(d["pn"]), lx, ly, rot, tx, anchor, _esc(label)))
        bw = max(_tw(br["name"], 13.5) + 24, 84)
        o.append('<g class="mm-branch" tabindex="0" role="button" aria-label="%s の構文を一覧で表示" data-branch="%s"><rect x="%.1f" y="%.1f" width="%.1f" height="34" rx="17"/>'
                 '<text x="%.1f" y="%.1f" text-anchor="middle" dy=".35em">%s</text></g>' % (_esc(br["name"]), br["key"], bx - bw / 2, by - 17, bw, bx, by, _esc(br["name"])))
        o.append("</g>")
    o.append('<g class="mm-center"><circle cx="%d" cy="%d" r="58"/><text x="%d" y="%d" text-anchor="middle">英文の</text><text x="%d" y="%d" text-anchor="middle">構造</text></g>' % (C, C, C, C - 5, C, C + 17))
    o.append("</svg>")
    if missing:
        raise SystemExit("構文マップに存在しない項目idがあります: %s" % sorted(set(missing)))
    return "\n".join(o)


def build_map_html():
    idx = {}
    for fname, label in item_pages():
        html = (ROOT / fname).read_text(encoding="utf-8")
        for m in ITEM_RE.finditer(html):
            tier, _id, body = m.groups()
            idx[_id] = {"p": fname, "pn": label, "t": tier, "ti": _plain(re.search(r"<h3>(.*?)</h3>", body, re.S).group(1))}
    missing = []

    def chip(i):
        if i not in idx:
            missing.append(i)
            return ""
        d = idx[i]
        return '<a class="mchip t-%s" data-id="%s" href="%s#%s" title="%s（%s）">%s</a>' % (d["t"], i, d["p"], i, d["ti"].replace('"', "&quot;"), d["pn"], _short(d["ti"]))

    svg = build_mindmap_svg(idx)
    out = ['<section class="map" id="map">',
           "  <h2>英語構文マップ</h2>",
           '  <p class="lead">中心の「英文の構造」から、<b>5つの部品</b>と<b>5つの変化</b>の10本の枝が広がる。<b>色つきの枝をクリック</b>すると、その分野の構文が一覧で出る。<b>先の項目をクリック</b>すると、その説明に移動する。</p>',
           '  <div class="mlegend"><span class="mkey"><i class="dot must"></i>必須</span><span class="mkey"><i class="dot core"></i>差がつく</span><span class="mkey"><i class="dot done"></i>完了した項目</span>'
           '<span class="mm-zoom" role="group" aria-label="拡大・縮小"><button type="button" data-z="out" aria-label="縮小">－</button><button type="button" data-z="fit">全体表示</button><button type="button" data-z="in" aria-label="拡大">＋</button></span></div>',
           '  <div class="mm-wrap" id="mm-wrap" tabindex="0" aria-label="構文マップ（スクロールして見る）">', svg, "  </div>",
           '  <div class="mm-panel" id="mm-panel" aria-live="polite"><p class="note">色つきの枝（丸い四角）をクリックすると、その分野の構文が、ここに一覧で出ます。</p></div>',
           '  <details class="mdetail"><summary>部品・変化ごとの一覧を、すべて表示する</summary><div class="mblocks">']
    for br in MINDMAP:
        ids = [i for i, _ in br["leaves"]] + br["more"]
        out.append('    <div class="mblock" data-branch="%s" style="--h:%d"><h4>%s<small>%s</small></h4><p>%s</p><div class="mchips">%s</div></div>' % (
            br["key"], br["hue"], br["name"], br["sub"], br["desc"], "".join(chip(i) for i in ids)))
    out.append("  </div></details>")
    out.append('  <h3 class="map-h">例文で見る、文の設計図</h3>')
    hue = {m["key"]: m["hue"] for m in MINDMAP}
    out.append('  <div class="msent">')
    out.append('    <p class="msent-en">'
               '<span class="w" style="--h:%d"><i>Although she was tired,</i><em>副詞節・接続（譲歩）</em></span> '
               '<span class="w" style="--h:%d"><i>the student</i><em>主語 S</em></span> '
               '<span class="w" style="--h:%d"><i>who sat next to me</i><em>修飾 M（関係詞節）</em></span> '
               '<span class="w" style="--h:%d"><i>finished</i><em>動詞 V</em></span> '
               '<span class="w" style="--h:%d"><i>the report</i><em>目的語 O</em></span> '
               '<span class="w" style="--h:%d"><i>that the teacher had given us.</i><em>修飾 M（関係詞節）</em></span></p>' % (
                   hue["adv"], hue["s"], hue["m"], hue["v"], hue["o"], hue["m"]))
    out.append('    <p class="msent-ja">疲れていたけれども、私の隣に座っていたその生徒は、先生が私たちに出したレポートを書き終えた。</p>')
    out.append("  </div>")
    out.append('  <p class="mformula" aria-hidden="true"><span style="--h:%d">副詞節</span><b>,</b><span style="--h:%d">S</span><b>＋</b><span style="--h:%d">V</span><b>＋</b><span style="--h:%d">O / C</span><b>＋</b><span style="--h:%d">M</span></p>' % (
        hue["adv"], hue["s"], hue["v"], hue["o"], hue["m"]))
    out.append('  <h3 class="map-h">読む手順</h3>')
    out.append('  <div class="msteps">')
    for name, ids in STEPS:
        out.append('    <div class="mstep"><b>%s</b>%s</div>' % (name, "".join(chip(i) for i in ids)))
    out.append("  </div>")
    out.append('  <h3 class="map-h">分野別（ページ別）の全構文 %d項目</h3>' % sum(1 for v in idx.values() if v["p"].startswith("p-")))
    out.append('  <div class="mcats">')
    for m in PATTERN_PAGES:
        P = m.PAGE
        chips = "".join(chip(it["id"]) for _, items in P["sections"] for it in items)
        out.append('    <div class="mcat mblock" data-page="%s"><h4><a href="%s">%s　%s</a><span class="mprog"></span></h4><p>%s</p><div class="mchips">%s</div></div>' % (
            P["file"], P["file"], P["icon"], P["name"], P["summary"], chips))
    out.append("  </div>")
    out.append("</section>")
    if missing:
        raise SystemExit("構文マップに存在しない項目idがあります: %s" % sorted(set(missing)))
    return "\n".join(out)


def build_toc_page():
    TL = {"must": "必須", "core": "差がつく", "skip": "不要"}
    sec = []
    for fname, label in item_pages():
        html = (ROOT / fname).read_text(encoding="utf-8")
        summ = ""
        for m in PATTERN_PAGES:
            if m.PAGE["file"] == fname:
                summ = m.PAGE["summary"]
        parts, n, ol_open = [], 0, False
        for m in re.finditer(r'<h2[^>]*>(.*?)</h2>|<article class="item" data-tier="(must|core|skip)" id="([^"]+)">\s*<header>.*?<h3>(.*?)</h3>', html, re.S):
            if m.group(1) is not None:
                h = _plain(m.group(1))
                if h == "確認問題" or "図解の読み方" in h:
                    continue
                if ol_open:
                    parts.append("      </ol>")
                parts.append('      <p class="toc-h">%s</p>\n      <ol>' % h)
                ol_open = True
            else:
                if not ol_open:
                    parts.append("      <ol>")
                    ol_open = True
                n += 1
                tier, _id, title = m.group(2), m.group(3), _plain(m.group(4))
                parts.append('        <li data-id="%s" data-tier="%s"><a href="%s#%s"><span class="tier tier-%s">%s</span><span class="no">No.%02d</span> %s</a></li>' % (_id, tier, fname, _id, tier, TL[tier], n, title))
        if ol_open:
            parts.append("      </ol>")
        sec.append('    <details class="tocp" data-page="%s">\n      <summary><span class="tp-name">%s</span><span class="count"></span></summary>\n      <p class="note"><a href="%s">%sのページを開く →</a>%s</p>\n%s\n    </details>' % (
            fname, label, fname, label, ("　" + summ) if summ else "", "\n".join(parts)))
    others = ('    <section class="tocp-other">\n      <h2>そのほか</h2>\n      <ul>\n'
              '        <li><a href="patterns.html">構文ライブラリ（8分野の入口）</a></li>\n'
              '        <li><a href="skip-list.html">ここまでは不要（一覧）</a></li>\n'
              '        <li><a href="progress.html">記録（レベル・トロフィー）</a></li>\n'
              '        <li><a href="privacy.html">プライバシーポリシー</a></li>\n      </ul>\n    </section>')
    page = [HEAD.format(title="目次", desc="受験英語 完全攻略ノートの全項目の目次。ページごとの項目一覧から、読みたい項目にすぐ移動できる。"),
            "  <h1>目次</h1>",
            '  <p class="lead">全ページの項目の一覧。読みたい項目をクリックすると、その項目に移動する。<b>キーワードで探すときは、右上の「検索」</b>（または <kbd>/</kbd> キー）を使う。</p>',
            '  <p class="note">↓ 目次の下に、<a href="#map">英語構文マップ</a>（文の設計図・分野別の全構文）があります。</p>',
            '  <p class="toc-ctl"><button type="button" id="toc-all" class="hd">すべて開く</button></p>',
            "  <div class=\"tocs\">", "\n".join(sec), others, "  </div>",
            build_map_html(),
            "  <footer>\n    <p><a href=\"index.html\">← トップへ戻る</a></p>\n  </footer>", FOOT]
    (ROOT / "toc.html").write_text("\n".join(page), encoding="utf-8")


if __name__ == "__main__":
    counts = [build_category(i) for i in range(len(PATTERN_PAGES))]
    total, tiers = build_hub()
    build_toc_page()
    sync_nav()
    ads_added = inject_ads()
    skip_rows = build_skip_section()
    n, by, q = build_manifest()
    sdocs, ssize = build_search()
    print("構文ページ:", counts, "合計", total, tiers)
    print("不要リストに集計した構文の不要項目:", skip_rows)
    print("全項目:", n, by, "確認問題:", q)
    print("検索インデックス:", sdocs, "件", ssize // 1024, "KB")
    print("広告スクリプトを追加したページ:", ads_added)
