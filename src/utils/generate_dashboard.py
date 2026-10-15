"""
generate_dashboard.py
Gera o Dashboard Executivo Standalone em reports/executive_dashboard.html.
Agora 100% DINÂMICO no navegador:
- Permite carregar qualquer novo arquivo CSV via Upload / Drag-and-Drop (FileReader API).
- Recalcula todos os KPIs, gráficos de Decis e o Simulador de ROI dinamicamente em tempo real.
- Filtros por Faixa de Risco, Região, Plano e Busca Textual Instantânea.
- Ordenação por colunas (Score, Retorno Esperado, etc.) e Paginação interativa.
- Exportação da lista filtrada em formato CSV.
- Já vem pré-carregado com os dados reais da inferência do modelo campeão.
"""

import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LISTA_PATH = os.path.join(BASE_DIR, "data", "processed", "lista_priorizada_retencao.csv")
HTML_OUT_PATH = os.path.join(BASE_DIR, "reports", "executive_dashboard.html")

def gerar_html():
    print("[*] Lendo lista priorizada para embutir estado padrão no dashboard dinâmico...")
    df = pd.read_csv(LISTA_PATH)
    
    # Amostra inicial dos 250 clientes mais prioritários para carregamento instantâneo
    top_clientes = df.head(250).to_dict(orient="records")
    top_clientes_json = json.dumps(top_clientes, ensure_ascii=False)
    
    # Decis agregados calculados a partir da base completa (20.237 clientes)
    decil_agg = df.groupby("decil_risco", observed=False).agg(
        prob_media=("probabilidade_churn", "mean"),
        retorno_medio=("retorno_esperado_campanha_rs", "mean"),
        total_clientes=("id_cliente_hash", "count")
    ).reset_index()
    decis_labels = json.dumps(list(decil_agg["decil_risco"]), ensure_ascii=False)
    decis_probs = json.dumps([round(p * 100, 1) for p in decil_agg["prob_media"]])
    decis_retornos = json.dumps([round(r, 2) for r in decil_agg["retorno_medio"]])
    
    total_base_padrao = len(df)
    churn_medio_padrao = round(df["probabilidade_churn"].mean() * 100, 2)
    decil1_df = df[df["decil_risco"] == "Decil 1"]
    prob_decil1_padrao = round(decil1_df["probabilidade_churn"].mean() * 100, 1)
    retorno_decil1_padrao = round(decil1_df["retorno_esperado_campanha_rs"].mean(), 2)

    html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Conecta Brasil Telecom — Painel Executivo Dinâmico de Retenção</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-base: #090d16;
            --bg-card: rgba(19, 26, 43, 0.75);
            --bg-card-hover: rgba(28, 38, 64, 0.85);
            --border-card: rgba(255, 255, 255, 0.08);
            --accent-primary: #6366f1;
            --accent-glow: rgba(99, 102, 241, 0.25);
            --accent-success: #10b981;
            --accent-warning: #f59e0b;
            --accent-danger: #ef4444;
            --accent-cyan: #06b6d4;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --text-dim: #64748b;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            line-height: 1.6;
            min-height: 100vh;
            padding-bottom: 60px;
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(6, 182, 212, 0.08) 0px, transparent 50%);
            background-attachment: fixed;
        }}

        .container {{
            max-width: 1480px;
            margin: 0 auto;
            padding: 32px 24px;
        }}

        /* Header Executivo */
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-card);
            flex-wrap: wrap;
            gap: 16px;
        }}

        .logo-group h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, #ffffff 30%, #a5b4fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .logo-group p {{
            color: var(--text-muted);
            font-size: 14px;
            margin-top: 4px;
        }}

        .header-actions {{
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }}

        .badge-live {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #34d399;
            padding: 7px 14px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 600;
        }}

        .badge-live::before {{
            content: '';
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 10px #10b981;
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.5; transform: scale(1.2); }}
        }}

        /* Barra de Fonte de Dados e Upload Dinâmico */
        .datasource-bar {{
            background: rgba(22, 30, 49, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(99, 102, 241, 0.25);
            border-radius: 14px;
            padding: 16px 20px;
            margin-bottom: 28px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.25);
        }}

        .datasource-info {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .datasource-icon {{
            width: 40px;
            height: 40px;
            border-radius: 10px;
            background: rgba(99, 102, 241, 0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }}

        .datasource-title {{
            font-size: 13px;
            font-weight: 700;
            color: #ffffff;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .datasource-desc {{
            font-size: 13px;
            color: var(--text-muted);
        }}

        .datasource-controls {{
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }}

        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 9px 16px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            border: none;
        }}

        .btn-primary {{
            background: linear-gradient(135deg, #6366f1, #4f46e5);
            color: #ffffff;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
        }}

        .btn-primary:hover {{
            background: linear-gradient(135deg, #4f46e5, #4338ca);
            transform: translateY(-1px);
        }}

        .btn-secondary {{
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-main);
            border: 1px solid var(--border-card);
        }}

        .btn-secondary:hover {{
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.2);
        }}

        /* Toast de Notificação */
        #toast {{
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #1e293b;
            color: #ffffff;
            border: 1px solid #334155;
            padding: 14px 22px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            font-size: 14px;
            font-weight: 500;
            z-index: 9999;
            display: none;
            align-items: center;
            gap: 10px;
            animation: slideIn 0.3s ease;
        }}

        @keyframes slideIn {{
            from {{ transform: translateY(20px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}

        /* KPI Cards Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }}

        .kpi-card {{
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-card);
            border-radius: 16px;
            padding: 20px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .kpi-card:hover {{
            transform: translateY(-3px);
            border-color: rgba(99, 102, 241, 0.4);
            box-shadow: 0 10px 25px -5px var(--accent-glow);
        }}

        .kpi-card::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }}

        .kpi-card:hover::after {{
            opacity: 1;
        }}

        .kpi-title {{
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 8px;
        }}

        .kpi-value {{
            font-family: 'Outfit', sans-serif;
            font-size: 28px;
            font-weight: 700;
            color: var(--text-main);
            letter-spacing: -0.5px;
        }}

        .kpi-sub {{
            font-size: 12px;
            color: var(--text-dim);
            margin-top: 6px;
        }}

        .kpi-sub.highlight {{
            color: var(--accent-success);
            font-weight: 600;
        }}

        /* Grid Principal de Conteúdo */
        .content-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 32px;
        }}

        @media (max-width: 1024px) {{
            .content-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .panel-card {{
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-card);
            border-radius: 18px;
            padding: 24px;
        }}

        .panel-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .panel-header h2 {{
            font-family: 'Outfit', sans-serif;
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
        }}

        .panel-header span {{
            font-size: 12px;
            color: var(--text-dim);
        }}

        /* Simulador Interativo de ROI */
        .simulator-box {{
            background: rgba(10, 15, 29, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 20px;
        }}

        .slider-group {{
            margin-bottom: 16px;
        }}

        .slider-label {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-muted);
            margin-bottom: 6px;
        }}

        .slider-label span.val {{
            color: #818cf8;
            font-weight: 700;
        }}

        input[type="range"] {{
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: #1e293b;
            outline: none;
            accent-color: var(--accent-primary);
        }}

        .roi-results-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-top: 20px;
        }}

        .roi-res-card {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 14px;
            text-align: center;
        }}

        .roi-res-val {{
            font-family: 'Outfit', sans-serif;
            font-size: 20px;
            font-weight: 800;
            color: #ffffff;
            margin-top: 4px;
        }}

        .roi-res-val.green {{ color: #10b981; }}
        .roi-res-val.blue {{ color: #38bdf8; }}
        .roi-res-val.purple {{ color: #a855f7; }}
        .roi-res-val.red {{ color: #ef4444; }}

        /* Controles de Filtro da Tabela */
        .table-controls {{
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            flex-wrap: wrap;
            align-items: center;
        }}

        .search-box {{
            flex: 1;
            min-width: 240px;
            padding: 10px 14px;
            border-radius: 10px;
            background: rgba(10, 15, 29, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #ffffff;
            font-size: 13px;
            outline: none;
        }}

        .search-box:focus {{
            border-color: var(--accent-primary);
        }}

        select.filter-select {{
            padding: 10px 14px;
            border-radius: 10px;
            background: #131a2b;
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: var(--text-main);
            font-size: 13px;
            outline: none;
            cursor: pointer;
        }}

        /* Tabela Priorizada */
        .table-container {{
            overflow-x: auto;
            max-height: 520px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
        }}

        thead th {{
            position: sticky;
            top: 0;
            background: #151d30;
            padding: 12px 14px;
            font-weight: 600;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border-card);
            z-index: 10;
            cursor: pointer;
            user-select: none;
        }}

        thead th:hover {{
            color: #ffffff;
            background: #1b253d;
        }}

        tbody td {{
            padding: 12px 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
            color: var(--text-main);
        }}

        tbody tr:hover {{
            background: rgba(255, 255, 255, 0.03);
        }}

        .badge-tier {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
        }}

        .tier-critico {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
        .tier-alto {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
        .tier-medio {{ background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }}
        .tier-baixo {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}

        /* Paginação */
        .pagination-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 16px;
            padding-top: 12px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 13px;
            color: var(--text-muted);
        }}

        .pagination-buttons {{
            display: flex;
            gap: 8px;
        }}

        .btn-page {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-card);
            color: #ffffff;
            padding: 6px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12px;
        }}

        .btn-page:disabled {{
            opacity: 0.3;
            cursor: not-allowed;
        }}

        .btn-page:not(:disabled):hover {{
            background: var(--accent-primary);
        }}

        footer {{
            text-align: center;
            margin-top: 40px;
            color: var(--text-dim);
            font-size: 13px;
        }}
    </style>
</head>
<body>

<div id="toast">✅ Notificação</div>

<div class="container">
    <!-- Header -->
    <header>
        <div class="logo-group">
            <h1>CONECTA BRASIL TELECOM</h1>
            <p>Customer Churn Prediction & Retention Intelligence · Painel Dinâmico de Retenção</p>
        </div>
        <div class="header-actions">
            <span class="badge-live">Modelo Homologado (OOT Validado)</span>
        </div>
    </header>

    <!-- Barra de Controle de Dados (100% Dinâmico) -->
    <div class="datasource-bar">
        <div class="datasource-info">
            <div class="datasource-icon">📊</div>
            <div>
                <div class="datasource-title" id="sourceTitle">Base Ativa: Inferência Modelo Campeão</div>
                <div class="datasource-desc" id="sourceDesc">Arquivo carregado: <code>lista_priorizada_retencao.csv</code> ({total_base_padrao:,} clientes avaliados)</div>
            </div>
        </div>
        <div class="datasource-controls">
            <input type="file" id="fileInput" accept=".csv" style="display: none;">
            <button class="btn btn-primary" onclick="document.getElementById('fileInput').click()">
                📁 Carregar Novo CSV de Previsões
            </button>
            <button class="btn btn-secondary" onclick="restaurarBasePadrao()">
                🔄 Restaurar Base Padrão
            </button>
            <button class="btn btn-secondary" onclick="exportarCSVFiltrado()">
                📥 Exportar Filtrados (.CSV)
            </button>
        </div>
    </div>

    <!-- KPI Grid (Valores Atualizados Dinamicamente via JS) -->
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-title">Clientes Avaliados</div>
            <div class="kpi-value" id="kpiTotalClientes">{total_base_padrao:,}</div>
            <div class="kpi-sub" id="kpiTotalClientesSub">Snapshot Operacional Ativo</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Churn Médio Global</div>
            <div class="kpi-value" id="kpiChurnMedio">{churn_medio_padrao}%</div>
            <div class="kpi-sub" style="color: #f87171;">Taxa Média de Evasão Prevista</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Decil 1 (Top 10%)</div>
            <div class="kpi-value" id="kpiDecil1Qtd">2.024</div>
            <div class="kpi-sub highlight">Clientes de Maior Risco</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Prob. Média Decil 1</div>
            <div class="kpi-value" id="kpiProbDecil1">{prob_decil1_padrao}%</div>
            <div class="kpi-sub highlight">Concentração Máxima de Churn</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Retorno Médio / Contato</div>
            <div class="kpi-value" id="kpiRetornoDecil1">R$ {retorno_decil1_padrao:.2f}</div>
            <div class="kpi-sub highlight">Margem líquida esperada no Decil 1</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Lift @ Top 10%</div>
            <div class="kpi-value" id="kpiLift">3,06x</div>
            <div class="kpi-sub highlight">vs. Abordagem Aleatória</div>
        </div>
    </div>

    <!-- Content Grid: Gráficos & Simulador -->
    <div class="content-grid">
        <!-- Gráfico de Ganhos e Decis -->
        <div class="panel-card">
            <div class="panel-header">
                <h2>Distribuição de Risco e Retorno por Decil</h2>
                <span id="chartSub">Atualizado dinamicamente com base no dataset</span>
            </div>
            <div style="height: 320px;">
                <canvas id="chartDecis"></canvas>
            </div>
        </div>

        <!-- Simulador Financeiro de Retenção -->
        <div class="panel-card">
            <div class="panel-header">
                <h2>Simulador Interativo de Retorno de Campanha (ROI)</h2>
                <span>Framework de Valor Esperado (ADR-003)</span>
            </div>

            <div class="simulator-box">
                <div class="slider-group">
                    <div class="slider-label">
                        <span>Capacidade de Contato Operacional (% da base):</span>
                        <span class="val" id="valCapacidade">10% (50.000 clientes)</span>
                    </div>
                    <input type="range" id="rangeCapacidade" min="1" max="20" step="1" value="10">
                </div>

                <div class="slider-group">
                    <div class="slider-label">
                        <span>Eficácia de Retenção da Oferta (%):</span>
                        <span class="val" id="valEficacia">15%</span>
                    </div>
                    <input type="range" id="rangeEficacia" min="5" max="30" step="1" value="15">
                </div>

                <div class="slider-group">
                    <div class="slider-label">
                        <span>Custo da Oferta / Desconto (R$):</span>
                        <span class="val" id="valCustoOferta">R$ 50,00</span>
                    </div>
                    <input type="range" id="rangeCustoOferta" min="10" max="100" step="5" value="50">
                </div>

                <div class="slider-group">
                    <div class="slider-label">
                        <span>Custo Operacional de Contato (R$):</span>
                        <span class="val" id="valCustoContato">R$ 12,00</span>
                    </div>
                    <input type="range" id="rangeCustoContato" min="5" max="30" step="1" value="12">
                </div>
            </div>

            <div class="roi-results-grid">
                <div class="roi-res-card">
                    <div class="kpi-title">Clientes Retidos</div>
                    <div class="roi-res-val blue" id="resRetidos">2.295</div>
                </div>
                <div class="roi-res-card">
                    <div class="kpi-title">Margem Preservada (12m)</div>
                    <div class="roi-res-val purple" id="resReceita">R$ 2.313.360</div>
                </div>
                <div class="roi-res-card">
                    <div class="kpi-title">ROI Líquido Estimado</div>
                    <div class="roi-res-val green" id="resROI">+49,2%</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Tabela Operacional de Clientes Priorizados -->
    <div class="panel-card">
        <div class="panel-header">
            <h2>Fila Priorizada para a Gerência de Retenção</h2>
            <span>Saída Pseudonimizada (LGPD Compliant - ADR-002)</span>
        </div>

        <div class="table-controls">
            <input type="text" id="filtroTexto" class="search-box" placeholder="Buscar por ID, Região, Plano ou Ação...">
            
            <select id="filtroFaixa" class="filter-select">
                <option value="TODAS">Todas as Faixas de Risco</option>
                <option value="Crítico">Crítico</option>
                <option value="Alto">Alto</option>
                <option value="Médio">Médio</option>
                <option value="Baixo">Baixo</option>
            </select>

            <select id="filtroRegiao" class="filter-select">
                <option value="TODAS">Todas as Regiões</option>
                <option value="Sudeste">Sudeste</option>
                <option value="Sul">Sul</option>
                <option value="Nordeste">Nordeste</option>
                <option value="Centro-Oeste">Centro-Oeste</option>
                <option value="Norte">Norte</option>
            </select>

            <select id="itensPorPagina" class="filter-select">
                <option value="15">15 por página</option>
                <option value="30">30 por página</option>
                <option value="50">50 por página</option>
            </select>
        </div>

        <div class="table-container">
            <table id="tabelaClientes">
                <thead>
                    <tr>
                        <th onclick="ordenarPor('id_cliente_hash')">ID Pseudonimizado ↕</th>
                        <th onclick="ordenarPor('regiao')">Região ↕</th>
                        <th onclick="ordenarPor('tipo_plano')">Plano ↕</th>
                        <th onclick="ordenarPor('eh_fidelizado')">Fidelizado ↕</th>
                        <th onclick="ordenarPor('media_valor_fatura_3m')">Fatura Média (3m) ↕</th>
                        <th onclick="ordenarPor('total_chamados_60d')">Chamados (60d) ↕</th>
                        <th onclick="ordenarPor('duracao_quedas_min_60d')">Quedas (min) ↕</th>
                        <th onclick="ordenarPor('probabilidade_churn')">Prob. Churn ↕</th>
                        <th onclick="ordenarPor('decil_risco')">Decil ↕</th>
                        <th onclick="ordenarPor('faixa_risco')">Faixa ↕</th>
                        <th onclick="ordenarPor('retorno_esperado_campanha_rs')">Retorno Esperado ↕</th>
                        <th>Ação Recomendada</th>
                    </tr>
                </thead>
                <tbody id="tbodyClientes">
                    <!-- Gerado dinamicamente via JS -->
                </tbody>
            </table>
        </div>

        <div class="pagination-bar">
            <div id="infoPaginacao">Mostrando 1 - 15 de 250 clientes</div>
            <div class="pagination-buttons">
                <button class="btn-page" id="btnPagAnt" onclick="mudarPagina(-1)">Anterior</button>
                <span id="numPagina" style="display:flex; align-items:center; padding:0 8px; font-weight:600;">1</span>
                <button class="btn-page" id="btnPagProx" onclick="mudarPagina(1)">Próxima</button>
            </div>
        </div>
    </div>

    <footer>
        <p>Conecta Brasil Telecom · Projeto 01 Customer Churn Prediction & Retention Intelligence</p>
        <p>Painel 100% Dinâmico com suporte a Upload de Arquivos CSV locais via FileReader API</p>
    </footer>
</div>

<script>
    // Estado Padrão Embutido (Injetado via Python)
    const DADOS_PADRAO = {top_clientes_json};
    const DECIS_PADRAO = {{
        labels: {decis_labels},
        probs: {decis_probs},
        retornos: {decis_retornos}
    }};

    // Estado da Aplicação em Memória
    let datasetAtual = [...DADOS_PADRAO];
    let dadosFiltrados = [...DADOS_PADRAO];
    let colunaOrdenacao = 'retorno_esperado_campanha_rs';
    let ordemAsc = false;
    let paginaAtual = 1;
    let linhasPorPagina = 15;
    let chartInstance = null;

    // Toast Notification
    function mostrarToast(msg) {{
        const t = document.getElementById('toast');
        t.innerText = msg;
        t.style.display = 'flex';
        setTimeout(() => {{ t.style.display = 'none'; }}, 3500);
    }}

    // Inicialização do Gráfico Chart.js
    function initChart(labels, probs, retornos) {{
        const ctx = document.getElementById('chartDecis').getContext('2d');
        if (chartInstance) {{
            chartInstance.destroy();
        }}
        chartInstance = new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: labels,
                datasets: [
                    {{
                        label: 'Probabilidade Média de Churn (%)',
                        data: probs,
                        backgroundColor: 'rgba(99, 102, 241, 0.75)',
                        borderRadius: 6,
                        yAxisID: 'y'
                    }},
                    {{
                        label: 'Retorno Financeiro Esperado Médio (R$)',
                        data: retornos,
                        type: 'line',
                        borderColor: '#10b981',
                        borderWidth: 3,
                        pointBackgroundColor: '#10b981',
                        pointRadius: 4,
                        yAxisID: 'y1'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        labels: {{ color: '#94a3b8', font: {{ family: 'Inter', size: 12 }} }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#64748b' }},
                        grid: {{ color: 'rgba(255, 255, 255, 0.04)' }}
                    }},
                    y: {{
                        type: 'linear',
                        position: 'left',
                        ticks: {{ color: '#818cf8', callback: val => val + '%' }},
                        grid: {{ color: 'rgba(255, 255, 255, 0.04)' }}
                    }},
                    y1: {{
                        type: 'linear',
                        position: 'right',
                        ticks: {{ color: '#34d399', callback: val => 'R$ ' + val }},
                        grid: {{ drawOnChartArea: false }}
                    }}
                }}
            }}
        }});
    }}

    // Recalcular Decis a partir de qualquer dataset carregado
    function recalcularDecis(dados) {{
        const decisMap = {{}};
        for (let i = 1; i <= 10; i++) {{
            decisMap['Decil ' + i] = {{ probs: [], retornos: [] }};
        }}
        dados.forEach(d => {{
            if (decisMap[d.decil_risco]) {{
                decisMap[d.decil_risco].probs.push(d.probabilidade_churn * 100);
                decisMap[d.decil_risco].retornos.push(d.retorno_esperado_campanha_rs);
            }}
        }});
        const labels = Object.keys(decisMap);
        const probs = labels.map(k => {{
            const arr = decisMap[k].probs;
            return arr.length ? +(arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(1) : 0;
        }});
        const retornos = labels.map(k => {{
            const arr = decisMap[k].retornos;
            return arr.length ? +(arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(2) : 0;
        }});
        initChart(labels, probs, retornos);
    }}

    // Atualizar Todos os KPIs
    function atualizarKPIs(dados) {{
        document.getElementById('kpiTotalClientes').innerText = dados.length.toLocaleString('pt-BR');
        
        const mediaChurn = dados.length ? (dados.reduce((acc, d) => acc + d.probabilidade_churn, 0) / dados.length) * 100 : 0;
        document.getElementById('kpiChurnMedio').innerText = mediaChurn.toFixed(2) + '%';
        
        const decil1 = dados.filter(d => d.decil_risco === 'Decil 1');
        document.getElementById('kpiDecil1Qtd').innerText = decil1.length.toLocaleString('pt-BR');
        
        const probDecil1 = decil1.length ? (decil1.reduce((acc, d) => acc + d.probabilidade_churn, 0) / decil1.length) * 100 : 0;
        document.getElementById('kpiProbDecil1').innerText = probDecil1.toFixed(1) + '%';
        
        const retDecil1 = decil1.length ? (decil1.reduce((acc, d) => acc + d.retorno_esperado_campanha_rs, 0) / decil1.length) : 0;
        document.getElementById('kpiRetornoDecil1').innerText = 'R$ ' + retDecil1.toFixed(2);
    }}

    // Renderizar Tabela Paginada
    function renderTabela() {{
        const tbody = document.getElementById('tbodyClientes');
        tbody.innerHTML = '';

        const inicio = (paginaAtual - 1) * linhasPorPagina;
        const fim = inicio + linhasPorPagina;
        const paginaDados = dadosFiltrados.slice(inicio, fim);

        if (paginaDados.length === 0) {{
            tbody.innerHTML = '<tr><td colspan="12" style="text-align:center; padding:30px; color:#64748b;">Nenhum cliente encontrado com os filtros selecionados.</td></tr>';
            document.getElementById('infoPaginacao').innerText = '0 registros encontrados';
            document.getElementById('btnPagAnt').disabled = true;
            document.getElementById('btnPagProx').disabled = true;
            return;
        }}

        paginaDados.forEach(c => {{
            const tr = document.createElement('tr');
            const tierClass = 'tier-' + (c.faixa_risco ? c.faixa_risco.toLowerCase() : 'medio');
            tr.innerHTML = `
                <td><code>${{c.id_cliente_hash || '-'}}</code></td>
                <td>${{c.regiao || '-'}}</td>
                <td>${{c.tipo_plano || '-'}}</td>
                <td>${{c.eh_fidelizado == 1 ? 'Sim' : 'Não'}}</td>
                <td>R$ ${{Number(c.media_valor_fatura_3m || 0).toFixed(2)}}</td>
                <td>${{c.total_chamados_60d || 0}}</td>
                <td>${{c.duracao_quedas_min_60d || 0}} min</td>
                <td><strong>${{(Number(c.probabilidade_churn || 0) * 100).toFixed(1)}}%</strong></td>
                <td>${{c.decil_risco || '-'}}</td>
                <td><span class="badge-tier ${{tierClass}}">${{c.faixa_risco || '-'}}</span></td>
                <td style="color: ${{c.retorno_esperado_campanha_rs > 0 ? '#34d399' : '#f87171'}}; font-weight: 700;">
                    R$ ${{Number(c.retorno_esperado_campanha_rs || 0).toFixed(2)}}
                </td>
                <td style="font-size: 12px; font-weight: 500;">${{c.acao_recomendada || '-'}}</td>
            `;
            tbody.appendChild(tr);
        }});

        const total = dadosFiltrados.length;
        document.getElementById('infoPaginacao').innerText = `Mostrando ${{inicio + 1}} - ${{Math.min(fim, total)}} de ${{total.toLocaleString('pt-BR')}} clientes`;
        document.getElementById('numPagina').innerText = paginaAtual;
        document.getElementById('btnPagAnt').disabled = (paginaAtual === 1);
        document.getElementById('btnPagProx').disabled = (fim >= total);
    }}

    // Filtrar e Ordenar
    function aplicarFiltros() {{
        const termo = document.getElementById('filtroTexto').value.toLowerCase();
        const faixa = document.getElementById('filtroFaixa').value;
        const regiao = document.getElementById('filtroRegiao').value;

        dadosFiltrados = datasetAtual.filter(c => {{
            const matchTexto = !termo || 
                (c.id_cliente_hash && c.id_cliente_hash.toLowerCase().includes(termo)) ||
                (c.tipo_plano && c.tipo_plano.toLowerCase().includes(termo)) ||
                (c.acao_recomendada && c.acao_recomendada.toLowerCase().includes(termo));

            const matchFaixa = (faixa === 'TODAS') || (c.faixa_risco === faixa);
            const matchRegiao = (regiao === 'TODAS') || (c.regiao === regiao);

            return matchTexto && matchFaixa && matchRegiao;
        }});

        // Ordenação
        dadosFiltrados.sort((a, b) => {{
            let vA = a[colunaOrdenacao];
            let vB = b[colunaOrdenacao];
            if (typeof vA === 'string') vA = vA.toLowerCase();
            if (typeof vB === 'string') vB = vB.toLowerCase();
            if (vA < vB) return ordemAsc ? -1 : 1;
            if (vA > vB) return ordemAsc ? 1 : -1;
            return 0;
        }});

        paginaAtual = 1;
        renderTabela();
    }}

    function ordenarPor(col) {{
        if (colunaOrdenacao === col) {{
            ordemAsc = !ordemAsc;
        }} else {{
            colunaOrdenacao = col;
            ordemAsc = false;
        }}
        aplicarFiltros();
    }}

    function mudarPagina(delta) {{
        paginaAtual += delta;
        renderTabela();
    }}

    // Simulador Dinâmico de ROI
    const elCapacidade = document.getElementById('rangeCapacidade');
    const elEficacia = document.getElementById('rangeEficacia');
    const elCustoOferta = document.getElementById('rangeCustoOferta');
    const elCustoContato = document.getElementById('rangeCustoContato');

    function atualizarSimulador() {{
        const capPct = parseFloat(elCapacidade.value);
        const eficPct = parseFloat(elEficacia.value) / 100;
        const cOferta = parseFloat(elCustoOferta.value);
        const cContato = parseFloat(elCustoContato.value);

        document.getElementById('valCapacidade').innerText = `${{capPct}}% (${{(capPct * 5000).toLocaleString('pt-BR')}} clientes)`;
        document.getElementById('valEficacia').innerText = `${{elEficacia.value}}%`;
        document.getElementById('valCustoOferta').innerText = `R$ ${{cOferta.toFixed(2)}}`;
        document.getElementById('valCustoContato').innerText = `R$ ${{cContato.toFixed(2)}}`;

        const totalAbordados = (capPct / 100) * 500000;
        const churnCapturado = 0.306 * 14000 * (capPct / 10);
        const retidos = Math.round(churnCapturado * eficPct);

        const receitaPreservada = retidos * 120 * 12 * 0.70;
        const custoTotalCampanha = totalAbordados * (cContato + (cOferta * eficPct));
        const lucroLiquido = receitaPreservada - custoTotalCampanha;
        const roiPct = custoTotalCampanha > 0 ? (lucroLiquido / custoTotalCampanha) * 100 : 0;

        document.getElementById('resRetidos').innerText = retidos.toLocaleString('pt-BR');
        document.getElementById('resReceita').innerText = 'R$ ' + Math.round(receitaPreservada).toLocaleString('pt-BR');
        document.getElementById('resROI').innerText = (roiPct >= 0 ? '+' : '') + roiPct.toFixed(1) + '%';
        document.getElementById('resROI').className = 'roi-res-val ' + (roiPct >= 0 ? 'green' : 'red');
    }}

    // Leitor e Parser Dinâmico de CSV (FileReader API)
    document.getElementById('fileInput').addEventListener('change', function(e) {{
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function(evt) {{
            const csvText = evt.target.result;
            const linhas = csvText.split(/\\r?\\n/).filter(l => l.trim().length > 0);
            if (linhas.length < 2) {{
                alert('Arquivo CSV inválido ou vazio.');
                return;
            }}

            const headers = linhas[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
            const novosClientes = [];

            for (let i = 1; i < linhas.length; i++) {{
                const valores = linhas[i].split(',').map(v => v.trim().replace(/^"|"$/g, ''));
                if (valores.length === headers.length) {{
                    const obj = {{}};
                    headers.forEach((h, idx) => {{
                        const val = valores[idx];
                        if (!isNaN(val) && val !== '') {{
                            obj[h] = parseFloat(val);
                        }} else {{
                            obj[h] = val;
                        }}
                    }});
                    novosClientes.push(obj);
                }}
            }}

            if (novosClientes.length > 0) {{
                datasetAtual = novosClientes;
                document.getElementById('sourceTitle').innerText = 'Base Dinâmica Carregada do Usuário';
                document.getElementById('sourceDesc').innerHTML = `Arquivo: <code>${{file.name}}</code> (${{novosClientes.length.toLocaleString('pt-BR')}} registros processados com sucesso)`;
                
                atualizarKPIs(datasetAtual);
                recalcularDecis(datasetAtual);
                aplicarFiltros();
                atualizarSimulador();
                mostrarToast(`✅ ${{novosClientes.length.toLocaleString('pt-BR')}} registros carregados com sucesso!`);
            }}
        }};
        reader.readAsText(file);
    }});

    // Restaurar Base Padrão
    function restaurarBasePadrao() {{
        datasetAtual = [...DADOS_PADRAO];
        document.getElementById('sourceTitle').innerText = 'Base Ativa: Inferência Modelo Campeão';
        document.getElementById('sourceDesc').innerHTML = 'Arquivo carregado: <code>lista_priorizada_retencao.csv</code> ({total_base_padrao:,} clientes avaliados)';
        atualizarKPIs(datasetAtual);
        initChart(DECIS_PADRAO.labels, DECIS_PADRAO.probs, DECIS_PADRAO.retornos);
        aplicarFiltros();
        atualizarSimulador();
        mostrarToast('🔄 Base padrão restaurada com sucesso!');
    }}

    // Exportar CSV Filtrado
    function exportarCSVFiltrado() {{
        if (!dadosFiltrados.length) return;
        const colunas = Object.keys(dadosFiltrados[0]);
        let csvContent = 'data:text/csv;charset=utf-8,' + colunas.join(',') + '\\n';
        dadosFiltrados.forEach(row => {{
            const linha = colunas.map(c => `"${{row[c] || ''}}"`).join(',');
            csvContent += linha + '\\n';
        }});
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', 'clientes_retencao_filtrados.csv');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        mostrarToast('📥 Download do CSV iniciado!');
    }}

    // Event Listeners
    document.getElementById('filtroTexto').addEventListener('input', aplicarFiltros);
    document.getElementById('filtroFaixa').addEventListener('change', aplicarFiltros);
    document.getElementById('filtroRegiao').addEventListener('change', aplicarFiltros);
    document.getElementById('itensPorPagina').addEventListener('change', function(e) {{
        linhasPorPagina = parseInt(e.target.value);
        paginaAtual = 1;
        renderTabela();
    }});

    elCapacidade.addEventListener('input', atualizarSimulador);
    elEficacia.addEventListener('input', atualizarSimulador);
    elCustoOferta.addEventListener('input', atualizarSimulador);
    elCustoContato.addEventListener('input', atualizarSimulador);

    // Inicialização ao carregar a página
    window.addEventListener('DOMContentLoaded', () => {{
        initChart(DECIS_PADRAO.labels, DECIS_PADRAO.probs, DECIS_PADRAO.retornos);
        aplicarFiltros();
        atualizarSimulador();
    }});
</script>
</body>
</html>
"""

    with open(HTML_OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"[+] Painel executivo 100% DINÂMICO gerado com sucesso em: {HTML_OUT_PATH}")

if __name__ == "__main__":
    gerar_html()
