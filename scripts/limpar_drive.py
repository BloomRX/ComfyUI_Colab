#!/usr/bin/env python3
"""Audita os modelos no Drive e diz o que da para apagar.

NAO APAGA NADA sozinho. Lista, classifica e gera os comandos `rm` para voce
revisar e executar.

Classificacao:
  MANTER    referenciado por um workflow do pipeline ativo
  DESCARTAR referenciado so por workflow que ja foi reprovado/aposentado
  ORFAO     esta no Drive e nenhum workflow do repo referencia

Uso no Colab (uma celula):
    !python /content/ComfyUI_Colab/scripts/limpar_drive.py
    !python /content/ComfyUI_Colab/scripts/limpar_drive.py --gerar-script
"""
import argparse
import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = r'\.(safetensors|ckpt|gguf|pt|pth|bin|onnx|sft)$'

# Workflows do pipeline ATIVO. O resto e do tutorial ou de teste concluido.
ATIVOS = {
    'WaifuSurvivors_Base',            # concept -> splash + chibi
    'WaifuSurvivors_Concept',         # exploracao
    'WaifuSurvivors_CharacterSheet',  # turnaround / dataset de LoRA
    'WaifuSurvivors_AnimateWan',      # ANIMACAO — arquitetura vencedora
    'WaifuSurvivors_VideoToSprites',  # frames -> spritesheet
    'AB_D_illustrious_wan_idle',      # prototipo validado
}

# Motivo pelo qual algo saiu do pipeline (para explicar no relatorio).
APOSENTADOS = {
    'WaifuSurvivors_Animate':    'Hotshot-XL: reprovado (v32/v50), WAN e melhor',
    'WaifuSurvivors_AnimateSD15': 'SD1.5: reprovado (v51), fidelidade 73.8',
    'AB_A_sd15_idle':            'teste A/B concluido',
    'AB_B_wan_idle':             'teste A/B concluido',
    'AB_C_sd15_walk':            'rota SD1.5 reprovada',
    'DEN_040_denoise':           'teste de denoise concluido (v54)',
    'DEN_050_denoise':           'teste de denoise concluido (v54)',
    'DEN_060_denoise':           'teste de denoise concluido (v54)',
    'DEN_070_denoise':           'teste de denoise concluido (v54)',
    'DEN_100_denoise':           'teste de denoise concluido (v54)',
    'CharDesignandPartSplitting': 'workflow do tutorial, nunca usado',
    'Mesh_Processing':           'nao cabe no T4 (documentado)',
    'Efaces_Pony_XL_V01':        'workflow do tutorial, nunca usado',
    'PotatCats-inpaint_workflow-ANIMA-V1Beta-rel': 'tutorial, nunca usado',
    'Skintoken':                 'exige Blender no PATH, nunca usado',
    'Detailer':                  'tutorial; util no futuro para retoque',
    'WaifuInpaintXL':            'tutorial; modelo gated',
    'WaifuVroid':                'projeto Lia (parado)',
    'WaifuVroid_FromConcept':    'projeto Lia (parado)',
}


# Modelos que NENHUMA varredura de texto acha, porque o no os carrega por
# preset e nao por nome de arquivo. Sem isto o script os marcaria como orfaos
# e mandaria apagar algo em uso.
IMPLICITOS = {
    'IPAdapterUnifiedLoader': [
        'ip-adapter-plus_sdxl_vit-h.safetensors',
        'ip-adapter-plus_sd15.safetensors',
        'CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors',
    ],
    'InspyrenetRembg': [],   # baixa sozinho no primeiro uso
}


def refs_do_workflow(caminho):
    achados = set()

    def walk(o):
        if isinstance(o, str):
            s = o.strip()
            if re.search(EXT, s, re.I) and not s.lower().startswith('http'):
                achados.add(s.replace('\\', '/').split('/')[-1])
        elif isinstance(o, list):
            for x in o:
                walk(x)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)

    try:
        d = json.load(open(caminho, encoding='utf-8'))
        walk(d)
        # nos que carregam por preset
        for n in d.get('nodes', []):
            for extra in IMPLICITOS.get(n.get('type'), []):
                achados.add(extra)
    except Exception:
        pass
    return achados


def humano(n):
    for u in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or u == 'GB':
            return f'{n:.1f} {u}'
        n /= 1024


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--drive', default=None)
    ap.add_argument('--gerar-script', action='store_true',
                    help='escreve apagar.sh em vez de so listar')
    a = ap.parse_args()

    bases = [a.drive] if a.drive else [
        '/content/drive/MyDrive/ComfyUI_Data',
        os.path.expanduser('~/ComfyUI_Data'),
    ]
    base = next((b for b in bases if b and os.path.isdir(b)), None)
    if not base:
        sys.exit('ComfyUI_Data nao encontrado. Use --drive CAMINHO')

    # quem usa o que
    usado_por = {}
    for p in sorted(glob.glob(os.path.join(RAIZ, 'Workflows', '*.json'))):
        nome = os.path.basename(p)[:-5]
        for f in refs_do_workflow(p):
            usado_por.setdefault(f, set()).add(nome)

    # o que existe no Drive
    arquivos = []
    for dirpath, _, nomes in os.walk(os.path.join(base, 'models')):
        for n in nomes:
            if re.search(EXT, n, re.I):
                fp = os.path.join(dirpath, n)
                try:
                    arquivos.append((fp, os.path.getsize(fp)))
                except OSError:
                    pass

    if not arquivos:
        sys.exit(f'Nenhum modelo em {base}/models')

    manter, descartar, orfao = [], [], []
    for fp, sz in arquivos:
        n = os.path.basename(fp)
        wfs = usado_por.get(n, set())
        if wfs & ATIVOS:
            manter.append((fp, sz, sorted(wfs & ATIVOS)))
        elif wfs:
            descartar.append((fp, sz, sorted(wfs)))
        else:
            orfao.append((fp, sz, []))


    tot = sum(s for _, s in arquivos)
    print(f'Drive: {base}/models')
    print(f'Total em modelos: {humano(tot)}  ({len(arquivos)} arquivos)\n')

    def bloco(titulo, itens, explica=False):
        if not itens:
            return 0
        soma = sum(s for _, s, _ in itens)
        print('=' * 74)
        print(f'  {titulo}  —  {humano(soma)} em {len(itens)} arquivo(s)')
        print('=' * 74)
        for fp, sz, wfs in sorted(itens, key=lambda x: -x[1]):
            rel = fp.replace(base + '/', '')
            print(f'  {humano(sz):>9}  {rel}')
            if explica and wfs:
                for w in wfs:
                    print(f'             ^ so {w}: {APOSENTADOS.get(w, "?")}')
        print()
        return soma

    bloco('MANTER (pipeline ativo)', manter)
    s_desc = bloco('DESCARTAR (so workflow aposentado)', descartar, explica=True)
    s_orf = bloco('ORFAO (nenhum workflow usa)', orfao)

    print('=' * 74)
    print(f'  LIBERAVEL: {humano(s_desc + s_orf)}')
    print('=' * 74)
    print('\n  Revise a lista. ORFAO pode conter algo que voce baixou de')
    print('  proposito e ainda quer — conferir antes de apagar.\n')

    if a.gerar_script:
        cam = os.path.join(base, 'apagar.sh')
        with open(cam, 'w') as f:
            f.write('#!/bin/bash\n# Revise antes de rodar!  bash apagar.sh\n\n')
            for titulo, itens in (('DESCARTAR', descartar), ('ORFAO', orfao)):
                f.write(f'\n# ---- {titulo} ----\n')
                for fp, sz, _ in sorted(itens, key=lambda x: -x[1]):
                    f.write(f'rm -v "{fp}"   # {humano(sz)}\n')
        print(f'  Script gerado: {cam}')
        print(f'  Revise e rode:  !bash "{cam}"')


if __name__ == '__main__':
    main()
