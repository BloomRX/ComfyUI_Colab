#!/usr/bin/env python3
"""Valida os workflows do repo contra as definicoes REAIS dos nos.

Motivacao: workflows gerados por script podem ficar sintaticamente perfeitos
(JSON valido, links coerentes) e mesmo assim nao abrir na UI, porque um no tem
entrada com nome errado, widget faltando, ou usa um node_id deprecado.

Duas fontes de verdade, em ordem de preferencia:

1. `--server http://127.0.0.1:8188`  -> usa /object_info, a mesma coisa que a
   UI usa. E a checagem definitiva.
2. sem servidor -> valida so o que da para conferir offline (estrutura, links,
   ids, duplicatas) e avisa que a parte semantica ficou de fora.

Uso:
    python scripts/validar_workflows.py
    python scripts/validar_workflows.py --server http://127.0.0.1:8188
    python scripts/validar_workflows.py --only WaifuSurvivors
"""
import argparse
import glob
import json
import os
import re
import sys
import urllib.request

UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


def carregar_object_info(server):
    url = server.rstrip('/') + '/object_info'
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'  ! nao consegui falar com {url}: {str(e)[:70]}')
        return None


def checar_estrutura(d):
    """Erros que quebram o carregamento independente dos nos instalados."""
    problemas = []
    if 'nodes' not in d:
        return ['sem chave "nodes" (formato API nao abre na aba)']
    if not UUID_RE.match(str(d.get('id', ''))):
        problemas.append(f'id nao e UUID: {d.get("id")!r}')

    nodes = d['nodes']
    ids = [n.get('id') for n in nodes]
    if len(ids) != len(set(ids)):
        vistos, dup = set(), set()
        for i in ids:
            if i in vistos:
                dup.add(i)
            vistos.add(i)
        problemas.append(f'ids de no duplicados: {sorted(dup)}')

    N = {n['id']: n for n in nodes if 'id' in n}
    links = {}
    for l in d.get('links', []):
        if not isinstance(l, list) or len(l) < 6:
            problemas.append(f'link malformado: {l}')
            continue
        if l[0] in links:
            problemas.append(f'link id duplicado: {l[0]}')
        links[l[0]] = l
        if l[1] not in N:
            problemas.append(f'link {l[0]} sai de no inexistente {l[1]}')
        if l[3] not in N:
            problemas.append(f'link {l[0]} entra em no inexistente {l[3]}')

    for n in nodes:
        for i in n.get('inputs') or []:
            lk = i.get('link')
            if lk is None:
                continue
            l = links.get(lk)
            if l is None:
                problemas.append(f"no {n.get('id')}.{i['name']}: link {lk} nao existe")
            elif l[3] != n.get('id'):
                problemas.append(
                    f"no {n.get('id')}.{i['name']}: link {lk} aponta para {l[3]}")
        for si, o in enumerate(n.get('outputs') or []):
            for lk in o.get('links') or []:
                l = links.get(lk)
                if l is None:
                    problemas.append(f"no {n.get('id')} saida {si}: link {lk} nao existe")
                elif l[1] != n.get('id') or l[2] != si:
                    problemas.append(
                        f"no {n.get('id')} saida {si}: link {lk} incoerente")
    return problemas


def checar_contra_servidor(d, oinfo):
    """A checagem que importa: os nos existem e as entradas batem?"""
    problemas = []
    for n in d.get('nodes', []):
        t = n.get('type')
        if t in ('Note', 'MarkdownNote', 'Reroute', 'PrimitiveNode'):
            continue
        spec = oinfo.get(t)
        if spec is None:
            problemas.append(f"no {n.get('id')}: tipo '{t}' NAO EXISTE no servidor")
            continue
        if spec.get('deprecated'):
            problemas.append(f"no {n.get('id')}: '{t}' esta DEPRECADO "
                             f"(some da busca; pode nao renderizar)")
        it = spec.get('input', {}) or {}
        obrig = it.get('required', {}) or {}
        opc = it.get('optional', {}) or {}
        validos = set(obrig) | set(opc) | {'control_after_generate'}

        ligados = {i['name'] for i in (n.get('inputs') or [])}
        for nome in ligados:
            if nome not in validos:
                problemas.append(
                    f"no {n.get('id')} ({t}): entrada '{nome}' nao existe. "
                    f"validas: {sorted(validos)}")

        # widgets: entradas required que NAO sao ligacao viram widget, na ordem
        tipos_link = set()
        for nome, cfg in list(obrig.items()) + list(opc.items()):
            tp = cfg[0] if isinstance(cfg, (list, tuple)) and cfg else None
            if isinstance(tp, str) and tp.isupper() and tp not in ('INT', 'FLOAT',
                                                                   'STRING', 'BOOLEAN'):
                tipos_link.add(nome)
        esperados = [nome for nome in obrig if nome not in tipos_link]
        tem = len(n.get('widgets_values') or [])
        # control_after_generate acrescenta 1 widget depois de cada seed/noise_seed
        extra = sum(1 for nome in esperados if nome in ('seed', 'noise_seed'))
        if tem and tem not in (len(esperados), len(esperados) + extra):
            problemas.append(
                f"no {n.get('id')} ({t}): {tem} widget(s) para "
                f"{len(esperados)} esperado(s) {esperados}")
    return problemas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--server', default=None,
                    help='ex: http://127.0.0.1:8188 (usa /object_info)')
    ap.add_argument('--only', default='', help='filtra pelo nome do arquivo')
    ap.add_argument('--dir', default='Workflows')
    a = ap.parse_args()

    oinfo = None
    if a.server:
        print(f'Consultando {a.server}/object_info ...')
        oinfo = carregar_object_info(a.server)
        if oinfo:
            print(f'  {len(oinfo)} tipos de no conhecidos pelo servidor\n')
    else:
        print('Sem --server: checagem SEMANTICA pulada '
              '(rode com o ComfyUI ligado para a checagem completa)\n')

    arquivos = sorted(glob.glob(os.path.join(a.dir, '*.json')))
    if a.only:
        arquivos = [f for f in arquivos if a.only.lower() in os.path.basename(f).lower()]

    total_ruins = 0
    for f in arquivos:
        nome = os.path.basename(f)
        try:
            d = json.load(open(f, encoding='utf-8'))
        except Exception as e:
            print(f'[ERRO ] {nome}: JSON invalido: {str(e)[:60]}')
            total_ruins += 1
            continue
        probs = checar_estrutura(d)
        if oinfo and 'nodes' in d:
            probs += checar_contra_servidor(d, oinfo)
        if probs:
            total_ruins += 1
            print(f'[FALHA] {nome}')
            for p in probs[:12]:
                print(f'         - {p}')
            if len(probs) > 12:
                print(f'         ... e mais {len(probs)-12}')
        else:
            print(f'[  ok  ] {nome}')

    print()
    if total_ruins:
        print(f'{total_ruins} workflow(s) com problema.')
        sys.exit(1)
    print('Todos os workflows passaram.')


if __name__ == '__main__':
    main()
