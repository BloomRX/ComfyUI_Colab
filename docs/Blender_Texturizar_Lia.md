# Texturizar a Lia no Blender por projeção (caminho E)

Objetivo: substituir a textura borrada do TRELLIS.2/Pixal3D por uma textura
**projetada das imagens 2D da própria Lia**. Mesma técnica dos nós de
"texture projection", só que manual, no Blender, com licença limpa (o output
do Blender é seu; nada de nvdiffrast/Hunyuan).

Tempo: ~15–20 min por personagem depois da primeira vez. Blender 4.x.

---

## 0. O que você precisa ter antes

| item | de onde vem |
|---|---|
| `Lia_*.glb` (mesh) | `Lia_Trellis2_Image2Mesh` ou `Lia_Pixal3D_MultiView` (pasta `output/3d/Lia/`) |
| 4 imagens ortográficas da Lia: frente, costas, esquerda, direita | `Lia_Klein_Partes` com as instruções **pose A — costas e lados** (`orthographic, same scale, same framing`). Use os PNGs **com alpha** de `output/Lia_partes/` |
| Blender 4.x | blender.org |

Regras das imagens: mesma pose que o mesh (pose A), mesmo enquadramento,
fundo removido, ≥ 1024 px. Se a Lia do mesh está em pose A, as 4 vistas
têm de ser pose A também — a projeção não corrige pose.

> A imagem que gerou o mesh (a `Lia_front.png` do TRELLIS) **é** a vista de
> frente. Não gere outra; use ela. Quanto mais fiel a vista ao mesh, menos
> "fantasma" na projeção.

---

## 1. Importar e preparar o mesh (3 min)

1. `File > Import > glTF 2.0` → escolha o `Lia_*.glb`.
2. Selecione o mesh, `Tab` (Edit Mode), `A` (tudo), `Mesh > Clean Up > Merge by Distance`. `Tab` de volta.
3. **UV**: o GLB do TRELLIS já traz UV (do `UnwrapMesh`). Confira em `UV Editing`: se o atlas parecer razoável, mantenha. Se estiver muito fragmentado, `U > Smart UV Project` (Angle Limit 66°, Island Margin 0.02) — para toon/VRM serve.
4. Na aba **Material**: crie um material novo, `Base Color` → `Image Texture` → `New`: nome `Lia_albedo`, **2048×2048**, cor preta, sem alpha. Deixe esse nó **selecionado** (é nele que o bake grava).
5. Coloque a Lia na origem, de pé, olhando para **-Y** (frente do Blender). `Object > Apply > All Transforms`.

## 2. Montar as 4 câmeras ortográficas (5 min)

Para cada vista (frente / costas / esquerda / direita):

1. `Shift+A > Camera`. Na aba da câmera: **Type = Orthographic**, `Orthographic Scale` = altura da Lia × 1.1 (ex.: Lia com 1,7 m → 1.87). Mesmo valor nas 4.
2. Posição/rotação (Lia na origem, altura H, centro em Z = H/2):

| vista | Location (X, Y, Z) | Rotation (X, Y, Z) |
|---|---|---|
| frente | (0, -5, H/2) | (90°, 0, 0) |
| costas | (0, 5, H/2) | (90°, 0, 180°) |
| esquerda (lado esquerdo da Lia) | (5, 0, H/2) | (90°, 0, 90°) |
| direita | (-5, 0, H/2) | (90°, 0, -90°) |

3. Renomeie `Cam_front`, `Cam_back`, `Cam_left`, `Cam_right`.
4. Confira olhando pela câmera (`Numpad 0`) se o enquadramento **bate** com a imagem gerada (mesma margem em cima/embaixo). Ajuste o `Orthographic Scale` até bater — esse é o passo que mais influencia o resultado.

> Atalho: salve esse arquivo como `Lia_texturizar_template.blend`. Na próxima
> personagem, só reimporta o GLB.

## 3. Projetar cada imagem (Texture Paint) — 5 min

1. Workspace **Texture Paint**. No painel N (lado direito) > aba **Tool**:
   - Brush: **Draw**, `Strength 1.0`.
   - **Texture Slots**: `Mode = Material`, confirme que `Lia_albedo` está ativa.
   - **Texture** (do pincel): `Open` → escolha `Lia_front.png`. **Mapping = Stencil**.
   - Em **Falloff**: `Angle = 60°`, ative `Front Faces Only` (evita pintar as costas pela frente).
2. Viewport: `Numpad 0` com `Cam_front` ativa (`Ctrl+Numpad 0` sobre a câmera para torná-la ativa).
3. Alinhe o stencil: `Right Mouse` arrasta, `Shift+RMB` escala, `Ctrl+RMB` gira. Encaixe a imagem sobre a silhueta da Lia. (Com `Image Aspect` marcado o stencil mantém proporção.)
4. **Projetar**: não existe um botão "projetar tudo" no modo stencil — o stencil projeta a imagem pixel a pixel onde o pincel passa. Então aumente o pincel (`F` + arrastar) até cobrir meio corpo e dê 3–4 passadas largas sobre toda a silhueta. **Não gire a viewport** enquanto pinta a vista (a projeção é em espaço de tela); se girar sem querer, `Numpad 0` de novo e realinhe o stencil.
5. Repita para `Cam_back` / `Lia_back.png`, depois os lados. Para os lados use `Strength 0.7` para o blend com o que já foi pintado ficar suave.
6. `Image > Save All Images` (ou `Alt+S` no Image Editor) — a textura pintada fica em `Lia_albedo`.

> **Modo alternativo (mais preciso, sem esfregar pincel)**: para cada vista,
> `UV Editing` → em Edit Mode selecione tudo → com a câmera ativa
> `U > Project from View` (**em um UV map secundário**, crie `UVMap_proj` antes) →
> ligue `Lia_front.png` num material temporário usando esse UV map → faça um
> **bake Emit** de `UVMap_proj` para `UVMap` (atlas real) com máscara de faces
> voltadas à câmera. É o que os nós de projeção fazem; dá mais trabalho na
> primeira vez, mas é reproduzível e sem mão. Se você gostar do resultado do
> modo pincel, fique com ele — para VRM/toon a diferença é pequena.

## 4. Consertar as costuras (3 min)

- Zonas que nenhuma câmera viu bem (axilas, entre as pernas, topo da cabeça, embaixo do queixo) ficam pretas. Em Texture Paint, pincel **Clone** (`Ctrl+LMB` define a origem) ou **Smear** para puxar cor vizinha. Para toon, uma cor chapada resolve.
- Para descolorir "fantasmas" de projeção lateral no rosto, pinte de novo só o rosto com o stencil da frente em `Strength 1.0`.
- **Dilatação**: no Image Editor, `Image > Save As` com `Margin` não existe; use no bake final (passo 5) `Margin = 16 px` para as bordas das ilhas não vazarem.

## 5. Bake final + exportar (2 min)

Se você pintou direto em `Lia_albedo` (modo pincel), não precisa de bake:
`Image > Save As` → `Lia_albedo.png`.

Se usou o modo UV secundário: `Render Properties > Render Engine = Cycles`,
`Bake > Bake Type = Emit`, `Margin 16 px`, alvo `Lia_albedo`, `Bake`.

Exportar: `File > Export > glTF 2.0`, `Format = glb`, `Materials = Export`,
`Images = Automatic`. Confira em <https://gltf-viewer.donmccurdy.com/>.

Para o VRM: mesmo mesh, mesma textura — o add-on **VRM Add-on for Blender**
usa o `Lia_albedo` como `MToon Lit Color`. Defina `Shade Color` um pouco mais
escuro e pronto: albedo "flat unlit" é exatamente o que MToon quer.

---

## Problemas comuns

| sintoma | causa | conserto |
|---|---|---|
| textura deslocada / "olhos na testa" | `Orthographic Scale` ou enquadramento diferente da imagem | ajuste a escala da câmera até a silhueta bater; não mova o mesh |
| costas com o rosto | esqueceu `Front Faces Only` | ative e repinte as costas |
| faixas escuras nos lados | ângulo rasante | `Falloff Angle 45°` e Strength menor nos lados; deixe frente/costas dominarem |
| textura borrada | imagem < 1024 ou atlas 1024 | regenere as vistas em 1024+ e use atlas 2048 |
| pose não bate (braço em outro lugar) | as vistas não estão na mesma pose do mesh | regenere as vistas a partir da `Lia_front.png` que gerou o mesh, com a instrução de pose A |

---

## O que isso valida

Se a textura projetada ficar boa aqui, o mesmo processo vira o nó próprio
de ComfyUI (caminho A': render de normais/máscara com `RenderMesh` do core →
Klein 4B gera cada vista fiel → bake por projeção em `trimesh`+`torch`, MIT).
Se ficar ruim mesmo com as vistas bem alinhadas, o problema é o mesh (forma)
e não a textura — aí o ajuste é no TRELLIS/Pixal3D, não na projeção.
