#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💎 PRIZMBET - Синхронизация с Google Sheets
Получает данные из Google Sheets и обновляет matches.json
"""

import json
import datetime
import re
import csv
import urllib.request
import sys

# =========================
# КОНФИГУРАЦИЯ
# =========================

# ID вашей таблицы Google Sheets
SHEET_ID = "1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk"

# URL для экспорта CSV
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
    'NBA': 'basket',
    'Евролига': 'basket',
    'Dota 2': 'esports',
    'CS2': 'esports',
}

# =========================
# ФУНКЦИИ
# =========================

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
    if any(k in league_lower for k in ['футбол', 'лига', 'премьер', 'кубок']):
        return 'football'
    if any(k in league_lower for k in ['хоккей', 'кхл', 'нхл']):
        return 'hockey'
    if any(k in league_lower for k in ['баскет', 'nba', 'евролига']):
        return 'basket'
    if any(k in league_lower for k in ['dota', 'cs', 'киберспорт', 'esports']):
        return 'esports'
    
    return 'football'  # По умолчанию

def parse_date_time(date_str, time_str):
    """Парсинг даты и времени"""
    date_str = norm(date_str)
    time_str = norm(time_str)
    
    # Формат даты: "17 фев" или "17.02"
    if not date_str or not time_str:
        return "", ""
    
    return date_str, time_str

def download_csv():
    """Скачивание CSV из Google Sheets"""
    print("📥 Загрузка данных из Google Sheets...")
    try:
        with urllib.request.urlopen(CSV_URL) as response:
            content = response.read().decode('utf-8')
        print("✅ Данные успешно загружены")
        return content
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        sys.exit(1)

def parse_csv_content(csv_content):
    """Парсинг CSV контента"""
    print("🔄 Обработка данных...")
    
    matches = []
    lines = csv_content.strip().split('\n')
    reader = csv.reader(lines)
    
    # Пропускаем заголовок
    next(reader, None)
    
    for row in reader:
        if len(row) < 12:  # Недостаточно колонок
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
        
        # Извлекаем команды из полного текста (может быть "Команда1 17 фев 20:45")
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
        
        # Парсим дату и время
        date_str, time_str = parse_date_time(date, time)
        
        match = {
            "sport": sport,
            "league": league,
            "id": match_id,
            "date": date_str,
            "time": time_str,
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
    
    print(f"✅ Обработано {len(matches)} матчей")
    return matches

def save_matches(matches):
    """Сохранение матчей в JSON"""
    data = {
        "last_update": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "matches": matches
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Данные сохранены в {OUTPUT_FILE}")

def main():
    """Главная функция"""
    print("=" * 70)
    print("💎 PRIZMBET - Синхронизация с Google Sheets")
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
    print("📊 СТАТИСТИКА:")
    print(f"   Всего матчей: {len(matches)}")
    
    # Группировка по спортам
    sports = {}
    for match in matches:
        sport = match['sport']
        sports[sport] = sports.get(sport, 0) + 1
    
    sport_names = {
        'football': '⚽ Футбол',
        'hockey': '🏒 Хоккей',
        'basket': '🏀 Баскетбол',
        'esports': '🎮 Киберспорт'
    }
    
    for sport, count in sorted(sports.items()):
        print(f"   {sport_names.get(sport, sport)}: {count}")
    
    print("=" * 70)
    print("✅ СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА!")
    print("=" * 70)

if __name__ == "__main__":
    main()
