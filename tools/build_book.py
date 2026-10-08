#!/usr/bin/env python3
"""KDPペーパーバック用の本文PDFを作る。tools/content/*.py（サイトと同じ元データ）から
book/book.html を生成し、Chrome headless で book/interior.pdf に印刷する。
使い方: python3 tools/build_book.py
判型は A5（148×210mm）、白黒・白紙(cream不可)、裁ち落としなし。著者名は AUTHOR を設定する。
"""
import pathlib, subprocess, sys, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from content import order, modifier, clause, verbal, compare, negation, subj, verbs  # noqa: E402

PAGES = [order, modifier, clause, verbal, compare, negation, subj, verbs]
TIER = {"must": "必須", "core": "差がつく", "skip": "ここまで不要"}
TITLE = "受験英語 構文 線引きノート"
SUBTITLE = "必須・差がつく・不要に分けた 131の構文"
AUTHOR = "（著者名）"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: 148mm 210mm; }
@page :right { margin: 16mm 13mm 18mm 19mm; }
@page :left  { margin: 16mm 19mm 18mm 13mm; }
@page :first { margin: 0; }
html { font-family: "Hiragino Mincho ProN","Hiragino Kaku Gothic ProN",serif; font-size: 9.6pt; line-height: 1.65; color:#000; }
body { margin:0; }
h1,h2,h3 { font-family: "Hiragino Kaku Gothic ProN",sans-serif; margin:0; }
.cover { page-break-after: always; height:210mm; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; }
.cover h1 { font-size: 26pt; line-height:1.3; }
.cover .sub { font-size: 12pt; margin-top: 10mm; }
.cover .au { font-size: 11pt; margin-top: 30mm; }
.pb { page-break-before: always; }
.chapter { page-break-before: always; height: 170mm; display:flex; flex-direction:column; justify-content:center; }
.chapter .no { font-size: 11pt; letter-spacing: .2em; }
.chapter h1 { font-size: 22pt; margin: 4mm 0 6mm; border-bottom: 1.2pt solid #000; padding-bottom: 3mm; }
.chapter p { font-size: 10pt; }
h2.sec { font-size: 12pt; margin: 7mm 0 3mm; padding: 1.2mm 3mm; background:#000; color:#fff; break-after: avoid; }
.item { break-inside: avoid; border-top: .6pt solid #000; padding: 2.5mm 0 3mm; }
.item h3 { font-size: 10.6pt; margin: 0 0 1.5mm; }
.chk { display:inline-block; width:3.4mm; height:3.4mm; border:.8pt solid #000; margin-right:2mm; vertical-align:-0.5mm; }
.tier { display:inline-block; font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:7.5pt; padding:0 1.6mm; border:.8pt solid #000; margin-right:2mm; vertical-align:.3mm; }
.tier-must { background:#000; color:#fff; }
.tier-core { background:#fff; }
.tier-skip { border-style:dashed; }
.focus { font-size:9pt; margin-bottom:1.5mm; }
.focus .lab { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:8pt; border-bottom:.8pt solid #000; margin-right:2mm; }
.ex { margin: 1.2mm 0 1.2mm 2mm; padding-left: 2.5mm; border-left: 1.5pt solid #000; }
.ex .en { margin:0; font-family:"Times New Roman","Hiragino Mincho ProN",serif; font-size:10pt; }
.ex .ja { margin:0; font-size:8.6pt; }
mark { background:none; font-weight:bold; text-decoration: underline; text-underline-offset:1.2pt; }
p { margin: 1.2mm 0; }
.tip, .warn, .line { font-size:9pt; }
.tip .lab, .warn .lab, .line .lab { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-size:8pt; padding:0 1.2mm; border:.7pt solid #000; margin-right:1mm; }
.warn .lab { background:#000; color:#fff; }
table { border-collapse: collapse; width:100%; margin:1.5mm 0; font-size:8.8pt; break-inside: avoid; }
th, td { border:.6pt solid #000; padding: .8mm 1.6mm; text-align:left; vertical-align:top; }
th { background:#ddd; font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.quiz .q { break-inside: avoid; margin: 3mm 0; }
.quiz .qn { font-family:"Hiragino Kaku Gothic ProN",sans-serif; font-weight:bold; }
.quiz .blank { border-bottom:.5pt dotted #000; height:7mm; }
.ans { margin: 2.5mm 0; break-inside: avoid; }
.ans .a { font-family:"Hiragino Kaku Gothic ProN",sans-serif; }
.memo { page-break-before: always; }
.memo .l { border-bottom:.5pt solid #999; height:8.4mm; }
.legal { font-size:8.6pt; }
.toc li { list-style:none; }
.toc ul { padding:0; margin:0; }
.toc .it { display:flex; }
.toc .it span:first-child { flex:1; }
.skiplist td:first-child { width:55%; }
"""

def item(it, n):
    h = ['<article class="item">',
         '<h3><span class="chk"></span><span class="tier tier-%s">%s</span>%s</h3>' % (it["tier"], TIER[it["tier"]], it["title"])]
    if it["focus"]:
        h.append('<p class="focus"><span class="lab">着眼点</span>%s</p>' % it["focus"])
    if it["body"]:
        h.append("<p>%s</p>" % it["body"])
    if it["table"]:
        head, rows = it["table"]
        h.append("<table><tr>" + "".join("<th>%s</th>" % c for c in head) + "</tr>" +
                 "".join("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>" for r in rows) + "</table>")
    for en, ja in it["ex"]:
        h.append('<div class="ex"><p class="en">%s</p><p class="ja">%s</p></div>' % (en, ja))
    for k, cls, lab in (("tip", "tip", "ポイント"), ("warn", "warn", "注意"), ("line", "line", "線引き")):
        if it[k]:
            h.append('<p class="%s"><span class="lab">%s</span>%s</p>' % (cls, lab, it[k]))
    h.append("</article>")
    return "\n".join(h)


def main():
    out = ['<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>%s</title><style>%s</style></head><body>' % (TITLE, CSS)]
    out.append('<section class="cover"><h1>%s</h1><p class="sub">%s</p><p class="au">%s</p></section>' % (TITLE, SUBTITLE, AUTHOR))

    total = sum(len(s[1]) for m in PAGES for s in m.PAGE["sections"])
    counts = {"must": 0, "core": 0, "skip": 0}
    for m in PAGES:
        for _, its in m.PAGE["sections"]:
            for it in its:
                counts[it["tier"]] += 1

    out.append('<section class="pb"><h1 style="font-size:16pt;margin-bottom:5mm">はじめに</h1>'
               '<p>入試の英語には、無数の構文が登場します。しかし、全部を完璧にする必要はありません。'
               '大切なのは、<b>やることと、やらないことを決める</b>ことです。</p>'
               '<p>この本は、%d の構文を、次の3段階に分けて整理しています。</p>'
               '<table><tr><th>印</th><th>意味</th><th>数</th></tr>'
               '<tr><td><span class="tier tier-must">必須</span></td><td>共通テスト〜MARCH・地方国公立で確実に差がつかないよう、必ず押さえる</td><td>%d</td></tr>'
               '<tr><td><span class="tier tier-core">差がつく</span></td><td>できると他の受験生より一歩先に出られる</td><td>%d</td></tr>'
               '<tr><td><span class="tier tier-skip">ここまで不要</span></td><td>この範囲の入試では、深追いしなくてよい</td><td>%d</td></tr></table>'
               '<h2 style="font-size:12pt;margin:6mm 0 2mm">使い方</h2>'
               '<p>① 各項目の見出しの前にある <span class="chk"></span> は、「理解した」の記入欄です。理解できたらチェックを入れてください。</p>'
               '<p>② まず <span class="tier tier-must">必須</span> だけを1周します。次に <span class="tier tier-core">差がつく</span> に進みます。</p>'
               '<p>③ 各章の最後に確認問題があります。答えは章末の次のページにあります。答えを見る前に、書き込み欄に自分の答えを書いてください。</p>'
               '<p>④ <span class="tier tier-skip">ここまで不要</span> の項目は、読むだけで構いません。時間を使わないことも、得点への戦略です。</p>'
               '<p style="margin-top:5mm;font-size:8.6pt">※ 線引きは、共通テスト〜MARCH・地方国公立を志望校の目安にしています。志望校の過去問に頻出する構文は、「不要」であっても優先してください。</p>'
               '</section>' % (total, counts["must"], counts["core"], counts["skip"]))

    # 目次
    out.append('<section class="pb toc"><h1 style="font-size:16pt;margin-bottom:5mm">もくじ</h1><ul>')
    for k, m in enumerate(PAGES, 1):
        n = sum(len(s[1]) for s in m.PAGE["sections"])
        out.append('<li class="it"><span>第%d章　%s</span><span>%d項目</span></li>' % (k, m.PAGE["name"], n))
    out.append('<li class="it"><span>巻末　「ここまで不要」一覧</span><span></span></li>'
               '<li class="it"><span>巻末　メモ</span><span></span></li></ul></section>')

    for k, m in enumerate(PAGES, 1):
        P = m.PAGE
        out.append('<section class="chapter"><p class="no">第%d章</p><h1>%s</h1><p>%s</p></section>' % (k, P["name"], P["lead"]))
        for h2, its in P["sections"]:
            out.append('<h2 class="sec">%s</h2>' % h2)
            out.extend(item(it, 0) for it in its)
        quiz = P.get("quiz")
        if quiz:
            out.append('<section class="quiz pb"><h2 class="sec">確認問題</h2>')
            for n, (q, a) in enumerate(quiz, 1):
                out.append('<div class="q"><p class="qn">問%d</p><p>%s</p><div class="blank"></div><div class="blank"></div></div>' % (n, q))
            out.append('</section><section class="pb"><h2 class="sec">答え</h2>')
            for n, (q, a) in enumerate(quiz, 1):
                out.append('<div class="ans"><p class="qn">問%d</p>%s</div>' % (n, a))
            out.append('</section>')

    # 不要一覧
    rows = []
    for m in PAGES:
        for _, its in m.PAGE["sections"]:
            for it in its:
                if it["tier"] == "skip":
                    rows.append("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (it["title"], m.PAGE["name"], it["line"]))
    out.append('<section class="pb skiplist"><h1 style="font-size:16pt;margin-bottom:3mm">「ここまで不要」一覧</h1>'
               '<table><tr><th>不要なこと</th><th>分野</th><th>線引き</th></tr>%s</table></section>' % "".join(rows))

    out.append('<section class="memo"><h2 class="sec">メモ</h2>' + '<div class="l"></div>' * 20 + '</section>')
    out.append('<section class="pb legal"><h2 style="font-size:12pt;margin-bottom:3mm">この本について</h2>'
               '<p>例文と解説はすべて独自に作成したものです。志望校の出題傾向や、最新の入試情報は、各自で必ずご確認ください。</p>'
               '<p style="margin-top:60mm">%s<br>%s</p><p>著者　%s</p><p>©%s</p></section>' % (TITLE, SUBTITLE, AUTHOR, AUTHOR))
    out.append("</body></html>")

    html = ROOT / "book" / "book.html"
    html.write_text("\n".join(out), encoding="utf-8")
    pdf = ROOT / "book" / "interior.pdf"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--print-to-pdf=" + str(pdf), "file://" + str(html)], check=True, capture_output=True)
    print("項目数", total, counts, "->", pdf)


main()
