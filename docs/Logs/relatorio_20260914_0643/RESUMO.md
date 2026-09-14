# Relatório da sessão ComfyUI — 2026-09-14 06:43:40

GPU: Tesla T4, 15360 MiB
VRAM pico: 6.9 GB

## Prompts executados

### 001_7df01742 — success — 235 nós, 31 imagem(ns)
- nós-chave: DecimateMesh, LiaPickReference, LiaProjectTextureAccumulate, LiaRenderTextured, LiaTextureFinalize, RemeshMesh, SaveGLB, UnwrapMesh
- 1 Frente: render parcial + máscara: `["az 0 el 0: 100.0% da vista ainda sem textura"]`
- 1 Frente: acumula no atlas: `["az 0 el 0: +297084 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 18.5%"]`
- 2 Costas: render parcial + máscara: `["az 180 el 0: 99.7% da vista ainda sem textura"]`
- 2 Costas: acumula no atlas: `["az 180 el 0: +280188 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 35.9%"]`
- 3 Esquerda: render parcial + máscara: `["az 90 el 0: 20.1% da vista ainda sem textura"]`
- 3 Esquerda: acumula no atlas: `["az 90 el 0: +68273 texels novos, sobreposição 78588, ganho RGB [1.136, 1.136, 1.136], cobertura 40.1%"]`
- 4 Direita: render parcial + máscara: `["az 270 el 0: 19.3% da vista ainda sem textura"]`
- 4 Direita: acumula no atlas: `["az 270 el 0: +67660 texels novos, sobreposição 76762, ganho RGB [1.09, 1.09, 1.09], cobertura 44.3%"]`
- 5 Frente/cima: render parcial + máscara: `["az 0 el 30: 0.4% da vista ainda sem textura"]`
- 5 Frente/cima: acumula no atlas: `["az 0 el 30: +4345 texels novos, sobreposição 38629, ganho RGB [0.979, 0.979, 0.979], cobertura 44.6%"]`
- 6 Costas/cima: render parcial + máscara: `["az 180 el 30: 0.3% da vista ainda sem textura"]`
- 6 Costas/cima: acumula no atlas: `["az 180 el 30: +3141 texels novos, sobreposição 21421, ganho RGB [1.018, 1.018, 1.018], cobertura 44.8%"]`
- 7 Frente/baixo: render parcial + máscara: `["az 0 el -30: 9.3% da vista ainda sem textura"]`
- 7 Frente/baixo: acumula no atlas: `["az 0 el -30: +32136 texels novos, sobreposição 73034, ganho RGB [1.027, 1.027, 1.027], cobertura 46.8%"]`
- 8 Costas/baixo: render parcial + máscara: `["az 180 el -30: 6.9% da vista ainda sem textura"]`
- 8 Costas/baixo: acumula no atlas: `["az 180 el -30: +27731 texels novos, sobreposição 73584, ganho RGB [1.039, 1.039, 1.039], cobertura 48.5%"]`
- Conferência 3/4 (textura FINAL; magenta = buraco real): `["az 30 el 15: 0.0% da vista ainda sem textura"]`

## Conteúdo
- `comfyui.log` — saída completa do servidor
- `prompts/*.json` — cada execução: grafo API com valores, status, textos de saída, imagens
- `imagens/` — miniaturas das saídas/previews
- `eventos.jsonl` — fila, VRAM, erros