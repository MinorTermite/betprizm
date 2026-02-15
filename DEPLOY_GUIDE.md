# 🚀 Полное руководство по деплою PRIZMBET на Netlify

## Вариант 1: Простой деплой (без автообновления)

### Шаг 1: Подготовка файлов
1. Скачайте все файлы из архива
2. Убедитесь, что у вас есть:
   - index_ultimate.html (переименуйте в index.html)
   - matches.json
   - prizmbet-logo.gif
   - prizmbet-info-1.png
   - prizmbet-info-2.png
   - qr_wallet.png

### Шаг 2: Деплой на Netlify
1. Зайдите на https://netlify.com
2. Зарегистрируйтесь (бесплатно)
3. Нажмите "Add new site" → "Deploy manually"
4. Перетащите папку с файлами на сайт
5. Готово! Ваш сайт опубликован

---

## Вариант 2: Деплой с GitHub + автообновление

### Шаг 1: Создание репозитория на GitHub

```bash
# На вашем компьютере
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/ваш-юзернейм/prizmbet.git
git push -u origin main
```

### Шаг 2: Подключение к Netlify

1. На Netlify: "Add new site" → "Import an existing project"
2. Выберите GitHub
3. Выберите ваш репозиторий `prizmbet`
4. Deploy!

### Шаг 3: Настройка автообновления

Создайте файл `.github/workflows/auto-update.yml`:

```yaml
name: Auto Update Matches

on:
  schedule:
    # Запуск каждые 5 часов
    - cron: '0 */5 * * *'
  workflow_dispatch: # Ручной запуск

jobs:
  update:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install requests beautifulsoup4 lxml
      
      - name: Run parser
        run: |
          python auto_parser.py
      
      - name: Commit changes
        run: |
          git config --global user.name 'GitHub Actions'
          git config --global user.email 'actions@github.com'
          git add matches.json
          git diff --quiet && git diff --staged --quiet || git commit -m "Auto-update matches [$(date)]"
          git push
```

---

## Вариант 3: VPS сервер с автообновлением

### Для Ubuntu/Debian:

```bash
# 1. Установка зависимостей
sudo apt update
sudo apt install python3 python3-pip git nginx -y

# 2. Клонирование репозитория
cd /var/www/
git clone https://github.com/ваш-юзернейм/prizmbet.git
cd prizmbet

# 3. Установка Python пакетов
pip3 install requests beautifulsoup4 lxml

# 4. Создание systemd сервиса для парсера
sudo nano /etc/systemd/system/prizmbet-parser.service
```

Содержимое файла:
```ini
[Unit]
Description=PRIZMBET Auto Parser
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/prizmbet
ExecStart=/usr/bin/python3 /var/www/prizmbet/auto_parser.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 5. Запуск сервиса
sudo systemctl daemon-reload
sudo systemctl enable prizmbet-parser
sudo systemctl start prizmbet-parser

# 6. Проверка статуса
sudo systemctl status prizmbet-parser

# 7. Настройка Nginx
sudo nano /etc/nginx/sites-available/prizmbet
```

Конфигурация Nginx:
```nginx
server {
    listen 80;
    server_name ваш-домен.com;
    root /var/www/prizmbet;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /matches.json {
        add_header Cache-Control "no-cache, must-revalidate";
        expires 0;
    }
}
```

```bash
# 8. Активация сайта
sudo ln -s /etc/nginx/sites-available/prizmbet /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Вариант 4: Netlify Functions (автообновление на serverless)

Создайте `netlify/functions/update-matches.js`:

```javascript
const fetch = require('node-fetch');
const fs = require('fs');
const path = require('path');

exports.handler = async (event, context) => {
  try {
    // Здесь ваш код парсинга
    // Например, вызов внешнего API или парсинг сайта
    
    const matches = {
      last_update: new Date().toISOString(),
      matches: [
        // ... ваши матчи
      ]
    };

    // Сохранение в файл
    const matchesPath = path.join(__dirname, '../../matches.json');
    fs.writeFileSync(matchesPath, JSON.stringify(matches, null, 2));

    return {
      statusCode: 200,
      body: JSON.stringify({ success: true, message: 'Matches updated' })
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message })
    };
  }
};
```

Создайте `netlify.toml`:

```toml
[build]
  functions = "netlify/functions"

[[redirects]]
  from = "/api/update"
  to = "/.netlify/functions/update-matches"
  status = 200

# Scheduled function (требует платный план Netlify)
[[plugins]]
  package = "@netlify/plugin-scheduled-functions"

  [plugins.inputs]
    schedule = "0 */5 * * *"  # Каждые 5 часов
```

---

## Мониторинг и логи

### Просмотр логов парсера (VPS):
```bash
sudo journalctl -u prizmbet-parser -f
```

### Ручное обновление:
```bash
cd /var/www/prizmbet
python3 auto_parser.py
```

### Перезапуск парсера:
```bash
sudo systemctl restart prizmbet-parser
```

---

## Troubleshooting

### Парсер не работает?
1. Проверьте логи: `sudo journalctl -u prizmbet-parser`
2. Проверьте права: `sudo chown -R www-data:www-data /var/www/prizmbet`
3. Проверьте Python: `python3 --version`

### Matches.json не обновляется?
1. Проверьте права на запись: `ls -la matches.json`
2. Проверьте наличие файла: `cat matches.json`
3. Проверьте systemd сервис: `systemctl status prizmbet-parser`

### Сайт не открывается?
1. Проверьте Nginx: `sudo nginx -t`
2. Проверьте логи: `sudo tail -f /var/log/nginx/error.log`
3. Проверьте firewall: `sudo ufw status`

---

## Рекомендации

1. **Для начала**: Используйте Netlify (Вариант 1 или 2)
2. **Для масштаба**: VPS сервер (Вариант 3)
3. **Для бизнеса**: GitHub Actions + Netlify (Вариант 2)

**Важно**: Парсер `auto_parser.py` - это базовая версия. Замените функцию `create_sample_matches()` на ваш реальный парсер из папки `marathon_to_sheets.py`.

---

💡 **Совет**: Начните с простого деплоя на Netlify, протестируйте, затем добавьте автообновление через GitHub Actions.
