Set-Location "$PSScriptRoot\.."

$postgresVars = railway variable list -s Postgres -k | Out-String
$apiVars = railway variable list -s api -k | Out-String

$databaseUrlMatch = [regex]::Match(
    $postgresVars,
    'DATABASE_PUBLIC_URL=([^\r\n]+)'
)
$publicDomainMatch = [regex]::Match(
    $apiVars,
    'RAILWAY_PUBLIC_DOMAIN=([^\r\n]+)'
)

if (-not $databaseUrlMatch.Success) {
    throw 'Nao foi possivel localizar DATABASE_PUBLIC_URL do servico Postgres no Railway.'
}

if (-not $publicDomainMatch.Success) {
    throw 'Nao foi possivel localizar RAILWAY_PUBLIC_DOMAIN do servico api no Railway.'
}

$env:DATABASE_URL = $databaseUrlMatch.Groups[1].Value.Trim()
$env:APP_BASE_URL = "https://$($publicDomainMatch.Groups[1].Value.Trim())"

Write-Output 'Executando seed remoto via DATABASE_PUBLIC_URL...'
python scripts/seed.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Output 'Executando client smoke contra a URL publica...'
python scripts/client_smoke_test.py
exit $LASTEXITCODE