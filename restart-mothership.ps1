# restart-mothership.ps1
# Automatically bumps the version in the compose project name and restarts the stack.

$composePath = "$PSScriptRoot\.devcontainer\docker-compose.yml"
$envPath = "$PSScriptRoot\.env"

# Load .env file into the current process environment so docker compose can read it
if (Test-Path $envPath) {
    Get-Content $envPath | Where-Object { $_ -match '^\s*[^#]' } | ForEach-Object {
        $key, $value = $_ -split '=', 2
        [System.Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim(), 'Process')
    }
} else {
    Write-Warning ".env file not found at $envPath — copy .env.example and fill in values."
}

$content = Get-Content $composePath -Raw

# Extract current version number
if ($content -match 'name: lms-mothership-v(\d+)') {
    $currentVersion = [int]$Matches[1]
    $nextVersion = $currentVersion + 1
} else {
    Write-Error "Could not find version in docker-compose.yml"
    exit 1
}

$oldName = "lms-mothership-v$currentVersion"
$newName = "lms-mothership-v$nextVersion"

Write-Host "`n🚀 Bumping $oldName → $newName`n" -ForegroundColor Cyan

# Tear down the old stack
Write-Host "⬇  Stopping $oldName..." -ForegroundColor Yellow
docker compose -f $composePath down

# Write new version into docker-compose.yml
$content = $content -replace "name: $oldName", "name: $newName"
Set-Content $composePath $content -NoNewline

# Bring up the new stack
Write-Host "`n⬆  Starting $newName..." -ForegroundColor Green
docker compose -f $composePath up -d

Write-Host "`n✅ Mothership is live at $newName`n" -ForegroundColor Green
docker ps --filter "name=$newName" --format "table {{.Names}}`t{{.Status}}"
