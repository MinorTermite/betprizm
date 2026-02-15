# 🚀 ДЕПЛОЙ НА NETLIFY - PRIZMBET

## ✅ Проект готов к деплою!

**URL:** https://prizmbet.netlify.app/

---

## 📋 Быстрый деплой

### Вариант 1: Через GitHub (рекомендуется)

1. **Создайте репозиторий на GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - PRIZMBET v2.0"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/prizmbet.git
   git push -u origin main
   ```

2. **Подключите к Netlify**
   - Войдите на https://app.netlify.com
   - Нажмите "Add new site" → "Import from Git"
   - Выберите GitHub и ваш репозиторий
   - **Build settings:**
     - Build command: *(оставьте пустым)*
     - Publish directory: `/`
   - Нажмите "Deploy site"

3. **Готово!**
   - Сайт будет доступен по URL: https://YOUR-SITE.netlify.app
   - Автоматический деплой при каждом push в GitHub

### Вариант 2: Drag & Drop

1. Перейдите на https://app.netlify.com/drop
2. Перетащите папку проекта в окно браузера
3. Готово! Сайт задеплоен

---

## ⚙️ Настройка кастомного домена

После деплоя в Netlify Dashboard:

1. Перейдите в **Domain settings**
2. Нажмите **Add custom domain**
3. Введите: `prizmbet.netlify.app` (или свой домен)
4. Следуйте инструкциям для настройки DNS

---

## 🔄 Автообновление на Netlify

### Вариант 1: GitHub Actions (рекомендуется)

Создайте файл `.github/workflows/update-matches.yml`:

```yaml
name: Update Matches Data

on:
  schedule:
    - cron: '0 */5 * * *'  # Каждые 5 часов
  workflow_dispatch:  # Ручной запуск

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install requests beautifulsoup4 lxml
      
      - name: Run parser
        run: python marathon_to_sheets.py
      
      - name: Commit and push if changed
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add matches.json
          git diff --quiet && git diff --staged --quiet || (git commit -m "Auto-update matches data" && git push)
```

### Вариант 2: Netlify Functions

1. Создайте файл `netlify/functions/update-matches.js`:

```javascript
const { spawn } = require('child_process');
const fs = require('fs');

exports.handler = async function(event, context) {
    return new Promise((resolve, reject) => {
        const python = spawn('python3', ['marathon_to_sheets.py']);
        
        let output = '';
        python.stdout.on('data', (data) => {
            output += data.toString();
        });
        
        python.on('close', (code) => {
            if (code === 0 && fs.existsSync('matches.json')) {
                resolve({
                    statusCode: 200,
                    body: JSON.stringify({ 
                        message: 'Matches updated successfully',
                        output: output
                    })
                });
            } else {
                resolve({
                    statusCode: 500,
                    body: JSON.stringify({ 
                        message: 'Update failed',
                        code: code
                    })
                });
            }
        });
    });
};
```

2. Настройте **Scheduled Functions** в Netlify Dashboard:
   - Перейдите в Functions → Scheduled Functions
   - Добавьте расписание: `0 */5 * * *` (каждые 5 часов)

---

## 📊 Структура проекта для деплоя

### Необходимые файлы:
```
prizmbet-final/
├── index.html              ✅ Главная страница
├── matches.json            ✅ База данных (создается автоматически)
├── prizmbet-logo.gif       ✅ Логотип GIF
├── prizmbet-logo.mp4       ✅ Логотип видео
├── qr_wallet.png           ✅ QR-код
├── prizmbet-info-1.png     ✅ Правила 1
├── prizmbet-info-2.png     ✅ Правила 2
├── netlify.toml            ✅ Конфигурация Netlify
├── .gitignore              ✅ Git ignore
├── README.md               ✅ Документация
└── DEPLOYMENT.md           ✅ Этот файл
```

### Файлы для локальной разработки (не нужны на Netlify):
```
├── marathon_to_sheets.py      (парсер)
├── auto_update_server.py      (локальное автообновление)
├── START.bat                  (Windows launcher)
├── requirements.txt           (Python зависимости)
└── *.md                       (документация)
```

---

## 🔍 Проверка перед деплоем

### 1. Проверьте файлы медиа:
```bash
# Все файлы должны существовать:
- prizmbet-logo.gif
- prizmbet-logo.mp4
- qr_wallet.png
- prizmbet-info-1.png
- prizmbet-info-2.png
```

### 2. Проверьте index.html:
```bash
# Откройте index.html в браузере
# Должно работать:
- 3D анимация
- Загрузка логотипа
- Фильтры
- Копирование адреса кошелька
```

### 3. Проверьте matches.json:
```bash
# Создайте тестовый файл:
python marathon_to_sheets.py

# Проверьте структуру:
{
  "last_update": "2026-02-15 12:00:00",
  "matches": [...]
}
```

### 4. Проверьте кошелек:
```
Адрес: PRIZM-4N7T-L2A7-RQZA-5BETW
```

---

## 🐛 Устранение проблем

### Проблема: Сайт не загружается

**Решение:**
- Проверьте Build log в Netlify Dashboard
- Убедитесь, что все файлы закоммичены
- Проверьте netlify.toml

### Проблема: Логотип не отображается

**Решение:**
- Проверьте наличие файлов prizmbet-logo.gif и prizmbet-logo.mp4
- Проверьте пути в index.html (должны быть относительные)

### Проблема: matches.json не обновляется

**Решение для GitHub Actions:**
- Проверьте логи в Actions → Update Matches Data
- Убедитесь, что установлены правильные permissions для workflow

**Решение для Netlify Functions:**
- Проверьте логи в Netlify Dashboard → Functions
- Убедитесь, что Python доступен в окружении

---

## 📱 После деплоя

### 1. Проверьте сайт
Откройте https://prizmbet.netlify.app и убедитесь:
- ✅ Страница загружается
- ✅ 3D анимация работает
- ✅ Логотип отображается
- ✅ Фильтры работают
- ✅ Кошелек отображается
- ✅ Изображения правил загружаются

### 2. Настройте SSL
Netlify автоматически выдает бесплатный SSL сертификат от Let's Encrypt.

### 3. Настройте аналитику (опционально)
В Netlify Dashboard:
- Перейдите в Analytics
- Включите Netlify Analytics ($9/месяц) или подключите Google Analytics

### 4. Поделитесь ссылкой
```
🔗 https://prizmbet.netlify.app
📱 Telegram: https://t.me/+PMrQ9Nbzu08wYmI0
```

---

## ✅ Финальный чеклист

- [ ] Все медиафайлы на месте
- [ ] index.html работает локально
- [ ] matches.json создается корректно
- [ ] Адрес кошелька правильный: PRIZM-4N7T-L2A7-RQZA-5BETW
- [ ] Репозиторий создан на GitHub
- [ ] Проект подключен к Netlify
- [ ] Сайт задеплоен успешно
- [ ] Автообновление настроено (опционально)
- [ ] SSL работает
- [ ] Все проверки пройдены

---

## 🎉 Готово!

Ваш сайт задеплоен и доступен по адресу:

**🌐 https://prizmbet.netlify.app**

---

**Версия:** 2.0  
**Дата:** 15 февраля 2026  
**Статус:** ✅ READY FOR PRODUCTION

💎 **PRIZMBET** — криптобукмекер онлайн!
