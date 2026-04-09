$ErrorActionPreference = 'Stop'

Set-Location (Join-Path $PSScriptRoot '..')

$envPath = Join-Path (Get-Location) '.env'
$examplePath = Join-Path (Get-Location) '.env.example'

if (-not (Test-Path $envPath)) {
    if (-not (Test-Path $examplePath)) {
        throw '.env.example não encontrado.'
    }

    Copy-Item $examplePath $envPath
}

$secureKey = Read-Host 'Cole a SHOTSTACK_API_KEY para habilitar o fallback local' -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)

function Set-Or-AddEnvValue {
    param(
        [string]$Path,
        [string]$Name,
        [string]$Value
    )

    $content = Get-Content $Path -Raw
    $escapedName = [Regex]::Escape($Name)
    if ($content -match "(?m)^$escapedName=") {
        $content = [Regex]::Replace(
            $content,
            "(?m)^$escapedName=.*$",
            "$Name=$Value"
        )
    }
    else {
        if (-not $content.EndsWith("`n")) {
            $content += "`r`n"
        }

        $content += "$Name=$Value`r`n"
    }

    Set-Content -Path $Path -Value $content -Encoding utf8
}

try {
    $shotstackKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)

    if (-not $shotstackKey -or -not $shotstackKey.Trim()) {
        throw 'SHOTSTACK_API_KEY vazia.'
    }

    Set-Or-AddEnvValue -Path $envPath -Name 'SHOTSTACK_API_KEY' -Value $shotstackKey.Trim()

    Write-Output 'configure-shotstack-fallback:ok'
    Write-Output 'Próximo passo: powershell -ExecutionPolicy Bypass -File .\scripts\run_external_smoke.ps1'
}
finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}