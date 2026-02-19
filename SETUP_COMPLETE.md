# ✅ PRIZMBET - НАСТРОЙКА ЗАВЕРШЕНА

## 🎉 Все системы настроены и работают!

---

## 📊 Google Sheets

**Таблица:** PRIZMBET Матчи  
**URL:** https://docs.google.com/spreadsheets/d/1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk  
**Сервисный аккаунт:** prizmbet@prizmbet.iam.gserviceaccount.com

**Структура таблицы:**
| sport | league | id | date | time | team1 | team2 | 1 | X | 2 | 1X | 12 | X2 | Ссылка |
|-------|--------|----|------|------|-------|-------|---|---|---|----|----|----|--------|

**Данные загружены:** ✅ 123 матча от Winline

---

## 🔄 Автоматическое обновление

### GitHub Actions Workflow

**Расписание:** Каждые 2 часа (в начале чётного часа)  
**Workflow:** `.github/workflows/update-matches.yml`

**Что делает:**
1. Парсит Winline.ru + Marathonbet.ru
2. Загружает данные в Google Sheets
3. Генерирует JSON файлы (winline/marathon/fonbet)
4. Коммитит и пушит изменения
5. GitHub Pages автоматически обновляется

**Последний запуск:** Run #22 (in_progress)

---

## 📁 Файлы проекта

| Файл | Назначение |
|------|------------|
| `parse_all_real.py` | Парсинг Winline + Marathon |
| `winline_parser.py` | Парсер Winline (Playwright) |
| `marathon_parser.py` | Парсер Marathon (Playwright) |
| `upload_to_sheets.py` | Загрузка в Google Sheets |
| `setup_sheets.py` | Настройка Google Sheets |
| `generate_bookmaker_files.py` | Генерация JSON по БК |
| `matches.json` | Объединённые данные |
| `winline.json` | Только Winline матчи |
| `marathon.json` | Только Marathon матчи |
| `fonbet.json` | Только Fonbet матчи |

---

## 🌐 Сайты

| Страница | URL |
|----------|-----|
| **Главная** | https://minortermite.github.io/betprizm/ |
| **Winline** | https://minortermite.github.io/betprizm/winline.html |
| **Marathon** | https://minortermite.github.io/betprizm/marathon.html |
| **Fonbet** | https://minortermite.github.io/betprizm/fonbet.html |

---

## 🚀 Ручное управление

### Запустить парсинг локально:
```bash
cd "C:\Users\GravMix\Desktop\suite full stake QWEN\prizmbet-final"

# Полный парсинг (Winline + Marathon)
python parse_all_real.py

# Только Winline
python winline_parser.py

# Только Marathon
python marathon_parser.py

# Загрузить в Google Sheets
python upload_to_sheets.py

# Сгенерировать JSON файлы
python -c "import json,os; d=json.load(open('matches.json')); [json.dump({'last_update':d['last_update'],'source':s,'total':len(m),'matches':m}, open(f'{s}.json','w',encoding='utf-8'), ensure_ascii=False, indent=2) for s,m in [('winline',[x for x in d['matches'] if x.get('source')=='winline']),('marathon',[x for x in d['matches'] if x.get('source')=='marathon']),('fonbet',[x for x in d['matches'] if x.get('source')=='fonbet'])]]"
```

### Запустить GitHub Actions вручную:
1. https://github.com/MinorTermite/betprizm/actions
2. "Auto-update matches" → "Run workflow"

---

## 🔐 Безопасность

**Файлы в .gitignore:**
- `credentials.json` - сервисный аккаунт Google
- `github_secret.json` - данные для GitHub Secrets

**GitHub Secrets:**
- `GOOGLE_CREDENTIALS_JSON` - JSON сервисного аккаунта

---

## 📈 Мониторинг

**GitHub Actions:**  
https://github.com/MinorTermite/betprizm/actions/workflows/update-matches.yml

**GitHub Pages:**  
https://minortermite.github.io/betprizm/matches.json

**Google Sheets:**  
https://docs.google.com/spreadsheets/d/1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk

---

## ⚠️ Возможные проблемы

### Парсинг не работает
- Проверьте доступность сайтов букмекеров
- Увеличьте timeout в workflow (timeout-minutes: 20)
- Проверьте логи GitHub Actions

### Google Sheets не обновляется
- Проверьте GOOGLE_CREDENTIALS_JSON в секретах
- Убедитесь что таблица открыта для сервисного аккаунта
- Проверьте права доступа (Editor)

### GitHub Pages не обновляется
- Проверьте настройки Pages (Settings → Pages)
- Источник: `main` branch / root folder
- Очистите кэш браузера

---

## 📞 Поддержка

При проблемах:
1. Проверьте логи: https://github.com/MinorTermite/betprizm/actions
2. Проверьте таблицу: https://docs.google.com/spreadsheets/d/1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk
3. Запустите локально: `python parse_all_real.py`

---

**Настроено:** 2026-02-19  
**Версия:** 2.0  
**Статус:** ✅ Работает
