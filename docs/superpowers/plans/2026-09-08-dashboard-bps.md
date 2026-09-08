# Dashboard BPS 2020–2026 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar o Mini-Projeto Avaliativo M2S06 — base BPS 2020–2026 consolidada e tratada, dashboard Power BI de três páginas, README documentado e vídeo de até 5 minutos, publicados no GitHub.

**Architecture:** Um pipeline Python em quatro módulos (`io_bps` lê os sete `.zip`, `tratamento` reúne funções puras de limpeza e derivação, `perfil_dados` gera o relatório de discrepâncias, `consolidar` orquestra e valida) produz um CSV único que alimenta um modelo plano no Power BI Desktop com uma `dCalendario` para inteligência temporal. As funções de tratamento são puras e testadas com pytest sobre DataFrames sintéticos; a orquestração é validada por asserções sobre a base real.

**Tech Stack:** Python 3.12.10, pandas 3.0.3, pytest 9.0.3, Power BI Desktop, git + gh 2.92.

**Spec:** `docs/superpowers/specs/2026-09-08-bps-dashboard-design.md`

## Global Constraints

- **Prazo: 14/09/2026.** Cronograma dia a dia na seção 12 do spec.
- **Nenhum crédito ao Claude em lugar nenhum do repositório.** Nada de `Co-Authored-By:`, nada de `Claude-Session:`, nada de `claude` em mensagem de commit, arquivo ou README. Antes de **todo** push: `git log --format=%B | grep -ci "claude\|co-authored"` tem de retornar `0`.
- **Push em partes, com distância no tempo.** Uma branch por push, nunca duas seguidas. Intervalo mínimo de 4 minutos e alvo de 4 a 9 minutos entre pushes. Implementar a espera com `sleep` em background (`run_in_background: true`), nunca em foreground.
- **Conferir integridade dos arquivos antes de cada commit.** Esta máquina já apagou 100 linhas de comentários de arquivos `.sql` depois de gravados. Rodar `wc -l` nos arquivos tocados e `git diff --stat` antes de `git commit`.
- **Nomes de branch:** `chore/`, `feat/`, `docs/`. Merges sempre com `--no-ff`.
- **Idioma:** todo artefato do repositório (código, comentários, docstrings, README, relatórios) em português.
- **O CSV de ~126 MB nunca entra no git.** Só o `.zip` de ~20 MB é versionado, e uma única vez, na Task 8.
- **Ordem das colunas derivadas** e nomes exatos: `arquivo_origem`, `tipo_produto`, `principio_ativo`, `regiao`, `n_grupo`, `mediana_grupo`, `razao_vs_mediana`, `flag_preco_atipico`.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `src/io_bps.py` | Ler os sete `.zip` como texto puro. Nenhuma inferência de tipo. |
| `src/tratamento.py` | Funções puras de limpeza, derivação e flag. Sem I/O. |
| `src/perfil_dados.py` | CLI: perfila os sete anos e grava `docs/perfil_discrepancias.md`. |
| `src/consolidar.py` | CLI: orquestra leitura → concat → tratamento → validação → CSV + ZIP. |
| `tests/test_io_bps.py` | Leitura de zip sintético. |
| `tests/test_tratamento.py` | Cada função de tratamento sobre DataFrames sintéticos. |
| `tests/test_consolidar.py` | Validações do pipeline sobre DataFrames sintéticos. |
| `dashboard/BPS_2020_2026.pbix` | Modelo, medidas e três páginas. |
| `dashboard/img/` | Capturas PNG das três páginas para o README. |

O spec listava três módulos em `src/`; o quarto (`io_bps.py`) existe porque tanto `perfil_dados.py` quanto `consolidar.py` precisam ler os arquivos, e duplicar a leitura nos dois seria a única alternativa.

---

## Task 1: Estrutura do repositório e dependências

**Branch:** `chore/estrutura-inicial`

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `data/raw/2020_csv.zip` … `data/raw/2026_csv.zip` (cópia dos sete arquivos já baixados)

**Interfaces:**
- Consumes: nada.
- Produces: `tests/conftest.py` expõe a fixture `dir_raw` (`Path` para `data/raw`), usada pelas tasks 2 e 4.

- [ ] **Step 1: Criar a branch**

```bash
git checkout -b chore/estrutura-inicial
```

- [ ] **Step 2: Escrever o `.gitignore`**

```gitignore
# Base consolidada: 126 MB, versionada apenas como .zip
data/processed/*.csv

# Roteiro do vídeo fica só no disco
docs/roteiro_video.md

# Python
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
```

- [ ] **Step 3: Escrever o `requirements.txt`**

```text
pandas>=3.0
pytest>=9.0
```

- [ ] **Step 4: Criar os pacotes vazios e a fixture**

`src/__init__.py` e `tests/__init__.py` ficam vazios.

`tests/conftest.py`:

```python
"""Fixtures compartilhadas pelos testes do projeto."""
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def dir_raw() -> Path:
    """Diretório com os sete .zip anuais originais do BPS."""
    return RAIZ / "data" / "raw"
```

- [ ] **Step 5: Copiar os sete arquivos originais para `data/raw/`**

```bash
mkdir -p data/raw data/processed dashboard/img
cp ../2020_csv.zip ../2021_csv.zip ../2022_csv.zip ../2023_csv.zip \
   ../2024_csv.zip ../2025_csv.zip ../2026_csv.zip data/raw/
ls -la data/raw/
```

Esperado: sete arquivos, ~19,6 MB no total.

- [ ] **Step 6: Confirmar que o pytest roda**

Run: `python -m pytest -q`
Expected: `no tests ran` (sem erro de coleta).

- [ ] **Step 7: Conferir integridade e commitar**

```bash
wc -l .gitignore requirements.txt tests/conftest.py
git add .gitignore requirements.txt src/ tests/ data/raw/
git status --short
git commit -m "chore: estrutura inicial do projeto e bases originais do BPS"
```

- [ ] **Step 8: Criar o repositório no GitHub e fazer o primeiro push**

Confirmar com o Leo antes de rodar — é a primeira ação pública.

```bash
gh repo create Mini-Projeto-Avaliativo-Modulo-2-Semana-06-SCTEC --public --source=. --remote=origin
git log --format=%B | grep -ci "claude\|co-authored"   # tem de ser 0
git push -u origin chore/estrutura-inicial
```

- [ ] **Step 9: Fazer o merge em `main` e push**

Respeitar o intervalo: iniciar `sleep 300` em background antes deste push.

```bash
git checkout main
git merge --no-ff chore/estrutura-inicial -m "merge: estrutura inicial do projeto"
git push -u origin main
```

---

## Task 2: Leitura dos arquivos anuais

**Branch:** `feat/perfil-e-discrepancias`

**Files:**
- Create: `src/io_bps.py`
- Test: `tests/test_io_bps.py`

**Interfaces:**
- Consumes: fixture `dir_raw` da Task 1.
- Produces:
  - `ANOS: tuple[int, ...]` = `(2020, 2021, 2022, 2023, 2024, 2025, 2026)`
  - `ler_ano(dir_raw: Path, ano: int) -> pd.DataFrame` — todas as colunas como `str`, mais `arquivo_origem: str`
  - `ler_todos(dir_raw: Path) -> dict[int, pd.DataFrame]`

- [ ] **Step 1: Criar a branch**

```bash
git checkout -b feat/perfil-e-discrepancias
```

- [ ] **Step 2: Escrever o teste que falha**

`tests/test_io_bps.py`:

```python
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
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `python -m pytest tests/test_io_bps.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.io_bps'`

- [ ] **Step 4: Implementar `src/io_bps.py`**

```python
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
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python -m pytest tests/test_io_bps.py -q`
Expected: PASS — 5 passed.

- [ ] **Step 6: Conferir integridade e commitar**

```bash
wc -l src/io_bps.py tests/test_io_bps.py
git add src/io_bps.py tests/test_io_bps.py
git commit -m "feat: leitura dos arquivos anuais do BPS direto dos zips"
```

---

## Task 3: Relatório de discrepâncias entre os anos

**Branch:** `feat/perfil-e-discrepancias` (mesma da Task 2)

**Files:**
- Create: `src/perfil_dados.py`
- Create: `docs/perfil_discrepancias.md` (gerado pelo script)
- Test: `tests/test_perfil_dados.py`

**Interfaces:**
- Consumes: `ler_todos`, `ANOS` de `src/io_bps.py`.
- Produces:
  - `comparar_colunas(frames: dict[int, pd.DataFrame]) -> dict[int, list[str]]` — anos cujas colunas diferem do ano de referência, mapeados para a lista de diferenças; dicionário vazio quando os esquemas são idênticos
  - `resumir_ano(df: pd.DataFrame) -> dict[str, object]` — chaves `linhas`, `duplicatas`, `nulos_por_coluna`
  - `montar_relatorio(frames: dict[int, pd.DataFrame]) -> str` — markdown pronto

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_perfil_dados.py`:

```python
"""Testes do perfil e do mapeamento de discrepâncias entre os anos."""
import pandas as pd

from src.perfil_dados import comparar_colunas, montar_relatorio, resumir_ano


def test_comparar_colunas_nao_acusa_diferenca_quando_esquemas_sao_iguais():
    frames = {
        2020: pd.DataFrame({"uf": ["PA"], "preco_total": ["10"]}),
        2021: pd.DataFrame({"uf": ["SP"], "preco_total": ["20"]}),
    }

    assert comparar_colunas(frames) == {}


def test_comparar_colunas_aponta_coluna_ausente_e_extra():
    frames = {
        2020: pd.DataFrame({"uf": ["PA"], "preco_total": ["10"]}),
        2021: pd.DataFrame({"uf": ["SP"], "valor": ["20"]}),
    }

    diferencas = comparar_colunas(frames)

    assert 2021 in diferencas
    assert "preco_total" in " ".join(diferencas[2021])
    assert "valor" in " ".join(diferencas[2021])


def test_resumir_ano_conta_linhas_duplicatas_e_nulos():
    df = pd.DataFrame(
        {
            "uf": ["PA", "PA", "SP"],
            "anvisa": ["123", "123", None],
        }
    )

    resumo = resumir_ano(df)

    assert resumo["linhas"] == 3
    assert resumo["duplicatas"] == 1
    assert resumo["nulos_por_coluna"]["anvisa"] == 1


def test_montar_relatorio_declara_esquema_identico_quando_e_o_caso():
    frames = {
        2020: pd.DataFrame({"uf": ["PA"]}),
        2021: pd.DataFrame({"uf": ["SP"]}),
    }

    relatorio = montar_relatorio(frames)

    assert "Nenhuma discrepância de esquema" in relatorio
    assert "2020" in relatorio and "2021" in relatorio
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_perfil_dados.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.perfil_dados'`

- [ ] **Step 3: Implementar `src/perfil_dados.py`**

```python
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

from src.io_bps import ANOS, ler_todos

RAIZ = Path(__file__).resolve().parent.parent
DIR_RAW = RAIZ / "data" / "raw"
SAIDA = RAIZ / "docs" / "perfil_discrepancias.md"


def comparar_colunas(frames: dict[int, pd.DataFrame]) -> dict[int, list[str]]:
    """Compara o esquema de cada ano com o do primeiro ano disponível.

    Returns:
        Dicionário vazio se todos os anos têm exatamente as mesmas colunas na
        mesma ordem. Caso contrário, mapeia cada ano divergente para a lista
        de diferenças encontradas.
    """
    anos_ordenados = sorted(frames)
    ano_referencia = anos_ordenados[0]
    colunas_referencia = list(frames[ano_referencia].columns)

    diferencas: dict[int, list[str]] = {}
    for ano in anos_ordenados[1:]:
        colunas = list(frames[ano].columns)
        if colunas == colunas_referencia:
            continue

        achados = []
        for ausente in set(colunas_referencia) - set(colunas):
            achados.append(f"ausente em {ano}: {ausente}")
        for extra in set(colunas) - set(colunas_referencia):
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
        colunas = list(frames[anos_ordenados[0]].columns)
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
    for coluna in frames[anos_ordenados[0]].columns:
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
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_perfil_dados.py -q`
Expected: PASS — 4 passed.

- [ ] **Step 5: Gerar o relatório sobre a base real**

Run: `python -m src.perfil_dados`
Expected: grava `docs/perfil_discrepancias.md` e imprime 2020 = 84.819 … 2026 = 819.

- [ ] **Step 6: Conferir o relatório**

```bash
head -30 docs/perfil_discrepancias.md
grep -c "Nenhuma discrepância de esquema" docs/perfil_discrepancias.md
```

Expected: `1` — os sete anos têm o mesmo esquema.

- [ ] **Step 7: Conferir integridade e commitar**

```bash
wc -l src/perfil_dados.py tests/test_perfil_dados.py docs/perfil_discrepancias.md
git add src/perfil_dados.py tests/test_perfil_dados.py docs/perfil_discrepancias.md
git commit -m "feat: relatorio de perfil e discrepancias entre os sete anos"
```

- [ ] **Step 8: Merge e push, respeitando o intervalo**

```bash
git checkout main
git merge --no-ff feat/perfil-e-discrepancias -m "merge: perfil e mapeamento de discrepancias"
git log --format=%B | grep -ci "claude\|co-authored"   # tem de ser 0
git push origin main
```

---

## Task 4: Consolidação bruta e validações

**Branch:** `feat/consolidacao-bases`

**Files:**
- Create: `src/consolidar.py`
- Test: `tests/test_consolidar.py`

**Interfaces:**
- Consumes: `ler_todos`, `ANOS` de `src/io_bps.py`.
- Produces:
  - `concatenar(frames: dict[int, pd.DataFrame]) -> pd.DataFrame`
  - `validar(df: pd.DataFrame, n_lidas: int, n_duplicatas: int) -> None` — levanta `ValueError` listando todos os problemas encontrados
  - `gravar(df: pd.DataFrame, dir_saida: Path, nome: str) -> tuple[Path, Path]` — devolve `(caminho_csv, caminho_zip)`
  - `NOME_BASE = "BPS_20_26_LeoGobel"`

Nesta task o `.zip` **não** é commitado — ele entra no repositório uma única vez, na Task 8, já com os tratamentos aplicados.

- [ ] **Step 1: Criar a branch**

```bash
git checkout -b feat/consolidacao-bases
```

- [ ] **Step 2: Escrever o teste que falha**

`tests/test_consolidar.py`:

```python
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
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `python -m pytest tests/test_consolidar.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.consolidar'`

- [ ] **Step 4: Implementar `src/consolidar.py`**

```python
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
    for coluna in ("qtd_itens_comprados", "preco_unitario", "preco_total"):
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    validar(df, n_lidas=n_lidas, n_duplicatas=0)
    caminho_csv, caminho_zip = gravar(df, DIR_SAIDA, NOME_BASE)

    print(f"Linhas lidas:      {n_lidas:,}")
    print(f"Linhas gravadas:   {len(df):,}")
    print(f"CSV: {caminho_csv} ({caminho_csv.stat().st_size / 1024**2:,.1f} MB)")
    print(f"ZIP: {caminho_zip} ({caminho_zip.stat().st_size / 1024**2:,.1f} MB)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python -m pytest tests/test_consolidar.py -q`
Expected: PASS — 6 passed.

- [ ] **Step 6: Rodar sobre a base real**

Run: `python -m src.consolidar`
Expected: `Linhas lidas: 342,716` / `Linhas gravadas: 342,716`, CSV de ~126 MB, ZIP de ~20 MB, sem exceção de validação.

- [ ] **Step 7: Conferir que o CSV ficou fora do git**

```bash
git status --short data/processed/
```

Expected: nada listado — o `.gitignore` cobre `data/processed/*.csv`, e o `.zip` só é commitado na Task 8.

- [ ] **Step 8: Conferir integridade e commitar**

```bash
wc -l src/consolidar.py tests/test_consolidar.py
git add src/consolidar.py tests/test_consolidar.py
git commit -m "feat: consolidacao dos sete anos com validacao de integridade"
```

- [ ] **Step 9: Merge e push, respeitando o intervalo**

```bash
git checkout main
git merge --no-ff feat/consolidacao-bases -m "merge: consolidacao das bases anuais"
git log --format=%B | grep -ci "claude\|co-authored"   # tem de ser 0
git push origin main
```

---

## Task 5: Limpeza — tipos, datas, texto, esfera e duplicatas

**Branch:** `feat/tratamento-e-flag`

**Files:**
- Create: `src/tratamento.py`
- Test: `tests/test_tratamento.py`

**Interfaces:**
- Consumes: nada (funções puras sobre DataFrames).
- Produces:
  - `COLUNAS_NUMERICAS: tuple[str, ...]`, `COLUNAS_DATA: tuple[str, ...]`
  - `normalizar_espacos(s: pd.Series) -> pd.Series`
  - `converter_numericos(df: pd.DataFrame) -> pd.DataFrame`
  - `converter_datas(df: pd.DataFrame) -> pd.DataFrame`
  - `normalizar_descricao(df: pd.DataFrame) -> pd.DataFrame`
  - `corrigir_esfera(df: pd.DataFrame) -> pd.DataFrame`
  - `remover_duplicatas(df: pd.DataFrame) -> tuple[pd.DataFrame, int]`

Todas devolvem um DataFrame novo; nenhuma altera o argumento no lugar.

- [ ] **Step 1: Criar a branch**

```bash
git checkout -b feat/tratamento-e-flag
```

- [ ] **Step 2: Escrever os testes que falham**

`tests/test_tratamento.py`:

```python
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
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `python -m pytest tests/test_tratamento.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.tratamento'`

- [ ] **Step 4: Implementar a primeira metade de `src/tratamento.py`**

```python
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
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python -m pytest tests/test_tratamento.py -q`
Expected: PASS — 8 passed.

- [ ] **Step 6: Conferir integridade e commitar**

```bash
wc -l src/tratamento.py tests/test_tratamento.py
git add src/tratamento.py tests/test_tratamento.py
git commit -m "feat: limpeza de tipos, datas, acentuacao, esfera e duplicatas"
```

---

## Task 6: Colunas derivadas

**Branch:** `feat/tratamento-e-flag` (mesma da Task 5)

**Files:**
- Modify: `src/tratamento.py` (acrescentar ao final)
- Modify: `tests/test_tratamento.py` (acrescentar ao final)

**Interfaces:**
- Consumes: `NAO_INFORMADO` da Task 5.
- Produces:
  - `UF_PARA_REGIAO: dict[str, str]`
  - `derivar_tipo_produto(df: pd.DataFrame) -> pd.DataFrame` — cria `tipo_produto`
  - `derivar_principio_ativo(df: pd.DataFrame) -> pd.DataFrame` — cria `principio_ativo`
  - `derivar_regiao(df: pd.DataFrame) -> pd.DataFrame` — cria `regiao`

- [ ] **Step 1: Escrever os testes que falham**

Acrescentar ao final de `tests/test_tratamento.py`:

```python
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
```

E acrescentar os três nomes ao `import` no topo do arquivo:

```python
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
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_tratamento.py -q`
Expected: FAIL — `ImportError: cannot import name 'derivar_tipo_produto'`

- [ ] **Step 3: Implementar as três derivações**

Acrescentar ao final de `src/tratamento.py`:

```python
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
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_tratamento.py -q`
Expected: PASS — 11 passed.

- [ ] **Step 5: Conferir integridade e commitar**

```bash
wc -l src/tratamento.py tests/test_tratamento.py
git add src/tratamento.py tests/test_tratamento.py
git commit -m "feat: colunas derivadas de tipo de produto, principio ativo e regiao"
```

---

## Task 7: Flag de preço atípico

**Branch:** `feat/tratamento-e-flag` (mesma das Tasks 5 e 6)

**Files:**
- Modify: `src/tratamento.py` (acrescentar ao final)
- Modify: `tests/test_tratamento.py` (acrescentar ao final)

**Interfaces:**
- Consumes: nada das tasks anteriores.
- Produces:
  - `N_MINIMO_GRUPO = 5`, `FATOR_ATIPICO = 10`
  - `calcular_flag_atipico(df: pd.DataFrame, n_minimo: int = 5, fator: float = 10) -> pd.DataFrame` — cria `n_grupo`, `mediana_grupo`, `razao_vs_mediana`, `flag_preco_atipico`
  - `aplicar_tratamentos(df: pd.DataFrame) -> tuple[pd.DataFrame, int]` — pipeline completo, devolve a base tratada e o número de duplicatas removidas

- [ ] **Step 1: Escrever os testes que falham**

Acrescentar ao final de `tests/test_tratamento.py`:

```python
def _base_para_flag() -> pd.DataFrame:
    """Grupo A com amostra suficiente e um preço 20x a mediana;
    grupo B com apenas dois registros, abaixo do mínimo exigido."""
    return pd.DataFrame(
        {
            "codigo_br": ["A"] * 5 + ["B"] * 2,
            "unidade_fornecimento": ["AMPOLA"] * 7,
            "preco_unitario": [10.0, 10.0, 10.0, 10.0, 200.0, 1.0, 500.0],
        }
    )


def test_flag_marca_o_preco_desproporcional_do_grupo_com_amostra():
    resultado = calcular_flag_atipico(_base_para_flag(), n_minimo=5, fator=10)

    assert list(resultado["flag_preco_atipico"]) == [
        False, False, False, False, True, False, False
    ]


def test_flag_calcula_a_razao_contra_a_mediana_do_grupo():
    resultado = calcular_flag_atipico(_base_para_flag(), n_minimo=5, fator=10)

    assert resultado.loc[4, "mediana_grupo"] == 10.0
    assert resultado.loc[4, "razao_vs_mediana"] == 20.0


def test_flag_poupa_grupos_pequenos_por_falta_de_base_de_comparacao():
    """Dois registros não estabelecem o que é preço normal para um produto."""
    resultado = calcular_flag_atipico(_base_para_flag(), n_minimo=5, fator=10)

    grupo_b = resultado[resultado["codigo_br"] == "B"]
    assert not grupo_b["flag_preco_atipico"].any()
    assert list(grupo_b["n_grupo"]) == [2, 2]


def test_flag_separa_grupos_por_unidade_de_fornecimento():
    """Mesmo produto em AMPOLA e em BOLSA não é comparável."""
    df = pd.DataFrame(
        {
            "codigo_br": ["A"] * 10,
            "unidade_fornecimento": ["AMPOLA"] * 5 + ["BOLSA"] * 5,
            "preco_unitario": [1.0] * 5 + [100.0] * 5,
        }
    )

    resultado = calcular_flag_atipico(df, n_minimo=5, fator=10)

    assert not resultado["flag_preco_atipico"].any()
```

E acrescentar `calcular_flag_atipico` ao `import` no topo do arquivo.

- [ ] **Step 2: Rodar e ver falhar**

Run: `python -m pytest tests/test_tratamento.py -q`
Expected: FAIL — `ImportError: cannot import name 'calcular_flag_atipico'`

- [ ] **Step 3: Implementar o flag e o pipeline**

Acrescentar ao final de `src/tratamento.py`:

```python
N_MINIMO_GRUPO = 5
FATOR_ATIPICO = 10.0

CHAVE_COMPARACAO = ["codigo_br", "unidade_fornecimento"]


def calcular_flag_atipico(
    df: pd.DataFrame,
    n_minimo: int = N_MINIMO_GRUPO,
    fator: float = FATOR_ATIPICO,
) -> pd.DataFrame:
    """Sinaliza registros cujo preço unitário destoa dos comparáveis.

    Comparar preço só faz sentido entre itens comparáveis, e o que define
    comparabilidade aqui é o par (código CATMAT, unidade de fornecimento):
    o mesmo cloreto de sódio em AMPOLA e em BOLSA não tem o mesmo preço por
    unidade, e tratá-los como um grupo só produziria alarme falso.

    Grupos com menos de `n_minimo` registros ficam de fora porque não
    estabelecem o que é preço normal para aquele item.

    O flag não afirma irregularidade. Aponta registros que merecem
    verificação: diferenças legítimas de fabricante, apresentação,
    quantidade, localidade, modalidade ou período explicam parte deles.
    """
    resultado = df.copy()
    grupo = resultado.groupby(CHAVE_COMPARACAO)["preco_unitario"]

    resultado["n_grupo"] = grupo.transform("size")
    resultado["mediana_grupo"] = grupo.transform("median")
    resultado["razao_vs_mediana"] = (
        resultado["preco_unitario"] / resultado["mediana_grupo"]
    )
    resultado["flag_preco_atipico"] = (
        (resultado["n_grupo"] >= n_minimo)
        & (resultado["razao_vs_mediana"] >= fator)
    )
    return resultado


def aplicar_tratamentos(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Roda o pipeline completo de tratamento na ordem correta.

    A ordem importa: os tipos são convertidos antes do flag, que depende de
    preço numérico; as duplicatas saem antes das derivações, para não gastar
    cálculo em linha que vai embora.

    Returns:
        (base tratada, quantidade de duplicatas removidas).
    """
    resultado, duplicatas_removidas = remover_duplicatas(df)
    resultado = converter_numericos(resultado)
    resultado = converter_datas(resultado)
    resultado = normalizar_descricao(resultado)
    resultado = corrigir_esfera(resultado)
    resultado["nome_instituicao"] = normalizar_espacos(
        resultado["nome_instituicao"]
    )
    resultado = derivar_tipo_produto(resultado)
    resultado = derivar_principio_ativo(resultado)
    resultado = derivar_regiao(resultado)
    resultado = calcular_flag_atipico(resultado)
    return resultado, duplicatas_removidas
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python -m pytest tests/test_tratamento.py -q`
Expected: PASS — 15 passed.

- [ ] **Step 5: Conferir integridade e commitar**

```bash
wc -l src/tratamento.py tests/test_tratamento.py
git add src/tratamento.py tests/test_tratamento.py
git commit -m "feat: flag de preco atipico por grupo comparavel e pipeline de tratamento"
```

---

## Task 8: Pipeline completo e base entregue

**Branch:** `feat/tratamento-e-flag` (mesma das Tasks 5, 6 e 7)

**Files:**
- Modify: `src/consolidar.py` — função `main`
- Create: `data/processed/BPS_20_26_LeoGobel.zip` (único commit do binário)

**Interfaces:**
- Consumes: `aplicar_tratamentos` da Task 7; `concatenar`, `validar`, `gravar` da Task 4.
- Produces: `data/processed/BPS_20_26_LeoGobel.csv` (local, fora do git) e `.zip` (versionado).

- [ ] **Step 1: Ligar o tratamento ao `main` de `src/consolidar.py`**

Substituir a função `main` inteira por:

```python
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
```

E acrescentar ao topo do arquivo, junto dos outros imports:

```python
from src.tratamento import aplicar_tratamentos
```

- [ ] **Step 2: Rodar o pipeline completo sobre a base real**

Run: `python -m src.consolidar`

Expected — estes números vêm do perfil já feito e servem de conferência:

```
Linhas lidas:        342,716
Duplicatas removidas:      19
Linhas gravadas:     342,697
Registros atipicos:  4,922 (1.44%) carregando R$ 34,0... (43.3% do total)
```

Se qualquer um divergir, parar e investigar antes de seguir — não ajustar o número esperado para caber no resultado.

- [ ] **Step 3: Conferir que a suíte inteira segue verde**

Run: `python -m pytest -q`
Expected: PASS — 30 passed (5 de `io_bps`, 4 de `perfil_dados`, 6 de `consolidar`, 15 de `tratamento`).

- [ ] **Step 4: Conferir o tamanho do ZIP antes de commitar**

```bash
ls -lh data/processed/
```

Expected: `.zip` na casa de 20 MB, bem abaixo do limite de 100 MB do GitHub. O `.csv` aparece no diretório mas não no `git status`.

- [ ] **Step 5: Commitar o código e a base**

```bash
git status --short
git add src/consolidar.py
git commit -m "feat: pipeline completo de consolidacao com tratamento aplicado"
git add -f data/processed/BPS_20_26_LeoGobel.zip
git commit -m "feat: base consolidada e tratada de 2020 a 2026"
```

- [ ] **Step 6: Merge e push, respeitando o intervalo**

```bash
git checkout main
git merge --no-ff feat/tratamento-e-flag -m "merge: tratamento da base e flag de preco atipico"
git log --format=%B | grep -ci "claude\|co-authored"   # tem de ser 0
git push origin main
```

---

## Task 9: Dashboard no Power BI

**Branch:** `feat/dashboard-powerbi`

**Files:**
- Create: `dashboard/BPS_2020_2026.pbix`
- Create: `dashboard/img/p1-visao-geral.png`, `p2-geografia-instituicoes.png`, `p3-investigacao-precos.png`

**Interfaces:**
- Consumes: `data/processed/BPS_20_26_LeoGobel.csv` gerado na Task 8.
- Produces: as três capturas PNG, consumidas pelo README na Task 10.

Esta task é manual, no Power BI Desktop. Não há teste automatizado; a verificação é conferir cada KPI contra os números já apurados no pipeline.

- [ ] **Step 1: Instalar o Power BI Desktop**

Microsoft Store, ou o instalador avulso em `https://powerbi.microsoft.com/desktop/`. Confirmar com `Get-AppxPackage -Name "*PowerBI*"` ou abrindo o programa.

- [ ] **Step 2: Criar a branch**

```bash
git checkout -b feat/dashboard-powerbi
```

- [ ] **Step 3: Importar a base**

Página Inicial > Obter dados > Texto/CSV > `data/processed/BPS_20_26_LeoGobel.csv`.
Na janela de visualização: **Origem do arquivo = 65001: Unicode (UTF-8)**, **Delimitador = Ponto e vírgula**, **Detecção de tipo de dados = Com base no conjunto de dados inteiro**. Clicar em **Transformar Dados**.

- [ ] **Step 4: Conferir os tipos no Editor do Power Query**

Renomear a consulta para `fBPS`. Conferir coluna a coluna:

| Coluna | Tipo |
|---|---|
| `compra`, `insercao` | Data |
| `qtd_itens_comprados`, `preco_unitario`, `preco_total` | Número Decimal |
| `mediana_grupo`, `razao_vs_mediana` | Número Decimal |
| `n_grupo` | Número Inteiro |
| `flag_preco_atipico` | Verdadeiro/Falso |
| todas as demais | Texto |

Página Inicial > Fechar e Aplicar. A carga de 342.697 linhas leva alguns minutos.

- [ ] **Step 5: Criar a tabela de calendário**

Modelagem > Nova tabela:

```dax
dCalendario =
VAR DataMinima = MIN(fBPS[compra])
VAR DataMaxima = MAX(fBPS[compra])
RETURN
ADDCOLUMNS(
    CALENDAR(DataMinima, DataMaxima),
    "Ano", YEAR([Date]),
    "Mês", MONTH([Date]),
    "Nome do Mês", FORMAT([Date], "MMM"),
    "Ano-Mês", FORMAT([Date], "YYYY-MM")
)
```

Marcar como tabela de datas (Modelagem > Marcar como tabela de data > coluna `Date`) e criar a relação `dCalendario[Date]` 1:N `fBPS[compra]`.

- [ ] **Step 6: Criar as seis medidas obrigatórias**

```dax
Valor Total Registrado = SUM(fBPS[preco_total])

Qtd Total de Itens = SUM(fBPS[qtd_itens_comprados])

Nº de Registros = COUNTROWS(fBPS)

Instituições Compradoras = DISTINCTCOUNT(fBPS[cnpj_instituicao])

Fornecedores = DISTINCTCOUNT(fBPS[cnpj_fornecedor])

Preço Unit. Médio Ponderado = DIVIDE([Valor Total Registrado], [Qtd Total de Itens])
```

Formatar `Valor Total Registrado` como moeda com 0 casas e `Preço Unit. Médio Ponderado` como moeda com 4 casas.

- [ ] **Step 7: Criar as três medidas de apoio**

```dax
Valor Registros Atípicos =
CALCULATE([Valor Total Registrado], fBPS[flag_preco_atipico] = TRUE())

% do Valor em Atípicos =
DIVIDE([Valor Registros Atípicos], [Valor Total Registrado])

Preço Médio Pond. s/ Atípicos =
CALCULATE([Preço Unit. Médio Pond.], fBPS[flag_preco_atipico] = FALSE())
```

- [ ] **Step 8: Validar as medidas contra os números do pipeline**

Colocar cada medida em um cartão sem nenhum filtro e conferir:

| Medida | Valor esperado |
|---|---|
| Valor Total Registrado | R$ 78,6 bi |
| Nº de Registros | 342.697 |
| Instituições Compradoras | 831 |
| Fornecedores | 3.502 |
| % do Valor em Atípicos | 43,3% |

Divergência aqui significa erro de tipo na importação — voltar ao Step 4 antes de desenhar qualquer visual.

- [ ] **Step 9: Montar a página 1 — Visão Geral**

Seis cartões de KPI no topo, na ordem do enunciado. Abaixo, quatro visuais:

1. **Gráfico de colunas e linhas agrupadas** — eixo `dCalendario[Ano]`, colunas `Valor Total Registrado`, linha `Preço Unit. Médio Ponderado`.
2. **Gráfico de barras empilhadas** — eixo `modalidade_compra`, valor `Valor Total Registrado`.
3. **Gráfico de rosca** — legenda `tipo_produto`, valor `Nº de Registros`.
4. **Gráfico de barras** — eixo `principio_ativo` (10 principais por valor), valor `Valor Total Registrado`.

- [ ] **Step 10: Montar a página 2 — Geografia e Instituições**

1. **Mapa coroplético** — localização `uf`, saturação `Valor Total Registrado`.
2. **Barras** — `municipio_instituicao`, 10 principais por `Valor Total Registrado`.
3. **Barras** — `nome_instituicao`, 10 principais por `Valor Total Registrado`.
4. **Tabela** — `fornecedor`, `fabricante`, `Valor Total Registrado`, `Nº de Registros`.
5. **Rosca** — `esfera` por `Valor Total Registrado`.

- [ ] **Step 11: Montar a página 3 — Investigação de Preços**

1. **Cartões lado a lado** — `Valor Total Registrado` e `Preço Médio Pond. s/ Atípicos`, deixando a diferença visível.
2. **Dispersão** — eixo X `mediana_grupo`, eixo Y `preco_unitario`, detalhe `principio_ativo`, tamanho `preco_total`.
3. **Tabela** — colunas `ano_compra`, `uf`, `nome_instituicao`, `principio_ativo`, `unidade_fornecimento`, `qtd_itens_comprados`, `preco_unitario`, `mediana_grupo`, `razao_vs_mediana`, `preco_total`, filtrada por `flag_preco_atipico = Verdadeiro`, ordenada por `preco_total` decrescente. O caso da Penicilamina aparece na primeira linha.
4. **Barras** — `uf` por `Valor Total Registrado`, para demonstrar ao vivo a inversão PR/SP ao alternar o filtro do flag.

Acrescentar uma caixa de texto com a ressalva do enunciado: diferença de preço não é prova de irregularidade, e pode decorrer de fabricante, apresentação, unidade, quantidade, localidade, modalidade ou período.

- [ ] **Step 12: Adicionar os filtros e sincronizar**

Segmentações de `ano_compra`, `uf`, `esfera`, `modalidade_compra`, `tipo_produto` e `flag_preco_atipico`. Exibir > Sincronizar segmentações, marcando as três páginas para todas elas.

- [ ] **Step 13: Salvar e exportar as capturas**

Salvar como `dashboard/BPS_2020_2026.pbix`. Exportar uma captura PNG de cada página para `dashboard/img/`.

- [ ] **Step 14: Conferir o tamanho do `.pbix` e commitar**

```bash
ls -lh dashboard/
```

Se passar de 100 MB, parar e reavaliar (o esperado é bem menos). Se ficar entre 50 e 100 MB, o GitHub aceita mas emite aviso.

```bash
git add dashboard/
git commit -m "feat: dashboard Power BI com tres paginas, seis KPIs e filtros sincronizados"
```

- [ ] **Step 15: Merge e push, respeitando o intervalo**

```bash
git checkout main
git merge --no-ff feat/dashboard-powerbi -m "merge: dashboard Power BI"
git log --format=%B | grep -ci "claude\|co-authored"   # tem de ser 0
git push origin main
```

---

## Task 10: README

**Branch:** `docs/readme`

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: `docs/perfil_discrepancias.md` da Task 3; as capturas de `dashboard/img/` da Task 9; os números impressos pela Task 8.
- Produces: o placeholder da seção de vídeo, preenchido na Task 11.

- [ ] **Step 1: Criar a branch**

```bash
git checkout -b docs/readme
```

- [ ] **Step 2: Escrever o README com as doze seções exigidas**

Na ordem do enunciado, sem pular nenhuma:

1. **Objetivo do projeto**
2. **Contextualização do problema** — gestão de recursos públicos em saúde, o papel do BPS
3. **Fonte dos dados** — link do dataset e do dicionário oficial
3b. **Perguntas de negócio** — as oito perguntas da seção 3 do spec, cada uma apontando a página do dashboard que a responde. Não está na lista de seções do enunciado, mas o critério 06 da rubrica pontua a formulação delas, e sem uma seção própria não há onde o avaliador ler isso.
4. **Procedimentos de download e concatenação** — os sete `.zip`, `src/io_bps.py` e `src/consolidar.py`, com o comando exato
5. **Tratamentos e transformações** — a tabela da seção 5.3 do spec, tratamento por tratamento, com a contagem de linhas afetadas
6. **Descrição das principais colunas** — as 25 originais mais as 8 derivadas
7. **Definição dos KPIs e métricas** — as seis medidas com o DAX, explicando a contagem por CNPJ e a razão de somas
8. **Imagens do dashboard** — as três capturas de `dashboard/img/`
9. **Principais análises e descobertas** — a seção 7.1 do spec: o registro de 29%, a inversão PR/SP, a queda de volume pós-2022, a dispersão explicada por unidade de fornecimento
10. **Recomendações** — verificar os 4.922 registros sinalizados antes de usar a base para referência de preço; usar preço mediano por grupo comparável em vez de média; considerar a ausência de AM, AP e DF
11. **Limitações** — 24 de 27 UFs, 2026 parcial até 05/03, `capacidade` e `unidade_medida` nulos em 63%, o flag é indício e não prova
12. **Instruções para reprodução** — `pip install -r requirements.txt`, `python -m src.perfil_dados`, `python -m src.consolidar`, abrir o `.pbix`

Incluir a seção de vídeo com o placeholder:

```markdown
## 🎥 Vídeo de apresentação

_Link do vídeo será adicionado aqui após a gravação._
```

- [ ] **Step 3: Conferir que nada no README credita o Claude**

```bash
grep -ci "claude" README.md
```

Expected: `0`.

- [ ] **Step 4: Conferir integridade e commitar**

```bash
wc -l README.md
git add README.md
git commit -m "docs: readme com objetivo, tratamentos, KPIs, achados e reproducao"
```

- [ ] **Step 5: Merge e push, respeitando o intervalo**

```bash
git checkout main
git merge --no-ff docs/readme -m "merge: documentacao do readme"
git log --format=%B | grep -ci "claude\|co-authored"   # tem de ser 0
git push origin main
```

---

## Task 11: Roteiro, gravação e link do vídeo

**Branch:** `docs/video`

**Files:**
- Create: `docs/roteiro_video.md` (fica no `.gitignore`, só no disco)
- Modify: `README.md` — trocar o placeholder pelo link

**Interfaces:**
- Consumes: o dashboard da Task 9 e o README da Task 10.
- Produces: entrega final.

- [ ] **Step 1: Criar a branch**

```bash
git checkout -b docs/video
```

- [ ] **Step 2: Escrever o roteiro cobrindo as dez perguntas do item 4.1**

Objetivo do dashboard · problema investigado · como os arquivos foram obtidos e consolidados · tratamentos · como usar filtros e visuais · KPIs · resultados · recomendações · como as tarefas foram organizadas (o spec e este plano respondem isso diretamente) · o que faltou ou daria para melhorar.

Marcar cada fala com `> "` no início da linha, para o contador conseguir medir.

- [ ] **Step 3: Medir o roteiro por contagem de palavras**

Nunca estimar no olho — na entrega anterior a estimativa errou 40% duas vezes seguidas.

```bash
python - <<'EOF'
import re
from pathlib import Path

falas = [
    l for l in Path("docs/roteiro_video.md").read_text(encoding="utf-8").splitlines()
    if l.strip().startswith('> "')
]
palavras = sum(len(re.findall(r"\S+", l)) for l in falas)
for ritmo, nome in ((140, "lento"), (150, "normal"), (165, "rapido")):
    print(f"{nome:>7}: {palavras / ritmo * 60:5.0f}s para {palavras} palavras")
EOF
```

Alvo: até 600 palavras, deixando margem para o tempo de tela dentro dos 5 minutos. Se passar, cortar por bloco com alvo numérico, protegendo os blocos de KPIs e de achados.

- [ ] **Step 4: Gravar o vídeo**

Rosto visível, boa iluminação, tela do dashboard demonstrada, no máximo 5 minutos.

- [ ] **Step 5: Hospedar e pegar o link**

Subir para uma pasta do Google Drive em modo leitor para qualquer pessoa com o link. Conferir o acesso em uma janela anônima antes de colar o link.

- [ ] **Step 6: Colar o link no README**

Substituir a linha em itálico pelo link. Conferir:

```bash
grep -A2 "Vídeo de apresentação" README.md
```

- [ ] **Step 7: Commitar**

```bash
git add README.md
git commit -m "docs: link do video de apresentacao"
git status --short   # docs/roteiro_video.md nao pode aparecer
```

- [ ] **Step 8: Merge e push final**

```bash
git checkout main
git merge --no-ff docs/video -m "merge: link do video de apresentacao"
git log --format=%B | grep -ci "claude\|co-authored"   # tem de ser 0
git push origin main
```

- [ ] **Step 9: Conferência final antes de submeter no AVA**

```bash
git log --oneline --graph --all | head -40
gh repo view --web
```

Conferir na página do repositório: **Contributors = 1**, os sete `.zip` em `data/raw/`, o `.zip` consolidado em `data/processed/`, o `.pbix` e as três imagens em `dashboard/`, o README renderizando as capturas e o link do vídeo abrindo em janela anônima.

Submeter no AVA o link do repositório e o link do vídeo.

---

## Cobertura da rubrica

| Critério | Task |
|---|---|
| 01 — Versionamento com branches e commits | Todas (7 branches, merges `--no-ff`) |
| 02 — Organização dos arquivos e README | 1, 10 |
| 03 — Gravação de vídeo | 11 |
| 04 — Download e organização da base | 1 |
| 05 — Mapeamento de discrepâncias | 3 |
| 06 — Formulação de perguntas de negócio | 10 (spec §3) |
| 07 — Tratamento de encoding e acentuação | 5 |
| 08 — Nulos, inconsistências e duplicatas | 5, 6 |
| 09 — Junção de todas as bases anuais | 4, 8 |
| 10 — Estruturação de KPIs e métricas | 9 (Steps 6–8) |
| 11 — KPIs mínimos funcionando dinamicamente | 9 |
| 12 — Cinco visuais mais filtros interativos | 9 (13 visuais) |
| 13 — Organização visual e legibilidade | 9 |
