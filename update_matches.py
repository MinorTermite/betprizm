#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET - Единый скрипт синхронизации данных из Google Sheets
Используется в GitHub Actions и для локального запуска
"""

import json
import datetime
import re
import csv
import urllib.request
import sys
import io
import os

# КОНФИГУРАЦИЯ
SHEET_ID = os.getenv("SHEET_ID", "1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk")
GID = os.getenv("SHEET_GID", "0")
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
OUTPUT_FILE = "matches.json"

# Маппинг спортов по началу названия лиги
SPORT_MAPPING = {
    'Лига чемпионов УЕФА': 'football',
    'Лига Европы УЕФА': 'football',
    'Лига конференций УЕФА': 'football',
    'Англия. Премьер-лига': 'football',
    'Англия. Кубок': 'football',
    'Испания. Ла Лига': 'football',
    'Италия. Серия A': 'football',
    'Германия. Бундеслига': 'football',
    'Франция. Лига 1': 'football',
    'Россия. Премьер-лига': 'football',
    'Россия. Кубок': 'football',
    'КХЛ': 'hockey',
    'НХЛ': 'hockey',
    'NHL': 'hockey',
    'NBA': 'basket',
    'Евролига': 'basket',
    'Dota 2': 'esports',
    'CS2': 'esports',
    'Counter-Strike': 'esports',
    'Valorant': 'esports',
    'League of Legends': 'esports',
}

def norm(s):
    """Нормализация строки"""
    return (s or "").strip()

def detect_sport(league):
    """Определение спорта по названию лиги"""
    for key, sport in SPORT_MAPPING.items():
        if league.startswith(key):
            return sport
    ll = league.lower()
    if any(k in ll for k in ['футбол', 'лига', 'премьер', 'кубок', 'uefa', 'уефа', 'серия', 'бундес', 'ла лига']):
        return 'football'
    if any(k in ll for k in ['хоккей', 'кхл', 'нхл', 'hockey', 'nhl']):
        return 'hockey'
    if any(k in ll for k in ['баскет', 'nba', 'евролига', 'basketball']):
        return 'basket'
    if any(k in ll for k in ['dota', 'cs2', 'counter-strike', 'киберспорт', 'esports', 'valorant']):
        return 'esports'
    return 'football'

def download_csv():
    """Скачивание CSV из Google Sheets с retry"""
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[{attempt}/{max_retries}] Loading data from Google Sheets...")
            req = urllib.request.Request(CSV_URL, headers={
                'User-Agent': 'Mozilla/5.0 PRIZMBET-Bot/1.0'
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8')
            if content.strip():
                print(f"OK: loaded {len(content)} bytes")
                return content
            print("WARNING: empty response")
        except Exception as e:
            print(f"ERROR attempt {attempt}: {e}")
            if attempt == max_retries:
                return None
            import time
            time.sleep(5 * attempt)
    return None

def parse_csv_content(csv_content):
    """Парсинг CSV и создание списка матчей"""
    matches = []
    lines = csv_content.strip().split('\n')
    reader = csv.reader(lines)
    header = next(reader, None)

    if header:
        print(f"Columns: {len(header)} -> {header[:6]}...")

    row_num = 0
    skipped = 0

    for row in reader:
        row_num += 1
        if len(row) < 12:
            skipped += 1
            continue

        league = norm(row[0])
        match_id = norm(row[1])
        date = norm(row[2])
        time_val = norm(row[3])
        team1 = norm(row[4])
        team2 = norm(row[5])

        if not league or not team1 or not team2:
            skipped += 1
            continue

        # Очистка: иногда дата/время попадает в имя команды
        team1 = re.sub(r'\d{1,2}\s+\w{3}\s+\d{1,2}:\d{2}', '', team1).strip()
        team2 = re.sub(r'\d{1,2}\s+\w{3}\s+\d{1,2}:\d{2}', '', team2).strip()

        if not team1 or not team2:
            skipped += 1
            continue

        p1 = norm(row[6]) or "0.00"
        x = norm(row[7]) or "0.00"
        p2 = norm(row[8]) or "0.00"
        p1x = norm(row[9]) or "0.00"
        p12 = norm(row[10]) or "0.00"
        px2 = norm(row[11]) or "0.00"

        sport = detect_sport(league)

        matches.append({
            "sport": sport,
            "league": league,
            "id": match_id,
            "date": date,
            "time": time_val,
            "team1": team1,
            "team2": team2,
            "p1": p1,
            "x": x,
            "p2": p2,
            "p1x": p1x,
            "p12": p12,
            "px2": px2
        })

    print(f"Parsed {len(matches)} matches from {row_num} rows (skipped {skipped})")
    return matches

def save_matches(matches):
    """Атомарное сохранение matches.json"""
    data = {
        "last_update": datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        "matches": matches
    }

    tmp_file = OUTPUT_FILE + ".tmp"
    with open(tmp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Атомарная замена
    if os.path.exists(OUTPUT_FILE):
        os.replace(tmp_file, OUTPUT_FILE)
    else:
        os.rename(tmp_file, OUTPUT_FILE)

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"Saved {OUTPUT_FILE} ({size_kb:.1f} KB)")

def print_stats(matches):
    """Вывод статистики"""
    sports = {}
    leagues = {}
    for m in matches:
        sports[m['sport']] = sports.get(m['sport'], 0) + 1
        leagues[m['league']] = leagues.get(m['league'], 0) + 1

    print(f"\nTotal: {len(matches)} matches, {len(leagues)} leagues")
    for sport, count in sorted(sports.items()):
        print(f"  {sport}: {count}")

def main():
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 60)
    print("PRIZMBET - Google Sheets Sync")
    print("=" * 60)

    csv_content = download_csv()
    if not csv_content:
        print("FATAL: Could not download data from Google Sheets")
        sys.exit(1)

    matches = parse_csv_content(csv_content)
    if not matches:
        print("FATAL: No matches parsed from CSV")
        sys.exit(1)

    save_matches(matches)
    print_stats(matches)
    print("=" * 60)
    print("SYNC OK")

if __name__ == "__main__":
    main()
