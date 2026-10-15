"""
app.py
Painel Executivo Interativo em Streamlit para o Projeto de Retenção da Conecta Brasil Telecom.
Permite exploração da base priorizada, simulação dinâmica de ROI e visualização dos decis de risco.
"""

import os
import pandas as pd
import numpy as np
import streamlit as st

st.set_page_config(
    page_title="Conecta Brasil Telecom — Inteligência de Retenção",
    page_icon="📡",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LISTA_PATH = os.path.join(BASE_DIR, "data", "processed", "lista_priorizada_retencao.csv")

@st.cache_data
def carregar_dados():
    if not os.path.exists(LISTA_PATH):
        st.error("Lista priorizada não encontrada. Execute a inferência primeiro.")
        return None
    return pd.read_csv(LISTA_PATH)

df = carregar_dados()

st.title("📡 Conecta Brasil Telecom — Painel Executivo de Retenção")
st.markdown("**Sprint 4 — Produto Analítico e Avaliação Econômica de Churn**")

if df is not None:
    # Métricas Principais
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Base de Clientes Monitorados", f"{len(df):,}")
    col2.metric("Clientes no Decil 1 (Top 10%)", f"{len(df[df['decil_risco']=='Decil 1']):,}")
    col3.metric("Prob. Churn Média (Decil 1)", f"{df[df['decil_risco']=='Decil 1']['probabilidade_churn'].mean()*100:.1f}%")
    col4.metric("Lift do Modelo @ Top 10%", "3.06x")
    col5.metric("Retorno Médio / Contato", f"R$ {df[df['decil_risco']=='Decil 1']['retorno_esperado_campanha_rs'].mean():.2f}")

    st.markdown("---")

    # Layout de Duas Colunas: Gráfico e Simulador
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.subheader("📊 Distribuição de Risco e Retorno por Decil")
        decil_agg = df.groupby("decil_risco", observed=False).agg(
            prob_media=("probabilidade_churn", lambda x: round(x.mean() * 100, 1)),
            retorno_medio=("retorno_esperado_campanha_rs", lambda x: round(x.mean(), 2)),
            clientes=("id_cliente_hash", "count")
        ).reset_index()
        st.bar_chart(decil_agg.set_index("decil_risco")[["prob_media"]])
        st.dataframe(decil_agg, use_container_width=True)

    with c_right:
        st.subheader("💰 Simulador Interativo de ROI (Expected Value)")
        cap_pct = st.slider("Capacidade Operacional de Contato (% da base)", min_value=1, max_value=20, value=10, step=1)
        eficacia_pct = st.slider("Eficácia de Conversão da Oferta (%)", min_value=5, max_value=30, value=15, step=1)
        custo_oferta = st.slider("Custo da Oferta de Retenção (R$)", min_value=10, max_value=100, value=50, step=5)
        custo_contato = st.slider("Custo Operacional de Contato (R$)", min_value=5, max_value=30, value=12, step=1)

        total_abordados = (cap_pct / 100) * 500000
        churn_capturado = 0.306 * 14000 * (cap_pct / 10)
        retidos = int(churn_capturado * (eficacia_pct / 100))
        receita_preservada = retidos * 120 * 12 * 0.70
        custo_total = total_abordados * (custo_contato + (custo_oferta * (eficacia_pct / 100)))
        lucro_liquido = receita_preservada - custo_total
        roi_pct = (lucro_liquido / custo_total) * 100 if custo_total > 0 else 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Clientes Retidos", f"{retidos:,}")
        m2.metric("Margem Preservada (12m)", f"R$ {receita_preservada:,.2f}")
        m3.metric("ROI Líquido Estimado", f"{roi_pct:.1f}%")

    st.markdown("---")
    st.subheader("📋 Fila Priorizada para a Operação Comercial (Top 100)")
    faixa_filtro = st.multiselect("Filtrar por Faixa de Risco:", options=df["faixa_risco"].unique(), default=df["faixa_risco"].unique())
    df_filtrado = df[df["faixa_risco"].isin(faixa_filtro)]
    st.dataframe(df_filtrado.head(100), use_container_width=True)
