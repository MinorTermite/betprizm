# ============================================================
#  PRIZMBET — Автозапуск Telegram-бота через Task Scheduler
#  Запускать от имени Администратора!
#  Выполнить: powershell -ExecutionPolicy Bypass -File setup_bot_autostart.ps1
# ============================================================

$TaskName  = "PRIZMBET_TelegramBot"
$BotScript = Join-Path $PSScriptRoot "telegram_bot.py"
$Python    = "C:\Python312\python.exe"
$LogFile   = Join-Path $PSScriptRoot "bot_autostart.log"

# Проверяем Python
if (-not (Test-Path $Python)) {
    Write-Host "[ERROR] Python не найден: $Python" -ForegroundColor Red
    Write-Host "Укажи путь вручную в переменной `$Python" -ForegroundColor Yellow
    pause
    exit 1
}

# Проверяем скрипт бота
if (-not (Test-Path $BotScript)) {
    Write-Host "[ERROR] Не найден telegram_bot.py: $BotScript" -ForegroundColor Red
    pause
    exit 1
}

# Удаляем старое задание если есть
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "[OK] Старое задание удалено" -ForegroundColor Yellow
}

# Действие: запуск Python с ботом
$Action = New-ScheduledTaskAction `
    -Execute $Python `
    -Argument "`"$BotScript`"" `
    -WorkingDirectory $PSScriptRoot

# Триггер: при загрузке Windows (через 30 сек задержка)
$Trigger = New-ScheduledTaskTrigger -AtStartup

# Настройки запуска
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 2) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Принципал — текущий пользователь
$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Highest

# Создаём задание
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "PRIZMBET Telegram Bot — автозапуск при входе в Windows" `
    -Force | Out-Null

# Добавляем задержку 30 сек через wrapper (чтобы сеть успела подняться)
$Task = Get-ScheduledTask -TaskName $TaskName
$Task.Triggers[0].Delay = "PT30S"
$Task | Set-ScheduledTask | Out-Null

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PRIZMBET TelegramBot — Автозапуск настроен!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Задание: $TaskName" -ForegroundColor White
Write-Host "  Скрипт:  $BotScript" -ForegroundColor White
Write-Host "  Python:  $Python" -ForegroundColor White
Write-Host "  Запуск:  При загрузке Windows (задержка 30 сек)" -ForegroundColor White
Write-Host "  Рестарт: 5 попыток с интервалом 2 мин при сбое" -ForegroundColor White
Write-Host ""
Write-Host "[INFO] Бот стартует автоматически при каждом включении ПК" -ForegroundColor Green
Write-Host "[INFO] Управление: Task Scheduler -> PRIZMBET_TelegramBot" -ForegroundColor Gray
Write-Host ""

# Спрашиваем запустить ли сейчас
$answer = Read-Host "Запустить бота прямо сейчас? (y/n)"
if ($answer -eq 'y' -or $answer -eq 'Y' -or $answer -eq 'д' -or $answer -eq 'Д') {
    Write-Host "Запускаю бота..." -ForegroundColor Yellow
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 3
    $state = (Get-ScheduledTask -TaskName $TaskName).State
    Write-Host "Состояние задания: $state" -ForegroundColor Cyan
}

pause
