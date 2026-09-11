#!/usr/bin/env python3
"""Gera as poses-chave que o SparseCtrl usa como condicionamento.

O `WaifuSurvivors_AnimateSD15` precisa de imagens de pose nos frames-chave.
Este script desenha bonecos-palito nos momentos certos de cada ciclo de
animacao, no formato que o SparseCtrl RGB aceita.

Nao substitui arte: e um andaime. Se voce tiver sketches melhores do proprio
chibi nas mesmas poses, use os seus — ficam melhores.

Uso:
    python scripts/gerar_poses.py --anim walk
    python scripts/gerar_poses.py --anim attack --tam 512
    python scripts/gerar_poses.py --listar

Saida: pose_<anim>_00.png, _01.png ... + a lista de indices para o no 10.
"""
import argparse
import math
import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit('Falta Pillow:  pip install pillow')


# Cada pose e descrita por angulos simples (graus) das articulacoes.
# ombro/cotovelo/quadril/joelho, negativo = para tras.
# (nome, braco_esq, braco_dir, perna_esq, perna_dir, inclinacao, altura_quadril)
CICLOS = {
    'walk': {
        'frames': 16,
        'indices': [0, 4, 8, 12],
        'poses': [
            ('contact esquerdo',  30, -30, -35,  35, 0,  0),
            ('passing',            0,   0,   0,  10, 0, -6),
            ('contact direito',  -30,  30,  35, -35, 0,  0),
            ('passing',            0,   0,  10,   0, 0, -6),
        ],
    },
    'run': {
        'frames': 16,
        'indices': [0, 4, 8, 12],
        'poses': [
            ('contact esquerdo',  55, -55, -55,  50, 12, 0),
            ('air',               20, -20,  25,  60, 15, -14),
            ('contact direito',  -55,  55,  50, -55, 12, 0),
            ('air',              -20,  20,  60,  25, 15, -14),
        ],
    },
    'idle': {
        'frames': 16,
        'indices': [0, 8],
        'poses': [
            ('respirando (cima)',  8, -8, 0, 0, 0, -3),
            ('respirando (baixo)', 5, -5, 0, 0, 0,  0),
        ],
    },
    'attack': {
        'frames': 16,
        'indices': [0, 4, 8, 12],
        'poses': [
            ('preparacao',       -60,  40,  10, -10, -10, 0),
            ('inicio do golpe',   20, -10,  20, -20,   5, 0),
            ('impacto',          100, -40,  30, -30,  18, 0),
            ('recuperacao',       40, -20,  10, -10,   5, 0),
        ],
    },
    'hit': {
        'frames': 12,
        'indices': [0, 4, 8],
        'poses': [
            ('impacto',      -40,  60, -20,  20, -22, 0),
            ('recuo',        -20,  40, -30,  10, -14, -4),
            ('recuperacao',    5,  -5,   0,   0,   0, 0),
        ],
    },
    'death': {
        'frames': 16,
        'indices': [0, 6, 12],
        'poses': [
            ('cambaleia',   -30,  40, -15,  15, -18,  0),
            ('joelhos',     -10,  20,  70, -70,  25, 34),
            ('no chao',      60, -60,  85, -85,  85, 62),
        ],
    },
    'jump': {
        'frames': 16,
        'indices': [0, 5, 10, 14],
        'poses': [
            ('agachado',      -25,  25,  60, -60,  8, 26),
            ('impulso',       -70,  70, -20,  20, -6, -10),
            ('no ar',         -50,  50,  30, -30,  0, -18),
            ('aterrissagem',  -20,  20,  50, -50,  8,  20),
        ],
    },
}


def ponto(x, y, ang, comp):
    """Extremidade de um segmento saindo de (x,y).

    ang = 0 aponta para BAIXO. Positivo joga para a frente (direita da tela),
    negativo para tras. Em tela, y cresce para baixo, entao cos entra positivo.
    """
    r = math.radians(ang)
    return (x + comp * math.sin(r), y + comp * math.cos(r))


def desenhar(tam, bracos, pernas, incl, dy):
    """Boneco-palito com proporcao CHIBI: cabeca grande, corpo curto."""
    im = Image.new('RGB', (tam, tam), (0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = tam // 2
    esc = tam / 512.0
    lw = max(3, int(10 * esc))

    # chibi ~2 cabecas: cabeca grande em cima, tronco curto, membros visiveis
    r_cab = int(78 * esc)
    y_cab = int(120 * esc) + int(dy * esc)      # centro da cabeca
    y_omb = y_cab + r_cab + int(10 * esc)       # ombros ABAIXO da cabeca
    y_qua = y_omb + int(70 * esc)               # quadril

    ix = math.sin(math.radians(incl)) * 26 * esc   # inclinacao do tronco

    # cabeca
    d.ellipse([cx + ix - r_cab, y_cab - r_cab, cx + ix + r_cab, y_cab + r_cab],
              outline=(255, 255, 255), width=lw)
    # tronco (do ombro ao quadril)
    d.line([cx + ix, y_omb, cx, y_qua], fill=(255, 255, 255), width=lw)

    # bracos em VERDE, saindo do ombro para BAIXO (ang 0 = pendido)
    for ang, cor in zip(bracos, [(90, 255, 90), (40, 170, 40)]):
        ox = cx + ix
        cot = ponto(ox, y_omb, ang, 44 * esc)
        mao = ponto(cot[0], cot[1], ang * 0.55, 40 * esc)
        d.line([ox, y_omb, *cot], fill=cor, width=lw)
        d.line([*cot, *mao], fill=cor, width=lw)
        d.ellipse([mao[0] - 8 * esc, mao[1] - 8 * esc,
                   mao[0] + 8 * esc, mao[1] + 8 * esc], fill=cor)

    # pernas em VERMELHO, saindo do quadril para BAIXO
    for ang, cor in zip(pernas, [(255, 90, 90), (180, 40, 40)]):
        joe = ponto(cx, y_qua, ang, 54 * esc)
        pe = ponto(joe[0], joe[1], ang * 0.35, 50 * esc)
        d.line([cx, y_qua, *joe], fill=cor, width=lw)
        d.line([*joe, *pe], fill=cor, width=lw)
        d.ellipse([pe[0] - 9 * esc, pe[1] - 9 * esc,
                   pe[0] + 9 * esc, pe[1] + 9 * esc], fill=cor)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--anim', default='walk', choices=sorted(CICLOS))
    ap.add_argument('--tam', type=int, default=512)
    ap.add_argument('--saida', default=None,
                    help='pasta de saida (default: input do ComfyUI, se existir)')
    ap.add_argument('--listar', action='store_true')
    a = ap.parse_args()

    if a.listar:
        print('Ciclos disponiveis:\n')
        for nome, c in CICLOS.items():
            print(f"  {nome:8} {len(c['poses'])} poses em {c['frames']} frames"
                  f"  -> indices {','.join(map(str, c['indices']))}")
        return

    c = CICLOS[a.anim]
    # por padrao escreve direto no input/ do ComfyUI, para o no 9 enxergar
    if a.saida is None:
        for base in ('/content/drive/MyDrive/ComfyUI_Data/input',
                     os.path.expanduser('~/ComfyUI_Data/input'),
                     'input'):
            if os.path.isdir(base):
                a.saida = os.path.join(base, f'poses_{a.anim}')
                break
        else:
            a.saida = f'poses_{a.anim}'
    os.makedirs(a.saida, exist_ok=True)
    for i, (nome, be, bd, pe, pd, incl, dy) in enumerate(c['poses']):
        im = desenhar(a.tam, (be, bd), (pe, pd), incl, dy)
        p = os.path.join(a.saida, f'pose_{a.anim}_{i:02d}.png')
        im.save(p)
        print(f'  frame {c["indices"][i]:2}  {nome:20} -> {p}')

    print(f'\n{len(c["poses"])} pose(s) em {a.saida}/')
    print(f'\nNo workflow WaifuSurvivors_AnimateSD15:')
    print(f'  no  9 : escolha a pasta "{os.path.basename(a.saida)}" no dropdown')
    print(f'  no 10 : indexes = {",".join(map(str, c["indices"]))}')
    print(f'  no 15 : batch_size = {c["frames"]}')
    print(f'\nO AnimateDiff interpola os frames entre as poses.')


if __name__ == '__main__':
    main()
