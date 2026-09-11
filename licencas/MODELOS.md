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
| licença | Illustrious License (herdada) — provável OpenRAIL++-M |
| saída comercial | **SIM** — autor declara *"Commercial Allowed"* na página |
| restrições | dependem de qual: ver tabela |
| download | **MANUAL** — não existe no HuggingFace, e o Civitai exige login |
| usado em | Base, Concept, CharacterSheet, TrocarRoupa |

#### Qual licença, afinal?

A Onoma AI **mudou a licença do Illustrious entre versões**, e o WAI **mudou de
base**:

| Illustrious base | licença | usada por |
|---|---|---|
| v0.1 | Fair AI Public License 1.0-SD | WAI até v13 |
| **v1.0** | **CreativeML Open RAIL++-M** | **WAI v14 em diante** |
| v2.0 | CreativeML Open RAIL-M | rejeitada pelo autor do WAI |

Como usamos a **v17.0**, a herança mais provável é **OpenRAIL++-M**. O Civitai
ainda rotula "Illustrious License" apontando para a FAIPL da v0.1 — rótulo
desatualizado.

**As duas permitem uso comercial da saída:**

- FAIPL: *"The output of this software is not covered by this license, and no
  contributor claims any rights to it."*
- OpenRAIL++-M: Output é do usuário; uso comercial permitido, com as
  *use-based restrictions* propagando para derivados.

Se for OpenRAIL++-M, você tem **mais** liberdade: some o copyleft forte e a
exigência de fornecer o modelo em serviço de rede.

**Verificado em 2026-09-10** (usuário, logado no `civitai.red`): a página da
v17.0 declara **"Commercial Allowed"**.

Três camadas concordando: a licença da base permite, a licença herdada permite,
e o autor declara explicitamente.

⚠️ **Ainda vale fazer:** salvar um PDF/print dessa página com a data. Um campo
de permissão no Civitai não é o texto integral da licença, mas é a declaração
do autor — e serve como evidência de boa-fé se a página mudar.

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

---

## Alternativas ao Illustrious (se quiser licença sem ambiguidade)

O `waiIllustrious` é o único componente do pipeline com licença incerta. Se
isso incomodar, há saídas — todas com custo.

| opção | licença | custo de trocar |
|---|---|---|
| **manter o WAI v170** | OpenRAIL++-M (provável) | zero |
| Illustrious XL 1.1 oficial | OpenRAIL++-M declarada | requalificar prompts; perde o ajuste estético do WAI |
| **treinar LoRA própria** sobre base permissiva | a que você escolher | semanas de trabalho |
| Pony Diffusion V6 XL | OpenRAIL++-M | estilo diferente; refazer todos os testes |

### Recomendação

**Manter o WAI v170.** As duas licenças candidatas permitem uso comercial da
saída — a incerteza é sobre *quais obrigações você tem ao redistribuir o
modelo*, e nós não redistribuímos o modelo.

O risco real do projeto **não é a licença do checkpoint**: é gerar personagem
parecida com obra protegida (o modelo é treinado em Danbooru). Isso vale para
qualquer modelo anime, inclusive os de licença "limpa".

### Se um dia o jogo crescer

Aí vale pagar uma consulta jurídica de algumas horas, com estes documentos em
mãos. O custo é irrelevante perto do de um problema, e o registro datado que
temos aqui é exatamente o que um advogado pediria.
