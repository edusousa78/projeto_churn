# Dicionário de Dados Corporativo
**Empresa:** Conecta Brasil Telecom  
**Repositório:** Projeto 01 — Customer Churn Prediction & Retention Intelligence  
**Ambiente:** Relacional (SQL / SQLite / PostgreSQL) & Arquivos CSV Brutos (`data/raw/`)  

---

## 1. Tabela: `clientes`
Armazena os dados cadastrais, demográficos e de relacionamento de cada cliente ativo ou histórico.

| Coluna | Tipo de Dado | Restrição | Descrição | Domínio / Exemplo de Valores |
| :--- | :--- | :--- | :--- | :--- |
| `id_cliente` | VARCHAR(10) | PRIMARY KEY, NOT NULL | Identificador único do cliente no ecossistema | `CLI_000001`, `CLI_000002`, ... |
| `nome_cliente` | VARCHAR(100) | PII (LGPD), NOT NULL | Nome completo do titular do contrato | `Ana Silva`, `Carlos Santos` |
| `cpf` | VARCHAR(14) | PII (LGPD), NOT NULL | Cadastro de Pessoa Física formatado | `123.456.789-00` |
| `email` | VARCHAR(100) | PII (LGPD), NOT NULL | Endereço eletrônico de contato | `ana.silva12@email.com` |
| `regiao` | VARCHAR(20) | NOT NULL | Macrorregião geográfica da instalação | `Sudeste`, `Sul`, `Nordeste`, `Centro-Oeste`, `Norte` |
| `faixa_etaria` | VARCHAR(10) | NOT NULL | Faixa de idade do titular | `18-25`, `26-35`, `36-50`, `51-65`, `65+` |
| `genero` | VARCHAR(10) | NOT NULL | Identificação de gênero declarada | `F`, `M`, `Outro` |
| `data_cadastro` | DATE | NOT NULL | Data em que o cliente iniciou seu vínculo | `2021-04-15` (formato `YYYY-MM-DD`) |
| `tempo_relacionamento_meses`| INTEGER | NOT NULL, >= 0 | Antiguidade (tenure) do cliente em meses | `0`, `12`, `24`, `36`, ... |

---

## 2. Tabela: `contratos`
Detalha as características contratuais, vigência e opções de pagamento vigentes.

| Coluna | Tipo de Dado | Restrição | Descrição | Domínio / Exemplo de Valores |
| :--- | :--- | :--- | :--- | :--- |
| `id_contrato` | VARCHAR(10) | PRIMARY KEY, NOT NULL | Identificador único do contrato de prestação de serviços | `CTR_000001`, `CTR_000002`, ... |
| `id_cliente` | VARCHAR(10) | FOREIGN KEY (clientes) | Chave estrangeira que referencia o titular | `CLI_000001` |
| `tipo_plano` | VARCHAR(30) | NOT NULL | Categoria do plano contratado | `Fibra 300MB`, `Fibra 600MB`, `Fibra 1GB`, `Combo Fibra+Movel`, `Movel Individual`, `Corporativo PME` |
| `fidelizacao_meses` | INTEGER | NOT NULL, IN (0, 12, 24)| Período de carência/fidelidade contratual | `0` (sem fidelidade), `12`, `24` |
| `forma_pagamento` | VARCHAR(25) | NOT NULL | Método de cobrança recorrente | `Boleto Bancario`, `Cartao Credito`, `Debito Automatico`, `PIX` |
| `data_inicio` | DATE | NOT NULL | Data de ativação do contrato atual | `YYYY-MM-DD` |

---

## 3. Tabela: `faturamento`
Histórico mensal de títulos faturados, valores e comportamento de pagamento.

| Coluna | Tipo de Dado | Restrição | Descrição | Domínio / Exemplo de Valores |
| :--- | :--- | :--- | :--- | :--- |
| `id_fatura` | VARCHAR(12) | PRIMARY KEY, NOT NULL | Identificador único do documento de cobrança | `FAT_00000001` |
| `id_cliente` | VARCHAR(10) | FOREIGN KEY (clientes) | Chave do cliente faturado | `CLI_000001` |
| `mes_referencia` | VARCHAR(7) | NOT NULL | Ano e mês do ciclo faturado | `2024-05` (formato `YYYY-MM`) |
| `valor_fatura` | NUMERIC(10,2) | NOT NULL, > 0 | Valor bruto faturado em Reais (R$) | `129.90`, `149.90`, etc. |
| `data_vencimento` | DATE | NOT NULL | Data estipulada para liquidação do título | `YYYY-MM-DD` |
| `data_pagamento` | DATE | NULL (se em aberto) | Data efetiva do pagamento bancário | `YYYY-MM-DD` ou `NULL` |
| `dias_atraso` | INTEGER | NOT NULL, >= 0 | Dias decorridos entre o vencimento e a quitação | `0` (pontual), `5`, `15`, `45`, ... |
| `status_pagamento` | VARCHAR(20) | NOT NULL | Situação cadastral da cobrança | `Pago em dia`, `Pago com atraso`, `Inadimplente` |

---

## 4. Tabela: `atendimento`
Registro de contatos e solicitações realizadas pelo cliente em canais de atendimento.

| Coluna | Tipo de Dado | Restrição | Descrição | Domínio / Exemplo de Valores |
| :--- | :--- | :--- | :--- | :--- |
| `id_chamado` | VARCHAR(12) | PRIMARY KEY, NOT NULL | Protocolo de atendimento | `CHAM_0000001` |
| `id_cliente` | VARCHAR(10) | FOREIGN KEY (clientes) | Chave do cliente que abriu o chamado | `CLI_000001` |
| `data_abertura` | TIMESTAMP | NOT NULL | Data e hora de abertura do protocolo | `YYYY-MM-DD HH:MM:SS` |
| `motivo_chamado` | VARCHAR(50) | NULL (falha migração) | Assunto ou categoria do contato | `Lentidão ou Queda de Conexão`, `Cobrança Indevida`, `Dúvidas sobre Fatura`, `Falha de Equipamento/Roteador`, `Mudança de Endereço`, `Cancelamento Solicitado`, `NULL` |
| `canal_atendimento` | VARCHAR(20) | NOT NULL | Ponto de contato utilizado pelo cliente | `Call Center`, `WhatsApp`, `App Conecta`, `Loja Física` |
| `sistema_origem` | VARCHAR(30) | NOT NULL | Sistema CRM de registro | `Legado_CRM`, `Transição_CRM`, `Novo_OmniChannel`, `Sistema_Migracao_Incompleta` |
| `tempo_resolucao_horas` | NUMERIC(5,1) | NULL (falha migração) | Tempo até o encerramento do chamado | `1.5`, `24.0`, `NULL` |
| `resolvido_primeiro_contato`| INTEGER | NOT NULL, IN (0, 1) | Indicador First Contact Resolution (FCR) | `1` (sim), `0` (não) |
| `status_chamado` | VARCHAR(15) | NOT NULL | Situação final do chamado | `Fechado`, `Aberto` |

---

## 5. Tabela: `rede`
Telemetria técnica de incidentes operacionais, quedas de sinal e degradação de infraestrutura.

| Coluna | Tipo de Dado | Restrição | Descrição | Domínio / Exemplo de Valores |
| :--- | :--- | :--- | :--- | :--- |
| `id_evento_rede` | VARCHAR(12) | PRIMARY KEY, NOT NULL | Identificador do incidente técnico | `RED_0000001` |
| `id_cliente` | VARCHAR(10) | FOREIGN KEY (clientes) | Cliente impactado pelo incidente | `CLI_000001` |
| `regiao` | VARCHAR(20) | NOT NULL | Região do ponto de acesso afetado | `Sudeste`, `Sul`, `Nordeste`, etc. |
| `data_evento` | TIMESTAMP | NOT NULL | Momento em que a telemetria acusou a falha | `YYYY-MM-DD HH:MM:SS` |
| `tipo_falha` | VARCHAR(30) | NOT NULL | Classificação técnica da ocorrência | `Rompimento de Fibra`, `Manutenção Programada`, `Instabilidade Roteador`, `Degradação Sinal` |
| `duracao_queda_minutos`| INTEGER | NOT NULL, >= 0 | Tempo total de indisponibilidade | `15`, `60`, `360`, etc. |
| `taxa_perda_pacotes` | NUMERIC(5,2) | NOT NULL, >= 0 | Porcentagem média de pacotes IP perdidos | `1.2%`, `8.5%`, `15.0%` |
| `latencia_media_ms` | NUMERIC(6,1) | NOT NULL, >= 0 | Latência medida em milissegundos | `18.5`, `45.2`, `120.0` |

---

## 6. Tabela: `cancelamentos`
Registro consolidado de encerramento de contratos e desligamento de clientes.

| Coluna | Tipo de Dado | Restrição | Descrição | Domínio / Exemplo de Valores |
| :--- | :--- | :--- | :--- | :--- |
| `id_cancelamento` | VARCHAR(10) | PRIMARY KEY, NOT NULL | Registro de baixa de contrato | `CNC_000001` |
| `id_cliente` | VARCHAR(10) | FOREIGN KEY (clientes) | Cliente desligado | `CLI_000001` |
| `data_cancelamento` | DATE | NOT NULL | Data formal do cancelamento | `YYYY-MM-DD` |
| `tipo_cancelamento` | VARCHAR(35) | NOT NULL | Natureza da desativação | `Voluntário`, `Involuntário por inadimplência` |
| `motivo_declarado` | VARCHAR(50) | NOT NULL | Motivo coletado no desligamento | `Preço elevado / Concorrência`, `Instabilidade na Conexão`, `Mau Atendimento`, `Mudança de Endereço`, `Inadimplência prolongada` |
