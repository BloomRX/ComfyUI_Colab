# Relatório da sessão ComfyUI — 2026-09-14 05:22:40

GPU: Tesla T4, 15360 MiB
VRAM pico: 7.0 GB

## Prompts executados

### 001_6b81fb5e — success — 235 nós, 31 imagem(ns)
- nós-chave: DecimateMesh, LiaPickReference, LiaProjectTextureAccumulate, LiaRenderTextured, LiaTextureFinalize, RemeshMesh, SaveGLB, UnwrapMesh
- 1 Frente: render parcial + máscara: `["az 0 el 0: 100.0% da vista ainda sem textura"]`
- 1 Frente: acumula no atlas: `["az 0 el 0: +308418 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 18.1%"]`
- 2 Costas: render parcial + máscara: `["az 180 el 0: 100.0% da vista ainda sem textura"]`
- 2 Costas: acumula no atlas: `["az 180 el 0: +301774 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 35.8%"]`
- 3 Esquerda: render parcial + máscara: `["az 90 el 0: 32.3% da vista ainda sem textura"]`
- 3 Esquerda: acumula no atlas: `["az 90 el 0: +76451 texels novos, sobreposição 153794, ganho RGB [1.127, 1.127, 1.127], cobertura 40.3%"]`
- 4 Direita: render parcial + máscara: `["az 270 el 0: 35.7% da vista ainda sem textura"]`
- 4 Direita: acumula no atlas: `["az 270 el 0: +81572 texels novos, sobreposição 143943, ganho RGB [1.144, 1.144, 1.144], cobertura 45.1%"]`
- 5 Frente/cima: render parcial + máscara: `["az 0 el 55: 3.6% da vista ainda sem textura"]`
- 5 Frente/cima: acumula no atlas: `["az 0 el 55: +8530 texels novos, sobreposição 253252, ganho RGB [0.85, 0.85, 0.85], cobertura 45.6%"]`
- 6 Costas/cima: render parcial + máscara: `["az 180 el 55: 1.8% da vista ainda sem textura"]`
- 6 Costas/cima: acumula no atlas: `["az 180 el 55: +2950 texels novos, sobreposição 237073, ganho RGB [1.008, 1.008, 1.008], cobertura 45.8%"]`
- 7 Frente/baixo: render parcial + máscara: `["az 0 el -50: 21.9% da vista ainda sem textura"]`
- 7 Frente/baixo: acumula no atlas: `["az 0 el -50: +48459 texels novos, sobreposição 207321, ganho RGB [1.071, 1.071, 1.071], cobertura 48.6%"]`
- 8 Costas/baixo: render parcial + máscara: `["az 180 el -50: 18.8% da vista ainda sem textura"]`
- 8 Costas/baixo: acumula no atlas: `["az 180 el -50: +48827 texels novos, sobreposição 239506, ganho RGB [1.2, 1.2, 1.2], cobertura 51.5%"]`
- Conferência 3/4 (magenta = texel nunca visto): `["az 30 el 15: 3.3% da vista ainda sem textura"]`

## Conteúdo
- `comfyui.log` — saída completa do servidor
- `prompts/*.json` — cada execução: grafo API com valores, status, textos de saída, imagens
- `imagens/` — miniaturas das saídas/previews
- `eventos.jsonl` — fila, VRAM, erros