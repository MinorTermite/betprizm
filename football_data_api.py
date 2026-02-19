#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET — Football-Data.org API Parser
Бесплатный API для футбольных матчей
API: https://www.football-data.org/
"""

import json
import os
import requests
from datetime import datetime, timezone
from collections import Counter

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'football_api.json')
API_TOKEN = '4b245f519ada45d19b14cf6316d6015d'
API_BASE = 'https://api.football-data.org/v4'

HEADERS = {
    'X-Auth-Token': API_TOKEN,
    'User-Agent': 'PRIZMBet/1.0',
}

# Популярные соревнования (бесплатный план)
COMPETITIONS = [
    ('PL', 'Англия. Премьер-лига'),      # Premier League
    ('PD', 'Испания. Ла Лига'),          # Primera Division
    ('SA', 'Италия. Серия A'),           # Serie A
    ('BL1', 'Германия. Бундеслига'),     # Bundesliga
    ('FL1', 'Франция. Лига 1'),          # Ligue 1
    ('CL', 'Лига Чемпионов УЕФА'),       # Champions League
    ('ELC', 'Англия. Чемпионшип'),       # Championship
    ('PPL', 'Португалия. Примейра Лига'), # Primeira Liga
    ('DED', 'Нидерланды. Эредивизие'),   # Eredivisie
    ('BSA', 'Бразилия. Серия A'),        # Campeonato Brasileiro Série A
]

def fetch_matches(competition_code: str, competition_name: str) -> list:
    """Загружает матчи из соревнования"""
    matches = []
    
    try:
        print(f"  Loading: {competition_name} ({competition_code})")
        
        # Загружаем матчи на ближайшие 7 дней
        url = f"{API_BASE}/competitions/{competition_code}/matches"
        params = {
            'status': 'SCHEDULED',
            'matchday': '',
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        
        if response.status_code == 429:
            print(f"    Rate limit exceeded!")
            return matches
        
        if response.status_code != 200:
            print(f"    Status: {response.status_code}")
            return matches
        
        data = response.json()
        matches_list = data.get('matches', [])
        
        for match in matches_list:
            try:
                home_team = match.get('homeTeam', {}).get('name', 'Unknown')
                away_team = match.get('awayTeam', {}).get('name', 'Unknown')
                
                # Дата и время
                match_date = match.get('utcDate', '')
                if match_date:
                    dt = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
                    date_str = dt.strftime('%d %b').lower()
                    # Перевод месяцев на русский
                    months = {
                        'jan': 'янв', 'feb': 'фев', 'mar': 'мар', 'apr': 'апр',
                        'may': 'май', 'jun': 'июн', 'jul': 'июл', 'aug': 'авг',
                        'sep': 'сен', 'oct': 'окт', 'nov': 'ноя', 'dec': 'дек'
                    }
                    for en, ru in months.items():
                        date_str = date_str.replace(en, ru)
                    time_str = dt.strftime('%H:%M')
                else:
                    date_str = ''
                    time_str = ''
                
                # Коэффициенты (если доступны в бесплатном API)
                odds = match.get('odds', {})
                p1 = '—'
                x = '—'
                p2 = '—'
                
                # Пробуем получить коэффициенты
                if odds:
                    try:
                        # Бесплатный API может не отдавать коэффициенты
                        p1 = str(odds.get('home', '—'))
                        x = str(odds.get('draw', '—'))
                        p2 = str(odds.get('away', '—'))
                    except:
                        pass
                
                match_id = match.get('id', '')
                match_url = f"https://www.football-data.org/match/{match_id}/"
                
                matches.append({
                    'sport': 'football',
                    'league': competition_name,
                    'id': f'fd_{match_id}',
                    'date': date_str,
                    'time': time_str,
                    'team1': home_team,
                    'team2': away_team,
                    'match_url': match_url,
                    'p1': p1,
                    'x': x,
                    'p2': p2,
                    'p1x': '—',
                    'p12': '—',
                    'px2': '—',
                    'source': 'football-data.org'
                })
                
            except Exception as e:
                continue
        
        print(f"    Found: {len(matches)} matches")
        
    except Exception as e:
        print(f"    Error: {e}")
    
    return matches


def main():
    print("=" * 60)
    print("PRIZMBET - Football-Data.org API Parser")
    print("=" * 60)
    
    all_matches = []
    
    for code, name in COMPETITIONS:
        matches = fetch_matches(code, name)
        all_matches.extend(matches)
        
        # Задержка между запросами (бесплатный план: 10 запросов в минуту)
        import time
        time.sleep(6)
    
    # Save
    data = {
        'last_update': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'football-data.org',
        'total': len(all_matches),
        'matches': all_matches
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n[OK] Saved: {OUTPUT_FILE}")
    print(f"[OK] Total: {len(all_matches)} football matches")
    
    # Statistics by league
    leagues = Counter(m['league'] for m in all_matches)
    print("\nBy league:")
    for league, count in sorted(leagues.items(), key=lambda x: -x[1]):
        print(f"  {league}: {count}")


if __name__ == "__main__":
    main()
