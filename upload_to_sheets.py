#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET - Upload real matches to Google Sheets
Source: winline.ru (real parser)
Links: direct match URLs from winline.ru/stavki/event/{id}
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

WINLINE_BASE = 'https://winline.ru/stavki/event/'


def build_match_url(match: dict) -> str:
    """Returns real winline.ru match URL if available, else constructs from id."""
    url = match.get('match_url', '')
    if url and url.startswith('http'):
        return url
    match_id = match.get('id', '')
    if match_id:
        return f"{WINLINE_BASE}{match_id}"
    return ''


def main():
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 60)
    print("PRIZMBET - Upload to Google Sheets (winline.ru real matches)")
    print("=" * 60)

    # Load credentials
    print("\nLoading credentials...")
    creds = Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
    )
    print(f"[OK] Service Account: {creds.service_account_email}")

    # Open spreadsheet
    print(f"\nOpening spreadsheet {SPREADSHEET_ID}...")
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sheet.get_worksheet(0)
    print(f"[OK] Worksheet: {worksheet.title}")

    # Load matches
    print(f"\nLoading matches from {MATCHES_FILE}...")
    with open(MATCHES_FILE, encoding='utf-8') as f:
        data = json.load(f)
    matches = data.get('matches', [])
    source = data.get('source', 'winline.ru')
    last_update = data.get('last_update', '')
    print(f"[OK] Matches: {len(matches)} | Source: {source} | Updated: {last_update}")

    # Prepare header
    header = [
        'Спорт', 'Лига', 'ID', 'Дата', 'Время',
        'Команда 1', 'Команда 2',
        'К1', 'X', 'К2',
        'Ссылка на матч'
    ]

    rows = [header]
    no_url_count = 0

    for m in matches:
        match_url = build_match_url(m)
        if not match_url:
            no_url_count += 1

        rows.append([
            m.get('sport', ''),
            m.get('league', ''),
            m.get('id', ''),
            m.get('date', ''),
            m.get('time', ''),
            m.get('team1', ''),
            m.get('team2', ''),
            m.get('p1', '—'),
            m.get('x', '—'),
            m.get('p2', '—'),
            match_url,
        ])

    if no_url_count:
        print(f"[WARN] {no_url_count} matches have no URL")

    # Upload to sheet
    print(f"\nClearing worksheet...")
    worksheet.clear()
    print(f"Uploading {len(rows) - 1} matches...")
    worksheet.update('A1', rows, value_input_option='RAW')

    print("\n" + "=" * 60)
    print(f"[OK] SUCCESS: {len(rows) - 1} real matches uploaded")
    print(f"[URL] https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print(f"[SOURCE] {source}")
    print("=" * 60)


if __name__ == "__main__":
    main()
