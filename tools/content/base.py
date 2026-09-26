def i(id, tier, title, focus="", ex=None, tip="", warn="", line="", table=None, body=""):
    """1項目。tier: must / core / skip。文字列にはHTML(<b>,<mark>,<i>,<u>)を使ってよい。"""
    return dict(id=id, tier=tier, title=title, focus=focus, ex=ex or [], tip=tip,
                warn=warn, line=line, table=table, body=body)
