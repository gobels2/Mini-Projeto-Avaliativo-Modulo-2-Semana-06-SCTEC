"""Perfil dos sete anos do BPS e mapeamento das discrepâncias entre eles.

O enunciado pede para identificar diferenças de nomes, formatos ou estruturas
entre os anos. A resposta honesta para esta base é que o esquema não muda: as
25 colunas são as mesmas, na mesma ordem, com o mesmo separador e a mesma
codificação nos sete arquivos. Este módulo prova isso em vez de presumir, e
levanta as divergências que de fato existem, que são de volume e de qualidade.

Uso:
    python -m src.perfil_dados
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.io_bps import ANOS, COLUNA_PROVENIENCIA, ler_todos

RAIZ = Path(__file__).resolve().parent.parent
DIR_RAW = RAIZ / "data" / "raw"
SAIDA = RAIZ / "docs" / "perfil_discrepancias.md"


def colunas_da_fonte(df: pd.DataFrame) -> list[str]:
    """Colunas como o BPS as publica, sem a coluna de proveniência.

    `arquivo_origem` é acrescentada por `src.io_bps.ler_ano`. Descrevê-la
    junto com as demais faria o relatório afirmar um esquema de origem que
    não é o do Ministério da Saúde.
    """
    return [c for c in df.columns if c != COLUNA_PROVENIENCIA]


def comparar_colunas(frames: dict[int, pd.DataFrame]) -> dict[int, list[str]]:
    """Compara o esquema de cada ano com o do primeiro ano disponível.

    Returns:
        Dicionário vazio se todos os anos têm exatamente as mesmas colunas na
        mesma ordem. Caso contrário, mapeia cada ano divergente para a lista
        de diferenças encontradas.
    """
    anos_ordenados = sorted(frames)
    ano_referencia = anos_ordenados[0]
    colunas_referencia = colunas_da_fonte(frames[ano_referencia])

    diferencas: dict[int, list[str]] = {}
    for ano in anos_ordenados[1:]:
        colunas = colunas_da_fonte(frames[ano])
        if colunas == colunas_referencia:
            continue

        achados = []
        for ausente in sorted(set(colunas_referencia) - set(colunas)):
            achados.append(f"ausente em {ano}: {ausente}")
        for extra in sorted(set(colunas) - set(colunas_referencia)):
            achados.append(f"extra em {ano}: {extra}")
        if not achados:
            achados.append(f"mesma composição, ordem diferente em {ano}")
        diferencas[ano] = achados

    return diferencas


def resumir_ano(df: pd.DataFrame) -> dict[str, object]:
    """Conta linhas, duplicatas exatas e nulos por coluna de um ano."""
    return {
        "linhas": len(df),
        "duplicatas": int(df.duplicated().sum()),
        "nulos_por_coluna": df.isna().sum().to_dict(),
    }


def montar_relatorio(frames: dict[int, pd.DataFrame]) -> str:
    """Gera o relatório em markdown com o perfil e as discrepâncias."""
    anos_ordenados = sorted(frames)
    diferencas = comparar_colunas(frames)
    resumos = {ano: resumir_ano(frames[ano]) for ano in anos_ordenados}

    linhas = ["# Perfil dos dados e discrepâncias entre os anos", ""]

    linhas.append("## Esquema")
    linhas.append("")
    if diferencas:
        linhas.append("Discrepâncias de esquema encontradas:")
        linhas.append("")
        for ano, achados in diferencas.items():
            for achado in achados:
                linhas.append(f"- {achado}")
    else:
        colunas = colunas_da_fonte(frames[anos_ordenados[0]])
        linhas.append(
            f"**Nenhuma discrepância de esquema.** Os {len(anos_ordenados)} "
            f"arquivos têm as mesmas {len(colunas)} colunas, na mesma ordem."
        )
        linhas.append("")
        linhas.append("Colunas: " + ", ".join(f"`{c}`" for c in colunas))
    linhas.append("")

    linhas.append("## Volume por ano")
    linhas.append("")
    linhas.append("| Ano | Linhas | Duplicatas exatas |")
    linhas.append("|---|---|---|")
    for ano in anos_ordenados:
        resumo = resumos[ano]
        linhas.append(f"| {ano} | {resumo['linhas']:,} | {resumo['duplicatas']} |")
    linhas.append("")

    linhas.append("## Percentual de nulos por coluna e por ano")
    linhas.append("")
    cabecalho = "| Coluna | " + " | ".join(str(a) for a in anos_ordenados) + " |"
    linhas.append(cabecalho)
    linhas.append("|---" * (len(anos_ordenados) + 1) + "|")
    for coluna in colunas_da_fonte(frames[anos_ordenados[0]]):
        celulas = []
        for ano in anos_ordenados:
            resumo = resumos[ano]
            pct = resumo["nulos_por_coluna"].get(coluna, 0) / resumo["linhas"] * 100
            celulas.append(f"{pct:.1f}%")
        linhas.append(f"| `{coluna}` | " + " | ".join(celulas) + " |")
    linhas.append("")

    return "\n".join(linhas)


def main() -> None:
    frames = ler_todos(DIR_RAW)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(montar_relatorio(frames), encoding="utf-8")
    print(f"Relatório gravado em {SAIDA}")
    for ano in ANOS:
        print(f"  {ano}: {len(frames[ano]):,} linhas")


if __name__ == "__main__":
    main()
