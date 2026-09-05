#!/usr/bin/env python3
"""Monta spritesheet a partir dos frames extraidos de um clipe.

Faz localmente o que o Sprite Analyzer do video do DevDude faz:
  - recorta o excesso transparente mantendo TODOS os frames no mesmo canvas
  - alinha horizontalmente (tira o "jitter" que faz o loop pular no fim)
  - acha o melhor loop comparando o primeiro frame com os candidatos a ultimo
  - escreve o spritesheet PNG + JSON com os dados + .tres do Godot

Uso:
    python scripts/make_spritesheet.py <pasta_dos_frames> [--nome walk] [--cols 0]
        [--sem-loop] [--altura 128]

Depende so de Pillow.
"""
import argparse
import json
import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit('Falta Pillow:  pip install pillow')


def carregar(pasta):
    exts = ('.png', '.webp')
    # ignora saidas de execucoes anteriores, senao o spritesheet vira "frame"
    arqs = sorted(f for f in os.listdir(pasta)
                  if f.lower().endswith(exts) and not f.endswith('_sheet.png'))
    if not arqs:
        sys.exit(f'Nenhum PNG em {pasta}')
    ims = [Image.open(os.path.join(pasta, f)).convert('RGBA') for f in arqs]
    return arqs, ims


def bbox_uniao(ims):
    """Uma caixa que serve para todos os frames: o personagem nao muda de escala."""
    caixas = [im.getbbox() for im in ims]
    caixas = [c for c in caixas if c]
    if not caixas:
        sys.exit('Todos os frames estao vazios (alpha 100%). O rembg comeu tudo?')
    return (min(c[0] for c in caixas), min(c[1] for c in caixas),
            max(c[2] for c in caixas), max(c[3] for c in caixas))


def centro_x(im):
    """Centro horizontal da massa de pixels opacos."""
    a = im.split()[-1]
    w, h = a.size
    px = a.load()
    total = soma = 0
    for x in range(w):
        col = 0
        for y in range(0, h, 2):          # amostra: 2x mais rapido, precisao igual
            col += px[x, y]
        soma += col * x
        total += col
    return soma / total if total else w / 2


def alinhar(ims):
    """Reposiciona cada frame para o mesmo centro horizontal.

    Sem isto o ciclo de walk "pula para tras" no fim do loop, porque o modelo
    de video deriva o personagem alguns pixels por frame.
    """
    centros = [centro_x(im) for im in ims]
    alvo = sum(centros) / len(centros)
    out = []
    for im, c in zip(ims, centros):
        dx = int(round(alvo - c))
        novo = Image.new('RGBA', im.size, (0, 0, 0, 0))
        novo.paste(im, (dx, 0))
        out.append(novo)
    return out


def diferenca(a, b):
    """Distancia media entre dois frames (menor = mais parecidos)."""
    pa, pb = a.load(), b.load()
    w, h = a.size
    soma = n = 0
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            ca, cb = pa[x, y], pb[x, y]
            soma += abs(ca[0]-cb[0]) + abs(ca[1]-cb[1]) + abs(ca[2]-cb[2]) + abs(ca[3]-cb[3])
            n += 1
    return soma / max(n, 1)


def descartar_outliers(ims):
    """Remove frames que destoam de todo o resto.

    Clipes de IA costumam abrir/fechar com frames de transicao (fade, pose
    quebrada, personagem saindo do quadro). Eles sao muito diferentes da
    mediana do clipe.
    """
    n = len(ims)
    if n < 6:
        return 0, n - 1
    meio = ims[n // 2]
    ds = [diferenca(im, meio) for im in ims]
    ordenado = sorted(ds)
    mediana = ordenado[len(ordenado) // 2]
    limite = max(mediana * 2.5, 12.0)
    ini = 0
    while ini < n - 3 and ds[ini] > limite:
        ini += 1
    fim = n - 1
    while fim > ini + 2 and ds[fim] > limite:
        fim -= 1
    return ini, fim


def achar_loop(ims, minimo=4):
    """Acha onde cortar para o loop fechar.

    O truque do video: descartar frames do inicio e do fim. A emenda boa nao e
    a que tem frames IGUAIS (isso premiaria dois frames-lixo identicos) — e a
    que tem entre o ultimo e o primeiro a MESMA distancia que existe entre dois
    frames consecutivos quaisquer. Assim o movimento continua no mesmo ritmo.
    """
    a, b = descartar_outliers(ims)
    if b - a + 1 < minimo:
        a, b = 0, len(ims) - 1
    janela = ims[a:b + 1]
    n = len(janela)
    if n <= minimo:
        return a, b

    consec = [diferenca(janela[i], janela[i + 1]) for i in range(n - 1)]
    passo = sorted(consec)[len(consec) // 2] or 1.0

    melhor, score = (a, b), None
    for ini in range(0, max(1, n // 3)):
        for fim in range(n - 1, ini + minimo - 1, -1):
            emenda = diferenca(janela[fim], janela[ini])
            # perto de um passo normal = loop suave; penaliza loop curto demais
            s = abs(emenda - passo) / passo + 0.35 * (1.0 - (fim - ini) / (n - 1))
            if score is None or s < score:
                score, melhor = s, (a + ini, a + fim)
    return melhor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pasta')
    ap.add_argument('--nome', default=None, help='nome da animacao (default: nome da pasta)')
    ap.add_argument('--cols', type=int, default=0, help='0 = tudo numa linha')
    ap.add_argument('--altura', type=int, default=0, help='redimensiona o frame (ex: 128)')
    ap.add_argument('--sem-loop', action='store_true', help='usa todos os frames')
    ap.add_argument('--sem-alinhar', action='store_true')
    ap.add_argument('--fps', type=int, default=12)
    a = ap.parse_args()

    nome = a.nome or os.path.basename(os.path.abspath(a.pasta))
    arqs, ims = carregar(a.pasta)
    print(f'{len(ims)} frames em {a.pasta}')

    # ALINHAR ANTES DE RECORTAR: se o personagem deriva pela tela, a caixa de
    # uniao fica larguissima (soma a deriva). Alinhado, a caixa cola no corpo.
    if not a.sem_alinhar:
        ims = alinhar(ims)
        print('frames alinhados no centro de massa')

    caixa = bbox_uniao(ims)
    ims = [im.crop(caixa) for im in ims]
    print(f'recorte comum: {caixa[2]-caixa[0]}x{caixa[3]-caixa[1]}')

    if a.sem_loop:
        ini, fim = 0, len(ims) - 1
    else:
        ini, fim = achar_loop(ims)
        print(f'loop: frames {ini}..{fim}  (descartados {ini} no inicio, '
              f'{len(ims)-1-fim} no fim)')
    ims = ims[ini:fim + 1]

    if a.altura:
        r = a.altura / ims[0].height
        ims = [im.resize((max(1, int(im.width * r)), a.altura), Image.LANCZOS) for im in ims]
        print(f'redimensionado para altura {a.altura}')

    fw, fh = ims[0].size
    cols = a.cols if a.cols > 0 else len(ims)
    rows = (len(ims) + cols - 1) // cols
    folha = Image.new('RGBA', (cols * fw, rows * fh), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        folha.paste(im, ((i % cols) * fw, (i // cols) * fh))

    saida = os.path.join(a.pasta, f'{nome}_sheet.png')
    folha.save(saida)
    meta = {'nome': nome, 'frames': len(ims), 'frame_w': fw, 'frame_h': fh,
            'cols': cols, 'rows': rows, 'fps': a.fps, 'loop': not a.sem_loop}
    with open(os.path.join(a.pasta, f'{nome}_sheet.json'), 'w') as fh_:
        json.dump(meta, fh_, indent=2)

    tres = f'''[gd_resource type="SpriteFrames" format=3]

[ext_resource type="Texture2D" path="res://sprites/{nome}_sheet.png" id="1"]

; {len(ims)} frames de {fw}x{fh}, {cols} coluna(s) x {rows} linha(s)
; No Godot: AnimatedSprite2D -> SpriteFrames -> "Add frames from sheet"
; Horizontal: {cols}   Vertical: {rows}   FPS: {a.fps}   Loop: {str(not a.sem_loop).lower()}
; Vire o sprite com flip_h para o outro lado (nao gere de novo).
'''
    with open(os.path.join(a.pasta, f'{nome}_godot.txt'), 'w') as fh_:
        fh_.write(tres)

    print(f'\nspritesheet: {saida}')
    print(f'  {len(ims)} frames de {fw}x{fh} | grade {cols}x{rows} | {a.fps} fps')
    print(f'  no Godot: importe e use "Add frames from sheet" {cols}x{rows}')


if __name__ == '__main__':
    main()
