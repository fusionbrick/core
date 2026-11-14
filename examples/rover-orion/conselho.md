# Rover Orion — ata do conselho

Conselho `fusionbrick-council`, câmara de produto. Ficha `review`: **APTO, 15/15 portões**. Números de `review`, `stats`, `physics` e `fb_collide`; massa é estimativa (plástico a 55% sólido, componentes com massa declarada).

**A ideia em uma frase:** um rover de exploração de seis rodas cuja cabine aberta sobe numa linha só, do nariz ao mastro.

## Primeira volta

| Perfil | Voto | O quê | Evidência |
| --- | --- | --- | --- |
| Maker | OK | monta em subconjuntos, um movimento por peça | ASM-012 = 0; 23 passos, todos com nota |
| Maker | RESSALVA | haste da antena presa por uma junta só | ASM-004: 1 junção — virou haste de 2 células |
| Engenheiro | OK | fica em pé com folga | tombamento lateral 49°, centro de massa a 85 mm |
| Designer | **VETO** | o LiDAR no teto era o ponto mais alto e disputava o olhar com a cabeça | vista lateral: topo do LiDAR acima da cabeça — "uma ideia" e "presença" com nota 0 |
| Designer | RESSALVA | letreiro lido de trás para a frente na vista principal | render |

**Conflito:** LiDAR alto (Engenheiro: melhor visão) × cabeça como ponto focal (Designer). Saída: LiDAR no **nariz**, à frente do arco baixo — vê o caminho, baixa o centro de massa, e a cabeça volta a ser o topo. O braço saiu do centro para o ombro direito do nariz, como nos rovers reais. Custo: o LiDAR perde a visão traseira (a cabine faz sombra) e o centro de massa sai 2 mm do eixo.

## Segunda volta — notas (0 · 1 · 2)

| # | Princípio | Nota | Quem | Por quê |
| --- | --- | --- | --- | --- |
| 1 | Uma ideia | 2 | Designer | a linha nariz → mastro lê na lateral; cada grupo serve a ela (os trilhos são o único elemento só de história: bagageiro) |
| 2 | Menos, porém melhor | 1 | Engenheiro / Designer | 4,7 cópias por STL e 3 cores; mas 14 nós para 7 diagonais, cada inclinação com nó próprio |
| 3 | Funciona de verdade | 1 | Engenheiro | 50° de tombamento e base do mastro com 4 juntas a 34 mm; a suspensão não articula e o motor não liga na roda |
| 4 | Onde ninguém vê | 2 | Maker | 0 pinos sem uso, zero colisão em 249 pares, fios pela borda do deck, berço da bateria por baixo |
| 5 | Encaixe e acabamento | 2 | Engenheiro | 0 erros, simétrico (centro de massa a 2 mm do eixo), emendas das laterais desencontradas |
| 6 | Montar | 2 | Maker | subconjuntos por lado, ASM-012 = 0, cavilhas em 40% das peças impressas |
| 7 | Possível | 1 | Maker | maior peça 160 mm; mas os blocos 16×12×2 e as 4 placas do deck são impressões longas |
| 8 | Presença | 2 | Designer | corpo erguido, pernas à vista, cabeça laranja como rosto no ponto mais alto, roda = 0,27 do comprimento |

**Média 1,63 · nenhum veto aberto · nenhuma nota 0 · 2 em "Uma ideia" e em "Presença" → passa a barra.**

## Antes → depois (dentro desta revisão)

| Medida | 1ª volta | Entregue |
| --- | --- | --- |
| Ponto mais alto | LiDAR | cabeça |
| Portões da ficha | 13/15 (colisão não rodada, haste com 1 junta) | 15/15 |
| Peças estruturais / impressas | 93 / 179 | 92 / 174 |
| Centro de massa | 85 mm | 82 mm |

## Contra o rover anterior (rover-x6)

| Medida | rover-x6 | rover-orion |
| --- | --- | --- |
| Peças impressas | 196 | 174 |
| Cavilhas | 86 (44%) | 70 (40%) |
| Cores da estrutura | 4 (reprova no portão novo) | 3 |
| Linhas do `gen.py` | 262 | 199 |
| Cabine | dois quadros empilhados (caixa) | três arcos e duas longarinas (perfil inclinado) |

## Limites declarados

- **Suspensão visual:** o rocker-bogie é de peças fixas; articular pede um pino de giro que o catálogo não tem.
- **Motor × roda:** os N20 são volume reservado; ligar ao eixo pede um cubo adaptador (DOCK, fora da IR).
- **Pi** apoia numa laje lisa: a furação dele não cai no grid de 8 mm.
- **LiDAR** no nariz não vê para trás.
- **Massa** estimada em 1,3 kg: confira na balança.
