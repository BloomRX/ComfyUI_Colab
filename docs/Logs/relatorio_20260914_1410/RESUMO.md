# Relatório da sessão ComfyUI — 2026-09-14 14:10:20

GPU: Tesla T4, 15360 MiB
VRAM pico: 7.1 GB

## Prompts executados

### 001_56b4ff0d — success — 297 nós, 41 imagem(ns)
- nós-chave: DecimateMesh, LiaPickReference, LiaProjectTextureAccumulate, LiaRenderTextured, LiaTextureFinalize, RemeshMesh, SaveGLB, UnwrapMesh
- 1 Frente: render parcial + máscara: `["az 0 el 0: 100.0% da vista ainda sem textura"]`
- 1 Frente: acumula no atlas: `["az 0 el 0: +274278 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 18.1%"]`
- 2 Costas: render parcial + máscara: `["az 180 el 0: 99.8% da vista ainda sem textura"]`
- 2 Costas: acumula no atlas: `["az 180 el 0: +266768 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 35.7%"]`
- 3 Esquerda: render parcial + máscara: `["az 90 el 0: 23.5% da vista ainda sem textura"]`
- 3 Esquerda: acumula no atlas: `["az 90 el 0: +67631 texels novos, sobreposição 77183, ganho RGB [1.137, 1.137, 1.137], cobertura 40.2%"]`
- 4 Direita: render parcial + máscara: `["az 270 el 0: 20.5% da vista ainda sem textura"]`
- 4 Direita: acumula no atlas: `["az 270 el 0: +64468 texels novos, sobreposição 68780, ganho RGB [1.079, 1.079, 1.079], cobertura 44.5%"]`
- 5 Frente/cima: render parcial + máscara: `["az 0 el 30: 0.4% da vista ainda sem textura"]`
- 5 Frente/cima: acumula no atlas: `["az 0 el 30: +3886 texels novos, sobreposição 25702, ganho RGB [0.985, 0.985, 0.985], cobertura 44.7%"]`
- 6 Costas/cima: render parcial + máscara: `["az 180 el 30: 0.4% da vista ainda sem textura"]`
- 6 Costas/cima: acumula no atlas: `["az 180 el 30: +3349 texels novos, sobreposição 28208, ganho RGB [1.005, 1.005, 1.005], cobertura 45.0%"]`
- 7 Frente/baixo: render parcial + máscara: `["az 0 el -30: 9.0% da vista ainda sem textura"]`
- 7 Frente/baixo: acumula no atlas: `["az 0 el -30: +29262 texels novos, sobreposição 57552, ganho RGB [1.038, 1.038, 1.038], cobertura 46.9%"]`
- 8 Costas/baixo: render parcial + máscara: `["az 180 el -30: 7.0% da vista ainda sem textura"]`
- 8 Costas/baixo: acumula no atlas: `["az 180 el -30: +26038 texels novos, sobreposição 57766, ganho RGB [1.048, 1.048, 1.048], cobertura 48.6%"]`
- F1 Rosto: render da textura Klein (zoom 3): `["az 0 el 0: 0.0% da vista ainda sem textura"]`
- F1 Rosto: SUBSTITUI no atlas (replace): `["az 0 el 0: +111 texels novos, sobreposição 57152, ganho RGB [1.0, 1.0, 1.0], cobertura 48.6%"]`
- F2 Frente: render da textura Klein (zoom 1): `["az 0 el 0: 0.0% da vista ainda sem textura"]`
- F2 Frente: SUBSTITUI no atlas (replace): `["az 0 el 0: +0 texels novos, sobreposição 213690, ganho RGB [1.0, 1.0, 1.0], cobertura 48.6%"]`
- F3 Costas: render da textura Klein (zoom 1): `["az 180 el 0: 0.0% da vista ainda sem textura"]`
- F3 Costas: SUBSTITUI no atlas (replace): `["az 180 el 0: +0 texels novos, sobreposição 217142, ganho RGB [1.0, 1.0, 1.0], cobertura 48.6%"]`
- F4 Esquerda: render da textura Klein (zoom 1): `["az 90 el 0: 0.0% da vista ainda sem textura"]`
- F4 Esquerda: SUBSTITUI no atlas (replace): `["az 90 el 0: +2186 texels novos, sobreposição 166654, ganho RGB [1.0, 1.0, 1.0], cobertura 48.8%"]`
- F5 Direita: render da textura Klein (zoom 1): `["az 270 el 0: 0.1% da vista ainda sem textura"]`
- F5 Direita: SUBSTITUI no atlas (replace): `["az 270 el 0: +3006 texels novos, sobreposição 162233, ganho RGB [1.0, 1.0, 1.0], cobertura 49.0%"]`
- Conferência 3/4 (textura FINAL; magenta = buraco real): `["az 30 el 15: 0.0% da vista ainda sem textura"]`

## Conteúdo
- `comfyui.log` — saída completa do servidor
- `prompts/*.json` — cada execução: grafo API com valores, status, textos de saída, imagens
- `imagens/` — miniaturas das saídas/previews
- `eventos.jsonl` — fila, VRAM, erros