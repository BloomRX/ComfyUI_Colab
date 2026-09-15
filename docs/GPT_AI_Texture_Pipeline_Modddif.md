# Pipeline Local de IA 3D para a Lia
## Alternativa ao Modddif com ComfyUI + Blender

Este documento descreve como reproduzir localmente, para o projeto **Lia / Project AIRI**, as principais ideias do serviço **Modddif**, evitando dependência permanente de SaaS, APIs pagas e uploads de assets para terceiros.

A proposta principal é usar:

- **Blender** para malha, UV, câmeras, projeção, bake e automação 3D;
- **ComfyUI** como motor local de IA para geração de textura, referência visual, img2img e inpainting;
- modelos locais de IA selecionados com atenção às respectivas licenças;
- o **VRM final da Lia** como artefato de produção, sem necessidade de distribuir o stack de IA junto com o produto final.

---

# 1. O que o Modddif faz

O Modddif funciona principalmente como um **editor 3D assistido por IA**.

Entre suas funções estão:

- geração de malha a partir de imagem;
- importação de formatos 3D;
- geração de textura por múltiplas câmeras;
- projeção de imagens sobre uma malha existente;
- correção localizada via inpainting;
- simplificação de malha;
- geração e bake de mapas;
- edição visual baseada em referências.

A parte mais interessante para o projeto da Lia é o sistema de **texturização multiview**.

Em termos conceituais, o processo é:

```text
Mesh 3D
  ↓
Várias câmeras
  ↓
IA gera uma imagem para cada ângulo
  ↓
Cada imagem é projetada sobre a malha
  ↓
As vistas são combinadas
  ↓
Bake em UV
  ↓
Correções localizadas por inpainting
```

Esse conceito pode ser reproduzido localmente.

---

# 2. Por que isso é útil para a Lia

Para uma personagem VRM como a Lia, reconstruir todo o modelo com IA do zero não é necessariamente a melhor estratégia.

O avatar precisa manter:

- rig humano estável;
- blendshapes;
- piscadas;
- movimento ocular;
- expressões faciais;
- cabelo separado;
- roupas separadas;
- topologia previsível;
- compatibilidade com VRM;
- compatibilidade com o Project AIRI.

Por isso, a estratégia recomendada é:

```text
Geometria controlada
+
IA para aparência e textura
```

Em vez de:

```text
Imagem
↓
IA gera um personagem 3D inteiro
↓
Tentativa de transformar o resultado em VRM
```

A geometria pode continuar vindo do VRoid/Blender, enquanto a IA ajuda a aproximar o visual final das referências oficiais da Lia.

---

# 3. Arquitetura recomendada

## 3.1 Responsabilidade de cada ferramenta

| Etapa | Ferramenta |
|---|---|
| Mesh / topologia | VRoid Studio / Blender |
| UV | Blender |
| Rig / blendshapes | VRoid / Blender / VRM pipeline |
| Câmeras multiview | Blender |
| Depth / Normal / Mask | Blender |
| IA de imagem | ComfyUI |
| Referência visual | Imagens oficiais da Lia |
| Img2img | ComfyUI |
| Inpainting | ComfyUI |
| Projeção de textura | Blender / Python |
| Mistura das vistas | Blender |
| Bake final | Blender |
| Exportação final | VRM / GLB |
| Automação | Python / Blender Add-on |

O ComfyUI atua como **motor de IA**.

O Blender continua sendo responsável pela lógica tridimensional.

---

# 4. Fluxo de texturização multiview

Um pipeline próprio pode usar câmeras automáticas ao redor da personagem.

Exemplo:

```text
FRONT
FRONT_LEFT
LEFT
BACK_LEFT
BACK
BACK_RIGHT
RIGHT
FRONT_RIGHT
```

Para cada câmera, o Blender pode gerar:

```text
color.png
depth.png
normal.png
mask.png
uv_position.png
current_texture.png
```

Essas informações são enviadas ao ComfyUI junto das referências oficiais da Lia.

O ComfyUI gera, por exemplo:

```text
lia_front_albedo.png
lia_front_left_albedo.png
lia_left_albedo.png
lia_back_left_albedo.png
lia_back_albedo.png
lia_back_right_albedo.png
lia_right_albedo.png
lia_front_right_albedo.png
```

Depois o Blender:

1. calcula quais faces estão visíveis por câmera;
2. descarta regiões ocultas ou em ângulos ruins;
3. projeta cada imagem apenas sobre as faces adequadas;
4. mistura áreas sobrepostas;
5. executa o bake para o UV final.

Resultado:

```text
lia_body_albedo_4k.png
```

---

# 5. Arquitetura visual

```text
                ┌────────────────────┐
                │ Referências da Lia │
                └─────────┬──────────┘
                          │
                          ▼
┌────────────┐     ┌──────────────┐
│ VRoid/VRM  │ ──► │   Blender    │
└────────────┘     │              │
                   │ mesh / UV    │
                   │ camera       │
                   │ depth        │
                   │ normals      │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │   ComfyUI    │
                   │              │
                   │ img2img      │
                   │ reference    │
                   │ inpainting   │
                   └──────┬───────┘
                          │
                          ▼
                ┌──────────────────┐
                │ Multiview images │
                └─────────┬────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │   Blender    │
                   │ projection   │
                   │ blending     │
                   │ UV baking    │
                   └──────┬───────┘
                          │
                          ▼
                 ┌────────────────┐
                 │ Lia Albedo 4K  │
                 │ Normal         │
                 │ Roughness      │
                 │ Masks          │
                 └───────┬────────┘
                         │
                         ▼
                      Lia.vrm
```

---

# 6. Possível ferramenta própria

Uma ferramenta interna poderia ser criada com o nome provisório:

```text
Lia AI Texture Pipeline
```

Dentro do Blender, por exemplo, poderia existir um painel:

```text
LIA AI TOOLS

[ Generate Multiview Cameras ]
[ Render Guidance Passes ]
[ Send to ComfyUI ]
[ Generate AI Views ]
[ Project Textures ]
[ Bake Final Albedo ]
[ Validate Texture ]
```

Isso permitiria reproduzir as partes úteis do Modddif sem precisar copiar o produto inteiro.

---

# 7. Estrutura de diretórios sugerida

```text
/tools/
    lia_texture_ai/

/comfy/
    workflows/
        lia_multiview.json
        lia_face_inpaint.json
        lia_clothes.json
        lia_hair.json

/blender/
    addons/
        lia_ai_tools/

    scripts/
        render_views.py
        export_guidance.py
        call_comfyui.py
        project_texture.py
        blend_views.py
        bake_albedo.py
        validate_uv.py

/models/
    README_LICENSES.md

/output/
    textures/
    previews/
    temp/
```

---

# 8. Preservação da identidade visual da Lia

Como o pipeline seria específico para a personagem, ele pode impor regras que um sistema genérico não conhece.

Exemplos:

- cor dos olhos deve permanecer dentro de uma faixa definida;
- cabelo deve manter rosa/magenta;
- franja deve preservar a direção de referência;
- pele não deve receber sombras pintadas permanentemente;
- blazer deve manter regiões pretas;
- detalhes violetas/magenta devem seguir a identidade visual;
- rosto deve permanecer consistente entre as vistas;
- determinadas regiões podem ser bloqueadas contra alteração por IA.

Também é possível salvar junto de cada geração:

```text
seed
prompt
negative prompt
checkpoint
LoRA
ControlNet
IP-Adapter
workflow version
reference image hash
date
```

Isso aumenta a reprodutibilidade.

---

# 9. Albedo versus imagem renderizada

Para um avatar 3D, é importante evitar que a IA pinte iluminação diretamente na textura.

A textura principal deve se aproximar de um **albedo limpo**.

Evitar:

- sombras fortes pintadas;
- highlight especular permanente;
- reflexos;
- luz lateral;
- rim light;
- ambient occlusion exagerado;
- gradientes que pertencem à iluminação da cena.

Preferir:

```text
Base Color / Albedo
+
Normal
+
Roughness
+
outros mapas quando necessários
```

Assim a personagem reage corretamente à iluminação real do Project AIRI.

---

# 10. Inpainting localizado

Um dos recursos mais úteis é poder corrigir somente uma região.

Fluxo:

```text
Render da câmera atual
↓
Usuário seleciona região problemática
↓
Máscara
↓
ComfyUI inpaint
↓
Nova imagem
↓
Reprojeção apenas da área modificada
```

Exemplos de regiões:

- olho esquerdo;
- boca;
- franja;
- manga;
- gola;
- blazer;
- saia;
- costura;
- parte traseira do cabelo.

Isso evita regenerar toda a textura.

---

# 11. Geração 3D do zero com IA

Também é possível usar modelos image-to-3D para gerar uma personagem ou base 3D.

Exemplo conceitual:

```text
reference_lia.png
↓
Image-to-3D
↓
lia_generated.glb
↓
Blender
↓
Retopology
↓
UV
↓
Rig
↓
Blendshapes
↓
VRM
```

Modelos como TRELLIS e outras soluções atuais podem ser usados como ferramentas auxiliares.

Porém, para uma personagem que precisa funcionar como avatar animado, o resultado gerado normalmente ainda exige bastante trabalho.

Problemas comuns:

- topologia inadequada para animação;
- cabelo fundido ao corpo;
- roupas fundidas;
- mãos ruins;
- pés ruins;
- geometria interna;
- assimetria;
- UV ruim;
- rig inexistente;
- edge flow facial inadequado;
- ausência de blendshapes;
- materiais inconsistentes.

Por isso, para a Lia, image-to-3D deve ser tratado principalmente como:

- referência;
- prototipagem;
- concept mesh;
- comparação;
- geração de acessórios;
- geração de roupas ou objetos auxiliares.

Não necessariamente como fonte principal do VRM final.

---

# 12. Licenças

O objetivo não deve ser literalmente:

> não usar nenhuma licença externa

Isso é praticamente impossível.

Blender, Python, PyTorch, ComfyUI, bibliotecas e drivers possuem licenças.

O objetivo mais realista e útil é:

> não depender de SaaS proprietário, API paga, upload externo ou modelo cuja licença comprometa o uso desejado dos assets finais.

---

# 13. Software versus output

É importante separar:

```text
licença do software
```

de:

```text
licença do modelo de IA
```

e de:

```text
direitos sobre o output
```

Essas três coisas não são necessariamente iguais.

Por exemplo, usar software GPL no pipeline de produção não significa automaticamente que uma textura exportada precise ser distribuída sob GPL.

O ponto que merece mais atenção normalmente são os **pesos dos modelos de IA** e suas licenças específicas.

---

# 14. Auditoria de modelos

Antes de colocar qualquer modelo no pipeline oficial, criar uma tabela como:

| Modelo | Função | Licença | Comercial | Redistribuição | Output | Observações |
|---|---|---|---|---|---|---|
| Modelo A | img2img | ... | Sim/Não | ... | ... | ... |
| Modelo B | ControlNet | ... | Sim/Não | ... | ... | ... |
| Modelo C | image-to-3D | ... | Sim/Não | ... | ... | ... |

E manter:

```text
/models/README_LICENSES.md
```

Esse arquivo deve registrar:

- nome do modelo;
- URL oficial;
- versão;
- hash;
- licença;
- data da auditoria;
- restrições relevantes;
- finalidade dentro do pipeline.

---

# 15. Separação entre produção e produto final

Uma estratégia especialmente interessante é usar toda a stack de IA apenas durante o desenvolvimento.

```text
DESENVOLVIMENTO

Blender
+
ComfyUI
+
modelos de IA
+
scripts
        ↓
      Lia.vrm


PRODUTO FINAL

Project AIRI
+
Lia.vrm
```

Assim, o usuário final não precisa receber:

- ComfyUI;
- checkpoints;
- ControlNets;
- modelos image-to-3D;
- Python;
- Blender;
- workflows de geração.

Ele recebe apenas o asset final necessário para o aplicativo.

---

# 16. Pipeline recomendado para a Lia

A estratégia principal recomendada é:

```text
VRoid / Blender
↓
Geometria e rig estáveis
↓
UV controlado
↓
Render multiview de guias
↓
ComfyUI
↓
Geração de albedo por referência
↓
Projeção multiview
↓
Inpainting localizado
↓
Bake final
↓
Validação
↓
VRM
↓
Project AIRI
```

---

# 17. O que vale a pena reproduzir do Modddif

Não é necessário recriar todo o produto.

As partes de maior valor para a Lia são:

## Prioridade alta

- geração multiview;
- projection painting;
- inpainting localizado;
- geração guiada por referências;
- albedo sem iluminação;
- bake automático;
- máscaras por região;
- controle de consistência facial.

## Prioridade média

- geração de normal map;
- geração de roughness;
- simplificação automática;
- interface visual de histórico;
- presets.

## Prioridade baixa

- geração genérica de qualquer tipo de objeto;
- marketplace;
- galeria pública;
- sistema de créditos;
- recursos SaaS.

---

# 18. Vantagens da solução local

## Privacidade

As referências da Lia podem permanecer no computador local.

## Reprodutibilidade

Workflows, seeds e modelos podem ser versionados.

## Controle

É possível decidir exatamente quais regiões a IA pode alterar.

## Independência

O pipeline não depende da continuidade de um serviço SaaS.

## Automação

Blender e ComfyUI possuem APIs e sistemas adequados para automação.

## Integração

O pipeline pode ser integrado ao repositório existente da Lia.

---

# 19. Riscos técnicos

Os principais desafios são:

- consistência entre vistas;
- seams entre projeções;
- diferenças de cor;
- deformações faciais;
- geração inconsistente de detalhes pequenos;
- oclusão;
- cabelo transparente;
- regiões nunca visíveis pelas câmeras;
- relação entre textura gerada e UV real;
- geração de sombras indesejadas;
- dificuldade em preservar detalhes muito específicos.

Esses problemas são resolvíveis, mas exigem lógica adicional além do workflow de IA.

---

# 20. Estratégia de blend entre câmeras

A qualidade do resultado depende bastante de como as vistas são combinadas.

Uma abordagem pode atribuir peso baseado no ângulo entre:

```text
normal da superfície
```

e

```text
direção da câmera
```

Superfícies vistas diretamente recebem peso alto.

Superfícies vistas de lado recebem peso baixo.

Exemplo conceitual:

```text
weight = max(dot(surface_normal, camera_direction), 0)
```

Outros fatores podem entrar no peso:

- distância da câmera;
- profundidade;
- oclusão;
- borda da máscara;
- confiança da IA;
- região anatômica;
- proximidade de seams UV.

---

# 21. Regiões separadas

Para a Lia, pode ser melhor dividir a geração por categoria.

Exemplo:

```text
FACE
HAIR
SKIN
BLAZER
SHIRT
SKIRT
LEGS
SHOES
ACCESSORIES
```

Cada região pode ter:

- prompt próprio;
- modelo próprio;
- referências próprias;
- intensidade própria;
- máscara própria.

Isso reduz alterações acidentais.

---

# 22. Possível roadmap

## Fase 1 — Prova de conceito

- carregar VRM no Blender;
- gerar 8 câmeras;
- renderizar depth/normal/mask;
- enviar uma vista ao ComfyUI;
- projetar uma textura gerada de volta na malha.

## Fase 2 — Multiview

- automatizar as 8 câmeras;
- gerar todas as vistas;
- implementar cálculo de visibilidade;
- implementar blend por ângulo.

## Fase 3 — Bake

- bake para UV final;
- correção de seams;
- exportação automática.

## Fase 4 — Inpainting

- seleção de região;
- render da câmera;
- geração por máscara;
- atualização parcial.

## Fase 5 — Lia-specific

- referências oficiais;
- prompts específicos;
- máscaras por roupa;
- preservação de olhos;
- preservação de cabelo;
- controle de identidade.

## Fase 6 — Ferramenta

- painel dentro do Blender;
- integração com ComfyUI API;
- logs;
- cache;
- versionamento;
- presets.

---

# 23. Recomendação final

Para o Project AIRI e a Lia, a melhor abordagem é:

> não reconstruir o Modddif inteiro.

Em vez disso, implementar localmente a parte que mais agrega valor:

> **texturização multiview por IA sobre uma malha VRM já controlada.**

A arquitetura recomendada é:

```text
VRoid / Blender
+
ComfyUI
+
referências oficiais
+
projeção multiview
+
bake
+
VRM
```

Dessa forma, mantemos:

- controle da geometria;
- rig estável;
- blendshapes;
- compatibilidade com AIRI;
- privacidade dos assets;
- independência de SaaS;
- possibilidade de auditoria de licença;
- capacidade de reproduzir resultados.

O resultado final continua sendo um asset VRM tradicional e pode ser usado pelo AIRI sem carregar toda a infraestrutura de IA durante a execução.

---

# 24. Próximo passo sugerido

O próximo passo técnico recomendado é criar um protótipo mínimo:

```text
Lia VRM
↓
Blender
↓
8 câmeras
↓
Depth + Normal + Mask
↓
ComfyUI
↓
1 conjunto multiview
↓
Projection
↓
Bake 4K
↓
VRM atualizado
```

Depois desse teste será possível medir:

- fidelidade às referências;
- qualidade dos seams;
- estabilidade facial;
- tempo de geração;
- VRAM necessária;
- modelos mais adequados;
- complexidade real da automação.

Esse protótipo será suficiente para decidir se o pipeline deve evoluir para uma ferramenta completa integrada ao projeto Lia.
