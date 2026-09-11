<#
.SYNOPSIS
    Cria uma pasta espelho com arquivos vazios, para o SAA listar os modelos.

.DESCRIPTION
    O Character Select SAA monta as listas suspensas lendo o DISCO LOCAL
    (scripts/main/modelList.js -> fs.readdirSync). Como o nosso ComfyUI roda
    no Colab, essas pastas nao existem no PC e os dropdowns ficam vazios.

    O readDirectory do SAA so olha NOME e EXTENSAO — nunca abre o arquivo.
    Entao arquivos de 0 byte com o nome certo resolvem: o dropdown lista, voce
    seleciona, e o SAA manda a string para o ComfyUI, que resolve o arquivo
    de verdade do lado dele.

    Os nomes sao lidos de config/node_registry.json, entao acompanham o
    projeto automaticamente.

.EXAMPLE
    .\scripts\espelho_modelos.ps1

.EXAMPLE
    .\scripts\espelho_modelos.ps1 -Destino "D:\meu_espelho"
#>

param(
    [string]$Destino = ""
)

$ErrorActionPreference = 'Stop'

$Aqui = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($Destino)) {
    $Destino = Join-Path $Aqui 'model_mirror'
}

Write-Host ''
Write-Host '==============================================================' -ForegroundColor Cyan
Write-Host '  Espelho de modelos para o Character Select SAA' -ForegroundColor Cyan
Write-Host '==============================================================' -ForegroundColor Cyan
Write-Host "  destino: $Destino"
Write-Host ''

# ------------------------------------------------- le os modelos do registry
$regPath = Join-Path $Aqui 'config\node_registry.json'
if (-not (Test-Path $regPath)) {
    Write-Host "ERRO: nao achei $regPath" -ForegroundColor Red
    exit 1
}
$reg = Get-Content $regPath -Raw | ConvertFrom-Json

# dir do registry -> subpasta que o SAA espera (relativa a models/)
$mapa = @{
    'checkpoints'        = 'checkpoints'
    'loras'              = 'loras'
    'controlnet'         = 'controlnet'
    'clip_vision'        = 'clip_vision'
    'ipadapter'          = 'ipadapter'
    'upscale_models'     = 'upscale_models'
    'vae'                = 'vae'
    'animatediff_models' = 'animatediff_models'
    'diffusion_models'   = 'diffusion_models'
    'text_encoders'      = 'text_encoders'
}

# So os workflows ATIVOS (Workflows/), nao os arquivados. Espelhar modelo
# que voce apagou do Drive so polui o dropdown com opcoes que dao erro.
$ativos = @{}
Get-ChildItem -Path (Join-Path $Aqui 'Workflows') -Filter '*.json' -ErrorAction SilentlyContinue |
    ForEach-Object { $ativos[$_.Name] = $true }

$itens = @{}
foreach ($wf in $reg.workflow_models.PSObject.Properties) {
    if (-not $ativos.ContainsKey($wf.Name)) { continue }
    foreach ($m in $wf.Value) {
        if ($m.dir -and $m.file -and $mapa.ContainsKey($m.dir)) {
            $itens["$($m.dir)|$($m.file)"] = $true
        }
    }
}

# o checkpoint principal nao esta em workflow_models (download manual, Civitai)
$itens['checkpoints|waiIllustriousSDXL_v170.safetensors'] = $true

if ($itens.Count -eq 0) {
    Write-Host 'Nenhum modelo encontrado no registry.' -ForegroundColor Yellow
    exit 0
}

# --------------------------------------------------------------- cria tudo
$criados = 0
$existiam = 0
foreach ($chave in ($itens.Keys | Sort-Object)) {
    $parte = $chave -split '\|', 2
    $sub = $mapa[$parte[0]]
    $nome = $parte[1]

    $pasta = Join-Path $Destino $sub
    New-Item -ItemType Directory -Force -Path $pasta | Out-Null

    $arq = Join-Path $pasta $nome
    if (Test-Path $arq) {
        $existiam++
    } else {
        New-Item -ItemType File -Path $arq | Out-Null
        $criados++
        Write-Host "  + $sub\$nome" -ForegroundColor DarkGray
    }
}

Write-Host ''
Write-Host "  $criados criado(s), $existiam ja existia(m)"
Write-Host ''
Write-Host '==============================================================' -ForegroundColor Green
Write-Host '  PRONTO' -ForegroundColor Green
Write-Host '==============================================================' -ForegroundColor Green
Write-Host ''
Write-Host '  No SAA, quando pedir o caminho dos Checkpoints, cole:'
Write-Host ''
Write-Host "     $(Join-Path $Destino 'checkpoints')" -ForegroundColor Cyan
Write-Host ''
Write-Host '  Sao arquivos de 0 byte: servem so para o SAA montar as listas.'
Write-Host '  O ComfyUI do Colab e quem carrega os modelos de verdade.'
Write-Host ''
Write-Host '  Rode de novo depois de adicionar modelos ao registry.'
Write-Host '=============================================================='
Write-Host ''
