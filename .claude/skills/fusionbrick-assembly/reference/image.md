# A partir de imagem

A imagem só muda como se chega à primeira ocupação. Depois o fluxo é o do texto: IR → check → stats → render → **comparar com a imagem** → ajustar.

## Escolher a rota

| A imagem é… | Rota |
| --- | --- |
| foto ou render de objeto mecânico, kit técnico, protótipo | **A · Descrever** |
| croqui com vista lateral, frontal ou de topo, desenho técnico | **B · Projetar** |
| forma orgânica (figura, carroceria curva) | **C · Reconstruir** — só com modelo imagem→3D disponível; senão, A |

## Escala

Imagem não traz medida. Em ordem de preferência:

1. o usuário disse uma dimensão;
2. objeto de medida conhecida na foto (Arduino Uno 68,6 × 53,4 · Pi 4 85 × 56 · pilha 9V 48,5 × 26,5 · AA Ø14,5 · motor 130 Ø20 · roda de kit comum Ø43–Ø88);
3. **escala pela resolução**: escolha o tamanho em que a forma cabe em 15–40 peças estruturais por 100 mm (`quality.md`). Em pedido de "alta qualidade", escale **para cima** — o `buggy-vt2` ficou 1,8× a foto.

Diga sempre qual escala assumiu e por quê.

## A · Descrever

1. **Inventário**: liste as partes visíveis e a função de cada uma (chassi, laterais, gaiola, teto, rodas, para-choques, eletrônica, luzes, fios).
2. **Proporções**: meça na foto, em pixels, as razões que definem a silhueta: comprimento : largura : altura; Ø roda : comprimento; altura da gaiola : altura do corpo; posição dos eixos ao longo do comprimento; balanço dianteiro e traseiro.
3. **Tabela "na imagem → em FusionBrick"** — antes de qualquer IR:

   | Na imagem | Medida (proporção) | Em FusionBrick | Células |
   | --- | --- | --- | --- |
   | lateral perfurada laranja | 1,0 × 0,25 | vigas em 5 camadas, `rounded="y"` | 34 × 1 × 5 |
   | coluna A inclinada | ~37° | `strut` 9-12-15 | Δ (12, 0, −9) |
   | rodas balão | Ø = 0,37 × comprimento | `wheel` balloon, 5 raios Y | diameter 14, width 5 |
   | bateria no deck | — | `component` 9V | 48,5 × 26,5 × 17,5 mm |

4. **Ângulos**: cada inclinação da foto vira o terno pitagórico mais próximo (37°/53° → 3-4-5; 23° → 5-12-13; 28° → 8-15-17). Cada canto arredondado vira `curve` (`radius` pelo raio aparente). Diga quais ângulos mudaram.
5. Siga o fluxo; o critério do passo "olhar" é a **mesma tabela de proporções**, medida agora no render.

## B · Projetar (visual hull)

1. Para cada vista, desenhe a silhueta numa grade de células (`#` cheio, `.` vazio), com a escala definida.
2. A célula (x,y,z) está cheia se está cheia na lateral (x,z) **e** no topo (x,y) **e** na frontal (y,z). Com uma vista só, extruda na largura pedida.
3. Agrupe em blocos: blocos maiores primeiro, alternando a direção do bloco longo a cada camada para que as emendas se cruzem (alvenaria) — rigidez de graça.
4. Faces: a peça de cima leva `studs = "bottom"`; o resto `auto`.
5. Esvazie interiores: troque blocos cheios por paredes de 1 célula ou por quadros de vigas.
6. Suba a resolução (`quality.md` §3) antes de entregar.

## C · Reconstruir

Imagem → malha (TRELLIS, Hunyuan3D) → escalar → voxelizar no passo de 8 mm → passo 3 da rota B. Exige GPU ou API externa; não existe neste repositório.

## Fechar o laço com o usuário

- Depois do primeiro render, mostre **lado a lado** a referência e a vista de mesmo ângulo, com as 3–4 razões medidas nas duas.
- Se o usuário quiser conferir por outro caminho, extraia um **prompt de imagem** da montagem (estilo, peças, cores, rodas, componentes, ângulo de câmera) para ele gerar e comparar. Diferença apontada por ele vira ajuste de proporção, não de peça.
- "Não é bem isso" quase sempre é contagem ou proporção (ex.: "3 rodas" = 3 **de cada lado**). Repita o entendimento em uma frase antes de remontar.
