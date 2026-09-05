#!/usr/bin/env python3
"""Verifica automaticamente as regras que ja foram violadas antes.

Cada checagem aqui existe porque o erro correspondente JA ACONTECEU e custou
tempo. Documentar nao bastou (o bug das abas foi documentado 4x e a hipotese
errada se repetiu nas 4). Isto executa a memoria em vez de confiar na leitura.

Uso:
    python scripts/checar_regras.py
    python scripts/checar_regras.py --online   # tambem valida URLs no HF
"""
import argparse
import glob
import json
import os
import re
import sys
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
falhas = []
avisos = []


def erro(regra, msg):
    falhas.append(f'[{regra}] {msg}')


def aviso(regra, msg):
    avisos.append(f'[{regra}] {msg}')


def carregar_workflows():
    out = {}
    for f in sorted(glob.glob(os.path.join(RAIZ, 'Workflows', '*.json'))):
        try:
            out[os.path.basename(f)] = json.load(open(f, encoding='utf-8'))
        except Exception as e:
            erro('JSON', f'{os.path.basename(f)}: invalido: {str(e)[:60]}')
    return out


def r_uuid(wfs):
    """Regra: id de workflow tem de ser UUID e unico."""
    U = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
                   r'[0-9a-f]{4}-[0-9a-f]{12}$')
    vistos = {}
    for nome, d in wfs.items():
        if 'nodes' not in d:
            continue
        i = str(d.get('id', ''))
        if not U.match(i):
            erro('v21', f'{nome}: id nao e UUID ({i!r})')
        if i in vistos:
            erro('v21', f'{nome}: id duplicado com {vistos[i]}')
        vistos[i] = nome


def r_checkpoint(wfs):
    """Regra: um unico checkpoint em todo o repo (nada de v160 esquecido)."""
    achados = set()
    alvos = [os.path.join(RAIZ, 'config', 'node_registry.json'),
             os.path.join(RAIZ, 'scripts', 'roster.example.json')]
    alvos += glob.glob(os.path.join(RAIZ, 'Workflows', '*.json'))
    for f in alvos:
        if not os.path.exists(f):
            continue
        achados |= set(re.findall(r'waiIllustriousSDXL_v\d+', open(f, encoding='utf-8').read()))
    if len(achados) > 1:
        erro('v30', f'versoes de checkpoint misturadas: {sorted(achados)}')


def r_links(wfs):
    """Regra: links coerentes (orfaos quebram o carregamento)."""
    for nome, d in wfs.items():
        if 'nodes' not in d:
            continue
        N = {n['id']: n for n in d['nodes'] if 'id' in n}
        L = {}
        for l in d.get('links', []):
            if not isinstance(l, list) or len(l) < 6:
                erro('v37', f'{nome}: link malformado {l}')
                continue
            L[l[0]] = l
            if l[1] not in N or l[3] not in N:
                erro('v37', f'{nome}: link {l[0]} referencia no inexistente')
        for n in d['nodes']:
            for i in n.get('inputs') or []:
                lk = i.get('link')
                if lk is not None and lk not in L:
                    erro('v37', f"{nome}: no {n.get('id')}.{i['name']} usa link {lk} inexistente")


def r_deprecados(wfs):
    """Regra: nao usar node_id deprecado (some da UI)."""
    conhecidos = {
        'ADE_AnimateDiffUniformContextOptions': 'ADE_LoopedUniformContextOptions',
        'ADE_AnimateDiffLoaderWithContext': 'ADE_LoadAnimateDiffModel + ADE_UseEvolvedSampling',
    }
    for nome, d in wfs.items():
        for n in d.get('nodes', []):
            t = n.get('type')
            if t in conhecidos:
                erro('v37', f'{nome}: no {n.get("id")} usa {t} (DEPRECADO) '
                            f'-> use {conhecidos[t]}')


def r_registry(wfs):
    """Regra: todo tipo de no tem de ter fonte conhecida no registry."""
    p = os.path.join(RAIZ, 'config', 'node_registry.json')
    r = json.load(open(p, encoding='utf-8'))
    cm, nat = r['class_map'], set(r.get('native_ignore', []))
    for nome, d in wfs.items():
        for n in d.get('nodes', []):
            t = n.get('type')
            if t in ('Note', 'MarkdownNote', 'Reroute', 'PrimitiveNode'):
                continue
            # subgrafo: o 'type' e o UUID da definicao, nao um no de pack
            if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-', str(t)):
                continue
            if t not in cm and t not in nat:
                aviso('registry', f'{nome}: no "{t}" sem fonte no class_map')


def r_urls(online=False):
    """Regra v33: nunca escrever URL de modelo de memoria."""
    p = os.path.join(RAIZ, 'config', 'node_registry.json')
    r = json.load(open(p, encoding='utf-8'))
    vistas = {}
    for wf, ms in (r.get('workflow_models') or {}).items():
        for m in ms:
            url, arq = m.get('url', ''), m.get('file', '')
            if not url:
                continue
            vistas.setdefault(url, (arq, wf))
            mm = re.match(r'https://huggingface\.co/([^/]+/[^/]+)/resolve/', url)
            if url.startswith('https://huggingface.co/') and not mm:
                erro('v33', f'{arq}: URL do HF fora do padrao /resolve/: {url}')
    if not online:
        return
    for url, (arq, wf) in vistas.items():
        mm = re.match(r'https://huggingface\.co/([^/]+/[^/]+)/resolve/([^/]+)/(.+)$', url)
        if not mm:
            continue
        repo, rev, caminho = mm.groups()
        pasta = '/'.join(caminho.split('/')[:-1])
        alvo = caminho.split('/')[-1]
        api = f'https://huggingface.co/api/models/{repo}/tree/{rev}'
        if pasta:
            api += '/' + pasta
        try:
            req = urllib.request.Request(api, headers={'User-Agent': 'Mozilla/5.0'})
            dados = json.loads(urllib.request.urlopen(req, timeout=60).read())
            nomes = {x['path'].split('/')[-1] for x in dados if x.get('type') == 'file'}
            if alvo not in nomes:
                erro('v33', f'{arq}: 404 -> {alvo} nao existe em {repo}')
        except Exception as e:
            aviso('v33', f'nao consegui verificar {repo}: {str(e)[:50]}')


def r_notebook():
    """Regras do notebook que ja quebraram antes."""
    p = os.path.join(RAIZ, 'notebooks', 'ComfyUI_Colab_Limpo.ipynb')
    nb = json.load(open(p, encoding='utf-8'))
    fonte = {i: ''.join(c['source']) for i, c in enumerate(nb['cells'])
             if c['cell_type'] == 'code'}
    todo = '\n'.join(fonte.values())

    # v34: chaves de settings que NAO existem
    inventadas = ['Comfy.Workflow.Persist', 'Comfy.Workflow.PersistOpenWorkflows']
    for k in inventadas:
        if k in todo:
            erro('v34', f'notebook usa chave de setting inexistente: {k}')

    # v24: nunca decidir copia por "se nao existe"
    if re.search(r'if\s+not\s+os\.path\.exists\([^)]*\)\s*:\s*\n\s*\w*\.?copytree', todo):
        erro('v24', 'copia condicional entre Drive e local (use dirs_exist_ok=True)')

    # cada celula de codigo tem de compilar
    for i, s in fonte.items():
        chk = '\n'.join('pass' if re.match(r'^\s*[!%]', l) else l
                        for l in s.split('\n'))
        try:
            compile(chk, f'cell{i}', 'exec')
        except SyntaxError as e:
            erro('sintaxe', f'celula {i} nao compila: {e.msg} (linha {e.lineno})')

    # v40: o patch do 404 atras do proxy tem de estar presente
    if 'zz_proxy_userdata' not in todo:
        erro('v40', 'falta o patch /userdata/{file:.+/.+} (404 dos workflows '
                    'atras do proxy do Colab)')

    # NB_VERSION tem de existir e ser unico
    vs = re.findall(r"NB_VERSION\s*=\s*'([^']+)'", todo)
    if not vs:
        erro('versao', 'NB_VERSION nao encontrado')
    elif len(set(vs)) > 1:
        erro('versao', f'NB_VERSION conflitante: {set(vs)}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--online', action='store_true',
                    help='tambem verifica se as URLs do HF existem')
    a = ap.parse_args()

    wfs = carregar_workflows()
    print(f'{len(wfs)} workflow(s) carregado(s)\n')
    r_uuid(wfs)
    r_checkpoint(wfs)
    r_links(wfs)
    r_deprecados(wfs)
    r_registry(wfs)
    r_urls(a.online)
    r_notebook()

    for x in avisos:
        print('AVISO  ' + x)
    if avisos:
        print()
    for x in falhas:
        print('FALHA  ' + x)
    print()
    if falhas:
        print(f'{len(falhas)} regra(s) violada(s). Consulte o indice do DRIVE_LAYOUT.md.')
        sys.exit(1)
    print('Todas as regras conhecidas passaram.')
    print('Lembrete: a checagem SEMANTICA dos nos exige o servidor ligado:')
    print('  python scripts/validar_workflows.py --server http://127.0.0.1:8188')


if __name__ == '__main__':
    main()
