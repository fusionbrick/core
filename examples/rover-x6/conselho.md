# Rover X6 — ata do conselho

Conselho de montagem (`.claude/skills/fusionbrick-assembly/reference/council.md`) sobre a versão com suspensão rocker-bogie. Ordem: Maker → Engenheiro → Designer. Números de `fb_assemble.py check / stats / physics`; massas dos componentes declaradas (`mass`), plástico a 55% sólido — ordem de grandeza, não balança.

## Votos (antes)

| Perfil | Voto | O quê | Evidência |
| --- | --- | --- | --- |
| Maker | VETO | 16 peças não entram com um movimento só | ASM-012: bloco da base em −x e −y; postes entre dois quadros (±z); lateral direita entre blocos e camada de baixo |
| Maker | VETO | rover de 6 rodas sem motor, driver nem fio | nenhum componente de tração |
| Maker | RESSALVA | bateria solta sobre o deck; Pi sem base | sem berço nem laje adaptadora |
| Engenheiro | RESSALVA | tombamento lateral abaixo do de um rover | 38° (alvo ≥ 45°); centro de massa a 103 mm |
| Engenheiro | RESSALVA | base do mastro com braço de alavanca curto | 202 g a 105 mm sobre 4 juntas afastadas 11 mm; cavilha segura pouco contra arrancamento |
| Engenheiro | RESSALVA | componente de LiDAR com medida inexistente | 20×20×12 mm para um sensor de 170 g; um LD06 real tem 38,6×38,6×33,5 mm e 42 g |
| Designer | RESSALVA | rodas pequenas para um rover | Ø72 = 0,20 do comprimento (rover ≈ 0,22–0,30) |
| Designer | RESSALVA | cabeça não lê como rosto | bloco grafite 2×6×2 com lentes de 9 mm |
| Designer | OK | silhueta de rover | corpo erguido, 6 rodas, pernas à vista |

## Conflitos e decisões

- **Roda maior (Designer) × centro de massa baixo (Engenheiro).** Roda maior desce o chão e sobe o centro de massa relativo. Resolvido com **bitola mais larga**: a suspensão saiu 2 células para fora por um **ombro** em cada lado. Ganha estabilidade e postura.
- **Mastro alto (Designer) × momento na base (Engenheiro).** Mastro mantido; a base virou um **pé 4×4** (juntas a 34 mm) e o sensor pesado saiu do topo.
- **LiDAR no mastro (2ª volta, Designer).** Com a medida real, virou uma cartola preta escondendo a cabeça. Foi para o **nariz do deck**: a cabeça volta a ser o ponto focal e o centro de massa desce mais. Custo: o LiDAR perde parte da visão traseira, porque o mastro e os arcos fazem sombra.

## O que mudou

| Perfil | Mudança |
| --- | --- |
| Maker | Ordem de montagem em subconjuntos (`sub = true`): lateral esquerda → blocos → lateral direita → bicos → deck → berço → ombros → suspensões → rodas → quadro inferior → postes → quadro superior → arcos |
| Maker | Lados x dos blocos e emendas das laterais sem encaixe (`flat`); quadros com vigas divididas e emenda lisa (`split = "flat"`) e ordem de fechamento que começa depois da emenda |
| Maker | 6 motores N20, driver de motor, fios pela lateral e pela borda do deck até o driver; berço da bateria **embaixo do corpo** (4 pendurais + bandeja; a bateria sai pela frente); laje adaptadora do Pi; 2 faróis |
| Engenheiro | Ombro + suspensão em y = −3 (bitola 160 → 192 mm); bateria 7 células mais baixa; pé 4×4 do mastro; LiDAR LD06 com medida e massa reais |
| Designer | Rodas Ø88 (0,25 do comprimento); cabeça 3×8×2 laranja com olhos de 14 mm; LiDAR no nariz |

## Depois

| Métrica | Antes | Depois |
| --- | --- | --- |
| ASM-012 (não monta à mão) | 16 | **0** (controle negativo: trocar a ordem traz 10 avisos de volta) |
| Tombamento lateral / longitudinal | 38° / 47° | **50° / 54°** |
| Centro de massa | 103 mm | 82 mm |
| Bitola | 160 mm | 192 mm |
| Base do mastro | 4 juntas a 11 mm, 104 N·mm a 0,5 g | 6 juntas a 34 mm, 13 N·mm |
| Roda / comprimento | 0,20 | 0,25 |
| Motores / driver / berço | 0 / 0 / não | 6 / 1 / sim |
| Peças estruturais / impressas | 87 / 177 | 98 / 196 |
| Resolução | 24,7 peças/100 mm | 27,8 |
| Pinos livres · maior peça | 0 · 192 mm | 0 · 192 mm |

## Ressalvas que ficam

- **Suspensão é visual.** O rocker-bogie é de peças fixas e não articula. Articular pede um pino de giro de verdade, que o catálogo ainda não tem.
- **Eixo × motor.** As rodas giram num eixo impresso; os motores N20 são volume reservado. Ligar motor e roda pede um cubo adaptador (DOCK, fora da IR).
- **Pi** apoia numa laje lisa: a furação dele não cai no grid de 8 mm.
- **Massa** é estimativa: confira na balança com as peças impressas.
