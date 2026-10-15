# ADR-001: Tratamento de Dados Ausentes Decorrentes da Migração do Sistema de CRM
**Status:** Aprovado pelo CTO & Product Owner  
**Data:** Outubro de 2026  
**Contexto do Desafio:** Imprevisto 1 (Sprint 1 / Sprint 2)  
**Autor:** Cientista de Dados Júnior  

---

## 1. Contexto do Problema
Entre **01/03/2024 e 31/05/2024**, a Conecta Brasil Telecom realizou uma migração gradual de seu sistema de atendimento (`Legado_CRM`) para uma nova plataforma de atendimento ao cliente (`Novo_OmniChannel`).
Durante esse trimestre de transição:
- A camada de ingestão apresentou instabilidade no mapeamento dos campos `motivo_chamado` e `tempo_resolucao_horas`.
- Cerca de **45% dos chamados abertos no período** foram persistidos com valores nulos nesses atributos ou rotulados sob o sistema de origem transitório (`Sistema_Migracao_Incompleta`).
- Por outro lado, a identificação do protocolo (`id_chamado`), o identificador do cliente (`id_cliente`) e a data/hora exata de abertura (`data_abertura`) mantiveram **100% de integridade**.

---

## 2. Alternativas Avaliadas

### Alternativa A: Exclusão Completa dos 3 Meses de Histórico
- **Mecanismo:** Descartar todos os registros de chamados ocorridos entre março e maio de 2024.
- **Avaliação:** **Inviável e prejudicial.** Como as safras de corte de modelagem estão situadas em `2024-05-01` e `2024-06-01`, descartar esses meses eliminaria o sinal comportamental mais recente e preditivo do cliente.

### Alternativa B: Imputação Sintética Cega (Média ou Moda)
- **Mecanismo:** Preencher `motivo_chamado` com a moda histórica ("Lentidão") e `tempo_resolucao_horas` com a média geral (~18 horas).
- **Avaliação:** **Inadequada e temerária.** A ausência não é aleatória (*MCAR*), mas vinculada ao sistema (*MAR*). Imputar valores arbitrários inventaria evidências falsas de satisfação ou de falha técnica para clientes específicos, enviesando os coeficientes do modelo.

### Alternativa C: Engenharia de Atributos Resiliente com Categoria Explícita de Incerteza (ESCOLHIDA)
- **Mecanismo:**
  1. Preservar a **frequência total de chamados** abertos pelo cliente em janelas móveis (30d, 60d, 90d), visto que a ocorrência do contato é 100% confiável.
  2. Na agregação por tipo de motivo, tratar os valores nulos com a categoria explícita `Nao_Informado_Migracao`.
  3. Criar uma variável indicadora (flag binária) `teve_chamado_periodo_migracao`.
  4. Para o tempo de resolução, utilizar métricas agregadas condicionadas apenas aos registros com medição válida, atribuindo valor neutro (0) se o cliente não teve chamados medidos e sinalizando na flag correspondente.

---

## 3. Decisão
Adotou-se formalmente a **Alternativa C**.
A decisão garante que a informação comportamental de "esforço do cliente em buscar atendimento" não seja perdida, ao mesmo tempo em que a incerteza gerada pela migração de software seja tratada de forma explícita e transparente pelos algoritmos de Machine Learning.

---

## 4. Consequências e Riscos Residuais
- **Positivo:** Não há distorção sintética dos dados; o modelo aprende se o evento de migração causou fricção adicional.
- **Risco Residual:** Modelos lineares podem atribuir peso moderado à categoria `Nao_Informado_Migracao`.
- **Monitoramento:** Na Sprint 3, a importância dessa variável será auditada para assegurar que ela não atue como proxy espúria.
