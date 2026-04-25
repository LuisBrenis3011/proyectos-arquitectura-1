import customtkinter as ctk
import requests
import tkinter.messagebox as messagebox
from datetime import datetime

URL_ORQUESTADOR = "http://127.0.0.1:5000/api/biometria"
URL_CERRAR_SESION = "http://127.0.0.1:5000/api/cerrar_sesion"
URL_BUSCAR_DNI = "http://127.0.0.1:5000/api/buscar_por_dni"

INTERVALO_POLLING_MS = 3000

class KioscoBiometricoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Kiosco Biometrico Moderno")
        self.geometry("420x500")
        self.resizable(False, False)
        self.id_cliente_activo = None
        self.polling_sesion_activo = False
        self.mostrar_pantalla_principal()

    def limpiar_pantalla(self):
        for widget in self.winfo_children():
            widget.destroy()

    def mostrar_pantalla_principal(self):
        self.id_cliente_activo = None
        self.polling_sesion_activo = False
        self.limpiar_pantalla()

        ctk.CTkLabel(self, text="KIOSCO BIOMETRICO", font=("Arial", 20, "bold")).pack(pady=30)
        ctk.CTkLabel(
            self,
            text="Sistema de acceso por reconocimiento facial.\nSeparado del sistema bancario legacy.",
            font=("Arial", 11), text_color="gray"
        ).pack()

        ctk.CTkLabel(self, text="Ingrese su DNI:", font=("Arial", 12)).pack(pady=(30, 4))
        self.entry_dni = ctk.CTkEntry(self, placeholder_text="Ej: 76543210", width=280)
        self.entry_dni.pack(pady=4)

        ctk.CTkButton(
            self, text="Iniciar Acceso Biometrico", width=280,
            fg_color="#27ae60", hover_color="#1e8449",
            command=self.iniciar_biometria
        ).pack(pady=20)

        self.label_estado = ctk.CTkLabel(self, text="", font=("Arial", 11))
        self.label_estado.pack(pady=10)

    def iniciar_biometria(self):
        dni = self.entry_dni.get().strip()
        if not dni:
            messagebox.showwarning("Atencion", "Ingrese su DNI.")
            return

        self.label_estado.configure(text="Buscando cliente...", text_color="orange")
        self.update()

        # Paso 1: resolver DNI a ID interno via orquestador
        try:
            respuesta_dni = requests.post(
                URL_BUSCAR_DNI,
                json={"dni": dni},
                timeout=10
            )
            datos_dni = respuesta_dni.json()

            if not datos_dni.get("encontrado"):
                self.label_estado.configure(
                    text="DNI no encontrado en el sistema.",
                    text_color="#e74c3c"
                )
                return

            id_cliente = str(datos_dni.get("id_cliente"))

        except requests.exceptions.ConnectionError:
            messagebox.showerror("Error", "El Orquestador no esta activo.")
            return

        # Paso 2: iniciar proceso biometrico con el ID resuelto
        self.label_estado.configure(text="Abriendo camara, espere...", text_color="orange")
        self.update()

        try:
            respuesta = requests.post(
                URL_ORQUESTADOR,
                json={"id_cliente": id_cliente},
                timeout=180
            )
            datos = respuesta.json()

            if datos.get("acceso_concedido"):
                self.id_cliente_activo = id_cliente
                self.mostrar_pantalla_sesion_activa(dni, id_cliente)
            else:
                self.label_estado.configure(
                    text=datos.get("mensaje", "Sin respuesta del orquestador."),
                    text_color="#e67e22"
                )

        except requests.exceptions.ConnectionError:
            messagebox.showerror("Error", "El Orquestador no esta activo.")
        except requests.exceptions.Timeout:
            messagebox.showerror("Tiempo agotado", "El proceso biometrico tardo demasiado.")

    def mostrar_pantalla_sesion_activa(self, dni, id_cliente):
        self.limpiar_pantalla()
        hora_actual = datetime.now().strftime("%H:%M:%S")

        ctk.CTkLabel(self, text="KIOSCO BIOMETRICO", font=("Arial", 20, "bold")).pack(pady=20)

        frame_info = ctk.CTkFrame(self, corner_radius=10)
        frame_info.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(
            frame_info, text="ACCESO CONCEDIDO",
            font=("Arial", 16, "bold"), text_color="#27ae60"
        ).pack(pady=(14, 4))

        ctk.CTkLabel(frame_info, text=f"DNI: {dni}", font=("Arial", 12)).pack()
        ctk.CTkLabel(frame_info, text="Metodo: Reconocimiento Facial", font=("Arial", 12)).pack()
        ctk.CTkLabel(frame_info, text=f"Hora: {hora_actual}", font=("Arial", 12)).pack()

        ctk.CTkLabel(
            frame_info,
            text="El Sistema Legacy fue notificado automaticamente.",
            font=("Arial", 10), text_color="gray"
        ).pack(pady=(8, 14))

        ctk.CTkLabel(
            self,
            text="Cuando termine su operacion en el banco,\ncierre la sesion desde aqui.",
            font=("Arial", 11), text_color="gray"
        ).pack(pady=10)

        self.label_estado_sesion = ctk.CTkLabel(
            self, text="Sesion activa en Sistema Legacy...",
            font=("Arial", 10), text_color="#888888"
        )
        self.label_estado_sesion.pack(pady=4)

        ctk.CTkButton(
            self, text="Cerrar Sesion", width=280,
            fg_color="#c0392b", hover_color="#922b21",
            command=lambda: self.ejecutar_cierre_sesion(id_cliente)
        ).pack(pady=10)

        # Iniciar polling para detectar si el legacy se cierra externamente
        self.polling_sesion_activo = True
        self.ciclo_polling_sesion(id_cliente)

    def ciclo_polling_sesion(self, id_cliente):
        """Detecta si el Sistema Legacy cerro la sesion o la aplicacion."""
        if not self.polling_sesion_activo:
            return

        try:
            respuesta = requests.get(
                f"http://127.0.0.1:5000/api/estado_sesion/{id_cliente}",
                timeout=5
            )
            datos = respuesta.json()

            if not datos.get("sesion_activa"):
                self.polling_sesion_activo = False
                messagebox.showinfo(
                    "Sesion finalizada",
                    "El Sistema Legacy cerro la sesion o fue cerrado.\nVolviendo al inicio."
                )
                self.mostrar_pantalla_principal()
                return

        except Exception:
            pass

        self.after(INTERVALO_POLLING_MS, lambda: self.ciclo_polling_sesion(id_cliente))

    def ejecutar_cierre_sesion(self, id_cliente):
        self.polling_sesion_activo = False
        try:
            respuesta = requests.post(
                URL_CERRAR_SESION,
                json={"id_cliente": id_cliente},
                timeout=10
            )
            datos = respuesta.json()

            if datos.get("exito"):
                messagebox.showinfo(
                    "Sesion cerrada",
                    "La sesion fue cerrada correctamente.\nEl Sistema Legacy ha sido notificado."
                )
                self.mostrar_pantalla_principal()
            else:
                messagebox.showerror("Error", datos.get("mensaje", "No se pudo cerrar la sesion."))

        except requests.exceptions.ConnectionError:
            messagebox.showerror("Error", "No se pudo conectar al Orquestador.")

if __name__ == "__main__":
    app = KioscoBiometricoApp()
    app.mainloop()