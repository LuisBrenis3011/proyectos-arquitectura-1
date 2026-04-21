from flask import Flask, request, jsonify
import subprocess
import sys  # <-- agregar esto
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
        resultado = subprocess.run([sys.executable, 'login_biometrico.py'], capture_output=False)  # <-- sys.executable

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

if __name__ == '__main__':
    print("Microservicio Biometrico activo en puerto 5000...")
    app.run(host='127.0.0.1', port=5000)