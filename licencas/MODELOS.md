# Registro de modelos e licenças

Ficha técnica de cada modelo e ferramenta do projeto. Consulta rápida; a
análise do que isso significa para o jogo está em [`../LICENCAS.md`](../LICENCAS.md).

**Última verificação: 2026-09-08.** Evidências cruas em `evidencias/`.

Legenda de risco comercial:
🟢 sem restrição · 🟡 restrição que não nos afeta · 🔴 atenção

---

## Em uso hoje (workflows ativos)

### waiIllustriousSDXL_v170.safetensors 🟡

| | |
|---|---|
| papel | checkpoint principal — identidade de todos os personagens |
| onde | `models/checkpoints/` · ~6,5 GB |
| origem | Civitai — WAI-NSFW-illustrious-SDXL v17.0 (autor: WAI0731) |
| base | Illustrious XL (Onoma AI) → SDXL |
| licença | **Fair AI Public License 1.0-SD** (herdada) |
| saída comercial | **SIM** — cláusula *Output* renuncia a direitos |
| restrições | copyleft ao redistribuir o **modelo**; proibido como serviço em rede |
| download | **MANUAL** — não existe no HuggingFace, e o Civitai exige login |
| usado em | Base, Concept, CharacterSheet, TrocarRoupa |

> A cláusula que libera tudo:
> *"The output of this software is not covered by this license, and no
> contributor claims any rights to it."*

⚠️ **Não apagar do Drive** — a Célula 5 não consegue rebaixar.
⚠️ Treinado em tags do Danbooru: **capaz de reproduzir personagens com
copyright**. Ver risco 4.1 em `../LICENCAS.md`.

---

### wan2.2_ti2v_5B_fp16.safetensors 🟢

| | |
|---|---|
| papel | motor de animação (image-to-video) |
| onde | `models/diffusion_models/` · 9,31 GB |
| origem | `Comfy-Org/Wan_2.2_ComfyUI_Repackaged` |
| base | Wan-AI/Wan2.2-TI2V-5B (Alibaba) |
| licença | **Apache 2.0** |
| saída comercial | **SIM**, sem condições |
| usado em | AnimateWan |

Escolhido no A/B da v50/v54. Pico de ~9,3 GB de VRAM com `--cache-none`.

---

### umt5_xxl_fp8_e4m3fn_scaled.safetensors 🟢

| | |
|---|---|
| papel | text encoder do WAN |
| onde | `models/text_encoders/` · 6,27 GB |
| origem | `Comfy-Org/Wan_2.2_ComfyUI_Repackaged` |
| licença | **Apache 2.0** |
| usado em | AnimateWan |

---

### wan2.2_vae.safetensors 🟢

| | |
|---|---|
| papel | VAE do WAN |
| onde | `models/vae/` · 1,31 GB |
| origem | `Comfy-Org/Wan_2.2_ComfyUI_Repackaged` |
| licença | **Apache 2.0** |
| usado em | AnimateWan |

---

### ip-adapter-plus_sdxl_vit-h.safetensors 🟢

| | |
|---|---|
| papel | transfere aparência da referência |
| onde | `models/ipadapter/` · 848 MB |
| origem | `h94/IP-Adapter` |
| licença | **Apache 2.0** |
| usado em | Base, CharacterSheet |

---

### CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors 🟢

| | |
|---|---|
| papel | encoder de imagem do IPAdapter |
| onde | `models/clip_vision/` · 2,53 GB |
| origem | `h94/IP-Adapter` → `models/image_encoder/model.safetensors` |
| licença | **Apache 2.0** |
| usado em | Base, CharacterSheet |

⚠️ O nome do arquivo **tem de ser exatamente esse** — o IPAdapter identifica
pelo nome, não pelo conteúdo.

---

### controlnet-union-sdxl-1.0.safetensors 🟢

| | |
|---|---|
| papel | controle de pose no character sheet |
| onde | `models/controlnet/` · 2,51 GB |
| origem | `xinsir/controlnet-union-sdxl-1.0` (arquivo `_promax`) |
| licença | **Apache 2.0** |
| usado em | CharacterSheet |

---

## Avaliados e arquivados

### hsxl_temporal_layers.f16.safetensors 🟡

| | |
|---|---|
| papel | movimento SDXL (Hotshot-XL) |
| origem | `hotshotco/Hotshot-XL` |
| licença | **CreativeML OpenRAIL++-M** — *não é Apache* |
| saída comercial | sim, com as cláusulas de uso proibido do RAIL |
| status | **reprovado** (v32/v50): cor invertida, cabeça dupla |

Se um dia voltar ao pipeline, reler as restrições de uso do OpenRAIL++.

### v3_sd15_mm.ckpt · v3_sd15_sparsectrl_rgb.ckpt 🟢

| | |
|---|---|
| origem | `guoyww/animatediff` |
| licença | **Apache 2.0** |
| status | **reprovado** (v51): fidelidade 73,8 vs 9,9 do WAN |

### toonyou_beta6.safetensors 🔴

| | |
|---|---|
| origem | `frankjoshua/toonyou_beta6` (mirror de um modelo do Civitai) |
| licença | **não declarada no mirror** |
| status | **reprovado** (v51) — saída escura, fundo sujo |

⚠️ Se voltar a usar, **verificar a licença no Civitai original**. Mirror sem
licença declarada é risco.

---

## Ferramentas (rodam no Colab, não vão no jogo)

| pacote | licença | risco |
|---|---|---|
| ComfyUI (core) | GPL-3.0 (arquivo LICENSE) | 🟢 |
| ComfyUI-Manager | GPL-3.0 | 🟢 |
| ComfyUI_IPAdapter_plus | GPL-3.0 | 🟢 |
| ComfyUI-VideoHelperSuite | GPL-3.0 | 🟢 |
| ComfyUI-Advanced-ControlNet | GPL-3.0 | 🟢 |
| ComfyUI-AnimateDiff-Evolved | Apache-2.0 | 🟢 |
| ComfyUI-Inspyrenet-Rembg | MIT | 🟢 |
| ComfyUI_Mira | MIT | 🟢 |
| character_select_stand_alone_app | MIT | 🟢 |

GPL não contamina o jogo: são ferramentas, não componentes distribuídos.
Um PNG feito num programa GPL não vira GPL.

---

## Ao adicionar um modelo novo

1. `python3 scripts/coletar_licencas.py` — atualiza `evidencias/`
2. acrescente a ficha aqui
3. adicione o nome do arquivo à lista `AUDITADOS` em `scripts/checar_regras.py`

O `checar_regras.py` **falha** se um modelo de workflow ativo não estiver
auditado. É proposital: obriga a decisão de licença antes do uso.
