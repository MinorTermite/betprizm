#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET — Объединённый парсер реальных матчей
Источники:
  1. winline.ru  — playwright (winline_parser.py)
  2. fonbet.ru   — REST API  (fonbet_parser.py)

Запуск:
  python parse_all_real.py

GitHub Actions запускает этот файл каждые 2 часа.
Результат: matches.json (объединённый, без дублей, отсортированный по времени)
Затем: upload_to_sheets.py загружает данные в Google Sheets.
"""

from __future__ import annotations

import json
import os
import sys
import io
import datetime
from typing import List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "matches.json")


def merge_and_save(all_matches: List[dict], sources: List[str]) -> None:
    """Дедупликация, сортировка, сохранение."""
    seen: dict = {}
    for m in all_matches:
        k = m.get("id", "")
        if k and k not in seen:
            seen[k] = m
    unique = list(seen.values())

    months = {
        'янв': '01', 'фев': '02', 'мар': '03', 'апр': '04',
        'май': '05', 'июн': '06', 'июл': '07', 'авг': '08',
        'сен': '09', 'окт': '10', 'ноя': '11', 'дек': '12',
    }

    def sort_key(m):
        d = m.get('date', '')
        t = m.get('time', '')
        parts = d.split()
        if len(parts) == 2:
            return f"{months.get(parts[1].lower(), '01')}-{parts[0].zfill(2)} {t}"
        return f"99-99 {t}"

    unique.sort(key=sort_key)

    data = {
        "last_update": datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        "source": ", ".join(sources),
        "matches": unique,
    }

    tmp = OUTPUT_FILE + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if os.path.exists(OUTPUT_FILE):
        os.replace(tmp, OUTPUT_FILE)
    else:
        os.rename(tmp, OUTPUT_FILE)

    kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"\n✓ matches.json сохранён ({kb:.1f} KB)")
    print(f"✓ Итого уникальных матчей: {len(unique)}")
    print(f"✓ Источники: {', '.join(sources)}")


def run_winline() -> tuple[List[dict], bool]:
    """Запускает winline_parser и возвращает матчи."""
    print("\n" + "=" * 60)
    print("[1/2] Winline.ru (playwright)")
    print("=" * 60)
    try:
        from winline_parser import run_parser
        matches = run_parser()
        print(f"  Winline: {len(matches)} матчей")
        return matches, True
    except Exception as e:
        print(f"  Winline ОШИБКА: {e}")
        return [], False


def run_fonbet() -> tuple[List[dict], bool]:
    """Запускает fonbet_parser и возвращает матчи."""
    print("\n" + "=" * 60)
    print("[2/2] Fonbet.ru (REST API)")
    print("=" * 60)
    try:
        from fonbet_parser import run_parser
        matches = run_parser()
        print(f"  Fonbet: {len(matches)} матчей")
        return matches, True
    except Exception as e:
        print(f"  Fonbet ОШИБКА: {e}")
        return [], False


def print_stats(matches: List[dict]) -> None:
    from collections import Counter
    sports = Counter(m['sport'] for m in matches)
    print("\n📊 По видам спорта:")
    icons = {
        'football': '⚽', 'hockey': '🏒', 'basket': '🏀',
        'esports': '🎮', 'tennis': '🎾', 'volleyball': '🏐', 'mma': '🥊',
    }
    for sport, cnt in sorted(sports.items(), key=lambda x: -x[1]):
        print(f"  {icons.get(sport, '?')} {sport}: {cnt}")


def main():
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 60)
    print("PRIZMBET — Объединённый парсер реальных матчей")
    print("Источники: winline.ru + fonbet.ru")
    print("=" * 60)

    all_matches: List[dict] = []
    sources: List[str] = []

    winline_matches, ok1 = run_winline()
    if ok1 and winline_matches:
        all_matches.extend(winline_matches)
        sources.append("winline.ru")

    fonbet_matches, ok2 = run_fonbet()
    if ok2 and fonbet_matches:
        all_matches.extend(fonbet_matches)
        sources.append("fonbet.ru")

    if not all_matches:
        print("\nFATAL: ни один источник не вернул матчи")
        sys.exit(1)

    merge_and_save(all_matches, sources)
    print_stats(all_matches)

    print("\n" + "=" * 60)
    print("✅ ГОТОВО")


if __name__ == "__main__":
    main()
