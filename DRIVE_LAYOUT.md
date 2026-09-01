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
