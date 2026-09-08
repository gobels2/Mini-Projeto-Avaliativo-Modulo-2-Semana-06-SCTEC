"""Testes das funções de tratamento da base do BPS."""
import pandas as pd

from src.tratamento import (
    converter_datas,
    converter_numericos,
    corrigir_esfera,
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
