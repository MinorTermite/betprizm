#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET Marathon parser — MAXIMUM POPULAR LEAGUES + LIVE (OPTIMIZED & SAFE)
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import time
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

BASE = "https://www.marathonbet.ru"

POPULAR_FALLBACK = [
    ("football", "Лига чемпионов УЕФА", f"{BASE}/su/popular/Football/UEFA/Champions%2BLeague%2B-%2B26493"),
    ("football", "Лига Европы УЕФА", f"{BASE}/su/popular/Football/UEFA/Europa%2BLeague%2B-%2B26494"),
    ("football", "Лига конференций УЕФА", f"{BASE}/su/popular/Football/UEFA/Conference%2BLeague%2B-%2B26495"),
    ("football", "Англия. Премьер-лига", f"{BASE}/su/popular/Football/England/Premier%2BLeague%2B-%2B21520?lid=15600999"),
    ("football", "Испания. Ла Лига", f"{BASE}/su/popular/Football/Spain/Primera%2BDivision%2B-%2B8736?lid=26570477"),
    ("football", "Италия. Серия A", f"{BASE}/su/popular/Football/Italy/Serie%2BA%2B-%2B22434?lid=15601013"),
    ("football", "Германия. Бундеслига", f"{BASE}/su/popular/Football/Germany/Bundesliga%2B-%2B22436"),
    ("football", "Франция. Лига 1", f"{BASE}/su/popular/Football/France/Ligue%2B1%2B-%2B21533?interval=ALL_TIME"),
    ("football", "Россия. Премьер-лига", f"{BASE}/su/betting/Football/Russia/Premier%2BLeague%2B-%2B22433"),
    ("football", "Россия. 1-я лига", f"{BASE}/su/betting/Football/Russia/1st%2BLeague%2B-%2B45766"),
    ("football", "Англия. Чемпионшип", f"{BASE}/su/betting/Football/England/Championship%2B-%2B21521"),
    ("football", "Испания. Сегунда", f"{BASE}/su/betting/Football/Spain/Segunda%2BDivision%2B-%2B8737"),
    ("football", "Италия. Серия B", f"{BASE}/su/betting/Football/Italy/Serie%2BB%2B-%2B22435"),
    ("football", "Германия. 2. Бундеслига", f"{BASE}/su/betting/Football/Germany/2.%2BBundesliga%2B-%2B22437"),
    ("football", "Франция. Лига 2", f"{BASE}/su/betting/Football/France/Ligue%2B2%2B-%2B21534"),
    ("hockey", "КХЛ", f"{BASE}/su/popular/Ice%2BHockey/KHL%2B-%2B52309?lid=15577535"),
    ("hockey", "НХЛ", f"{BASE}/su/popular/Ice%2BHockey/NHL%2B-%2B52310"),
    ("basket", "NBA", f"{BASE}/su/popular/Basketball/NBA%2B-%2B69367?lid=15577646"),
    ("basket", "Евролига", f"{BASE}/su/betting/Basketball/Europe/EuroLeague%2B-%2B69368"),
    ("tennis", "Теннис (ATP/WTA/ITF)", f"{BASE}/su/betting/Tennis/"),
    ("volleyball", "CEV. Лига чемпионов", f"{BASE}/su/betting/Volleyball/Europe/CEV%2BChampions%2BLeague%2B-%2B77777"),
    ("mma", "UFC", f"{BASE}/su/betting/MMA/UFC%2B-%2B99999"),
    ("esports", "CS2. Major", f"{BASE}/su/betting/e-Sports/Counter-Strike/Major%2B-%2B111111"),
    ("esports", "Dota 2. The International", f"{BASE}/su/betting/e-Sports/Dota%2B2/The%2BInternational%2B-%2B111115"),
]

LIVE_URLS = []
OUT_JSON = "matches.json"

WRITE_SHEETS = os.getenv("WRITE_SHEETS", "1") != "0"
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
SHEET_NAME = os.getenv("SHEET_NAME", "Matches")
CREDS_FILE = os.getenv("CREDS_FILE", "credentials.json")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
TIMEOUT = 25

# Настраиваем сессию под многопоточность
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=3, pool_maxsize=3)
session.mount('https://', adapter)
session.headers.update({
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru,en;q=0.9",
    "Connection": "keep-alive",
})

def http_get(url: str) -> str:
    r = session.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text

def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def clean_name(s: str) -> str:
    if not s: return ""
    s = re.sub(r"\(?Первый матч\s+\d+:\d+\)?", "", s, flags=re.I)
    s = re.sub(r"\(?счет\s+\d+:\d+\)?", "", s, flags=re.I)
    s = re.sub(r"\(?серия\s+\d+:\d+\)?", "", s, flags=re.I)
    s = re.sub(r"\(\d{1,2}:\d{1,2}(?:,\s*\d{1,2}:\d{1,2})*\)", "", s)
    s = re.sub(r"\d+:\d+", "", s).strip()
    s = re.sub(r"\bматч\b", "", s, flags=re.I).strip()
    return re.sub(r"\s+", " ", s).strip(" -/\\")

def as_float(s: str) -> Optional[float]:
    if s is None: return None
    s = s.replace(",", ".").strip()
    if not s: return None
    try: return float(s)
    except: return None

def parse_football_table(html: str) -> List[dict]:
    soup = BeautifulSoup(html, "lxml")
    out = []
    for row in soup.select("div.coupon-row"):
        event_id = row.get("data-event-treeid") or row.get("data-event-treeId") or row.get("data-event-id")
        if not event_id: continue
        member_links = row.select("a.member-link")
        if len(member_links) < 2: continue
            
        t1 = clean_name(member_links[0].get_text())
        t2 = clean_name(member_links[1].get_text())
        m_link = member_links[0].get("href")
        match_url = urljoin(BASE, m_link) if m_link else ""

        time_el = row.select_one(".date-wrapper") or row.select_one(".date")
        time_txt = norm_space(time_el.get_text()) if time_el else ""
        date_str, time_str = "", ""
        m_dt = re.search(r"(\d{1,2}\s+[а-яёА-Я]{2,4})\s+(\d{1,2}:\d{2})", time_txt)
        if m_dt:
            date_str, time_str = m_dt.group(1), m_dt.group(2)
        else:
            time_str = time_txt if ":" in time_txt else ""

        odds_dict = {}
        key_map = {
            "Match_Result.1": "p1", "Match_Result.draw": "x", "Match_Result.3": "p2",
            "Result.HD": "p1x", "Result.HA": "p12", "Result.AD": "px2"
        }
        for btn in row.select(".selection-link"):
            sel_key = btn.get("data-selection-key", "")
            for suffix, field in key_map.items():
                if sel_key.endswith(suffix):
                    val = btn.get_text().strip()
                    odds_dict[field] = f"{as_float(val):.3g}" if as_float(val) else "0.00"
                    break

        out.append({
            "sport": "football", "league": "", "id": event_id,
            "date": date_str, "time": time_str, "team1": t1, "team2": t2,
            "match_url": match_url,
            "p1": odds_dict.get("p1", "0.00"), "x": odds_dict.get("x", "0.00"), "p2": odds_dict.get("p2", "0.00"),
            "p1x": odds_dict.get("p1x", "0.00"), "p12": odds_dict.get("p12", "0.00"), "px2": odds_dict.get("px2", "0.00"),
        })
    return out

def parse_2way_winner(html: str, sport: str) -> List[dict]:
    soup = BeautifulSoup(html, "lxml")
    out = []
    for row in soup.select("div.coupon-row"):
        event_id = row.get("data-event-treeid") or row.get("data-event-treeId") or row.get("data-event-id")
        if not event_id: continue
            
        member_links = row.select("a.member-link")
        m_link, t1, t2 = "", "", ""
        if len(member_links) >= 2:
            t1 = clean_name(member_links[0].get_text())
            t2 = clean_name(member_links[1].get_text())
            m_link = member_links[0].get("href")
        else:
            event_name = row.get("data-event-name", "")
            if " - " in event_name: t1, t2 = [clean_name(x) for x in event_name.split(" - ", 1)]
            elif " vs " in event_name: t1, t2 = [clean_name(x) for x in event_name.split(" vs ", 1)]
            
            m_link_el = row.select_one("a[href*='/betting/']")
            if m_link_el: m_link = m_link_el.get("href")

        if not t1 or not t2: continue
        match_url = urljoin(BASE, m_link) if m_link else ""

        time_el = row.select_one(".date-wrapper") or row.select_one(".date")
        time_txt = norm_space(time_el.get_text()) if time_el else ""
        date_str, time_str = "", ""
        m_dt = re.search(r"(\d{1,2}\s+[а-яёА-Я]{2,4})\s+(\d{1,2}:\d{2})", time_txt)
        if m_dt:
            date_str, time_str = m_dt.group(1), m_dt.group(2)
        else:
            time_str = time_txt if ":" in time_txt else ""

        odds_btns = row.select(".selection-link")
        if len(odds_btns) < 2: odds_btns = row.select(".price")
        p1_val = x_val = p2_val = 0.0
        if len(odds_btns) >= 3:
            p1_val = as_float(odds_btns[0].get_text())
            x_val  = as_float(odds_btns[1].get_text())
            p2_val = as_float(odds_btns[2].get_text())
        elif len(odds_btns) == 2:
            p1_val = as_float(odds_btns[0].get_text())
            p2_val = as_float(odds_btns[1].get_text())

        # Пропускаем матчи без ссылки — это LIVE-матчи других видов спорта,
        # которые MarathonBet показывает вверху популярных страниц
        if not match_url:
            continue

        out.append({
            "sport": sport, "league": "", "id": event_id,
            "date": date_str, "time": time_str, "team1": t1, "team2": t2,
            "match_url": match_url,
            "p1": f"{p1_val:.3g}" if p1_val else "0.00",
            "x": f"{x_val:.3g}" if x_val else "—",
            "p2": f"{p2_val:.3g}" if p2_val else "0.00",
            "p1x": "—", "p12": "—", "px2": "—",
        })
    return out

def fetch_and_parse(sport: str, title: str, url: str) -> tuple:
    time.sleep(0.5) # Пауза для защиты от бана
    try:
        html = http_get(url)
        if sport == "football":
            items = parse_football_table(html)
            for it in items: it["league"] = title
            cat_m = re.search(r'/(?:betting|popular)/Football/(.+?)(?:%2B|\+)?-(?:%2B|\+)?\d+', url, re.I)
            if cat_m:
                cat_path = cat_m.group(1).replace('%2B', ' ').replace('+', ' ').lower().strip()
                def url_ok(match_url, cat_path=cat_path):
                    mu = match_url.replace('+', ' ').lower()
                    if cat_path in mu: return True
                    if cat_path.startswith('uefa/'): return ('europe/' + cat_path[5:]) in mu
                    return False
                items = [it for it in items if url_ok(it.get('match_url', ''))]
            return (title, items, None)
        elif sport == "esports":
            items = parse_2way_winner(html, "esports")
            for it in items: it["league"] = title  # исправляем: лига не устанавливалась
            return (title, items, None)
        else:
            items = parse_2way_winner(html, sport)
            for it in items: it["league"] = title
            return (title, items, None)
    except Exception as e:
        return (title, [], str(e))

def main() -> None:
    print("=" * 60)
    print("PRIZMBET Marathon Parser — SAFE THREADING MODE")
    print("=" * 60)
    
    all_items: List[dict] = []
    success_count = 0
    error_count = 0
    
    # max_workers=3 спасает от блокировок
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fetch_and_parse, s, t, u): (s, t, u) for s, t, u in POPULAR_FALLBACK}
        for future in as_completed(futures):
            title, items, err = future.result()
            if err:
                error_count += 1
                print(f"[ERR] Пропущено ({title}): {err}")
            else:
                print(f"[OK] {title} - Событий: {len(items)}")
                all_items.extend(items)
                if len(items) > 0:
                    success_count += 1

    uniq = {}
    for m in all_items:
        m_id = m.get('id', '')
        if m_id and m_id not in uniq:
            uniq[m_id] = m

    all_items = list(uniq.values())
    payload = {
        "last_update": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "matches": all_items,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Всего матчей: {len(all_items)} (Лиг: {success_count})")

if __name__ == "__main__":
    main()