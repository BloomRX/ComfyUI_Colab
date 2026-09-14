# Relatório da sessão ComfyUI — 2026-09-14 17:49:26

GPU: Tesla T4, 15360 MiB
VRAM pico: 6.8 GB

## Prompts executados

### 001_6504b0b3 — success — 260 nós, 34 imagem(ns)
- nós-chave: DecimateMesh, LiaPickReference, LiaProjectTextureAccumulate, LiaRenderTextured, LiaTextureFinalize, SaveGLB, UnwrapMesh
- 1 Frente: render parcial + máscara: `["az 0 el 0: 100.0% da vista ainda sem textura"]`
- 1 Frente: acumula no atlas: `["az 0 el 0: +212683 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 15.1%"]`
- 2 Costas: render parcial + máscara: `["az 180 el 0: 99.6% da vista ainda sem textura"]`
- 2 Costas: acumula no atlas: `["az 180 el 0: +217056 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 30.4%"]`
- 3 Esquerda: render parcial + máscara: `["az 90 el 0: 23.6% da vista ainda sem textura"]`
- 3 Esquerda: acumula no atlas: `["az 90 el 0: +50614 texels novos, sobreposição 50926, ganho RGB [0.984, 0.984, 0.984], cobertura 34.0%"]`
- 4 Direita: render parcial + máscara: `["az 270 el 0: 20.8% da vista ainda sem textura"]`
- 4 Direita: acumula no atlas: `["az 270 el 0: +48255 texels novos, sobreposição 52101, ganho RGB [0.85, 0.85, 0.85], cobertura 37.4%"]`
- 5 Frente/cima: render parcial + máscara: `["az 0 el 30: 5.7% da vista ainda sem textura"]`
- 5 Frente/cima: acumula no atlas: `["az 0 el 30: +32804 texels novos, sobreposição 66308, ganho RGB [1.032, 1.032, 1.032], cobertura 39.8%"]`
- 6 Costas/cima: render parcial + máscara: `["az 180 el 30: 3.3% da vista ainda sem textura"]`
- 6 Costas/cima: acumula no atlas: `["az 180 el 30: +19531 texels novos, sobreposição 33030, ganho RGB [1.005, 1.005, 1.005], cobertura 41.2%"]`
- 7 Frente/baixo: render parcial + máscara: `["az 0 el -30: 22.5% da vista ainda sem textura"]`
- 7 Frente/baixo: acumula no atlas: `["az 0 el -30: +93387 texels novos, sobreposição 60470, ganho RGB [1.112, 1.112, 1.112], cobertura 47.8%"]`
- 8 Costas/baixo: render parcial + máscara: `["az 180 el -30: 5.8% da vista ainda sem textura"]`
- 8 Costas/baixo: acumula no atlas: `["az 180 el -30: +20913 texels novos, sobreposição 41831, ganho RGB [1.009, 1.009, 1.009], cobertura 49.2%"]`
- 9 Rosto (zoom 3x): render parcial + máscara: `["az 0 el 0: 0.0% da vista ainda sem textura"]`
- 9 Rosto (zoom 3x): acumula no atlas: `["az 0 el 0: +35 texels novos, sobreposição 21359, ganho RGB [1.0, 1.0, 1.0], cobertura 49.3%"]`
- Conferência 3/4 (textura FINAL; magenta = buraco real): `["az 30 el 15: 0.0% da vista ainda sem textura"]`

## Conteúdo
- `comfyui.log` — saída completa do servidor
- `prompts/*.json` — cada execução: grafo API com valores, status, textos de saída, imagens
- `imagens/` — miniaturas das saídas/previews
- `eventos.jsonl` — fila, VRAM, erros