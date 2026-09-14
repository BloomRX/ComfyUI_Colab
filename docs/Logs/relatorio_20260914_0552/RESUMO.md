# Relatório da sessão ComfyUI — 2026-09-14 05:52:51

GPU: Tesla T4, 15360 MiB
VRAM pico: 7.0 GB

## Prompts executados

### 001_e93dcb27 — success — 235 nós, 31 imagem(ns)
- nós-chave: DecimateMesh, LiaPickReference, LiaProjectTextureAccumulate, LiaRenderTextured, LiaTextureFinalize, RemeshMesh, SaveGLB, UnwrapMesh
- 1 Frente: render parcial + máscara: `["az 0 el 0: 100.0% da vista ainda sem textura"]`
- 1 Frente: acumula no atlas: `["az 0 el 0: +319920 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 18.6%"]`
- 2 Costas: render parcial + máscara: `["az 180 el 0: 100.0% da vista ainda sem textura"]`
- 2 Costas: acumula no atlas: `["az 180 el 0: +297566 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 35.9%"]`
- 3 Esquerda: render parcial + máscara: `["az 90 el 0: 33.9% da vista ainda sem textura"]`
- 3 Esquerda: acumula no atlas: `["az 90 el 0: +78026 texels novos, sobreposição 148741, ganho RGB [1.146, 1.146, 1.146], cobertura 40.5%"]`
- 4 Direita: render parcial + máscara: `["az 270 el 0: 33.1% da vista ainda sem textura"]`
- 4 Direita: acumula no atlas: `["az 270 el 0: +76056 texels novos, sobreposição 159677, ganho RGB [1.103, 1.103, 1.103], cobertura 44.9%"]`
- 5 Frente/cima: render parcial + máscara: `["az 0 el 30: 2.7% da vista ainda sem textura"]`
- 5 Frente/cima: acumula no atlas: `["az 0 el 30: +9184 texels novos, sobreposição 281009, ganho RGB [0.85, 0.85, 0.85], cobertura 45.4%"]`
- 6 Costas/cima: render parcial + máscara: `["az 180 el 30: 2.2% da vista ainda sem textura"]`
- 6 Costas/cima: acumula no atlas: `["az 180 el 30: +5647 texels novos, sobreposição 258677, ganho RGB [1.049, 1.049, 1.049], cobertura 45.8%"]`
- 7 Frente/baixo: render parcial + máscara: `["az 0 el -30: 13.5% da vista ainda sem textura"]`
- 7 Frente/baixo: acumula no atlas: `["az 0 el -30: +37595 texels novos, sobreposição 253596, ganho RGB [1.167, 1.167, 1.167], cobertura 47.9%"]`
- 8 Costas/baixo: render parcial + máscara: `["az 180 el -30: 11.1% da vista ainda sem textura"]`
- 8 Costas/baixo: acumula no atlas: `["az 180 el -30: +30364 texels novos, sobreposição 262730, ganho RGB [1.145, 1.145, 1.145], cobertura 49.7%"]`
- Conferência 3/4 (textura FINAL; magenta = buraco real): `["az 30 el 15: 1.3% da vista ainda sem textura"]`

## Conteúdo
- `comfyui.log` — saída completa do servidor
- `prompts/*.json` — cada execução: grafo API com valores, status, textos de saída, imagens
- `imagens/` — miniaturas das saídas/previews
- `eventos.jsonl` — fila, VRAM, erros