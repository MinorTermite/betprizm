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

:: Запускаем парсер
echo [%DT%] Running parser... >> "%LOG%"
"%PYTHON%" marathon_parser_real.py >> "%LOG%" 2>&1

if %errorlevel% neq 0 (
    echo [%DT%] ERROR: Parser failed >> "%LOG%"
    exit /b 1
)

echo [%DT%] Parser OK >> "%LOG%"

:: Git push через PowerShell (обходит проблему credential manager)
echo [%DT%] Pushing to GitHub... >> "%LOG%"
powershell.exe -NoProfile -NonInteractive -Command ^
    "Set-Location '%DIR%'; git add matches.json; git commit -m 'auto: %DT%'; git -c credential.helper=manager push origin main" >> "%LOG%" 2>&1

if %errorlevel% equ 0 (
    echo [%DT%] OK: Pushed to GitHub >> "%LOG%"
) else (
    echo [%DT%] WARNING: Push failed (will retry in 30 min) >> "%LOG%"
)

:: Обрезаем лог до 300 строк
powershell.exe -NoProfile -NonInteractive -Command ^
    "if ((Get-Content '%LOG%').Count -gt 300) { Get-Content '%LOG%' | Select-Object -Last 300 | Set-Content '%LOG%' }"

echo [%DT%] === DONE === >> "%LOG%"
exit /b 0
