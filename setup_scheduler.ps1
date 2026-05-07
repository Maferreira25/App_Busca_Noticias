$pythonPath = Join-Path (Get-Location) ".venv\Scripts\python.exe"
$scriptPath = Join-Path (Get-Location) "main.py"
$workDir = Get-Location

# Ação da tarefa
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptPath`"" -WorkingDirectory "$workDir"

# Triggers: Domingo às 22:00 e 23:00 (backup)
$trigger1 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 10:00PM
$trigger2 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 11:00PM
$triggers = @($trigger1, $trigger2)

# Configurações avançadas: Acordar o PC, rodar se estiver na bateria, e iniciar assim que possível se perder o horário
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun

# Principal: Rodar com privilégios máximos para garantir acesso ao Docker
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

# Registro da tarefa
Register-ScheduledTask -TaskName "Boletim_IAGenerativa_Semanal" -Action $action -Trigger $triggers -Settings $settings -Principal $principal -Description "Automação Semanal de Notícias de IA com ativação automática de Docker/Evolution API" -Force

Write-Host "---"
Write-Host "Tarefa 'Boletim_IAGenerativa_Semanal' atualizada com SUCESSO!"
Write-Host "Novas configurações aplicadas:"
Write-Host "1. O PC será acordado para rodar a tarefa (WakeToRun)."
Write-Host "2. Rodará com Privilégios Máximos (para gerenciar o Docker)."
Write-Host "3. Se o PC estiver desligado às 22h, ela rodará assim que ligar (StartWhenAvailable)."
Write-Host "---"
