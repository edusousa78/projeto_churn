"""
test_inference_pipeline.py
Testes automatizados com pytest para validação da esteira produtiva de inferência e regras de ranking.
"""

import os
import pytest
import joblib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "src", "models", "saved_models")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
LISTA_PATH = os.path.join(PROCESSED_DIR, "lista_priorizada_retencao.csv")

def test_modelo_campeao_salvo():
    p = os.path.join(MODELS_DIR, "best_churn_model.joblib")
    assert os.path.exists(p), "Arquivo serializado do modelo campeão não encontrado!"
    modelo = joblib.load(p)
    assert hasattr(modelo, "predict_proba"), "Modelo carregado não possui método predict_proba!"

def test_lista_priorizada_retencao():
    assert os.path.exists(LISTA_PATH), "Arquivo lista_priorizada_retencao.csv não foi gerado!"
    df = pd.read_csv(LISTA_PATH)
    
    colunas_obrigatorias = [
        "id_cliente_hash", "regiao", "tipo_plano", "eh_fidelizado",
        "media_valor_fatura_3m", "total_chamados_60d", "duracao_quedas_min_60d",
        "probabilidade_churn", "decil_risco", "faixa_risco",
        "retorno_esperado_campanha_rs", "acao_recomendada"
    ]
    for col in colunas_obrigatorias:
        assert col in df.columns, f"Coluna obrigatória '{col}' ausente na lista priorizada!"
        
    assert ((df["probabilidade_churn"] >= 0.0) & (df["probabilidade_churn"] <= 1.0)).all(), "Probabilidades fora do intervalo [0, 1]!"
    assert set(df["faixa_risco"].unique()).issubset({"Crítico", "Alto", "Médio", "Baixo"}), "Faixa de risco contém valores inválidos!"
    
    # Validação de Decis
    decil_1 = df[df["decil_risco"] == "Decil 1"]
    prop_decil_1 = len(decil_1) / len(df)
    assert abs(prop_decil_1 - 0.10) < 0.02, f"Decil 1 não contém ~10% da base (contém {prop_decil_1*100:.1f}%)!"
