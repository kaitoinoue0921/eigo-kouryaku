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
        head = '<a href="%s">%s</a>' % (fname, label)
        sec.append('    <section class="tocp" data-page="%s">\n      <h2>%s<span class="count"></span></h2>%s\n%s\n    </section>' % (
            fname, head, ('\n      <p class="note">%s</p>' % summ) if summ else "", "\n".join(parts)))
    others = ('    <section class="tocp-other">\n      <h2>そのほか</h2>\n      <ul>\n'
              '        <li><a href="patterns.html">構文ライブラリ（8分野の入口）</a></li>\n'
              '        <li><a href="skip-list.html">ここまでは不要（一覧）</a></li>\n'
              '        <li><a href="progress.html">記録（レベル・トロフィー）</a></li>\n'
              '        <li><a href="privacy.html">プライバシーポリシー</a></li>\n      </ul>\n    </section>')
    page = [HEAD.format(title="目次", desc="受験英語 完全攻略ノートの全項目の目次。ページごとの項目一覧から、読みたい項目にすぐ移動できる。"),
            "  <h1>目次</h1>",
            '  <p class="lead">全ページの項目の一覧。読みたい項目をクリックすると、その項目に移動する。<b>キーワードで探すときは、右上の「検索」</b>（または <kbd>/</kbd> キー）を使う。</p>',
            "  <div class=\"tocs\">", "\n".join(sec), others, "  </div>",
            "  <footer>\n    <p><a href=\"index.html\">← トップへ戻る</a></p>\n  </footer>", FOOT]
    (ROOT / "toc.html").write_text("\n".join(page), encoding="utf-8")


if __name__ == "__main__":
    counts = [build_category(i) for i in range(len(PATTERN_PAGES))]
    total, tiers = build_hub()
    build_toc_page()
    sync_nav()
    skip_rows = build_skip_section()
    n, by, q = build_manifest()
    sdocs, ssize = build_search()
    print("構文ページ:", counts, "合計", total, tiers)
    print("不要リストに集計した構文の不要項目:", skip_rows)
    print("全項目:", n, by, "確認問題:", q)
    print("検索インデックス:", sdocs, "件", ssize // 1024, "KB")
