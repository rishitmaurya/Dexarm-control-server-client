# client.py

import socket
import cv2
import numpy as np
import sys
import threading
import struct
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel, QLineEdit, QComboBox, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage

# Server Configuration
SERVER_IP = " "  # Change this to your server's IP
PORT = 12346

class VideoStreamThread(QThread):
    update_frame_signal = pyqtSignal(np.ndarray)

    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket
        self.running = True

    def run(self):
        while self.running:
            frame = self.receive_frame()
            if frame is not None:
                self.update_frame_signal.emit(frame)

    def receive_frame(self):
        """Receive a frame from the server and decode it."""
        try:
            data = b""
            payload_size = struct.calcsize("Q")  # Expected size of message header
            while len(data) < payload_size:
                packet = self.client_socket.recv(4 * 1024)
                if not packet:
                    return None
                data += packet

            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]

            while len(data) < msg_size:
                data += self.client_socket.recv(4 * 1024)

            frame_data = data[:msg_size]
            frame = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

            if frame is None:
                print("Decoding failed")
                return None

            print("Frame received successfully")
            return frame

        except Exception as e:
            print(f"Error receiving frame: {e}")
            return None

    def stop(self):
        """Stop the thread."""
        self.running = False
        self.quit()
        self.wait()


class DexArmControlPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DexArm Control Panel")
        self.setGeometry(100, 100, 1000, 600)  # Updated width to 1000
        self.initUI()

        # Connect to server
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((SERVER_IP, PORT))
            self.update_chat("Connected to server!")
            self.start_video_thread()  # Start video streaming thread
        except Exception as e:
            self.update_chat(f"Connection failed: {e}")

    def initUI(self):
        layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Control Panel
        tab_label = QLabel("Control")
        left_layout.addWidget(tab_label)

        # Grid Layout for Movement Buttons
        grid_layout = QGridLayout()
        commands = [
            ("Y+", 0, 1), ("Z+", 0, 2), ("Home", 0, 3),
            ("X+", 1, 0), ("Z0", 1, 1), ("X-", 1, 2),
            ("Y-", 2, 1), ("Z-", 2, 2)
        ]

        for text, row, col in commands:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _, cmd=text: self.send_command(cmd))
            grid_layout.addWidget(btn, row, col)

        left_layout.addLayout(grid_layout)

        # Additional buttons
        self.goToOriginButton = QPushButton("Go To Work Origin")
        self.setWorkOriginButton = QPushButton("Set Work Origin")
        self.goToOriginButton.clicked.connect(lambda: self.send_command("GoToWorkOrigin"))
        self.setWorkOriginButton.clicked.connect(lambda: self.send_command("SetWorkOrigin"))
        left_layout.addWidget(self.goToOriginButton)
        left_layout.addWidget(self.setWorkOriginButton)

        # Input for Distance
        self.distanceInput = QLineEdit("10")
        left_layout.addWidget(QLabel("Distance (mm):"))
        left_layout.addWidget(self.distanceInput)

        # Mode Dropdown
        self.modeDropdown = QComboBox()
        self.modeDropdown.addItems(["Fast", "Normal", "Slow"])
        left_layout.addWidget(QLabel("Select Mode:"))
        left_layout.addWidget(self.modeDropdown)

        # Speed Input
        self.speedInput = QLineEdit("1000")
        left_layout.addWidget(QLabel("Speed (mm/min):"))
        left_layout.addWidget(self.speedInput)

        # Tool Dropdown
        self.toolDropdown = QComboBox()
        self.toolDropdown.addItems(["AirPick", "Vacuum", "Gripper"])
        left_layout.addWidget(QLabel("Select Tool:"))
        left_layout.addWidget(self.toolDropdown)

        # Pick & Place Buttons
        button_layout = QHBoxLayout()
        self.placeButton = QPushButton("Place")
        self.pickButton = QPushButton("Pick")
        self.placeButton.clicked.connect(lambda: self.send_command("Place"))
        self.pickButton.clicked.connect(lambda: self.send_command("Pick"))
        button_layout.addWidget(self.placeButton)
        button_layout.addWidget(self.pickButton)
        left_layout.addLayout(button_layout)

        # Chat Section
        chat_label = QLabel("Chat with Server")
        left_layout.addWidget(chat_label)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        left_layout.addWidget(self.chat_display)

        self.message_entry = QLineEdit()
        left_layout.addWidget(self.message_entry)
        self.message_entry.returnPressed.connect(self.send_custom_command)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_custom_command)
        left_layout.addWidget(send_button)

        # Camera Section
        camera_label = QLabel("Camera")
        right_layout.addWidget(camera_label)

        self.camera_label = QLabel(self)
        self.camera_label.setFixedSize(400, 550)
        self.camera_label.setStyleSheet("background-color: black; border: 1px solid gray;")
        right_layout.addWidget(self.camera_label)

        # Set layouts
        layout.addLayout(left_layout, stretch=2)
        layout.addLayout(right_layout, stretch=1)
        self.setLayout(layout)

    def start_video_thread(self):
        """Start the video streaming thread."""
        self.video_thread = VideoStreamThread(self.client)
        self.video_thread.update_frame_signal.connect(self.update_camera)
        self.video_thread.start()

    def update_camera(self, frame):
        """Update the camera display with the received frame."""
        print("Updating camera feed")
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        self.camera_label.setPixmap(pixmap)

    def send_command(self, command):
        """Send predefined command to server and display response."""
        self.send_to_server(command)

    def send_custom_command(self):
        """Send custom command entered by user."""
        command = self.message_entry.text()
        if command:
            self.send_to_server(command)
            self.message_entry.clear()

    def send_to_server(self, command):
        """Send command and receive response."""
        try:
            self.client.send(command.encode('utf-8'))
            response = self.client.recv(1024).decode('utf-8')
            self.update_chat(f"You: {command}")
            self.update_chat(f"Server: {response}")
        except Exception as e:
            self.update_chat(f"Error: {e}")

    def update_chat(self, message):
        """Update chat display."""
        self.chat_display.append(message)
        self.chat_display.ensureCursorVisible()

    def closeEvent(self, event):
        """Close connection and stop video thread when window is closed."""
        self.video_thread.stop()
        self.client.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DexArmControlPanel()
    window.show()
    sys.exit(app.exec())
