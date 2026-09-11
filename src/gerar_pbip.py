"""Gera o projeto Power BI (PBIP) do Mini-Projeto M2S06.

Emite o modelo semântico em TMSL (model.bim) e o relatório em PBIR
(definition/), ambos formatos públicos e editáveis fora do Power BI Desktop.

Uso:
    python gerar_pbip.py <pasta_dashboard> <caminho_absoluto_do_csv>
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

NOME = "BPS_2020_2026"
TABELA = "fBPS"
CAL = "dCalendario"

S_PBIP = "https://developer.microsoft.com/json-schemas/fabric/item/pbip/definitionProperties/1.0.0/schema.json"
S_PBISM = "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json"
S_PBIR = "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json"
S_VER = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json"
S_REPORT = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/1.0.0/schema.json"
S_PAGES = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json"
S_PAGE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/1.0.0/schema.json"
S_VISUAL = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/1.0.0/schema.json"

# (coluna, tipo TMSL, tipo M)
COLUNAS = [
    ("ano_compra", "int64", "Int64.Type"),
    ("nome_instituicao", "string", "type text"),
    ("esfera", "string", "type text"),
    ("cnpj_instituicao", "string", "type text"),
    ("municipio_instituicao", "string", "type text"),
    ("uf", "string", "type text"),
    ("compra", "dateTime", "type date"),
    ("insercao", "dateTime", "type date"),
    ("codigo_br", "string", "type text"),
    ("descricao_catmat", "string", "type text"),
    ("unidade_fornecimento", "string", "type text"),
    ("generico", "string", "type text"),
    ("anvisa", "string", "type text"),
    ("modalidade_compra", "string", "type text"),
    ("tipo_compra", "string", "type text"),
    ("capacidade", "double", "type number"),
    ("unidade_medida", "string", "type text"),
    ("unidade_fornecimento_capacidade", "string", "type text"),
    ("cnpj_fornecedor", "string", "type text"),
    ("fornecedor", "string", "type text"),
    ("cnpj_fabricante", "string", "type text"),
    ("fabricante", "string", "type text"),
    ("qtd_itens_comprados", "double", "type number"),
    ("preco_unitario", "double", "type number"),
    ("preco_total", "double", "type number"),
    ("arquivo_origem", "string", "type text"),
    ("tipo_produto", "string", "type text"),
    ("principio_ativo", "string", "type text"),
    ("regiao", "string", "type text"),
    ("n_grupo", "double", "type number"),
    ("mediana_grupo", "double", "type number"),
    ("razao_vs_mediana", "double", "type number"),
    ("flag_preco_atipico", "boolean", "type logical"),
]

MEDIDAS = [
    ("Valor Total Registrado", "SUM(fBPS[preco_total])",
     '"R$" #,0;-"R$" #,0;"R$" #,0'),
    ("Qtd Total de Itens", "SUM(fBPS[qtd_itens_comprados])", "#,0"),
    ("Nº de Registros", "COUNTROWS(fBPS)", "#,0"),
    ("Instituições Compradoras", "DISTINCTCOUNT(fBPS[cnpj_instituicao])", "#,0"),
    ("Fornecedores", "DISTINCTCOUNT(fBPS[cnpj_fornecedor])", "#,0"),
    ("Preço Unit. Médio Ponderado",
     "DIVIDE([Valor Total Registrado], [Qtd Total de Itens])",
     '"R$" #,0.0000;-"R$" #,0.0000;"R$" #,0.0000'),
    ("Valor Registros Atípicos",
     "CALCULATE([Valor Total Registrado], fBPS[flag_preco_atipico] = TRUE())",
     '"R$" #,0;-"R$" #,0;"R$" #,0'),
    ("% do Valor em Atípicos",
     "DIVIDE([Valor Registros Atípicos], [Valor Total Registrado])", "0.0%"),
    ("Preço Médio Pond. s/ Atípicos",
     "CALCULATE([Preço Unit. Médio Ponderado], fBPS[flag_preco_atipico] = FALSE())",
     '"R$" #,0.0000;-"R$" #,0.0000;"R$" #,0.0000'),
]


def m_query(csv_path: str) -> list[str]:
    """Expressão Power Query que carrega o CSV consolidado.

    A cultura "en-US" é obrigatória: o pipeline em pandas gravou decimais com
    ponto e datas em ISO. Usar pt-BR aqui leria 4.5 como quarenta e cinco.
    """
    tipos = ", ".join(f'{{"{c}", {t}}}' for c, _, t in COLUNAS)
    return [
        "let",
        f'    Fonte = Csv.Document(File.Contents("{csv_path}"), '
        f"[Delimiter=\";\", Columns={len(COLUNAS)}, Encoding=65001, "
        "QuoteStyle=QuoteStyle.Csv]),",
        "    Promovido = Table.PromoteHeaders(Fonte, [PromoteAllScalars=true]),",
        f'    Tipado = Table.TransformColumnTypes(Promovido, {{{tipos}}}, "en-US")',
        "in",
        "    Tipado",
    ]


def model_bim(csv_path: str) -> dict:
    colunas = [
        {
            "name": c,
            "dataType": t,
            "sourceColumn": c,
            "summarizeBy": "none",
            "annotations": [
                {"name": "SummarizationSetBy", "value": "Automatic"}
            ],
        }
        for c, t, _ in COLUNAS
    ]
    for col in colunas:
        if col["name"] in ("compra", "insercao"):
            col["formatString"] = "yyyy-mm-dd"

    # Rótulo legível para o gráfico de instituições. O KPI continua contando
    # cnpj_instituicao, que é exato (831). Este rótulo agrupa por nome + UF
    # (694 combinações): 20 pares nome+UF abrigam mais de um CNPJ, então São
    # Paulo aparece como R$ 22,06 bi em vez de R$ 21,89 bi. É uma aproximação
    # de 0,8% em troca de um eixo legível — muito melhor que agrupar só por
    # nome, que somava R$ 48,75 bi numa barra que não é instituição nenhuma.
    colunas.append({
        "name": "instituicao",
        "dataType": "string",
        "type": "calculated",
        "isDataTypeInferred": True,
        "expression": 'fBPS[nome_instituicao] & " · " & fBPS[uf]',
        "summarizeBy": "none",
    })

    medidas = [
        {
            "name": nome,
            "expression": expr,
            "formatString": fmt,
            "lineageTag": f"med-{i}",
        }
        for i, (nome, expr, fmt) in enumerate(MEDIDAS)
    ]

    cal_dax = (
        "ADDCOLUMNS(\n"
        "    CALENDAR(MIN(fBPS[compra]), MAX(fBPS[compra])),\n"
        '    "Ano", YEAR([Date]),\n'
        '    "Mês", MONTH([Date]),\n'
        '    "Nome do Mês", FORMAT([Date], "MMM"),\n'
        '    "Ano-Mês", FORMAT([Date], "YYYY-MM")\n'
        ")"
    )

    return {
        "name": NOME,
        "compatibilityLevel": 1567,
        "model": {
            "culture": "pt-BR",
            "dataAccessOptions": {
                "legacyRedirects": True,
                "returnErrorValuesAsNull": True,
            },
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "pt-BR",
            "tables": [
                {
                    "name": TABELA,
                    "lineageTag": "tabela-fbps",
                    "columns": colunas,
                    "measures": medidas,
                    "partitions": [
                        {
                            "name": f"{TABELA}-particao",
                            "mode": "import",
                            "source": {
                                "type": "m",
                                "expression": m_query(csv_path),
                            },
                        }
                    ],
                },
                {
                    "name": CAL,
                    "lineageTag": "tabela-dcal",
                    "dataCategory": "Time",
                    "columns": [
                        {
                            "name": "Date",
                            "dataType": "dateTime",
                            "isNameInferred": True,
                            "isDataTypeInferred": True,
                            "isKey": True,
                            "sourceColumn": "[Date]",
                            "formatString": "yyyy-mm-dd",
                            "summarizeBy": "none",
                            "type": "calculatedTableColumn",
                        },
                        {
                            "name": "Ano",
                            "dataType": "int64",
                            "isNameInferred": True,
                            "isDataTypeInferred": True,
                            "sourceColumn": "[Ano]",
                            "summarizeBy": "none",
                            "type": "calculatedTableColumn",
                        },
                        {
                            "name": "Mês",
                            "dataType": "int64",
                            "isNameInferred": True,
                            "isDataTypeInferred": True,
                            "sourceColumn": "[Mês]",
                            "summarizeBy": "none",
                            "type": "calculatedTableColumn",
                        },
                        {
                            "name": "Nome do Mês",
                            "dataType": "string",
                            "isNameInferred": True,
                            "isDataTypeInferred": True,
                            "sourceColumn": "[Nome do Mês]",
                            "summarizeBy": "none",
                            "type": "calculatedTableColumn",
                        },
                        {
                            "name": "Ano-Mês",
                            "dataType": "string",
                            "isNameInferred": True,
                            "isDataTypeInferred": True,
                            "sourceColumn": "[Ano-Mês]",
                            "summarizeBy": "none",
                            "type": "calculatedTableColumn",
                        },
                    ],
                    "partitions": [
                        {
                            "name": f"{CAL}-particao",
                            "mode": "import",
                            "source": {"type": "calculated", "expression": cal_dax},
                        }
                    ],
                },
            ],
            "relationships": [
                {
                    "name": "rel-dcal-fbps",
                    "fromTable": TABELA,
                    "fromColumn": "compra",
                    "toTable": CAL,
                    "toColumn": "Date",
                    "crossFilteringBehavior": "oneDirection",
                }
            ],
            "annotations": [
                {"name": "PBI_QueryOrder", "value": json.dumps([TABELA])},
            ],
        },
    }


# --------------------------------------------------------------------------
# Relatório (PBIR)
# --------------------------------------------------------------------------

def campo_medida(nome: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": TABELA}}, "Property": nome}}


def campo_coluna(tabela: str, nome: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": nome}}


def proj(campo: dict, ref: str, nome_nativo: str) -> dict:
    return {"field": campo, "queryRef": ref, "nativeQueryRef": nome_nativo}


def titulo(texto: str) -> dict:
    return {
        "title": [
            {
                "properties": {
                    "text": {"expr": {"Literal": {"Value": f"'{texto}'"}}},
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                }
            }
        ]
    }


def visual_card(nome: str, medida: str, x, y, w, h) -> dict:
    return {
        "$schema": S_VISUAL,
        "name": nome,
        "position": {"x": x, "y": y, "width": w, "height": h, "z": 0},
        "visual": {
            "visualType": "card",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [
                            proj(campo_medida(medida), f"{TABELA}.{medida}", medida)
                        ]
                    }
                }
            },
            "visualContainerObjects": titulo(medida),
        },
    }


def filtro_topn(tabela_cat: str, coluna_cat: str, medida: str, n: int) -> dict:
    """Filtro Top N do visual, equivalente ao "N Principais" do painel Filtros.

    A estrutura é a do próprio Power BI: uma subconsulta ordenada pela medida
    e cortada em `Top`, exposta no `From` como tabela de expressão (Type 2), e
    um `In` no `Where` restringindo a categoria ao resultado dela.
    """
    return {
        "name": f"topn_{coluna_cat}",
        "displayName": f"Top {n} por {medida}",
        "type": "TopN",
        "howCreated": "User",
        "field": campo_coluna(tabela_cat, coluna_cat),
        "filter": {
            "Version": 2,
            "From": [
                {"Name": "t", "Entity": tabela_cat, "Type": 0},
                {
                    "Name": "top",
                    "Type": 2,
                    "Expression": {
                        "Subquery": {
                            "Query": {
                                "Version": 2,
                                "From": [
                                    {"Name": "s", "Entity": tabela_cat, "Type": 0},
                                    {"Name": "m", "Entity": TABELA, "Type": 0},
                                ],
                                "Select": [
                                    {
                                        "Column": {
                                            "Expression": {"SourceRef": {"Source": "s"}},
                                            "Property": coluna_cat,
                                        },
                                        "Name": f"{tabela_cat}.{coluna_cat}",
                                    }
                                ],
                                "OrderBy": [
                                    {
                                        "Direction": 2,
                                        "Expression": {
                                            "Measure": {
                                                "Expression": {"SourceRef": {"Source": "m"}},
                                                "Property": medida,
                                            }
                                        },
                                    }
                                ],
                                "Top": n,
                            }
                        }
                    },
                },
            ],
            "Where": [
                {
                    "Condition": {
                        "In": {
                            "Expressions": [
                                {
                                    "Column": {
                                        "Expression": {"SourceRef": {"Source": "t"}},
                                        "Property": coluna_cat,
                                    }
                                }
                            ],
                            "Table": {"SourceRef": {"Source": "top"}},
                        }
                    }
                }
            ],
        },
    }


def visual_categoria(nome, tipo, tabela_cat, coluna_cat, medida, x, y, w, h,
                     texto_titulo, ordenar_desc=True, topn=None) -> dict:
    v = {
        "$schema": S_VISUAL,
        "name": nome,
        "position": {"x": x, "y": y, "width": w, "height": h, "z": 0},
        "visual": {
            "visualType": tipo,
            "query": {
                "queryState": {
                    "Category": {
                        "projections": [
                            proj(campo_coluna(tabela_cat, coluna_cat),
                                 f"{tabela_cat}.{coluna_cat}", coluna_cat)
                        ]
                    },
                    "Y": {
                        "projections": [
                            proj(campo_medida(medida), f"{TABELA}.{medida}", medida)
                        ]
                    },
                }
            },
            "visualContainerObjects": titulo(texto_titulo),
        },
    }
    if ordenar_desc:
        v["visual"]["query"]["sortDefinition"] = {
            "sort": [{"field": campo_medida(medida), "direction": "Descending"}],
            "isDefaultSort": True,
        }
    if topn:
        v["filterConfig"] = {
            "filters": [filtro_topn(tabela_cat, coluna_cat, medida, topn)]
        }
    return v


def visual_slicer(nome, tabela, coluna, x, y, w, h, texto_titulo) -> dict:
    return {
        "$schema": S_VISUAL,
        "name": nome,
        "position": {"x": x, "y": y, "width": w, "height": h, "z": 0},
        "visual": {
            "visualType": "slicer",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [
                            proj(campo_coluna(tabela, coluna),
                                 f"{tabela}.{coluna}", coluna)
                        ]
                    }
                }
            },
            "visualContainerObjects": titulo(texto_titulo),
        },
    }


def visual_tabela(nome, campos, x, y, w, h, texto_titulo) -> dict:
    projs = []
    for tabela, col, is_medida in campos:
        campo = campo_medida(col) if is_medida else campo_coluna(tabela, col)
        projs.append(proj(campo, f"{tabela}.{col}", col))
    return {
        "$schema": S_VISUAL,
        "name": nome,
        "position": {"x": x, "y": y, "width": w, "height": h, "z": 0},
        "visual": {
            "visualType": "tableEx",
            "query": {"queryState": {"Values": {"projections": projs}}},
            "visualContainerObjects": titulo(texto_titulo),
        },
    }


KPIS = [
    "Valor Total Registrado", "Qtd Total de Itens", "Nº de Registros",
    "Instituições Compradoras", "Fornecedores", "Preço Unit. Médio Ponderado",
]


def paginas() -> list[tuple[str, str, list[dict]]]:
    p1 = []
    for i, m in enumerate(KPIS):
        p1.append(visual_card(f"kpi{i+1}", m, 16 + i * 208, 12, 200, 88))
    p1 += [
        visual_categoria("valor_por_ano", "clusteredColumnChart", CAL, "Ano",
                         "Valor Total Registrado", 16, 112, 412, 290,
                         "Valor registrado por ano", ordenar_desc=False),
        visual_categoria("preco_por_ano", "lineChart", CAL, "Ano",
                         "Preço Unit. Médio Ponderado", 436, 112, 412, 290,
                         "Preço unitário médio ponderado por ano", ordenar_desc=False),
        visual_categoria("por_modalidade", "clusteredBarChart", TABELA,
                         "modalidade_compra", "Valor Total Registrado",
                         856, 112, 400, 290, "Valor por modalidade de compra"),
        visual_categoria("por_principio", "clusteredBarChart", TABELA,
                         "principio_ativo", "Valor Total Registrado",
                         16, 410, 620, 296,
                         "Top 10 princípios ativos e produtos por valor", topn=10),
        visual_categoria("por_tipocompra", "clusteredBarChart", TABELA,
                         "tipo_compra", "Preço Unit. Médio Ponderado",
                         644, 410, 300, 296,
                         "Preço médio ponderado: administrativa x judicial"),
        visual_categoria("por_tipoproduto", "clusteredBarChart", TABELA,
                         "tipo_produto", "Nº de Registros",
                         952, 410, 304, 296, "Registros por tipo de produto"),
    ]

    p2 = [
        visual_categoria("por_uf", "clusteredBarChart", TABELA, "uf",
                         "Valor Total Registrado", 16, 12, 412, 340,
                         "Valor registrado por UF (24 de 27 - faltam AM, AP e DF)"),
        visual_categoria("por_municipio", "clusteredBarChart", TABELA,
                         "municipio_instituicao", "Valor Total Registrado",
                         436, 12, 412, 340, "Top 10 municípios por valor", topn=10),
        visual_categoria("por_instituicao", "clusteredBarChart", TABELA,
                         "instituicao", "Valor Total Registrado",
                         856, 12, 400, 340,
                         "Top 10 instituições compradoras (nome + UF)", topn=10),
        visual_categoria("por_fornecedor", "clusteredBarChart", TABELA,
                         "fornecedor", "Valor Total Registrado",
                         16, 360, 412, 346, "Top 10 fornecedores por valor", topn=10),
        visual_categoria("por_fabricante", "clusteredBarChart", TABELA,
                         "fabricante", "Valor Total Registrado",
                         436, 360, 412, 346, "Top 10 fabricantes por valor", topn=10),
        visual_categoria("por_esfera", "clusteredBarChart", TABELA, "esfera",
                         "Valor Total Registrado", 856, 360, 400, 346,
                         "Valor por esfera de governo"),
    ]

    p3 = [
        visual_slicer("filtro_flag", TABELA, "flag_preco_atipico",
                      16, 12, 250, 110, "Registros de preço atípico"),
        visual_card("card_valor", "Valor Total Registrado", 278, 12, 230, 110),
        visual_card("card_pct", "% do Valor em Atípicos", 520, 12, 230, 110),
        visual_card("card_pmp_sem", "Preço Médio Pond. s/ Atípicos", 762, 12, 250, 110),
        visual_card("card_pmp", "Preço Unit. Médio Ponderado", 1024, 12, 232, 110),
        visual_categoria("uf_flag", "clusteredBarChart", TABELA, "uf",
                         "Valor Total Registrado", 16, 134, 500, 280,
                         "Ranking de UF - alterne o filtro e veja PR e SP trocarem"),
        visual_categoria("razao_por_principio", "clusteredBarChart", TABELA,
                         "principio_ativo", "Valor Registros Atípicos",
                         524, 134, 492, 280,
                         "Top 10 produtos por valor sinalizado", topn=10),
        visual_categoria("atipico_por_ano", "clusteredColumnChart", CAL, "Ano",
                         "Valor Registros Atípicos", 1024, 134, 232, 280,
                         "Valor atípico por ano", ordenar_desc=False),
        visual_tabela(
            "tabela_atipicos",
            [
                (TABELA, "ano_compra", False), (TABELA, "uf", False),
                (TABELA, "nome_instituicao", False), (TABELA, "principio_ativo", False),
                (TABELA, "unidade_fornecimento", False),
                (TABELA, "qtd_itens_comprados", False),
                (TABELA, "preco_unitario", False), (TABELA, "mediana_grupo", False),
                (TABELA, "razao_vs_mediana", False),
                (TABELA, "Valor Total Registrado", True),
            ],
            16, 422, 1240, 284,
            "Registros a verificar - filtre flag_preco_atipico = Verdadeiro",
        ),
    ]

    return [
        ("pagina1", "1. Visão Geral", p1),
        ("pagina2", "2. Geografia e Instituições", p2),
        ("pagina3", "3. Investigação de Preços", p3),
    ]


def escrever(caminho: Path, obj: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    destino = Path(sys.argv[1])
    csv_path = sys.argv[2]

    sm = destino / f"{NOME}.SemanticModel"
    rp = destino / f"{NOME}.Report"
    for pasta in (sm, rp):
        if pasta.exists():
            shutil.rmtree(pasta)

    escrever(destino / f"{NOME}.pbip", {
        "$schema": S_PBIP,
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NOME}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    })

    escrever(sm / "definition.pbism", {
        "$schema": S_PBISM, "version": "4.0", "settings": {},
    })
    escrever(sm / "model.bim", model_bim(csv_path))

    escrever(rp / "definition.pbir", {
        "$schema": S_PBIR,
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NOME}.SemanticModel"}},
    })

    d = rp / "definition"
    escrever(d / "version.json", {"$schema": S_VER, "version": "1.0.0"})
    escrever(d / "report.json", {
        "$schema": S_REPORT,
        "layoutOptimization": "None",
        "themeCollection": {
            "baseTheme": {
                "name": "CY24SU06",
                "reportVersionAtImport": "5.55",
                "type": "SharedResources",
            }
        },
    })

    pgs = paginas()
    escrever(d / "pages" / "pages.json", {
        "$schema": S_PAGES,
        "pageOrder": [n for n, _, _ in pgs],
        "activePageName": pgs[0][0],
    })

    total_visuais = 0
    for nome, titulo_pag, visuais in pgs:
        base = d / "pages" / nome
        escrever(base / "page.json", {
            "$schema": S_PAGE,
            "name": nome,
            "displayName": titulo_pag,
            "displayOption": "FitToPage",
            "width": 1280,
            "height": 720,
        })
        for v in visuais:
            escrever(base / "visuals" / v["name"] / "visual.json", v)
            total_visuais += 1

    print(f"Projeto gerado em {destino}")
    print(f"  {NOME}.pbip")
    print(f"  {NOME}.SemanticModel/model.bim  "
          f"({len(COLUNAS)} colunas, {len(MEDIDAS)} medidas, 2 tabelas)")
    print(f"  {NOME}.Report/  ({len(pgs)} páginas, {total_visuais} visuais)")


if __name__ == "__main__":
    main()
