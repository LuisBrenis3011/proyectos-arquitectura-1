import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

def obtener_conexion_moderna():
    """Establece y retorna la conexión a la Base de Datos Nueva"""
    try:
        conexion = mysql.connector.connect(
            host=os.getenv("DB_MODERNA_HOST"),
            user=os.getenv("DB_MODERNA_USER"),
            password=os.getenv("DB_MODERNA_PASSWORD"),
            database=os.getenv("DB_MODERNA_NAME")
        )
        if conexion.is_connected():
            print(" Conexión exitosa a la BD Nueva")
            return conexion
            
    except Error as e:
        print(f" Error al conectar a MySQL: {e}")
        return None
    
    
def obtener_conexion_legacy():
    """Establece y retorna la conexión a la Base de Datos Antigua (Caja Negra)"""
    try:
        conexion = mysql.connector.connect(
            host=os.getenv("DB_LEGACY_HOST"),
            user=os.getenv("DB_LEGACY_USER"),
            password=os.getenv("DB_LEGACY_PASSWORD"),
            database=os.getenv("DB_LEGACY_NAME")
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"Error al conectar a Legacy MySQL: {e}")
        return None

if __name__ == '__main__':
    print("Intentando conectar a la base de datos...")
    conn = obtener_conexion_moderna()
    if conn:
        conn.close()
        print("Conexión cerrada correctamente. ¡Todo listo!")