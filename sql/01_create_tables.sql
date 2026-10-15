-- =============================================================================
-- PROJETO 01: CONECTA BRASIL TELECOM — CHURN PREDICTION & RETENTION
-- Script DDL: Criação das Tabelas e Índices no PostgreSQL 14+
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -----------------------------------------------------------------------------
-- 1. TABELA: clientes
-- Armazena o cadastro demográfico e histórico de relacionamento do assinante
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS clientes CASCADE;
CREATE TABLE clientes (
    id_cliente VARCHAR(10) PRIMARY KEY,
    nome_cliente VARCHAR(120) NOT NULL,
    cpf VARCHAR(14) NOT NULL,
    email VARCHAR(120) NOT NULL,
    regiao VARCHAR(25) NOT NULL,
    faixa_etaria VARCHAR(10) NOT NULL,
    genero VARCHAR(10) NOT NULL,
    data_cadastro DATE NOT NULL,
    tempo_relacionamento_meses INTEGER NOT NULL CHECK (tempo_relacionamento_meses >= 0)
);

CREATE INDEX idx_clientes_regiao ON clientes(regiao);
CREATE INDEX idx_clientes_data_cadastro ON clientes(data_cadastro);

-- -----------------------------------------------------------------------------
-- 2. TABELA: contratos
-- Detalha a modalidade de plano, fidelização e método de pagamento
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS contratos CASCADE;
CREATE TABLE contratos (
    id_contrato VARCHAR(12) PRIMARY KEY,
    id_cliente VARCHAR(10) NOT NULL REFERENCES clientes(id_cliente) ON DELETE RESTRICT,
    tipo_plano VARCHAR(40) NOT NULL,
    fidelizacao_meses INTEGER NOT NULL CHECK (fidelizacao_meses IN (0, 12, 24)),
    forma_pagamento VARCHAR(30) NOT NULL,
    data_inicio DATE NOT NULL
);

CREATE INDEX idx_contratos_id_cliente ON contratos(id_cliente);
CREATE INDEX idx_contratos_plano ON contratos(tipo_plano);
CREATE INDEX idx_contratos_fidelizacao ON contratos(fidelizacao_meses);

-- -----------------------------------------------------------------------------
-- 3. TABELA: faturamento
-- Histórico mensal de cobranças, vencimentos, liquidações e dias de atraso
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS faturamento CASCADE;
CREATE TABLE faturamento (
    id_fatura VARCHAR(14) PRIMARY KEY,
    id_cliente VARCHAR(10) NOT NULL REFERENCES clientes(id_cliente) ON DELETE RESTRICT,
    mes_referencia VARCHAR(7) NOT NULL, -- Formato YYYY-MM
    valor_fatura NUMERIC(10, 2) NOT NULL CHECK (valor_fatura > 0),
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    dias_atraso INTEGER NOT NULL CHECK (dias_atraso >= 0),
    status_pagamento VARCHAR(25) NOT NULL CHECK (status_pagamento IN ('Pago em dia', 'Pago com atraso', 'Inadimplente'))
);

CREATE INDEX idx_faturamento_cliente_venc ON faturamento(id_cliente, data_vencimento);
CREATE INDEX idx_faturamento_status ON faturamento(status_pagamento);

-- -----------------------------------------------------------------------------
-- 4. TABELA: atendimento
-- Protocolos de suporte, chamados técnicos, canais e resolução
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS atendimento CASCADE;
CREATE TABLE atendimento (
    id_chamado VARCHAR(14) PRIMARY KEY,
    id_cliente VARCHAR(10) NOT NULL REFERENCES clientes(id_cliente) ON DELETE RESTRICT,
    data_abertura TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    motivo_chamado VARCHAR(60), -- Permite NULL devido à falha de migração CRM (Imprevisto 1)
    canal_atendimento VARCHAR(30) NOT NULL,
    sistema_origem VARCHAR(40) NOT NULL,
    tempo_resolucao_horas NUMERIC(5, 1),
    resolvido_primeiro_contato INTEGER NOT NULL CHECK (resolvido_primeiro_contato IN (0, 1)),
    status_chamado VARCHAR(20) NOT NULL
);

CREATE INDEX idx_atendimento_cliente_abertura ON atendimento(id_cliente, data_abertura);
CREATE INDEX idx_atendimento_motivo ON atendimento(motivo_chamado);
CREATE INDEX idx_atendimento_sistema ON atendimento(sistema_origem);

-- -----------------------------------------------------------------------------
-- 5. TABELA: rede
-- Telemetria técnica de incidentes operacionais, quedas e degradação de sinal
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS rede CASCADE;
CREATE TABLE rede (
    id_evento_rede VARCHAR(14) PRIMARY KEY,
    id_cliente VARCHAR(10) NOT NULL REFERENCES clientes(id_cliente) ON DELETE RESTRICT,
    regiao VARCHAR(25) NOT NULL,
    data_evento TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    tipo_falha VARCHAR(40) NOT NULL,
    duracao_queda_minutos INTEGER NOT NULL CHECK (duracao_queda_minutos >= 0),
    taxa_perda_pacotes NUMERIC(5, 2) NOT NULL CHECK (taxa_perda_pacotes >= 0),
    latencia_media_ms NUMERIC(6, 1) NOT NULL CHECK (latencia_media_ms >= 0)
);

CREATE INDEX idx_rede_cliente_evento ON rede(id_cliente, data_evento);
CREATE INDEX idx_rede_regiao_evento ON rede(regiao, data_evento);

-- -----------------------------------------------------------------------------
-- 6. TABELA: cancelamentos
-- Registro oficial de desligamento contratual (alvo de churn e histórico)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS cancelamentos CASCADE;
CREATE TABLE cancelamentos (
    id_cancelamento VARCHAR(12) PRIMARY KEY,
    id_cliente VARCHAR(10) NOT NULL REFERENCES clientes(id_cliente) ON DELETE RESTRICT,
    data_cancelamento DATE NOT NULL,
    tipo_cancelamento VARCHAR(40) NOT NULL CHECK (tipo_cancelamento IN ('Voluntário', 'Involuntário por inadimplência')),
    motivo_declarado VARCHAR(60) NOT NULL
);

CREATE INDEX idx_cancelamentos_cliente_data ON cancelamentos(id_cliente, data_cancelamento);
CREATE INDEX idx_cancelamentos_tipo ON cancelamentos(tipo_cancelamento);
