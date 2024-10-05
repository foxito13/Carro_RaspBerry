#Código del transmisor (El joystick envía datos)

import wifi
import socketpool
import analogio
import digitalio
import time
import board

# Configuración Wi-Fi
SSID = "Julian"  # Reemplaza con tu SSID
PASSWORD = "12345678"  # Reemplaza con tu contraseña

# Configuración del servidor receptor
HOST = "192.168.252.223"  # IP del receptor
PORT = 5000  # Debe coincidir con el puerto usado por el receptor

# Conectar a la red Wi-Fi
wifi.radio.connect(SSID, PASSWORD)
print(f"Conectado a {SSID} con la dirección IP: {wifi.radio.ipv4_address}")

# Inicializar el socket para enviar datos
pool = socketpool.SocketPool(wifi.radio)
sock = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
sock.connect((HOST, PORT))
print(f"Conectado al servidor en {HOST}:{PORT}")

# Inicializar entradas analógicas del joystick
x_axis = analogio.AnalogIn(board.A0)  # Eje X
y_axis = analogio.AnalogIn(board.A1)  # Eje Y

# Inicializar el botón del joystick
button = digitalio.DigitalInOut(board.GP22)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP  # Con resistencia pull-up interna

def get_voltage(pin):
    # Convertir lectura analógica a voltaje (0-3.3V)
    return (pin.value * 3.3) / 65536

while True:
    # Leer los valores del joystick
    x_value = get_voltage(x_axis)
    y_value = get_voltage(y_axis)
    
    # Leer el estado del botón (True = no presionado, False = presionado)
    button_state = not button.value
    
    # Crear una cadena con los datos a enviar
    data = f"{x_value:.2f},{y_value:.2f},{button_state}\n"
    
    # Enviar los datos al receptor
    try:
        sock.send(data.encode('utf-8'))
    except Exception as e:
        print(f"Error enviando datos: {e}")
    
    # Esperar un segundo antes de la siguiente lectura
    time.sleep(0.5)
