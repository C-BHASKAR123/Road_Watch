# Keeps RoadWatch available for long-term use.
# - Restarts the Flask site if port 5000 stops listening.
# - Turns the RoadWatch hotspot back on if Windows switches it off.
# Runs hidden and checks every 20 seconds.

$ErrorActionPreference = "Continue"
$project = $PSScriptRoot
$logPath = Join-Path $project "watchdog.log"

function Write-WatchdogLog {
    param([string]$Message)
    try {
        if ((Test-Path $logPath) -and ((Get-Item $logPath).Length -gt 1MB)) {
            Move-Item -LiteralPath $logPath -Destination ($logPath + ".old") -Force
        }
        Add-Content -LiteralPath $logPath -Value ("{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message)
    } catch {
        # Logging must never stop the watchdog.
    }
}

function Test-RoadWatchPort {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $result = $client.BeginConnect("127.0.0.1", 5000, $null, $null)
        if (-not $result.AsyncWaitHandle.WaitOne(1200)) {
            return $false
        }
        $client.EndConnect($result)
        return $true
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

# Only one watchdog may run.
$mutex = New-Object System.Threading.Mutex($false, "Global\RoadWatchLongRunWatchdog")
if (-not $mutex.WaitOne(0)) {
    exit 0
}

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Networking.Connectivity.NetworkInformation, Windows.Networking.Connectivity, ContentType = WindowsRuntime]
$null = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager, Windows.Networking.NetworkOperators, ContentType = WindowsRuntime]

$methods = [System.WindowsRuntimeSystemExtensions].GetMethods()
$asTaskGeneric = ($methods | Where-Object {
    $_.Name -eq 'AsTask' -and
    $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]
$asTaskAction = ($methods | Where-Object {
    $_.Name -eq 'AsTask' -and
    $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'
})[0]

function Await-Result($operation, $resultType) {
    $task = $asTaskGeneric.MakeGenericMethod($resultType).Invoke($null, @($operation))
    $task.Wait(-1) | Out-Null
    return $task.Result
}

function Await-Action($operation) {
    $task = $asTaskAction.Invoke($null, @($operation))
    $task.Wait(-1) | Out-Null
}

$onState = [Windows.Networking.NetworkOperators.TetheringOperationalState]::On
$resultType = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult]

while ($true) {
    # 1. Keep the website listening on port 5000.
    if (-not (Test-RoadWatchPort)) {
        Write-WatchdogLog "Port 5000 is down. Starting the RoadWatch server."
        $serverCommand = 'set "HOST=0.0.0.0"&& set "PORT=5000"&& ".venv\Scripts\python.exe" app.py >> server.log 2>&1'
        Start-Process -FilePath "cmd.exe" -ArgumentList '/c', $serverCommand -WorkingDirectory $project -WindowStyle Hidden
        Start-Sleep -Seconds 4
    }

    # 2. Keep the RoadWatch hotspot available.
    try {
        $profile = [Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile()
        if ($profile) {
            $manager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::CreateFromConnectionProfile($profile)
            if ($manager -and $manager.TetheringOperationalState -ne $onState) {
                $config = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringAccessPointConfiguration]::new()
                $config.Ssid = "RoadWatch"
                $config.Passphrase = "RoadWatch@2026"
                Await-Action $manager.ConfigureAccessPointAsync($config)
                $result = Await-Result $manager.StartTetheringAsync() $resultType
                Write-WatchdogLog ("Hotspot start: " + $result.Status)
            }
        }
    } catch {
        Write-WatchdogLog ("Hotspot error: " + $_.Exception.Message)
    }

    Start-Sleep -Seconds 20
}
