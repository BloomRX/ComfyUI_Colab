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
