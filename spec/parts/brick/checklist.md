# BRICK — Constitution Check

Uma linha por premissa de [`../../constitution.md`](../../constitution.md). Premissa violada exige **justificativa escrita** aqui — não silêncio.

Reavaliar quando a peça ou a constituição mudarem.

| # | Premissa | BRICK | Como se sabe |
| --- | --- | :---: | --- |
| 1 | O grid é sagrado | ✅ | Toda posição sai de `skin + grid/2 + i·grid`. Nenhuma junção move furo. |
| 2 | O grid é DERIVADO | ✅ | `grid` só existe como fórmula em `contracts.toml`; não há parâmetro `grid` em implementação nenhuma. `make spec-check` [1] confere. |
| 3 | O furo é sempre passante | ✅ | REQ-002. `bores()` no core e `bores()` no `.scad` atravessam a peça inteira; não existe furo cego. |
| 4 | Circuito elétrico passa por padrão | ✅ | Furo `Ø hole_d` passante em todo eixo `bored`. `passage_max` no contrato protege a seção livre: o macho para na tangência, sem comer a passagem transversal. |
| 5 | Encaixe simultâneo nas 6 faces | ⚠️ | REQ-006 satisfeito por construção (`pin_len ≤ pin_len_max`, checado), mas **AC-012 não tem automação** — foi medido à mão por interseção de sólidos. Ver ressalva abaixo. |
| 6 | Compatibilidade é permanente | ✅ | O BRICK absorveu 5 peças antigas sem quebrar interface: cada uma virou uma configuração, não um formato novo. |
| 7 | Press-fit primeiro | ⚠️ | Geometria de press-fit está lá (colar Ø4.6 em rebaixo Ø4.8), mas `tolerance` **nunca foi calibrada contra impressão real** — AC-013. Ver ressalva abaixo. |
| 8 | Spec-first | ✅ | Esta pasta. `contracts.toml` é fonte única e `make spec-check` reprova divergência. |

---

## Ressalvas

### § 5 — encaixe simultâneo sem automação

O teto `pin_len ≤ pin_len_max` é conferido a cada `make spec-check`, e a geometria foi validada por dilatação (minkowski) contra o sólido real: em `pin_len = 2.0` a folga entre machos perpendiculares é ≥ `gap`.

Mas essa medição foi **manual e pontual**. Nada a repete. Se alguém mudar `collar_depth` ou `lead_in`, o `spec-check` continua passando e a colisão real não é detectada.

`tasks.md` **T040** cobre isso.

### § 7 — press-fit não verificado fisicamente

O modelo produz `0.2mm` de folga diametral em toda superfície — **folga, não interferência**. O aperto depende inteiramente da impressora entregar acima do nominal (superextrusão, pé de elefante, encolhimento do furo).

Em impressora bem calibrada o par pode sair **frouxo**. Existe um conjunto de STLs com `tolerance = 0` em `renders/stl-tol0/` para medir isso, ainda não impresso.

`tasks.md` **T041** cobre isso.

---

## Nota sobre § 5 e a emenda

A premissa 5 estava **errada** até esta conversão: derivava `pin_len` por `wall + collar_w + tolerance/2 − gap` = `1.6mm`, descontando `gap` no eixo quando a aproximação entre machos perpendiculares é diagonal. Cobrava √2 a mais.

As quatro implementações já usavam `2.0` e repudiavam a fórmula por escrito no comentário. A spec ficou errada por tempo indeterminado sem que nada acusasse — porque não havia nada que pudesse acusar.

Foi o caso que motivou `contracts.toml` e `make spec-check`.
