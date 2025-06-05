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

class UDPSenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Отправитель UDP")
        ttk.Label(root, text="IP получателя:").grid(row=0, column=0, sticky="e")
        self.ip_entry = ttk.Entry(root); self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.grid(row=0, column=1, pady=2)

        ttk.Label(root, text="Порт получателя:").grid(row=1, column=0, sticky="e")
        self.port_entry = ttk.Entry(root); self.port_entry.insert(0, "10000")
        self.port_entry.grid(row=1, column=1, pady=2)

        ttk.Label(root, text="Число пакетов:").grid(row=2, column=0, sticky="e")
        self.packets_entry = ttk.Entry(root); self.packets_entry.insert(0, "20")
        self.packets_entry.grid(row=2, column=1, pady=2)

        ttk.Label(root, text="Размер пакета (KB):").grid(row=3, column=0, sticky="e")
        self.size_entry = ttk.Entry(root); self.size_entry.insert(0, "2")
        self.size_entry.grid(row=3, column=1, pady=2)

        self.send_button = ttk.Button(root, text="Отправить", command=self.start_sending)
        self.send_button.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Label(root, text="Статус:").grid(row=10, column=0, sticky="e")
        self.status_var = tk.StringVar(); ttk.Entry(root, textvariable=self.status_var, state="readonly").grid(row=5, column=1)

    def start_sending(self):
        threading.Thread(target=self.send_packets, daemon=True).start()

    def send_packets(self):
        server_ip = self.ip_entry.get()
        server_port = int(self.port_entry.get())
        num_packets = int(self.packets_entry.get())
        pkt_size_kb = int(self.size_entry.get())
        pkt_size = pkt_size_kb * 1024

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sent_count = 0
        loss_count = 0

        for i in range(num_packets):
            ts_bytes = struct.pack('!d', time.time())
            payload = generate_random_data(pkt_size)
            pkt = ts_bytes + payload
            try:
                sock.sendto(pkt, (server_ip, server_port))
                sent_count += 1
            except:
                loss_count += 1
            time.sleep(0.01)
        sock.sendto(b'', (server_ip, server_port))
        sock.close()
        loss_pct = (loss_count / num_packets) * 100 if num_packets > 0 else 0
        self.status_var.set(f"Отправлено {sent_count}, Потеря {loss_pct:.1f}%")

if __name__ == "__main__":
    root = tk.Tk()
    app = UDPSenderGUI(root)
    root.mainloop()
