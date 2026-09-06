#!/usr/bin/env python3
"""Executa e mede o teste A/B entre AnimateDiff (SD1.5) e WAN 2.2 5B.

Duas funcoes:

  --medir   analisa os frames gerados e junta com tempo/VRAM medidos pela C6

TEMPO E VRAM: nao precisam de celula separada (o Colab so roda uma por vez e a
C6 e bloqueante). O monitor vive DENTRO da C6 como thread e grava em
output/ab_test/medicoes.json a cada job que termina.

O que da para medir por codigo (e o que este script faz):
  - tempo de processamento
  - VRAM maxima
  - estabilidade entre frames (quanto muda de um frame para o proximo)
  - deriva de identidade (frame N vs frame 0)
  - quantidade real de movimento
  - flicker de cor (o sintoma que apareceu no WAN sem ModelSamplingSD3)
  - se o loop fecha (ultimo frame parecido com o primeiro)

O que NAO da para medir por codigo: se ficou bonito. Isso e voce quem julga
olhando os GIFs.

Uso:
    python scripts/ab_test.py --rodar
    python scripts/ab_test.py --medir
    python scripts/ab_test.py --medir --dir /content/drive/MyDrive/ComfyUI_Data/output
"""
import argparse
import glob
import json
import os
import statistics
import sys
import threading
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = 'http://127.0.0.1:8188'


# --------------------------------------------------------------- medicao
def carregar(pasta):
    from PIL import Image
    fs = sorted(f for f in glob.glob(os.path.join(pasta, '*.png'))
                if '_sheet' not in f)
    return fs, [Image.open(f).convert('RGB') for f in fs]


def dif(a, b, passo=3):
    """Distancia media entre dois frames, contando so onde ha personagem.

    Normalizar pela area do personagem evita que uma imagem com muito fundo
    branco pareca "estavel" so por ter poucos pixels uteis.
    """
    pa, pb = a.load(), b.load()
    w, h = a.size
    s = n = 0
    for y in range(0, h, passo):
        for x in range(0, w, passo):
            ca, cb = pa[x, y], pb[x, y]
            fundo_a = max(ca[:3]) > 240 and min(ca[:3]) > 240
            fundo_b = max(cb[:3]) > 240 and min(cb[:3]) > 240
            if fundo_a and fundo_b:
                continue
            s += abs(ca[0]-cb[0]) + abs(ca[1]-cb[1]) + abs(ca[2]-cb[2])
            n += 3
    return s / max(n, 1)


def cor_media(im, passo=3):
    """Cor media SO do personagem.

    Medir a imagem toda dilui o flicker no fundo branco: um desvio forte na
    roupa vira um numero pequeno. Ignoramos pixels quase brancos/pretos.
    """
    px = im.load()
    w, h = im.size
    r = g = b = n = 0
    for y in range(0, h, passo):
        for x in range(0, w, passo):
            c = px[x, y]
            mx, mn = max(c[:3]), min(c[:3])
            if mx > 240 and mn > 240:      # fundo branco
                continue
            if mx < 18:                    # fundo preto/alpha
                continue
            r += c[0]; g += c[1]; b += c[2]; n += 1
    if not n:
        return (0.0, 0.0, 0.0)
    return (r/n, g/n, b/n)


def analisar(pasta, rotulo):
    fs, ims = carregar(pasta)
    if len(ims) < 2:
        print(f'  [{rotulo}] frames insuficientes em {pasta} ({len(ims)})')
        return None

    consec = [dif(ims[i], ims[i+1]) for i in range(len(ims)-1)]
    deriva = [dif(ims[0], ims[i]) for i in range(1, len(ims))]
    cores = [cor_media(im) for im in ims]
    flick = [max(abs(cores[i][c]-cores[i+1][c]) for c in range(3))
             for i in range(len(cores)-1)]
    loop = dif(ims[-1], ims[0])
    passo = statistics.median(consec) if consec else 0

    r = {
        'rotulo': rotulo,
        'frames': len(ims),
        'movimento': round(statistics.mean(consec), 2),
        'movimento_max': round(max(consec), 2),
        'estabilidade': round(statistics.pstdev(consec), 2) if len(consec) > 1 else 0.0,
        'deriva_final': round(deriva[-1], 2),
        'deriva_max': round(max(deriva), 2),
        'flicker_cor': round(max(flick), 2) if flick else 0.0,
        'loop': round(loop, 2),
        'loop_ok': round(abs(loop - passo) / max(passo, 0.01), 2),
    }
    return r


def imprimir(rs):
    if not any(rs):
        print('\nNenhum resultado. Rode os workflows primeiro.')
        return
    rs = [r for r in rs if r]
    print('\n' + '=' * 74)
    print('  MEDIDAS OBJETIVAS  (menor = melhor, exceto "movimento")')
    print('=' * 74)
    linhas = [
        ('frames gerados',      'frames',        ''),
        ('movimento medio',     'movimento',     'quanto muda entre frames'),
        ('pico de movimento',   'movimento_max', 'salto brusco = ruim'),
        ('INSTABILIDADE',       'estabilidade',  'variacao do movimento'),
        ('deriva no ultimo',    'deriva_final',  'quanto fugiu do frame 0'),
        ('deriva maxima',       'deriva_max',    'pior fuga de identidade'),
        ('FLICKER de cor',      'flicker_cor',   'oscilacao de cor'),
        ('emenda do loop',      'loop_ok',       '0 = loop perfeito'),
    ]
    cab = f"  {'metrica':22} " + ''.join(f"{r['rotulo']:>14}" for r in rs)
    print(cab)
    print('  ' + '-' * 70)
    for nome, chave, obs in linhas:
        vals = ''.join(f"{r[chave]:>14}" for r in rs)
        print(f'  {nome:22} {vals}   {obs}')
    print('=' * 74)

    if len(rs) == 2:
        a, b = rs
        print('\n  LEITURA:')
        for r in rs:
            if r['movimento'] < 1.5:
                print(f"  !! {r['rotulo']}: movimento {r['movimento']} — "
                      f"praticamente PARADO.")
            if r['flicker_cor'] > 6:
                print(f"  !! {r['rotulo']}: flicker de cor {r['flicker_cor']} — "
                      f"a cor OSCILA entre frames (ruim para sprite).")
            if r['deriva_max'] > 25:
                print(f"  !! {r['rotulo']}: deriva {r['deriva_max']} — "
                      f"o personagem MUDA ao longo da animacao.")
        est = min(rs, key=lambda r: r['estabilidade'])
        print(f'  Mais estavel entre frames: {est["rotulo"]}')
        idt = min(rs, key=lambda r: r['deriva_max'])
        print(f'  Preserva mais a identidade: {idt["rotulo"]}')
        lp = min(rs, key=lambda r: r['loop_ok'])
        print(f'  Loop fecha melhor: {lp["rotulo"]}')
        print('\n  Isto mede ESTABILIDADE, nao beleza. Abra os dois GIFs para')
        print('  julgar qualidade do movimento e deformacao.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--medir', action='store_true', help='analisa os frames')
    ap.add_argument('--server', default=SERVER)
    ap.add_argument('--dir', default=None, help='pasta output do ComfyUI')
    a = ap.parse_args()

    if not a.medir:
        ap.print_help()
        return

    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        sys.exit('Falta Pillow:  pip install pillow')

    bases = [a.dir] if a.dir else [
        '/content/drive/MyDrive/ComfyUI_Data/output',
        os.path.expanduser('~/ComfyUI_Data/output'),
        'output']
    base = next((b for b in bases if b and os.path.isdir(b)), None)
    if not base:
        sys.exit(f'Pasta de output nao encontrada. Use --dir')

    print(f'Lendo de: {base}')

    med = []
    pm = os.path.join(base, 'ab_test', 'medicoes.json')
    if os.path.exists(pm):
        try:
            med = json.load(open(pm))
        except Exception:
            pass
    if med:
        print(f'\n  TEMPO E VRAM (medidos pela C6, ultimos {min(2,len(med))} jobs):')
        for m in med[-2:]:
            print(f"    {m['quando']}  {m['segundos']/60:5.1f} min   "
                  f"pico {m['vram_pico_mb']:5} MB  (+{m['vram_delta_mb']} do idle)")
    else:
        print('\n  (sem medicoes.json — rode os workflows com a C6 v48+ ativa)')

    rs = []
    for sub, rot in (('ab_test/A_sd15_idle', 'A_SD1.5'),
                     ('ab_test/B_wan_idle', 'B_WAN')):
        p = os.path.join(base, sub)
        if os.path.isdir(p):
            rs.append(analisar(p, rot))
        else:
            print(f'  (ainda nao existe: {p})')
            rs.append(None)
    imprimir(rs)


if __name__ == '__main__':
    main()
