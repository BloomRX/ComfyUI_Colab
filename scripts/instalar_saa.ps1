<#
.SYNOPSIS
    Instala o Character Select SAA com as configuracoes do WAIFU SURVIVORS.

.DESCRIPTION
    Versao PowerShell nativa (nao precisa de WSL nem Git Bash).
    Clona o repo do SAA, aplica nosso settings.json e roda npm install.
    Reexecutar e seguro: se ja existir, atualiza em vez de clonar.

.PARAMETER Destino
    Onde instalar. Padrao: character_select_saa DENTRO deste repo
    (a pasta esta no .gitignore, entao nao suja o versionamento).

.EXAMPLE
    .\scripts\instalar_saa.ps1

.EXAMPLE
    .\scripts\instalar_saa.ps1 -Destino "D:\outro\lugar"
#>

param(
    [string]$Destino = ""
)

$ErrorActionPreference = 'Stop'

$Repo = 'https://github.com/mirabarukaso/character_select_stand_alone_app.git'
$Aqui = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($Destino)) {
    # DENTRO do repo, nao ao lado dele. O .gitignore ja exclui esta pasta.
    $Destino = Join-Path $Aqui 'character_select_saa'
}

Write-Host ''
Write-Host '==============================================================' -ForegroundColor Cyan
Write-Host '  Character Select SAA - instalacao com config do projeto' -ForegroundColor Cyan
Write-Host '==============================================================' -ForegroundColor Cyan
Write-Host "  destino: $Destino"
Write-Host ''

# ------------------------------------------------------- pre-requisitos
foreach ($cmd in @('git', 'node', 'npm')) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        Write-Host "ERRO: '$cmd' nao encontrado no PATH." -ForegroundColor Red
        switch ($cmd) {
            'git'  { Write-Host '  Instale o Git: https://git-scm.com/download/win' }
            'node' { Write-Host '  Instale o Node.js LTS: https://nodejs.org' }
            'npm'  { Write-Host '  O npm vem junto com o Node.js: https://nodejs.org' }
        }
        Write-Host '  Feche e reabra o PowerShell depois de instalar.'
        exit 1
    }
}
Write-Host "  node $(node --version)  |  npm v$(npm --version)"
Write-Host ''

# --------------------------------------------------------------- clone
if (Test-Path (Join-Path $Destino '.git')) {
    Write-Host '-> ja existe, atualizando...' -ForegroundColor Yellow
    git -C $Destino fetch --quiet
    git -C $Destino pull --quiet
} else {
    Write-Host '-> clonando...' -ForegroundColor Yellow
    git clone --quiet $Repo $Destino
}

# ------------------------------------------------------------ settings
Write-Host '-> aplicando settings do projeto' -ForegroundColor Yellow

$PastaSet = Join-Path $Destino 'settings'
New-Item -ItemType Directory -Force -Path $PastaSet | Out-Null
$Alvo = Join-Path $PastaSet 'settings.json'

if (Test-Path $Alvo) {
    $bk = "$Alvo.bak.$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item $Alvo $bk
    Write-Host "   (settings anterior salvo em $(Split-Path -Leaf $bk))"
}

$Nosso = Get-Content (Join-Path $Aqui 'saa\settings.json') -Raw | ConvertFrom-Json

# monta a saida preservando o que ja existia
$saida = [ordered]@{}
$antigo = $null          # declarado sempre: senao a checagem de favoritos
                         # quebraria com Set-StrictMode quando nao ha arquivo
if (Test-Path $Alvo) {
    try {
        $antigo = Get-Content $Alvo -Raw | ConvertFrom-Json
        foreach ($p in $antigo.PSObject.Properties) { $saida[$p.Name] = $p.Value }
    } catch {
        Write-Host '   (settings anterior ilegivel, comecando do zero)' -ForegroundColor DarkYellow
    }
}
# aplica o nosso por cima, menos o bloco de comentario
foreach ($p in $Nosso.PSObject.Properties) {
    if ($p.Name -ne '_comentario') { $saida[$p.Name] = $p.Value }
}
# favoritos do usuario nunca se perdem
if ($antigo -and $antigo.fav_characters -and $antigo.fav_characters.Count -gt 0) {
    $saida['fav_characters'] = $antigo.fav_characters
    Write-Host "   favoritos preservados: $($antigo.fav_characters.Count)"
}

$saida | ConvertTo-Json -Depth 10 | Set-Content $Alvo -Encoding UTF8
Write-Host "   settings.json escrito ($($saida.Count) chaves)"

# ---------------------------------------------------------------- deps
Write-Host '-> npm install (pode demorar alguns minutos)' -ForegroundColor Yellow
Push-Location $Destino
try {
    npm install --silent
} finally {
    Pop-Location
}

# --------------------------------------------------------------- pronto
Write-Host ''
Write-Host '==============================================================' -ForegroundColor Green
Write-Host '  PRONTO' -ForegroundColor Green
Write-Host '==============================================================' -ForegroundColor Green
Write-Host ''
Write-Host '  1. No Colab, na Celula 6, marque  TUNEL_TCP = True  e rode.'
Write-Host '     O log vai imprimir algo como:'
Write-Host ''
Write-Host '        API Address = 0.tcp.sa.ngrok.io:14523' -ForegroundColor Cyan
Write-Host ''
Write-Host '  2. Inicie o app:'
Write-Host ''
Write-Host "        cd `"$Destino`"" -ForegroundColor Cyan
Write-Host '        npm start' -ForegroundColor Cyan
Write-Host ''
Write-Host '  3. No SAA:  Settings -> API Interface = ComfyUI'
Write-Host '              API Address = (o endereco do passo 1, SEM http://)'
Write-Host ''
Write-Host '  O endereco MUDA a cada sessao do Colab. So o campo API Address'
Write-Host '  precisa ser reajustado; o resto fica salvo.'
Write-Host ''
Write-Host '  Modelo ja configurado: waiIllustriousSDXL_v170.safetensors'
Write-Host '  Negative do projeto ja aplicado.'
Write-Host ''
Write-Host '  Exige o custom node ComfyUI_Mira no ComfyUI (ja no registry).'
Write-Host '=============================================================='
Write-Host ''
