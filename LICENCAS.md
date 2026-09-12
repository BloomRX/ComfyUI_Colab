# Licenças — uso comercial no WAIFU SURVIVORS

Levantamento feito em setembro/2026, checando cada licença na fonte
(API do HuggingFace, API do GitHub e o texto integral da FAIPL).

**Não sou advogado e isto não é parecer jurídico.** É um levantamento técnico
das licenças declaradas, para você saber onde há risco real e onde não há.

---

## Resumo

| componente | licença | comercial? |
|---|---|---|
| **waiIllustriousSDXL_v170** | Fair AI Public License 1.0-SD | **ver abaixo — o ponto crítico** |
| WAN 2.2 TI2V-5B | Apache 2.0 | sim |
| umt5_xxl / wan2.2_vae | Apache 2.0 | sim |
| IP-Adapter (h94) | Apache 2.0 | sim |
| CLIP-ViT-H-14 | Apache 2.0 | sim |
| controlnet-union-sdxl | Apache 2.0 | sim |
| ComfyUI-AnimateDiff-Evolved | Apache 2.0 | sim |
| hsxl_temporal_layers (Hotshot-XL) | **CreativeML OpenRAIL++-M** | sim, com ressalva |
| ComfyUI-Inspyrenet-Rembg | MIT | sim |
| ComfyUI_Mira | MIT | sim |
| Character Select SAA | MIT | sim |
| ComfyUI_IPAdapter_plus | **GPL-3.0** | sim (ver nota) |
| ComfyUI-VideoHelperSuite | **GPL-3.0** | sim (ver nota) |
| ComfyUI-Advanced-ControlNet | **GPL-3.0** | sim (ver nota) |
| ComfyUI-Manager | **GPL-3.0** | sim (ver nota) |
| ComfyUI (core) | sem licença declarada na API do GitHub | ver nota |
| **TRELLIS.2** (`trellis_2_int8_convrot`, VAEs) — projeto Lia | MIT (Comfy-Org repack de microsoft/TRELLIS.2-4B, também MIT) | sim |
| **Pixal3D MV** (`pixal3d_multiview_int8_convrot`) — projeto Lia | MIT (repack de TencentARC/Pixal3D, MIT) | sim |
| **BiRefNet** (`birefnet.safetensors`) — projeto Lia | MIT (repack de ZhengPeng7/BiRefNet, MIT) | sim |
| **DINOv3 ViT-L** (`dino_v3_L_naf_fp32`) — projeto Lia | repack MIT, **mas deriva da DINOv3 License (Meta)** | sim, com **obrigação de crédito** — ver §7 |
| **Flux.2 Klein 4B** (`flux-2-klein-4b-fp8`, `qwen_3_4b_fp8_mixed`, `flux2-vae`) — projeto Lia | **Apache-2.0** (BFL; encoder Qwen3 Apache-2.0) | sim — ver §7 (o **9B** é Non-Commercial e está **vetado**) |

> **Correção (v65):** eu havia agrupado o Hotshot-XL como Apache 2.0. A API do
> HuggingFace mostra `license:openrail++` — **CreativeML OpenRAIL++-M**, que
> permite uso comercial mas traz cláusulas de uso proibido. Ele está arquivado
> (reprovado na v32/v50), então não afeta o pipeline atual; se voltar, reler.

Registro estruturado, com evidência datada de cada fonte:
**[`licencas/MODELOS.md`](licencas/MODELOS.md)** e
**[`licencas/INDICE.md`](licencas/INDICE.md)**.

---

## 1. O ponto que decide tudo: a cláusula "Output"

> **Confirmado (v67) — o autor declara "Commercial Allowed".**
>
> O usuário logou no `civitai.red` e leu o bloco de permissões da v17.0:
> **Commercial Allowed**.
>
> Isso encerra a ambiguidade prática. Havia dúvida sobre qual licença o v170
> herda (a Onoma AI mudou entre versões, e o WAI mudou de base na v14):
>
> | Illustrious base | licença | usada por |
> |---|---|---|
> | v0.1 | Fair AI Public License 1.0-SD | WAI até v13 |
> | **v1.0** | **CreativeML Open RAIL++-M** | **WAI v14+ (a nossa)** |
> | v2.0 | CreativeML Open RAIL-M | rejeitada pelo autor |
>
> **As duas candidatas já permitiam uso comercial da saída** — a FAIPL pela
> cláusula *Output*, a OpenRAIL++-M por definir o Output como do usuário. E
> agora o autor confirma explicitamente na página.
>
> Três camadas concordando: licença da base, licença herdada e declaração do
> autor. **Para gerar sprites e vender o jogo, está resolvido.**

## 2. GPL-3.0 nos custom nodes — não contamina o jogo

Quatro packs são GPL-3.0. Isso **não** afeta o jogo, porque:

- eles rodam no ComfyUI, no Colab — **não são distribuídos com o jogo**
- a GPL trata de *distribuição de software*, não de arquivos produzidos por ele
- um PNG gerado por um programa GPL não é obra derivada do programa

Comparação: uma imagem feita no GIMP (GPL) não vira GPL.

**Cuidado apenas se um dia você distribuir uma cópia modificada desses nodes** —
aí a GPL exige publicar o fonte.

---

## 3. ComfyUI core sem licença declarada

A API do GitHub não retorna licença para `comfyanonymous/ComfyUI`. O repositório
tem um arquivo LICENSE (GPL-3.0) que a API não reconheceu automaticamente.

Mesmo raciocínio do item 2: ferramenta, não componente do jogo.

---

## 4. Riscos que NÃO são de licença de modelo

Estes são os que realmente podem te dar problema:

### 4.1 Personagens de anime existentes — o risco mais concreto

O `waiIllustrious` é **treinado em tags do Danbooru** e reproduz personagens com
copyright (Hatsune Miku, personagens de animes etc.) com muita fidelidade. O
Character Select SAA existe justamente para selecionar esses personagens.

**Gerar uma personagem reconhecível de outra obra e vender no seu jogo é
violação de copyright/marca — independente de qualquer licença de IA.**

Para o WAIFU SURVIVORS: use o SAA para *explorar estilo*, mas as 5 personagens
finais têm de ser **originais**. Não use nomes de personagens conhecidas no
prompt do `Concept`.

### 4.2 Conteúdo adulto e lojas

Já documentado na v23: Steam aceita adulto com marcação; **consoles e app
stores não**. Se pretende publicar fora do Steam, mantenha as versões
`sensitive` fora do build.

### 4.3 Marca d'água herdada do dataset

Documentado antes: ~1 em 10-20 imagens sai com resquício de logo/assinatura do
dataset de treino. **Inspecione cada sprite** antes de colocar no jogo — vender
arte com marca d'água de terceiro é problema.

---

## 5. Recomendações práticas

1. **Guarde evidência**: salve a página de licença do Civitai (PDF/print) na
   data do download do v170.
2. **Nunca embuta o checkpoint** no jogo, nem em DLC, nem em ferramenta de mod.
3. **Personagens originais.** Nada de nome de personagem existente no prompt.
4. **Revise cada sprite** procurando marca d'água antes de integrar.
5. **Se publicar LoRA**, publique sob FAIPL e diga que deriva do Illustrious.
6. **Créditos**: não é exigido pela cláusula Output, mas listar as ferramentas
   (ComfyUI, WAN, Illustrious) nos créditos é barato e evita atrito.

---

## 6. Veredito

**Para gerar sprites e vender o jogo, o caminho está livre.** Todo componente
do pipeline permite uso comercial da saída, e o `waiIllustrious` — o único que
gerava dúvida — tem três camadas concordando: a licença da base permite, a
licença herdada permite, e o autor declara **"Commercial Allowed"** na página.

### O que sobra de risco (nenhum é de licença de modelo)

| risco | gravidade | o que fazer |
|---|---|---|
| **personagem parecida com obra protegida** | **alta** | personagens originais; nada de nome de personagem existente no prompt |
| marca d'água herdada do dataset | média | revisar cada sprite antes de integrar |
| conteúdo adulto em loja errada | média | Steam aceita com marcação; consoles não |
| licença mudar depois | baixa | guardar PDF datado das páginas |

O primeiro é o que realmente pode custar caro, e **não some trocando de
modelo** — qualquer modelo anime treinado em Danbooru reproduz personagens com
copyright. Some com disciplina de prompt.

### Pendência prática

Salvar PDF/print da página do Civitai (v17.0, com o "Commercial Allowed"
visível) e guardar junto do projeto. A Onoma AI já alterou termos
retroativamente uma vez; a evidência datada é o que protege.

---

## 7. Projeto Lia (imagem → 3D) — auditoria v69

Cinco modelos novos entraram com `Workflows/Lia_Trellis2_Image2Mesh.json`.
Evidências em `licencas/evidencias/hf_Comfy-Org_*.json` e dos repositórios de
origem (`hf_microsoft_TRELLIS.2-4B.json`, `hf_ZhengPeng7_BiRefNet.json`,
`hf_facebook_dinov3-vitl16-pretrain-lvd1689m.json`), coletadas em 2026-09-11.

| arquivo | repack (Comfy-Org) | original | licença que vale |
|---|---|---|---|
| `trellis_2_int8_convrot.safetensors` | MIT | microsoft/TRELLIS.2-4B — MIT | **MIT** |
| `trellis_2_shape_vae_bf16.safetensors` | MIT | microsoft/TRELLIS.2-4B — MIT | **MIT** |
| `trellis_2_texture_vae_bf16.safetensors` | MIT | microsoft/TRELLIS.2-4B — MIT | **MIT** |
| `birefnet.safetensors` | MIT | ZhengPeng7/BiRefNet — MIT | **MIT** |
| `pixal3d_multiview_int8_convrot.safetensors` | MIT | TencentARC/Pixal3D — MIT | **MIT** |
| `dino_v3_L_naf_fp32.safetensors` | MIT | facebook/dinov3-vitl16 — **DINOv3 License** | **DINOv3 License** |
| `flux-2-klein-4b-fp8.safetensors` | — (publicado pela própria BFL) | black-forest-labs/FLUX.2-klein-4B — Apache-2.0 | **Apache-2.0** |
| `qwen_3_4b_fp8_mixed.safetensors` | Apache-2.0 (Comfy-Org/z_image_turbo) | Qwen/Qwen3-4B — Apache-2.0 | **Apache-2.0** |
| `flux2-vae.safetensors` | repo Comfy-Org/flux2-dev marcado `other` | mesmo arquivo (sha256 idêntico) do black-forest-labs/FLUX.2-klein-4B — Apache-2.0 | **Apache-2.0** (ver nota) |

### O ponto de atenção: DINOv3

O Comfy-Org marca o repositório inteiro como MIT, mas o `dino_v3_L_naf_fp32`
é o DINOv3 ViT-L da Meta convertido. Repack não muda a licença dos pesos
originais. A **DINOv3 License** (14/08/2025):

- **permite uso comercial** (a própria Meta anunciou assim);
- ao **redistribuir os pesos ou derivados**: incluir cópia da licença e exibir
  **"Built with DINOv3"** em site/UI/documentação;
- proíbe usos sujeitos a ITAR/Trade Controls (militar, armas etc.);
- o que você produz com ele é seu.

**O que isso muda para o jogo: quase nada.** O DINOv3 é o *encoder da imagem
de entrada*; ele roda no Colab na hora de gerar o mesh e **não vai dentro do
jogo**. Nenhum peso da Meta é redistribuído. A malha GLB/VRM da Lia é output
seu. Para ficar confortável, basta uma linha nos créditos/README da pipeline
("modelos 3D gerados com TRELLIS.2 + DINOv3"), que é boa prática de qualquer
jeito.

Não há nada equivalente ao problema da FAIPL/Illustrious aqui: os três
modelos-base são MIT ou permitem comercial explicitamente.

**Não sou advogado; isto é levantamento técnico das licenças declaradas.**

### Flux.2 Klein: 4B sim, 9B não (v71)

O `Lia_Klein_Partes` usa o **Klein 4B** (Apache-2.0, não gated). A família
Flux.2 tem duas licenças diferentes e é fácil confundir:

| modelo | licença | no projeto |
|---|---|---|
| FLUX.2 [klein] **4B** (base e distilled) | Apache-2.0 | **sim** |
| FLUX.2 [klein] **9B** | FLUX Non-Commercial License (gated) | **não** |
| FLUX.2 [dev] | FLUX Non-Commercial License | **não** |
| Separation LoRA (Aero-Ex/Klein9B-Separation_LoRa) | sem licença declarada; treinada no 9B | **não** |

Nota sobre o VAE: o `flux2-vae.safetensors` está hospedado no repo
`Comfy-Org/flux2-dev` (marcado `other` por causa do dev), mas é o mesmo
arquivo do Klein 4B (mesmo oid/sha256 no `Comfy-Org/vae-text-encorder-for-flux-klein-4b`).
Evidência: `licencas/evidencias/hf_Comfy-Org_flux2-dev.json`.

