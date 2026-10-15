# Documento de Requisitos de Negócio e Engenharia
**Projeto:** Customer Churn Prediction & Retention Intelligence  
**Organização:** Conecta Brasil Telecom  
**Área:** Diretoria Comercial & Gerência de Retenção  
**Versão:** 1.0 (Sprint 1)  
**Status:** Aprovado para Desenvolvimento  

---

## 1. Contexto e Motivação Estratégica
A Conecta Brasil Telecom é uma operadora de telecomunicações que atende 500 mil clientes ativos em serviços de banda larga fixa por fibra ótica, telefonia móvel e soluções corporativas.
A empresa opera atualmente sob um modelo de retenção reativo, abordando o cliente apenas quando este formaliza a insatisfação ou solicita o cancelamento definitivo.
Com uma taxa média de cancelamento mensal de 2,8% (~14.000 clientes/mês) e um ticket médio (ARPU) de R$ 120,00, a perda bruta mensal em faturamento recorrente atinge R$ 1,68 milhão.

### Objetivos do Projeto:
1. **Identificação Proativa de Risco:** Estimar com precisão a probabilidade individual de cancelamento nos próximos 30 dias com base no histórico comportamental, contratual, financeiro e operacional.
2. **Priorização Orientada a Retorno Econômico:** Substituir a concessão indiscriminada de descontos por uma fila de acionamento otimizada pela sensibilidade e valor econômico do cliente.
3. **Eficiência Operacional:** Adequar a lista de clientes priorizados à capacidade física e de discagem da equipe de retenção (ex.: Top 5% a 10% da base ativa).
4. **Governança e Reprodutibilidade:** Entregar uma esteira modular, testável, documentada e aderente à LGPD.

---

## 2. Partes Interessadas (Stakeholders) e Papéis

| Stakeholder | Papel no Projeto | Expectativa Principal |
| :--- | :--- | :--- |
| **CTO & Product Owner** | Patrocínio executivo, definição de metas e homologação | Rigor metodológico, prevenção de vazamento de dados e viabilidade econômica. |
| **Diretoria Comercial** | Patrocínio estratégico | Redução do churn mensal de 2,8% para 2,5% e preservação de receita recorrente. |
| **Gerência de Retenção** | Usuário operacional final | Lista mensal ranqueada por risco e explicabilidade dos fatores que motivaram o alerta. |
| **Engenharia de Dados** | Provedor de infraestrutura | Pipelines reproduzíveis, consultas SQL eficientes e integridade das fontes. |
| **Cientista de Dados (Você)** | Desenvolvedor técnico da solução | Modelagem, validação temporal, tratamento de contingências e comunicação dos resultados. |

---

## 3. Requisitos Funcionais (RF)

- **RF-01 (Ingestão Relacional):** O sistema deve consolidar dados de 6 fontes primárias (`clientes`, `contratos`, `faturamento`, `atendimento`, `rede`, `cancelamentos`).
- **RF-02 (Corte Temporal - Point-in-Time):** A esteira deve calcular atributos preditivos estritamente antes ou na data de corte $T_0$, eliminando qualquer dependência de eventos posteriores.
- **RF-03 (Classificação e Probabilidade):** O modelo deve estimar a propensão de churn em uma escala contínua de probabilidade $P(\text{churn}) \in [0, 1]$.
- **RF-04 (Segmentação por Faixa de Risco):** Os clientes devem ser categorizados em decis de risco (Decil 1 = maior risco, Decil 10 = menor risco) e faixas operacionais (`Crítico`, `Alto`, `Médio`, `Baixo`).
- **RF-05 (Fatores Explicativos):** O produto analítico deve indicar as variáveis que mais contribuíram para a elevação do risco de cada cliente (explicabilidade local).
- **RF-06 (Saída Pseudonimizada):** A lista final para a operação comercial deve conter identificadores pseudonimizados, probabilidade, faixa de risco e receita associada.

---

## 4. Requisitos Não Funcionais (RNF)

- **RNF-01 (Reprodutibilidade):** O pipeline deve permitir execução de ponta a ponta a partir de um comando único, com controle estrito de sementes aleatórias (`seed=42`).
- **RNF-02 (Privacidade e LGPD):** Dados pessoais sensíveis (CPF, nome completo, e-mail) não devem transitar na camada de treinamento nem ser versionados no repositório.
- **RNF-03 (Validação Temporal OOT):** A performance dos modelos deve ser avaliada em um conjunto de dados posterior no tempo (*Out-of-Time*) em relação ao conjunto de treino.
- **RNF-04 (Testabilidade Automatizada):** Regras de integridade de dados e lógica de inferência devem possuir cobertura de testes automatizados via `pytest`.
- **RNF-05 (Performance e Custo Computacional):** O treinamento e a inferência devem rodar de forma eficiente em ambiente padrão, sem dependência obrigatória de clusters caros.

---

## 5. Indicadores Chave de Sucesso (KPIs)

### KPIs Técnicos
- **ROC-AUC:** Meta $\ge 0,75$ no conjunto Out-of-Time.
- **PR-AUC:** Ganho substancial sobre a prevalência basal (~0,028).
- **Recall no Top 10%:** Capturar no mínimo 30% a 35% de todos os cancelamentos nos 10% de clientes com maior score.
- **Precisão no Top 10%:** Superar significativamente a taxa média da base.
- **Brier Score / Calibração:** Probabilidades calibradas para suporte a decisões financeiras.

### KPIs de Negócio
- **Taxa Mensal de Churn:** Redução do patamar de 2,8% para 2,5%.
- **Receita Preservada Teórica:** Até R$ 180.000,00/mês em 500k clientes.
- **ROI da Campanha de Retenção:** Positivo, calculado por $\frac{\text{Benefício Incremental Líquido}}{\text{Custo Incremental da Campanha}}$.
