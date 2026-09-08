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


def test_relatorio_descreve_o_esquema_da_fonte_sem_a_coluna_de_proveniencia():
    """`arquivo_origem` é acrescentada pela leitura, não vem do BPS.

    Contá-la faria o relatório afirmar 26 colunas de origem onde a fonte tem
    25, exatamente o número que o README e o dicionário de dados declaram.
    """
    frames = {
        2020: pd.DataFrame({"uf": ["PA"], "arquivo_origem": ["2020.csv"]}),
        2021: pd.DataFrame({"uf": ["SP"], "arquivo_origem": ["2021.csv"]}),
    }

    relatorio = montar_relatorio(frames)

    assert "as mesmas 1 colunas" in relatorio
    assert "`arquivo_origem`" not in relatorio


def test_comparar_colunas_ignora_a_coluna_de_proveniencia():
    frames = {
        2020: pd.DataFrame({"uf": ["PA"], "arquivo_origem": ["2020.csv"]}),
        2021: pd.DataFrame({"uf": ["SP"], "arquivo_origem": ["2021.csv"]}),
    }

    assert comparar_colunas(frames) == {}
