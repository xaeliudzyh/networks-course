import socket
import threading
import time
import struct
import tkinter as tk
from tkinter import ttk

class TCPReceiverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Получатель TCP")
        ttk.Label(root, text="Локальный IP (или оставить пустым):").grid(row=0, column=0, sticky="e")
        self.ip_entry = ttk.Entry(root); self.ip_entry.insert(0, "")
        self.ip_entry.grid(row=0, column=1, pady=2)

        ttk.Label(root, text="Порт для получения:").grid(row=1, column=0, sticky="e")
        self.port_entry = ttk.Entry(root); self.port_entry.insert(0, "9000")
        self.port_entry.grid(row=1, column=1, pady=2)

        self.start_button = ttk.Button(root, text="Получить", command=self.start_receiving)
        self.start_button.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Label(root, text="Время передачи (s):").grid(row=3, column=0, sticky="e")
        self.time_var = tk.StringVar(); ttk.Entry(root, textvariable=self.time_var, state="readonly").grid(row=3, column=1)

        ttk.Label(root, text="Скорость (KB/s):").grid(row=4, column=0, sticky="e")
        self.speed_var = tk.StringVar(); ttk.Entry(root, textvariable=self.speed_var, state="readonly").grid(row=4, column=1)

        ttk.Label(root, text="Получено байт:").grid(row=5, column=0, sticky="e")
        self.bytes_var = tk.StringVar(); ttk.Entry(root, textvariable=self.bytes_var, state="readonly").grid(row=5, column=1)

        self.server_thread = None

    def start_receiving(self):
        if self.server_thread and self.server_thread.is_alive():
            return  # уже запущено
        ip = self.ip_entry.get().strip()
        host = ip if ip else "0.0.0.0"
        port = int(self.port_entry.get())
        self.server_thread = threading.Thread(target=self.receive_once, args=(host, port), daemon=True)
        self.server_thread.start()

    def receive_once(self, host: str, port: int):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((host, port))
        server_sock.listen(1)
        conn, addr = server_sock.accept()
        start_time = None
        total_bytes = 0
        try:
            hdr = conn.recv(8)
            if len(hdr) < 8:
                conn.close()
                server_sock.close()
                return
            send_ts = struct.unpack('!d', hdr)[0]
            start_time = send_ts
        except:
            conn.close()
            server_sock.close()
            return
        while True:
            data = conn.recv(4096)
            if not data:
                break
            total_bytes += len(data)

        end_time = time.time()
        duration = end_time - start_time if start_time else 0
        speed_kb_s = total_bytes / duration / 1024 if duration > 0 else 0

        self.time_var.set(f"{duration:.4f}")
        self.speed_var.set(f"{speed_kb_s:.2f}")
        self.bytes_var.set(f"{total_bytes}")

        conn.close()
        server_sock.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = TCPReceiverGUI(root)
    root.mainloop()