# 💎 PRIZMBET — Мониторинг линий Marathonbet

Современный сервис для мониторинга спортивных событий и коэффициентов. Статический сайт с автоматическим обновлением линии через GitHub Actions.

---

## 🌐 Ссылка на сайт

**[minortermite.github.io/betprizm](https://minortermite.github.io/betprizm)**

---

## 🏗 Архитектура проекта

- **index.html** — Основной интерфейс (Prematch + LIVE)
- **live_index.html** — Специальная версия для LIVE-событий
- **marathon_parser_real.py** — Основной парсер Marathonbet (использует числовые ID категорий)
- **matches.json** — База данных матчей (обновляется автоматически)
- **.github/workflows/update-matches.yml** — Автоматизация парсинга каждые 2 часа

---

## ⚙️ Технологии

- **Backend**: Python, BeautifulSoup4, Requests
- **Frontend**: Vanilla JS, HTML5, CSS3 (Modern Glassmorphism Design)
- **CI/CD**: GitHub Actions, GitHub Pages

---

## 🏆 Поддерживаемые виды спорта

| Иконка | Спорт | Детали |
|---|---|---|
| ⚽ | Футбол | Топ-лиги + LIVE |
| 🏒 | Хоккей | КХЛ, НХЛ, ВХЛ |
| 🏀 | Баскетбол | NBA, Евролига |
| 🎾 | Теннис | ATP, WTA |
| 🏓 | Наст. теннис | **Новое!** Удаление мусора из названий команд |
| 🎮 | Киберспорт | CS2, Dota 2, LoL |
| 🏐 | Волейбол | Суперлига |
| 🥊 | MMA | UFC, Bellator |

---

## 🔄 Автоматизация

Парсинг запускается автоматически через GitHub Actions. Скрипт:

1. Собирает данные по Prematch линиям (150+ лиг).
2. Собирает LIVE события по прямым ID категорий.
3. Очищает названия команд и нормализует коэффициенты.
4. Обновляет `matches.json` и пушит изменения.

---

## 🛠 Локальный запуск

```bash
# Установка зависимостей
pip install requests beautifulsoup4 lxml

# Запуск парсера
python marathon_parser_real.py

# Просмотр сайта
python -m http.server 8000
```

---

## 💰 Приём ставок

**Кошелёк:** `PRIZM-4N7T-L2A7-RQZA-5BETW`
*В комментарии указывать ID события.*

---

*© 2026 PRIZMBET — Современные технологии беттинга.*
