#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET — Fonbet Parser (Web Scraping)
Парсит популярные лиги с Fonbet.ru
"""

import json
import os
import re
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'fonbet.json')
FONBET_BASE = "https://www.fonbet.ru"

# Популярные лиги
LEAGUES = [
    ("football", "UEFA Champions League", f"{FONBET_BASE}/football/18079/turnir-champions-league"),
    ("football", "UEFA Europa League", f"{FONBET_BASE}/football/18080/turnir-europa-league"),
    ("football", "England Premier League", f"{FONBET_BASE}/football/18033/turnir-angliya-premer-liga"),
    ("football", "Spain La Liga", f"{FONBET_BASE}/football/18036/turnir-ispaniya-primera"),
    ("football", "Italy Serie A", f"{FONBET_BASE}/football/18035/turnir-italiya-seriya-a"),
    ("football", "Germany Bundesliga", f"{FONBET_BASE}/football/18034/turnir-germaniya-bundesliga"),
    ("hockey", "KHL", f"{FONBET_BASE}/hockey/18219/turnir-khl"),
    ("hockey", "NHL", f"{FONBET_BASE}/hockey/18220/turnir-nhl"),
    ("basket", "NBA", f"{FONBET_BASE}/basketball/18269/turnir-nba"),
    ("esports", "Dota 2", f"{FONBET_BASE}/esports/19006/discipline-dota-2"),
    ("esports", "CS2", f"{FONBET_BASE}/esports/19001/discipline-counter-strike"),
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9',
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
        event_cards = soup.find_all('div', class_='live-event__content')
        if not event_cards:
            event_cards = soup.find_all('div', {'data-event-id': True})
        
        for card in event_cards:
            try:
                # ID матча
                event_id = card.get('data-event-id', '')
                if not event_id:
                    continue
                
                # Команды
                teams = card.find_all('div', class_='live-event__team-name')
                if len(teams) < 2:
                    teams = card.find_all(class_='participant')
                if len(teams) < 2:
                    continue
                
                team1 = teams[0].get_text(strip=True)
                team2 = teams[1].get_text(strip=True)
                
                # Дата и время
                event_time = card.find('div', class_='live-event__start-time')
                date_str = ''
                time_str = ''
                if event_time:
                    time_text = event_time.get_text(strip=True)
                    time_str = time_text if ':' in time_text else ''
                
                # Коэффициенты
                coefs = []
                coef_buttons = card.find_all('button', class_='live-event__coef')
                for btn in coef_buttons[:6]:
                    coef_text = btn.get_text(strip=True)
                    if re.match(r'^\d+\.?\d*$', coef_text):
                        coefs.append(coef_text)
                    else:
                        coefs.append('—')
                
                while len(coefs) < 6:
                    coefs.append('—')
                
                p1, x, p2, p1x, p12, px2 = coefs[:6]
                
                match_url = f"{FONBET_BASE}/line/{event_id}/"
                
                matches.append({
                    'sport': sport,
                    'league': league_name,
                    'id': f'fb_{event_id}',
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
                    'source': 'fonbet'
                })
                
            except Exception as e:
                continue
        
        print(f"    Found: {len(matches)} matches")
        
    except Exception as e:
        print(f"    Error: {e}")
    
    return matches


def main():
    print("=" * 60)
    print("PRIZMBET - Fonbet Parser (Web Scraping)")
    print("=" * 60)

    all_matches = []

    for sport, league, url in LEAGUES:
        matches = parse_league(sport, league, url)
        all_matches.extend(matches)

    # Save result
    data = {
        'last_update': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'fonbet',
        'total': len(all_matches),
        'matches': all_matches
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Saved: {OUTPUT_FILE}")
    print(f"[OK] Total matches: {len(all_matches)}")

    # Statistics
    from collections import Counter
    sports = Counter(m['sport'] for m in all_matches)
    print("\nBy sport:")
    for sport, count in sorted(sports.items(), key=lambda x: -x[1]):
        print(f"  {sport}: {count}")


if __name__ == "__main__":
    main()
