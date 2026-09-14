# Relatório da sessão ComfyUI — 2026-09-14 04:21:33

GPU: Tesla T4, 15360 MiB
VRAM pico: 6.2 GB

## Prompts executados

### 001_9428baa8 — success — 211 nós, 31 imagem(ns)
- nós-chave: DecimateMesh, LiaPickReference, LiaProjectTextureAccumulate, LiaRenderTextured, LiaTextureFinalize, SaveGLB, UnwrapMesh
- 1 Frente: render parcial + máscara: `["az 0 el 0: 100.0% da vista ainda sem textura"]`
- 1 Frente: acumula no atlas: `["az 0 el 0: +262965 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 15.5%"]`
- 2 Costas: render parcial + máscara: `["az 180 el 0: 100.0% da vista ainda sem textura"]`
- 2 Costas: acumula no atlas: `["az 180 el 0: +277345 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 31.9%"]`
- 3 Esquerda: render parcial + máscara: `["az 90 el 0: 41.8% da vista ainda sem textura"]`
- 3 Esquerda: acumula no atlas: `["az 90 el 0: +81258 texels novos, sobreposição 128032, ganho RGB [1.338, 1.36, 1.375], cobertura 36.7%"]`
- 4 Direita: render parcial + máscara: `["az 270 el 0: 46.2% da vista ainda sem textura"]`
- 4 Direita: acumula no atlas: `["az 270 el 0: +83952 texels novos, sobreposição 118585, ganho RGB [1.303, 1.357, 1.377], cobertura 41.7%"]`
- 5 Frente/cima: render parcial + máscara: `["az 0 el 55: 5.7% da vista ainda sem textura"]`
- 5 Frente/cima: acumula no atlas: `["az 0 el 55: +9207 texels novos, sobreposição 223167, ganho RGB [0.734, 0.702, 0.689], cobertura 42.2%"]`
- 6 Costas/cima: render parcial + máscara: `["az 180 el 55: 2.3% da vista ainda sem textura"]`
- 6 Costas/cima: acumula no atlas: `["az 180 el 55: +2793 texels novos, sobreposição 221311, ganho RGB [1.168, 1.134, 1.083], cobertura 42.4%"]`
- 7 Frente/baixo: render parcial + máscara: `["az 0 el -50: 25.8% da vista ainda sem textura"]`
- 7 Frente/baixo: acumula no atlas: `["az 0 el -50: +55453 texels novos, sobreposição 179705, ganho RGB [1.021, 1.115, 1.214], cobertura 45.7%"]`
- 8 Costas/baixo: render parcial + máscara: `["az 180 el -50: 20.8% da vista ainda sem textura"]`
- 8 Costas/baixo: acumula no atlas: `["az 180 el -50: +50055 texels novos, sobreposição 218888, ganho RGB [1.432, 1.482, 1.416], cobertura 48.6%"]`
- Conferência 3/4 (magenta = texel nunca visto): `["az 30 el 15: 6.1% da vista ainda sem textura"]`

## Conteúdo
- `comfyui.log` — saída completa do servidor
- `prompts/*.json` — cada execução: grafo API com valores, status, textos de saída, imagens
- `imagens/` — miniaturas das saídas/previews
- `eventos.jsonl` — fila, VRAM, erros