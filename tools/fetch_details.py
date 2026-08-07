#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サウナイキタイの施設ページから 住所/定休日/営業時間/料金/対象/座標 を取る"""
import html as ihtml
import json, os, re, subprocess, time

IDS = {
    88: "サウナ&カプセルホテル 北欧",
    1649: "みやこ湯",
    1823: "スパ&カプセル ニューウイング",
    4342: "ゆ家 和ごころ 吉の湯",
    1523: "湯乃泉 草加健康センター",
    1706: "サウナセンター鶯谷本店",
    2779: "サウナしきじ",
    2509: "ウェルビー栄",
    2507: "SaunaLab Nagoya",
    2385: "大磯プリンスホテル THERMAL SPA S.WAVE",
    1873: "天空のアジト マルシンスパ",
    4044: "サウナと天然温泉 湯らっくす",
    55: "OMO7旭川 by 星野リゾート サウナプラトー",
    98: "吹上温泉保養センター 白銀荘",
    1647: "豊島園 庭の湯",
    1802: "スパ&カプセルイン リアルサウナ錦糸町",
    1757: "東京ドーム天然温泉 Spa LaQua",
    9134: "黄金湯",
    5130: "青野原野呂ロッジキャンプ場",
    1687: "タイムズ スパ・レスタ",
    3110: "ニュージャパン 梅田店",
    2716: "五香湯",
    2721: "サウナの梅湯",
    3140: "神戸サウナ&スパ",
    1872: "亀島川温泉 新川の湯 ドーミーイン東京八丁堀",
    5405: "HOTEL Love Fairy",
    1459: "BIO-RESORT HOTEL&SPA O Park OGOSE",
    6060: "御船山楽園ホテル らかんの湯",
    2062: "秋山温泉",
    1693: "天然温泉 湯どんぶり栄湯",
    12818: "ROOFTOP",
    5357: "The Sauna",
    9806: "三ノ輪 改栄湯",
    79709: "HUBHUB下北沢",
    1054: "スパ・アルプス",
    7302: "田辺温熱保養所",
    2336: "大垣サウナ",
}

CACHE = "cache_sauna"
os.makedirs(CACHE, exist_ok=True)


def get(sid):
    p = os.path.join(CACHE, "%d.html" % sid)
    if not (os.path.exists(p) and os.path.getsize(p) > 5000):
        subprocess.run(["curl", "-s", "-o", p,
                        "https://sauna-ikitai.com/saunas/%d" % sid], check=True)
        time.sleep(1.2)
    return open(p, encoding="utf-8", errors="replace").read()


def texts(block):
    """<dd> 相当のブロックから行を取り出す"""
    t = re.sub(r'<br\s*/?>', '\n', block)
    t = re.sub(r'<[^>]+>', '\n', t)
    t = ihtml.unescape(t)
    return [l.strip() for l in t.split('\n') if l.strip()]


def field(h, label):
    m = re.search(r'<dt[^>]*>\s*' + re.escape(label) + r'\s*</dt>\s*<dd[^>]*>(.*?)</dd>', h, re.S)
    return texts(m.group(1)) if m else []


out = []
for sid, nm in IDS.items():
    h = get(sid)
    rec = {"id": sid, "key": nm}
    m = re.search(r'<p class="p-saunaDetailHeader_target">対象：(.*?)</p>', h)
    rec["target"] = m.group(1).strip() if m else ""
    m = re.search(r'<p class="p-saunaDetailHeader_caution">(.*?)</p>', h)
    rec["caution"] = m.group(1).strip() if m else ""
    m = re.search(r'<h1 class="p-saunaDetailHeader_name">(.*?)</h1>', h, re.S)
    if not m:
        m = re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S)
    rec["name"] = ihtml.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip() if m else nm
    m = re.search(r'data-lat="([\d.\-]+)"\s+data-lng="([\d.\-]+)"', h)
    if m:
        rec["lat"], rec["lng"] = float(m.group(1)), float(m.group(2))
    for label, key in [("施設タイプ", "type"), ("住所", "address"), ("TEL", "tel"),
                       ("HP", "hp"), ("定休日", "holiday"), ("営業時間", "hours"),
                       ("料金", "fee"), ("アクセス", "access")]:
        rec[key] = field(h, label)
    out.append(rec)
    print(sid, rec["name"], "|", rec["target"], "|", rec.get("lat"))

json.dump(out, open("ikitai.json", "w"), ensure_ascii=False, indent=1)
print("saved", len(out))
