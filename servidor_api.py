from conexion import obtener_conexion_moderna, obtener_conexion_legacy
from flask import Flask, request, jsonify
import subprocess
import sys 
from conexion import obtener_conexion_moderna

app = Flask(__name__)

@app.route('/api/biometria', methods=['POST'])
def procesar_biometria():
    datos_recibidos = request.json
    id_legacy = str(datos_recibidos.get('id_cliente'))

    print("="*40)
    print(f"PETICION RECIBIDA PARA ID: {id_legacy}")

    try:
        conn = obtener_conexion_moderna()
        if not conn:
            return jsonify({"acceso_concedido": False, "mensaje": "Error al conectar a la BD Moderna."})

        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM credenciales_faciales WHERE legacy_cliente_id = %s AND activo = True",
            (id_legacy,)
        )
        existe_rostro = cursor.fetchone()
        cursor.close()
        conn.close()

    except Exception as e:
        return jsonify({"acceso_concedido": False, "mensaje": f"Error interno: {e}"})

    if existe_rostro:
        print("Rostro encontrado en BD. Iniciando LOGIN biometrico...")
        resultado = subprocess.run(
        [sys.executable, 'login_biometrico.py', id_legacy],
        capture_output=False)
        if resultado.returncode == 0:
            return jsonify({"acceso_concedido": True, "mensaje": "Rostro verificado. Acceso concedido."})
        else:
            return jsonify({"acceso_concedido": False, "mensaje": "Rostro no coincide o proceso cancelado."})

    else:
        print("Rostro NO encontrado. Iniciando ENROLAMIENTO...")
        resultado = subprocess.run([sys.executable, 'enrolamiento.py', id_legacy], capture_output=False)  # <-- sys.executable

        if resultado.returncode == 0:
            return jsonify({"acceso_concedido": False, "mensaje": "Registro facial exitoso. Vuelve a presionar el boton para iniciar sesion."})
        else:
            return jsonify({"acceso_concedido": False, "mensaje": "El enrolamiento fue cancelado o fallo. Intente de nuevo."})


@app.route('/api/cerrar_sesion', methods=['POST'])
def cerrar_sesion():
    datos = request.json
    id_legacy = str(datos.get('id_cliente'))

    print("="*40)
    print(f"CIERRE DE SESION SOLICITADO PARA ID: {id_legacy}")

    try:
        conn = obtener_conexion_legacy()
        if not conn:
            return jsonify({"exito": False, "mensaje": "Error al conectar a la BD Legacy."})

        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ESTADO_SESIONES SET SESION_ACTIVA = False, METODO_ACCESO = 'NINGUNO' WHERE ID_CLIENTE = %s",
            (id_legacy,)
        )
        conn.commit()
        cursor.close()
        conn.close()

        print(f"Sesion cerrada correctamente para ID: {id_legacy}")
        return jsonify({"exito": True, "mensaje": "Sesion cerrada correctamente."})

    except Exception as e:
        return jsonify({"exito": False, "mensaje": f"Error: {e}"})


@app.route('/api/buscar_por_dni', methods=['POST'])
def buscar_por_dni():
    datos = request.json
    dni = datos.get('dni')

    try:
        conn = obtener_conexion_legacy()
        if not conn:
            return jsonify({"encontrado": False, "mensaje": "Error al conectar a BD Legacy."})

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT ID_CLIENTE FROM CLIENTES_CORE WHERE DNI_RUT = %s", (dni,))
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()

        if resultado:
            return jsonify({"encontrado": True, "id_cliente": resultado['ID_CLIENTE']})
        else:
            return jsonify({"encontrado": False})

    except Exception as e:
        return jsonify({"encontrado": False, "mensaje": str(e)})


@app.route('/api/estado_sesion/<id_cliente>', methods=['GET'])
def estado_sesion(id_cliente):
    try:
        conn = obtener_conexion_legacy()
        if not conn:
            return jsonify({"sesion_activa": False})

        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT SESION_ACTIVA FROM ESTADO_SESIONES WHERE ID_CLIENTE = %s",
            (id_cliente,)
        )
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()

        if resultado:
            return jsonify({"sesion_activa": bool(resultado['SESION_ACTIVA'])})
        return jsonify({"sesion_activa": False})

    except Exception as e:
        return jsonify({"sesion_activa": False})


if __name__ == '__main__':
    print("Microservicio Biometrico activo en puerto 5000...")
    app.run(host='127.0.0.1', port=5000)