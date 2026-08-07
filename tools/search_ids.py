#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サ道 登場施設をサウナイキタイで検索して候補IDを出す"""
import json, re, subprocess, sys, time, urllib.parse, os

KEYWORDS = [
    "サウナ&カプセルホテル 北欧",
    "みやこ湯",
    "ニューウイング",
    "吉の湯",
    "草加健康センター",
    "サウナセンター",
    "太古の湯 グリーンサウナ",
    "サウナしきじ",
    "ウェルビー栄",
    "サウナラボ 名古屋",
    "THERMAL SPA S.WAVE",
    "マルシンスパ",
    "湯らっくす",
    "OMO7旭川",
    "白銀荘",
    "豊島園 庭の湯",
    "サウナ錦糸町",
    "スパ ラクーア",
    "黄金湯",
    "野呂ロッジ",
    "タイムズ スパ・レスタ",
    "ニュージャパン梅田",
    "五香湯",
    "サウナの梅湯",
    "神戸サウナ&スパ",
    "ドーミーイン東京八丁堀",
    "Love fairy 町田",
    "O Park OGOSE",
    "御船山楽園ホテル らかんの湯",
    "秋山温泉",
    "湯どんぶり栄湯",
    "ROOFTOP 西荻",
    "The Sauna 野尻湖",
    "改栄湯",
    "HUBHUB 下北沢",
    "スパ・アルプス",
    "LUOVA SAUNA",
    "田辺温熱保養所",
    "大垣サウナ",
]

CACHE = "cache_search"
os.makedirs(CACHE, exist_ok=True)


def fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return open(path, encoding="utf-8", errors="replace").read()
    subprocess.run(["curl", "-s", "-o", path, url], check=True)
    time.sleep(1.0)
    return open(path, encoding="utf-8", errors="replace").read()


ITEM = re.compile(
    r'<a href="https://sauna-ikitai\.com/saunas/(\d+)"></a>(.*?)</address>', re.S)

out = {}
for kw in KEYWORDS:
    url = "https://sauna-ikitai.com/search?keyword=" + urllib.parse.quote(kw)
    path = os.path.join(CACHE, re.sub(r'[^\w]', '_', kw) + ".html")
    h = fetch(url, path)
    cands = []
    for m in ITEM.finditer(h):
        block = re.sub(r'<[^>]+>', ' ', m.group(2))
        block = re.sub(r'\s+', ' ', block).strip()
        cands.append((m.group(1), block[:90]))
    out[kw] = cands[:4]
    print("■", kw)
    for c in cands[:4]:
        print("   ", c[0], c[1])
json.dump(out, open("search_candidates.json", "w"), ensure_ascii=False, indent=1)
