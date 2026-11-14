# spec/ — o contrato do sistema

Especificação independente de ferramenta. `impl/` traduz isto para OpenSCAD, Python e Fusion 360.

Segue a forma do [GitHub Spec Kit](https://github.com/github/spec-kit) — `constitution → spec → plan → tasks → contracts` com **Constitution Check** como portão — adaptada de feature de software para **peça de CAD**. O Spec Kit usa `specs/###-feature/` com user story e critério Gherkin; geometria não cabe nesse molde, então a unidade aqui é a **peça**, não a feature.

## Estrutura

```
constitution.md        as premissas — governa toda peça (sem números: eles vivem no contrato)
params.md              cotas do sistema — tabelas GERADAS do contrato (`make spec-docs`)
rules.md               Lei do Grid, interfaces, junções
assembly.md            como peças se juntam: os NOMES (vocabulário público ↔ OpenSCAD), tabela de portas, regras ASM-###, a IR e as variantes
parts/
  <peça>/              peça convertida
    spec.md            intenção, REQ-###, critérios de aceite
    contracts.toml     a interface em números — FONTE ÚNICA
    plan.md            como cada implementação realiza, e onde não
    tasks.md           status por implementação
    checklist.md       Constitution Check
  <peça>.md            peça ainda em arquivo único
```

Variante persistida (HUB, PLATE) **não** ganha pasta — mora dentro do `spec.md` da peça que ela configura. Só peça ganha pasta.

## Por que `contracts.toml` existe

Antes dele as fórmulas de derivação estavam escritas à mão em **quatro lugares independentes**: as tabelas da spec, o cabeçalho de cada `.scad`, as `@property` de `params.py` e o bloco `awk` do `variables.mk`.

E divergiram. A spec dizia que `pin_len` era derivado e valia `1.6mm`, listando isso como assert crítico. As quatro implementações declaravam `2.0` e **repudiavam a fórmula por escrito**. Ficou assim por tempo indeterminado porque não havia nada capaz de acusar.

`contracts.toml` é a fonte única, e `make spec-check` confere as cópias contra ela.

TOML e não YAML porque `tomllib` é stdlib desde 3.11 — o core roda dentro do Fusion, onde instalar dependência é hostil. E aceita comentário, que JSON não aceita: contrato sem comentário perde o *porquê*.

## Comandos

```bash
make spec-check              # confere contrato vs implementações
make spec-check PART=brick   # uma peça só
make spec-docs               # regenera as tabelas de params.md a partir do contrato
make spec-status             # quais peças estão convertidas
```

`spec-check` faz cinco checagens: auto-consistência do contrato (fórmula bate com o `value`), core Python, echos do OpenSCAD, `make vars` e se as tabelas de `params.md` estão em dia com o contrato. Falha aponta **qual** cópia divergiu e de quanto.

Divergência vinda do `.env` local é **informada, não reprovada** — `.env` é config da máquina, e reprovar tornaria o check inútil justamente para quem está calibrando.

## Converter uma peça

1. `mkdir spec/parts/<peça>` e mover o `.md` atual para `spec/parts/<peça>/spec.md`
2. Extrair todo número para `contracts.toml`, cada derivado com `formula` **e** `value`
3. `make spec-check PART=<peça>` — vai apontar o que a implementação faz diferente
4. Decidir, caso a caso, se o errado é o contrato ou a implementação — e corrigir
5. `plan.md` (como cada impl realiza, e as lacunas), `tasks.md`, `checklist.md`
6. Reescrever `spec.md` no formato: `## Requisitos` com `REQ-###` em linguagem MUST, `## Critérios de aceite` com `AC-###` separando o que é verificado por máquina do que é manual

O passo 4 é o que dá valor: é onde a divergência acumulada aparece.

Se a implementação estiver certa e a spec errada, a correção é **emenda da constituição** — ver a seção Governança lá.

## Estado

| Peça | Formato |
| --- | --- |
| BRICK | pasta spec-driven ✅ |
| PIN · NODE · DOCK · WHEEL | arquivo único, ainda não convertidas |

Regras de montagem (como as peças se juntam): [`assembly.md`](assembly.md).
