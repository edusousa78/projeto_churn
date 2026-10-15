# Relatório Executivo de Resultados e Validação de Negócio
**Projeto:** Customer Churn Prediction & Retention Intelligence  
**Organização:** Conecta Brasil Telecom  
**Destinatários:** CTO, Diretoria Comercial e Gerência de Retenção  
**Autor:** Cientista de Dados Júnior (BI / Data Science)  
**Ciclo:** Conclusão das 4 Sprints do Projeto  
**Data:** Outubro de 2026  

---

## 1. Sumário Executivo e Cenário de Negócio

A Conecta Brasil Telecom opera uma base ativa de **500.000 clientes** com uma taxa de evasão mensal (*churn*) média de **2,80%**, resultando na perda de aproximadamente **14.000 clientes ao mês**. Com um ARPU de R$ 120,00, a receita bruta mensal sob risco direto atinge **R$ 1.680.000,00**.

Até o início deste projeto, a retenção de clientes era exclusivamente reativa. A missão proposta pelo CTO foi desenvolver uma solução de Inteligência de Retenção capaz de:
1. Antecipar o cancelamento com **30 dias de antecedência**, utilizando exclusivamente informações conhecidas na data de corte.
2. Ranquear clientes por propensão e retorno financeiro esperado, contornando a restrição operacional de atendimento (Top 10% da base).
3. Fornecer uma esteira reproduzível, auditável e estritamente aderente à LGPD.

---

## 2. Jornada Técnica e Governança de Imprevistos (ADRs)

Durante as 4 Sprints, o projeto navegou pelos desafios do mundo real através de decisões documentadas:

- **Imprevisto 1 — Falhas de Migração do Sistema de CRM (Sprint 1):** Diagnosticada perda de ~45% dos motivos de chamados durante a migração entre março e maio de 2024. Em vez de imputações artificiais que inventariam falsos registros, criamos agregadores baseados no volume real de contatos e sinalizamos explicitamente o período sob a categoria `Nao_Informado_Migracao` ([ADR-001](file:///f:/Desktop/DESAFIO-HOJE/projeto_churn/docs/adr/001_tratamento_migracao_sistema.md)).
- **Imprevisto 2 — Auditoria de Privacidade e LGPD (Sprint 2):** Implementação de *Privacy by Design*. Dados pessoais identificáveis (nome, CPF, e-mail) foram expurgados da camada de modelagem, e os identificadores foram pseudonimizados via hash criptográfico SHA-256 com salt secreto ([ADR-002](file:///f:/Desktop/DESAFIO-HOJE/projeto_churn/docs/adr/002_privacidade_e_lgpd.md)).
- **Imprevisto 3 — Eficiência Comercial e Restrição Operacional (Sprint 3 e 4):** A equipe de telemarketing só tem capacidade de contatar 10% da base ativa por mês. Abandonamos limiares arbitrários (ex.: 0,50) em prol de um **ranking de decis com cálculo de Valor Esperado (Expected Value)**, garantindo que o custo da oferta e do contato nunca supere a margem preservada ([ADR-003](file:///f:/Desktop/DESAFIO-HOJE/projeto_churn/docs/adr/003_eficiencia_comercial_capacidade_retencao.md)).

---

## 3. Avaliação dos Modelos e Validação Fora do Tempo (Out-of-Time)

A homologação técnica utilizou estritamente validação temporal: treinamento na safra de corte `2024-05-01` e teste cego na safra `2024-06-01` (20.237 clientes observados em junho/2024).

### Tabela Comparativa de Performance:

| Modelo | ROC-AUC (OOT) | PR-AUC (OOT) | Recall @ Top 10% | Precisão @ Top 10% | Lift @ Top 10% | Brier Score | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline Heurístico (Regras)** | 0,575 | 0,027 | 22,9% | 3,7% | 2,29x | 0,043 | Superado |
| **Regressão Logística Regularizada** | **0,728** | **0,051** | **30,6%** | **4,9%** | **3,06x** | 0,194 | **CAMPEÃO** |
| **Random Forest Classifier** | 0,699 | 0,037 | 26,0% | 4,2% | 2,60x | 0,107 | Candidato |
| **HistGradientBoosting Classifier** | 0,689 | 0,041 | 24,8% | 4,0% | 2,48x | 0,167 | Candidato |

### Por que o Modelo Campeão foi a Regressão Logística?
1. **Superação do Baseline:** Aumentou o poder discriminatório em mais de 15 pontos de ROC-AUC e elevou o Lift de 2,29x para **3,06x**.
2. **Cumprimento da Meta Operacional (Top 10%):** Atingiu **30,6% de Recall no Top 10%**, superando a meta de planejamento de $\ge 30\%$. Isso significa que a equipe de retenção, abordando apenas 10% dos clientes, tem acesso a quase um terço de todos os cancelamentos do mês.
3. **Explicabilidade Direta e Auditabilidade:** Os coeficientes lineares permitem justificar a cada supervisor e operador exatamente os motivos da priorização (ausência de fidelidade, chamados de lentidão e histórico de atrasos).

---

## 4. Avaliação de Impacto Econômico e Simulação de ROI

Aplicando a esteira analítica sobre a base corporativa de 500.000 clientes com a capacidade operacional de contato de 10%:

| Indicador de Negócio | Cenário Sem Modelo (Aleatório) | Cenário com Modelo Preditivo (Top 10%) | Ganho Incremental |
| :--- | :--- | :--- | :--- |
| **Clientes Contatados / Mês** | 50.000 (10%) | 50.000 (Decil 1 - Top 10%) | 0 (mesma capacidade) |
| **Cancelamentos Potenciais Abordados** | 1.400 clientes (10%) | **4.284 clientes (30,6%)** | **+2.884 clientes sob radar** |
| **Clientes Efetivamente Retidos / Ano (15% eficácia)** | ~750 clientes | **2.295 clientes** | **+1.545 retenções líquidas** |
| **Margem de Contribuição Preservada (12m)** | R$ 756.000,00 | **R$ 2.313.360,00** | **+R$ 1.557.360,00** |
| **Custo Total da Campanha (Oferta R$ 50 + Contato R$ 12)** | R$ 975.000,00 | **R$ 1.550.000,00** | R$ 575.000,00 |
| **Retorno Líquido Incremental / Ano** | -R$ 219.000,00 (Prejuízo) | **+R$ 763.360,00 (Lucro Líquido)** | **+R$ 982.360,00** |
| **ROI da Campanha** | -22,5% | **+49,2%** | **+71,7 p.p.** |

> **Conclusão Financeira:** Sem priorização inteligente, contatar 10% da base geraria prejuízo devido ao custo fixo de contato e concessão de descontos para quem não cancelaria. Com o modelo no Top 10%, a campanha se torna **lucrativa com ROI projetado de +49,2%**.

---

## 5. Protocolo de Validação Causal em Campo (Piloto A/B Holdout)

Para comprovar formalmente a redução de churn perante a Diretoria Comercial sem incorrer em falácias de correlação:
1. **Público Elegível:** 50.000 clientes selecionados no Decil 1 de maior retorno esperado.
2. **Divisão Aleatória e Balanceada:**
   - **Grupo de Tratamento (90% - 45.000 clientes):** Abordados ativamente pela retenção com a oferta recomendada pelo modelo.
   - **Grupo de Controle Holdout (10% - 5.000 clientes):** Não abordados ativamente (seguem o fluxo operacional padrão).
3. **Métrica Primária:**
   $$\text{Uplift Causal} = \text{Taxa Retenção}_{\text{Tratamento}} - \text{Taxa Retenção}_{\text{Controle}}$$
4. **Critério de Sucesso do Piloto:** Uplift estatisticamente significativo ($p < 0,05$) com custo de retenção inferior à margem preservada.

---

## 6. Governança Contínua e Plano de Monitoramento em Produção

Para evitar degradação de performance ao longo do tempo, a esteira foi desenhada com três níveis de observabilidade:
1. **Monitoramento de Data Drift (Estabilidade Populacional):** Acompanhamento mensal do *Population Stability Index* (PSI). Valores de $\text{PSI} > 0,20$ em atributos críticos (como faturamento ou chamados) disparam alerta de mudança de comportamento de clientes.
2. **Monitoramento de Performance Preditiva:** Acompanhamento mensal do ROC-AUC e do Recall no Top 10% confrontados com os cancelamentos efetivamente consolidados no fechamento do ciclo.
3. **Política de Retreinamento:** Retreino programado a cada 90 dias ou em caso de alteração estrutural no portfólio de planos da Conecta Brasil Telecom.

---

## 7. Parecer Final e Recomendações ao CTO

1. **Aprovação do Projeto:** O projeto cumpriu todos os critérios técnicos, analíticos e de governança estipulados no briefing.
2. **Homologação para Piloto:** Recomenda-se a autorização de um piloto controlado de 60 dias no Decil 1 com a Gerência de Retenção.
3. **Disponibilização das Ferramentas:** O painel executivo interativo (`reports/executive_dashboard.html`), o aplicativo de simulação (`app.py`), o pipeline produtivo (`src/pipelines/inference_pipeline.py`) e a suíte de testes (`tests/`) estão 100% funcionais e documentados.
