"""Testes das funções de tratamento da base do BPS."""
import pandas as pd

from src.tratamento import (
    converter_datas,
    converter_numericos,
    corrigir_esfera,
    derivar_principio_ativo,
    derivar_regiao,
    derivar_tipo_produto,
    normalizar_descricao,
    normalizar_espacos,
    remover_duplicatas,
)


def test_normalizar_espacos_colapsa_espacos_internos_e_das_pontas():
    s = pd.Series(["FUNDO  MUNICIPAL   DE  SAUDE", "  MUNICIPIO DE PATOS  "])

    assert list(normalizar_espacos(s)) == [
        "FUNDO MUNICIPAL DE SAUDE",
        "MUNICIPIO DE PATOS",
    ]


def test_normalizar_espacos_preserva_nulos():
    s = pd.Series(["A  B", None])

    resultado = normalizar_espacos(s)

    assert resultado[0] == "A B"
    assert pd.isna(resultado[1])


def test_converter_numericos_converte_as_tres_colunas_de_valor():
    df = pd.DataFrame(
        {
            "qtd_itens_comprados": ["9750"],
            "preco_unitario": ["4.5"],
            "preco_total": ["43875.0"],
        }
    )

    resultado = converter_numericos(df)

    assert resultado.loc[0, "qtd_itens_comprados"] == 9750.0
    assert resultado.loc[0, "preco_unitario"] == 4.5
    assert resultado.loc[0, "preco_total"] == 43875.0


def test_converter_datas_le_o_padrao_brasileiro():
    df = pd.DataFrame({"compra": ["01/01/2020"], "insercao": ["19/01/2024"]})

    resultado = converter_datas(df)

    assert resultado.loc[0, "compra"] == pd.Timestamp("2020-01-01")
    assert resultado.loc[0, "insercao"] == pd.Timestamp("2024-01-19")


def test_normalizar_descricao_corrige_acento_minusculo_no_meio_de_maiusculas():
    """Os 2.578 registros com 'SOLUçÃO' e 'APRESENTAçãO' vêm assim da fonte."""
    df = pd.DataFrame(
        {"descricao_catmat": ["ERITROMICINA, APRESENTAçãO:ESTEARATO"]}
    )

    resultado = normalizar_descricao(df)

    assert resultado.loc[0, "descricao_catmat"] == (
        "ERITROMICINA, APRESENTAÇÃO:ESTEARATO"
    )


def test_corrigir_esfera_troca_o_valor_zero_e_os_nulos():
    df = pd.DataFrame({"esfera": ["MUNICIPAL", "0", None]})

    resultado = corrigir_esfera(df)

    assert list(resultado["esfera"]) == [
        "MUNICIPAL",
        "NÃO INFORMADO",
        "NÃO INFORMADO",
    ]


def test_remover_duplicatas_devolve_a_base_limpa_e_a_contagem():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})

    resultado, removidas = remover_duplicatas(df)

    assert len(resultado) == 2
    assert removidas == 1


def test_funcoes_nao_alteram_o_dataframe_original():
    df = pd.DataFrame({"esfera": ["0"]})

    corrigir_esfera(df)

    assert df.loc[0, "esfera"] == "0"


def test_derivar_tipo_produto_usa_a_presenca_do_registro_anvisa():
    """anvisa nulo não é erro: indica item que não é medicamento."""
    df = pd.DataFrame({"anvisa": ["1031100350033", None]})

    resultado = derivar_tipo_produto(df)

    assert list(resultado["tipo_produto"]) == [
        "MEDICAMENTO",
        "DISPOSITIVO/OUTRO",
    ]


def test_derivar_principio_ativo_pega_o_token_antes_da_primeira_virgula():
    df = pd.DataFrame(
        {
            "descricao_catmat": [
                "GLICONATO DE CÁLCIO, DOSAGEM:10%, APRESENTAÇÃO:SOLUÇÃO",
                "PIPETA SEM VIRGULA",
            ]
        }
    )

    resultado = derivar_principio_ativo(df)

    assert list(resultado["principio_ativo"]) == [
        "GLICONATO DE CÁLCIO",
        "PIPETA SEM VIRGULA",
    ]


def test_derivar_regiao_mapeia_as_cinco_regioes_e_o_desconhecido():
    df = pd.DataFrame({"uf": ["PA", "CE", "GO", "SP", "RS", "ZZ"]})

    resultado = derivar_regiao(df)

    assert list(resultado["regiao"]) == [
        "NORTE",
        "NORDESTE",
        "CENTRO-OESTE",
        "SUDESTE",
        "SUL",
        "NÃO INFORMADO",
    ]
