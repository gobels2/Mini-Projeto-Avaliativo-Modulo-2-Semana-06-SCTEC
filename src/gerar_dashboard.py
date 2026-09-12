"""Gera o relatório PBIR redesenhado: tema escuro, trilho de navegação e visuais variados.

Substitui a pasta `definition/` do relatório. O modelo semântico (model.bim)
não é tocado: ele já está correto e carregado.

As três páginas compartilham o mesmo trilho de navegação à esquerda, com botões
de navegação nativos. O resultado se opera como um painel único com abas — que
é, aliás, como o próprio exemplo do ZoomCharts é montado: várias páginas com
uma navegação comum, não uma página só.

Uso:
    python src/gerar_dashboard.py
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REPORT = RAIZ / "dashboard" / "BPS_2020_2026.Report"
DEF = REPORT / "definition"
TABELA = "fBPS"
CAL = "dCalendario"

S_VER = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json"
S_REPORT = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json"
S_PAGES = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json"
S_PAGE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json"
S_VISUAL = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.2.0/schema.json"

# O trilho passou de 168 para 226px; o conteudo mantem a mesma largura, entao
# a tela precisa crescer os mesmos 58px, senao o ultimo cartao de cada linha
# fica cortado na borda direita.
L, A = 1660, 900          # canvas widescreen
RAIL_W = 226              # trilho de navegação — largo o bastante para o título
                          # não sair cortado em "BPS 2020–"

# ---- paleta escura -------------------------------------------------------
FUNDO = "#0F1420"
RAIL_BG = "#161D2E"
CARTAO = "#1A2233"
BORDA = "#2A3550"
TINTA = "#E9EDF6"
TINTA2 = "#8E9AB5"
AZUL = "#3E9BFF"
AZUL_ESC = "#14406F"
TEAL = "#00D6A4"
TEAL_ESC = "#0B5946"
VERMELHO = "#FF5C5C"
VERMELHO_ESC = "#6E1B1B"
AMARELO = "#FFC24B"


def lit(v: str) -> dict:
    return {"expr": {"Literal": {"Value": v}}}


def txt(v: str) -> dict:
    return lit(f"'{v}'")


def num(v) -> dict:
    return lit(f"{v}D")


def bol(v: bool) -> dict:
    return lit("true" if v else "false")


def cor(h: str) -> dict:
    return {"solid": {"color": lit(f"'{h}'")}}


def grad(medida: str, c0: str, c1: str) -> dict:
    return {"solid": {"color": {"expr": {"FillRule": {
        "Input": {"Measure": {"Expression": {"SourceRef": {"Entity": TABELA}},
                              "Property": medida}},
        "FillRule": {"linearGradient2": {
            "min": {"color": {"Literal": {"Value": f"'{c0}'"}}},
            "max": {"color": {"Literal": {"Value": f"'{c1}'"}}}}}}}}}}


def o(**p) -> list:
    return [{"properties": p}]


def o_estado(mostrar: bool, **p) -> list:
    """Objeto com estado nomeado.

    Botões e formas separam o `show` (bloco sem seletor) do conteúdo, que vai
    num bloco com `selector: {"id": "default"}`. Sem o seletor o Power BI
    aceita o JSON e ignora a formatação — foi por isso que os botões saíram
    como retângulos brancos sem texto.
    """
    return [
        {"properties": {"show": bol(mostrar)}},
        {"properties": p, "selector": {"id": "default"}},
    ]


def med(nome: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": TABELA}}, "Property": nome}}


def col(tab: str, nome: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": tab}}, "Property": nome}}


def proj(campo: dict, ref: str) -> dict:
    return {"field": campo, "queryRef": ref, "active": True}


def moldura(titulo: str | None, cor_titulo: str = TINTA) -> dict:
    m = {
        "background": o(show=bol(True), color=cor(CARTAO), transparency=num(0)),
        "border": o(show=bol(True), color=cor(BORDA), radius=num(10)),
        "dropShadow": o(show=bol(False)),
        "padding": o(top=num(6), bottom=num(6), left=num(8), right=num(8)),
    }
    if titulo:
        m["title"] = o(show=bol(True), text=txt(titulo), fontSize=num(13),
                       bold=bol(True), fontColor=cor(cor_titulo),
                       background=cor(CARTAO), alignment=txt("left"),
                       titleWrap=bol(True))
    return m


def eixos(rotulos=False, rot_cor=TINTA2) -> dict:
    return {
        "categoryAxis": o(show=bol(True), showAxisTitle=bol(False), fontSize=num(11),
                          labelColor=cor(TINTA2),
                          # Sem isto o Power BI reserva so 25% da largura para
                          # os rotulos e quatro barras viram "SECRETARIA ...".
                          maxMarginFactor=num(45)),
        "valueAxis": o(show=bol(True), showAxisTitle=bol(False), fontSize=num(11),
                       labelColor=cor(TINTA2), gridlineShow=bol(True),
                       gridlineColor=cor(BORDA), gridlineThickness=num(1)),
        "labels": o(show=bol(rotulos), fontSize=num(11), color=cor(rot_cor)),
        "legend": o(show=bol(False), showTitle=bol(False)),
    }


def visual(nome, tipo, x, y, w, h, roles, titulo=None, objs=None,
           cor_titulo=TINTA, sort_med=None, topn=None, cat=None) -> dict:
    qs = {papel: {"projections": ps} for papel, ps in roles.items()}
    v = {
        "$schema": S_VISUAL,
        "name": nome,
        "position": {"x": x, "y": y, "z": 0, "width": w, "height": h},
        "visual": {
            "visualType": tipo,
            "query": {"queryState": qs},
            "objects": objs or {},
            "visualContainerObjects": moldura(titulo, cor_titulo),
        },
    }
    if sort_med:
        v["visual"]["query"]["sortDefinition"] = {
            "sort": [{"field": med(sort_med), "direction": "Descending"}],
            "isDefaultSort": True}
    if topn and cat:
        tab, coluna = cat
        v["filterConfig"] = {"filters": [{
            "name": f"topn_{nome}",
            "displayName": f"Top {topn}",
            "type": "TopN",
            "howCreated": "User",
            "field": col(tab, coluna),
            "filter": {
                "Version": 2,
                "From": [{"Name": "t", "Entity": tab, "Type": 0},
                         {"Name": "top", "Type": 2, "Expression": {"Subquery": {"Query": {
                             "Version": 2,
                             "From": [{"Name": "s", "Entity": tab, "Type": 0},
                                      {"Name": "m", "Entity": TABELA, "Type": 0}],
                             "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "s"}},
                                                    "Property": coluna},
                                         "Name": f"{tab}.{coluna}"}],
                             "OrderBy": [{"Direction": 2, "Expression": {"Measure": {
                                 "Expression": {"SourceRef": {"Source": "m"}},
                                 "Property": sort_med or "Valor Total Registrado"}}}],
                             "Top": topn}}}}],
                "Where": [{"Condition": {"In": {
                    "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}},
                                                "Property": coluna}}],
                    "Table": {"SourceRef": {"Source": "top"}}}}}]}}]}
    return v


def cartao(nome, medida, x, y, w, h, acento=AZUL) -> dict:
    return visual(
        nome, "card", x, y, w, h,
        {"Values": [proj(med(medida), f"{TABELA}.{medida}")]},
        titulo=medida,
        cor_titulo=TINTA2,
        objs={
            # Sem labelPrecision: ele sobrepõe o formatString da medida e
            # transformava R$ 1,3751 em "R$ 1".
            "labels": o(fontSize=num(30), color=cor(acento)),
            "categoryLabels": o(show=bol(False)),
            "wordWrap": o(show=bol(False)),
        },
    )


def botao(nome, rotulo, destino, indice, ativo: bool) -> dict:
    """Botão do trilho: navegação nativa entre páginas."""
    y = 158 + indice * 60
    return {
        "$schema": S_VISUAL,
        "name": nome,
        "position": {"x": 16, "y": y, "z": 10, "width": RAIL_W - 32, "height": 48},
        "visual": {
            "visualType": "actionButton",
            "objects": {
                "text": o_estado(True, text=txt(rotulo),
                                 fontColor=cor(TINTA if ativo else TINTA2),
                                 fontSize=num(15), bold=bol(ativo),
                                 horizontalAlignment=txt("left"),
                                 leftMargin=num(16)),
                "fill": o_estado(True,
                                 fillColor=cor(AZUL if ativo else CARTAO),
                                 transparency=num(0)),
                "icon": o_estado(False, shapeType=txt("blank")),
                "outline": o(show=bol(False)),
            },
            "visualContainerObjects": {
                "visualLink": o(show=bol(True), type=txt("PageNavigation"),
                                navigationSection=txt(destino)),
                "border": o(show=bol(False)),
                "dropShadow": o(show=bol(False)),
            },
        },
    }


def rotulo_texto(nome, texto, x, y, w, h, tamanho=14, cor_txt=TINTA, negrito=True) -> dict:
    return {
        "$schema": S_VISUAL,
        "name": nome,
        "position": {"x": x, "y": y, "z": 10, "width": w, "height": h},
        "visual": {
            "visualType": "textbox",
            "objects": {"general": [{"properties": {"paragraphs": [{
                "textRuns": [{"value": texto, "textStyle": {
                    "fontSize": f"{tamanho}pt", "color": cor_txt,
                    "fontWeight": "bold" if negrito else "normal"}}]}]}}]},
            "visualContainerObjects": {
                "background": o(show=bol(False)),
                "border": o(show=bol(False)),
            },
        },
    }


KPIS = [("Valor Total Registrado", AZUL), ("Qtd Total de Itens", TEAL),
        ("Nº de Registros", TEAL), ("Instituições Compradoras", AZUL),
        ("Fornecedores", AZUL), ("Preço Unit. Médio Ponderado", AMARELO)]

PAGINAS = [("pagina1", "Visão Geral"), ("pagina2", "Geografia"),
           ("pagina3", "Investigação")]


def painel_trilho() -> dict:
    """Retângulo de fundo do trilho — dá a ele uma superfície própria."""
    return {
        "$schema": S_VISUAL,
        "name": "rail_bg",
        "position": {"x": 0, "y": 0, "z": 0, "width": RAIL_W, "height": A},
        "visual": {
            # basicShape, com shapeType em "general" — o tipo "shape" com
            # "tileShape" é aceito pelo schema mas ignorado na renderização, e
            # o retângulo sai com o azul padrão do tema.
            "visualType": "basicShape",
            "objects": {
                "general": o(shapeType=txt("rectangle")),
                "fill": o(show=bol(True), fillColor=cor(RAIL_BG),
                          transparency=num(0)),
                "line": o(transparency=num(100)),
            },
            "visualContainerObjects": {
                "background": o(show=bol(False)),
                "border": o(show=bol(False)),
            },
        },
    }


def trilho(indice_ativo: int) -> list:
    vs = [painel_trilho(),
          rotulo_texto("marca", "BPS 2020–2026", 16, 26, RAIL_W - 32, 46, 19),
          rotulo_texto("marca2", "Banco de Preços em Saúde", 14, 68, RAIL_W - 32, 52, 12,
                       TINTA2, False)]
    for i, (pid, rot) in enumerate(PAGINAS):
        vs.append(botao(f"nav_{pid}", rot, pid, i, i == indice_ativo))
    return vs


def faixa_kpis(prefixo: str) -> list:
    x0, larg, gap = RAIL_W + 16, 218, 10
    return [cartao(f"{prefixo}_kpi{i+1}", m, x0 + i * (larg + gap), 84, larg, 82, c)
            for i, (m, c) in enumerate(KPIS)]


def pagina1() -> list:
    x0 = RAIL_W + 16
    vs = trilho(0) + faixa_kpis("p1")
    vs.append(rotulo_texto("t1", "Visão Geral", x0, 24, 700, 46, 24))
    vs += [
        visual("valor_ano_modalidade", "ribbonChart", x0, 182, 700, 300,
               {"Category": [proj(col(CAL, "Ano"), f"{CAL}.Ano")],
                "Series": [proj(col(TABELA, "modalidade_compra"), f"{TABELA}.modalidade_compra")],
                "Y": [proj(med("Valor Total Registrado"), f"{TABELA}.Valor Total Registrado")]},
               "Valor por ano e modalidade de compra",
               {**eixos(), "legend": o(show=bol(True), position=txt("Bottom"),
                                       fontSize=num(11), labelColor=cor(TINTA2),
                                       showTitle=bol(False))}),
        visual("preco_ano", "areaChart", x0 + 712, 182, 684, 300,
               {"Category": [proj(col(CAL, "Ano"), f"{CAL}.Ano")],
                "Y": [proj(med("Preço Unit. Médio Ponderado"), f"{TABELA}.Preço Unit. Médio Ponderado")]},
               "Preço unitário médio ponderado por ano",
               {**eixos(True, AMARELO), "dataPoint": o(fill=cor(AMARELO)),
                "fillPoint": o(show=bol(True))}),
        visual("treemap_produtos", "treemap", x0, 494, 700, 322,
               {"Group": [proj(col(TABELA, "principio_ativo"), f"{TABELA}.principio_ativo")],
                "Values": [proj(med("Valor Total Registrado"), f"{TABELA}.Valor Total Registrado")]},
               "Top 12 princípios ativos e produtos por valor",
               {"dataPoint": o(fill=grad("Valor Total Registrado", AZUL_ESC, AZUL)),
                "labels": o(show=bol(True), fontSize=num(11), color=cor(TINTA)),
                "legend": o(show=bol(False))},
               sort_med="Valor Total Registrado", topn=12,
               cat=(TABELA, "principio_ativo")),
        visual("donut_tipo", "donutChart", x0 + 712, 494, 336, 322,
               {"Category": [proj(col(TABELA, "tipo_produto"), f"{TABELA}.tipo_produto")],
                "Y": [proj(med("Nº de Registros"), f"{TABELA}.Nº de Registros")]},
               "Registros por tipo de produto",
               {"legend": o(show=bol(True), position=txt("Bottom"), fontSize=num(11),
                            labelColor=cor(TINTA2), showTitle=bol(False)),
                "labels": o(show=bol(True), fontSize=num(11), color=cor(TINTA)),
                "slices": o(innerRadiusRatio=num(60))}),
        visual("barras_tipocompra", "clusteredBarChart", x0 + 1060, 494, 336, 322,
               {"Category": [proj(col(TABELA, "tipo_compra"), f"{TABELA}.tipo_compra")],
                "Y": [proj(med("Preço Unit. Médio Ponderado"), f"{TABELA}.Preço Unit. Médio Ponderado")]},
               "Preço médio: administrativa × judicial",
               {**eixos(True), "dataPoint": o(fill=grad("Preço Unit. Médio Ponderado",
                                                        TEAL_ESC, TEAL))}),
    ]
    return vs


def pagina2() -> list:
    x0 = RAIL_W + 16
    vs = trilho(1) + faixa_kpis("p2")
    vs.append(rotulo_texto("t2", "Geografia e Instituições", x0, 24, 700, 46, 24))
    vs += [
        visual("arvore", "decompositionTreeVisual", x0, 182, 700, 372,
               # Os papéis da árvore são "Analyze" e "ExplainBy" — com
               # "Analysis"/"Group" o visual carrega mas exibe
               # "No field to analyze".
               {"Analyze": [proj(med("Valor Total Registrado"), f"{TABELA}.Valor Total Registrado")],
                "ExplainBy": [proj(col(TABELA, "regiao"), f"{TABELA}.regiao"),
                              proj(col(TABELA, "uf"), f"{TABELA}.uf"),
                              proj(col(TABELA, "instituicao"), f"{TABELA}.instituicao")]},
               "Clique para abrir região, UF e instituição",
               {}),
        visual("barras_uf", "clusteredBarChart", x0 + 712, 182, 342, 372,
               {"Category": [proj(col(TABELA, "uf"), f"{TABELA}.uf")],
                "Y": [proj(med("Valor Total Registrado"), f"{TABELA}.Valor Total Registrado")]},
               "Valor por UF — 24 de 27, sem AM, AP e DF",
               {**eixos(), "dataPoint": o(fill=grad("Valor Total Registrado", AZUL_ESC, AZUL))},
               sort_med="Valor Total Registrado"),
        visual("donut_esfera", "donutChart", x0 + 1066, 182, 330, 372,
               {"Category": [proj(col(TABELA, "esfera"), f"{TABELA}.esfera")],
                "Y": [proj(med("Valor Total Registrado"), f"{TABELA}.Valor Total Registrado")]},
               "Valor por esfera de governo",
               {"legend": o(show=bol(True), position=txt("Bottom"), fontSize=num(11),
                            labelColor=cor(TINTA2), showTitle=bol(False)),
                "labels": o(show=bol(True), fontSize=num(11), color=cor(TINTA)),
                "slices": o(innerRadiusRatio=num(60))}),
        visual("barras_municipio", "clusteredBarChart", x0, 566, 460, 268,
               {"Category": [proj(col(TABELA, "municipio_instituicao"), f"{TABELA}.municipio_instituicao")],
                "Y": [proj(med("Valor Total Registrado"), f"{TABELA}.Valor Total Registrado")]},
               "Top 10 municípios",
               {**eixos(), "dataPoint": o(fill=grad("Valor Total Registrado", AZUL_ESC, AZUL))},
               sort_med="Valor Total Registrado", topn=10,
               cat=(TABELA, "municipio_instituicao")),
        visual("barras_instituicao", "clusteredBarChart", x0 + 472, 566, 460, 268,
               {"Category": [proj(col(TABELA, "instituicao"), f"{TABELA}.instituicao")],
                "Y": [proj(med("Valor Total Registrado"), f"{TABELA}.Valor Total Registrado")]},
               "Top 10 instituições compradoras",
               {**eixos(), "dataPoint": o(fill=grad("Valor Total Registrado", AZUL_ESC, AZUL))},
               sort_med="Valor Total Registrado", topn=10, cat=(TABELA, "instituicao")),
        visual("barras_fornecedor", "clusteredBarChart", x0 + 944, 566, 452, 268,
               {"Category": [proj(col(TABELA, "fornecedor"), f"{TABELA}.fornecedor")],
                "Y": [proj(med("Valor Total Registrado"), f"{TABELA}.Valor Total Registrado")]},
               "Top 10 fornecedores",
               {**eixos(), "dataPoint": o(fill=grad("Valor Total Registrado", TEAL_ESC, TEAL))},
               sort_med="Valor Total Registrado", topn=10, cat=(TABELA, "fornecedor")),
    ]
    return vs


def pagina3() -> list:
    x0 = RAIL_W + 16
    vs = trilho(2) + faixa_kpis("p3")
    vs.append(rotulo_texto("t3", "Investigação de Preços", x0, 24, 700, 46, 24))
    vs += [
        visual("slicer_flag", "slicer", x0, 182, 250, 150,
               {"Values": [proj(col(TABELA, "flag_preco_atipico"), f"{TABELA}.flag_preco_atipico")]},
               "Filtrar registros atípicos",
               {"items": o(fontColor=cor(TINTA), fontSize=num(12)),
                "header": o(show=bol(False))}),
        visual("cascata", "waterfallChart", x0 + 262, 182, 700, 360,
               {"Category": [proj(col(CAL, "Ano"), f"{CAL}.Ano")],
                "Y": [proj(med("Valor Registros Atípicos"), f"{TABELA}.Valor Registros Atípicos")]},
               "Contribuição do valor sinalizado, ano a ano",
               {**eixos(True, VERMELHO),
                "sentimentColors": o(increaseFill=cor(VERMELHO), decreaseFill=cor(TEAL),
                                     totalFill=cor(AZUL))}),
        visual("dispersao", "scatterChart", x0 + 974, 182, 422, 360,
               {"Category": [proj(col(TABELA, "principio_ativo"), f"{TABELA}.principio_ativo")],
                "X": [proj(med("Qtd Total de Itens"), f"{TABELA}.Qtd Total de Itens")],
                "Y": [proj(med("Preço Unit. Médio Ponderado"), f"{TABELA}.Preço Unit. Médio Ponderado")],
                "Size": [proj(med("Valor Total Registrado"), f"{TABELA}.Valor Total Registrado")]},
               "Quantidade × preço unitário, bolha = valor",
               {**eixos(), "dataPoint": o(fill=cor(VERMELHO)),
                "fillPoint": o(show=bol(True))},
               sort_med="Valor Total Registrado", topn=40,
               cat=(TABELA, "principio_ativo")),
        visual("barras_atipico_produto", "clusteredBarChart", x0, 344, 250, 198,
               {"Category": [proj(col(TABELA, "uf"), f"{TABELA}.uf")],
                "Y": [proj(med("Valor Registros Atípicos"), f"{TABELA}.Valor Registros Atípicos")]},
               "UF por valor sinalizado",
               {**eixos(), "dataPoint": o(fill=grad("Valor Registros Atípicos",
                                                    VERMELHO_ESC, VERMELHO))},
               sort_med="Valor Registros Atípicos"),
        visual("tabela", "tableEx", x0, 556, 1396, 280,
               {"Values": [
                   proj(col(TABELA, "ano_compra"), f"{TABELA}.ano_compra"),
                   proj(col(TABELA, "uf"), f"{TABELA}.uf"),
                   proj(col(TABELA, "instituicao"), f"{TABELA}.instituicao"),
                   proj(col(TABELA, "principio_ativo"), f"{TABELA}.principio_ativo"),
                   proj(col(TABELA, "unidade_fornecimento"), f"{TABELA}.unidade_fornecimento"),
                   proj(col(TABELA, "qtd_itens_comprados"), f"{TABELA}.qtd_itens_comprados"),
                   proj(col(TABELA, "preco_unitario"), f"{TABELA}.preco_unitario"),
                   proj(col(TABELA, "mediana_grupo"), f"{TABELA}.mediana_grupo"),
                   proj(col(TABELA, "razao_vs_mediana"), f"{TABELA}.razao_vs_mediana"),
                   proj(med("Valor Total Registrado"), f"{TABELA}.Valor Total Registrado")]},
               "Registros a verificar — maiores valores da base",
               # A tabela usa fontColorPrimary/backColorPrimary (e o par
               # Secondary das linhas alternadas). Com fontColor/backColor o
               # JSON passa mas as linhas ficam brancas sobre o tema escuro.
               {"grid": o(gridVertical=bol(False), gridHorizontalColor=cor(BORDA),
                          rowPadding=num(4)),
                "columnHeaders": o(fontSize=num(11), bold=bol(True),
                                   fontColor=cor(TINTA), backColor=cor(RAIL_BG)),
                "values": o(fontSize=num(11),
                            fontColorPrimary=cor(TINTA), backColorPrimary=cor(CARTAO),
                            fontColorSecondary=cor(TINTA), backColorSecondary=cor(RAIL_BG))},
               sort_med="Valor Total Registrado"),
    ]
    return vs


NOME_TEMA = "BPS_Escuro"


def tema() -> dict:
    """Tema personalizado do relatório.

    Existe por um motivo concreto: a árvore de decomposição não expõe objetos
    de formatação de fonte, então o texto dos nós (os valores em cinza escuro)
    só muda pelas classes de texto do tema. O `label` abaixo é o que deixa
    aquele texto maior e claro.

    O JSON de tema usa valores crus — nada de `{"expr": {"Literal": ...}}`,
    que é a sintaxe do visual.json.
    """
    return {
        "name": NOME_TEMA,
        "dataColors": [AZUL, TEAL, AMARELO, VERMELHO, "#9B7BFF", "#38C6E0",
                       "#FF9F45", "#7CD992"],
        "background": FUNDO,
        "foreground": TINTA,
        "tableAccent": AZUL,
        "textClasses": {
            "label": {"fontSize": 12, "color": TINTA},
            "callout": {"fontSize": 30, "color": AZUL},
            "title": {"fontSize": 13, "color": TINTA},
            "header": {"fontSize": 13, "color": TINTA},
            "largeTitle": {"fontSize": 16, "color": TINTA},
        },
        "visualStyles": {
            "page": {"*": {
                "background": [{"color": {"solid": {"color": FUNDO}}, "transparency": 0}],
                "outspace": [{"color": {"solid": {"color": FUNDO}}}],
            }},
            "*": {"*": {
                "background": [{"color": {"solid": {"color": CARTAO}}, "transparency": 0}],
                "border": [{"color": {"solid": {"color": BORDA}}, "radius": 10}],
                "title": [{"fontColor": {"solid": {"color": TINTA}}, "fontSize": 13,
                           "background": {"solid": {"color": CARTAO}}}],
                "labels": [{"color": {"solid": {"color": TINTA}}, "fontSize": 11}],
                "categoryAxis": [{"labelColor": {"solid": {"color": TINTA2}},
                                  "fontSize": 11, "showAxisTitle": False}],
                "valueAxis": [{"labelColor": {"solid": {"color": TINTA2}},
                               "fontSize": 11, "showAxisTitle": False,
                               "gridlineColor": {"solid": {"color": BORDA}}}],
                "legend": [{"labelColor": {"solid": {"color": TINTA2}}, "fontSize": 11}],
            }},
        },
    }


# Os visuais com filtro Top N não conseguem realçar a árvore: o Power BI avisa
# que "Top N cross highlighting isn't supported". Passar a interação para
# DataFilter resolve — o clique continua filtrando a árvore, só não tenta
# realçar.
INTERACOES_P2 = [
    {"source": s, "target": "arvore", "type": "DataFilter"}
    for s in ("barras_municipio", "barras_instituicao", "barras_fornecedor")
]


def escrever(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    if DEF.exists():
        shutil.rmtree(DEF)

    escrever(DEF / "version.json", {"$schema": S_VER, "version": "2.0.0"})
    escrever(REPORT / "StaticResources" / "RegisteredResources" / f"{NOME_TEMA}.json",
             tema())
    escrever(DEF / "report.json", {
        "$schema": S_REPORT,
        "themeCollection": {
            "baseTheme": {
                "name": "CY19SU12",
                "reportVersionAtImport": {"visual": "1.8.46", "report": "2.0.46",
                                          "page": "1.3.46"},
                "type": "SharedResources"},
            "customTheme": {
                "name": NOME_TEMA,
                "reportVersionAtImport": {"visual": "1.8.46", "report": "2.0.46",
                                          "page": "1.3.46"},
                "type": "RegisteredResources"},
        },
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": "CY19SU12", "path": "BaseThemes/CY19SU12.json",
                        "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": NOME_TEMA, "path": f"{NOME_TEMA}.json",
                        "type": "CustomTheme"}]},
        ],
    })
    escrever(DEF / "pages" / "pages.json", {
        "$schema": S_PAGES,
        "pageOrder": [p for p, _ in PAGINAS],
        "activePageName": PAGINAS[0][0]})

    total = 0
    for (pid, nome), construtor in zip(PAGINAS, (pagina1, pagina2, pagina3)):
        base = DEF / "pages" / pid
        pg = {
            "$schema": S_PAGE, "name": pid, "displayName": nome,
            "displayOption": "FitToPage", "width": L, "height": A,
            "objects": {
                "background": o(color=cor(FUNDO), transparency=num(0)),
                "outspace": o(color=cor(FUNDO), transparency=num(0)),
            }}
        if pid == "pagina2":
            pg["visualInteractions"] = INTERACOES_P2
        escrever(base / "page.json", pg)
        for v in construtor():
            escrever(base / "visuals" / v["name"] / "visual.json", v)
            total += 1

    conferir_geometria()
    print(f"canvas {L}x{A} escuro, {len(PAGINAS)} páginas, {total} visuais")


def conferir_geometria() -> None:
    """Falha se algum visual passar da borda da tela.

    Alargar o trilho sem encolher o conteúdo empurrou tudo para fora da tela
    e cortou o último cartão de cada linha nas três páginas. O erro só
    apareceu nas capturas; esta checagem o pega antes.
    """
    estouros = []
    for f in (DEF / "pages").rglob("visual.json"):
        p = json.loads(f.read_text(encoding="utf-8"))["position"]
        if p["x"] + p["width"] > L or p["y"] + p["height"] > A:
            estouros.append(
                f'{f.parent.name}: termina em '
                f'({p["x"] + p["width"]}, {p["y"] + p["height"]}) '
                f'numa tela de {L}x{A}')
    if estouros:
        raise SystemExit("Visuais fora da tela:\n  - " + "\n  - ".join(estouros))


if __name__ == "__main__":
    main()
