# Testes e validação

Não existe framework de testes, arquivo de teste nem pipeline de CI neste repositório: não há `*_test.*`, nem workflows, nem target de teste no `Makefile`. A garantia de que o sistema encaixa vem de três mecanismos que convivem — asserções embutidas em cada peça, teste de colisão nas montagens e validação visual dos renders — mais o teste canônico definido na própria spec.

## 1. Asserções por `echo` em cada peça

Todo arquivo de `impl/openscad/` termina com um bloco `echo` que imprime as dimensões calculadas e, depois de um separador `---`, as verificações de compatibilidade daquela peça no formato `SIM` / `VERIFICAR (...)`. São elas que protegem as invariantes de `spec/rules.md` quando alguém mexe nos parâmetros:

| Arquivo | Invariantes verificadas |
| --- | --- |
| `impl/openscad/plate.scad` | há pelo menos 1 mm de parede em cada lado do furo de borda (`thickness >= edge_hole_d + 2`) |
| `impl/openscad/link.scad` | cada lado não invade o rebaixo oposto da PLATE (`pin <= thickness − 2×relief_depth`) e o pino cabe no ATOM; imprime a regra "1 pino por furo" |
| `impl/openscad/bridge.scad` | o meio-dowel não bate no fundo do furo e dois dowels opostos caibam na seção compartilhada (`2 × half <= shared_sec − 0.5`) |
| `impl/openscad/corner.scad` | encaixe em "L" alinhado (`edge_inset == wall_thickness/2`), parede do canal ≥ 1 mm, pino menor que a profundidade do furo, dois machos opostos na seção de 5 mm |
| `impl/openscad/pin.scad` | posições coincidem com o centro da seção (`edge_inset == sec_w/2`), pino compatível com o furo de borda, dois machos opostos em `min(sec_w, sec_h)` |
| `impl/openscad/track.scad` | furos no passo do grid (`span % cell_size == 0`) e parede furo→borda ≥ 1.5 mm |
| `impl/openscad/wheel.scad` | parede entre furo e banda ≥ 2 mm e furo central compatível com o LINK padrão (`hole_d == 10`) |

Para lê-las, renderize o arquivo (por exemplo com `make preview`, que não suprime a saída do OpenSCAD) ou abra a peça no OpenSCAD e observe o console.

Limites reais dessa abordagem, que convém conhecer antes de confiar nela:

- as mensagens são informativas — um `VERIFICAR` **não** falha o render nem impede a exportação do STL;
- `impl/openscad/atom.scad` e `impl/openscad/link-oneside.scad` só imprimem dimensões, sem nenhuma verificação;
- as checagens de `elbow.scad` e `vertex.scad` (`c == sec/2`) são tautológicas, já que `c` é definido como `sec/2` no próprio arquivo;
- nada verifica a consistência **entre** peças: como cada `.scad` redeclara os parâmetros globais de `spec/params.md`, uma divergência de `hole_d` ou `edge_inset` entre dois arquivos passa silenciosamente;
- `preview-animated` e o render de frames de montagem usam `2>/dev/null` e descartam essa saída.

## 2. Teste de colisão nas montagens

Cada `examples/*/assembly.scad` expõe dois parâmetros de verificação: `check_collisions`, que desenha em vermelho as interseções par a par sobre a montagem, e `collisions_only`, que oculta as peças e renderiza **apenas** as interseções. O segundo é o que permite medir: exportando essa versão como STL, o volume do sólido é a medida da interferência.

Restrição incontornável, avisada nos comentários dos próprios arquivos: `intersection()` entre módulos só é calculado no **render completo** (`F6` / `--render`); no preview (`F5` / `--preview`) o resultado não aparece.

O procedimento completo está registrado em `.claude/skills/fusionbrick-builder/SKILL.md`: exportar `collisions_only=true` com `--render --export-format binstl` e somar o volume dos triângulos do STL binário. O critério é `0.0000 mm³` — faces coincidentes (peças encostadas, que é o comportamento correto do sistema) geram triângulos degenerados de volume zero, enquanto interpenetração real gera volume positivo.

A cobertura é **enumerada, não exaustiva**: só os pares listados dentro do bloco `if (check_collisions || collisions_only)` são testados. Em `examples/u-channel/assembly.scad` são 9 pares (placas × dowels, placas × cada corner, cada parede × seu corner, placas × paredes, e o ATOM contra parede e base). Em `examples/rover-chassis/assembly.scad` são 11 pares cobrindo piso × trilhos/para-choques/capô/deck, trilhos × elbows e a cadeia da gaiola (postes, vértices, travessas, trilhos longitudinais e dowels). Pares não listados não são verificados.

## 3. Validação visual

Como a geometria depende de rotações e espelhamentos fáceis de errar, o render isométrico é tratado como etapa de validação, não como enfeite: `make assembly` gera o still normal e a vista explodida (`-D explode=12`) de cada montagem, e a vista explodida é justamente o que revela peça fora de posição ou conector no furo errado. O fluxo de trabalho para novas montagens em `.claude/skills/fusionbrick-builder/SKILL.md` exige renderizar, **olhar a imagem** e iterar até bater com a intenção, antes de rodar o teste de colisão.

A armadilha conhecida: contato flush entre peças produz z-fighting no preview. Isso é esperado — junções do sistema têm gap zero — e não deve ser "corrigido" inserindo espaçamento, o que violaria a Lei do Grid.

## 4. Teste canônico do sistema

`spec/design-system.md` e `spec/rules.md` definem a verificação que vale para o sistema inteiro, acima de qualquer peça: em qualquer montagem, **um ATOM deve entrar em qualquer célula interior e alinhar com todos os furos vizinhos**; para um canal em "U" com base de `n` células, o interior deve ter exatamente `n` células livres.

`examples/u-channel/assembly.scad` existe para materializar esse teste — daí o ATOM interno ligado por dois LINKs assimétricos, um vertical na base e um horizontal na parede. Uma peça nova ou uma mudança de interface só está validada quando esse cenário continua fechando.

## Lacunas atuais

- `impl/openscad/track.scad` e `impl/openscad/wheel.scad` não participam de nenhuma montagem, não têm spec em `spec/parts/` e não têm artefatos em `renders/` — nenhum dos três mecanismos acima as cobre hoje.
- Não há automação que colete o resultado das verificações: o teste de colisão precisa ser disparado à mão, peça por montagem, e as asserções de `echo` precisam ser lidas por uma pessoa.
