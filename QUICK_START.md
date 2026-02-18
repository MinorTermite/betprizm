# Быстрый старт PRIZMBET

## Как обновить матчи

### Автоматически (GitHub Actions)
Матчи обновляются автоматически каждые 2 часа через GitHub Actions.
Парсеры собирают реальные коэффициенты с Winline.ru и Marathonbet.ru.

### Вручную (локально)
```bash
# Установить зависимости
pip install -r requirements.txt
playwright install chromium

# Запустить парсеры (Winline + Marathon)
python parse_all_real.py

# Загрузить в Google Sheets (нужен credentials.json)
python upload_to_sheets.py

# Загрузить на GitHub
python upload_to_github.py
```

### Через батник (Windows)
```
update.bat
```

## Что делают парсеры

- **winline_parser.py** — парсит реальную линию winline.ru (Playwright)
- **marathon_parser.py** — парсит реальную линию marathonbet.ru
- **fonbet_parser.py** — парсит fonbet.com
- **parse_all_real.py** — запускает все парсеры + дедупликация

Каждый матч содержит:
- Команды, лигу, дату, время
- Коэффициенты П1, X, П2
- Ссылку на матч для проверки (match_url)
- Источник (source: winline/marathon/fonbet)

## Как открыть сайт

### Локально
Откройте `index.html` в браузере

### На GitHub Pages
Сайт: https://minortermite.github.io/betprizm/

### Страницы БК
- Winline: https://minortermite.github.io/betprizm/winline.html
- Marathon: https://minortermite.github.io/betprizm/marathon.html
- Fonbet: https://minortermite.github.io/betprizm/fonbet.html

## Структура проекта

```
betprizm/
├── index.html              <- Главная страница (все БК)
├── winline.html            <- Страница Winline
├── marathon.html           <- Страница Marathon
├── fonbet.html             <- Страница Fonbet
├── matches.json            <- Данные матчей
├── winline_parser.py       <- Парсер Winline
├── marathon_parser.py      <- Парсер Marathon
├── fonbet_parser.py        <- Парсер Fonbet
├── parse_all_real.py       <- Общий парсер
├── upload_to_sheets.py     <- Загрузка в Google Sheets
├── upload_to_github.py     <- Загрузка на GitHub
├── update.bat              <- Быстрое обновление (Windows)
└── .github/workflows/      <- GitHub Actions (автообновление)
```

## Google Sheets

Таблица с матчами и ссылками на БК:
https://docs.google.com/spreadsheets/d/1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk

Столбцы: Спорт | Лига | Дата | Время | Команда 1 | Команда 2 | К1 | X | К2 | Winline (ссылка) | Marathon (ссылка)

## Поддержка

- Telegram: https://t.me/+PMrQ9Nbzu08wYmI0
- Документация: README.md, DEPLOY_INSTRUCTIONS.md

---

**PRIZMBET 2026** — криптобукмекер на PRIZM
