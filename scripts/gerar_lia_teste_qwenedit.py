#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera Workflows/Lia_Teste_QwenEdit.json — teste A/B de UMA vista (costas).

Mesma máscara, mesmas referências: o Klein 4B (fluxo atual) e o
Qwen-Image-Edit-2509 Q3_K_S GGUF + LoRA Lightning 4 passos (v79: Q3_K_S cabe inteiro na VRAM do T4; latente 768; prompt anti-sombra; imagem 3 = crop dos ornamentos) pintam as costas da
Lia. Os dois resultados vão para Preview/Save lado a lado. Nada é acumulado no
atlas — é só para decidir se vale migrar o Lia_Texturizar.

Rode:  python scripts/gerar_lia_teste_qwenedit.py
"""
import json
import os
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Workflows", "Lia_Teste_QwenEdit.json")

nodes, links, lid, nid = [], [], [0], [0]
HF = "https://huggingface.co/"
LIA = "BloomRX/ComfyUI_Colab"
GGUF = "city96/ComfyUI-GGUF"
BYPASS = 4


def L(src, sslot, dst, dslot, typ):
    lid[0] += 1
    links.append([lid[0], src, sslot, dst, dslot, typ])
    return lid[0]


def N(type, pos, size, widgets=None, inputs=(), outputs=(), title=None, mode=0, props=None, color=None, cnr="comfy-core"):
    nid[0] += 1
    n = {"id": nid[0], "type": type, "pos": list(pos), "size": list(size), "flags": {}, "order": nid[0], "mode": mode,
         "inputs": [{"name": a, "type": b, "link": None} for a, b in inputs],
         "outputs": [{"name": a, "type": b, "links": []} for a, b in outputs],
         "properties": {"Node name for S&R": type, "cnr_id": cnr, "ver": "0.16.3"},
         "widgets_values": widgets if widgets is not None else []}
    if cnr != "comfy-core":
        n["properties"] = {"Node name for S&R": type, "aux_id": cnr}
    if props:
        n["properties"].update(props)
    if title:
        n["title"] = title
    if color:
        n["color"] = color[0]; n["bgcolor"] = color[1]
    nodes.append(n)
    return n


def conn(a, aslot, b, bname, typ):
    slot = [i["name"] for i in b["inputs"]].index(bname)
    k = L(a["id"], aslot, b["id"], slot, typ)
    a["outputs"][aslot]["links"].append(k)
    b["inputs"][slot]["link"] = k


def widget_in(n, name, typ):
    n["inputs"].append({"name": name, "type": typ, "widget": {"name": name}, "link": None})


def opt_in(n, name, typ):
    n["inputs"].append({"name": name, "type": typ, "link": None})


GREEN = ("#232", "#353"); BLUE = ("#223", "#335"); BROWN = ("#432", "#653"); PURPLE = ("#323", "#535"); ORANGE = ("#432", "#864")

# ---------------------------------------------------------------- 1. mesh (mesmo preparo do Lia_Texturizar) + frente pintada
X1 = -2600
load3d = N("Load3D", (X1, -700), (420, 560), ["Lia_trellis2_00001_.glb", "upload3dmodel", "uploadExtraResources", "clear", "", 1024, 1024],
           outputs=[("image", "IMAGE"), ("mask", "MASK"), ("mesh_path", "STRING"), ("normal", "IMAGE"), ("camera_info", "LOAD3D_CAMERA"),
                    ("recording_video", "VIDEO"), ("model_3d", "FILE_3D"), ("model_3d_info", "LOAD3D_MODEL_INFO")], title="GLB da Lia")
get = N("Get3DComponents", (X1 + 460, -700), (260, 46), inputs=[("model_3d", "FILE_3D")], outputs=[("mesh", "MESH")])
remesh = N("RemeshMesh", (X1 + 460, -600), (340, 300), [512, "udf", False, False, False, 1, 0, False, 3, 0.01, 20000000], inputs=[("mesh", "MESH")], outputs=[("mesh", "MESH")])
weld = N("WeldVertices", (X1 + 460, -260), (340, 82), [1e-5, 0.0], inputs=[("mesh", "MESH")], outputs=[("mesh", "MESH")])
deci = N("DecimateMesh", (X1 + 460, -150), (340, 106), [30000, "midpoint"], inputs=[("mesh", "MESH")], outputs=[("mesh", "MESH")])
unwrap = N("UnwrapMesh", (X1 + 460, -20), (340, 130), ["pec", 2048, 12, 0.001], inputs=[("mesh", "MESH")], outputs=[("mesh", "MESH")])
widget_in(unwrap, "resolution", "INT")
smooth = N("MeshSmoothNormals", (X1 + 460, 140), (340, 58), [180], inputs=[("mesh", "MESH")], outputs=[("mesh", "MESH")], title="mesh BAIXO com UV")
conn(load3d, 6, get, "model_3d", "FILE_3D"); conn(get, 0, remesh, "mesh", "MESH"); conn(remesh, 0, weld, "mesh", "MESH")
conn(weld, 0, deci, "mesh", "MESH"); conn(deci, 0, unwrap, "mesh", "MESH"); conn(unwrap, 0, smooth, "mesh", "MESH")
MESH = smooth

front = N("LoadImage", (X1, 260), (320, 360), ["Lia_front.png", "image"], outputs=[("IMAGE", "IMAGE"), ("MASK", "MASK")], title="Lia FRENTE 2D", color=GREEN)
back_ref = N("LoadImage", (X1, 660), (320, 360), ["Lia_back.png", "image"], outputs=[("IMAGE", "IMAGE"), ("MASK", "MASK")], title="Lia COSTAS 2D (opcional — Ctrl+B)", mode=BYPASS)
pick = N("LiaPickReference", (X1 + 460, 260), (300, 130), ["back"], inputs=[("front", "IMAGE")], outputs=[("image", "IMAGE"), ("used", "STRING")], cnr=LIA, title="referência das costas")
for k in ("back", "left", "right"):
    opt_in(pick, k, "IMAGE")
conn(front, 0, pick, "front", "IMAGE"); conn(back_ref, 0, pick, "back", "IMAGE")
ref_sc = N("ImageScaleToTotalPixels", (X1 + 460, 430), (300, 106), ["lanczos", 1, 1], inputs=[("image", "IMAGE")], outputs=[("IMAGE", "IMAGE")])
conn(pick, 0, ref_sc, "image", "IMAGE")

# vista de costas: render sem estado (100% faltando) + normal
ren = N("LiaRenderTextured", (X1 + 860, -700), (330, 250), [180.0, 0.0, 1024, 1.1, 12, "grey"], inputs=[("mesh", "MESH")],
        outputs=[("image", "IMAGE"), ("inpaint_mask", "MASK"), ("silhouette", "MASK"), ("normals", "IMAGE"), ("missing_fraction", "FLOAT")],
        cnr=LIA, title="Costas: render (tudo cinza) + normal map", color=BLUE)
opt_in(ren, "state", "LIA_TEXSTATE"); conn(MESH, 0, ren, "mesh", "MESH")
pvn = N("PreviewImage", (X1 + 860, -400), (330, 300), inputs=[("images", "IMAGE")], title="normal map das costas")
conn(ren, 3, pvn, "images", "IMAGE")

# "frente pintada" para image 3: aqui usamos a própria imagem 2D frontal (não há vista 1 neste teste)
PROMPT = ("back view, seen from behind. Paint this exact character from image 1 onto the pose and silhouette of the normal map in image 2. "
          "Image 2 is only a pose and shape guide: do NOT copy its shading. Image 3 shows the character's ornaments up close: keep EVERY "
          "gold trim, the gold belt line around the waist and the embroidered border along the hem, continuous all the way around the back. "
          "Flat cel-shaded albedo texture for a game: uniform flat colors, no shadows, no folds shading, no highlights, no directional lighting, "
          "no ambient occlusion, no outlines. Plain white background. Same anime art style as image 1.")
prompt = N("PrimitiveStringMultiline", (X1 + 860, 20), (330, 220), [PROMPT], outputs=[("STRING", "STRING")], title="Prompt (igual para os dois)", color=GREEN)

# ---------------------------------------------------------------- 2. A — Klein 4B (fluxo atual)
X2 = -1500
unet = N("UNETLoader", (X2, -700), (400, 82), ["flux-2-klein-4b-fp8.safetensors", "default"], outputs=[("MODEL", "MODEL")],
         props={"models": [{"name": "flux-2-klein-4b-fp8.safetensors", "url": HF + "black-forest-labs/FLUX.2-klein-4b-fp8/resolve/main/flux-2-klein-4b-fp8.safetensors", "directory": "diffusion_models"}]})
clip = N("CLIPLoader", (X2, -580), (400, 106), ["qwen_3_4b_fp8_mixed.safetensors", "flux2", "default"], outputs=[("CLIP", "CLIP")],
         props={"models": [{"name": "qwen_3_4b_fp8_mixed.safetensors", "url": HF + "Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b_fp8_mixed.safetensors", "directory": "text_encoders"}]})
vae = N("VAELoader", (X2, -440), (400, 58), ["flux2-vae.safetensors"], outputs=[("VAE", "VAE")],
        props={"models": [{"name": "flux2-vae.safetensors", "url": HF + "Comfy-Org/flux2-dev/resolve/main/split_files/vae/flux2-vae.safetensors", "directory": "vae"}]})
sched = N("Flux2Scheduler", (X2, -350), (400, 106), [4, 1024, 1024], outputs=[("SIGMAS", "SIGMAS")])
samp = N("KSamplerSelect", (X2, -210), (400, 58), ["euler"], outputs=[("SAMPLER", "SAMPLER")])
lat = N("EmptyFlux2LatentImage", (X2, -120), (400, 106), [1024, 1024, 1], outputs=[("LATENT", "LATENT")])

renc = N("VAEEncode", (X2 + 450, -700), (260, 46), inputs=[("pixels", "IMAGE"), ("vae", "VAE")], outputs=[("LATENT", "LATENT")], title="image 1 = referência")
nenc = N("VAEEncode", (X2 + 450, -620), (260, 46), inputs=[("pixels", "IMAGE"), ("vae", "VAE")], outputs=[("LATENT", "LATENT")], title="image 2 = normal")
fenc = N("VAEEncode", (X2 + 450, -540), (260, 46), inputs=[("pixels", "IMAGE"), ("vae", "VAE")], outputs=[("LATENT", "LATENT")], title="image 3 = frente")
conn(ref_sc, 0, renc, "pixels", "IMAGE"); conn(vae, 0, renc, "vae", "VAE")
conn(ren, 3, nenc, "pixels", "IMAGE"); conn(vae, 0, nenc, "vae", "VAE")
fsc0 = N("ImageScale", (X1 + 860, 280), (330, 130), ["lanczos", 1024, 1024, "center"], inputs=[("image", "IMAGE")], outputs=[("IMAGE", "IMAGE")], title="frente 1024² (corte central)")
fsc = N("ImageCrop", (X1 + 860, 450), (330, 130), [1024, 640, 0, 384], inputs=[("image", "IMAGE")], outputs=[("IMAGE", "IMAGE")], title="image 3 = cintura→barra (ornamentos)")
conn(front, 0, fsc0, "image", "IMAGE"); conn(fsc0, 0, fsc, "image", "IMAGE"); conn(fsc, 0, fenc, "pixels", "IMAGE"); conn(vae, 0, fenc, "vae", "VAE")
pvc = N("PreviewImage", (X1 + 860, 620), (330, 240), inputs=[("images", "IMAGE")], title="confira: cintura e barra visíveis?")
conn(fsc, 0, pvc, "images", "IMAGE")
te = N("CLIPTextEncode", (X2 + 450, -320), (260, 80), [""], inputs=[("clip", "CLIP")], outputs=[("CONDITIONING", "CONDITIONING")]); widget_in(te, "text", "STRING")
zo = N("ConditioningZeroOut", (X2 + 450, -200), (260, 26), inputs=[("conditioning", "CONDITIONING")], outputs=[("CONDITIONING", "CONDITIONING")])
conn(clip, 0, te, "clip", "CLIP"); conn(prompt, 0, te, "text", "STRING"); conn(te, 0, zo, "conditioning", "CONDITIONING")


def refchain(cond, x, yy, sign):
    prev = cond
    for j, (lat_node, nm) in enumerate([(renc, "ref"), (nenc, "normal"), (fenc, "frente")]):
        r = N("ReferenceLatent", (x, yy + j * 60), (240, 46), inputs=[("conditioning", "CONDITIONING"), ("latent", "LATENT")], outputs=[("CONDITIONING", "CONDITIONING")], title=f"{nm} {sign}")
        conn(prev, 0, r, "conditioning", "CONDITIONING"); conn(lat_node, 0, r, "latent", "LATENT"); prev = r
    return prev


rp = refchain(te, X2 + 760, -700, "+")
rn = refchain(zo, X2 + 760, -480, "−")
gd = N("CFGGuider", (X2 + 1040, -700), (260, 98), [1], inputs=[("model", "MODEL"), ("positive", "CONDITIONING"), ("negative", "CONDITIONING")], outputs=[("GUIDER", "GUIDER")])
nz = N("RandomNoise", (X2 + 1040, -560), (260, 82), [201, "fixed"], outputs=[("NOISE", "NOISE")])
sca = N("SamplerCustomAdvanced", (X2 + 1340, -700), (280, 120), inputs=[("noise", "NOISE"), ("guider", "GUIDER"), ("sampler", "SAMPLER"), ("sigmas", "SIGMAS"), ("latent_image", "LATENT")],
        outputs=[("output", "LATENT"), ("denoised_output", "LATENT")])
dec = N("VAEDecode", (X2 + 1340, -540), (280, 46), inputs=[("samples", "LATENT"), ("vae", "VAE")], outputs=[("IMAGE", "IMAGE")])
conn(unet, 0, gd, "model", "MODEL"); conn(rp, 0, gd, "positive", "CONDITIONING"); conn(rn, 0, gd, "negative", "CONDITIONING")
conn(nz, 0, sca, "noise", "NOISE"); conn(gd, 0, sca, "guider", "GUIDER"); conn(samp, 0, sca, "sampler", "SAMPLER"); conn(sched, 0, sca, "sigmas", "SIGMAS"); conn(lat, 0, sca, "latent_image", "LATENT")
conn(sca, 0, dec, "samples", "LATENT"); conn(vae, 0, dec, "vae", "VAE")
pvA = N("PreviewImage", (X2 + 1660, -700), (420, 420), inputs=[("images", "IMAGE")], title="A — Klein 4B (costas)")
svA = N("SaveImage", (X2 + 1660, -240), (420, 100), ["3d/Lia/teste_costas_A_klein"], inputs=[("images", "IMAGE")])
conn(dec, 0, pvA, "images", "IMAGE"); conn(dec, 0, svA, "images", "IMAGE")

# ---------------------------------------------------------------- 3. B — Qwen-Image-Edit-2509 Q4_K_M GGUF + Lightning 4 passos
Y = 300
qunet = N("UnetLoaderGGUF", (X2, Y), (400, 58), ["Qwen-Image-Edit-2509-Q3_K_S.gguf"], outputs=[("MODEL", "MODEL")], cnr=GGUF,
          props={"models": [{"name": "Qwen-Image-Edit-2509-Q3_K_S.gguf", "url": HF + "QuantStack/Qwen-Image-Edit-2509-GGUF/resolve/main/Qwen-Image-Edit-2509-Q3_K_S.gguf", "directory": "unet"}]},
          title="Qwen-Image-Edit-2509 Q3_K_S (9,0 GB — cabe inteiro no T4)")
qlora = N("LoraLoaderModelOnly", (X2, Y + 90), (400, 82), ["Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors", 1.0], inputs=[("model", "MODEL")], outputs=[("MODEL", "MODEL")],
          props={"models": [{"name": "Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors", "url": HF + "lightx2v/Qwen-Image-Lightning/resolve/main/Qwen-Image-Edit-2509/Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors", "directory": "loras"}]},
          title="Lightning 4 passos (0,85 GB)")
qclip = N("CLIPLoader", (X2, Y + 210), (400, 106), ["qwen_2.5_vl_7b_fp8_scaled.safetensors", "qwen_image", "default"], outputs=[("CLIP", "CLIP")],
          props={"models": [{"name": "qwen_2.5_vl_7b_fp8_scaled.safetensors", "url": HF + "Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors", "directory": "text_encoders"}]},
          title="Qwen2.5-VL 7B fp8 (9,4 GB) — encoder do Qwen-Image")
qvae = N("VAELoader", (X2, Y + 350), (400, 58), ["qwen_image_vae.safetensors"], outputs=[("VAE", "VAE")],
         props={"models": [{"name": "qwen_image_vae.safetensors", "url": HF + "Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors", "directory": "vae"}]})
qms = N("ModelSamplingAuraFlow", (X2 + 450, Y), (260, 58), [3.0], inputs=[("model", "MODEL")], outputs=[("MODEL", "MODEL")])
qcfg = N("CFGNorm", (X2 + 450, Y + 90), (260, 82), [1.0, False], inputs=[("model", "MODEL")], outputs=[("MODEL", "MODEL")])
conn(qunet, 0, qlora, "model", "MODEL"); conn(qlora, 0, qms, "model", "MODEL"); conn(qms, 0, qcfg, "model", "MODEL")
qpos = N("TextEncodeQwenImageEditPlus", (X2 + 450, Y + 210), (300, 170), [""], inputs=[("clip", "CLIP"), ("vae", "VAE"), ("image1", "IMAGE"), ("image2", "IMAGE"), ("image3", "IMAGE")],
         outputs=[("CONDITIONING", "CONDITIONING")], title="positivo (img1 ref, img2 normal, img3 frente)")
widget_in(qpos, "prompt", "STRING")
qneg = N("TextEncodeQwenImageEditPlus", (X2 + 450, Y + 420), (300, 170), [""], inputs=[("clip", "CLIP"), ("vae", "VAE"), ("image1", "IMAGE"), ("image2", "IMAGE"), ("image3", "IMAGE")],
         outputs=[("CONDITIONING", "CONDITIONING")], title="negativo (vazio, mesmas imagens)")
widget_in(qneg, "prompt", "STRING")
for q in (qpos, qneg):
    conn(qclip, 0, q, "clip", "CLIP"); conn(qvae, 0, q, "vae", "VAE")
    conn(ref_sc, 0, q, "image1", "IMAGE"); conn(ren, 3, q, "image2", "IMAGE"); conn(fsc, 0, q, "image3", "IMAGE")
conn(prompt, 0, qpos, "prompt", "STRING")
qlat = N("EmptySD3LatentImage", (X2 + 800, Y + 420), (260, 106), [768, 768, 1], outputs=[("LATENT", "LATENT")])
qks = N("KSampler", (X2 + 800, Y), (300, 260), [201, "fixed", 4, 1.0, "euler", "simple", 1.0],
        inputs=[("model", "MODEL"), ("positive", "CONDITIONING"), ("negative", "CONDITIONING"), ("latent_image", "LATENT")], outputs=[("LATENT", "LATENT")])
qdec = N("VAEDecode", (X2 + 1340, Y), (280, 46), inputs=[("samples", "LATENT"), ("vae", "VAE")], outputs=[("IMAGE", "IMAGE")])
conn(qcfg, 0, qks, "model", "MODEL"); conn(qpos, 0, qks, "positive", "CONDITIONING"); conn(qneg, 0, qks, "negative", "CONDITIONING"); conn(qlat, 0, qks, "latent_image", "LATENT")
conn(qks, 0, qdec, "samples", "LATENT"); conn(qvae, 0, qdec, "vae", "VAE")
pvB = N("PreviewImage", (X2 + 1660, Y), (420, 420), inputs=[("images", "IMAGE")], title="B — Qwen-Image-Edit Q3_K_S 768 (costas)")
svB = N("SaveImage", (X2 + 1660, Y + 460), (420, 100), ["3d/Lia/teste_costas_B_qwenedit"], inputs=[("images", "IMAGE")])
conn(qdec, 0, pvB, "images", "IMAGE"); conn(qdec, 0, svB, "images", "IMAGE")

N("MarkdownNote", (X1 - 720, -700), (680, 900), ["""# Teste A/B v2 — Klein 4B × Qwen-Image-Edit-2509 (costas da Lia)

Rodada 1 (relatório 0919, Q4_K_M, 1024): Qwen preservou tecido/cabelo muito melhor, mas (a) pintou **sombra das dobras** (luz cozida no albedo — ruim para VRM), (b) perdeu o **cinto dourado e o bordado da barra**, (c) levou **17 min** porque o Q4 não coube na VRAM (200 s/passo).

## O que mudou nesta v2
- **Q3_K_S** (9,0 GB) → cabe inteiro nos ~9,6 GB usáveis do T4; meta: < 1 min/passo.
- latente **768²** (VRAM) — o Klein continua em 1024 para comparar com a rodada anterior.
- prompt: "image 2 é só guia de pose, não copie o sombreado"; "mantenha TODA linha dourada da cintura e o bordado da barra"; "flat cel-shaded albedo".
- **imagem 3 = crop cintura→barra** da frente 2D (o encoder VL vê as imagens em 384²; a frente inteira apagava o ornamento). Confira no preview se cintura e barra aparecem; se a sua imagem tiver outro enquadramento, ajuste `y`/`height` no `ImageCrop`.

## Espaço no Drive
| arquivo | pasta | GB |
|---|---|---|
| Qwen-Image-Edit-2509-**Q3_K_S**.gguf | unet | 9,0 |
| qwen_2.5_vl_7b_fp8_scaled.safetensors | text_encoders | 9,4 (já baixado) |
| qwen_image_vae.safetensors | vae | 0,25 (já) |
| Lightning 4 passos bf16 | loras | 0,85 (já) |

O `Q4_K_M` (13,1 GB) pode ser apagado de `models/unet` depois deste teste.

## Critério
- B sem sombra de dobra + cinto/barra presentes + ≤ 4 min → migro as 4 vistas principais do `Lia_Texturizar` para o Qwen (inclinadas ficam no Klein).
- Se o Q3 perder muito detalhe, próximo passo é Q4_K_S com latente 768 (12,2 GB, ainda parcial).
"""], title="LEIA-ME", color=BROWN)

groups = [
    {"id": 1, "title": "1. Mesh + vista de costas + referências", "bounding": [X1 - 20, -780, 1260, 1850], "color": "#3f789e", "flags": {}},
    {"id": 2, "title": "A — Flux.2 Klein 4B (atual)", "bounding": [X2 - 20, -780, 2140, 1000], "color": "#8A8", "flags": {}},
    {"id": 3, "title": "B — Qwen-Image-Edit-2509 Q3_K_S + Lightning 4 passos (768)", "bounding": [X2 - 20, Y - 60, 2140, 700], "color": "#b58b2a", "flags": {}},
]
wf = {"id": str(uuid.uuid4()), "revision": 0, "last_node_id": nid[0], "last_link_id": lid[0], "nodes": nodes, "links": links,
      "groups": groups, "config": {}, "extra": {"ds": {"scale": 0.35, "offset": [3400, 850]}, "frontendVersion": "1.49.6"}, "version": 0.4}
json.dump(wf, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("ok", nid[0], "nodes", lid[0], "links ->", OUT)
