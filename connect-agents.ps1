# PowerShell helper script to connect all local agents on Windows to Remote Context Store
param (
    [string]$Url = "http://localhost:8000/sse",
    [string]$Token = "",
    [switch]$ScanOnly
)

$PSScriptRoot = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
Set-Location $PSScriptRoot

if (-not $Token -and -not $ScanOnly) {
    if ($env:AUTH_TOKEN) {
        $Token = $env:AUTH_TOKEN
    } elseif (Test-Path ".env") {
        $envMatch = Get-Content ".env" | Select-String "^AUTH_TOKEN=(.+)$"
        if ($envMatch) {
            $Token = $envMatch.Matches[0].Groups[1].Value.Trim()
        }
    }
}

if ($ScanOnly) {
    python -m src.scanner --scan-only
} else {
    if (-not $Token) {
        Write-Host "Warning: No token specified. Provide via -Token, .env, or `$env:AUTH_TOKEN" -ForegroundColor Yellow
    }
    python -m src.scanner --url $Url --token $Token
}
