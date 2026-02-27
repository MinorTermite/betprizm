@echo off
chcp 65001 >nul

:: Путь к папке скрипта
cd /d "%~dp0"

:: Лог-файл
set LOG=%~dp0auto_update.log
set DT=%DATE% %TIME:~0,8%

echo [%DT%] === Запуск авто-обновления === >> "%LOG%"

:: Проверяем есть ли Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [%DT%] ОШИБКА: Python не найден >> "%LOG%"
    exit /b 1
)

:: Запускаем парсер
echo [%DT%] Запускаем парсер... >> "%LOG%"
python marathon_parser_real.py >> "%LOG%" 2>&1

if %errorlevel% neq 0 (
    echo [%DT%] ОШИБКА: Парсер завершился с ошибкой >> "%LOG%"
    exit /b 1
)

echo [%DT%] Парсер завершён успешно >> "%LOG%"

:: Git push
git add matches.json >> "%LOG%" 2>&1
git commit -m "auto: matches %DATE% %TIME:~0,5%" >> "%LOG%" 2>&1

git -c credential.helper=manager push origin main >> "%LOG%" 2>&1

if %errorlevel% equ 0 (
    echo [%DT%] OK: Запушено на GitHub >> "%LOG%"
) else (
    echo [%DT%] ОШИБКА: Git push не удался >> "%LOG%"
)

:: Обрезаем лог до 500 строк чтобы не раздувался
powershell -Command "if ((Get-Content '%LOG%').Count -gt 500) { Get-Content '%LOG%' | Select-Object -Last 500 | Set-Content '%LOG%' }"

exit /b 0
