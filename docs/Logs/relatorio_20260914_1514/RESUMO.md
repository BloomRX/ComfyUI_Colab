# Relatório da sessão ComfyUI — 2026-09-14 15:14:57

GPU: Tesla T4, 15360 MiB
VRAM pico: 8.9 GB

## Prompts executados

### 001_289432fb — success — 304 nós, 41 imagem(ns)
- nós-chave: DecimateMesh, LiaPickReference, LiaProjectTextureAccumulate, LiaRenderTextured, LiaTextureFinalize, RemeshMesh, SaveGLB, UnwrapMesh
- 1 Frente: render parcial + máscara: `["az 0 el 0: 100.0% da vista ainda sem textura"]`
- 1 Frente: acumula no atlas: `["az 0 el 0: +271961 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 18.2%"]`
- 2 Costas: render parcial + máscara: `["az 180 el 0: 99.7% da vista ainda sem textura"]`
- 2 Costas: acumula no atlas: `["az 180 el 0: +267919 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 36.1%"]`
- 3 Esquerda: render parcial + máscara: `["az 90 el 0: 19.7% da vista ainda sem textura"]`
- 3 Esquerda: acumula no atlas: `["az 90 el 0: +64466 texels novos, sobreposição 71001, ganho RGB [1.124, 1.124, 1.124], cobertura 40.4%"]`
- 4 Direita: render parcial + máscara: `["az 270 el 0: 21.6% da vista ainda sem textura"]`
- 4 Direita: acumula no atlas: `["az 270 el 0: +66425 texels novos, sobreposição 72399, ganho RGB [1.1, 1.1, 1.1], cobertura 44.8%"]`
- 5 Frente/cima: render parcial + máscara: `["az 0 el 30: 0.4% da vista ainda sem textura"]`
- 5 Frente/cima: acumula no atlas: `["az 0 el 30: +3722 texels novos, sobreposição 26684, ganho RGB [0.985, 0.985, 0.985], cobertura 45.1%"]`
- 6 Costas/cima: render parcial + máscara: `["az 180 el 30: 0.4% da vista ainda sem textura"]`
- 6 Costas/cima: acumula no atlas: `["az 180 el 30: +3061 texels novos, sobreposição 21405, ganho RGB [1.01, 1.01, 1.01], cobertura 45.3%"]`
- 7 Frente/baixo: render parcial + máscara: `["az 0 el -30: 9.1% da vista ainda sem textura"]`
- 7 Frente/baixo: acumula no atlas: `["az 0 el -30: +29929 texels novos, sobreposição 58206, ganho RGB [1.047, 1.047, 1.047], cobertura 47.3%"]`
- 8 Costas/baixo: render parcial + máscara: `["az 180 el -30: 6.9% da vista ainda sem textura"]`
- 8 Costas/baixo: acumula no atlas: `["az 180 el -30: +26089 texels novos, sobreposição 58195, ganho RGB [1.027, 1.027, 1.027], cobertura 49.0%"]`
- F1 Frente: render da textura Klein (zoom 1): `["az 0 el 0: 0.1% da vista ainda sem textura"]`
- F1 Frente: SUBSTITUI no atlas (replace): `["az 0 el 0: +0 texels novos, sobreposição 198830, ganho RGB [1.0, 1.0, 1.0], cobertura 49.0%"]`
- F2 Costas: render da textura Klein (zoom 1): `["az 180 el 0: 0.0% da vista ainda sem textura"]`
- F2 Costas: SUBSTITUI no atlas (replace): `["az 180 el 0: +0 texels novos, sobreposição 202206, ganho RGB [1.0, 1.0, 1.0], cobertura 49.0%"]`
- F3 Esquerda: render da textura Klein (zoom 1): `["az 90 el 0: 0.0% da vista ainda sem textura"]`
- F3 Esquerda: SUBSTITUI no atlas (replace): `["az 90 el 0: +2037 texels novos, sobreposição 160057, ganho RGB [1.0, 1.0, 1.0], cobertura 49.2%"]`
- F4 Direita: render da textura Klein (zoom 1): `["az 270 el 0: 0.0% da vista ainda sem textura"]`
- F4 Direita: SUBSTITUI no atlas (replace): `["az 270 el 0: +2611 texels novos, sobreposição 148102, ganho RGB [1.0, 1.0, 1.0], cobertura 49.3%"]`
- F5 Rosto: render da textura Klein (zoom 3): `["az 0 el 0: 0.0% da vista ainda sem textura"]`
- F5 Rosto: SUBSTITUI no atlas (replace): `["az 0 el 0: +90 texels novos, sobreposição 50850, ganho RGB [1.0, 1.0, 1.0], cobertura 49.3%"]`
- Conferência 3/4 (textura FINAL; magenta = buraco real): `["az 30 el 15: 0.0% da vista ainda sem textura"]`

## Conteúdo
- `comfyui.log` — saída completa do servidor
- `prompts/*.json` — cada execução: grafo API com valores, status, textos de saída, imagens
- `imagens/` — miniaturas das saídas/previews
- `eventos.jsonl` — fila, VRAM, erros