Set-Location "$PSScriptRoot\.."

$apiVars = railway variable list -s api -k | Out-String
$publicDomainMatch = [regex]::Match(
    $apiVars,
    'RAILWAY_PUBLIC_DOMAIN=([^\r\n]+)'
)

if (-not $publicDomainMatch.Success) {
    throw 'Nao foi possivel localizar RAILWAY_PUBLIC_DOMAIN do servico api no Railway.'
}

$publicBaseUrl = "https://$($publicDomainMatch.Groups[1].Value.Trim())"

Write-Output 'Executando seed + smoke HTTP no Railway...'
powershell -ExecutionPolicy Bypass -File .\scripts\railway_seed_and_smoke.ps1
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$env:PLAYWRIGHT_BASE_URL = $publicBaseUrl

Write-Output 'Executando E2E desktop contra a URL publica...'
npm run test:e2e
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Output 'Executando E2E mobile contra a URL publica...'
npm run test:e2e:mobile
exit $LASTEXITCODE