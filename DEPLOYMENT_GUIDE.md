# 🚀 Полное руководство по развертыванию PRIZMBET

## 📦 Что входит в комплект

1. **index_ultimate.html** - Улучшенный сайт с:
   - ✨ Параллакс эффектами
   - 📊 Живой статистикой
   - 🎨 Цветовая дифференциация спортов
   - 📈 Прогресс-бар прокрутки
   - 🔄 Автообновление каждые 5 часов

2. **auto_update_server.py** - Автоматический парсер
3. **netlify_deploy.sh** - Скрипт деплоя
4. **.github/workflows/auto-update.yml** - GitHub Actions

---

## 🌐 Вариант 1: Netlify (Рекомендуется)

### Подготовка

```bash
# 1. Установите Node.js и npm
# Windows: https://nodejs.org/
# Mac: brew install node
# Linux: sudo apt install nodejs npm

# 2. Установите Netlify CLI
npm install -g netlify-cli

# 3. Войдите в аккаунт
netlify login
```

### Деплой

```bash
# Запустите скрипт деплоя
./netlify_deploy.sh

# Или вручную:
cd deploy
netlify deploy --prod
```

### Настройка автообновления на Netlify

**Вариант A: Netlify Functions (Serverless)**

1. Создайте папку `netlify/functions`:
```bash
mkdir -p netlify/functions
```

2. Создайте файл `netlify/functions/update-matches.js`:
```javascript
const fetch = require('node-fetch');

exports.handler = async function(event, context) {
  try {
    // Здесь ваш код парсинга
    // Можно вызывать Python скрипт или переписать на JS
    
    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'Matches updated!' })
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message })
    };
  }
};
```

3. Настройте Build Hook в Netlify:
   - Settings → Build & deploy → Build hooks
   - Create build hook → "Auto Update Matches"
   - Скопируйте URL

4. Настройте cron через внешний сервис (например, cron-job.org):
   - URL: ваш build hook
   - Интервал: каждые 5 часов
   - Метод: POST

---

## 🐙 Вариант 2: GitHub Pages + Actions

### 1. Создайте репозиторий

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/username/prizmbet.git
git push -u origin main
```

### 2. Включите GitHub Pages

- Settings → Pages
- Source: Deploy from a branch
- Branch: main → / (root)
- Save

### 3. Настройте секреты (если нужен Netlify)

- Settings → Secrets and variables → Actions
- New repository secret:
  - `NETLIFY_AUTH_TOKEN` - ваш токен Netlify
  - `NETLIFY_SITE_ID` - ID сайта

### 4. GitHub Actions запустится автоматически

Workflow в `.github/workflows/auto-update.yml` будет:
- Обновлять данные каждые 5 часов
- Коммитить изменения
- Деплоить на Netlify (опционально)

---

## 🖥️ Вариант 3: Собственный сервер

### VPS/Dedicated сервер

```bash
# 1. Установите зависимости
sudo apt update
sudo apt install python3 python3-pip nginx

# 2. Установите Python пакеты
pip3 install -r requirements.txt

# 3. Скопируйте файлы
sudo cp -r * /var/www/prizmbet/

# 4. Настройте Nginx
sudo nano /etc/nginx/sites-available/prizmbet
```

Конфигурация Nginx:
```nginx
server {
    listen 80;
    server_name prizmbet.yourdomain.com;
    root /var/www/prizmbet;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /matches.json {
        add_header Cache-Control "public, max-age=300";
    }
}
```

```bash
# 5. Активируйте конфигурацию
sudo ln -s /etc/nginx/sites-available/prizmbet /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 6. Настройте автообновление через cron
crontab -e
```

Добавьте:
```cron
0 */5 * * * cd /var/www/prizmbet && python3 auto_update_server.py
```

### Или используйте systemd service

```bash
sudo nano /etc/systemd/system/prizmbet-update.service
```

```ini
[Unit]
Description=PRIZMBET Auto Update Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/prizmbet
ExecStart=/usr/bin/python3 /var/www/prizmbet/auto_update_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable prizmbet-update
sudo systemctl start prizmbet-update
sudo systemctl status prizmbet-update
```

---

## 🐳 Вариант 4: Docker

### Создайте Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "http.server", "8000"]
```

### Docker Compose с автообновлением

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./matches.json:/app/matches.json
    restart: unless-stopped

  updater:
    build: .
    command: python auto_update_server.py
    volumes:
      - ./matches.json:/app/matches.json
    restart: unless-stopped
```

### Запуск

```bash
docker-compose up -d
```

---

## ⚙️ Локальное тестирование

### Запуск автообновления

```bash
# Windows
python auto_update_server.py

# Mac/Linux
python3 auto_update_server.py
```

### Локальный веб-сервер

```bash
# Python 3
python -m http.server 8000

# Или Node.js
npx http-server -p 8000
```

Откройте: http://localhost:8000

---

## 📊 Мониторинг

### Проверка логов

```bash
# Локально
tail -f update_log.txt

# На сервере
sudo tail -f /var/www/prizmbet/update_log.txt

# Docker
docker logs -f prizmbet-updater
```

### Проверка статуса

```bash
# GitHub Actions
# Вкладка Actions в репозитории

# Systemd
sudo systemctl status prizmbet-update

# Docker
docker ps
docker-compose ps
```

---

## 🔧 Настройки

### Изменить интервал обновления

**auto_update_server.py:**
```python
UPDATE_INTERVAL_HOURS = 3  # Изменить на нужное значение
```

**GitHub Actions (.github/workflows/auto-update.yml):**
```yaml
schedule:
  - cron: '0 */3 * * *'  # Каждые 3 часа
```

**Cron:**
```cron
0 */3 * * * ...  # Каждые 3 часа
```

---

## 🐛 Решение проблем

### Парсер не работает

1. Проверьте доступность Marathon:
```bash
curl -I https://www.marathonbet.com
```

2. Проверьте зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите вручную:
```bash
python marathon_to_sheets.py
```

### Данные не обновляются

1. Проверьте права на файлы:
```bash
ls -la matches.json
chmod 666 matches.json
```

2. Проверьте логи:
```bash
cat update_log.txt
```

3. Проверьте cron/service:
```bash
# Cron
crontab -l

# Service
sudo systemctl status prizmbet-update
```

---

## 🎯 Рекомендации

1. **Для новичков**: Netlify с Build Hooks
2. **Для GitHub пользователей**: GitHub Pages + Actions
3. **Для опытных**: VPS + Nginx + Systemd
4. **Для Docker фанатов**: Docker Compose

---

## 📞 Поддержка

Telegram: https://t.me/+PMrQ9Nbzu08wYmI0

---

💎 **PRIZMBET** - Криптобукмекер на монетах PRIZM
