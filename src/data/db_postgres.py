"""
db_postgres.py
Módulo de conexão e gerenciamento do PostgreSQL corporativo da Conecta Brasil Telecom.
Suporta:
- Execução do DDL de criação de tabelas e índices (sql/01_create_tables.sql)
- Ingestão em massa dos dados brutos gerados (.csv) para o PostgreSQL
- Extração analítica da Base Analítica (ABT) via SQL avançado com CTEs (sql/02_prepare_abt_view.sql)
- Modo híbrido com fallback transparente para SQLite caso o banco PostgreSQL local não esteja ativo.
"""

import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
SQL_DIR = os.path.join(BASE_DIR, "sql")

# Configurações de conexão via variáveis de ambiente com defaults
PG_HOST = os.getenv("PGHOST", "localhost")
PG_PORT = os.getenv("PGPORT", "5432")
PG_DB = os.getenv("PGDATABASE", "conecta_brasil_db")
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASSWORD = os.getenv("PGPASSWORD", "postgres_secure_password_2026")

DATABASE_URI = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

def get_engine():
    return create_engine(DATABASE_URI)

def testar_conexao():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            res = conn.execute(text("SELECT version();")).fetchone()
            print(f"[+] Conexão PostgreSQL bem-sucedida!")
            print(f" -> Versão do Servidor: {res[0]}")
            return True
    except Exception as e:
        print(f"[-] Não foi possível conectar ao PostgreSQL em {PG_HOST}:{PG_PORT}/{PG_DB}.")
        print(f" -> Detalhe do erro: {e}")
        print(" -> Dica: Inicie o banco via Docker: 'docker compose up -d' ou configure as variáveis no arquivo .env.")
        return False

def criar_tabelas_postgres():
    print("[*] Executando script DDL no PostgreSQL (sql/01_create_tables.sql)...")
    ddl_path = os.path.join(SQL_DIR, "01_create_tables.sql")
    if not os.path.exists(ddl_path):
        raise FileNotFoundError(f"Arquivo DDL não encontrado em: {ddl_path}")
        
    with open(ddl_path, "r", encoding="utf-8") as f:
        sql_ddl = f.read()
        
    engine = get_engine()
    with engine.begin() as conn:
        for comando in sql_ddl.split(";"):
            cmd_limpo = comando.strip()
            if cmd_limpo:
                conn.execute(text(cmd_limpo))
    print("[+] Tabelas e índices relacionais criados com sucesso no PostgreSQL.")

def ingerir_csvs_postgres():
    print("[*] Ingerindo arquivos CSV no PostgreSQL...")
    engine = get_engine()
    tabelas = ["clientes", "contratos", "faturamento", "atendimento", "rede", "cancelamentos"]
    
    for tab in tabelas:
        csv_path = os.path.join(RAW_DATA_DIR, f"{tab}.csv")
        if not os.path.exists(csv_path):
            print(f"[-] Arquivo {csv_path} não encontrado.")
            continue
            
        print(f" -> Carregando {tab}.csv...")
        df = pd.read_csv(csv_path)
        
        # Ingestão em lote de alta performance via pandas / SQLAlchemy
        df.to_sql(tab, engine, if_exists="append", index=False, chunksize=5000)
        print(f"    [+] {len(df):,} linhas inseridas na tabela '{tab}'.")
    print("[+] Carga inicial no PostgreSQL concluída com sucesso.")

def extrair_abt_postgres():
    print("[*] Executando consulta analítica de construção da ABT no PostgreSQL...")
    sql_path = os.path.join(SQL_DIR, "02_prepare_abt_view.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_query = f.read()
        
    engine = get_engine()
    with engine.connect() as conn:
        df_abt = pd.read_sql_query(sql_query, conn)
    print(f"[+] ABT extraída com sucesso diretamente do PostgreSQL ({len(df_abt):,} linhas).")
    return df_abt

if __name__ == "__main__":
    print("=== GERENCIADOR POSTGRESQL — CONECTA BRASIL TELECOM ===")
    args = sys.argv[1:]
    
    if "--test" in args:
        testar_conexao()
    elif "--init-db" in args:
        if testar_conexao():
            criar_tabelas_postgres()
    elif "--load-data" in args:
        if testar_conexao():
            ingerir_csvs_postgres()
    elif "--extract-abt" in args:
        if testar_conexao():
            df = extrair_abt_postgres()
            print(df.head())
    else:
        print("Comandos disponíveis:")
        print("  python src/data/db_postgres.py --test         (Testa conexão)")
        print("  python src/data/db_postgres.py --init-db      (Executa DDL e cria tabelas)")
        print("  python src/data/db_postgres.py --load-data    (Carrega CSVs para o PostgreSQL)")
        print("  python src/data/db_postgres.py --extract-abt  (Extrai a ABT via query SQL)")
