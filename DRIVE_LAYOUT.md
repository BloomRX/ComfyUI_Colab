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

---

# Baixar um modelo avulso do HuggingFace

Exemplo: `https://huggingface.co/ShinoharaHare/Waifu-Inpaint-XL`

Esse repo tem duas particularidades comuns que vale saber reconhecer.

## 1. É "gated" — precisa de token

A página diz *"You need to agree to share your contact information to access this
model"*. Ele é público, mas exige aceite. Sem isso, o download retorna **401/403**.

Passos:
1. Logue no HuggingFace e abra a página do modelo.
2. Aceite as condições (botão *Agree and access repository*). É uma vez só, por conta.
3. Gere um token em **huggingface.co/settings/tokens** (tipo *Read* basta).
4. Cole em **`HF_TOKEN`** na Célula 5.

## 2. Tem dois formatos no mesmo repo — pegue o certo

| O que é | Serve no ComfyUI? |
|---|---|
| `Waifu-Inpaint-XL.safetensors` (6.94 GB) | **Sim** — é este que você quer |
| pastas `unet/`, `vae/`, `text_encoder/`, `scheduler/`... | Não — formato `diffusers`, para Python |

O ComfyUI carrega **checkpoint de arquivo único**. Ignore as pastas.

## Como baixar

Na **Célula 5**:
- `URL_EXTRA` = link do arquivo
- `PASTA_EXTRA` = `checkpoints`
- `HF_TOKEN` = seu token

```
https://huggingface.co/ShinoharaHare/Waifu-Inpaint-XL/resolve/main/Waifu-Inpaint-XL.safetensors
```

A célula aceita também o link `/blob/` (o que aparece ao clicar no arquivo) e
converte sozinha para `/resolve/`. Se você colar a URL da **página do repo**, ela
avisa em vez de baixar um HTML de 200 KB com nome de `.safetensors` — erro clássico,
que só aparece depois como "checkpoint corrompido".

Como pegar o link certo: aba **Files** → clique no `.safetensors` → botão **download**
→ copiar endereço do link.

## Onde cada tipo vai

| Tipo | `PASTA_EXTRA` |
|---|---|
| Checkpoint SD/SDXL (arquivo único) | `checkpoints` |
| LoRA | `loras` |
| VAE avulso | `vae` |
| ControlNet | `controlnet` |
| Upscaler (`.pth`) | `upscale_models` |
| UNet/GGUF isolado | `unet` ou `diffusion_models` |

## Inpaint: cuidado com o workflow

Modelo de inpaint SDXL não funciona num grafo txt2img comum. Precisa de
`VAEEncodeForInpaint` (ou `SetLatentNoiseMask`) e de uma máscara. Nos templates do
ComfyUI: *Workflow → Browse Templates → Inpainting*.

---

# Como pegar o token do HuggingFace

## 1. Criar o token (no site)

1. Crie a conta / logue em **huggingface.co**.
2. Vá em **huggingface.co/settings/tokens**
   (ou: sua foto no canto superior direito → *Settings* → *Access Tokens*).
3. **Create new token**.
4. Tipo: **Read** — é o suficiente para baixar. Nunca use *Write* aqui.
5. Dê um nome (ex: `colab-comfyui`) e crie.
6. **Copie na hora.** O HF mostra o token uma única vez; depois só resta gerar outro.
   Formato: `hf_` seguido de ~34 caracteres.

Antes de baixar um modelo *gated*, ainda é preciso abrir a página dele logado e
clicar em **Agree and access repository**. O token sozinho não pula esse aceite.

## 2. Guardar o token (no Colab) — sem colar no notebook

**Não** existe mais campo de texto para o token no notebook. Isso foi proposital:
um `#@param` grava o valor **dentro do arquivo .ipynb**, e se você salvasse uma
cópia no Drive ou commitasse no Git, o token ia junto, em texto puro.

Use o cofre do Colab:

1. Painel esquerdo → ícone de **chave 🔑** (*Secrets*).
2. **+ Adicionar novo secret**.
3. Nome: **`HF_TOKEN`** (exatamente assim). Valor: o token.
4. Ligue a chavinha **"Acesso ao notebook"**.
5. Rode a Célula 5 de novo.

Confirmação no log:
```
HF_TOKEN carregado de: Colab Secrets (…a1b2)
```
Só os 4 últimos caracteres aparecem — o suficiente para conferir qual token é,
sem expor nada.

O secret fica na sua conta Google, não no arquivo: vale para todos os notebooks,
sobrevive à troca de sessão e nunca é commitado.

### Alternativa para uma vez só

Se não quiser criar o secret, rode numa célula nova:

```python
pedir_token()
```

Abre um campo mascarado (`getpass`), guarda só na memória da sessão e some quando
o runtime reinicia. Depois é só reexecutar a Célula 5.

## Ordem de busca do token

1. **Colab Secrets** (`HF_TOKEN`) — recomendado
2. Variável de ambiente `HF_TOKEN`
3. `pedir_token()` na hora

Sem nenhum dos três, a célula avisa e segue baixando só o que é público.

---

# `IMPORT FAILED: custom_nodes/ComfyUI`

Erro no log:

```
FileNotFoundError: '/content/ComfyUI/custom_nodes/ComfyUI/__init__.py'
Cannot import /content/ComfyUI/custom_nodes/ComfyUI module for custom nodes
0.0 seconds (IMPORT FAILED): /content/ComfyUI/custom_nodes/ComfyUI
```

Causa: no `extension-node-map.json` do Manager, os nós **do core** aparecem
apontando para o repo `comfyanonymous/ComfyUI`. O auto-resolve pegava esse link,
extraía o basename `ComfyUI` e clonava para `custom_nodes/ComfyUI` — uma cópia do
ComfyUI inteiro dentro da pasta de custom nodes. Sem `__init__.py` na raiz, o
import falha.

Era inofensivo (só barulho no log), mas desperdiçava download e podia confundir.

Correções:
- Lista `never_install` no registry (`ComfyUI`, `ComfyUI-Manager`, frontend).
- `resolve()` devolve `None` para qualquer coisa que aponte para o repo do core.
- A Célula 4 **apaga** `custom_nodes/ComfyUI` inválido, se já existir.

## Custom nodes "sobrando" no log

O log também mostrou `ComfyUI-Impact-Pack` e `ComfyUI-Impact-Subpack` carregando,
mesmo sem estarem nos workflows selecionados. Isso é esperado: o notebook só
desativa o que ele mesmo instalou naquela sessão. Nodes instalados **pela UI do
Manager** ficam ativos até você desativá-los.

Se quiser sessão 100% limpa, rode a Célula 4 de novo — ela renomeia para
`.disabled` tudo que não pertence aos workflows marcados.

---

# Workflows 4–7: o que aconteceu

Aquela listagem saiu de uma sessão **anterior ao fix `v13`**, por isso o pacote
fantasma `ComfyUI` aparecia em quase todos. Já está corrigido.

Também ampliei o registry: **37 pacotes** (era 25) e **96 nós** mapeados, cobrindo
Comfyroll, tinyterra, mikey, WAS, ComfyMath, Chibi, AutomaticCFG, Extra-Samplers,
QualityOfLife, temperature-settings, perturbed-attention, ComfyI2I e Cosmos-Reference.

## Duas novas camadas de dedução

Os "sem fonte" eram quase todos **display names**, não class types:

| Antes | Agora |
|---|---|
| `Lora Loader Stack (rgthree)` | sufixo `(rgthree)` → `rgthree-comfy` |
| `Image Comparer (rgthree)` | idem |
| `CR Apply LoRA Stack` | prefixo `CR ` → `ComfyUI_Comfyroll_CustomNodes` |
| `PrimitiveNode` | reconhecido como nativo do core |
| `FreeU_V2 (Advanced)` | mapeado para `sd-perturbed-attention` |

Prefixos conhecidos ficam em `prefix_hints` no registry (`CR `, `ttN `, `Mikey`,
`WAS `, `Chibi`, `CM_`). Isso faz packs inteiros serem reconhecidos sem eu precisar
listar nó por nó.

Ordem de resolução agora: **registry → mapa do Manager → prefixo → sufixo `(pack)`**.

## Sobre os workflows novos

Eles estão só no seu Drive — no Git há apenas os 3 originais. Funciona, mas se
commitar em `Workflows/` você ganha versionamento e eu consigo validar cada um.

## Atenção ao `Efaces_Pony_XL_V01`

São **15 pacotes** num workflow só. Isso multiplica o risco de conflito de
dependência (vários deles mexem em `numpy`/`opencv`) e o tempo de import. Se algo
quebrar depois de rodá-lo, é o primeiro suspeito — rode-o numa sessão isolada.

## `WaifuInpaintXL` — só nós nativos

Não precisa de nenhum custom node, só do checkpoint de 6.94 GB. Como é *gated*,
configure o secret `HF_TOKEN` antes (veja a seção acima).

---

# Validação dos 7 workflows (todos no Git)

Rodei o parser real em cada um. Resultado: **zero nós sem fonte**.

| # | Workflow | Pacotes | Observação |
|---|---|---|---|
| 1 | CharDesignandPartSplitting | 1 | Krea-2, ~19 GB |
| 2 | Detailer | 3 | Impact Pack + Subpack |
| 3 | Efaces_Pony_XL_V01 | **14** | o mais arriscado |
| 4 | Mesh_Processing | 6 | não cabe em T4 |
| 5 | PotatCats-inpaint ANIMA | 8 | modelos ANIMA são do autor |
| 6 | Skintoken | 1 | precisa de Blender |
| 7 | WaifuInpaintXL | **0** | só nós nativos |

Foram 32 nós desconhecidos mapeados nesta rodada. Os grupos maiores:
- **Impact Pack**: `ToBasicPipe`, `FromBasicPipe`, `MaskToSEGS`, `SegsToCombinedMask`,
  `DetailerForEachDebug`, `MaskPreview`, `ImpactImageInfo`.
- **WAS Suite**: `Constant Number`, `Image Resize`, `Images to RGB`.
- **Nativos do core** (não eram custom node): `BasicScheduler`, `GITSScheduler`,
  `CLIPTextEncodeSDXL`, `PatchModelAddDownscale`, `ImageBlend`, `ImageCompositeMasked`.

Registry hoje: **38 pacotes, 135 nós, 98 nativos**.

## Downloads automáticos adicionados

| Workflow | Arquivo | Tamanho |
|---|---|---|
| WaifuInpaintXL | `Waifu-Inpaint-XL.safetensors` | 6.94 GB (**gated**) |
| Detailer | `v1-5-pruned-emaonly-fp16.safetensors` | 2.13 GB |
| Efaces | `sdxl_vae.safetensors` | 335 MB |

A Célula 5 agora **detecta modelo gated sem token** e explica o que fazer, em vez
de tentar baixar e salvar um HTML de erro com nome de `.safetensors`.

## O que continua manual (Civitai / autor)

Civitai não tem URL estável para download direto, então estes ficam com nota:
`waiIllustriousSDXL_v160`, `Eyeful_v2-Paired.pt` (vai em `models/ultralytics/bbox`),
`aaaautismPonyFinetune_v4`, `Expressive_H-000001`, `detailed_notrigger`,
e os modelos ANIMA (`anima-base-v1.0`, `AnimeEditV2`, `qwen_3_06b_base`).

Baixe manualmente e coloque na pasta indicada, ou use `URL_EXTRA` + `PASTA_EXTRA`
se tiver link direto.

## Recomendação de ordem

1. **WaifuInpaintXL** — zero custom nodes, 1 modelo. Melhor teste inicial.
2. **Detailer** — 3 pacotes estáveis.
3. **CharDesign** — pesado mas automático.
4. **Efaces** — 14 pacotes: rode isolado, é o candidato natural a conflito.
5. **Mesh_Processing** — só em GPU maior que T4.

---

# PixAI, Civitai e afins — de onde dá para puxar

## PixAI (pixai.art)

É uma **plataforma de geração**, não um repositório de modelos. Você gera na nuvem
deles, com os modelos deles. Isso muda o que dá para trazer:

| O que | Dá? |
|---|---|
| **Workflow ComfyUI** | **Não.** O PixAI não usa ComfyUI. Não existe JSON para exportar. |
| **Prompt + parâmetros** | Sim — ficam visíveis na página da imagem (quando o autor compartilha). |
| **LoRA / checkpoint** | **Às vezes.** Depende do autor ter permitido download. |

Se o download existir, fica no menu de três pontinhos (`...`) na página do modelo.
Muitos são "somente geração no site" e não têm essa opção — não há truque, é
decisão de quem subiu.

**O caminho mais produtivo:** a maioria das LoRAs de anime populares no PixAI é
reupload (ou tem equivalente) no **Civitai** ou no **HuggingFace**. Procure pelo nome
lá primeiro — quase sempre acha, e com download direto.

O que sempre dá para aproveitar é a **receita**: prompt, negative, sampler, steps,
CFG, LoRAs usadas e pesos. Isso você reproduz no seu ComfyUI com os modelos
equivalentes.

## Onde cada fonte se encaixa

| Fonte | Modelos | Workflow ComfyUI | Download automatizável |
|---|---|---|---|
| **HuggingFace** | sim | às vezes | **sim** (Célula 5) |
| **Civitai** | sim | sim (aba *Workflows*) | não (URL instável) |
| **PixAI** | parcial | não | não |
| **OpenArt / Comfy Workflows** | não | **sim**, feitos para ComfyUI | n/a |

Para **workflows** prontos de ComfyUI, os lugares certos são
`openart.ai/workflows`, `comfyworkflows.com`, a aba *Workflows* do Civitai e os
templates embutidos (*Workflow → Browse Templates*).

## Trazendo um workflow de fora

O fluxo já está pronto para isso:
1. Baixe o `.json` (ou arraste o **PNG** gerado pelo ComfyUI — ele carrega o grafo
   embutido nos metadados).
2. Ponha em `Workflows/` no repo, ou em `ComfyUI_Data/workflows/` no Drive.
3. Rode as Células 3 → 4 → 5. Os custom nodes e os modelos conhecidos são
   resolvidos automaticamente.

> Cuidado com licença: vários modelos de anime têm restrição de uso comercial ou
> proíbem redistribuição. Se for usar para algo além de teste pessoal, leia a
> licença na página do modelo.

---

# Waifu para o Project AIRI: Live2D ou 3D (VRM)?

O AIRI aceita os dois: **Live2D** e **VRM** (e, nas versoes recentes, tambem MMD,
Spine 2D e "Tachie"). Os dois tem auto-blink, look-at, idle e lip-sync. Ou seja:
pelo lado do AIRI, nao ha um vencedor. A escolha e sobre **producao**, nao sobre
suporte.

## O ponto que costuma ser mal entendido

**O ComfyUI nao gera Live2D nem VRM.** Ele nao produz o arquivo final em nenhum
dos dois casos. O que ele faz e produzir a **materia-prima**:

- Live2D -> a arte da personagem, ja **separada em partes** (cabelo, olhos, boca,
  braco esquerdo, etc.), em PNG com transparencia.
- 3D/VRM -> a **referencia visual** (e, opcionalmente, uma malha bruta).

O rig — o que faz a personagem se mexer — e feito **fora** do ComfyUI:
Cubism Editor (Live2D) ou Blender/VRoid Studio (VRM). Nao existe atalho para
essa parte hoje.

## Comparacao honesta

| | Live2D | 3D / VRM |
|---|---|---|
| Fidelidade ao seu desenho | **altissima** — e literalmente o seu desenho | media — o estilo passa por um filtro 3D |
| Trabalho para o primeiro resultado | alto (rig manual, camada por camada) | **baixo** se usar VRoid Studio |
| Angulos | so o angulo desenhado (~30 graus de giro) | **qualquer** angulo, camera livre |
| Custo de mudar a personagem depois | alto | baixo |
| Ferramenta de rig | Cubism (versao gratis limita parametros) | VRoid Studio / Blender (gratis) |
| Curva de aprendizado | ingreme | suave |
| Cara de "VTuber classica" | sim | mais "jogo" |

## Recomendacao pratica

**Comece pelo 3D (VRM), mesmo que voce prefira Live2D no fim.**

O motivo nao e estetico, e de risco. Com o **VRoid Studio** (gratis) voce tem
uma VRM funcional rodando dentro do AIRI **no mesmo dia** — e ai voce descobre
coisas que so aparecem no uso real: se a personalidade combina, se a proporcao
funciona na tela, se voce se cansa do design. Um rig Live2D decente leva
**semanas** e trava o design: se voce mudar de ideia sobre o penteado, refaz
boa parte do rig.

Ou seja: use a VRM como **protótipo jogável** do conceito. Se depois de umas
semanas convivendo com ela voce ainda quiser o visual 2D, ai sim investe no
Live2D — e ai voce ja vai saber exatamente qual design quer rigar.

## Como os SEUS workflows se encaixam

Isso e o que mais importa: voce ja tem as duas trilhas montadas.

### Trilha comum (defina a personagem) — faca isso primeiro

| Workflow | Papel |
|---|---|
| `Efaces_Pony_XL_V01` ou `PotatCats-inpaint ANIMA` | gerar a personagem a partir do seu conceito |
| `Detailer` | consertar rosto/olhos (ADetailer) |
| `WaifuInpaintXL` | corrigir pedacos pontuais sem refazer tudo |

Saida desejada: um **character sheet** — a mesma personagem de frente, 3/4,
perfil e costas, com o mesmo outfit. Isso e o insumo das duas trilhas. Gaste
tempo aqui; e o unico passo que nao da para refazer barato depois.

Dica de consistencia: fixe a **seed** e o prompt, mude so a pose/angulo. Se a
personagem "escorregar" entre as imagens, gere uma vez, e use `WaifuInpaintXL` /
`Detailer` para trazer as outras de volta ao mesmo rosto.

### Trilha Live2D

| Workflow | Papel |
|---|---|
| `CharDesignandPartSplitting` | **este e o coracao da trilha 2D** — separa a personagem em partes |
| `WaifuInpaintXL` | preencher o que fica escondido atras de outra camada |

Aquele segundo workflow tem um papel que nao e obvio: no Live2D, quando o braco
se move, aparece o pedaco do torso que estava atras dele. Esse pedaco **nunca
foi desenhado**. O inpaint serve exatamente para inventar essas areas ocultas —
e sem isso o rig fica com buracos. Depois disso, os PNGs vao para o **Cubism
Editor**, e o `.model3.json` resultante voce importa no AIRI.

Custo: `CharDesignandPartSplitting` puxa o Krea-2, **~19 GB**. Cabe no T4, mas
demora para baixar. Vale deixar no Drive.

### Trilha 3D

| Workflow | Papel |
|---|---|
| `Mesh_Processing` | imagem -> malha 3D (Trellis2) |
| `Skintoken` | texturas de pele |

**Aviso importante e ja conhecido:** `Mesh_Processing` **nao roda no T4** (usa
flux-2-klein-9b + Trellis2; precisa de A100). E o `Skintoken` exige Blender no
PATH. Nenhum dos dois esta disponivel para voce hoje no Colab gratuito.

E aqui vai a parte contraintuitiva: **isso nao te bloqueia**. A malha que o
Trellis2 gera e uma malha bruta, sem esqueleto, sem blendshapes de expressao,
sem os "spring bones" do cabelo — ou seja, **nao e uma VRM** e ainda daria muito
trabalho no Blender. Para uma waifu de companhia, o **VRoid Studio** e o caminho
mais curto e melhor: exporta VRM ja rigada, com expressoes e fisica de cabelo
prontas. Voce usa o character sheet do ComfyUI so como **referencia visual** e
recria no VRoid.

Traduzindo: no seu hardware atual, a trilha 3D e **ComfyUI para o conceito +
VRoid para o modelo**. O `Mesh_Processing` fica guardado para o dia que voce
tiver uma GPU maior — e ainda assim seria mais util para props/cenario do que
para a personagem.

## Caminho sugerido

1. Gerar a personagem (`Efaces` ou `ANIMA`) + `Detailer` -> travar o design.
2. Fazer o character sheet em 4 angulos, mesma seed.
3. Recriar no **VRoid Studio** -> exportar `.vrm` -> importar no AIRI.
   *Voce tem uma waifu funcional aqui.*
4. Conviver com ela algumas semanas.
5. Se ainda quiser 2D: `CharDesignandPartSplitting` + inpaint das areas
   ocultas -> **Cubism** -> importar no AIRI.

Passos 1-3 sao viaveis no seu Colab hoje. O passo 5 tambem (o Cubism e local, no
seu PC). Nada disso depende do `Mesh_Processing`.

## Selecao no notebook

Para a trilha comum + Live2D, selecione na Celula 3:
`CharDesignandPartSplitting`, `Detailer`, `Efaces_Pony_XL_V01`, `WaifuInpaintXL`.

Cuidado: o `Efaces_Pony_XL_V01` traz **14 packs** e e o mais propenso a conflito
de dependencias (numpy/opencv). Se der erro de import, rode-o **sozinho**, em
sessao separada dos outros.

---

# WaifuVroid.json — character sheet de 4 angulos

Workflow proprio deste repo (nao veio do tutorial). Gera o **mesmo personagem em
4 angulos** — front, 3/4, side, back — para servir de referencia de modelagem.

**Zero custom nodes.** So nos nativos: `CheckpointLoaderSimple`, `LoraLoader`,
`CLIPTextEncode`, `ConditioningConcat`, `EmptyLatentImage`, `KSampler`,
`VAEDecode`, `SaveImage`. Roda em qualquer ComfyUI limpo.

## Como funciona

O truque esta no `ConditioningConcat`. A **identidade** do personagem e
codificada **uma unica vez** (no no 3) e reaproveitada nos 4 ramos; so o trecho
do **angulo** muda e e concatenado depois. Isso garante que o texto de identidade
seja byte-a-byte identico nos quatro — se voce escrevesse quatro prompts
completos, pequenas diferencas de tokenizacao ja fariam o personagem escorregar.

Combinado com a **mesma seed** nos 4 KSamplers, e o maximo de consistencia que
da para conseguir sem LoRA.

## Como usar

1. No **no 1**, escolha o checkpoint (anime SDXL — `waiIllustriousSDXL_v160`,
   Pony, etc).
2. No **no 3**, escreva a identidade do personagem. **Nao** escreva angulo ali.
3. Rode. Gostou de um resultado? Copie a seed e coloque nos 4 KSamplers.
4. Quando tiver a LoRA do personagem, selecione no **no 2** — a consistencia
   melhora muito.

Fundo branco e luz chapada sao propositais: isso e **referencia para modelagem**,
nao arte final. Sombra dura atrapalha na hora de modelar.

Custo no T4: 832x1216 x4 = ~2-3 min. Faltou VRAM? Use 768x1152.

## "Preciso gerar as partes separadas para o VRoid?"

**Nao.** Essa e a confusao mais comum, e vale entender a diferenca:

| | Live2D (Cubism) | 3D / VRM (VRoid) |
|---|---|---|
| Precisa de partes separadas? | **Sim** — PNGs com alpha, camada por camada | **Nao** |
| O que o ComfyUI entrega | os recortes de fato | so **referencia visual** |
| Workflow | `CharDesignandPartSplitting` | `WaifuVroid` |

No **Live2D** as partes recortadas *sao* o material final — elas viram camadas
que o rig move. Por isso existe o `CharDesignandPartSplitting`.

No **VRoid** e outra logica: voce nao monta a personagem colando imagens. Voce
**esculpe** a malha e **pinta** a textura dentro do proprio VRoid, usando presets
(blazer, saia plissada, meia knee-high ja existem prontos). A imagem do ComfyUI
serve so para voce **olhar enquanto modela** — igual a um artista com a
referencia aberta na segunda tela.

Uma imagem 2D recortada nao ajuda a modelar 3D. O que ajuda e ver **o mesmo
personagem de varios angulos**, para entender o volume. E exatamente o que o
`WaifuVroid` entrega.

**Onde o ComfyUI ainda ajuda no 3D:**
- **Referencia de angulos** — o `WaifuVroid` (este workflow).
- **Close-ups de detalhe** — rosto, brasao, acessorio. Rode o workflow mudando o
  texto do angulo para `close-up of face` / `close-up of the emblem`. Util para
  pintar detalhe pequeno na textura.
- **Texturas planas** — padrao de tecido, estampa, o brasao isolado em fundo
  branco para importar como decal.
- **Pele** — o `Skintoken` faz isso, mas exige Blender no PATH.

O que o ComfyUI **nao** faz: gerar a malha rigada. `Mesh_Processing` (Trellis2)
produz malha bruta, sem esqueleto nem blendshapes — e nao roda em T4. Para uma
waifu de companhia o VRoid continua o caminho mais curto.

---

# WaifuVroid_FromConcept.json — partindo de uma imagem de concept

Mesma estrutura do `WaifuVroid`, mas com uma **imagem de referencia** entrando
via **IPAdapter**. Serve para quem ja tem um concept art (feito no GPT/DALL-E,
Midjourney, PixAI, ou desenhado a mao) e quer que o ComfyUI produza **aquele**
personagem, nao um parecido.

A diferenca conceitual: no `WaifuVroid` o modelo so **le** o texto; aqui ele
tambem **olha** a imagem.

Pack necessario: `ComfyUI_IPAdapter_plus` (a Celula 3 instala). Na primeira
execucao o `IPAdapterUnifiedLoader` baixa sozinho os modelos IPAdapter +
CLIP Vision (~2.5 GB).

## Preparar a imagem (o passo que as pessoas pulam)

**Nao jogue a folha de concept inteira no `LoadImage`.** Uma folha tipica tem
varias poses, texto, barra de paleta e close-ups. O IPAdapter nao entende
"isso e um documento" — ele trata tudo como referencia visual e tenta reproduzir
o conjunto, **inclusive as letras**. O resultado costuma ser uma colagem borrada.

Recorte **uma** imagem limpa, so o personagem, sem texto:
- um recorte do **full body** -> referencia de roupa e proporcao;
- um recorte do **rosto** -> referencia de identidade facial.

Salve em `ComfyUI/input/` e escolha no no 2. Vale gerar os dois arquivos e
testar qual funciona melhor: o recorte do rosto costuma dar identidade mais
forte, o de corpo inteiro acerta melhor a roupa.

## Ajustar o weight (no 4)

| Weight | Efeito |
|---|---|
| 0.4–0.5 | inspiracao solta, muita liberdade criativa |
| **0.75** | equilibrado — padrao do arquivo |
| 1.0+ | copia agressiva; tende a repetir a **pose** da referencia |

Sintoma tipico: os 4 angulos saem quase iguais, todos de frente. Causa: weight
alto demais — a referencia esta impondo a pose. **Abaixe** para ~0.6. Se em vez
disso o personagem perder a cara, suba.

O parametro `weight_type` tambem ajuda: `linear` e o padrao; `style transfer`
pega o estilo e solta a composicao, util justamente quando o angulo nao quer
mudar.

## Limitacao honesta

IPAdapter da **semelhanca forte**, nao identidade travada. Detalhes pequenos —
um brasao especifico, um acessorio incomum, um padrao de olho — vao variar entre
as geracoes. Isso e esperado.

Corrija com o que voce ja tem: `Detailer` para o rosto e `WaifuInpaintXL` para
consertos pontuais.

## O papel disto no projeto

IPAdapter e a **ponte**, nao o destino:

```
concept (GPT/desenho)
   -> WaifuVroid_FromConcept  (IPAdapter: ~20 imagens boas)
   -> Detailer / WaifuInpaintXL  (limpar as imperfeicoes)
   -> treinar a LoRA do personagem
   -> WaifuVroid + LoRA  (consistencia real, character sheet final)
   -> VRoid Studio -> .vrm -> AIRI
```

Sem imagens consistentes nao da para treinar LoRA; e sem LoRA nao da para ter
consistencia real. O IPAdapter quebra esse circulo: ele produz o dataset inicial.
Depois que a LoRA existir, este workflow deixa de ser necessario.

---

## Erro: "ClipVision model not found." (IPAdapter)

**Causa:** o `IPAdapterUnifiedLoader` **nao baixa nada**. Ele so procura os
modelos no disco e lanca excecao se nao achar. O nome "UnifiedLoader" sugere que
ele resolve tudo sozinho — nao resolve.

**Solucao:** rode a **Celula 5** com `WaifuVroid_FromConcept` selecionado. Ela
baixa os dois arquivos, ja com o nome certo:

| Arquivo | Pasta | Tamanho |
|---|---|---|
| `CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors` | `models/clip_vision` | 2.53 GB |
| `ip-adapter-plus_sdxl_vit-h.safetensors` | `models/ipadapter` | 848 MB |

**O nome do CLIP Vision importa.** O IPAdapter identifica o encoder pelo nome do
arquivo. No repositorio `h94/IP-Adapter` ele se chama `model.safetensors` — se
voce baixar manualmente e nao renomear, o no continua dizendo que nao encontrou.
A Celula 5 ja salva com o nome correto (usa o campo `file` do registry, nao o
nome remoto).

Alternativa manual: **Manager > Model Manager**, procure por `ipadapter` e por
`clip vision`, e instale `IPAdapter plus SDXL` + `CLIP-ViT-H-14`.

**Conferir se deu certo:**

```
ls -la /content/drive/MyDrive/ComfyUI_Data/models/clip_vision/
ls -la /content/drive/MyDrive/ComfyUI_Data/models/ipadapter/
```

Os dois caminhos ja aparecem nos `extra search path` do log de boot, entao basta
o arquivo estar la. Se voce baixou com o servidor no ar, **reinicie a Celula 6** —
o ComfyUI indexa os modelos no boot.

**Escolha do preset (no 3):** `PLUS (high strength)` casa com
`ip-adapter-plus_sdxl_vit-h`. Se trocar o preset, o par de arquivos muda — e o
erro volta. Mantenha o preset ou baixe o modelo correspondente.

---

## Imagem "queimada": cores neon, pele vermelha, fundo saturado

**Causa: CFG alto demais.** Modelos **Illustrious e Pony** trabalham com CFG
muito mais baixo que o SDXL base. CFG 7 — o padrao que se ve em tutorial de
SD1.5 — satura as cores nesses modelos: pele fica vermelha, o fundo vira um
amarelo/laranja neon, tudo ganha contraste artificial.

| Modelo | CFG saudavel |
|---|---|
| SD 1.5 | 7 – 9 |
| SDXL base | 6 – 8 |
| **Illustrious / Pony** | **3.5 – 5.0** |
| Turbo / Lightning / LCM | 1 – 2 |

Os dois `WaifuVroid` agora vem com **CFG 4.5**. Se ainda queimar, baixe para 3.5
e troque o sampler para `euler_a`.

Sintoma parecido, causa diferente: se a imagem sair *cinzenta e sem contraste*, o
CFG esta baixo **demais**. Suba um pouco.

Tambem adicionei ao negative: `oversaturated, neon colors, burnt colors,
high contrast, glowing skin, red skin`. Ajuda, mas **nao substitui** corrigir o
CFG — negative nao conserta parametro errado.

## O angulo "back" veio de frente

O IPAdapter esta **impondo a pose** da imagem de referencia. Se o seu recorte e
um full body de frente, com weight alto ele forca todas as saidas para frente,
ignorando `from behind` no prompt.

Solucao, em ordem:

1. **Abaixe o weight** do no 4: 0.75 -> **0.6** (ja e o padrao agora) -> 0.4.
2. Mude `weight_type` para **`style transfer`** — pega o estilo e solta a
   composicao. E o ajuste mais eficaz quando o angulo nao muda.
3. Reforce o texto do angulo. Os presets ja foram reforcados:
   `from behind, back view, facing away from viewer, head turned away,
   back of head, hair from behind, no face visible`.
4. Acrescente ao negative, so no ramo `back`: `looking at viewer, face, frontal`.

Existe um limite real: **IPAdapter e referencia, nao controle de pose.** Para
angulo garantido seria preciso ControlNet (OpenPose) com uma pose de costas. Para
dataset de LoRA, porem, isso nao e critico — se um angulo nao sair, gere mais
seeds e aproveite o que vier. Variedade importa mais que os 4 angulos exatos.

---

## "Pacotes de nós ausentes" e o botao Instalar do Manager nao funciona

Sintoma: o Manager acusa `ComfyUI_IPAdapter_plus` como ausente; voce clica em
**Instalar** e nada acontece (ou ele diz que instalou, mas o erro continua).

**O pack nao sumiu — ele foi DESATIVADO pela Celula 4.**

No fim da Celula 4 existe este bloco, que e o coracao do "so os nodes da sessao":

```python
for d in sorted(os.listdir(CN)):
    if d == 'ComfyUI-Manager' or d in need: continue
    os.rename(pth, pth + '.disabled')
```

Ou seja: **tudo que nao pertence aos workflows selecionados vira `.disabled`.**
Se voce rodou a Celula 4 de novo sem marcar o `WaifuVroid_FromConcept`, a pasta
virou `ComfyUI_IPAdapter_plus.disabled` e os nos sumiram da UI.

**Por que o botao Instalar do Manager falha:** a pasta `.disabled` ainda esta
la. O `git clone` do Manager recusa gravar num destino em conflito, e o
ComfyUI so carrega o diretorio com o nome exato. Instalar por cima nao resolve.

### Conserto (o jeito certo)

Rode a **Celula 3**, veja o numero do `WaifuVroid_FromConcept` na lista, e rode a
**Celula 4** com esse numero na `SELECAO`. Ela detecta o `.disabled` e reativa:

```
reativado ComfyUI_IPAdapter_plus
```

Depois **reinicie a Celula 6**. Custom node so e carregado no boot — reativar
com o servidor no ar nao adianta.

Para usar varios workflows juntos, liste todos: `SELECAO = "2,3,9"`.
Ou `SELECAO = "all"` para ativar tudo (mais lento no boot, porem sem surpresa).

### Conserto manual (uma celula avulsa)

```python
import os
CN='/content/ComfyUI/custom_nodes'
for d in os.listdir(CN):
    if d.endswith('.disabled'):
        os.rename(f'{CN}/{d}', f'{CN}/{d[:-9]}')
        print('reativado', d[:-9])
```

Reativa **todos** de uma vez. Reinicie a Celula 6 depois. Util para destravar
rapido, mas lembre que na proxima Celula 4 eles voltam a ser desativados se nao
estiverem na selecao — isso e o comportamento desejado, nao um bug.

### Regra pratica

> A selecao da Celula 4 e a **fonte da verdade** de quais nodes existem.
> Instalou algo pela UI do Manager? Ou adicione o workflow correspondente a
> selecao, ou nao rode a Celula 4 de novo naquela sessao.

---

# WaifuSurvivors_Assets.json — 3 saidas do mesmo personagem

Para projetos de **jogo**, onde a mesma personagem precisa existir em contextos
visuais diferentes. Um unico grafo produz:

| Saida | Resolucao | Uso |
|---|---|---|
| **SPLASH** | 832x1216 | menu, tela de selecao, gacha |
| **PORTRAIT** | 1024x1024 | HUD, card, dialogo |
| **CHIBI** | 1024x1024 | sprite de gameplay, **com fundo removido** |

Custom node: apenas `ComfyUI-Inspyrenet-Rembg` (ramo chibi). Todo o resto e
nativo.

## A regra de ouro: identidade separada de estilo

A **identidade** fica so no no 3. Os nos de estilo dizem apenas **como**
desenhar — nunca **quem**. Cada ramo faz `ConditioningConcat(identidade, estilo)`.

Isso importa porque um jogo tem varios personagens. Com essa separacao, trocar
de personagem e editar **um** campo; os tres estilos acompanham. Se voce
escrevesse "chibi + identidade" num prompt so, cada personagem novo exigiria
reescrever os tres.

## Consistencia entre as tres saidas

Aqui esta a parte dificil, e vale ser direto: **prompt sozinho nao garante que
os tres sejam a mesma pessoa.** Para um jogo — onde o jogador ve o splash e o
chibi lado a lado — isso e visivel e incomoda.

Para producao real, uma **LoRA por personagem** (no 2) deixa de ser luxo e vira
requisito. O ramo **chibi** e o que mais diverge, porque chibi e o estilo mais
distante do que o checkpoint viu no treino.

Estrategia recomendada: gere e aprove o **splash** primeiro (e a arte mais
"cara" e a que define a personagem), depois derive portrait e chibi. Se o chibi
teimar em nao parecer, use o splash como referencia via **IPAdapter** — o mesmo
mecanismo do `WaifuVroid_FromConcept`.

## O chibi: nao gere pequeno

Erro comum: pedir 128x128 porque o sprite e pequeno. **Difusao em resolucao
baixa produz papa** — o modelo nao foi treinado nessa escala.

Gere em **1024** e reduza depois: na engine, ou num passo separado. Para pixel
art, reduza com filtro **NEAREST** (nunca bilinear/lanczos) — e o que preserva
a borda dura.

O ramo chibi ja sai com **canal alpha** via `InspyrenetRembg`, pronto para
importar na engine. Nao quer isso? Delete o no e ligue o `VAEDecode` direto no
`SaveImage`.

## Sobre "2 heads tall"

O prompt do chibi pede proporcao de 2 cabecas. Modelos anime entendem `chibi` e
`super deformed` bem, mas a proporcao exata varia. Se sair inconsistente entre
personagens — o que quebra a leitura no jogo — as saidas sao: LoRA de estilo
chibi (treinada em chibis, nao em personagem), ou padronizar via img2img a
partir de um chibi aprovado.

---

# Waifu Survivors — pipeline de assets (Godot)

Decisoes do projeto: **Godot**, chibi **anime** (nao pixel art), animacao
**walk/attack/death** com flip horizontal, **~5 personagens**.

Tres pecas:

| Arquivo | O que faz |
|---|---|
| `Workflows/WaifuSurvivors_Assets.json` | splash + portrait + chibi (1 pose) |
| `Workflows/WaifuSurvivors_ChibiPoses.json` | as **5 poses** chibi, mesma seed |
| `scripts/batch_survivors.py` | gera **tudo, para todos**, pela API |

Custom node: so `ComfyUI-Inspyrenet-Rembg` (fundo transparente do chibi).

## O limite que define o design da animacao

**Difusao nao faz animacao frame-a-frame consistente.** Cada imagem e gerada do
zero: cabelo, dobra da saia e dedos mudam entre frames. Em 2 frames alternados
quase nao se percebe; em 8, o sprite "ferve".

Por isso a recomendacao para um Vampire Survivors-like:

- **walk** = 2 frames (`walk_a` / `walk_b`) alternando;
- **death** = 1 frame + tween de rotacao/fade no Godot;
- **attack** = muitas vezes dispensavel — em bullet heaven o efeito visual e do
  **projetil**, nao do corpo;
- o resto = **animacao procedural** no Godot: squash & stretch, bob vertical,
  leve rotacao, flash branco ao tomar dano.

Isso e o que a maioria dos jogos do genero faz. Sprite pequeno em movimento
rapido: ninguem percebe, e economiza a maior parte do trabalho.

Flip: gere so `facing right` e use `flip_h` no Godot.

## Resolucao

Gere em **1024** e reduza no Godot. Nunca gere em 128 — difusao em resolucao
baixa vira papa. No import do Godot, `Filter: Nearest` se quiser borda dura.

## Automacao: `scripts/batch_survivors.py`

Nao depende de workflow salvo — monta o grafo em formato API na hora. Trocar o
elenco e editar um JSON.

```bash
cp scripts/roster.example.json scripts/roster.json   # e edite

python scripts/batch_survivors.py --roster scripts/roster.json --dry-run
python scripts/batch_survivors.py --roster scripts/roster.json
python scripts/batch_survivors.py --only lia --kinds chibi
```

No Colab, com o servidor da Celula 6 no ar, numa celula nova:

```python
!python /content/ComfyUI_Colab/scripts/batch_survivors.py \
        --roster /content/ComfyUI_Colab/scripts/roster.json
```

Cada personagem rende **7 imagens** (splash, portrait, 5 poses). Cinco
personagens = 35 imagens numa tacada. O script respeita a fila
(`--max-pending`) para nao afogar o ComfyUI.

Saida: `output/survivors/<personagem>/<tipo>_<pose>_00001_.png`.

O `roster.json` tem `defaults` (checkpoint, negative, cfg) e uma lista de
`characters`, cada um com `id`, `identity`, `lora` e `seed`. Testado com
servidor simulado: 14 jobs, zero falhas, todas as referencias entre nos validas.

## Consistencia entre splash, portrait e chibi

Este e **o** problema do projeto, e prompt nao resolve. Com 5 personagens e o
jogador vendo splash e chibi lado a lado, divergencia fica obvia.

Caminho recomendado, por personagem:

1. Gere e **aprove o splash** — e a arte que define a personagem.
2. Produza ~25 imagens variadas a partir dele
   (`WaifuVroid_FromConcept` com IPAdapter + `Detailer`).
3. **Treine uma LoRA** (ver o guia de treino).
4. Preencha `lora` no `roster.json` e rode o batch.

Com LoRA, os tres estilos passam a ser a mesma pessoa. Sem ela, o **chibi** e o
que mais diverge — e o estilo mais distante do treino do checkpoint.

Para 5 personagens sao 5 LoRAs. Parece muito, mas e o unico jeito de ter
identidade estavel — e depois voce gera quantas variacoes quiser de graca.

## Estilo chibi consistente entre personagens

Cuidado separado: cada personagem pode sair com uma proporcao chibi diferente,
o que quebra a leitura no jogo. Duas saidas: treinar uma **LoRA de estilo
chibi** (treinada em chibis, nao em personagem) e aplica-la junto da LoRA do
personagem; ou padronizar via img2img a partir de um chibi aprovado.

---

## WaifuSurvivors_Concept.json — a fase ANTES da splash oficial

Explorar barato. Nao e arte final, e rascunho: **4 variacoes por Run**, 20 steps,
768x1152 (~1 min no T4). A splash oficial usa 30 steps em 832x1216 — 3x mais
caro. Nao gaste isso enquanto ainda esta decidindo como a personagem e.

Zero custom nodes.

**A diferenca de mentalidade:** nos outros workflows a identidade e fixa e voce
varia o angulo. Aqui e o oposto — a **seed e `randomize`** e o prompt e solto,
de proposito. Voce nao esta reproduzindo um personagem, esta **descobrindo** um.

### Ciclo

1. No no 2, escreva solto, com lacunas:
   `1girl, solo, full body, knight girl, silver armor, red cape`
   O modelo preenche os buracos e te da ideias que voce nao teve.
2. **Run** → saem 4. Nao gostou? Run de novo.
3. Repita ate algo te fazer parar.
4. Anote a **seed** e o **prompt** da imagem boa.
5. Leve para o `WaifuSurvivors_Assets` (no 3 + seed nos KSamplers) e gere em
   qualidade cheia.

Varie **uma** coisa por vez: cabelo, roupa, paleta, vibe. As combinacoes que
funcionarem viram o seu elenco.

### O criterio que importa num bullet heaven

O jogador ve o sprite **pequeno**. O que le em miniatura e a **silhueta** e a
**cor dominante** — nao o detalhe.

Teste pratico: aperte os olhos olhando as 4 imagens. Ainda da para distinguir as
personagens? Se viram todas o mesmo borrao, o elenco esta fraco. Varie
**silhueta e paleta**, nao acessorio.

Isso vale mais para o seu projeto do que qualquer ajuste de sampler: cinco
personagens que se parecem em miniatura sao cinco personagens que o jogador nao
vai diferenciar durante a partida.

### Ordem dos workflows no projeto

```
WaifuSurvivors_Concept     -> explorar, descobrir o elenco  (rapido, 4 por vez)
        |  escolheu? anote seed + prompt
WaifuSurvivors_Assets      -> splash + portrait + chibi     (qualidade cheia)
        |  chibi ficou bom?
WaifuSurvivors_ChibiPoses  -> as 5 poses de animacao
        |  varios personagens?
scripts/batch_survivors.py -> tudo, para todos, de uma vez
```

---

## UI trava na tela "Comfy" por muito tempo / precisa recarregar a pagina

O log de boot engana: `Starting server` aparece em segundos, mas a tela preta com
a logo continua. **O servidor esta pronto — quem esta lenta e a UI.**

**Causa: `--user-directory` apontando para o Drive.**

Ao abrir, o frontend faz dezenas de requisicoes pequenas em `user/`: settings,
lista de workflows, layout, templates e o cache do Manager. Cada leitura no Drive
passa por FUSE e custa ~100 ms. Trinta arquivos = alguns segundos so de espera,
as vezes com timeout — e dai a necessidade de recarregar.

E o mesmo motivo pelo qual o ComfyUI nao roda dentro do Drive. Faltava aplicar a
regra ao `user/`.

**Correcao (v17):** o `user/` passa a viver em `/content/comfy_user` (disco
local, rapido) e e **espelhado no Drive a cada 2 minutos** por uma thread.

- No boot, a Celula 6 copia `user/` do Drive para o local.
- Durante a sessao, tudo e lido/escrito local — UI abre rapido.
- A cada 2 min, o conteudo volta para o Drive.
- A Celula 4 grava os workflows nos **dois** lugares.

Para forcar o backup antes de encerrar a sessao, rode numa celula:

```python
salvar_agora()
```

Nao e obrigatorio (a thread ja salva sozinha), mas garante que os ultimos
minutos nao se percam se voce fechar o Colab logo apos salvar um workflow.

### Outras causas possiveis

- **Cloudflare frio**: o primeiro acesso ao tunel demora alguns segundos. Se a
  pagina ficar em branco *antes* de aparecer a logo, e o tunel, nao a UI.
- **rgthree "Nodes 2.0"**: deixa a UI lenta em workflows grandes.
  *Settings > Lite Graph > Nodes 2.0* > desligar.
- **Muitos workflows na aba**: a UI lista todos no boot. A Celula 4 so copia os
  selecionados, mas o que voce salvou pela UI fica la para sempre.

---

## A UI continua demorando (mesmo com user/ local) — como DIAGNOSTICAR

A Celula 6 **bloqueia** (o `main.py` roda em primeiro plano), entao nao da para
rodar uma celula de diagnostico depois dela. Por isso a medicao virou uma
**thread dentro da propria Celula 6** (v18).

Ela espera o servidor subir e, alguns segundos depois, imprime no meio do mesmo
log:

```
==================================================================
  DIAGNOSTICO DA UI (medido no localhost, sem o tunel)
==================================================================
  /system_stats                     0.05s        1 KB
  /queue                            0.01s        0 KB
  /api/userdata?dir=workflows       0.02s        2 KB
  /embeddings                       0.01s        0 KB
  /object_info                     12.40s     3200 KB   <<< LENTO
  TOTAL                            12.49s
==================================================================
```

Como as medidas sao feitas em `127.0.0.1`, elas **excluem o tunel**. Isso separa
as duas causas possiveis:

**Caso A — nenhum endpoint lento, total < 5 s.**
O servidor esta rapido; o gargalo e o **tunel** ou o navegador. O `cloudflared`
gratuito as vezes pega um edge ruim.
1. **Proxy de portas do Colab** — chave inglesa no painel esquerdo > *Portas* >
   `8188` > abrir. Nao passa pela internet publica; costuma ser o mais rapido.
2. Reinicie a Celula 6 para sortear outro tunel (a URL muda).
3. Troque `TUNEL` para `ngrok`.

**Caso B — algum endpoint marcado LENTO.**
O gargalo e o servidor. O suspeito e quase sempre **`/object_info`**: ele monta a
lista de todos os nos e, para cada loader, **varre as pastas de modelos**. Com os
modelos no Drive, cada varredura passa por FUSE. A UI nao desenha nada ate essa
resposta chegar — e a tela da logo parada.

Mitigacoes:
- Menos custom nodes ativos: cada pack acrescenta nos ao `/object_info`.
  Use a **menor selecao possivel** na Celula 4.
- Limpe arquivos soltos das pastas de modelo (`.part`, duplicatas).
- Tire da pasta os modelos gigantes que o workflow atual nao usa.

### Observacao do log da 2a sessao

Apareceu `one-node-flux-2-klein` entre os custom nodes e o banco rodou 6
migracoes (`0001_assets` -> `0006_add_loader_path`). As migracoes acontecem uma
vez so, apos atualizacao do ComfyUI — explicam aquele boot especifico, nao a
lentidao recorrente.

---

## Bugs da Celula 4 corrigidos na v19

Dois problemas apareceram juntos neste log:

```
desativado one-node-flux-2-klein.disabled
Workflows na UI: ['CharDesignandPartSplitting.json', 'WaifuSurvivors_Concept.json']
Ativos: ['ComfyUI-Manager', '__pycache__']
```

### 1. `.disabled.disabled`

O laco que desativa packs nao verificava se a pasta **ja** terminava em
`.disabled`. Resultado: `one-node-flux-2-klein.disabled` virava
`one-node-flux-2-klein.disabled.disabled` a cada execucao da celula.

O pack nunca mais seria reativado: a Celula 4 procura por `<pack>.disabled`
exatamente, e o Manager tambem nao o encontra. Ficaria como "no ausente" para
sempre.

Corrigido: pastas ja desativadas sao ignoradas, e ha uma limpeza que renomeia
nomes acumulados de volta ao formato certo.

### 2. Workflow nao chegava no diretorio local

Com a v17 (user/ local), a Celula 4 escrevia nos dois diretorios — **mas** o
teste "ja existe e e igual" olhava so o do Drive. Se o arquivo ja estivesse la,
ela imprimia `= (ja estava la)` e **pulava a copia para o local**, que e de onde
a Celula 6 serve. O workflow nao aparecia na aba.

Corrigido: cada diretorio e verificado e copiado independentemente.

### 3. `__pycache__` listado como "Ativo"

Cosmetico: `__pycache__` nao e custom node. Removido da listagem.

### Sobre "workflows a mais na aba"

O log mostrava `CharDesignandPartSplitting.json` mesmo com a selecao `10`. Isso
**nao e bug**: a celula copia os selecionados, mas **nunca apaga** o que ja
estava la. Workflows de sessoes anteriores permanecem — inclusive os que voce
salvou pela UI. Agora a mensagem diz isso explicitamente.

Se quiser limpar, apague pela aba Workflows da propria UI.

---

## Veredito: a lentidao era o TUNEL (v20)

O autodiagnostico da v18 fechou a questao:

```
  /system_stats                     0.00s         1 KB
  /queue                            0.00s         0 KB
  /api/userdata?dir=workflows       0.00s         0 KB
  /embeddings                       0.00s         0 KB
  /object_info                      0.20s      1702 KB
  TOTAL                             0.20s
```

**0,20 s no total** — o servidor responde instantaneamente, inclusive o
`/object_info` (1,7 MB em 200 ms). Os minutos de tela preta eram inteiramente do
**cloudflared**.

Por que isso acontece: o `trycloudflare.com` e um tunel gratuito e anonimo. O
trafego sai do Colab, atravessa a rede da Cloudflare, chega ao seu browser no
Brasil e volta. O edge sorteado varia a cada execucao — as vezes bom, as vezes
pessimo. A UI do ComfyUI baixa varios MB de JS no primeiro acesso; num edge ruim
isso leva minutos ou estoura o timeout (dai o "recarregar resolve").

### Solucao: `TUNEL = 'colab'` (novo padrao)

O Colab tem um **proxy interno** (`google.colab.kernel.proxyPort`). O trafego vai
pela mesma conexao autenticada do notebook, sem passar por terceiros. E o
caminho mais curto e mais rapido.

A Celula 6 agora imprime esse link automaticamente. Alternativa manual, a
qualquer momento: **chave inglesa no painel esquerdo > Portas > 8188 > abrir**.

Limitacao: o link so funciona **para voce, nesse navegador**, enquanto a sessao
estiver viva. Nao da para compartilhar nem abrir no celular.

Quando ainda usar os outros:
- `cloudflared` — precisa de link publico (mostrar para alguem, abrir no
  celular). Se estiver lento, reinicie a Celula 6 para sortear outro edge.
- `ngrok` — mesma finalidade, com conta; costuma ser mais estavel que o
  cloudflared gratuito.

### Nota sobre as migracoes do banco

O log mostrou de novo `Running upgrade 0001_assets -> ... -> 0006_add_loader_path`.
Elas rodam a cada sessao porque o banco (`comfyui.db`) fica no `user/`, que e
recriado. Sao rapidas (menos de 1 s) e nao tem relacao com a lentidao da UI.

---

## Logo / marca d'agua nas imagens

Aparece porque o modelo aprendeu isso do dataset: muita arte de anime na
internet tem assinatura do artista, logo de site ou moldura de "character card".
O modelo nao sabe que aquilo nao faz parte do desenho — para ele e so mais um
padrao visual que costuma acompanhar personagens.

Frequencia tipica: **1 em cada 10 a 20 imagens**. Nao e defeito da sua
configuracao.

Todos os workflows `Waifu*` ganharam estes termos no negative:

```
logo, watermark, signature, artist name, username, web address,
text, english text, japanese text, letters, title, caption,
character sheet, reference sheet, border, frame, inset,
speech bubble, patreon logo, twitter username
```

Isso reduz bastante, mas **nao zera**. Quando escapar, simplesmente descarte a
imagem — na fase de concept voce gera muitas e fica com poucas, entao perder
uma nao custa nada.

Se aparecer com muita insistencia, o checkpoint provavelmente tem isso
"assado". Alternativas: trocar de checkpoint, ou cortar a regiao da logo
(elas quase sempre ficam num canto) e usar o `WaifuInpaintXL` para preencher.

**Nao gaste tempo salvando uma imagem com logo na fase de concept.** Consertar
custa mais do que gerar outra.

---

## Workflow aparece na aba mas nao abre (v21)

**Causa: o campo `id` do JSON.**

Comparando um workflow exportado pelo ComfyUI com os que eu gerei por script:

```
WaifuInpaintXL.json           id='49b62f18-6a99-41b9-81cf-4eadb1b9e819'   <- UUID
WaifuSurvivors_Concept.json   id='survivors-concept'                      <- string livre
```

Todo workflow salvo pela UI recebe um **UUID**. A aba Workflows indexa os
arquivos por esse campo; com um id em formato diferente, o item ate aparece na
lista, mas ao clicar nao carrega. Por isso funcionava ao arrastar o arquivo
manualmente — esse caminho nao passa pelo indice.

Corrigido nos 5 workflows criados aqui. O UUID e **derivado do nome do arquivo**
(`uuid5`), entao e sempre o mesmo — o mesmo workflow nao vira duas entradas.

Tambem preenchi `extra.ds` (zoom/offset iniciais), que os workflows reais tem e
os meus estavam com `{}`.

A Celula 4 agora **valida e conserta** o `id` de todo workflow nos diretorios da
UI, inclusive os que ja estavam la. Ids que ja sao UUID sao preservados.

### Segunda causa: cache do frontend

Mesmo com o JSON correto, copiar arquivos **com o servidor no ar** nao atualiza a
lista: a aba e carregada uma vez no boot. Depois de rodar a Celula 4, sempre:

1. **F5 na aba do ComfyUI** — resolve na maioria das vezes;
2. se nao, reinicie a **Celula 6**.

Ordem correta e sempre: Celula 4 -> Celula 5 -> Celula 6 -> abrir a UI.

---

## Recomendacoes oficiais do WAI-illustrious-SDXL (aplicadas na v22)

A pagina do Civitai exige login, mas o mesmo card do autor esta espelhado em
tensor.art, Shakker, Moescape e Tungsten. Consolidado:

| Parametro | Recomendado pelo autor | O que eu tinha |
|---|---|---|
| Sampler | **Euler a** (`euler_ancestral`) | `dpmpp_2m` / karras |
| CFG | **5 – 7** | 4.5 |
| Steps | **15 – 30** | 20 – 30 (ok) |
| Resolucao | **maior que 1024x1024** | ok |
| VAE | **ja embutido** — nao carregar externo | ok |
| Positive | `masterpiece, best quality, amazing quality` | tinha tags demais |
| Negative | `bad quality, worst quality, worst detail, sketch, censor` | **longo demais** |

### O aviso mais importante (e contraintuitivo)

> *"Please do not add too many quality and aesthetic-related tags, nor overly
> long negative prompts, as this will actually reduce image quality and make it
> more blurry."*

**Negative longo PIORA a imagem neste modelo.** Eu vinha empilhando termos —
anti-queimado, anti-logo, anti-pose — e isso estava contra a recomendacao do
autor. O negative foi enxugado para ~120 caracteres.

Isso muda a estrategia contra a logo: em vez de empilhar
`artist name, username, web address, patreon logo, twitter username...`,
ficam so `watermark, signature, logo, text`. Vai escapar uma logo de vez em
quando — descarte e siga.

### Mudancas aplicadas em todos os `Waifu*`

- Sampler → **`euler_ancestral`** + scheduler `normal`
- CFG → **5.5** (era 4.5; a faixa do autor comeca em 5)
- Negative → curto, base do autor + 4 termos anti-logo
- Positive → removidos `very aesthetic`, `absurdres`, `highly detailed`,
  `intricate details`, `newest`; ficou `masterpiece, best quality, amazing quality`

### Duas dicas especificas que valem guardar

- **Pontinhos brancos** na imagem → adicione ao negative:
  `lens flare, particles, dust`
- **Pupilas ficam vermelhas** sem motivo → adicione: `heart pupil`

### Filtro de conteudo

O modelo tem quatro tags de classificacao: `general`, `sensitive`, `nsfw`,
`explicit`. O autor recomenda por **`nsfw` no negative** para evitar saidas
inadequadas — ja incluido em todos os workflows. Para um jogo, mantenha.

### Hires fix (quando for gerar a arte final)

Upscale 1.5x, 20 steps, upscaler **R-ESRGAN 4x+ Anime6B**, denoise 0.35–0.5.
No ComfyUI, o equivalente e `UpscaleModelLoader` + `ImageUpscaleWithModel`, ou
um segundo KSampler com denoise 0.4. Nao adicionei — na fase de concept e
desperdicio.

---

## Teor ecchi: menu sim, gameplay nao (v23)

O WAI tem **quatro niveis de rating**, e a escolha do nivel e o controle
principal:

| Tag | Teor | Onde usar |
|---|---|---|
| `general` | limpo | — |
| **`sensitive`** | **sugestivo, ecchi** | **splash, portrait** |
| `nsfw` | nudez parcial / forte | (nao usado) |
| `explicit` | explicito | **no negative** |

Configuracao aplicada:

- **SPLASH / PORTRAIT** → `sensitive, alluring pose, attractive` no positive,
  `explicit` no negative. Sugestivo sem virar hentai.
- **CHIBI** → deixado **limpo de proposito**. Um sprite de 64 px nao tem
  resolucao para fanservice; tentar isso so suja a silhueta e piora a leitura
  durante a partida.

E exatamente o padrao do genero: Azur Lane, Nikke e Genshin colocam fanservice
na arte de menu e mantem o gameplay legivel.

Antes eu tinha posto `nsfw` no negative de tudo, seguindo a recomendacao
generica do autor do modelo — o que bloqueava justamente o teor desejado.
Removido de splash/portrait.

### Subir ou baixar o teor

No no de estilo **SPLASH** (ou em `STYLES` do `batch_survivors.py`):

| Nivel | Positive | Negative |
|---|---|---|
| Recatado | (nada) | `sensitive, explicit` |
| **Leve (atual)** | `sensitive, alluring pose` | `explicit` |
| Medio | `+ cleavage, thighs, bare shoulders, skindentation` | `explicit` |
| Pesado | `nsfw` | (remover `explicit`) |

Para uma personagem especifica mais recatada, basta dar a ela um `negative`
proprio no `roster.json` incluindo `sensitive`.

### Distribuicao — vale saber antes de fechar o teor

- **Steam**: aceita conteudo adulto, com aviso e build separada.
- **Consoles** (Nintendo/PlayStation/Xbox) e **app stores**: bem mais
  restritivos.
- **`sensitive`** passa praticamente em qualquer lugar; **`explicit`** nao.

Se quiser os dois, gere versao SFW e ecchi da **mesma** personagem com a **mesma
seed** — muda so o texto de estilo — e troque os assets por build. Fica barato
porque a identidade nao muda.

### Nota sobre LoRA de personagem

Quando treinar as LoRAs, o **dataset define o teor**. Se todas as imagens forem
ecchi, a LoRA vai puxar para isso mesmo quando voce pedir algo limpo — inclusive
no chibi. Misture: cerca de 70% neutras, 30% ecchi.

---

## "Nao foi possivel encontrar o fluxo de trabalho em X.json" (v24)

Erro diferente dos anteriores: aqui o frontend **sabe** que o workflow existe
(esta na lista de abas abertas) mas nao acha o arquivo.

**Causa: um efeito colateral da v17.** A Celula 6 copiava o `user/` do Drive
para o local assim:

```python
if not os.path.exists(USER_LOCAL):
    shutil.copytree(DRIVE_USER, USER_LOCAL)
```

Mas a **Celula 4 roda antes** e ja cria `/content/comfy_user/default/workflows`
para gravar os workflows selecionados. Quando a Celula 6 chegava, o diretorio
**ja existia** — e o `copytree` era pulado inteiro.

Consequencia: `comfy.settings.json`, `__manager/` e todos os workflows antigos
**nunca chegavam ao diretorio local**. O frontend lia um `user/` quase vazio,
tentava restaurar as abas abertas da sessao anterior e nao encontrava os
arquivos. Dai a mensagem.

**Correcao:** a copia virou um **merge incondicional**
(`copytree(..., dirs_exist_ok=True)`), mais uma reconciliacao nos dois sentidos
da pasta `workflows/`. A celula agora imprime quantos workflows estao
disponiveis para a UI:

```
Sincronizando user/ do Drive para o disco local... ok
Workflows disponiveis para a UI: 12
```

Se esse numero vier menor do que voce espera, o problema e anterior a UI.

### Destravar sem reiniciar tudo

Se a sessao ja esta no ar e voce nao quer esperar, rode numa celula nova:

```python
import shutil, os
D='/content/drive/MyDrive/ComfyUI_Data/user'; L='/content/comfy_user'
shutil.copytree(D, L, dirs_exist_ok=True)
wl=f'{L}/default/workflows'
print(len([f for f in os.listdir(wl) if f.endswith('.json')]), 'workflows')
```

Depois **F5** na aba do ComfyUI. Nao precisa reiniciar a Celula 6.

### Se a mensagem insistir

O frontend guarda as abas abertas em `comfy.settings.json`. Se ele continuar
tentando reabrir um workflow que nao existe mais, feche a aba pelo X na propria
UI — isso limpa o registro.

---

# WaifuSurvivors_FromConcept.json — a imagem aprovada gera TUDO (v25)

Critica justa ao fluxo anterior: exigir que voce **anote a seed e recopie o
prompt** entre workflows e fragil. Um caractere errado e a personagem muda — e
em producao, com 5 personagens x 7 assets, isso e questao de tempo.

**Este workflow elimina esse passo.** A imagem aprovada e a fonte da verdade.

```
imagem aprovada  ->  [1 Run]  ->  splash + portrait + 5 poses chibi
```

Sao **7 saidas** num unico grafo, todas condicionadas pela mesma imagem via
IPAdapter. Nao ha seed para copiar nem texto de identidade para redigitar,
porque a identidade **nao esta em texto**.

### Como usar

1. Gostou de uma imagem no `WaifuSurvivors_Concept`? Botao direito >
   **Save Image**.
2. Suba o arquivo para `ComfyUI_Data/input/` (ou arraste no proprio no 2).
3. Selecione no **no 2** e clique em **Run**.

So isso. As poses chibi ja saem com **alpha**, prontas para o Godot.

### O unico ajuste: weight do no 4

| Weight | Efeito |
|---|---|
| 0.5 | mais liberdade criativa |
| **0.7** | padrao |
| 0.9 | copia agressiva |

- Chibi saiu igual ao concept, sem virar chibi? **Abaixe** para 0.5.
- Chibi nao parece o personagem? **Suba** para 0.85.

Splash e chibi podem querer weights diferentes — se precisar, rode duas vezes.

### Seeds em `randomize`, de proposito

Nao gostou de **um** asset? Rode de novo: so ele muda, a identidade continua
vindo da imagem. Voce nao perde os outros seis.

### Producao: o mesmo no batch

O `batch_survivors.py` ganhou o campo **`concept`** no roster:

```json
{
  "id": "lia",
  "concept": "lia_concept.png",
  "ipadapter_weight": 0.7
}
```

Com `concept` preenchido, o script injeta `LoadImage` + IPAdapter em **todos** os
7 jobs daquele personagem. Sem ele, cai no modo texto (`identity`) — que
continua funcionando para quem ainda nao tem imagem aprovada.

O script valida na entrada: personagem sem `concept` **e** sem `identity` para a
execucao com mensagem clara. E o log diz o modo de cada um:

```
Personagens: {'lia': 'imagem', 'exemplo2': 'texto'}
```

Testado contra servidor simulado: 14 jobs, todas as referencias entre nos
validas, IPAdapter presente so em quem tem `concept`.

### Fluxo de producao recomendado

```
1. WaifuSurvivors_Concept          -> explorar, 4 por Run (rapido)
2. salvar as imagens aprovadas em ComfyUI_Data/input/
3. WaifuSurvivors_FromConcept      -> 7 assets por personagem
   ou scripts/batch_survivors.py   -> 5 personagens de uma vez
4. (opcional) treinar LoRA -> consistencia definitiva
```

Os workflows `Assets` e `ChibiPoses` continuam no repo para quem quiser
controle manual, mas **o caminho recomendado agora e o `FromConcept`**.

## v26 — abas travadas e "Nao foi possivel encontrar o fluxo de trabalho"

Sintomas relatados: alerta apontando `WaifuSurvivors_FromConcept.json`, **so um
workflow abre por vez** e **clicar nas abas de cima nao faz nada**.

### Nao era o arquivo

Comparei a estrutura dos workflows gerados por script com os do tutorial (que
abrem normal): mesmas chaves de nó (`id/type/pos/size/order/flags/mode/inputs/
outputs/properties/widgets_values`), `links` no formato de 6 posições, todo
`output` com `links`, `id` UUID válido, sem duplicados. Estruturalmente idênticos.

### Era o estado de abas do frontend

O ComfyUI guarda em `user/default/comfy.settings.json`:

- `Comfy.Workflow.OpenWorkflows` — as abas abertas na sessao anterior
- `Comfy.Workflow.ActiveIndex` — qual estava ativa
- `Comfy.PreviousWorkflow`

Se **uma** entrada aponta para arquivo que nao existe mais (renomeado, workflow
de outra sessao, `.disabled`, Drive fora de sincronia), a restauracao do tabbar
**aborta no meio**: a primeira aba abre, as demais viram entradas mortas e os
cliques nao respondem. O alerta cita o primeiro nome que falhou — por isso
apareceu o `FromConcept`, que era so a vitima visivel.

`ActiveIndex` apontando para um indice que nao existe mais na lista produz o
mesmo travamento.

### Correcao (C6, `v26-tabfix`)

No boot, depois do merge do `user/`, roda `_sanear_settings()` nos dois lados
(local e Drive):

1. remove de `OpenWorkflows` toda referencia sem arquivo correspondente;
2. reajusta `ActiveIndex` para um indice valido (`-1` se nao sobrou nada);
3. descarta `PreviousWorkflow` morto;
4. forca `WorkflowTabsPosition = Topbar` (sem isso as abas ficam so na sidebar);
5. se o JSON estiver corrompido, salva `.bak` e zera — settings quebrado trava
   a UI inteira.

Idempotente: rodar de novo num settings limpo nao altera nada.

### Destrave imediato (sem reiniciar a C6)

Cole numa celula nova, rode, e **F5** na aba do ComfyUI:

```python
import json, os
L = '/content/comfy_user/default'
p = f'{L}/comfy.settings.json'
st = json.load(open(p)) if os.path.exists(p) else {}
existe = set(os.listdir(f'{L}/workflows'))
ok = lambda w: isinstance(w, str) and os.path.basename(w) in existe
st['Comfy.Workflow.OpenWorkflows'] = [w for w in st.get('Comfy.Workflow.OpenWorkflows', []) if ok(w)]
st['Comfy.Workflow.ActiveIndex'] = 0 if st['Comfy.Workflow.OpenWorkflows'] else -1
st.pop('Comfy.PreviousWorkflow', None)
st['Comfy.Workflow.WorkflowTabsPosition'] = 'Topbar'
json.dump(st, open(p, 'w'), indent=2)
print('abas:', st['Comfy.Workflow.OpenWorkflows'])
```

### Regra

Estado de UI que referencia arquivos **sempre** tem de ser reconciliado com o
disco no boot. Nunca confiar que o que o frontend salvou continua existindo —
a C4 troca os workflows disponiveis a cada sessao.

## v27 — por que o Concept sai melhor que o resto (imagens neon/queimadas)

Sintoma: as saidas do `Concept` sao limpas e bonitas; splash e chibis saem
**neon, queimados, com cores saturadas irreais** e ate cabeca duplicada.
Nao era CFG (o usuario ja tinha baixado para 5).

### Causa: o Concept nao usa IPAdapter, o resto usa

Comparando os grafos, o `Concept` e um pipeline nu:
`Checkpoint -> CLIPTextEncode -> KSampler`. Nada entre o modelo e o sampler.

Nos outros, o `model` do KSampler vem do `IPAdapterAdvanced`, que estava com
`embeds_scaling = "V only"`. O proprio autor do pack (cubiq, NODES.md) diz que
`K+mean(V) w/ C penalty` e o modo que "grants good quality at high weights
without burning the image" — ou seja, **`V only` queima**. Com peso 0.7 em
Illustrious (modelo ja saturado) o resultado e exatamente o neon visto.

Somando: `V only` + `end_at 1.0` (IPAdapter agindo ate o ultimo passo, sem
deixar o modelo resolver cor/contraste no final) + prompts sem ancora de
coloracao = imagem torrada.

### Correcoes aplicadas

1. **`embeds_scaling` -> `K+mean(V) w/ C penalty`** nos dois IPAdapters.
2. **`end_at` < 1.0**: 0.9 em splash/portrait, 0.7 no chibi. Os passos finais
   voltam a ser do checkpoint, que e quem sabe fechar a imagem.
3. **IPAdapter separado para o chibi** (novo no 50, weight **0.45**). Com 0.7 a
   referencia realista impedia a deformacao chibi — o sprite saia com corpo
   longo e proporcao de adulto. Splash/portrait seguem em 0.7 no no 4.
4. **Negative anti-neon** em todos: `oversaturated, neon colors, glowing skin,
   rim lighting, chromatic aberration, harsh shadows, high contrast,
   extra head, duplicate, blurry`.
5. **Negative dedicado do chibi** (no 51): + `realistic, detailed background,
   long body, adult proportions`.
6. **Prompts alinhados ao Concept**: adotado `flat anime coloring, soft lighting`
   e a mesma estrutura que ja estava funcionando. O `sensitive/attractive` do
   splash foi mantido; do chibi continua fora.

### Regra

Quando um workflow sai melhor que outro, **comparar os grafos antes de mexer em
CFG**. Aqui a variavel nao era parametro de sampler, era um no a mais no caminho
do `model`. `V only` e o default do node e e a pior escolha para Illustrious.

## v28 — pipeline de animacao a partir de video (metodo do DevDude)

Referencia: https://youtu.be/tU2Q99plP1Q (DevDude, "AI Spritesheet Creation
Workflow", 8min44).

### O que ele faz

1. concept art da personagem de lado;
2. coloca num **green screen solido** (usa Nano Banana 2 para isso);
3. gera **clipes de 1 segundo** com a imagem como referencia (Grok Imagine);
4. extrai **todo frame** do video -> spritesheet;
5. remove o green screen (modelo Corridor Key);
6. um analisador acha o loop e alinha os frames.

**A ideia central resolve o nosso problema real.** Hoje as 5 poses chibi sao 5
geracoes independentes: nada garante que walk_a e walk_b sejam a mesma
personagem. Vindo do MESMO video, a consistencia e estrutural.

Duas sacadas dele que valem por si:
- **1 segundo.** Clipe longo "o modelo se confunde e inventa coisa que voce nao
  quer". 1-2s para walk/attack, 3s para idle (tempo do cabelo ao vento).
- **Canvas landscape para ataque.** Quadrado nao da espaco para braco/espada —
  ele mesmo errou isso no video.

### O que NAO da para copiar

Ele nao usa ComfyUI. E o **Sorceress Game Suite**, produto pago dele proprio, e
a geracao de video e **Grok Imagine na nuvem**. Nao existe workflow JSON.

Portar para WAN 2.2 local **nao cabe no T4**, e o limite nao e VRAM: o 14B em
GGUF depende de descarregar o text encoder (~9 GB) para a RAM de CPU, e as
fontes convergem em **24-32 GB de RAM de sistema**. Temos **12.976 MB** — o
mesmo teto que ja barrou o `Mesh_Processing`. Estimativa: 10-15 min por clipe
de 1s com risco alto de OOM. Inviavel para iterar 5 personagens.

### O que foi entregue

Metade do fluxo — a que roda no T4 — mais um substituto melhor para o chroma key.

**`Workflows/WaifuSurvivors_VideoToSprites.json`** (6 nos):
`VHS_LoadVideo -> InspyrenetRembg -> ImageScale -> SaveImage`.
O clipe entra, os frames saem ja com alpha em `output/survivors_frames/`.

**Dispensa o green screen.** O Inspyrenet segmenta direto e nao deixa o
"green edge spillage" que ele mesmo reclama do chroma classico. Um passo a
menos que no fluxo original.

**`scripts/make_spritesheet.py`** faz o que o Sprite Analyzer dele cobra:
- descarta frames-lixo de inicio/fim (comparacao com a mediana do clipe);
- **alinha pelo centro de massa** — mata o "jitter back" que ele conserta na mao;
- acha o loop por ritmo: a emenda boa nao e a de frames iguais (isso premiaria
  dois frames-lixo identicos), e a que mantem a MESMA distancia de um passo
  normal entre o ultimo e o primeiro;
- monta o PNG + JSON + instrucoes do Godot.

Testado com 16 frames sinteticos com deriva de 3px/frame e 4 frames-lixo:
descartou os 4, achou loop de 8 frames, caixa final 57x181.

Dois bugs pegos no teste, ambos corrigidos:
- o script lia o proprio `_sheet.png` da rodada anterior como frame;
- **alinhar tem de vir ANTES de recortar** — com a ordem invertida a caixa de
  uniao somava a deriva e dava 1968px de largura em vez de 57.

### Como usar

1. gere o clipe de 1s onde preferir (Grok Imagine, Kling, Sora), usando a
   splash/concept aprovada como referencia;
2. salve o `.mp4` em `ComfyUI_Data/input/`;
3. rode o `VideoToSprites`;
4. `python scripts/make_spritesheet.py output/survivors_frames --nome walk`;
5. no Godot: `AnimatedSprite2D -> SpriteFrames -> Add frames from sheet`.

Gere so o lado direito e use `flip_h`, como ja combinado.

## v29 — consolidacao dos workflows + animacao local

### Removidos

`WaifuSurvivors_Assets.json`, `WaifuSurvivors_ChibiPoses.json` e
`WaifuSurvivors_FromConcept.json` foram **apagados**. Faziam trabalho repetido
e geravam do zero coisas que dava para derivar.

### Nova estrutura (2 workflows + 1 script)

```
Concept  ->  Base  ->  Animate  ->  make_spritesheet.py
                 \-> PORTRAIT por recorte da splash
```

**`WaifuSurvivors_Base.json`** (19 nos) — entrada unica: o concept aprovado.
Um Run entrega **splash + chibi idle**, ambos ancorados na mesma imagem.
Dois IPAdapters: no 4 em **0.7** (splash, fiel) e no 5 em **0.45** (o chibi
precisa de liberdade para deformar).

**PORTRAIT nao se gera: recorta-se da splash.** A identidade fica identica por
construcao — mesmo cabelo, mesmos olhos, mesmo traco. Gerar de novo so cria
chance de divergir. Excecao: se o portrait precisar de **expressao diferente**
(brava, sorrindo, para dialogo), ai sim vale gerar mudando o no 6.

**`WaifuSurvivors_Animate.json`** (17 nos) — AnimateDiff sobre o chibi idle.

### Por que AnimateDiff e nao WAN

O gargalo desta maquina e **RAM de CPU (~13 GB)**, nao VRAM (14,9 GB). Por isso
"trocar por modelo menor" resolve pouco: mesmo o WAN 5B quer 24 GB de RAM,
porque o text encoder T5 (~9 GB) e o decode de video moram la.

O AnimateDiff **anima o checkpoint SDXL que ja temos**. Nao baixa modelo de
video, nao tem T5. Custa ~6 GB de VRAM. E o unico caminho local viavel no T4.

**Ressalva honesta:** o `mm_sdxl_v10_beta` e beta e subtreinado — a propria
comunidade diz que "para ser usavel voce provavelmente precisa treinar voce
mesmo". Para chibi em loop curto costuma bastar; se o movimento sair ruim, o
plano B continua sendo clipe de 1s na nuvem + `VideoToSprites`.

### Flags de memoria (C6, `v29-anim`)

`ECONOMIZAR_RAM = True` adiciona:
- `--cache-none` — descarrega cada modelo apos o uso (o mais citado para RAM)
- `--disable-smart-memory` — nao segura modelo na memoria por precaucao
- `--mmap-torch-files` — le o peso do disco em vez de copiar para a RAM

**Diagnostico:** processo que **morre/trava sem mensagem** = falta de RAM.
Erro **CUDA/torch out of memory** = falta de VRAM. No T4 sera quase sempre o
primeiro.

### Downloads necessarios

| arquivo | pasta | tamanho | para |
|---|---|---|---|
| `CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors` | `clip_vision` | 2,53 GB | Base + Animate |
| `ip-adapter-plus_sdxl_vit-h.safetensors` | `ipadapter` | 848 MB | Base + Animate |
| `mm_sdxl_v10_beta.ckpt` | `animatediff_models` | 950 MB | Animate |

Os tres estao em `workflow_models` — a **Celula 5 baixa sozinha**. O CLIP Vision
**tem de manter esse nome de arquivo**, o IPAdapter o identifica assim.

### Poses: trocar so o no 9 do Animate

walk `walking cycle, legs moving` · attack `attacking, swinging arm forward`
· death `falling down, collapsing, defeated` · idle `standing, breathing, slight sway`

Seed **555 fixa** mantem a aparencia entre animacoes. Para **attack**, mudar o
no 11 para **1024x768 landscape** — quadrado corta o braco/arma (erro que o
autor do video original cometeu ao vivo).

## v30 — checkpoint v170 e a causa REAL das abas travadas

### Checkpoint

Trocado `waiIllustriousSDXL_v160` -> **`v170`** em tudo: 6 workflows
(`Detailer`, `Base`, `Animate`, `Concept`, `WaifuVroid`,
`WaifuVroid_FromConcept`), `node_registry.json` e `roster.example.json`.

### As abas: meu diagnostico da v26 estava incompleto

Na v26 eu limpei referencias mortas do `comfy.settings.json` (lado servidor).
O print do usuario mostrou que o problema continuou, e revelou o que faltava:
**a sidebar ainda listava `Assets`, `ChibiPoses` e `FromConcept`** — apagados
do repo na v29, mas ainda presentes no Drive e no `user/` local.

Duas causas somadas:

**1. A C4 nunca removia workflows.** Ela so copia. Um workflow apagado do repo
ficava para sempre no Drive e na sidebar. Clicar nele = arquivo inexistente =
alerta "Nao foi possivel encontrar o fluxo de trabalho" e o tabbar trava.

**2. Bug conhecido do frontend, nao nosso.**
`Comfy-Org/ComfyUI_frontend#9317` descreve exatamente os sintomas: a
restauracao de abas guarda rascunhos no armazenamento do **navegador**, e
"tab restoration never activates the correct workflow". Relatos identicos:
clicar numa aba abre `Unsaved Workflow (n)` em vez do workflow — que e
precisamente o que se ve no print (aba "Unsaved Workflow" ativa ao lado de
`WaifuSurvivors_Base`).

Por isso limpar so o lado servidor nao bastava: **metade do estado vive no
navegador**.

### Correcoes

**C4 — manifesto de injetados.** `user/.injetados.json` registra o que o
notebook copiou. A cada execucao, o que esta no manifesto mas nao esta mais no
repo e **removido dos dois lados**. Workflows criados pelo usuario na UI nunca
entram no manifesto, entao **nunca sao apagados**.

Testado com 8 workflows na UI (3 orfaos + 4 do repo + 1 pessoal): removeu os 3,
preservou o pessoal.

**C6 (`v30-tabs`) — desliga a persistencia de abas.** Agora tambem grava
`Comfy.Workflow.Persist = false`. Sem a restauracao automatica, cada workflow
abre limpo do disco. Perde-se reabrir as abas da sessao anterior — o que num
Colab efemero nao vale nada — e ganha-se um tabbar que funciona.

### Se ainda travar: limpar o estado do NAVEGADOR

Isto o notebook nao alcanca. No navegador, com a UI aberta:
F12 -> Application -> Storage -> **Clear site data** (ou Ctrl+Shift+Del para o
endereco do Colab). Depois F5.

Os rascunhos ficam la, nao no servidor; enquanto nao forem limpos o bug pode
voltar mesmo com o disco correto.

### Regra

Estado de UI existe em **dois lugares**: `user/` no servidor e o armazenamento
do navegador. Diagnostico de aba travada tem de considerar os dois. E toda
sincronizacao repo->Drive precisa de **manifesto** para saber o que remover;
copiar sem nunca apagar acumula lixo que quebra o frontend.
