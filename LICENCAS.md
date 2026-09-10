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
