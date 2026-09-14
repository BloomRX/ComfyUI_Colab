# Histórico dos relatórios de GPU (resumo — os arquivos foram removidos em v83)

Todos em Colab **Tesla T4 15 GB**, RAM 12,7 GB, ComfyUI 0.35, `--cache-none --disable-smart-memory`.
Os relatórios completos (log, JSON do grafo, PNGs; ~35 MB) ficaram no histórico do git até `190cfa0`
(`git show 190cfa0:docs/Logs/<pasta>/RESUMO.md`).

## `Lia_Texturizar` — 4 rodadas (14/09/2026)

| relatório | versão | tempo | VRAM pico | resultado |
|---|---|---|---|---|
| 0421 | v74 (v2.0) | 15m30 | 6,2 GB | cobertura 48,6 %. Costas com outra paleta, tênis brancos, buracos. → v2.1: image 3 = frente pintada, `ImageCompositeMasked`, color_match só brilho, Remesh 512, fill_only cima/baixo |
| 0522 | v2.1 | ~16m | 7,0 GB | cobertura 51,5 %. Klein pintou **rosto no topo da cabeça** nas vistas de 55°. → v2.2: vistas inclinadas ±30°, prompts "só cabelo", Finalize expõe state, fill_reach 64 |
| 0552 | v2.2 | ~16m | 7,0 GB | conferência 1,3 % faltando, mas "chuvisco" magenta por toda a vista e manchas cinzas (borda de ilha UV virava faltando). → v2.3: dilata 4 texels no render, Finalize valid = mesh + margem; UnwrapMesh adaptive testado |
| 0643 | v2.3 | ~16m | 6,9 GB | **0,0 % faltando, sem magenta — primeiro resultado utilizável**. Cobertura 48,5 %. `adaptive` deu 4266 ilhas em 82 s (pec 921) → voltou a pec (v78). Vistas 5/7 previews estranhos mas só 0,4–9 % usados |

| 1410 | v3 (v82) Klein + passe WAI-Inpaint | 28m52 | 7,1 GB | **Melhor resultado**: rosto (zoom 3×) nítido com olhos vermelhos, lados sem "escorrido", conferência 0,0 %. Bug: F2 frente 1× rodava depois do rosto e o sobrescrevia (replace) → v85: rosto é o último passe |

| 1514 | v3.1 (v86) + ControlNet normal 0,85 | 31m18 | 8,9 GB | Pior: ControlNet normal fez o WAI pintar **olhos semicerrados** (o mesh TRELLIS não tem olhos → normal map liso). Pele no cabelo continuou. **Passe WAI removido (v87)**; o rosto passa a ser uma 9ª vista Klein em zoom 3× com replace |

| 1634 | v4 (v87) + mesh novo (chifres, capa fina) | 20m06 | 7,0 GB | Silhueta em **serra** já no render da vista 1: `Remesh udf 512` + `Decimate midpoint 30k` destruíram capa/pernas finas (24 663 faces, 2289 ilhas). Pintura irrelevante. → v88: Remesh desligado por padrão, Decimate 60k QEM |

Aprendizados fixos: Klein 4B 4 passos ≈ 30–40 s por vista 1024²; Remesh+Decimate+Unwrap pec ≈ 2 min;
o rosto sai com ~150 px no atlas (motivo do passe de correção em zoom, v82).

## `Lia_Teste_QwenEdit` — A/B Klein × Qwen-Image-Edit-2509 (costas)

| relatório | config Qwen | tempo Qwen | veredito |
|---|---|---|---|
| 0919 | Q4_K_M, latente 1024, img2 = normal map | 17 min (3,1 GB offload, 200 s/passo) | tecido/cabelo melhores que Klein, mas sombra de dobras cozida, **perdeu cinto e bordado da barra** |
| 1032 | Q3_K_S, 768, img3 = crop dos ornamentos | 9 min (coube inteiro, 137 s/passo — desquantização) | ornamentos voltaram; **mudou o enquadramento** (cortou cabeça/pés) |
| 1141 | + latente = render + `SetLatentNoiseMask`, img2 = silhueta | 8m40 | Qwen quebrou (cabelo flutuando, ombros pretos — não é modelo de inpaint). Klein também ficou cinza porque perdeu o normal map (erro de setup, não do modelo) |

Conclusão (v81): Qwen-Edit fora do pipeline — sem máscara muda enquadramento, com máscara quebra, e custa 9–17 min/vista no T4.
Klein 4B em 4 vistas + WAI-Inpaint como passe de correção (v82) é o caminho. Modelos Qwen podem ser apagados do Drive (−32,6 GB).
Referência que deu o melhor Klein: `v_00067_.png` (desenho 2D limpo das costas) → ter desenho 2D por vista vale mais que trocar o pintor.
