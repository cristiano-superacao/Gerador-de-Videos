$requiredKeys = @(
    'OPENAI_API_KEY',
    'SHOTSTACK_API_KEY',
    'SHOTSTACK_OWNER_ID'
)

$searchScopes = @('Process', 'User', 'Machine')
$missingKeys = @()

foreach ($key in $requiredKeys) {
    $value = $null

    foreach ($scope in $searchScopes) {
        $value = [Environment]::GetEnvironmentVariable($key, $scope)
        if ($value) {
            break
        }
    }

    if (-not $value) {
        $missingKeys += $key
    }
}

if (-not ([Environment]::GetEnvironmentVariable('TAVILY_API_KEY', 'Process')) -and
    -not ([Environment]::GetEnvironmentVariable('TAVILY_API_KEY', 'User')) -and
    -not ([Environment]::GetEnvironmentVariable('TAVILY_API_KEY', 'Machine')) -and
    -not ([Environment]::GetEnvironmentVariable('PERPLEXITY_API_KEY', 'Process')) -and
    -not ([Environment]::GetEnvironmentVariable('PERPLEXITY_API_KEY', 'User')) -and
    -not ([Environment]::GetEnvironmentVariable('PERPLEXITY_API_KEY', 'Machine'))) {
    $missingKeys += 'TAVILY_API_KEY ou PERPLEXITY_API_KEY'
}

if ($missingKeys.Count -gt 0) {
    Write-Output 'Credenciais ausentes para o smoke externo:'
    $missingKeys | ForEach-Object { Write-Output "- $_" }
    exit 1
}

$env:RUN_EXTERNAL_API_SMOKE = '1'

python scripts/external_api_smoke.py