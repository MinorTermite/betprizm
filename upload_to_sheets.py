#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET — Upload real matches to Google Sheets
Sources: marathonbet.ru

Столбцы в таблице:
  Спорт | Лига | Дата | Время | Команда 1 | Команда 2 | К1 | X | К2 | 1X | 12 | X2 | Ссылка Marathon

Ссылки:
  - Marathon: https://marathonbet.ru/...              (из поля match_url_marathon, если есть)
"""

import json
import os
import sys
import io
import gspread
from google.oauth2.service_account import Credentials

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MATCHES_FILE = os.path.join(SCRIPT_DIR, 'matches.json')
CREDS_FILE = os.path.join(SCRIPT_DIR, 'credentials.json')
SPREADSHEET_ID = '1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk'


MARATHON_BASE = 'https://www.marathonbet.ru/su/betting/'

def get_marathon_url(m: dict) -> str:
    """Возвращает прямую ссылку на матч в Marathonbet."""
    # Явное поле от marathon парсера
    url = m.get('match_url_marathon', '')
    if url and url.startswith('http'):
        return url
    # Если матч пришёл из marathon
    src = m.get('source', '')
    match_url = m.get('match_url', '')
    if src == 'marathon' and match_url and match_url.startswith('http'):
        return match_url
    if 'marathonbet' in match_url:
        return match_url
    # Строим из id если префикс ma_
    match_id = m.get('id', '')
    if match_id.startswith('ma_'):
        raw_id = match_id[3:]
        return f"{MARATHON_BASE}{raw_id}"
    return ''


def main():
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 60)
    print("PRIZMBET — Upload to Google Sheets")
    print("MAPPING: Split by Sport tabs")
    print("=" * 60)

    # Credentials
    print("\nLoading credentials...")
    creds = Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
        ]
    )
    print(f"[OK] Service Account: {creds.service_account_email}")

    # Open spreadsheet
    print(f"\nOpening spreadsheet {SPREADSHEET_ID}...")
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Load matches
    print(f"\nLoading {MATCHES_FILE}...")
    with open(MATCHES_FILE, encoding='utf-8') as f:
        data = json.load(f)
    matches = data.get('matches', [])
    print(f"[OK] Total Matches: {len(matches)}")

    # Header
    header = [
        'Спорт', 'Лига', 'Дата', 'Время',
        'Команда 1', 'Команда 2',
        'К1', 'X', 'К2', '1X', '12', 'X2',
        'Marathon (ссылка)'
    ]

    # Mapping
    SPORT_TABS = {
        'football': 'Футбол',
        'hockey': 'Хоккей',
        'basket': 'Баскетбол',
        'tennis': 'Теннис',
        'esports': 'Киберспорт',
        'volleyball': 'Волейбол',
        'mma': 'MMA',
    }

    # Группируем матчи
    grouped = {}
    for m in matches:
        sport = m.get('sport', 'other').lower()
        if sport not in grouped:
            grouped[sport] = []
        
        ma_url = get_marathon_url(m)

        grouped[sport].append([
            m.get('sport', ''),
            m.get('league', ''),
            m.get('date', ''),
            m.get('time', ''),
            m.get('team1', ''),
            m.get('team2', ''),
            m.get('p1', '—'),
            m.get('x', '—'),
            m.get('p2', '—'),
            m.get('p1x', '—'),
            m.get('p12', '—'),
            m.get('px2', '—'),
            ma_url
        ])

    print("\nUploading to tabs...")
    existing_worksheets = {ws.title: ws for ws in sheet.worksheets()}

    for sport, group_rows in grouped.items():
        tab_name = SPORT_TABS.get(sport, 'Other')
        
        if tab_name not in existing_worksheets:
            print(f"  Creating tab: {tab_name}...")
            ws = sheet.add_worksheet(title=tab_name, rows=len(group_rows) + 100, cols=13)
            existing_worksheets[tab_name] = ws
        else:
            ws = existing_worksheets[tab_name]
        
        print(f"  [{tab_name}] Clearing and uploading {len(group_rows)} matches...")
        ws.clear()
        
        upload_data = [header] + group_rows
        ws.update(values=upload_data, range_name='A1', value_input_option='RAW')

    print("\nCleaning up legacy tabs...")
    for title, ws in list(existing_worksheets.items()):
        lower_title = title.lower()
        if "winline" in lower_title or "fonbet" in lower_title or "summary" in lower_title or "matches" == lower_title:
            try:
                print(f"  Deleting legacy tab: {title}")
                sheet.del_worksheet(ws)
            except Exception as e:
                print(f"  [ERROR] Cannot delete {title}: {e}")

    print("\n" + "=" * 60)
    print(f"[OK] SUCCESS: All categories uploaded")
    print(f"[URL] https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print("=" * 60)


if __name__ == "__main__":
    main()
