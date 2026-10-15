# Conecta Brasil Telecom — Customer Churn Prediction & Retention Intelligence

[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-active%20sprint%201-success.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Code Style](https://img.shields.io/badge/code%20style-PEP8-black.svg)]()

> **Briefing Executivo Simulado de Ciência de Dados e Inteligência de Negócios**  
> **Cenário Corporativo:** Conecta Brasil Telecom (Operadora de Telecomunicações)  
> **Stack Principal:** Python (pandas, scikit-learn, numpy), SQL (SQLite/PostgreSQL), pytest, Git & GitHub  
> **Metodologia:** 4 Sprints Estruturadas com Validação Temporal e Gestão de Impacto Financeiro  

---

## 1. Visão Geral do Negócio e Impacto Financeiro

A **Conecta Brasil Telecom** possui uma base ativa estimada em **500 mil clientes** distribuídos em serviços de banda larga fixa via fibra ótica, telefonia móvel e serviços corporativos.

Historicamente, a retenção de clientes opera sob um modelo predominantemente **reativo**: o cliente insatisfeito só é abordado após protocolar uma solicitação formal de cancelamento.

### Indicadores Chave de Referência:
- **Base Ativa de Clientes:** 500.000 clientes
- **Taxa Média Mensal de Churn:** 2,8% (~14.000 cancelamentos/mês)
- **Receita Média Mensal por Cliente (ARPU):** R$ 120,00
- **Perda Mensal Bruta em Receita Recorrente:** **R$ 1.680.000,00**
- **Meta Estratégica (CTO):** Reduzir o churn de **2,8% para 2,5%** (-1.500 cancelamentos/mês, preservando até **R$ 180.000,00/mês** brutos).

### O Princípio Orientador:
> **Prever cancelamento não equivale a impedir cancelamento.**  
> Um modelo de churn só gera valor real se permitir que a Gerência de Retenção identifique **clientes com alto risco, alto valor e sensíveis a ações de retenção**, respeitando a capacidade operacional de discagem e gerando **ROI incremental positivo**.

---

## 2. Cronograma de Desenvolvimento (4 Sprints)

| Sprint | Foco Temático | Principais Entregas | Status |
| :---: | :--- | :--- | :---: |
| **01** | **Entendimento e Auditoria de Dados** | Requisitos, Dicionário de Dados, Relatório de Qualidade, Tratamento do Imprevisto 1 (Migração CRM). | **Concluído** |
| **02** | **EDA e Engenharia de Atributos** | Diagnóstico estatístico, revisão LGPD / Privacy by Design (Imprevisto 2), construção de ABT Point-in-Time. | *Em Execução* |
| **03** | **Modelagem e Otimização Comercial** | Benchmark, Regressão Logística, Random Forest, Gradient Boosting, Curva de Custo-Benefício (Imprevisto 3). | *Planejado* |
| **04** | **Produto Analítico e Governança** | Pipeline de inferência, testes automatizados (pytest), painel executivo e relatório final de ROI. | *Planejado* |

---

## 3. Arquitetura da Solução e Estrutura do Repositório

```text
projeto_churn/
├── data/
│   ├── raw/                 # Dados brutos das 6 fontes relacionais (.csv)
│   ├── processed/           # Conjuntos analíticos temporais (.parquet)
│   └── conecta_brasil.db    # Banco relacional SQLite para consultas analíticas
├── docs/
│   ├── business_requirements.md  # Requisitos formais de negócio e engenharia
│   ├── data_dictionary.md        # Dicionário de dados das 6 tabelas
│   ├── data_quality_report.md    # Relatório detalhado da auditoria de qualidade
│   ├── target_definition.md      # Definição matemática do churn e cortes temporais
│   └── adr/                      # Architecture Decision Records (Imprevistos)
│       └── 001_tratamento_migracao_sistema.md
├── notebooks/               # Análises exploratórias e prototipação
├── src/
│   ├── data/                # Ingestão e scripts de auditoria
│   ├── features/            # Engenharia de atributos point-in-time
│   ├── models/              # Treinamento, validação e explicabilidade
│   └── pipelines/           # Esteira de inferência produtiva
├── tests/                   # Testes automatizados com pytest
├── requirements.txt         # Dependências do projeto
├── .gitignore               # Proteção contra vazamento de dados e chaves
└── README.md                # Apresentação executiva
```

---

## 4. Gestão de Imprevistos do Mundo Real

1. **Imprevisto 1 (Migração de CRM - Sprint 1):** Diagnosticada falha na captura de motivos de chamados durante a migração entre março e maio de 2024. Resolvido via engenharia de atributos focada em volume de contatos e categorização explícita de incerteza (ver [ADR-001](file:///f:/Desktop/DESAFIO-HOJE/projeto_churn/docs/adr/001_tratamento_migracao_sistema.md)).
2. **Imprevisto 2 (Privacidade e LGPD - Sprint 2):** Implementação de *Privacy by Design* com pseudonimização criptográfica de IDs e expurgo de dados cadastrais sensíveis na camada de treinamento.
3. **Imprevisto 3 (Capacidade Operacional de Retenção - Sprint 3):** Calibração de probabilidade e priorização via Curva de Ganho Cumulativo (Top 10%) para garantir retorno econômico positivo.

---

## 5. Como Reproduzir o Projeto

### Pré-requisitos
- Python 3.10 ou superior
- Git

### Instalação e Execução
```bash
# 1. Clonar o repositório
git clone https://github.com/edusousa78/projeto_churn.git
cd projeto_churn

# 2. Criar e ativar o ambiente virtual (opcional)
python -m venv venv
# Windows: venv\Scripts\activate | Linux: source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Gerar dados sintéticos e inicializar banco relacional
python src/data/generate_simulated_data.py

# 5. Executar auditoria de qualidade dos dados
python src/data/audit_quality.py

# 6. Rodar os testes automatizados
pytest tests/
```
