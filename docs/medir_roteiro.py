"""Mede a duração falada do roteiro do vídeo, bloco a bloco.

Estimar duração de roteiro no olho erra feio — no projeto do Módulo 1 a
estimativa errou cerca de 40% duas vezes seguidas. Este script conta as
palavras efetivamente faladas e converte em segundos, para que o corte seja
feito com alvo numérico por bloco.

Só conta linhas de fala, que no roteiro começam com `> "`. Linhas de ação
(**Tela:**), títulos e tabelas ficam de fora — mas o tempo de tela precisa ser
somado por cima do resultado.

Uso:
    python docs/medir_roteiro.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROTEIRO = Path(__file__).resolve().parent / "roteiro_video.md"

#: Palavras por minuto em português falado, lendo roteiro.
RITMOS = {"lento": 140, "normal": 150, "rápido": 165}
LIMITE_SEGUNDOS = 300


def medir(texto: str) -> list[tuple[str, int]]:
    """Devolve (título do bloco, palavras faladas) na ordem do arquivo."""
    blocos: list[tuple[str, int]] = []
    titulo = "(sem bloco)"
    palavras = 0

    for linha in texto.splitlines():
        if linha.startswith("## "):
            if palavras:
                blocos.append((titulo, palavras))
            titulo = linha[3:].strip()
            palavras = 0
        elif linha.lstrip().startswith('> "'):
            palavras += len(re.findall(r"\S+", linha.lstrip()[3:]))

    if palavras:
        blocos.append((titulo, palavras))
    return blocos


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    blocos = medir(ROTEIRO.read_text(encoding="utf-8"))
    total = sum(p for _, p in blocos)

    print(f"{'Bloco':<52} {'Palavras':>9} {'Segundos':>9}")
    print("-" * 73)
    for titulo, palavras in blocos:
        print(f"{titulo[:52]:<52} {palavras:>9} {palavras / 150 * 60:>8.0f}s")
    print("-" * 73)
    print(f"{'TOTAL':<52} {total:>9} {total / 150 * 60:>8.0f}s")
    print()

    for nome, wpm in RITMOS.items():
        seg = total / wpm * 60
        folga = LIMITE_SEGUNDOS - seg
        print(
            f"  {nome:<8} {wpm} pal/min -> {seg:5.0f}s "
            f"({int(seg // 60)}min{int(seg % 60):02d}) "
            f"| folga para tempo de tela: {folga:4.0f}s"
        )


if __name__ == "__main__":
    main()
