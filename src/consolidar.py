"""Consolidação dos sete anos do BPS em uma base única.

Lê os arquivos anuais, concatena preservando todas as linhas, aplica os
tratamentos, valida o resultado e grava a base consolidada em CSV e em ZIP.
O CSV tem cerca de 126 MB e fica fora do git; o ZIP, de cerca de 20 MB, é o
arquivo versionado e entregue.

Uso:
    python -m src.consolidar
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

from src.io_bps import ANOS, ler_todos
from src.tratamento import aplicar_tratamentos

RAIZ = Path(__file__).resolve().parent.parent
DIR_RAW = RAIZ / "data" / "raw"
DIR_SAIDA = RAIZ / "data" / "processed"
NOME_BASE = "BPS_20_26_LeoGobel"

TOLERANCIA_REAIS = 0.01


def concatenar(frames: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Empilha os anos em ordem crescente, preservando todas as linhas."""
    return pd.concat(
        [frames[ano] for ano in sorted(frames)],
        ignore_index=True,
    )


def validar(df: pd.DataFrame, n_lidas: int, n_duplicatas: int) -> None:
    """Confere a integridade da base consolidada.

    Raises:
        ValueError: com a lista completa de problemas, para que uma rodada
            mostre tudo o que está errado em vez de um problema por vez.
    """
    problemas: list[str] = []

    esperado = n_lidas - n_duplicatas
    if len(df) != esperado:
        problemas.append(
            f"contagem de linhas: esperadas {esperado:,}, obtidas {len(df):,}"
        )

    anos_presentes = set(df["ano_compra"].astype(int))
    faltando = sorted(set(ANOS) - anos_presentes)
    if faltando:
        problemas.append(f"anos ausentes na base: {faltando}")

    divergencia = (
        df["qtd_itens_comprados"] * df["preco_unitario"] - df["preco_total"]
    ).abs()
    fora = int((divergencia > TOLERANCIA_REAIS).sum())
    if fora:
        problemas.append(
            f"{fora:,} linhas onde qtd x preco_unitario != preco_total"
        )

    if problemas:
        raise ValueError("Validação falhou:\n- " + "\n- ".join(problemas))


def gravar(df: pd.DataFrame, dir_saida: Path, nome: str) -> tuple[Path, Path]:
    """Grava a base em CSV e compacta em ZIP com o mesmo nome.

    Returns:
        (caminho do CSV, caminho do ZIP).
    """
    dir_saida = Path(dir_saida)
    dir_saida.mkdir(parents=True, exist_ok=True)

    caminho_csv = dir_saida / f"{nome}.csv"
    caminho_zip = dir_saida / f"{nome}.zip"

    df.to_csv(caminho_csv, index=False, sep=";", encoding="utf-8")
    with zipfile.ZipFile(caminho_zip, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(caminho_csv, arcname=caminho_csv.name)

    return caminho_csv, caminho_zip


def main() -> None:
    frames = ler_todos(DIR_RAW)
    n_lidas = sum(len(df) for df in frames.values())

    df = concatenar(frames)
    df, duplicatas = aplicar_tratamentos(df)

    validar(df, n_lidas=n_lidas, n_duplicatas=duplicatas)
    caminho_csv, caminho_zip = gravar(df, DIR_SAIDA, NOME_BASE)

    atipicos = int(df["flag_preco_atipico"].sum())
    valor_total = df["preco_total"].sum()
    valor_atipicos = df.loc[df["flag_preco_atipico"], "preco_total"].sum()

    print(f"Linhas lidas:        {n_lidas:,}")
    print(f"Duplicatas removidas:{duplicatas:>8,}")
    print(f"Linhas gravadas:     {len(df):,}")
    print(f"Colunas:             {len(df.columns)}")
    print(f"Valor total:         R$ {valor_total:,.2f}")
    print(
        f"Registros atipicos:  {atipicos:,} "
        f"({atipicos / len(df) * 100:.2f}%) "
        f"carregando R$ {valor_atipicos:,.2f} "
        f"({valor_atipicos / valor_total * 100:.1f}% do total)"
    )
    print(f"CSV: {caminho_csv} ({caminho_csv.stat().st_size / 1024**2:,.1f} MB)")
    print(f"ZIP: {caminho_zip} ({caminho_zip.stat().st_size / 1024**2:,.1f} MB)")


if __name__ == "__main__":
    main()
