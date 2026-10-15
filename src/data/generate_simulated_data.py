"""
generate_simulated_data.py
Gera bases de dados sintéticas hiper-realistas para o cenário corporativo da Conecta Brasil Telecom.
Simula dados de 25.000 clientes (amostra representativa da base de 500k, taxa de churn mensal de ~2,8%,
ARPU de ~R$ 120,00, histórico de faturamento, chamados com anomalia de migração e falhas de rede).
Exporta arquivos CSV brutos em data/raw/ e popula o banco relacional SQLite data/conecta_brasil.db.
"""

import os
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Configurações de reprodutibilidade
SEED = 42
np.random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
DB_PATH = os.path.join(BASE_DIR, "data", "conecta_brasil.db")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

N_CLIENTES = 25000  # Amostra estratificada escalável (5% da base de 500k)
DATA_INICIO_HISTORICO = datetime(2023, 7, 1)
DATA_FIM_HISTORICO = datetime(2024, 7, 1)

def gerar_clientes(n):
    print(f"[*] Gerando {n} clientes...")
    ids = [f"CLI_{i:06d}" for i in range(1, n + 1)]
    
    regioes = ["Sudeste", "Sul", "Nordeste", "Centro-Oeste", "Norte"]
    prob_regioes = [0.45, 0.20, 0.18, 0.10, 0.07]
    
    faixas_etarias = ["18-25", "26-35", "36-50", "51-65", "65+"]
    prob_faixas = [0.12, 0.35, 0.32, 0.15, 0.06]
    
    generos = ["F", "M", "Outro"]
    prob_generos = [0.49, 0.49, 0.02]
    
    # Datas de cadastro distribuídas nos últimos 4 anos
    dias_cadastro = np.random.exponential(scale=450, size=n).clip(30, 1460).astype(int)
    datas_cadastro = [DATA_FIM_HISTORICO - timedelta(days=int(d)) for d in dias_cadastro]
    tempo_meses = [int(d / 30.4) for d in dias_cadastro]
    
    # Dados pessoais simulados para teste de conformidade LGPD (Sprint 2)
    primeiros_nomes = ["Ana", "Carlos", "Beatriz", "Lucas", "Mariana", "Gabriel", "Juliana", "Rodrigo", "Fernanda", "Rafael"]
    sobrenomes = ["Silva", "Santos", "Oliveira", "Souza", "Pereira", "Lima", "Carvalho", "Ferreira", "Ribeiro", "Almeida"]
    
    nomes = [f"{np.random.choice(primeiros_nomes)} {np.random.choice(sobrenomes)}" for _ in range(n)]
    cpfs = [f"{np.random.randint(100, 999)}.{np.random.randint(100, 999)}.{np.random.randint(100, 999)}-{np.random.randint(10, 99)}" for _ in range(n)]
    emails = [f"{nome.lower().replace(' ', '.')}{np.random.randint(10, 99)}@email.com" for nome in nomes]

    df_clientes = pd.DataFrame({
        "id_cliente": ids,
        "nome_cliente": nomes,
        "cpf": cpfs,
        "email": emails,
        "regiao": np.random.choice(regioes, size=n, p=prob_regioes),
        "faixa_etaria": np.random.choice(faixas_etarias, size=n, p=prob_faixas),
        "genero": np.random.choice(generos, size=n, p=prob_generos),
        "data_cadastro": [d.strftime("%Y-%m-%d") for d in datas_cadastro],
        "tempo_relacionamento_meses": tempo_meses
    })
    return df_clientes

def gerar_contratos(df_clientes):
    print("[*] Gerando contratos para cada cliente...")
    n = len(df_clientes)
    tipos_planos = [
        "Fibra 300MB", "Fibra 600MB", "Fibra 1GB", 
        "Combo Fibra+Movel", "Movel Individual", "Corporativo PME"
    ]
    prob_planos = [0.35, 0.28, 0.12, 0.15, 0.07, 0.03]
    
    fidelizacao = [0, 12, 24]
    prob_fidelidade = [0.25, 0.60, 0.15]
    
    formas_pagamento = ["Boleto Bancario", "Cartao Credito", "Debito Automatico", "PIX"]
    prob_pagamento = [0.42, 0.30, 0.18, 0.10]
    
    df_contratos = pd.DataFrame({
        "id_contrato": [f"CTR_{i:06d}" for i in range(1, n + 1)],
        "id_cliente": df_clientes["id_cliente"],
        "tipo_plano": np.random.choice(tipos_planos, size=n, p=prob_planos),
        "fidelizacao_meses": np.random.choice(fidelizacao, size=n, p=prob_fidelidade),
        "forma_pagamento": np.random.choice(formas_pagamento, size=n, p=prob_pagamento),
        "data_inicio": df_clientes["data_cadastro"]
    })
    return df_contratos

def gerar_faturamento(df_contratos):
    print("[*] Gerando faturamento mensal recorrente...")
    # Tabela de preços base para dar ARPU médio ~ R$ 120
    precos_base = {
        "Fibra 300MB": 99.90,
        "Fibra 600MB": 129.90,
        "Fibra 1GB": 179.90,
        "Combo Fibra+Movel": 149.90,
        "Movel Individual": 59.90,
        "Corporativo PME": 249.90
    }
    
    meses_ref = [
        "2023-07", "2023-08", "2023-09", "2023-10", "2023-11", "2023-12",
        "2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"
    ]
    
    registros = []
    fat_id = 1
    
    for _, row in df_contratos.iterrows():
        cli_id = row["id_cliente"]
        preco = precos_base[row["tipo_plano"]]
        data_inicio = datetime.strptime(row["data_inicio"], "%Y-%m-%d")
        
        # Perfil de inadimplência latente do cliente
        prob_atraso_base = 0.08 if row["forma_pagamento"] == "Boleto Bancario" else 0.02
        if np.random.rand() < 0.10:
            prob_atraso_base += 0.35  # Cliente com histórico de atrito financeiro
        
        for mes in meses_ref:
            dt_mes = datetime.strptime(f"{mes}-01", "%Y-%m-%d")
            if dt_mes < data_inicio.replace(day=1):
                continue
                
            valor = round(preco * np.random.uniform(0.95, 1.05), 2)
            dt_venc = dt_mes + timedelta(days=10)
            
            tem_atraso = np.random.rand() < prob_atraso_base
            if tem_atraso:
                dias_atraso = int(np.clip(np.random.exponential(scale=12), 1, 60))
                dt_pagto = dt_venc + timedelta(days=dias_atraso)
                status = "Pago com atraso" if dias_atraso < 45 else "Inadimplente"
                dt_pagto_str = dt_pagto.strftime("%Y-%m-%d") if status != "Inadimplente" else None
            else:
                dias_atraso = 0
                dt_pagto = dt_venc - timedelta(days=np.random.randint(0, 5))
                status = "Pago em dia"
                dt_pagto_str = dt_pagto.strftime("%Y-%m-%d")
                
            registros.append({
                "id_fatura": f"FAT_{fat_id:08d}",
                "id_cliente": cli_id,
                "mes_referencia": mes,
                "valor_fatura": valor,
                "data_vencimento": dt_venc.strftime("%Y-%m-%d"),
                "data_pagamento": dt_pagto_str,
                "dias_atraso": dias_atraso,
                "status_pagamento": status
            })
            fat_id += 1
            
    df_faturamento = pd.DataFrame(registros)
    return df_faturamento

def gerar_atendimento(df_clientes):
    print("[*] Gerando histórico de chamados (com anomalia de migração no CRM)...")
    # Imprevisto 1: Migração para nova plataforma entre 2024-03-01 e 2024-05-31
    # Durante esses 3 meses, chamados registraram dados ausentes ou não foram logados
    motivos = [
        "Lentidão ou Queda de Conexão", "Cobrança Indevida", 
        "Dúvidas sobre Fatura", "Falha de Equipamento/Roteador", 
        "Mudança de Endereço", "Insatisfação Geral", "Cancelamento Solicitado"
    ]
    prob_motivos = [0.38, 0.22, 0.15, 0.12, 0.05, 0.05, 0.03]
    canais = ["Call Center", "WhatsApp", "App Conecta", "Loja Física"]
    
    chamados = []
    chamado_id = 1
    
    # Subgrupo de clientes com alta incidência de chamados
    clientes_insatisfeitos = set(np.random.choice(df_clientes["id_cliente"], size=int(len(df_clientes)*0.18), replace=False))
    
    for _, cli in df_clientes.iterrows():
        cid = cli["id_cliente"]
        dt_cad = datetime.strptime(cli["data_cadastro"], "%Y-%m-%d")
        
        # Média de chamados no período
        if cid in clientes_insatisfeitos:
            n_chamados = np.random.poisson(lam=4)
        else:
            n_chamados = np.random.poisson(lam=0.8)
            
        for _ in range(n_chamados):
            dias_apos = np.random.randint(0, 365)
            dt_chamado = dt_cad + timedelta(days=dias_apos)
            if dt_chamado > DATA_FIM_HISTORICO or dt_chamado < DATA_INICIO_HISTORICO:
                continue
                
            # Verifica se caiu no período da migração do sistema (2024-03 a 2024-05)
            na_migracao = (datetime(2024, 3, 1) <= dt_chamado <= datetime(2024, 5, 31))
            
            sistema = "Novo_OmniChannel" if dt_chamado >= datetime(2024, 6, 1) else ("Transição_CRM" if na_migracao else "Legado_CRM")
            
            motivo = np.random.choice(motivos, p=prob_motivos)
            canal = np.random.choice(canais)
            tempo_resolucao = round(float(np.clip(np.random.exponential(scale=18), 1, 96)), 1)
            fcr = int(np.random.rand() > 0.35)
            
            # IMPREVISTO 1: No período da migração, 45% dos chamados sofreram perda de dados de motivo e tempo
            if na_migracao and np.random.rand() < 0.45:
                motivo = None  # Ausência provocada pela falha de integração
                tempo_resolucao = None
                sistema = "Sistema_Migracao_Incompleta"
                
            chamados.append({
                "id_chamado": f"CHAM_{chamado_id:07d}",
                "id_cliente": cid,
                "data_abertura": dt_chamado.strftime("%Y-%m-%d %H:%M:%S"),
                "motivo_chamado": motivo,
                "canal_atendimento": canal,
                "sistema_origem": sistema,
                "tempo_resolucao_horas": tempo_resolucao,
                "resolvido_primeiro_contato": fcr,
                "status_chamado": "Fechado" if dt_chamado < (DATA_FIM_HISTORICO - timedelta(days=2)) else "Aberto"
            })
            chamado_id += 1
            
    df_atendimento = pd.DataFrame(chamados)
    return df_atendimento

def gerar_rede(df_clientes):
    print("[*] Gerando telemetria e falhas de rede por região...")
    falhas = ["Rompimento de Fibra", "Manutenção Programada", "Instabilidade Roteador", "Degradação Sinal"]
    prob_falhas = [0.25, 0.35, 0.25, 0.15]
    
    eventos = []
    evt_id = 1
    
    # Clientes com problemas crônicos de rede
    clientes_rede_ruim = set(np.random.choice(df_clientes["id_cliente"], size=int(len(df_clientes)*0.15), replace=False))
    
    for _, cli in df_clientes.iterrows():
        cid = cli["id_cliente"]
        regiao = cli["regiao"]
        
        n_eventos = np.random.poisson(lam=3.5 if cid in clientes_rede_ruim else 0.6)
        for _ in range(n_eventos):
            dias_aleatorios = np.random.randint(0, 365)
            dt_evento = DATA_INICIO_HISTORICO + timedelta(days=dias_aleatorios)
            
            duracao = int(np.clip(np.random.exponential(scale=60 if cid in clientes_rede_ruim else 25), 5, 720))
            perda_pct = round(float(np.random.uniform(1.0, 15.0 if cid in clientes_rede_ruim else 3.5)), 2)
            latencia = round(float(np.clip(np.random.normal(loc=65 if cid in clientes_rede_ruim else 22, scale=10), 5, 250)), 1)
            
            eventos.append({
                "id_evento_rede": f"RED_{evt_id:07d}",
                "id_cliente": cid,
                "regiao": regiao,
                "data_evento": dt_evento.strftime("%Y-%m-%d %H:%M:%S"),
                "tipo_falha": np.random.choice(falhas, p=prob_falhas),
                "duracao_queda_minutos": duracao,
                "taxa_perda_pacotes": perda_pct,
                "latencia_media_ms": latencia
            })
            evt_id += 1
            
    df_rede = pd.DataFrame(eventos)
    return df_rede

def simular_cancelamentos(df_clientes, df_contratos, df_faturamento, df_atendimento, df_rede):
    print("[*] Calculando probabilidades reais de churn e gerando tabela de cancelamentos...")
    # Cria propensão latente realista baseada nos dados operacionais
    # Fatores que aumentam churn:
    # - Contrato sem fidelização
    # - Pagamento via Boleto com atraso
    # - Múltiplos chamados de suporte (especialmente lentidão/cobrança)
    # - Tempo de casa baixo (curva de sobrevivência clássica)
    # - Alto índice de instabilidade de rede
    
    # 1. Contratos sem fidelidade
    sem_fidelidade = set(df_contratos[df_contratos["fidelizacao_meses"] == 0]["id_cliente"])
    
    # 2. Inadimplência recente
    inadimplentes = set(df_faturamento[df_faturamento["dias_atraso"] > 15]["id_cliente"].unique())
    
    # 3. Reclamações de suporte
    chamados_por_cli = df_atendimento.groupby("id_cliente").size().to_dict()
    
    # 4. Falhas de rede crônicas
    quedas_por_cli = df_rede.groupby("id_cliente")["duracao_queda_minutos"].sum().to_dict()
    
    cancelamentos = []
    canc_id = 1
    
    # Calibraremos para gerar ~2,8% ao mês
    # Para o período de referência (especialmente maio e junho de 2024)
    # Vamos gerar cancelamentos distribuídos ao longo do ano
    
    for _, cli in df_clientes.iterrows():
        cid = cli["id_cliente"]
        tempo_meses = cli["tempo_relacionamento_meses"]
        
        score_risco = 0.015  # Risco base (~1.5%)
        
        if cid in sem_fidelidade:
            score_risco += 0.035
        if cid in inadimplentes:
            score_risco += 0.040
        n_cham = chamados_por_cli.get(cid, 0)
        if n_cham >= 3:
            score_risco += 0.045
        elif n_cham >= 1:
            score_risco += 0.015
        
        duracao_queda = quedas_por_cli.get(cid, 0)
        if duracao_queda > 240:
            score_risco += 0.030
            
        if tempo_meses < 6:
            score_risco += 0.025
        elif tempo_meses > 24:
            score_risco -= 0.010
            
        score_risco = max(0.005, min(0.35, score_risco))
        
        # Sorteia se o cliente cancelou em algum mês
        # Probabilidade mensal ~ score_risco
        for mes_idx, mes_str in enumerate(["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]):
            if np.random.rand() < score_risco:
                # Cliente cancelou neste mês
                dia = np.random.randint(1, 28)
                dt_canc = datetime.strptime(f"{mes_str}-{dia:02d}", "%Y-%m-%d")
                
                motivos_canc = ["Preço elevado / Concorrência", "Instabilidade na Conexão", "Mau Atendimento", "Mudança de Endereço"]
                tipo = "Involuntário por inadimplência" if (cid in inadimplentes and np.random.rand() < 0.6) else "Voluntário"
                
                cancelamentos.append({
                    "id_cancelamento": f"CNC_{canc_id:06d}",
                    "id_cliente": cid,
                    "data_cancelamento": dt_canc.strftime("%Y-%m-%d"),
                    "tipo_cancelamento": tipo,
                    "motivo_declarado": np.random.choice(motivos_canc) if tipo == "Voluntário" else "Inadimplência prolongada"
                })
                canc_id += 1
                break  # Cancela apenas uma vez
                
    df_cancelamentos = pd.DataFrame(cancelamentos)
    return df_cancelamentos

def salvar_csvs_e_banco(tabelas):
    print("[*] Exportando arquivos CSV em data/raw/ e gravando no SQLite...")
    conn = sqlite3.connect(DB_PATH)
    
    for nome, df in tabelas.items():
        csv_file = os.path.join(RAW_DATA_DIR, f"{nome}.csv")
        df.to_csv(csv_file, index=False)
        print(f" -> Salvo {csv_file} ({len(df):,} registros)")
        
        # Grava na base relacional
        df.to_sql(nome, conn, if_exists="replace", index=False)
        print(f" -> Tabela SQL '{nome}' criada com sucesso.")
        
    # Criar índices relacionais para consultas de alta performance
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientes_id ON clientes(id_cliente);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contratos_id ON contratos(id_cliente);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_faturamento_id ON faturamento(id_cliente);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_atendimento_id ON atendimento(id_cliente);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rede_id ON rede(id_cliente);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cancelamentos_id ON cancelamentos(id_cliente);")
    conn.commit()
    conn.close()
    print(f"[+] Banco SQLite consolidado com sucesso em: {DB_PATH}")

def main():
    print("=== INICIANDO GERAÇÃO DE DADOS SINTÉTICOS EMPRESARIAIS ===")
    df_clientes = gerar_clientes(N_CLIENTES)
    df_contratos = gerar_contratos(df_clientes)
    df_faturamento = gerar_faturamento(df_contratos)
    df_atendimento = gerar_atendimento(df_clientes)
    df_rede = gerar_rede(df_clientes)
    df_cancelamentos = simular_cancelamentos(df_clientes, df_contratos, df_faturamento, df_atendimento, df_rede)
    
    tabelas = {
        "clientes": df_clientes,
        "contratos": df_contratos,
        "faturamento": df_faturamento,
        "atendimento": df_atendimento,
        "rede": df_rede,
        "cancelamentos": df_cancelamentos
    }
    
    salvar_csvs_e_banco(tabelas)
    print("=== GERAÇÃO CONCLUÍDA COM SUCESSO ===")

if __name__ == "__main__":
    main()
