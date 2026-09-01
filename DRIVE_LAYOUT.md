# O que fica no Drive e o que NÃO fica

## Regra geral

| Critério | Onde vive |
|---|---|
| Grande + demora pra baixar + não muda | **Drive** (modelos) |
| Você não pode perder | **Drive** (outputs, inputs) |
| Reproduzível com 1 comando em 1 min | **/content** (código, venv) |
| Versionável em texto | **Git** (workflows, registry) |

---

## ✅ FICA no Drive — `MyDrive/ComfyUI_Data/`

```
ComfyUI_Data/
├── models/            ← 95% do espaço. O que dói rebaixar.
│   ├── diffusion_models/   krea2, flux-2-klein-9b...
│   ├── text_encoders/      qwen3vl_4b, qwen_3_8b...
│   ├── vae/                qwen_image_vae, flux2-vae, wan_2.1_vae
│   ├── loras/              krea2_turbo_lora, Alb_LoRaV3, Detailer-KREA2
│   ├── skintoken/          grpo_1400.ckpt
│   ├── trellis2/           pesos do TRELLIS.2
│   └── birefnet/           birefnet.safetensors
├── output/            ← suas imagens/meshes gerados
├── input/             ← imagens e meshes de entrada
├── user/              ← settings da UI + workflows salvos DENTRO do ComfyUI
└── node_cache/        ← ver aviso abaixo
```

## ❌ NÃO fica no Drive

| Item | Por quê | Onde fica |
|---|---|---|
| `ComfyUI/` (código) | milhares de arquivos pequenos; FUSE torna o boot lento demais | `/content/ComfyUI`, reclonado em ~1 min |
| `custom_nodes/` | idem, e ainda quebra em update | `/content`, reinstalado pela Célula 4 |
| `venv` / `site-packages` | nunca ponha env Python no Drive | ambiente do Colab |
| `.git` dos repos de node | lixo puro | — |
| `temp/`, `__pycache__` | descartável | local |
| **Workflows** | são texto, versionar é melhor | **Git**, pasta `Workflows/` |

### Aviso sobre `node_cache/`
Eu tinha colocado cache dos repos de custom node no Drive. **Para o seu caso, desligue.**
O TRELLIS2 compila extensões CUDA (`nvdiffrast`, `cumesh`, `flex_gemm`) contra a
versão exata de torch/CUDA da sessão. Cachear isso no Drive guarda binário que
provavelmente não serve na próxima sessão — ocupa GB e ainda dá erro obscuro.
Melhor reclonar. Só vale cache para nodes puros em Python.

---

## Sobre a pasta antiga

**Sim, pode apagar `MyDrive/ComfyUI/` — mas salve os modelos antes.** Nunca apague direto.

```python
# Ver o que tem lá antes de qualquer coisa
!du -sh /content/drive/MyDrive/ComfyUI/* | sort -h
!find /content/drive/MyDrive/ComfyUI/models -size +50M
```

Passos:
1. **Mova os modelos** para a estrutura nova (mover no mesmo Drive é instantâneo,
   não re-upa nada):
   ```python
   !mkdir -p /content/drive/MyDrive/ComfyUI_Data
   !mv /content/drive/MyDrive/ComfyUI/models /content/drive/MyDrive/ComfyUI_Data/models
   ```
2. **Salve outputs e inputs** que você queira manter (`output/`, `input/`).
3. **Confira workflows** dentro de `ComfyUI/user/default/workflows/` — se tiver algo
   que não está no Git, copie para `Workflows/` e commite.
4. Aí sim apague `custom_nodes/` e o resto:
   ```python
   !rm -rf /content/drive/MyDrive/ComfyUI
   ```

Apagar `custom_nodes/` do Drive é a maior economia: 20 repos com `.git` completo
costumam dar vários GB, e são 100% descartáveis.

Atenção: a Lixeira do Google Drive **conta na sua cota**. Depois de apagar,
esvazie a lixeira, senão o espaço não volta.

---

## VRAM dos seus 3 workflows

Sua estimativa de 6 GB não bate com o que os workflows pedem:

| Workflow | Modelos | Realidade |
|---|---|---|
| `CharDesignandPartSplitting` | krea2 int8 + qwen3vl_4b fp8 | ~8–10 GB. Cabe no T4 com `lowvram`. |
| `Mesh_Processing` | flux-2-klein-9b + qwen_3_8b fp8 + TRELLIS2 | **9B + 8B na mesma sessão.** Não roda em T4. Precisa de A100. |
| `Skintoken` | grpo_1400.ckpt (Qwen3-0.6B) | ~4 GB, leve. Mas exige **Blender 4.0+** instalado. |

Ou seja: mais um motivo forte para uma sessão por workflow — e o `Mesh_Processing`
não é questão de organização, é questão de não caber mesmo em GPU pequena.

---

# Como rodar o notebook no Colab

**Direto do Git, sem baixar nada.** Abra:

```
https://colab.research.google.com/github/BloomRX/ComfyUI_Colab/blob/arena/01a05a82-comfyui-collab/notebooks/ComfyUI_Colab_Limpo.ipynb
```

Regra: troque `github.com` por `colab.research.google.com/github`.

Isso abre em **modo leitura** — roda normalmente, mas `Ctrl+S` não volta para o Git.
Para manter suas edições: *Arquivo → Salvar uma cópia no Drive*.

Você **não precisa** editar o notebook para adicionar workflows (veja abaixo), então
na prática dá para sempre abrir pelo link do GitHub e ter a versão mais recente.

O notebook clona este repo dentro do Colab, então workflows e registry chegam
sempre atualizados sem você mexer em nada.

---

# Adicionar workflows depois — sem me avisar

O notebook se adapta sozinho. Fluxo:

1. Commite o `.json` em `Workflows/` (ou solte em `ComfyUI_Data/workflows/` no Drive).
2. Rode as células. Ele aparece na lista numerada da Célula 3 automaticamente.

A Célula 3 só **lista**; a escolha é na Célula 4, escrevendo os números (`1`, `1,3`, `all`).
Se a lista vier vazia, a Célula 2 imprime quantos workflows achou em cada pasta —
isso diz na hora se o problema foi o clone do repo ou a pasta do Drive.

Para descobrir os custom nodes, há **três camadas**, nesta ordem:

| Camada | O que é | Cobre |
|---|---|---|
| 1. `config/node_registry.json` | mapa curado, com deps extras (Blender, DINOv3...) | seus 3 workflows, 100% |
| 2. `extension-node-map.json` do Manager | ~2.3 MB, milhares de nodes da comunidade | quase todo node público |
| 3. Manager na UI | *Install Missing Custom Nodes* | o resto |

A camada 2 é o que faz a adaptação automática: um node que eu nunca vi, mas que existe
no ecossistema, é resolvido sem intervenção. Na Célula 3 ele aparece marcado `(auto: ...)`.
Se nem o Manager conhecer, aparece `[!] sem fonte` e aí é instalação manual.

**Quando me chamar:** só se o node precisar de algo além de `git clone` +
`requirements.txt` — como o SkinTokens, que precisa de Blender via `apt`, ou o
Trellis2-GGUF, que precisa dos pesos do DINOv3. Essas coisas ficam em `pack_extras`
no registry, e são o único caso que exige curadoria.

---

# O que os installers do tutorial revelaram

Os `.bat` são para **ComfyUI Easy Install no Windows** (`python_embeded`, wheels
`win_amd64`, PATH do Blender). Nada disso roda no Colab. Mas eles corrigiram os
repositórios — meu chute inicial estava errado:

| Antes (errado) | Correto, segundo o `.bat` |
|---|---|
| `PozzettiAndrea/ComfyUI-TRELLIS2` | `visualbruno/ComfyUI-Trellis2` (wheels) + `Aero-Ex/ComfyUI-Trellis2-GGUF` (nodes `*_GGUF`) |
| `Rizzlord/ComfyUI-SkinToken` | `Aero-Ex/ComfyUI-SkinTokens` |
| *(faltando)* | `Aero-Ex/Texture_Projection-Nodes` |

Também extraí dos `.bat` e coloquei em `pack_extras`:
- **DINOv3** (`PIA-SPACE-LAB/dinov3-vitl-pretrain-lvd1689m`) → baixado para
  `models/facebook/dinov3-vitl16-pretrain-lvd1689m/`, exigido pelo Trellis2-GGUF.
- **Blender** → instalado via `apt` quando o SkinTokens é selecionado.

O que **não** dá para portar: as wheels pré-compiladas (`cumesh`, `nvdiffrast`,
`flex_gemm`, `o_voxel`, `flash_attn`) são todas `cp312-win_amd64`. No Linux o
`install.py` precisa compilar — é lento e pode falhar. Alvo do `.bat` é
Torch 2.8.0 + CUDA 12.8 + Python 3.12; se o Colab divergir muito disso, o Trellis2
é o primeiro a quebrar.

---

# Flags do `main.py` — cuidado

**`--normalvram` não existe.** O modo normal é o padrão do ComfyUI: você não passa
flag nenhuma. As flags reais são `--highvram`, `--lowvram`, `--novram`, `--gpu-only`, `--cpu`.
Por isso a Célula 6 usa `auto` como padrão (= não passa nada).

A Célula 6 agora roda `main.py --help` antes de subir e **descarta qualquer flag que
aquela versão não reconheça**. Assim uma atualização do ComfyUI que remova ou renomeie
uma flag não derruba mais o notebook.

Ela também detecta `--enable-manager`: nas versões novas o ComfyUI-Manager vem
integrado ao core e precisa dessa flag para ligar a UI dele.

---

# 403 no link do cloudflared

Sintoma: o ComfyUI sobe, o log mostra `To see the GUI go to: http://127.0.0.1:8188`,
mas o link `*.trycloudflare.com` responde **HTTP ERROR 403**.

Causa: `--listen 127.0.0.1` faz o ComfyUI aceitar só requisições cujo `Host` seja
localhost. O túnel encaminha o `Host: xxx.trycloudflare.com`, o servidor considera
isso um ataque de DNS-rebinding e devolve 403 — antes mesmo de servir a página.

Correção na Célula 6: **`--listen 0.0.0.0`** (+ `--enable-cors-header *`).
Continua seguro: nada da VM do Colab é exposto além do túnel, que é efêmero.

# Manager não aparecia

O log trazia:

```
To use the `--enable-manager` feature, the `comfyui-manager` package must be installed first.
```

Desde as versões novas o ComfyUI-Manager virou **pacote pip do core** — clonar em
`custom_nodes/` não basta. A Célula 6 agora roda
`pip install -r manager_requirements.txt` antes de subir, e o ícone de plugin aparece
(ou em *Menu → Manage Extensions*).

---

# "Corrigi o notebook mas o erro é o mesmo"

O Colab **guarda em cache** o `.ipynb` aberto via `colab.research.google.com/github/...`.
Reexecutar a célula roda o código velho — o commit novo não chega sozinho.

Como saber: a Célula 6 imprime `Notebook Celula 6: v6-wf-inject` na primeira linha.
Se esse marcador não aparecer, ou o comando ecoado mostrar `--listen 127.0.0.1`,
você está numa cópia antiga.

Como forçar a versão nova (qualquer uma serve):
1. Fechar a aba do Colab e reabrir o link do GitHub;
2. *Arquivo → Reverter para a versão salva*;
3. Abrir o link com um parâmetro qualquer no fim, ex: `...ipynb?v=2`.

Se você salvou uma cópia no Drive, ela **não** recebe atualizações do Git — nesse caso
apague a cópia e reabra pelo link do GitHub.

---

# Aba "Workflows" vazia

A aba lê de `<user-directory>/default/workflows/`, que no nosso caso é
`ComfyUI_Data/user/default/workflows/`. Os workflows do repo ficam em outro lugar,
então a aba nascia vazia.

A Célula 4 agora **copia os workflows selecionados para lá** automaticamente.
Ao abrir a UI eles já aparecem na aba, sem precisar de *Load* ou arrastar arquivo.

Detalhes:
- Só copia o que foi selecionado — a aba fica com os da sessão, não com tudo.
- Como a pasta está no Drive, o que você editar e salvar **persiste** entre sessões.
- Se o arquivo já existe e é idêntico, não sobrescreve (não perde suas edições).
- Workflows em **formato API** não aparecem na aba (limitação da UI). O aviso é
  impresso na Célula 4. Seus 3 são formato UI, então todos aparecem.

> Cuidado: se você editar um workflow na UI e quiser versionar a mudança, copie de
> volta para `Workflows/` no repo e commite. A pasta do Drive não é o Git.

---

# Os 2 tipos de erro ao abrir um workflow

## A) "Pacotes de nós ausentes" — eu resolvo (registry)

Era um bug meu, em duas partes:

1. Marquei `FluxKleinOneNode` e `ResolutionSelector` como **nativos** no
   `native_ignore`. Não são: vêm de `yanokusnir-ai/one-node-flux-2-klein`.
   Como estavam na lista de ignorados, o notebook nunca instalava o pacote.
2. **O parser não entrava em subgraphs.** O workflow tem um nó com nome de UUID
   (`53a025e4-...`) que é um subgraph com **21 nós dentro** — todos invisíveis
   para o parser. Corrigido: agora ele desce em `definitions.subgraphs`.

Depois da correção, os 3 workflows resolvem com **zero nós desconhecidos**.

**Quando me chamar:** sempre que a Célula 3 imprimir `[!] sem fonte: ...`, ou a UI
acusar pacote ausente. É sinal de registry incompleto, e o conserto é no repo —
não adianta você contornar na UI, porque na próxima sessão volta.

Alternativa imediata (funciona, mas não persiste): Manager → *Install Missing
Custom Nodes* → Restart.

## B) "Modelos Ausentes" — a Célula 5 resolve

Modelo é arquivo de peso, não código: nunca vem no `git clone`. Agora a **Célula 5
baixa os modelos dos workflows selecionados**, direto para o Drive, pulando o que
já existe. Para o `CharDesignandPartSplitting`:

| Arquivo | Pasta | Tamanho |
|---|---|---|
| `krea2_turbo_int8_convrot.safetensors` | `diffusion_models` | 13.5 GB |
| `qwen3vl_4b_fp8_scaled.safetensors` | `text_encoders` | 4.88 GB |
| `krea2_turbo_lora_rank_64_bf16.safetensors` | `loras` | 469 MB |
| `qwen_image_vae.safetensors` | `vae` | 254 MB |

**~19 GB.** Baixa uma vez, fica no Drive. Confira sua cota antes.

### Os que a UI listou e não têm download automático

- **`krea2_raw_int8_convrot`** — existe no repo oficial (13.5 GB), mas é a variante
  *raw*, alternativa à *turbo*. Baixar as duas = 27 GB. Está marcado `optional`;
  desmarque `PULAR_OPCIONAIS` se quiser. Ou aponte o `UNETLoader` para a turbo.
- **`wan_2.1_vae`** — de um ramo alternativo do grafo. O caminho principal usa
  `qwen_image_vae`. Troque no node ou bypasse o ramo.
- **`Detailer-KREA2`** — LoRA de detalhe, não está no repo oficial. Bypasse o
  `LoraLoaderModelOnly` (Ctrl+B) ou procure no Manager → Model Manager.

### Workflows futuros: a Célula 5 se adapta sozinha

Você estava certo em desconfiar — na primeira versão, `workflow_models` era uma
lista fixa e um workflow novo não baixaria nada. Agora são **três camadas**, igual
ao que já fazemos com custom nodes:

| Camada | O que faz | Cobre |
|---|---|---|
| 1. `workflow_models` no registry | curado por mim, com notas e `optional` | seus workflows atuais |
| 2. `model-list.json` do Manager | ~281 KB, milhares de modelos conhecidos | SDXL, VAEs, upscalers, ControlNets, Flux... |
| 3. Aviso explícito | lista o que sobrou e por quê | LoRA de Patreon, arquivo privado |

Como a camada 2 funciona: a célula varre o JSON do workflow atrás de qualquer
string terminada em `.safetensors`, `.ckpt`, `.gguf`, `.pt`, `.pth`, `.bin`, `.onnx`,
pega o nome do arquivo e procura na base do Manager. Achou, baixa para a pasta
certa (deduz de `save_path`/`type`) e marca `[auto]` no log.

Testado com um workflow inventado: resolveu `sd_xl_base_1.0` e `4x-UltraSharp`
sozinho, detectou que o VAE já existia no Drive e **não** rebaixou, e listou só a
LoRA fictícia como sem fonte.

Também há **deduplicação por nome em todo o `models/`**: se o arquivo já está no
Drive em qualquer subpasta, ele pula — não importa se você baixou pelo Manager,
manualmente ou por outro workflow.

`SO_LISTAR = True` mostra o plano sem baixar nada. Use antes de um workflow pesado
para ver quantos GB vão entrar.

**Quando ainda me chamar:** só se o modelo não estiver na base do Manager e vier de
uma fonte pública estável — aí eu adiciono em `workflow_models` com a URL e uma nota.
Modelo de Patreon/Discord/civitai privado nunca dá para automatizar: baixe manual,
ou use `URL_EXTRA` + `PASTA_EXTRA` na Célula 5 se tiver link direto.

---

# Barras de progresso (sem spam no log)

Módulo `config/nbui.py`, importado por todas as células.

O spam que você viu vem de duas fontes: `wget --show-progress` e barras tipo `tqdm`
dentro de scripts de instalação. No Colab, cada atualização vira **uma linha nova**
porque a saída é bufferizada por linha, não é um terminal de verdade.

Solução: no Colab usamos `ipywidgets.FloatProgress` — um objeto que se atualiza
**no lugar**, ocupando uma linha só de verdade. Fora do Colab cai para `\r`.

O que cada célula mostra agora:

| Célula | Barra |
|---|---|
| 1 | `Preparando ambiente: 3/4` + uma barra por git/pip |
| 4 | `Instalando pacotes: 2/6` + barra por clone, deps e `install.py` |
| 5 | `Modelos: 1/4` + barra por download com **MB, MB/s e ETA** |
| 6 | barra durante o pip do Manager |

Detalhes do downloader próprio (substitui o `wget`):
- Mostra `1.2GB/13.5GB · 8.3MB/s · ETA 1470s` numa linha só.
- Baixa para `.part` e só renomeia no fim — **arquivo truncado nunca é confundido
  com download completo** (o `wget -c` antigo deixava lixo pela metade).
- Retoma de onde parou via header `Range` se a sessão cair no meio.

Comandos (`git clone`, `pip`, `install.py`) mostram uma barra viva com a última
linha do log ao lado. **Se falhar, aí sim imprime as últimas 12 linhas** — silencioso
quando dá certo, verboso quando quebra, que é quando você precisa.

---

# Checagem de ambiente (GPU x CPU) na Célula 6

Antes de subir o servidor, a Célula 6 imprime um resumo:

```
================================================================
  AMBIENTE DE EXECUCAO
================================================================
  Acelerador : GPU — Tesla T4
  VRAM       : 15360 MB
  PyTorch    : 2.11.0+cu128  | CUDA disponivel: True
  RAM        : 12.9 GB   | Disco livre: 78.2 GB
================================================================
```

**Com GPU:** segue direto, sem perguntar nada.

**Sem GPU:** explica as consequências e **pergunta antes de ligar**, com dois botões
(*Sim, ligar em CPU* / *Não, vou trocar para GPU*). Sem resposta em 120s, não liga.
Fora do Colab cai para `input()`; sem stdin, cancela — nunca sobe por acidente.

O aviso é específico, não genérico:
- geração ~20x a 100x mais lenta;
- Trellis2 e SkinTokens **não rodam** em CPU (dependem de kernels CUDA);
- Krea-2 / Flux2 provavelmente estouram a RAM.

Detecção cruzada: `nvidia-smi` **e** `torch.cuda.is_available()`. Se o `nvidia-smi`
enxerga a placa mas o torch não acessa CUDA, isso é dito explicitamente — é um caso
real (torch CPU-only instalado por engano) que passaria despercebido.

Quando o modo CPU é confirmado, o notebook adiciona **`--cpu`** ao `main.py`.
Sem essa flag o ComfyUI tenta inicializar CUDA e quebra no boot.

> Trocar o ambiente **reinicia a sessão**: é preciso rodar as células 1..5 de novo.
> Nada que já esteja no Drive é baixado outra vez, então costuma ser rápido.
