#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ Google Sheets - поиск всех вкладок с данными
"""

import json
import os
import sys

try:
    from google.oauth2.service_account import Credentials
    import gspread
except ImportError as e:
    print(f"ERROR: {e}")
    print("Install: pip install gspread google-auth")
    sys.exit(1)

# Загружаем credentials
creds_file = 'credentials.json'
if not os.path.exists(creds_file):
    print('ERROR: credentials.json not found')
    sys.exit(1)

try:
    creds = Credentials.from_service_account_file(creds_file, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    gc = gspread.authorize(creds)
    print("[OK] Connected to Google Sheets API")
except Exception as e:
    print(f"[ERROR] Google API: {e}")
    sys.exit(1)

# Открываем таблицу
SHEET_ID = '1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk'
try:
    sheet = gc.open_by_key(SHEET_ID)
    print(f"[OK] Table: {sheet.title}")
except Exception as e:
    print(f"[ERROR] Open table: {e}")
    sys.exit(1)

print('=' * 80)
print('GOOGLE SHEETS ANALYSIS')
print('=' * 80)
print(f'Table URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}')
print()

# Проверяем все вкладки
worksheets = sheet.worksheets()
print(f'Total worksheets: {len(worksheets)}')
print()

stats = []

for ws in worksheets:
    title = ws.title
    gid = ws._properties['sheetId']
    
    # Получаем все данные
    try:
        all_values = ws.get_all_values()
    except Exception as e:
        print(f"[ERROR] Read {title}: {e}")
        continue
    
    total_rows = len(all_values)
    
    # Ищем marathon/fonbet/winline
    marathon_rows = 0
    fonbet_rows = 0
    winline_rows = 0
    
    for i, row in enumerate(all_values[1:], 2):  # пропускаем заголовок
        if len(row) >= 13:
            link = row[12].lower() if len(row) > 12 else ''
            if 'marathon' in link:
                marathon_rows += 1
            if 'fonbet' in link or 'bkfon' in link:
                fonbet_rows += 1
            if 'winline' in link:
                winline_rows += 1
    
    stats.append({
        'title': title,
        'gid': gid,
        'total_rows': total_rows,
        'marathon_rows': marathon_rows,
        'fonbet_rows': fonbet_rows,
        'winline_rows': winline_rows
    })
    
    print(f'Worksheet: {title}')
    print(f'  GID: {gid}')
    print(f'  Total rows: {total_rows}')
    print(f'  Marathon rows: {marathon_rows}')
    print(f'  Fonbet rows: {fonbet_rows}')
    print(f'  Winline rows: {winline_rows}')
    print()

# Текущий GID
current_gid = os.getenv('SHEET_GID', '0')
print(f'Current SHEET_GID: {current_gid}')
print()

# Считаем totals
total_marathon = sum(s['marathon_rows'] for s in stats)
total_fonbet = sum(s['fonbet_rows'] for s in stats)
total_winline = sum(s['winline_rows'] for s in stats)

print('=' * 80)
print('SUMMARY')
print('=' * 80)
print(f'Total Marathon rows (all tabs): {total_marathon}')
print(f'Total Fonbet rows (all tabs): {total_fonbet}')
print(f'Total Winline rows (all tabs): {total_winline}')
print()

# Рекомендация
if total_marathon > 0:
    print('✅ Marathon data EXISTS in Google Sheets!')
    print('   RECOMMENDATION: Scan ALL tabs or use correct GID')
    
    # Находим вкладку с максимальным количеством marathon
    best_tab = max(stats, key=lambda x: x['marathon_rows'])
    print(f'   Best tab: {best_tab["title"]} (GID={best_tab["gid"]}, Marathon rows={best_tab["marathon_rows"]})')
else:
    print('❌ NO Marathon data in Google Sheets')
    print('   Need to add Marathon URLs to the table')

if total_fonbet > 0:
    print('✅ Fonbet data EXISTS in Google Sheets!')
else:
    print('❌ NO Fonbet data in Google Sheets')

print()
print('=' * 80)
print('RECOMMENDATION')
print('=' * 80)
if total_marathon > 0 or total_fonbet > 0:
    print('Update update_matches.py to scan ALL tabs:')
    print('  - Loop through all worksheets')
    print('  - Combine rows from all tabs')
    print('  - Or set SHEET_GID to the tab with most data')
else:
    print('No Marathon/Fonbet data in ANY tab.')
    print('Data source only has Winline URLs.')
