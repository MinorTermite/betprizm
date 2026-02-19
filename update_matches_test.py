#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from datetime import datetime, timezone

# Загружаем текущий файл
with open('matches.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Обновляем первые 10 матчей тестовыми коэффициентами 1X/12/X2
for i, m in enumerate(data['matches'][:10]):
    m['p1x'] = str(round(1.1 + i * 0.1, 2))
    m['p12'] = str(round(1.2 + i * 0.1, 2))
    m['px2'] = str(round(1.3 + i * 0.1, 2))

# Обновляем timestamp
data['last_update'] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

# Сохраняем
with open('matches.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Updated 10 matches with 1X/12/X2 coefficients')
print('Last update:', data['last_update'])
print('Sample match:', data['matches'][2]['team1'], 'vs', data['matches'][2]['team2'])
print('Coefficients: p1x=', data['matches'][2]['p1x'], 'p12=', data['matches'][2]['p12'], 'px2=', data['matches'][2]['px2'])
