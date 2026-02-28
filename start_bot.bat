@echo off
chcp 65001 >nul
title PRIZMBET - Telegram Bot
cd /d "%~dp0"

echo.
echo ============================================================
echo   PRIZMBET Telegram Bot
echo ============================================================
echo.
echo Бот запускается... Не закрывайте это окно!
echo Для остановки нажмите Ctrl+C
echo.

C:\Python312\python.exe telegram_bot.py

echo.
echo Бот остановлен. Нажмите любую клавишу...
pause >nul
