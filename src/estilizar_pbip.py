"""Aplica identidade visual ao relatório PBIR do projeto.

Edita os arquivos que o Power BI Desktop já gravou, em vez de regerá-los: ao
abrir o projeto o Desktop normalizou tudo para a revisão 2.12.0 de schema e
acrescentou propriedades próprias. Reescrever por cima jogaria isso fora.

Paleta: uma rampa sequencial azul para magnitude de valor, vermelho reservado
para registro sinalizado e um verde-azulado para contagem de registros. Azul e
verde-azulado puxam para o tema de saúde e gestão pública que o enunciado pede;
o vermelho nunca é decorativo — só aparece onde o dado é atípico.

Uso:
    python src/estilizar_pbip.py
"""
from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINAS = RAIZ / "dashboard" / "BPS_2020_2026.Report" / "definition" / "pages"
TABELA = "fBPS"

# Rampa sequencial azul (claro -> escuro) para magnitude.
GRAD_MIN = "#CDE2FB"
GRAD_MAX = "#104281"
# Rampa vermelha, exclusiva do que está sinalizado como atípico.
GRAD_ALERTA_MIN = "#F6D6D6"
GRAD_ALERTA_MAX = "#8E2020"
# Verde-azulado para contagem de registros, que não é dinheiro.
GRAD_TEAL_MIN = "#CFF0E4"
GRAD_TEAL_MAX = "#0C6B4C"

TINTA = "#1A1A19"
TINTA_SUAVE = "#5C5B57"
GRADE = "#E8E7E1"
FUNDO_CARTAO = "#FFFFFF"
BORDA = "#E1E0D9"


def lit(valor: str) -> dict:
    """Literal do Power BI: texto vai entre aspas simples, número leva D."""
    return {"expr": {"Literal": {"Value": valor}}}


def texto(v: str) -> dict:
    return lit(f"'{v}'")


def numero(v) -> dict:
    return lit(f"{v}D")


def booleano(v: bool) -> dict:
    return lit("true" if v else "false")


def cor(hexa: str) -> dict:
    return {"solid": {"color": lit(f"'{hexa}'")}}


def gradiente(medida: str, c_min: str, c_max: str) -> dict:
    """Preenchimento condicional: a cor acompanha o valor da medida."""
    return {
        "solid": {
            "color": {
                "expr": {
                    "FillRule": {
                        "Input": {
                            "Measure": {
                                "Expression": {"SourceRef": {"Entity": TABELA}},
                                "Property": medida,
                            }
                        },
                        "FillRule": {
                            "linearGradient2": {
                                "min": {"color": {"Literal": {"Value": f"'{c_min}'"}}},
                                "max": {"color": {"Literal": {"Value": f"'{c_max}'"}}},
                            }
                        },
                    }
                }
            }
        }
    }


def obj(**props) -> list:
    """Um objeto de formatação do Power BI é sempre uma lista de blocos."""
    return [{"properties": props}]


def moldura(titulo: str | None = None, destaque: bool = False) -> dict:
    """Título, fundo e borda — a moldura que faz os cartões lerem como um só sistema."""
    o = {
        "background": obj(show=booleano(True), color=cor(FUNDO_CARTAO), transparency=numero(0)),
        "border": obj(show=booleano(True), color=cor(BORDA), radius=numero(6)),
        "dropShadow": obj(show=booleano(False)),
    }
    if titulo is not None:
        o["title"] = obj(
            show=booleano(True),
            text=texto(titulo),
            fontSize=numero(11),
            bold=booleano(True),
            fontColor=cor("#B22222" if destaque else TINTA),
            titleWrap=booleano(True),
        )
    return o


def eixos(mostrar_rotulos: bool = True) -> dict:
    """Eixos discretos: sem títulos redundantes, grade em fio de cabelo."""
    return {
        "categoryAxis": obj(
            show=booleano(True), showAxisTitle=booleano(False),
            fontSize=numero(9), labelColor=cor(TINTA_SUAVE),
        ),
        "valueAxis": obj(
            show=booleano(True), showAxisTitle=booleano(False),
            fontSize=numero(9), labelColor=cor(TINTA_SUAVE),
            gridlineShow=booleano(True), gridlineColor=cor(GRADE),
            gridlineThickness=numero(1),
        ),
        "labels": obj(
            show=booleano(mostrar_rotulos), fontSize=numero(9),
            color=cor(TINTA_SUAVE),
        ),
    }


# visual -> (tipo novo ou None, medida do gradiente, rampa, rótulos de dados)
ESTILO = {
    # ---- página 1
    "kpi1": ("card", None, None, False),
    "kpi2": ("card", None, None, False),
    "kpi3": ("card", None, None, False),
    "kpi4": ("card", None, None, False),
    "kpi5": ("card", None, None, False),
    "kpi6": ("card", None, None, False),
    "valor_por_ano": (None, "Valor Total Registrado", "azul", True),
    "preco_por_ano": ("areaChart", None, "azul", False),
    "por_modalidade": (None, "Valor Total Registrado", "azul", False),
    "por_principio": ("treemap", "Valor Total Registrado", "azul", True),
    "por_tipocompra": (None, "Preço Unit. Médio Ponderado", "azul", True),
    "por_tipoproduto": (None, "Nº de Registros", "teal", True),
    # ---- página 2
    "por_uf": (None, "Valor Total Registrado", "azul", False),
    "por_municipio": (None, "Valor Total Registrado", "azul", False),
    "por_instituicao": (None, "Valor Total Registrado", "azul", False),
    "por_fornecedor": (None, "Valor Total Registrado", "azul", False),
    "por_fabricante": (None, "Valor Total Registrado", "azul", False),
    "por_esfera": ("donutChart", None, "azul", True),
    # ---- página 3
    "card_valor": ("card", None, None, False),
    "card_pct": ("card", None, None, False),
    "card_pmp_sem": ("card", None, None, False),
    "card_pmp": ("card", None, None, False),
    "uf_flag": (None, "Valor Total Registrado", "azul", False),
    "razao_por_principio": (None, "Valor Registros Atípicos", "alerta", True),
    "atipico_por_ano": (None, "Valor Registros Atípicos", "alerta", True),
}

RAMPAS = {
    "azul": (GRAD_MIN, GRAD_MAX),
    "alerta": (GRAD_ALERTA_MIN, GRAD_ALERTA_MAX),
    "teal": (GRAD_TEAL_MIN, GRAD_TEAL_MAX),
}

# Títulos finais, já sem as instruções de montagem que estavam nos provisórios.
TITULOS = {
    "valor_por_ano": "Valor registrado por ano",
    "preco_por_ano": "Preço unitário médio ponderado por ano",
    "por_modalidade": "Valor por modalidade de compra",
    "por_principio": "Top 10 princípios ativos e produtos por valor",
    "por_tipocompra": "Preço médio ponderado: administrativa × judicial",
    "por_tipoproduto": "Registros por tipo de produto",
    "por_uf": "Valor registrado por UF — 24 de 27, sem AM, AP e DF",
    "por_municipio": "Top 10 municípios por valor",
    "por_instituicao": "Top 10 instituições compradoras",
    "por_fornecedor": "Top 10 fornecedores",
    "por_fabricante": "Top 10 fabricantes",
    "por_esfera": "Valor por esfera de governo",
    "uf_flag": "Ranking de UF — alterne o filtro e veja PR e SP trocarem",
    "razao_por_principio": "Top 10 produtos por valor sinalizado",
    "atipico_por_ano": "Valor sinalizado por ano",
    "tabela_atipicos": "Registros a verificar — maiores valores da base",
    "filtro_flag": "Registros de preço atípico",
}

DESTAQUE = {"razao_por_principio", "atipico_por_ano", "uf_flag"}


def estilizar_cartao(v: dict) -> None:
    """Cartão de KPI: número grande sem estourar e sem rótulo duplicado.

    O rótulo de categoria é desligado porque o título do contêiner já diz o
    nome da medida — mantê-lo cortava a frase ao pé do cartão.
    """
    v["visual"]["objects"] = {
        "labels": obj(fontSize=numero(20), color=cor(TINTA), labelPrecision=numero(0)),
        "categoryLabels": obj(show=booleano(False)),
        "wordWrap": obj(show=booleano(True)),
    }


def ordenar_tabela(visual: dict) -> None:
    """Ordena a tabela pelo valor, decrescente.

    Sem isto a tabela abre em 2020/AC com compras de R$ 3.400, e o registro de
    R$ 22,8 bilhões — que é a razão de a página existir — fica soterrado.
    """
    visual.setdefault("query", {})["sortDefinition"] = {
        "sort": [
            {
                "field": {
                    "Measure": {
                        "Expression": {"SourceRef": {"Entity": TABELA}},
                        "Property": "Valor Total Registrado",
                    }
                },
                "direction": "Descending",
            }
        ],
        "isDefaultSort": True,
    }


def main() -> None:
    alterados = tipos_trocados = 0
    for caminho in sorted(PAGINAS.rglob("visual.json")):
        nome = caminho.parent.name
        doc = json.loads(caminho.read_text(encoding="utf-8"))
        visual = doc.get("visual")
        if not visual:
            continue

        if nome in TITULOS:
            doc["visual"].setdefault("visualContainerObjects", {})
            doc["visual"]["visualContainerObjects"].update(
                moldura(TITULOS[nome], destaque=nome in DESTAQUE)
            )
        else:
            doc["visual"].setdefault("visualContainerObjects", {})
            doc["visual"]["visualContainerObjects"].update(moldura())

        if nome == "tabela_atipicos":
            ordenar_tabela(visual)
            visual.setdefault("objects", {}).update({
                "grid": obj(gridVertical=booleano(False),
                            gridHorizontalColor=cor(GRADE),
                            rowPadding=numero(3)),
                "columnHeaders": obj(fontSize=numero(9), bold=booleano(True),
                                     fontColor=cor(TINTA)),
                "values": obj(fontSize=numero(9), fontColor=cor(TINTA_SUAVE)),
            })

        if nome in ESTILO:
            novo_tipo, medida, rampa, rotulos = ESTILO[nome]
            if novo_tipo and novo_tipo != visual["visualType"]:
                visual["visualType"] = novo_tipo
                tipos_trocados += 1

            if visual["visualType"] == "card":
                estilizar_cartao(doc)
            else:
                objetos = eixos(rotulos)
                if medida and rampa:
                    c_min, c_max = RAMPAS[rampa]
                    objetos["dataPoint"] = obj(fill=gradiente(medida, c_min, c_max))
                if visual["visualType"] in ("donutChart", "treemap"):
                    objetos.pop("categoryAxis", None)
                    objetos.pop("valueAxis", None)
                    objetos["legend"] = obj(
                        show=booleano(True), position=texto("Right"),
                        fontSize=numero(9), labelColor=cor(TINTA_SUAVE),
                    )
                if visual["visualType"] == "areaChart":
                    objetos["fillPoint"] = obj(show=booleano(True))
                    objetos["dataPoint"] = obj(fill=cor("#2A78D6"))
                visual.setdefault("objects", {}).update(objetos)

        caminho.write_text(
            json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        alterados += 1

    print(f"visuais estilizados: {alterados}")
    print(f"tipos de visual trocados: {tipos_trocados}")


if __name__ == "__main__":
    main()
