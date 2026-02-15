#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET - Синхронизация с Google Sheets (Fixed version)
"""

import json
import datetime
import re
import csv
import urllib.request
import sys
import io

# КОНФИГУРАЦИЯ
SHEET_ID = "1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
OUTPUT_FILE = "matches.json"

# Маппинг спортов
SPORT_MAPPING = {
    'Лига чемпионов УЕФА': 'football',
    'Лига Европы УЕФА': 'football',
    'Англия. Премьер-лига': 'football',
    'Россия. Премьер-лига': 'football',
    'Россия. Кубок': 'football',
    'КХЛ': 'hockey',
    'НХЛ': 'hockey',
    'NHL': 'hockey',
    'NBA': 'basket',
    'Евролига': 'basket',
    'Dota 2': 'esports',
    'CS2': 'esports',
}

def norm(s):
    """Нормализация строки"""
    return (s or "").strip()

def detect_sport(league):
    """Определение спорта по названию лиги"""
    league_lower = league.lower()
    
    # Проверяем точное совпадение
    for key, sport in SPORT_MAPPING.items():
        if league.startswith(key):
            return sport
    
    # Fallback по ключевым словам
    if any(k in league_lower for k in ['футбол', 'лига', 'премьер', 'кубок', 'uefa', 'уефа']):
        return 'football'
    if any(k in league_lower for k in ['хоккей', 'кхл', 'нхл', 'hockey']):
        return 'hockey'
    if any(k in league_lower for k in ['баскет', 'nba', 'евролига']):
        return 'basket'
    if any(k in league_lower for k in ['dota', 'cs', 'киберспорт', 'esports']):
        return 'esports'
    
    return 'football'

def download_csv():
    """Скачивание CSV из Google Sheets"""
    print("Loading data from Google Sheets...")
    try:
        with urllib.request.urlopen(CSV_URL) as response:
            content = response.read().decode('utf-8')
        print("Data loaded successfully")
        return content
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

def parse_csv_content(csv_content):
    """Парсинг CSV контента"""
    print("Processing data...")
    
    matches = []
    lines = csv_content.strip().split('\n')
    reader = csv.reader(lines)
    
    # Пропускаем заголовок
    next(reader, None)
    
    for row in reader:
        if len(row) < 12:
            continue
        
        league = norm(row[0])
        match_id = norm(row[1])
        date = norm(row[2])
        time = norm(row[3])
        team1 = norm(row[4])
        team2 = norm(row[5])
        
        # Пропускаем пустые строки
        if not league or not team1 or not team2:
            continue
        
        # Убираем дату и время из названия команды
        team1_clean = re.sub(r'\d{1,2}\s+\w{3}\s+\d{1,2}:\d{2}', '', team1).strip()
        team2_clean = re.sub(r'\d{1,2}\s+\w{3}\s+\d{1,2}:\d{2}', '', team2).strip()
        
        # Коэффициенты
        p1 = norm(row[6]) or "0.00"
        x = norm(row[7]) or "0.00"
        p2 = norm(row[8]) or "0.00"
        p1x = norm(row[9]) or "0.00"
        p12 = norm(row[10]) or "0.00"
        px2 = norm(row[11]) or "0.00"
        
        # Определяем спорт
        sport = detect_sport(league)
        
        match = {
            "sport": sport,
            "league": league,
            "id": match_id,
            "date": date,
            "time": time,
            "team1": team1_clean or team1,
            "team2": team2_clean or team2,
            "p1": p1,
            "x": x,
            "p2": p2,
            "p1x": p1x,
            "p12": p12,
            "px2": px2
        }
        
        matches.append(match)
    
    print(f"Processed {len(matches)} matches")
    return matches

def save_matches(matches):
    """Сохранение матчей в JSON"""
    data = {
        "last_update": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "matches": matches
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Data saved to {OUTPUT_FILE}")

def main():
    """Главная функция"""
    print("=" * 70)
    print("PRIZMBET - Google Sheets Sync")
    print("=" * 70)
    print()
    
    # Загружаем CSV
    csv_content = download_csv()
    
    # Парсим данные
    matches = parse_csv_content(csv_content)
    
    # Сохраняем
    save_matches(matches)
    
    # Статистика
    print()
    print("=" * 70)
    print("STATISTICS:")
    print(f"   Total matches: {len(matches)}")
    
    # Группировка по спортам
    sports = {}
    for match in matches:
        sport = match['sport']
        sports[sport] = sports.get(sport, 0) + 1
    
    for sport, count in sorted(sports.items()):
        print(f"   {sport}: {count}")
    
    print("=" * 70)
    print("SYNC COMPLETED!")
    print("=" * 70)

if __name__ == "__main__":
    # Установка кодировки для Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    main()
