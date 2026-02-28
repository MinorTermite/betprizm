# ============================================================
# PRIZMBET - Автообновление матчей каждое утро в 09:00
# Запускать от имени Администратора!
# ============================================================

$TaskName   = "PRIZMBET_AutoUpdate"
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$BatFile    = Join-Path $ScriptPath "auto_update.bat"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  PRIZMBET - Установка планировщика задач (ежедневно 09:00)" -ForegroundColor Cyan
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

# Триггер: ежедневно в 09:00
$Trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At "09:00"

# Настройки: StartWhenAvailable — если ПК был выключен в 09:00, запустить при следующем включении
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
Write-Host "     Запуск: ежедневно в 09:00" -ForegroundColor Green
Write-Host "     StartWhenAvailable: запустится при включении ПК если пропустил 09:00" -ForegroundColor Green
Write-Host "     Лог: $ScriptPath\auto_update.log" -ForegroundColor Green
Write-Host ""
Write-Host "Управление задачей:" -ForegroundColor Cyan
Write-Host "  Запустить сейчас : Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Остановить       : Stop-ScheduledTask  -TaskName '$TaskName'"
Write-Host "  Удалить          : Unregister-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Статус           : Get-ScheduledTask   -TaskName '$TaskName'"
Write-Host ""

# Предлагаем зарегистрировать сейчас
$answer = Read-Host "Установить задачу в планировщик Windows прямо сейчас? (y/n)"
if ($answer -eq "y") {
    Write-Host "[OK] Задача установлена! Следующий запуск завтра в 09:00" -ForegroundColor Green
}

Write-Host ""
Write-Host "Нажмите Enter для выхода..."
Read-Host
