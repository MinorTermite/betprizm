#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
УЛУЧШЕННЫЙ ПАРСЕР PRIZMBET для Marathon
- Правильный формат даты и времени
- Корректные названия команд для всех видов спорта
- Формат данных как в Google Sheets
"""

import datetime as dt
import json
import os
import re
from typing import List, Optional
import requests
from bs4 import BeautifulSoup

# =========================
# CONFIG
# =========================
BASE = "https://www.marathonbet.ru"

# Источники для парсинга
SOURCES = [
    ("football", "Англия. Премьер-лига", f"{BASE}/su/popular/Football/England/Premier%2BLeague%2B-%2B21520"),
    ("football", "Испания. Ла Лига", f"{BASE}/su/popular/Football/Spain/Primera%2BDivision%2B-%2B8736"),
    ("football", "Италия. Серия A", f"{BASE}/su/popular/Football/Italy/Serie%2BA%2B-%2B22434"),
    ("football", "Германия. Бундеслига", f"{BASE}/su/popular/Football/Germany/Bundesliga%2B-%2B22436"),
    ("football", "Франция. Лига 1", f"{BASE}/su/popular/Football/France/Ligue%2B1%2B-%2B21533"),
    ("football", "Лига чемпионов УЕФА", f"{BASE}/su/popular/Football/UEFA/Champions%2BLeague%2B-%2B52287"),
    ("football", "Лига Европы УЕФА", f"{BASE}/su/popular/Football/UEFA/Europa%2BLeague%2B-%2B14"),
    ("hockey", "КХЛ", f"{BASE}/su/popular/Ice%2BHockey/KHL%2B-%2B52309"),
    ("hockey", "NHL", f"{BASE}/su/popular/Ice%2BHockey/NHL%2B-%2B69368"),
    ("basket", "NBA", f"{BASE}/su/popular/Basketball/NBA%2B-%2B69367"),
    ("basket", "Евролига", f"{BASE}/su/popular/Basketball/Euroleague%2B-%2B22469"),
    ("esports", "Dota 2", f"{BASE}/su/popular/e-Sports/Dota+2/"),
    ("esports", "CS2", f"{BASE}/su/popular/e-Sports/Counter-Strike+2/"),
]

OUT_JSON = "matches.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
TIMEOUT = 25

# =========================
# UTILS
# =========================
def http_get(url: str) -> str:
    """HTTP GET запрос"""
    headers = {
        "User-Agent": UA,
        "Accept": "text/html",
        "Accept-Language": "ru,en;q=0.9",
    }
    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text

def norm(s: str) -> str:
    """Нормализация текста"""
    return re.sub(r'\s+', ' ', (s or "").strip())

def parse_odds(text: str) -> List[float]:
    """Извлечение коэффициентов из текста"""
    odds = []
    for match in re.finditer(r'\b(\d+(?:[.,]\d+)?)\b', text):
        try:
            val = float(match.group(1).replace(',', '.'))
            if 1.0 <= val <= 100.0:  # Разумные пределы для коэффициентов
                odds.append(val)
        except:
            pass
    return odds

def parse_datetime(text: str) -> tuple:
    """Извлечение даты и времени"""
    # Дата: "17 фев", "28 фев", "01 мар"
    date_match = re.search(r'(\d{1,2})\s+(янв|фев|мар|апр|мая|июн|июл|авг|сен|окт|ноя|дек)', text, re.I)
    date_str = ""
    if date_match:
        day = date_match.group(1)
        month = date_match.group(2)
        date_str = f"{day} {month}"
    
    # Время: "20:00", "23:00"
    time_match = re.search(r'\b(\d{1,2}:\d{2})\b', text)
    time_str = time_match.group(1) if time_match else ""
    
    return date_str, time_str

def extract_teams(text: str, sport: str) -> tuple:
    """Извлечение названий команд"""
    # Удаляем дату/время из текста для более точного поиска
    clean_text = re.sub(r'\d{1,2}\s+(?:янв|фев|мар|апр|мая|июн|июл|авг|сен|окт|ноя|дек)\s+\d{1,2}:\d{2}', '', text, flags=re.I)
    clean_text = re.sub(r'\d{1,2}:\d{2}', '', clean_text)
    clean_text = re.sub(r'\+\d+', '', clean_text)
    
    # Паттерны для разных видов спорта
    patterns = [
        r'(?:^|\s)(.+?)\s+(?:-|—|vs\.?|против)\s+(.+?)(?:\s+\d|$)',  # Команда1 - Команда2
        r'1\.\s*(.+?)\s+2\.\s*(.+?)(?:\s|$)',  # 1. Команда1 2. Команда2
    ]
    
    for pattern in patterns:
        match = re.search(pattern, clean_text, re.I)
        if match:
            team1 = norm(match.group(1))
            team2 = norm(match.group(2))
            
            # Убираем числа из конца (часто это коэффициенты)
            team1 = re.sub(r'\s+\d+(?:[.,]\d+)?$', '', team1)
            team2 = re.sub(r'\s+\d+(?:[.,]\d+)?$', '', team2)
            
            if len(team1) > 2 and len(team2) > 2:
                return team1, team2
    
    return "", ""

# =========================
# ПАРСЕРЫ
# =========================

def parse_football_page(html: str, league: str) -> List[dict]:
    """Парсинг футбольной страницы"""
    soup = BeautifulSoup(html, 'lxml')
    matches = []
    
    for row in soup.select('tr'):
        text = norm(row.get_text())
        if not text or len(text) < 20:
            continue
        
        # ID события
        id_match = re.search(r'\+(\d{3,})', text)
        if not id_match:
            continue
        event_id = id_match.group(1)
        
        # Дата и время
        date_str, time_str = parse_datetime(text)
        
        # Команды
        team1, team2 = extract_teams(text, 'football')
        if not team1 or not team2:
            continue
        
        # Коэффициенты (должно быть 6 для футбола: П1, X, П2, 1X, 12, X2)
        odds = parse_odds(text)
        if len(odds) < 6:
            continue
        
        matches.append({
            "sport": "football",
            "league": league,
            "id": event_id,
            "date": date_str,
            "time": time_str,
            "team1": team1,
            "team2": team2,
            "p1": f"{odds[0]:.2f}",
            "x": f"{odds[1]:.2f}",
            "p2": f"{odds[2]:.2f}",
            "p1x": f"{odds[3]:.2f}",
            "p12": f"{odds[4]:.2f}",
            "px2": f"{odds[5]:.2f}",
        })
    
    return matches

def parse_2way_page(html: str, league: str, sport: str) -> List[dict]:
    """Парсинг хоккея/баскетбола (2 исхода)"""
    soup = BeautifulSoup(html, 'lxml')
    matches = []
    
    for row in soup.select('tr'):
        text = norm(row.get_text())
        if not text or len(text) < 20:
            continue
        
        # ID события
        id_match = re.search(r'\+(\d{3,})', text)
        if not id_match:
            continue
        event_id = id_match.group(1)
        
        # Дата и время
        date_str, time_str = parse_datetime(text)
        
        # Команды
        team1, team2 = extract_teams(text, sport)
        if not team1 or not team2:
            continue
        
        # Коэффициенты (должно быть минимум 2: П1, П2)
        odds = parse_odds(text)
        if len(odds) < 2:
            continue
        
        matches.append({
            "sport": sport,
            "league": league,
            "id": event_id,
            "date": date_str,
            "time": time_str,
            "team1": team1,
            "team2": team2,
            "p1": f"{odds[0]:.2f}",
            "x": "0.00",
            "p2": f"{odds[1]:.2f}",
            "p1x": "0.00",
            "p12": "0.00",
            "px2": "0.00",
        })
    
    return matches

def parse_esports_page(html: str, league: str) -> List[dict]:
    """Парсинг киберспорта"""
    return parse_2way_page(html, league, 'esports')

# =========================
# MAIN
# =========================

def main():
    print("=" * 70)
    print("УЛУЧШЕННЫЙ ПАРСЕР PRIZMBET")
    print("=" * 70)
    
    all_matches = []
    
    for sport, league, url in SOURCES:
        print(f"\n[INFO] Парсинг: {league}")
        try:
            html = http_get(url)
            
            if sport == 'football':
                matches = parse_football_page(html, league)
            elif sport in ['hockey', 'basket']:
                matches = parse_2way_page(html, league, sport)
            elif sport == 'esports':
                matches = parse_esports_page(html, league)
            else:
                print(f"[WARN] Неизвестный спорт: {sport}")
                continue
            
            print(f"[OK] Найдено матчей: {len(matches)}")
            all_matches.extend(matches)
            
        except Exception as e:
            print(f"[ERROR] Ошибка: {e}")
    
    # Удаление дубликатов
    unique_matches = {}
    for m in all_matches:
        key = f"{m['sport']}:{m['id']}"
        unique_matches[key] = m
    all_matches = list(unique_matches.values())
    
    # Сохранение
    data = {
        "last_update": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "matches": all_matches
    }
    
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print(f"[SUCCESS] Сохранено {len(all_matches)} матчей в {OUT_JSON}")
    print("=" * 70)

if __name__ == "__main__":
    main()
