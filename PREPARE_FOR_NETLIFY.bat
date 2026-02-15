@echo off
chcp 65001 >nul
cls

echo ╔══════════════════════════════════════════════════════════════════╗
echo ║                                                                  ║
echo ║        💎 PRIZMBET - ПОДГОТОВКА К ДЕПЛОЮ НА NETLIFY             ║
echo ║                                                                  ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

echo 🔍 Проверка файлов...
echo.

REM Проверяем наличие обязательных файлов
set "error=0"

if exist "index_updated.html" (
    echo ✅ index_updated.html найден
) else (
    echo ❌ index_updated.html НЕ найден!
    set "error=1"
)

if exist "matches.json" (
    echo ✅ matches.json найден
) else (
    echo ❌ matches.json НЕ найден!
    set "error=1"
)

if exist "netlify.toml" (
    echo ✅ netlify.toml найден
) else (
    echo ❌ netlify.toml НЕ найден!
    set "error=1"
)

if exist "prizmbet-logo.mp4" (
    echo ✅ prizmbet-logo.mp4 найден
) else (
    echo ⚠️  prizmbet-logo.mp4 НЕ найден (необязательно)
)

if exist "prizmbet-logo.gif" (
    echo ✅ prizmbet-logo.gif найден
) else (
    echo ❌ prizmbet-logo.gif НЕ найден!
    set "error=1"
)

if exist "prizmbet-info-1.png" (
    echo ✅ prizmbet-info-1.png найден
) else (
    echo ❌ prizmbet-info-1.png НЕ найден!
    set "error=1"
)

if exist "prizmbet-info-2.png" (
    echo ✅ prizmbet-info-2.png найден
) else (
    echo ❌ prizmbet-info-2.png НЕ найден!
    set "error=1"
)

if exist "qr_wallet.png" (
    echo ✅ qr_wallet.png найден
) else (
    echo ❌ qr_wallet.png НЕ найден!
    set "error=1"
)

echo.
echo ══════════════════════════════════════════════════════════════════
echo.

if %error%==1 (
    echo ❌ ОШИБКА! Некоторые файлы отсутствуют.
    echo    Пожалуйста, убедитесь, что все файлы на месте.
    echo.
    pause
    exit /b 1
)

echo ✅ Все файлы найдены!
echo.

REM Переименовываем index_updated.html в index.html
echo 🔄 Переименование index_updated.html в index.html...

if exist "index.html" (
    echo    Создаем резервную копию старого index.html...
    copy /Y "index.html" "index.html.backup" >nul
    echo    ✅ Резервная копия создана: index.html.backup
)

copy /Y "index_updated.html" "index.html" >nul
echo ✅ Файл переименован!
echo.

echo ══════════════════════════════════════════════════════════════════
echo.
echo ✅ ПОДГОТОВКА ЗАВЕРШЕНА!
echo.
echo 📋 Следующие шаги:
echo    1. Откройте https://app.netlify.com/drop
echo    2. Перетащите ВСЮПАПКУ в браузер
echo    3. Дождитесь завершения загрузки
echo    4. Получите ссылку на ваш сайт!
echo.
echo 🔄 Для настройки автообновления:
echo    Прочитайте файл NETLIFY_DEPLOY_GUIDE.md
echo.
echo 📱 Поддержка: https://t.me/+PMrQ9Nbzu08wYmI0
echo.
echo ══════════════════════════════════════════════════════════════════
echo.
pause
