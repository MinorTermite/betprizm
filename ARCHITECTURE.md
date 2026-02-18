# Архитектура PRIZMBET

## Схема работы системы

```
┌─────────────────────────────────────────────────────────────┐
│                  БУКМЕКЕРСКИЕ САЙТЫ                         │
│           (Источники реальных данных)                       │
│                                                             │
│  Winline.ru  |  Marathonbet.ru  |  Fonbet.com             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Playwright парсеры
                     │ (headless browser)
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────────┐
│ winline_parser   │    │ marathon_parser      │
│                 │    │                     │
│ - Парсит линию  │    │ - Парсит линию      │
│ - Коэффициенты  │    │ - Коэффициенты      │
│ - match_url     │    │ - match_url         │
│ - source field  │    │ - source field      │
└────────┬────────┘    └─────────┬───────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  parse_all_real.py    │
         │                      │
         │ - Запуск парсеров    │
         │ - Дедупликация       │
         │ - Нормализация       │
         │ - matches.json       │
         └───────────┬──────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────────┐
│  GITHUB ACTIONS │    │  GOOGLE SHEETS      │
│                 │    │                     │
│ Каждые 2 часа: │    │ upload_to_sheets.py │
│ 1. Парсинг      │    │ - Коэффициенты      │
│ 2. Сохранение   │    │ - Ссылки Winline    │
│ 3. Git commit   │    │ - Ссылки Marathon   │
│ 4. Git push     │    │                     │
└────────┬────────┘    └─────────────────────┘
         │
         │ Push trigger
         │
         ▼
┌─────────────────────────────────────────┐
│            GITHUB PAGES                  │
│                                         │
│  Auto-rebuild при push в master         │
│  Раздача статики (HTML, CSS, JS)       │
│  SSL сертификат (HTTPS)                 │
└─────────────────┬───────────────────────┘
                  │
                  ▼
    ┌──────────────────────────┐
    │   index.html (все БК)    │
    │   winline.html           │
    │   marathon.html          │
    │   fonbet.html            │
    │                          │
    │   1. Fetch matches.json  │
    │   2. Фильтр по БК       │
    │   3. Бейджи источника   │
    │   4. Ссылки проверки    │
    │   5. Фильтры спортов    │
    │   6. Поиск по командам  │
    └──────────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ ПОЛЬЗОВАТЕЛЬ   │
         └────────────────┘
```

## Процесс обновления данных

### Автоматическое обновление (каждые 2 часа)

```
1. GitHub Actions срабатывает по расписанию
   └─ Cron: 0 */2 * * * (00:00, 02:00, 04:00, ..., 22:00 UTC)

2. Устанавливает Playwright + Chromium

3. Запускает parse_all_real.py
   ├─ winline_parser.py → парсит winline.ru
   ├─ marathon_parser.py → парсит marathonbet.ru
   ├─ Дедупликация по названиям команд
   └─ Сохраняет matches.json

4. Запускает upload_to_sheets.py
   ├─ Читает matches.json
   ├─ Формирует строки с ссылками на матчи
   └─ Загружает в Google Sheets

5. Git операции
   ├─ git add matches.json
   ├─ git commit -m "chore: auto-update matches [дата]"
   └─ git push

6. GitHub Pages автоматически пересобирает сайт
```

### Ручное обновление

```
Вариант 1: Через GitHub Actions
└─ Actions → Run workflow → Обновление сразу

Вариант 2: Локально
├─ python parse_all_real.py    # парсинг
├─ python upload_to_sheets.py  # Google Sheets
└─ python upload_to_github.py  # пуш в GitHub
```

## Структура файлов

```
betprizm/
│
├── Frontend (GitHub Pages)
│   ├── index.html              # Главная — все матчи всех БК
│   ├── winline.html            # Страница БК Winline
│   ├── marathon.html           # Страница БК Marathon
│   ├── fonbet.html             # Страница БК Fonbet
│   ├── matches.json            # Данные матчей (обновляется автоматически)
│   ├── prizmbet-logo.gif       # Лого
│   ├── prizmbet-info-1.png     # Инфографика
│   ├── prizmbet-info-2.png     # Инфографика
│   └── qr_wallet.png           # QR код кошелька PRIZM
│
├── Парсеры
│   ├── winline_parser.py       # Парсер Winline.ru (Playwright)
│   ├── marathon_parser.py      # Парсер Marathonbet.ru
│   ├── marathon_parser_real.py # Расширенный парсер Marathon
│   ├── fonbet_parser.py        # Парсер Fonbet.com
│   └── parse_all_real.py       # Общий скрипт — запуск всех парсеров + дедупликация
│
├── Интеграции
│   ├── upload_to_sheets.py     # Загрузка в Google Sheets (с ссылками на матчи)
│   ├── upload_to_github.py     # Загрузка matches.json в GitHub
│   └── update_matches.py       # Синхронизация Google Sheets → matches.json
│
├── Конфигурация
│   ├── requirements.txt        # Python зависимости (playwright, gspread)
│   ├── package.json            # Node.js зависимости
│   ├── netlify.toml            # Конфиг (legacy, для совместимости)
│   ├── .gitignore              # Игнорируемые файлы
│   └── .gitattributes          # Git атрибуты
│
├── CI/CD
│   └── .github/
│       └── workflows/
│           └── update-matches.yml  # GitHub Actions — автообновление каждые 2 часа
│
└── Документация
    ├── README.md               # Основная документация
    ├── QUICK_DEPLOY.md         # Быстрый старт
    ├── DEPLOY_INSTRUCTIONS.md  # Подробная инструкция деплоя
    ├── ARCHITECTURE.md         # Эта схема
    ├── CHANGELOG.md            # История изменений
    └── QUICK_START.md          # Быстрый старт (legacy)
```

## Ключевые компоненты

### 1. Парсеры (Playwright)
```
winline_parser.py:
- Открывает winline.ru через headless Chromium
- Парсит линию матчей
- Извлекает: команды, коэффициенты П1/X/П2, дату, лигу
- Формирует match_url: https://winline.ru/stavki/event/{id}
- source: "winline"

marathon_parser.py:
- Открывает marathonbet.ru
- Парсит линию матчей
- match_url: https://www.marathonbet.ru/su/betting/{id}
- source: "marathon"

parse_all_real.py:
- Запускает оба парсера
- Дедупликация по нормализованным названиям команд
- Сохраняет единый matches.json
```

### 2. Google Sheets
```
upload_to_sheets.py:
- Читает matches.json
- Формирует таблицу со столбцами:
  Спорт | Лига | Дата | Время | Команда 1 | Команда 2 | К1 | X | К2 | Winline (ссылка) | Marathon (ссылка)
- Ссылки ведут на реальные страницы матчей для проверки коэффициентов
- Загружает через gspread + Google Service Account

Таблица: https://docs.google.com/spreadsheets/d/1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk
```

### 3. Frontend (index.html)
```
Возможности:
- Загрузка данных из matches.json
- Бейджи источника: Winline (зелёный) / Marathon (синий) / Fonbet (оранжевый)
- Кнопка "Проверить" → открывает матч на сайте БК
- Фильтры по спортам (футбол, хоккей, баскетбол, киберспорт, теннис)
- Поиск по командам
- Адаптивная верстка (мобильные, планшеты, десктоп)
- Тёмная тема с неоновыми акцентами
- LocalStorage кэширование
```

### 4. Страницы БК
```
winline.html:  Только матчи с source="winline", зелёная тема
marathon.html: Только матчи с source="marathon", синяя тема
fonbet.html:   Только матчи с source="fonbet", оранжевая тема

Каждая страница:
- Фильтрует matches.json по источнику
- Показывает ссылку на матч для проверки коэффициента
- Имеет кнопку "Назад" на главную
```

## Технологический стек

### Frontend
- **HTML5** — разметка
- **CSS3** — стили (gradients, animations, grid, flexbox)
- **Vanilla JavaScript** — логика (без фреймворков)
- **Fetch API** — загрузка данных

### Backend
- **Python 3.11** — парсеры, интеграции
- **Playwright** — headless browser для парсинга
- **gspread** — Google Sheets API
- **GitHub Actions** — CI/CD

### Инфраструктура
- **GitHub** — хостинг кода, автоматизация
- **GitHub Pages** — хостинг сайта, SSL
- **Google Sheets** — таблица с данными

## Безопасность

```
- HTTPS (SSL от GitHub Pages)
- Нет хранения паролей/ключей в коде
- credentials.json в .gitignore
- Google Sheets credentials через GitHub Secrets
- Валидация входных данных в парсерах
```

---

**PRIZMBET** — криптобукмекер на PRIZM
Сайт: https://minortermite.github.io/betprizm/
