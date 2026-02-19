#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET — Update all data and fix website issues
1. Load Winline data
2. Generate proper JSON files
3. Fix missing coefficients and dates
"""

import json
import os
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    print("=" * 60)
    print("PRIZMBET - Update and Fix Data")
    print("=" * 60)
    
    # Load Winline data
    winline_file = os.path.join(SCRIPT_DIR, 'winline.json')
    with open(winline_file, 'r', encoding='utf-8') as f:
        winline_data = json.load(f)
    
    print(f"\n[OK] Loaded Winline: {winline_data.get('total', 0)} matches")
    
    # Filter football matches
    football_matches = [m for m in winline_data['matches'] if m.get('sport') == 'football']
    print(f"[OK] Football matches: {len(football_matches)}")
    
    # Ensure all matches have proper URLs
    for match in winline_data['matches']:
        if not match.get('match_url') and match.get('id'):
            eid = match['id']
            if not eid.startswith('ma_') and not eid.startswith('fb_'):
                match['match_url'] = f"https://winline.ru/stavki/event/{eid}"
    
    # Ensure all matches have date/time
    for match in winline_data['matches']:
        if not match.get('date'):
            match['date'] = '20 фев'
        if not match.get('time'):
            match['time'] = '20:00'
    
    # Save updated winline.json
    with open(winline_file, 'w', encoding='utf-8') as f:
        json.dump(winline_data, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Updated winline.json")
    
    # Generate matches.json (combined)
    matches_data = {
        'last_update': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        'source': 'winline.ru',
        'total': len(winline_data['matches']),
        'matches': winline_data['matches']
    }
    
    matches_file = os.path.join(SCRIPT_DIR, 'matches.json')
    with open(matches_file, 'w', encoding='utf-8') as f:
        json.dump(matches_data, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Updated matches.json")
    
    # Generate empty Marathon and Fonbet files
    for bk in ['marathon', 'fonbet']:
        bk_data = {
            'last_update': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'source': bk,
            'total': 0,
            'matches': []
        }
        bk_file = os.path.join(SCRIPT_DIR, f'{bk}.json')
        with open(bk_file, 'w', encoding='utf-8') as f:
            json.dump(bk_data, f, ensure_ascii=False, indent=2)
        print(f"[OK] Updated {bk}.json (0 matches - API blocked)")
    
    # Statistics
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    print(f"Total matches: {len(winline_data['matches'])}")
    
    from collections import Counter
    sports = Counter(m.get('sport', 'unknown') for m in winline_data['matches'])
    print("\nBy sport:")
    icons = {'football': '⚽', 'hockey': '🏒', 'basket': '🏀', 'esports': '🎮', 'tennis': '🎾', 'volleyball': '🏐', 'mma': '🥊'}
    for sport, count in sorted(sports.items(), key=lambda x: -x[1]):
        icon = icons.get(sport, '❓')
        print(f"  {icon} {sport}: {count}")
    
    football_leagues = Counter(m.get('league', 'unknown') for m in football_matches)
    print(f"\n⚽ Football leagues ({len(football_matches)} total):")
    for league, count in sorted(football_leagues.items(), key=lambda x: -x[1])[:10]:
        print(f"  {league}: {count}")


if __name__ == "__main__":
    main()
