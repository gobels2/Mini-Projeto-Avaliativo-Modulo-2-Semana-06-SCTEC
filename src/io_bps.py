"""Leitura dos arquivos anuais do Banco de Preços em Saúde (BPS).

Os sete anos chegam como data/raw/<ano>_csv.zip, cada um contendo um único
<ano>.csv separado por ponto e vírgula em UTF-8. A leitura é feita direto de
dentro do .zip para não manter 126 MB descompactados no disco.

Tudo é lido como texto de propósito: converter tipos aqui esconderia os
problemas que o perfil de dados precisa enxergar (valores fora de formato,
nulos gravados como string vazia, datas em padrão brasileiro).
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

ANOS: tuple[int, ...] = (2020, 2021, 2022, 2023, 2024, 2025, 2026)
SEPARADOR = ";"
CODIFICACAO = "utf-8"


def ler_ano(dir_raw: Path, ano: int) -> pd.DataFrame:
    """Lê um ano do BPS e acrescenta a coluna de proveniência.

    Args:
        dir_raw: diretório onde estão os arquivos <ano>_csv.zip.
        ano: ano a ler, de 2020 a 2026.

    Returns:
        DataFrame com todas as colunas originais como str, mais
        `arquivo_origem` indicando de qual CSV a linha veio.
    """
    caminho = Path(dir_raw) / f"{ano}_csv.zip"
    with zipfile.ZipFile(caminho) as arquivo_zip:
        bruto = arquivo_zip.read(f"{ano}.csv")

    df = pd.read_csv(
        io.BytesIO(bruto),
        sep=SEPARADOR,
        encoding=CODIFICACAO,
        dtype=str,
        low_memory=False,
    )
    df["arquivo_origem"] = f"{ano}.csv"
    return df


def ler_todos(dir_raw: Path) -> dict[int, pd.DataFrame]:
    """Lê os sete anos, devolvendo um DataFrame por ano."""
    return {ano: ler_ano(dir_raw, ano) for ano in ANOS}
