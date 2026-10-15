# Definição Analítica da Variável-Alvo e Estratégia de Validação Temporal
**Projeto:** Customer Churn Prediction & Retention Intelligence  
**Organização:** Conecta Brasil Telecom  
**Versão:** 1.0 (Sprint 1)  

---

## 1. Formulação Matemática do Problema
O problema é estruturado como uma tarefa de **Classificação Binária Supervisionada com Horizonte Temporal Fixo**.

Para um determinado cliente ativo $i$ observado no momento de corte $T_0$, a variável-alvo $Y_i \in \{0, 1\}$ é definida como:

$$
Y_i = 
\begin{cases} 
1, & \text{se o cliente formalizar o cancelamento do serviço no intervalo } (T_0, T_0 + 30\text{ dias}] \\
0, & \text{se o cliente permanecer ativo durante todo o intervalo } (T_0, T_0 + 30\text{ dias}]
\end{cases}
$$

---

## 2. Ponto de Corte Temporal ($T_0$) e Janelas Operacionais

Para simular o ambiente real de produção da Conecta Brasil Telecom, adotamos uma estratégia de validação temporal estrita (*Point-in-Time*):

```
Histórico de Eventos                       Data de Corte (T_0)       Horizonte Preditivo (30 dias)
[Consumo, Faturas, Chamados, Rede] ------------> | ---------------------> [Y = 1 se cancelou / Y = 0 se ativo]
                                                 |
                                         Apenas dados até T_0
                                         são usados em Features
```

### Configuração dos Períodos de Modelagem:
1. **Safra de Treinamento ($T_{train}$):** Data de corte em `2024-05-01`.
   - **Histórico de Atributos:** Eventos ocorridos até `2024-05-01 00:00:00`.
   - **Janela de Observação do Alvo ($Y_{train}$):** `2024-05-01` a `2024-05-31`.
2. **Safra de Validação Fora do Tempo / Out-of-Time ($T_{test}$):** Data de corte em `2024-06-01`.
   - **Histórico de Atributos:** Eventos ocorridos até `2024-06-01 00:00:00`.
   - **Janela de Observação do Alvo ($Y_{test}$):** `2024-06-01` a `2024-06-30`.

---

## 3. Critérios de Elegibilidade (Inclusão e Exclusão de Clientes)

### Critérios de Inclusão na Base Analítica (ABT):
1. O cliente deve possuir contrato ativo no instante $T_0$.
2. O cliente deve ter no mínimo 30 dias de relacionamento na operadora em $T_0$ (`data_cadastro <= T_0 - 30 dias`).
3. O cliente deve possuir pelo menos 1 fatura gerada no histórico.

### Critérios de Exclusão:
1. Clientes que já cancelaram seus serviços em datas $t \le T_0$ (não são clientes ativos sob risco de churn futuro).
2. Clientes com contratos corporativos sob negociação judicial ou suspensão regulatória específica.
3. Clientes com tempo de observação inferior a 30 dias após $T_0$ que não tenham cancelado (evita viés de censura à direita).

---

## 4. Regras Antitransbordamento (Prevenção Estrita de Data Leakage)

O vazamento de dados é o risco mais destrutivo em modelos de propensão. Para garantir integridade:
- **Regra Leakage 01 (Chamados de Cancelamento):** Chamados com motivo "Cancelamento Solicitado" abertos após $T_0$ são consequência do evento alvo e **nunca** poderão ser utilizados como preditores.
- **Regra Leakage 02 (Eventos Financeiros):** Pagamentos ou faturas emitidas com data posterior a $T_0$ são sumariamente bloqueados na construção de atributos daquela safra.
- **Regra Leakage 03 (Agregações de Suporte e Rede):** Janelas móveis (ex.: chamados nos últimos 30 dias, quedas de rede nos últimos 60 dias) consideram estritamente o intervalo $[T_0 - \Delta, T_0]$.
