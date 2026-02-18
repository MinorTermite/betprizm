# Инструкция по деплою PRIZMBET на GitHub Pages

## Содержание
1. [Быстрый деплой](#быстрый-деплой)
2. [Настройка автообновления](#настройка-автообновления)
3. [Google Sheets интеграция](#google-sheets)
4. [Проверка работы](#проверка)
5. [Устранение проблем](#проблемы)

---

## Быстрый деплой

### Шаг 1: Подготовка проекта

Убедитесь, что в папке есть:
- `index.html` — главная страница
- `winline.html` — страница БК Winline
- `marathon.html` — страница БК Marathon
- `fonbet.html` — страница БК Fonbet
- `matches.json` — данные матчей
- `winline_parser.py` — парсер Winline
- `marathon_parser.py` — парсер Marathon
- `fonbet_parser.py` — парсер Fonbet
- `parse_all_real.py` — общий парсер
- `.github/workflows/update-matches.yml` — GitHub Actions

### Шаг 2: Создание GitHub репозитория

1. Откройте https://github.com/new
2. Название: `betprizm`
3. Выберите **Public** (нужен для GitHub Pages бесплатно)
4. **НЕ** добавляйте README, .gitignore — они уже есть в проекте
5. Нажмите "Create repository"

### Шаг 3: Загрузка кода

```bash
cd "C:\Users\GravMix\Desktop\suite full stake QWEN\prizmbet-final"

git remote add origin https://github.com/YOUR_USERNAME/betprizm.git
git push -u origin master
```

**Если просит авторизацию:**
- Логин: ваш GitHub username
- Пароль: **Personal Access Token** (не обычный пароль)
  - Создать токен: https://github.com/settings/tokens
  - Permissions: `repo` (полный доступ)

### Шаг 4: Включение GitHub Pages

1. Перейдите в Settings репозитория
2. Раздел "Pages" (левая панель)
3. Source: **Deploy from a branch**
4. Branch: `master`, папка: `/ (root)`
5. Нажмите "Save"
6. Через 1-2 минуты сайт будет доступен по адресу:
   `https://YOUR_USERNAME.github.io/betprizm/`

---

## Настройка автообновления

GitHub Actions уже настроен в `.github/workflows/update-matches.yml`.

Автоматически каждые **2 часа**:
1. Запускает парсеры Winline + Marathon (Playwright)
2. Обновляет `matches.json`
3. Загружает данные в Google Sheets (если настроен)
4. Делает commit + push
5. GitHub Pages автоматически обновляет сайт

### Проверить работу Actions:
1. GitHub → репозиторий → вкладка "Actions"
2. Должны быть зелёные галочки
3. Ручной запуск: "Run workflow" → "Run workflow"

### Необходимые secrets:
- `GOOGLE_CREDENTIALS_JSON` — содержимое credentials.json (для Google Sheets)

Как добавить secret:
1. Settings → Secrets and variables → Actions
2. "New repository secret"
3. Name: `GOOGLE_CREDENTIALS_JSON`
4. Value: вставьте содержимое файла credentials.json

---

## Google Sheets

Данные автоматически загружаются в таблицу:
`https://docs.google.com/spreadsheets/d/1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk`

### Столбцы:
| Спорт | Лига | Дата | Время | Команда 1 | Команда 2 | К1 | X | К2 | Winline | Marathon |

### Ссылки в таблице:
- **Winline**: `https://winline.ru/stavki/event/{id}` — прямая ссылка на матч
- **Marathon**: `https://www.marathonbet.ru/su/betting/{id}` — ссылка Marathon

### Локальный запуск загрузки:
```bash
python upload_to_sheets.py
```
Требуется файл `credentials.json` от Google Service Account.

---

## Проверка

### 1. Главная страница
- Откройте: `https://minortermite.github.io/betprizm/`
- Должны загрузиться матчи с бейджами БК
- Проверьте фильтры по спортам
- Проверьте поиск

### 2. Страницы БК
- Winline: `https://minortermite.github.io/betprizm/winline.html`
- Marathon: `https://minortermite.github.io/betprizm/marathon.html`
- Fonbet: `https://minortermite.github.io/betprizm/fonbet.html`

### 3. Ссылки на матчи
- Нажмите "Проверить" на любом матче
- Должна открыться страница матча на winline.ru/marathonbet.ru

### 4. GitHub Actions
- GitHub → Actions → должны быть зелёные галочки
- Ручной запуск: "Run workflow"

---

## Проблемы

### Матчи не загружаются
1. Проверьте что `matches.json` не пустой
2. Откройте консоль браузера (F12) — посмотрите ошибки
3. Убедитесь что GitHub Pages включен

### GitHub Actions не работает
1. Settings → Actions → General → "Allow all actions"
2. Проверьте secrets (GOOGLE_CREDENTIALS_JSON)
3. Запустите вручную: Actions → Run workflow

### Парсеры падают
1. Проверьте что Playwright установлен: `playwright install chromium`
2. Проверьте requirements.txt — все зависимости
3. Логи Actions покажут ошибку

### Google Sheets не обновляется
1. Проверьте secret GOOGLE_CREDENTIALS_JSON
2. Проверьте доступ Service Account к таблице
3. `continue-on-error: true` — Sheets ошибка не блокирует остальное

---

## Структура деплоя

```
GitHub Repository (MinorTermite/betprizm)
    │
    │ (каждые 2 часа — GitHub Actions)
    │
    ├─ parse_all_real.py → Winline + Marathon парсеры
    │   └─ matches.json (обновлённые данные)
    │
    ├─ upload_to_sheets.py → Google Sheets
    │   └─ Таблица с коэффициентами и ссылками
    │
    ├─ git commit + push
    │   └─ GitHub Pages автоматически пересобирает
    │
    └─ Сайт: https://minortermite.github.io/betprizm/
        ├─ index.html (все матчи)
        ├─ winline.html (только Winline)
        ├─ marathon.html (только Marathon)
        └─ fonbet.html (только Fonbet)
```

---

## Контакты

- **Telegram**: https://t.me/+PMrQ9Nbzu08wYmI0
- **Кошелек PRIZM**: PRIZM-4N7T-L2A7-RQZA-5BETW
- **Сайт**: https://minortermite.github.io/betprizm/
