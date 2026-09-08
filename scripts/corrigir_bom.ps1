<#
.SYNOPSIS
    Remove o BOM do settings.json do Character Select SAA.

.DESCRIPTION
    O Windows PowerShell 5.x grava um BOM (EF BB BF) quando se usa
    `Set-Content -Encoding UTF8`. O JSON.parse do Node rejeita:

        SyntaxError: Unexpected token '<U+FEFF>', "<U+FEFF>{ ..." is not valid JSON

    Este script reescreve o arquivo sem BOM. Nao altera o conteudo.

.EXAMPLE
    .\scripts\corrigir_bom.ps1
#>

param(
    [string]$Arquivo = ""
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Arquivo)) {
    $repo = Split-Path -Parent $PSScriptRoot
    $Arquivo = Join-Path $repo 'character_select_saa\settings\settings.json'
}

if (-not (Test-Path $Arquivo)) {
    Write-Host "Nao encontrei: $Arquivo" -ForegroundColor Red
    Write-Host 'Passe o caminho:  .\scripts\corrigir_bom.ps1 -Arquivo "C:\...\settings.json"'
    exit 1
}

Write-Host ''
Write-Host "Arquivo: $Arquivo"

$bytes = [System.IO.File]::ReadAllBytes($Arquivo)
$temBom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)

if (-not $temBom) {
    Write-Host 'Nao ha BOM neste arquivo. Nada a fazer.' -ForegroundColor Green
    # ainda assim valida o JSON
    try {
        Get-Content $Arquivo -Raw | ConvertFrom-Json | Out-Null
        Write-Host 'JSON valido.' -ForegroundColor Green
    } catch {
        Write-Host "JSON INVALIDO: $($_.Exception.Message)" -ForegroundColor Red
    }
    exit 0
}

Write-Host 'BOM encontrado. Removendo...' -ForegroundColor Yellow

# le o texto ja sem o BOM (o .NET remove ao decodificar) e regrava
$texto = [System.IO.File]::ReadAllText($Arquivo)
$semBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($Arquivo, $texto, $semBom)

# confere
$b2 = [System.IO.File]::ReadAllBytes($Arquivo)
$aindaTem = ($b2.Length -ge 3 -and $b2[0] -eq 0xEF -and $b2[1] -eq 0xBB -and $b2[2] -eq 0xBF)

if ($aindaTem) {
    Write-Host 'FALHOU: o BOM continua la.' -ForegroundColor Red
    exit 1
}

try {
    Get-Content $Arquivo -Raw | ConvertFrom-Json | Out-Null
    Write-Host 'Pronto. BOM removido e JSON valido.' -ForegroundColor Green
    Write-Host ''
    Write-Host 'Agora rode:  npm start'
} catch {
    Write-Host "BOM removido, mas o JSON tem outro problema:" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)"
    exit 1
}
Write-Host ''
