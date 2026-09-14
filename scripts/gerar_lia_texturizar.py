#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera Workflows/Lia_Texturizar.json (v2 — projeta-e-completa sequencial).

Arquitetura (o mesmo princípio do Modddif / TEXTure, só com nós):
  1. Retopologia "game-ready": Remesh (opcional) → Decimate → UnwrapMesh (UV novo) → normais
     suaves; normal map + AO bakeados do mesh original (alto) para o baixo.
  2. Para cada vista, em ORDEM: `LiaRenderTextured` mostra o que já foi pintado + máscara do
     que falta; o Flux.2 Klein 4B faz inpaint só do que falta (image1 = referência da vista,
     image2 = normal map, latente = render parcial + SetLatentNoiseMask); a vista pintada volta
     para o atlas com `LiaProjectTextureAccumulate` (correção de tom contra o já pintado).
  3. `LiaTextureFinalize` → ApplyTextureToMesh (+ normal map + AO) → SaveGLB / PNGs.

Rode:  python scripts/gerar_lia_texturizar.py
"""
import json
import os
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "Workflows", "Lia_Texturizar.json")

nodes, links, lid, nid = [], [], [0], [0]
HF = "https://huggingface.co/"
LIA = "BloomRX/ComfyUI_Colab"
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


GREEN = ("#232", "#353"); BLUE = ("#223", "#335"); BROWN = ("#432", "#653"); PURPLE = ("#323", "#535")

# ---------------------------------------------------------------- 1. mesh + retopo game-ready
X1 = -3000
load3d = N("Load3D", (X1, -700), (420, 560), ["Lia_trellis2_00001_.glb", "upload3dmodel", "uploadExtraResources", "clear", "", 1024, 1024],
           outputs=[("image", "IMAGE"), ("mask", "MASK"), ("mesh_path", "STRING"), ("normal", "IMAGE"), ("camera_info", "LOAD3D_CAMERA"),
                    ("recording_video", "VIDEO"), ("model_3d", "FILE_3D"), ("model_3d_info", "LOAD3D_MODEL_INFO")],
           title="GLB da Lia (Trellis2 / Pixal3D)")
get = N("Get3DComponents", (X1 + 460, -700), (260, 46), inputs=[("model_3d", "FILE_3D")], outputs=[("mesh", "MESH")], title="mesh ALTO (original)")
remesh = N("RemeshMesh", (X1 + 460, -600), (340, 300), [512, "udf", False, False, False, 1, 0, False, 3, 0.01, 20000000],
           inputs=[("mesh", "MESH")], outputs=[("mesh", "MESH")],
           title="Remesh (triângulos uniformes → ilhas UV grandes; Ctrl+B para pular)")
weld = N("WeldVertices", (X1 + 460, -310), (340, 82), [1e-5, 0.0], inputs=[("mesh", "MESH")], outputs=[("mesh", "MESH")],
         title="Weld (arestas duplicadas → normais suaves contínuas)")
deci = N("DecimateMesh", (X1 + 460, -200), (340, 106), [30000, "midpoint"], inputs=[("mesh", "MESH")], outputs=[("mesh", "MESH")],
         title="Decimate → contagem de faces de jogo")
unwrap = N("UnwrapMesh", (X1 + 460, -70), (340, 130), ["pec", 2048, 12, 0.001], inputs=[("mesh", "MESH")], outputs=[("mesh", "MESH")],
           title="UV NOVO — pec (adaptive deu 4266 ilhas em 82 s)")
widget_in(unwrap, "resolution", "INT")
smooth = N("MeshSmoothNormals", (X1 + 460, 90), (340, 58), [180], inputs=[("mesh", "MESH")], outputs=[("mesh", "MESH")], title="mesh BAIXO (game-ready, UV limpo)")
bnorm = N("BakeNormalMapFromMesh", (X1 + 860, -700), (320, 130), [2048, 0.05, True], inputs=[("low_poly", "MESH"), ("high_poly", "MESH")],
          outputs=[("normal_map", "IMAGE")], title="normal map: alto → baixo")
bao = N("BakeAmbientOcclusion", (X1 + 860, -520), (320, 180), [1024, 64, 0.5, 1, 0.01], inputs=[("low_poly", "MESH"), ("high_poly", "MESH")],
        outputs=[("occlusion", "IMAGE")], title="AO: alto → baixo")
uvprev = N("RenderUVAtlas", (X1 + 860, -300), (320, 82), [1024], inputs=[("mesh", "MESH")], outputs=[("image", "IMAGE")], title="prévia do UV novo")
uvpv = N("PreviewImage", (X1 + 860, -180), (320, 280), inputs=[("images", "IMAGE")], title="UV novo (ilhas)")
conn(load3d, 6, get, "model_3d", "FILE_3D"); conn(get, 0, remesh, "mesh", "MESH"); conn(remesh, 0, weld, "mesh", "MESH"); conn(weld, 0, deci, "mesh", "MESH")
conn(deci, 0, unwrap, "mesh", "MESH"); conn(unwrap, 0, smooth, "mesh", "MESH")
conn(smooth, 0, bnorm, "low_poly", "MESH"); conn(get, 0, bnorm, "high_poly", "MESH")
conn(smooth, 0, bao, "low_poly", "MESH"); conn(get, 0, bao, "high_poly", "MESH")
conn(smooth, 0, uvprev, "mesh", "MESH"); conn(uvprev, 0, uvpv, "images", "IMAGE")
MESH = smooth

# ---------------------------------------------------------------- 2. referências (frente obrigatória, resto opcional)
refs = {}
for i, (k, fn, t, mode) in enumerate([("front", "Lia_front.png", "Lia FRENTE (obrigatória — a mesma do mesh)", 0),
                                      ("back", "Lia_back.png", "Lia COSTAS (opcional — Ctrl+B para desligar)", BYPASS),
                                      ("left", "Lia_left.png", "Lia ESQUERDA (opcional)", BYPASS),
                                      ("right", "Lia_right.png", "Lia DIREITA (opcional)", BYPASS)]):
    li = N("LoadImage", (X1, 260 + i * 400), (320, 360), [fn, "image"], outputs=[("IMAGE", "IMAGE"), ("MASK", "MASK")], title=t, mode=mode,
           color=GREEN if k == "front" else None)
    refs[k] = li

# ---------------------------------------------------------------- 3. Klein 4B
X2 = -2000
unet = N("UNETLoader", (X2, 260), (400, 82), ["flux-2-klein-4b-fp8.safetensors", "default"], outputs=[("MODEL", "MODEL")],
         props={"models": [{"name": "flux-2-klein-4b-fp8.safetensors", "url": HF + "black-forest-labs/FLUX.2-klein-4b-fp8/resolve/main/flux-2-klein-4b-fp8.safetensors", "directory": "diffusion_models"}]})
clip = N("CLIPLoader", (X2, 380), (400, 106), ["qwen_3_4b_fp8_mixed.safetensors", "flux2", "default"], outputs=[("CLIP", "CLIP")],
         props={"models": [{"name": "qwen_3_4b_fp8_mixed.safetensors", "url": HF + "Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b_fp8_mixed.safetensors", "directory": "text_encoders"}]})
vae = N("VAELoader", (X2, 520), (400, 58), ["flux2-vae.safetensors"], outputs=[("VAE", "VAE")],
        props={"models": [{"name": "flux2-vae.safetensors", "url": HF + "Comfy-Org/flux2-dev/resolve/main/split_files/vae/flux2-vae.safetensors", "directory": "vae"}]})
sched = N("Flux2Scheduler", (X2, 620), (400, 106), [4, 1024, 1024], outputs=[("SIGMAS", "SIGMAS")])
samp = N("KSamplerSelect", (X2, 760), (400, 58), ["euler"], outputs=[("SAMPLER", "SAMPLER")])
style = N("PrimitiveStringMultiline", (X2, 860), (400, 260),
          ["Paint this exact character from image 1 onto the pose and silhouette of the normal map in image 2. "
           "Image 3 shows the SAME character already painted from the front: keep exactly the same outfit design, neckline, "
           "trims, hair and colors as image 3. Some parts of the character are already painted; the flat grey areas are unpainted. "
           "Fill ONLY the grey areas so they continue the already painted parts seamlessly. "
           "Flat unlit albedo texture: flat colors, no shadows, no highlights, no directional lighting, no outlines. "
           "Plain white background. Same art style."],
          outputs=[("STRING", "STRING")], title="Estilo comum (todas as vistas)", color=GREEN)

# ---------------------------------------------------------------- 4. vistas em sequência
VIEWS = [
    # az, el, weight, ref, texto, nome
    (0, 0, 1.0, "front", "front view, facing the camera", "1 Frente"),
    (180, 0, 1.0, "back", "back view, seen from behind", "2 Costas"),
    (90, 0, 0.8, "left", "left side view, orthographic profile", "3 Esquerda"),
    (270, 0, 0.8, "right", "right side view, orthographic profile", "4 Direita"),
    (0, 30, 0.5, "front", "front view seen slightly from above (camera 30 degrees up). The top of the head is hair only, never a face; the face stays where it already is", "5 Frente/cima"),
    (180, 30, 0.5, "back", "back view seen slightly from above (camera 30 degrees up). The top of the head is hair only, never a face", "6 Costas/cima"),
    (0, -30, 0.4, "front", "front view seen slightly from below (camera 30 degrees down). Underside of the chin, sleeves and skirt hem, shoes; no extra face", "7 Frente/baixo"),
    (180, -30, 0.4, "back", "back view seen slightly from below (camera 30 degrees down). Underside of the hem and shoes; no extra face", "8 Costas/baixo"),
]
X3 = -1500
ROW = 760
prev_state = None
acc_nodes = []
front_latent = None   # vista 1 pintada → image 3 das demais
for i, (az, el, wgt, refk, vtxt, name) in enumerate(VIEWS):
    fill_only = el != 0   # cima/baixo só preenchem o que falta
    y = -700 + i * ROW
    ren = N("LiaRenderTextured", (X3, y), (330, 250), [float(az), float(el), 1024, 1.1, 12, "grey", 1.0, 0.0], inputs=[("mesh", "MESH")],
            outputs=[("image", "IMAGE"), ("inpaint_mask", "MASK"), ("silhouette", "MASK"), ("normals", "IMAGE"), ("missing_fraction", "FLOAT")],
            cnr=LIA, title=f"{name}: render parcial + máscara", color=BLUE)
    opt_in(ren, "state", "LIA_TEXSTATE")
    conn(MESH, 0, ren, "mesh", "MESH")
    if prev_state is not None:
        conn(prev_state, 0, ren, "state", "LIA_TEXSTATE")
    pvr = N("PreviewImage", (X3, y + 290), (330, 300), inputs=[("images", "IMAGE")], title=f"{name}: o que já existe (cinza = a pintar)")
    conn(ren, 0, pvr, "images", "IMAGE")

    pick = N("LiaPickReference", (X3 + 370, y), (300, 130), [refk], inputs=[("front", "IMAGE")], outputs=[("image", "IMAGE"), ("used", "STRING")],
             cnr=LIA, title=f"referência da vista ({refk})")
    for k in ("back", "left", "right"):
        opt_in(pick, k, "IMAGE")
    conn(refs["front"], 0, pick, "front", "IMAGE")
    for k in ("back", "left", "right"):
        conn(refs[k], 0, pick, k, "IMAGE")
    rsc = N("ImageScaleToTotalPixels", (X3 + 370, y + 170), (300, 106), ["lanczos", 1, 1], inputs=[("image", "IMAGE")], outputs=[("IMAGE", "IMAGE")])
    renc = N("VAEEncode", (X3 + 370, y + 310), (300, 46), inputs=[("pixels", "IMAGE"), ("vae", "VAE")], outputs=[("LATENT", "LATENT")], title="image 1 = referência")
    nenc = N("VAEEncode", (X3 + 370, y + 390), (300, 46), inputs=[("pixels", "IMAGE"), ("vae", "VAE")], outputs=[("LATENT", "LATENT")], title="image 2 = normal map")
    penc = N("VAEEncode", (X3 + 370, y + 470), (300, 46), inputs=[("pixels", "IMAGE"), ("vae", "VAE")], outputs=[("LATENT", "LATENT")], title="latente = render parcial")
    nmask = N("SetLatentNoiseMask", (X3 + 370, y + 550), (300, 46), inputs=[("samples", "LATENT"), ("mask", "MASK")], outputs=[("LATENT", "LATENT")], title="inpaint só do que falta")
    conn(pick, 0, rsc, "image", "IMAGE"); conn(rsc, 0, renc, "pixels", "IMAGE"); conn(vae, 0, renc, "vae", "VAE")
    conn(ren, 3, nenc, "pixels", "IMAGE"); conn(vae, 0, nenc, "vae", "VAE")
    conn(ren, 0, penc, "pixels", "IMAGE"); conn(vae, 0, penc, "vae", "VAE")
    conn(penc, 0, nmask, "samples", "LATENT"); conn(ren, 1, nmask, "mask", "MASK")

    vt = N("PrimitiveStringMultiline", (X3 + 710, y), (280, 110), [vtxt], outputs=[("STRING", "STRING")], title=f"Vista: {name}")
    cat = N("StringConcatenate", (X3 + 710, y + 150), (280, 82), ["", "", ". "], outputs=[("STRING", "STRING")])
    widget_in(cat, "string_a", "STRING"); widget_in(cat, "string_b", "STRING")
    te = N("CLIPTextEncode", (X3 + 710, y + 270), (280, 80), [""], inputs=[("clip", "CLIP")], outputs=[("CONDITIONING", "CONDITIONING")])
    widget_in(te, "text", "STRING")
    zo = N("ConditioningZeroOut", (X3 + 710, y + 390), (280, 26), inputs=[("conditioning", "CONDITIONING")], outputs=[("CONDITIONING", "CONDITIONING")])
    conn(vt, 0, cat, "string_a", "STRING"); conn(style, 0, cat, "string_b", "STRING")
    conn(clip, 0, te, "clip", "CLIP"); conn(cat, 0, te, "text", "STRING"); conn(te, 0, zo, "conditioning", "CONDITIONING")

    def refchain(cond, x, yy, sign):
        r1 = N("ReferenceLatent", (x, yy), (240, 46), inputs=[("conditioning", "CONDITIONING"), ("latent", "LATENT")], outputs=[("CONDITIONING", "CONDITIONING")], title=f"ref 1 (referência) {sign}")
        r2 = N("ReferenceLatent", (x, yy + 70), (240, 46), inputs=[("conditioning", "CONDITIONING"), ("latent", "LATENT")], outputs=[("CONDITIONING", "CONDITIONING")], title=f"ref 2 (normal) {sign}")
        conn(cond, 0, r1, "conditioning", "CONDITIONING"); conn(renc, 0, r1, "latent", "LATENT")
        conn(r1, 0, r2, "conditioning", "CONDITIONING"); conn(nenc, 0, r2, "latent", "LATENT")
        if front_latent is not None:
            r3 = N("ReferenceLatent", (x, yy + 140), (240, 46), inputs=[("conditioning", "CONDITIONING"), ("latent", "LATENT")], outputs=[("CONDITIONING", "CONDITIONING")], title=f"ref 3 (frente pintada) {sign}")
            conn(r2, 0, r3, "conditioning", "CONDITIONING"); conn(front_latent, 0, r3, "latent", "LATENT")
            return r3
        return r2
    rp = refchain(te, X3 + 1030, y, "+")
    rn = refchain(zo, X3 + 1030, y + 240, "−")
    gd = N("CFGGuider", (X3 + 1310, y), (260, 98), [1], inputs=[("model", "MODEL"), ("positive", "CONDITIONING"), ("negative", "CONDITIONING")], outputs=[("GUIDER", "GUIDER")])
    nz = N("RandomNoise", (X3 + 1310, y + 140), (260, 82), [200 + i, "fixed"], outputs=[("NOISE", "NOISE")])
    sca = N("SamplerCustomAdvanced", (X3 + 1610, y), (280, 120), inputs=[("noise", "NOISE"), ("guider", "GUIDER"), ("sampler", "SAMPLER"), ("sigmas", "SIGMAS"), ("latent_image", "LATENT")],
            outputs=[("output", "LATENT"), ("denoised_output", "LATENT")])
    dec = N("VAEDecode", (X3 + 1610, y + 160), (280, 46), inputs=[("samples", "LATENT"), ("vae", "VAE")], outputs=[("IMAGE", "IMAGE")])
    comp = N("ImageCompositeMasked", (X3 + 1610, y + 250), (280, 130), [0, 0, False],
             inputs=[("destination", "IMAGE"), ("source", "IMAGE")], outputs=[("IMAGE", "IMAGE")], title="cola só a área da máscara (fora dela nada muda)")
    opt_in(comp, "mask", "MASK")
    pv = N("PreviewImage", (X3 + 1610, y + 420), (280, 300), inputs=[("images", "IMAGE")], title=f"{name}: pintada")
    conn(unet, 0, gd, "model", "MODEL"); conn(rp, 0, gd, "positive", "CONDITIONING"); conn(rn, 0, gd, "negative", "CONDITIONING")
    conn(nz, 0, sca, "noise", "NOISE"); conn(gd, 0, sca, "guider", "GUIDER"); conn(samp, 0, sca, "sampler", "SAMPLER"); conn(sched, 0, sca, "sigmas", "SIGMAS")
    conn(nmask, 0, sca, "latent_image", "LATENT")
    conn(sca, 0, dec, "samples", "LATENT"); conn(vae, 0, dec, "vae", "VAE")
    conn(ren, 0, comp, "destination", "IMAGE"); conn(dec, 0, comp, "source", "IMAGE"); conn(ren, 1, comp, "mask", "MASK")
    conn(comp, 0, pv, "images", "IMAGE")
    if front_latent is None:
        fenc = N("VAEEncode", (X3 + 1940, y + 420), (300, 46), inputs=[("pixels", "IMAGE"), ("vae", "VAE")], outputs=[("LATENT", "LATENT")], title="frente pintada → image 3 das outras vistas")
        conn(comp, 0, fenc, "pixels", "IMAGE"); conn(vae, 0, fenc, "vae", "VAE")
        front_latent = fenc

    acc = N("LiaProjectTextureAccumulate", (X3 + 1940, y), (340, 350), [float(az), float(el), 1.1, 2048, wgt, 4.0, 0.10, 0.015, True, fill_only, 1.0, 0.0, False],
            inputs=[("mesh", "MESH"), ("image", "IMAGE")],
            outputs=[("state", "LIA_TEXSTATE"), ("base_color", "IMAGE"), ("coverage", "IMAGE"), ("info", "STRING")],
            cnr=LIA, title=f"{name}: acumula no atlas", color=PURPLE)
    opt_in(acc, "state", "LIA_TEXSTATE"); opt_in(acc, "mask", "MASK")
    conn(MESH, 0, acc, "mesh", "MESH"); conn(comp, 0, acc, "image", "IMAGE"); conn(ren, 1, acc, "mask", "MASK")
    if prev_state is not None:
        conn(prev_state, 0, acc, "state", "LIA_TEXSTATE")
    pvc = N("PreviewImage", (X3 + 2320, y), (280, 280), inputs=[("images", "IMAGE")], title=f"{name}: cobertura (vermelho = falta)")
    conn(acc, 2, pvc, "images", "IMAGE")
    prev_state = acc
    acc_nodes.append(acc)

# ---------------------------------------------------------------- 4b. passe de correção — Waifu-Inpaint-XL (SDXL inpaint anime)
# O Klein preenche tudo (cobertura); o WAI-Inpaint refina as vistas que o jogador
# vê de perto: repinta rosto/frente/costas/lados em img2img de baixo denoise com
# IP-Adapter da referência 2D, e o resultado SUBSTITUI (replace) o que existia.
XB = X3 + 2700
ckpt = N("CheckpointLoaderSimple", (XB, -700), (400, 98), ["Waifu-Inpaint-XL.safetensors"], outputs=[("MODEL", "MODEL"), ("CLIP", "CLIP"), ("VAE", "VAE")],
         props={"models": [{"name": "Waifu-Inpaint-XL.safetensors", "url": HF + "ShinoharaHare/Waifu-Inpaint-XL/resolve/main/Waifu-Inpaint-XL.safetensors", "directory": "checkpoints"}]},
         title="Waifu-Inpaint-XL (gated: HF_TOKEN na Célula 5)")
vpred = N("ModelSamplingDiscrete", (XB, -560), (400, 82), ["v_prediction", True], inputs=[("model", "MODEL")], outputs=[("MODEL", "MODEL")], title="v-prediction + ZSNR (o WAI v14 é v-pred)")
rcfg = N("RescaleCFG", (XB, -440), (400, 58), [0.7], inputs=[("model", "MODEL")], outputs=[("MODEL", "MODEL")])
ipl = N("IPAdapterUnifiedLoader", (XB, -350), (400, 82), ["PLUS (high strength)"], inputs=[("model", "MODEL")], outputs=[("model", "MODEL"), ("ipadapter", "IPADAPTER")], cnr="cubiq/ComfyUI_IPAdapter_plus")
opt_in(ipl, "ipadapter", "IPADAPTER")
ipa = N("IPAdapterAdvanced", (XB, -230), (400, 300), [0.55, "style transfer", "concat", 0.0, 0.8, "K+mean(V) w/ C penalty"],
        inputs=[("model", "MODEL"), ("ipadapter", "IPADAPTER"), ("image", "IMAGE")], outputs=[("MODEL", "MODEL")], cnr="cubiq/ComfyUI_IPAdapter_plus",
        title="IP-Adapter: estilo/cores da Lia 2D (frente)")
for k, t in (("image_negative", "IMAGE"), ("attn_mask", "MASK"), ("clip_vision", "CLIP_VISION")):
    opt_in(ipa, k, t)
conn(ckpt, 0, vpred, "model", "MODEL"); conn(vpred, 0, rcfg, "model", "MODEL"); conn(rcfg, 0, ipl, "model", "MODEL")
conn(ipl, 0, ipa, "model", "MODEL"); conn(ipl, 1, ipa, "ipadapter", "IPADAPTER"); conn(refs["front"], 0, ipa, "image", "IMAGE")
wpos = N("CLIPTextEncode", (XB, 110), (400, 160),
         ["masterpiece, best quality, 1girl, black hair with red tips, short bob, black long-sleeved dress with gold trim and gold belt, ornate gold hem, "
          "flat color, cel shading, anime coloring, simple white background, texture sheet, no lighting"],
         inputs=[("clip", "CLIP")], outputs=[("CONDITIONING", "CONDITIONING")], title="WAI positivo — AJUSTE as tags para a sua Lia", color=GREEN)
wneg = N("CLIPTextEncode", (XB, 310), (400, 120),
         ["worst quality, low quality, blurry, jpeg artifacts, shadow, dramatic lighting, lens flare, depth of field, 3d, realistic, "
          "extra face, extra eyes, text, watermark, signature, multiple views, gradient background"],
         inputs=[("clip", "CLIP")], outputs=[("CONDITIONING", "CONDITIONING")], title="WAI negativo")
conn(ckpt, 1, wpos, "clip", "CLIP"); conn(ckpt, 1, wneg, "clip", "CLIP")

FIX_VIEWS = [
    # az, el, zoom, offset_y, denoise, weight, texto, nome
    (0, 0, 3.0, 0.42, 0.45, 1.5, "close-up of the face and hair, looking at viewer, detailed eyes, symmetrical face, small mouth", "F1 Rosto"),
    (0, 0, 1.0, 0.0, 0.35, 1.0, "full body, front view, standing, arms at sides", "F2 Frente"),
    (180, 0, 1.0, 0.0, 0.35, 1.0, "full body, from behind, back of the head is hair only", "F3 Costas"),
    (90, 0, 1.0, 0.0, 0.35, 0.8, "full body, from side, profile", "F4 Esquerda"),
    (270, 0, 1.0, 0.0, 0.35, 0.8, "full body, from side, profile", "F5 Direita"),
]
fix_state = prev_state
for j, (az, el, zm, oy, dn, wgt, vtxt, name) in enumerate(FIX_VIEWS):
    y = -700 + j * ROW
    x0 = XB + 460
    renf = N("LiaRenderTextured", (x0, y), (330, 250), [float(az), float(el), 1024, 1.1, 0, "grey", zm, oy], inputs=[("mesh", "MESH")],
             outputs=[("image", "IMAGE"), ("inpaint_mask", "MASK"), ("silhouette", "MASK"), ("normals", "IMAGE"), ("missing_fraction", "FLOAT")],
             cnr=LIA, title=f"{name}: render da textura Klein (zoom {zm:g})", color=BLUE)
    opt_in(renf, "state", "LIA_TEXSTATE")
    conn(MESH, 0, renf, "mesh", "MESH"); conn(fix_state, 0, renf, "state", "LIA_TEXSTATE")
    pvf0 = N("PreviewImage", (x0, y + 290), (330, 300), inputs=[("images", "IMAGE")], title=f"{name}: antes")
    conn(renf, 0, pvf0, "images", "IMAGE")
    # máscara = silhueta encolhida 6 px (não toca a borda → o fundo branco fica intacto e o enquadramento não muda)
    shrink = N("GrowMask", (x0 + 370, y), (300, 82), [-6, True], inputs=[("mask", "MASK")], outputs=[("MASK", "MASK")], title="silhueta −6 px")
    conn(renf, 2, shrink, "mask", "MASK")
    vtn = N("CLIPTextEncode", (x0 + 370, y + 130), (300, 100), [vtxt], inputs=[("clip", "CLIP")], outputs=[("CONDITIONING", "CONDITIONING")], title=f"{name}: tags da vista")
    conn(ckpt, 1, vtn, "clip", "CLIP")
    ccat = N("ConditioningConcat", (x0 + 370, y + 270), (300, 46), inputs=[("conditioning_to", "CONDITIONING"), ("conditioning_from", "CONDITIONING")], outputs=[("CONDITIONING", "CONDITIONING")])
    conn(wpos, 0, ccat, "conditioning_to", "CONDITIONING"); conn(vtn, 0, ccat, "conditioning_from", "CONDITIONING")
    imc = N("InpaintModelConditioning", (x0 + 710, y), (300, 150), [True],
            inputs=[("positive", "CONDITIONING"), ("negative", "CONDITIONING"), ("vae", "VAE"), ("pixels", "IMAGE"), ("mask", "MASK")],
            outputs=[("positive", "CONDITIONING"), ("negative", "CONDITIONING"), ("latent", "LATENT")], title="inpaint 9 canais (modelo de inpaint de verdade)")
    conn(ccat, 0, imc, "positive", "CONDITIONING"); conn(wneg, 0, imc, "negative", "CONDITIONING"); conn(ckpt, 2, imc, "vae", "VAE")
    conn(renf, 0, imc, "pixels", "IMAGE"); conn(shrink, 0, imc, "mask", "MASK")
    ks = N("KSampler", (x0 + 710, y + 190), (300, 262), [300 + j, "fixed", 24, 4.5, "euler_ancestral", "normal", dn],
           inputs=[("model", "MODEL"), ("positive", "CONDITIONING"), ("negative", "CONDITIONING"), ("latent_image", "LATENT")], outputs=[("LATENT", "LATENT")],
           title=f"{name}: denoise {dn:g} (sobe = muda mais)")
    conn(ipa, 0, ks, "model", "MODEL"); conn(imc, 0, ks, "positive", "CONDITIONING"); conn(imc, 1, ks, "negative", "CONDITIONING"); conn(imc, 2, ks, "latent_image", "LATENT")
    decf = N("VAEDecode", (x0 + 1050, y), (280, 46), inputs=[("samples", "LATENT"), ("vae", "VAE")], outputs=[("IMAGE", "IMAGE")])
    conn(ks, 0, decf, "samples", "LATENT"); conn(ckpt, 2, decf, "vae", "VAE")
    compf = N("ImageCompositeMasked", (x0 + 1050, y + 90), (280, 130), [0, 0, False],
              inputs=[("destination", "IMAGE"), ("source", "IMAGE")], outputs=[("IMAGE", "IMAGE")], title="cola só dentro da silhueta")
    opt_in(compf, "mask", "MASK")
    conn(renf, 0, compf, "destination", "IMAGE"); conn(decf, 0, compf, "source", "IMAGE"); conn(shrink, 0, compf, "mask", "MASK")
    pvf = N("PreviewImage", (x0 + 1050, y + 260), (280, 300), inputs=[("images", "IMAGE")], title=f"{name}: depois (WAI)")
    conn(compf, 0, pvf, "images", "IMAGE")
    accf = N("LiaProjectTextureAccumulate", (x0 + 1370, y), (340, 380), [float(az), float(el), 1.1, 2048, wgt, 4.0, 0.25, 0.015, False, False, zm, oy, True],
             inputs=[("mesh", "MESH"), ("image", "IMAGE")],
             outputs=[("state", "LIA_TEXSTATE"), ("base_color", "IMAGE"), ("coverage", "IMAGE"), ("info", "STRING")],
             cnr=LIA, title=f"{name}: SUBSTITUI no atlas (replace)", color=PURPLE)
    opt_in(accf, "state", "LIA_TEXSTATE"); opt_in(accf, "mask", "MASK")
    conn(MESH, 0, accf, "mesh", "MESH"); conn(compf, 0, accf, "image", "IMAGE"); conn(shrink, 0, accf, "mask", "MASK")
    conn(fix_state, 0, accf, "state", "LIA_TEXSTATE")
    fix_state = accf
prev_state = fix_state

# ---------------------------------------------------------------- 5. finalização
X4 = XB + 2300
fin = N("LiaTextureFinalize", (X4, -700), (340, 170), [8, True, 64], inputs=[("mesh", "MESH"), ("state", "LIA_TEXSTATE")],
        outputs=[("base_color", "IMAGE"), ("coverage", "IMAGE"), ("unseen_mask", "MASK"), ("state", "LIA_TEXSTATE")], cnr=LIA, title="Fecha a textura", color=PURPLE)
conn(MESH, 0, fin, "mesh", "MESH"); conn(prev_state, 0, fin, "state", "LIA_TEXSTATE")
pt = N("PreviewImage", (X4, -480), (340, 340), inputs=[("images", "IMAGE")], title="Atlas final")
pc = N("PreviewImage", (X4, -100), (340, 340), inputs=[("images", "IMAGE")], title="Cobertura final")
conn(fin, 0, pt, "images", "IMAGE"); conn(fin, 1, pc, "images", "IMAGE")
st = N("SaveImage", (X4 + 380, -700), (340, 340), ["3d/Lia/Lia_albedo"], inputs=[("images", "IMAGE")], title="PNG albedo (Blender/VRM MToon)")
sn = N("SaveImage", (X4 + 380, -320), (340, 340), ["3d/Lia/Lia_normal"], inputs=[("images", "IMAGE")], title="PNG normal map")
sa = N("SaveImage", (X4 + 380, 60), (340, 340), ["3d/Lia/Lia_ao"], inputs=[("images", "IMAGE")], title="PNG AO")
conn(fin, 0, st, "images", "IMAGE"); conn(bnorm, 0, sn, "images", "IMAGE"); conn(bao, 0, sa, "images", "IMAGE")
app = N("ApplyTextureToMesh", (X4, 300), (340, 130), inputs=[("mesh", "MESH"), ("base_color", "IMAGE"), ("metallic", "IMAGE"), ("roughness", "IMAGE"), ("occlusion", "IMAGE"), ("normal_map", "IMAGE")],
        outputs=[("mesh", "MESH")])
conn(MESH, 0, app, "mesh", "MESH"); conn(fin, 0, app, "base_color", "IMAGE"); conn(bao, 0, app, "occlusion", "IMAGE"); conn(bnorm, 0, app, "normal_map", "IMAGE")
sg = N("SaveGLB", (X4, 480), (340, 500), ["3d/Lia/Lia_texturizado", ""], inputs=[("mesh", "MESH")], title="GLB final (game-ready: UV novo + albedo + normal + AO)")
conn(app, 0, sg, "mesh", "MESH")
chk = N("LiaRenderTextured", (X4 + 760, -700), (330, 250), [30.0, 15.0, 1024, 1.1, 0, "magenta", 1.0, 0.0], inputs=[("mesh", "MESH")],
        outputs=[("image", "IMAGE"), ("inpaint_mask", "MASK"), ("silhouette", "MASK"), ("normals", "IMAGE"), ("missing_fraction", "FLOAT")],
        cnr=LIA, title="Conferência 3/4 (textura FINAL; magenta = buraco real)", color=BLUE)
opt_in(chk, "state", "LIA_TEXSTATE")
conn(MESH, 0, chk, "mesh", "MESH"); conn(fin, 3, chk, "state", "LIA_TEXSTATE")
pvk = N("PreviewImage", (X4 + 760, -420), (330, 330), inputs=[("images", "IMAGE")], title="Conferência")
conn(chk, 0, pvk, "images", "IMAGE")

# ---------------------------------------------------------------- notas
N("MarkdownNote", (X1 - 720, -700), (680, 900), ["""# Lia → textura por projeção **v2** (projeta-e-completa, estilo Modddif)

Entrada: **GLB** do `Lia_Trellis2_Image2Mesh` / `Lia_Pixal3D_MultiView` + a imagem 2D **frontal** da Lia (obrigatória) e, se tiver, costas/esquerda/direita (as mesmas do Pixal3D — opcionais, ligue com Ctrl+B).

## O que mudou em relação à v1
A v1 pintava 4 vistas **independentes** e misturava: costas com outra paleta, tênis de dentro branco, buracos. Agora as vistas são pintadas **em ordem**, cada uma **vendo o que já foi pintado**:

1. **Retopo game-ready** — `Weld` → `Decimate` (30 k faces, ajuste) → `UnwrapMesh` (UV **novo**, limpo, padding 8 — o padding 1 do fluxo antigo era o que causava as franjas coloridas na silhueta do normal map) → normais suaves. Normal map + AO são *bakeados* do mesh alto original, então o detalhe não se perde. `Remesh` fica em bypass; ligue se o GLB vier com casca dupla/não-manifold.
2. **Vista 1 (frente)** — geração completa (image1 = Lia, image2 = normal map).
3. **Vistas 2–8** — `Render Textured View` renderiza o mesh **com a textura parcial**; o que falta sai **cinza** e vira máscara. O Klein recebe esse render como latente + `SetLatentNoiseMask` e só pinta o cinza, continuando o que já existe. `Accumulate` corrige o tom da vista nova pelo que já está pintado (`color_match`) e soma no atlas.
4. Ordem: frente → costas → esq → dir → frente/cima 30° → costas/cima → frente/baixo −30° → costas/baixo. As inclinadas fecham ombros, axila, queixo, parte de dentro do tênis. O **topo absoluto** da cabeça e as solas ficam para o preenchimento por vizinhança do `Finalize` (cabelo continua cabelo) — a 55° o Klein pintava um rosto no topo da cabeça.
5. `Finalize` → `ApplyTextureToMesh` (+ normal + AO) → `SaveGLB` em `output/3d/Lia/`. PNGs separados para MToon/VRM.

## v2.1 (após o 1º teste real, relatório `docs/Logs/relatorio_20260914_0421`)
- **Image 3 = frente pintada** em todas as vistas 2–8: costas/lados nunca têm texels em comum com a frente, então o Klein não "via" a frente e inventava decote/roupa. Agora vê.
- `ImageCompositeMasked` cola só a área da máscara de volta no render parcial: fora dela **nada** muda.
- `color_match` virou ganho escalar de brilho, só em pixels claros, clamp 0,85–1,2 (antes lavava o casaco preto).
- Vistas de cima/baixo em `fill_only` (só preenchem, não misturam). `min_cos` 0,10 e `depth_tolerance` 0,015 (menos frestas magenta).
- `Remesh` ligado por padrão: triângulos uniformes → ilhas UV grandes em vez de 900 tiras.

## v2.2
- Vistas inclinadas 55°/−50° → **±30°**: a 55° faltava só o topo da cabeça e o Klein inventava um rosto ali (olhos no cabelo). A ±30° o que falta são frestas que ele continua do vizinho.
- Conferência agora usa a textura **finalizada** (antes mostrava costuras de UV ainda não dilatadas como magenta).

## v2.3
- `Render Textured View` dilata a textura 4 texels para dentro das bordas das ilhas antes de amostrar → acaba o chuvisco magenta/cinza espalhado (era borda de ilha UV, não buraco). O inpaint agora só recebe buracos reais.
- `UnwrapMesh` **pec** com weld 0,001 e padding 12 (v78: o `adaptive` foi testado e gerou 4266 ilhas em 82 s — pior que as 921 do pec).

## v3 (v82) — passe de correção com Waifu-Inpaint-XL
Depois das 8 vistas Klein (que garantem **cobertura**), 5 passes com o **Waifu-Inpaint-XL** (SDXL inpaint anime, 9 canais) refinam o que o jogador vê de perto: **rosto em zoom 3×** (o Klein pintava o rosto com ~150 px; agora são ~700 px de rosto no mesmo atlas), frente, costas e lados. Cada passe: render da textura atual → `InpaintModelConditioning` (máscara = silhueta encolhida, então o fundo e o enquadramento **não mudam**) → KSampler denoise 0,35–0,45 (img2img: mantém a composição do Klein, redesenha linha/cor no estilo anime) → `Accumulate` com **replace** (o novo substitui o Klein onde a vista enxerga, `min_cos` 0,25 para não substituir em ângulo raso). IP-Adapter PLUS com a frente 2D segura estilo e paleta. `ModelSamplingDiscrete v_prediction+zsnr` e `RescaleCFG 0,7` porque o WAI v14 é v-pred. Teste no Qwen-Image-Edit (relatórios 0919–1141) foi descartado: 9–17 min/vista e quebra com máscara.
- **Tags**: o positivo do WAI está genérico ("black hair with red tips, black dress with gold trim…") — ajuste para a sua Lia; é Illustrious, responde a tags Danbooru.
- Rosto torto/duplicado → baixe o denoise F1 para 0,3 ou troque o seed (300). Trocou demais a roupa → denoise F2–F5 0,25.
- Não quer o passe → Ctrl+B nos 5 `KSampler` do grupo 4b (o `Finalize` continua recebendo o estado, só que sem correção)… ou mais simples: ligue o `Finalize.state` direto no último `Accumulate` do grupo 4.

## Ajustes
- Uma vista saiu ruim → mude só o seed daquela vista (`RandomNoise`, fixos 200–207); as anteriores ficam em cache.
- Conferência (magenta) mostra texels que **nenhuma** vista viu; se sobrar, adicione uma vista copiando um bloco (render → Klein → accumulate) e encadeando o `state`.
- Faces de jogo: `DecimateMesh` 15 k (mobile) / 30 k (PC/VRM) / 80 k (alta).
- `view_weight`: frente/costas 1.0, lados 0.8, cima/baixo 0.4–0.5 (só completam, não sobrescrevem).
- `grow_mask_px` 12: borda extra para o Klein fundir o novo com o antigo; suba se aparecer costura, desça se ele "repintar" demais.

**T4**: 8 gerações Klein 4B (~40 s cada) + 5 passes WAI (SDXL 24 passos ≈ 50–70 s cada) + bakes ≈ **15–20 min**. Drive: +6,9 GB `Waifu-Inpaint-XL` (gated — HF_TOKEN) + IP-Adapter/CLIP-ViT-H (3,4 GB, já usados nos WaifuSurvivors). Nós próprios MIT em `custom_nodes/ComfyUI-Lia-TextureProjection` (torch puro).
"""], title="LEIA-ME", color=BROWN)
N("MarkdownNote", (X1 - 720, 260), (680, 520), ["""## Comparação com o Modddif

| Modddif | aqui |
|---|---|
| texturas de múltiplos ângulos de câmera | 8 vistas ortográficas sequenciais |
| inpaint só do que precisa | `Render Textured View` → máscara → `SetLatentNoiseMask` |
| retopo + UV + bake | `Decimate` + `UnwrapMesh` + `BakeNormalMapFromMesh` + `BakeAmbientOcclusion` (core, MIT) |
| normal map estimado | normal map bakeado do mesh alto (mais fiel) |
| web, pago | local/Colab T4, tudo MIT/Apache |

O que ele faz e nós não: retopo **quad** (o nosso é triângulo decimado — para VRM/jogo é aceitável; para retopo quad use o Blender/Instant Meshes) e refinamento de textura em UV com super-resolução.

**Limite**: o Klein 4B em 4 passos é rápido mas não perfeito no inpaint; se uma costura ficar visível, regere a vista com outro seed ou pinte o retoque no Blender (`docs/Blender_Texturizar_Lia.md`).
"""], title="Contexto", color=("#233", "#355"))

groups = [
    {"id": 1, "title": "1. Mesh → retopo game-ready (UV novo, normal, AO)", "bounding": [X1 - 20, -780, 1260, 900], "color": "#3f789e", "flags": {}},
    {"id": 2, "title": "2. Referências (frente obrigatória; costas/lados opcionais)", "bounding": [X1 - 20, 180, 400, 1620], "color": "#8A8", "flags": {}},
    {"id": 3, "title": "3. Flux.2 Klein 4B", "bounding": [X2 - 20, 180, 460, 980], "color": "#88A", "flags": {}},
    {"id": 4, "title": "4. Vistas em sequência: render parcial → inpaint → acumula (a ordem importa)", "bounding": [X3 - 20, -780, 2680, ROW * len(VIEWS) + 100], "color": "#a1309b", "flags": {}},
    {"id": 6, "title": "4b. Passe de correção — Waifu-Inpaint-XL (rosto em zoom + 4 vistas, substitui a textura Klein)", "bounding": [XB - 20, -780, 2260, ROW * 5 + 100], "color": "#a55", "flags": {}},
    {"id": 5, "title": "5. Textura final + GLB", "bounding": [X4 - 20, -780, 1160, 1800], "color": "#b58b2a", "flags": {}},
]
wf = {"id": str(uuid.uuid4()), "revision": 0, "last_node_id": nid[0], "last_link_id": lid[0], "nodes": nodes, "links": links,
      "groups": groups, "config": {}, "extra": {"ds": {"scale": 0.25, "offset": [3800, 850]}, "frontendVersion": "1.49.6"}, "version": 0.4}
json.dump(wf, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("ok", nid[0], "nodes", lid[0], "links ->", OUT)
