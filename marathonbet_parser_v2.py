#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET — Marathonbet Parser v2
Парсит матчи с marathonbet.ru через requests + BeautifulSoup
URL: https://www.marathonbet.ru/su/betting/
"""

import json
import os
import re
import time
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from collections import Counter

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'marathon.json')
BASE_URL = "https://www.marathonbet.ru"

# Основные разделы
SECTIONS = [
    ("football", "Футбол", f"{BASE_URL}/su/betting/Football/"),
    ("hockey", "Хоккей", f"{BASE_URL}/su/betting/Ice+Hockey/"),
    ("basket", "Баскетбол", f"{BASE_URL}/su/betting/Basketball/"),
    ("tennis", "Теннис", f"{BASE_URL}/su/betting/Tennis/"),
    ("volleyball", "Волейбол", f"{BASE_URL}/su/betting/Volleyball/"),
    ("esports", "Киберспорт", f"{BASE_URL}/su/betting/e-Sports/"),
    ("mma", "Единоборства", f"{BASE_URL}/su/betting/MMA/"),
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
}

def parse_section(sport: str, sport_name: str, url: str) -> list:
    """Парсит матчи из раздела"""
    matches = []
    
    try:
        print(f"  Loading: {sport_name}")
        print(f"  URL: {url}")
        
        session = requests.Session()
        response = session.get(url, headers=HEADERS, timeout=20)
        
        print(f"  Status: {response.status_code}")
        print(f"  Content-Length: {len(response.text)}")
        
        if response.status_code != 200:
            return matches
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Ищем события - разные селекторы
        events = []
        
        # Пробуем разные селекторы
        selectors = [
            '[data-event-id]',
            '.event',
            '.match-item',
            '[class*="event"]',
            '[class*="match"]',
        ]
        
        for selector in selectors:
            found = soup.select(selector)
            if found:
                print(f"  Found {len(found)} events with selector: {selector}")
                events = found
                break
        
        if not events:
            # Пробуем найти все ссылки на события
            links = soup.find_all('a', href=re.compile(r'/su/betting/.*?\d+'))
            print(f"  Found {len(links)} links")
            events = links[:50]  # Берём первые 50
        
        for event in events[:30]:  # Максимум 30 событий
            try:
                event_id = event.get('data-event-id', '')
                if not event_id:
                    # Пробуем извлечь из href
                    href = event.get('href', '')
                    match = re.search(r'/(\d{6,})', href)
                    if match:
                        event_id = match.group(1)
                
                if not event_id:
                    continue
                
                # Ищем названия команд
                teams = []
                team_selectors = [
                    '[class*="team"]',
                    '[class*="participant"]',
                    '[class*="competitor"]',
                    '.name',
                ]
                
                for ts in team_selectors:
                    found = event.select(ts)
                    if len(found) >= 2:
                        teams = [t.get_text(strip=True) for t in found[:2]]
                        break
                
                if not teams:
                    # Пробуем извлечь из текста
                    text = event.get_text(separator=' ', strip=True)
                    # Ищем паттерн "Команда1 - Команда2"
                    team_match = re.search(r'([A-ZА-Я][^|–-]+)\s*[|–-]\s*([A-ZА-Я][^|–-]+)', text)
                    if team_match:
                        teams = [team_match.group(1).strip(), team_match.group(2).strip()]
                
                if len(teams) < 2:
                    continue
                
                team1 = teams[0][:50]
                team2 = teams[1][:50]
                
                # Ищем коэффициенты
                coefs = []
                coef_selectors = [
                    '[class*="coef"]',
                    '[class*="price"]',
                    '[class*="odd"]',
                    '[class*="koeff"]',
                ]
                
                for cs in coef_selectors:
                    found = event.select(cs)
                    if found:
                        for f in found[:6]:
                            txt = f.get_text(strip=True)
                            if re.match(r'^\d+\.?\d*$', txt):
                                coefs.append(txt)
                            else:
                                coefs.append('—')
                        break
                
                while len(coefs) < 6:
                    coefs.append('—')
                
                p1, x, p2, p1x, p12, px2 = coefs[:6]
                
                # Дата и время
                date_str = ''
                time_str = ''
                date_el = event.find(class_=re.compile(r'date|time'))
                if date_el:
                    dt_text = date_el.get_text(strip=True)
                    if ':' in dt_text:
                        time_str = dt_text[:5]
                
                match_url = f"{BASE_URL}/su/betting/{event_id}/"
                
                matches.append({
                    'sport': sport,
                    'league': f'{sport_name}',
                    'id': f'ma_{event_id}',
                    'date': date_str,
                    'time': time_str,
                    'team1': team1,
                    'team2': team2,
                    'match_url': match_url,
                    'p1': p1,
                    'x': x,
                    'p2': p2,
                    'p1x': p1x,
                    'p12': p12,
                    'px2': px2,
                    'source': 'marathon'
                })
                
            except Exception as e:
                continue
        
        print(f"  Parsed: {len(matches)} matches")
        
    except Exception as e:
        print(f"  Error: {e}")
    
    return matches


def main():
    print("=" * 60)
    print("PRIZMBET - Marathonbet Parser v2")
    print("=" * 60)
    
    all_matches = []
    
    for sport, name, url in SECTIONS:
        matches = parse_section(sport, name, url)
        all_matches.extend(matches)
        time.sleep(0.5)
    
    # Save
    data = {
        'last_update': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'marathon',
        'total': len(all_matches),
        'matches': all_matches
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] Saved: {OUTPUT_FILE}")
    print(f"[OK] Total: {len(all_matches)} matches")
    
    sports = Counter(m['sport'] for m in all_matches)
    print("\nBy sport:")
    for s, c in sorted(sports.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c}")


if __name__ == "__main__":
    main()
