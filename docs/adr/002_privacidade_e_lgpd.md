# ADR-002: Governança de Dados, Privacidade e Conformidade com a LGPD
**Status:** Aprovado  
**Data:** Outubro de 2026  
**Contexto do Desafio:** Imprevisto 2 (Sprint 2)  
**Autor:** Cientista de Dados Júnior  
**Intervenientes:** Encarregado de Proteção de Dados (DPO) & Compliance Corporativo  

---

## 1. Contexto do Problema
Durante a homologação da esteira de dados para a modelagem preditiva, a equipe de *Compliance* e Privacidade identificou a presença de Dados Pessoais Identificáveis (PII - *Personally Identifiable Information*) na tabela cadastral de clientes:
- `nome_cliente` (Nome completo)
- `cpf` (Cadastro de Pessoa Física)
- `email` (Endereço eletrônico)

A empresa exigiu a implementação imediata de salvaguardas de **Privacy by Design**, garantindo o cumprimento estrito da Lei Geral de Proteção de Dados (Lei nº 13.709/2018 - LGPD), em especial os princípios de:
- **Finalidade:** O tratamento destina-se exclusivamente à identificação antecipada de churn para fins legítimos de retenção de clientes.
- **Adequação e Necessidade (Minimização de Dados):** Nenhum dado pessoal direto (nome, CPF, e-mail) é preditor de churn. Sua utilização em modelos de Machine Learning é desnecessária e ilegal.
- **Segurança e Prevenção:** Garantir que identificadores não sejam expostos em logs, repositórios de código ou relatórios de experimentos.

---

## 2. Decisões Arquiteturais Implementadas

### 2.1 Minimização e Expurgo de PII
- As colunas `nome_cliente`, `cpf` e `email` foram **eliminadas sumariamente** da camada analítica (ABT - *Analytical Base Table*).
- Elas nunca serão lidas pelos scripts de treinamento (`src/models/`) nem farão parte de transformações estatísticas.

### 2.2 Pseudonimização Irreversível de Identificadores
- Para garantir que a lista de clientes ranqueada possa ser operacionalizada pela Gerência de Retenção sem expor chaves de banco de dados diretamente nos artefatos analíticos:
  - Adotou-se o algoritmo criptográfico **HMAC-SHA256** com semente/salt secreto corporativo para gerar a chave pseudonimizada:
  
  $$\text{id\_cliente\_hash} = \text{SHA256}(\text{id\_cliente} + \text{SECRET\_SALT})[:16]$$
  
  - A tabela de conversão (*de-para*) permanece restrita à infraestrutura segura do banco de dados relacional e não é versionada no Git.

### 2.3 Avaliação de Variáveis Demográficas e Prevenção de Viés (Fairness)
- Avaliou-se o papel de `genero` e `faixa_etaria`.
- A variável `genero` foi desconsiderada como preditor na modelagem final para evitar discriminação algorítmica ou viés demográfico irrelevante para a prestação do serviço técnico de telecomunicações.
- As variáveis de maior relevância são estritamente operacionais, contratuais e comportamentais (qualidade da rede, atrasos em pagamento, tipo de plano e suporte).

---

## 3. Consequências
- **Conformidade Legal:** Repositório, artefatos e notebooks 100% seguros contra vazamento de dados pessoais.
- **Reprodutibilidade:** Ambientes de teste e portfólio utilizam dados completamente pseudonimizados.
- **Risco Mitigado:** Exposição zero de titulares de dados perante órgãos reguladores (ANPD).
