# Relatório da sessão ComfyUI — 2026-09-14 16:34:26

GPU: Tesla T4, 15360 MiB
VRAM pico: 7.0 GB

## Prompts executados

### 001_4c39a20c — success — 57 nós, 9 imagem(ns)
- nós-chave: DecimateMesh, RemeshMesh, SaveGLB, UnwrapMesh
- Visualizar 3D (Avançado): `["preview3d_advanced_976436f692ef4caaba204ebea314d5b1.glb [temp]", {"position": {"x": 10, "y": 10, "z": 10.000000000000002}, "target": {"x": 0, "y": 0, "z": 0}, "zoom": 1, "cameraType": "perspective", "quaternion": {"x": -0.2798481423331213, "y": 0.3647051996310008, "z": 0.11591689595929511, "w": 0.`
- Obter informações da malha: `["Vertices:   4,563,598 (4.56M)\nFaces:      9,393,144 (9.39M)\nAttributes: none"]`
- Visualizar 3D (Avançado): `["preview3d_advanced_59e08d7083d34ef2b5687fad704f0f1d.glb [temp]", {"position": {"x": 10, "y": 10, "z": 10.000000000000002}, "target": {"x": 0, "y": 0, "z": 0}, "zoom": 1, "cameraType": "perspective", "quaternion": {"x": -0.2798481423331213, "y": 0.3647051996310008, "z": 0.11591689595929511, "w": 0.`
- Visualizar 3D (Avançado): `["preview3d_advanced_6bdec9a472cd4834a721e3fcc082d7fa.glb [temp]", {"position": {"x": 10, "y": 10, "z": 10.000000000000002}, "target": {"x": 0, "y": 0, "z": 0}, "zoom": 1, "cameraType": "perspective", "quaternion": {"x": -0.2798481423331213, "y": 0.3647051996310008, "z": 0.11591689595929511, "w": 0.`

### 002_f6274696 — success — 261 nós, 34 imagem(ns)
- nós-chave: DecimateMesh, LiaPickReference, LiaProjectTextureAccumulate, LiaRenderTextured, LiaTextureFinalize, RemeshMesh, SaveGLB, UnwrapMesh
- 1 Frente: render parcial + máscara: `["az 0 el 0: 100.0% da vista ainda sem textura"]`
- 1 Frente: acumula no atlas: `["az 0 el 0: +212301 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 14.9%"]`
- 2 Costas: render parcial + máscara: `["az 180 el 0: 81.0% da vista ainda sem textura"]`
- 2 Costas: acumula no atlas: `["az 180 el 0: +261674 texels novos, sobreposição 0, ganho RGB [1.0, 1.0, 1.0], cobertura 33.3%"]`
- 3 Esquerda: render parcial + máscara: `["az 90 el 0: 59.9% da vista ainda sem textura"]`
- 3 Esquerda: acumula no atlas: `["az 90 el 0: +86160 texels novos, sobreposição 71775, ganho RGB [0.914, 0.914, 0.914], cobertura 39.3%"]`
- 4 Direita: render parcial + máscara: `["az 270 el 0: 45.6% da vista ainda sem textura"]`
- 4 Direita: acumula no atlas: `["az 270 el 0: +80784 texels novos, sobreposição 70801, ganho RGB [1.06, 1.06, 1.06], cobertura 45.0%"]`
- 5 Frente/cima: render parcial + máscara: `["az 0 el 30: 38.1% da vista ainda sem textura"]`
- 5 Frente/cima: acumula no atlas: `["az 0 el 30: +36362 texels novos, sobreposição 157565, ganho RGB [0.85, 0.85, 0.85], cobertura 47.5%"]`
- 6 Costas/cima: render parcial + máscara: `["az 180 el 30: 23.9% da vista ainda sem textura"]`
- 6 Costas/cima: acumula no atlas: `["az 180 el 30: +47955 texels novos, sobreposição 201955, ganho RGB [1.115, 1.115, 1.115], cobertura 50.9%"]`
- 7 Frente/baixo: render parcial + máscara: `["az 0 el -30: 34.7% da vista ainda sem textura"]`
- 7 Frente/baixo: acumula no atlas: `["az 0 el -30: +69607 texels novos, sobreposição 151216, ganho RGB [1.016, 1.016, 1.016], cobertura 55.8%"]`
- 8 Costas/baixo: render parcial + máscara: `["az 180 el -30: 20.7% da vista ainda sem textura"]`
- 8 Costas/baixo: acumula no atlas: `["az 180 el -30: +45194 texels novos, sobreposição 169917, ganho RGB [1.2, 1.2, 1.2], cobertura 59.0%"]`
- 9 Rosto (zoom 3x): render parcial + máscara: `["az 0 el 0: 2.8% da vista ainda sem textura"]`
- 9 Rosto (zoom 3x): acumula no atlas: `["az 0 el 0: +105 texels novos, sobreposição 15933, ganho RGB [1.0, 1.0, 1.0], cobertura 59.0%"]`
- Conferência 3/4 (textura FINAL; magenta = buraco real): `["az 30 el 15: 0.0% da vista ainda sem textura"]`

## Conteúdo
- `comfyui.log` — saída completa do servidor
- `prompts/*.json` — cada execução: grafo API com valores, status, textos de saída, imagens
- `imagens/` — miniaturas das saídas/previews
- `eventos.jsonl` — fila, VRAM, erros