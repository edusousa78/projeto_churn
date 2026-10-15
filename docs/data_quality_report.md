# Relatório de Qualidade e Auditoria dos Dados — Sprint 1
**Projeto:** Customer Churn Prediction & Retention Intelligence  
**Empresa:** Conecta Brasil Telecom  
**Responsável Técnico:** Cientista de Dados Júnior (BI / Data Science)  
**Destinatário:** CTO & Product Owner  
**Data da Auditoria:** Outubro de 2026  

---

## 1. Resumo Executivo da Auditoria
A auditoria foi realizada sobre as 6 tabelas relacionais que compõem o ecossistema de dados da Conecta Brasil Telecom. O objetivo foi validar chaves, integridade referencial, completude de campos e mapear o impacto operacional da migração de CRM ocorrida entre março e maio de 2024.

### Principais Conclusões:
1. **Unicidade e Integridade Primária (100% Aprovado):** Todas as chaves primárias são estritamente únicas e sem duplicidades.
2. **Integridade Referencial (100% Aprovado):** Não foram detectados registros órfãos nas tabelas filhas. Todos os clientes referenciados existem na tabela `clientes`.
3. **Métricas de Negócio Confirmadas:**
   - **Receita Média Mensal (ARPU):** R$ 127.49 (em total conformidade com a premissa de negócio de R$ 120,00).
   - **Taxa de Inadimplência em Faturas:** 0.18%.
   - **Cancelamentos Históricos Mapeados:** 5,697 registros (4,983 voluntários e 714 involuntários).
4. **Alerta Crítico Diagnosticado (Imprevisto 1):** Confirmada anomalia de sistema na tabela `atendimento` concentrada nos meses `2024-03`, `2024-04` e `2024-05`.

---

## 2. Auditoria de Chaves Primárias e Unicidade

| Tabela | Chave Primária | Total de Linhas | Valores Únicos | Registros Duplicados | Avaliação |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `clientes` | `id_cliente` | 25,000 | 25,000 | 0 | **APROVADO (100% único)** |
| `contratos` | `id_contrato` | 25,000 | 25,000 | 0 | **APROVADO (100% único)** |
| `faturamento` | `id_fatura` | 212,691 | 212,691 | 0 | **APROVADO (100% único)** |
| `atendimento` | `id_chamado` | 13,139 | 13,139 | 0 | **APROVADO (100% único)** |
| `rede` | `id_evento_rede` | 26,048 | 26,048 | 0 | **APROVADO (100% único)** |
| `cancelamentos` | `id_cancelamento` | 5,697 | 5,697 | 0 | **APROVADO (100% único)** |

---

## 3. Integridade Referencial (Chaves Estrangeiras)

| Tabela Filha | Chave Estrangeira | Registros Avaliados | Registros Órfãos | Status de Integridade |
| :--- | :--- | :--- | :--- | :--- |
| `contratos` | `id_cliente` | 25,000 | 0 | **APROVADO (0 órfãos)** |
| `faturamento` | `id_cliente` | 212,691 | 0 | **APROVADO (0 órfãos)** |
| `atendimento` | `id_cliente` | 13,139 | 0 | **APROVADO (0 órfãos)** |
| `rede` | `id_cliente` | 26,048 | 0 | **APROVADO (0 órfãos)** |
| `cancelamentos` | `id_cliente` | 5,697 | 0 | **APROVADO (0 órfãos)** |

---

## 4. Diagnóstico Detalhado do Imprevisto 1: Migração do Sistema de Atendimento

### Contexto do Problema
Durante a transição da plataforma de suporte do `Legado_CRM` para o `Novo_OmniChannel` (entre 01/03/2024 e 31/05/2024), a esteira de captura de chamados apresentou falhas de mapeamento de esquema, rotulando os registros como `Sistema_Migracao_Incompleta` e deixando campos essenciais sem preenchimento.

### Evidência Quantitativa Mês a Mês:

| Mês de Abertura | Total de Chamados | Chamados sem Motivo | % Nulos no Motivo | Chamados sem Tempo Resolução | Sistemas de Origem Identificados |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `2023-07` | 739 | 0 | **0.0%** | 0 | `Legado_CRM` |
| `2023-08` | 808 | 0 | **0.0%** | 0 | `Legado_CRM` |
| `2023-09` | 814 | 0 | **0.0%** | 0 | `Legado_CRM` |
| `2023-10` | 912 | 0 | **0.0%** | 0 | `Legado_CRM` |
| `2023-11` | 939 | 0 | **0.0%** | 0 | `Legado_CRM` |
| `2023-12` | 1,033 | 0 | **0.0%** | 0 | `Legado_CRM` |
| `2024-01` | 1,118 | 0 | **0.0%** | 0 | `Legado_CRM` |
| `2024-02` | 1,101 | 0 | **0.0%** | 0 | `Legado_CRM` |
| `2024-03` | 1,341 | 627 | **46.8%** | 627 | `Transição_CRM, Sistema_Migracao_Incompleta` |
| `2024-04` | 1,247 | 548 | **43.9%** | 548 | `Sistema_Migracao_Incompleta, Transição_CRM` |
| `2024-05` | 1,452 | 644 | **44.4%** | 644 | `Sistema_Migracao_Incompleta, Transição_CRM` |
| `2024-06` | 1,591 | 0 | **0.0%** | 0 | `Novo_OmniChannel` |
| `2024-07` | 44 | 0 | **0.0%** | 0 | `Novo_OmniChannel` |

### Análise Técnica do Padrão de Ausência:
- **Classificação:** Não se trata de ausência puramente aleatória (*MCAR - Missing Completely At Random*). É uma ausência sistemática dependente do período (*MAR - Missing At Random* condicional à data do evento e ao canal de integração).
- **Risco de Viés:** Imputar valores médios ou categorias arbitrárias (como "Sem Reclamação") criaria uma falsa percepção de satisfação para clientes que ligaram para o suporte mas tiveram seus dados corrompidos pelo sistema.
- **Decisão Metodológica (ADR-001):**
  1. A variável mais confiável de suporte é a **frequência de chamados abertos** (o ID e a data de abertura foram preservados em 100% das ocorrências).
  2. Em vez de descartar os 3 meses de histórico (o que destruiria o sinal recente anterior à data de previsão), criaremos atributos agregados baseados na **contagem de interações** e categorizaremos o motivo ausente sob uma categoria explícita `Nao_Informado_Migracao`, tratando a incerteza de forma transparente sem introduzir viés artificial.

---

## 5. Auditoria de Nulos Geral por Tabela e Coluna

| Tabela | Coluna | Tipo de Dado | Linhas Totais | Qtd Nulos | % Ausência | Diagnóstico / Tratamento |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `clientes` | `id_cliente` | `object` | 25,000 | 0 | 0.0% | Completude 100% |
| `clientes` | `nome_cliente` | `object` | 25,000 | 0 | 0.0% | Completude 100% |
| `clientes` | `cpf` | `object` | 25,000 | 0 | 0.0% | Completude 100% |
| `clientes` | `email` | `object` | 25,000 | 0 | 0.0% | Completude 100% |
| `clientes` | `regiao` | `object` | 25,000 | 0 | 0.0% | Completude 100% |
| `clientes` | `faixa_etaria` | `object` | 25,000 | 0 | 0.0% | Completude 100% |
| `clientes` | `genero` | `object` | 25,000 | 0 | 0.0% | Completude 100% |
| `clientes` | `data_cadastro` | `object` | 25,000 | 0 | 0.0% | Completude 100% |
| `clientes` | `tempo_relacionamento_meses` | `int64` | 25,000 | 0 | 0.0% | Completude 100% |
| `contratos` | `id_contrato` | `object` | 25,000 | 0 | 0.0% | Completude 100% |
| `contratos` | `id_cliente` | `object` | 25,000 | 0 | 0.0% | Completude 100% |
| `contratos` | `tipo_plano` | `object` | 25,000 | 0 | 0.0% | Completude 100% |
| `contratos` | `fidelizacao_meses` | `int64` | 25,000 | 0 | 0.0% | Completude 100% |
| `contratos` | `forma_pagamento` | `object` | 25,000 | 0 | 0.0% | Completude 100% |
| `contratos` | `data_inicio` | `object` | 25,000 | 0 | 0.0% | Completude 100% |
| `faturamento` | `id_fatura` | `object` | 212,691 | 0 | 0.0% | Completude 100% |
| `faturamento` | `id_cliente` | `object` | 212,691 | 0 | 0.0% | Completude 100% |
| `faturamento` | `mes_referencia` | `object` | 212,691 | 0 | 0.0% | Completude 100% |
| `faturamento` | `valor_fatura` | `float64` | 212,691 | 0 | 0.0% | Completude 100% |
| `faturamento` | `data_vencimento` | `object` | 212,691 | 0 | 0.0% | Completude 100% |
| `faturamento` | `data_pagamento` | `object` | 212,691 | 385 | 0.18% | Faturas em aberto / inadimplentes |
| `faturamento` | `dias_atraso` | `int64` | 212,691 | 0 | 0.0% | Completude 100% |
| `faturamento` | `status_pagamento` | `object` | 212,691 | 0 | 0.0% | Completude 100% |
| `atendimento` | `id_chamado` | `object` | 13,139 | 0 | 0.0% | Completude 100% |
| `atendimento` | `id_cliente` | `object` | 13,139 | 0 | 0.0% | Completude 100% |
| `atendimento` | `data_abertura` | `object` | 13,139 | 0 | 0.0% | Completude 100% |
| `atendimento` | `motivo_chamado` | `object` | 13,139 | 1,819 | 13.84% | Falha de migração CRM (Imprevisto 1) |
| `atendimento` | `canal_atendimento` | `object` | 13,139 | 0 | 0.0% | Completude 100% |
| `atendimento` | `sistema_origem` | `object` | 13,139 | 0 | 0.0% | Completude 100% |
| `atendimento` | `tempo_resolucao_horas` | `float64` | 13,139 | 1,819 | 13.84% | Falha de migração CRM (Imprevisto 1) |
| `atendimento` | `resolvido_primeiro_contato` | `int64` | 13,139 | 0 | 0.0% | Completude 100% |
| `atendimento` | `status_chamado` | `object` | 13,139 | 0 | 0.0% | Completude 100% |
| `rede` | `id_evento_rede` | `object` | 26,048 | 0 | 0.0% | Completude 100% |
| `rede` | `id_cliente` | `object` | 26,048 | 0 | 0.0% | Completude 100% |
| `rede` | `regiao` | `object` | 26,048 | 0 | 0.0% | Completude 100% |
| `rede` | `data_evento` | `object` | 26,048 | 0 | 0.0% | Completude 100% |
| `rede` | `tipo_falha` | `object` | 26,048 | 0 | 0.0% | Completude 100% |
| `rede` | `duracao_queda_minutos` | `int64` | 26,048 | 0 | 0.0% | Completude 100% |
| `rede` | `taxa_perda_pacotes` | `float64` | 26,048 | 0 | 0.0% | Completude 100% |
| `rede` | `latencia_media_ms` | `float64` | 26,048 | 0 | 0.0% | Completude 100% |
| `cancelamentos` | `id_cancelamento` | `object` | 5,697 | 0 | 0.0% | Completude 100% |
| `cancelamentos` | `id_cliente` | `object` | 5,697 | 0 | 0.0% | Completude 100% |
| `cancelamentos` | `data_cancelamento` | `object` | 5,697 | 0 | 0.0% | Completude 100% |
| `cancelamentos` | `tipo_cancelamento` | `object` | 5,697 | 0 | 0.0% | Completude 100% |
| `cancelamentos` | `motivo_declarado` | `object` | 5,697 | 0 | 0.0% | Completude 100% |

---

## 6. Parecer Técnico de Viabilidade para Modelagem

| Critério de Viabilidade | Status | Justificativa Técnica |
| :--- | :--- | :--- |
| **Identificação do Churn** | **Aprovado** | Histórico de cancelamento possui datas explícitas e distinção entre churn voluntário e involuntário. |
| **Rastreabilidade Temporal** | **Aprovado** | Todas as tabelas possuem carimbos de data/hora permitindo reconstruir snapshots em $T_0$ sem data leakage. |
| **Integridade Relacional** | **Aprovado** | 100% de consistência entre clientes, contratos e transações. |
| **Mitigação do Imprevisto 1** | **Aprovado** | Solução estruturada na contagem de chamados e categorização explícita de nulos sem imputação sintética enviesada. |

**Conclusão da Auditoria:** Os dados foram auditados, validados e aprovados para a continuidade do projeto. A base está apta para a Análise Exploratória e Engenharia de Atributos da Sprint 2.
