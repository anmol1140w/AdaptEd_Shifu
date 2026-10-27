$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Test-Path '.env')) {
    $appBytes = [byte[]]::new(32)
    $databaseBytes = [byte[]]::new(32)
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($appBytes)
    $rng.GetBytes($databaseBytes)
    $rng.Dispose()
    $appSecret = [BitConverter]::ToString($appBytes).Replace('-', '')
    $databaseSecret = [BitConverter]::ToString($databaseBytes).Replace('-', '')
    $contents = Get-Content '.env.example'
    $contents = $contents -replace '^POSTGRES_PASSWORD=.*$', "POSTGRES_PASSWORD=$databaseSecret"
    $contents = $contents -replace '^ADAPTED_SECRET_KEY=.*$', "ADAPTED_SECRET_KEY=$appSecret"
    $utf8WithoutBom = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false
    [System.IO.File]::WriteAllLines((Join-Path $repoRoot '.env'), [string[]]$contents, $utf8WithoutBom)
    Write-Host 'Created .env with machine-local secrets. Keep it private.'
}

docker compose up --build -d
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose failed to start AdaptEd.' }
$webPort = '5173'
$match = Select-String -Path '.env' -Pattern '^ADAPTED_WEB_PORT=(\d+)$' | Select-Object -First 1
if ($match) { $webPort = $match.Matches[0].Groups[1].Value }
Write-Host "AdaptEd is starting. Open http://localhost:$webPort"
