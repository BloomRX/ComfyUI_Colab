#!/usr/bin/env python3
"""Coleta e arquiva as licencas dos modelos e ferramentas do projeto.

Salva a resposta CRUA das APIs oficiais em licencas/evidencias/, com a data
da coleta. Serve como registro do estado da licenca no momento em que o
modelo foi usado — a Onoma AI ja alterou o TOS do Illustrious v0.1
retroativamente, entao o print datado protege.

Uso:
    python3 scripts/coletar_licencas.py
    python3 scripts/coletar_licencas.py --resumo    (so mostra, nao grava)

No Colab:
    !python3 /content/ComfyUI_Colab/scripts/coletar_licencas.py
"""
import argparse
import datetime
import json
import os
import sys
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(RAIZ, 'licencas', 'evidencias')

# repo -> arquivos que usamos dele. Fonte de verdade do que precisa ser
# auditado; acrescente aqui ao adotar um modelo novo.
HF = {
    'Comfy-Org/Wan_2.2_ComfyUI_Repackaged': [
        'wan2.2_ti2v_5B_fp16.safetensors',
        'umt5_xxl_fp8_e4m3fn_scaled.safetensors',
        'wan2.2_vae.safetensors',
    ],
    'h94/IP-Adapter': [
        'ip-adapter-plus_sdxl_vit-h.safetensors',
        'ip-adapter-plus_sd15.safetensors',
        'CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors',
    ],
    'xinsir/controlnet-union-sdxl-1.0': [
        'controlnet-union-sdxl-1.0.safetensors',
    ],
    'hotshotco/Hotshot-XL': [
        'hsxl_temporal_layers.f16.safetensors',
    ],
    'guoyww/animatediff': [
        'v3_sd15_mm.ckpt',
        'v3_sd15_sparsectrl_rgb.ckpt',
    ],
    'frankjoshua/toonyou_beta6': [
        'toonyou_beta6.safetensors',
    ],
    # --- projeto Lia (imagem -> 3D) ---
    'Comfy-Org/TRELLIS.2': [
        'trellis_2_int8_convrot.safetensors',
    ],
    'Comfy-Org/Pixal3D': [
        'dino_v3_L_naf_fp32.safetensors',
        'trellis_2_shape_vae_bf16.safetensors',
        'trellis_2_texture_vae_bf16.safetensors',
    ],
    'Comfy-Org/BiRefNet': [
        'birefnet.safetensors',
    ],
    # bases dos repackages acima (a licenca que vale e a do ORIGINAL)
    'microsoft/TRELLIS.2-4B': [],
    'ZhengPeng7/BiRefNet': [],
    'facebook/dinov3-vitl16-pretrain-lvd1689m': [],
}

GH = [
    'comfyanonymous/ComfyUI',
    'Comfy-Org/ComfyUI-Manager',
    'cubiq/ComfyUI_IPAdapter_plus',
    'Kosinkadink/ComfyUI-VideoHelperSuite',
    'Kosinkadink/ComfyUI-AnimateDiff-Evolved',
    'Kosinkadink/ComfyUI-Advanced-ControlNet',
    'john-mnz/ComfyUI-Inspyrenet-Rembg',
    'mirabarukaso/ComfyUI_Mira',
    'mirabarukaso/character_select_stand_alone_app',
]

# Modelos que nao tem API publica — registro manual.
MANUAIS = {
    'waiIllustriousSDXL_v170.safetensors': {
        'origem': 'Civitai — WAI-NSFW-illustrious-SDXL v17.0',
        'url': 'https://civitai.com/models/827184',
        'licenca': 'Fair AI Public License 1.0-SD',
        'licenca_url': 'https://freedevproject.org/faipl-1.0-sd/',
        'base': 'Illustrious XL (Onoma AI) -> SDXL',
        'saida_comercial': True,
        'clausula_chave': (
            'Output: The output of this software is not covered by this '
            'license, and no contributor claims any rights to it.'),
        'restricoes': [
            'copyleft ao redistribuir o MODELO ou derivados (LoRA, merge)',
            'proibido oferecer o modelo como servico em rede sem dar o fonte',
            'Prohibited Uses: nada ilegal, nada envolvendo menores, etc.',
        ],
        'alertas': [
            'download MANUAL: nao existe no HuggingFace, Civitai exige login',
            'treinado em tags do Danbooru: pode reproduzir personagens com '
            'copyright — nao usar nomes de personagens existentes',
        ],
        'nota': (
            'A Onoma AI alterou o TOS do Illustrious v0.1 retroativamente em '
            '2025. Guarde print da pagina do Civitai na data do download.'),
    },
}


def buscar(url, timeout=45):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def licenca_hf(d):
    lic = (d.get('cardData') or {}).get('license')
    if lic:
        return lic
    for t in d.get('tags', []):
        if t.startswith('license:'):
            return t.split(':', 1)[1]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resumo', action='store_true',
                    help='so imprime, nao grava as evidencias')
    a = ap.parse_args()

    hoje = datetime.date.today().isoformat()
    if not a.resumo:
        os.makedirs(DEST, exist_ok=True)

    print(f'Coleta de licencas — {hoje}\n')
    linhas = []
    falhas = []

    print('HUGGINGFACE')
    for repo, arquivos in HF.items():
        try:
            d = buscar(f'https://huggingface.co/api/models/{repo}')
        except Exception as e:
            falhas.append((repo, str(e)[:60]))
            print(f'  !! {repo:44} {str(e)[:40]}')
            continue
        lic = licenca_hf(d) or '(nao declarada)'
        gated = d.get('gated') or False
        print(f'  {lic:22} {repo}')
        for f in arquivos:
            linhas.append((f, lic, repo, 'huggingface'))
        if not a.resumo:
            reg = {
                '_coletado_em': hoje,
                '_fonte': f'https://huggingface.co/api/models/{repo}',
                '_arquivos_que_usamos': arquivos,
                'licenca': lic,
                'gated': gated,
                'lastModified': d.get('lastModified'),
                'sha': d.get('sha'),
                'resposta_crua': d,
            }
            nome = 'hf_' + repo.replace('/', '_') + '.json'
            with open(os.path.join(DEST, nome), 'w', encoding='utf-8') as fh:
                json.dump(reg, fh, indent=2, ensure_ascii=False)

    print('\nGITHUB')
    for repo in GH:
        try:
            d = buscar(f'https://api.github.com/repos/{repo}')
        except Exception as e:
            falhas.append((repo, str(e)[:60]))
            print(f'  !! {repo:44} {str(e)[:40]}')
            continue
        l = d.get('license') or {}
        lic = l.get('spdx_id') or l.get('name') or '(nao declarada)'
        print(f'  {lic:22} {repo}')
        linhas.append((repo.split('/')[-1], lic, repo, 'github'))
        if not a.resumo:
            reg = {
                '_coletado_em': hoje,
                '_fonte': f'https://api.github.com/repos/{repo}',
                'licenca': lic,
                'licenca_url': l.get('url'),
                'pushed_at': d.get('pushed_at'),
                'resposta_crua': {k: d.get(k) for k in
                                  ('full_name', 'license', 'html_url',
                                   'description', 'pushed_at', 'archived')},
            }
            nome = 'gh_' + repo.replace('/', '_') + '.json'
            with open(os.path.join(DEST, nome), 'w', encoding='utf-8') as fh:
                json.dump(reg, fh, indent=2, ensure_ascii=False)

    print('\nREGISTRO MANUAL (sem API publica)')
    for arq, info in MANUAIS.items():
        print(f'  {info["licenca"]:22} {arq}')
        linhas.append((arq, info['licenca'], info['origem'], 'manual'))
        if not a.resumo:
            reg = dict(info)
            reg['_coletado_em'] = hoje
            reg['_arquivo'] = arq
            nome = 'manual_' + arq.replace('.', '_') + '.json'
            with open(os.path.join(DEST, nome), 'w', encoding='utf-8') as fh:
                json.dump(reg, fh, indent=2, ensure_ascii=False)

    # indice consolidado, facil de ler
    if not a.resumo:
        idx = os.path.join(RAIZ, 'licencas', 'INDICE.md')
        with open(idx, 'w', encoding='utf-8') as fh:
            fh.write('# Índice de licenças (gerado automaticamente)\n\n')
            fh.write(f'Coletado em **{hoje}** por `scripts/coletar_licencas.py`.\n')
            fh.write('Não edite à mão — rode o script de novo.\n\n')
            fh.write('| arquivo / pacote | licença | origem |\n')
            fh.write('|---|---|---|\n')
            for arq, lic, origem, _ in sorted(linhas):
                fh.write(f'| `{arq}` | {lic} | {origem} |\n')
            if falhas:
                fh.write('\n## Não foi possível verificar\n\n')
                for r, e in falhas:
                    fh.write(f'- `{r}`: {e}\n')
        print(f'\nÍndice: {idx}')
        print(f'Evidências: {DEST}/  ({len(os.listdir(DEST))} arquivos)')

    if falhas:
        print(f'\n{len(falhas)} repo(s) nao verificados — rode de novo depois.')
        return 1
    print('\nTudo verificado.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
