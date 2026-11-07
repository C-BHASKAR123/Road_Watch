# Starts the RoadWatch Mobile Hotspot (SSID: RoadWatch).
# Safe to run repeatedly: it exits when the hotspot is already on.
$ErrorActionPreference = "Stop"

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

# Wait up to 90 seconds for the normal Wi-Fi to connect after sign-in.
$profile = $null
for ($attempt = 0; $attempt -lt 45; $attempt++) {
    $profile = [Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile()
    if ($profile) { break }
    Start-Sleep -Seconds 2
}

if (-not $profile) {
    Write-Output "No internet connection profile is available yet."
    exit 1
}

$manager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::CreateFromConnectionProfile($profile)
$onState = [Windows.Networking.NetworkOperators.TetheringOperationalState]::On
if ($manager.TetheringOperationalState -eq $onState) {
    Write-Output "RoadWatch hotspot is already on."
    exit 0
}

$config = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringAccessPointConfiguration]::new()
$config.Ssid = "RoadWatch"
$config.Passphrase = "RoadWatch@2026"
Await-Action $manager.ConfigureAccessPointAsync($config)

$resultType = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult]
$result = Await-Result $manager.StartTetheringAsync() $resultType
Write-Output ("RoadWatch hotspot start: " + $result.Status)
if ($result.AdditionalErrorMessage) {
    Write-Output $result.AdditionalErrorMessage
}
