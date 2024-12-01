import RPi.GPIO as GPIO
import time
import socket

# Motor control pins for left and right motors
leftMotorA = 17
leftMotorB = 18
leftMotorE = 22
rightMotorA = 23
rightMotorB = 24
rightMotorE = 25

# Setup GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup motor pins
motor_pins = [leftMotorA, leftMotorB, leftMotorE, rightMotorA, rightMotorB, rightMotorE]
for pin in motor_pins:
    GPIO.setup(pin, GPIO.OUT)

# Ultrasonic sensor pins remain the same
trig = 26
echo = 27
GPIO.setup(trig, GPIO.OUT)
GPIO.setup(echo, GPIO.IN)

def move_forward(duration):
    # Set both motors to move forward
    GPIO.output([leftMotorA, rightMotorA], GPIO.HIGH)
    GPIO.output([leftMotorB, rightMotorB], GPIO.LOW)
    GPIO.output([leftMotorE, rightMotorE], GPIO.HIGH)
    time.sleep(duration)
    GPIO.output([leftMotorE, rightMotorE], GPIO.LOW)

def turn(direction, duration):
    # Turn left or right
    if direction == "left":
        GPIO.output([leftMotorA, rightMotorB], GPIO.LOW)
        GPIO.output([leftMotorB, rightMotorA], GPIO.HIGH)
    else: # right
        GPIO.output([leftMotorB, rightMotorA], GPIO.LOW)
        GPIO.output([leftMotorA, rightMotorB], GPIO.HIGH)
    GPIO.output([leftMotorE, rightMotorE], GPIO.HIGH)
    time.sleep(duration)
    GPIO.output([leftMotorE, rightMotorE], GPIO.LOW)

def setup_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '0.0.0.0'
    port = 12345
    server_socket.bind((host, port))
    server_socket.listen(1)
    print(f"Listening on port {port}...")
    return server_socket

def handle_client(client_socket):
    while True:
        # Receiving the command from the client
        command = client_socket.recv(1024).decode('utf-8')
        print("Received command:", command)
        if command == 'forward':
            move_forward(2)
        elif command == 'left':
            turn('left', 1)
        elif command == 'right':
            turn('right', 1)
        elif command == 'stop':
            # Stops the robot
            GPIO.output([leftMotorE, rightMotorE], GPIO.LOW)
        elif command == 'quit':
            break

def main():
    server_socket = setup_server()
    client_socket, addr = server_socket.accept()
    print("Connection from:", addr)
    handle_client(client_socket)
    client_socket.close()
    server_socket.close()
    GPIO.cleanup()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
