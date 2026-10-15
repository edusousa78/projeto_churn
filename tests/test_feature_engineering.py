"""
test_feature_engineering.py
Testes automatizados com pytest para validação da esteira de atributos e salvaguardas LGPD.
"""

import os
import pytest
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

@pytest.fixture(scope="module")
def abt_treino():
    p = os.path.join(PROCESSED_DIR, "abt_churn_train.parquet")
    assert os.path.exists(p), "Arquivo abt_churn_train.parquet não existe!"
    return pd.read_parquet(p)

def test_expurgo_pii_lgpd(abt_treino):
    pii_proibidos = ["nome_cliente", "cpf", "email", "telefone", "endereco"]
    for col in pii_proibidos:
        assert col not in abt_treino.columns, f"Violação de LGPD: Coluna de PII '{col}' detectada na base analítica!"

def test_pseudonimizacao_id(abt_treino):
    assert "id_cliente_hash" in abt_treino.columns, "Coluna id_cliente_hash não encontrada na ABT!"
    assert (abt_treino["id_cliente_hash"].str.len() == 16).all(), "Hash de pseudonimização não possui 16 caracteres!"
    assert abt_treino["id_cliente_hash"].nunique() == len(abt_treino), "Existem colisões de hash na base!"

def test_features_obrigatorias_presentes(abt_treino):
    features_esperadas = [
        "tempo_relacionamento_meses_corte", "eh_fidelizado", "fidelizacao_meses",
        "media_valor_fatura_3m", "max_dias_atraso_3m", "total_faturas_atrasadas_3m",
        "inadimplente_recente_flag", "total_chamados_30d", "total_chamados_60d",
        "total_chamados_90d", "chamados_lentidao_60d", "chamados_cobranca_60d",
        "taxa_fcr_atendimento_60d", "chamados_sistema_migracao_flag",
        "total_eventos_rede_60d", "duracao_quedas_min_60d",
        "taxa_media_perda_pacotes_60d", "latencia_media_ms_60d",
        "instabilidade_critica_flag"
    ]
    for feat in features_esperadas:
        assert feat in abt_treino.columns, f"Atributo preditivo essencial '{feat}' ausente da ABT!"
        assert not abt_treino[feat].isnull().any(), f"Atributo '{feat}' possui valores nulos na ABT!"
