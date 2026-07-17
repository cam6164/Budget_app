param(
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"

function Get-ListenerProcessIds {
    param([int]$LocalPort)

    @(
        netstat -ano -p tcp |
            Select-String -Pattern ":$LocalPort\s+.*LISTENING\s+(\d+)$" |
            ForEach-Object {
                if ($_.Matches.Count) {
                    [int]$_.Matches[0].Groups[1].Value
                }
            } |
            Sort-Object -Unique
    )
}

$listenerIds = Get-ListenerProcessIds -LocalPort $Port
if (-not $listenerIds.Count) {
    exit 0
}

$processes = $null
try {
    $processes = @(Get-CimInstance Win32_Process -ErrorAction Stop)
} catch {
    Write-Host "Inspection detaillee indisponible, verification des processus Python."
}

if ($null -ne $processes) {
    $streamlitServers = @(
        $processes | Where-Object {
            $_.ProcessId -in $listenerIds -and
            $_.CommandLine -match "(?i)streamlit\s+run\s+app\.py"
        }
    )

    $foreignIds = @(
        $listenerIds | Where-Object { $_ -notin $streamlitServers.ProcessId }
    )
    if ($foreignIds.Count) {
        throw "Le port $Port est utilise par un autre programme (PID : $($foreignIds -join ', '))."
    }

    $targetIds = @($streamlitServers.ProcessId)
    foreach ($server in $streamlitServers) {
        $parent = $processes |
            Where-Object { $_.ProcessId -eq $server.ParentProcessId } |
            Select-Object -First 1
        if ($parent -and $parent.CommandLine -match "(?i)streamlit\s+run\s+app\.py") {
            $targetIds += $parent.ProcessId
        }
    }
} else {
    $listenerProcesses = @(
        $listenerIds | ForEach-Object { Get-Process -Id $_ -ErrorAction Stop }
    )
    $foreignIds = @(
        $listenerProcesses |
            Where-Object { $_.ProcessName -notmatch "(?i)^python(w)?$" } |
            Select-Object -ExpandProperty Id
    )
    if ($foreignIds.Count) {
        throw "Le port $Port est utilise par un autre programme (PID : $($foreignIds -join ', '))."
    }
    $targetIds = @($listenerIds)
}

$targetIds = @($targetIds | Sort-Object -Unique)
if ($targetIds.Count) {
    Stop-Process -Id $targetIds -Force
}

for ($tentative = 0; $tentative -lt 20; $tentative++) {
    if (-not (Get-ListenerProcessIds -LocalPort $Port).Count) {
        Write-Host "Ancienne instance Streamlit arretee."
        exit 0
    }
    Start-Sleep -Milliseconds 100
}

throw "L'ancienne instance Streamlit n'a pas libere le port $Port."
