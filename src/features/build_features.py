"""
build_features.py
Engenharia de Atributos e Construção da Base Analítica (ABT - Analytical Base Table)
com rigorosa validação temporal (Point-in-Time) e salvaguardas de privacidade (LGPD).

Gera duas safras analíticas:
1. Safra de Treino/Validação: T_0 = 2024-05-01 (Alvo observado em maio/2024)
2. Safra Fora do Tempo (OOT): T_0 = 2024-06-01 (Alvo observado em junho/2024)

Salva em formato Parquet de alta performance:
- data/processed/abt_churn_train.parquet
- data/processed/abt_churn_oot.parquet
"""

import os
import hashlib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

SECRET_SALT = "ConectaBrasil_LGPD_2026_SecSalt"

def pseudonimizar_id(cid):
    raw = f"{cid}_{SECRET_SALT}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]

def carregar_bases_brutas():
    print("[*] Carregando bases brutas para engenharia de atributos...")
    df_clientes = pd.read_csv(os.path.join(RAW_DATA_DIR, "clientes.csv"))
    df_contratos = pd.read_csv(os.path.join(RAW_DATA_DIR, "contratos.csv"))
    df_faturamento = pd.read_csv(os.path.join(RAW_DATA_DIR, "faturamento.csv"))
    df_atendimento = pd.read_csv(os.path.join(RAW_DATA_DIR, "atendimento.csv"))
    df_rede = pd.read_csv(os.path.join(RAW_DATA_DIR, "rede.csv"))
    df_cancelamentos = pd.read_csv(os.path.join(RAW_DATA_DIR, "cancelamentos.csv"))
    
    # Conversão de tipos de data
    df_clientes["data_cadastro"] = pd.to_datetime(df_clientes["data_cadastro"])
    df_faturamento["data_vencimento"] = pd.to_datetime(df_faturamento["data_vencimento"])
    df_atendimento["data_abertura"] = pd.to_datetime(df_atendimento["data_abertura"])
    df_rede["data_evento"] = pd.to_datetime(df_rede["data_evento"])
    df_cancelamentos["data_cancelamento"] = pd.to_datetime(df_cancelamentos["data_cancelamento"])
    
    return {
        "clientes": df_clientes,
        "contratos": df_contratos,
        "faturamento": df_faturamento,
        "atendimento": df_atendimento,
        "rede": df_rede,
        "cancelamentos": df_cancelamentos
    }

def construir_abt_safra(tabelas, t_corte, dias_horizonte=30):
    """
    Constrói uma Analytical Base Table estritamente no ponto de corte t_corte.
    NENHUM evento posterior a t_corte é utilizado nas features (prevenção de Data Leakage).
    """
    print(f"\n[+] Construindo ABT para o ponto de corte: {t_corte.strftime('%Y-%m-%d')} (Horizonte: {dias_horizonte} dias)")
    
    df_cli = tabelas["clientes"].copy()
    df_ctr = tabelas["contratos"].copy()
    df_fat = tabelas["faturamento"].copy()
    df_ate = tabelas["atendimento"].copy()
    df_red = tabelas["rede"].copy()
    df_cnc = tabelas["cancelamentos"].copy()
    
    # 1. Filtro de Elegibilidade no instante t_corte:
    # Cliente cadastrado com pelo menos 30 dias de casa
    limite_cadastro = t_corte - timedelta(days=30)
    df_elegiveis = df_cli[df_cli["data_cadastro"] <= limite_cadastro].copy()
    
    # Excluir clientes que já haviam cancelado antes ou no dia do corte
    canc_anteriores = set(df_cnc[df_cnc["data_cancelamento"] <= t_corte]["id_cliente"])
    df_elegiveis = df_elegiveis[~df_elegiveis["id_cliente"].isin(canc_anteriores)].copy()
    
    print(f" -> Clientes ativos elegíveis em {t_corte.strftime('%Y-%m-%d')}: {len(df_elegiveis):,}")
    
    # 2. Definição da Variável-Alvo (Target Y):
    # Cliente cancelou nos 30 dias subsequentes? (t_corte, t_corte + 30 dias]
    dt_fim_alvo = t_corte + timedelta(days=dias_horizonte)
    canc_no_horizonte = set(
        df_cnc[
            (df_cnc["data_cancelamento"] > t_corte) & 
            (df_cnc["data_cancelamento"] <= dt_fim_alvo)
        ]["id_cliente"]
    )
    df_elegiveis["churn_30d"] = df_elegiveis["id_cliente"].apply(lambda cid: 1 if cid in canc_no_horizonte else 0)
    
    taxa_churn = df_elegiveis["churn_30d"].mean() * 100
    total_churns = df_elegiveis["churn_30d"].sum()
    print(f" -> Target churn_30d calculado: {total_churns:,} cancelamentos ({taxa_churn:.2f}% de prevalência)")
    
    # 3. Features Contratuais e Cadastrais (Privacy by Design - sem nome, CPF ou email)
    df_elegiveis["id_cliente_hash"] = df_elegiveis["id_cliente"].apply(pseudonimizar_id)
    df_elegiveis["tempo_relacionamento_meses_corte"] = (
        (t_corte - df_elegiveis["data_cadastro"]).dt.days / 30.4
    ).astype(int)
    
    # Merge com contratos
    df_abt = df_elegiveis[[
        "id_cliente", "id_cliente_hash", "regiao", "faixa_etaria", 
        "tempo_relacionamento_meses_corte", "churn_30d"
    ]].merge(
        df_ctr[["id_cliente", "tipo_plano", "fidelizacao_meses", "forma_pagamento"]],
        on="id_cliente",
        how="left"
    )
    df_abt["eh_fidelizado"] = (df_abt["fidelizacao_meses"] > 0).astype(int)
    
    # 4. Features de Faturamento (Point-in-Time: faturas vencidas até t_corte)
    dt_90d_ant = t_corte - timedelta(days=90)
    fat_corte = df_fat[
        (df_fat["data_vencimento"] <= t_corte) & 
        (df_fat["data_vencimento"] >= dt_90d_ant)
    ].copy()
    
    fat_agg = fat_corte.groupby("id_cliente").agg(
        media_valor_fatura_3m=("valor_fatura", "mean"),
        max_dias_atraso_3m=("dias_atraso", "max"),
        total_faturas_atrasadas_3m=("dias_atraso", lambda x: (x > 0).sum()),
        inadimplente_recente_flag=("dias_atraso", lambda x: int((x > 15).any()))
    ).reset_index()
    
    df_abt = df_abt.merge(fat_agg, on="id_cliente", how="left")
    df_abt["media_valor_fatura_3m"] = df_abt["media_valor_fatura_3m"].fillna(120.0).round(2)
    df_abt["max_dias_atraso_3m"] = df_abt["max_dias_atraso_3m"].fillna(0).astype(int)
    df_abt["total_faturas_atrasadas_3m"] = df_abt["total_faturas_atrasadas_3m"].fillna(0).astype(int)
    df_abt["inadimplente_recente_flag"] = df_abt["inadimplente_recente_flag"].fillna(0).astype(int)
    
    # 5. Features de Atendimento (Point-in-Time: chamados abertos até t_corte)
    dt_30d_ant = t_corte - timedelta(days=30)
    dt_60d_ant = t_corte - timedelta(days=60)
    
    ate_corte = df_ate[df_ate["data_abertura"] <= t_corte].copy()
    
    # Chamados 30d
    c30 = ate_corte[ate_corte["data_abertura"] >= dt_30d_ant].groupby("id_cliente").size().rename("total_chamados_30d")
    # Chamados 60d
    c60 = ate_corte[ate_corte["data_abertura"] >= dt_60d_ant].groupby("id_cliente").size().rename("total_chamados_60d")
    # Chamados 90d
    c90 = ate_corte[ate_corte["data_abertura"] >= dt_90d_ant].groupby("id_cliente").size().rename("total_chamados_90d")
    
    # Chamados específicos 60d
    ate_60 = ate_corte[ate_corte["data_abertura"] >= dt_60d_ant]
    lentidao_60 = ate_60[ate_60["motivo_chamado"] == "Lentidão ou Queda de Conexão"].groupby("id_cliente").size().rename("chamados_lentidao_60d")
    cobranca_60 = ate_60[ate_60["motivo_chamado"] == "Cobrança Indevida"].groupby("id_cliente").size().rename("chamados_cobranca_60d")
    fcr_60 = ate_60.groupby("id_cliente")["resolvido_primeiro_contato"].mean().rename("taxa_fcr_atendimento_60d")
    
    # Flag Imprevisto 1: chamado durante a migração
    cham_migracao = ate_corte[
        (ate_corte["data_abertura"] >= dt_90d_ant) & 
        (ate_corte["sistema_origem"] == "Sistema_Migracao_Incompleta")
    ].groupby("id_cliente").size().rename("chamados_sistema_migracao_flag")
    
    df_abt = df_abt.merge(c30, on="id_cliente", how="left")
    df_abt = df_abt.merge(c60, on="id_cliente", how="left")
    df_abt = df_abt.merge(c90, on="id_cliente", how="left")
    df_abt = df_abt.merge(lentidao_60, on="id_cliente", how="left")
    df_abt = df_abt.merge(cobranca_60, on="id_cliente", how="left")
    df_abt = df_abt.merge(fcr_60, on="id_cliente", how="left")
    df_abt = df_abt.merge(cham_migracao, on="id_cliente", how="left")
    
    df_abt["total_chamados_30d"] = df_abt["total_chamados_30d"].fillna(0).astype(int)
    df_abt["total_chamados_60d"] = df_abt["total_chamados_60d"].fillna(0).astype(int)
    df_abt["total_chamados_90d"] = df_abt["total_chamados_90d"].fillna(0).astype(int)
    df_abt["chamados_lentidao_60d"] = df_abt["chamados_lentidao_60d"].fillna(0).astype(int)
    df_abt["chamados_cobranca_60d"] = df_abt["chamados_cobranca_60d"].fillna(0).astype(int)
    df_abt["taxa_fcr_atendimento_60d"] = df_abt["taxa_fcr_atendimento_60d"].fillna(1.0).round(2)
    df_abt["chamados_sistema_migracao_flag"] = (df_abt["chamados_sistema_migracao_flag"].fillna(0) > 0).astype(int)
    
    # 6. Features de Rede e Telemetria (Point-in-Time: eventos até t_corte)
    red_corte = df_red[
        (df_red["data_evento"] <= t_corte) & 
        (df_red["data_evento"] >= dt_60d_ant)
    ].copy()
    
    red_agg = red_corte.groupby("id_cliente").agg(
        total_eventos_rede_60d=("id_evento_rede", "count"),
        duracao_quedas_min_60d=("duracao_queda_minutos", "sum"),
        taxa_media_perda_pacotes_60d=("taxa_perda_pacotes", "mean"),
        latencia_media_ms_60d=("latencia_media_ms", "mean")
    ).reset_index()
    
    df_abt = df_abt.merge(red_agg, on="id_cliente", how="left")
    df_abt["total_eventos_rede_60d"] = df_abt["total_eventos_rede_60d"].fillna(0).astype(int)
    df_abt["duracao_quedas_min_60d"] = df_abt["duracao_quedas_min_60d"].fillna(0).astype(int)
    df_abt["taxa_media_perda_pacotes_60d"] = df_abt["taxa_media_perda_pacotes_60d"].fillna(1.5).round(2)
    df_abt["latencia_media_ms_60d"] = df_abt["latencia_media_ms_60d"].fillna(22.0).round(1)
    
    # Indicador de instabilidade crítica de rede
    df_abt["instabilidade_critica_flag"] = (
        (df_abt["duracao_quedas_min_60d"] > 180) | 
        (df_abt["taxa_media_perda_pacotes_60d"] > 5.0)
    ).astype(int)
    
    return df_abt

def main():
    print("=== INICIANDO CONSTRUÇÃO DAS BASES ANALÍTICAS TEMPORAIS (ABT) ===")
    tabelas = carregar_bases_brutas()
    
    # Safra de Treinamento: Corte em 2024-05-01 (Alvo observado em maio/2024)
    t_treino = datetime(2024, 5, 1)
    df_train = construir_abt_safra(tabelas, t_treino, dias_horizonte=31)
    train_path = os.path.join(PROCESSED_DATA_DIR, "abt_churn_train.parquet")
    df_train.to_parquet(train_path, index=False)
    print(f"[+] Safra de Treino salva com sucesso: {train_path} ({len(df_train):,} linhas)")
    
    # Safra Out-of-Time (OOT) de Teste: Corte em 2024-06-01 (Alvo observado em junho/2024)
    t_teste = datetime(2024, 6, 1)
    df_oot = construir_abt_safra(tabelas, t_teste, dias_horizonte=30)
    oot_path = os.path.join(PROCESSED_DATA_DIR, "abt_churn_oot.parquet")
    df_oot.to_parquet(oot_path, index=False)
    print(f"[+] Safra Out-of-Time salva com sucesso: {oot_path} ({len(df_oot):,} linhas)")
    
    print("\n=== ENGENHARIA DE ATRIBUTOS CONCLUÍDA COM SUCESSO ===")

if __name__ == "__main__":
    main()
