#!/usr/bin/env python3
"""全ページの項目(.item)と確認問題(.q)を走査して assets/manifest.js を作る。
項目を追加・削除したら、公開前にこのスクリプトを再実行すること。"""
import json, re, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
pages = [
    ("symbols.html", "記号"),
    ("grammar.html", "文法"),
    ("patterns.html", "構文"),
    ("before-reading.html", "長文の前に"),
    ("score-tips.html", "得点のコツ"),
]
items, page_info, ids = [], {}, set()
for fname, label in pages:
    html = (root / fname).read_text(encoding="utf-8")
    quizzes = len(re.findall(r'<details class="q"', html))
    page_info[fname] = {"name": label, "quizzes": quizzes}
    for m in re.finditer(r'<article class="item" data-tier="(must|core|skip)" id="([^"]+)">(.*?)</article>', html, re.S):
        tier, _id, body = m.groups()
        d = re.search(r'data-id="([^"]+)"', body)
        if not d:
            raise SystemExit(f"{fname}: #{_id} にチェックボックス(data-id)がありません")
        if d.group(1) in ids:
            raise SystemExit(f"data-id が重複しています: {d.group(1)}")
        ids.add(d.group(1))
        title = re.sub(r"<[^>]+>", "", re.search(r"<h3>(.*?)</h3>", body, re.S).group(1)).strip()
        items.append({"id": d.group(1), "tier": tier, "page": fname, "title": title})

out = "window.EIKO_ITEMS=" + json.dumps(items, ensure_ascii=False) + ";\nwindow.EIKO_PAGES=" + json.dumps(page_info, ensure_ascii=False) + ";\n"
(root / "assets" / "manifest.js").write_text(out, encoding="utf-8")
by = {}
for i in items:
    by[i["tier"]] = by.get(i["tier"], 0) + 1
print("items:", len(items), by, "quizzes:", sum(p["quizzes"] for p in page_info.values()))
