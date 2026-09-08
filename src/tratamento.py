"""Tratamento da base consolidada do BPS.

Reúne as funções de limpeza, as colunas derivadas e o critério de preço
atípico. Todas são puras: recebem um DataFrame e devolvem outro, sem tocar no
original e sem nenhum I/O. Isso é o que permite testá-las sobre amostras
sintéticas pequenas em vez de sobre os 126 MB da base real.
"""
from __future__ import annotations

import pandas as pd

COLUNAS_NUMERICAS: tuple[str, ...] = (
    "qtd_itens_comprados",
    "preco_unitario",
    "preco_total",
)
COLUNAS_DATA: tuple[str, ...] = ("compra", "insercao")

FORMATO_DATA_ORIGEM = "%d/%m/%Y"
NAO_INFORMADO = "NÃO INFORMADO"


def normalizar_espacos(s: pd.Series) -> pd.Series:
    """Tira espaços das pontas e colapsa os internos.

    Nomes de instituição vêm da fonte com espaçamento irregular
    ("FUNDO  MUNICIPAL  DE  SAUDE"), o que faria a mesma instituição contar
    como duas em qualquer agrupamento por nome.
    """
    return s.str.strip().str.replace(r"\s+", " ", regex=True)


def converter_numericos(df: pd.DataFrame) -> pd.DataFrame:
    """Converte quantidade, preço unitário e preço total para numérico."""
    resultado = df.copy()
    for coluna in COLUNAS_NUMERICAS:
        resultado[coluna] = pd.to_numeric(resultado[coluna], errors="coerce")
    return resultado


def converter_datas(df: pd.DataFrame) -> pd.DataFrame:
    """Converte as datas do padrão brasileiro para datetime.

    Gravar em ISO na saída evita que o Power BI dependa do locale da máquina
    para interpretar 01/07 como 1º de julho ou 7 de janeiro.
    """
    resultado = df.copy()
    for coluna in COLUNAS_DATA:
        resultado[coluna] = pd.to_datetime(
            resultado[coluna], format=FORMATO_DATA_ORIGEM, errors="coerce"
        )
    return resultado


def normalizar_descricao(df: pd.DataFrame) -> pd.DataFrame:
    """Uniformiza a descrição do CATMAT em caixa alta.

    A fonte traz 2.578 descrições com acento minúsculo dentro de texto
    maiúsculo ("APRESENTAçãO"), resquício de conversão de codificação. Subir
    tudo para caixa alta resolve sem precisar mapear caractere a caractere.
    """
    resultado = df.copy()
    resultado["descricao_catmat"] = (
        resultado["descricao_catmat"].str.upper().pipe(normalizar_espacos)
    )
    return resultado


def corrigir_esfera(df: pd.DataFrame) -> pd.DataFrame:
    """Troca o valor inválido "0" e os nulos por NÃO INFORMADO.

    São 43 registros, todos de 2020, de uma associação que não se enquadra nas
    três esferas de governo.
    """
    resultado = df.copy()
    resultado["esfera"] = resultado["esfera"].replace("0", NAO_INFORMADO)
    resultado["esfera"] = resultado["esfera"].fillna(NAO_INFORMADO)
    return resultado


def remover_duplicatas(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove linhas idênticas em todas as colunas.

    Returns:
        (base sem duplicatas, quantidade de linhas removidas).
    """
    antes = len(df)
    resultado = df.drop_duplicates().reset_index(drop=True)
    return resultado, antes - len(resultado)


UF_PARA_REGIAO: dict[str, str] = {
    "AC": "NORTE", "AP": "NORTE", "AM": "NORTE", "PA": "NORTE",
    "RO": "NORTE", "RR": "NORTE", "TO": "NORTE",
    "AL": "NORDESTE", "BA": "NORDESTE", "CE": "NORDESTE", "MA": "NORDESTE",
    "PB": "NORDESTE", "PE": "NORDESTE", "PI": "NORDESTE", "RN": "NORDESTE",
    "SE": "NORDESTE",
    "DF": "CENTRO-OESTE", "GO": "CENTRO-OESTE", "MT": "CENTRO-OESTE",
    "MS": "CENTRO-OESTE",
    "ES": "SUDESTE", "MG": "SUDESTE", "RJ": "SUDESTE", "SP": "SUDESTE",
    "PR": "SUL", "RS": "SUL", "SC": "SUL",
}


def derivar_tipo_produto(df: pd.DataFrame) -> pd.DataFrame:
    """Separa medicamentos de dispositivos pelo registro na Anvisa.

    Metade da base tem `anvisa` e `generico` nulos. Não é falha de
    preenchimento: dispositivo médico não tem registro de medicamento. Em vez
    de imputar um valor, a ausência vira informação.
    """
    resultado = df.copy()
    resultado["tipo_produto"] = resultado["anvisa"].notna().map(
        {True: "MEDICAMENTO", False: "DISPOSITIVO/OUTRO"}
    )
    return resultado


def derivar_principio_ativo(df: pd.DataFrame) -> pd.DataFrame:
    """Extrai o nome do produto do início da descrição do CATMAT.

    A descrição segue o padrão "NOME, ATRIBUTO:VALOR, ATRIBUTO:VALOR". O
    primeiro token dá 2.198 nomes distintos contra 12.994 códigos CATMAT, o
    que é a diferença entre um ranking legível e um ilegível.
    """
    resultado = df.copy()
    resultado["principio_ativo"] = (
        resultado["descricao_catmat"].str.split(",").str[0].str.strip()
    )
    return resultado


def derivar_regiao(df: pd.DataFrame) -> pd.DataFrame:
    """Mapeia a UF para a região geográfica."""
    resultado = df.copy()
    resultado["regiao"] = resultado["uf"].map(UF_PARA_REGIAO).fillna(NAO_INFORMADO)
    return resultado
