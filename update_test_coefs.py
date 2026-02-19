#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET - Тестовое обновление коэффициентов 1X/12/X2
Для демонстрации работы системы
"""

import json
from datetime import datetime, timezone

# Загружаем winline.json
with open('winline.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Обновляем коэффициенты 1X/12/X2 для первых 20 матчей
test_values = [
    {'p1x': '1.15', 'p12': '1.25', 'px2': '1.35'},
    {'p1x': '1.20', 'p12': '1.30', 'px2': '1.40'},
    {'p1x': '1.25', 'p12': '1.35', 'px2': '1.45'},
    {'p1x': '1.30', 'p12': '1.40', 'px2': '1.50'},
    {'p1x': '1.35', 'p12': '1.45', 'px2': '1.55'},
    {'p1x': '1.40', 'p12': '1.50', 'px2': '1.60'},
    {'p1x': '1.45', 'p12': '1.55', 'px2': '1.65'},
    {'p1x': '1.50', 'p12': '1.60', 'px2': '1.70'},
    {'p1x': '1.55', 'p12': '1.65', 'px2': '1.75'},
    {'p1x': '1.60', 'p12': '1.70', 'px2': '1.80'},
    {'p1x': '1.65', 'p12': '1.75', 'px2': '1.85'},
    {'p1x': '1.70', 'p12': '1.80', 'px2': '1.90'},
    {'p1x': '1.75', 'p12': '1.85', 'px2': '1.95'},
    {'p1x': '1.80', 'p12': '1.90', 'px2': '2.00'},
    {'p1x': '1.85', 'p12': '1.95', 'px2': '2.05'},
    {'p1x': '1.90', 'p12': '2.00', 'px2': '2.10'},
    {'p1x': '1.95', 'p12': '2.05', 'px2': '2.15'},
    {'p1x': '2.00', 'p12': '2.10', 'px2': '2.20'},
    {'p1x': '2.05', 'p12': '2.15', 'px2': '2.25'},
    {'p1x': '2.10', 'p12': '2.20', 'px2': '2.30'},
]

for i, m in enumerate(data['matches'][:20]):
    if i < len(test_values):
        m['p1x'] = test_values[i]['p1x']
        m['p12'] = test_values[i]['p12']
        m['px2'] = test_values[i]['px2']

# Обновляем timestamp
data['last_update'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

# Сохраняем winline.json
with open('winline.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Создаём matches.json с объединёнными данными
matches_data = {
    'last_update': data['last_update'],
    'source': 'winline.ru (test)',
    'total': data['total'],
    'matches': data['matches']
}

with open('matches.json', 'w', encoding='utf-8') as f:
    json.dump(matches_data, f, ensure_ascii=False, indent=2)

print(f"Updated {min(20, len(data['matches']))} matches with 1X/12/X2 coefficients")
print(f"Last update: {data['last_update']}")
print(f"Files updated: winline.json, matches.json")

# Проверяем результат
print("\nSample matches:")
for i in range(min(3, len(data['matches']))):
    m = data['matches'][i]
    print(f"  {i+1}. {m['team1']} vs {m['team2']}")
    print(f"     P1:{m['p1']} X:{m['x']} P2:{m['p2']} | 1X:{m['p1x']} 12:{m['p12']} X2:{m['px2']}")
