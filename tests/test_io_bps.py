"""Testes da leitura dos arquivos anuais do BPS."""
import zipfile
from pathlib import Path

import pandas as pd

from src.io_bps import ANOS, ler_ano, ler_todos


def _criar_zip(tmp_path: Path, ano: int, conteudo: str) -> None:
    """Monta um <ano>_csv.zip sintético no formato exato do BPS."""
    with zipfile.ZipFile(tmp_path / f"{ano}_csv.zip", "w") as z:
        z.writestr(f"{ano}.csv", conteudo.encode("utf-8"))


def test_ler_ano_le_o_csv_de_dentro_do_zip(tmp_path):
    _criar_zip(tmp_path, 2020, "ano_compra;uf;preco_total\n2020;PA;43875.0\n")

    df = ler_ano(tmp_path, 2020)

    assert list(df.columns) == ["ano_compra", "uf", "preco_total", "arquivo_origem"]
    assert len(df) == 1


def test_ler_ano_mantem_tudo_como_texto(tmp_path):
    """A conversão de tipos é do tratamento; aqui nada pode ser inferido."""
    _criar_zip(tmp_path, 2020, "ano_compra;preco_total\n2020;43875.0\n")

    df = ler_ano(tmp_path, 2020)

    assert df.loc[0, "preco_total"] == "43875.0"


def test_ler_ano_registra_a_proveniencia(tmp_path):
    _criar_zip(tmp_path, 2023, "ano_compra;uf\n2023;MG\n")

    df = ler_ano(tmp_path, 2023)

    assert df.loc[0, "arquivo_origem"] == "2023.csv"


def test_ler_todos_devolve_um_dataframe_por_ano(tmp_path):
    for ano in ANOS:
        _criar_zip(tmp_path, ano, f"ano_compra;uf\n{ano};SP\n")

    frames = ler_todos(tmp_path)

    assert set(frames) == set(ANOS)
    assert all(isinstance(df, pd.DataFrame) for df in frames.values())


def test_ler_ano_funciona_sobre_a_base_real(dir_raw):
    df = ler_ano(dir_raw, 2026)

    assert len(df) == 819
    assert "descricao_catmat" in df.columns
