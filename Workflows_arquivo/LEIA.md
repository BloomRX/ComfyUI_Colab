# Workflows arquivados

Nao aparecem na Celula 3 porque a busca e em `Workflows/**`, e esta pasta
esta fora dela. Ficam versionados no Git, so nao poluem a selecao.

## Por que cada um saiu

| workflow | motivo |
|---|---|
| `WaifuSurvivors_Animate` | Hotshot-XL reprovado (v32: cor invertida, cabeca dupla) |
| `WaifuSurvivors_AnimateSD15` | SD1.5 reprovado (v51: fidelidade 73,8 vs 9,9 do WAN) |
| `Detailer` | tutorial; util no futuro para retoque de rosto |
| `WaifuInpaintXL` | tutorial; modelo gated no HF |
| `CharDesignandPartSplitting` | tutorial; exige krea2 (27 GB) |
| `Mesh_Processing` | nao cabe no T4 (documentado) |
| `Efaces_Pony_XL_V01` | tutorial; nunca usado |
| `PotatCats-inpaint...` | tutorial; nunca usado |
| `Skintoken` | exige Blender no PATH |
| `WaifuVroid`, `WaifuVroid_FromConcept` | projeto Lia, parado |

## Para reativar

```
mv Workflows_arquivo/NOME.json Workflows/
```

Rode a C4 e a C5 depois — a C5 rebaixa os modelos que faltarem.
