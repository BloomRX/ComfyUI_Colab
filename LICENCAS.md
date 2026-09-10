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

O `waiIllustriousSDXL` herda a **Fair AI Public License 1.0-SD** do Illustrious
XL. Li o texto integral em freedevproject.org. A seção que importa:

> ## Output
> **The output of this software is not covered by this license, and no
> contributor claims any rights to it.**

Ou seja: **as imagens que você gera não são cobertas pela licença do modelo, e
nenhum contribuidor reivindica direitos sobre elas.** Os sprites do seu jogo
são seus.

Isso é confirmado pelas plataformas que hospedam o modelo (TensorArt, SeaArt,
PixAI listam "allow commercial use of generated images").

### O que a FAIPL restringe de fato

A licença é do tipo *copyleft* e se aplica ao **modelo**, não à saída:

- **redistribuir o modelo** (ou um derivado, incluindo LoRA e merge) exige
  manter a mesma licença e fornecer o "source code"
- **serviço em rede**: se você deixar usuários interagirem com o modelo pela
  internet, precisa oferecer download do modelo derivado
- **Prohibited Uses**: nada ilegal, nada envolvendo menores, nada de
  desinformação/assédio etc.

### Como isso afeta o WAIFU SURVIVORS

| o que você faz | permitido? |
|---|---|
| vender o jogo com os sprites gerados | **sim** — cláusula Output |
| distribuir os PNGs dentro do .exe/.pck | **sim** — são output |
| treinar uma LoRA da sua personagem e usar em casa | sim |
| **publicar** essa LoRA | sim, **mas sob FAIPL** (copyleft) |
| embutir o checkpoint no jogo | **não faça** — seria redistribuir o modelo |
| oferecer um gerador de personagens online no jogo | **evite** — cai na
  cláusula de rede |

**Regra prática: o modelo fica no seu Colab. Só os PNGs vão para o jogo.**

### A ressalva honesta

Há um debate real na comunidade sobre a validade dessas cláusulas, já que nos
EUA o Copyright Office considera saída de IA sem edição humana substancial como
domínio público. **Não dependa disso.** A cláusula Output da FAIPL já resolve
nosso caso sem precisar entrar nessa discussão.

Também vale notar: a Onoma AI acrescentou um **TOS** ao Illustrious v0.1
*retroativamente* em 2025. Licenças podem mudar. Recomendo **guardar uma cópia
da página de licença** do Civitai na data do download, como registro.

---

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

**Para o uso que fazemos — gerar sprites e vender o jogo — o caminho está
livre.** Todos os componentes permitem uso comercial da saída, e o Illustrious
é explícito ao não reivindicar direito nenhum sobre o output.

O risco real do projeto **não está nas licenças de modelo**: está em gerar
personagens semelhantes a obras protegidas e em não revisar marca d'água.
