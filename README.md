# DexArm Server-Client System

This project implements a server-client architecture to control a DexArm robotic arm and stream video feed from a connected camera. The server handles G-code commands sent by clients to control the DexArm and streams real-time video to clients.

## Features
- Control DexArm movement via G-code commands.
- Stream live video from the camera to connected clients.
- Multi-threaded server for handling multiple clients.
- Simple TCP socket communication.

## Prerequisites
Ensure you have the following installed before running the project:
- Python 3.x
- OpenCV (`cv2`)
- NumPy (`numpy`)
- PySerial (`serial`)

You can install the required dependencies using:
```sh
pip install opencv-python numpy pyserial
```

## Project Structure
```
server-client-dexarm/
│── server.py        # Main server script
│── client.py        # Client script for connecting and controlling DexArm
│── gui.py           # GUI-based client for interaction
│── README.md        # Project documentation
```

## How to Run
### Start the Server
1. Connect DexArm to the computer via USB.
2. Update the `COM` port in `server.py` to match DexArm's port.
3. Run the server:
   ```sh
   python server.py
   ```

### Start the Client
1. Update the server IP in `client.py`.
2. Run the client script:
   ```sh
   python client.py
   ```


## Troubleshooting
- If the camera feed is not showing, ensure the correct camera index is used in `server.py` (`cv2.VideoCapture(0)`).
- If the connection fails, check firewall settings and ensure the correct IP and port are used.
- If the DexArm is not responding, verify the serial connection and update the `COM` port.



