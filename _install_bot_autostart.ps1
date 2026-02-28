$Python    = "C:\Python312\python.exe"
$BotScript = "C:\Users\GravMix\Desktop\suite full stake QWEN\prizmbet-final\telegram_bot.py"
$RegKey    = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$RegName   = "PRIZMBET_TelegramBot"
$VbsPath   = "C:\Users\GravMix\Desktop\suite full stake QWEN\prizmbet-final\start_bot_hidden.vbs"

$VbsContent = "Set WshShell = CreateObject(""WScript.Shell"")" + [Environment]::NewLine
$VbsContent += "WshShell.Run chr(34) & """ + $Python + """ & chr(34) & "" "" & chr(34) & """ + $BotScript + """ & chr(34), 0, False"

Set-Content -Path $VbsPath -Value $VbsContent -Encoding ASCII
Write-Host "VBS created: $VbsPath"

$RunValue = "wscript.exe `"$VbsPath`""
Set-ItemProperty -Path $RegKey -Name $RegName -Value $RunValue
Write-Host "Registry key added: $RegName"
Write-Host "Value: $RunValue"
Write-Host "Bot will autostart on Windows login!"
