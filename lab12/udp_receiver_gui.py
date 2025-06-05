import socket
import time
import struct
import threading
import tkinter as tk
from tkinter import ttk

class UDPReceiverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Получатель UDP")

        ttk.Label(root, text="Локальный IP (или оставить пустым):").grid(row=0, column=0, sticky="e")
        self.ip_entry = ttk.Entry(root); self.ip_entry.insert(0, "")
        self.ip_entry.grid(row=0, column=1, pady=2)

        ttk.Label(root, text="Порт для получения:").grid(row=1, column=0, sticky="e")
        self.port_entry = ttk.Entry(root); self.port_entry.insert(0, "10000")
        self.port_entry.grid(row=1, column=1, pady=2)

        self.start_button = ttk.Button(root, text="Получить", command=self.start_receiving)
        self.start_button.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Label(root, text="Получено байт:").grid(row=3, column=0, sticky="e")
        self.bytes_var = tk.StringVar(); ttk.Entry(root, textvariable=self.bytes_var, state="readonly").grid(row=3, column=1)

        ttk.Label(root, text="Время приёма (s):").grid(row=4, column=0, sticky="e")
        self.time_var = tk.StringVar(); ttk.Entry(root, textvariable=self.time_var, state="readonly").grid(row=4, column=1)

        ttk.Label(root, text="Скорость (KB/s):").grid(row=5, column=0, sticky="e")
        self.speed_var = tk.StringVar(); ttk.Entry(root, textvariable=self.speed_var, state="readonly").grid(row=5, column=1)

        self.server_thread = None

    def start_receiving(self):
        if self.server_thread and self.server_thread.is_alive():
            return
        ip = self.ip_entry.get().strip()
        host = ip if ip else "0.0.0.0"
        port = int(self.port_entry.get())
        self.server_thread = threading.Thread(target=self.receive_packets, args=(host, port), daemon=True)
        self.server_thread.start()

    def receive_packets(self, host: str, port: int):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((host, port))
        sock.settimeout(5.0)

        received_bytes = 0
        start_time = None

        while True:
            try:
                data, addr = sock.recvfrom(8192)
            except socket.timeout:
                break
            if not data:
                break
            if start_time is None:
                start_time = time.time()
            try:
                sent_ts = struct.unpack('!d', data[:8])[0]
            except:
                continue
            payload = data[8:]
            received_bytes += len(payload)

        end_time = time.time()
        duration = end_time - (start_time if start_time else end_time)
        speed_kb_s = received_bytes / duration / 1024 if duration > 0 else 0
        self.bytes_var.set(f"{received_bytes}")
        self.time_var.set(f"{duration:.4f}")
        self.speed_var.set(f"{speed_kb_s:.2f}")

        sock.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = UDPReceiverGUI(root)
    root.mainloop()
