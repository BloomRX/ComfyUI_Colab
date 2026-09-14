# ComfyUI-Lia-TextureProjection

Projeção de texturas por múltiplas vistas para meshes no ComfyUI — **torch puro**,
sem nvdiffrast, sem código de terceiros. Escrito do zero (clean-room) para o
projeto ComfyUI_Colab; licença **MIT**.

## Nós

| nó | faz |
|---|---|
| `Projection Angles (Lia)` | lista de ângulos (presets 4/6/8 vistas ou custom) + `frame_scale` |
| `Render Projection Views (Lia)` | mesh → normal map (espaço de câmera), máscara, profundidade e prévia sombreada, uma por ângulo |
| `Project Images To Texture (Lia)` | imagens pintadas (uma por ângulo) → `base_color` no atlas UV do mesh |

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

`python tests/test_projection.py` — esfera com cor conhecida em função da
posição: renderiza 4 vistas, projeta de volta e exige erro médio < 0.03.
