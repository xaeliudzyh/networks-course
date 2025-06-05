import socket
import time
import threading
import random
import string
import struct
import tkinter as tk
from tkinter import ttk

def generate_random_data(size_bytes: int) -> bytes:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size_bytes)).encode('utf-8')

class TCPSenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Отправитель TCP")
        ttk.Label(root, text="IP получателя:").grid(row=0, column=0, sticky="e")
        self.ip_entry = ttk.Entry(root); self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.grid(row=0, column=1, pady=2)

        ttk.Label(root, text="Порт получателя:").grid(row=1, column=0, sticky="e")
        self.port_entry = ttk.Entry(root); self.port_entry.insert(0, "9000")
        self.port_entry.grid(row=1, column=1, pady=2)

        ttk.Label(root, text="Размер данных (KB):").grid(row=2, column=0, sticky="e")
        self.size_entry = ttk.Entry(root); self.size_entry.insert(0, "100")
        self.size_entry.grid(row=2, column=1, pady=2)

        self.send_button = ttk.Button(root, text="Отправить", command=self.start_sending)
        self.send_button.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Label(root, text="Статус:").grid(row=4, column=0, sticky="e")
        self.status_var = tk.StringVar(); ttk.Entry(root, textvariable=self.status_var, state="readonly").grid(row=4, column=1)

    def start_sending(self):
        threading.Thread(target=self.send_data, daemon=True).start()

    def send_data(self):
        server_ip = self.ip_entry.get()
        server_port = int(self.port_entry.get())
        size_kb = int(self.size_entry.get())
        size_bytes = size_kb * 1024

        data = generate_random_data(size_bytes)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((server_ip, server_port))
            send_time = time.time()
            sock.sendall(struct.pack('!d', send_time))
            time.sleep(0.001)
            sock.sendall(data)
            sock.close()
            self.status_var.set("Отправлено")
        except Exception as e:
            self.status_var.set("Ошибка")
            print(f"[TCP Sender] Ошибка: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TCPSenderGUI(root)
    root.mainloop()