#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET — Simple Marathon Parser
Парсит популярные футбольные лиги с Marathonbet
"""

import json
import os
import re
import time
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

BASE_URL = "https://www.marathonbet.ru"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'marathon.json')

# Популярные лиги для парсинга
LEAGUES = [
    ("football", "Лига чемпионов", f"{BASE_URL}/su/popular/Football/UEFA/Champions+League+-+26493"),
    ("football", "Лига Европы", f"{BASE_URL}/su/popular/Football/UEFA/Europa+League+-+26494"),
    ("football", "Англия. Премьер-лига", f"{BASE_URL}/su/popular/Football/England/Premier+League+-+21520"),
    ("football", "Испания. Ла Лига", f"{BASE_URL}/su/popular/Football/Spain/Primera+Division+-+8736"),
    ("football", "Италия. Серия A", f"{BASE_URL}/su/popular/Football/Italy/Serie+A+-+22434"),
    ("football", "Германия. Бундеслига", f"{BASE_URL}/su/popular/Football/Germany/Bundesliga+-+22436"),
    ("hockey", "КХЛ", f"{BASE_URL}/su/popular/Ice+Hockey/KHL+-+52309"),
    ("hockey", "НХЛ", f"{BASE_URL}/su/popular/Ice+Hockey/NHL+-+52310"),
    ("basket", "NBA", f"{BASE_URL}/su/popular/Basketball/NBA+-+52316"),
    ("esports", "Dota 2", f"{BASE_URL}/su/popular/e-Sports/Dota+2+-+135167"),
    ("esports", "CS2", f"{BASE_URL}/su/popular/e-Sports/Counter-Strike+-+135166"),
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
}

def parse_league(sport: str, league_name: str, url: str) -> list:
    """Парсит матчи из одной лиги"""
    matches = []
    try:
        print(f"  Loading: {league_name}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"    Status: {response.status_code}")
            return matches
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Ищем карточки матчей
        event_cards = soup.find_all('div', class_='event__match')
        
        for card in event_cards:
            try:
                # ID матча
                event_id = card.get('data-event-id', '')
                if not event_id:
                    continue
                
                # Команды
                teams = card.find_all('div', class_='event__participant')
                if len(teams) < 2:
                    continue
                team1 = teams[0].get_text(strip=True)
                team2 = teams[1].get_text(strip=True)
                
                # Дата и время
                event_time = card.find('div', class_='event__time')
                date_str = ''
                time_str = ''
                if event_time:
                    time_text = event_time.get_text(strip=True)
                    # Парсим дату и время
                    time_match = re.search(r'(\d{2})\.(\d{2})\s+(\d{2}:\d{2})', time_text)
                    if time_match:
                        date_str = f"{time_match.group(1)} янв"  # Упрощённо
                        time_str = time_match.group(3)
                
                # Коэффициенты
                coef_buttons = card.find_all('button', class_='price__btn')
                p1 = '—'
                x = '—'
                p2 = '—'
                p1x = '—'
                p12 = '—'
                px2 = '—'
                
                if len(coef_buttons) >= 3:
                    p1 = coef_buttons[0].get_text(strip=True)
                    x = coef_buttons[1].get_text(strip=True)
                    p2 = coef_buttons[2].get_text(strip=True)
                
                if len(coef_buttons) >= 6:
                    p1x = coef_buttons[3].get_text(strip=True)
                    p12 = coef_buttons[4].get_text(strip=True)
                    px2 = coef_buttons[5].get_text(strip=True)
                
                match_url = f"{BASE_URL}/su/betting/{event_id}"
                
                matches.append({
                    'sport': sport,
                    'league': league_name,
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
        
        print(f"    Found: {len(matches)} matches")
        
    except Exception as e:
        print(f"    Error: {e}")
    
    return matches


def main():
    print("=" * 60)
    print("PRIZMBET - Marathon Parser")
    print("=" * 60)
    
    all_matches = []
    
    for sport, league, url in LEAGUES:
        matches = parse_league(sport, league, url)
        all_matches.extend(matches)
        time.sleep(1)  # Delay between requests
    
    # Save result
    data = {
        'last_update': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'marathon',
        'total': len(all_matches),
        'matches': all_matches
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] Saved: {OUTPUT_FILE}")
    print(f"[OK] Total matches: {len(all_matches)}")
    
    # Statistics by sport
    from collections import Counter
    sports = Counter(m['sport'] for m in all_matches)
    print("\nBy sport:")
    for sport, count in sorted(sports.items(), key=lambda x: -x[1]):
        print(f"  {sport}: {count}")


if __name__ == "__main__":
    main()
