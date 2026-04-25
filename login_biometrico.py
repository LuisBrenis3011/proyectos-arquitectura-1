import cv2
from deepface import DeepFace
import json
import numpy as np
import os
import sys
from conexion import obtener_conexion_moderna, obtener_conexion_legacy

def calcular_distancia_coseno(vec1, vec2):
    a = np.dot(vec1, vec2)
    b = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    if b == 0:
        return 1.0
    return 1 - (a / b)

if len(sys.argv) < 2:
    print("Error: se requiere el ID del cliente como argumento.")
    sys.exit(1)

id_cliente_objetivo = sys.argv[1]

print("--- INICIO DE SESION BIOMETRICO ---")
print(f"Verificando identidad para ID: {id_cliente_objetivo}")

captura = cv2.VideoCapture(0)
if not captura.isOpened():
    print("Error: No se pudo abrir la camara.")
    sys.exit(1)

print("Mire a la camara y presione 'c' para ingresar, o 'q' para cancelar.")

vector_en_vivo = None

while True:
    exito, frame = captura.read()
    if not exito:
        break

    cv2.imshow('Login Biometrico - Presione C para ingresar', frame)
    tecla = cv2.waitKey(1) & 0xFF

    if tecla == ord('c'):
        print("Analizando rostro...")
        cv2.imwrite("temp_login.jpg", frame)
        try:
            resultado_ia = DeepFace.represent(
                img_path="temp_login.jpg",
                model_name="Facenet",
                enforce_detection=True
            )
            vector_en_vivo = resultado_ia[0]["embedding"]
            print("Rostro capturado. Verificando contra el ID registrado...")
            break
        except Exception as e:
            print(f"No se detecto un rostro ({e}). Intente de nuevo.")

    elif tecla == ord('q'):
        print("Login cancelado.")
        break

captura.release()
cv2.destroyAllWindows()

if os.path.exists("temp_login.jpg"):
    os.remove("temp_login.jpg")

if not vector_en_vivo:
    print("ACCESO DENEGADO. No se capturo ningun rostro.")
    sys.exit(1)

# Buscar SOLO el vector del ID especifico, no todos
conn_moderna = obtener_conexion_moderna()
if not conn_moderna:
    print("Error: No se pudo conectar a la BD Moderna.")
    sys.exit(1)

cursor_moderna = conn_moderna.cursor()
cursor_moderna.execute(
    "SELECT vector_facial FROM credenciales_faciales WHERE legacy_cliente_id = %s AND activo = True",
    (id_cliente_objetivo,)
)
registro = cursor_moderna.fetchone()
cursor_moderna.close()
conn_moderna.close()

if not registro:
    print("ACCESO DENEGADO. No hay rostro registrado para este ID.")
    sys.exit(1)

vector_guardado = json.loads(registro[0])
distancia = calcular_distancia_coseno(vector_en_vivo, vector_guardado)
print(f"Distancia calculada: {distancia:.4f}")

UMBRAL_DISTANCIA = 0.7

if distancia < UMBRAL_DISTANCIA:
    print(f"Rostro verificado para ID: {id_cliente_objetivo}")
    print("Modificando ESTADO_SESIONES en la BD Legacy...")

    conn_legacy = obtener_conexion_legacy()
    if not conn_legacy:
        print("Error: No se pudo conectar a la BD Legacy.")
        sys.exit(1)

    try:
        cursor_legacy = conn_legacy.cursor()
        sql_update = "UPDATE ESTADO_SESIONES SET SESION_ACTIVA = True, METODO_ACCESO = 'BIOMETRICO' WHERE ID_CLIENTE = %s"
        cursor_legacy.execute(sql_update, (id_cliente_objetivo,))
        conn_legacy.commit()
        cursor_legacy.close()
        conn_legacy.close()
        print("ACCESO CONCEDIDO. El sistema Legacy ahora reconoce la sesion activa.")
        sys.exit(0)
    except Exception as e:
        print(f"Error al actualizar BD Legacy: {e}")
        conn_legacy.close()
        sys.exit(1)
else:
    print("ACCESO DENEGADO. Rostro no coincide con el ID proporcionado.")
    sys.exit(1)