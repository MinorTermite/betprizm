#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET Marathon parser — Popular (auto) + fallback, with safe Google Sheets batch update

Почему раньше было 404:
- У Marathon у вас 404 на /su/popular и даже /su/popular/ (главная популярного).
- Но отдельные страницы popular (АПЛ/ЛаЛига/NBA/КХЛ/турниры кибера) при этом открываются.

Что делает эта версия:
1) Пытается автодискаверить "популярные" не только с /su/popular/,
   но и с корневых разделов:
   /su/popular/Football/
   /su/popular/Basketball/
   /su/popular/Ice+Hockey/
   /su/popular/Tennis/
   /su/popular/e-Sports/
   Если и они недоступны — уходит в fallback список (топ-лиги/КХЛ/NBA + якорные Dota/CS2).

2) Парсинг:
   - Football: 1, X, 2, 1X, 12, X2
   - Остальные (NBA/КХЛ/теннис): 2-way (П1/П2), X=0.00, 1X/12/X2=0.00
   - eSports: 2-way победитель матча (форы/тоталы/карты игнорируются), X=0.00

3) Google Sheets: ОДИН batch update (clear + update A1) + защита от 429:
   - если словили 429, печатаем предупреждение и не падаем.
   - можно отключить запись в Sheets флагом WRITE_SHEETS=0

Установка:
  pip install -U requests beautifulsoup4 lxml gspread google-auth

Запуск:
  python marathon_to_sheets.py
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# =========================
# CONFIG
# =========================
BASE = "https://www.marathonbet.ru"

# Попытка автодискавери (главная может быть 404 — поэтому добавляем корни)
POPULAR_ROOTS = [
    f"{BASE}/su/popular/",
    f"{BASE}/su/popular/Football/",
    f"{BASE}/su/popular/Basketball/",
    f"{BASE}/su/popular/Ice+Hockey/",
    f"{BASE}/su/popular/Tennis/",
    f"{BASE}/su/popular/e-Sports/",
]

# Fallback "самое популярное" (если автодискавери не смогло найти ссылки)
POPULAR_FALLBACK = [
    ("football", "Англия. Премьер-лига", f"{BASE}/su/popular/Football/England/Premier%2BLeague%2B-%2B21520?lid=15600999"),
    ("football", "Испания. Ла Лига", f"{BASE}/su/popular/Football/Spain/Primera%2BDivision%2B-%2B8736?lid=26570477"),
    ("football", "Италия. Серия A", f"{BASE}/su/popular/Football/Italy/Serie%2BA%2B-%2B22434?lid=15601013"),
    ("football", "Германия. Бундеслига", f"{BASE}/su/popular/Football/Germany/Bundesliga%2B-%2B22436"),
    ("football", "Франция. Лига 1", f"{BASE}/su/popular/Football/France/Ligue%2B1%2B-%2B21533?interval=ALL_TIME"),
    ("hockey",  "КХЛ", f"{BASE}/su/popular/Ice%2BHockey/KHL%2B-%2B52309?lid=15577535"),
    ("basket",  "NBA", f"{BASE}/su/popular/Basketball/NBA%2B-%2B69367?lid=15577646"),
    # eSports anchors (можно расширять; если конкретный турнир 404 — просто заменишь ссылку)
    ("esports", "Dota 2. BLAST Slam", f"{BASE}/su/popular/e-Sports/Dota+2/BLAST+Slam+-+20603920?lid=20621739"),
]

# Ключевые слова чтобы из найденных ссылок выбрать "популярные" (если их много)
POPULAR_KEYWORDS = [
    "Россия. Премьер-лига", "КХЛ", "Испания. Ла Лига", "Англия. Премьер-лига",
    "Италия. Серия", "Германия. Бундеслига", "Франция. Лига", "NBA", "Лига ВТБ",
    "CS2", "Counter-Strike", "Dota 2", "Valorant", "LoL", "WTA", "ATP",
    "Топ-клубы", "Лига чемпионов", "Лига Европы"
]

# Output
OUT_JSON = "matches.json"

# Google Sheets (опционально)
WRITE_SHEETS = os.getenv("WRITE_SHEETS", "1") != "0"
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
SHEET_NAME = os.getenv("SHEET_NAME", "Matches")
CREDS_FILE = os.getenv("CREDS_FILE", "credentials.json")

# Requests
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
TIMEOUT = 25


# =========================
# HTTP
# =========================
def http_get(url: str) -> str:
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru,en;q=0.9",
        "Connection": "keep-alive",
    }
    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def as_float(s: str) -> Optional[float]:
    if s is None:
        return None
    s = s.replace(",", ".").strip()
    if not s:
        return None
    try:
        return float(s)
    except:
        return None


@dataclass
class Link:
    sport: str
    title: str
    url: str


def detect_sport_from_href(href: str, text: str) -> str:
    h = (href or "").lower()
    t = (text or "").lower()
    if "e-sports" in h or "киберспорт" in t or "dota" in h or "counter-strike" in h or "cs2" in h:
        return "esports"
    if "/football/" in h:
        return "football"
    if "ice%2bhockey" in h or "/ice" in h or "hockey" in h or "кхл" in t:
        return "hockey"
    if "basketball" in h or "nba" in t:
        return "basket"
    if "tennis" in h or "atp" in t or "wta" in t:
        return "tennis"
    return "other"


def discover_popular_links() -> List[Link]:
    collected: List[Link] = []
    seen = set()

    for root in POPULAR_ROOTS:
        try:
            html = http_get(root)
        except Exception as e:
            print(f"[WARN] root недоступен: {root} ({e})")
            continue

        soup = BeautifulSoup(html, "lxml")
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            title = norm_space(a.get_text(" "))
            if not href or not title:
                continue
            if "/su/popular/" not in href:
                continue

            full = urljoin(BASE, href)
            sport = detect_sport_from_href(href, title)

            # фильтр по ключам (чтобы не тянуть весь сайт)
            if not any(k.lower() in title.lower() for k in POPULAR_KEYWORDS):
                if sport != "esports":
                    continue

            if full in seen:
                continue
            seen.add(full)
            collected.append(Link(sport=sport, title=title, url=full))

    return collected


# =========================
# PARSERS
# =========================

def parse_football_table(html: str) -> List[dict]:
    soup = BeautifulSoup(html, "lxml")
    out = []

    for row in soup.select("tr"):
        txt = norm_space(row.get_text(" "))
        if not txt:
            continue

        m_id = re.search(r"\+(\d{2,})", txt)
        if not m_id:
            continue
        event_id = m_id.group(1)

        tds = [norm_space(td.get_text(" ")) for td in row.select("td")]
        odds: List[float] = []
        for td in tds:
            if re.fullmatch(r"\d+(?:[.,]\d+)?", td):
                f = as_float(td)
                if f is not None:
                    odds.append(f)

        if len(odds) < 3:
            continue

        p1 = odds[0]
        x = odds[1] if len(odds) > 1 else 0.0
        p2 = odds[2] if len(odds) > 2 else 0.0
        p1x = odds[3] if len(odds) > 3 else 0.0
        p12 = odds[4] if len(odds) > 4 else 0.0
        x2 = odds[5] if len(odds) > 5 else 0.0

        t1 = t2 = ""
        m_teams = re.search(r"1\.\s*(.+?)\s+2\.\s*(.+?)(?:\s+\+|\s+\d{1,2}:\d{2}|\s+\d{1,2}\s+\w+)", txt)
        if m_teams:
            t1 = norm_space(m_teams.group(1))
            t2 = norm_space(m_teams.group(2))

        m_time = re.search(r"\b(\d{1,2}:\d{2})\b", txt)
        time_str = m_time.group(1) if m_time else ""

        out.append({
            "sport": "football",
            "league": "",
            "id": event_id,
            "date": "",
            "time": time_str,
            "team1": t1,
            "team2": t2,
            "p1": f"{p1:.3g}" if p1 else "0.00",
            "x": f"{x:.3g}" if x else "0.00",
            "p2": f"{p2:.3g}" if p2 else "0.00",
            "p1x": f"{p1x:.3g}" if p1x else "0.00",
            "p12": f"{p12:.3g}" if p12 else "0.00",
            "px2": f"{x2:.3g}" if x2 else "0.00",
        })

    return out


def parse_2way_winner(html: str, sport: str) -> List[dict]:
    soup = BeautifulSoup(html, "lxml")
    out = []

    for row in soup.select("tr"):
        txt = norm_space(row.get_text(" "))
        if not txt:
            continue
        m_id = re.search(r"\+(\d{2,})", txt)
        if not m_id:
            continue
        event_id = m_id.group(1)

        nums = [as_float(x) for x in re.findall(r"\b\d+(?:[.,]\d+)?\b", txt)]
        nums = [x for x in nums if x is not None]
        if len(nums) < 2:
            continue

        t1 = t2 = ""
        m_teams = re.search(r"1\.\s*(.+?)\s+2\.\s*(.+?)(?:\s+\+|\s+\d{1,2}:\d{2}|\s+\d{1,2}\s+\w+)", txt)
        if m_teams:
            t1 = norm_space(m_teams.group(1))
            t2 = norm_space(m_teams.group(2))

        m_time = re.search(r"\b(\d{1,2}:\d{2})\b", txt)
        time_str = m_time.group(1) if m_time else ""

        p1, p2 = nums[0], nums[1]
        out.append({
            "sport": sport,
            "league": "",
            "id": event_id,
            "date": "",
            "time": time_str,
            "team1": t1,
            "team2": t2,
            "p1": f"{p1:.3g}" if p1 else "0.00",
            "x": "0.00",
            "p2": f"{p2:.3g}" if p2 else "0.00",
            "p1x": "0.00",
            "p12": "0.00",
            "px2": "0.00",
        })

    return out


def parse_esports_winner_only(html: str, league_title: str) -> List[dict]:
    soup = BeautifulSoup(html, "lxml")
    out = []

    for row in soup.select("tr"):
        txt = norm_space(row.get_text(" "))
        if not txt:
            continue
        if "(" in txt or ")" in txt:
            continue

        m_id = re.search(r"\+(\d{2,})", txt)
        if not m_id:
            continue
        event_id = m_id.group(1)

        nums = [as_float(x) for x in re.findall(r"\b\d+(?:[.,]\d+)?\b", txt)]
        nums = [x for x in nums if x is not None]
        if len(nums) < 2:
            continue

        t1 = t2 = ""
        m_teams = re.search(r"1\.\s*(.+?)\s+2\.\s*(.+?)(?:\s+\+|\s+\d{1,2}:\d{2}|\s+\d{1,2}\s+\w+)", txt)
        if m_teams:
            t1 = norm_space(m_teams.group(1))
            t2 = norm_space(m_teams.group(2))

        m_time = re.search(r"\b(\d{1,2}:\d{2})\b", txt)
        time_str = m_time.group(1) if m_time else ""

        p1, p2 = nums[0], nums[1]
        out.append({
            "sport": "esports",
            "league": league_title,
            "id": event_id,
            "date": "",
            "time": time_str,
            "team1": t1,
            "team2": t2,
            "p1": f"{p1:.3g}" if p1 else "0.00",
            "x": "0.00",
            "p2": f"{p2:.3g}" if p2 else "0.00",
            "p1x": "0.00",
            "p12": "0.00",
            "px2": "0.00",
        })

    return out


def update_google_sheets(rows: List[List[str]]) -> None:
    if not WRITE_SHEETS:
        print("[INFO] Google Sheets: отключено (WRITE_SHEETS=0).")
        return
    if not SPREADSHEET_ID:
        print("[WARN] SPREADSHEET_ID пустой — пропуск записи в Sheets.")
        return

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except Exception:
        print("[WARN] Google Sheets libs не установлены — пропуск записи.")
        return

    if not os.path.exists(CREDS_FILE):
        print(f"[WARN] credentials.json не найден ({CREDS_FILE}) — пропуск записи в Sheets.")
        return

    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
        gc = gspread.authorize(creds)
        ws = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

        ws.clear()
        ws.update("A1", rows, value_input_option="RAW")
        print("[OK] Google Sheets обновлён (batch).")
    except Exception as e:
        msg = str(e)
        if "429" in msg or "Quota exceeded" in msg:
            print("[WARN] Google Sheets не обновлён: квота 429 (попробуй позже).")
        else:
            print(f"[WARN] Google Sheets не обновлён: {e}")


def main() -> None:
    links = discover_popular_links()
    if not links:
        print("[WARN] Автодискавери не сработал — беру fallback список.")
        links = [Link(s, t, u) for (s, t, u) in POPULAR_FALLBACK]

    print(f"[OK] Источников для парсинга: {len(links)}")

    all_items: List[dict] = []
    for ln in links:
        print(f"[INFO] Парсинг: {ln.title}")
        try:
            html = http_get(ln.url)
            if ln.sport == "football":
                items = parse_football_table(html)
                for it in items:
                    it["league"] = ln.title
                print(f"[OK]  Матчей: {len(items)}")
            elif ln.sport == "esports":
                items = parse_esports_winner_only(html, ln.title)
                print(f"[OK]  Событий: {len(items)}")
            else:
                items = parse_2way_winner(html, ln.sport)
                for it in items:
                    it["league"] = ln.title
                print(f"[OK]  Событий: {len(items)}")
            all_items.extend(items)
        except Exception as e:
            print(f"[ERR] Пропущено ({ln.title}): {e}")

    # Dedup by (sport,id)
    uniq = {}
    for m in all_items:
        key = f"{m.get('sport','')}:{m.get('id','')}"
        uniq[key] = m
    all_items = list(uniq.values())

    payload = {
        "last_update": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "matches": all_items,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[OK] JSON обновлён: {OUT_JSON} (событий: {len(all_items)})")

    header = ["sport","league","id","date","time","team1","team2","1","X","2","1X","12","X2"]
    rows = [header]
    for m in all_items:
        rows.append([
            m.get("sport",""),
            m.get("league",""),
            m.get("id",""),
            m.get("date",""),
            m.get("time",""),
            m.get("team1",""),
            m.get("team2",""),
            m.get("p1","0.00"),
            m.get("x","0.00"),
            m.get("p2","0.00"),
            m.get("p1x","0.00"),
            m.get("p12","0.00"),
            m.get("px2","0.00"),
        ])
    update_google_sheets(rows)


if __name__ == "__main__":
    main()
