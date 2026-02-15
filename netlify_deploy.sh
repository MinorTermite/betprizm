#!/bin/bash

# PRIZMBET Netlify Deployment Script

echo "╔═══════════════════════════════════════════════════╗"
echo "║   💎 PRIZMBET - Деплой на Netlify               ║"
echo "╚═══════════════════════════════════════════════════╝"
echo ""

# Проверка наличия Netlify CLI
if ! command -v netlify &> /dev/null; then
    echo "⚠️  Netlify CLI не установлен!"
    echo "📦 Установка Netlify CLI..."
    npm install -g netlify-cli
fi

# Создание папки для деплоя
echo "📁 Подготовка файлов..."
rm -rf deploy
mkdir -p deploy

# Копирование файлов
cp index_ultimate.html deploy/index.html
cp matches.json deploy/
cp prizmbet-logo.gif deploy/
cp prizmbet-info-1.png deploy/
cp prizmbet-info-2.png deploy/
cp qr_wallet.png deploy/

# Создание _redirects для SPA
echo "/* /index.html 200" > deploy/_redirects

# Создание netlify.toml
cat > deploy/netlify.toml << 'TOML'
[build]
  publish = "."
  
[[headers]]
  for = "/*"
  [headers.values]
    Cache-Control = "public, max-age=0, must-revalidate"
    
[[headers]]
  for = "/matches.json"
  [headers.values]
    Cache-Control = "public, max-age=300, s-maxage=300"
    
[[headers]]
  for = "/*.png"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
    
[[headers]]
  for = "/*.gif"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
TOML

echo "✅ Файлы подготовлены!"
echo ""

# Деплой
echo "🚀 Запуск деплоя на Netlify..."
cd deploy

# Первый деплой (создание сайта)
if [ ! -f ".netlify/state.json" ]; then
    echo "📝 Первый деплой - создание нового сайта..."
    netlify deploy --prod
else
    echo "🔄 Обновление существующего сайта..."
    netlify deploy --prod
fi

echo ""
echo "✅ Деплой завершен!"
echo "🌐 Ваш сайт доступен по адресу, который показан выше"
echo ""
