import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool

# ==========================================================
# CONFIGURAÇÃO BANCO SUPABASE
# ==========================================================

DB_URI = os.getenv("DATABASE_URL")

if not DB_URI:
    raise Exception("DATABASE_URL não configurada!")

# ==========================================================
# POOL DE CONEXÕES
# ==========================================================

pool = SimpleConnectionPool(1, 10, DB_URI)

def conectar():
    return pool.getconn()

def devolver_conexao(conn):
    pool.putconn(conn)

# ==========================================================
# CRIAÇÃO DA TABELA
# ==========================================================

def criar_banco():
    conn = conectar()
    try:
        with conn.cursor() as cursor:
            # Removido UNIQUE da coluna whatsapp
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                whatsapp VARCHAR(20) NOT NULL,
                cidade VARCHAR(100) NOT NULL,
                marca VARCHAR(50) NOT NULL,
                modelo VARCHAR(50) NOT NULL,
                ano VARCHAR(10) NOT NULL,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Caso a tabela já existisse com a restrição UNIQUE antiga no whatsapp, removemos se existir
            cursor.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'clientes_whatsapp_key'
                ) THEN
                    ALTER TABLE clientes DROP CONSTRAINT clientes_whatsapp_key;
                END IF;
            END $$;
            """)

            # NOVO ÍNDICE ÚNICO COMPOSTO: Garante que só haverá bloqueio se for o mesmo Telefone + Marca + Modelo + Ano
            cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_cliente_caminhao_unico 
            ON clientes(whatsapp, marca, modelo, ano);
            """)

            # Índices de performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_whatsapp ON clientes(whatsapp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_marca ON clientes(marca);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_modelo ON clientes(modelo);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ano ON clientes(ano);")

        conn.commit()
    except Exception as e:
        print(f"❌ Erro ao criar/atualizar banco: {e}")
    finally:
        devolver_conexao(conn)

# ==========================================================
# VERIFICAR DUPLICIDADE EXATA (Telefone + Caminhão)
# ==========================================================

def cliente_existe(whatsapp, marca, modelo, ano):
    conn = conectar()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 
                FROM clientes
                WHERE whatsapp = %s 
                  AND marca = %s 
                  AND modelo = %s 
                  AND ano = %s
                """,
                (whatsapp, marca, modelo, ano)
            )
            return cursor.fetchone() is not None
    except Exception as e:
        print(f"❌ Erro ao verificar cliente: {e}")
        return False
    finally:
        devolver_conexao(conn)

# ==========================================================
# SALVAR CLIENTE
# ==========================================================

def salvar_cliente(nome, whatsapp, cidade, marca, modelo, ano):
    conn = conectar()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO clientes (nome, whatsapp, cidade, marca, modelo, ano)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (nome, whatsapp, cidade, marca, modelo, ano)
            )
        conn.commit()
    except Exception as e:
        print(f"❌ Erro ao salvar cliente: {e}")
        raise e
    finally:
        devolver_conexao(conn)

# ==========================================================
# EXCLUIR CLIENTE
# ==========================================================

def excluir_cliente(id_cliente):
    conn = conectar()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM clientes WHERE id=%s", (id_cliente,))
        conn.commit()
    finally:
        devolver_conexao(conn)

# Inicializa/atualiza estrutura do banco
criar_banco()