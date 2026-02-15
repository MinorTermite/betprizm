#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💎 PRIZMBET ПАРСЕР MARATHON + GOOGLE SHEETS v2.5
✅ Полная валидация данных
✅ Обработка ошибок
✅ Rate limiting
✅ Формат как в Google Sheets
"""

import datetime as dt
import json
import os
import re
import time
import random
from typing import List, Optional, Dict, Tuple
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =========================
# CONFIG
# =========================
BASE = "https://www.marathonbet.ru"

# Источники для парсинга
SOURCES = [
    ("football", "Англия. Премьер-лига", f"{BASE}/su/popular/Football/England/Premier%2BLeague%2B-%2B21520"),
    ("football", "Испания. Ла Лига", f"{BASE}/su/popular/Football/Spain/Primera%2BDivision%2B-%2B8736"),
    ("football", "Италия. Серия A", f"{BASE}/su/popular/Football/Italy/Serie%2BA%2B-%2B22434"),
    ("football", "Германия. Бундеслига", f"{BASE}/su/popular/Football/Germany/Bundesliga%2B-%2B22436"),
    ("football", "Франция. Лига 1", f"{BASE}/su/popular/Football/France/Ligue%2B1%2B-%2B21533"),
    ("football", "ЛЧ УЕФА", f"{BASE}/su/popular/Football/UEFA/Champions%2BLeague%2B-%2B52287"),
    ("football", "ЛЕ УЕФА", f"{BASE}/su/popular/Football/UEFA/Europa%2BLeague%2B-%2B14"),
    ("hockey", "КХЛ", f"{BASE}/su/popular/Ice%2BHockey/KHL%2B-%2B52309"),
    ("hockey", "НХЛ", f"{BASE}/su/popular/Ice%2BHockey/NHL%2B-%2B69368"),
    ("basket", "NBA", f"{BASE}/su/popular/Basketball/NBA%2B-%2B69367"),
    ("basket", "Евролига", f"{BASE}/su/popular/Basketball/Euroleague%2B-%2B22469"),
    ("esports", "Dota 2", f"{BASE}/su/popular/e-Sports/Dota+2/"),
    ("esports", "CS2", f"{BASE}/su/popular/e-Sports/Counter-Strike+2/"),
]

OUT_JSON = "matches.json"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36"
TIMEOUT = 30

# Google Sheets config (опционально)
WRITE_SHEETS = os.getenv("WRITE_SHEETS", "0") == "1"
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
SHEET_NAME = os.getenv("SHEET_NAME", "Matches")

# =========================
# RATE LIMITER
# =========================
class RateLimiter:
    """Контроллер частоты запросов"""
    
    def __init__(self, min_delay=2.0, max_delay=5.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request = 0
    
    def wait(self):
        """Подождать перед следующим запросом"""
        now = time.time()
        elapsed = now - self.last_request
        
        # Случайная задержка
        delay = random.uniform(self.min_delay, self.max_delay)
        
        if elapsed < delay:
            sleep_time = delay - elapsed
            print(f"   ⏳ Задержка {sleep_time:.1f}с...")
            time.sleep(sleep_time)
        
        self.last_request = time.time()

# Глобальный rate limiter
rate_limiter = RateLimiter(min_delay=2.0, max_delay=5.0)

# =========================
# HTTP SESSION
# =========================
def create_robust_session():
    """Создание надёжной сессии с retry"""
    session = requests.Session()
    
    # Настройка retry стратегии
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Глобальная сессия
http_session = create_robust_session()

# =========================
# UTILS
# =========================
def http_get(url: str) -> Optional[str]:
    """HTTP GET запрос с обработкой ошибок"""
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ru,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": BASE,
    }
    
    try:
        # Rate limiting
        rate_limiter.wait()
        
        response = http_session.get(url, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response.text
        
    except requests.exceptions.Timeout:
        print(f"   ❌ Таймаут запроса")
        return None
        
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Ошибка соединения")
        return None
        
    except requests.exceptions.HTTPError as e:
        print(f"   ❌ HTTP ошибка: {e.response.status_code}")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Ошибка запроса: {e}")
        return None

def norm(s: str) -> str:
    """Нормализация текста"""
    if not s:
        return ""
    return re.sub(r'\s+', ' ', s.strip())

def extract_numbers(text: str) -> List[float]:
    """Извлечение всех чисел из текста"""
    numbers = []
    for match in re.finditer(r'\b(\d+(?:[.,]\d+)?)\b', text):
        try:
            val = float(match.group(1).replace(',', '.'))
            if 1.01 <= val <= 100.0:
                numbers.append(val)
        except:
            pass
    return numbers

def parse_date_time(text: str) -> Tuple[str, str]:
    """Извлечение даты и времени"""
    # Дата: "17 фев", "28 фев", "01 мар"
    months_ru = {
        'янв': '01', 'фев': '02', 'мар': '03', 'апр': '04',
        'мая': '05', 'июн': '06', 'июл': '07', 'авг': '08',
        'сен': '09', 'окт': '10', 'ноя': '11', 'дек': '12'
    }
    
    date_str = ""
    date_match = re.search(r'(\d{1,2})\s+(янв|фев|мар|апр|мая|июн|июл|авг|сен|окт|ноя|дек)', text, re.I)
    if date_match:
        day = date_match.group(1).zfill(2)
        month_name = date_match.group(2).lower()
        month = months_ru.get(month_name, '??')
        date_str = f"{day}.{month}"
    
    # Время: "20:00", "23:00"
    time_str = ""
    time_match = re.search(r'\b(\d{1,2}:\d{2})\b', text)
    if time_match:
        time_str = time_match.group(1)
    
    return date_str, time_str

def extract_teams_smart(text: str) -> Tuple[str, str]:
    """Умное извлечение названий команд"""
    # Удаляем даты, время, числа в конце
    clean = text
    clean = re.sub(r'\d{1,2}\s+(?:янв|фев|мар|апр|мая|июн|июл|авг|сен|окт|ноя|дек)', '', clean, flags=re.I)
    clean = re.sub(r'\d{1,2}:\d{2}', '', clean)
    clean = re.sub(r'\+\d+', '', clean)
    clean = re.sub(r'\s+\d+[.,]\d+\s*$', '', clean)
    clean = norm(clean)
    
    # Паттерны разделителей
    separators = [' - ', ' — ', ' vs ', ' против ', '  ']
    
    for sep in separators:
        if sep in clean:
            parts = clean.split(sep, 1)
            if len(parts) == 2:
                team1 = norm(parts[0])
                team2 = norm(parts[1])
                
                # Удаляем числа в конце (коэффициенты)
                team1 = re.sub(r'\s+\d+(?:[.,]\d+)?$', '', team1)
                team2 = re.sub(r'\s+\d+(?:[.,]\d+)?$', '', team2)
                
                # Проверка валидности
                if len(team1) >= 3 and len(team2) >= 3:
                    # Удаляем время если осталось
                    team1 = re.sub(r'\s+\d{1,2}:\d{2}$', '', team1)
                    team2 = re.sub(r'\s+\d{1,2}:\d{2}$', '', team2)
                    return norm(team1), norm(team2)
    
    return "", ""

# =========================
# VALIDATION
# =========================
def validate_match(match: Dict) -> Optional[Dict]:
    """Валидация и очистка данных матча"""
    
    # 1. Обязательные поля
    if not all([match.get('id'), match.get('sport'), match.get('league')]):
        return None
    
    # 2. Команды
    team1 = norm(match.get('team1', ''))
    team2 = norm(match.get('team2', ''))
    
    if not team1 or not team2:
        print(f"   ⚠️  ID {match['id']}: пустые команды")
        return None
    
    if len(team1) < 3 or len(team2) < 3:
        print(f"   ⚠️  ID {match['id']}: слишком короткие названия")
        return None
    
    # Очистка времени из команд
    team1 = re.sub(r'\s*\d{1,2}:\d{2}\s*$', '', team1)
    team2 = re.sub(r'\s*\d{1,2}:\d{2}\s*$', '', team2)
    match['team1'] = norm(team1)
    match['team2'] = norm(team2)
    
    # 3. Коэффициенты
    try:
        p1 = float(match.get('p1', 0))
        p2 = float(match.get('p2', 0))
        
        if not (1.01 <= p1 <= 100 and 1.01 <= p2 <= 100):
            print(f"   ⚠️  ID {match['id']}: некорректные коэффициенты П1={p1:.2f}, П2={p2:.2f}")
            return None
        
        # Для футбола проверяем X
        if match['sport'] == 'football':
            x = float(match.get('x', 0))
            if not (1.01 <= x <= 100):
                print(f"   ⚠️  ID {match['id']}: некорректный X={x:.2f}")
                return None
            
    except (ValueError, TypeError) as e:
        print(f"   ⚠️  ID {match['id']}: ошибка в коэффициентах: {e}")
        return None
    
    # 4. Форматирование коэффициентов
    match['p1'] = f"{float(match['p1']):.2f}"
    match['p2'] = f"{float(match['p2']):.2f}"
    
    if match['sport'] == 'football':
        match['x'] = f"{float(match['x']):.2f}"
        match['p1x'] = f"{float(match.get('p1x', 0)):.2f}"
        match['p12'] = f"{float(match.get('p12', 0)):.2f}"
        match['px2'] = f"{float(match.get('px2', 0)):.2f}"
    else:
        match['x'] = "0.00"
        match['p1x'] = "0.00"
        match['p12'] = "0.00"
        match['px2'] = "0.00"
    
    return match

# =========================
# PARSERS
# =========================
def parse_marathon_page(html: str, league: str, sport: str) -> List[Dict]:
    """Универсальный парсер страницы Marathon"""
    soup = BeautifulSoup(html, 'lxml')
    matches = []
    
    # Ищем строки с событиями
    for row in soup.select('tr[data-event-id], tr.event-row, div.event-wrapper'):
        try:
            # Получаем весь текст из строки
            text = norm(row.get_text(' ', strip=True))
            
            if not text or len(text) < 20:
                continue
            
            # ID события из атрибута или из текста
            event_id = row.get('data-event-id', '')
            if not event_id:
                id_match = re.search(r'\+(\d{3,})', text)
                if not id_match:
                    continue
                event_id = id_match.group(1)
            
            # Дата и время
            date_str, time_str = parse_date_time(text)
            
            # Команды
            team1, team2 = extract_teams_smart(text)
            if not team1 or not team2:
                continue
            
            # Коэффициенты
            odds = extract_numbers(text)
            
            if sport == 'football':
                # Футбол: нужно минимум 6 коэффициентов (П1, X, П2, 1X, 12, X2)
                if len(odds) < 6:
                    continue
                
                match = {
                    "sport": sport,
                    "league": league,
                    "id": event_id,
                    "date": date_str,
                    "time": time_str,
                    "team1": team1,
                    "team2": team2,
                    "p1": odds[0],
                    "x": odds[1],
                    "p2": odds[2],
                    "p1x": odds[3] if len(odds) > 3 else odds[0],
                    "p12": odds[4] if len(odds) > 4 else odds[0],
                    "px2": odds[5] if len(odds) > 5 else odds[2],
                }
            else:
                # Хоккей/Баскетбол/Киберспорт: нужно минимум 2 коэффициента (П1, П2)
                if len(odds) < 2:
                    continue
                
                match = {
                    "sport": sport,
                    "league": league,
                    "id": event_id,
                    "date": date_str,
                    "time": time_str,
                    "team1": team1,
                    "team2": team2,
                    "p1": odds[0],
                    "x": 0.00,
                    "p2": odds[1],
                    "p1x": 0.00,
                    "p12": 0.00,
                    "px2": 0.00,
                }
            
            # Валидация
            validated = validate_match(match)
            if validated:
                matches.append(validated)
                
        except Exception as e:
            # Пропускаем проблемные строки
            continue
    
    return matches

# =========================
# GOOGLE SHEETS
# =========================
def write_to_sheets(matches: List[Dict]):
    """Запись в Google Sheets"""
    if not WRITE_SHEETS or not SPREADSHEET_ID:
        return
    
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        print("\n📊 Запись в Google Sheets...")
        
        # Подключение
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
        
        # Очистка
        sheet.clear()
        
        # Заголовки
        headers = ["Спорт", "Лига", "ID", "Дата", "Время", "Команда 1", "Команда 2", 
                   "П1", "X", "П2", "1X", "12", "X2"]
        sheet.append_row(headers)
        
        # Данные
        rows = []
        for m in matches:
            row = [
                m["sport"], m["league"], m["id"], m["date"], m["time"],
                m["team1"], m["team2"], m["p1"], m["x"], m["p2"],
                m["p1x"], m["p12"], m["px2"]
            ]
            rows.append(row)
        
        # Пакетная запись (быстрее)
        if rows:
            sheet.append_rows(rows)
        
        print(f"✅ Записано {len(matches)} матчей в Google Sheets")
    
    except FileNotFoundError:
        print("❌ Файл credentials.json не найден")
    except Exception as e:
        print(f"❌ Ошибка записи в Google Sheets: {e}")

# =========================
# MAIN
# =========================
def save_to_json(matches: List[Dict]):
    """Сохранение в JSON"""
    
    # Удаление дубликатов по ID
    unique = {}
    for m in matches:
        key = f"{m['sport']}:{m['id']}"
        unique[key] = m
    matches = list(unique.values())
    
    # Группировка по лигам
    by_league = {}
    for m in matches:
        league = m['league']
        by_league[league] = by_league.get(league, 0) + 1
    
    print(f"\n📊 Статистика:")
    print(f"   ✅ Уникальных матчей: {len(matches)}")
    print(f"   📋 Лиг: {len(by_league)}")
    
    print(f"\n📋 Матчей по лигам:")
    for league, count in sorted(by_league.items(), key=lambda x: -x[1])[:10]:
        print(f"   • {league}: {count}")
    
    # Сохранение
    data = {
        "last_update": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "matches": matches
    }
    
    try:
        with open(OUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        size = os.path.getsize(OUT_JSON) / 1024
        print(f"\n💾 Сохранено в {OUT_JSON}")
        print(f"   📁 Размер: {size:.2f} KB")
        
    except Exception as e:
        print(f"\n❌ Ошибка сохранения: {e}")
        raise

def main():
    """Главная функция"""
    print("=" * 70)
    print("💎 PRIZMBET ПАРСЕР MARATHON v2.5")
    print("=" * 70)
    print(f"⏰ Запуск: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Источников: {len(SOURCES)}")
    print("=" * 70)
    
    all_matches = []
    failed = []
    
    for i, (sport, league, url) in enumerate(SOURCES, 1):
        print(f"\n[{i}/{len(SOURCES)}] 🔍 {league}")
        
        try:
            html = http_get(url)
            
            if html is None:
                failed.append((league, "HTTP ошибка"))
                continue
            
            matches = parse_marathon_page(html, league, sport)
            print(f"   ✅ Найдено: {len(matches)} матчей")
            all_matches.extend(matches)
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            failed.append((league, str(e)))
    
    # Сохранение
    if all_matches:
        save_to_json(all_matches)
    else:
        print("\n⚠️  Не найдено ни одного матча!")
    
    # Итог
    print("\n" + "=" * 70)
    print(f"✅ ПАРСИНГ ЗАВЕРШЁН")
    print("=" * 70)
    print(f"📊 Всего матчей: {len(all_matches)}")
    
    if failed:
        print(f"\n⚠️  Не удалось загрузить ({len(failed)}):")
        for league, error in failed[:5]:
            print(f"   • {league}: {error}")
    
    print("=" * 70)
    
    # Google Sheets
    if WRITE_SHEETS and all_matches:
        write_to_sheets(all_matches)

if __name__ == "__main__":
    main()
