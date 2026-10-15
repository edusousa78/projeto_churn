# ADR-003: Eficiência Econômica, Capacidade de Retenção e Priorização por Ranking
**Status:** Aprovado pelo CTO & Product Owner  
**Data:** Outubro de 2026  
**Contexto do Desafio:** Imprevisto 3 (Sprint 3 / Sprint 4)  
**Autor:** Cientista de Dados Júnior  
**Intervenientes:** Gerência de Retenção & Diretoria Comercial  

---

## 1. Contexto do Problema
Durante a validação preliminar dos modelos de propensão, observou-se uma armadilha corporativa clássica:
1. **Desbalanceamento e Limiar Arbitrário:** Modelos de Machine Learning avaliados com o limiar padrão ($p = 0,50$) praticamente não classificam clientes como churn ou geram previsões incompatíveis com a operação, pois a taxa natural da base é de ~2,8% a 4,0%.
2. **Capacidade Operacional Finita:** A equipe de telemarketing e retenção da Conecta Brasil Telecom possui capacidade humana e de discador limitada a abordar no máximo **10% da base ativa por mês** (em uma base de 500 mil clientes, isso equivale a 50 mil contatos mensais).
3. **Custo das Ofertas vs. Margem Preservada:** Se a empresa conceder descontos (ex.: R$ 20/mês ou upgrade gratuito) indiscriminadamente para clientes que não cancelariam espontaneamente (*falsos positivos*), a campanha gerará **destruição líquida de receita**.

---

## 2. Decisão Arquitetural e Metodológica

### 2.1 Abandono de Limiares Fixos em Favor do Ranqueamento Ordenado
- Não utilizaremos limiar estático ($0,50$). A saída analítica primária para a equipe de retenção será o **ranking decrescente de probabilidade calibrada de churn** ($P(\text{churn})$).
- A seleção para campanhas será parametrizada pela **capacidade de atendimento (Top K%)**, garantindo que a equipe foque estritamente nos clientes situados nos decis de maior ganho (Decil 1 e Decil 2).

### 2.2 Avaliação Econômica e Valor Esperado (Expected Value Framework)
Para cada cliente elegível priorizado, calculamos o retorno financeiro esperado da abordagem:

$$
\mathbb{E}[\text{Valor}] = P(\text{churn}) \times \text{Taxa Sucesso Retenção} \times \text{LTV Preservado} - \text{Custo da Oferta} - \text{Custo Operacional de Contato}
$$

- Se $\mathbb{E}[\text{Valor}] > 0$, o acionamento é economicamente viável.
- Se $\mathbb{E}[\text{Valor}] \le 0$, mesmo que o cliente tenha alta probabilidade de cancelamento, a retenção geraria prejuízo operacional e deve ser evitada.

### 2.3 Protocolo de Validação Causal via Grupo de Controle (A/B Test / Holdout)
Para assegurar que o impacto financeiro seja causalmente mensurável:
- **Grupo Tratamento (90% dos selecionados no Top 10%):** Recebe o contato ativo com oferta personalizada da retenção.
- **Grupo de Controle Holdout (10% dos selecionados no Top 10%):** Não recebe contato ativo (permanece no fluxo padrão da empresa).
- **Métrica de Negócio:** *Retenção Incremental (Uplift)*:
  $$\text{Retenção Incremental} = \text{Taxa Retenção}_{\text{Tratamento}} - \text{Taxa Retenção}_{\text{Controle}}$$
Isso isola matematicamente o efeito da campanha do comportamento espontâneo do cliente.

---

## 3. Consequências
- **Alinhamento com a Operação:** A esteira de Machine Learning gera listas dimensionadas exatamente para a capacidade de discagem da equipe.
- **Maximização do ROI:** Ofertas caras são restritas a clientes onde o risco e a margem justificam o investimento.
- **Transparência Executiva:** O sucesso do projeto é medido em **R$ de margem líquida incremental preservada**, e não apenas em AUC estática.
