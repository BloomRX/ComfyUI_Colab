# O que fica no Drive e o que NÃO fica

## Regra geral

| Critério | Onde vive |
|---|---|
| Grande + demora pra baixar + não muda | **Drive** (modelos) |
| Você não pode perder | **Drive** (outputs, inputs) |
| Reproduzível com 1 comando em 1 min | **/content** (código, venv) |
| Versionável em texto | **Git** (workflows, registry) |

---

## ✅ FICA no Drive — `MyDrive/ComfyUI_Data/`

```
ComfyUI_Data/
├── models/            ← 95% do espaço. O que dói rebaixar.
│   ├── diffusion_models/   krea2, flux-2-klein-9b...
│   ├── text_encoders/      qwen3vl_4b, qwen_3_8b...
│   ├── vae/                qwen_image_vae, flux2-vae, wan_2.1_vae
│   ├── loras/              krea2_turbo_lora, Alb_LoRaV3, Detailer-KREA2
│   ├── skintoken/          grpo_1400.ckpt
│   ├── trellis2/           pesos do TRELLIS.2
│   └── birefnet/           birefnet.safetensors
├── output/            ← suas imagens/meshes gerados
├── input/             ← imagens e meshes de entrada
├── user/              ← settings da UI + workflows salvos DENTRO do ComfyUI
└── node_cache/        ← ver aviso abaixo
```

## ❌ NÃO fica no Drive

| Item | Por quê | Onde fica |
|---|---|---|
| `ComfyUI/` (código) | milhares de arquivos pequenos; FUSE torna o boot lento demais | `/content/ComfyUI`, reclonado em ~1 min |
| `custom_nodes/` | idem, e ainda quebra em update | `/content`, reinstalado pela Célula 4 |
| `venv` / `site-packages` | nunca ponha env Python no Drive | ambiente do Colab |
| `.git` dos repos de node | lixo puro | — |
| `temp/`, `__pycache__` | descartável | local |
| **Workflows** | são texto, versionar é melhor | **Git**, pasta `Workflows/` |

### Aviso sobre `node_cache/`
Eu tinha colocado cache dos repos de custom node no Drive. **Para o seu caso, desligue.**
O TRELLIS2 compila extensões CUDA (`nvdiffrast`, `cumesh`, `flex_gemm`) contra a
versão exata de torch/CUDA da sessão. Cachear isso no Drive guarda binário que
provavelmente não serve na próxima sessão — ocupa GB e ainda dá erro obscuro.
Melhor reclonar. Só vale cache para nodes puros em Python.

---

## Sobre a pasta antiga

**Sim, pode apagar `MyDrive/ComfyUI/` — mas salve os modelos antes.** Nunca apague direto.

```python
# Ver o que tem lá antes de qualquer coisa
!du -sh /content/drive/MyDrive/ComfyUI/* | sort -h
!find /content/drive/MyDrive/ComfyUI/models -size +50M
```

Passos:
1. **Mova os modelos** para a estrutura nova (mover no mesmo Drive é instantâneo,
   não re-upa nada):
   ```python
   !mkdir -p /content/drive/MyDrive/ComfyUI_Data
   !mv /content/drive/MyDrive/ComfyUI/models /content/drive/MyDrive/ComfyUI_Data/models
   ```
2. **Salve outputs e inputs** que você queira manter (`output/`, `input/`).
3. **Confira workflows** dentro de `ComfyUI/user/default/workflows/` — se tiver algo
   que não está no Git, copie para `Workflows/` e commite.
4. Aí sim apague `custom_nodes/` e o resto:
   ```python
   !rm -rf /content/drive/MyDrive/ComfyUI
   ```

Apagar `custom_nodes/` do Drive é a maior economia: 20 repos com `.git` completo
costumam dar vários GB, e são 100% descartáveis.

Atenção: a Lixeira do Google Drive **conta na sua cota**. Depois de apagar,
esvazie a lixeira, senão o espaço não volta.

---

## VRAM dos seus 3 workflows

Sua estimativa de 6 GB não bate com o que os workflows pedem:

| Workflow | Modelos | Realidade |
|---|---|---|
| `CharDesignandPartSplitting` | krea2 int8 + qwen3vl_4b fp8 | ~8–10 GB. Cabe no T4 com `lowvram`. |
| `Mesh_Processing` | flux-2-klein-9b + qwen_3_8b fp8 + TRELLIS2 | **9B + 8B na mesma sessão.** Não roda em T4. Precisa de A100. |
| `Skintoken` | grpo_1400.ckpt (Qwen3-0.6B) | ~4 GB, leve. Mas exige **Blender 4.0+** instalado. |

Ou seja: mais um motivo forte para uma sessão por workflow — e o `Mesh_Processing`
não é questão de organização, é questão de não caber mesmo em GPU pequena.
