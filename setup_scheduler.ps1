param(
    [ValidateSet("Geral", "Agentes", "All")]
    [string]$Type = "All"
)

$pythonPath = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) { $pythonPath = "python.exe" }
$scriptPath = Join-Path (Get-Location) "main.py"
$workDir = Get-Location

# Configurações avançadas: Acordar o PC, rodar se estiver na bateria, e iniciar assim que possível se perder o horário
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

if ($Type -eq "Geral" -or $Type -eq "All") {
    $actionGeral = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptPath`" --type geral" -WorkingDirectory "$workDir"
    $triggerGeral1 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 10:00PM
    $triggerGeral2 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 11:00PM
    $triggersGeral = @($triggerGeral1, $triggerGeral2)
    Register-ScheduledTask -TaskName "BoletimIANews" -Action $actionGeral -Trigger $triggersGeral -Settings $settings -Principal $principal -Description "Automação Semanal de Notícias de IA e Jurídico" -Force
    Write-Host "Tarefa 'BoletimIANews' (Geral) configurada com sucesso!"
}

if ($Type -eq "Agentes" -or $Type -eq "All") {
    $actionAgentes = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptPath`" --type agentes" -WorkingDirectory "$workDir"
    $triggerAgentes = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 08:00AM
    Register-ScheduledTask -TaskName "BoletimIAAgentes" -Action $actionAgentes -Trigger $triggerAgentes -Settings $settings -Principal $principal -Description "Automação Semanal de Papers e Inovações com Agentes de IA" -Force
    Write-Host "Tarefa 'BoletimIAAgentes' (Agentes de IA) configurada com sucesso!"
}

Write-Host "---"
Write-Host "Configurações aplicadas com privilégios máximos e WakeToRun ativados."
Write-Host "---"

