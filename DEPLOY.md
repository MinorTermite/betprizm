# 🚀 PRIZMBET — Деплой на VPS (без домашнего ПК)

Эта инструкция позволяет запустить Telegram-бот и парсер на облачном сервере,
чтобы всё работало 24/7 независимо от твоего компьютера.

---

## 📋 Что нужно

| Компонент | Описание |
|-----------|----------|
| VPS | Ubuntu 22.04 LTS, минимум 1 CPU / 512 MB RAM |
| GitHub | Репозиторий уже есть: `minortermite/betprizm` |
| Telegram Bot | Токен уже настроен в `telegram_bot.py` |
| PRIZM кошелёк | Настроен в коде |

**Хостинги (цена ~$3–6/мес):**
- [DigitalOcean](https://digitalocean.com) — Droplet Basic $4/мес
- [Hetzner](https://hetzner.com) — Cloud CX11 €3.29/мес
- [Timeweb Cloud](https://timeweb.cloud) — от 160₽/мес
- [Reg.ru VPS](https://reg.ru/vps/) — от 99₽/мес

---

## ⚙️ Шаг 1 — Настройка VPS

Подключись к серверу по SSH:
```bash
ssh root@ВАШ_IP_АДРЕС
```

Обновляем систему и ставим зависимости:
```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git curl
```

Проверяем Python:
```bash
python3 --version   # должно быть 3.10+
```

---

## 📁 Шаг 2 — Клонируем репозиторий

```bash
cd /opt
git clone https://github.com/minortermite/betprizm.git
cd betprizm/prizmbet-final
```

Создаём виртуальное окружение и ставим зависимости:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🔑 Шаг 3 — Настройка переменных

Открой файл `telegram_bot.py` и убедись что данные верны:
```bash
nano telegram_bot.py
```

Проверь строки:
```python
BOT_TOKEN = "8560914086:AAFGDc70pfIwBX0FhwQDWmFjcnnpVvKOxps"
ADMIN_ID  = 984705599
WALLET    = "PRIZM-4N7T-L2A7-RQZA-5BETW"
```

Сохрани: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## 🤖 Шаг 4 — Systemd сервис для Telegram-бота

Создаём systemd-юнит (автозапуск бота при старте сервера):

```bash
nano /etc/systemd/system/prizmbet-bot.service
```

Вставь содержимое:
```ini
[Unit]
Description=PRIZMBET Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/betprizm/prizmbet-final
ExecStart=/opt/betprizm/prizmbet-final/venv/bin/python telegram_bot.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Активируем и запускаем:
```bash
systemctl daemon-reload
systemctl enable prizmbet-bot
systemctl start prizmbet-bot
```

Проверяем статус:
```bash
systemctl status prizmbet-bot
```

Логи бота:
```bash
journalctl -u prizmbet-bot -f
# или
tail -f /opt/betprizm/prizmbet-final/bot.log
```

---

## ⏰ Шаг 5 — Cron для парсера матчей

Парсер запускается каждые 30 минут и обновляет `matches.json`:

```bash
crontab -e
```

Добавь строки в конец файла:
```
# PRIZMBET — обновление матчей каждые 30 минут
*/30 * * * * cd /opt/betprizm/prizmbet-final && /opt/betprizm/prizmbet-final/venv/bin/python marathon_parser_real.py >> /var/log/prizmbet-parser.log 2>&1

# PRIZMBET — проверка ставок каждые 5 минут
*/5 * * * * cd /opt/betprizm/prizmbet-final && /opt/betprizm/prizmbet-final/venv/bin/python bet_parser.py >> /var/log/prizmbet-bets.log 2>&1
```

Сохрани и выйди (`Ctrl+X` если nano).

---

## 🔄 Шаг 6 — Автопуш изменений на GitHub Pages

Чтобы сайт обновлялся автоматически после парсера, нужно настроить git push:

### Вариант A: GitHub Actions (уже настроен)
GitHub Actions уже запускает парсер каждые 30 минут через `.github/workflows/update-matches.yml`.
На VPS парсер нужен только если хочешь чаще обновлять или иметь контроль.

### Вариант B: Push с VPS

Настраиваем SSH-ключ для GitHub:
```bash
ssh-keygen -t ed25519 -C "prizmbet-vps" -f ~/.ssh/github_prizmbet -N ""
cat ~/.ssh/github_prizmbet.pub
```

Скопируй публичный ключ, зайди в:
`GitHub → Settings → SSH and GPG keys → New SSH key`
Вставь ключ и сохрани.

Настраиваем SSH конфиг:
```bash
nano ~/.ssh/config
```
```
Host github.com
  IdentityFile ~/.ssh/github_prizmbet
  StrictHostKeyChecking no
```

Настраиваем git:
```bash
cd /opt/betprizm
git remote set-url origin git@github.com:minortermite/betprizm.git
git config user.email "bot@prizmbet.local"
git config user.name "PRIZMBET Bot"
```

Создаём скрипт обновления `/opt/betprizm/prizmbet-final/update_and_push.sh`:
```bash
#!/bin/bash
set -e
cd /opt/betprizm/prizmbet-final

echo "[$(date)] Запуск парсера..."
../venv/bin/python marathon_parser_real.py

echo "[$(date)] Пуш на GitHub..."
cd /opt/betprizm
git add prizmbet-final/matches.json
git diff --staged --quiet && echo "Нет изменений" && exit 0
git commit -m "auto: update matches $(date '+%Y-%m-%d %H:%M')"
git push origin main

echo "[$(date)] Готово"
```

```bash
chmod +x /opt/betprizm/prizmbet-final/update_and_push.sh
```

Обновляем cron:
```bash
crontab -e
```
```
*/30 * * * * /opt/betprizm/prizmbet-final/update_and_push.sh >> /var/log/prizmbet-update.log 2>&1
```

---

## 🔍 Шаг 7 — Проверка работы

### Проверить бота:
```bash
systemctl status prizmbet-bot   # должен быть Active (running)
journalctl -u prizmbet-bot -n 50
```

### Проверить парсер:
```bash
cd /opt/betprizm/prizmbet-final
source ../venv/bin/activate
python marathon_parser_real.py
cat matches.json | python -c "import json,sys; d=json.load(sys.stdin); print(f'Матчей: {len(d[\"matches\"])}')"
```

### Посмотреть логи:
```bash
tail -f /var/log/prizmbet-parser.log
tail -f /var/log/prizmbet-bets.log
```

---

## 🔧 Обновление кода

При изменениях в коде:
```bash
cd /opt/betprizm
git pull origin main
source prizmbet-final/venv/bin/activate
pip install -r prizmbet-final/requirements.txt  # если изменились зависимости
systemctl restart prizmbet-bot
```

---

## ⚠️ Важные замечания

1. **GitHub Actions** — парсер уже работает через GitHub Actions каждые 30 мин.
   Если поднимаешь VPS только для бота — **шаг 6 можно пропустить**.

2. **Playwright** — `requirements.txt` включает Playwright (браузерный парсер).
   На VPS нужно дополнительно установить браузер:
   ```bash
   source venv/bin/activate
   playwright install chromium --with-deps
   ```
   Если не нужен (marathon_parser_real.py не использует Playwright) — пропусти.

3. **Firewall** — бот работает только через исходящие HTTPS соединения, открывать порты не нужно.

4. **Мониторинг** — бесплатный мониторинг через [UptimeRobot](https://uptimerobot.com):
   Создай монитор типа "Keyword" на https://minortermite.github.io/betprizm —
   получишь уведомления если сайт упадёт.

---

## 📞 Быстрый старт (TL;DR)

```bash
# 1. Подключился к VPS
ssh root@IP

# 2. Установил всё
apt update && apt install -y python3 python3-pip python3-venv git
git clone https://github.com/minortermite/betprizm.git /opt/betprizm
cd /opt/betprizm/prizmbet-final
python3 -m venv venv && source venv/bin/activate
pip install python-telegram-bot apscheduler requests

# 3. Запустил бота как сервис
nano /etc/systemd/system/prizmbet-bot.service   # вставь конфиг из Шага 4
systemctl daemon-reload && systemctl enable --now prizmbet-bot

# 4. Проверил
systemctl status prizmbet-bot
```

Готово! Бот работает 24/7 на сервере. 🎉
