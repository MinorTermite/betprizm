# 🔄 АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ PRIZMBET

## ⚙️ Настройка автоматического обновления

### 1. GitHub Secrets

Добавьте следующие секреты в репозиторий GitHub (Settings → Secrets → Actions → New repository secret):

#### GOOGLE_CREDENTIALS_JSON
JSON сервисного аккаунта Google Cloud для доступа к Google Sheets.

**Как получить:**
1. Откройте [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте проект или выберите существующий
3. Включите Google Sheets API и Google Drive API
4. Создайте сервисный аккаунт (Service Account)
5. Скачайте JSON ключ
6. Скопируйте содержимое файла в секрет `GOOGLE_CREDENTIALS_JSON`

#### SHEET_ID (опционально)
ID Google таблицы для загрузки коэффициентов.
```
SHEET_ID=1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk
```

---

## 📅 Расписание обновлений

GitHub Actions автоматически запускается **каждые 2 часа**:
- Парсит матчи с Winline.ru и Marathonbet.ru
- Загружает данные в Google Sheets
- Обновляет `matches.json` на GitHub Pages

**Время запуска:** В начале каждого чётного часа (00:00, 02:00, 04:00, ...)

---

## 🚀 Ручной запуск

### Через GitHub UI
1. Откройте https://github.com/MinorTermite/betprizm/actions
2. Выберите workflow "Auto-update matches"
3. Нажмите "Run workflow"
4. Выберите ветку (master)
5. Нажмите "Run workflow"

### Локально (Windows)
```bash
cd "C:\Users\GravMix\Desktop\suite full stake QWEN\prizmbet-final"

# Запустить полный парсинг (Winline + Marathon)
python parse_all_real.py

# Только Winline
python winline_parser.py

# Только Marathon
python marathon_parser.py

# Обновить Google Sheets
python upload_to_sheets.py

# Сгенерировать JSON файлы по БК
python -c "import json,os; d=json.load(open('matches.json')); [json.dump({'last_update':d['last_update'],'source':s,'total':len(m),'matches':m}, open(f'{s}.json','w',encoding='utf-8'), ensure_ascii=False, indent=2) for s,m in [('winline',[x for x in d['matches'] if x.get('source')=='winline']),('marathon',[x for x in d['matches'] if x.get('source')=='marathon']),('fonbet',[x for x in d['matches'] if x.get('source')=='fonbet'])]]"
```

---

## 📊 Структура данных

### matches.json
```json
{
  "last_update": "2026-02-19 12:00:00",
  "source": "winline.ru, marathonbet.ru",
  "total": 250,
  "matches": [
    {
      "sport": "football",
      "league": "Испания. Ла Лига",
      "id": "12345",
      "date": "20 фев",
      "time": "20:00",
      "team1": "Реал Мадрид",
      "team2": "Барселона",
      "match_url": "https://winline.ru/stavki/event/12345",
      "p1": "2.15",
      "x": "3.50",
      "p2": "3.20",
      "p1x": "1.35",
      "p12": "1.28",
      "px2": "1.72",
      "source": "winline"
    }
  ]
}
```

### Страницы БК
- **winline.json** — матчи только от Winline
- **marathon.json** — матчи только от Marathon
- **fonbet.json** — матчи только от Fonbet

---

## 🔧 Проверка статуса

### GitHub Actions
https://github.com/MinorTermite/betprizm/actions

### GitHub Pages
https://minortermite.github.io/betprizm/matches.json

### Google Sheets
https://docs.google.com/spreadsheets/d/1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk

---

## ⚠️ Возможные проблемы

### Парсинг не работает
- Проверьте доступность сайтов букмекеров
- Увеличьте timeout в workflow (timeout-minutes: 20)
- Проверьте логи GitHub Actions

### Google Sheets не обновляется
- Проверьте GOOGLE_CREDENTIALS_JSON в секретах
- Убедитесь что таблица открыта для доступа
- Проверьте права сервисного аккаунта

### GitHub Pages не обновляется
- Проверьте настройки Pages (Settings → Pages)
- Источник должен быть: `main` branch / root folder
- Очестите кэш браузера

---

## 📝 Логи

Логи парсинга сохраняются в GitHub Actions:
https://github.com/MinorTermite/betprizm/actions/workflows/update-matches.yml
