"""
test_data_quality.py
Testes automatizados com pytest para validação de integridade e qualidade dos dados.
"""

import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

@pytest.fixture(scope="module")
def tabelas_brutas():
    tabelas = {}
    for nome in ["clientes", "contratos", "faturamento", "atendimento", "rede", "cancelamentos"]:
        p = os.path.join(RAW_DIR, f"{nome}.csv")
        assert os.path.exists(p), f"Arquivo bruto {p} não foi encontrado!"
        tabelas[nome] = pd.read_csv(p)
    return tabelas

def test_unicidade_chaves_primarias(tabelas_brutas):
    pk_map = {
        "clientes": "id_cliente",
        "contratos": "id_contrato",
        "faturamento": "id_fatura",
        "atendimento": "id_chamado",
        "rede": "id_evento_rede",
        "cancelamentos": "id_cancelamento"
    }
    for tab_nome, pk in pk_map.items():
        df = tabelas_brutas[tab_nome]
        assert df[pk].nunique() == len(df), f"Chave primária {pk} na tabela {tab_nome} possui duplicatas!"

def test_integridade_referencial_clientes(tabelas_brutas):
    ids_clientes_validos = set(tabelas_brutas["clientes"]["id_cliente"])
    for tab_nome in ["contratos", "faturamento", "atendimento", "rede", "cancelamentos"]:
        df = tabelas_brutas[tab_nome]
        orfaos = df[~df["id_cliente"].isin(ids_clientes_validos)]
        assert len(orfaos) == 0, f"Encontrados {len(orfaos)} registros órfãos na tabela {tab_nome}!"

def test_regras_negocio_faturamento(tabelas_brutas):
    df_fat = tabelas_brutas["faturamento"]
    assert (df_fat["valor_fatura"] > 0).all(), "Existem faturas com valor menor ou igual a zero!"
    assert (df_fat["dias_atraso"] >= 0).all(), "Existem faturas com dias de atraso negativos!"
    assert df_fat["status_pagamento"].isin(["Pago em dia", "Pago com atraso", "Inadimplente"]).all(), "Status de pagamento inválido!"

def test_abt_alvo_binario():
    p_train = os.path.join(PROCESSED_DIR, "abt_churn_train.parquet")
    p_oot = os.path.join(PROCESSED_DIR, "abt_churn_oot.parquet")
    
    assert os.path.exists(p_train), "ABT de treino não encontrada!"
    assert os.path.exists(p_oot), "ABT Out-of-Time não encontrada!"
    
    df_train = pd.read_parquet(p_train)
    df_oot = pd.read_parquet(p_oot)
    
    assert set(df_train["churn_30d"].unique()).issubset({0, 1}), "Variável alvo de treino não é binária {0, 1}!"
    assert set(df_oot["churn_30d"].unique()).issubset({0, 1}), "Variável alvo OOT não é binária {0, 1}!"
    assert df_train["churn_30d"].mean() > 0, "Alvo de treino possui 0 positivos!"
    assert df_oot["churn_30d"].mean() > 0, "Alvo OOT possui 0 positivos!"
