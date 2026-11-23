# Starts local PostgreSQL (portable, in %USERPROFILE%\pgsql) and the game server.
# Usage: .\start.ps1   then open http://127.0.0.1:8000
$pg = "$env:USERPROFILE\pgsql"

& "$pg\bin\pg_ctl.exe" -D "$pg\data" status *> $null
if ($LASTEXITCODE -ne 0) {
    & "$pg\bin\pg_ctl.exe" -D "$pg\data" -l "$pg\postgres.log" -o "-p 5432 -c listen_addresses=localhost" start -w
}

Set-Location $PSScriptRoot
& "$PSScriptRoot\venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
