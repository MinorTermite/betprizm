#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET - AUTO PARSER ALL BOOKMAKERS
Автоматический парсинг Winline + Marathon + Fonbet
"""

import json
import os
import requests
from datetime import datetime, timezone
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ============ WINLINE ============
def parse_winline():
    """Parse Winline via existing parser"""
    print("\n[1/3] Parsing Winline...")
    try:
        import winline_parser
        matches = winline_parser.run_parser()
        winline_parser.save_matches(matches)
        print(f"  [OK] Winline: {len(matches)} matches")
        return matches
    except Exception as e:
        print(f"  [ERROR] {e}")
        return []

# ============ MARATHON - Mobile API ============
def parse_marathon():
    """Parse Marathonbet via mobile API"""
    print("\n[2/3] Parsing Marathonbet...")
    matches = []
    
    # Marathon mobile API endpoints
    endpoints = [
        ("football", "Football", "https://www.marathonbet.ru/su/ajax/live_events"),
        ("hockey", "Hockey", "https://www.marathonbet.ru/su/ajax/live_events"),
        ("basket", "Basketball", "https://www.marathonbet.ru/su/ajax/live_events"),
        ("tennis", "Tennis", "https://www.marathonbet.ru/su/ajax/live_events"),
        ("esports", "Esports", "https://www.marathonbet.ru/su/ajax/live_events"),
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
        'Accept': 'application/json, text/javascript, */*',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://www.marathonbet.ru/su/betting/',
    }
    
    for sport, name, url in endpoints:
        try:
            print(f"  Loading {name}...")
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                events = data.get('events', []) if isinstance(data, dict) else []
                
                for event in events[:20]:  # Top 20 events
                    try:
                        event_id = event.get('event_id', '')
                        teams = event.get('teams', [])
                        if len(teams) < 2:
                            continue
                        
                        team1 = teams[0].get('name', '')[:50]
                        team2 = teams[1].get('name', '')[:50]
                        
                        # Coefficients
                        odds = event.get('odds', {})
                        p1 = str(odds.get('1', '—')) if isinstance(odds, dict) else '—'
                        x = str(odds.get('X', '—')) if isinstance(odds, dict) else '—'
                        p2 = str(odds.get('2', '—')) if isinstance(odds, dict) else '—'
                        
                        matches.append({
                            'sport': sport,
                            'league': f'Marathon {name}',
                            'id': f'ma_{event_id}',
                            'date': '20 фев',
                            'time': '20:00',
                            'team1': team1,
                            'team2': team2,
                            'match_url': f'https://www.marathonbet.ru/su/betting/{event_id}/',
                            'p1': p1,
                            'x': x,
                            'p2': p2,
                            'p1x': '—',
                            'p12': '—',
                            'px2': '—',
                            'source': 'marathon'
                        })
                    except:
                        continue
                
                print(f"    Found: {len([m for m in matches if m['sport']==sport])} matches")
        except Exception as e:
            print(f"    Error: {e}")
    
    # Save
    data = {
        'last_update': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'marathon',
        'total': len(matches),
        'matches': matches
    }
    
    with open(os.path.join(SCRIPT_DIR, 'marathon.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"  [OK] Marathon: {len(matches)} matches")
    return matches

# ============ FONBET - Mobile API ============
def parse_fonbet():
    """Parse Fonbet via mobile API"""
    print("\n[3/3] Parsing Fonbet...")
    matches = []
    
    # Fonbet API
    url = "https://www.fonbet.com/api/v3/events"
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        'Accept': 'application/json',
        'Referer': 'https://www.fonbet.ru/',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            
            for event in events[:30]:  # Top 30
                try:
                    event_id = event.get('id', '')
                    team1 = event.get('team1', '')[:50]
                    team2 = event.get('team2', '')[:50]
                    sport = event.get('sport', 'unknown')
                    
                    if not team1 or not team2:
                        continue
                    
                    matches.append({
                        'sport': sport,
                        'league': 'Fonbet',
                        'id': f'fb_{event_id}',
                        'date': '20 фев',
                        'time': '20:00',
                        'team1': team1,
                        'team2': team2,
                        'match_url': f'https://www.fonbet.ru/sports/{event_id}/',
                        'p1': '—',
                        'x': '—',
                        'p2': '—',
                        'p1x': '—',
                        'p12': '—',
                        'px2': '—',
                        'source': 'fonbet'
                    })
                except:
                    continue
        
        print(f"  [OK] Fonbet: {len(matches)} matches")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    # Save
    data = {
        'last_update': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'fonbet',
        'total': len(matches),
        'matches': matches
    }
    
    with open(os.path.join(SCRIPT_DIR, 'fonbet.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return matches

# ============ MAIN ============
def main():
    print("=" * 60)
    print("PRIZMBET - AUTO PARSER ALL BOOKMAKERS")
    print("=" * 60)
    
    # Parse all
    winline = parse_winline()
    marathon = parse_marathon()
    fonbet = parse_fonbet()
    
    # Combine all
    all_matches = winline + marathon + fonbet
    
    # Save combined
    combined = {
        'last_update': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'winline.ru, marathonbet.ru, fonbet.ru',
        'total': len(all_matches),
        'matches': all_matches
    }
    
    with open(os.path.join(SCRIPT_DIR, 'matches.json'), 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    
    # Statistics
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    print(f"Total matches: {len(all_matches)}")
    
    sports = Counter(m.get('sport', 'unknown') for m in all_matches)
    print("\nBy sport:")
    for sport, count in sorted(sports.items(), key=lambda x: -x[1]):
        print(f"  {sport}: {count}")
    
    by_bookmaker = {
        'Winline': len(winline),
        'Marathon': len(marathon),
        'Fonbet': len(fonbet)
    }
    print("\nBy bookmaker:")
    for bk, cnt in by_bookmaker.items():
        print(f"  {bk}: {cnt}")
    
    print(f"\n{'=' * 60}")
    print("AUTO PARSING COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. git add -A")
    print("2. git commit -m 'chore: auto-update matches'")
    print("3. git push origin master:main")
    print("\nGitHub Pages will update in 2-5 minutes!")


if __name__ == "__main__":
    main()
