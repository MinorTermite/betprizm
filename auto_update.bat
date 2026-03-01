@echo off
chcp 65001 >nul

set PYTHON=C:\Python312\python.exe
set GIT=C:\Program Files\Git\bin\git.exe
set DIR=%~dp0
set LOG=%DIR%auto_update.log

cd /d "%DIR%"

:: Дата и время для лога
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set DT=%%I
set DT=%DT:~0,4%-%DT:~4,2%-%DT:~6,2% %DT:~8,2%:%DT:~10,2%

echo [%DT%] === START === >> "%LOG%"

:: Проверяем Python
if not exist "%PYTHON%" (
    echo [%DT%] ERROR: Python not found at %PYTHON% >> "%LOG%"
    exit /b 1
)

:: Запускаем основной парсер
echo [%DT%] Running marathon parser... >> "%LOG%"
"%PYTHON%" marathon_parser_real.py >> "%LOG%" 2>&1
if %errorlevel% neq 0 (
    echo [%DT%] ERROR: Marathon parser failed >> "%LOG%"
    exit /b 1
)
echo [%DT%] Marathon Parser OK >> "%LOG%"

:: Запускаем парсер ставок
echo [%DT%] Running bet parser... >> "%LOG%"
"%PYTHON%" bet_parser.py >> "%LOG%" 2>&1
if %errorlevel% neq 0 (
    echo [%DT%] ERROR: Bet parser failed >> "%LOG%"
    :: Выходим, чтобы не пушить битые или неполные данные
    exit /b 1 
)
echo [%DT%] Bets OK >> "%LOG%"

:: Git push — добавляем только matches.json и bets.json (игнорируем другие файлы)
echo [%DT%] Pushing to GitHub... >> "%LOG%"
powershell.exe -NoProfile -NonInteractive -Command ^
    "Set-Location '%DIR%'; & '%GIT%' add matches.json bets.json; if ((& '%GIT%' status --porcelain) -ne $null) { & '%GIT%' commit -m 'auto: %DT%' } else { Write-Host 'nothing to commit' }; & '%GIT%' push origin main" >> "%LOG%" 2>&1

if %errorlevel% equ 0 (
    echo [%DT%] OK: Pushed to GitHub >> "%LOG%"
) else (
    echo [%DT%] WARNING: Push failed (will retry next time) >> "%LOG%"
)

:: Оптимизированная обрезка лога до 300 строк
powershell.exe -NoProfile -NonInteractive -Command ^
    "$lines = Get-Content '%LOG%'; if ($lines.Count -gt 300) { $lines[-300..-1] | Set-Content '%LOG%' }"

echo [%DT%] === DONE === >> "%LOG%"
exit /b 0