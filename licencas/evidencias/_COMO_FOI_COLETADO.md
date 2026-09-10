# Evidências de licença

Cada `.json` aqui é a resposta **crua** da API oficial na data da coleta.
Não é interpretação minha: é o que o servidor devolveu.

- HuggingFace: `https://huggingface.co/api/models/<repo>`
- GitHub:      `https://api.github.com/repos/<owner>/<repo>`

O campo que importa é `license` / `cardData.license` / `tags` (`license:*`).

## Por que guardar isto

A Onoma AI alterou o TOS do Illustrious v0.1 **retroativamente** em 2025.
Licença pode mudar depois de você já ter baixado e usado. Estes arquivos
registram o estado na data em que o modelo entrou no projeto.

## Como atualizar

    python3 scripts/coletar_licencas.py

Roda de novo e sobrescreve, mantendo a data no campo `_coletado_em`.
