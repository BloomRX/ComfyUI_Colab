# ComfyUI-Lia-TextureProjection

Projeção de texturas por múltiplas vistas para meshes no ComfyUI — **torch puro**,
sem nvdiffrast, sem código de terceiros. Escrito do zero (clean-room) para o
projeto ComfyUI_Colab; licença **MIT**.

## Nós

| nó | faz |
|---|---|
| `Projection Angles (Lia)` | lista de ângulos (presets 4/6/8 vistas ou custom) + `frame_scale` |
| `Render Projection Views (Lia)` | mesh → normal map (espaço de câmera), máscara, profundidade e prévia sombreada, uma por ângulo |
| `Project Images To Texture (Lia)` | imagens pintadas (uma por ângulo) → `base_color` no atlas UV do mesh (modo v1, tudo de uma vez) |
| `Render Textured View (Lia)` | **v2** — renderiza a vista com a textura parcial; devolve imagem (falta = cinza), `inpaint_mask`, silhueta, normal map |
| `Accumulate View Into Texture (Lia)` | **v2** — soma UMA vista pintada ao estado `LIA_TEXSTATE` (correção de tom `color_match`, `fill_only`) |
| `Finalize Texture (Lia)` | **v2** — dilata, preenche o não-visto, devolve `base_color` + `unseen_mask` |
| `Pick Reference Image (Lia)` | escolhe a referência da vista (costas/lados opcionais, cai na frontal) |

### Fluxo v2 — projeta-e-completa (sequencial, estilo Modddif/TEXTure)

```
state=∅ ─► Render Textured View(az0) ─► imagem cinza + máscara ─► Klein inpaint ─► Accumulate(az0) ─► state
state   ─► Render Textured View(az1) ─► "já pintado" + falta   ─► Klein inpaint ─► Accumulate(az1) ─► state
   …  (frente → costas → lados → cima → baixo)  …                                  Finalize ─► ApplyTextureToMesh
```

Cada vista **vê o que já foi pintado**, então as costas continuam a paleta da frente, e as
vistas de cima/baixo só preenchem axila, topo da cabeça, solas e o lado interno das pernas.
`missing_fraction` diz quanto da vista ainda estava vazio; `info` do Accumulate mostra texels
novos, sobreposição e o ganho RGB aplicado.

Fluxo típico:

```
mesh (com UV) ─► Render Projection Views ─► normais/máscaras ─► gerador de imagem (Flux.2 Klein 4B,
                                                                  referência = personagem 2D)
                                                                          │
mesh ────────────────────────────────────► Project Images To Texture ◄────┘
                                                      │
                                              ApplyTextureToMesh ─► SaveGLB
```

## Convenções

- Mesh em Y-up (como o GLB). `azimuth` 0 = frente (câmera em +Z), 90 = lado
  esquerdo do personagem, 180 = costas, 270 = direito. `elevation` positivo = de cima.
- Câmera **ortográfica**; quadro = maior lado do bounding box × `frame_scale`.
  Render e bake usam o mesmo `angles`, então as imagens encaixam pixel a pixel.
- Visibilidade por z-buffer (oclusão correta: a frente não pinta as costas).
- Peso por vista = `max(0, cos θ)^cos_power` (θ = ângulo entre normal e câmera),
  × máscara × `view_weights`. Média ponderada, depois dilatação de 8 px.
- Saída `coverage`: verde = texel visto por ≥1 vista; vermelho = mesh que
  nenhuma vista viu (preenchido pela cor vizinha se `fill_unseen`).

## Custo

Tudo em tiles em torch; sem kernels CUDA custom. Sphere 4k tris, 4 vistas 256²,
atlas 512²: ~30 s **em CPU**. Em GPU (T4) um personagem de 150k tris, 4 vistas
1024², atlas 2048² deve ficar na casa de 10–30 s. Memória cresce com
`resolution²` (render) e `texture_size²` (bake); em T4 use 1024 / 2048.

## Teste

- `python tests/test_projection.py` — esfera com cor conhecida em função da
  posição: renderiza 4 vistas, projeta de volta e exige erro médio < 0.03.
- `python tests/test_sequential.py` — fluxo v2: 6 vistas em sequência, só o
  "faltando" é pintado a cada passo; exige erro < 0.03, cobertura ≈ 100% e
  que `color_match` corrija uma vista com ganho errado.
- `python tests/test_nodes_smoke.py` — os nós em si, com mock da API do core.
