# Câmara de PRODUTO — Maker, Engenheiro, Designer

Revisa um **objeto montado** (rover, case, suporte) depois do render e **depois da ficha `review` dar APTO**. Ordem Maker → Engenheiro → Designer: do que impede o objeto de existir ao que impede de convencer. Cada perfil dá VETO / RESSALVA / OK por item e nota 0–2 nos princípios que são dele (`padrao.md`).

| Perfil | Princípios que ele nota |
| --- | --- |
| Maker | 6 Montar · 7 Possível · 4 Onde ninguém vê (fios, pinos, parte de baixo) |
| Engenheiro | 3 Funciona de verdade · 5 Encaixe e acabamento · 2 Menos, porém melhor (peças e juntas) |
| Designer / CEO / PO | 1 Uma ideia · 8 Presença · 2 Menos, porém melhor (cores e elementos) |

## Medidas

```bash
python3 hack/scripts/fb_assemble.py review  <toml>   # todos os portões de uma vez
python3 hack/scripts/fb_assemble.py check   <toml>   # ASM-012 = direção de inserção
python3 hack/scripts/fb_assemble.py stats   <toml>   # resolução, cavilhas, pinos livres, mesa
python3 hack/scripts/fb_assemble.py physics <toml>   # massa, centro de massa, tombamento, base de peças altas
```

---

## 1. Maker — imprime, monta e liga

> **Mandato:** dá para imprimir na mesa comum, montar com as mãos numa ordem que existe, e ligar a eletrônica de verdade?

**Veto:** *"mostra a ordem de montagem — cada peça entra com um movimento só?"*

### O que olha

- **ASM-012 zerado.** Cada peça, na ordem dos `groups`, encaixa nas anteriores por **um** eixo e **um** sentido. Peça entre duas já montadas, ou com pinos em dois eixos, não entra. Correção: reordenar, montar subconjunto antes (`sub = true` no grupo) ou deixar `flat` a face que trava o segundo movimento.
- **Impressão:** maior peça ≤ 220 mm; placas ≤ ~130 células (render e impressão); nenhum pino livre (`stats`); peças repetidas saem do mesmo STL.
- **Eletrônica plausível** — o DS não resolve a eletrônica, mas o produto precisa dela:
  - **motor** para cada roda que deveria tracionar (componente com medida real: N20 12×10×34, TT 70×22×18);
  - **driver** de motor e **bateria** com caminho de fio até ele;
  - **bateria removível** sem desmontar a estrutura, e presa (berço ou presilhas);
  - placa (Pi, ESP32) com base de fixação — furação de placa não cai no grid: reserve uma chapa adaptadora e diga que o DOCK fica para depois;
  - fios passando por furos ou ao longo de vigas, não atravessando peças.
- **Peças por junta:** junta que exige cavilha + 2 peças ao mesmo tempo não vai ser usada.

### O que NÃO é dele

Se a estrutura aguenta carga (Engenheiro) e se o produto convence (Designer).

---

## 2. Engenheiro — estrutura, física, material

> **Mandato:** faz sentido como objeto físico? Aguenta o próprio peso, um tranco e o uso, no material real?

**Veto:** *"qual é o caminho da carga, e qual o número que mostra que ele aguenta?"*

### O que olha

- **Estabilidade:** centro de massa e ângulo de tombamento (`physics`). Referência: rover ≥ 45° de lado; abaixo de 35° é veto. Corrige-se baixando massa (bateria embaixo), alargando a bitola ou abaixando o corpo — não com peso extra.
- **Caminho da carga:** do componente pesado até a roda. Cada junta no caminho: pino impresso, cavilha ou nó. Uma cavilha de press-fit aguenta cisalhamento (~400 N em PLA Ø3,8), mas **segura pouco contra arrancamento** (ordem de 10–20 N): base de mastro, braço e suporte em balanço precisam de várias juntas **afastadas** (braço de alavanca), não de duas a 8 mm.
- **Momento em balanço:** massa × altura × aceleração de tranco (0,5 g). Mastro, antena, braço robótico.
- **Rigidez real vs geométrica:** ASM-004 só garante que as juntas não estão numa linha. Suspensão "rocker-bogie" de peças fixas é **visual** — diga.
- **Material e impressão:** pino impresso em pé (eixo Z) quebra na camada sob flexão; prefira cargas de cisalhamento nos pinos. PLA quebra, PETG deforma, ABS encolhe. Peça longa e fina flamba.
- **Folgas de funcionamento:** roda não roça (ASM-002/010), vão livre plausível para o terreno.

### O que NÃO é dele

Se monta à mão (Maker) e se é bonito (Designer).

---

## 3. Designer / CEO / PO — imagem e história

> **Mandato:** em 3 segundos, a imagem conta o que o objeto é e por que alguém quer um?

**Veto:** *"se esta for a única imagem no post de lançamento, ela vende?"*

### O que olha

- **Silhueta e arquétipo:** reconhece-se a categoria (rover = corpo erguido, 6 rodas abertas, suspensão à vista, mastro com "cabeça")? Nada de caixa.
- **Proporção heroica:** rodas com presença (rover ≈ 0,22–0,30 do comprimento), mastro como ponto focal, nada de balanço exagerado na frente ou atrás.
- **Ponto focal e "rosto":** a cabeça de sensores lê como rosto (dois olhos grandes, acento de cor).
- **História:** cada elemento tem papel (o arco protege o compartimento, a antena fala com a base, o braço coleta amostra). Elemento sem papel sai ou ganha um.
- **Cor e acabamento:** 2–3 cores com função; o acento marca o que se move ou é importante (curvas, suspensão, cabeça). Componente flutuando ou mal encostado mata a credibilidade.
- **Apresentação:** a vista principal (`view_angle`) mostra o melhor lado; o explodido mostra o sistema; nome/letreiro visível.

- **O que eu tiraria?** Liste os elementos e a função de cada um na história. Sem função, sai. Menos elementos bem resolvidos vencem mais elementos médios.
- **Uma decisão ousada.** Algo que este produto faz de um jeito próprio (a silhueta, a postura, o modo de abrir). Correto e genérico não basta para nota 2.

### O que NÃO é dele

Se aguenta (Engenheiro) e se monta (Maker). Ele pode pedir mastro mais alto; o Engenheiro diz quanto custa em tombamento.

---

## Conflitos típicos e a saída que atende os dois

| Conflito | Saída que já funcionou |
| --- | --- |
| Designer quer roda maior × Engenheiro quer centro de massa baixo | alargar a bitola (ombro) e descer a bateria |
| Designer quer mastro alto × Engenheiro teme o momento na base | pé largo sob o mastro; sensor pesado fora do topo |
| Designer quer mais detalhe × Maker quer menos peças | detalhe por repetição da mesma peça, não por peça nova |
| Engenheiro quer travar tudo × Maker precisa montar | subconjuntos (`sub = true`) e emendas lisas onde a peça já está presa |
| Maker quer bateria acessível × Engenheiro quer massa baixa | berço por baixo, que abre para a frente |

Registre a ata em `examples/<nome>/conselho.md` (modelo: `examples/rover-x6/conselho.md`).
