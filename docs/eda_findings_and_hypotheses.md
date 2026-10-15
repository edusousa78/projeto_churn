# Relatório de Diagnóstico Exploratório e Validação de Hipóteses — Sprint 2
**Projeto:** Customer Churn Prediction & Retention Intelligence  
**Empresa:** Conecta Brasil Telecom  
**Base Analisada:** Safra de Treinamento Point-in-Time (17.330 clientes elegíveis)  
**Taxa Média de Churn Observada:** 3.97%  

---

## 1. Teste e Validação das Hipóteses de Negócio

### Hipótese 1: Clientes sem fidelidade contratual apresentam risco desproporcionalmente maior
- **Resultado:** **CONFIRMADA.**
- **Evidência Quantitativa:**
  - Churn em contratos sem fidelidade: **7.03%**
  - Churn em contratos com fidelidade (12 ou 24 meses): **3.10%**
  - **Lift de Risco:** Clientes sem fidelidade têm **2.3x mais chance de cancelar** no mês subsequente.

### Hipótese 2: Inadimplência recente e atrasos frequentes antecipam o desligamento
- **Resultado:** **CONFIRMADA.**
- **Evidência Quantitativa:**
  - Churn entre clientes com atraso severo recente (>15 dias): **7.07%**
  - Churn entre clientes adimplentes: **3.81%**
  - **Lift de Risco:** Clientes com fricção de faturamento apresentam **1.9x maior propensão ao cancelamento**.

### Hipótese 3: Volume elevado de chamados ao suporte técnico sinaliza atrito irreversível
- **Resultado:** **CONFIRMADA.**
- **Evidência Quantitativa:**
  - Churn para clientes com 3 ou mais chamados nos últimos 60 dias: **8.89%**
  - Churn para clientes sem nenhum chamado: **3.72%**
  - **Lift de Risco:** Clientes que abriram 3+ chamados têm **2.4x maior taxa de saída**.

### Hipótese 4: Instabilidade severa de rede e perda de pacotes aceleram a evasão
- **Resultado:** **CONFIRMADA.**
- **Evidência Quantitativa:**
  - Churn para clientes com instabilidade crítica de rede (>180 min de queda ou >5% perda de pacotes): **5.32%**
  - Churn para clientes com conexão estável: **3.90%**
  - **Lift de Risco:** Instabilidade técnica eleva a probabilidade de cancelamento em **1.4x**.

---

## 2. Implicações para a Modelagem Preditiva (Sprint 3)
1. **Poder Discriminatório das Features:** Os quatro pilares (contratual, financeiro, suporte e telemetria de rede) demonstraram forte separabilidade univariada. Modelos baseados em árvore e modelos lineares regularizados conseguirão capturar tanto os efeitos principais quanto interações complexas (ex.: cliente sem fidelidade + falha de rede recorrente).
2. **Invariância Temporal:** A relação entre fricção de atendimento e cancelamento manteve-se consistente mesmo com a presença de dados de transição de CRM, confirmando a robustez da estratégia da ADR-001.
3. **Revisão de Privacidade (ADR-002 Concluída):** Nenhuma variável pessoal identificável foi mantida na base analítica. O pipeline está plenamente seguro e em conformidade com a LGPD.
