import cv2
from deepface import DeepFace
import json
import numpy as np
import os
import sys
from conexion import obtener_conexion_moderna, obtener_conexion_legacy

def calcular_distancia_coseno(vec1, vec2):
    """Compara dos vectores faciales. Cuanto mas cercano a 0, mas similar es el rostro."""
    a = np.dot(vec1, vec2)
    b = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    if b == 0:
        return 1.0
    return 1 - (a / b)

print("--- INICIO DE SESION BIOMETRICO ---")
print("No necesitas usuario ni contrasena. Solo tu rostro.")

# Capturar el rostro en vivo
captura = cv2.VideoCapture(0)
if not captura.isOpened():
    print("Error: No se pudo abrir la camara.")
    sys.exit(1)

print("Mire a la camara y presione 'c' para ingresar, o 'q' para cancelar.")

vector_en_vivo = None

while True:
    exito, frame = captura.read()
    if not exito:
        print("Error: Fallo al leer el frame de la camara.")
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
            print("Rostro capturado. Buscando coincidencias...")
            break
        except Exception as e:
            print(f"No se detecto un rostro ({e}). Intente de nuevo.")

    elif tecla == ord('q'):
        print("Login cancelado por el usuario.")
        break

captura.release()
cv2.destroyAllWindows()

if os.path.exists("temp_login.jpg"):
    os.remove("temp_login.jpg")

if not vector_en_vivo:
    print("ACCESO DENEGADO. No se capturo ningun rostro.")
    sys.exit(1)

# Buscar coincidencia en la Base de Datos Moderna
conn_moderna = obtener_conexion_moderna()
if not conn_moderna:
    print("Error: No se pudo conectar a la BD Moderna.")
    sys.exit(1)

cursor_moderna = conn_moderna.cursor()
cursor_moderna.execute(
    "SELECT legacy_cliente_id, vector_facial FROM credenciales_faciales WHERE activo = True"
)
registros = cursor_moderna.fetchall()
cursor_moderna.close()
conn_moderna.close()

if not registros:
    print("ACCESO DENEGADO. No hay rostros registrados en el sistema.")
    sys.exit(1)

cliente_match_id = None
UMBRAL_DISTANCIA = 0.25

for registro in registros:
    id_legacy = registro[0]
    vector_guardado = json.loads(registro[1])
    distancia = calcular_distancia_coseno(vector_en_vivo, vector_guardado)
    print(f"Comparando con ID {id_legacy} - Distancia: {distancia:.4f}")

    if distancia < UMBRAL_DISTANCIA:
        cliente_match_id = id_legacy
        break

# Inyeccion de estado en la BD Legacy
if cliente_match_id:
    print(f"Rostro reconocido. Corresponde al ID Legacy: {cliente_match_id}")
    print("Modificando ESTADO_SESIONES en la BD Legacy...")

    conn_legacy = obtener_conexion_legacy()
    if not conn_legacy:
        print("Error: No se pudo conectar a la BD Legacy para actualizar sesion.")
        sys.exit(1)

    try:
        cursor_legacy = conn_legacy.cursor()
        sql_update = "UPDATE ESTADO_SESIONES SET SESION_ACTIVA = True WHERE ID_CLIENTE = %s"
        cursor_legacy.execute(sql_update, (cliente_match_id,))
        conn_legacy.commit()
        cursor_legacy.close()
        conn_legacy.close()

        print("ACCESO CONCEDIDO. El sistema Legacy ahora reconoce la sesion activa.")
        sys.exit(0)

    except Exception as e:
        print(f"Error al actualizar la BD Legacy: {e}")
        conn_legacy.close()
        sys.exit(1)

else:
    print("ACCESO DENEGADO. Rostro no reconocido en el sistema.")
    sys.exit(1)