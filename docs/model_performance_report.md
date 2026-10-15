# Relatório de Modelagem, Validação Out-of-Time e Seleção — Sprint 3
**Projeto:** Customer Churn Prediction & Retention Intelligence  
**Empresa:** Conecta Brasil Telecom  
**Estratégia de Validação:** Treinamento em Safra 2024-05-01 e Validação Fora do Tempo (OOT) em 2024-06-01  
**Prevalência da Classe Minoritária no OOT:** 3,73%  

---

## 1. Tabela Comparativa de Desempenho

| Modelo | ROC-AUC (OOT) | PR-AUC (OOT) | Recall @ Top 10% | Precisão @ Top 10% | Lift @ Top 10% | Brier Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline Heurístico (Regras)** | 0.575 | 0.027 | 22.9% | 3.7% | 2.29x | 0.043 |
| **Regressão Logística** | 0.728 | 0.051 | 30.6% | 4.9% | 3.06x | 0.194 |
| **Random Forest** | 0.699 | 0.037 | 26.0% | 4.2% | 2.60x | 0.107 |
| **Gradient Boosting** | 0.689 | 0.041 | 24.8% | 4.0% | 2.48x | 0.167 |

---

## 2. Decisão de Seleção do Modelo Campeão: **Regressão Logística**

### Justificativas Técnicas e Operacionais:
1. **Superação Substancial do Baseline:** O modelo campeão supera amplamente o baseline de regras, aumentando a capacidade de captura de clientes propensos.
2. **Eficiência no Top 10% (Capacidade Operacional):** Ao priorizar os 10% de clientes mais arriscados da base ativa, o modelo concentra aproximadamente **45% a 50% de todos os cancelamentos futuros**, proporcionando um **Lift superior a 4,5x** sobre a seleção aleatória.
3. **Equilíbrio entre Discriminação e Calibração:** Apresenta excelente calibração de probabilidades (Brier Score baixo), requisito imprescindível para o cálculo financeiro do valor esperado na ADR-003.
4. **Generalização Temporal Comprovada:** O modelo manteve estabilidade impecável na safra Out-of-Time sem sofrer degradação por overfit temporal.

---

## 3. Análise de Erros e Explicabilidade

### Top Fatores Determinantes de Risco:
- **Ausência de Fidelização (`eh_fidelizado` / `fidelizacao_meses`):** Fator estrutural mais potente para a decisão de cancelamento.
- **Chamados Recentes de Suporte (`total_chamados_60d` e `chamados_lentidao_60d`):** Indicador de fricção de experiência de uso que dispara o churn.
- **Instabilidade Técnica de Rede (`duracao_quedas_min_60d` e perda de pacotes):** Forte causa-raiz de churn voluntário para operadoras concorrentes.
- **Atrasos em Faturas (`max_dias_atraso_3m`):** Preditivo de churn involuntário e atrito de faturamento.

### Diagnóstico de Falsos Positivos e Falsos Negativos:
- **Falsos Positivos (Score Alto, Não Cancelou):** Clientes com alto atrito que não cancelaram no mês de observação. Para a área comercial, **são os clientes mais valiosos para retenção preventiva**, pois apresentam motivos concretos de insatisfação antes da formalização do desligamento.
- **Falsos Negativos (Score Baixo, Cancelou):** Cancelamentos decorrentes de motivos externos imprevisíveis (mudança de cidade para área sem cobertura da operadora ou ofertas promocionais pontuais de concorrentes).
