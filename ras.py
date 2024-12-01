import RPi.GPIO as GPIO
import time
import socket
import random
import threading

# Motor GPIO Pins
leftMotorA = 17
leftMotorB = 18
leftMotorE = 22
rightMotorA = 23
rightMotorB = 24
rightMotorE = 25

# Ultrasonic Sensor GPIO Pins
frontTrig = 26
frontEcho = 27
# Assuming additional side sensors for improved decision-making
leftTrig = 5
leftEcho = 6
rightTrig = 13
rightEcho = 19

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup motor and sensor pins
motor_pins = [leftMotorA, leftMotorB, leftMotorE, rightMotorA, rightMotorB, rightMotorE]
sensor_pins = [frontTrig, frontEcho, leftTrig, leftEcho, rightTrig, rightEcho]
for pin in motor_pins + sensor_pins:
    GPIO.setup(pin, GPIO.OUT if pin in [leftMotorE, rightMotorE, frontTrig, leftTrig, rightTrig] else GPIO.IN)

def motor_control(left_speed, right_speed, duration):
    """Control motors for movement. Speed range is -1 (full reverse) to 1 (full forward)."""
    GPIO.output([leftMotorA, rightMotorA], GPIO.HIGH if left_speed > 0 else GPIO.LOW)
    GPIO.output([leftMotorB, rightMotorB], GPIO.LOW if left_speed > 0 else GPIO.HIGH)
    GPIO.output([leftMotorE, rightMotorE], GPIO.HIGH)  # Enable motors
    # I can Adjust PWM to control speed
    time.sleep(100)
    GPIO.output([leftMotorE, rightMotorE], GPIO.LOW)  # Stop motors

def get_distance(trig, echo):
    """Measure distance using ultrasonic sensor."""
    GPIO.output(trig, False)
    time.sleep(0.1)
    GPIO.output(trig, True)
    time.sleep(0.00001)
    GPIO.output(trig, False)
    while GPIO.input(echo) == 0:
        pulse_start = time.time()
    while GPIO.input(echo) == 1:
        pulse_end = time.time()
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    return distance

def autonomous_navigation():
    """Autonomous navigation logic with obstacle avoidance."""
    try:
        while True:
            front_distance = get_distance(frontTrig, frontEcho)
            if front_distance < 20:
                # Obstacle detected in front, decide direction
                left_distance = get_distance(leftTrig, leftEcho)
                right_distance = get_distance(rightTrig, rightEcho)
                if left_distance > right_distance:
                    print("Turning left")
                    motor_control(-0.5, 0.5, 1)  # Turn left
                else:
                    print("Turning right")
                    motor_control(0.5, -0.5, 1)  # Turn right
            else:
                print("Moving forward")
                motor_control(1, 1, 2)  # Move forward
    except KeyboardInterrupt:
        GPIO.cleanup()

def setup_server():
    """Setup TCP server for manual control."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = '0.0.0.0'
    port = 12345
    server_socket.bind((host, port))
    server_socket.listen(1)
    print("COM3", port)
    return server_socket

def manual_control(client_socket):
    """Handle manual control commands from a client."""
    try:
        while True:
            command = client_socket.recv(1024).decode('utf-8')
            if command == 'forward':
                motor_control(1, 1, 2)
            elif command == 'left':
                motor_control(-0.5, 0.5, 1)
            elif command == 'right':
                motor_control(0.5, -0.5, 1)
            elif command == 'stop':
                motor_control(0, 0, 0)
            elif command == 'quit':
                break
    finally:
        client_socket.close()

def main():
    server_socket = setup_server()
    client_socket, addr = server_socket.accept()
    print("Connected by", addr)
    
    # Start autonomous navigation in a separate thread
    auto_nav_thread = threading.Thread(target=autonomous_navigation)
    auto_nav_thread.start()
    
    # Handle manual control in the main thread
    manual_control(client_socket)
    
    auto_nav_thread.join()
    GPIO.cleanup()

if __name__ == "__main__":
    main()
