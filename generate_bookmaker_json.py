#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET — Generate bookmaker JSON files from matches.json
Разделяет матчи по БК на основе source И match_url
"""

import json
import os
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MATCHES_FILE = os.path.join(SCRIPT_DIR, 'matches.json')

def get_bookmaker_source(match):
    """Определяет БК по source и match_url"""
    source = (match.get('source', '') or '').lower()
    match_url = (match.get('match_url', '') or '').lower()
    match_url_marathon = (match.get('match_url_marathon', '') or '').lower()
    
    # Проверяем по URL в приоритете
    if 'marathon' in match_url or 'marathon' in match_url_marathon:
        return 'marathon'
    if 'fonbet' in match_url or 'bkfon' in match_url:
        return 'fonbet'
    if 'winline' in match_url:
        return 'winline'
    
    # Проверяем по source
    if 'marathon' in source:
        return 'marathon'
    if 'fonbet' in source:
        return 'fonbet'
    if 'winline' in source:
        return 'winline'
    
    return 'unknown'

def generate_bookmaker_files():
    """Генерирует JSON файлы для каждого БК"""
    print("=" * 60)
    print("PRIZMBET - Generate Bookmaker JSON Files")
    print("=" * 60)
    
    # Загружаем matches.json
    try:
        with open(MATCHES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"\n[OK] Loaded: {data.get('total', 0)} matches")
    except FileNotFoundError:
        print(f"\n[ERROR] {MATCHES_FILE} not found!")
        return
    except json.JSONDecodeError as e:
        print(f"\n[ERROR] Invalid JSON: {e}")
        return
    
    matches = data.get('matches', [])
    last_update = data.get('last_update', datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'))
    
    # Разделяем по БК
    bookmakers = {
        'winline': [],
        'marathon': [],
        'fonbet': [],
        'unknown': []
    }
    
    for match in matches:
        bk = get_bookmaker_source(match)
        bookmakers[bk].append(match)
    
    # Генерируем файлы
    for bk_name, bk_matches in bookmakers.items():
        if bk_name == 'unknown':
            continue
        
        bk_data = {
            'last_update': last_update,
            'source': bk_name,
            'total': len(bk_matches),
            'matches': bk_matches
        }
        
        output_file = os.path.join(SCRIPT_DIR, f'{bk_name}.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(bk_data, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] {bk_name}.json: {len(bk_matches)} matches")
    
    # Итог
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    total_generated = sum(len(bookmakers[bk]) for bk in ['winline', 'marathon', 'fonbet'])
    print(f"Total matches: {total_generated}")
    print(f"  Winline:   {len(bookmakers['winline'])}")
    print(f"  Marathon:  {len(bookmakers['marathon'])}")
    print(f"  Fonbet:    {len(bookmakers['fonbet'])}")
    
    if bookmakers['unknown']:
        print(f"\n[WARN] {len(bookmakers['unknown'])} matches with unknown bookmaker")


if __name__ == "__main__":
    generate_bookmaker_files()
