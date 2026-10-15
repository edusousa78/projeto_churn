"""
inference_pipeline.py
Esteira de inferência produtiva do modelo de Churn da Conecta Brasil Telecom.
Lê os dados mais recentes de clientes ativos, aplica o modelo treinado,
calcula probabilidades calibradas, classifica em faixas e decis de risco,
calcula o Valor Econômico Esperado (EV) de retenção e exporta a lista
priorizada pseudonimizada para a Gerência de Retenção.

Saída: data/processed/lista_priorizada_retencao.csv
"""

import os
import joblib
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "src", "models", "saved_models")
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "lista_priorizada_retencao.csv")

# Premissas Financeiras de Retenção (Validadas com Finanças e Comercial)
TAXA_SUCESSO_RETENCAO = 0.15  # 15% de eficácia incremental da campanha de contato
MARGEM_CONTRIBUICAO = 0.70    # 70% de margem de contribuição média do serviço
HORIZONTE_MESES_LTV = 12       # 12 meses de retenção preservada no cálculo
CUSTO_OFERTA_DESCONTO = 50.0  # R$ 50,00 de desconto ou benefício concedido
CUSTO_OPERACIONAL_CONTATO = 12.0 # R$ 12,00 por tentativa/contato de telemarketing

def carregar_modelo():
    model_path = os.path.join(MODELS_DIR, "best_churn_model.joblib")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Modelo não encontrado em: {model_path}. Execute o treino primeiro.")
    print(f"[*] Carregando modelo campeão de: {model_path}")
    return joblib.load(model_path)

def carregar_dados_inferencia():
    # Utiliza o snapshot mais recente para inferência operacional (safra OOT)
    input_path = os.path.join(PROCESSED_DIR, "abt_churn_oot.parquet")
    print(f"[*] Carregando snapshot de clientes para inferência: {input_path}")
    return pd.read_parquet(input_path)

def executar_inferencia(df, modelo):
    cat_cols = ["regiao", "faixa_etaria", "tipo_plano", "forma_pagamento"]
    num_cols = [
        "tempo_relacionamento_meses_corte", "fidelizacao_meses", "eh_fidelizado",
        "media_valor_fatura_3m", "max_dias_atraso_3m", "total_faturas_atrasadas_3m",
        "inadimplente_recente_flag", "total_chamados_30d", "total_chamados_60d",
        "total_chamados_90d", "chamados_lentidao_60d", "chamados_cobranca_60d",
        "taxa_fcr_atendimento_60d", "chamados_sistema_migracao_flag",
        "total_eventos_rede_60d", "duracao_quedas_min_60d",
        "taxa_media_perda_pacotes_60d", "latencia_media_ms_60d",
        "instabilidade_critica_flag"
    ]
    
    X = df[cat_cols + num_cols]
    
    print("[*] Estimando probabilidades de cancelamento...")
    probs = modelo.predict_proba(X)[:, 1]
    
    df_out = df[[
        "id_cliente_hash", "regiao", "tipo_plano", "eh_fidelizado", 
        "media_valor_fatura_3m", "total_chamados_60d", "duracao_quedas_min_60d"
    ]].copy()
    
    df_out["probabilidade_churn"] = np.round(probs, 4)
    
    # 1. Atribuição de Decis de Risco (Decil 1 = Maior Risco, Decil 10 = Menor Risco)
    df_out["decil_risco"] = pd.qcut(
        df_out["probabilidade_churn"].rank(method="first", ascending=False),
        q=10,
        labels=[f"Decil {i}" for i in range(1, 11)]
    )
    
    # 2. Faixa Operacional de Risco
    def categorizar_faixa(prob):
        if prob >= 0.20:
            return "Crítico"
        elif prob >= 0.10:
            return "Alto"
        elif prob >= 0.04:
            return "Médio"
        else:
            return "Baixo"
            
    df_out["faixa_risco"] = df_out["probabilidade_churn"].apply(categorizar_faixa)
    
    # 3. Cálculo do Retorno Financeiro Esperado (Expected Value - ADR-003)
    # LTV_12m = media_valor_fatura_3m * 12 * 0.70
    ltv_esperado = df_out["media_valor_fatura_3m"] * HORIZONTE_MESES_LTV * MARGEM_CONTRIBUICAO
    beneficio_bruto_retencao = df_out["probabilidade_churn"] * TAXA_SUCESSO_RETENCAO * ltv_esperado
    custo_total_acao = CUSTO_OFERTA_DESCONTO + CUSTO_OPERACIONAL_CONTATO
    
    df_out["retorno_esperado_campanha_rs"] = np.round(beneficio_bruto_retencao - custo_total_acao, 2)
    
    # 4. Ação Recomendada para a Gerência de Retenção
    def definir_acao(row):
        if row["decil_risco"] in ["Decil 1", "Decil 2"] and row["retorno_esperado_campanha_rs"] > 0:
            return "Contato Prioritário Imediato (Oferta Premium)"
        elif row["decil_risco"] in ["Decil 3"] and row["retorno_esperado_campanha_rs"] > 0:
            return "Contato Digital / WhatsApp (Oferta Padrão)"
        elif row["retorno_esperado_campanha_rs"] <= 0 and row["faixa_risco"] in ["Crítico", "Alto"]:
            return "Monitorar sem Oferta (Risco Alto, Margem Baixa)"
        else:
            return "Sem Ação Preventiva (Fluxo Padrão)"
            
    df_out["acao_recomendada"] = df_out.apply(definir_acao, axis=1)
    
    # Ordenar pelo maior retorno financeiro esperado
    df_out = df_out.sort_values(by=["retorno_esperado_campanha_rs", "probabilidade_churn"], ascending=[False, False])
    return df_out

def main():
    print("=== INICIANDO PIPELINE DE INFERÊNCIA OPERACIONAL ===")
    modelo = carregar_modelo()
    df_input = carregar_dados_inferencia()
    df_priorizada = executar_inferencia(df_input, modelo)
    
    df_priorizada.to_csv(OUTPUT_PATH, index=False)
    print(f"[+] Lista priorizada exportada com sucesso em: {OUTPUT_PATH}")
    print(f" -> Total de clientes ranqueados: {len(df_priorizada):,}")
    
    top_10 = df_priorizada[df_priorizada["decil_risco"] == "Decil 1"]
    print(f" -> Clientes no Decil 1 (Top 10% mais arriscados): {len(top_10):,}")
    print(f" -> Probabilidade média de churn no Decil 1: {top_10['probabilidade_churn'].mean()*100:.1f}%")
    print(f" -> Retorno financeiro esperado médio no Decil 1: R$ {top_10['retorno_esperado_campanha_rs'].mean():.2f}/cliente")
    print("=== PIPELINE DE INFERÊNCIA CONCLUÍDO ===")

if __name__ == "__main__":
    main()
