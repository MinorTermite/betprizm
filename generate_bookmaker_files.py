#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET — Генерация отдельных JSON файлов для каждого БК
Создаёт:
  - winline.json — матчи только от Winline
  - marathon.json — матчи только от Marathon
  - fonbet.json — матчи только от Fonbet (если есть)
  - matches.json — объединённые данные для Google Sheets
"""

import json
import os
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MATCHES_FILE = os.path.join(SCRIPT_DIR, 'matches.json')


def load_matches():
    """Загружает общий matches.json"""
    with open(MATCHES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def filter_by_source(data, source):
    """Фильтрует матчи по источнику"""
    filtered = [
        m for m in data.get('matches', [])
        if m.get('source', '').lower() == source.lower()
    ]
    return {
        'last_update': data.get('last_update', ''),
        'source': source,
        'total': len(filtered),
        'matches': filtered
    }


def save_json(data, filename):
    """Сохраняет JSON файл"""
    filepath = os.path.join(SCRIPT_DIR, filename)
    tmp = filepath + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if os.path.exists(filepath):
        os.replace(tmp, filepath)
    else:
        os.rename(tmp, filepath)
    print(f"  [OK] {filename} - {data['total']} matches")


def main():
    print("=" * 60)
    print("PRIZMBET - Generation of bookmaker JSON files")
    print("=" * 60)
    
    # Загружаем общий файл
    print("\nLoading matches.json...")
    data = load_matches()
    print(f"[OK] Loaded {data.get('total', 0)} matches")
    
    # Фильтруем по БК
    print("\nGenerating files:")
    
    # Winline
    winline_data = filter_by_source(data, 'winline')
    save_json(winline_data, 'winline.json')
    
    # Marathon
    marathon_data = filter_by_source(data, 'marathon')
    save_json(marathon_data, 'marathon.json')
    
    # Fonbet (если есть)
    fonbet_matches = [m for m in data.get('matches', []) if m.get('source', '').lower() == 'fonbet']
    fonbet_data = {
        'last_update': data.get('last_update', ''),
        'source': 'fonbet',
        'total': len(fonbet_matches),
        'matches': fonbet_matches
    }
    save_json(fonbet_data, 'fonbet.json')
    
    # Итог
    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"\nFiles:")
    print(f"  - winline.json   - {winline_data['total']} matches")
    print(f"  - marathon.json  - {marathon_data['total']} matches")
    print(f"  - fonbet.json    - {fonbet_data['total']} matches")


if __name__ == "__main__":
    main()
