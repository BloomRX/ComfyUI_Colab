#!/usr/bin/env bash
# Clona o Character Select SAA e aplica as configuracoes do WAIFU SURVIVORS.
#
# Roda no SEU PC (nao no Colab). Windows: use Git Bash ou WSL.
#
#   bash scripts/instalar_saa.sh [pasta-destino]
#
# Reexecutar e seguro: se ja existir, atualiza em vez de clonar.

set -euo pipefail

REPO="https://github.com/mirabarukaso/character_select_stand_alone_app.git"
DEST="${1:-$HOME/character_select_saa}"
AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=============================================================="
echo "  Character Select SAA — instalacao com config do projeto"
echo "=============================================================="
echo "  destino: $DEST"
echo

for cmd in git node npm; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERRO: '$cmd' nao encontrado."
    [ "$cmd" = "node" ] && echo "  Instale o Node.js: https://nodejs.org (LTS)"
    [ "$cmd" = "git" ] && echo "  Instale o Git: https://git-scm.com"
    exit 1
  fi
done
echo "  node $(node --version)  |  npm $(npm --version)"
echo

# ---------------------------------------------------------------- clone
if [ -d "$DEST/.git" ]; then
  echo "-> ja existe, atualizando..."
  git -C "$DEST" fetch --quiet
  git -C "$DEST" pull --quiet
else
  echo "-> clonando..."
  git clone --quiet "$REPO" "$DEST"
fi

# ------------------------------------------------------------ settings
echo "-> aplicando settings do projeto"
mkdir -p "$DEST/settings"

if [ -f "$DEST/settings/settings.json" ]; then
  BK="$DEST/settings/settings.json.bak.$(date +%s)"
  cp "$DEST/settings/settings.json" "$BK"
  echo "   (settings anterior salvo em $(basename "$BK"))"
fi

# remove as chaves _comentario (JSON com comentario quebra alguns parsers)
node -e "
const fs = require('fs');
const src = JSON.parse(fs.readFileSync('$AQUI/saa/settings.json', 'utf8'));
delete src._comentario;
const dst = '$DEST/settings/settings.json';
let base = {};
if (fs.existsSync(dst)) {
  try { base = JSON.parse(fs.readFileSync(dst, 'utf8')); } catch (e) {}
}
// preserva o que o usuario ja tinha (favoritos, loras) e sobrepoe o nosso
const out = Object.assign({}, base, src);
if (base.fav_characters && base.fav_characters.length) {
  out.fav_characters = base.fav_characters;   // nunca perder favoritos
}
fs.writeFileSync(dst, JSON.stringify(out, null, 2));
console.log('   settings.json escrito (' + Object.keys(out).length + ' chaves)');
"

# ---------------------------------------------------------------- deps
echo "-> npm install (pode demorar alguns minutos)"
( cd "$DEST" && npm install --silent )

# --------------------------------------------------------------- pronto
cat <<EOF

==============================================================
  PRONTO
==============================================================

  1. No Colab, na Celula 6, marque  TUNEL_TCP = True  e rode.
     O log vai imprimir algo como:

        API Address = 0.tcp.sa.ngrok.io:14523

  2. Inicie o app:

        cd "$DEST"
        npm start

  3. No SAA:  Settings -> API Interface = ComfyUI
              API Address = (cole o endereco do passo 1, SEM http://)

  O endereco MUDA a cada sessao do Colab. So o campo API Address
  precisa ser reajustado; o resto das configuracoes fica salvo.

  Modelo ja configurado: waiIllustriousSDXL_v170.safetensors
  Negative do projeto ja aplicado.

  Exige o custom node ComfyUI_Mira no ComfyUI (ja no nosso registry:
  selecione qualquer workflow na Celula 4 que o use, ou instale pelo
  Manager).

==============================================================
EOF
