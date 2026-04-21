import cv2

print("Iniciando cámara... (Puede tardar un par de segundos)")

captura = cv2.VideoCapture(0)

if not captura.isOpened():
    print("Error: No se pudo acceder a la cámara.")
    exit()

print("Cámara encendida. ¡Sonríe! (Presiona la tecla 'q' para apagarla)")

while True:
    exito, frame = captura.read()
    
    if not exito:
        print("Error al leer la imagen de la cámara")
        break

    cv2.imshow('Modulo Biometrico - Prueba', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

captura.release()
cv2.destroyAllWindows()
print("Cámara apagada correctamente.")