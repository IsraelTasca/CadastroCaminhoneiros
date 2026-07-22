import sqlite3


def salvar_cliente(nome, whatsapp, cidade, marca, modelo, ano):

    conn = sqlite3.connect("clientes.db")

    cursor = conn.cursor()

    cursor.execute("""

        INSERT INTO clientes
        (nome, whatsapp, cidade, marca, modelo, ano)

        VALUES (?,?,?,?,?,?)

    """,(

        nome,
        whatsapp,
        cidade,
        marca,
        modelo,
        ano

    ))

    conn.commit()

    conn.close()