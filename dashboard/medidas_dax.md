# Medidas DAX do dashboard

Referência das medidas usadas em `BPS_2020_2026.pbix`. Cada bloco é para colar
direto em **Modelagem > Nova medida** no Power BI Desktop.

A tabela de fatos chama-se `fBPS` e vem de
`data/processed/BPS_20_26_LeoGobel.csv`.

---

## 1. Importação

**Página Inicial > Obter dados > Texto/CSV** apontando para
`data/processed/BPS_20_26_LeoGobel.csv`.

Na janela de visualização, antes de carregar:

| Opção | Valor |
|---|---|
| Origem do arquivo | **65001: Unicode (UTF-8)** |
| Delimitador | **Ponto e vírgula** |
| Detecção de tipo de dados | Com base no conjunto de dados inteiro |

Clicar em **Transformar Dados**, renomear a consulta para `fBPS` e conferir os
tipos antes de aplicar:

| Coluna | Tipo |
|---|---|
| `compra`, `insercao` | Data |
| `qtd_itens_comprados`, `preco_unitario`, `preco_total` | Número Decimal |
| `mediana_grupo`, `razao_vs_mediana` | Número Decimal |
| `n_grupo` | Número Inteiro |
| `flag_preco_atipico` | Verdadeiro/Falso |
| todas as demais | Texto |

As datas já saem do pipeline em ISO (`2020-01-01`), então o Power BI não
depende do locale da máquina para interpretá-las.

---

## 2. Tabela de calendário

**Modelagem > Nova tabela:**

```dax
dCalendario =
VAR DataMinima = MIN(fBPS[compra])
VAR DataMaxima = MAX(fBPS[compra])
RETURN
ADDCOLUMNS(
    CALENDAR(DataMinima, DataMaxima),
    "Ano", YEAR([Date]),
    "Mês", MONTH([Date]),
    "Nome do Mês", FORMAT([Date], "MMM"),
    "Ano-Mês", FORMAT([Date], "YYYY-MM")
)
```

Depois: **Modelagem > Marcar como tabela de data**, coluna `Date`. E criar a
relação `dCalendario[Date]` 1:N `fBPS[compra]`.

---

## 3. Os seis KPIs obrigatórios

```dax
Valor Total Registrado = SUM(fBPS[preco_total])
```

```dax
Qtd Total de Itens = SUM(fBPS[qtd_itens_comprados])
```

```dax
Nº de Registros = COUNTROWS(fBPS)
```

```dax
Instituições Compradoras = DISTINCTCOUNT(fBPS[cnpj_instituicao])
```

```dax
Fornecedores = DISTINCTCOUNT(fBPS[cnpj_fornecedor])
```

```dax
Preço Unit. Médio Ponderado = DIVIDE([Valor Total Registrado], [Qtd Total de Itens])
```

### Por que essas duas decisões

**Contagem distinta por CNPJ, não por nome.** A base tem **831 CNPJs** de
instituição para apenas **663 nomes** distintos — a mesma instituição aparece
grafada de várias formas ("FUNDO MUNICIPAL DE SAUDE" repete-se em dezenas de
municípios diferentes). Contar por nome subestimaria o indicador em 20%.

**Preço médio ponderado é razão de somas, nunca média de preço unitário.**
`AVERAGE(fBPS[preco_unitario])` daria o mesmo peso a uma compra de 10 unidades
e a uma de 4 milhões. `DIVIDE` do valor total pela quantidade total é o preço
efetivamente pago por unidade — e é exatamente a agregação que o enunciado
manda usar em vez da soma de preços unitários.

---

## 4. Medidas de apoio da página de investigação

```dax
Valor Registros Atípicos =
CALCULATE([Valor Total Registrado], fBPS[flag_preco_atipico] = TRUE())
```

```dax
% do Valor em Atípicos =
DIVIDE([Valor Registros Atípicos], [Valor Total Registrado])
```

```dax
Preço Médio Pond. s/ Atípicos =
CALCULATE([Preço Unit. Médio Ponderado], fBPS[flag_preco_atipico] = FALSE())
```

---

## 5. Formatação

| Medida | Formato |
|---|---|
| Valor Total Registrado | Moeda, 0 casas decimais |
| Valor Registros Atípicos | Moeda, 0 casas decimais |
| Preço Unit. Médio Ponderado | Moeda, **4 casas decimais** |
| Preço Médio Pond. s/ Atípicos | Moeda, **4 casas decimais** |
| % do Valor em Atípicos | Porcentagem, 1 casa decimal |
| Qtd Total de Itens, Nº de Registros | Número inteiro com separador de milhar |

O preço médio ponderado precisa de 4 casas porque o valor fica abaixo de
R$ 1,40 — com 2 casas a diferença entre com e sem atípicos ficaria ilegível.

---

## 6. Conferência obrigatória antes de desenhar qualquer visual

Colocar cada medida em um cartão, **sem nenhum filtro aplicado**, e comparar
com os números que o pipeline imprimiu. Divergência aqui significa erro de
tipo na importação — voltar à etapa 1 antes de seguir.

| Medida | Valor esperado |
|---|---|
| Valor Total Registrado | R$ 78.557.477.974,09 |
| Qtd Total de Itens | 57.127.143.721 |
| Nº de Registros | 342.697 |
| Instituições Compradoras | 831 |
| Fornecedores | 3.502 |
| Preço Unit. Médio Ponderado | R$ 1,3751 |
| Valor Registros Atípicos | R$ 34.040.763.532,94 |
| % do Valor em Atípicos | 43,3% |
| Preço Médio Pond. s/ Atípicos | R$ 0,7795 |

---

## 7. O que a página 3 precisa demonstrar ao vivo

Com o filtro `flag_preco_atipico` alternado entre Verdadeiro e Falso, o
ranking de UF por `Valor Total Registrado` **inverte**:

| | 1º | 2º | 3º |
|---|---|---|---|
| **Com** atípicos | PR — R$ 29,2 bi | SP — R$ 25,4 bi | CE — R$ 5,4 bi |
| **Sem** atípicos | SP — R$ 20,1 bi | PR — R$ 5,6 bi | CE — R$ 5,4 bi |

O Paraná só aparece como maior comprador do país por causa de **um registro**:
Penicilamina 250 mg, Secretaria de Estado da Saúde, 2025, 77.500 unidades a
R$ 294.400,00 cada — R$ 22,8 bilhões, ou 29% de toda a base.

Isso é indício para investigação, **não prova de irregularidade**. Diferenças
de preço podem decorrer de fabricante, apresentação, unidade de fornecimento,
quantidade adquirida, localidade, modalidade de compra, período e
características da negociação.
