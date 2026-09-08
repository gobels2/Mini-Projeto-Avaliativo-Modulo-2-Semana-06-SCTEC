"""Testes da consolidação e das validações do pipeline."""
import zipfile

import pandas as pd
import pytest

from src.consolidar import concatenar, gravar, validar


def _base_valida() -> pd.DataFrame:
    """Base mínima que passa em todas as validações."""
    return pd.DataFrame(
        {
            "ano_compra": ["2020", "2021", "2022", "2023", "2024", "2025", "2026"],
            "qtd_itens_comprados": [2.0] * 7,
            "preco_unitario": [3.0] * 7,
            "preco_total": [6.0] * 7,
        }
    )


def test_concatenar_preserva_todas_as_linhas():
    frames = {
        2020: pd.DataFrame({"uf": ["PA", "SP"]}),
        2021: pd.DataFrame({"uf": ["MG"]}),
    }

    df = concatenar(frames)

    assert len(df) == 3
    assert list(df["uf"]) == ["PA", "SP", "MG"]


def test_validar_aceita_base_integra():
    validar(_base_valida(), n_lidas=7, n_duplicatas=0)


def test_validar_recusa_contagem_de_linhas_incoerente():
    with pytest.raises(ValueError, match="linhas"):
        validar(_base_valida(), n_lidas=10, n_duplicatas=0)


def test_validar_recusa_ano_faltando():
    df = _base_valida().iloc[:6]

    with pytest.raises(ValueError, match="2026"):
        validar(df, n_lidas=6, n_duplicatas=0)


def test_validar_recusa_quando_qtd_vezes_preco_nao_bate():
    df = _base_valida()
    df.loc[0, "preco_total"] = 99.0

    with pytest.raises(ValueError, match="preco_total"):
        validar(df, n_lidas=7, n_duplicatas=0)


def test_gravar_produz_csv_e_zip_com_o_nome_exigido(tmp_path):
    df = pd.DataFrame({"uf": ["PA"], "preco_total": [10.0]})

    caminho_csv, caminho_zip = gravar(df, tmp_path, "BPS_20_26_LeoGobel")

    assert caminho_csv.name == "BPS_20_26_LeoGobel.csv"
    assert caminho_zip.name == "BPS_20_26_LeoGobel.zip"
    with zipfile.ZipFile(caminho_zip) as z:
        assert z.namelist() == ["BPS_20_26_LeoGobel.csv"]
