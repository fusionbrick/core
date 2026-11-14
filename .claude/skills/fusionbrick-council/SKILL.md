---
name: fusionbrick-council
description: Conselho de qualidade do FusionBrick — garante que toda peça e todo produto gerado saia num padrão de produto de verdade (inovador, bonito, funcional e possível), inspirado no rigor de Apple, Braun, LEGO, Dyson e Toyota. Roda a ficha de portões medidos e depois três perfis com veto. Use ANTES de entregar qualquer montagem, ANTES de gerar STL para imprimir, ANTES de aceitar peça/parâmetro novo, e quando pedirem revisão. Triggers - "revisa isso", "o conselho acha", "council", "está bom?", "padrão de qualidade", "melhora o produto", "antes de entregar", "antes de imprimir", "peça nova", "vale a pena", "está superengenheirado".
---

# Conselho FusionBrick

Nada sai sem passar por aqui. O conselho existe para que cada geração pareça **produto**, não exercício: uma ideia clara, executada com cuidado até onde ninguém olha, que funciona e que dá para fabricar.

| Arquivo | Para quê |
| --- | --- |
| `reference/padrao.md` | o padrão de qualidade: 8 princípios, de onde vêm e como se medem aqui |
| `reference/produto.md` | câmara de **produto** — Maker · Engenheiro · Designer (rover, case, suporte montado) |
| `reference/pecas.md` | câmara de **peça** — Simplicidade · Maker · Impressor (peça, parâmetro, catálogo) |

## O padrão em uma página

Oito princípios. Cada um tem um teste; os que têm número viram **portão** (falhou, não segue).

| # | Princípio | Teste | Portão medido |
| --- | --- | --- | --- |
| 1 | **Uma ideia.** O produto diz o que é em uma frase, e tudo serve a ela | tire um elemento: a frase piora? Se não, ele sai | — |
| 2 | **Menos, porém melhor.** Poucas peças diferentes, poucos tipos de junta | conte STLs únicos e cores | cópias por STL ≥ 2 · cores ≤ 3 |
| 3 | **Funciona de verdade.** Fica em pé, aguenta o uso, tem como andar e ligar | massa, tombamento, motores, bateria | tombamento ≥ 45° · base de peça alta ≥ 4 juntas a ≥ 24 mm |
| 4 | **Cuidado onde ninguém vê.** Embaixo, por dentro e atrás no mesmo nível da frente | vire o modelo; siga cada fio | pinos sem uso = 0 · colisão exata = zero |
| 5 | **Encaixe e acabamento.** Tudo alinhado, simétrico, sem folga nem sobra | vista de topo e de frente | centro de massa ≤ 10 mm do centro · erros = 0 |
| 6 | **Montar é parte do produto.** Sem ferramenta, uma ordem que existe, um movimento por peça | leia `steps.md` como quem nunca viu | ASM-012 = 0 · todo passo com nota · cavilhas ≤ 55% |
| 7 | **Possível.** Imprime na máquina comum, hoje | maior peça, material, tempo | maior peça ≤ 220 mm |
| 8 | **Presença.** A imagem principal vende sozinha | 3 segundos, sem legenda | resolução 15–40 · roda/comprimento 0,20–0,45 |

## Como rodar

### 1. Ficha de qualidade — antes de qualquer opinião

```bash
make assemble NAME=<nome>               # STLs + render
make assemble-collide NAME=<nome>       # colisão exata; grava collide.txt
python3 hack/scripts/fb_assemble.py review examples/<nome>/assembly.toml
```

`review` roda todos os portões medidos e termina em **APTO** ou **NÃO APTO**. Com portão falhando, o conselho **não opina**: conserta-se primeiro. Discutir gosto sobre algo que tomba ou não monta é desperdício.

### 2. Os três perfis — com veto e com nota

Câmara de **produto** (`reference/produto.md`), na ordem Maker → Engenheiro → Designer; câmara de **peça** (`reference/pecas.md`), na ordem Simplicidade → Maker → Impressor. Cada perfil devolve, por item:

```
VETO | RESSALVA | OK
  o quê:      uma frase
  evidência:  número (review / stats / physics / render / impressão) — ou "nenhuma"
  proposta:   a mudança, e o que ela custa aos outros dois
```

e uma **nota de 0 a 2** em cada princípio que é dele (0 = falha, 1 = aceitável, 2 = exemplar). Evidência "nenhuma" não sustenta VETO: vira RESSALVA e uma tarefa de medir.

### 3. A barra

O produto só é entregue como "alta qualidade" com:

- ficha **APTO** (todos os portões);
- **nenhum VETO** aberto e **nenhuma nota 0**;
- **média ≥ 1,5** nos oito princípios;
- pelo menos **um 2** em Presença ou em Uma ideia — produto correto e sem graça não passa.

Abaixo disso, entrega-se dizendo o que falta — nunca calado.

### 4. Conflitos, mudanças, ata

Os perfis discordam por projeto (mastro alto × tombamento; roda grande × centro de massa; menos peças × mais detalhe). **Resolva cada conflito por escrito**, de preferência com a solução que atende os dois. Implemente, rode `review` de novo e reavalie só o que mudou. A ata fica em `examples/<nome>/conselho.md`: votos, conflitos, o que mudou, e **antes → depois de cada número**.

## Regras que valem para todos

> **Afirmação sem evidência não vota. Evidência sem controle negativo não é evidência.**

Antes de aceitar um número, pergunte: *o que este teste mostraria se a coisa estivesse quebrada?* Se a resposta for "a mesma coisa", o teste não vale. (O `ASM-012` só virou confiável quando a ordem foi trocada de propósito e os avisos voltaram; o `fb_collide` acusava ~500 mm³ onde o motor geométrico tinha simplesmente falhado.)

- **Três aprovações fáceis é teatro.** Se ninguém discordou, o conselho só carimbou.
- **Perfil fora do território é ruído.** O Designer não decide tolerância; o Impressor não decide catálogo.
- **Todo VETO diz o que muda o voto.** Sem isso é bloqueio, não revisão.
- **Dizer não é o trabalho.** Elemento sem função, parâmetro sem dois casos reais, peça que é configuração de outra: saem.
- **Não convoque no meio da implementação** de algo já decidido, nem com `check` falhando.
