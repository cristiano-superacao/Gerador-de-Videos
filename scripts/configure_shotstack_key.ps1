$ErrorActionPreference = 'Stop'

Set-Location (Join-Path $PSScriptRoot '..')

$secureKey = Read-Host 'Cole a SHOTSTACK_API_KEY' -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)

try {
    $shotstackKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)

    if (-not $shotstackKey -or -not $shotstackKey.Trim()) {
        throw 'SHOTSTACK_API_KEY vazia.'
    }

    $shotstackKey | railway variable set -s api SHOTSTACK_API_KEY --stdin
    railway redeploy -s api -y
    railway variable list -s api -k | Select-String '^SHOTSTACK_API_KEY='

    Write-Output 'configure-shotstack-key:ok'
}
finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}