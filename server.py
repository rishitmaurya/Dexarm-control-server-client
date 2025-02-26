import socket
import threading
import serial
import time
import cv2
import imutils
import numpy as np

# Server Configuration
HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 12345
VIDEO_PORT = 12346  # Separate port for video streaming

# Initialize Position Tracking
position = {"X": 0, "Y": 0, "Z": 0}  # Current position of DexArm

# Connect to DexArm via Serial (Update COM port)
try:
    dexarm = serial.Serial(port="COM10", baudrate=115200, timeout=1)  # Change "COM10" accordingly
    time.sleep(2)  # Allow DexArm to initialize
    print("[INFO] Connected to DexArm")
except Exception as e:
    print(f"[ERROR] Unable to connect to DexArm: {e}")
    dexarm = None  # Prevent crashes if serial fails

# Function to send a command dynamically
def send_command_to_dexarm(command):
    """Sends command to DexArm and ensures execution"""
    if dexarm:
        try:
            dexarm.flushInput()  # Clear buffer to prevent stale responses
            dexarm.write((command + "\n").encode())  # Send command
            time.sleep(0.1)  # Short delay to allow command execution
            dexarm.write(b"M400\n")  # Ensure DexArm waits for completion

            # Read response from DexArm
            response = dexarm.readline().decode().strip()
            return response if response else "Command executed."
        except Exception as e:
            return f"Error communicating with DexArm: {e}"
    else:
        return "DexArm not connected."

# Function to handle client requests
def handle_client(client_socket, address):
    """Handles communication with a client."""
    global position  # Use global position dictionary
    print(f"[NEW CONNECTION] {address} connected.")

    while True:
        try:
            command = client_socket.recv(1024).decode('utf-8').strip()
            if not command:
                break
            print(f"[{address}] Command received: {command}")

            gcode_command = None

            if command in ["X+", "X-", "Y+", "Y-", "Z+", "Z-"]:
                axis = command[0]  # Extract the axis (X, Y, Z)
                sign = 1 if "+" in command else -1  # Determine direction
                position[axis] += sign * 10  # Update position by ±10 units
                gcode_command = f"G0 {axis}{position[axis]}"  # Format G-code

            elif command in ["Z0"]:
                position["Z"] = 0
                gcode_command = "G0 Z0"

            elif command in ["Home", "GoToWorkOrigin"]:
                position = {"X": 0, "Y": 0, "Z": 0}  # Reset positions
                gcode_command = "G28" if command == "Home" else "G0 X0 Y0 Z0"

            elif command == "SetWorkOrigin":
                gcode_command = "G92 X0 Y0 Z0"

            elif command == "Pick":
                gcode_command = "M1000"

            elif command == "Place":
                gcode_command = "M1001"

            if gcode_command:
                response = send_command_to_dexarm(gcode_command)
            else:
                response = "Invalid Command"

            client_socket.send(response.encode('utf-8'))
        except ConnectionResetError:
            break

    print(f"[DISCONNECTED] {address} disconnected.")
    client_socket.close()

# Function to stream video to clients
def video_stream():
    """Streams video frames to clients."""
    video_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    video_server.bind((HOST, VIDEO_PORT))
    video_server.listen(5)
    print(f"[VIDEO STREAMING] Server is running on {HOST}:{VIDEO_PORT}")

    while True:
        client_socket, client_address = video_server.accept()
        print(f"[NEW VIDEO CONNECTION] {client_address} connected.")
        cap = cv2.VideoCapture(0)  # Open default camera

        if not cap.isOpened():
            print("[ERROR] Could not open camera.")
            client_socket.close()
            continue

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame = imutils.resize(frame, width=400)
                _, encoded_frame = cv2.imencode('.jpg', frame)
                data = np.array(encoded_frame)
                string_data = data.tobytes()
                
                # Send frame size first
                client_socket.sendall(len(string_data).to_bytes(4, 'big'))
                client_socket.sendall(string_data)
                # print(f"[INFO] Sending frame of size {len(string_data)} bytes")
        except (ConnectionResetError, BrokenPipeError):
            print(f"[VIDEO DISCONNECTED] {client_address} disconnected.")
        finally:
            cap.release()
            client_socket.close()
            
        


# Function to start the main server
def start_server():
    """Starts the server."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[LISTENING] Server is running on {HOST}:{PORT}")

    # Start video streaming in a separate thread
    threading.Thread(target=video_stream, daemon=True).start()

    while True:
        client_socket, client_address = server.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()
