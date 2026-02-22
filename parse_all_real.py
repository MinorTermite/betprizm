#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET — Парсер реальных матчей (Marathon-only)
Внимание: Winline и Fonbet отключены.
Используется только marathon_parser.py / marathon.json.

Запуск:
  python parse_all_real.py
"""

from __future__ import annotations

import json
import os
import sys
import io
import re
import datetime
from typing import List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "matches.json")


# =============================================================================
# НОРМАЛИЗАЦИЯ ИМЁН ДЛЯ ДЕДУПЛИКАЦИИ
# =============================================================================

# Таблица транслитерации/синонимов — чтобы "Реал" и "Real Madrid" не считались разными
_SYNONYMS = {
    # Русский → латинский или сокращения
    "манчестер сити": "man city",
    "манчестер юнайтед": "man united",
    "реал мадрид": "real madrid",
    "барселона": "barcelona",
    "ювентус": "juventus",
    "интер": "inter milan",
    "милан": "ac milan",
    "ливерпуль": "liverpool",
    "арсенал": "arsenal",
    "челси": "chelsea",
    "тоттенхэм": "tottenham",
    "бавария": "fc bayern",
    "боруссия": "borussia",
    "спартак": "spartak",
    "цска": "cska",
    "зенит": "zenit",
    "динамо": "dynamo",
}

_NOISE = re.compile(
    r'\b(fc|fk|sc|bk|hk|ac|as|if|ik|sk|nk|rk|ok|cd|ud|cf|rc|sporting|club|'
    r'city|united|town|rovers|wanderers|athletic|athletico|atletico|'
    r'женщины|men|women|w|u17|u19|u21|u23|reserve|ii|2|b)\b',
    re.IGNORECASE
)


def normalize_team(name: str) -> str:
    """Нормализует имя команды для сравнения."""
    s = name.lower().strip()
    # Синонимы
    for src, dst in _SYNONYMS.items():
        if src in s:
            s = s.replace(src, dst)
    # Убираем шумовые слова
    s = _NOISE.sub('', s)
    # Оставляем только буквы и цифры
    s = re.sub(r'[^a-zа-яё0-9]', '', s)
    return s


def teams_match(t1a: str, t2a: str, t1b: str, t2b: str) -> bool:
    """Считает матчи одинаковыми если команды совпадают (в любом порядке)."""
    a1, a2 = normalize_team(t1a), normalize_team(t2a)
    b1, b2 = normalize_team(t1b), normalize_team(t2b)
    if not a1 or not a2 or not b1 or not b2:
        return False
    # Прямое совпадение
    if a1 == b1 and a2 == b2:
        return True
    # Обратный порядок
    if a1 == b2 and a2 == b1:
        return True
    # Частичное совпадение (одна команда содержит другую как подстроку)
    # Защита от ложных срабатываний — минимум 4 символа
    if len(a1) >= 4 and len(b1) >= 4:
        if (a1 in b1 or b1 in a1) and (a2 in b2 or b2 in a2):
            return True
        if (a1 in b2 or b2 in a1) and (a2 in b1 or b1 in a2):
            return True
    return False


def merge_coefs(primary: dict, secondary: dict) -> dict:
    """Берёт коэффициенты из вторичного источника если у первичного они отсутствуют."""
    result = dict(primary)
    for key in ('p1', 'x', 'p2', 'p1x', 'p12', 'px2'):
        if result.get(key, '—') in ('—', '', None):
            val = secondary.get(key, '—')
            if val not in ('—', '', None):
                result[key] = val
    return result


# =============================================================================
# ДЕДУПЛИКАЦИЯ МЕЖДУ ИСТОЧНИКАМИ
# =============================================================================

def dedup_matches(primary: List[dict], secondary: List[dict]) -> List[dict]:
    """
    Объединяет два списка матчей без дублей.
    primary — приоритетный источник (новые данные).
    secondary — дополнительный (существующие).
    """
    result = list(primary)

    for m_sec in secondary:
        t1_s = m_sec.get('team1', '')
        t2_s = m_sec.get('team2', '')
        sport_s = m_sec.get('sport', '')

        found = False
        for i, m_pri in enumerate(result):
            # Матчи должны быть одного вида спорта
            if m_pri.get('sport', '') != sport_s:
                continue
            t1_p = m_pri.get('team1', '')
            t2_p = m_pri.get('team2', '')

            if teams_match(t1_p, t2_p, t1_s, t2_s):
                # Матч уже есть — дополняем коэффициентами если нужно
                result[i] = merge_coefs(m_pri, m_sec)
                # Если у winline есть URL матча а у marathon нет — добавим как второй
                if not result[i].get('match_url_winline') and m_sec.get('match_url'):
                    result[i]['match_url_winline'] = m_sec['match_url']
                found = True
                break

        if not found:
            # Матча нет у marathon — добавляем из winline
            result.append(m_sec)

    return result


# =============================================================================
# СОРТИРОВКА И СОХРАНЕНИЕ
# =============================================================================

MONTHS = {
    'янв': '01', 'фев': '02', 'мар': '03', 'апр': '04',
    'май': '05', 'июн': '06', 'июл': '07', 'авг': '08',
    'сен': '09', 'окт': '10', 'ноя': '11', 'дек': '12',
}


def sort_key(m: dict) -> str:
    d = m.get('date', '')
    t = m.get('time', '')
    parts = d.split()
    if len(parts) == 2:
        return f"{MONTHS.get(parts[1].lower(), '01')}-{parts[0].zfill(2)} {t}"
    return f"99-99 {t}"


def save_matches(matches: List[dict], sources: List[str]) -> None:
    # Финальная дедупликация по id внутри одного источника
    seen: dict = {}
    for m in matches:
        k = m.get('id', '')
        if k and k not in seen:
            seen[k] = m
    unique = list(seen.values())
    unique.sort(key=sort_key)

    data = {
        "last_update": datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        "source": ", ".join(sources),
        "total": len(unique),
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


# =============================================================================
# ЗАПУСК ПАРСЕРОВ
# =============================================================================

def run_marathon() -> List[dict]:
    print("\n" + "=" * 60)
    print("[1/1] Marathonbet.ru")
    print("=" * 60)
    try:
        from marathon_parser import run_parser
        matches = run_parser()
        for m in matches:
            m.setdefault('source', 'marathon')
        print(f"  Marathon: {len(matches)} матчей")
        return matches
    except ImportError as e:
        print(f"  Marathon ПРЕДУПРЕЖДЕНИЕ: {e} (парсер не доступен)")
        print("  Установите playwright: pip install playwright && playwright install chromium")
        return []  # Не ломаем пайплайн, если парсер недоступен
    except Exception as e:
        print(f"  Marathon ОШИБКА: {e}")
        # Возвращаем пустой список вместо прерывания всего пайплайна
        return []


def print_stats(matches: List[dict]) -> None:
    from collections import Counter
    sports = Counter(m['sport'] for m in matches)
    sources = Counter(m.get('source', '?') for m in matches)
    icons = {
        'football': '⚽', 'hockey': '🏒', 'basket': '🏀',
        'esports': '🎮', 'tennis': '🎾', 'volleyball': '🏐', 'mma': '🥊',
    }
    print("\n📊 По видам спорта:")
    for sport, cnt in sorted(sports.items(), key=lambda x: -x[1]):
        print(f"  {icons.get(sport, '?')} {sport}: {cnt}")
    print("\n📡 По источникам:")
    for src, cnt in sorted(sources.items()):
        print(f"  {src}: {cnt}")


# =============================================================================
# MAIN
# =============================================================================

def load_existing_matches() -> List[dict]:
    """Загружает существующие матчи из matches.json для объединения"""
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('matches', [])
    except (FileNotFoundError, json.JSONDecodeError):
        print("  Нет существующего файла matches.json, начинаем с пустого")
        return []


def main():
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 60)
    print("PRIZMBET — Парсер: Marathon")
    print("Дедупликация по именам команд")
    print("=" * 60)

    # Загружаем существующие матчи из Google Sheets
    existing_matches = load_existing_matches()
    print(f"  Загружено существующих матчей: {len(existing_matches)}")

    marathon_matches = run_marathon()

    if not marathon_matches:
        print("\nПРЕДУПРЕЖДЕНИЕ: источник не вернул матчи, но продолжаем выполнение")

    parsed_matches = marathon_matches
    
    # Затем объединяем с существующими матчами
    final_matches = dedup_matches(existing_matches, parsed_matches)

    sources = ["google_sheets"]
    if marathon_matches:
        sources.append("marathonbet.ru")

    save_matches(final_matches, sources)
    print_stats(final_matches)

    print("\n" + "=" * 60)
    print("✅ ГОТОВО")


if __name__ == "__main__":
    main()
