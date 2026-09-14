# Relatório da sessão ComfyUI — 2026-09-14 22:00:25

GPU: Tesla T4, 15360 MiB
VRAM pico: 6.8 GB

## Prompts executados

### 001_56d1e6cc — success — 260 nós, 34 imagem(ns)
- nós-chave: DecimateMesh, LiaPickReference, LiaProjectTextureAccumulate, LiaRenderTextured, LiaTextureFinalize, SaveGLB, UnwrapMesh
- 1 Frente: render parcial + máscara: `["az 0 el 0: 100.0% da vista ainda sem textura"]`
- 1 Frente: acumula no atlas: `["az 0 el 0: +170478 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 12.0%"]`
- 2 Costas: render parcial + máscara: `["az 180 el 0: 100.0% da vista ainda sem textura"]`
- 2 Costas: acumula no atlas: `["az 180 el 0: +174945 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 24.4%"]`
- 3 Esquerda: render parcial + máscara: `["az 90 el 0: 41.1% da vista ainda sem textura"]`
- 3 Esquerda: acumula no atlas: `["az 90 el 0: +60853 texels novos, sobreposição 31211, ganho RGB [0.942, 0.942, 0.942], cobertura 28.6%"]`
- 4 Direita: render parcial + máscara: `["az 270 el 0: 38.1% da vista ainda sem textura"]`
- 4 Direita: acumula no atlas: `["az 270 el 0: +57326 texels novos, sobreposição 33094, ganho RGB [0.868, 0.868, 0.868], cobertura 32.7%"]`
- 5 Frente/cima: render parcial + máscara: `["az 0 el 30: 10.5% da vista ainda sem textura"]`
- 5 Frente/cima: acumula no atlas: `["az 0 el 30: +33699 texels novos, sobreposição 46404, ganho RGB [1.051, 1.051, 1.051], cobertura 35.1%"]`
- 6 Costas/cima: render parcial + máscara: `["az 180 el 30: 9.0% da vista ainda sem textura"]`
- 6 Costas/cima: acumula no atlas: `["az 180 el 30: +36715 texels novos, sobreposição 33353, ganho RGB [1.029, 1.029, 1.029], cobertura 37.7%"]`
- 7 Frente/baixo: render parcial + máscara: `["az 0 el -30: 30.1% da vista ainda sem textura"]`
- 7 Frente/baixo: acumula no atlas: `["az 0 el -30: +99941 texels novos, sobreposição 41018, ganho RGB [1.199, 1.199, 1.199], cobertura 44.7%"]`
- 8 Costas/baixo: render parcial + máscara: `["az 180 el -30: 7.8% da vista ainda sem textura"]`
- 8 Costas/baixo: acumula no atlas: `["az 180 el -30: +21930 texels novos, sobreposição 31925, ganho RGB [1.012, 1.012, 1.012], cobertura 46.2%"]`
- 9 Rosto (zoom 3x): render parcial + máscara: `["az 0 el 0: 0.3% da vista ainda sem textura"]`
- 9 Rosto (zoom 3x): acumula no atlas: `["az 0 el 0: +179 texels novos, sobreposição 21654, ganho RGB [1.0, 1.0, 1.0], cobertura 46.3%"]`
- Conferência 3/4 (textura FINAL; magenta = buraco real): `["az 30 el 15: 0.0% da vista ainda sem textura"]`

## Conteúdo
- `comfyui.log` — saída completa do servidor
- `prompts/*.json` — cada execução: grafo API com valores, status, textos de saída, imagens
- `imagens/` — miniaturas das saídas/previews
- `eventos.jsonl` — fila, VRAM, erros