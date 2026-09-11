# Índice de licenças

Gerado por `scripts/coletar_licencas.py` a partir das respostas
cruas das APIs oficiais, arquivadas em `evidencias/`.
**Não edite à mão.**

| arquivo / pacote | licença | verificado | fonte |
|---|---|---|---|
| `CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors` | apache-2.0 | 2026-09-08 | HF: h94/IP-Adapter |
| `birefnet.safetensors` | mit | 2026-09-11 | HF: Comfy-Org/BiRefNet (base ZhengPeng7/BiRefNet: mit) |
| `dino_v3_L_naf_fp32.safetensors` | mit (repack) / **DINOv3 License** (original) | 2026-09-11 | HF: Comfy-Org/Pixal3D ← facebook/dinov3-vitl16-pretrain-lvd1689m |
| `pixal3d_multiview_int8_convrot.safetensors` | mit | 2026-09-11 | HF: Comfy-Org/Pixal3D (base TencentARC/Pixal3D: mit) |
| `trellis_2_int8_convrot.safetensors` | mit | 2026-09-11 | HF: Comfy-Org/TRELLIS.2 (base microsoft/TRELLIS.2-4B: mit) |
| `trellis_2_shape_vae_bf16.safetensors` | mit | 2026-09-11 | HF: Comfy-Org/Pixal3D |
| `trellis_2_texture_vae_bf16.safetensors` | mit | 2026-09-11 | HF: Comfy-Org/Pixal3D |
| `Comfy-Org/ComfyUI-Manager` | GPL-3.0 | 2026-09-10 | GH: Comfy-Org/ComfyUI-Manager |
| `Kosinkadink/ComfyUI-Advanced-ControlNet` | GPL-3.0 | 2026-09-10 | GH: Kosinkadink/ComfyUI-Advanced-ControlNet |
| `Kosinkadink/ComfyUI-AnimateDiff-Evolved` | Apache-2.0 | 2026-09-10 | GH: Kosinkadink/ComfyUI-AnimateDiff-Evolved |
| `Kosinkadink/ComfyUI-VideoHelperSuite` | GPL-3.0 | 2026-09-10 | GH: Kosinkadink/ComfyUI-VideoHelperSuite |
| `comfyanonymous/ComfyUI` | GPL-3.0 | 2026-09-10 | GH: comfyanonymous/ComfyUI |
| `controlnet-union-sdxl-1.0.safetensors` | apache-2.0 | 2026-09-08 | HF: xinsir/controlnet-union-sdxl-1.0 |
| `cubiq/ComfyUI_IPAdapter_plus` | GPL-3.0 | 2026-09-10 | GH: cubiq/ComfyUI_IPAdapter_plus |
| `hsxl_temporal_layers.f16.safetensors` | openrail++ | 2026-09-08 | HF: hotshotco/Hotshot-XL |
| `ip-adapter-plus_sd15.safetensors` | apache-2.0 | 2026-09-08 | HF: h94/IP-Adapter |
| `ip-adapter-plus_sdxl_vit-h.safetensors` | apache-2.0 | 2026-09-08 | HF: h94/IP-Adapter |
| `john-mnz/ComfyUI-Inspyrenet-Rembg` | MIT | 2026-09-10 | GH: john-mnz/ComfyUI-Inspyrenet-Rembg |
| `mirabarukaso/ComfyUI_Mira` | MIT | 2026-09-10 | GH: mirabarukaso/ComfyUI_Mira |
| `mirabarukaso/character_select_stand_alone_app` | MIT | 2026-09-10 | GH: mirabarukaso/character_select_stand_alone_app |
| `toonyou_beta6.safetensors` | (NAO DECLARADA no mirror) | 2026-09-08 | HF: frankjoshua/toonyou_beta6 |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | apache-2.0 | 2026-09-08 | HF: Comfy-Org/Wan_2.2_ComfyUI_Repackaged |
| `v3_sd15_mm.ckpt` | apache-2.0 | 2026-09-08 | HF: guoyww/animatediff |
| `v3_sd15_sparsectrl_rgb.ckpt` | apache-2.0 | 2026-09-08 | HF: guoyww/animatediff |
| `waiIllustriousSDXL_v170.safetensors` | Fair AI Public License 1.0-SD | 2026-09-10 | Civitai: 827184 |
| `wan2.2_ti2v_5B_fp16.safetensors` | apache-2.0 | 2026-09-08 | HF: Comfy-Org/Wan_2.2_ComfyUI_Repackaged |
| `wan2.2_vae.safetensors` | apache-2.0 | 2026-09-08 | HF: Comfy-Org/Wan_2.2_ComfyUI_Repackaged |

## Atenção

- **`dino_v3_L_naf_fp32.safetensors`**: o repack diz MIT, mas os pesos derivam do DINOv3 da Meta (licenca propria, comercial OK, exige credito "Built with DINOv3" ao redistribuir). Ver LICENCAS.md §7.

- **`toonyou_beta6.safetensors`**: Mirror de um modelo do Civitai. Licenca nao declarada no HF. REPROVADO na v51; se voltar a usar, verificar no Civitai original.
- **`hsxl_temporal_layers.f16.safetensors`**: NAO e Apache. CreativeML OpenRAIL++-M tem clausulas de uso proibido.
