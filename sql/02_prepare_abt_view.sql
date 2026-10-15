-- =============================================================================
-- PROJETO 01: CONECTA BRASIL TELECOM — CHURN PREDICTION & RETENTION
-- Script SQL: Construção da Base Analítica (ABT - Analytical Base Table)
-- Demonstração de SQL Avançado com CTEs, Agregações Temporais e Point-in-Time
-- =============================================================================

-- Parâmetros da Safra de Treinamento:
-- Data de Corte (T_0): '2024-05-01'
-- Fim do Horizonte de Churn (T_0 + 31 dias): '2024-05-31'

WITH parametros AS (
    SELECT 
        DATE '2024-05-01' AS data_corte,
        DATE '2024-05-31' AS data_fim_horizonte,
        'ConectaBrasil_LGPD_2026_SecSalt' AS secret_salt
),

-- 1. Clientes Ativos e Elegíveis no Ponto de Corte (Tenure >= 30 dias e sem cancelamento prévio)
clientes_elegiveis AS (
    SELECT 
        c.id_cliente,
        -- Pseudonimização criptográfica em SQL (SHA-256 com salt)
        SUBSTRING(encode(digest(c.id_cliente || '_' || p.secret_salt, 'sha256'), 'hex') FROM 1 FOR 16) AS id_cliente_hash,
        c.regiao,
        c.faixa_etaria,
        FLOOR((p.data_corte - c.data_cadastro) / 30.4)::INTEGER AS tempo_relacionamento_meses_corte,
        ctr.tipo_plano,
        ctr.fidelizacao_meses,
        CASE WHEN ctr.fidelizacao_meses > 0 THEN 1 ELSE 0 END AS eh_fidelizado,
        ctr.forma_pagamento,
        p.data_corte,
        p.data_fim_horizonte
    FROM clientes c
    CROSS JOIN parametros p
    INNER JOIN contratos ctr ON c.id_cliente = ctr.id_cliente
    WHERE c.data_cadastro <= (p.data_corte - INTERVAL '30 days')
      AND NOT EXISTS (
          SELECT 1 
          FROM cancelamentos cnc 
          WHERE cnc.id_cliente = c.id_cliente 
            AND cnc.data_cancelamento <= p.data_corte
      )
),

-- 2. Definição do Alvo (Target Y): Evasão estritamente no intervalo (T_0, T_0 + 30 dias]
alvo_churn AS (
    SELECT 
        ce.id_cliente,
        CASE 
            WHEN EXISTS (
                SELECT 1 
                FROM cancelamentos cnc
                WHERE cnc.id_cliente = ce.id_cliente
                  AND cnc.data_cancelamento > ce.data_corte
                  AND cnc.data_cancelamento <= ce.data_fim_horizonte
            ) THEN 1 
            ELSE 0 
        END AS churn_30d
    FROM clientes_elegiveis ce
),

-- 3. Métricas Financeiras Point-in-Time (Janela de 90 dias anteriores a T_0)
faturamento_agregado AS (
    SELECT 
        f.id_cliente,
        ROUND(AVG(f.valor_fatura), 2) AS media_valor_fatura_3m,
        MAX(f.dias_atraso) AS max_dias_atraso_3m,
        COUNT(CASE WHEN f.dias_atraso > 0 THEN 1 END) AS total_faturas_atrasadas_3m,
        CASE WHEN MAX(f.dias_atraso) > 15 THEN 1 ELSE 0 END AS inadimplente_recente_flag
    FROM faturamento f
    CROSS JOIN parametros p
    WHERE f.data_vencimento <= p.data_corte
      AND f.data_vencimento >= (p.data_corte - INTERVAL '90 days')
    GROUP BY f.id_cliente
),

-- 4. Métricas de Atendimento e Suporte Point-in-Time (Janelas de 30d, 60d e 90d)
atendimento_agregado AS (
    SELECT 
        a.id_cliente,
        COUNT(CASE WHEN a.data_abertura >= (p.data_corte - INTERVAL '30 days') THEN 1 END) AS total_chamados_30d,
        COUNT(CASE WHEN a.data_abertura >= (p.data_corte - INTERVAL '60 days') THEN 1 END) AS total_chamados_60d,
        COUNT(CASE WHEN a.data_abertura >= (p.data_corte - INTERVAL '90 days') THEN 1 END) AS total_chamados_90d,
        COUNT(CASE WHEN a.data_abertura >= (p.data_corte - INTERVAL '60 days') AND a.motivo_chamado = 'Lentidão ou Queda de Conexão' THEN 1 END) AS chamados_lentidao_60d,
        COUNT(CASE WHEN a.data_abertura >= (p.data_corte - INTERVAL '60 days') AND a.motivo_chamado = 'Cobrança Indevida' THEN 1 END) AS chamados_cobranca_60d,
        ROUND(COALESCE(AVG(CASE WHEN a.data_abertura >= (p.data_corte - INTERVAL '60 days') THEN a.resolvido_primeiro_contato::NUMERIC END), 1.0), 2) AS taxa_fcr_atendimento_60d,
        -- Flag Imprevisto 1: Chamados durante a migração incompleta
        MAX(CASE WHEN a.data_abertura >= (p.data_corte - INTERVAL '90 days') AND a.sistema_origem = 'Sistema_Migracao_Incompleta' THEN 1 ELSE 0 END) AS chamados_sistema_migracao_flag
    FROM atendimento a
    CROSS JOIN parametros p
    WHERE a.data_abertura <= p.data_corte
      AND a.data_abertura >= (p.data_corte - INTERVAL '90 days')
    GROUP BY a.id_cliente
),

-- 5. Métricas de Rede e Telemetria Point-in-Time (Janela de 60 dias anteriores a T_0)
rede_agregada AS (
    SELECT 
        r.id_cliente,
        COUNT(r.id_evento_rede) AS total_eventos_rede_60d,
        COALESCE(SUM(r.duracao_queda_minutos), 0) AS duracao_quedas_min_60d,
        ROUND(COALESCE(AVG(r.taxa_perda_pacotes), 1.5), 2) AS taxa_media_perda_pacotes_60d,
        ROUND(COALESCE(AVG(r.latencia_media_ms), 22.0), 1) AS latencia_media_ms_60d,
        CASE WHEN SUM(r.duracao_queda_minutos) > 180 OR AVG(r.taxa_perda_pacotes) > 5.0 THEN 1 ELSE 0 END AS instabilidade_critica_flag
    FROM rede r
    CROSS JOIN parametros p
    WHERE r.data_evento <= p.data_corte
      AND r.data_evento >= (p.data_corte - INTERVAL '60 days')
    GROUP BY r.id_cliente
)

-- 6. Consolidação da Tabela Analítica de Modelagem (ABT)
SELECT 
    ce.id_cliente_hash,
    ce.regiao,
    ce.faixa_etaria,
    ce.tempo_relacionamento_meses_corte,
    ce.tipo_plano,
    ce.fidelizacao_meses,
    ce.eh_fidelizado,
    ce.forma_pagamento,
    -- Variáveis Financeiras
    COALESCE(fa.media_valor_fatura_3m, 120.00) AS media_valor_fatura_3m,
    COALESCE(fa.max_dias_atraso_3m, 0) AS max_dias_atraso_3m,
    COALESCE(fa.total_faturas_atrasadas_3m, 0) AS total_faturas_atrasadas_3m,
    COALESCE(fa.inadimplente_recente_flag, 0) AS inadimplente_recente_flag,
    -- Variáveis de Atendimento
    COALESCE(ate.total_chamados_30d, 0) AS total_chamados_30d,
    COALESCE(ate.total_chamados_60d, 0) AS total_chamados_60d,
    COALESCE(ate.total_chamados_90d, 0) AS total_chamados_90d,
    COALESCE(ate.chamados_lentidao_60d, 0) AS chamados_lentidao_60d,
    COALESCE(ate.chamados_cobranca_60d, 0) AS chamados_cobranca_60d,
    COALESCE(ate.taxa_fcr_atendimento_60d, 1.00) AS taxa_fcr_atendimento_60d,
    COALESCE(ate.chamados_sistema_migracao_flag, 0) AS chamados_sistema_migracao_flag,
    -- Variáveis de Rede
    COALESCE(red.total_eventos_rede_60d, 0) AS total_eventos_rede_60d,
    COALESCE(red.duracao_quedas_min_60d, 0) AS duracao_quedas_min_60d,
    COALESCE(red.taxa_media_perda_pacotes_60d, 1.50) AS taxa_media_perda_pacotes_60d,
    COALESCE(red.latencia_media_ms_60d, 22.0) AS latencia_media_ms_60d,
    COALESCE(red.instabilidade_critica_flag, 0) AS instabilidade_critica_flag,
    -- Variável Alvo
    alv.churn_30d
FROM clientes_elegiveis ce
INNER JOIN alvo_churn alv ON ce.id_cliente = alv.id_cliente
LEFT JOIN faturamento_agregado fa ON ce.id_cliente = fa.id_cliente
LEFT JOIN atendimento_agregado ate ON ce.id_cliente = ate.id_cliente
LEFT JOIN rede_agregada red ON ce.id_cliente = red.id_cliente
ORDER BY alv.churn_30d DESC, ce.id_cliente_hash;
