#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サウナイキタイの検索ページから施設の情報を取って ikitai.json に足す。

施設詳細ページ（/saunas/<id>）は AWS WAF の CAPTCHA が出るようになって取れない。
検索ページ（/search?keyword=）には地図表示用の JSON（window.__MAP_DATA）が
埋まっていて、座標・住所・男女別の可否・定休日・営業時間まで入っているので、そちらを使う。
公式サイトのURLと電話番号だけはこのJSONに無いので、手で足す（OFFICIAL）。

  python3 tools/fetch_from_search.py 高輪SAUNAS 改良湯 ...
"""
import json, os, re, subprocess, sys, time, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IKITAI = os.path.join(ROOT, "tools", "ikitai.json")
CACHE = os.path.join(ROOT, "tools", "cache", "search")
MAP_DATA = re.compile(r'window\.__MAP_DATA\s*=\s*(\[.*?\]);\s*\n', re.S)

# __MAP_DATA に入っていないぶん。公式サイトで確かめて書く。
OFFICIAL = {
    100877: ("https://saunas-saunas.com/takanawa/", ""),      # 高輪SAUNAS
    1934: ("https://kairyou-yu.com/", ""),                     # 改良湯
    1846: ("https://www.jexer.jp/fitness/shinjuku/", "03-5333-2101"),  # ジェクサー新宿
}


def search(keyword):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, re.sub(r'[^\w]', '_', keyword) + ".html")
    if not (os.path.exists(p) and "__MAP_DATA" in open(p, encoding="utf-8", errors="replace").read()):
        subprocess.run(["curl", "-sS", "--retry", "2", "-o", p,
                        "https://sauna-ikitai.com/search?keyword=" + urllib.parse.quote(keyword)],
                       check=True)
        time.sleep(1.5)
    h = open(p, encoding="utf-8", errors="replace").read()
    m = MAP_DATA.search(h)
    if not m:
        raise RuntimeError("__MAP_DATA が無い（CAPTCHAの可能性）: " + keyword)
    return json.loads(m.group(1))


def to_record(x):
    """__MAP_DATA の1件を ikitai.json の形に直す"""
    male, female = x.get("is_male_available"), x.get("is_female_available")
    target = "対象：男女"
    if male and not female:
        target = "男性専用"
    elif female and not male:
        target = "女性専用"

    area = "%s - %s %s" % (x.get("facility_type_jp") or "その他",
                           x.get("prefecture", ""), x.get("address1", ""))
    if x.get("guest_type") == "guests_only":
        area += " 宿泊者限定"
    elif x.get("guest_type") == "members_only":
        area += " 会員のみ"
    if x.get("require_booking"):
        area += " 事前予約制"

    hp, tel = OFFICIAL.get(x["id"], ("", ""))
    r = {
        "id": x["id"], "key": x["name"], "target": target, "caution": "",
        "area": area.strip(), "name": x["name"],
        "fullname": [x["name"]],
        "type": [x.get("facility_type_jp") or "その他"],
        "address": [("%s %s" % (x.get("prefecture", ""), x.get("address1", ""))).strip(),
                    ((x.get("address2") or "") + (x.get("address3") or "")).strip()],
        "access": [], "tel": [tel] if tel else [], "hp": [hp] if hp else [],
        "holiday": [x.get("regular_holiday_text") or "未確認"],
        "fee": ["大人 %d円〜" % x["min_fee"]] if x.get("min_fee") else [],
    }
    if x.get("geolat"):
        r["lat"], r["lng"] = x["geolat"], x["geolong"]
    if x.get("business_hours"):
        r["hours_blocks"] = [["営業時間", [l.strip() for l in
                                        str(x["business_hours"]).replace("\r", "").split("\n")
                                        if l.strip()]]]
    return r


def norm(s):
    return re.sub(r'[\s　・＆&\-–—]', '', s).lower()


def pick(kw, hits):
    """先頭ヒットを鵜呑みにすると別施設を拾う。名前が噛み合うものだけ採る。
    `キーワード=ID` と書けば、その施設を名指しできる。"""
    if "=" in kw:
        want = int(kw.split("=")[-1])
        return next((h for h in hits if h["id"] == want), None)
    # 地名で引くと無関係な施設が先頭に来る（「日暮里」→「スポーツクラブNAS 西日暮里」）。
    # 施設名の頭から一致しているものだけ採る。
    k = norm(kw)
    named = [h for h in hits if norm(h["name"]).startswith(k) or norm(h["name"]) == k]
    return named[0] if len(named) == 1 else None


def main(keywords):
    data = json.load(open(IKITAI))
    by_id = {r["id"]: r for r in data}
    for kw in keywords:
        hits = search(kw.split("=")[0])
        if not hits:
            print("!! 見つからない:", kw)
            continue
        if len(hits) > 1:
            print("   候補が %d 件:" % len(hits),
                  "／".join("%s(%d)" % (h["name"], h["id"]) for h in hits[:5]))
        x = pick(kw, hits)
        if x is None:
            print("!! どれか分からないので飛ばす:", kw,
                  "／".join("%s(%d)" % (h["name"], h["id"]) for h in hits[:5]))
            continue
        r = to_record(x)
        mark = "更新" if r["id"] in by_id else "追加"
        by_id[r["id"]] = r
        print("%s %6d %s（%s%s・%s）" % (mark, r["id"], r["name"],
                                        x.get("prefecture", ""), x.get("address1", ""),
                                        r["target"]))
    out = sorted(by_id.values(), key=lambda r: r["id"])
    json.dump(out, open(IKITAI, "w"), ensure_ascii=False, indent=1)
    print("ikitai.json: %d 件" % len(out))


if __name__ == "__main__":
    main(sys.argv[1:] or ["高輪SAUNAS"])
