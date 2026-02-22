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
from typing import Optional, List, Dict

# КОНФИГУРАЦИЯ
SHEET_ID = os.getenv("SHEET_ID", "1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk")
GID = os.getenv("SHEET_GID", "")  # Пустой = сканировать все вкладки
CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
    if GID
    else f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
)
OUTPUT_FILE = "matches.json"

# Google API ключ (для прямого доступа к Sheets API)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyBt2XLnnAo36M1rk_8F3fbE0id1wdOLpkk")

# Учетные данные для Google Sheets (сервис-аккаунт)
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

# SHEET_GIDS - список ID вкладок через запятую для чтения
SHEET_GIDS = os.getenv("SHEET_GIDS", "")

# Маппинг спортов по началу названия лиги
SPORT_MAPPING = {
    # ── FOOTBALL ──────────────────────────────────────────────
    "Лига чемпионов УЕФА": "football",
    "Лига Европы УЕФА": "football",
    "Лига конференций УЕФА": "football",
    "УЕФА": "football",
    "UEFA": "football",
    "Англия. Премьер-лига": "football",
    "Англия. Чемпионшип": "football",
    "Англия. Лига 1": "football",
    "Англия. Лига 2": "football",
    "Англия. Кубок": "football",
    "Англия. Кубок Лиги": "football",
    "Испания. Ла Лига": "football",
    "Испания. Сегунда": "football",
    "Испания. Кубок Короля": "football",
    "Германия. Бундеслига": "football",
    "Германия. 2. Бундеслига": "football",
    "Германия. Кубок": "football",
    "Италия. Серия A": "football",
    "Италия. Серия B": "football",
    "Итальянский. Кубок": "football",
    "Франция. Лига 1": "football",
    "Франция. Лига 2": "football",
    "Россия. Премьер-лига": "football",
    "Россия. ФНЛ": "football",
    "Россия. Кубок": "football",
    "Нидерланды. Эредивизие": "football",
    "Португалия. Примейра Лига": "football",
    "Турция. Суперлига": "football",
    "Шотландия. Премьершип": "football",
    "Бельгия. Про Лига": "football",
    "Бразилия. Серия A": "football",
    "Аргентина. Примера Дивисьон": "football",
    "США. MLS": "football",
    "MLS": "football",
    "Мексика. Лига MX": "football",
    "КОНМЕБОЛ. Копа Либертадорес": "football",
    "КОНКАКАФ": "football",
    "Саудовская Аравия. Про Лига": "football",
    "Япония. Джей-Лига": "football",
    "Южная Корея. К-Лига": "football",
    "Австралия. A-League": "football",
    "Африка. КАФ": "football",
    "Азия. AFC": "football",
    "Греция. Суперлига": "football",
    "Украина. Премьер-лига": "football",
    "Польша. Экстракласа": "football",
    "Чехия. Первая лига": "football",
    "Австрия. Бундеслига": "football",
    "Швейцария. Суперлига": "football",
    "Дания. Суперлига": "football",
    "Норвегия. Элитесерия": "football",
    "Швеция. Алльсвенскан": "football",
    # ── HOCKEY ────────────────────────────────────────────────
    "КХЛ": "hockey",
    "НХЛ": "hockey",
    "NHL": "hockey",
    "ВХЛ": "hockey",
    "МХЛ": "hockey",
    "AHL": "hockey",
    "ECHL": "hockey",
    "Швеция. SHL": "hockey",
    "Финляндия. Liiga": "hockey",
    "Чехия. Extraliga": "hockey",
    "Германия. DEL": "hockey",
    "Швейцария. National League": "hockey",
    "Беларусь. Экстралига": "hockey",
    "Казахстан. ЧРК": "hockey",
    "Австрия. ICEHL": "hockey",
    "Словакия. Extraliga": "hockey",
    # ── BASKETBALL ────────────────────────────────────────────
    "NBA": "basket",
    "НБА": "basket",
    "Евролига": "basket",
    "EuroLeague": "basket",
    "EuroCup": "basket",
    "Единая лига ВТБ": "basket",
    "Испания. ACB": "basket",
    "Турция. BSL": "basket",
    "Италия. LBA": "basket",
    "Франция. Про A": "basket",
    "Германия. BBL": "basket",
    "Греция. HEBA A1": "basket",
    "Израиль. Winner League": "basket",
    "Австралия. NBL": "basket",
    "Китай. CBA": "basket",
    "ФИБА": "basket",
    "FIBA": "basket",
    # ── ESPORTS ───────────────────────────────────────────────
    "CS2": "esports",
    "Counter-Strike": "esports",
    "Dota 2": "esports",
    "Valorant": "esports",
    "League of Legends": "esports",
    "LoL": "esports",
    "Rocket League": "esports",
    "RLCS": "esports",
    "Overwatch": "esports",
    "PUBG": "esports",
    "Apex Legends": "esports",
    "Rainbow Six": "esports",
    "Hearthstone": "esports",
    "StarCraft": "esports",
    # ── TENNIS ────────────────────────────────────────────────
    "ATP": "tennis",
    "WTA": "tennis",
    "ITF": "tennis",
    "Теннис": "tennis",
    # ── VOLLEYBALL ────────────────────────────────────────────
    "CEV": "volleyball",
    "ВНЛ": "volleyball",
    "VNL": "volleyball",
    "Россия. Суперлига": "volleyball",
    "Польша. PlusLiga": "volleyball",
    "Италия. SuperLega": "volleyball",
    "Волейбол": "volleyball",
    # ── MMA ───────────────────────────────────────────────────
    "UFC": "mma",
    "Bellator": "mma",
    "ONE Championship": "mma",
    "ONE FC": "mma",
    "ACB MMA": "mma",
    "PFL": "mma",
    "M-1": "mma",
    "Absolute Championship": "mma",
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
    if any(
        k in ll
        for k in [
            "футбол",
            "лига",
            "премьер",
            "кубок",
            "уефа",
            "серия",
            "бундес",
            "ла лига",
            "копа",
            "mls",
        ]
    ):
        return "football"
    if any(
        k in ll
        for k in ["хоккей", "кхл", "нхл", "hockey", "nhl", "ahl", "shl", "liiga", "del"]
    ):
        return "hockey"
    if any(
        k in ll
        for k in ["баскет", "nba", "евролига", "basketball", "vtb", "acb", "bbl"]
    ):
        return "basket"
    if any(
        k in ll
        for k in [
            "dota",
            "cs2",
            "counter-strike",
            "valorant",
            "esports",
            "rlcs",
            "pubg",
            "apex",
        ]
    ):
        return "esports"
    if any(
        k in ll
        for k in [
            "теннис",
            "atp",
            "wta",
            "itf",
            "уимблдон",
            "ролан гаррос",
            "открытый чемпионат",
        ]
    ):
        return "tennis"
    if any(
        k in ll
        for k in [
            "волейбол",
            "volleyball",
            "суперлига",
            "cev",
            "vnl",
            "plusliga",
            "superlega",
        ]
    ):
        return "volleyball"
    if any(
        k in ll for k in ["ufc", "bellator", "mma", "one championship", "pfl", "acb"]
    ):
        return "mma"
    return "football"


def download_csv_from_api():
    """
    Скачивание данных из ВСЕХ вкладок через Google Sheets API v4.
    Если SHEET_GID пустой - сканируем все вкладки.
    Используем API ключ для доступа.
    """
    try:
        import requests

        # 1. Сначала получаем метаданные таблицы (список вкладок)
        metadata_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}?key={GOOGLE_API_KEY}"
        resp = requests.get(metadata_url, timeout=15)

        if resp.status_code != 200:
            print(f"[WARN] API metadata: {resp.status_code}")
            return None

        metadata = resp.json()
        sheet_title = metadata.get("properties", {}).get("title", "Unknown")
        worksheets = metadata.get("sheets", [])

        print(f"[OK] Connected to Google Sheets API: {sheet_title}")
        print(f"[INFO] Found {len(worksheets)} worksheets")

        # Определяем какие вкладки читать
        target_gids = set()

        # Если указан SHEET_GIDS - используем его (список gid через запятую)
        if SHEET_GIDS:
            target_gids = set(
                str(g.strip()) for g in SHEET_GIDS.split(",") if g.strip()
            )
            print(f"[INFO] Using SHEET_GIDS: {target_gids}")
        elif GID:
            # Если указан одиночный GID
            target_gids = {str(GID)}

        if target_gids:
            # Фильтруем вкладки по GID
            worksheets = [
                ws
                for ws in worksheets
                if str(ws.get("properties", {}).get("sheetId", "")) in target_gids
            ]
            if not worksheets:
                print(
                    f"[WARN] Worksheet GID not found in {target_gids}, scanning all tabs"
                )
                worksheets = metadata.get("sheets", [])
            else:
                print(f"[INFO] Filtered to {len(worksheets)} worksheets by GID")

        # Сканируем все вкладки и собираем данные
        all_rows = []

        for ws in worksheets:
            props = ws.get("properties", {})
            title = props.get("title", "Unknown")
            gid = props.get("sheetId", "unknown")
            sheet_id = props.get("sheetId", 0)

            # Пропускаем Summary
            if "summary" in title.lower():
                print(f"  [SKIP] {title} (summary tab)")
                continue

            # Получаем данные из вкладки через API
            range_name = f"'{title}'!A1:N"  # Читаем колонки A-N
            values_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{range_name}?key={GOOGLE_API_KEY}"

            try:
                values_resp = requests.get(values_url, timeout=15)
                if values_resp.status_code != 200:
                    print(f"  [ERROR] {title}: HTTP {values_resp.status_code}")
                    continue

                values_data = values_resp.json()
                all_values = values_data.get("values", [])

                if not all_values:
                    continue

                # Считаем статистику
                total_rows = len(all_values) - 1  # без заголовка
                marathon_count = 0
                fonbet_count = 0
                winline_count = 0

                for row in all_values[1:]:  # пропускаем заголовок
                    if len(row) < 12:
                        continue

                    # Проверяем URL в колонке 12 (Ссылка)
                    link = row[12].lower() if len(row) > 12 else ""
                    if "marathon" in link:
                        marathon_count += 1
                        all_rows.append(row)
                    elif "fonbet" in link or "bkfon" in link:
                        fonbet_count += 1
                        all_rows.append(row)
                    elif "winline" in link:
                        winline_count += 1
                        all_rows.append(row)

                print(
                    f"  [{title}] GID={gid}, Rows={total_rows}, Marathon={marathon_count}, Fonbet={fonbet_count}, Winline={winline_count}"
                )

            except Exception as e:
                print(f"  [ERROR] {title}: {e}")
                continue

        print(f"[OK] Total rows collected: {len(all_rows)}")

        if not all_rows:
            return None

        # Преобразуем в CSV формат
        header = all_rows[0]
        csv_lines = [",".join(f'"{cell}"' for cell in header)]

        for row in all_rows[1:]:
            csv_lines.append(",".join(f'"{cell}"' for cell in row))

        return "\n".join(csv_lines)

    except ImportError:
        print("[WARN] requests not installed")
        return None
    except Exception as e:
        print(f"[ERROR] Google API: {e}")
        return None


def download_csv():
    """Скачивание CSV из Google Sheets с retry - приоритет: Google API, затем CSV export"""
    print("Попытка использовать Google API...")
    content = download_csv_from_api()

    if content:
        return content

    print("Google API недоступен, используем CSV export...")

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[{attempt}/{max_retries}] Loading data from Google Sheets...")
            req = urllib.request.Request(
                CSV_URL, headers={"User-Agent": "Mozilla/5.0 PRIZMBET-Bot/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode("utf-8")
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
    lines = csv_content.strip().split("\n")
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

        # Определяем тип данных по URL (колонка 12)
        match_url = norm(row[12]) if len(row) > 12 else ""
        is_marathon = "marathon" in match_url.lower()

        if is_marathon:
            # Для marathon данных структура другая:
            # row[0]=sport, row[1]=league_id, row[2]=date, row[3]=time
            # row[4]=team1, row[5]=team2(?), row[6]=p1, row[7]=x, row[8]=p2
            # row[9]=p1x, row[10]=p12, row[11]=league_name, row[12]=URL

            # Проверяем: если row[0] - это число (league_id), значит структура marathon
            if row[0].isdigit() or (row[0] and row[0][0].isdigit()):
                # Marathon структура
                league_id = norm(row[0])
                date = norm(row[1])  # это date
                time_val = norm(row[2])  # это time
                team1 = norm(row[3])
                team2 = norm(row[4])

                # Очистка: иногда дата/время попадает в имя команды
                DATE_TIME_RX = r"\d{1,2}\s+[а-яёА-ЯЁa-zA-Z]{2,4}\s+\d{1,2}:\d{2}"
                team1 = re.sub(DATE_TIME_RX, "", team1).strip()
                team2 = re.sub(DATE_TIME_RX, "", team2).strip()

                # Проверяем: если team2 - число, это коэффициент, значит данные ещё смещены
                # Пробуем взять team1 из row[4], team2 из row[5]
                if not team2 or team2.replace(".", "").isdigit():
                    team1 = norm(row[4])
                    team2 = norm(row[5])
                    team1 = re.sub(DATE_TIME_RX, "", team1).strip()
                    team2 = re.sub(DATE_TIME_RX, "", team2).strip()

                p1 = norm(row[6]) or "0.00"
                x = norm(row[7]) or "0.00"
                p2 = norm(row[8]) or "0.00"
                p1x = norm(row[9]) or "0.00"
                p12 = norm(row[10]) or "0.00"
                league = norm(row[11])  # Это название лиги!
                match_id = date + " " + time_val if date and time_val else league_id
            else:
                # Стандартная структура
                league = norm(row[0])
                match_id = norm(row[1])
                date = norm(row[2])
                time_val = norm(row[3])
                team1 = norm(row[4])
                team2 = norm(row[5])

                DATE_TIME_RX = r"\d{1,2}\s+[а-яёА-ЯЁa-zA-Z]{2,4}\s+\d{1,2}:\d{2}"
                team1 = re.sub(DATE_TIME_RX, "", team1).strip()
                team2 = re.sub(DATE_TIME_RX, "", team2).strip()

                p1 = norm(row[6]) or "0.00"
                x = norm(row[7]) or "0.00"
                p2 = norm(row[8]) or "0.00"
                p1x = norm(row[9]) or "0.00"
                p12 = norm(row[10]) or "0.00"
                px2 = norm(row[11]) or "0.00"
        else:
            # Стандартная структура для Winline
            league = norm(row[0])
            match_id = norm(row[1])
            date = norm(row[2])
            time_val = norm(row[3])
            team1 = norm(row[4])
            team2 = norm(row[5])

            # Очистка: иногда дата/время попадает в имя команды
            DATE_TIME_RX = r"\d{1,2}\s+[а-яёА-ЯЁa-zA-Z]{2,4}\s+\d{1,2}:\d{2}"
            team1 = re.sub(DATE_TIME_RX, "", team1).strip()
            team2 = re.sub(DATE_TIME_RX, "", team2).strip()

            p1 = norm(row[6]) or "0.00"
            x = norm(row[7]) or "0.00"
            p2 = norm(row[8]) or "0.00"
            p1x = norm(row[9]) or "0.00"
            p12 = norm(row[10]) or "0.00"
            px2 = norm(row[11]) or "0.00"

        if not team1 or not team2:
            skipped += 1
            continue

        sport = detect_sport(league)

        entry = {
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
            "px2": px2 if "px2" in dir() else "0.00",
        }
        if match_url:
            entry["match_url"] = match_url
            url_lower = match_url.lower()
            if "winline" in url_lower:
                entry["source"] = "winline"
            elif "marathon" in url_lower:
                entry["source"] = "marathon"
            elif "fonbet" in url_lower or "bkfon" in url_lower:
                entry["source"] = "fonbet"

        matches.append(entry)

    print(f"Parsed {len(matches)} matches from {row_num} rows (skipped {skipped})")
    return matches


def save_matches(matches):
    """Атомарное сохранение matches.json"""
    data = {
        "last_update": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "matches": matches,
    }

    tmp_file = OUTPUT_FILE + ".tmp"
    with open(tmp_file, "w", encoding="utf-8") as f:
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
        sports[m["sport"]] = sports.get(m["sport"], 0) + 1
        leagues[m["league"]] = leagues.get(m["league"], 0) + 1

    print(f"\nTotal: {len(matches)} matches, {len(leagues)} leagues")
    for sport, count in sorted(sports.items()):
        print(f"  {sport}: {count}")


def main():
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

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
