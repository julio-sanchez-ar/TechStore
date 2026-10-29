import mysql.connector
from config import DB_CONFIG


def conectar():
    """Abre una conexión nueva a la base de datos techstore."""
    return mysql.connector.connect(**DB_CONFIG)


def consultar(sql, params=(), uno=False):
    """Ejecuta un SELECT y devuelve las filas como diccionarios."""
    db = conectar()
    try:
        cur = db.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchone() if uno else cur.fetchall()
    finally:
        db.close()


def ejecutar(sql, params=()):
    """Ejecuta un INSERT, UPDATE o DELETE y guarda los cambios."""
    db = conectar()
    try:
        cur = db.cursor()
        cur.execute(sql, params)
        db.commit()
        return cur.lastrowid
    finally:
        db.close()