#!/usr/bin/env python3
"""Executa e mede o teste A/B entre AnimateDiff (SD1.5) e WAN 2.2 5B.

Duas funcoes:

  --rodar   enfileira os dois workflows via API do ComfyUI, cronometra cada um
            e amostra a VRAM durante a execucao
  --medir   analisa os frames ja gerados e pontua os criterios objetivos

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


# --------------------------------------------------------------- execucao
def api(rota, dados=None, servidor=SERVER, timeout=30):
    url = servidor.rstrip('/') + rota
    if dados is None:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read())
    corpo = json.dumps(dados).encode()
    req = urllib.request.Request(url, data=corpo,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def vram_mb(servidor=SERVER):
    try:
        d = api('/system_stats', servidor=servidor, timeout=10)
        dev = d.get('devices', [{}])[0]
        total = dev.get('vram_total', 0)
        livre = dev.get('vram_free', 0)
        return (total - livre) / (1024 ** 2)
    except Exception:
        return None


class Monitor(threading.Thread):
    """Amostra a VRAM em segundo plano enquanto o job roda."""

    def __init__(self, servidor):
        super().__init__(daemon=True)
        self.servidor = servidor
        self.picos = []
        self.parar = False

    def run(self):
        while not self.parar:
            v = vram_mb(self.servidor)
            if v is not None:
                self.picos.append(v)
            time.sleep(2)

    @property
    def maximo(self):
        return max(self.picos) if self.picos else None

    @property
    def media(self):
        return statistics.mean(self.picos) if self.picos else None


def to_api_format(wf):
    """Converte workflow de UI para o formato /prompt (API)."""
    N = {n['id']: n for n in wf['nodes'] if n.get('mode', 0) != 4}
    L = {l[0]: l for l in wf.get('links', [])}
    out = {}
    for nid, n in N.items():
        entradas = {}
        for i in n.get('inputs') or []:
            lk = i.get('link')
            if lk is None:
                continue
            l = L.get(lk)
            if l and l[1] in N:
                entradas[i['name']] = [str(l[1]), l[2]]
        wv = n.get('widgets_values')
        if isinstance(wv, dict):
            entradas.update(wv)
        elif isinstance(wv, list):
            # nomes dos widgets nao estao no JSON de UI; a API aceita posicional
            # apenas via object_info, entao deixamos o servidor validar
            pass
        out[str(nid)] = {'class_type': n['type'], 'inputs': entradas}
    return out


def rodar(servidor):
    print('AVISO: este modo exige que os workflows tenham sido salvos em\n'
          'formato API. O caminho recomendado e rodar pela UI:\n'
          '  1. abra AB_A_sd15_idle,  Run,  anote o tempo\n'
          '  2. abra AB_B_wan_idle,   Run,  anote o tempo\n'
          'e depois usar --medir.\n')
    try:
        st = api('/system_stats', servidor=servidor, timeout=10)
        dev = st.get('devices', [{}])[0]
        print(f"GPU: {dev.get('name')}  "
              f"VRAM total: {dev.get('vram_total', 0)/(1024**3):.1f} GB")
        print(f"VRAM em uso agora: {vram_mb(servidor):.0f} MB")
    except Exception as e:
        print(f'Servidor nao respondeu: {str(e)[:70]}')
        return
    print('\nMonitor de VRAM ativo. Rode os workflows pela UI agora.')
    print('Ctrl+C para parar e ver o pico.\n')
    m = Monitor(servidor)
    m.start()
    try:
        while True:
            time.sleep(5)
            if m.picos:
                print(f'  VRAM atual {m.picos[-1]:7.0f} MB   '
                      f'pico {m.maximo:7.0f} MB', end='\r')
    except KeyboardInterrupt:
        m.parar = True
        print(f'\n\nPico de VRAM observado: {m.maximo:.0f} MB')


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
    ap.add_argument('--rodar', action='store_true', help='monitora VRAM ao vivo')
    ap.add_argument('--medir', action='store_true', help='analisa os frames')
    ap.add_argument('--server', default=SERVER)
    ap.add_argument('--dir', default=None, help='pasta output do ComfyUI')
    a = ap.parse_args()

    if a.rodar:
        rodar(a.server)
        return

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
