# -*- coding: utf-8 -*-
"""Relatório de sessão do ComfyUI no Colab.

Ligado pelo toggle RELATORIO da Célula 1. Enquanto o ComfyUI roda (Célula 6):

* ``tee`` do log do servidor para ``comfyui.log`` (tudo que o main.py imprime,
  inclusive tracebacks de nós e tempos de execução);
* um coletor consulta ``/history`` a cada poucos segundos e, para cada prompt
  novo, grava ``prompts/<n>_<prompt_id>.json`` com o grafo em formato API (todos
  os widgets/valores usados), o status (sucesso/erro + mensagens) e a lista de
  arquivos de saída; as imagens de saída/preview citadas são copiadas em
  miniatura (lado máximo 768 px) para ``imagens/``;
* ``eventos.jsonl`` registra fila, GPU (VRAM pico) e erros com timestamp.

A Célula 7 fecha (``finalizar``): escreve ``RESUMO.md``, zipa em
``ComfyUI_Data/relatorios/relatorio_<data>.zip`` e oferece o download.
Nada disso é enviado para lugar nenhum — o zip é para você anexar no chat.
"""
from __future__ import annotations

import datetime as _dt
import glob
import json
import os
import shutil
import subprocess
import threading
import time
import urllib.request
import zipfile

MARK = "/content/.lia_relatorio_on"
ROOT = "/content/relatorio"


def ativar(on: bool) -> str | None:
    """Célula 1: grava o marcador do toggle. Devolve a pasta se ligado."""
    if on:
        os.makedirs(ROOT, exist_ok=True)
        for sub in ("prompts", "imagens"):
            os.makedirs(os.path.join(ROOT, sub), exist_ok=True)
        open(MARK, "w").write(_dt.datetime.now().isoformat())
        return ROOT
    if os.path.exists(MARK):
        os.remove(MARK)
    return None


def ligado() -> bool:
    return os.path.exists(MARK)


def _now() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Coletor:
    """Thread que acompanha /history e /queue e copia resultados."""

    def __init__(self, port=8188, comfy="/content/ComfyUI", output_dir=None, input_dir=None,
                 intervalo=4.0, thumb=768):
        self.base = f"http://127.0.0.1:{port}"
        self.comfy = comfy
        self.output_dir = output_dir or os.path.join(comfy, "output")
        self.input_dir = input_dir or os.path.join(comfy, "input")
        self.temp_dir = os.path.join(comfy, "temp")
        self.intervalo = intervalo
        self.thumb = thumb
        self.vistos: set[str] = set()
        self.n = 0
        self.pico_vram = 0.0
        self.eventos = open(os.path.join(ROOT, "eventos.jsonl"), "a", encoding="utf-8")
        self.ev("inicio", {"comfy": comfy, "output": self.output_dir})
        self._parar = False

    # ---------------------------------------------------------------- util
    def ev(self, tipo, dados=None):
        self.eventos.write(json.dumps({"t": _now(), "tipo": tipo, **(dados or {})}, ensure_ascii=False) + "\n")
        self.eventos.flush()

    def _get(self, ep, timeout=20):
        with urllib.request.urlopen(self.base + ep, timeout=timeout) as r:
            return json.loads(r.read())

    def _vram(self):
        try:
            out = subprocess.run("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits",
                                 shell=True, capture_output=True, text=True, timeout=10).stdout.strip()
            return float(out.split("\n")[0]) / 1024.0
        except Exception:
            return None

    def _copiar_img(self, item, prompt_tag):
        """item = {"filename","subfolder","type"} do /history → miniatura em imagens/."""
        base = {"output": self.output_dir, "temp": self.temp_dir, "input": self.input_dir}.get(item.get("type", "output"))
        if not base:
            return None
        src = os.path.join(base, item.get("subfolder", ""), item["filename"])
        if not os.path.exists(src):
            return None
        nome = f"{prompt_tag}__{item.get('type','out')}__{item['filename']}"
        dst = os.path.join(ROOT, "imagens", nome)
        try:
            from PIL import Image
            im = Image.open(src)
            im.thumbnail((self.thumb, self.thumb))
            if im.mode not in ("RGB", "RGBA", "L"):
                im = im.convert("RGB")
            dst = os.path.splitext(dst)[0] + ".png"
            im.save(dst, optimize=True)
        except Exception:
            try:
                shutil.copy2(src, dst)
            except Exception:
                return None
        return os.path.basename(dst)

    # ---------------------------------------------------------------- prompts
    def _registrar(self, pid, h):
        self.n += 1
        tag = f"{self.n:03d}_{pid[:8]}"
        prompt = h.get("prompt", [])
        grafo = prompt[2] if len(prompt) > 2 else {}
        status = h.get("status", {})
        outputs = h.get("outputs", {})
        # tipos de nó usados (para eu saber que workflow é sem abrir o grafo)
        tipos = sorted({v.get("class_type", "?") for v in grafo.values()}) if isinstance(grafo, dict) else []
        imgs = []
        for nid, out in outputs.items():
            for k in ("images", "gifs", "files"):
                for it in out.get(k, []) or []:
                    if isinstance(it, dict) and it.get("filename"):
                        c = self._copiar_img(it, tag)
                        imgs.append({"node": nid, "arquivo": it.get("filename"), "tipo": it.get("type"), "copia": c})
        # textos que os nós devolvem na UI (ex.: 'info' do Accumulate, ShowText)
        textos = {}
        for nid, out in outputs.items():
            for k, v in out.items():
                if k in ("text", "string", "info") or (isinstance(v, list) and v and isinstance(v[0], str)):
                    textos[nid] = v
        msgs = status.get("messages", [])
        erros = [m for m in msgs if isinstance(m, list) and m and "error" in str(m[0])]
        # títulos dos nós (o grafo API guarda _meta.title)
        titulos = {nid: (v.get("_meta") or {}).get("title") for nid, v in grafo.items()} if isinstance(grafo, dict) else {}
        reg = {
            "prompt_id": pid, "registrado_em": _now(),
            "status": status.get("status_str"), "completo": status.get("completed"),
            "tipos_de_no": tipos, "n_nos": len(grafo) if isinstance(grafo, dict) else 0,
            "erros": erros, "mensagens": msgs, "textos_saida": textos, "imagens": imgs,
            "titulos": titulos, "grafo_api": grafo,
        }
        with open(os.path.join(ROOT, "prompts", f"{tag}.json"), "w", encoding="utf-8") as f:
            json.dump(reg, f, ensure_ascii=False, indent=1)
        self.ev("prompt", {"tag": tag, "status": reg["status"], "n_nos": reg["n_nos"],
                           "imagens": len(imgs), "erros": len(erros), "tipos": tipos[:40]})
        return tag

    # ---------------------------------------------------------------- loop
    def _loop(self):
        # espera o servidor
        while not self._parar:
            try:
                self._get("/system_stats", timeout=5)
                break
            except Exception:
                time.sleep(3)
        try:
            self.ev("servidor_ok", {"system_stats": self._get("/system_stats")})
        except Exception:
            pass
        fila_ant = -1
        while not self._parar:
            time.sleep(self.intervalo)
            try:
                q = self._get("/queue")
                fila = len(q.get("queue_running", [])) + len(q.get("queue_pending", []))
                if fila != fila_ant:
                    self.ev("fila", {"rodando": len(q.get("queue_running", [])), "pendente": len(q.get("queue_pending", []))})
                    fila_ant = fila
                v = self._vram()
                if v is not None and v > self.pico_vram:
                    self.pico_vram = v
                    self.ev("vram_pico", {"gb": round(v, 2)})
                hist = self._get("/history?max_items=200")
                for pid, h in hist.items():
                    if pid in self.vistos:
                        continue
                    st = (h.get("status") or {})
                    if not st.get("completed") and st.get("status_str") != "error":
                        continue
                    self.vistos.add(pid)
                    try:
                        self._registrar(pid, h)
                    except Exception as e:
                        self.ev("erro_registro", {"pid": pid, "erro": repr(e)})
            except Exception as e:
                self.ev("erro_coletor", {"erro": repr(e)[:200]})

    def iniciar(self):
        threading.Thread(target=self._loop, daemon=True).start()
        return self

    def parar(self):
        self._parar = True


def rodar_comfy_com_log(cmd: str, cwd: str, log_path: str | None = None):
    """Substitui o ``!python main.py`` quando o relatório está ligado: imprime
    o log na célula E grava em ``comfyui.log``. Ctrl+C / parar célula encerra
    o servidor como antes."""
    log_path = log_path or os.path.join(ROOT, "comfyui.log")
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n===== {_now()} $ {cmd}\n")
        p = subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, bufsize=1)
        try:
            for line in p.stdout:
                print(line, end="")
                log.write(line)
        except KeyboardInterrupt:
            p.terminate()
            try:
                p.wait(15)
            except Exception:
                p.kill()
            log.write(f"===== {_now()} interrompido pelo usuário\n")
            raise
        finally:
            log.write(f"===== {_now()} fim (rc={p.poll()})\n")


def _resumo():
    linhas = [f"# Relatório da sessão ComfyUI — {_now()}", ""]
    try:
        smi = subprocess.run("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader", shell=True,
                             capture_output=True, text=True, timeout=10).stdout.strip()
        linhas.append(f"GPU: {smi}")
    except Exception:
        pass
    evs = []
    p = os.path.join(ROOT, "eventos.jsonl")
    if os.path.exists(p):
        for l in open(p, encoding="utf-8"):
            try:
                evs.append(json.loads(l))
            except Exception:
                pass
    pico = max([e.get("gb", 0) for e in evs if e.get("tipo") == "vram_pico"] or [0])
    linhas += [f"VRAM pico: {pico:.1f} GB", "", "## Prompts executados", ""]
    for f in sorted(glob.glob(os.path.join(ROOT, "prompts", "*.json"))):
        try:
            r = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        linhas.append(f"### {os.path.basename(f)[:-5]} — {r.get('status')} — {r.get('n_nos')} nós, {len(r.get('imagens', []))} imagem(ns)")
        lia = [t for t in r.get("tipos_de_no", []) if t.startswith("Lia") or t in ("UnwrapMesh", "DecimateMesh", "RemeshMesh", "SaveGLB", "Trellis2", "Pixal3D")]
        if lia:
            linhas.append(f"- nós-chave: {', '.join(lia)}")
        for e in r.get("erros", []):
            linhas.append(f"- **ERRO**: `{json.dumps(e, ensure_ascii=False)[:400]}`")
        for nid, tx in (r.get("textos_saida") or {}).items():
            tt = r.get("titulos", {}).get(nid) or nid
            linhas.append(f"- {tt}: `{json.dumps(tx, ensure_ascii=False)[:300]}`")
        linhas.append("")
    # erros do log
    lp = os.path.join(ROOT, "comfyui.log")
    if os.path.exists(lp):
        tb = []
        for l in open(lp, encoding="utf-8", errors="replace"):
            if "Traceback" in l or "Error" in l or "error" in l[:40]:
                tb.append(l.rstrip())
        if tb:
            linhas += ["## Linhas de erro do log (últimas 60)", "```"] + tb[-60:] + ["```", ""]
    linhas += ["## Conteúdo", "- `comfyui.log` — saída completa do servidor",
               "- `prompts/*.json` — cada execução: grafo API com valores, status, textos de saída, imagens",
               "- `imagens/` — miniaturas das saídas/previews", "- `eventos.jsonl` — fila, VRAM, erros"]
    open(os.path.join(ROOT, "RESUMO.md"), "w", encoding="utf-8").write("\n".join(linhas))


def finalizar(drive_data="/content/drive/MyDrive/ComfyUI_Data", baixar=True):
    """Célula 7: fecha o relatório, zipa, copia no Drive e baixa."""
    if not os.path.isdir(ROOT):
        print("Relatório não estava ligado nesta sessão (toggle da Célula 1).")
        return None
    _resumo()
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M")
    dest_dir = os.path.join(drive_data, "relatorios")
    os.makedirs(dest_dir, exist_ok=True)
    zpath = os.path.join(dest_dir, f"relatorio_{stamp}.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, _, fs in os.walk(ROOT):
            for fn in fs:
                full = os.path.join(dp, fn)
                z.write(full, os.path.relpath(full, ROOT))
    mb = os.path.getsize(zpath) / 1e6
    print(f"Relatório: {zpath}  ({mb:.1f} MB)")
    print(open(os.path.join(ROOT, "RESUMO.md"), encoding="utf-8").read()[:3000])
    if baixar:
        try:
            from google.colab import files
            files.download(zpath)
        except Exception as e:
            print("(download automático falhou — pegue no Drive:", e, ")")
    return zpath
