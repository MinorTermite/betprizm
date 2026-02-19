#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET - Настройка Google Sheets и GitHub Secrets
"""

import json
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread
import base64

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE = os.path.join(SCRIPT_DIR, 'credentials.json')
SHEET_ID = '1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk'

def main():
    print("=" * 60)
    print("PRIZMBET - Google Sheets Setup")
    print("=" * 60)
    
    # Загружаем credentials
    print("\n[1/4] Loading credentials...")
    with open(CREDS_FILE, 'r', encoding='utf-8') as f:
        creds_data = json.load(f)
    
    creds = Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
    )
    
    print(f"  Service Account: {creds.service_account_email}")
    print(f"  Project: {creds.project_id}")
    
    # Предоставляем доступ к таблице
    print("\n[2/4] Setting up Google Sheets access...")
    drive_service = build('drive', 'v3', credentials=creds)
    
    try:
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': creds_data['client_email']
        }
        
        result = drive_service.permissions().create(
            fileId=SHEET_ID,
            body=permission,
            fields='id'
        ).execute()
        
        print(f"  [OK] Permission added: {result.get('id')}")
    except Exception as e:
        print(f"  [INFO] Permission may already exist")
    
    # Тестируем доступ к таблице
    print("\n[3/4] Testing Google Sheets access...")
    gc = gspread.authorize(creds)
    
    try:
        sheet = gc.open_by_key(SHEET_ID)
        worksheet = sheet.get_worksheet(0)
        
        print(f"  [OK] Sheet: {sheet.title}")
        print(f"  [OK] Worksheet: {worksheet.title}")
        
        # Получаем данные
        all_values = worksheet.get_all_values()
        print(f"  [OK] Rows: {len(all_values)}")
        
        if all_values:
            print(f"  Header: {all_values[0]}")
            if len(all_values) > 1:
                print(f"  First row: {all_values[1]}")
        
    except Exception as e:
        print(f"  [ERROR] {e}")
        print("\  IMPORTANT: Share sheet with service account email:")
        print(f"  {creds_data['client_email']}")
        print(f"  URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
        return
    
    # Подготовка данных для GitHub Secrets
    print("\n[4/4] Preparing GitHub Secrets data...")
    
    # Кодируем в base64 для безопасности
    creds_json = json.dumps(creds_data)
    creds_base64 = base64.b64encode(creds_json.encode()).decode()
    
    print(f"\n{'=' * 60}")
    print("SETUP COMPLETE!")
    print("=" * 60)
    
    print("\n=== Google Sheets Access ===")
    print(f"Sheet URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    print(f"Service Account: {creds_data['client_email']}")
    
    print("\n=== GitHub Secret (for reference) ===")
    print("The credentials.json file is ready for GitHub Actions")
    
    print("\n=== Next Steps ===")
    print("1. Run: python upload_to_sheets.py")
    print("2. Or trigger GitHub Actions workflow")
    
    return 0

if __name__ == "__main__":
    main()
