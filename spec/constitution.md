# Design System — Premissas

Princípios que governam o FusionBrick. Toda peça nova, mudança de parâmetro ou nova implementação deve respeitar todos eles. Se uma proposta viola qualquer premissa, a proposta muda — não a premissa.

---

## 1. O grid é sagrado

O passo do grid nunca muda por causa de uma junção.

- Peças auxiliares conectam furos existentes **sem inserir espaçamento**
- Material fora do volume do grid é permitido (espessura de PLATE, pele de adaptador) — ver [Lei do Grid](rules.md)
- Teste canônico: em qualquer montagem, uma célula deve entrar em qualquer posição interior e alinhar com todos os furos vizinhos

## 2. O grid é DERIVADO, não declarado

> **grid = furo + 2 × (parede + colar)**

A célula não é um número escolhido: é o que sobra quando você decide o **furo** (a interface mecânica) e a **parede** (o limite de impressão). O sistema é orientado a grid, mas a unidade do grid é *resultado* do encaixe.

Isso inverte o modelo antigo, em que furo e posição eram declarados e a parede era resíduo — um valor que nunca aparecia em lugar nenhum e que produzia lascas de 0.6mm nas quinas.

**Consequência:** só dois dos três (`furo`, `parede`, `grid`) podem ser primitivos. Declarar os três reintroduz divergência.

## 3. O furo é sempre passante

Todo furo atravessa a peça inteira ao longo do seu eixo. Não existe furo cego.

- O que limita o encaixe é **até onde o pino vai**, nunca a profundidade do furo
- Furos de eixos diferentes **se cruzam** no centro de cada célula — isso é projeto, não defeito
- Daí sai a passagem de fio da premissa 4, de graça

## 4. Circuito elétrico passa por padrão

Toda peça e todo conector nascem com passagem para fio/jumper — fechar é opt-in, nunca default.

- Furos passantes em todos os eixos (premissa 3)
- Conector é vazado sempre que o diâmetro permitir: `canal = pino − 2 × parede`, existindo se ≥ `2.5mm` (jumper Dupont)
- Quando a seção não comporta canal, a peça não pode **bloquear** as passagens existentes
- Fechar o canal é escolha do usuário, nunca da spec

## 5. Encaixe simultâneo em todas as faces

> **Uma célula 1×1 toda fêmea deve aceitar pino em todas as 6 faces ao mesmo tempo, sem um invadir o espaço do outro.**

Os três furos passantes se cruzam no centro, então um macho tem de parar antes de encostar no perpendicular. O limite é geométrico:

```text
pin_len ≤ grid/2 − pin_d/2        teto de colisão      = 2.1mm
pin_len ≤ grid/2 − hole_d/2       tangência da passagem = 2.0mm
```

O primeiro é onde duas hastes se **tocam**. O segundo é onde o macho começa a comer a **seção livre do furo transversal** — a passagem de fio, que a premissa 4 garante. O sistema adota **2.0mm**: o maior macho que não obstrui passagem nenhuma.

**`pin_len` é DECLARADO, não derivado.** A versão anterior desta premissa derivava por `parede + colar + tolerância/2 − gap` = `1.6mm`. Está errado: essa conta desconta `gap` no **eixo**, mas dois machos perpendiculares se afastam na **diagonal**. Cobrava √2 a mais — gastava `0.5mm` de engate para comprar `0.71mm` de folga.

Medido por dilatação (minkowski) contra o sólido real: em `pin_len = 2.0` a folga entre machos perpendiculares é **≥ 0.5mm**, que é o `gap` do sistema. O valor certo por 25% de engate a mais.

O diâmetro do furo **não desaparece** da conta, ao contrário do que esta premissa afirmava: ele entra pelos dois tetos acima. O que continua verdadeiro é que **engate se compra com parede**, porque o grid cresce com ela:

| Parede | Grid | Teto de colisão | Teto de passagem |
| --- | --- | --- | --- |
| **1.6** | **8.0** | **2.10mm** | **2.00mm** |
| 2.4 | 9.6 | 2.90mm | 2.80mm |
| 3.2 | 11.2 | 3.70mm | 3.60mm |

Com `collar_depth = 1mm`, **o colar é a superfície de encaixe** (Ø4.6 em Ø4.8) e a haste avança `1.0mm` além dele. Quem retém é o colar; a haste alinha e resiste a torção.

## 6. Compatibilidade é permanente

Tudo conecta com tudo, sempre — inclusive com peças impressas antes.

- Parâmetros globais idênticos em todas as peças; divergiu, quebrou
- Peça nova usa as interfaces existentes; interface nova só quando nenhuma resolve — e vira contrato, documentada em `spec/`
- Mudança de interface propaga para todas as peças, specs, implementações e exemplos **de uma vez**
- Nada de pares exclusivos: se A conecta em B, conecta em qualquer peça com a mesma interface

## 7. Press-fit primeiro

- Sem ferramentas, sem parafusos, sem cola (cola é opção do usuário para montagem permanente)
- `tolerância` subtraída sempre do **conector**, nunca da peça receptora — receptoras são nominais
- Ajuste por impressora acontece no conector: peça pequena, reimpressão barata

## 8. Spec-first

- `spec/` é o contrato; `impl/` implementa. Divergência é bug na implementação — ou proposta de mudança que começa pela spec
- Qualquer implementação que respeite a spec produz peças intercompatíveis
- **A implementação deve validar** — parâmetro que viola proporção não gera peça silenciosamente (ver *Validação*)

---

## Parâmetros

Sete primitivos (`hole_d`, `wall`, `collar_w`, `collar_depth`, `tolerance`, `gap`, `pin_len`); todo o resto é derivado. Os valores, as fórmulas e os invariantes **não se repetem aqui**: vivem em [`parts/brick/contracts.toml`](parts/brick/contracts.toml) e aparecem, gerados, em [params.md](params.md).

`collar_w`, `collar_depth`, `tolerance` e `gap` são do **processo de fabricação** (bico, camada, precisão), não do tamanho da peça. Escalá-los junto com o grid produz números quebrados sem ganho.

---

## Configuração das peças

Parâmetros de extensibilidade — não mudam o contrato, escolhem a variante.

## Dimensões

Toda peça compatível aceita **três eixos em células**:

```text
cells_x · cells_y · cells_z
```

Uma PLATE 4×4 é `4×4×1`. Um bloco é `2×2×2`. Não há eixo com unidade diferente — espessura é célula como qualquer outra dimensão.

**Pele** (`skin_*`) acrescenta material **fora** do volume de grid, na escala fina, quando o conteúdo não cabe em múltiplo de célula. Os furos continuam ancorados no grid; só o envelope cresce.

**Comprimento livre** (`len`) é permitido em vigas. Uma diagonal entre dois pontos do grid mede `Δ·√2`, que nunca é múltiplo do passo — e não precisa ser, desde que as duas **pontas** caiam em furo existente.

## Eixos e faces

Duas camadas, e a distinção importa: o **furo pertence ao eixo**, o **acabamento pertence à face**.

Fundir as duas acopla faces opostas — se o furo é passante (premissa 3) e fosse propriedade da face, declarar `hole` numa face abriria a face oposta à revelia dela.

### Eixo — 3 por peça

| Estado | Significado |
| --- | --- |
| `bored` | furo passante ao longo do eixo, atravessando o corpo inteiro |
| `solid` | sem furo nesse eixo |

Numa viga `1×1×10`, o eixo longo `bored` produz um canal de `80mm` de ponta a ponta.

### Face — 6 por peça

| Estado | Significado |
| --- | --- |
| `recess` | fêmea — rebaixo na boca, recebe o colar de um macho |
| `pin` | macho — adicionado **por fora** do corpo |
| `plain` | lisa — o furo sai cru, ou não há furo |

O macho é material **somado** à face, não subtraído. Por isso ele pode existir numa face cujo eixo é `bored`: o pino **tampa** a boca daquele lado. Se o canal precisa sair inteiro, use `recess` ou `plain` nas duas pontas.

### O que isso permite

Uma viga de 10 células com macho numa ponta e fêmea na outra:

```text
cells      = 1 × 1 × 10
axis_z     = bored          canal de 80mm
face_zn    = pin            macho
face_zp    = recess         fêmea
axis_x/y   = solid          laterais sem furo (economiza filamento)
```

### Regras

- `recess` exige o eixo `bored` — rebaixo sem furo atrás não tem função
- `pin` num eixo `bored` tampa aquele lado, a menos que o canal do próprio pino passe do mínimo útil
- Configurável face a face, com presets para os casos comuns. `plain` e `solid` onde não há encaixe economizam filamento e são o comportamento recomendado

### Por que `pin_len` é constante do sistema

A restrição da premissa 5 vale quando existe furo perpendicular por perto. Numa viga de laterais `solid` não existe, e o macho poderia ser mais longo.

**Não pode.** Se o comprimento variasse por peça, um macho longo entraria fundo demais numa célula que espera `pin_len` e colidiria com o pino perpendicular *dela* — quebrando a premissa 6. O comprimento do macho é contrato do sistema, não escolha da peça.

## Variantes por peça

Parâmetros específicos que não violam o contrato:

| Peça | Parâmetro | Faixa |
| --- | --- | --- |
| Curva | `angle` | qualquer ângulo; só ternos pitagóricos devolvem a diagonal ao grid |
| Curva | `inner_r` | raio interno; 0 = compacta |
| Viga | `len` | comprimento livre |
| Conector de face | `spacer` | afastamento entre as duas pontas |
| Adaptador | perfil do dispositivo | cavidade exclusiva, exterior padrão |

## Recurso central — a generalização do "macro"

"Macro" e "micro" são **abstração de leitura**, não entidades do sistema. O que existe é um recurso no **centro de um bloco N×N**, com tamanho livre:

```text
center       = none | hole | pin
center_size  = <diâmetro>
```

O bloco mínimo é **consequência** do tamanho, não escolha. O recurso engole os furos que alcança, por filtro de distância — não há lista fixa a manter.

---

## Validação

A implementação **deve** verificar as proporções. Violação crítica **para a geração**; violação de julgamento **avisa**.

## Críticas — erro, não gera

| Regra | Por quê |
| --- | --- |
| `grid = hole_d + 2·(wall + collar_w)` | definição; se não fecha, os primitivos são incoerentes |
| `pin_len ≤ grid/2 − pin_d/2` (`pin_len_max`) | senão machos perpendiculares colidem (premissa 5) |
| `hole_d · √2 > recess_d` | senão o rebaixo morde a barra da aresta |
| `center_recess/2 + (grid/2)·√2 ≤ dist(centro, furo vizinho)` | **folga de MONTAGEM** — uma peça encaixada no furo vizinho ocupa espaço acima da face. Continuidade de material não basta |
| `recess` exige eixo `bored` | rebaixo sem furo atrás não recebe nada |
| `pin_len` é o valor do sistema, não da peça | macho mais longo colide com o pino perpendicular da peça receptora |

A última só apareceu na impressão: a quina de uma célula encaixada ao lado invadia o furo central. A peça estava geometricamente correta e mesmo assim inutilizável.

## De julgamento — avisa e gera

- parede efetiva abaixo do mínimo declarado
- envelope acima do necessário (desperdício)
- bloco maior que o mínimo para o recurso central
- canal axial abaixo do mínimo útil

## Liberdade do usuário

A implementação final é OpenSCAD e o código é aberto: quem quiser sai da proporção. O papel da spec é **tornar a saída deliberada** — o default protege, o override é explícito.

---

## Notas de aplicação

**Ordem de cálculo.** Declare `hole_d` e `wall`; o `grid` sai. Se você precisa de um grid específico, resolva ao contrário — `hole_d = grid − 2·(wall + collar_w)` — e declare o resultado. A spec não impede; só exige que os primitivos sejam coerentes.

**O engate é raso por construção.** `2.0mm` num pino `Ø3.8` é `0.53 × D`, abaixo do que press-fit costuma pedir. É o preço da premissa 5, e foi decisão consciente em favor da célula compacta. Se a retenção não bastar na prática, o caminho é engordar a **parede**, não o grid.

---

## Governança

Este arquivo é a **constituição** do sistema: as premissas que toda peça deve respeitar. Segue a forma do [GitHub Spec Kit](https://github.com/github/spec-kit), adaptada de feature de software para peça de CAD.

### Cadeia de artefatos

```
constitution.md          as premissas — este arquivo
  parts/<peça>/
    spec.md              intenção, requisitos, critérios de aceite
    contracts.toml       a interface em números — FONTE ÚNICA
    plan.md              como cada implementação realiza
    tasks.md             status por implementação
    checklist.md         Constitution Check
```

### Constitution Check

Toda peça responde, no seu `checklist.md`, uma linha por premissa. Premissa violada exige **justificativa escrita** ali — não silêncio.

### Emenda

Uma premissa muda pela spec, nunca pela implementação. O procedimento:

1. Editar a premissa aqui, com o **porquê** e o que a mediu
2. Ajustar `contracts.toml` das peças afetadas
3. `make spec-check` — tem de apontar as implementações que agora divergem
4. Ajustar as implementações até fechar
5. Propagar para docs e skills

Divergência entre contrato e implementação é **bug**, não escolha. O passo 3 existe para que ela seja visível: antes de `make spec-check` as fórmulas viviam escritas à mão em quatro lugares, e a premissa 5 ficou errada por tempo indeterminado sem que nada acusasse.

Formato e como converter uma peça: [`README.md`](README.md).
