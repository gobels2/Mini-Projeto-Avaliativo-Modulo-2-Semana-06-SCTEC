# Design — Mini-Projeto Avaliativo M2S06: Dashboard BPS 2020–2026

**Aluno:** Leo Gobel
**Curso:** Visualização de Dados e Business Intelligence — T2 (SCTEC / "IA para Devs")
**Peso:** 25% da nota do módulo, escala 0–10
**Prazo:** 14/09/2026
**Data deste documento:** 08/09/2026

---

## 1. Objetivo

Construir um dashboard analítico sobre as compras públicas de medicamentos e
dispositivos médicos registradas no **Banco de Preços em Saúde (BPS)** do
Ministério da Saúde entre 2020 e 2026, entregando também a base consolidada, a
documentação em README e um vídeo de apresentação.

O dashboard deve permitir acompanhar a evolução dos valores, identificar os
entes e produtos mais relevantes, comparar fornecedores e fabricantes e —
principal diferencial deste trabalho — **sinalizar registros cujo preço
unitário destoa dos comparáveis**, sem tratar essa diferença como prova de
irregularidade.

## 2. Fonte e perfil dos dados

**Fonte:** Portal Brasileiro de Dados Abertos — Ministério da Saúde
`https://dadosabertos.saude.gov.br/dataset/bps`
Sete arquivos anuais `.csv` (2020 a 2026), baixados compactados.

Perfil levantado em 08/09/2026 sobre os sete arquivos:

| Métrica | Valor |
|---|---|
| Registros brutos | 342.716 |
| Registros após remoção de duplicatas exatas | 342.697 |
| Colunas | 25, idênticas nos sete anos |
| Separador / codificação | `;` / UTF-8 em todos os anos |
| Período coberto (`compra`) | 01/01/2020 a 05/03/2026 |
| Valor total registrado | R$ 78,6 bilhões |
| UFs presentes | 24 de 27 |
| Instituições (CNPJ distintos) | 831 |
| Fornecedores (CNPJ distintos) | 3.502 |
| Fabricantes | 2.124 |
| Produtos (`codigo_br` distintos) | 12.994 |

Registros por ano: 2020 = 84.819 · 2021 = 83.622 · 2022 = 88.991 ·
2023 = 31.992 · 2024 = 26.258 · 2025 = 26.215 · 2026 = 819.

## 3. Perguntas de negócio

Definidas na Sprint 1 e usadas para dirigir a construção do dashboard. Todas
são respondíveis com as colunas disponíveis na base.

1. Como evoluiu o valor total registrado entre 2020 e 2026, e como se comporta
   o número de registros no mesmo período?
2. Quais UFs, municípios e instituições concentram o maior volume financeiro —
   e esse ranking se sustenta quando os registros de preço atípico são
   excluídos?
3. Quais princípios ativos e dispositivos respondem pela maior parte do valor
   registrado e da quantidade adquirida?
4. Quais fornecedores e fabricantes têm maior participação, e qual o grau de
   concentração desse mercado?
5. Qual a modalidade de compra predominante, e o preço unitário médio ponderado
   varia entre modalidades?
6. Para um mesmo produto (`codigo_br`) e mesma unidade de fornecimento, qual a
   dispersão do preço unitário entre instituições, UFs e anos?
7. Quantos registros apresentam preço unitário desproporcional à mediana do seu
   grupo comparável, e qual o peso deles no valor total?
8. Compras judiciais apresentam preço unitário diferente das administrativas?

## 4. Mapeamento de discrepâncias entre os anos

**Não há discrepância de esquema.** Os sete arquivos têm as mesmas 25 colunas,
na mesma ordem, com o mesmo separador e a mesma codificação. Isso será afirmado
no README com a evidência do script `perfil_dados.py`, e não presumido.

As divergências reais entre os anos são semânticas e de qualidade:

| Discrepância | Observação |
|---|---|
| Queda de volume | 88.991 registros em 2022 → 31.992 em 2023 (−64%) |
| Ano parcial | 2026 tem 819 registros (base vai até 05/03/2026) |
| Nulos em `generico` e `anvisa` | caem de 56,2% (2020) para 20,5% (2026) |
| Nulos em `capacidade` e `unidade_medida` | ~63% de forma estável em todos os anos |
| Duplicatas exatas | só a partir de 2024 (16 em 2024, 1 em 2025, 2 em 2026) |
| Valor inválido em `esfera` | `"0"` em 43 registros, todos de 2020 |
| Cobertura geográfica | AM, AP e DF sem nenhum registro no período |
| Acentuação | 2.578 descrições com acento minúsculo dentro de texto maiúsculo (`SOLUçÃO`) |

## 5. Preparação e consolidação

Feita em **Python (pandas)**, e não em Power Query, porque o script fica
versionado, legível para o avaliador e reaproveitável — além de ser necessário
de qualquer forma para calcular o flag de preço atípico.

### 5.1 `src/perfil_dados.py`

Lê os sete `.zip` sem descompactar em disco, confere nomes e ordem de colunas,
codificação, contagens, nulos por ano e duplicatas. Gera o relatório de
discrepâncias que alimenta a seção 4 do README.

### 5.2 `src/consolidar.py`

Concatena os sete anos em uma única estrutura preservando todas as linhas,
acrescenta `arquivo_origem` como rastreio de proveniência e grava
`data/processed/BPS_20_26_LeoGobel.csv` (~126 MB), compactado em seguida para
`BPS_20_26_LeoGobel.zip` (~20 MB), que é o arquivo versionado no repositório.

### 5.3 `src/tratamento.py`

Tratamentos aplicados, todos documentados no README:

- **Tipos numéricos:** `qtd_itens_comprados`, `preco_unitario` e `preco_total`
  convertidos para numérico. Nenhum valor não numérico foi encontrado.
- **Datas:** `compra` e `insercao` lidas como `%d/%m/%Y` e gravadas em ISO
  `YYYY-MM-DD`, para o Power BI não depender de locale.
- **Texto:** `strip` e colapso de espaços múltiplos em nomes de instituição
  (ex.: `"FUNDO  MUNICIPAL  DE  SAUDE"`).
- **Acentuação:** `.str.upper()` em `descricao_catmat`, normalizando os 2.578
  registros com acento minúsculo em meio a texto maiúsculo.
- **`esfera`:** o valor `"0"` (43 registros) passa a `NÃO INFORMADO`.
- **Duplicatas:** removidas as 19 linhas exatamente repetidas.
- **Nulos:** `generico` e `anvisa` nulos não são erro — indicam item que não é
  medicamento registrado na Anvisa. Em vez de imputar, viram a coluna derivada
  `tipo_produto`.

### 5.4 Colunas derivadas

| Coluna | Definição |
|---|---|
| `tipo_produto` | `MEDICAMENTO` se `anvisa` preenchido, senão `DISPOSITIVO/OUTRO` |
| `principio_ativo` | primeiro token de `descricao_catmat` antes da vírgula — 2.198 valores distintos contra 12.994 `codigo_br`, o que torna os rankings legíveis |
| `regiao` | derivada de `uf` (N, NE, CO, SE, S) |
| `mediana_grupo` | mediana de `preco_unitario` no grupo (`codigo_br`, `unidade_fornecimento`) |
| `n_grupo` | tamanho do grupo comparável |
| `razao_vs_mediana` | `preco_unitario / mediana_grupo` |
| `flag_preco_atipico` | `True` quando `n_grupo >= 5` e `razao_vs_mediana >= 10` |

### 5.5 Critério do flag de preço atípico

Comparar preço unitário só faz sentido entre itens comparáveis. O grupo de
comparação é (`codigo_br`, `unidade_fornecimento`) — mesmo produto do catálogo,
mesma forma de fornecimento —, e só grupos com pelo menos 5 registros são
elegíveis (95,9% da base). O corte é **10× a mediana do grupo**.

Resultado: **4.922 registros (1,44%)** carregando **R$ 34,0 bi — 43,3% do valor
total**. Cortes de 20× e 50× capturam praticamente o mesmo valor (R$ 34,0 bi e
R$ 33,8 bi), o que mostra que a conclusão não depende do limiar escolhido.

O flag **não afirma irregularidade**. Sinaliza registros que merecem
verificação, e as causas legítimas possíveis (fabricante, apresentação, unidade,
quantidade, localidade, modalidade, período) ficam explicitadas no dashboard e
no README.

### 5.6 Validações do pipeline

- 342.716 linhas lidas; 342.697 após remoção de duplicatas.
- `qtd_itens_comprados × preco_unitario = preco_total` em 100% das linhas
  (verificado: zero divergências acima de R$ 0,01).
- Soma de `preco_total` preservada da leitura até o arquivo consolidado.
- Os sete anos presentes no arquivo final.

## 6. Modelo e KPIs no Power BI

Tabela fato única (plana) mais uma `dCalendario` para inteligência temporal.
342 mil linhas não justificam esquema estrela, e o modelo plano mantém a
demonstração de 5 minutos honesta.

### 6.1 Os seis KPIs obrigatórios

```dax
Valor Total Registrado   = SUM(fBPS[preco_total])
Qtd Total de Itens       = SUM(fBPS[qtd_itens_comprados])
Nº de Registros          = COUNTROWS(fBPS)
Instituições Compradoras = DISTINCTCOUNT(fBPS[cnpj_instituicao])
Fornecedores             = DISTINCTCOUNT(fBPS[cnpj_fornecedor])
Preço Unit. Médio Pond.  = DIVIDE([Valor Total Registrado], [Qtd Total de Itens])
```

Duas decisões deliberadas, a serem defendidas no vídeo:

- **Contagem distinta por CNPJ, não por nome.** São 831 CNPJs de instituição
  contra 663 nomes: a mesma instituição aparece grafada de várias formas, e
  contar nome subestima o total.
- **Preço médio ponderado como razão de somas**, nunca
  `AVERAGE(preco_unitario)`. Média simples de preço unitário é exatamente a
  agregação inválida que o enunciado manda evitar.

### 6.2 Medidas de apoio

```dax
Valor Registros Atípicos = CALCULATE([Valor Total Registrado], fBPS[flag_preco_atipico] = TRUE())
% do Valor em Atípicos   = DIVIDE([Valor Registros Atípicos], [Valor Total Registrado])
Preço Médio Pond. s/ Atípicos = CALCULATE([Preço Unit. Médio Pond.], fBPS[flag_preco_atipico] = FALSE())
```

## 7. Dashboard — três páginas

**P1 · Visão Geral** — seis cartões de KPI; evolução anual (colunas de valor
com linha do preço médio ponderado); modalidade de compra; composição por
`tipo_produto`; top 10 princípio ativo por valor.

**P2 · Geografia e Instituições** — mapa por UF; top 10 municípios; top 10
instituições compradoras; fornecedores × fabricantes; distribuição por esfera.

**P3 · Investigação de Preços** — alternância do flag; dispersão de
`razao_vs_mediana`; tabela dos 4.922 registros sinalizados; o caso da
Penicilamina; comparação COM/SEM que inverte o ranking de UF.

Slicers sincronizados nas três páginas: Ano, UF, Esfera, Modalidade,
Tipo de produto e Flag de preço atípico. São **13 visuais** (4 na P1, 5 na P2,
4 na P3) além dos seis cartões de KPI, contra o mínimo de 5 exigido.

### 7.1 Achados que o dashboard precisa evidenciar

- Um único registro — Penicilamina 250 mg, SES-PR, 2025, 77.500 unidades a
  R$ 294.400,00 cada — responde por **29% de todo o valor da base**. Os dez
  maiores registros somam 42,7%.
- Excluindo os registros sinalizados, o valor total cai de R$ 78,6 bi para
  R$ 44,5 bi e o preço unitário médio ponderado cai de R$ 1,3751 para R$ 0,7795.
- **O ranking de UF se inverte:** com os atípicos, PR lidera com R$ 29,2 bi;
  sem eles, SP lidera com R$ 20,1 bi e PR cai para R$ 5,6 bi.
- Nem toda dispersão é erro: cloreto de sódio varia 1.403× porque mistura
  AMPOLA, BOLSA e FRASCO; já a enoxaparina 100 mg/ml varia 4.372× dentro da
  mesma unidade SERINGA.

## 8. Estrutura do repositório

```
Mini-Projeto-Avaliativo-Modulo-2-Semana-06-SCTEC/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/            2020_csv.zip … 2026_csv.zip
│   └── processed/      BPS_20_26_LeoGobel.zip
├── src/
│   ├── perfil_dados.py
│   ├── consolidar.py
│   └── tratamento.py
├── dashboard/
│   ├── BPS_2020_2026.pbix
│   └── img/            capturas das três páginas
└── docs/
    ├── planejamento/       este documento e o plano de implementação
    └── roteiro_video.md     (no .gitignore, fica só no disco)
```

O `.gitignore` cobre três coisas: `data/processed/*.csv` (o arquivo de 126 MB
não vai para o repositório — só o `.zip` de ~20 MB vai), `docs/roteiro_video.md`
e os artefatos de Python (`__pycache__/`, `.venv/`).

## 9. Branches e commits

Mesmo padrão que funcionou no Projeto Avaliativo do Módulo 1: uma branch por
etapa, nomeada pela finalidade, com merge `--no-ff` no `main` para que o
histórico mostre cada funcionalidade separadamente.

1. `chore/estrutura-inicial`
2. `feat/perfil-e-discrepancias`
3. `feat/consolidacao-bases`
4. `feat/tratamento-e-flag`
5. `feat/dashboard-powerbi`
6. `docs/readme`
7. `docs/video`

## 10. README — seções exigidas

Objetivo · Contextualização · Fonte dos dados · Procedimentos de download e
concatenação · Tratamentos e transformações · Descrição das colunas · Definição
dos KPIs e métricas · Imagens do dashboard · Principais análises e descobertas ·
Recomendações · Limitações · Instruções de reprodução.

## 11. Vídeo

Máximo de 5 minutos, rosto visível, tela do dashboard demonstrada. As dez
perguntas do item 4.1 do enunciado precisam ser respondidas. O roteiro será
medido **por contagem de palavras** (~150 palavras/min em português falado),
não por estimativa: teto de aproximadamente 600 palavras faladas mais o tempo
de tela. O vídeo é hospedado em pasta do repositório em modo leitor e o link é
colado no README e submetido no AVA.

## 12. Cronograma até 14/09

| Dia | Entrega |
|---|---|
| 08/09 | Estrutura do repo; `perfil_dados.py` e relatório de discrepâncias |
| 09/09 | `consolidar.py` e `tratamento.py`; `BPS_20_26_LeoGobel.zip` gerado e validado |
| 10/09 | Instalar Power BI Desktop; modelo, `dCalendario`, seis KPIs, página 1 |
| 11/09 | Páginas 2 e 3, slicers sincronizados, formatação |
| 12/09 | README completo e capturas de tela |
| 13/09 | Roteiro medido, gravação do vídeo, revisão final |
| 14/09 | Entrega no AVA |

## 13. Riscos

- **Power BI Desktop não está instalado** nesta máquina (verificado em
  08/09/2026). É pré-requisito do dia 10/09 e está no caminho crítico.
- **Perda de comentários em arquivos no disco** — comportamento já observado
  nesta máquina, que apagou 100 linhas de comentários dos `.sql` do Módulo 1.
  Conferir `wc -l` e `git diff --stat` antes de cada commit.
- **Tamanho do `.pbix`** — a compressão VertiPaq deve deixar 342 mil linhas bem
  abaixo do limite de 100 MB do GitHub, mas isso será verificado, não presumido.
- **Sem link ao vivo do dashboard** — publicar no Power BI Service exige conta
  corporativa ou acadêmica. A entrega são o `.pbix`, as capturas e o vídeo.

## 14. Critérios de aceite

Cada item mapeia um critério da rubrica do enunciado.

- [ ] Sete arquivos `.csv` de 2020 a 2026 baixados e organizados (crit. 04)
- [ ] Discrepâncias entre anos mapeadas e documentadas com evidência (crit. 05)
- [ ] Oito perguntas de negócio formuladas e respondidas pelo dashboard (crit. 06)
- [ ] Codificação, acentuação e caracteres corrompidos tratados (crit. 07)
- [ ] Nulos, inconsistências e duplicatas investigados e tratados (crit. 08)
- [ ] Sete bases consolidadas em estrutura única sem perda de linhas (crit. 09)
- [ ] Seis KPIs com agregações válidas e fórmulas conferidas (crit. 10, 11)
- [ ] Mínimo de cinco visuais mais filtros interativos (crit. 12)
- [ ] Organização visual e legibilidade permitindo a análise da Sprint 5 (crit. 13)
- [ ] Branches e commits padronizados por funcionalidade (crit. 01)
- [ ] Arquivos estruturados e README completo (crit. 02)
- [ ] Vídeo de até 5 min cobrindo as dez perguntas do item 4.1 (crit. 03)
