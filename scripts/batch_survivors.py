#!/usr/bin/env python3
"""
batch_survivors.py — gera todos os assets do Waifu Survivors pela API do ComfyUI.

Le um roster.json (varios personagens) e enfileira, para cada um:
  splash, portrait e as 5 poses chibi (idle, walk_a, walk_b, attack, death).

Nao depende de nenhum workflow salvo: monta o grafo em formato API na hora.
Assim voce troca o elenco editando so o JSON.

USO
    python scripts/batch_survivors.py --roster scripts/roster.json
    python scripts/batch_survivors.py --only lia --kinds chibi
    python scripts/batch_survivors.py --dry-run          # so mostra o plano

No Colab, o ComfyUI roda em 127.0.0.1:8188 na mesma maquina, entao o padrao
funciona. Rode numa celula nova, com o servidor da Celula 6 no ar:
    !python /content/ComfyUI_Colab/scripts/batch_survivors.py --roster ...
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

# ----------------------------------------------------------------- estilos ---

STYLES = {
    "splash": {
        # 'sensitive' = teor ecchi do WAI (nivel entre general e nsfw).
        # Ajuste ECCHI no roster.json por personagem, se quiser.
        "text": ("cowboy shot, dynamic pose, detailed background, cinematic lighting, "
                 "sensitive, alluring pose, attractive, detailed costume, "
                 "masterpiece, best quality, amazing quality"),
        "w": 832, "h": 1216, "steps": 30, "rembg": False,
    },
    "portrait": {
        "text": ("portrait, upper body, looking at viewer, simple background, "
                 "soft lighting, detailed face, sensitive, alluring, "
                 "masterpiece, best quality, amazing quality"),
        "w": 1024, "h": 1024, "steps": 28, "rembg": False,
    },
    "chibi": {
        "text": ("chibi, super deformed, 2 heads tall, big head, small body, "
                 "thick outlines, flat colors, simple shading, minimal detail, "
                 "full body, side view, facing right, white background, "
                 "simple background, centered, feet visible"),
        "w": 1024, "h": 1024, "steps": 26, "rembg": True,
    },
}

CHIBI_POSES = [
    ("idle",    "standing still, idle pose, arms relaxed at sides"),
    ("walk_a",  "walking, left leg forward, right arm forward, mid stride"),
    ("walk_b",  "walking, right leg forward, left arm forward, mid stride"),
    ("attack",  "attacking, swinging arm forward, dynamic action pose"),
    ("death",   "falling down, defeated, lying on ground, eyes closed"),
]


# ------------------------------------------------------------------ grafo ----

def build_graph(char, defaults, kind, pose_name=None, pose_text=None):
    """Monta o grafo no formato API (dict de nos por id-string)."""
    st = STYLES[kind]
    ckpt = char.get("checkpoint", defaults["checkpoint"])
    neg = char.get("negative", defaults["negative"])
    cfg = char.get("cfg", defaults.get("cfg", 5.5))
    steps = char.get("steps", st["steps"])
    sampler = char.get("sampler", defaults.get("sampler", "dpmpp_2m"))
    sched = char.get("scheduler", defaults.get("scheduler", "karras"))
    seed = char.get("seed", 555)
    lora = char.get("lora")

    g = {}
    g["1"] = {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": ckpt}}

    model_src, clip_src = ["1", 0], ["1", 1]
    if lora:
        g["2"] = {"class_type": "LoraLoader", "inputs": {
            "lora_name": lora,
            "strength_model": char.get("lora_strength", 0.85),
            "strength_clip": char.get("lora_strength", 0.85),
            "model": model_src, "clip": clip_src}}
        model_src, clip_src = ["2", 0], ["2", 1]

    g["3"] = {"class_type": "CLIPTextEncode",
              "inputs": {"text": char["identity"], "clip": clip_src}}
    g["4"] = {"class_type": "CLIPTextEncode",
              "inputs": {"text": st["text"], "clip": clip_src}}
    g["5"] = {"class_type": "CLIPTextEncode",
              "inputs": {"text": neg, "clip": clip_src}}
    g["6"] = {"class_type": "ConditioningConcat",
              "inputs": {"conditioning_to": ["3", 0], "conditioning_from": ["4", 0]}}

    pos_src = ["6", 0]
    if pose_text:
        g["7"] = {"class_type": "CLIPTextEncode",
                  "inputs": {"text": pose_text, "clip": clip_src}}
        g["8"] = {"class_type": "ConditioningConcat",
                  "inputs": {"conditioning_to": ["6", 0], "conditioning_from": ["7", 0]}}
        pos_src = ["8", 0]

    g["10"] = {"class_type": "EmptyLatentImage",
               "inputs": {"width": st["w"], "height": st["h"], "batch_size": 1}}
    g["11"] = {"class_type": "KSampler", "inputs": {
        "seed": seed, "control_after_generate": "fixed", "steps": steps, "cfg": cfg,
        "sampler_name": sampler, "scheduler": sched, "denoise": 1.0,
        "model": model_src, "positive": pos_src,
        "negative": ["5", 0], "latent_image": ["10", 0]}}
    g["12"] = {"class_type": "VAEDecode",
               "inputs": {"samples": ["11", 0], "vae": ["1", 2]}}

    img = ["12", 0]
    if st["rembg"]:
        g["13"] = {"class_type": "InspyrenetRembg",
                   "inputs": {"image": ["12", 0], "torchscript_jit": "default"}}
        img = ["13", 0]

    suffix = f"_{pose_name}" if pose_name else ""
    g["14"] = {"class_type": "SaveImage", "inputs": {
        "filename_prefix": f"survivors/{char['id']}/{kind}{suffix}",
        "images": img}}
    return g


def jobs_for(char, defaults, kinds):
    out = []
    for kind in kinds:
        if kind == "chibi":
            for pose_name, pose_text in CHIBI_POSES:
                out.append((f"{char['id']}/chibi_{pose_name}",
                            build_graph(char, defaults, "chibi", pose_name, pose_text)))
        else:
            out.append((f"{char['id']}/{kind}",
                        build_graph(char, defaults, kind)))
    return out


# -------------------------------------------------------------------- API ----

def post_prompt(server, graph):
    data = json.dumps({"prompt": graph}).encode()
    req = urllib.request.Request(f"{server}/prompt", data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def queue_len(server):
    try:
        with urllib.request.urlopen(f"{server}/queue", timeout=10) as r:
            q = json.loads(r.read())
        return len(q.get("queue_running", [])) + len(q.get("queue_pending", []))
    except Exception:
        return -1


def wait_for_slot(server, max_pending):
    while True:
        n = queue_len(server)
        if n < 0 or n <= max_pending:
            return
        time.sleep(3)


# ------------------------------------------------------------------- main ----

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--roster", default="scripts/roster.json")
    ap.add_argument("--server", default="http://127.0.0.1:8188")
    ap.add_argument("--kinds", default="splash,portrait,chibi",
                    help="quais gerar (padrao: todos)")
    ap.add_argument("--only", default="", help="so estes ids, separados por virgula")
    ap.add_argument("--dry-run", action="store_true", help="mostra o plano e sai")
    ap.add_argument("--max-pending", type=int, default=4,
                    help="quantos jobs deixar na fila do ComfyUI de cada vez")
    a = ap.parse_args()

    if not os.path.exists(a.roster):
        sys.exit(f"roster nao encontrado: {a.roster}\n"
                 f"Copie scripts/roster.example.json e edite.")

    cfg = json.load(open(a.roster, encoding="utf-8"))
    defaults = cfg.get("defaults", {})
    chars = cfg["characters"]

    if a.only:
        keep = {x.strip() for x in a.only.split(",")}
        chars = [c for c in chars if c["id"] in keep]
        if not chars:
            sys.exit(f"nenhum personagem com id em {sorted(keep)}")

    kinds = [k.strip() for k in a.kinds.split(",") if k.strip()]
    for k in kinds:
        if k not in STYLES:
            sys.exit(f"kind invalido: {k}. Use: {', '.join(STYLES)}")

    all_jobs = []
    for c in chars:
        all_jobs += jobs_for(c, defaults, kinds)

    print(f"Personagens: {[c['id'] for c in chars]}")
    print(f"Tipos      : {kinds}")
    print(f"Total      : {len(all_jobs)} imagens\n")

    if a.dry_run:
        for name, _ in all_jobs:
            print("  ", name)
        print("\n(dry-run: nada foi enfileirado)")
        return

    if queue_len(a.server) < 0:
        sys.exit(f"nao consegui falar com o ComfyUI em {a.server}\n"
                 f"O servidor esta no ar? (Celula 6)")

    ok = fail = 0
    for i, (name, graph) in enumerate(all_jobs, 1):
        wait_for_slot(a.server, a.max_pending)
        try:
            r = post_prompt(a.server, graph)
            print(f"[{i}/{len(all_jobs)}] enfileirado {name}  ({r.get('prompt_id','?')[:8]})")
            ok += 1
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:400]
            print(f"[{i}/{len(all_jobs)}] FALHOU {name}: {e.code}\n    {body}")
            fail += 1
        except Exception as e:
            print(f"[{i}/{len(all_jobs)}] FALHOU {name}: {e}")
            fail += 1

    print(f"\n{ok} enfileirados, {fail} falharam.")
    print("Acompanhe na UI do ComfyUI. As imagens vao para "
          "output/survivors/<personagem>/.")


if __name__ == "__main__":
    main()
