# Relatório da sessão ComfyUI — 2026-09-14 18:34:59

GPU: Tesla T4, 15360 MiB
VRAM pico: 6.8 GB

## Prompts executados

### 001_10c60227 — error — 260 nós, 0 imagem(ns)
- nós-chave: DecimateMesh, LiaPickReference, LiaProjectTextureAccumulate, LiaRenderTextured, LiaTextureFinalize, SaveGLB, UnwrapMesh

### 002_bfe36a48 — success — 260 nós, 4 imagem(ns)
- nós-chave: DecimateMesh, LiaPickReference, LiaProjectTextureAccumulate, LiaRenderTextured, LiaTextureFinalize, SaveGLB, UnwrapMesh
- 1 Frente: render parcial + máscara: `["az 0 el 0: 100.0% da vista ainda sem textura"]`

### 003_4e03eaea — success — 260 nós, 34 imagem(ns)
- nós-chave: DecimateMesh, LiaPickReference, LiaProjectTextureAccumulate, LiaRenderTextured, LiaTextureFinalize, SaveGLB, UnwrapMesh
- 1 Frente: render parcial + máscara: `["az 0 el 0: 100.0% da vista ainda sem textura"]`
- 1 Frente: acumula no atlas: `["az 0 el 0: +220779 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 15.5%"]`
- 2 Costas: render parcial + máscara: `["az 180 el 0: 99.7% da vista ainda sem textura"]`
- 2 Costas: acumula no atlas: `["az 180 el 0: +212502 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 30.4%"]`
- 3 Esquerda: render parcial + máscara: `["az 90 el 0: 23.8% da vista ainda sem textura"]`
- 3 Esquerda: acumula no atlas: `["az 90 el 0: +51811 texels novos, sobreposição 53629, ganho RGB [0.94, 0.94, 0.94], cobertura 34.0%"]`
- 4 Direita: render parcial + máscara: `["az 270 el 0: 20.1% da vista ainda sem textura"]`
- 4 Direita: acumula no atlas: `["az 270 el 0: +49408 texels novos, sobreposição 54877, ganho RGB [0.85, 0.85, 0.85], cobertura 37.5%"]`
- 5 Frente/cima: render parcial + máscara: `["az 0 el 30: 5.4% da vista ainda sem textura"]`
- 5 Frente/cima: acumula no atlas: `["az 0 el 30: +33307 texels novos, sobreposição 66609, ganho RGB [1.042, 1.042, 1.042], cobertura 39.8%"]`
- 6 Costas/cima: render parcial + máscara: `["az 180 el 30: 3.1% da vista ainda sem textura"]`
- 6 Costas/cima: acumula no atlas: `["az 180 el 30: +20493 texels novos, sobreposição 36049, ganho RGB [1.015, 1.015, 1.015], cobertura 41.2%"]`
- 7 Frente/baixo: render parcial + máscara: `["az 0 el -30: 22.2% da vista ainda sem textura"]`
- 7 Frente/baixo: acumula no atlas: `["az 0 el -30: +94408 texels novos, sobreposição 64942, ganho RGB [1.084, 1.084, 1.084], cobertura 47.9%"]`
- 8 Costas/baixo: render parcial + máscara: `["az 180 el -30: 5.8% da vista ainda sem textura"]`
- 8 Costas/baixo: acumula no atlas: `["az 180 el -30: +20582 texels novos, sobreposição 42243, ganho RGB [1.009, 1.009, 1.009], cobertura 49.3%"]`
- 9 Rosto (zoom 3x): render parcial + máscara: `["az 0 el 0: 0.0% da vista ainda sem textura"]`
- 9 Rosto (zoom 3x): acumula no atlas: `["az 0 el 0: +44 texels novos, sobreposição 22097, ganho RGB [1.0, 1.0, 1.0], cobertura 49.3%"]`
- Conferência 3/4 (textura FINAL; magenta = buraco real): `["az 30 el 15: 0.0% da vista ainda sem textura"]`

## Conteúdo
- `comfyui.log` — saída completa do servidor
- `prompts/*.json` — cada execução: grafo API com valores, status, textos de saída, imagens
- `imagens/` — miniaturas das saídas/previews
- `eventos.jsonl` — fila, VRAM, erros