$TaskName  = "PRIZMBET_TelegramBot"
$BotScript = "C:\Users\GravMix\Desktop\suite full stake QWEN\prizmbet-final\telegram_bot.py"
$Python    = "C:\Python312\python.exe"
$WorkDir   = "C:\Users\GravMix\Desktop\suite full stake QWEN\prizmbet-final"

if (-not (Test-Path $Python)) { Write-Host "ERROR: Python not found" -ForegroundColor Red; exit 1 }

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Old task removed" -ForegroundColor Yellow
}

$Action    = New-ScheduledTaskAction -Execute $Python -Argument "`"$BotScript`"" -WorkingDirectory $WorkDir
$Trigger   = New-ScheduledTaskTrigger -AtStartup
$Settings  = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 2) -StartWhenAvailable -RunOnlyIfNetworkAvailable
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "PRIZMBET Telegram Bot autostart" -Force | Out-Null

$Task = Get-ScheduledTask -TaskName $TaskName
$Task.Triggers[0].Delay = "PT30S"
$Task | Set-ScheduledTask | Out-Null

Write-Host "SUCCESS: Task '$TaskName' created" -ForegroundColor Green
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName, State | Format-Table
