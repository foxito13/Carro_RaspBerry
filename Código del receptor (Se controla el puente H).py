#Código del receptor (Se controla el puente H)

import wifi
import socketpool
import pwmio
from digitalio import DigitalInOut, Direction
import board
import time

# Configuración de Wi-Fi
SSID = "Julian"  # Reemplaza con tu SSID
PASSWORD = "12345678"  # Reemplaza con tu contraseña

# Configuración del servidor receptor
PORT = 5000  # Puerto para escuchar la conexión del transmisor

# Conectar a la red Wi-Fi
wifi.radio.connect(SSID, PASSWORD)
print(f"Conectado a {SSID} con la dirección IP: {wifi.radio.ipv4_address}")

# Inicializar el socket para recibir los datos del transmisor
pool = socketpool.SocketPool(wifi.radio)
server_socket = pool.socket(pool.AF_INET, pool.SOCK_STREAM)

# Asociar el socket a la dirección IP y al puerto
server_socket.bind((str(wifi.radio.ipv4_address), PORT))
server_socket.listen(1)
print(f"Servidor escuchando en {wifi.radio.ipv4_address}:{PORT}")

# Esperar una conexión del transmisor
client_socket, client_address = server_socket.accept()
print(f"Conexión establecida desde {client_address}")

# Configurar los pines de control del puente H para el motor A
in1 = DigitalInOut(board.GP10)  # Pin IN1 (Motor A forward)
in2 = DigitalInOut(board.GP11)  # Pin IN2 (Motor A reverse)
in1.direction = Direction.OUTPUT
in2.direction = Direction.OUTPUT

# Configurar los pines de control del puente H para el motor B
in3 = DigitalInOut(board.GP12)  # Pin IN3 (Motor B forward)
in4 = DigitalInOut(board.GP13)  # Pin IN4 (Motor B reverse)
in3.direction = Direction.OUTPUT
in4.direction = Direction.OUTPUT

# Configurar PWM para el control de la velocidad del motor A y B
pwm_motor_a = pwmio.PWMOut(board.GP14, frequency=1000)  # PWM en GP14 para motor A
pwm_motor_b = pwmio.PWMOut(board.GP15, frequency=1000)  # PWM en GP15 para motor B

# Variable para el estado de los motores (encendido o apagado)
motors_on = True
last_button_state = False  # Estado anterior del botón

# Función para controlar la dirección del motor A
def motor_a_direction(forward):
    in1.value = forward
    in2.value = not forward

# Función para controlar la dirección del motor B
def motor_b_direction(forward):
    in3.value = forward
    in4.value = not forward

# Función para establecer la velocidad del motor A
def motor_a_speed(speed_percent):
    duty_cycle = int((speed_percent / 100) * 65535)
    pwm_motor_a.duty_cycle = duty_cycle

# Función para establecer la velocidad del motor B
def motor_b_speed(speed_percent):
    duty_cycle = int((speed_percent / 100) * 65535)
    pwm_motor_b.duty_cycle = duty_cycle

# Función para detener ambos motores
def stop_motors():
    pwm_motor_a.duty_cycle = 0
    pwm_motor_b.duty_cycle = 0

# Función para encender/apagar los motores
def toggle_motors():
    global motors_on
    motors_on = not motors_on
    if not motors_on:
        stop_motors()

try:
    while True:
        # Recibir los datos del transmisor
        buffer = bytearray(1024)
        bytes_received = client_socket.recv_into(buffer)
        received_data = buffer[:bytes_received].decode('utf-8').strip()

        if received_data:
            try:
                # Verificar que haya exactamente 3 valores separados por comas
                parts = received_data.split(',')
                if len(parts) == 3:
                    x_value, y_value, button_state = parts
                    x_value = float(x_value)
                    y_value = float(y_value)
                    button_state = button_state == "True"  # Convertir a booleano
                else:
                    raise ValueError("Se recibieron datos mal formados")
                
                # Convertir los valores del joystick a un rango -100 a 100
                x_percentage = (x_value - 1.65) * 100 / 1.65
                y_percentage = (y_value - 1.65) * 100 / 1.65

                # Detectar si el botón fue presionado (transición de no presionado a presionado)
                if not last_button_state and button_state:
                    toggle_motors()  # Cambiar el estado de los motores

                # Actualizar el estado anterior del botón
                last_button_state = button_state

                # Si los motores están encendidos, controlar la dirección y velocidad
                if motors_on:
                    # Lógica para controlar los motores con base en los ejes X y Y
                    if y_percentage < -5 and -5 < x_percentage < 5:  # Adelante
                        motor_a_direction(True)
                        motor_b_direction(True)
                        motor_a_speed(abs(y_percentage))
                        motor_b_speed(abs(y_percentage))

                    elif y_percentage > 5 and -5 < x_percentage < 5:  # Atrás
                        motor_a_direction(False)
                        motor_b_direction(False)
                        motor_a_speed(abs(y_percentage))
                        motor_b_speed(abs(y_percentage))

                    elif x_percentage > 5 and -5 < y_percentage < 5:  # Girar a la derecha
                        motor_a_direction(False)
                        motor_b_direction(True)
                        motor_a_speed(abs(x_percentage))
                        motor_b_speed(abs(x_percentage))

                    elif x_percentage < -5 and -5 < y_percentage < 5:  # Girar a la izquierda
                        motor_a_direction(True)
                        motor_b_direction(False)
                        motor_a_speed(abs(x_percentage))
                        motor_b_speed(abs(x_percentage))

                    else:  # Detener los motores si el joystick está centrado
                        stop_motors()

            except ValueError as e:
                print(f"Error procesando los datos: {e}")

        time.sleep(0.1)

finally:
    # Cerrar los sockets cuando termine el bucle
    client_socket.close()
    server_socket.close()
