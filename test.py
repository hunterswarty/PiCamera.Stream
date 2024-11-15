import socket
import threading
import time
from picamera2 import Picamera2, Preview
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
from libcamera import controls

class CameraControl:
    def __init__(self, tuning_file_path, flush=True, flicker_period=8333):
        # Load the tuning file
        self.tuning = Picamera2.load_tuning_file('arducam_64mp.json', dir='/usr/share/libcamera/ipa/rpi/pisp')
        self.camera = Picamera2(tuning=self.tuning)

        # Configure preview
        self.preview_config = self.camera.create_preview_configuration()
        self.camera.configure(self.preview_config)

        self.camera.start()

        # Set initial control values
        self.current_gain = 1.0  # Initial gain
        self.ev = 0  # Initial EV compensation
        self.sharpness = 1.0  # Initial sharpness setting
        self.hdr = False  # Initial HDR (off)

        # Initialize video recording
        self.encoder = H264Encoder(bitrate=5000000)
        self.output = FileOutput(stream)  # Adjust this path as needed
        self.camera.start_recording(self.encoder, self.output)

    def adjust_gain(self, increase=True):
        """Dynamically adjust gain."""
        self.current_gain += 0.1 if increase else -0.1
        self.current_gain = max(1.0, min(8.0, self.current_gain))  # Limit gain between 1.0 and 8.0
        self.camera.set_controls({"AnalogueGain": self.current_gain})

    def adjust_ev(self, increase=True):
        """Adjust EV (exposure value) compensation."""
        self.ev += 1 if increase else -1
        self.camera.set_controls({"ExposureValue": self.ev})

    def toggle_hdr(self):
        """Toggle HDR mode on or off."""
        self.hdr = not self.hdr
        self.camera.set_controls({"hdr": "sensor" if self.hdr else "off"})

    def adjust_sharpness(self, increase=True):
        """Adjust image sharpness."""
        self.sharpness += 0.1 if increase else -0.1
        self.sharpness = max(0.0, min(2.0, self.sharpness))  # Limit sharpness between 0.0 and 2.0
        self.camera.set_controls({"Sharpness": self.sharpness})

    def stop(self):
        """Stop the camera preview and recording."""
        self.camera.stop_recording()
        self.camera.stop()

class CameraServer:
    def __init__(self, ip='0.0.0.0', port=8888, tuning_file_path='/usr/share/libcamera/ipa/rpi/pisp/arducam_64mp.json'):
        self.camera_control = CameraControl(tuning_file_path)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((ip, port))
        self.sock.listen(1)

    def handle_client(self, conn):
        try:
            while True:
                command = conn.recv(1024).decode().strip().lower()
                if command == "stop":
                    self.camera_control.stop()
                    break
                elif command == "g+":
                    self.camera_control.adjust_gain(increase=True)
                elif command == "g-":
                    self.camera_control.adjust_gain(increase=False)
                elif command == "ev+":
                    self.camera_control.adjust_ev(increase=True)
                elif command == "ev-":
                    self.camera_control.adjust_ev(increase=False)
                elif command == "hdr":
                    self.camera_control.toggle_hdr()
                elif command == "sharp+":
                    self.camera_control.adjust_sharpness(increase=True)
                elif command == "sharp-":
                    self.camera_control.adjust_sharpness(increase=False)
                else:
                    conn.sendall(b"Unknown command.\n")
        finally:
            conn.close()

    def start_server(self):
        print("Waiting for a connection...")
        while True:
            conn, addr = self.sock.accept()
            print(f"Connected to {addr}")
            client_thread = threading.Thread(target=self.handle_client, args=(conn,))
            client_thread.start()

if __name__ == "__main__":
    server = CameraServer()
    server.start_server()
