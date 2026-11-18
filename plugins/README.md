# Plugins de CAD

Implementações do padrão FusionBrick dentro de outras ferramentas de CAD. Cada plugin usa a spec (`spec/`) e o core Python (`impl/python/fusionbrick`) deste repositório, então uma mudança na spec quebra o plugin no mesmo PR — e o CI pega.

| Plugin | Ferramenta | Estado | Docs |
| --- | --- | --- | --- |
| [`fusion360/`](fusion360/) | Autodesk Fusion | experimental | [`hack/automations/fusion.md`](../hack/automations/fusion.md) |

## Convenções

- Uma pasta por ferramenta: `plugins/<ferramenta>/`.
- O plugin importa o core de `impl/python/` (desenvolvimento) ou de uma cópia embutida (distribuição); nunca reimplementa regra de encaixe nem número da spec.
- Plugins de terceiros vivem em repositórios próprios. Plugins do FusionBrick Studio (o editor) são outra coisa: usam o SDK em `fusionbrick/plugin-sdk`.
