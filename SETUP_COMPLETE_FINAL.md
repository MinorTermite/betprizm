# ✅ НАСТРОЙКА ЗАВЕРШЕНА

## 🎯 Что исправлено:

### 1. Workflow (.github/workflows/update-matches.yml)
✅ Шаг 1: `python update_matches.py` - читает Google Sheets  
✅ Шаг 2: `python upload_to_sheets.py` - загружает обратно  
✅ Шаг 3: `python generate_bookmaker_json.py` - генерирует JSON по БК

### 2. update_matches.py
✅ Читает Google API через GOOGLE_CREDENTIALS_JSON  
✅ Гибкий парсинг заголовков (_header_index)  
✅ Проставляет source по match_url (winline/marathon/fonbet)

### 3. generate_bookmaker_json.py (НОВЫЙ)
✅ Делит матчи по БК по source И по URL  
✅ Генерирует winline.json, marathon.json, fonbet.json

---

## 🔄 РАБОЧИЙ ПРОЦЕСС

### GitHub Actions (каждые 2 часа):
```
1. update_matches.py → читает Google Sheets → matches.json
2. upload_to_sheets.py → загружает данные обратно
3. generate_bookmaker_json.py → создаёт winline/marathon/fonbet.json
4. Коммит и пуш изменений
```

### Локальный запуск:
```bash
# 1. Обновить данные из таблицы
export SHEET_ID='1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk'
export SHEET_GID='0'
python update_matches.py

# 2. Разделить на файлы БК
python generate_bookmaker_json.py

# 3. Проверить totals
python -c "import json; [print(f, json.load(open(f))['total']) for f in ['matches.json','winline.json','marathon.json','fonbet.json']]"

# 4. Отправить на GitHub
git add -A && git commit -m "chore: update matches" && git push origin master:main
```

---

## 📊 ПРОВЕРКА ДАННЫХ

### В Google Sheets должны быть:
✅ Строки с Ссылка содержащей `marathon...` для Marathon  
✅ Строки с Ссылка содержащей `fonbet...` или `bkfon...` для Fonbet  
✅ Коэффициенты в колонках 1, X, 2, 1X, 12, X2 (не "—" и не 0.00)

### После генерации проверить:
```bash
python -c "
import json
for f in ['matches.json','winline.json','marathon.json','fonbet.json']:
    d=json.load(open(f,encoding='utf-8'))
    print(f'{f}: {d.get(\"total\", 0)} matches')
    if d.get('matches'):
        m=d['matches'][0]
        print(f'  First: {m.get(\"team1\")} vs {m.get(\"team2\")}')
        print(f'  URL: {m.get(\"match_url\", \"NO URL\")}')
        print(f'  Source: {m.get(\"source\", \"NO SOURCE\")}')
"
```

---

## 🌐 ПРОВЕРКА САЙТА

### Локально:
```bash
python -m http.server 8000
```

Открыть:
- http://localhost:8000/index.html
- http://localhost:8000/marathon.html
- http://localhost:8000/fonbet.html

### Проверить:
✅ На карточках есть коэффициенты  
✅ Кнопка «Проверить» ведёт на реальный URL  
✅ На Marathon/Fonbet страницах есть матчи (если есть ссылки в таблице)

---

## 🔧 ДИАГНОСТИКА

### Если matches.json пустой:
```bash
# Проверить Google Sheets
echo "Sheet: https://docs.google.com/spreadsheets/d/1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk"

# Запустить вручную
python update_matches.py
```

### Если marathon.json/fonbet.json пустые:
1. Проверить что в таблице есть ссылки на marathonbet.ru / fonbet.ru
2. Проверить логи generate_bookmaker_json.py

### Если Actions падает:
1. Проверить GOOGLE_CREDENTIALS_JSON в Secrets
2. Проверить SHEET_ID и SHEET_GID в Secrets
3. Посмотреть логи workflow

---

## 📁 ФАЙЛЫ

| Файл | Назначение |
|------|------------|
| `update_matches.py` | Чтение/запись Google Sheets |
| `generate_bookmaker_json.py` | Генерация JSON по БК |
| `upload_to_sheets.py` | Загрузка в Google Sheets |
| `matches.json` | Все матчи |
| `winline.json` | Только Winline |
| `marathon.json` | Только Marathon |
| `fonbet.json` | Только Fonbet |

---

## ✅ ВСЁ ГОТОВО!

**Workflow настроен и работает!**  
**Google Sheets - источник истины!**  
**JSON файлы генерируются автоматически!**
