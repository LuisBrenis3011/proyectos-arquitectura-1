import cv2
from deepface import DeepFace
import json
import uuid
import os
import sys
from conexion import obtener_conexion_moderna, obtener_conexion_legacy

print("--- ENROLAMIENTO BIOMETRICO ---")

if len(sys.argv) > 1:
    # Modo automatico: el Sistema Legacy ya valido al usuario antes de llamar este script
    usuario_id = sys.argv[1]
    print(f"ID {usuario_id} recibido desde el Sistema Legacy. Saltando validacion de credenciales.")

else:
    # Modo manual: el usuario ejecuta este script directamente
    usuario_id = input("Ingrese su ID de cliente Legacy: ")
    password = input("Ingrese su contrasena: ")

    conn_legacy = obtener_conexion_legacy()
    if not conn_legacy:
        print("Error: No se pudo conectar a la BD Legacy.")
        sys.exit(1)

    cursor_legacy = conn_legacy.cursor()
    cursor_legacy.execute(
        "SELECT ID_CLIENTE FROM CLIENTES_CORE WHERE ID_CLIENTE = %s AND PASSWORD_HASH = %s",
        (usuario_id, password)
    )
    cliente = cursor_legacy.fetchone()
    cursor_legacy.close()
    conn_legacy.close()

    if not cliente:
        print("Error: Credenciales incorrectas en el sistema antiguo.")
        sys.exit(1)

print(f"Usuario {usuario_id} listo. Iniciando camara para captura facial...")

# Capturar el rostro
captura = cv2.VideoCapture(0)
if not captura.isOpened():
    print("Error: No se pudo abrir la camara.")
    sys.exit(1)

print("Mire a la camara y presione 'c' para tomar la foto, o 'q' para cancelar.")

vector_facial = None

while True:
    exito, frame = captura.read()
    if not exito:
        print("Error: Fallo al leer el frame de la camara.")
        break

    cv2.imshow('Registro Facial - Presione C para capturar', frame)

    tecla = cv2.waitKey(1) & 0xFF

    if tecla == ord('c'):
        print("Foto capturada. Extrayendo biometria (puede tardar unos segundos)...")
        cv2.imwrite("temp_rostro.jpg", frame)

        try:
            resultado_ia = DeepFace.represent(
                img_path="temp_rostro.jpg",
                model_name="Facenet",
                enforce_detection=True
            )
            vector_facial = resultado_ia[0]["embedding"]
            print("Rostro procesado correctamente.")
            break
        except Exception as e:
            print(f"No se detecto un rostro claro ({e}). Intente de nuevo presionando 'c'.")

    elif tecla == ord('q'):
        print("Enrolamiento cancelado por el usuario.")
        break

captura.release()
cv2.destroyAllWindows()

if os.path.exists("temp_rostro.jpg"):
    os.remove("temp_rostro.jpg")

if not vector_facial:
    print("Error: No se capturo ningun vector facial. Proceso terminado.")
    sys.exit(1)

# Guardar en la Base de Datos Moderna
conn_moderna = obtener_conexion_moderna()
if not conn_moderna:
    print("Error: No se pudo conectar a la BD Moderna.")
    sys.exit(1)

try:
    cursor_moderna = conn_moderna.cursor()
    vector_json = json.dumps(vector_facial)
    id_biometrico = str(uuid.uuid4())

    sql = """
        INSERT INTO credenciales_faciales (id, legacy_cliente_id, vector_facial, activo)
        VALUES (%s, %s, %s, True)
    """
    cursor_moderna.execute(sql, (id_biometrico, usuario_id, vector_json))
    conn_moderna.commit()
    cursor_moderna.close()
    conn_moderna.close()

    print(f"EXITO. Rostro registrado para el usuario {usuario_id}.")
    sys.exit(0)

except Exception as e:
    print(f"Error al guardar en BD Moderna: {e}")
    conn_moderna.close()
    sys.exit(1)