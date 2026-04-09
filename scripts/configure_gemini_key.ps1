$ErrorActionPreference = 'Stop'

Set-Location (Join-Path $PSScriptRoot '..')

$envFile = Join-Path (Get-Location) '.env'
$envExampleFile = Join-Path (Get-Location) '.env.example'

function Set-OrAppendEnvVar {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    $escapedValue = [Regex]::Escape($Value)
    $content = Get-Content $FilePath -Raw
    $pattern = "(?m)^$([Regex]::Escape($Name))=.*$"
    $replacement = "$Name=$Value"

    if ($content -match $pattern) {
        $updated = [Regex]::Replace($content, $pattern, $replacement)
    }
    else {
        $trimmed = $content.TrimEnd("`r", "`n")
        $updated = "$trimmed`r`n$replacement`r`n"
    }

    Set-Content -Path $FilePath -Value $updated -Encoding utf8
}

if (-not (Test-Path $envFile)) {
    if (-not (Test-Path $envExampleFile)) {
        throw '.env.example não encontrado.'
    }

    Copy-Item $envExampleFile $envFile
}

$secureKey = Read-Host 'Cole a GEMINI_API_KEY' -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)

try {
    $geminiKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)

    if (-not $geminiKey -or -not $geminiKey.Trim()) {
        throw 'GEMINI_API_KEY vazia.'
    }

    Set-OrAppendEnvVar -FilePath $envFile -Name 'VIDEO_PROVIDER' -Value 'veo'
    Set-OrAppendEnvVar -FilePath $envFile -Name 'GEMINI_API_KEY' -Value $geminiKey.Trim()
    Set-OrAppendEnvVar -FilePath $envFile -Name 'EXTERNAL_API_SMOKE_ALLOW_VEO_RENDER' -Value '1'

    Write-Output 'configure-gemini-key:ok'
    Write-Output 'provider:veo'
    Write-Output 'smoke:EXTERNAL_API_SMOKE_ALLOW_VEO_RENDER=1'
    Write-Output 'next:powershell -ExecutionPolicy Bypass -File .\scripts\run_external_smoke.ps1'
}
finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}