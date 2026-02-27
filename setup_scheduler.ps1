# ============================================================
# PRIZMBET - Настройка автоматического обновления
# Запускать от имени Администратора!
# ============================================================

$TaskName   = "PRIZMBET_AutoUpdate"
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$BatFile    = Join-Path $ScriptPath "auto_update.bat"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PRIZMBET - Установка планировщика задач" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Скрипт: $BatFile"
Write-Host ""

# Удаляем старую задачу если есть
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "[INFO] Старая задача удалена" -ForegroundColor Yellow
}

# Действие: запуск bat-файла
$Action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$BatFile`"" `
    -WorkingDirectory $ScriptPath

# Триггер: каждые 30 минут, начиная с текущего момента
$Trigger = New-ScheduledTaskTrigger `
    -RepetitionInterval (New-TimeSpan -Minutes 30) `
    -Once `
    -At (Get-Date)

# Настройки: запускать только если ПК не на батарее, не будить из сна
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -DontStopIfGoingOnBatteries `
    -WakeToRun:$false

# Регистрируем задачу (от текущего пользователя)
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -RunLevel Highest `
    -Force | Out-Null

Write-Host ""
Write-Host "[OK] Задача '$TaskName' создана!" -ForegroundColor Green
Write-Host "     Запуск каждые 30 минут" -ForegroundColor Green
Write-Host "     Лог: $ScriptPath\auto_update.log" -ForegroundColor Green
Write-Host ""
Write-Host "Управление задачей:" -ForegroundColor Cyan
Write-Host "  Запустить сейчас : Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Остановить       : Stop-ScheduledTask  -TaskName '$TaskName'"
Write-Host "  Удалить          : Unregister-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Статус           : Get-ScheduledTask   -TaskName '$TaskName'"
Write-Host ""

# Запускаем первый раз сразу
$answer = Read-Host "Запустить прямо сейчас? (y/n)"
if ($answer -eq "y") {
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "[OK] Задача запущена!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Нажмите Enter для выхода..."
Read-Host
